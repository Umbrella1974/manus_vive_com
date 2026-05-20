#!/usr/bin/env python3
"""Capture raw MANUS/Vive combined JSON frames as JSONL."""

import argparse
import time
from pathlib import Path

from manus_data_receiver import ManusDataReceiver


def parse_args():
    parser = argparse.ArgumentParser(description="Capture raw combined MANUS JSON frames as JSONL.")
    parser.add_argument("--host", default="127.0.0.1", help="TCP host to bind. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8888, help="TCP port to bind. Default: 8888")
    parser.add_argument("--out", default="data/raw_frames.jsonl", help="Output JSONL path.")
    parser.add_argument("--duration", type=float, default=None, help="Stop this many seconds after the first frame.")
    parser.add_argument("--max-frames", type=int, default=None, help="Stop after this many frames.")
    parser.add_argument("--print-every", type=int, default=30, help="Print stats every N frames.")
    parser.set_defaults(flush=True)
    parser.add_argument("--flush", dest="flush", action="store_true", help="Flush after every frame. Default: enabled.")
    parser.add_argument("--no-flush", dest="flush", action="store_false", help="Do not flush after every frame.")
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = Path(args.out)
    receiver = ManusDataReceiver(
        host=args.host,
        port=args.port,
        raw_jsonl_path=str(output_path),
        flush_raw_jsonl=args.flush,
    )

    first_frame_time = None
    last_printed_frame = 0

    def on_frame(frame_data):
        nonlocal first_frame_time, last_printed_frame

        if first_frame_time is None:
            first_frame_time = time.time()
            print("[CAPTURE] First frame received; duration timer started.")

        if args.print_every > 0 and receiver.frame_count - last_printed_frame >= args.print_every:
            last_printed_frame = receiver.frame_count
            skeleton_count = len(frame_data.get("skeletons", []))
            tracker_count = len(frame_data.get("trackers", []))
            print(
                f"[CAPTURE] frames={receiver.frame_count} "
                f"skeletons={skeleton_count} trackers={tracker_count} "
                f"frame={frame_data.get('frame')}"
            )

    receiver.register_callback(on_frame)
    script_start_time = time.time()

    try:
        receiver.start()

        while receiver.running:
            if args.max_frames is not None and receiver.frame_count >= args.max_frames:
                break

            if args.duration is not None and first_frame_time is not None:
                if time.time() - first_frame_time >= args.duration:
                    break

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n[CAPTURE] Interrupted by user.")
    finally:
        receiver.stop()
        elapsed = time.time() - script_start_time
        print(f"[CAPTURE] total frames received: {receiver.frame_count}")
        print(f"[CAPTURE] output path: {output_path}")
        print(f"[CAPTURE] elapsed time: {elapsed:.2f}s")


if __name__ == "__main__":
    main()
