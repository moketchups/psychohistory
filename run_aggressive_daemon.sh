#!/bin/bash
# Aggressive trading daemon - runs until $1M or $0
# Paper trading test

export ALPACA_API_KEY=PKY4VXOV6JMYJH2WGFK7NKNL5P
export ALPACA_SECRET_KEY=iUVcndotdXd61JPnzwKWKUzAF5YDYc1v4V6nhfVPKXV
export PYTHONPATH=/Users/jamienucho/psychohistory

LOG_FILE="/Users/jamienucho/psychohistory/data/aggressive_daemon.log"
PID_FILE="/Users/jamienucho/psychohistory/data/daemon.pid"

echo "Starting Aggressive Trading Daemon at $(date)" >> "$LOG_FILE"
echo "Target: \$1,000,000 or \$0" >> "$LOG_FILE"
echo "Mode: AGGRESSIVE - Big positions, wide stops, let winners run" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"

# Run the daemon with many cycles
python3 -m psychohistory daemon run --cycles 100000 2>&1 | tee -a "$LOG_FILE" &
DAEMON_PID=$!
echo $DAEMON_PID > "$PID_FILE"

echo "Daemon started with PID: $DAEMON_PID"
echo "Log file: $LOG_FILE"
echo "To stop: kill \$(cat $PID_FILE)"

# Wait for daemon
wait $DAEMON_PID
