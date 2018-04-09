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
import time, random, pickle
import messages

FOLLOWER = 1 # move to config file
CANDIDATE = 2
LEADER = 3

class Validator():
    """
    Class for all nodes participating in consensus process
    """
    def __init__(self, nodeid, reactor, connections, log, own_connection):
     
        self.reactor = reactor
        self.nodeid = nodeid 

        self.log = log
        self.state = FOLLOWER #MAke None and become follower when up to date
        self.voted_for = None #update on stable storage
        self.votes = 0
    
        self.current_term = 0 #update on stable storage        
        self.last_log_index = 1 #highest log entry known, not yet commited (latest validated propose_block), 1 because node_id at 0
        self.last_log_term = 0 #term of last_log_index
        self.last_commited = 0 #highest log entry applied to state machine (index of head_block)
      
        self.leader_conn = None
        self.leader_id = None

        self.connections = connections
        self.own_connection = own_connection

        self.election_timeout = None        
        self.reset_election_timeout()
        #self.append_entries_lc = LoopingCall(self.append_entries)
       
        #If a new node joins the system, have variable sync = False until leader validates node is up to date
        #Up to date requires same blockchain, and possible new pre-commits
      
       
    def request_votes(self):
        msg = {'msgtype': 'request_vote', 'term': self.current_term, 'candidate_id': self.nodeid, 'last_log_index': self.last_log_index, 'last_log_term': self.last_log_term}
        messages.broadcast_to_followers(msg, self.connections, self.nodeid)


    def respond_request_vote(self, msg, conn):
        """
        Respond to candidates request to become leader
        New nodes not updated are not allowed to participate in voting
        If candidate is not up to date in term or log, dismiss vote
        """
        if self.state is not None:
            if msg['term'] < self.current_term:
                """
                Candidates term is less than this nodes, cannot become leader
                """
                respond_msg = {'msgtype': 'respond_request_vote', 'vote': 'false', 'node': self.nodeid}
                self.send_to_conn(respond_msg, conn, self.own_connection)
            
            elif msg['term'] > self.current_term:
                """
                New term so node can vote again
                """ 
                self.voted_for = None
                self.current_term = msg['term']


            if (self.voted_for == None or self.voted_for == msg['candidate_id']) and (msg['last_log_index'] >= self.last_log_index \
                and msg['last_log_term'] >= self.last_log_term):
                """
                If node has not already voted in this term, and the candidates log is up to date, 
                vote for candidate
                If already voted for this candidate, resend vote
                """
                self.voted_for = msg['candidate_id']
                respond_msg = {'msgtype': 'respond_request_vote', 'vote': 'true', 'node': self.nodeid}
                messages.send_to_conn(respond_msg, conn)

            else:
                """
                If node already voted for someone else this term, or candidates log is not up to date,
                cannot vote for this candidate
                """
                respond_msg = {'msgtype': 'respond_request_vote', 'vote': 'false', 'node': self.nodeid}
                messages.send_to_conn(respond_msg, conn, self.own_connection)
                

    def receive_vote(self, msg):
        """
        Recive votes from other nodes
        Become leader if majority of votes
        """
        if self.state is not LEADER:  
            if msg['vote'] == 'true':
                self.votes += 1
            if self.votes > int((len(self.connections))/2): 
            #TODO: subtract voters not allowed to participate yet
                self._become_leader()

    def append_entries(self):
        """
        Send append entries RPC to followers 
        May or may not contain new blocks 
        """
        msg = {'msgtype': 'append_entries', 'leaderid': self.nodeid, 'term': self.current_term}
        """
        prev_log_index, prev_log_term, tx, leader_commit_index
        latest block waiting for conf,  new tx, head_block of BC
        """
        messages.broadcast_to_followers(msg, self.connections, self.nodeid)

    def respond_append_entries(self, msg, conn):
        """
        If 
        """
        self.reset_election_timeout()
        if self.state is not None:
            
            if msg['leaderid'] != self.leader_id:
                self.leader_conn = conn
                self.leader_id = msg['leaderid']
            
            if msg['term'] > self.current_term:
                self._back_to_follower()
                self.current_term = msg['term']

            if msg['term'] == self.current_term:
                if self.state == CANDIDATE:
                    self.state = FOLLOWER
                    print("FOLLOWER")

                     
        """
        reply with current term so leader can update
        success = true if matching prev_log_term and prev_log_index
        false if term < currentTerm or log doesnæt contain an entry at prev_log_index 
        whose term matches perv_log_term
        if existing entry conflicts with new one (same index but different term), delete 
        existing entry and all that follow it
        append new entrues not allready in log
        if leadercommit > commitindex -> commitIndex = min(leadercommit, index of last new entry)
        """

    def receive_append_entries_response(self, msg, conn):
        pass

    def _become_leader(self):
        """
        Change state to leader, stop election_timeout and broadcast self as leader to network
        """
        print("LEADER")
        self.state = LEADER
        if self.election_timeout != None: self.election_timeout.cancel()
        self.election_timeout = None
         
        self._reset_votes()     
        self.append_entries()

        #TODO: Initialize view of others

    def _reset_votes(self):
        self.votes = 0
        self.voted_for = None

    def _back_to_follower(self):
        self.state = FOLLOWER
        print("FOLLOWER")
        self._reset_votes()

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
        
        self.votes = 1
        self.current_term += 1
        self.voted_for = self.nodeid
        #TODO: Save above info to disk
        if len(self.connections) == 1:
            self._become_leader()
        else:
            self.request_votes()

    def new_connection(self, conn):
        """
        Helper function for adding new connections
        """
        self.connections.update(conn)

    def delete_connection(self, conn):
        """
        Helper function for deleting old connections
        """
        self.connections.pop(conn)