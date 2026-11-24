#!/bin/bash
# Usage: ./install_cron.sh [HH:MM]   (default 09:00, local time)
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
T="${1:-09:00}"
H=$((10#${T%%:*})); M=$((10#${T##*:}))
LINE="$M $H * * * cd $DIR && $DIR/.venv/bin/python agent.py >> $DIR/agent.log 2>&1"
( crontab -l 2>/dev/null | grep -v "$DIR/.venv/bin/python agent.py" ; echo "$LINE" ) | crontab -
echo "Installed: $LINE"
