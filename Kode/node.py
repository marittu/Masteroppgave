from peer import PeerManager
from blockchain import Block, Blockchain
import time, random

from twisted.internet import reactor
from twisted.internet.task import LoopingCall

PING_INTERVAL = 10
TIMEOUT = 3 * PING_INTERVAL
MAX_PEERS = 5


class Node(PeerManager):
    def __init__(self, hostport, nodeid):
        """
        Subclass of PeerManager

        peers_alive holds the time of last pong message for all connected peers
        """
        super().__init__(hostport, nodeid)
        self.peers_alive = {}
        self.blockchain = Blockchain()
        self.blockchain.print_chain()
        #reactor.callLater(1, self.broadcast_block)
        #self.b_call = LoopingCall(self.broadcast_block).start(10)

    def receive_pong_message(self, message):
        """
        Update peer_alive dict with time of last pong message and check if all connections are alive
        """
        self.peers_alive.update({message['nodeid']:message['time']})
        self.check_connections_alive()

    def receive_block(self, message):
        block = message['data']
        block.print_block()
        self.blockchain.add_block(block)
        self.blockchain.print_chain()


    def check_connections_alive(self):
        """
        Check if all connections are still alive
        Drop connections if last pong exceeds timeout and ask peers for new connections
        """
        remove = False
        for peer in self.peers_alive:
            last_pong = self.peers_alive[peer]
            if (time.time() - last_pong > TIMEOUT):
                self.remove_peer(peer)
                remove = True
                rem_peer = peer
        #Cannot remove item from dict during iteration
        if remove:
            del self.peers_alive[rem_peer]
            msg = {'msgtype':'req_peers'}
            self.broadcast(msg)

    def get_block(self):
        pass
        
        
    def broadcast_block(self):
        """
        Broadcast new block with random transactions at random interval
        """
        block = Block(random.randint(1,100))
        p_block = self.blockchain.propose_block(block)
        #p_block.print_block()
        #b_dict = p_block.make_dict()
        #print(b_dict)

        msg = {'msgtype': 'block', 'data': p_block}
        self.broadcast(msg)
        

if __name__ == '__main__':
    main()