import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, AppendEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, TextSubstitution, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    sim_pkg_share = get_package_share_directory('msauber_sim')
    description_pkg_share = get_package_share_directory('msauber_description')

    world = LaunchConfiguration('world')

    declare_world = DeclareLaunchArgument(
        'world',
        default_value='my_empty',
        description='World name without .sdf extension'
    )

    gz_env = [
        AppendEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=sim_pkg_share,
            separator=':'
        ),
        AppendEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=os.path.join(sim_pkg_share, 'worlds'),
            separator=':'
        ),
        AppendEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=os.path.join(sim_pkg_share, 'models'),
            separator=':'
        ),
        AppendEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=os.path.join(sim_pkg_share, 'meshes'),
            separator=':'
        ),
        AppendEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=description_pkg_share,
            separator=':'
        ),
        AppendEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=os.path.join(description_pkg_share, 'meshes'),
            separator=':'
        ),
    ]

    world_file = PathJoinSubstitution([
        FindPackageShare('msauber_sim'),
        'worlds',
        world
    ])

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                FindPackageShare('ros_gz_sim').find('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            )
        ),
        launch_arguments={
            'gz_args': [
                world_file,
                TextSubstitution(text='.sdf'),
                TextSubstitution(text=' -v 4 -r')
            ]
        }.items()
    )

    return LaunchDescription([
        *gz_env,
        declare_world,
        gz_sim,
    ])