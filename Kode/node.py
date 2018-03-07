import network
import socket
import sys
from threading import Thread 


class Node():
    def __init__(self, state, master_addr):
        self.alive = False
        self.master_addr = master_addr
        self.state = state

    def run(self):
        self.alive = True
        self.client = network.Client(self.master_addr, 50505)

        self.messenger = Thread(target=network.Msg_receiver, args=(self.client.connection,))
        self.messenger.daemon = True
        self.messenger.start()
        self.sender = Thread(target=network.Msg_sender, args=(self.client.connection,))
        self.sender.daemon = True
        self.sender.start()
         

    def close(self):
        if self.alive:
            self.alive = False
            self.messenger.join()
            self.sender.join()


if __name__ == "__main__":

    master_sock = network.socket_setup(40404)

    try: 
        master_address = master_sock.recvfrom(4096)[1]
        state = 'client'
    except socket.timeout:
        state = 'master'
        master_address = network.get_ip()

    master_sock.close()
    print(state)
    
    if state == 'master':
        try:
            master = network.Server()
        except(KeyboardInterrupt):
            sys.exit(0)

    else:
        try:
            node = Node(state, master_address[0])
            node.run()
            while True:
                pass
        except KeyboardInterrupt:
            node.close()
            sys.exit(0)
