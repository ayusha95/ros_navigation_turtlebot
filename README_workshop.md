# TurtleBot4 Navigation with Nav2 Route Server

ROS 2 navigation stack for the **TurtleBot4** platform, built on top of the ROSConDE 2025 Navigation Workshop base. This repository extends the base setup with custom maps, SLAM workflows, and topology-based route planning using the **Nav2 Route Server** introduced in ROS 2 Kilted.

Key additions over the base workshop:
- SLAM-based map creation workflow (`docker-compose-slam.yaml`)
- Custom map: `bot4House` (house floor plan)
- Custom route graph generation via the Nav2 Route Server Tool
- Extended `route_example_launch.py` with additional map types and poses

---

## Requirements

- Laptop with Docker installed
- ROS 2 Dev Container (Kilted recommended) — see `devcontainer/` folder
- Basic familiarity with ROS 2 and Docker
- Lichtblick Suite installed — see [installation instructions](#lichtblick-suite) below

---


## Initial Setup

```bash
# 1. Allow Docker containers to access the display
xhost +local:root

# 2. Checkout the correct branch
cd ros_navigation_turtlebot/
git checkout route_planner_v1

# 3. Clone dependencies for simulation
cd turtlebot_simulation/
vcs import < roscon.repos

# 4. Clone dependencies for navigation
cd ../turtlebot_navigation/
vcs import < roscon.repos

# 5. Pull the Docker image (optional but recommended)
#    All compose files use this image. Docker will auto-pull on first run if not present,
#    but pulling explicitly ensures you have the latest version.
docker pull cinoderobotics/turtlebot4_navigation:kilted-amd64-v1.2.0
```

### Step 1 — Create a Gazebo World (optional)

If you need a new simulation environment, follow the instructions in `turtlebot_simulation/worlds/template.sdf`.

After creating your own .sdf file, you can check it by running this command ```gz sim <your_world_name>```

**1a. Copy the world file to the simulator package:**

```bash
cp turtlebot_simulation/worlds/<your_world>.sdf \
   turtlebot_simulation/turtlebot4_simulator/turtlebot4_gz_bringup/worlds/<your_world>.sdf
```
### ⚠️ Note: whatever changes made in below three files should not be committed

**1b. Update the default world name in the following launch files** under `turtlebot_simulation/turtlebot4_simulator/turtlebot4_gz_bringup/launch/`:

| File | Line | Change |
|------|------|--------|
| `ros_gz_bridge.launch.py` | 38 | `default_value='<your_world>'` |
| `sim.launch.py` | 35 | `default_value='<your_world>'` |
| `turtlebot4_gz.launch.py` | 31 | `default_value='<your_world>'` |

---

---

## Workflow

### Step 2 — Create a Map (SLAM)

Run the SLAM stack and teleoperate the robot to build a map:

```bash
 ### Go to turtlebot_simulation/docker-compose-slam.yaml : 
 line 67 - command: /bin/bash -c 'ros2 launch nav2_simple_commander slam_mapping_launch.py world:=```<your_world_name>``` force_software_rendering:=True'
 
 # Slam mapping
change Map_type = ```<your_world_name```

# Start SLAM
docker compose -f docker-compose-slam.yaml up

# In a second terminal: teleoperate the robot
docker exec -it ros2-turtlebot4-slam-kilted \
  ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -p stamped:=true

if the above command not works then
 * docker exec -it ros2-turtlebot4-slam-kilted bash
 * source /opt/ros/kilted/setup.bash
 * apt update && apt install ros-kilted-teleop-twist-keyboard
 * ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true

### ⚠️ Note: Map name should be in this format
    ```<your_world_name>.pgm and <your_world_name>.yaml```

# Once the map looks complete in RViz, save it
docker exec ros2-turtlebot4-slam-kilted \
  ros2 run nav2_map_server map_saver_cli -f /maps/<your_map_name>
```

This saves your map files into `turtlebot_simulation/turtlebot4/turtlebot4_navigation/maps`.

---

### Step 3 — Create a Route Graph

Route graphs define the topology the robot navigates along. They are stored as `.geojson` files in `turtlebot_simulation/graphs/`.

**3a. Load the map in the Route Server Tool:**

Update the map path in `docker-compose-route-server-tool.yaml` to point to your map:

> ⚠️ Make sure the map path is set **before** running the compose file — otherwise an empty folder will be created with the map name.

```yaml
command: /bin/bash -c 'ros2 launch nav2_rviz_plugins route_tool.launch.py \
  yaml_filename:=/opt/ros/kilted/share/nav2_bringup/maps/<your_map_name>.yaml'
```

**3b. Launch the Route Server Tool:**

```bash
cd turtlebot_simulation/
docker compose -f docker-compose-route-server-tool.yaml up -d
```

RViz will open with your map. Use the **Route Tool** to:
1. Add nodes and edges on the map
2. Use the **Publish Point** tool in RViz to get precise x/y coordinates for node placement
3. Save the graph to `/opt/ros/kilted/share/nav2_bringup/graphs/<your_world_name>_graph.geojson`

The file is automatically synced to `turtlebot_simulation/graphs/`.

---

 ### Note 
    Gazebo file name :- __name__.sdf 
    Map file name :- __name__.pgm and __name__.yaml
    geojson file name :- __name__ _gragh.geojson

### Step 4 — Configure Start and Goal Poses

Edit `turtlebot_simulation/scripts/route_example_launch.py` to add your map's spawn and goal poses. Copy the x/y coordinates from your saved `.geojson` graph:

```python
MAP_POSES_DICT = {
    "depot":     {"x": -8.00,  "y":  0.00,  "z": 0.01, "R": 0.00, "P": 0.00, "Y": 0.00},
    "warehouse": {"x":  2.00,  "y": -19.65, "z": 0.01, "R": 0.00, "P": 0.00, "Y": 0.00},
    "bot4House": {"x": -4.107, "y":  3.730,  "z": 0.01, "R": 0.00, "P": 0.00, "Y": 0.00},
    # Add your map here
    "<your_map>": {"x": ..., "y": ..., "z": 0.01, "R": 0.00, "P": 0.00, "Y": 0.00},
}

ROUTE_POSES_DICT = {
    "start": {
        "depot":     {"x": 7.5,   "y":  7.5,   "yaw": 0.00},  # 3rd node
        "warehouse": {"x": 2.00,  "y": -19.65,  "yaw": 0.00},  # 0th node
        "bot4House": {"x": -4.107,"y":  3.730,   "yaw": 0.00},
        "<your_map>": {"x": ...,  "y": ...,      "yaw": 0.00},
    },
    "goal": {
        "depot":     {"x": 20.12, "y": 11.83, "yaw": 0.00},
        "warehouse": {"x": -13.0, "y": 13.0,  "yaw": 0.00},
        "bot4House": {"x": -2.552,"y":  4.216, "yaw": 0.00},
        "<your_map>": {"x": ...,  "y": ...,    "yaw": 0.00},
    },
}
```

Then set your active map:
```python
MAP_TYPE = "<your_map>"
```

---

### Step 5 — Run the Route Server Example

```bash
cd turtlebot_simulation/
docker compose -f docker-compose-route-example.yaml up -d
```

The TurtleBot4 will spawn at the defined start pose and navigate to the goal along the route graph. RViz opens automatically showing the robot's progress.

To switch environments, change `MAP_TYPE` in `route_example_launch.py` and restart the compose stack.

---

## Pre-configured Environments

| Map name    | Description            |
|-------------|------------------------|
| `depot`     | Depot/warehouse layout |
| `warehouse` | Larger warehouse space |
| `bot4House` | House floor plan       |

---

## Lichtblick Suite

Lichtblick Suite is used for robot visualization and interaction as an alternative to RViz — particularly useful when working with real robots where RMW middleware issues can make RViz unreliable.

Download the latest `.deb` release from the [Lichtblick Suite releases page](https://github.com/Lichtblick-Suite/lichtblick/releases), then install and launch:

```bash
# Install
sudo apt install ./lichtblick_1.22.1_amd64.deb

# Launch from terminal
lichtblick
```

Or find it in your applications menu after installation.

---

## Useful References

- [Nav2 Route Server Docs](https://docs.nav2.org/tutorials/docs/route_server_tools.html)
- [Nav2 Route Server Tool](https://docs.nav2.org/tutorials/docs/route_server_tools/navigation2_route_tool.html)
