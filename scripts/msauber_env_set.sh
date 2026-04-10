#!/usr/bin/env bash

# === PATH DINAMICI ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

sanitize_snap_gui_env() {
  if [[ "${SNAP_NAME:-}" == "code" || "${GTK_PATH:-}" == /snap/code/* || "${GTK_EXE_PREFIX:-}" == /snap/code/* ]]; then
    echo "⚠️ Cleaning Snap/VS Code GUI environment for Gazebo"
    unset GIO_MODULE_DIR
    unset GTK_EXE_PREFIX
    unset GTK_IM_MODULE_FILE
    unset GTK_PATH
    unset SNAP
    unset SNAP_ARCH
    unset SNAP_COMMON
    unset SNAP_CONTEXT
    unset SNAP_COOKIE
    unset SNAP_DATA
    unset SNAP_EUID
    unset SNAP_INSTANCE_NAME
    unset SNAP_LAUNCHER_ARCH_TRIPLET
    unset SNAP_LIBRARY_PATH
    unset SNAP_NAME
    unset SNAP_REAL_HOME
    unset SNAP_REVISION
    unset SNAP_UID
    unset SNAP_USER_COMMON
    unset SNAP_USER_DATA
    hash -r
  fi
}

# === DETECT ROS ===
if [[ -d /opt/ros/jazzy ]]; then
  ROS_DISTRO="jazzy"
else
  ROS_DISTRO="$(ls /opt/ros | head -n 1)"
fi

ROS_SETUP="/opt/ros/${ROS_DISTRO}/setup.bash"

if [[ ! -f "${ROS_SETUP}" ]]; then
  echo "❌ ROS setup not found"
  return
fi

# === RESET ENV (clean state) ===
unset PYTHONPATH
unset AMENT_PREFIX_PATH
unset CMAKE_PREFIX_PATH
unset COLCON_PREFIX_PATH
unset ROS_PACKAGE_PATH
unset ROS_NAMESPACE
unset COLCON_CURRENT_PREFIX
unset _COLCON_PREFIX_CHAIN_BASH_SOURCE
unset _COLCON_PREFIX_CHAIN_SH_SOURCE
unset VIRTUAL_ENV

if [[ ":$PATH:" == *":${WS_DIR}/.venv/bin:"* ]]; then
  PATH="$(echo ":$PATH:" | sed "s#:${WS_DIR}/.venv/bin:##g" | sed 's/^://; s/:$//')"
  export PATH
fi

# === SOURCE ROS ===
echo "🤖 Sourcing ROS (${ROS_DISTRO})"
sanitize_snap_gui_env
source "${ROS_SETUP}"

# === SOURCE WORKSPACE ===
if [[ -f "${WS_DIR}/install/setup.bash" ]]; then
  echo "📦 Sourcing workspace"
  source "${WS_DIR}/install/setup.bash"
else
  echo "⚠️ Workspace not built yet"
fi

# === POETRY ENV ===
if ! command -v poetry &> /dev/null; then
  echo "❌ Poetry not found"
  return
fi

echo "🐍 Activating Poetry environment"
cd "${WS_DIR}"

poetry env info --path >/dev/null 2>&1 || poetry install --no-root

VENV_PATH="$(poetry env info --path)"
if [[ -z "${VENV_PATH}" || ! -x "${VENV_PATH}/bin/python" ]]; then
  echo "❌ Poetry virtualenv not found or invalid"
  return
fi

VENV_SITE_PACKAGES="$("${VENV_PATH}/bin/python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"

export PATH="${VENV_PATH}/bin:${PATH}"
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}${VENV_SITE_PACKAGES}"

# === INFO ===
echo
echo "✅ Environment ready"
echo "ROS: ${ROS_DISTRO}"
echo "Workspace: ${WS_DIR}"
echo "Python: $(which python)"
echo "ros2: $(which ros2)"
