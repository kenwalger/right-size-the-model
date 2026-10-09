# Setting up the Pi

From a blank SD card to a machine that can run the kit. Written for a
Raspberry Pi 4 with 4GB RAM, flashed from a Windows laptop using PowerShell.

Budget an hour, most of it waiting on downloads.

## 1. Flash the card

Install Raspberry Pi Imager on the laptop, from `raspberrypi.com/software`.

In Imager:

- **Device**: Raspberry Pi 4
- **Operating System**: Raspberry Pi OS (other) → **Raspberry Pi OS Lite
  (64-bit)**
- **Storage**: the SD card

**Lite, and 64-bit, both matter.**

Lite has no desktop. You will work over SSH, so a desktop costs you a couple
of gigabytes of card and a few hundred megabytes of RAM that the models could
be using instead.

64-bit is not optional. Ollama has no 32-bit ARM build. If a future you ever
wonders why nothing installs, this is the reason.

Before writing, open the gear icon or **Edit Settings** and fill in:

- Hostname: something you will recognise, `cellar-pi` or similar
- Username and password
- Wi-Fi SSID and password, with the right country set
- Locale and timezone
- **Services tab: enable SSH**, with password authentication

Setting those here is what makes the Pi reachable on first boot with no
monitor or keyboard. Skip it and you need a screen.

Write the card, which takes a few minutes.

## 2. First boot

Put the card in the Pi, plug it in, wait two minutes for the first boot to
finish expanding the filesystem.

From PowerShell on the laptop:

```powershell
ssh <username>@<hostname>.local
```

If `.local` does not resolve, find the Pi's address in your router's client
list and use that instead.

Then bring it up to date:

```bash
sudo apt update && sudo apt full-upgrade -y
sudo reboot
```

Reconnect after the reboot.

## 3. Confirm the architecture before anything else

```bash
uname -m
```

**It must print `aarch64`.** If it prints `armv7l` you flashed a 32-bit
image; go back to step 1 and pick the 64-bit one. Five seconds now saves an
hour of confusing failures later.

While you are here, record what you have for the setup table:

```bash
cat /etc/os-release | head -2
free -h
uname -r
```

## 4. Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

The script detects arm64 and installs a systemd service, so Ollama starts on
boot and stays running. Check it:

```bash
ollama --version
systemctl status ollama
```

## 5. Pull the models

```bash
ollama pull smollm2:360m
ollama pull qwen2.5:1.5b
ollama list
```

Check what is current the morning you start and substitute if something
better has shipped; just write down exactly what you used. `ollama list`
prints digests, which belong in `PREDICTIONS.md`.

Roughly 1.5GB of downloads over your home connection, then they live on the
card.

## 6. Get the kit onto the Pi

```bash
sudo apt install -y git
git clone https://github.com/kenwalger/right-size-the-model.git
cd right-size-the-model
python3 --version
```

Python 3 ships with Raspberry Pi OS and the kit is standard library only, so
there is nothing to install and no virtualenv to make.

## 7. Smoke test before the real run

```bash
python3 scripts/run.py extraction regex
python3 scripts/score.py
```

Expect 30/30 in well under a second. That proves the fixtures, the runner and
the scorer all work before a model is involved.

Then one model call, to confirm Ollama is reachable:

```bash
ollama run smollm2:360m "Reply with the single word: ready"
```

## 8. Settings for the real run

**Raise the timeout.** The runner defaults to 180 seconds per call, sized for
faster hardware. On a Pi 4 a long answer over the whole corpus could brush
it:

```bash
export TIMEOUT=600
```

**Watch the temperature.** With the fan fitted this should stay well clear of
throttling, but check rather than assume. In a second SSH session:

```bash
watch -n 5 vcgencmd measure_temp
```

And afterwards:

```bash
vcgencmd get_throttled
```

`throttled=0x0` means it never throttled. Anything else means the latency
numbers are describing a machine that was slowing itself down, and that
belongs in the results rather than being quietly ignored.

**Do not add swap.** Default Raspberry Pi OS swap is small and lives on the
SD card. Both scoped models fit in 4GB comfortably, so swap should never be
touched. If a model does start swapping, the honest result is that it does
not fit on this hardware, not that it runs slowly with a workaround.

## 9. Run it

The run is roughly ninety minutes over SSH. If the laptop sleeps or the
connection drops, the session dies and takes the run with it, so do it inside
tmux:

```bash
sudo apt install -y tmux
tmux new -s run
```

Detach with `Ctrl-b` then `d`, reattach with `tmux attach -t run`.

Inside that session:

```bash
cd ~/right-size-the-model
export TIMEOUT=600

python3 scripts/run.py extraction     smollm2:360m
python3 scripts/run.py extraction     qwen2.5:1.5b
python3 scripts/run.py classification smollm2:360m
python3 scripts/run.py classification qwen2.5:1.5b
python3 scripts/run.py qa             smollm2:360m
python3 scripts/run.py qa             qwen2.5:1.5b
```

Fastest first. The regex baseline is already recorded from step 7.

Watch the first run finish before walking away: a wrong model tag or an
unreachable Ollama shows up there. After that, detach.

Each record prints its fixture id as it goes, and a call that fails prints
why and lets the run continue. Two kinds of failure are reported, and they
mean different things. A **model** failure means the model ran and produced
nothing usable, which counts against it. A **transport** failure means the
call never reached a working model, which makes the run incomplete and needs
fixing before the numbers mean anything.

Then score:

```bash
python3 scripts/score.py
python3 scripts/score.py --csv > results/summary.csv
vcgencmd get_throttled
```

## 10. Getting results back

Everything runs on the Pi and writes to `results/` there. To bring the files
to the laptop afterwards, from PowerShell:

```powershell
scp -r <username>@<hostname>.local:~/right-size-the-model/results ./results
```

## Notes

Raspberry Pi OS moved to a Debian Trixie base in October 2025, and the
Raspberry Pi team recommends flashing a clean image rather than upgrading an
existing install, which is what this guide does.

If you later want faster model loading, a USB SSD in place of the SD card is
the upgrade that matters. It changes startup, not inference, so it is not
worth buying for this experiment.

## Sources

- [Raspberry Pi OS documentation](https://www.raspberrypi.com/documentation/computers/os.html)
- [Trixie, the new version of Raspberry Pi OS](https://www.raspberrypi.com/news/trixie-the-new-version-of-raspberry-pi-os/)
- [Ollama Linux download](https://ollama.com/download/linux)