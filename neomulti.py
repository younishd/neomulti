#!/usr/bin/env python
from pyautogui import press
import pyautogui
from pynput.keyboard import Key, Listener
from time import sleep
import subprocess
from obswebsocket import obsws, requests
from obswebsocket.exceptions import ConnectionFailure
import threading
import os
import signal
import sys
import argparse


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
    print(f"unfreeze {pid}")
    os.kill(int(pid), signal.SIGCONT)


def main():
    def on_release(key):
        nonlocal instance, windows, ready, obs, timer_freeze, timer_scene

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

            if timer_freeze[instance - 1] is not None:
                timer_freeze[instance - 1].cancel()
            timer_freeze[instance - 1] = threading.Timer(freeze_after, freeze, (windows[instance][1],))
            timer_freeze[instance - 1].start()

            if timer_scene is not None:
                timer_scene.cancel()
            timer_scene = threading.Timer(freeze_after, obs.call, (requests.SetCurrentScene("Multi"),))
            timer_scene.start()

            instance = instance % total_instances + 1

            if timer_freeze[instance - 1] is not None:
                timer_freeze[instance - 1].cancel()
            unfreeze(windows[instance][1])

            press("f11")
            press("f6")

            obs.call(requests.SetCurrentScene(f"Multi {instance}/{total_instances}"))

            sleep(delay)

            focus_window(windows[instance][0])

            press("f11")
            press("esc")

    instance = 1
    delay = 0.1
    freeze_after = 15
    windows = {}
    ready = False
    pyautogui.FAILSAFE = False
    parser = argparse.ArgumentParser(
        description="Neo's multi instance resetter for Minecraft speedrunning on Linux.", prog="neomulti"
    )
    parser.add_argument(
        "-i",
        "--instances",
        default=2,
        type=int,
        help="number of minecraft instances",
    )
    args = parser.parse_args()
    total_instances = args.instances
    timer_freeze = [None] * total_instances
    timer_scene = None

    try:
        obs = obsws("localhost", 4444, "")
        obs.connect()
        with Listener(on_release=on_release) as listener:
            listener.join()
    except KeyboardInterrupt:
        print("goodbye")
        return
    except ConnectionFailure:
        print("error: failed to connect to obs!")
        sys.exit(1)
    finally:
        for _, w in windows.items():
            try:
                unfreeze(w[1])
            except:
                continue


if __name__ == "__main__":
    main()
