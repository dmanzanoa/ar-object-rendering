# Augmented Reality Object Rendering

This project provides a simple augmented reality (AR) object renderer implemented in Python. It demonstrates how to insert a virtual object into a background photograph at the correct scale and perspective using a pinhole camera model.

## Overview
Given a background photograph, a transparent object image (with an alpha channel) and the object's real‑world height (in metres), the renderer computes the appropriate size of the object in pixels based on camera parameters (focal length, sensor size, camera height and distance to the ground). It then pastes the object onto the background at a specified ground‑plane location, handling alpha blending.

The camera is 1.6 m above the ground, has a focal length of 15 mm, a 36×24 mm sensor, and looks straight ahead parallel to the ground plane

## Repository structure
| File | Description |
| --- | --- |
| `ar_render.py` | Core module defining `CameraParams` dataclass and functions to compute object pixel size and paste objects onto a background. |
| `main.py` | Command‑line interface that loads images, parses positions and renders objects using functions from `ar_render.py`. |
| `requirements.txt` | Python dependencies needed (`opencv-python`, `numpy`). |
| `README.md` | This documentation. |

## Installation
1. Clone this repository.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

You will also need background and object images. The object image must be a PNG with an alpha channel. The background image should be a photograph captured with the same camera parameters specified above.

## Usage
Run the command‑line script to render the object at one or more positions:

```
python main.py --object path/to/object.png --height 0.4 --positions 1300,1300 1800,2000 --background path/to/background.jpg --outdir renders
```

- `--object` – path to the PNG object.
- `--height` – real-world height of the object in metres.
- `--positions` – one or more y,x pairs specifying where the base of the object should appear in the image.
- `--background` – path to the background JPEG (default `background.jpg`).
- `--outdir` – directory where rendered images will be saved (default `renders`).

The script will output images `render_0.png`, `render_1.png`, etc., with the object inserted at the specified positions. Positions must lie on the ground plane and within the frame; otherwise a warning is printed.

## Customising camera parameters
The camera parameters are encapsulated in the `CameraParams` dataclass. You can adapt the renderer to other cameras by changing focal length, sensor size, camera height or ground distance. See `ar_render.py` for details.

