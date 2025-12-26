from client import Client
import datetime
import time

if __name__ == '__main__':
    client = Client(process="logger")
    filepath = "Log/" + datetime.datetime.now().strftime("%Y%m%d") + "_log.txt"
    logfile = open(filepath, "a", encoding="utf-8")
    while True:
        if not client._rx_queue.empty():
            msg = client._rx_queue.get()
            print(msg)
            msgtype,proc, content = msg.split(',')
            if msgtype == "reload":
                logfile.close()
                filepath = "../Log/" + datetime.datetime.now().strftime("%Y%m%d") + "_log.txt"
                logfile = open(filepath, "a", encoding="utf-8")
            elif msgtype == "error":
                logfile.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ",[ERROR]," + proc + "," + content + "\n")
                logfile.flush()
            elif msgtype == "warning":
                logfile.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ",[WARNING]," + proc + "," + content + "\n")
                logfile.flush()
            elif msgtype == "info":
                logfile.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ",[INFO]," + proc + "," + content + "\n")
                logfile.flush()
        time.sleep(0.1)
            