from node import Node
import sys, optparse, uuid
from twisted.internet import reactor
from twisted.python import log

def parse_args():
    usage = """usage: %prog [host]:port [connect]:port

    python peer.py 8000 8000
    python peer.py 8001 8000

    """

    parser = optparse.OptionParser(usage)

    _, args = parser.parse_args()

    if len(args) == 2:
        pass
    else:
        print(len(args))
        print (parser.format_help())
        parser.exit()

    if len(args) == 2:
        host, connect = args
    
    return int(host), int(connect)

#Always take two arguemts, initial just connects to self
#Start server and client in same method and use tcpendpoints?

def main():
    #log.startLogging(sys.stdout)
    host, connect = parse_args()

    nodeid = str(uuid.uuid4())
    print(nodeid)
    #peer.run_server(host, nodeid)
    node = Node(host, nodeid)
    node.run_node(host, connect, nodeid)

    node.broadcast_block()
        
    reactor.run()


if __name__ == '__main__':
    main()