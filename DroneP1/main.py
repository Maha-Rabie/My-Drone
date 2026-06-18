# main.py
import asyncio
from mission import MavsdkMission


# Generate a lawnmower grid path plan
lawnmower_plan = []
for x in range(5):
        if x % 2 == 0:
            for y in range(5): lawnmower_plan.append((x, y))
        else:
            for y in reversed(range(5)): lawnmower_plan.append((x, y))

# Initialize our MAVSDK class
uav_mission = MavsdkMission()
    
# Run the async loop
asyncio.run(uav_mission.run_mission(lawnmower_plan))