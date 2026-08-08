#!/bin/sh
# `zeus login` for a headless machine.
#
# zeus starts a localhost callback server on a random port and opens the Zepp
# login page via xdg-open. With no GUI, xdg-open falls back to $BROWSER — so we
# point $BROWSER back at this script, which prints the URL and SSH-forwarding
# instructions instead of opening anything. Complete the login from a machine
# with a browser; the OAuth redirect travels back through the SSH tunnel.
set -e
DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)

if [ -n "$1" ]; then
  # invoked by xdg-open as $BROWSER, with the login URL as $1
  URL=$1
  PORT=$(printf '%s' "$URL" | sed -n 's/.*localhost%3A\([0-9]*\).*/\1/p')
  {
    printf '\n== zeus login, headless edition ==\n'
    printf '\n1. On your laptop, open an SSH tunnel to this machine (leave it running):\n'
    printf '     ssh -N -L %s:localhost:%s %s\n' "$PORT" "$PORT" "$(hostname)"
    printf '\n2. Open this URL in your laptop browser and log in with your Zepp account:\n\n%s\n\n' "$URL"
    printf 'After login the browser redirects to localhost:%s, which the tunnel\n' "$PORT"
    printf 'delivers back here. zeus will then print "Login success".\n\n'
  } > /dev/tty 2>/dev/null || printf 'Open this URL after forwarding port %s:\n%s\n' "$PORT" "$URL"
  exit 0
fi

BROWSER="$DIR/login-headless.sh" exec "$DIR/../.zeus-global/bin/zeus" login
