#!/bin/bash
# FIELD EXECUTION MODE - 7D gradient direct translation
# 48-hour aggressive field execution run
# Paper trading account

export ALPACA_API_KEY=PKY4VXOV6JMYJH2WGFK7NKNL5P
export ALPACA_SECRET_KEY=iUVcndotdXd61JPnzwKWKUzAF5YDYc1v4V6nhfVPKXV
export PYTHONPATH=/Users/jamienucho/psychohistory

LOG_FILE="/Users/jamienucho/psychohistory/data/berserker.log"
PID_FILE="/Users/jamienucho/psychohistory/data/daemon.pid"

# Kill any existing daemon
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    kill $OLD_PID 2>/dev/null && echo "Killed old daemon PID $OLD_PID"
    sleep 2
fi

echo "=== FIELD EXECUTION MODE ===" >> "$LOG_FILE"
echo "Started: $(date)" >> "$LOG_FILE"
echo "Deadline: 48 hours" >> "$LOG_FILE"
echo "Target: \$1,000,000" >> "$LOG_FILE"
echo "Interval: 5 seconds" >> "$LOG_FILE"
echo "Position sizing: field_magnitude * 0.45 (direct)" >> "$LOG_FILE"
echo "Exit conditions: field direction flip + gradient collapse ONLY" >> "$LOG_FILE"
echo "Stop loss: DISABLED (field owns exits)" >> "$LOG_FILE"
echo "Take profit: DISABLED (field owns exits)" >> "$LOG_FILE"
echo "Constraint modifiers: ALL DISABLED (field dimensions encode risk)" >> "$LOG_FILE"
echo "Cooldowns: NONE" >> "$LOG_FILE"
echo "Max per symbol: 45% | Concurrent: 3 | Min signal: 70% density" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"

# 48 hours * 3600 sec/hour / 5 sec = 34,560 cycles
# Buffer to 35,000
# Crypto only until market opens (24/7 trading)
python3 -m psychohistory daemon run --interval 5 --cycles 35000 --symbols SOL,AVAX,LINK,DOGE,MATIC 2>&1 | tee -a "$LOG_FILE" &
DAEMON_PID=$!
echo $DAEMON_PID > "$PID_FILE"

echo "Daemon PID: $DAEMON_PID" >> "$LOG_FILE"
echo "Daemon started: PID $DAEMON_PID"
echo "Log: $LOG_FILE"
echo "To stop: kill $DAEMON_PID"
wait $DAEMON_PID
