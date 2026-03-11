from setuptools import find_packages, setup
from glob import glob

package_name = 'msauber_sim'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Launch files
        (f'share/{package_name}/launch', glob('launch/*.py')),

        # meshes
        (f'share/{package_name}/meshes/', glob('meshes/*')),

        # models
        (f'share/{package_name}/models/', glob('models/*')),
        
        # Config files (YAML)
        (f'share/{package_name}/config', glob('config/*.yaml')),

        # Config files (YAML)
        (f'share/{package_name}/worlds', glob('worlds/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='andreas',
    maintainer_email='andreas21steffens@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
