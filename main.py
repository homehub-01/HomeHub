from Server import server as Server
from HeartBeat import main as HeatBeat
import time
import psutil
import subprocess
import sys

def start_process():
    # プロセスを起動し、ハートビートに登録する
    def boot_process(process_name, module_name):
        try:
            proc = subprocess.Popen([sys.executable, "-m", module_name])
            Server.send(serverinfo, "logger", "info", "BSW", f"Started process {process_name} pid={proc.pid}")
            Server.send(serverinfo, "heartbeat", "REGISTER", process_name, str(proc.pid))
            return proc.pid
        except Exception as e:
            Server.send(serverinfo, "logger", "error", "BSW", f"Failed to start process {process_name}: {e}")
            return None
    
    pids = {}
    '''ロガーの起動'''
    pids["logger"] = boot_process("logger", "Logger.main")
    '''UIアプリの起動'''
    #pids["uiapp"] = boot_process("uiapp", "UIApp.main")
    return pids


if __name__ == '__main__':
    '''サーバーの起動'''
    serverinfo  = Server.Start()

    '''ハートビートの起動'''
    subprocess.Popen(["python", "-m", 'HeartBeat.main'])

    '''各プロセスの起動'''
    pids = start_process()

    while True:
        # サーバー自身の受信キューをチェック
        if not serverinfo.me_rx_queue.empty():
            fromprocess, command = serverinfo.me_rx_queue.get()
            if command[0] == "REBOOT":
                # 全プロセスを再起動する
                Server.send(serverinfo, "logger", "info", "BSW", f"Rebooting all processes as requested by {fromprocess}")
                # ハートビートに登録されているプロセスを取得
                for process in pids.keys():
                    try:
                        # プロセスを終了させる
                        Server.send(serverinfo, "heartbeat", "UNREGISTER", process)
                        Server.send(serverinfo, "logger", "info", "BSW", f"Terminating process {process} pid={pids[process]}")
                        proc = psutil.Process(pids[process])
                        proc.terminate()
                        proc.wait()
                    except Exception as e:
                        Server.send(serverinfo, "logger", "error", "BSW", f"Failed to terminate process {process}: {e}")
                time.sleep(2)
                pids = start_process()
        time.sleep(0.1)

