from node import Node
from storage import Config
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
    log.startLogging(sys.stdout)
    host, connect = parse_args()

    """
    Assume node uses same hostport if it restarts after a crash
    If node as participated in blockchain network before,
    it will be able to continue from where it left off, 
    otherwise it creates a new log with a new nodeid
    """
    try:
        with open('Log/Config/'+str(host)+'_config.txt', 'r') as f:
            nodeid = f.readline().rstrip()

        config_log = Config(str(host))
    
    except:
        nodeid = str(uuid.uuid4())
        config_log = Config(str(host))
        
        #Write nodeid to stable storage and initialize empty vote
        config_log.write(nodeid)
        
        

    print(nodeid)
    node = Node(host, nodeid, config_log)
    node.run_node(host, connect, nodeid)

    reactor.run()


if __name__ == '__main__':
    main()