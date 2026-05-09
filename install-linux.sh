#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 [--action install|uninstall] [--extension-id EXTENSION_ID] [--browser edge|chrome|chromium|brave|all]"
}

ACTION="install"
EXTENSION_ID="olgcbmgnoainnpfchiakbfcidhpcgdmo"
BROWSER="edge"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --action)
      ACTION="${2:-}"
      shift 2
      ;;
    --extension-id)
      EXTENSION_ID="${2:-}"
      shift 2
      ;;
    --browser)
      BROWSER="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Argument inconnu: $1" >&2
      usage
      exit 1
      ;;
  esac
done

case "$ACTION" in
  install|uninstall) ;;
  *)
    echo "Action invalide: $ACTION" >&2
    usage
    exit 1
    ;;
esac

case "$BROWSER" in
  edge|chrome|chromium|brave|all) ;;
  *)
    echo "Navigateur invalide: $BROWSER" >&2
    usage
    exit 1
    ;;
esac

if [[ "$ACTION" == "install" && ! "$EXTENSION_ID" =~ ^[a-p]{32}$ ]]; then
  echo "Extension ID invalide. Il doit contenir 32 caracteres entre a et p." >&2
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
RUNTIME_DIR="$REPO_ROOT/runtime"
VENV_DIR="$RUNTIME_DIR/.venv"
REQUIREMENTS_PATH="$RUNTIME_DIR/requirements.txt"
NATIVE_DIR="$REPO_ROOT/extension/NativesMessages"
HOST_NAME="com.amadeus.security_hub"
LAUNCHER_PATH="$NATIVE_DIR/run-native-host.sh"
MANIFEST_PATH="$NATIVE_DIR/$HOST_NAME.linux.json"

browser_manifest_dir() {
  case "$1" in
    edge)
      echo "$HOME/.config/microsoft-edge/NativeMessagingHosts"
      ;;
    chrome)
      echo "$HOME/.config/google-chrome/NativeMessagingHosts"
      ;;
    chromium)
      echo "$HOME/.config/chromium/NativeMessagingHosts"
      ;;
    brave)
      echo "$HOME/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts"
      ;;
  esac
}

selected_browsers() {
  if [[ "$BROWSER" == "all" ]]; then
    echo "edge chrome chromium brave"
  else
    echo "$BROWSER"
  fi
}

if [[ "$ACTION" == "uninstall" ]]; then
  for browser in $(selected_browsers); do
    target_dir="$(browser_manifest_dir "$browser")"
    rm -f "$target_dir/$HOST_NAME.json"
  done

  rm -f "$MANIFEST_PATH"

  echo "Desinstallation Linux terminee."
  echo "Host Native Messaging retire: $HOST_NAME"
  exit 0
fi

if [[ ! -f "$REQUIREMENTS_PATH" ]]; then
  echo "requirements.txt introuvable: $REQUIREMENTS_PATH" >&2
  exit 1
fi

mkdir -p "$NATIVE_DIR"

if [[ ! -f "$LAUNCHER_PATH" ]]; then
  echo "Launcher introuvable: $LAUNCHER_PATH" >&2
  exit 1
fi

chmod +x "$LAUNCHER_PATH"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Python est introuvable. Installe Python 3 puis relance cet installateur." >&2
  exit 1
fi

"$PYTHON_BIN" -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install --upgrade -r "$REQUIREMENTS_PATH"

cat > "$MANIFEST_PATH" <<EOF
{
  "name": "$HOST_NAME",
  "description": "Amadeus Security Hub native messaging host",
  "path": "$LAUNCHER_PATH",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://$EXTENSION_ID/"
  ]
}
EOF

install_manifest() {
  local target_dir="$1"
  mkdir -p "$target_dir"
  cp "$MANIFEST_PATH" "$target_dir/$HOST_NAME.json"
}

case "$BROWSER" in
  edge)
    install_manifest "$(browser_manifest_dir edge)"
    ;;
  chrome)
    install_manifest "$(browser_manifest_dir chrome)"
    ;;
  chromium)
    install_manifest "$(browser_manifest_dir chromium)"
    ;;
  brave)
    install_manifest "$(browser_manifest_dir brave)"
    ;;
  all)
    for browser in $(selected_browsers); do
      install_manifest "$(browser_manifest_dir "$browser")"
    done
    ;;
esac

echo "Installation Linux terminee."
echo "Virtualenv: $VENV_DIR"
echo "Host Native Messaging: $HOST_NAME"
echo "Manifest source: $MANIFEST_PATH"
echo "Extension autorisee: chrome-extension://$EXTENSION_ID/"
