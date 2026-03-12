#!/usr/bin/env bash
# Quick killer for msauber simulation stack.

set -euo pipefail

# Graceful stop first.
pkill -INT -f 'gz-sim|gz sim|ros_gz_sim' || true
pkill -INT -f 'ros2 launch.*msauber_bringup' || true
pkill -INT -f 'foxglove_bridge|teleop_twist_bridge' || true

sleep 1

# Force stop anything still alive.
pkill -KILL -f 'gz-sim|gz sim|ros_gz_sim' || true
pkill -KILL -f 'ros2 launch.*msauber_bringup' || true
pkill -KILL -f 'foxglove_bridge|teleop_twist_bridge' || true
