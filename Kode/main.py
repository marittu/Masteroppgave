import peer
import sys, optparse, uuid
from twisted.internet import reactor

def parse_args():
    usage = """usage: %prog [host]:port [connect]:port

    python peer.py 8000
    python peer.py 8001 8000

    """

    parser = optparse.OptionParser(usage)

    _, args = parser.parse_args()

    if len(args) == 1 or len(args) == 2:
        pass
    else:
        print(len(args))
        print (parser.format_help())
        parser.exit()

    if len(args) == 2:
        peertype = 'client'
        host, connect = args
        connect = int(connect)
    else: 
        peertype = 'initial'
        host = args[0]
        connect = None

    return peertype, int(host), connect


def main():
    peer_type, host, connect = parse_args()

    nodeid = uuid.uuid4()

    peer.run_server(host, nodeid)
    
    if peer_type == 'client':
        peer.run_client(connect, host, nodeid)

    #else:
    #    peer.run_client(host, host, nodeid)
        
    reactor.run()
if __name__ == '__main__':
    main()