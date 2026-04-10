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
    navigation_pkg_share = get_package_share_directory('msauber_navigation')

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
    nav_start_delay = LaunchConfiguration('nav_start_delay')
    params_file = LaunchConfiguration('params_file')
    nav_map = LaunchConfiguration('nav_map')
    use_nav2 = LaunchConfiguration('use_nav2')

    declare_world = DeclareLaunchArgument(
        'world',
        default_value='pista'
    )

    declare_ros_namespace = DeclareLaunchArgument(
        'ros_namespace',
        default_value='msauber'
    )

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true'
    )

    declare_use_nav2 = DeclareLaunchArgument(
        'use_nav2',
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

    declare_nav_start_delay = DeclareLaunchArgument(
        'nav_start_delay',
        default_value='30.0',
        description='Delay (s) before launching navigation after the rest of the stack is up'
    )

    declare_params_file = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(navigation_pkg_share, 'config', 'nav2_dubin_params.yaml'),
        description='Params file for nav'
    )
    declare_nav_map = DeclareLaunchArgument(
        'nav_map',
        default_value=os.path.join(navigation_pkg_share, 'maps', 'test_map.yaml'),
        description='Map file used by Nav2 when launched via bringup'
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
            # Keep controller namespace aligned with ros_namespace so topic/tf paths match odom_tf_bridge expectations
            'namespace': ros_namespace,
        }.items()
    )

    spawn_poses = {
        'my_empty': {'x': '0.0', 'y': '0.0', 'z': '0.3', 'yaw': '0.0'},
        'sonoma': {'x': '280.0', 'y': '-135.0', 'z': '10', 'yaw': '-0.78'},
        'cone_empty': {'x': '0', 'y': '0.0', 'z': '10', 'yaw': '0.0'},
        'pista': {'x': '0.0', 'y': '0.0', 'z': '0.3', 'yaw': '0.0'},
    }

    xacro_file = PathJoinSubstitution([
        FindPackageShare('msauber_description'),
        'urdf',
        'msauber.xacro'
    ])

    controllers_file = os.path.join(control_pkg_share, 'config', 'ackerman_config.yaml')

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

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(navigation_pkg_share, 'launch', 'nav.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'params_file' : params_file,
            'map': nav_map,
        }.items()
    )

    delayed_navigation = TimerAction(
        period=nav_start_delay,
        actions=[navigation_launch],
        condition=IfCondition(use_nav2),
    )

    actions = [
        SetEnvironmentVariable('ROS_NAMESPACE', ''),
        # Gazebo GUI is unstable on some Wayland setups; prefer X11 backend when available.
        SetEnvironmentVariable('QT_QPA_PLATFORM', 'xcb'),
        declare_world,
        declare_ros_namespace,
        declare_use_sim_time,
        declare_use_nav2,
        declare_enable_sensors,
        declare_use_foxglove,
        declare_use_twist_bridge,
        declare_use_yolo,
        declare_gz_start_delay,
        declare_spawn_delay,
        declare_spawner_delay,
        declare_nav_start_delay,
        declare_params_file,
        declare_nav_map,
        sim_launch,
        delayed_robot_stack,
        delayed_spawn_and_control,
        delayed_foxglove,
        delayed_twist_bridge,
        delayed_navigation

    ]
    
    return LaunchDescription(actions)
