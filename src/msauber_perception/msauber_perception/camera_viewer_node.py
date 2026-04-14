"""
camera_viewer_node.py
~~~~~~~~~~~~~~~~~~~~~
Scrollable camera / YOLO-detection viewer.

Subscribes to:
  /front_camera/image          – raw RGB camera
  /perception/annotated_image  – YOLO-annotated image (published by
                                  cone_detection_node when use_yolo is True)

Opens a single OpenCV window with two rows:
  • Top row   : raw camera feed
  • Bottom row: YOLO annotated feed (grey placeholder when unavailable)

The window is resizable and fully scrollable through the standard OpenCV
trackbar + mouse-wheel (on supported backends).  Press  Q  or  ESC  to close.
"""

import threading

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from sensor_msgs.msg import Image


# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
PANEL_W = 640          # width of each panel tile (pixels)
PANEL_H = 360          # height of each panel tile
GAP = 6                # vertical gap between rows (pixels)
LABEL_H = 28           # height of the label bar above each panel
BORDER = 3             # border thickness
BG_COLOR = (30, 30, 35)
BORDER_COLOR_ACTIVE = (80, 200, 80)
BORDER_COLOR_IDLE = (80, 80, 90)
TEXT_COLOR = (220, 220, 220)
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.55
FONT_THICK = 1

# Total canvas height (two panels + labels + gaps)
CANVAS_H = (LABEL_H + PANEL_H) * 2 + GAP + BORDER * 4
CANVAS_W = PANEL_W + BORDER * 2

WINDOW_H = min(CANVAS_H, 900)   # initial window height – user can resize


def _placeholder(text: str, active: bool = False) -> np.ndarray:
    """Return a dark placeholder tile with centered text."""
    tile = np.full((PANEL_H, PANEL_W, 3), 40, dtype=np.uint8)
    color = (120, 120, 120) if not active else (60, 160, 60)
    (tw, th), _ = cv2.getTextSize(text, FONT, FONT_SCALE, FONT_THICK)
    x = (PANEL_W - tw) // 2
    y = (PANEL_H + th) // 2
    cv2.putText(tile, text, (x, y), FONT, FONT_SCALE, color, FONT_THICK)
    return tile


def _label_bar(text: str, active: bool) -> np.ndarray:
    """Return a label bar with the panel title."""
    bar = np.full((LABEL_H, PANEL_W, 3), BG_COLOR, dtype=np.uint8)
    dot_color = BORDER_COLOR_ACTIVE if active else BORDER_COLOR_IDLE
    cv2.circle(bar, (12, LABEL_H // 2), 5, dot_color, -1)
    cv2.putText(bar, text, (24, LABEL_H - 7), FONT, FONT_SCALE,
                TEXT_COLOR, FONT_THICK)
    return bar


def _resize(frame: np.ndarray) -> np.ndarray:
    """Resize frame to PANEL_W x PANEL_H keeping aspect ratio, pad with black."""
    if frame is None:
        return _placeholder("no data")
    h, w = frame.shape[:2]
    scale = min(PANEL_W / w, PANEL_H / h)
    nw, nh = int(w * scale), int(h * scale)
    resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((PANEL_H, PANEL_W, 3), dtype=np.uint8)
    y0 = (PANEL_H - nh) // 2
    x0 = (PANEL_W - nw) // 2
    canvas[y0:y0 + nh, x0:x0 + nw] = resized
    return canvas


class CameraViewerNode(Node):

    def __init__(self):
        super().__init__("camera_viewer_node")

        self.bridge = CvBridge()
        self._lock = threading.Lock()
        self._raw_frame: np.ndarray | None = None
        self._ann_frame: np.ndarray | None = None

        # Scroll offset (pixels from the top of the virtual canvas)
        self._scroll_y = 0
        self._scroll_max = max(0, CANVAS_H - WINDOW_H)

        best_effort = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=1,
        )

        self.create_subscription(
            Image, "/front_camera/image",
            self._cb_raw, best_effort)

        self.create_subscription(
            Image, "/perception/annotated_image",
            self._cb_ann, best_effort)

        self.get_logger().info(
            "CameraViewerNode started.  "
            "Topics: /front_camera/image  /perception/annotated_image"
        )

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------
    def _cb_raw(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as exc:
            self.get_logger().warn(f"raw decode error: {exc}")
            return
        with self._lock:
            self._raw_frame = frame

    def _cb_ann(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as exc:
            self.get_logger().warn(f"annotated decode error: {exc}")
            return
        with self._lock:
            self._ann_frame = frame

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _build_canvas(self) -> np.ndarray:
        with self._lock:
            raw = self._raw_frame.copy() if self._raw_frame is not None else None
            ann = self._ann_frame.copy() if self._ann_frame is not None else None

        canvas = np.full((CANVAS_H, CANVAS_W, 3), BG_COLOR, dtype=np.uint8)

        y = 0
        for title, frame, active in [
            ("Front Camera  [/front_camera/image]", raw, raw is not None),
            ("YOLO Detections  [/perception/annotated_image]", ann, ann is not None),
        ]:
            label = _label_bar(title, active)
            tile = _resize(frame) if active else _placeholder(
                "waiting for topic..." if raw is None else "YOLO not running  (use_yolo:=true)",
                False,
            )

            # border
            bc = BORDER_COLOR_ACTIVE if active else BORDER_COLOR_IDLE
            cv2.rectangle(canvas,
                          (0, y),
                          (CANVAS_W - 1, y + LABEL_H + PANEL_H + BORDER * 2 - 1),
                          bc, BORDER)

            canvas[y + BORDER: y + BORDER + LABEL_H,
                   BORDER: BORDER + PANEL_W] = label
            canvas[y + BORDER + LABEL_H: y + BORDER + LABEL_H + PANEL_H,
                   BORDER: BORDER + PANEL_W] = tile

            y += LABEL_H + PANEL_H + BORDER * 2 + GAP

        return canvas

    def _scroll(self, delta: int):
        self._scroll_y = max(0, min(self._scroll_max, self._scroll_y + delta))
        self._update_trackbar()

    def _update_trackbar(self):
        if self._scroll_max > 0:
            cv2.setTrackbarPos("scroll", "msauber camera viewer", self._scroll_y)

    # ------------------------------------------------------------------
    # Main loop (called from main thread)
    # ------------------------------------------------------------------
    def spin_viewer(self):
        win = "msauber camera viewer"
        cv2.namedWindow(win, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win, CANVAS_W, WINDOW_H)

        if self._scroll_max > 0:
            cv2.createTrackbar(
                "scroll", win, 0, self._scroll_max,
                lambda v: setattr(self, "_scroll_y", v),
            )

        def _on_mouse(event, _x, y_pos, flags, _param):  # noqa: N803
            if event == cv2.EVENT_MOUSEWHEEL:
                # positive flags → scroll up, negative → scroll down
                self._scroll(
                    -int(PANEL_H * 0.15) if flags > 0 else int(PANEL_H * 0.15)
                )

        cv2.setMouseCallback(win, _on_mouse)

        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.03)

            canvas = self._build_canvas()
            view = canvas[self._scroll_y: self._scroll_y + WINDOW_H]

            # If window was resized by the user, adapt the viewport
            try:
                rect = cv2.getWindowImageRect(win)
                actual_h = rect[3] if rect[3] > 0 else WINDOW_H
                self._scroll_max = max(0, CANVAS_H - actual_h)
                view = canvas[self._scroll_y: self._scroll_y + actual_h]
            except Exception:
                pass

            cv2.imshow(win, view)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):
                break
            elif key == 82:   # up-arrow
                self._scroll(-30)
            elif key == 84:   # down-arrow
                self._scroll(30)

        cv2.destroyAllWindows()


def main():
    rclpy.init()
    node = CameraViewerNode()
    try:
        node.spin_viewer()
    finally:
        node.destroy_node()
        rclpy.shutdown()
