from Client.client import Client
import psutil
import time
import datetime
from pathlib import Path

def _log_local(level, message):
    try:
        log_dir = Path("Log")
        log_dir.mkdir(parents=True, exist_ok=True)
        filename = log_dir / (datetime.datetime.now().strftime("%Y%m%d") + "_heartbeat.log")
        with filename.open("a", encoding="utf-8") as f:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{ts},[{level}],HEARTBEAT,{message}\n")
    except Exception:
        pass
def main():
    '''ハートビート監視プロセスの起動'''
    '''応答がなければ全プロセスを再起動する'''
    processes = {}
    responses = {}
    client_inst = Client(process="heartbeat")
    _log_local("INFO", "Heartbeat monitor started.")
    while True:
        while not client_inst._rx_queue.empty():
            msg = client_inst._rx_queue.get()
            parts = msg.split(',')
            # 受信キューをチェックして登録・解除メッセージを処理
            if len(parts) >= 3:
                msgtype = parts[0]
                procname = parts[1]
                pid = parts[2]
                # 登録メッセージの処理
                if msgtype == "REGISTER":
                    processes[procname] = pid
                    responses[procname] = time.time()
                    client_inst.send("logger", "info", "HEARTBEAT", f"Registered process {procname} with pid={pid}")
                    _log_local("INFO", f"Registered process {procname} pid={pid}")
                # 解除メッセージの処理
                elif msgtype == "UNREGISTER":
                    if procname in processes:
                        del processes[procname]
                        del responses[procname]
                        client_inst.send("logger", "info", "HEARTBEAT", f"Unregistered process {procname}")
                        _log_local("INFO", f"Unregistered process {procname}")
            elif len(parts) >= 2:
                msgtype = parts[0]
                procname = parts[1]
                if msgtype == "ALIVE":
                    responses[procname] = time.time()
        
        for response in list(responses.keys()):
            # 応答が一定時間(15s)ないプロセスを削除
            last_seen = responses[response]
            if time.time() - last_seen > 6*5:
                # サーバーに対して再起動要求を送信
                msg = f"No response from {response} for 15s (last_seen={last_seen}). Requesting reboot."
                client_inst.send("logger", "warning", "HEARTBEAT", msg)
                _log_local("WARNING", msg)
                client_inst.send("server", "REBOOT", "HEARTBEAT_NO_RESPONSE", response)

        for process in list(processes.keys()):
            #プロセスが生きているか確認
            pid = processes[process]
            try:
                if not psutil.pid_exists(int(pid)):
                    # プロセスが存在しない場合、登録解除メッセージを送信
                    msg = f"Process {process} with pid={pid} not found. Unregistering."
                    client_inst.send("logger", "error", "HEARTBEAT", msg)
                    _log_local("ERROR", msg)
                    # サーバーに対して再起動要求を送信
                    client_inst.send("server", "REBOOT", "HEARTBEAT_PID_NOT_FOUND", process, pid)
                    del processes[process]
                    del responses[process]
                    break
            except Exception:
                continue
            # ハートビートメッセージを送信
            client_inst.send(process, "HEARTBEAT")
            time.sleep(0.2)
        
        time.sleep(5)


if __name__ == '__main__':
    main()
