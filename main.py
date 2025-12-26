from Server import server as Server
from HeartBeat import main as HeatBeat

import subprocess
import sys
if __name__ == '__main__':
    pids = {}
    '''サーバーの起動'''
    serverinfo  = Server.Start()
    '''ロガーの起動'''
    # Loggerを起動してPIDを取得
    proc = subprocess.Popen(["python", "-m", 'Logger.main'])
    pids["logger"] = proc.pid
    # 必要ならログやサーバーに通知
    Server.send(serverinfo, "logger", "info", "BSW", "Server started")
    Server.send(serverinfo, "logger", "info", "BSW", f"Logger started pid={pids['logger']}")
    '''ハートビートの起動'''
    while True:
        pass

