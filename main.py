# Framework
from ETS2LA.Events import *
from ETS2LA.Plugin import *
import Plugins.Map.data as mapdata

import time
import math

class Plugin(ETS2LAPlugin):
    
    description = PluginDescription(
        name="Automatic Blinkers",
        version="1.0.0",
        description="This plugin enables the blinkers depending on steering input and also activates them during lane changes.",
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
        self.previous_lane_change_status = None
        self.last_reset_time = 0
     
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
        lane_change_status = None

        if status_dict and "plugins.map" in status_dict:
            lane_change_status = status_dict["plugins.map"]

        if self.previous_lane_change_status and self.previous_lane_change_status.startswith("executing") and lane_change_status == "idle":
            print("Lane change completed. Resetting blinkers.")
            self.controller.lblinker = False
            self.controller.rblinker = False
            self.last_reset_time = time.time()

        self.previous_lane_change_status = lane_change_status

        if lane_change_status and lane_change_status.startswith("executing:"):
                percentage = float(lane_change_status.split(":")[1]) * 100
                print(f"Lane change in progress: {percentage:.1f}%")
                
                steeringgame = steeringgame

                if steeringgame < -0.01 and self.controller.lblinker == False:
                    self.controller.rblinker = True
                    self.controller.lblinker = False
                elif steeringgame > 0.01 and self.controller.rblinker == False:
                    self.controller.lblinker = True
                    self.controller.rblinker = False

                return
            
        if time.time() - self.last_reset_time > 2.0:  # 2 seconds cooldown
            if speed > 0:
                if steeringgame < -0.15:
                    self.controller.rblinker = True
                    self.controller.lblinker = False
                elif steeringgame > 0.15:
                    self.controller.lblinker = True
                    self.controller.rblinker = False
                else:
                    self.controller.lblinker = False
                    self.controller.rblinker = False
        # print(steeringgame)

