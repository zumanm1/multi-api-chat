#!/bin/bash
set -e

# Management helper for Multi-API Chat
# Usage:
#   ./manage.sh start   - start backend+frontend using start_app.sh
#   ./manage.sh stop    - stop using PID files or ports (stop_app.sh)
#   ./manage.sh status  - show status (PIDs and listening ports)

CMD=${1:-help}

case "$CMD" in
  start)
    chmod +x start_app.sh
    ./start_app.sh
    ;;
  stop)
    chmod +x stop_app.sh
    ./stop_app.sh
    ;;
  status)
    echo "--- PIDs ---"
    [ -f logs/backend.pid ] && echo "Backend PID: $(cat logs/backend.pid)" || echo "Backend PID: (none)"
    [ -f logs/frontend.pid ] && echo "Frontend PID: $(cat logs/frontend.pid)" || echo "Frontend PID: (none)"
    echo "--- Listening sockets (7001/7002) ---"
    if command -v ss >/dev/null 2>&1; then
      ss -tulpn | grep -E '(:7001|:7002)' || true
    else
      netstat -tulpn 2>/dev/null | grep -E '(:7001|:7002)' || true
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|status}"
    exit 1
    ;;
 esac

