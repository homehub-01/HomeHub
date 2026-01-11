import socket
import threading
import queue
import time

class ServeInfo:
    server = None
    rx_queue = queue.Queue()
    tx_queue = queue.Queue()
    me_rx_queue = queue.Queue()
    addrsbook = {"server": None}   # process_name -> conn

def Start():
    serverinfo = ServeInfo()
    serverinfo.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverinfo.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverinfo.server.bind(('', 50000))
    serverinfo.server.listen(10)
    threading.Thread(target=accept_loop, args=(serverinfo,), daemon=True).start()
    threading.Thread(target=tx, args=(serverinfo,), daemon=True).start()
    threading.Thread(target=sorting, args=(serverinfo,), daemon=True).start()
    return serverinfo

def send(serverinfo: ServeInfo, toprocess: str, *args):
    serverinfo.rx_queue.put((','.join(['server', toprocess] + [str(a) for a in args]), None))

def accept_loop(serverinfo: ServeInfo):
    while True:
        try:
            conn, addr = serverinfo.server.accept()
            threading.Thread(target=client_handler, args=(serverinfo, conn, addr), daemon=True).start()
        except Exception:
            time.sleep(0.1)

def client_handler(serverinfo: ServeInfo, conn: socket.socket, addr):
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            message = data.decode()
            serverinfo.rx_queue.put((message, conn))
    except Exception:
        pass
    finally:
        # 切断時は登録されているプロセスと接続一致を削除
        to_remove = [k for k, v in serverinfo.addrsbook.items() if v is conn]
        for k in to_remove:
            del serverinfo.addrsbook[k]
        try:
            conn.close()
        except Exception:
            pass

def tx(serverinfo: ServeInfo):
    while True:
        try:
            if not serverinfo.tx_queue.empty():
                conn, command = serverinfo.tx_queue.get()
                try:
                    conn.sendall(','.join(command).encode())
                except Exception:
                    # 送信失敗時は接続を閉じて登録削除
                    to_remove = [k for k, v in serverinfo.addrsbook.items() if v is conn]
                    for k in to_remove:
                        del serverinfo.addrsbook[k]
                    try:
                        conn.close()
                    except Exception:
                        pass
        except Exception:
            pass
        time.sleep(0.01)

def sorting(serverinfo: ServeInfo):
    while True:
        try:
            if not serverinfo.rx_queue.empty():
                message, conn = serverinfo.rx_queue.get()
                sp_message = message.split("\\SPLIT\\")
                if len(sp_message) > 1:
                    for i in range(1, len(sp_message),1):
                        serverinfo.rx_queue.put(sp_message[i])
                parts = sp_message[0].split(',')
                if len(parts) < 2:
                    continue
                fromprocess = parts[0]
                toprocess = parts[1]
                command = parts[2:]
                if fromprocess != "heartbeat" or toprocess != "heartbeat":
                    with open("test.txt", "a") as f:
                        f.write(sp_message[0]+"\n")
                # 初めてのプロセスなら登録、既に異なるコネクションなら更新
                if fromprocess not in serverinfo.addrsbook:
                    serverinfo.addrsbook[fromprocess] = conn
                elif serverinfo.addrsbook[fromprocess] is not conn:
                    serverinfo.addrsbook[fromprocess] = conn
                
                # 送信先が登録されていれば送信キューへ
                if toprocess == "server":
                    serverinfo.me_rx_queue.put((fromprocess, command))
                elif toprocess in serverinfo.addrsbook:
                    serverinfo.tx_queue.put((serverinfo.addrsbook[toprocess], command))
                elif toprocess == "-":
                    pass
                
                else:
                    # 未登録なら後ろへ戻す（短い遅延を入れて無限ループを避ける）
                    time.sleep(0.05)
                    serverinfo.rx_queue.put((message, conn))
        except Exception:
            pass
        time.sleep(0.01)