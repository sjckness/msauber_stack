import os

from ament_index_python.packages import get_package_share_directory, PackageNotFoundError

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def _maybe_include_yolo(context):
    """Include yolo.launch.py only when the yolo_bringup package is present."""
    try:
        yolo_pkg_share = get_package_share_directory('yolo_bringup')
    except PackageNotFoundError:
        from launch.actions import LogInfo
        return [LogInfo(msg=(
            '[yolo_bringup] Package "yolo_bringup" not found – '
            'skipping external YOLO node launch.  '
            'cone_detection_node will still run YOLO internally.'
        ))]

    image_topic = LaunchConfiguration('input_image_topic').perform(context)
    image_reliability = LaunchConfiguration('image_reliability').perform(context)
    model_name = LaunchConfiguration('model').perform(context)

    msauber_perception_share = get_package_share_directory('msauber_perception')
    model_path = os.path.join(msauber_perception_share, 'models', model_name)

    yolo_launch = os.path.join(yolo_pkg_share, 'launch', 'yolo.launch.py')

    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(yolo_launch),
            launch_arguments={
                'input_image_topic': image_topic,
                'image_reliability': image_reliability,
                'model': model_path,
                'device': 'cpu',
                'threshold': '0.15',
                'use_tracking': 'True',
                'use_debug': 'True',
                'use_3d': 'False',
            }.items()
        )
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'input_image_topic',
            default_value='/front_camera/image'
        ),

        DeclareLaunchArgument(
            'image_reliability',
            default_value='2',  # Best Effort matches most camera drivers
        ),

        DeclareLaunchArgument(
            'model',
            default_value='cones_v1.pt',
        ),

        OpaqueFunction(function=_maybe_include_yolo),
    ])
