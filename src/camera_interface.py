#!/usr/bin/env python3
"""
Camera Interface for Sanhum Robot
Python interface for camera capture and processing
"""

import cv2
import threading
import time
import numpy as np
from typing import Optional, Callable, Dict, List
import json

class CameraInterface:
    """Interface for camera capture and processing"""
    
    def __init__(self, camera_indices: List[int] = [0, 1, 2]):
        self.camera_indices = camera_indices
        self.captures = {}
        self.connected = {}
        self.running = False
        self.frame_callbacks = {}
        self.capture_threads = {}
        
        # Frame counters
        self.frame_counts = {i: 0 for i in camera_indices}
        
    def connect(self) -> bool:
        """Connect to all cameras"""
        success = True
        
        for idx in self.camera_indices:
            try:
                cap = cv2.VideoCapture(idx)
                
                # Test if camera is available
                if cap.isOpened():
                    # Set camera properties
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    # Test capture
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        self.captures[idx] = cap
                        self.connected[idx] = True
                        print(f"Camera {idx} connected successfully")
                    else:
                        print(f"Camera {idx} failed to capture frame")
                        cap.release()
                        self.connected[idx] = False
                        success = False
                else:
                    print(f"Camera {idx} not available")
                    self.connected[idx] = False
                    success = False
                    
            except Exception as e:
                print(f"Error connecting to camera {idx}: {e}")
                self.connected[idx] = False
                success = False
                
        return success and len(self.captures) > 0
        
    def disconnect(self):
        """Disconnect all cameras"""
        self.running = False
        
        # Wait for threads to finish
        for thread in self.capture_threads.values():
            if thread.is_alive():
                thread.join(timeout=2)
                
        # Release captures
        for idx, cap in self.captures.items():
            cap.release()
            
        self.captures.clear()
        self.connected.clear()
        print("All cameras disconnected")
        
    def start_capture(self):
        """Start camera capture threads"""
        if not self.captures:
            return False
            
        self.running = True
        
        for idx in self.captures.keys():
            thread = threading.Thread(target=self._capture_loop, args=(idx,), daemon=True)
            self.capture_threads[idx] = thread
            thread.start()
            
        print(f"Started capture for {len(self.captures)} cameras")
        return True
        
    def stop_capture(self):
        """Stop camera capture"""
        self.running = False
        
    def _capture_loop(self, camera_idx: int):
        """Capture loop for a single camera"""
        cap = self.captures[camera_idx]
        
        while self.running:
            try:
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    self.frame_counts[camera_idx] += 1
                    
                    # Call callback if set
                    if camera_idx in self.frame_callbacks:
                        self.frame_callbacks[camera_idx](frame, camera_idx)
                        
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"Error capturing from camera {camera_idx}: {e}")
                time.sleep(0.1)
                
    def set_frame_callback(self, camera_idx: int, callback: Callable[[np.ndarray, int], None]):
        """Set callback for frame updates"""
        self.frame_callbacks[camera_idx] = callback
        
    def get_frame(self, camera_idx: int) -> Optional[np.ndarray]:
        """Get single frame from camera"""
        if camera_idx not in self.captures:
            return None
            
        try:
            ret, frame = self.captures[camera_idx].read()
            return frame if ret else None
        except:
            return None
            
    def get_all_frames(self) -> Dict[int, np.ndarray]:
        """Get frames from all connected cameras"""
        frames = {}
        
        for idx in self.captures.keys():
            frame = self.get_frame(idx)
            if frame is not None:
                frames[idx] = frame
                
        return frames
        
    def get_camera_info(self) -> Dict[int, Dict]:
        """Get information about all cameras"""
        info = {}
        
        for idx in self.camera_indices:
            info[idx] = {
                'connected': self.connected.get(idx, False),
                'frame_count': self.frame_counts.get(idx, 0),
                'resolution': (640, 480) if self.connected.get(idx, False) else (0, 0)
            }
            
        return info
        
    def take_snapshot(self, camera_idx: int, filename: str = None) -> bool:
        """Take snapshot from specific camera"""
        if filename is None:
            timestamp = int(time.time())
            filename = f"camera_{camera_idx}_{timestamp}.jpg"
            
        frame = self.get_frame(camera_idx)
        if frame is not None:
            try:
                cv2.imwrite(filename, frame)
                print(f"Snapshot saved: {filename}")
                return True
            except Exception as e:
                print(f"Error saving snapshot: {e}")
                return False
        else:
            print(f"Failed to get frame from camera {camera_idx}")
            return False

# Simulation fallback
class CameraSimulation:
    """Simulation fallback for camera interface"""
    
    def __init__(self, camera_indices: List[int] = [0, 1, 2]):
        self.camera_indices = camera_indices
        self.connected = {idx: True for idx in camera_indices}
        self.running = False
        self.frame_callbacks = {}
        self.capture_threads = {}
        self.frame_counts = {idx: 0 for idx in camera_indices}
        
    def connect(self) -> bool:
        print("Camera simulation mode - no real hardware")
        return True
        
    def disconnect(self):
        self.running = False
        print("Camera simulation disconnected")
        
    def start_capture(self):
        """Start simulated capture threads"""
        self.running = True
        
        for idx in self.camera_indices:
            thread = threading.Thread(target=self._simulation_loop, args=(idx,), daemon=True)
            self.capture_threads[idx] = thread
            thread.start()
            
        return True
        
    def stop_capture(self):
        """Stop simulated capture"""
        self.running = False
        
    def _simulation_loop(self, camera_idx: int):
        """Simulated camera capture loop"""
        while self.running:
            try:
                # Generate simulated frame
                frame = self._generate_simulated_frame(camera_idx)
                self.frame_counts[camera_idx] += 1
                
                # Call callback if set
                if camera_idx in self.frame_callbacks:
                    self.frame_callbacks[camera_idx](frame, camera_idx)
                    
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"Error in camera simulation {camera_idx}: {e}")
                time.sleep(0.1)
                
    def _generate_simulated_frame(self, camera_idx: int) -> np.ndarray:
        """Generate simulated camera frame"""
        # Create a colorful simulated frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add some visual elements based on camera position
        if camera_idx == 0:  # Front camera
            # Green gradient
            for i in range(480):
                frame[i, :, 1] = int(255 * (i / 480))
            # Add "FRONT" text
            cv2.putText(frame, "FRONT CAMERA", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
        elif camera_idx == 1:  # Rear camera
            # Blue gradient
            for i in range(480):
                frame[i, :, 0] = int(255 * (i / 480))
            # Add "REAR" text
            cv2.putText(frame, "REAR CAMERA", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
        elif camera_idx == 2:  # Manipulator camera
            # Red gradient
            for i in range(480):
                frame[i, :, 2] = int(255 * (i / 480))
            # Add "MANIPULATOR" text
            cv2.putText(frame, "MANIPULATOR", (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
        # Add timestamp
        timestamp = time.strftime("%H:%M:%S")
        cv2.putText(frame, timestamp, (10, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add some moving elements
        import random
        for _ in range(10):
            x = random.randint(0, 640)
            y = random.randint(0, 480)
            cv2.circle(frame, (x, y), 3, (255, 255, 255), -1)
            
        return frame
        
    def set_frame_callback(self, camera_idx: int, callback: Callable[[np.ndarray, int], None]):
        """Set callback for frame updates"""
        self.frame_callbacks[camera_idx] = callback
        
    def get_frame(self, camera_idx: int) -> Optional[np.ndarray]:
        """Get simulated frame"""
        return self._generate_simulated_frame(camera_idx)
        
    def get_all_frames(self) -> Dict[int, np.ndarray]:
        """Get frames from all cameras"""
        frames = {}
        for idx in self.camera_indices:
            frames[idx] = self.get_frame(idx)
        return frames
        
    def get_camera_info(self) -> Dict[int, Dict]:
        """Get camera information"""
        info = {}
        for idx in self.camera_indices:
            info[idx] = {
                'connected': self.connected.get(idx, False),
                'frame_count': self.frame_counts.get(idx, 0),
                'resolution': (640, 480)
            }
        return info
        
    def take_snapshot(self, camera_idx: int, filename: str = None) -> bool:
        """Take simulated snapshot"""
        if filename is None:
            timestamp = int(time.time())
            filename = f"camera_{camera_idx}_{timestamp}.jpg"
            
        frame = self.get_frame(camera_idx)
        if frame is not None:
            try:
                cv2.imwrite(filename, frame)
                print(f"Simulated snapshot saved: {filename}")
                return True
            except Exception as e:
                print(f"Error saving simulated snapshot: {e}")
                return False
        return False

def get_camera_interface(simulation: bool = True, camera_indices: List[int] = [0, 1, 2]) -> object:
    """Get camera interface (real or simulation)"""
    if simulation:
        return CameraSimulation(camera_indices)
    else:
        return CameraInterface(camera_indices)

if __name__ == "__main__":
    # Test the interface
    camera = get_camera_interface(simulation=True)
    
    def frame_callback(frame, camera_idx):
        print(f"Received frame from camera {camera_idx}: {frame.shape}")
    
    # Set callbacks
    camera.set_frame_callback(0, frame_callback)
    camera.set_frame_callback(1, frame_callback)
    camera.set_frame_callback(2, frame_callback)
    
    if camera.connect():
        print("Camera interface connected")
        
        if camera.start_capture():
            print("Camera capture started")
            
            # Test for a few seconds
            time.sleep(5)
            
            camera.stop_capture()
        
        # Test snapshots
        camera.take_snapshot(0, "test_snapshot_0.jpg")
        camera.take_snapshot(1, "test_snapshot_1.jpg")
        camera.take_snapshot(2, "test_snapshot_2.jpg")
        
        # Get camera info
        info = camera.get_camera_info()
        print("Camera info:", info)
        
        camera.disconnect()
    else:
        print("Failed to connect to cameras")
