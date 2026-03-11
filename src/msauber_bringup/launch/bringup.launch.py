import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    description_pkg_share = get_package_share_directory('msauber_description')
    control_pkg_share = get_package_share_directory('msauber_control')
    sim_pkg_share = get_package_share_directory('msauber_sim')
    bringup_pkg_share = get_package_share_directory('msauber_bringup')

    world = LaunchConfiguration('world')
    use_sim_time = LaunchConfiguration('use_sim_time')
    enable_sensors = LaunchConfiguration('enable_sensors')
    use_foxglove = LaunchConfiguration('use_foxglove')
    use_twist_bridge = LaunchConfiguration('use_twist_bridge')
    gz_start_delay = LaunchConfiguration('gz_start_delay')
    spawn_delay = LaunchConfiguration('spawn_delay')

    declare_world = DeclareLaunchArgument(
        'world',
        default_value='my_empty'
    )

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true'
    )

    declare_enable_sensors = DeclareLaunchArgument(
        'enable_sensors',
        default_value='true'
    )

    declare_use_foxglove = DeclareLaunchArgument(
        'use_foxglove',
        default_value='false'
    )

    declare_use_twist_bridge = DeclareLaunchArgument(
        'use_twist_bridge',
        default_value='false'
    )

    declare_gz_start_delay = DeclareLaunchArgument(
        'gz_start_delay',
        default_value='2.0'
    )

    declare_spawn_delay = DeclareLaunchArgument(
        'spawn_delay',
        default_value='1.0'
    )

    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(sim_pkg_share, 'launch', 'sim.launch.py')
        ),
        launch_arguments={
            'world': world,
        }.items()
    )

    description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(description_pkg_share, 'launch', 'description.launch.py')
        ),
        launch_arguments={
            'use_sim': 'true',
            'use_sim_time': use_sim_time,
            'enable_sensors': enable_sensors,
            'use_joint_state_publisher_gui': 'false',
            'use_rviz': 'false',
            'robot_name': 'sauber',
        }.items()
    )

    control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(control_pkg_share, 'launch', 'control.launch.py')
        )
    )

    spawn_poses = {
        'my_empty': {'x': '0.0', 'y': '0.0', 'z': '0.3', 'yaw': '0.0'},
        'sonoma': {'x': '280.0', 'y': '-135.0', 'z': '0.3', 'yaw': '-0.78'},
    }

    def make_spawn_entity(context):
        selected_world = world.perform(context)
        pose = spawn_poses.get(selected_world, spawn_poses['my_empty'])

        return [Node(
            package='ros_gz_sim',
            executable='create',
            output='screen',
            arguments=[
                '-topic', '/robot_description',
                '-x', pose['x'],
                '-y', pose['y'],
                '-z', pose['z'],
                '-R', '0.0',
                '-P', '0.0',
                '-Y', pose['yaw'],
                '-name', 'msauber',
                '-allow_renaming', 'false'
            ],
        )]

    spawn_entity = OpaqueFunction(function=make_spawn_entity)

    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/front_camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/front_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/front_depth/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/front_depth/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
        ],
        output='screen'
    )

    foxglove_bridge = Node(
        package='foxglove_bridge',
        executable='foxglove_bridge',
        name='foxglove_bridge',
        output='screen',
        parameters=[{
            'port': 8765,
            'address': '0.0.0.0',
            'use_compression': False
        }]
    )

    twist_bridge = Node(
        package='msauber',
        executable='teleop_twist_bridge',
        name='teleop_twist_bridge',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    delayed_robot_stack = TimerAction(
        period=gz_start_delay,
        actions=[
            description_launch,
        ]
    )

    delayed_spawn_and_control = TimerAction(
        period=spawn_delay,
        actions=[
            spawn_entity,
            control_launch,
            gz_bridge,
        ]
    )

    delayed_foxglove = TimerAction(
        period=spawn_delay,
        actions=[foxglove_bridge]
    )

    delayed_twist_bridge = TimerAction(
        period=spawn_delay,
        actions=[twist_bridge]
    )

    actions = [
        declare_world,
        declare_use_sim_time,
        declare_enable_sensors,
        declare_use_foxglove,
        declare_use_twist_bridge,
        declare_gz_start_delay,
        declare_spawn_delay,
        sim_launch,
        delayed_robot_stack,
        delayed_spawn_and_control,
    ]

    if True:
        from launch.conditions import IfCondition
        foxglove_bridge.condition = IfCondition(use_foxglove)
        twist_bridge.condition = IfCondition(use_twist_bridge)
        actions.append(delayed_foxglove)
        actions.append(delayed_twist_bridge)

    return LaunchDescription(actions)