# mission.py
import asyncio
import numpy as np
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan

from signal_model import get_signal
from decision_engine import evaluate_signal
from visualization import show_heatmap

class MavsdkMission:
    def __init__(self, grid_size=(5, 5)):
        self.grid_size = grid_size
        self.scale = 0.0001  # 1 grid step = ~10 meters
        self.signal_map = np.full(grid_size, np.nan)

    async def check_arm(self, drone: System):
        async for armed in drone.telemetry.armed():
            if armed:
                print("Drone armed")
                return

    async def check_connection(self, drone: System):
        async for status in drone.core.connection_state():
            if status.is_connected:
                print("Drone connected.....")
                return

    async def run_mission(self, flight_plan):
        drone = System()
        await drone.connect(system_address="udp://:14540")
        print("connect request send")
        await self.check_connection(drone)

        home = await anext(drone.telemetry.home())
        ab_lat = home.latitude_deg
        ab_lon = home.longitude_deg

        mission_items = []
        visited_items = []  # Tracks safe waypoints to build our return path
        
        # --- 1. PATH PLANNING & SIGNAL PRE-EVALUATION ---
        for x, y in flight_plan:
            target_lat = ab_lat + (y * self.scale)
            target_lon = ab_lon + (x * self.scale)

            signal = get_signal(x, y)
            status = evaluate_signal(signal)

            if status == "NOT FEASIBLE":
                print(f"🚨 Failsafe: Grid ({x},{y}) is a dead zone! Creating reverse return path here.")
                break 

            self.signal_map[x, y] = signal

            # Create the waypoint item
            wp_item = MissionItem(
                target_lat, target_lon, 10, 5, True,
                float('nan'), float('nan'), MissionItem.CameraAction.NONE,
                float('nan'), float('nan'), 10, 2,
                float('nan'), MissionItem.VehicleAction.NONE
            )
            mission_items.append(wp_item)
            visited_items.append(wp_item) # Keep track for the return trip

        # Explicitly turn off straight-line RTL since we are doing a custom path return
        await drone.mission.set_return_to_launch_after_mission(False)
        
        mission_plan = MissionPlan(mission_items)

        print("Uploading forward mission...")
        await drone.mission.upload_mission(mission_plan)
        await asyncio.sleep(2)  

        print("⏳ Waiting for drone sensors to stabilize (GPS Lock)...")
        async for health in drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                print(" Pre-flight checks passed!")
                break
            await asyncio.sleep(1)

        await drone.action.arm()
        await self.check_arm(drone)

        print("Starting Forward Mission...")
        await drone.mission.start_mission()

        # Monitor forward progress
        async for mission_progress in drone.mission.mission_progress():
            print(f"Forward progress: {mission_progress.current}/{mission_progress.total}")
            if mission_progress.current == mission_progress.total:
                print("🏁 Destination reached!")
                break

        # --- 2. THE REVERSE RETURN-TO-LAND HANDSHAKE ---
        print("\n🔄 Reversing flight path for a safe Return-To-Land...")
        
        # Reverse our visited items list so the last point visited becomes the first return point
        return_items = visited_items[::-1]
        
        # Ensure the final point of the return mission is explicitly set to land
        # We look at the last item (which is back at home) and tell it to trigger a landing
        if return_items:
            last_item = return_items[-1]
            return_items[-1] = MissionItem(
                last_item.latitude_deg, last_item.longitude_deg, 10, 5, True,
                float('nan'), float('nan'), MissionItem.CameraAction.NONE,
                float('nan'), float('nan'), 10, 2,
                float('nan'), MissionItem.VehicleAction.LAND # <-- Tells PX4 to physically touch down here
            )

        return_plan = MissionPlan(return_items)
        
        print("📤 Uploading reversed return path layout to QGroundControl...")
        await drone.mission.upload_mission(return_plan)
        await asyncio.sleep(2)

        print("🚀 Executing Return Mission...")
        await drone.mission.start_mission()

        # Monitor return progress
        async for mission_progress in drone.mission.mission_progress():
            print(f"Return progress: {mission_progress.current}/{mission_progress.total}")
            if mission_progress.current == mission_progress.total:
                print("🛬 Touchdown sequence completed!")
                break

        # Wait until the drone disarms automatically after landing
        print("🔒 Waiting for motors to disarm...")
        async for armed in drone.telemetry.armed():
            if not armed:
                print("🔒 Drone safely disarmed on ground.")
                break
            await asyncio.sleep(1)

        print("📊 Opening Tunnel RF Heatmap Report...")
        show_heatmap(self.signal_map)