from peer import PeerManager
from blockchain import Block, Blockchain

from consensus import Validator
from storage import Proposed_blocks_log, Blockchain_log, clean_string, string_to_block
import messages

import time, random

from twisted.internet import reactor
from twisted.internet.task import LoopingCall

PING_INTERVAL = 10
TIMEOUT = 3 * PING_INTERVAL
MAX_PEERS = 5

FOLLOWER = 1
CANDIDATE = 2
LEADER = 3

"""
CORNER CASE - NEW NODES AND ELECTION HAPPENING AT THE SAME TIME
"""

class Node(PeerManager):
    def __init__(self, hostport, nodeid, config_log):
        """
        Subclass of PeerManager
        peers_alive holds the time of last pong message for all connected peers
        """
        super().__init__(hostport, nodeid)
        self.peers_alive = {}
        self.blockchain_log = Blockchain_log(str(hostport)) #WRITE GENESIS BLOCK TO LOG - CHIAN UPDATED IN SM IF COMMIT INDEX > LAST APPLIED
        self.proposed_block_log = Proposed_blocks_log(str(hostport))
        self.head_block = None
        self.config_log = config_log 
        
        self.i = 0
        self.validator = Validator(self.nodeid, self.reactor, self.connections, self.config_log, self.proposed_block_log, hostport)
        self.get_head_block_and_index() #TODO; MAKE OWN FUNCTION ONLY RUNNING AT INIT
        self.validator.commit_index = self.blockchain_log.last_index()
        LoopingCall(self.state_machine).start(4) 
        
        

    def state_machine(self):
        """
        Triggered by a loopingcall every second 
        Handles the consensus process, based on nodes validator state
        Write new updates to log 
        """

        #All server broadcast tx to mempool

        if self.validator.state == LEADER:
             
            propose_block = None #get_new_block()
            if self.i == 3:
                propose_block = Block(random.randint(1,100))
                self.get_head_block_and_index()
                propose_block.propose_block(self.head_block)
                self.i = 0
            self.validator.append_entries(propose_block)
            if propose_block is not None:
                self.validator.last_log_index += 1
                self.validator.last_log_term = self.validator.current_term
                self.validator.proposed_block_log.write(self.validator.current_term, self.validator.last_log_index, propose_block)
                self.validator.start_block_timeout() 
            self.i += 1
            
            if self.validator.block_majority():
                if self.validator.block_timeout != None:
                    self.validator.stop_block_timeout()
                self.commit_index = self.validator.last_log_index

        
        if self.validator.state == FOLLOWER:
            if self.validator.propose_block is not None:
                print("PROPOSE BLOCK")
                print(self.validator.propose_block.index)
                self.get_head_block_and_index()
                print("HEAD BLOCK")
                print(self.head_block.index)
                print("VALIDATION", self.validator.propose_block.validate_block(self.head_block))
                if self.validator.propose_block.validate_block(self.head_block):
                    self.validator.accepted_block = True
                    self.validator.last_log_index += 1
                    self.validator.last_log_term = self.validator.block_term
                    self.validator.proposed_block_log.write(self.validator.block_term, self.validator.last_log_index , self.validator.propose_block)
                else:
                    self.validator.accepted_block = False

        if self.validator.commit_index > self.blockchain_log.last_index():
            index = self.blockchain_log.last_index() + 1
            while index <= self.validator.commit_index:
                block = self.validator.proposed_block_log.get_block(index)
                if block is not None:
                    self.blockchain_log.write(block)
                    index = self.blockchain_log.last_index() + 1 
                else:
                    break



    def get_head_block_and_index(self):
        """
        Read last index in log and head block
        Create log and write gensis block to log if it does not exist
        """
        try:
            line = self.validator.proposed_block_log.read().split(',')
            self.validator.last_log_index = int(clean_string(line[0]))
            self.validator.last_log_term = int(clean_string(line[1]))
            
            self.head_block = string_to_block(line[2:])
             
            
        except:
            print("except in get block and index")
            self.write_genesis()
    
    def get_vote(self):
        line = self.validator.proposed_block_log.read().split(',')
        #self.validator.voted_for = line[2]

    def write_genesis(self):
        block = Block()
        self.validator.last_log_index = 1
        self.head_block = block.get_genesis()
        self.head_block.print_block()
        self.validator.proposed_block_log.write(0, self.validator.last_log_index, self.head_block)
        self.blockchain_log.write(self.head_block)

    def consensus_message(self, msg_type, msg, conn):
        """
        Handles consensus messages from other nodes
        """
        if msg_type == "append_entries":
            self.validator.respond_append_entries(msg, conn)
        elif msg_type == "respond_append_entries":
            self.validator.receive_append_entries_response(msg, conn)
        elif msg_type == "request_vote":
            self.validator.respond_request_vote(msg, conn)
        elif msg_type == "respond_request_vote":
            self.validator.receive_vote(msg)    

    def receive_pong_message(self, msg):
        """
        Update peer_alive dict with time of last pong message and check if all connections are alive
        """
        self.peers_alive.update({msg['nodeid']:msg['time']})
        self.check_connections_alive()

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

    def del_conn(self, conn):
        """
        Helper function for updating of connected nodes in validator
        """
        Validator.delete_connection(self.validator, conn)

    def add_conn(self, conn):
        """
        Helper function for updating of connected nodes in validator
        """
        Validator.new_connection(self.validator, conn)






    def receive_block(self, msg):
        """
        Validate block and add to chain
        """
        block = msg['data']
        block.print_block()
        if block.validate_block(self.head_block):
            self.blockchain.add_block(block)
            self.head_block = block #Move when add_block is moved
        else:
            #Temporary until consensus
            self.req_head_block()
            #raise ValueError('Block Invalid')
        
        #TODO: combine with chain_req. If head_block is same return (y), else see if block in chain and return (a given amount of) blocks in chain  
    def receive_head_block_req(self, conn, msg):
        """
        Message from other peer requesting head block
        """
        headblock = msg['headblock']
        if self.blockchain.head_block_in_chain(headblock):
            msg = {
                'msgtype': 'head_block', 
                'data': self.head_block
            }
            messages.send_to_conn(msg, conn)
        else:
            print("Wrong chain") #TODO handle

    def receive_head_block(self, msg, conn):
        """
        Comparing received head block and request blockchain if not the same
        """
        block = msg['data']

        #Expand to have at least same as three nodes, counter? 
        if self.head_block.assert_equal(block):
            pass

        else:
            msg = {'msgtype':'req_blockchain'}
            messages.send_to_conn(msg, conn)

    def receive_chain_req(self, conn):
        """
        Send blockchain to peer requesting it
        """

        msg = {
            'msgtype': 'blockchain', 
            'data': self.blockchain
        }
        messages.send_to_conn(msg, conn)

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

    def broadcast_block(self):
        """
        Broadcast proposal block with random transactions at random interval
        """
        block = Block(random.randint(1,100))
        block.propose_block(self.head_block)
        msg = {
            'msgtype': 'block', 
            'data': block
        }
        messages.broadcast(msg, self.connections)
        
    def req_head_block(self,):
        msg = {
            'msgtype': 'req_head_block', 
            'headblock': self.head_block
        }
        messages.send_to_peer(msg, self.connections, self.own_connection)
