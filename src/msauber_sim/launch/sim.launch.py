import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
    UnsetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def _clean_ld_library_path():
    ld_library_path = os.environ.get('LD_LIBRARY_PATH', '')
    if not ld_library_path:
        return ''

    filtered_paths = [
        path for path in ld_library_path.split(':')
        if path and '/snap/' not in path
    ]
    return ':'.join(filtered_paths)


def generate_launch_description():
    sim_pkg_share = get_package_share_directory('msauber_sim')
    description_pkg_share = get_package_share_directory('msauber_description')
    ros_gz_sim_pkg_share = get_package_share_directory('ros_gz_sim')

    world = LaunchConfiguration('world')
    declare_world = DeclareLaunchArgument(
        'world',
        default_value='my_empty',
        description='World name without .sdf extension'
    )

    resource_paths = [
        sim_pkg_share,
        os.path.join(sim_pkg_share, 'worlds'),
        os.path.join(sim_pkg_share, 'models'),
        os.path.join(sim_pkg_share, 'meshes'),
        description_pkg_share,
        os.path.join(description_pkg_share, 'meshes'),
    ]

    gz_env = []
    for env_var in ['GZ_SIM_RESOURCE_PATH', 'IGN_GAZEBO_RESOURCE_PATH']:
        for path in resource_paths:
            gz_env.append(
                AppendEnvironmentVariable(
                    name=env_var,
                    value=path,
                    separator=':'
                )
            )

    clean_env_actions = [
        SetEnvironmentVariable(
            name='LD_LIBRARY_PATH',
            value=_clean_ld_library_path()
        ),
    ]

    for env_var in [
        'SNAP',
        'SNAP_ARCH',
        'SNAP_COMMON',
        'SNAP_CONTEXT',
        'SNAP_COOKIE',
        'SNAP_DATA',
        'SNAP_EUID',
        'SNAP_INSTANCE_NAME',
        'SNAP_LAUNCHER_ARCH_TRIPLET',
        'SNAP_LIBRARY_PATH',
        'SNAP_NAME',
        'SNAP_REAL_HOME',
        'SNAP_REVISION',
        'SNAP_UID',
        'SNAP_USER_COMMON',
        'SNAP_USER_DATA',
        'SNAP_VERSION',
        'GDK_PIXBUF_MODULEDIR',
        'GDK_PIXBUF_MODULE_FILE',
        'GIO_MODULE_DIR',
        'GSETTINGS_SCHEMA_DIR',
        'GTK_EXE_PREFIX',
        'GTK_IM_MODULE_FILE',
        'GTK_PATH',
        'XDG_DATA_HOME',
    ]:
        clean_env_actions.append(UnsetEnvironmentVariable(name=env_var))

    def launch_gz_sim(context):
        requested_world = world.perform(context)
        world_filename = requested_world if requested_world.endswith('.sdf') else f'{requested_world}.sdf'

        candidate_worlds = [
            os.path.join(sim_pkg_share, 'worlds', world_filename),
            os.path.join(os.path.dirname(sim_pkg_share), 'src', 'msauber_sim', 'worlds', world_filename),
            os.path.join(os.path.dirname(os.path.dirname(sim_pkg_share)), 'src', 'msauber_sim', 'worlds', world_filename),
        ]

        world_path = next((path for path in candidate_worlds if os.path.isfile(path)), None)
        if world_path is None:
            available_worlds_dir = os.path.join(os.path.dirname(os.path.dirname(sim_pkg_share)), 'src', 'msauber_sim', 'worlds')
            available_worlds = []
            if os.path.isdir(available_worlds_dir):
                available_worlds = sorted(
                    os.path.splitext(name)[0]
                    for name in os.listdir(available_worlds_dir)
                    if name.endswith('.sdf')
                )
            raise FileNotFoundError(
                f"World '{requested_world}' not found. Searched: {candidate_worlds}. "
                f"Available worlds: {available_worlds}"
            )

        return [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        ros_gz_sim_pkg_share,
                        'launch',
                        'gz_sim.launch.py'
                    )
                ),
                launch_arguments={
                    'gz_args': f'{world_path} -v 5 -r'
                }.items()
            )
        ]

    return LaunchDescription([
        *clean_env_actions,
        *gz_env,
        declare_world,
        OpaqueFunction(function=launch_gz_sim),
    ])
