from threading import Thread 
import socket
import socketserver
import time
import sys

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

class Server():
    def __init__(self):
        self.alive = True
        self.ip = get_ip()

        self.broadcaster = Thread(target=self.broadcast_alive)
        self.broadcaster.daemon = True
        self.broadcaster.start()
       
        self.server = ThreadedTCPServer((self.ip, 50505), RequestHandler)
        self.server.port = 50505
        self.server.clients = {}
        self.server.peers = []
        #self.server.master = self     
        #self.server.peers.append((self.ip, 50505))
        self.server.serve_forever()
    
    def get_clients(self):
        return self.server.clients
    
    
    def broadcast_alive(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while (self.alive):
            sock.sendto(('master').encode('utf-8'), ('255.255.255.255', 40404))
            time.sleep(1)


    def disconnect(self):
        self.alive = False
        self.broadcaster.join()
    
class Client():
    def __init__(self, host, server_port):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        #self.host = host
        #self.server_port = server_port
        #print(self.host, ":", self.server_port)
        self.connection.connect((host, server_port))

    def disconnect(self):
        self.connection.close()

    def message_handler(self, message):
        pass

    def send_message(self, msg):
        #while True:
        
        self.connection.sendall(bytes(msg, 'utf-8'))
            #response = str(self.sock.recv(1024), 'utf-8')
            #print("Received: {}".format(response))
       

    def receive_message(self):
        
        data = self.connection.recv(1024)
        return data
        #print(str(data, 'utf-8'))

    #def run(self):
    #    self.alive = True
        #self.worker = Msg_receiver()

class RequestHandler(socketserver.BaseRequestHandler):
    def setup(self):
        """
        Self is the client connecting to the server.
        Client address and port is added to the servers client list.
        """
        self.ip = self.client_address[0]
        self.port = self.client_address[1]
        self.connection = self.request #TCP socket object for the client
        self.server.clients[(self.ip, self.port)] = self
        self.server.peers.append((self.connection)) 
        for client in self.server.clients:
            print("Connected client: ", client)

        #for peer in self.server.peers:
        #    print("Peers: ", peer)

    def handle(self):
        connected = True
        while connected:
            try:
                received_string = self.request.recv(1024)

                if (received_string):
                    print(str(received_string, 'utf-8'))
                    #print(self.request)

                    for peer in self.server.peers:
                        if peer != self.request:
                            peer.send(received_string)
                else:
                    connected = False
            except:
                print("failed connection")
                connected = False
                break
            

    def finish(self):
        pass


    def send_msg(self, data):
        self.connection.send(bytes(data, 'utf-8'))

    def broadcast_peers(self):
        pass


class Msg_receiver(Thread):
    def __init__(self, connection):
        self.connection = connection
        
        while True:
            #print("Running Msg_receiver")
            data = self.connection.recv(4096)
            print(str(data, 'utf-8'))

class Msg_sender(Thread):
    def __init__(self, connection):
        self.connection = connection
       
        while True:
            #print("Running Msg_sender")
            msg = input("")
            connection.send(bytes(msg, 'utf-8'))
            #self.connection.sendall(bytes(msg, 'utf-8'))


def socket_setup(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
    sock.settimeout(3)
    return sock

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

if __name__ == "__main__":

    master_sock = socket_setup(40404)

    try: 
        master_address = master_sock.recvfrom(4096)[1]
        state = 'slave'
    except socket.timeout:
        state = 'master'

    master_sock.close()

    if state == 'master':
        try: 

            print("Server")
            server = Server()
        except KeyboardInterrupt:
            sys.exit(0)

    else:
        try:
            print("client") 
            client = Client(master_address[0], 50505)
            
            while  True:
            
                msg = input("")
                print(msg)
                if not msg:
                    break
                client.send_message(msg)

                data = client.receive_message()
                if not data:
                    break
                print(str(data,'utf-8'))
               
        except KeyboardInterrupt:
            client.disconnect()
            sys.exit(0)
