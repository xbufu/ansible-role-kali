#!/usr/bin/env bash
# Export Burp Suite Community's CA certificate as PEM.
#
# Usage: burp_export_ca.sh <output.pem>
#
# Burp Community has no headless mode, so:
#  1. A headless start that reads "y" (accept the licence) and an empty line (Community
#     Edition, no licence key) creates the CA in the Java
#     preferences, then fails to open its GUI; it is stopped once the CA is stored.
#  2. Burp then runs under Xvfb and its startup dialogs are clicked at fixed spots of a
#     1280x1024 screen until the proxy serves the CA at http://127.0.0.1:8080/cert.
# If Burp changes its dialogs, step 2 times out and prints its log.
set -euo pipefail

out=$1
jar=/usr/share/burpsuite/burpsuite.jar
prefs="$HOME/.java/.userPrefs/burp/prefs.xml"
display=:93
# Private temp dir: Burp temp files left in /tmp by another or a killed Burp would
# otherwise raise a "Delete old temporary files?" dialog.
work=$(mktemp -d)
burp_pid=
xvfb_pid=

# TERM first; a Burp or Xvfb that ignores it gets KILL after 10 s, so nothing waits forever.
stop() {
  local pid=$1
  [ -n "$pid" ] || return 0
  kill "$pid" 2>/dev/null || return 0
  for _ in $(seq 1 10); do kill -0 "$pid" 2>/dev/null || break; sleep 1; done
  kill -9 "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
}

cleanup() {
  stop "$burp_pid"
  stop "$xvfb_pid"
  rm -rf "$work"
}
trap cleanup EXIT

stop_burp() {
  stop "$burp_pid"
  burp_pid=
}

has_ca() { grep -q 'key="caCert"' "$prefs" 2>/dev/null; }

# Java ignores a click when the pointer is already resting on the button (no enter event),
# so always arrive from elsewhere first.
click() { xdotool mousemove 10 10 sleep 0.3 mousemove "$1" "$2" sleep 0.5 click 1; }

# The start wizard's size depends on the theme and font of the user settings; its
# Next / Start Burp button sits 50x27 px inside the bottom-right corner either way.
click_wizard_button() {
  local X Y WIDTH HEIGHT
  eval "$(xdotool search --onlyvisible --name "Burp Suite Community Edition v" getwindowgeometry --shell 2> /dev/null | grep -E '^(X|Y|WIDTH|HEIGHT)=[0-9]+$')"
  if [ -n "${WIDTH:-}" ]; then click $((X + WIDTH - 50)) $((Y + HEIGHT - 27)); fi
}

# 1. Licence and CA. Java flushes preferences every 30 s and on exit, so poll the file.
if ! has_ca; then
  { echo y; echo; sleep 150; } 2>/dev/null | java -Djava.awt.headless=true -Djava.io.tmpdir="$work" -jar "$jar" > "$work/headless.log" 2>&1 &
  burp_pid=$!
  for _ in $(seq 1 60); do has_ca && break; sleep 2; done
  stop_burp
  has_ca || { echo "Burp created no CA" >&2; tail -n 30 "$work/headless.log" >&2; exit 1; }
fi

# 2. GUI under Xvfb until the proxy answers.
Xvfb "$display" -screen 0 1280x1024x24 > "$work/xvfb.log" 2>&1 &
xvfb_pid=$!
export DISPLAY=$display
sleep 2
java -Djava.io.tmpdir="$work" -jar "$jar" --suppress-jre-check --disable-check-for-updates-dialog --use-defaults > "$work/gui.log" 2>&1 &
burp_pid=$!

for _ in $(seq 1 60); do
  if curl -fsS -o "$work/ca.der" http://127.0.0.1:8080/cert 2> /dev/null; then
    break
  fi
  titles=$(xdotool search --onlyvisible --name . getwindowname %@ 2> /dev/null || true)
  case "$titles" in
    *"Temporary Project"*) ;;                                   # main window: wait for the proxy
    *"Delete old temporary files?"*) click 799 617 ;;    # Delete
    *"Burp Suite Community Edition v"*) click_wizard_button ;; # Next, then Start Burp
    *)
      if grep -qx 'Burp Suite' <<< "$titles"; then
        click 578 788                       # Continue with Community Edition
      fi
      ;;
  esac
  sleep 3
done
stop_burp
# Burp is killed during startup; without this its next start offers "Safe mode".
sed -i '/key="burp.suite.StartupInProgress"/d' "$prefs"

if [ ! -s "$work/ca.der" ]; then
  echo "Burp proxy never served its CA; last windows: ${titles:-none}" >&2
  tail -n 30 "$work/gui.log" >&2
  exit 1
fi
mkdir -p "$(dirname "$out")"
openssl x509 -inform der -in "$work/ca.der" -out "$out"
