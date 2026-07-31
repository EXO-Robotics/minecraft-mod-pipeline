#!/bin/sh
set -eu

label="com.crazycraft.factory-router"
domain="gui/$(id -u)"
root="/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-persistent-orchestrator-v1/stabilization-v1/pack-factory-v1/services/factory_router"
source_plist="$root/com.crazycraft.factory-router.plist"
installed_plist="$HOME/Library/LaunchAgents/$label.plist"

case "${1:-}" in
  install)
    mkdir -p "$HOME/Library/LaunchAgents" "$root/runtime"
    /usr/bin/plutil -lint "$source_plist"
    /usr/bin/install -m 600 "$source_plist" "$installed_plist"
    /bin/launchctl bootstrap "$domain" "$installed_plist"
    ;;
  start)
    /bin/launchctl kickstart "$domain/$label"
    ;;
  stop)
    /bin/launchctl bootout "$domain/$label" 2>/dev/null || true
    ;;
  status)
    /bin/launchctl print "$domain/$label"
    ;;
  run-once)
    /opt/homebrew/bin/python3 "$root/factory_router.py" \
      --config "$root/factory-router-config.json" --run-once
    ;;
  router-status)
    /opt/homebrew/bin/python3 "$root/factory_router.py" \
      --config "$root/factory-router-config.json" --status
    ;;
  *)
    printf 'usage: %s {install|start|stop|status|run-once|router-status}\n' "$0" >&2
    exit 64
    ;;
esac
