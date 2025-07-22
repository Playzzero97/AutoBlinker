# Framework
from ETS2LA.Events import *
from ETS2LA.Plugin import *
import Plugins.Map.data as mapdata

import time
import math

class Plugin(ETS2LAPlugin):
    
    description = PluginDescription(
        name="Automatic Blinkers",
        version="1.0.3",
        description="This plugin enables the blinkers depending on steering input and also activates them during lane changes.",
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
        self.previous_lane_change_status = None
        self.last_reset_time = 0
        self.last_lane_change_exec_time = 0
        self.in_lane_change = False
        self.lane_change_idle_start_time = None
    
    def reset_blinkers(self):
        if self.controller.lblinker or self.controller.rblinker:
            self.controller.lblinker = False
            self.controller.rblinker = False

     
    # Postponed feature until map rewrite    
    # def get_upcoming_turn_angle(self, min_z=1.0):
    #     points = self.globals.tags.steering_points
    #     points = self.globals.tags.merge(points)

    #     if not points or len(points) < 2:
    #         print("No valid steering points found.")
    #         return 0.0

    #     # Auto-reverse if most points are behind
    #     if sum(1 for p in points if p[2] < 0) > len(points) // 2:
    #         print("Reversing steering point list — it's pointing backwards.")
    #         points = list(reversed(points))

    #     # Find first point ahead of truck
    #     for point in points:
    #         x, z = point[0], point[2]
    #         if z > min_z:
    #             angle = math.degrees(math.atan2(x, z))
    #             print(f"Valid forward point: x={x:.2f}, z={z:.2f}, angle={angle:.2f}°")
    #             return angle

    #     print("No forward-facing steering points found.")
    #     return 0.0
        
    def run(self):
        data = self.modules.TruckSimAPI.run()
        steeringgame = data["truckFloat"]["gameSteer"]
        speed = data["truckFloat"]["speed"]

        status_dict = self.globals.tags.lane_change_status
        lane_change_status = status_dict.get("plugins.map") if status_dict else None

        now = time.time()

        if lane_change_status and lane_change_status.startswith("executing:"):
            if not self.in_lane_change:
                print("[AB] Lane change started.")
                self.in_lane_change = True
                self.lane_change_idle_start_time = None
                self.active_lane_change_blinker = None

            percentage = float(lane_change_status.split(":")[1]) * 100
            print(f"[AB] Lane change in progress: {percentage:.1f}%")

            if self.active_lane_change_blinker is None:
                if steeringgame < -0.01:
                    self.controller.rblinker = True
                    self.controller.lblinker = False
                    self.active_lane_change_blinker = "right"
                elif steeringgame > 0.01:
                    self.controller.lblinker = True
                    self.controller.rblinker = False
                    self.active_lane_change_blinker = "left"
            return

        if self.in_lane_change and lane_change_status == "idle":
            if self.lane_change_idle_start_time is None:
                self.lane_change_idle_start_time = now
            elif now - self.lane_change_idle_start_time > 0.5:
                print("[AB] Lane change finished. Resetting blinkers.")
                self.reset_blinkers()
                self.last_reset_time = now
                self.in_lane_change = False
                self.lane_change_idle_start_time = None
                self.active_lane_change_blinker = None
                
        if speed > 0 and now - self.last_reset_time > 2.0 and lane_change_status == "idle" and not self.in_lane_change:
            if steeringgame < -0.15:
                self.controller.rblinker = True
                self.controller.lblinker = False
            elif steeringgame > 0.15:
                self.controller.lblinker = True
                self.controller.rblinker = False
            else:
                if self.controller.lblinker or self.controller.rblinker:
                    print("[AB] Steering centered. Turning off blinkers.")
                    self.reset_blinkers()
                    self.last_reset_time = now

        # print(steeringgame)

