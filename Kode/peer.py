from twisted.internet.protocol import Factory, connectionDone
from twisted.protocols.basic import IntNStringReceiver
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint, connectProtocol #Protocol, ClientFactory, ClientCreator
from twisted.internet import reactor, task
from twisted.internet.task import LoopingCall
from twisted.python import log

import time, json, struct, pickle

PING_INTERVAL = 10
TIMEOUT = 3 * PING_INTERVAL
MAX_PEERS = 5

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

	def connectionMade(self):
		pass
		
	def connectionLost(self, reason):
		
		self.factory.remove_peer(self.remote_nodeid)
		try:
			self.factory.connections.pop(self.remote_nodeid)
		except:
			pass
		self.factory.print_peers()
		#Reconnect_loop?

		if self.ping.running:
			self.ping.stop()

	def stringReceived(self, data):
		try: 
			msg = json.loads(data)
		except:
			msg = pickle.loads(data)
		msg_type = msg['msgtype']
		#if msg_type != 'ping' and msg_type != 'pong':
		#	print(msg)
		#else:
		#	pass
			#print(msg)

		if msg_type == 'hello':
			self.remote_nodeid = msg['nodeid']
			self.factory.add_peers(self.remote_nodeid, msg['hostport'])
			if self.remote_nodeid not in self.factory.connections:
				self.factory.connections.update({self.remote_nodeid: self})

			if not self.ping.running:
				self.ping.start(PING_INTERVAL) #Ping every 30 minutes (seconds for testing) 

			#Send acknowlege and own peerlist
			self.hello_ack()
			self.send_peers()
		#TODO: Move duplicate code to handle_hello	
		elif msg_type == 'ack':
			self.remote_nodeid = msg['nodeid']
			self.factory.add_peers(self.remote_nodeid, msg['hostport'])
			if self.remote_nodeid not in self.factory.connections:
				self.factory.connections.update({self.remote_nodeid: self})

			if not self.ping.running:
				self.ping.start(PING_INTERVAL) #Ping every 30 minutes (seconds for testing) 
		
		elif msg_type == 'peer':
			self.handle_peers(msg)

		elif msg_type == 'req_peers':
			self.send_peers()

		elif msg_type == 'ping':
			if msg['nodeid'] != self.factory.nodeid:
				self.send_pong()
				

		elif msg_type == 'pong':
			#print("Pong from ", msg['nodeid'])
			self.factory.receive_pong_message(msg)
		
		else:
			#Handle other messages in Node/Peer_Factory
			print(msg)
			self.factory.message_callback(msg_type, msg)


	#Move rest of protocol to messages module

	def send_hello(self):
		msg = {'msgtype': 'hello', 'nodeid': self.factory.nodeid, 'hostport': self.factory.hostport} #Add IP?
		self.send_msg(msg)

	def hello_ack(self):
		msg = {'msgtype': 'ack', 'nodeid': self.factory.nodeid, 'hostport': self.factory.hostport} #Add IP?
		self.send_msg(msg)	
	
	def send_peers(self):
		send_msg = {'msgtype':'peer', 'peers': self.factory.peers}
		self.send_msg(send_msg)

	def handle_peers(self, msg):
		for peer in msg['peers']:
			host = msg['peers'][peer]
			#Add peer if not self or already added max peers
			if peer not in self.factory.peers and len(self.factory.peers) < MAX_PEERS:
				self.factory.connect_to_peer(self.factory.nodeid, host, peer)

	def send_ping(self):
		"""
		Pings from both server and client side TODO fix better ping/pong
		"""
		msg = {'msgtype':'ping', 'time':time.time(), 'nodeid':self.factory.nodeid}
		self.send_msg(msg)

	def send_pong(self):
		msg = {'msgtype':'pong', 'time':time.time(), 'nodeid':self.factory.nodeid}
		self.send_msg(msg)
		#time.sleep(15)


	def send_msg(self, msg):
		#print(self.pt, "Sending: ", msg)
		self.sendString(json.dumps(msg).encode('utf-8'))

#TODO: Update peerlist of already connected peers when node receives new connection
#TODO: Set limit to number of connected peers. Ask for more peers if connection lost 

class PeerManager(Factory):

	def __init__(self, hostport, nodeid): #peertype
		#include ip in addition to port
		self.hostport = hostport
		self.nodeid = nodeid
		self.peers = {} 
		self.connections = {} #Make set only containing conn
		self.message_callback = self.parse_msg
		self.reactor = reactor
		#incomming/outgoing hosts set()
		#reactor.callLater(1, self.broacast_block)

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
		if peer not in self.peers and hostport != self.hostport and len(self.peers) < MAX_PEERS:
			print("Added peer:", peer, hostport)
			self.peers[peer] = hostport
		for peer in self.peers:
			print("Peer", self.peers.get(peer))

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


	def clientConnectionFailed(self, connector, reason):
		print ('Failed to connect to:', connector.getDestination())
		self.finished(0)

	#def clientConnectionLost(self, connector, reason):
	#	print ('Lost connection.  Reason:', reason)


	def connect_to_peer(self, hostport, connect_port, nodeid):
		"""
		Let client to connect to other nodes pased on port
		"""	
		print("Connect nodeid", nodeid)
		endpoint = TCP4ClientEndpoint(reactor, '127.0.0.1', connect_port)
		d = connectProtocol(endpoint, Peer(self))
		d.addCallback(self.got_protocol)
		d.addErrback(log.err)
		#TODO?
		#Add connection to peer in peer dict, connection lets you send msg to specific peer
	
	def broadcast(self, msg):
		for _, conn in self.connections.items():
			conn.sendString(pickle.dumps(msg))
			

	def receive_pong_message(self, message):
		raise NotImplementedError("To be implemented in subclass")

	def receive_block(self, message):
		raise NotImplementedError("To be implemented in subclass")


	def parse_msg(self, msg_type, msg):
		if msg_type == "block":
			self.receive_block(msg)

	def run_node(self, hostport, connect_port, nodeid):
		"""
		Start server on host given by user
		Start client and connect to host given by user
		"""
		endpoint = TCP4ServerEndpoint(reactor, hostport)
		d = endpoint.listen(self)
		d.addErrback(log.err)
		
		self.connect_to_peer(hostport, connect_port, nodeid)
		
		reactor.run()



if __name__ == '__main__':

	reactor.run()