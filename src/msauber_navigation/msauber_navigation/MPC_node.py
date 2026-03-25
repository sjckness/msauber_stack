import math
from typing import Optional

import numpy as np
from tf_transformations import euler_from_quaternion

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry, Path

from msauber_navigation.MPC import MPCController


class MPCNode(Node):
    def __init__(self):
        super().__init__("mpc_node")

        # Parameters allow overriding topics and controller tuning.
        odom_topic = self.declare_parameter(
            "odom_topic", "/msauber/ackermann_steering_controller/odometry"
        ).value
        path_topic = self.declare_parameter("path_topic", "/plan").value
        cmd_vel_topic = self.declare_parameter("cmd_vel_topic", "/cmd_vel").value

        self.Ts = float(self.declare_parameter("Ts", 0.05).value)
        N = int(self.declare_parameter("N", 10).value)
        self.v_ref = float(self.declare_parameter("v_ref", 1.0).value)

        self.params = {"L": 0.33, "lr": 0.17}
        self.limits = {
            "deltaMin": -1.0,
            "deltaMax": 1.0,
            "aMin": -2.0,
            "aMax": 2.0,
            "dDeltaMin": -2.5,
            "dDeltaMax": 2.5,
            "dAMin": -4.0,
            "dAMax": 4.0,
            "vMin": 0.0,
            "vMax": 3.0,
        }
        self.weights = {
            "w_pos": 40.0,
            "w_psi": 8.0,
            "w_v": 4.0,
            "w_u": [0.01, 0.01],
            "w_du": [0.20, 0.10],
            "w_goal": 80.0,
        }

        self.mpc = MPCController(
            params=self.params,
            limits=self.limits,
            weights=self.weights,
            N=N,
            Ts=self.Ts,
        )

        # State and buffers
        self.state: Optional[np.ndarray] = None  # [x, y, yaw, v]
        self.last_u = np.zeros(2)  # [delta, a]
        self.path: Optional[np.ndarray] = None  # [[x, y, yaw], ...]

        # Subscriptions
        self.create_subscription(
            Odometry,
            odom_topic, 
            self._odom_callback, 
            qos_profile_sensor_data
        )
        self.create_subscription(
            Path, 
            path_topic, 
            self._path_callback,
            10)

        # Publisher
        self.cmd_pub = self.create_publisher(
            Twist,
            cmd_vel_topic, 
            10)

        # Main loop
        self.create_timer(self.Ts, self.control_loop)

        self.get_logger().info(
            f"Listening to odom '{odom_topic}', path '{path_topic}' "
            f"and publishing cmd_vel on '{cmd_vel_topic}'"
        )

    # ---------- Callbacks ----------
    def _odom_callback(self, msg: Odometry):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        _, _, yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])
        v = msg.twist.twist.linear.x
        self.state = np.array([p.x, p.y, yaw, v], dtype=float)

    def _path_callback(self, msg: Path):
        if not msg.poses:
            self.path = None
            return
        self.path = self._path_to_array(msg)

    # ---------- Helpers ----------
    @staticmethod
    def _path_to_array(msg: Path) -> np.ndarray:
        path = []
        for pose_stamped in msg.poses:
            p = pose_stamped.pose.position
            q = pose_stamped.pose.orientation
            _, _, yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])
            path.append([p.x, p.y, yaw])
        return np.array(path, dtype=float)

    def _nearest_index(self, x: float, y: float) -> int:
        d = (self.path[:, 0] - x) ** 2 + (self.path[:, 1] - y) ** 2
        return int(np.argmin(d))

    def _build_reference(self, idx: int, N: int, v_ref: float) -> np.ndarray:
        ref = []
        for k in range(N):
            i = min(idx + k, len(self.path) - 1)
            x_ref, y_ref, yaw_ref = self.path[i]
            ref.append([x_ref, y_ref, yaw_ref, v_ref])
        return np.array(ref, dtype=float)

    def _publish_cmd(self, u: np.ndarray):
        delta, a = u

        # propagate velocity one step for the published command
        v_curr = self.state[3]
        v_next = v_curr + a * self.Ts
        omega = v_next / self.params["L"] * math.tan(delta)

        msg = Twist()
        msg.linear.x = float(v_next)
        msg.angular.z = float(omega)
        self.cmd_pub.publish(msg)

        # keep internal velocity consistent until next odom arrives
        self.state[3] = v_next

    # ---------- Control loop ----------
    def control_loop(self):
        if self.state is None or self.path is None:
            return

        idx = self._nearest_index(self.state[0], self.state[1])
        refH = self._build_reference(idx, self.mpc.N, self.v_ref)

        u = self.mpc.solve(x0=self.state, last_u=self.last_u, refH=refH)
        self.last_u = u

        self._publish_cmd(u)


def main():
    rclpy.init()
    node = MPCNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
