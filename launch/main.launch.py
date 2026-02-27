from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='sanhum',
            executable='sanhum_gui',
            name='sanhum_gui',
            output='screen'
        )
    ])
