import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction, OpaqueFunction, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, TextSubstitution, Command
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    description_pkg_share = get_package_share_directory('msauber_description')
    control_pkg_share = get_package_share_directory('msauber_control')
    sim_pkg_share = get_package_share_directory('msauber_sim')
    bringup_pkg_share = get_package_share_directory('msauber_bringup')

    world = LaunchConfiguration('world')
    ros_namespace = LaunchConfiguration('ros_namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    enable_sensors = LaunchConfiguration('enable_sensors')
    use_foxglove = LaunchConfiguration('use_foxglove')
    use_twist_bridge = LaunchConfiguration('use_twist_bridge')
    use_yolo = LaunchConfiguration('use_yolo')
    gz_start_delay = LaunchConfiguration('gz_start_delay')
    spawn_delay = LaunchConfiguration('spawn_delay')
    spawner_delay = LaunchConfiguration('spawner_delay')

    declare_world = DeclareLaunchArgument(
        'world',
        default_value='sonoma'
    )

    declare_ros_namespace = DeclareLaunchArgument(
        'ros_namespace',
        default_value='msauber'
    )

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true'
    )

    declare_enable_sensors = DeclareLaunchArgument(
        'enable_sensors',
        default_value='false'
    )

    declare_use_foxglove = DeclareLaunchArgument(
        'use_foxglove',
        default_value='false'
    )

    declare_use_twist_bridge = DeclareLaunchArgument(
        'use_twist_bridge',
        default_value='true'
    )

    declare_use_yolo = DeclareLaunchArgument(
        'use_yolo',
        default_value='false',
        description='Launch YOLO perception stack'
    )

    declare_gz_start_delay = DeclareLaunchArgument(
        'gz_start_delay',
        default_value='2.0'
    )

    declare_spawn_delay = DeclareLaunchArgument(
        'spawn_delay',
        default_value='3.0'
    )

    declare_spawner_delay = DeclareLaunchArgument(
        'spawner_delay',
        default_value='6.0',
        description='Delay before spawning controllers (forwarded to msauber_control)'
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
            'ros_namespace': ros_namespace,
        }.items()
    )

    controller_manager_name = PathJoinSubstitution([
        TextSubstitution(text='/'),
        ros_namespace,
        'controller_manager'
    ])

    control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(control_pkg_share, 'launch', 'control.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'use_sim': 'true',
            'enable_sensors': enable_sensors,
            'robot_name': 'sauber',
            'start_controller_manager': 'false',
            'controller_manager_name': controller_manager_name,
            'spawner_delay': spawner_delay,
        }.items()
    )

    spawn_poses = {
        'my_empty': {'x': '0.0', 'y': '0.0', 'z': '0.3', 'yaw': '0.0'},
        'sonoma': {'x': '280.0', 'y': '-135.0', 'z': '10', 'yaw': '-0.78'},
        'cone_empty': {'x': '0', 'y': '0.0', 'z': '10', 'yaw': '0.0'},
    }

    xacro_file = PathJoinSubstitution([
        FindPackageShare('msauber_description'),
        'urdf',
        'msauber.xacro'
    ])

    controllers_files = PathJoinSubstitution([
        FindPackageShare('msauber_control'),
        'config',
        'ackerman_config.yaml'
    ])
    controllers_file = '/home/andreas/dev_ws/msauber_stack/src/msauber_control/config/ackerman_config.yaml'

    robot_description_str = Command([
        'xacro ',
        xacro_file,
        ' use_sim:=true',
        ' enable_sensors:=', enable_sensors,
        ' robot_name:=sauber',
        ' pkg_share:=', FindPackageShare('msauber_description'),
        ' control_config:=', controllers_file,
        ' ros_namespace:=', ros_namespace,
    ])

    def make_spawn_entity(context):
        selected_world = world.perform(context)
        pose = spawn_poses.get(selected_world, spawn_poses['my_empty'])

        return [Node(
            package='ros_gz_sim',
            executable='create',
            output='screen',
            arguments=[
                '-string', robot_description_str,
                '-x', pose['x'],
                '-y', pose['y'],
                '-z', pose['z'],
                '-R', '0.0',
                '-P', '0.0',
                '-Y', pose['yaw'],
                '-name', 'msauber',
            ],
        )]

    spawn_entity = OpaqueFunction(function=make_spawn_entity)

    perception_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('msauber_perception'),
                'launch',
                'perception.launch.py'
            )
        ),
        condition=IfCondition(use_yolo),
    )

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
        package='msauber_control',
        executable='teleop_bridge',
        name='teleop_bridge',
        namespace=ros_namespace,
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
            perception_launch,
        ]
    )

    delayed_foxglove = TimerAction(
        period=spawn_delay,
        actions=[foxglove_bridge],
        condition=IfCondition(use_foxglove),
    )

    delayed_twist_bridge = TimerAction(
        period=spawn_delay,
        actions=[twist_bridge],
        condition=IfCondition(use_twist_bridge),
    )

    actions = [
        # Ensure we rely only on the launch-provided namespace to avoid double prefixes
        SetEnvironmentVariable('ROS_NAMESPACE', ''),
        declare_world,
        declare_ros_namespace,
        declare_use_sim_time,
        declare_enable_sensors,
        declare_use_foxglove,
        declare_use_twist_bridge,
        declare_use_yolo,
        declare_gz_start_delay,
        declare_spawn_delay,
        declare_spawner_delay,
        sim_launch,
        delayed_robot_stack,
        delayed_spawn_and_control,
    ]

    actions.append(delayed_foxglove)
    actions.append(delayed_twist_bridge)

    return LaunchDescription(actions)
