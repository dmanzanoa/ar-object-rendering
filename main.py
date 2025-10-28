"""
main.py
=======

This script demonstrates how to use the ``ar_render`` module to place a
transparent object into a background scene.  It loads a background image
(``background.jpg``) and a sample object (any PNG with an alpha
channel), computes the appropriate scale based on the camera geometry and
specified object height, and pastes the object at one or more locations on
the ground plane.

Run the script from the command line, providing the path to the object
image and its real‑world height.  You can optionally specify multiple
locations where the object should be rendered.  The rendered images will
be saved alongside the originals for inspection.

Example usage
-------------

```
python main.py --object dog.png --height 0.4 --positions 1300,1300 1800,2000
```

This will render the 0.4 m tall dog at two positions in the scene and
write the resulting images ``render_0.png`` and ``render_1.png`` in the
current directory.
"""

from __future__ import annotations

import argparse
import os
from typing import List, Tuple

import cv2

from ar_render import CameraParams, load_rgba, paste_object


def parse_positions(position_strings: List[str]) -> List[Tuple[int, int]]:
    """Parse a list of ``"y,x"`` position strings into tuples of ints."""
    positions: List[Tuple[int, int]] = []
    for s in position_strings:
        try:
            y_str, x_str = s.split(",")
            y_px = int(y_str)
            x_px = int(x_str)
            positions.append((y_px, x_px))
        except Exception as e:
            raise argparse.ArgumentTypeError(
                f"Invalid position format '{s}'. Expected 'y,x'."
            ) from e
    return positions


def main() -> None:
    parser = argparse.ArgumentParser(description="Render an object into a scene")
    parser.add_argument(
        "--background",
        type=str,
        default="background.jpg",
        help="Path to the background JPEG image",
    )
    parser.add_argument(
        "--object",
        type=str,
        required=True,
        help="Path to a PNG object image with transparency",
    )
    parser.add_argument(
        "--height",
        type=float,
        required=True,
        help="Real‑world height of the object in metres",
    )
    parser.add_argument(
        "--positions",
        nargs="+",
        default=["1300,1300", "1800,2000"],
        help="One or more positions on the image where the object base should be placed (format y,x)",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default="renders",
        help="Directory where rendered images will be saved",
    )
    args = parser.parse_args()

    # Create output directory if necessary.
    os.makedirs(args.outdir, exist_ok=True)

    # Load images.
    bg_bgr = cv2.imread(args.background)
    if bg_bgr is None:
        raise FileNotFoundError(f"Background image '{args.background}' could not be loaded")
    obj_bgr, obj_alpha = load_rgba(args.object)

    # Define camera parameters according to the assignment specification.
    camera = CameraParams(
        focal_length_mm=15.0,
        sensor_width_mm=36.0,
        sensor_height_mm=24.0,
        camera_height_mm=1600.0,  # 160 cm converted to mm
        ground_distance_mm=2000.0,
    )

    # Convert positions from strings to tuples.
    positions = parse_positions(args.positions)

    # Render the object at each specified location.
    for i, (y_px, x_px) in enumerate(positions):
        try:
            rendered = paste_object(
                bg_bgr,
                obj_bgr,
                obj_alpha,
                (y_px, x_px),
                args.height,
                camera,
            )
        except ValueError as e:
            print(f"Skipping position {(y_px, x_px)}: {e}")
            continue
        out_path = os.path.join(args.outdir, f"render_{i}.png")
        cv2.imwrite(out_path, cv2.cvtColor(rendered, cv2.COLOR_BGR2RGB))
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
