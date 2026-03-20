# ROSConDE2025_navigation_workshop

This repository contains materials, example configurations, and Docker setups used in the ROSConDE 2025 navigation workshop.

For full workshop documentation, walkthroughs, and generated pages, see the hosted GitHub Pages site:

- Workshop documentation (GitHub Pages): https://pschnattinger.github.io/roscon_de_2025_navigation_workshop/index.html

Quick links
- Docs (rendered): https://pschnattinger.github.io/roscon_de_2025_navigation_workshop/index.html
- Source docs (RST): `introduction/`, `mapping/`, `navigation/`, `turtlebot4/`, etc.

Getting started
- Inspect the `simulated_turtlebot/`, `turtlebot_navigation/`, and `foxglove_web_bridge/` folders for Docker-compose and Dockerfile examples used in the workshop.
- See `configs/` for example `nav2` and localization YAML configuration files.

Repository contents (high level)
- `configs/` — nav2 and localization example configs
- `simulated_turtlebot/`, `turtlebot_navigation/` — Docker setups and simulation assets
- `docs/`, `introduction/`, `mapping/`, `navigation/`, `turtlebot4/`, `roadmap/` — workshop documentation sources (RST) and built HTML under `docs/_build/html`
- `envs/` — example maps and environment files
Contributing
- Contributions and fixes are welcome. Please open an issue or a pull request describing changes and the reason.

License
- See the `LICENSE` file in this repository for license terms.

If you'd like, I can also add badges, a short table of contents, or a local preview command for the docs.


Workflow:                                                                                                                               
  # 1. Start the mapping session                                                                                                          
  docker compose -f docker-compose-slam.yaml up                                                                                           
                                                                                                                                          
  # 2. Teleoperate the robot to explore the house                                                                                         
  docker exec -it ros2-turtlebot4-slam-kilted ros2 run teleop_twist_keyboard teleop_twist_keyboard  --ros-args -p stamped:=true                                        
                                                                                                                                          
  # 3. When the map looks complete in RViz, save it                                                                                       
  docker exec ros2-turtlebot4-slam-kilted ros2 run nav2_map_server map_saver_cli -f /maps/bot4house                                           
                                                                                                                                          
  This saves house.yaml and house.pgm directly into ./turtlebot4/turtlebot4_navigation/maps/. 


