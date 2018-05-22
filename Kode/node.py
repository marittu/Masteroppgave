from peer import PeerManager
from blockchain import Block, Blockchain

from consensus import Validator
from storage import Proposed_blocks_log, Blockchain_log, clean_string, string_to_block
from transactions import get_transaction
import messages

import time, random, pickle

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
    def __init__(self, host_ip, hostport, nodeid, config_log, public_key, private_key):
        """
        Subclass of PeerManager
        peers_alive holds the time of last pong message for all connected peers
        """
        super().__init__(host_ip, hostport, nodeid, public_key)
        self.peers_alive = {}
        self.blockchain_log = Blockchain_log(str(hostport)) #WRITE GENESIS BLOCK TO LOG - CHIAN UPDATED IN SM IF COMMIT INDEX > LAST APPLIED
        self.proposed_block_log = Proposed_blocks_log(str(hostport))
        self.head_block = None
        self.nodeid = nodeid
        self.config_log = config_log 
        self.private_key = private_key  
        self.public_key = public_key
        self.time_of_last_transaction = 0
        self.transactions = []
        self.transaction_file = 'Testdata/'+str(hostport)+'.csv'
        self.i = 0
        self.validator = Validator(self.nodeid, self.reactor, self.connections, self.blockchain_log, self.proposed_block_log, hostport)
        self.get_head_block_and_index() #TODO; MAKE OWN FUNCTION ONLY RUNNING AT INIT
        self.validator.commit_index = self.blockchain_log.last_index()
        #self.wallet/bill iou
        LoopingCall(self.state_machine).start(2) 
        LoopingCall(self.get_transaction).start(10)
        
        
    def state_machine(self):
        """
        Triggered by a loopingcall every second 
        Handles the consensus process, based on nodes validator state
        Write new updates to log 
        """
        if self.validator.state == LEADER:
            
            transaction = [] 
            if len(self.transactions) == 4:# or smart_contract: 
                if True:#settle(self.transactions):
                    propose_block = Block(transactions=self.transactions)

                    self.transactions = []
                    self.get_head_block_and_index()
                    propose_block.propose_block(self.head_block)
            else:
                propose_block = None 

            self.validator.append_entries(propose_block)
            if propose_block is not None:
                self.validator.last_log_index += 1
                self.validator.last_log_term = self.validator.current_term
                self.validator.proposed_block_log.write(self.validator.current_term, self.validator.last_log_index, propose_block)
                self.validator.start_block_timeout() 
            
            if self.validator.block_majority():
                if self.validator.block_timeout != None:
                    self.validator.stop_block_timeout()
                self.commit_index = self.validator.last_log_index

        
        if self.validator.state == FOLLOWER:
            if self.validator.propose_block is not None:
                #MAEK VALIDATE BLOCK AND ADD BLOCK METHOD
                self.get_head_block_and_index()
                if self.validator.propose_block.validate_block(self.head_block):
                    print('NEW BLOCK')
                    self.validator.last_log_index += 1
                    self.validator.last_log_term = self.validator.block_term
                    self.validator.proposed_block_log.write(self.validator.block_term, self.validator.last_log_index , self.validator.propose_block)
                else:
                    if self.validator.propose_block.index == self.validator.last_log_index + 1:
                        self.validator.proposed_block_log.update_index()
                    
        #MAKE ADD BLOCK TO BLOCKCHAIN METHOD
        if self.validator.commit_index > self.blockchain_log.last_index():
            index = self.blockchain_log.last_index() + 1
            while index <= self.validator.commit_index:
                block = self.validator.proposed_block_log.get_block(index)
                if block is not None:
                    self.blockchain_log.write(block)
                    index = self.blockchain_log.last_index() + 1 
                else:
                    break
        
    def get_transaction(self):
        if self.validator.leader_conn:       
            tx = get_transaction(self.transaction_file, self.time_of_last_transaction)
            self.time_of_last_transaction = tx[0]
            msg = {
            'msgtype': 'tx',
            'nodeid': self.nodeid,
            'time': tx[0],
            'consumed': tx[1],
            'produced': tx[2]

            }
            messages.send_to_conn(msg, self.validator.leader_conn)


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
        elif msg_type == "tx":
           if self.validator.state == LEADER:
            self.transactions.append([msg['nodeid'], msg['consumed'], msg['produced']])

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

    def add_conn(self, conn, key):
        """
        Helper function for updating of connected nodes in validator
        """
        Validator.new_connection(self.validator, conn, key)

