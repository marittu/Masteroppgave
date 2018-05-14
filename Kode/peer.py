from twisted.internet.protocol import Factory, connectionDone
from twisted.protocols.basic import IntNStringReceiver
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint, connectProtocol #Protocol, ClientFactory, ClientCreator
from twisted.internet import reactor, task
from twisted.internet.task import LoopingCall
from twisted.python import log

import time, json, struct, pickle, random
import messages

PING_INTERVAL = 30 * 60
TIMEOUT = 3 * PING_INTERVAL
#MAX_PEERS = 5

class Peer(IntNStringReceiver):
	"""
	Subclass of the protocol IntNStringReceiver.
	Each received message is a callback to the method 'stringReceived'
	Keeps track of information in a connection between two peers
	"""

	#Message format uses little endian, unsigned int
	structFormat = '<I'
	prefixLength = struct.calcsize(structFormat)

	def __init__(self, factory):
		self.factory = factory
		self.nodeid = self.factory.nodeid
		self.remote_nodeid = None
		self.ping = LoopingCall(messages.send_ping, self, self.factory.nodeid)

	def connectionLost(self, reason):
		try:
			self.factory.remove_peer(self.remote_nodeid)
			self.factory.connections.pop(self.remote_nodeid)
			self.factory.delete_conn(self.remote_nodeid)
		except:
			pass
		if self.ping.running:
			self.ping.stop()

	def stringReceived(self, data):
		
		msg = pickle.loads(data)
		msg_type = msg['msgtype']
		if msg_type == 'hello':
			self.handle_hello(msg)

			#Send acknowlege and own peerlist
			messages.send_hello_ack(self, self.factory.nodeid, self.factory.hostport)
			messages.send_peers(self, self.factory.peers)

		elif msg_type == 'ack':
			self.handle_hello(msg)

		
		elif msg_type == 'peer':
			self.handle_peers(msg)

		elif msg_type == 'req_peers':
			messages.send_peers(self, self.factory.peers)

		elif msg_type == 'ping':
			if msg['nodeid'] != self.factory.nodeid:
				messages.send_pong(self, self.factory.nodeid)
				

		elif msg_type == 'pong':
			self.factory.receive_pong_message(msg)
		
		else:
			#Handle other messages in Node/Peer_Factory
			#if msg_type != 'append_entries':print(msg)
			self.factory.parse_msg(msg_type, msg, self) #self is connection received from

	def send_hello(self):
		"""
		Initial hello message needs to be part of protocol to initate callback to start protocol
		"""
		msg = {
			'msgtype': 'hello', 
			'nodeid': self.factory.nodeid, 
			'hostport': self.factory.hostport
		} #Add IP?
		self.sendString(pickle.dumps(msg))


	def handle_hello(self, msg):
		"""
		If not already added peer, add to peers, connections and start pinging
		"""
		self.remote_nodeid = msg['nodeid']
		self.factory.add_peers(self.remote_nodeid, msg['hostport'])
		if self.remote_nodeid not in self.factory.connections:
			if self.remote_nodeid == self.factory.nodeid and self.factory.own_connection == None:
				self.factory.own_connection = self
			
			self.factory.connections.update({self.remote_nodeid: self})
			self.factory.new_conn({self.remote_nodeid: self})

		if not self.ping.running:
				self.ping.start(PING_INTERVAL)  


	def handle_peers(self, msg):
		"""
		Start making blocks if initial node, or request head block if connecting to a node
		Connect to peers received from other node
		"""
	
		for peer in msg['peers']:
			host = msg['peers'][peer]
			#Make connections to peers not already connected too
			if peer not in list(self.factory.connections.keys()):
				self.factory.connect_to_peer(host)
	

class PeerManager(Factory):
	"""
	The PeerManager is responsible for storing information about the node, 
	that is persistant between connections
	"""

	def __init__(self, hostport, nodeid): #peertype
		#include ip in addition to port
		self.hostport = hostport #Port to start node server
		self.nodeid = nodeid #Id of node
		self.peers = {} #Connected peers - used to notify connecting nodes of other peers in network
		self.connections = {} #Conections in network used for messaging
		self.own_connection = None #Servers connection to own client
		self.reactor = reactor
		#self.b_call = LoopingCall(self.broadcast_block) #looping call for testing
		
		self.requested = False
		
	def buildProtocol(self, addr):
		"""
		Builds the protocol that holds the connection between two peers
		"""
		return Peer(self)
		
	def got_protocol(self, p):
		"""
		Callback to start the protocol exchange by sending a hello message.
		"""
		p.send_hello()

	def print_peers(self):
		"""
		Helper function for testign
		"""
		for peer in self.peers:
			print(peer)

	def add_peers(self, peer, hostport):
		"""
		Add new peers if not already added, not self and not connected to max number of peers
		"""
		if peer not in self.peers and hostport != self.hostport:
			print("Added peer:", peer, hostport)
			self.peers[peer] = hostport

	def remove_peer(self, peer):
		"""
		Delete peer from peer list if connection is lost
		"""
		if peer != self.nodeid: #Causes error in disconnection
			try:
				del self.peers[peer]
				print (peer, "disconnected")
			except:
				pass

	def connect_to_peer(self, connect_port):
		"""
		Let client to connect to other nodes pased on port
		"""	
		endpoint = TCP4ClientEndpoint(reactor, '192.168.0.16', connect_port)
		d = connectProtocol(endpoint, Peer(self))
		d.addCallback(self.got_protocol)
		d.addErrback(log.err)

	def parse_msg(self, msg_type, msg, conn):
		"""
		Handle other messages not related to connection
		"""
		if msg_type == "block":
			self.receive_block(msg)
		elif msg_type == 'req_head_block':
			self.receive_head_block_req(conn, msg)
		elif msg_type =="head_block":
			self.receive_head_block(msg, conn)
		elif msg_type == "req_blockchain":
			self.receive_chain_req(conn)
		elif msg_type == "blockchain":
			self.receive_chain(msg)
		elif msg_type == "append_entries" or msg_type == "respond_append_entries"  \
		or msg_type == "request_vote" or msg_type == "respond_request_vote":
			self.consensus_message(msg_type, msg, conn)

	def new_conn(self, conn):
		"""
		Helper function for updating connections in consensus process
		"""
		self.add_conn(conn)

	def delete_conn(self, conn):
		"""
		Helper function for updating connections in consensus process
		"""
		self.del_conn(conn)


	def clientConnectionFailed(self, connector, reason):
		print ('Failed to connect to:', connector.getDestination())
		self.finished(0)

	def run_node(self, hostport, connect_port, nodeid):
		"""
		Start server on host given by user
		Start client and connect to host given by user
		"""
		endpoint = TCP4ServerEndpoint(reactor, hostport)
		d = endpoint.listen(self)
		d.addErrback(log.err)
		
		self.connect_to_peer(connect_port)
		
