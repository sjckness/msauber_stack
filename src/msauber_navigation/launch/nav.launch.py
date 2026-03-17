from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time')
    params_file = LaunchConfiguration('params_file')
    map_file = LaunchConfiguration('map')
    
    return LaunchDescription([

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true'
        ),

        DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(
                get_package_share_directory('msauber_navigation'),
                'config',
                'nav2_param.yaml'
            )
        ),

        DeclareLaunchArgument(
            'map',
            default_value=os.path.join(
                get_package_share_directory('msauber_navigation'),
                'maps',
                'test_map.yaml'
            )
        ),

        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[params_file, {'use_sim_time': use_sim_time}],
        ),

        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[{
                'yaml_filename': map_file,
                'use_sim_time': use_sim_time
            }],
        ),

        Node(
            package='nav2_costmap_2d',
            executable='nav2_costmap_2d',
            name='global_costmap',
            output='screen',
            parameters=[params_file, {'use_sim_time': use_sim_time}],
        ),

        Node(
            package='msauber_navigation',
            executable='odom_tf_bridge',
            name='odom_bridge',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time
            }],
        ),

        # Static transform map -> odom so Nav2 has a global frame (replace with localization when available)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='map_to_odom_broadcaster',
            arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        ),

        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'autostart': True,
                'node_names': [
                    'map_server',
                    'planner_server',
                    'global_costmap'
                ]
            }],
        ),

        

    ])
