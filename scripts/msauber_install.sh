#!/usr/bin/env bash

set -euo pipefail

# === PATH SETUP ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SRC_DIR="${WS_DIR}/src"

# === DETECT ROS DISTRO ===
detect_ros_distro() {
  if [[ -n "${ROS_DISTRO:-}" ]]; then
    echo "${ROS_DISTRO}"
    return
  fi

  if [[ -d /opt/ros/jazzy ]]; then
    echo "jazzy"
    return
  fi

  local first_distro
  first_distro="$(find /opt/ros -mindepth 1 -maxdepth 1 -type d 2>/dev/null | head -n 1 | xargs -r basename)"
  if [[ -n "${first_distro}" ]]; then
    echo "${first_distro}"
    return
  fi

  echo "Impossibile determinare ROS_DISTRO" >&2
  exit 1
}

ROS_DISTRO_NAME="$(detect_ros_distro)"
ROS_SETUP="/opt/ros/${ROS_DISTRO_NAME}/setup.bash"

if [[ ! -f "${ROS_SETUP}" ]]; then
  echo "File non trovato: ${ROS_SETUP}" >&2
  exit 1
fi

echo "Workspace: ${WS_DIR}"
echo "ROS_DISTRO: ${ROS_DISTRO_NAME}"
echo

# === SOURCE ROS ===
set +u
source "${ROS_SETUP}"
set -u

clean_stale_colcon_cache() {
  local pkg
  local stale_source="${WS_DIR}/src/yolo_ros/yolo_msgs"
  local current_source="${WS_DIR}/src/yolo_ros_repo/yolo_msgs"

  if [[ -d "${current_source}" && ! -d "${stale_source}" ]]; then
    for pkg in yolo_msgs yolo_ros yolo_bringup; do
      if [[ -d "${WS_DIR}/build/${pkg}" || -d "${WS_DIR}/install/${pkg}" ]]; then
        echo "🧹 Removing stale colcon artifacts for ${pkg} (old source path src/yolo_ros/...)"
        rm -rf "${WS_DIR}/build/${pkg}" "${WS_DIR}/install/${pkg}"
      fi
    done
  fi
}

# === SYSTEM + ROS PACKAGES ===
echo "🔧 Installing system and ROS packages..."

sudo apt-get update
sudo apt-get install -y \
  build-essential \
  git \
  python3-pip \
  python3-venv \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  pipx \
  "ros-${ROS_DISTRO_NAME}-rclpy" \
  "ros-${ROS_DISTRO_NAME}-tf2-ros" \
  "ros-${ROS_DISTRO_NAME}-std-msgs"

# === INSTALL POETRY ===
echo "Checking Poetry..."

if ! command -v poetry &> /dev/null; then
  echo "Installing Poetry..."
  pipx ensurepath
  pipx install poetry

  # fix PATH per lo script corrente
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "Using $(poetry --version)"

# === ROSDEP SETUP ===
echo "Setting up rosdep..."

if [[ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]]; then
  sudo rosdep init || true
fi

rosdep update

# === INSTALL PYTHON DEPS ===
echo "Installing Python dependencies via Poetry..."

cd "${WS_DIR}"
poetry install --no-root
poetry run python -m pip install empy catkin-pkg lark

# === INSTALL ROS DEPENDENCIES FROM SRC ===
echo "Installing ROS dependencies from src..."
echo "Skipping rosdep key: ament_python"

rosdep install \
  --from-paths "${SRC_DIR}" \
  --ignore-src \
  --rosdistro "${ROS_DISTRO_NAME}" \
  --skip-keys "ament_python" \
  -r -y

# === BUILD WORKSPACE ===
echo "🔨 Building workspace..."

clean_stale_colcon_cache
colcon build --symlink-install

# === DONE ===
cat <<EOF

INSTALLAZIONE COMPLETATA

EOF
