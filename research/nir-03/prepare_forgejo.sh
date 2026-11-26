#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "usage: prepare_forgejo.sh /path/to/forgejo-17.0.2 /tmp/fresh-forgejo-state [port]" >&2
  exit 2
fi
binary=$(realpath "$1")
state=$(realpath -m "$2")
port=${3:-30300}
[[ -x "$binary" ]] || { echo "Forgejo binary must be executable" >&2; exit 2; }
version=$("$binary" --version 2>&1)
[[ "$version" == *"version 17.0.2+"* ]] || { echo "expected Forgejo 17.0.2" >&2; exit 2; }
[[ ! -e "$state" ]] || { echo "state path already exists; choose a fresh disposable path" >&2; exit 2; }
[[ "$port" =~ ^[0-9]+$ ]] && (( port >= 1024 && port <= 65535 )) || { echo "port must be between 1024 and 65535" >&2; exit 2; }
umask 077
mkdir -p "$state/custom/conf" "$state/data" "$state/repositories"
export NIR03_BOOTSTRAP_STATE="$state" NIR03_BOOTSTRAP_PORT="$port"
python3 - <<'PY'
import os, secrets
from pathlib import Path
root=Path(os.environ['NIR03_BOOTSTRAP_STATE'])
port=int(os.environ['NIR03_BOOTSTRAP_PORT'])
secret=lambda: secrets.token_urlsafe(48)
config=f'''APP_NAME = NIR-03 Disposable Forgejo
RUN_MODE = prod

[database]
DB_TYPE = sqlite3
PATH = {root}/data/forgejo.db

[repository]
ROOT = {root}/repositories

[server]
DOMAIN = 127.0.0.1
ROOT_URL = http://127.0.0.1:{port}/
HTTP_ADDR = 127.0.0.1
HTTP_PORT = {port}
DISABLE_SSH = true
LFS_START_SERVER = false
APP_DATA_PATH = {root}/data

[service]
DISABLE_REGISTRATION = true
REQUIRE_SIGNIN_VIEW = true
ENABLE_NOTIFY_MAIL = false

[security]
INSTALL_LOCK = true
SECRET_KEY = {secret()}
INTERNAL_TOKEN = {secret()}

[session]
PROVIDER = memory

[mailer]
ENABLED = false

[openid]
ENABLE_OPENID_SIGNIN = false

[actions]
ENABLED = false

[packages]
ENABLED = false

[log]
MODE = console
LEVEL = Warn
'''
conf=root/'custom/conf/app.ini'
conf.write_text(config,encoding='utf-8')
conf.chmod(0o600)
PY
conf="$state/custom/conf/app.ini"
"$binary" --work-path "$state" --config "$conf" migrate >/dev/null
"$binary" --work-path "$state" --config "$conf" admin user create \
  --username researcher --random-password --email researcher@localhost \
  --admin --must-change-password=false >/dev/null
"$binary" --work-path "$state" --config "$conf" admin user generate-access-token \
  --username researcher --token-name nir03-disposable-pilot \
  --scopes write:repository,write:user --raw > "$state/api-token"
chmod 600 "$state/api-token"
printf 'Prepared disposable Forgejo state: %s\n' "$state"
printf 'Forgejo version: 17.0.2; bind address: 127.0.0.1; port: %s\n' "$port"
printf 'Token file: %s/api-token (mode 0600; do not print or commit)\n' "$state"
printf 'Start with: %q --work-path %q --config %q web\n' "$binary" "$state" "$conf"
