#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import av
import cv2
import numpy as np
from bootstrap_runtime import SetupError, require_ready_state

PAPER_BGR = (215, 235, 245)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="세로 손그림 이미지를 화이트보드 드로잉 MP4로 렌더링")
    parser.add_argument("image", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--duration-ms", type=int, required=True)
    parser.add_argument("--regions-json", type=Path)
    parser.add_argument("--hand", type=Path)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--pause-ms", type=int, default=500)
    parser.add_argument("--brush-px", type=int, default=86)
    parser.add_argument("--setup-state", type=Path, help="기본 위치가 아닌 setup-state.json 경로")
    return parser.parse_args()


def fit_image(source: np.ndarray, width: int, height: int) -> tuple[np.ndarray, float, int, int]:
    src_h, src_w = source.shape[:2]
    scale = min(width / src_w, height / src_h)
    new_w = max(2, int(round(src_w * scale)))
    new_h = max(2, int(round(src_h * scale)))
    resized = cv2.resize(source, (new_w, new_h), interpolation=cv2.INTER_AREA)
    canvas = np.full((height, width, 3), PAPER_BGR, dtype=np.uint8)
    offset_x = (width - new_w) // 2
    offset_y = (height - new_h) // 2
    canvas[offset_y : offset_y + new_h, offset_x : offset_x + new_w] = resized
    return canvas, scale, offset_x, offset_y


def read_regions(path: Path | None, src_w: int, src_h: int) -> list[dict[str, int]]:
    if path is None:
        return [{"x": 0, "y": 0, "width": src_w, "height": src_h}]
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get("regions", data.get("elements", [])) if isinstance(data, dict) else data
    regions: list[dict[str, int]] = []
    for item in raw:
        box = item.get("region", item) if isinstance(item, dict) else {}
        try:
            x = max(0, int(box["x"]))
            y = max(0, int(box["y"]))
            w = max(1, min(int(box["width"]), src_w - x))
            h = max(1, min(int(box["height"]), src_h - y))
        except (KeyError, TypeError, ValueError):
            continue
        if x < src_w and y < src_h:
            regions.append({"x": x, "y": y, "width": w, "height": h})
    return regions or [{"x": 0, "y": 0, "width": src_w, "height": src_h}]


def transform_regions(
    regions: list[dict[str, int]],
    scale: float,
    offset_x: int,
    offset_y: int,
    width: int,
    height: int,
) -> list[dict[str, int]]:
    result = []
    for box in regions:
        x = max(0, min(width - 1, offset_x + int(round(box["x"] * scale))))
        y = max(0, min(height - 1, offset_y + int(round(box["y"] * scale))))
        w = max(1, min(width - x, int(round(box["width"] * scale))))
        h = max(1, min(height - y, int(round(box["height"] * scale))))
        result.append({"x": x, "y": y, "width": w, "height": h})
    return result


def serpentine_path(box: dict[str, int], brush: int) -> list[tuple[int, int]]:
    x0, y0 = box["x"], box["y"]
    x1 = x0 + box["width"] - 1
    y1 = y0 + box["height"] - 1
    margin = max(2, brush // 3)
    left, right = min(x1, x0 + margin), max(x0, x1 - margin)
    top, bottom = min(y1, y0 + margin), max(y0, y1 - margin)
    row_step = max(10, int(brush * 0.55))
    point_step = max(8, int(brush * 0.18))
    points: list[tuple[int, int]] = []
    row = 0
    for y in range(top, bottom + 1, row_step):
        xs = list(range(left, right + 1, point_step))
        if not xs or xs[-1] != right:
            xs.append(right)
        if row % 2:
            xs.reverse()
        points.extend((x, y) for x in xs)
        row += 1
    return points or [((x0 + x1) // 2, (y0 + y1) // 2)]


def allocate_frames(weights: list[float], total: int) -> list[int]:
    if not weights:
        return []
    total = max(total, len(weights))
    weight_sum = sum(weights)
    frames = [max(1, int(total * weight / weight_sum)) for weight in weights]
    while sum(frames) < total:
        index = max(range(len(weights)), key=weights.__getitem__)
        frames[index] += 1
    while sum(frames) > total:
        candidates = [i for i, value in enumerate(frames) if value > 1]
        if not candidates:
            break
        index = max(candidates, key=lambda i: frames[i])
        frames[index] -= 1
    return frames


def draw_until(mask: np.ndarray, path: list[tuple[int, int]], start: int, end: int, brush: int) -> None:
    if end <= start:
        return
    first = max(0, start)
    for index in range(first, min(end, len(path) - 1)):
        cv2.line(mask, path[index], path[index + 1], 255, brush, cv2.LINE_AA)
    if len(path) == 1:
        cv2.circle(mask, path[0], brush // 2, 255, -1, cv2.LINE_AA)


def compose_frame(
    source: np.ndarray,
    ink_layer: np.ndarray,
    ink_mask: np.ndarray,
    color_mask: np.ndarray,
) -> np.ndarray:
    canvas = np.full_like(source, PAPER_BGR)
    ink_alpha = (ink_mask.astype(np.float32) / 255.0)[..., None]
    canvas = (canvas * (1.0 - ink_alpha) + ink_layer * ink_alpha).astype(np.uint8)
    color_alpha = (color_mask.astype(np.float32) / 255.0)[..., None]
    return (canvas * (1.0 - color_alpha) + source * color_alpha).astype(np.uint8)


def load_hand(path: Path | None, canvas_width: int) -> np.ndarray | None:
    if path is None or not path.is_file():
        return None
    hand = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if hand is None or hand.shape[2] != 4:
        return None
    target_w = max(140, int(canvas_width * 0.28))
    target_h = max(1, int(hand.shape[0] * target_w / hand.shape[1]))
    return cv2.resize(hand, (target_w, target_h), interpolation=cv2.INTER_AREA)


def overlay_hand(frame: np.ndarray, hand: np.ndarray | None, tip: tuple[int, int]) -> np.ndarray:
    if hand is None:
        return frame
    hand_h, hand_w = hand.shape[:2]
    left = int(tip[0] - hand_w * 0.09)
    top = int(tip[1] - hand_h * 0.05)
    x0, y0 = max(0, left), max(0, top)
    x1, y1 = min(frame.shape[1], left + hand_w), min(frame.shape[0], top + hand_h)
    if x0 >= x1 or y0 >= y1:
        return frame
    hx0, hy0 = x0 - left, y0 - top
    crop = hand[hy0 : hy0 + (y1 - y0), hx0 : hx0 + (x1 - x0)]
    alpha = (crop[:, :, 3].astype(np.float32) / 255.0)[..., None]
    frame[y0:y1, x0:x1] = (
        frame[y0:y1, x0:x1] * (1.0 - alpha) + crop[:, :, :3] * alpha
    ).astype(np.uint8)
    return frame


def encode_frames(output: Path, frames, width: int, height: int, fps: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    container = av.open(str(output), mode="w")
    stream = container.add_stream("libx264", rate=fps)
    stream.width = width
    stream.height = height
    stream.pix_fmt = "yuv420p"
    stream.options = {"crf": "20", "preset": "medium"}
    for image in frames:
        frame = av.VideoFrame.from_ndarray(image, format="bgr24")
        for packet in stream.encode(frame):
            container.mux(packet)
    for packet in stream.encode(None):
        container.mux(packet)
    container.close()


def render(args: argparse.Namespace):
    source_raw = cv2.imread(str(args.image), cv2.IMREAD_COLOR)
    if source_raw is None:
        raise FileNotFoundError(f"이미지를 읽을 수 없습니다: {args.image}")
    src_h, src_w = source_raw.shape[:2]
    source, scale, offset_x, offset_y = fit_image(source_raw, args.width, args.height)
    raw_regions = read_regions(args.regions_json, src_w, src_h)
    regions = transform_regions(raw_regions, scale, offset_x, offset_y, args.width, args.height)
    paths = [serpentine_path(box, args.brush_px) for box in regions]

    total_frames = max(2, round(args.duration_ms * args.fps / 1000))
    pause_frames = min(total_frames - 1, max(1, round(args.pause_ms * args.fps / 1000)))
    draw_frames = total_frames - pause_frames
    jobs = []
    weights = []
    for path in paths:
        jobs.extend([("ink", path), ("color", path)])
        weights.extend([max(1, len(path)) * 2.0, max(1, len(path))])
    frame_counts = allocate_frames(weights, draw_frames)

    gray = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 45, 135)
    edges = cv2.dilate(edges, np.ones((2, 2), dtype=np.uint8), iterations=1)
    ink_layer = np.full_like(source, PAPER_BGR)
    ink_layer[edges > 0] = (55, 55, 55)
    ink_mask = np.zeros((args.height, args.width), dtype=np.uint8)
    color_mask = np.zeros_like(ink_mask)
    hand = load_hand(args.hand, args.width)

    def frame_iterator():
        for (kind, path), count in zip(jobs, frame_counts):
            mask = ink_mask if kind == "ink" else color_mask
            previous = 0
            for frame_index in range(count):
                progress = (frame_index + 1) / count
                current = max(1, int(round(progress * max(1, len(path) - 1))))
                draw_until(mask, path, previous, current, args.brush_px)
                previous = current
                frame = compose_frame(source, ink_layer, ink_mask, color_mask)
                yield overlay_hand(frame, hand, path[min(current, len(path) - 1)])
        for _ in range(pause_frames):
            yield source.copy()

    encode_frames(args.output, frame_iterator(), args.width, args.height, args.fps)


def main() -> int:
    args = parse_args()
    if args.duration_ms < 500 or args.fps < 1 or args.width < 2 or args.height < 2:
        print("[error] duration, fps, width, height 값을 확인하세요.", file=sys.stderr)
        return 2
    try:
        require_ready_state(args.setup_state)
    except SetupError as error:
        print(f"[error] {error}", file=sys.stderr)
        return 2
    try:
        render(args)
    except Exception as error:
        print(f"[error] {error}", file=sys.stderr)
        return 1
    print(f"OUTPUT={args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
