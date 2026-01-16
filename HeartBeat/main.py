from Client.client import Client
import psutil
import time
def main():
    '''ハートビート監視プロセスの起動'''
    '''応答がなければ全プロセスを再起動する'''
    processes = {}
    responses = {}
    client_inst = Client(process="heartbeat")
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
                # 解除メッセージの処理
                elif msgtype == "UNREGISTER":
                    if procname in processes:
                        del processes[procname]
                        del responses[procname]
                        client_inst.send("logger", "info", "HEARTBEAT", f"Unregistered process {procname}")
            elif len(parts) >= 2:
                msgtype = parts[0]
                procname = parts[1]
                if msgtype == "ALIVE":
                    responses[procname] = time.time()
        
        for response in list(responses.keys()):
            # 応答が一定時間(15s)ないプロセスを削除
            if time.time() - responses[response] > 6*5:
                # サーバーに対して再起動要求を送信
                client_inst.send("logger", "warning", "HEARTBEAT", f"No response from {response} for 15s. Requesting reboot.")
                client_inst.send("server", "REBOOT") 

        for process in list(processes.keys()):
            #プロセスが生きているか確認
            pid = processes[process]
            try:
                if not psutil.pid_exists(int(pid)):
                    # プロセスが存在しない場合、登録解除メッセージを送信
                    client_inst.send("logger", "error", "HEARTBEAT", f"Process {process} with pid={pid} not found. Unregistering.")
                    # サーバーに対して再起動要求を送信
                    client_inst.send("server", "REBOOT")
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
