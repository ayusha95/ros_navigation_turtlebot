# Copyright (c) 2025 Open Navigation LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from pathlib import Path
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnShutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

# Map and robot spawn pose for house world
MAP_TYPE = "bot4House"
ROBOT_POSE = {"x": 0.0, "y": 0.0, "z": 0.01, "R": 0.00, "P": 0.00, "Y": 0.0}


def generate_launch_description() -> LaunchDescription:
    sim_dir = get_package_share_directory("nav2_minimal_tb4_sim")
    desc_dir = get_package_share_directory("nav2_minimal_tb4_description")
    slam_toolbox_dir = get_package_share_directory("slam_toolbox")

    robot_sdf = os.path.join(desc_dir, "urdf", "standard", "turtlebot4.urdf.xacro")
    world = os.path.join(sim_dir, "worlds", f"{MAP_TYPE}.sdf")

    headless = LaunchConfiguration("headless")

    declare_headless_cmd = DeclareLaunchArgument(
        "headless", default_value="False", description="Whether to execute gzclient"
    )

    # Start the simulation
    world_sdf = tempfile.mktemp(prefix="nav2_", suffix=".sdf")
    world_sdf_xacro = ExecuteProcess(
        cmd=["xacro", "-o", world_sdf, ["headless:=", headless], world]
    )
    start_gazebo_server_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py"
            )
        ),
        launch_arguments={"gz_args": ["-r -s ", world_sdf]}.items(),
    )

    remove_temp_sdf_file = RegisterEventHandler(
        event_handler=OnShutdown(
            on_shutdown=[OpaqueFunction(function=lambda _: os.remove(world_sdf))]
        )
    )

    set_env_vars_resources = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH", os.path.join(sim_dir, "worlds")
    )

    start_gazebo_client_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py"
            )
        ),
        condition=IfCondition(PythonExpression(["not ", headless])),
        launch_arguments={"gz_args": ["-v4 -g "]}.items(),
    )

    spawn_robot_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(sim_dir, "launch", "spawn_tb4.launch.py")
        ),
        launch_arguments={
            "use_sim_time": "True",
            "robot_sdf": robot_sdf,
            "x_pose": str(ROBOT_POSE["x"]),
            "y_pose": str(ROBOT_POSE["y"]),
            "z_pose": str(ROBOT_POSE["z"]),
            "roll": str(ROBOT_POSE["R"]),
            "pitch": str(ROBOT_POSE["P"]),
            "yaw": str(ROBOT_POSE["Y"]),
        }.items(),
    )

    start_robot_state_publisher_cmd = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "use_sim_time": True,
                "robot_description": Command(["xacro", " ", robot_sdf]),
            }
        ],
    )

    # Start RViz for visualization using slam_toolbox's config (shows the map being built)
    rviz_cmd = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=[
            "-d",
            os.path.join(slam_toolbox_dir, "rviz", "mapper_params_online_sync.rviz"),
        ],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )

    # Start SLAM Toolbox for mapping (online synchronous mode)
    slam_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_toolbox_dir, "launch", "online_sync_launch.py")
        ),
        launch_arguments={"use_sim_time": "True"}.items(),
    )

    set_env_vars_resources2 = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH", str(Path(os.path.join(desc_dir)).parent.resolve())
    )

    ld = LaunchDescription()
    ld.add_action(declare_headless_cmd)
    ld.add_action(set_env_vars_resources)
    ld.add_action(world_sdf_xacro)
    ld.add_action(remove_temp_sdf_file)
    ld.add_action(start_gazebo_server_cmd)
    ld.add_action(start_gazebo_client_cmd)
    ld.add_action(spawn_robot_cmd)
    ld.add_action(start_robot_state_publisher_cmd)
    ld.add_action(rviz_cmd)
    ld.add_action(slam_cmd)
    ld.add_action(set_env_vars_resources2)
    return ld
