from twisted.internet.protocol import Factory, connectionDone
from twisted.protocols.basic import IntNStringReceiver
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint, connectProtocol #Protocol, ClientFactory, ClientCreator
from twisted.internet import reactor, task
from twisted.internet.task import LoopingCall
from twisted.python import log

import time, json, struct


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
		self.factory.print_peers()
		#Reconnect_loop?

		if self.ping.running:
			self.ping.stop()

	def stringReceived(self, data):
		print(data)
		msg = json.loads(data)
		
		if msg['msgtype'] == 'hello':
			self.remote_nodeid = msg['nodeid']
			self.factory.add_peers(msg['nodeid'], msg['hostport'])

			if not self.ping.running:
				self.ping.start(30) #Ping every 30 minutes (seconds for testing) 
				#TODO make variable global

			self.hello_ack()
		#Move duplicate code to handle_hello	
		elif msg['msgtype'] == 'ack':
			self.remote_nodeid = msg['nodeid']
			self.factory.add_peers(msg['nodeid'], msg['hostport'])

			if not self.ping.running:
				self.ping.start(30) #Ping every 30 minutes (seconds for testing) 
				#TODO make variable global
		
		elif msg['msgtype'] == 'peer':
			self.handle_peers(msg)

		elif msg['msgtype'] == 'ping':
			self.send_pong()


	#Move rest of protocol to messages module

	def send_hello(self):
		
		msg = {'msgtype': 'hello', 'nodeid': self.factory.nodeid, 'hostport': self.factory.hostport} #Add IP?
		self.send_msg(msg)

	def hello_ack(self):
		msg = {'msgtype': 'ack', 'nodeid': self.factory.nodeid, 'hostport': self.factory.hostport} #Add IP?
		self.send_msg(msg)

		#Tell the new node about own peers
		reactor.callLater(0.1, self.send_peers)		
	
	
	def send_peers(self):
		send_msg = {'msgtype':'peer', 'peers': self.factory.peers}
		self.send_msg(send_msg)

	def handle_peers(self, msg):
		for peer in msg['peers']:
			host = msg['peers'][peer]
			print(peer)
			if peer not in self.factory.peers:
				self.factory.connect_to_peer(self.factory.nodeid, host, peer)

	def send_ping(self):
		msg = {'msgtype':'ping', 'time':time.time(), 'nodeid':self.factory.nodeid}
		self.send_msg(msg)

	def send_pong(self):
		msg = {'msgtype':'pong', 'time':time.time(), 'nodeid':self.factory.nodeid}
		self.send_msg(msg)


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
		self.client = None
		self.peers = {}
		#self.message_callback = self.parse_msg
		selfreactor = reactor
		#incomming/outgoing hosts set()
		

	def buildProtocol(self, addr):
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
		if peer not in self.peers:
			print("Added peer:", peer, hostport)
			self.peers[peer] = hostport
		for peer in self.peers:
			print("Peer", self.peers.get(peer))

	def remove_peer(self, peer):
		print (peer, "disconnected")
		del self.peers[peer]


	def clientConnectionFailed(self, connector, reason):
		print ('Failed to connect to:', connector.getDestination())
		self.finished(0)

	def clientConnectionLost(self, connector, reason):
		print ('Lost connection.  Reason:', reason)


	def connect_to_peer(self, hostport, connect_port, nodeid):
		"""
		Let client to connect to other nodes pased on port
		"""	
		print(hostport)
		print(connect_port)
		if nodeid not in self.peers:
			print("Connect nodeid", nodeid)
			endpoint = TCP4ClientEndpoint(reactor, '127.0.0.1', connect_port)
			d = connectProtocol(endpoint, Peer(self))
			d.addCallback(self.got_protocol)
			d.addErrback(log.err)

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