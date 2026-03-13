from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    image_topic = LaunchConfiguration('image_topic')
    image_reliability = LaunchConfiguration('image_reliability')
    model_name = LaunchConfiguration('model')
    yolo_launch = PathJoinSubstitution([
        FindPackageShare('yolo_bringup'),
        'launch',
        'yolo.launch.py'
    ])

    return LaunchDescription([
        DeclareLaunchArgument(
            'image_topic',
            default_value='/front_camera/image'
        ),

        DeclareLaunchArgument(
            'image_reliability',
            default_value='2',  # Best Effort matches most camera drivers
        ),

        DeclareLaunchArgument(
            'model',
            default_value='yolov8m.pt',  # auto-download from ultralytics if missing
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(yolo_launch),
            launch_arguments={
                'image_topic': image_topic,
                'image_reliability': image_reliability,
                'model': model_name,
                'device': 'cpu',
                'threshold': '0.15',
                'use_tracking': 'True',
                'use_debug': 'True',
                'use_3d': 'False',
            }.items()
        )
    ])
