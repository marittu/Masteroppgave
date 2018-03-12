import optparse

from twisted.internet.protocol import Protocol, ClientFactory, ClientCreator
from twisted.internet import reactor

import time, json


class Peer(Protocol):

	connected = False

	def __init__(self, factory, peer_type):
		
		self.pt = peer_type
		self.factory = factory
		self.remote_nodeid = None
		self.nodeid = self.factory.nodeid

	def connectionMade(self):
		port = self.transport.getPeer().port
		if self.pt == 'client':
			self.connected = True
			self.send_hello()

		
	def connectionLost(self, reason):
		
		if self.pt == 'client':
			self.connected = False
		else:
			self.factory.remove_peer(self.remote_nodeid)
			self.factory.print_peers()

	def dataReceived(self, data):
		msg = json.loads(data)
		print(self.pt, "Received: ", msg)
		if msg['msgtype'] == 'hello':

			if self.pt == 'server':
				self.handle_hello(msg)

			else:
				self.factory.add_peers(msg['nodeid'], msg['hostport'])
				
				
		elif msg['msgtype'] == 'peer':
			self.handle_peers(msg)

		elif msg['msgtype'] == 'broadcast':
			self.broadcast(msg) 

	#Move rest of protocol to messages module

	def send_hello(self):

		msg = {'msgtype': 'hello', 'nodeid': self.factory.nodeid, 'hostport': self.factory.hostport} #Add IP?
		self.send_msg(msg)


	def handle_hello(self, msg):
		self.remote_nodeid = msg['nodeid']
		if self.pt == 'server' and self.remote_nodeid == self.factory.nodeid:
			self.factory.client = self.transport.getPeer().port
			print(self.factory.client)
		else:
			self.factory.add_peers(msg['nodeid'], msg['hostport'])
		
			self.send_hello()
		
			reactor.callLater(1, self.send_peers)		
	
	def send_peers(self):
		send_msg = {'msgtype':'peer', 'peers': self.factory.peers}
		self.send_msg(send_msg)

	def handle_peers(self, msg):
		for peer in msg['peers']:
			host = msg['peers'][peer]
			if peer not in self.factory.peers:
				c = ClientCreator(reactor, Peer, self.factory, self.pt)
				c.connectTCP('localhost', host)
				self.factory.add_peers(peer, host)
	
	def broadcast(self, msg):
		for peer in self.peers:
			self.send_msg(msg)

	def test(self):
		msg = input("")
		if not msg:
			pass
		else:
			send_msg(msg)


	def send_msg(self, msg):
		print(self.pt, "Sending: ", msg)
		self.transport.write(json.dumps(msg).encode('utf-8'))

class PeerFactory(ClientFactory):

	def __init__(self, peertype, hostport, nodeid):
		#include ip in addition to port
		self.pt = peertype
		self.hostport = hostport
		self.nodeid = str(nodeid)
		self.client = None
		self.peers = {}

	def print_peers(self):
		for peer in self.peers:
			print(peer)

	def add_peers(self, peer, hostport):
		self.peers[peer] = hostport

		print (self.pt)
		for peer in self.peers:
			print(self.peers.get(peer))

	def remove_peer(self, peer):
		print (peer, "disconnected")
		del self.peers[peer]


	def clientConnectionFailed(self, connector, reason):
		print ('Failed to connect to:', connector.getDestination())
		self.finished(0)

	def clientConnectionLost(self, connector, reason):
		print ('Lost connection.  Reason:', reason)


	def buildProtocol(self, addr):
		protocol = Peer(self, self.pt)
		return protocol


def run_server(port, nodeid):
	factory = PeerFactory('server', port, nodeid)
	reactor.listenTCP(port, factory)
	print ("Starting server " + 'localhost' + " port " + str(port))
	
def run_client(port, hostport, nodeid):
	factory = PeerFactory('client', hostport, nodeid)
	host = '127.0.0.1'	
	reactor.connectTCP(host, port, factory)
	print ("Connecting to host " + host + " port " + str(port))

		


if __name__ == '__main__':
	peer_type, address = parse_args()


	if peer_type == 'server':
		factory = PeerFactory('server')
		reactor.listenTCP(address[1], factory)
		print ("Starting server " + address[0] + " port " + str(address[1]))
	else:

		factory = PeerFactory('client')
		host, port = address
		print ("Connecting to host " + host + " port " + str(port))
		reactor.connectTCP(host, port, factory)

	reactor.run()