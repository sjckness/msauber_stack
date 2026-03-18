import rclpy
from rclpy.node import Node
from tf2_msgs.msg import TFMessage
import tf2_ros


class TFBridge(Node):

    def __init__(self):
        super().__init__('tf_bridge')

        # Topic that carries the robot TF (default: controller odom TF)
        tf_topic = self.declare_parameter(
            'input_tf_topic',
            '/msauber/ackermann_steering_controller/tf_odometry'
        ).value

        self.br = tf2_ros.TransformBroadcaster(self)

        self.sub = self.create_subscription(
            TFMessage,
            tf_topic,
            self.callback,
            10
        )

        self.get_logger().info(f"Republishing TF from '{tf_topic}' to '/tf'")

    def callback(self, msg):
        for transform in msg.transforms:
            transform.header.stamp = self.get_clock().now().to_msg()
            self.br.sendTransform(transform)


def main():
    rclpy.init()
    node = TFBridge()
    rclpy.spin(node)
    rclpy.shutdown()
