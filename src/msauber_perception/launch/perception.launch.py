from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


def generate_launch_description():
    use_detection = LaunchConfiguration('use_detection')

    yolo_bringup = PathJoinSubstitution([
        FindPackageShare('msauber_perception'),
        'launch',
        'yolo_bringup.launch.py'
    ])

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_detection',
            default_value='True',
            description='Start cone_detection_node'
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(yolo_bringup),
        ),

        Node(
            package='msauber_perception',
            executable='cone_detection_node',
            name='cone_detection_node',
            output='screen',
            condition=IfCondition(use_detection),
        ),
    ])
