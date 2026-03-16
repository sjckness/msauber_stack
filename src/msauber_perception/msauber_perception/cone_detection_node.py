import os

from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image, CameraInfo
from visualization_msgs.msg import Marker
from visualization_msgs.msg import MarkerArray

from cv_bridge import CvBridge

from ultralytics import YOLO

import numpy as np


class ConePerceptionNode(Node):

    def __init__(self):

        super().__init__("cone_perception_node")

        self.bridge = CvBridge()

        # Locate the model inside the installed package to avoid cwd issues
        pkg_share = get_package_share_directory("msauber_perception")
        model_path = os.path.join(pkg_share, "models", "cones_v1.pt")

        if not os.path.exists(model_path):
            # Fail fast with a clear log message if the model is missing
            self.get_logger().error(f"Model file not found: {model_path}")
            raise FileNotFoundError(model_path)

        self.model = YOLO(model_path)
        # Only publish markers for these YOLO class names
        self.allowed_classes = {
            "blue_cone",
            "large_orange_cone",
            "orange_cone",
            "unknown_cone",
            "yellow_cone",
        }

        self.depth = None
        # Optional prefix (e.g. "sauber_") to match URDF link names
        # Default prefix matches the URDF links (e.g. "sauber_front_depth_link")
        self.frame_prefix = self.declare_parameter("frame_prefix", "sauber_").value
        # Optional explicit frame override if TF uses a different name
        self.depth_frame_id_override = self.declare_parameter(
            "depth_frame_id", ""
        ).value

        self.create_subscription(
            Image,
            "/front_camera/image",
            self.image_callback,
            10
        )

        self.create_subscription(
            Image,
            "/front_depth/image",
            self.depth_callback,
            10
        )

        # depth camera intrinsics (fallback defaults until CameraInfo arrives)
        self.depth_fx = 525.0
        self.depth_fy = 525.0
        self.depth_cx = 320.0
        self.depth_cy = 240.0
        # Default frame id tries to match URDF naming with prefix if provided
        self.depth_frame_id = (
            self.depth_frame_id_override
            if self.depth_frame_id_override
            else f"{self.frame_prefix}front_depth_link"
        )
        self.have_depth_info = False

        self.create_subscription(
            CameraInfo,
            "/front_depth/camera_info",
            self.depth_info_callback,
            10
        )

        self.marker_pub = self.create_publisher(
            MarkerArray,
            "/perception/cones_markers",
            10
        )

    def depth_callback(self, msg):

        self.depth = self.bridge.imgmsg_to_cv2(msg, "32FC1")

    def depth_info_callback(self, msg: CameraInfo):
        self.depth_fx = msg.k[0]
        self.depth_fy = msg.k[4]
        self.depth_cx = msg.k[2]
        self.depth_cy = msg.k[5]

        frame_from_msg = msg.header.frame_id

        if self.depth_frame_id_override:
            self.depth_frame_id = self.depth_frame_id_override
        elif frame_from_msg:
            # strip leading slash to avoid double-prefixing
            if frame_from_msg.startswith("/"):
                frame_from_msg = frame_from_msg[1:]
            if self.frame_prefix and not frame_from_msg.startswith(self.frame_prefix):
                frame_from_msg = f"{self.frame_prefix}{frame_from_msg}"
            self.depth_frame_id = frame_from_msg

        #if not self.have_depth_info:
            #self.get_logger().info(
            #    f"Depth intrinsics set fx={self.depth_fx:.1f} fy={self.depth_fy:.1f} "
            #    f"cx={self.depth_cx:.1f} cy={self.depth_cy:.1f} frame={self.depth_frame_id}"
            #)
        self.have_depth_info = True


    def image_callback(self, msg):

        # depth and rgb may not arrive perfectly synced; skip until we have depth
        if self.depth is None:
            return

        frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        depth = self.depth  # copy ref locally to avoid races

        frame_h, frame_w = frame.shape[:2]
        depth_h, depth_w = depth.shape[:2]
        scale_x = depth_w / frame_w
        scale_y = depth_h / frame_h

        results = self.model(frame, verbose=False)

        #self.get_logger().info(f"detections: {len(results[0].boxes)}")

        markers = MarkerArray()

        i = 0

        for box in results[0].boxes:

            cls = int(box.cls[0])
            name = self.model.names[cls]

            # Log every detected class
            #self.get_logger().info(f"detected class: {name}")

            if name not in self.allowed_classes:
                continue

            x1, y1, x2, y2 = box.xyxy[0]

            u_rgb = float(x1 + x2) / 2.0
            v_rgb = float(y1 + y2) / 2.0

            # Map bbox center from RGB coords to depth coords if resolutions differ
            if frame_w != depth_w or frame_h != depth_h:
                if not hasattr(self, "_warned_scale"):
                    #self.get_logger().warn(
                    #    f"RGB {frame_w}x{frame_h} vs depth {depth_w}x{depth_h}; scaling bbox center using factors "
                    #    f"{scale_x:.3f} (x) {scale_y:.3f} (y)"
                    #)
                    self._warned_scale = True
                u_depth = int(round(u_rgb * scale_x))
                v_depth = int(round(v_rgb * scale_y))
            else:
                u_depth = int(u_rgb)
                v_depth = int(v_rgb)

            h, w = depth.shape[:2]
            if u_depth < 0 or v_depth < 0 or u_depth >= w or v_depth >= h:
                # Detection center falls outside depth image bounds; skip gracefully
                self.get_logger().warn(
                    f"bbox center ({u_depth},{v_depth}) outside depth bounds {w}x{h}"
                )
                continue

            z = float(depth[v_depth, u_depth])
            #self.get_logger().info(f"depth: {z}")

            # Skip invalid/missing depth values
            if not np.isfinite(z) or z <= 0.0:
                self.get_logger().warn(f"invalid depth {z} at ({u_depth},{v_depth}); skipping")
                continue

            # Project using depth pixel coords and depth camera intrinsics (optical frame)
            x_opt = (u_depth - self.depth_cx) * z / self.depth_fx  # right
            y_opt = (v_depth - self.depth_cy) * z / self.depth_fy  # down
            z_opt = z                                              # forward

            # Convert optical frame (x right, y down, z forward) -> camera link (x forward, y left, z up)
            x = z_opt
            y = -x_opt
            z = -y_opt

            marker = Marker()

            marker.header.frame_id = self.depth_frame_id
            marker.header.stamp = self.get_clock().now().to_msg()

            marker.ns = "cones"
            marker.id = i

            marker.type = Marker.CUBE
            marker.action = Marker.ADD

            marker.pose.position.x = x
            marker.pose.position.y = y
            marker.pose.position.z = z

            # Smaller marker size to better fit cones
            marker.scale.x = 0.10
            marker.scale.y = 0.10
            marker.scale.z = 0.15

            marker.color.r = 1.0
            marker.color.g = 0.5
            marker.color.b = 0.0
            marker.color.a = 1.0

            markers.markers.append(marker)

            i += 1

        self.marker_pub.publish(markers)
        #self.get_logger().info(f"publishing {len(markers.markers)} markers")

def main():

    rclpy.init()

    node = ConePerceptionNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()
