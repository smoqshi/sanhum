from launch import LaunchDescription
from launch_ros.actions import Node
import sys

def generate_launch_description():
    platform = LaunchConfiguration('platform', default='auto')
    return LaunchDescription([
        Node(
            package='sanhum_qt',
            executable='sanhum_qt',
            name='sanhum_gui',
            parameters=[{'platform': platform}],
            output='screen'
        )
    ])
