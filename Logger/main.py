from Client.client import Client
import datetime
import time

if __name__ == '__main__':
    client = Client(process="logger")
    filepath = "Log/" + datetime.datetime.now().strftime("%Y%m%d") + "_log.txt"
    logfile = open(filepath, "a", encoding="utf-8")
    logfile.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ",[INFO]," + "logger" + "," + "Logger started." + "\n")
    logfile.flush()
    while True:
        if not client._rx_queue.empty():
            msg = client._rx_queue.get()
            if len(msg.split(',')) == 1:
                # ファイルを更新する。
                if msg == "reload":
                    logfile.close()
                    filepath = "../Log/" + datetime.datetime.now().strftime("%Y%m%d") + "_log.txt"
                    logfile = open(filepath, "a", encoding="utf-8")
                # 応答メッセージを返す
                elif msg == "HEARTBEAT":
                    client.send("heartbeat", "ALIVE","logger")
            elif len(msg.split(',')) >= 3:
                msgsplit = msg.split(',')
                msgtype,proc, content = msgsplit[0], msgsplit[1], ','.join(msgsplit[2:])
                # ログメッセージを書き込む
                if msgtype == "error":
                    logfile.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ",[ERROR]," + proc + "," + content + "\n")
                    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ",[ERROR]," + proc + "," + content + "\n")
                    logfile.flush()
                elif msgtype == "warning":
                    logfile.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ",[WARNING]," + proc + "," + content + "\n")
                    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ",[WARNING]," + proc + "," + content + "\n")
                    logfile.flush()
                elif msgtype == "info":
                    logfile.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ",[INFO]," + proc + "," + content + "\n")
                    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ",[INFO]," + proc + "," + content + "\n")
                    logfile.flush()
                elif msgtype == "debug1":
                    logfile.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ",[DEBUG1]," + proc + "," + content + "\n")
                    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ",[DEBUG1]," + proc + "," + content + "\n")
                    logfile.flush()
                elif msgtype == "debug2":
                    logfile.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ",[DEBUG2]," + proc + "," + content + "\n")
                    logfile.flush()
                else:
                    logfile.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ",[UNKNOWN]," + proc + "," + content + "\n")
                    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ",[UNKNOWN]," + proc + "," + content + "\n")
                    logfile.flush()
                
        time.sleep(0.1)
            