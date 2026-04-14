FROM osrf/ros:jazzy-desktop-full

ENV DEBIAN_FRONTEND=noninteractive \
    ROS_DISTRO=jazzy \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PYTHONUNBUFFERED=1

SHELL ["/bin/bash", "-lc"]

WORKDIR /ros2_ws

COPY pyproject.toml poetry.lock ./
COPY scripts ./scripts
COPY src ./src

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    pipx \
    ros-jazzy-ackermann-steering-controller \
    ros-jazzy-controller-manager \
    ros-jazzy-foxglove-bridge \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-joint-state-broadcaster \
    ros-jazzy-nav2-lifecycle-manager \
    ros-jazzy-nav2-map-server \
    ros-jazzy-nav2-msgs \
    ros-jazzy-nav2-planner \
    ros-jazzy-nav2-smac-planner \
    ros-jazzy-nav2-navfn-planner \
    ros-jazzy-ros-gz \
    python3-colcon-common-extensions \
    python3-colcon-ros \
    python3-pip \
    python3-rosdep \
    python3-vcstool \
    python3-venv \
    qtbase5-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pipx install poetry \
    && ln -sf /root/.local/bin/poetry /usr/local/bin/poetry

RUN rosdep init 2>/dev/null || true \
    && rosdep update --rosdistro "${ROS_DISTRO}"

RUN apt-get update \
    && source "/opt/ros/${ROS_DISTRO}/setup.bash" \
    && rosdep install \
      --from-paths src \
      --ignore-src \
      --rosdistro "${ROS_DISTRO}" \
      --skip-keys "ament_python gz-sim8 controller_manager joint_state_publisher_gui joint_state_broadcaster ackermann_steering_controller foxglove_bridge nav2_map_server nav2_planner nav2_lifecycle_manager nav2_msgs nav2_smac_planner nav2_navfn_planner" \
      -r -y

RUN poetry install --no-root

# Install PyTorch (CPU) + ultralytics outside of poetry to avoid numpy/system-package conflicts
RUN pip install \
    "torch==2.4.0+cpu" \
    "torchvision==0.19.0+cpu" \
    --index-url https://download.pytorch.org/whl/cpu \
    --break-system-packages --no-deps \
  && pip install \
    "ultralytics==8.4.37" \
    "ultralytics-thop>=2.0.18" \
    requests \
    --break-system-packages --no-deps

RUN source "/ros2_ws/.venv/bin/activate" \
    && source "/opt/ros/${ROS_DISTRO}/setup.bash" \
    && colcon build --symlink-install

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /root/.bashrc \
    && echo "source /ros2_ws/.venv/bin/activate 2>/dev/null || true" >> /root/.bashrc \
    && echo "source /ros2_ws/install/setup.bash 2>/dev/null || true" >> /root/.bashrc

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
