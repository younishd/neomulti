#!/usr/bin/env python
from pyautogui import press
from pynput.keyboard import Key, Listener
from time import sleep
import subprocess
from obswebsocket import obsws, requests


def main():
    instance = 1
    delay = 0.05
    windows = {}
    ready = False

    def current_window():
        return subprocess.run(["xdotool", "getactivewindow"], capture_output=True, check=True).stdout.decode().strip()

    def focus_window(wid):
        subprocess.run(["xdotool", "windowactivate", "--sync", wid], capture_output=True, check=True)

    def on_release(key):
        nonlocal instance, windows, ready, obs
        if key == Key.f8:
            if not ready:
                if len(windows) == 0:
                    windows[1] = current_window()
                else:
                    windows[2] = current_window()
                    ready = True
                return

            instance = 3 - instance
            press("f6")
            sleep(delay)
            obs.call(requests.SetCurrentScene(f"Multi {instance}"))
            sleep(delay)
            focus_window(windows[instance])
            press("esc")

    obs = obsws("localhost", 4444, "")
    obs.connect()
    with Listener(on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    main()
