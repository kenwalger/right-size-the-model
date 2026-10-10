#!/usr/bin/env bash
#
# The offline test, run headless over SSH.
#
#   sudo scripts/offline_test.sh [model]
#
# Turns the radio off, proves there is no route out, runs one call from
# each workflow, turns the radio back on. Your SSH session survives,
# because it is the Pi's own wireless being switched off and your shell is
# already connected; the session freezes while the radio is down and
# resumes when it comes back.
#
# A dead man's switch re-enables the radio after DEADMAN seconds no matter
# what happens to this script, including a kill or a crash. Without it a
# failure halfway through leaves a headless Pi with no network and you are
# hunting for a monitor.
#
# Loopback is untouched, which is the point: Ollama listens on localhost,
# so if inference needs the network the calls will fail for a real reason
# rather than because the server became unreachable.
#
# Everything is written to a log file as well as the terminal, and the
# script ignores SIGHUP so it finishes even if the session goes away. The
# first run of this lost its entire output to a connection reset: the Pi
# recovered exactly as designed and there was no record that it had,
# which for a test whose only product is evidence is a complete failure.
# Run it inside tmux as well if you want to watch it.

set -uo pipefail

MODEL="${1:-smollm2:360m}"
DEADMAN="${DEADMAN:-900}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(dirname "$HERE")"
RUN_AS="${SUDO_USER:-$(id -un)}"
LOG="${LOG:-$REPO/offline-test-$(date +%Y%m%d-%H%M%S).log}"

if [[ $EUID -ne 0 ]]; then
  echo "Needs root to switch the radio. Run with sudo." >&2
  exit 1
fi

# Survive the session going away, and record everything. The HUP trap is
# set before any child starts, so python inherits it too.
trap "" HUP
exec > >(tee -a "$LOG") 2>&1

echo "logging to $LOG"
echo

radio_up()   { rfkill unblock wifi; }
radio_down() { rfkill block wifi; }

# Can anything reach the internet? Two checks, because a DNS-only failure
# and a no-route failure are different things and only one of them means
# the radio is really off.
reachable() {
  local dns=1 ip=1
  timeout 6 getent hosts ollama.com >/dev/null 2>&1 && dns=0
  timeout 6 ping -c1 -W3 1.1.1.1 >/dev/null 2>&1 && ip=0
  echo "    dns lookup  $([[ $dns -eq 0 ]] && echo reachable || echo 'no answer')"
  echo "    ping 1.1.1.1 $([[ $ip -eq 0 ]] && echo reachable || echo 'no route')"
  [[ $dns -eq 0 || $ip -eq 0 ]]
}

echo "=== before: the network should be up"
if reachable; then
  echo "    network is up, as expected"
else
  echo "    WARNING: already offline. The test below proves nothing about"
  echo "    switching the radio off, because it was never on."
fi

# Dead man's switch. setsid detaches it so it outlives this script and any
# signal sent to it.
setsid bash -c "sleep $DEADMAN; rfkill unblock wifi" >/dev/null 2>&1 &
DEADMAN_PID=$!
echo
echo "dead man's switch armed: radio returns in ${DEADMAN}s whatever happens"

cleanup() {
  echo
  echo "=== restoring the radio"
  radio_up
  kill "$DEADMAN_PID" 2>/dev/null

  # Wifi needs to reassociate and get a lease, which takes longer than a
  # single check allows. The first version slept three seconds and then
  # announced the network had not come back, at the one moment in the run
  # where a false alarm is least welcome.
  local waited=0
  while [[ $waited -lt 45 ]]; do
    sleep 5
    waited=$((waited + 5))
    if reachable >/dev/null 2>&1; then
      echo "    network is back after ${waited}s"
      reachable
      return
    fi
    echo "    still down after ${waited}s, waiting"
  done

  echo "    network has NOT come back after ${waited}s. Check with:"
  echo "      sudo rfkill list"
  echo "      sudo rfkill unblock wifi"
}
trap cleanup EXIT

echo
echo "=== switching the radio off"
radio_down
sleep 3

echo "=== after: the network should be gone"
if reachable; then
  echo
  echo "    STILL REACHABLE. Something else is carrying traffic, most likely"
  echo "    an ethernet cable. Unplug it and run this again, or the result"
  echo "    below means nothing."
  exit 1
fi

echo
echo "=== running one call from each workflow, with no route out"
sudo -u "$RUN_AS" python3 "$REPO/scripts/offline_probe.py" "$MODEL"
RESULT=$?

echo
if [[ $RESULT -eq 0 ]]; then
  echo "RESULT: inference ran with the radio off and no route to the internet."
else
  echo "RESULT: something failed offline. The output above says what."
fi

echo
echo "full transcript: $LOG"

# tee is a child of this shell; give it a moment to flush before exit.
sleep 1
exit $RESULT