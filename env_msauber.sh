# env_msauber.sh

ROS_DISTRO_DIR="/opt/ros/jazzy"
VENV_DIR="$HOME/my_py_venv"
WS_DIR="$HOME/dev_ws/msauber_stack"

unset PYTHONPATH
unset AMENT_PREFIX_PATH
unset CMAKE_PREFIX_PATH
unset COLCON_PREFIX_PATH
unset ROS_PACKAGE_PATH
unset ROS_NAMESPACE
unset COLCON_CURRENT_PREFIX
unset _COLCON_PREFIX_CHAIN_BASH_SOURCE
unset _COLCON_PREFIX_CHAIN_SH_SOURCE

if [ ! -f "$ROS_DISTRO_DIR/setup.zsh" ]; then
  echo "ROS setup not found"
  return
fi

if [ ! -f "$VENV_DIR/bin/activate" ]; then
  echo "Venv not found"
  return
fi

source "$ROS_DISTRO_DIR/setup.zsh"
source "$VENV_DIR/bin/activate"

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
export PYTHONPATH="$VENV_DIR/lib/python${PY_VER}/site-packages:$PYTHONPATH"

if [ -f "$WS_DIR/install/setup.zsh" ]; then
  source "$WS_DIR/install/setup.zsh"
fi

echo "MSauber environment ready"
echo "python: $(which python3)"
