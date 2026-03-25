from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, TimerAction
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time')
    params_file = LaunchConfiguration('params_file')
    map_file = LaunchConfiguration('map')
    
    

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true'
    )

    declare_param_file = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(
            get_package_share_directory('msauber_navigation'),
            'config',
            'nav2_dubin_params.yaml'
        ),
    )
    
    declare_map = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(
            get_package_share_directory('msauber_navigation'),
            'maps',
            'test_map.yaml'
        )
    )

    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'yaml_filename': map_file,
            'use_sim_time': use_sim_time
        }],
    )

    planner_server_node = TimerAction(
        period=3.5,
        actions=[
            Node(
                package='nav2_planner',
                executable='planner_server',
                name='planner_server',
                output='screen',
                parameters=[params_file, {'use_sim_time': use_sim_time}],
            )
        ]
    )

    odom_bridge_node = Node(
        package='msauber_navigation',
        executable='odom_tf_bridge',
        name='odom_bridge',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'input_tf_topic': '/msauber/ackermann_steering_controller/tf_odometry',
        }],
    )

    map_to_odom_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='map_to_odom_broadcaster',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    lifeclycle_manager_node = TimerAction(
        period=6.0,
        actions=[
            Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_navigation',
                output='screen',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'bond_timeout': 5.0,
                    'autostart': True,
                    'node_names': [
                        'map_server',
                        'planner_server'
                    ]
                }],
            )
        ]
    )

    mpc_node = Node(
        package='msauber_navigation',
        executable='mpc_node',
        name='mpc_node',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'odom_topic': '/msauber/ackermann_steering_controller/odom',
            'path_topic': '/path',
            'cmd_vel_topic': '/msauber/ackermann_steering_controller/reference',
        }],
    )

    return LaunchDescription([    
        declare_use_sim_time,
        declare_param_file,
        declare_map,
        odom_bridge_node,
        map_to_odom_tf,
        map_server_node,
        planner_server_node,
        lifeclycle_manager_node,
        mpc_node,
    ])
