import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_name = 'msauber_description'
    pkg_share = get_package_share_directory(pkg_name)
    control_pkg_share = get_package_share_directory('msauber_control')
    controllers_file = os.path.join(control_pkg_share, 'config', 'ackerman_config.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time')
    use_sim = LaunchConfiguration('use_sim')
    enable_sensors = LaunchConfiguration('enable_sensors')
    use_joint_state_publisher_gui = LaunchConfiguration('use_joint_state_publisher_gui')
    use_rviz = LaunchConfiguration('use_rviz')
    robot_name = LaunchConfiguration('robot_name')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true'
    )

    declare_use_sim = DeclareLaunchArgument(
        'use_sim',
        default_value='false',
        description='Generate robot for simulation'
    )

    declare_enable_sensors = DeclareLaunchArgument(
        'enable_sensors',
        default_value='true',
        description='Enable sensors in xacro'
    )

    declare_use_joint_state_publisher_gui = DeclareLaunchArgument(
        'use_joint_state_publisher_gui',
        default_value='true',
        description='Launch joint_state_publisher_gui'
    )

    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Launch RViz'
    )

    declare_robot_name = DeclareLaunchArgument(
        'robot_name',
        default_value='sauber',
        description='Robot name passed to xacro'
    )

    xacro_file = PathJoinSubstitution([
        FindPackageShare(pkg_name),
        'urdf',
        'msauber.xacro'
    ])

    rviz_config = PathJoinSubstitution([
        FindPackageShare(pkg_name),
        'rviz',
        'description.rviz'
    ])

    robot_description_content = Command([
        'xacro ',
        xacro_file,
        ' use_sim:=', use_sim,
        ' enable_sensors:=', enable_sensors,
        ' robot_name:=', robot_name,
        ' pkg_share:=', pkg_share,
        ' control_config:=', controllers_file
    ])

    robot_description = {
        'robot_description': ParameterValue(
            robot_description_content,
            value_type=str
        )
    }

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[
            robot_description,
            {'use_sim_time': use_sim_time}
        ]
    )

    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        condition=IfCondition(use_joint_state_publisher_gui),
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        condition=IfCondition(use_rviz),
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_use_sim,
        declare_enable_sensors,
        declare_use_joint_state_publisher_gui,
        declare_use_rviz,
        declare_robot_name,
        joint_state_publisher_gui,
        robot_state_publisher,
        rviz2,
    ])