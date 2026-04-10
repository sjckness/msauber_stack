#!/bin/bash

SESSION="ros2_mpc_2"
WORKDIR="$HOME/dev_ws/msauber_stack"
BASE_CMD="cd ${WORKDIR} && source scripts/msauber_env_set.sh && clear"

# If the session already exists, kill it to start fresh (avoids re-splitting on reuse).
if tmux has-session -t "${SESSION}" 2>/dev/null; then
  tmux kill-session -t "${SESSION}"
fi

# Create session and lay out a 2x2 grid (4 panes).
tmux new-session -d -s "${SESSION}" -n main
tmux split-window -h -t "${SESSION}:0"          # panes 0 (left) and 1 (right)
tmux split-window -v -t "${SESSION}:0.0"        # split pane 0 -> panes 0 (top-left) and 2 (bottom-left)
tmux split-window -v -t "${SESSION}:0.1"        # split pane 1 -> panes 1 (top-right) and 3 (bottom-right)
tmux select-layout -t "${SESSION}:0" tiled      # ensure a balanced 2x2 grid

# Commands for each pane (customize as needed).
declare -a CMDS=(
  "${BASE_CMD} && echo 'Pane 0 ready: bringup'"
  "${BASE_CMD} && echo 'Pane 1 ready: gazebo'"
  "${BASE_CMD} && echo 'Pane 2 ready: mpc'"
  "${BASE_CMD} && echo 'Pane 3 ready: debug'"
)

for i in {0..3}; do
  tmux send-keys -t "${SESSION}:0.${i}" "${CMDS[$i]}" C-m
done

# Attach to the prepared session.
tmux attach -t "${SESSION}"
