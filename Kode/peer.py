import optparse

from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor
import time

def parse_args():
	usage = """usage: %prog [options] [client|server] [hostname]:port

	python peer.py server 127.0.0.1:8000
	python peer.py client 127.0.0.1:8000
	
	"""

	parser = optparse.OptionParser(usage)

	_, args = parser.parse_args()

	if len(args) != 2:
		print (parser.format_help())
		parser.exit()

	peertype, addresses = args

	def parse_address(addr):
		if ':' not in addr:
			host = '127.0.0.1'
			port = addr
		else:
			host, port = addr.split(':', 1)

		if not port.isdigit():
			parser.error('Ports must be integers.')

		return host, int(port)

	return peertype, parse_address(addresses)


class Peer(Protocol):

	acks = 0
	connected = False

	def __init__(self, factory, peer_type):
		self.pt = peer_type
		self.factory = factory

	def connectionMade(self):
		if self.pt == 'client':
			self.connected = True
			reactor.callLater(5, self.sendUpdate)
		else:
			print ("Connected from", self.transport.client)
			try:
				self.transport.write(bytes('<connection up>', 'utf-8'))
			except Exception as e:
				print (e)
			self.ts = time.time()

	def sendUpdate(self):
		print ("Sending update")
		try:
			self.transport.write(bytes('<update>', 'utf-8'))
		except Exception as inst:
			print ("Exception trying to send: ", inst)    
		if self.connected == True:
			reactor.callLater(5, self.sendUpdate)

	def sendAck(self):
		print ("sendAck")
		self.ts = time.time()
		try:
			self.transport.write(bytes('<Ack>', 'utf-8'))
		except Exception as e:
			print (e)

	def dataReceived(self, data):
		if self.pt == 'client':
			print ('Client received ' + str(data, 'utf-8'))
			self.acks += 1
		else:
			print ('Server received ' + str(data, 'utf-8'))
			self.sendAck()

	def connectionLost(self, reason):
		print ("Disconnected")
		if self.pt == 'client':
			self.connected = False
			self.done()

	def done(self):
		self.factory.finished(self.acks)


class PeerFactory(ClientFactory):

	def __init__(self, peertype, fname):
		print ('@__init__')
		self.pt = peertype
		self.acks = 0
		self.fname = fname
		self.records = []

	def finished(self, arg):
		self.acks = arg
		self.report()

	def report(self):
		print ('Received %d acks' % self.acks)

	def clientConnectionFailed(self, connector, reason):
		print ('Failed to connect to:', connector.getDestination())
		self.finished(0)

	def clientConnectionLost(self, connector, reason):
		print ('Lost connection.  Reason:', reason)

	def startFactory(self):
		print ("@startFactory")
		if self.pt == 'server':
			self.fp = open(self.fname, 'w+')

	def stopFactory(self):
		print ("@stopFactory")
		if self.pt == 'server':
			self.fp.close()

	def buildProtocol(self, addr):
		print ("@buildProtocol")
		protocol = Peer(self, self.pt)
		return protocol


if __name__ == '__main__':
	peer_type, address = parse_args()


	if peer_type == 'server':
		factory = PeerFactory('server', 'log')
		reactor.listenTCP(address[1], factory)
		print ("Starting server @" + address[0] + " port " + str(address[1]))
	else:
		factory = PeerFactory('client', '')
		host, port = address
		print ("Connecting to host " + host + " port " + str(port))
		reactor.connectTCP(host, port, factory)

	reactor.run()