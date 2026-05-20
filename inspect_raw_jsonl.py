#!/usr/bin/env python3
"""Inspect raw MANUS/Vive combined JSONL captures."""

import argparse
import json
from pathlib import Path
from statistics import mean


def parse_args():
    parser = argparse.ArgumentParser(description="Inspect raw combined MANUS JSONL captures.")
    parser.add_argument("--path", required=True, help="Path to raw_frames.jsonl.")
    return parser.parse_args()


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def summarize(values):
    if not values:
        return "n/a"
    return f"min={min(values):.3f}, mean={mean(values):.3f}, max={max(values):.3f}"


def main():
    args = parse_args()
    path = Path(args.path)

    stats = {
        "total lines": 0,
        "valid json lines": 0,
        "frames with skeletons": 0,
        "frames with trackers": 0,
        "frames with node 4": 0,
        "frames with node 9": 0,
        "frames with tracker position": 0,
        "frames with tracker valid=true": 0,
        "frames with combined_monotonic_ms": 0,
        "frames with skeleton_publish_time": 0,
        "frames with tracker_publish_time": 0,
        "frames with skeleton_receive_monotonic_ms": 0,
        "frames with tracker_receive_monotonic_ms": 0,
        "frames with skeleton_callback_index": 0,
        "frames with tracker_callback_index": 0,
        "frames where each tracker has last_update_time": 0,
    }

    skeleton_tracker_deltas = []
    combined_skeleton_deltas = []
    combined_tracker_deltas = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            stats["total lines"] += 1
            line = line.strip()
            if not line:
                continue

            try:
                frame = json.loads(line)
            except json.JSONDecodeError:
                continue

            stats["valid json lines"] += 1

            skeletons = frame.get("skeletons") or []
            trackers = frame.get("trackers") or []

            if skeletons:
                stats["frames with skeletons"] += 1
            if trackers:
                stats["frames with trackers"] += 1
            if any(len(skeleton.get("nodes") or []) > 4 for skeleton in skeletons):
                stats["frames with node 4"] += 1
            if any(len(skeleton.get("nodes") or []) > 9 for skeleton in skeletons):
                stats["frames with node 9"] += 1
            if any("position" in tracker for tracker in trackers):
                stats["frames with tracker position"] += 1
            if any(tracker.get("valid") is True for tracker in trackers):
                stats["frames with tracker valid=true"] += 1
            if trackers and all("last_update_time" in tracker for tracker in trackers):
                stats["frames where each tracker has last_update_time"] += 1

            for field in (
                "combined_monotonic_ms",
                "skeleton_publish_time",
                "tracker_publish_time",
                "skeleton_receive_monotonic_ms",
                "tracker_receive_monotonic_ms",
                "skeleton_callback_index",
                "tracker_callback_index",
            ):
                if frame.get(field) is not None:
                    stats[f"frames with {field}"] += 1

            combined_ms = frame.get("combined_monotonic_ms")
            skeleton_ms = frame.get("skeleton_receive_monotonic_ms")
            tracker_ms = frame.get("tracker_receive_monotonic_ms")

            if is_number(skeleton_ms) and is_number(tracker_ms):
                skeleton_tracker_deltas.append(abs(skeleton_ms - tracker_ms))
            if is_number(combined_ms) and is_number(skeleton_ms):
                combined_skeleton_deltas.append(combined_ms - skeleton_ms)
            if is_number(combined_ms) and is_number(tracker_ms):
                combined_tracker_deltas.append(combined_ms - tracker_ms)

    for name, value in stats.items():
        print(f"{name}: {value}")

    print(
        "abs(skeleton_receive_monotonic_ms - tracker_receive_monotonic_ms): "
        f"{summarize(skeleton_tracker_deltas)}"
    )
    print(
        "combined_monotonic_ms - skeleton_receive_monotonic_ms: "
        f"{summarize(combined_skeleton_deltas)}"
    )
    print(
        "combined_monotonic_ms - tracker_receive_monotonic_ms: "
        f"{summarize(combined_tracker_deltas)}"
    )


if __name__ == "__main__":
    main()
