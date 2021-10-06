import socket
import threading
import time

PORT = 8888
HOST = ''
MAX_CONN = 20

BUFFER_SIZE = 1048576

TIME_OUT = 0.5
TIME_WAIT = 0.05

BLACKLIST_FILE = "blacklist.conf"
blacklist = {}

FORBIDDEN_MESSAGE = '''
HTTP/1.1 403 Forbidden\r\n\r\n
<html>
<head>
<style>
h1 {text-align: center;}
p {text-align: center;}
div {text-align: center;}
</style>
</head>
<body>

<h1 style="font-family:arial; font-size:120px">403</h1>
<p style="font-family:arial; font-size:20px"><b>Forbidden</b></p>
<p style="font-family:arial">The server understood the request, but is refusing to authorize it.</p>

</body>
</html>\n\n'''

f = open(BLACKLIST_FILE, "rb")
data = ""
while True:
    line = f.read()
    if not len(line):
        break
    data += line.decode()
f.close()
blacklist = data.splitlines()


class Client:
    def __init__(self, sock):
        try:
            self.s = sock
            self.conn, self.addr = self.s.accept()
            print(f'*** A connection established from {self.addr}')
        except:
            pass

    def get_request(self):
        try:
            self.conn.setblocking(False)

            res = b''

            begin = time.time()
            while 1:
                if res and time.time() - begin > TIME_OUT:
                    break
                elif time.time() - begin > TIME_OUT * 2:
                    break

                try:
                    chunk = self.conn.recv(BUFFER_SIZE)
                    if chunk:
                        res += chunk
                        begin = time.time()
                    else:
                        time.sleep(TIME_WAIT)
                except:
                    pass

            self.conn.setblocking(True)

            return res
        except:
            pass

    def send_response(self, res: bytes):
        try:
            self.conn.sendall(res)
        except:
            pass

    def close(self):
        self.conn.close()


class Host:
    def __init__(self, webserver, port):
        try:
            self.webserver, self.port = webserver, port
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except:
            pass

    def connect(self):
        try:
            self.s.connect((self.webserver, self.port))
            print(f'> Connected to {self.webserver}')
        except:
            pass

    def send_request(self, req: bytes):
        try:
            self.s.sendall(req)
        except:
            pass

    def get_response(self):
        try:
            self.s.setblocking(False)

            res = b''

            begin = time.time()
            while 1:
                if res and time.time() - begin > TIME_OUT:
                    break
                elif time.time() - begin > TIME_OUT * 2:
                    break

                try:
                    chunk = self.s.recv(BUFFER_SIZE)
                    if chunk:
                        res += chunk
                        begin = time.time()
                    else:
                        time.sleep(TIME_WAIT)
                except:
                    pass

            self.s.setblocking(True)

            return res
        except:
            pass

    def close(self):
        self.s.close()


class ProxyServer:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((HOST, PORT))
        self.s.listen(MAX_CONN)
        self.s.settimeout(TIME_OUT)
        print(f'[] Listening at {PORT}')

    def process(self, client):
        try:
            req = client.get_request()
            webserver, port = get_request_detail(req)
            if webserver in blacklist:
                print('Forbidden website')
                client.send_response(FORBIDDEN_MESSAGE.encode())
            else:
                host = Host(webserver, port)
                host.connect()
                host.send_request(req)
                res = host.get_response()
                client.send_response(res)
            host.close()
            client.close()
            print('--- Connection closed\n')
        except:
            pass

    def start(self):
        while True:
            client = Client(self.s)
            thread = threading.Thread(target=ProxyServer.process, args=(self, client))
            thread.setDaemon(True)
            thread.start()


def get_request_detail(msg):
    try:
        url = msg.split()[1].decode()
        http_pos = url.find("://")

        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos + 3):]

        port_pos = temp.find(':')
        webserver_pos = temp.find('/')

        if webserver_pos == -1:
            webserver_pos = len(temp)

        if port_pos == -1 or webserver_pos < port_pos:
            port = 80
            webserver = temp[:webserver_pos]

        else:
            port = int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]

        return webserver, port
    except:
        pass


server = ProxyServer()
server.start()
