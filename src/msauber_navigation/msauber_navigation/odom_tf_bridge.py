import rclpy
from rclpy.node import Node
from tf2_msgs.msg import TFMessage
import tf2_ros


class TFBridge(Node):

    def __init__(self):
        super().__init__('tf_bridge')

        self.br = tf2_ros.TransformBroadcaster(self)

        self.sub = self.create_subscription(
            TFMessage,
            '/msauber/ackermann_steering_controller/tf_odometry',
            self.callback,
            10
        )

    def callback(self, msg):
        for transform in msg.transforms:
            transform.header.stamp = self.get_clock().now().to_msg()
            self.br.sendTransform(transform)


def main():
    rclpy.init()
    node = TFBridge()
    rclpy.spin(node)
    rclpy.shutdown()
