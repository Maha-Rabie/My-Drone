# 🚁 DroneP1 — Autonomous UAV Tunnel Inspection Mission

A Python-based autonomous drone mission system built on **MAVSDK** and **PX4**, designed for RF signal-guided inspection flights inside tunnel environments. The drone follows a lawnmower grid pattern, evaluates signal strength at each waypoint in real time, and executes a **custom reversed return-to-land path** rather than a straight-line RTL.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [File Structure](#file-structure)
- [How It Works](#how-it-works)
- [Signal Model](#signal-model)
- [Decision Engine](#decision-engine)
- [Reverse Return-to-Land](#reverse-return-to-land)
- [Visualization](#visualization)
- [Requirements](#requirements)
- [Running the Mission](#running-the-mission)

---

## Overview

DroneP1 autonomously scans a 5×5 grid using a lawnmower path, collecting RF signal readings at each cell. If a waypoint is deemed a **dead zone** (signal too weak to maintain safe operation), the mission halts immediately and the drone traces back the exact path it flew — in reverse — to return home safely. On completion, a **heatmap** of signal strength across the tunnel grid is displayed.

---

## Architecture

```
main.py
  └── MavsdkMission (mission.py)
        ├── signal_model.py     ← RF physics simulation
        ├── decision_engine.py  ← Classifies signal quality
        └── visualization.py   ← Heatmap rendering
```

---

## File Structure

| File | Purpose |
|---|---|
| `main.py` | Entry point — builds lawnmower path, launches async mission loop |
| `mission.py` | Core mission class: connects to drone, uploads waypoints, monitors progress, executes reverse RTL |
| `signal_model.py` | Computes simulated RF signal strength (dBm) using path loss + tunnel noise |
| `decision_engine.py` | Classifies signal as `GOOD`, `WEAK`, or `NOT FEASIBLE` |
| `visualization.py` | Renders a color-coded heatmap of the scanned RF signal map |

---

## How It Works

### 1. Path Planning (Lawnmower Grid)

`main.py` generates a 5×5 lawnmower scan path — alternating row directions to minimize travel distance:

```
Row 0 → left to right
Row 1 → right to left
Row 2 → left to right
...
```

### 2. Pre-flight Signal Evaluation

Before uploading each waypoint to the drone, the system calls `get_signal(x, y)` and evaluates the result. If a grid cell is classified as `NOT FEASIBLE`, the forward path is **cut short at that point** — the drone will never attempt to fly into a dead zone.

### 3. Mission Upload & Execution

The approved waypoints are packaged into a `MissionPlan` and uploaded to PX4 via MAVSDK. The drone arms, passes a GPS health check, and begins the forward scan mission.

### 4. Reverse Return-to-Land

Once the forward mission completes (or is cut short), the visited waypoint list is **reversed** to build the return path. The final waypoint of the return trip is explicitly tagged with `VehicleAction.LAND`, triggering a physical touchdown at the home position.

---

## Signal Model

**File:** `signal_model.py`

Simulates real-world RF propagation inside a tunnel using the **log-distance path loss model** with added sinusoidal tunnel noise.

### Parameters

| Parameter | Value | Description |
|---|---|---|
| `TRANSMITTER_POS` | `(2, 0)` | Antenna at tunnel entrance |
| `P0` | `-40 dBm` | Reference signal strength at 1 meter |
| `PATH_LOSS_EXPONENT` | `2.5` | Signal decay factor (tunnel walls) |
| `SHADOW_FADING_STD` | `2.0` | Intensity of reflective interference noise |

### Formula

```
signal = P0 - (10 × n × log10(distance)) + noise
```

Where `noise = sin(x×5) × cos(y×5) × SHADOW_FADING_STD` models tunnel wall reflections.

---

## Decision Engine

**File:** `decision_engine.py`

Classifies each signal reading into one of three states:

| Signal Strength | Status | Action |
|---|---|---|
| > -75 dBm | `GOOD` | Proceed to waypoint |
| -75 to -90 dBm | `WEAK` | Proceed with caution |
| ≤ -90 dBm | `NOT FEASIBLE` | 🚨 Halt — trigger reverse RTL |

---

## Reverse Return-to-Land

A key safety feature of DroneP1. Instead of using PX4's built-in straight-line RTL (which could fly through unmapped or hazardous areas), the mission:

1. Tracks every visited waypoint in order during the forward pass.
2. On completion or failsafe trigger, reverses the list: `visited_items[::-1]`.
3. Modifies the final waypoint's `VehicleAction` to `LAND`.
4. Uploads and executes the reversed path as a new mission plan.

This guarantees the drone returns via a **known-safe corridor**.

---

## Visualization

**File:** `visualization.py`

After the mission completes, a `matplotlib` heatmap is rendered showing signal strength (dBm) at each scanned grid cell using the `viridis` colormap.

- **Bright yellow** → Strong signal (near antenna)
- **Dark purple** → Weak signal (deep tunnel / dead zones)
- **NaN cells** (grey) → Waypoints not reached due to failsafe

---

## Requirements

```
mavsdk
numpy
matplotlib
```

Install dependencies:

```bash
pip install mavsdk numpy matplotlib
```

> **Note:** Requires a running PX4 SITL or hardware drone accessible at `udp://:14540`.

---

## Running the Mission

```bash
# Start PX4 SITL (in a separate terminal)
make px4_sitl gazebo

# Launch the mission
python main.py
```

Expected console output:

```
connect request send
Drone connected.....
 Pre-flight checks passed!
Drone armed
Starting Forward Mission...
Forward progress: 1/25
...
🏁 Destination reached!
🔄 Reversing flight path for a safe Return-To-Land...
📤 Uploading reversed return path layout to QGroundControl...
🚀 Executing Return Mission...
🛬 Touchdown sequence completed!
🔒 Drone safely disarmed on ground.
📊 Opening Tunnel RF Heatmap Report...
```

---

## License

This project is part of the **My-D** repository. See the root repository for license details.
