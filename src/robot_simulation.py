#!/usr/bin/env python3
"""
Sanhum Robot 3D Simulation
Low-poly robot model with tank tracks and manipulator
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Tuple, List
import time

@dataclass
class Vector3:
    x: float
    y: float
    z: float
    
    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self):
        mag = self.magnitude()
        if mag > 0:
            return Vector3(self.x/mag, self.y/mag, self.z/mag)
        return Vector3(0, 0, 0)

class RobotSimulation:
    """Low-poly robot simulation with tank tracks and manipulator"""
    
    def __init__(self):
        # Robot dimensions (meters)
        self.chassis_length = 0.8
        self.chassis_width = 0.6
        self.chassis_height = 0.3
        self.track_width = 0.15
        self.track_height = 0.2
        self.track_gauge = 0.5  # Distance between track centers
        self.wheel_radius = 0.1
        
        # Manipulator dimensions
        self.manipulator_base_height = 0.2
        self.link1_length = 0.3
        self.link2_length = 0.25
        self.link3_length = 0.2
        self.gripper_length = 0.15
        
        # Robot state
        self.position = Vector3(0.0, 0.0, 0.0)
        self.orientation = 0.0  # yaw angle in radians
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        
        # Manipulator state
        self.joint1_angle = 0.0  # Base rotation
        self.joint2_angle = 0.0  # Shoulder
        self.joint3_angle = 0.0  # Elbow
        self.gripper_open = 0.0  # 0=closed, 1=open
        
        # Track positions (left and right)
        self.left_track_position = 0.0
        self.right_track_position = 0.0
        
        # Simulation parameters
        self.max_linear_vel = 2.0  # m/s
        self.max_angular_vel = 3.14  # rad/s
        self.update_rate = 50  # Hz
        self.last_update = time.time()
        
    def update(self, dt):
        """Update robot simulation"""
        # Update position based on velocities
        if abs(self.linear_velocity) > 0.01 or abs(self.angular_velocity) > 0.01:
            # Differential drive kinematics
            self.position.x += self.linear_velocity * math.cos(self.orientation) * dt
            self.position.y += self.linear_velocity * math.sin(self.orientation) * dt
            self.orientation += self.angular_velocity * dt
            
            # Keep orientation in [-pi, pi]
            self.orientation = math.atan2(math.sin(self.orientation), math.cos(self.orientation))
            
            # Update track positions (for animation)
            self.left_track_position += (self.linear_velocity - self.angular_velocity * self.chassis_width/2) * dt / self.wheel_radius
            self.right_track_position += (self.linear_velocity + self.angular_velocity * self.chassis_width/2) * dt / self.wheel_radius
            
    def set_velocity(self, linear, angular):
        """Set robot velocities"""
        self.linear_velocity = max(-self.max_linear_vel, min(self.max_linear_vel, linear))
        self.angular_velocity = max(-self.max_angular_vel, min(self.max_angular_vel, angular))
        
    def set_manipulator_joints(self, joint1, joint2, joint3, joint4, joint5, gripper):
        """Set manipulator joint angles"""
        self.joint1_angle = joint1
        self.joint2_angle = joint2
        self.joint3_angle = joint3
        self.joint4_angle = joint4
        self.joint5_angle = joint5
        self.gripper_open = max(0.0, min(1.0, gripper))
        
    def get_chassis_vertices(self):
        """Get low-poly chassis vertices"""
        # Define chassis corners in local coordinates
        half_length = self.chassis_length / 2
        half_width = self.chassis_width / 2
        height = self.chassis_height
        
        vertices = [
            # Bottom face
            Vector3(-half_length, -half_width, 0),
            Vector3(half_length, -half_width, 0),
            Vector3(half_length, half_width, 0),
            Vector3(-half_length, half_width, 0),
            
            # Top face
            Vector3(-half_length, -half_width, height),
            Vector3(half_length, -half_width, height),
            Vector3(half_length, half_width, height),
            Vector3(-half_length, half_width, height),
        ]
        
        # Transform to world coordinates
        transformed = []
        for v in vertices:
            # Rotate around Z axis
            cos_o = math.cos(self.orientation)
            sin_o = math.sin(self.orientation)
            rotated_x = v.x * cos_o - v.y * sin_o
            rotated_y = v.x * sin_o + v.y * cos_o
            
            # Translate to world position
            world_pos = Vector3(
                rotated_x + self.position.x,
                rotated_y + self.position.y,
                v.z + self.position.z
            )
            transformed.append(world_pos)
            
        return transformed
        
    def get_track_vertices(self, side):
        """Get track vertices (left or right)"""
        half_length = self.chassis_length / 2
        track_offset = self.chassis_width / 2 + self.track_width / 2
        
        if side == 'left':
            offset = -track_offset
        else:
            offset = track_offset
            
        # Track segments (simplified low-poly)
        segments = []
        num_segments = 8
        segment_length = self.chassis_length / num_segments
        
        for i in range(num_segments):
            x_start = -half_length + i * segment_length
            x_end = x_start + segment_length
            
            # Add track movement animation
            track_offset_y = offset + math.sin(self.left_track_position * 2 * math.pi) * 0.01 if side == 'left' else \
                           math.sin(self.right_track_position * 2 * math.pi) * 0.01
            
            # Track segment vertices
            vertices = [
                Vector3(x_start, track_offset_y - self.track_width/2, 0),
                Vector3(x_end, track_offset_y - self.track_width/2, 0),
                Vector3(x_end, track_offset_y + self.track_width/2, self.track_height),
                Vector3(x_start, track_offset_y + self.track_width/2, self.track_height),
            ]
            
            # Transform to world coordinates
            transformed = []
            for v in vertices:
                cos_o = math.cos(self.orientation)
                sin_o = math.sin(self.orientation)
                rotated_x = v.x * cos_o - v.y * sin_o
                rotated_y = v.x * sin_o + v.y * cos_o
                
                world_pos = Vector3(
                    rotated_x + self.position.x,
                    rotated_y + self.position.y,
                    v.z + self.position.z
                )
                transformed.append(world_pos)
                
            segments.append(transformed)
            
        return segments
        
    def get_manipulator_vertices(self):
        """Get manipulator vertices"""
        vertices = []
        
        # Base position
        base_x = self.chassis_length / 2
        base_y = 0
        base_z = self.chassis_height
        
        # Joint 1 (base rotation)
        j1_x = base_x
        j1_y = base_y
        j1_z = base_z + self.manipulator_base_height
        
        # Joint 2 (shoulder)
        j2_x = j1_x + self.link1_length * math.cos(self.joint2_angle)
        j2_y = j1_y + self.link1_length * math.sin(self.joint1_angle)
        j2_z = j1_z + self.link1_length * math.sin(self.joint2_angle)
        
        # Joint 3 (elbow)
        j3_x = j2_x + self.link2_length * math.cos(self.joint2_angle + self.joint3_angle)
        j3_y = j2_y + self.link2_length * math.sin(self.joint1_angle)
        j3_z = j2_z + self.link2_length * math.sin(self.joint2_angle + self.joint3_angle)
        
        # Gripper end
        end_x = j3_x + self.link3_length * math.cos(self.joint2_angle + self.joint3_angle)
        end_y = j3_y + self.link3_length * math.sin(self.joint1_angle)
        end_z = j3_z + self.link3_length * math.sin(self.joint2_angle + self.joint3_angle)
        
        # Create link segments (simplified as lines)
        links = [
            [(base_x, base_y, base_z), (j1_x, j1_y, j1_z)],  # Base to joint1
            [(j1_x, j1_y, j1_z), (j2_x, j2_y, j2_z)],        # Joint1 to joint2
            [(j2_x, j2_y, j2_z), (j3_x, j3_y, j3_z)],        # Joint2 to joint3
            [(j3_x, j3_y, j3_z), (end_x, end_y, end_z)],      # Joint3 to end
        ]
        
        # Transform to world coordinates
        transformed_links = []
        for link in links:
            transformed_link = []
            for point in link:
                x, y, z = point
                
                # Rotate around Z axis
                cos_o = math.cos(self.orientation)
                sin_o = math.sin(self.orientation)
                rotated_x = x * cos_o - y * sin_o
                rotated_y = x * sin_o + y * cos_o
                
                # Translate to world position
                world_pos = Vector3(
                    rotated_x + self.position.x,
                    rotated_y + self.position.y,
                    z + self.position.z
                )
                transformed_link.append(world_pos)
                
            transformed_links.append(transformed_link)
            
        return transformed_links
        
    def get_gripper_vertices(self):
        """Get gripper vertices"""
        if self.gripper_open < 0.1:
            return []  # Closed gripper
            
        # Get end effector position
        manipulator_links = self.get_manipulator_vertices()
        if not manipulator_links:
            return []
            
        end_pos = manipulator_links[-1][-1]  # Last point of last link
        
        # Simple gripper representation
        gripper_width = 0.1 * self.gripper_open
        gripper_length = 0.05
        
        vertices = [
            Vector3(end_pos.x - gripper_width/2, end_pos.y, end_pos.z),
            Vector3(end_pos.x + gripper_width/2, end_pos.y, end_pos.z),
            Vector3(end_pos.x + gripper_width/2, end_pos.y, end_pos.z + gripper_length),
            Vector3(end_pos.x - gripper_width/2, end_pos.y, end_pos.z + gripper_length),
        ]
        
        return vertices
        
    def get_sensor_positions(self):
        """Get sensor positions for visualization"""
        sensors = {}
        
        # Front ultrasonic
        sensors['ultrasonic_front'] = Vector3(
            self.position.x + self.chassis_length/2 * math.cos(self.orientation),
            self.position.y + self.chassis_length/2 * math.sin(self.orientation),
            self.position.z + self.chassis_height/2
        )
        
        # Rear ultrasonic
        sensors['ultrasonic_rear'] = Vector3(
            self.position.x - self.chassis_length/2 * math.cos(self.orientation),
            self.position.y - self.chassis_length/2 * math.sin(self.orientation),
            self.position.z + self.chassis_height/2
        )
        
        # Left infrared
        left_offset = self.chassis_width/2
        sensors['infrared_left'] = Vector3(
            self.position.x - left_offset * math.sin(self.orientation),
            self.position.y + left_offset * math.cos(self.orientation),
            self.position.z + self.chassis_height/2
        )
        
        # Right infrared
        right_offset = self.chassis_width/2
        sensors['infrared_right'] = Vector3(
            self.position.x + right_offset * math.sin(self.orientation),
            self.position.y - right_offset * math.cos(self.orientation),
            self.position.z + self.chassis_height/2
        )
        
        return sensors
        
    def simulate_sensors(self, obstacles=None):
        """Simulate sensor readings"""
        if obstacles is None:
            obstacles = []
            
        sensor_readings = {}
        sensor_positions = self.get_sensor_positions()
        
        for sensor_name, sensor_pos in sensor_positions.items():
            # Simple distance simulation
            max_range = 3.0  # meters
            
            # Check for obstacles (simplified)
            min_distance = max_range
            
            for obstacle_pos in obstacles:
                distance = (sensor_pos - obstacle_pos).magnitude()
                if distance < min_distance:
                    min_distance = distance
                    
            sensor_readings[sensor_name] = min_distance
            
        return sensor_readings
        
    def get_bounding_box(self):
        """Get axis-aligned bounding box"""
        vertices = self.get_chassis_vertices()
        
        if not vertices:
            return None
            
        min_x = min(v.x for v in vertices)
        max_x = max(v.x for v in vertices)
        min_y = min(v.y for v in vertices)
        max_y = max(v.y for v in vertices)
        min_z = min(v.z for v in vertices)
        max_z = max(v.z for v in vertices)
        
        return {
            'min': Vector3(min_x, min_y, min_z),
            'max': Vector3(max_x, max_y, max_z)
        }
        
    def reset(self):
        """Reset robot to initial state"""
        self.position = Vector3(0.0, 0.0, 0.0)
        self.orientation = 0.0
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        self.joint1_angle = 0.0
        self.joint2_angle = 0.0
        self.joint3_angle = 0.0
        self.gripper_open = 0.0
        self.left_track_position = 0.0
        self.right_track_position = 0.0
