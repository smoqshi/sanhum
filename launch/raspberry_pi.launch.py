import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('sanhum'),
        'config',
        'raspberry_pi_config.yaml'
    )

    return LaunchDescription([
        Node(
            package='sanhum',
            executable='sanhum',
            name='sanhum_robot_node',
            parameters=[config],
            output='screen'
        )
    ])
