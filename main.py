# Framework
from ETS2LA.Events import *
from ETS2LA.Plugin import *
import time
import math

class Plugin(ETS2LAPlugin):
    
    description = PluginDescription(
        name="Automatic Blinkers",
        version="1.4.1",
        description="This plugin enables the blinkers for upcoming turns.",
        modules=["Traffic", "TruckSimAPI", "SDKController"],
        listen=["*.py"],
        tags=["Base"],
        fps_cap=15
    )
    
    author = Author(
        name="Playzzero97",
        url="https://github.com/Playzzero97",
        icon="https://avatars.githubusercontent.com/u/219891638?v=4"
    )

    def init(self):
        self.controller = self.modules.SDKController.SCSController()
        self.last_turn_direction = None
        self.active_blinker = None  # "left", "right", or None
        truck_indicating_left = None
        truck_indicating_right = None

    def get_turn_direction(self, points, angle_threshold=2.5, hold_time=1.5):
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

        avg_angle = total_angle / count
        now = time.time()
        # print(abs(avg_angle))

        if self.last_turn_direction is None:
            if avg_angle > angle_threshold:
                self.last_turn_direction = "right"
                self.turn_hold_until = now + hold_time
            elif avg_angle < -angle_threshold:
                self.last_turn_direction = "left"
                self.turn_hold_until = now + hold_time
            elif abs(avg_angle) > 3.8:
                return None
        else:
            # Only clear if angle is low AND hold time expired
            if abs(avg_angle) < angle_threshold and now >= self.turn_hold_until:
                self.last_turn_direction = None

        return self.last_turn_direction


    def reset_indicators(self):
        if self.truck_indicating_left:
            self.controller.lblinker = True
            time.sleep(1/20)
            self.controller.lblinker = False
            time.sleep(1/20)
        elif self.truck_indicating_right:
            self.controller.rblinker = True
            time.sleep(1/20)
            self.controller.rblinker = False
            time.sleep(1/20)
        
    def indicate_right(self):
        if not self.truck_indicating_right:
            self.controller.rblinker = True
            time.sleep(1/20)
            self.controller.rblinker = False
            time.sleep(1/20)
                
    def indicate_left(self):
        if not self.truck_indicating_left:
            self.controller.lblinker = True
            time.sleep(1/20)
            self.controller.lblinker = False
            time.sleep(1/20)

    def run(self):
        api_data = self.modules.TruckSimAPI.run()
        self.truck_indicating_left = api_data["truckBool"]["blinkerLeftActive"]
        self.truck_indicating_right = api_data["truckBool"]["blinkerRightActive"]

        status = self.globals.tags.status
        acc = False
        map = False
        if status:
            status = self.globals.tags.merge(status)
            acc = status.get("AdaptiveCruiseControl", False)
            map = status.get("Map", False)

            if map == False:
                return

        points = self.globals.tags.steering_points
        points = self.globals.tags.merge(points)
        if not points or len(points) < 3:
            return

        try:
            if isinstance(points, dict):
                points = list(points.values())
            points = [(float(x), float(y), float(z)) for x,y,z in points]
        except Exception as e:
            print(f"[AB] Failed to sanitize points: {e}")
            return

        direction = self.get_turn_direction(points[:30])

        distance = (self.globals.tags.next_intersection_distance or {}).get('plugins.map', 0)

        if self.globals.tags.road_type == "highway" or distance <= 25:
            # Turn started
            if direction == "left" and not self.truck_indicating_left:
                self.indicate_left()
                self.active_blinker = "left"
                print("[AB] Switching to left blinker")

            elif direction == "right" and not self.truck_indicating_right:
                self.indicate_right()
                self.active_blinker = "right"
                print("[AB] Switching to right blinker")

            # Turn ended
            elif direction is None and self.active_blinker is not None:
                self.active_blinker = None
                self.reset_indicators()
                self.last_turn_direction = None
                print("[AB] No turn detected, clearing blinkers")
