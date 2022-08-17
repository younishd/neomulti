#!/usr/bin/env python
from pyautogui import press
import pyautogui
from pynput.keyboard import Key, Listener
from time import sleep
import subprocess
from obswebsocket import obsws, requests
import threading
import os
import signal


def current_window():
    return subprocess.run(["xdotool", "getactivewindow"], capture_output=True, check=True).stdout.decode().strip()


def wid_to_pid(wid):
    return subprocess.run(["xdotool", "getwindowpid", wid], capture_output=True, check=True).stdout.decode().strip()


def focus_window(wid):
    subprocess.run(["xdotool", "windowactivate", "--sync", wid], capture_output=True, check=True)


def freeze(pid):
    print(f"freeze {pid}")
    os.kill(int(pid), signal.SIGSTOP)


def unfreeze(pid):
    os.kill(int(pid), signal.SIGCONT)


def main():
    total_instances = 2
    instance = 1
    delay = 0.05
    freeze_after = 15
    windows = {}
    ready = False
    timer = None

    pyautogui.FAILSAFE = False

    def on_release(key):
        nonlocal instance, windows, ready, obs, timer

        if key == Key.f8:
            if not ready:
                idx = total_instances - len(windows)
                wid = current_window()
                pid = wid_to_pid(wid)
                windows[idx] = (wid, pid)

                print(f"instance #{idx}: wid {wid}, pid {pid}")

                if total_instances == len(windows):
                    ready = True
                return

            if timer is not None:
                timer.cancel()
            timer = threading.Timer(freeze_after, freeze, [windows[instance][1]])
            timer.start()

            instance = instance % total_instances + 1

            unfreeze(windows[instance][1])

            press("f11")
            press("f6")

            obs.call(requests.SetCurrentScene(f"Multi {instance}"))

            sleep(delay)

            focus_window(windows[instance][0])

            press("f11")
            press("esc")

    try:
        obs = obsws("localhost", 4444, "")
        obs.connect()
        with Listener(on_release=on_release) as listener:
            listener.join()
    except KeyboardInterrupt:
        for _, w in windows.items():
            unfreeze(w[1])


if __name__ == "__main__":
    main()
