import socket
import queue
import threading
import time

class Client:
    def __init__(self, process, port=50000, on_message=None, reconnect=False):
        """
        process: 自プロセス名（サーバへ送るときに使う）
        host, port: サーバ接続先
        on_message: 受信時コールバック func(message_str: str) -> None
        reconnect: 接続が切れたら再接続する場合は True
        """
        self.process = process
        # 自PCのIPを自動検出（失敗時はループバックアドレスを使用）
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 到達必須ではない外部アドレスへ接続することでローカルIPを取得
            s.connect(('8.8.8.8', 80))
            self.host = s.getsockname()[0]
        except Exception:
            self.host = '127.0.0.1'
        finally:
            if s:
                try:
                    s.close()
                except Exception:
                    pass
        self.port = port
        self.on_message = on_message
        self.reconnect = reconnect

        self._sock = None
        self._lock = threading.Lock()
        self._stop_ev = threading.Event()
        # 受信保持用キュー（ここで受信データを保持する）
        self._rx_queue = queue.Queue()
        # 受信スレッドをコンストラクタで起動
        self._recv_thread = threading.Thread(target=self._receiver_loop, daemon=True)
        self._recv_thread.start()

    def __repr__(self):
        return f"Client(process={self.process!r}, host={self.host!r}, port={self.port!r})"

    def _ensure_connected(self):
        """必要に応じてソケットを接続する（内部利用、排他制御あり）"""
        with self._lock:
            if self._sock:
                return True
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((self.host, self.port))
                s.settimeout(None)
                self._sock = s
                # 登録メッセージを送る（必要に応じてフォーマットを合わせる）
                try:
                    reg = f"{self.process},-,HELLO" + r"\\SPLIT\\"
                    self._sock.sendall(reg.encode())
                except Exception:
                    pass
                return True
            except Exception:
                try:
                    s.close()
                except Exception:
                    pass
                self._sock = None
                return False

    def send(self, toprocess, *args, timeout=5.0):
        """
        同期的に送信する。接続がなければ接続を試みる（timeout 秒待つ）。
        引数は文字列化してカンマ区切りで送信する。
        例: send("other", "CMD", "arg1")
        戻り値: True=送信成功, False=失敗
        """
        deadline = time.time() + timeout
        # 接続を確立する試行
        while time.time() < deadline:
            if self._ensure_connected():
                break
            time.sleep(0.2)
        else:
            return False

        payload = ','.join([str(self.process), str(toprocess)] + [str(a) for a in args]) + r"\\SPLIT\\"
        with self._lock:
            try:
                self._sock.sendall(payload.encode())
                return True
            except Exception:
                try:
                    self._sock.close()
                except Exception:
                    pass
                self._sock = None
                return False

    def close(self):
        """明示的にクローズして受信スレッドを停止する"""
        self._stop_ev.set()
        with self._lock:
            try:
                if self._sock:
                    self._sock.close()
            except Exception:
                pass
            self._sock = None

    def _receiver_loop(self):
        """受信専用スレッド。接続が切れたら reconnect 設定によって再接続を試みる"""
        while not self._stop_ev.is_set():
            if not self._ensure_connected():
                if self.reconnect:
                    time.sleep(1.0)
                    continue
                else:
                    break

            sock = self._sock
            try:
                while not self._stop_ev.is_set():
                    data = sock.recv(4096)
                    if not data:
                        # 切断
                        break
                    text = data.decode(errors='ignore')
                    self._rx_queue.put(text)
                    # コールバック呼び出し（例外は無視）
                    if self.on_message:
                        try:
                            self.on_message(text)
                        except Exception:
                            pass
            except Exception:
                pass
            finally:
                # 切断されたらソケットを破棄
                with self._lock:
                    try:
                        if self._sock:
                            self._sock.close()
                    except Exception:
                        pass
                    self._sock = None

            if not self.reconnect:
                break
                # 再接続まで待つ
            time.sleep(1.0)