"""
ar_render.py
=============

This module implements a basic augmented‑reality object renderer.  Given a
background photograph, a transparent object image (RGBA) and real‑world
dimensions of the object, the code computes the appropriate size of the
object in pixels and pastes it into the scene at a specified location on
the ground plane. 

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import cv2
import numpy as np


@dataclass
class CameraParams:
    """Simple container for camera and scene geometry.

    All values are in millimetres unless otherwise noted.  Heights are
    measured relative to the ground plane (positive up), and the camera
    looks straight ahead parallel to the ground.

    Parameters
    ----------
    focal_length_mm : float
        Focal length of the camera lens in millimetres.

    sensor_width_mm : float
        Physical width of the imaging sensor.

    sensor_height_mm : float
        Physical height of the imaging sensor.

    camera_height_mm : float
        Height of the camera centre above the ground plane.

    ground_distance_mm : float, optional
        Nominal distance from the camera projection centre to the point
        directly beneath the camera on the ground plane. Changing this value will change how
        quickly objects shrink with distance.  Default is 2000 mm.
    """

    focal_length_mm: float
    sensor_width_mm: float
    sensor_height_mm: float
    camera_height_mm: float
    ground_distance_mm: float = 2000.0


def load_rgba(path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Load an RGBA image and return colour and alpha channels separately.

    Parameters
    ----------
    path : str
        Path to a PNG image with an alpha channel.

    Returns
    -------
    tuple
        A tuple ``(rgb, alpha)`` where ``rgb`` is a BGR image (as
        returned by OpenCV) and ``alpha`` is a single‑channel float array
        in the range [0, 1].
    """
    rgba = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if rgba is None:
        raise FileNotFoundError(f"Could not load image at {path}")
    if rgba.shape[2] != 4:
        raise ValueError("Image must have an alpha channel (RGBA)")
    bgr = rgba[:, :, :3]
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0
    return bgr, alpha


def compute_object_size_px(
    camera: CameraParams,
    bg_height_px: int,
    y_px: int,
    object_height_m: float,
) -> int:
    """Compute the vertical pixel height of an object given its real height.

    This function implements the perspective geometry used in the provided
    notebook.  It converts the real‑world height into an image height
    measured in pixels, based on the camera's intrinsic and extrinsic
    parameters and the object's vertical image coordinate.

    Parameters
    ----------
    camera : CameraParams
        Camera geometry parameters.

    bg_height_px : int
        Height of the background image in pixels.

    y_px : int
        Vertical position of the object base in pixels (measured from the
        top of the image).  Larger values indicate positions lower in the
        image.

    object_height_m : float
        Real‑world height of the object in metres.

    Returns
    -------
    int
        Height of the object in the image in pixels.  A value of zero or
        negative indicates that the object cannot be placed at the given
        position (e.g. above the horizon).
    """
    # Convert real heights to millimetres.
    H_mm = object_height_m * 1000.0
    # Pixels per millimetre on the sensor: background height corresponds
    # to the physical sensor height (sensor_height_mm).
    pixel_per_mm = bg_height_px / camera.sensor_height_mm

    # Compute the vertical coordinate on the sensor in millimetres.  The
    # origin of the sensor coordinate system is at the centre, so convert
    # from image coordinates (origin at top left).
    x_y_mm = (bg_height_px - y_px) / pixel_per_mm

    # Objects above the horizon (sensor height / 2) cannot be placed.
    if x_y_mm > (camera.sensor_height_mm / 2):
        return 0

    # Distance from camera to the point on the ground beneath the object.
    x_r_mm = (
        (camera.focal_length_mm * camera.camera_height_mm)
        / ((camera.sensor_height_mm / 2) - x_y_mm)
        - camera.ground_distance_mm
    )

    # Height of the object's projection on the sensor in millimetres.
    h_mm = (
        (camera.sensor_height_mm / 2)
        - x_y_mm
        - (camera.focal_length_mm * (camera.camera_height_mm - H_mm))
        / (camera.ground_distance_mm + x_r_mm)
    )
    h_px = int(h_mm * pixel_per_mm)
    return h_px


def paste_object(
    background: np.ndarray,
    object_bgr: np.ndarray,
    object_alpha: np.ndarray,
    location: Tuple[int, int],
    object_height_m: float,
    camera: CameraParams,
) -> np.ndarray:
    """Paste a scaled object onto a background image.

    The object is scaled according to its real‑world height and the
    specified location on the ground plane.  The object's base will be
    aligned with the ``location`` pixel, which must lie on the ground plane.

    Parameters
    ----------
    background : ndarray
        Colour background image (BGR) into which the object will be pasted.

    object_bgr : ndarray
        Colour channels of the object image (BGR).

    object_alpha : ndarray
        Alpha channel of the object image in the range [0, 1].

    location : tuple of int
        Coordinates ``(y_px, x_px)`` of the point on the image where the
        bottom centre of the object should be placed.

    object_height_m : float
        Real‑world height of the object in metres.

    camera : CameraParams
        Camera geometry used to compute the projected size of the object.

    Returns
    -------
    ndarray
        New background image with the object rendered onto it.  The
        original background is not modified.
    """
    y_px, x_px = location
    bg_h, bg_w = background.shape[:2]

    # Compute desired object height in pixels.
    target_h = compute_object_size_px(
        camera, bg_h, y_px, object_height_m
    )
    if target_h <= 0:
        raise ValueError(
            "Object cannot be rendered above the horizon or with non‑positive height"
        )

    # Preserve aspect ratio based on original object size.
    orig_h, orig_w = object_bgr.shape[:2]
    aspect = orig_w / orig_h
    target_w = int(aspect * target_h)

    # Resize the object and alpha mask.
    resized_bgr = cv2.resize(object_bgr, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
    resized_alpha = cv2.resize(object_alpha, (target_w, target_h), interpolation=cv2.INTER_LINEAR)

    # Determine the region of interest on the background.
    top = y_px - target_h
    bottom = y_px
    left = int(x_px - target_w // 2)
    right = left + target_w

    # Check boundaries.
    if top < 0 or bottom > bg_h or left < 0 or right > bg_w:
        raise ValueError("The object would extend beyond the background boundaries")

    # Copy the background and extract ROI.
    result = background.copy()
    roi = result[top:bottom, left:right]

    # Blend object onto ROI using alpha mask.
    alpha_3ch = np.dstack([resized_alpha] * 3)
    blended = (
        resized_bgr.astype(np.float32) * alpha_3ch
        + roi.astype(np.float32) * (1.0 - alpha_3ch)
    ).astype(np.uint8)

    result[top:bottom, left:right] = blended
    return result
