# Framework
from ETS2LA.Events import *
from ETS2LA.Plugin import *
import Plugins.Map.data as mapdata

import time
import math

class Plugin(ETS2LAPlugin):
    
    description = PluginDescription(
        name="Automatic Blinkers",
        version="1.1.0",
        description="Will activate the blinkers when turning and when doing lane changes (WIP)",
        modules=["Traffic", "TruckSimAPI", "SDKController"],
        listen=["*.py"],
        tags=["Base"],
        fps_cap=5
    )
    
    author = Author(
        name="Playzzero97",
        url="https://github.com/Playzzero97",
        icon="https://avatars.githubusercontent.com/u/219891638?v=4"
    )

    def init(self):
        self.controller = self.modules.SDKController.SCSController()
        self.last_turn_direction = None
        
    def get_turn_direction(self, points, on_threshold=1.5, off_threshold=0.2):
        if len(points) < 3:
            return None

        def vec(p1, p2): return (p2[0] - p1[0], p2[2] - p1[2])
        def normalize(v):
            length = math.hypot(v[0], v[1])
            return (v[0]/length, v[1]/length) if length else (0, 0)

        total_angle = 0
        count = 0

        for i in range(len(points) - 2):
            A, B, C = points[i], points[i + 1], points[i + 2]
            v1, v2 = normalize(vec(A, B)), normalize(vec(B, C))
            dot = max(min(v1[0]*v2[0] + v1[1]*v2[1], 1.0), -1.0)
            angle = math.acos(dot) * (180 / math.pi)
            cross = v1[0]*v2[1] - v1[1]*v2[0]
            signed_angle = angle if cross > 0 else -angle
            total_angle += signed_angle
            count += 1

        avg_angle = total_angle / count if count > 0 else 0
        # print(abs(avg_angle))

        if self.last_turn_direction is None:
            if avg_angle > on_threshold:
                self.last_turn_direction = "right"
            elif avg_angle < -on_threshold:
                self.last_turn_direction = "left"
        else:
            if abs(avg_angle) < off_threshold:
                self.last_turn_direction = None

        return self.last_turn_direction


        
    def run(self):
        data = self.modules.TruckSimAPI.run()
        speed = data["truckFloat"]["speed"]

        points = self.globals.tags.steering_points
        points = self.globals.tags.merge(points)

        if not points:
            print("[AB] No steering points found.")
            return

        if not isinstance(points, list):
            if isinstance(points, dict):
                points = list(points.values())
            else:
                try:
                    points = list(points)
                except Exception as e:
                    print(f"[AB] Could not convert steering_points to list: {e}")
                    return
                
        if len(points) < 3:
            print(f"[AB] Not enough points: {len(points)}")
            return

        try:
            points = [(float(x), float(y), float(z)) for (x, y, z) in points]
        except Exception as e:
            print(f"[AB] Failed to sanitize points: {e}")
            return

        # print(f"[AB] Loaded {len(points)} steering points")
        
        direction = self.get_turn_direction(points[:20])

        if direction == "left" and speed > 0:
            if not self.controller.lblinker:
                print("[AB] Detected left turn")
                self.controller.lblinker = True
                self.controller.rblinker = False
            self.last_turn_direction = "left"

        elif direction == "right" and speed > 0:
            if not self.controller.rblinker:
                print("[AB] Detected right turn")
                self.controller.rblinker = True
                self.controller.lblinker = False
            self.last_turn_direction = "right"

        else: 
            if self.last_turn_direction is None and speed > 0:
                self.controller.rblinker = False
                self.controller.lblinker = False




