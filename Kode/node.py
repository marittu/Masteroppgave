from peer import PeerManager
from blockchain import Block, Blockchain
import time, random

from twisted.internet import reactor
from twisted.internet.task import LoopingCall

PING_INTERVAL = 10
TIMEOUT = 3 * PING_INTERVAL
MAX_PEERS = 5


"""
TODO: Make request own function. Make function for requesting chain from  a specific block 
-E.g. send own headblock, receving node validates that headblock in chain, sends a given amount of 
blocks back to the node
"""

class Node(PeerManager):
    def __init__(self, hostport, nodeid):
        """
        Subclass of PeerManager

        peers_alive holds the time of last pong message for all connected peers
        """
        super().__init__(hostport, nodeid)
        self.peers_alive = {}
        self.blockchain = Blockchain()
        self.head_block = self.blockchain.get_head_block()
        self.blockchain.print_chain()
        

    def receive_pong_message(self, message):
        """
        Update peer_alive dict with time of last pong message and check if all connections are alive
        """
        self.peers_alive.update({message['nodeid']:message['time']})
        self.check_connections_alive()

    def receive_block(self, message):
        """
        Validate block and add to chain
        """
        block = message['data']
        block.print_block()
        if block.validate_block(self.head_block):
            #TODO: Consensus
            #if blockchain.consensus()#
            self.blockchain.add_block(block)
            self.head_block = block #Move when add_block is moved
        else:
            raise ValueError('Block Invalid')
            
        #self.blockchain.print_chain()
        
        #TODO: combine with chain_req. If head_block is same return (y), else see if block in chain and return (a given amount of) blocks in chain  
    def receive_head_block_req(self, conn, msg):
        """
        Message from other peer requesting head block
        """
        headblock = msg['headblock']
        if self.blockchain.head_block_in_chain(headblock):
            msg = {'msgtype': 'head_block', 'data': self.head_block}
            self.send_to_conn(msg, conn)
        else:
            print("Wrong chain") #TODO handle

    def receive_head_block(self, msg, conn):
        """
        Comparing received head block and request blockchain if not the same
        """
        block = msg['data']

        #Expand to have at least same as three nodes, counter? 
        if self.head_block.assert_equal(block):
            if not self.b_call.running:
                self.b_call.start(10)

        else:
            msg = {'msgtype':'req_blockchain'}
            self.send_to_conn(msg, conn)

    def receive_chain_req(self, conn):
        """
        Send blockchain to peer requesting it
        """

        msg = {'msgtype': 'blockchain', 'data': self.blockchain}
        self.send_to_conn(msg, conn)

    def receive_chain(self, msg):
        """
        Update blockchain and set new head block
        """
        self.blockchain = msg['data']
        self.blockchain.print_chain()

        if self.blockchain.validate_blockchain():
            self.head_block = self.blockchain.get_head_block()
            #See if another node has a more recent block
            self.req_head_block()
        else:
            raise ValueError('Blockchain Invalid')


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
        
    def broadcast_block(self):
        """
        Broadcast proposal block with random transactions at random interval
        """
        block = Block(random.randint(1,100))
        block.propose_block(self.head_block)
        msg = {'msgtype': 'block', 'data': block}
        self.broadcast(msg)
        
    def req_head_block(self,):
        msg = {'msgtype': 'req_head_block', 'headblock': self.head_block}
        self.send_to_peer(msg)


if __name__ == '__main__':
    main()