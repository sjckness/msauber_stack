from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    yolo_bringup = PathJoinSubstitution([
        FindPackageShare('msauber_perception'),
        'launch',
        'yolo_bringup.launch.py'
    ])

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(yolo_bringup)
        )
    ])