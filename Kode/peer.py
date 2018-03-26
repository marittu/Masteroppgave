from twisted.internet.protocol import Factory, connectionDone
from twisted.protocols.basic import IntNStringReceiver
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint, connectProtocol #Protocol, ClientFactory, ClientCreator
from twisted.internet import reactor, task
from twisted.internet.task import LoopingCall
from twisted.python import log

import time, json, struct, pickle, random

PING_INTERVAL = 30 * 60
TIMEOUT = 3 * PING_INTERVAL
#MAX_PEERS = 5

class Peer(IntNStringReceiver):
	"""
	Subclass of the protocol IntNStringReceiver.
	Each received messages is a callback to the method 'stringReceived'
	Keeps track of information in a connection between two peers
	"""

	#Message format uses little endian, unsigned int
	structFormat = '<I'
	prefixLength = struct.calcsize(structFormat)

	def __init__(self, factory):
		self.factory = factory
		self.nodeid = self.factory.nodeid
		self.remote_nodeid = None
		self.ping = LoopingCall(self.send_ping)

	def connectionLost(self, reason):
		
		self.factory.remove_peer(self.remote_nodeid)
		try:
			self.factory.connections.pop(self.remote_nodeid)
		except:
			pass
	
		#Reconnect_loop?

		if self.ping.running:
			self.ping.stop()

	def stringReceived(self, data):
		try: 
			msg = json.loads(data)
		except:
			msg = pickle.loads(data)
		msg_type = msg['msgtype']
		#TODO: better handling of connections
		if msg_type == 'hello':
			self.handle_hello(msg)

			#Send acknowlege and own peerlist
			self.send_hello_ack()
			self.send_peers()

		elif msg_type == 'ack':
			self.handle_hello(msg)

			
		
		elif msg_type == 'peer':
			self.handle_peers(msg)

		elif msg_type == 'req_peers':
			self.send_peers()

		elif msg_type == 'ping':
			if msg['nodeid'] != self.factory.nodeid:
				self.send_pong()
				

		elif msg_type == 'pong':
			self.factory.receive_pong_message(msg)
		
		else:
			#Handle other messages in Node/Peer_Factory
			print(msg)
			self.factory.message_callback(msg_type, msg, self) #self is connection received from


	#Move rest of protocol to messages module

	def send_hello(self):
		msg = {'msgtype': 'hello', 'nodeid': self.factory.nodeid, 'hostport': self.factory.hostport} #Add IP?
		self.send_msg(msg)

	def send_hello_ack(self):
		msg = {'msgtype': 'ack', 'nodeid': self.factory.nodeid, 'hostport': self.factory.hostport} #Add IP?
		self.send_msg(msg)	
	
	def send_peers(self):
		send_msg = {'msgtype':'peer', 'peers': self.factory.peers}
		self.send_msg(send_msg)

	def handle_hello(self, msg):
		"""
		If not already added peer, add to peers, connections and start pinging
		"""
		self.remote_nodeid = msg['nodeid']
		self.factory.add_peers(self.remote_nodeid, msg['hostport'])
		if self.remote_nodeid not in self.factory.connections:
			if self.remote_nodeid == self.factory.nodeid and self.factory.connection == None:
				self.factory.connection = self
			
			self.factory.connections.update({self.remote_nodeid: self})

		if not self.ping.running:
				self.ping.start(PING_INTERVAL) #Ping every 30 minutes (seconds for testing) 


	def handle_peers(self, msg):
		"""
		Start making blocks if initial node, or request head block if connecting to a node
		Connect to peers received from other node
		"""
		if not msg['peers']: 
			self.factory.initial = True
			if not self.factory.b_call.running:
				self.factory.b_call.start(10) #Make variable			
		else: 
			#Connecting to network where a blockchain already exists - needs to be updated
			#Only request from one peer
			if self.factory.requested == False:
				reactor.callLater(1,self.factory.req_head_block)
				self.factory.requested = True

		for peer in msg['peers']:
			host = msg['peers'][peer]
			#Make connections to peers not already connected too
			if peer not in list(self.factory.connections.keys()):
				self.factory.connect_to_peer(host)

	def send_ping(self):
		"""
		Pings from both server and client side TODO fix better ping/pong
		"""
		msg = {'msgtype':'ping', 'time':time.time(), 'nodeid':self.factory.nodeid}
		self.send_msg(msg)

	def send_pong(self):
		msg = {'msgtype':'pong', 'time':time.time(), 'nodeid':self.factory.nodeid}
		self.send_msg(msg)


	def send_msg(self, msg):
		self.sendString(json.dumps(msg).encode('utf-8'))

class PeerManager(Factory):

	def __init__(self, hostport, nodeid): #peertype
		#include ip in addition to port
		self.hostport = hostport #Port to start node server
		self.nodeid = nodeid #Id of node
		self.peers = {} #Connected peers
		self.connections = {} #Make set only containing conn
		self.connection = None
		self.message_callback = self.parse_msg #Handle messages not related to connection
		self.reactor = reactor
		self.initial = False #make on node initial - first to connect
		self.b_call = LoopingCall(self.broadcast_block) #looping call for testing
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
		for peer in self.peers:
			print(peer)

	def add_peers(self, peer, hostport):
		"""
		Add new peers if not already added, not self and not connected to max number of peers
		"""
		if peer not in self.peers and hostport != self.hostport:# and len(self.peers) < MAX_PEERS:
			print("Added peer:", peer, hostport)
			self.peers[peer] = hostport
		#for peer in self.peers:
		#	print("Peer", self.peers.get(peer))
		#print()

	def remove_peer(self, peer):
		"""
		Delete peer from peer list if connection is lost
		"""
		print (peer, "disconnected")
		if peer != self.nodeid: #Causes error in disconnection
			try:
				del self.peers[peer]
			except:
				pass

	def connect_to_peer(self, connect_port):
		"""
		Let client to connect to other nodes pased on port
		"""	
		endpoint = TCP4ClientEndpoint(reactor, '127.0.0.1', connect_port)
		d = connectProtocol(endpoint, Peer(self))
		d.addCallback(self.got_protocol)
		d.addErrback(log.err)
		
	def broadcast(self, msg):
		for _, conn in self.connections.items():
			conn.sendString(pickle.dumps(msg))
		
	def send_to_peer(self, msg):
		"""
		Send a message to a ramdom connected peer that is not self
		"""
		conn = self.connection
		n = len(self.connections) - 1 
		while conn == self.connection:
			peer = random.randint(0, n)
			conn = list(self.connections.values())[peer]

		conn.sendString(pickle.dumps(msg))

	def send_to_conn(self, msg, conn):
		"""
		Send message to a given connection
		"""
		conn.sendString(pickle.dumps(msg))	

	def parse_msg(self, msg_type, msg, conn):
		"""
		Handle other messages not related to connection
		"""
		if msg_type == "block":
			self.receive_block(msg)
		if msg_type == 'req_head_block':
			self.receive_head_block_req(conn, msg)
		if msg_type =="head_block":
			self.receive_head_block(msg, conn)
		if msg_type == "req_blockchain":
			self.receive_chain_req(conn)
		if msg_type == "blockchain":
			self.receive_chain(msg)

	def receive_pong_message(self, message):
		raise NotImplementedError("To be implemented in subclass")

	def receive_block(self, message):
		raise NotImplementedError("To be implemented in subclass")

	def receive_head_block_req(self, conn, msg):
		raise NotImplementedError("To be implemented in subclass")

	def receive_head_block(self, msg, conn):
		raise NotImplementedError("To be implemented in subclass")

	def receive_chain_req(self, conn):
		raise NotImplementedError("To be implemented in subclass")

	def receive_chain(self, msg):
		raise NotImplementedError("To be implemented in subclass")


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
		
		reactor.run()
