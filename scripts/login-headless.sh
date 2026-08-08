#!/bin/sh
# `zeus login` for a headless machine.
#
# zeus starts a localhost callback server on a random port and opens the Zepp
# login page via xdg-open. With no GUI, xdg-open falls back to $BROWSER — so we
# point $BROWSER at this script's helper mode, which writes the URL to a file
# (it runs detached, with no terminal of its own). The foreground half watches
# for that file and prints the URL plus SSH-forwarding instructions. Complete
# the login from a machine with a browser; the OAuth redirect travels back
# through the SSH tunnel.
set -e
DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
URL_FILE=${ZEUS_LOGIN_URL_FILE:-/tmp/zeus-login-url.$(id -u)}

if [ "$1" = "--catch-url" ]; then
  # invoked (detached, no tty) by xdg-open as $BROWSER, with the URL as $2
  printf '%s\n' "$2" > "$URL_FILE"
  exit 0
fi

rm -f "$URL_FILE"
ZEUS_LOGIN_URL_FILE=$URL_FILE BROWSER="$DIR/login-headless.sh --catch-url" \
  "$DIR/../.zeus-global/bin/zeus" login &
ZEUS_PID=$!

n=0
while [ ! -s "$URL_FILE" ]; do
  if ! kill -0 "$ZEUS_PID" 2>/dev/null; then
    echo "zeus login exited before producing a login URL" >&2
    exit 1
  fi
  n=$((n + 1))
  if [ "$n" -gt 60 ]; then
    echo "Timed out waiting for the login URL" >&2
    kill "$ZEUS_PID" 2>/dev/null
    exit 1
  fi
  sleep 0.5
done

URL=$(cat "$URL_FILE")
PORT=$(printf '%s' "$URL" | sed -n 's/.*localhost%3A\([0-9]*\).*/\1/p')
printf '\n== zeus login, headless edition ==\n'
printf '\n1. On your laptop, open an SSH tunnel to this machine (leave it running):\n'
printf '     ssh -N -L %s:localhost:%s %s\n' "$PORT" "$PORT" "$(hostname)"
printf '\n2. Open this URL in your laptop browser and log in with your Zepp account:\n\n%s\n\n' "$URL"
printf 'After login the browser redirects to localhost:%s, which the tunnel\n' "$PORT"
printf 'delivers back here. Waiting for the callback ...\n\n'

wait "$ZEUS_PID"
