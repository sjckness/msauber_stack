#!/usr/bin/env bash

# === PATH DINAMICI ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

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

# === SOURCE ROS ===
echo "🤖 Sourcing ROS (${ROS_DISTRO})"
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
poetry env info --path >/dev/null 2>&1 || poetry install --no-root

VENV_PATH="$(poetry env info --path)"
source "${VENV_PATH}/bin/activate"

# === INFO ===
echo
echo "✅ Environment ready"
echo "ROS: ${ROS_DISTRO}"
echo "Workspace: ${WS_DIR}"
echo "Python: $(which python)"
