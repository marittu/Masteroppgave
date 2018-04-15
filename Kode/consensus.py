"""
TX shared in local mempool - broadcasted to everyone
Leader proposes new block
Followers and candidates verify new block and respond to leader with vote
(Weigh votes, so nodes with tx in block are more weighted - stake)
Leader needs 2/3 of votes before broadcasting the new block

Validate TX by checking signature on smart contract or smart contract 
exists, sequence number, valid coins
"""

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
import time, random, pickle, string
import messages
from storage import Vote

FOLLOWER = 1 # move to config file
CANDIDATE = 2
LEADER = 3

class Validator():
    """
    Class for all nodes participating in consensus process
    """
    def __init__(self, nodeid, reactor, connections, config_log, proposed_block_log, hostport):
        
        self.reactor = reactor
        self.nodeid = nodeid 

        self.config_log = config_log
        self.proposed_block_log = proposed_block_log #INITIALIZE LOG HERE? TRY TO READ AND IF NOT MAKE NEW WITH EMPTY FIRST VOTE
        self.vote_log = Vote(hostport)
        self.state = FOLLOWER #Make None and become follower when up to date
        
        self.votes = 0
        self.voted_for = None
        self.current_term = 0
        try: 
            self._read_vote_log() #Update self.current_term and self.voted_for from stable storage
        except:
            self.vote_log.write({self.current_term: self.voted_for})
        
        self.last_log_index = 0 #highest log entry known, not yet commited (latest propose_block)
        self.last_log_term = 0 #term of last log index
        self.block_term = 0
        self.commit_index = 0 #highest log entry applied to state machine (index of head_block)
        
        self.leader_conn = None
        self.leader_id = None

        #Leader's view on followers
        self.match_index = {}
        self.next_index = {}

        #Used for sending messages
        self.connections = connections
        #self.followers = {} MAYBE USE TO EXTRACT NODES WITH NONE STATE

        self.election_timeout = None        
        self.reset_election_timeout()
       
        self.accepted_block = None
        self.propose_block = None
        #If a new node joins the system, have variable sync = False until leader validates node is up to date
        #Up to date requires same blockchain, and possible new pre-commits

 

    def append_entries(self, propose_block):
        """
        Send append entries RPC to followers 
        May or may not contain proposed blocks or blocks ready to be commited to Blockchain
        """
        #MOVE ALL MSG TO MESSAGES MODULE
        for nodeid, conn in self.connections.items():
            if nodeid != self.nodeid:
                prev_term = self.last_log_term
                block_term = self.current_term
                index = self.last_log_index
                if self.next_index[nodeid] < self.last_log_index + 1:
                    index = self.next_index[nodeid] - 1
                    res = self.proposed_block_log.get_block_term_from_index(self.next_index[nodeid])
                    if res != None:
                        prev_term = int(res[0])
                        block_term = int(res[1])
                        propose_block = res[2]
                msg = {
                    'msgtype': 'append_entries', 
                    'term': self.current_term,
                    'leaderid': self.nodeid, 
                    'prev_index': index, #index of prev proposed block
                    'prev_term': prev_term,   #term of prev proposed block
                    'leader_commit': self.commit_index, #Index of proposed block ready for commiting to chain
                    'propose_block': propose_block,
                    'block_term': block_term
                } 

                messages.send_to_conn(msg, conn)
        
        

    def respond_append_entries(self, msg, conn):
        """
        Must be follower or candidate to act on message
        Respond sucess = false if term < current term or 
        log doesn't contain an entry at prev_log_index matching term of prev_log_term,
        meaning the follower is not up to date
        Respond to leader with own log info
        """
        self.reset_election_timeout()
        if self.state is not None:

            success = True
            print(msg)

            #New leader
            if msg['leaderid'] != self.leader_id:
                self.leader_conn = conn
                self.leader_id = msg['leaderid']
                
                if msg['term'] > self.current_term:
                    self._follower_new_term() 
                    self.current_term = msg['term']
                
                #Step down from candidate because recognized a new leader 
                elif msg['term'] == self.current_term and self.state == CANDIDATE:
                        self.state = FOLLOWER
                        print("FOLLOWER")

            if msg['term'] < self.current_term:
                success = False 

            #interate through log in reverse until index match, if term doesnt match for index - FALSE
            entry = self.proposed_block_log.find_index_term(msg['prev_index'], msg['prev_term'])
            #print('Entry', entry)
            if entry == None:
                #No entry for index
                success = False
            elif entry == False:
                #print(msg['prev_index'], msg['prev_term'])
                #print(self.last_log_index, self.last_log_term)
                print("Updated log")
                num_lines = self.last_log_index - msg['prev_index'] + 1
                print(num_lines)
                self.proposed_block_log.update_index(num_lines)
                success = True
                #Update entry and delete following entries
            elif entry == True:
                #Log up to date
                success = True
                
            #Set below variables and handle in state machine in node 
            #Append new entries not already in log
            self.propose_block = msg['propose_block']
            if self.propose_block != None:
                #self.propose_block.print_block()
                #print(self.propose_block)
                #self.block_term = msg['prev_term']
                self.last_log_index = msg['prev_index'] + 1
                self.block_term = msg['block_term']
                #validate
            else:
                self.propose_block = None
        
            if msg['leader_commit'] > self.commit_index:
                pass 
                #self.commit_index = min(leadercommit, index of last proposed block in log)
                #Commit proposed_block at commit_index (and previous blocks) to blockchain
            #if log doesn't contain an entry at prev_log_index  whose term matches perv_log_term
                #success = False
        msg = { 
            'msgtype': 'respond_append_entries', 
            'nodeid': self.nodeid, 
            'success': success,
            'current_term': self.current_term,
            'last_term': self.last_log_term,
            'last_index': self.last_log_index
        }

        messages.send_to_conn(msg, conn)


    def receive_append_entries_response(self, msg, conn):
        
        nodeid = msg['nodeid']
        if msg['success'] == True:
            self.match_index[nodeid] = msg['last_index']
            self.next_index[nodeid] = msg['last_index'] + 1
            
            if self.next_index[nodeid] < self.last_log_index +1:
                print("Found match but need blocks")
                res = self.proposed_block_log.get_block_term_from_index(self.next_index[nodeid])
                term = res[0] 
                propose_block = res[1]
                #propose_block.print_block()
                
    
        else:
            self.next_index[nodeid] = self.next_index[nodeid] - 1
            res = self.proposed_block_log.get_block_term_from_index(self.next_index[nodeid])
            if res is not None:
                term = res[0] 
                propose_block = None#res[1]
   
           
       
    def request_votes(self):
        #get_log() for prev_log
        msg = {
            'msgtype': 'request_vote', 
            'term': self.current_term, 
            'candidate_id': self.nodeid, 
            'last_log_index': self.last_log_index, 
            'last_log_term': self.last_log_term
        }
        messages.broadcast_to_followers(msg, self.connections, self.nodeid)


    def respond_request_vote(self, msg, conn):
        """
        Respond to candidates request to become leader
        New nodes not updated are not allowed to participate in voting
        Grant vote if candidates term valid and log at least as up to date as node   
        """
        vote_granted = False
        if (msg['term'] > self.current_term or (msg['term'] == self.current_term and \
        (self.voted_for == None or self.voted_for == msg['candidate_id'] ))):
            
            if msg['last_log_index'] >= self.last_log_index and \
            msg['last_log_term'] >= self.last_log_term:
        
                vote_granted = True
                self.voted_for = msg['candidate_id']
                
                self.vote_log.write({self.msg['term']: self.voted_for})


        respond_msg = {
                'msgtype': 'respond_request_vote', 
                'vote_granted': vote_granted,
                'node': self.nodeid,
                'term': self.current_term
        }

        messages.send_to_conn(respond_msg, conn) 
        if msg['term'] > self.current_term:
            self.current_term = msg['term']        

    def receive_vote(self, msg):
        """
        If another node has a higher term, node cannot become leader
        Ignore votes if node is already leader
        Recive votes from other nodes
        Become leader if majority of votes
        """
        if msg['term'] <= self.current_term and self.state is not LEADER:  
            if msg['vote_granted']:
                self.votes += 1 
            if self.votes > int((len(self.connections))/2): 
                print(len(self.connections))
            #TODO: subtract voters not allowed to participate yet
                self._become_leader()


    def _become_leader(self):
        """
        Change state to leader, stop election_timeout and broadcast self as leader to network
        """
        print("LEADER")
        print(self.votes)
        self.state = LEADER
        if self.election_timeout != None: self.election_timeout.cancel()
        self.election_timeout = None
              
        self._initialize_views()
        self.append_entries(propose_block=None) #Send empty message to assert leadership
        

    def _initialize_views(self):
        for conn in self.connections:
            self.next_index[conn] = self.last_log_index + 1 #index of next log entry to send to each node
            self.match_index[conn] = 0 #index of highest log entry know to be replicated on server


    def _follower_new_term(self):
        self.state = FOLLOWER
        print("FOLLOWER")
        self.votes = 0
        self.voted_for = None

    def reset_election_timeout(self):
        """
        Cancel current election_timeout and start again
        """

        if self.state == FOLLOWER or self.state == CANDIDATE:
            if self.election_timeout != None and self.election_timeout.active():
                self.election_timeout.cancel() 

            self.election_timeout = self.reactor.callLater(5 + random.randint(300,500)/1000.0, self.start_leader_election)

    def start_leader_election(self):
        """
        Election timeout occured, node is candidate to become leader
        Vote for self
        Become leader if only node in network or request vote from followers
        New timeout may occure if election process takes to long, due to e.g. split votes
        """
        self.reset_election_timeout()
        print("CANDIDATE")
        self.state = CANDIDATE
        
        self.current_term += 1
        self.voted_for = self.nodeid
        self.votes = 1
    
        print(self.current_term)
        self.vote_log.write({self.current_term: self.voted_for})
        if len(self.connections) == 1:
            self._become_leader()
        else:
            self.request_votes()

    def new_connection(self, conn):
        """
        Helper function for adding new connections
        """
        self.connections.update(conn)
        if self.state == LEADER:
            for nodeid in conn:
                self.next_index[nodeid] =  self.last_log_index + 1
                self.match_index[nodeid] = 0

    def delete_connection(self, conn):
        """
        Helper function for deleting old connections
        """
        self.connections.pop(conn)
        if self.state == LEADER:
            self.next_index.pop(conn)
            self.match_index.pop(conn)

    
    def _read_vote_log(self):
        """
        Helper function for updating current_term and voted_for from log
        """
        votes = self.vote_log.read()
        
        self.current_term = int(votes.split(':')[0].strip('{'))
        voted = votes.split(':')[1]
        strip = " '}'"
        self.voted_for = str(voted).translate(str.maketrans('', '', strip))
       
        