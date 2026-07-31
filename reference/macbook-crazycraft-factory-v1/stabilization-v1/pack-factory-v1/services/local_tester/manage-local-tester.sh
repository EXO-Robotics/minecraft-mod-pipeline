#!/bin/sh
set -eu

label="com.crazycraft.local-tester"
domain="gui/$(id -u)"
source_plist="/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-persistent-orchestrator-v1/stabilization-v1/pack-factory-v1/services/local_tester/com.crazycraft.local-tester.plist"
installed_plist="$HOME/Library/LaunchAgents/$label.plist"
runtime="/Users/blakegrove/Desktop/bedrock-server/program/crazycraft-persistent-orchestrator-v1/stabilization-v1/pack-factory-v1/services/local_tester/runtime"

case "${1:-}" in
  install)
    mkdir -p "$HOME/Library/LaunchAgents" "$runtime"
    /usr/bin/install -m 600 "$source_plist" "$installed_plist"
    /bin/launchctl bootstrap "$domain" "$installed_plist"
    ;;
  start)
    /bin/launchctl kickstart -k "$domain/$label"
    ;;
  stop)
    /bin/launchctl kill SIGTERM "$domain/$label"
    ;;
  uninstall)
    /bin/launchctl bootout "$domain/$label" 2>/dev/null || true
    ;;
  status)
    /bin/launchctl print "$domain/$label"
    ;;
  *)
    printf 'usage: %s {install|start|stop|uninstall|status}\n' "$0" >&2
    exit 64
    ;;
esac
