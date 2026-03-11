from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    controller_manager_name = LaunchConfiguration('controller_manager_name')
    controllers_file = LaunchConfiguration('controllers_file')
    spawner_delay = LaunchConfiguration('spawner_delay')

    declare_controller_manager_name = DeclareLaunchArgument(
        'controller_manager_name',
        default_value='/controller_manager',
        description='Name of the controller manager node'
    )

    declare_controllers_file = DeclareLaunchArgument(
        'controllers_file',
        default_value=PathJoinSubstitution([
            FindPackageShare('msauber_control'),
            'config',
            'controllers.yaml'
        ]),
        description='Path to the controllers yaml file'
    )

    declare_spawner_delay = DeclareLaunchArgument(
        'spawner_delay',
        default_value='2.0',
        description='Delay before spawning controllers'
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', controller_manager_name,
            '--param-file', controllers_file,
        ],
        output='screen',
    )

    ackermann_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'ackermann_steering_controller',
            '--controller-manager', controller_manager_name,
            '--param-file', controllers_file,
        ],
        output='screen',
    )

    delayed_spawners = TimerAction(
        period=spawner_delay,
        actions=[
            joint_state_broadcaster_spawner,
            ackermann_controller_spawner,
        ]
    )

    return LaunchDescription([
        declare_controller_manager_name,
        declare_controllers_file,
        declare_spawner_delay,
        delayed_spawners,
    ])