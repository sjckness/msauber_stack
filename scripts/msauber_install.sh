#!/usr/bin/env bash

set -euo pipefail

log() {
  echo
  echo "==> $1"
}

fail() {
  echo "ERRORE: $1" >&2
  exit 1
}

require_command() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    fail "Comando richiesto non trovato: ${cmd}"
  fi
}

run_apt_update() {
  local apt_log
  apt_log="$(mktemp)"

  if sudo apt-get update 2>&1 | tee "${apt_log}"; then
    rm -f "${apt_log}"
    return
  fi

  echo >&2
  echo "apt-get update ha fallito." >&2

  if grep -q "ppa.launchpadcontent.net/nschloe/waybar" "${apt_log}"; then
    cat >&2 <<'EOF'
Sembra esserci una PPA esterna non più valida:
  https://ppa.launchpadcontent.net/nschloe/waybar/ubuntu

Per continuare, disattiva o rimuovi quella sorgente APT e rilancia lo script.
Di solito il file si trova in uno di questi percorsi:
  /etc/apt/sources.list.d/
  /etc/apt/sources.list

Comandi utili:
  grep -R "nschloe/waybar" /etc/apt/sources.list /etc/apt/sources.list.d 2>/dev/null
  sudo rm /etc/apt/sources.list.d/<file-waybar>.list
  sudo apt-get update
EOF
  else
    echo "Controlla le sorgenti APT configurate nel sistema e correggi gli errori mostrati sopra." >&2
  fi

  rm -f "${apt_log}"
  exit 1
}

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
  first_distro="$(
    find /opt/ros -mindepth 1 -maxdepth 1 -type d 2>/dev/null \
      | sort \
      | head -n 1 \
      | xargs -r basename
  )"
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

require_command sudo
require_command apt-get
require_command find
require_command mktemp
require_command tee
require_command grep

# === SOURCE ROS ===
set +u
source "${ROS_SETUP}"
set -u

clean_stale_colcon_cache() {
  local pkg
  for pkg in yolo_msgs yolo_ros yolo_bringup; do
    if [[ ! -d "${SRC_DIR}/yolo_ros/${pkg}" ]] && [[ -d "${WS_DIR}/build/${pkg}" || -d "${WS_DIR}/install/${pkg}" ]]; then
      echo "🧹 Removing stale colcon artifacts for ${pkg}"
      rm -rf "${WS_DIR}/build/${pkg}" "${WS_DIR}/install/${pkg}"
    fi
  done
}

# === SYSTEM + ROS PACKAGES ===
log "Installing system and ROS packages"

run_apt_update
sudo apt-get install -y \
  build-essential \
  curl \
  git \
  python3-colcon-ros \
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
log "Checking Poetry"

if ! command -v poetry &> /dev/null; then
  require_command pipx
  echo "Installing Poetry..."
  pipx ensurepath
  pipx install poetry

  # Make Poetry visible in the current shell too.
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "Using $(poetry --version)"

# === ROSDEP SETUP ===
log "Setting up rosdep"

if [[ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]]; then
  sudo rosdep init || true
fi

rosdep update --rosdistro "${ROS_DISTRO_NAME}"

# === INSTALL PYTHON DEPS ===
log "Installing Python dependencies via Poetry"

cd "${WS_DIR}"
poetry install --no-root
poetry run python -m pip install empy catkin-pkg lark

# === INSTALL ROS DEPENDENCIES FROM SRC ===
log "Installing ROS dependencies from src"
echo "Skipping rosdep key: ament_python"

rosdep install \
  --from-paths "${SRC_DIR}" \
  --ignore-src \
  --rosdistro "${ROS_DISTRO_NAME}" \
  --skip-keys "ament_python" \
  -r -y

# === BUILD WORKSPACE ===
log "Building workspace"

clean_stale_colcon_cache
colcon build --symlink-install

# === DONE ===
cat <<EOF

INSTALLAZIONE COMPLETATA

EOF
