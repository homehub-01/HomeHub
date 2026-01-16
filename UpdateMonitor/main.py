from Client import client
import json
from pathlib import Path
import time
import subprocess
import threading
import queue

class AppInfo:
    apphash = {}
    rebootrequired = False

def update_from_git(client, appinfo, repo_path):
    """指定されたリポジトリの最新のコミットハッシュを取得する"""
    fetch = subprocess.run(["git", "-C", repo_path, "fetch"], capture_output=True, text=True)
    if fetch.returncode != 0:
        client.send("logger", "error", "UPDATEMONITOR", f"Failed to fetch {repo_path}: {fetch.stderr.strip()}")
        return
    result = subprocess.run(
        ["git", "-C", repo_path, "rev-parse", "origin/develop"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        client.send("logger", "error", "UPDATEMONITOR", f"Failed to get git hash for {repo_path}: {result.stderr.strip()}")
        return
    latest_hash = result.stdout.strip()
    client.send("logger", "debug1", "UPDATEMONITOR", f"Latest git hash for {repo_path} is {latest_hash}")
    if appinfo.apphash.get(repo_path, "") != latest_hash:
        result = subprocess.run(["git","submodule","update", "--remote", repo_path], capture_output=True, text=True)
        client.send("logger", "info", "UPDATEMONITOR", f"Pulled latest changes for {repo_path}: {result.stdout.strip()}")
        appinfo.apphash[repo_path] = latest_hash
        appinfo.rebootrequired = True
        client.send("logger", "info", "UPDATEMONITOR", f"App {repo_path} updated to hash {latest_hash}. Reboot required.")

def main():
    client_inst = client.Client(process="updatemonitor")
    appinfo = AppInfo()
    json_path = "APPHash.json"
    if not Path(json_path).exists():
        with Path(json_path).open("w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    try:
        appinfo.apphash = json.load(open(json_path, "r", encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        appinfo.apphash = {}
    reloadtime = 0
    threads = queue.Queue()
    updateflag = True
    forced_update = False
    while True:
        if not client_inst._rx_queue.empty():
            msg = client_inst._rx_queue.get()
            if len(msg.split(',')) == 1:
                if msg == "HEARTBEAT":
                    client_inst.send("heartbeat", "ALIVE","updatemonitor")
                elif msg == "update":
                    forced_update = True
        if time.time() - reloadtime > 1500 or forced_update:
            forced_update = False
            reloadtime = time.time()
            while not threads.empty():
                thread = threads.get()
                if thread.is_alive():
                    updateflag = False
                    threads.put(thread)
                    client_inst.send("logger", "warning", "UPDATEMONITOR", "Update thread still running, skipping this cycle.")
                    break
            if threads.empty():
                updateflag = True
            if updateflag:
                for app in appinfo.apphash.keys():
                    updatethread = threading.Thread(target=update_from_git, args=(client_inst, appinfo, app,))
                    updatethread.start()
                    threads.put(updatethread)
        if appinfo.rebootrequired:
            client_inst.send("logger", "info", "UPDATEMONITOR", "Reboot required due to app updates. Sending REBOOT command to server.")
            appinfo.rebootrequired = False
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(appinfo.apphash, f, ensure_ascii=False, indent=2)
            client_inst.send("server", "REBOOT")
        time.sleep(1)


if __name__ == "__main__":
    main()
        
