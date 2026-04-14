from typing import Optional

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import ComputePathToPose
from nav_msgs.msg import Odometry, Path


class GoalPoseToPathNode(Node):
    def __init__(self):
        super().__init__("goal_pose_to_path")

        self.goal_topic = self.declare_parameter("goal_topic", "/goal_pose").value
        self.path_topic = self.declare_parameter("path_topic", "/path").value
        self.odom_topic = self.declare_parameter(
            "odom_topic", "/msauber/ackermann_steering_controller/odometry"
        ).value
        self.global_frame = self.declare_parameter("global_frame", "map").value
        self.planner_action = self.declare_parameter(
            "planner_action", "compute_path_to_pose"
        ).value
        self.planner_id = self.declare_parameter("planner_id", "GridBased").value

        self.latest_odom: Optional[Odometry] = None

        self.create_subscription(Odometry, self.odom_topic, self._odom_callback, 10)
        self.create_subscription(PoseStamped, self.goal_topic, self._goal_callback, 10)
        self.path_pub = self.create_publisher(Path, self.path_topic, 10)
        self.compute_path_client = ActionClient(
            self, ComputePathToPose, self.planner_action
        )

        self.get_logger().info(
            f"Listening for goals on '{self.goal_topic}', odom on '{self.odom_topic}' "
            f"and publishing planned path on '{self.path_topic}'"
        )

    def _odom_callback(self, msg: Odometry):
        self.latest_odom = msg

    def _goal_callback(self, goal_pose: PoseStamped):
        if self.latest_odom is None:
            self.get_logger().warning(
                "Received a goal pose but odometry is not available yet"
            )
            return

        if not self.compute_path_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().warning(
                f"Planner action '{self.planner_action}' is not available yet"
            )
            return

        goal = ComputePathToPose.Goal()
        goal.goal = goal_pose
        goal.goal.header.frame_id = goal.goal.header.frame_id or self.global_frame
        goal.start = self._start_pose_from_odom(self.latest_odom)
        goal.planner_id = self.planner_id
        goal.use_start = True

        future = self.compute_path_client.send_goal_async(goal)
        future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().warning("ComputePathToPose goal was rejected")
            return

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._path_result_callback)

    def _path_result_callback(self, future):
        result = future.result()
        if result is None:
            self.get_logger().warning("No response received from ComputePathToPose")
            return

        path = result.result.path
        if not path.poses:
            self.get_logger().warning("Planner returned an empty path")
            return

        self.path_pub.publish(path)
        self.get_logger().info(
            f"Published planned path with {len(path.poses)} poses on '{self.path_topic}'"
        )

    def _start_pose_from_odom(self, odom: Odometry) -> PoseStamped:
        start = PoseStamped()
        start.header = odom.header
        start.pose = odom.pose.pose

        if not start.header.frame_id:
            start.header.frame_id = "odom"

        return start


def main():
    rclpy.init()
    node = GoalPoseToPathNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
