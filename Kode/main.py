from node import Node
from storage import Config, clean_string
import sys, optparse, uuid, os
from ecdsa import SigningKey, VerifyingKey
import socket, pickle
from twisted.internet import reactor
from twisted.python import log


def parse_args():
    usage = """usage: %prog [host]:port [connect]ip [connect]:port

    python peer.py 8000 192.168.0.1 8000
    python peer.py 8001 192.168.0.1 8000

    """

    parser = optparse.OptionParser(usage)

    _, args = parser.parse_args()

    if len(args) == 3:
        pass
    else:
        print(len(args))
        print (parser.format_help())
        parser.exit()

    if len(args) == 3:
        host, ip, connect = args
    
    return int(host), str(ip), int(connect)

#Always take two arguemts, initial just connects to self
#Start server and client in same method and use tcpendpoints?

def main():
    log.startLogging(sys.stdout)
    host_port, connect_ip, connect_port = parse_args()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    host_ip = s.getsockname()[0]
    s.close()

    """
    Assume node uses same hostport if it restarts after a crash
    If node as participated in blockchain network before,
    it will be able to continue from where it left off, 
    otherwise it creates a new log with a new nodeid
    """
   
    #Make two functions - try: read_from file, except: create config - also make run_node function

    try:
        with open('Log/Config/'+str(host_port)+'_config.txt', 'r') as f:
            nodeid = f.readline().rstrip()
        private_key = SigningKey.from_pem(open('Log/Config/'+str(nodeid)+'private_key.pem', 'rb').read())
        public_key = VerifyingKey.from_pem(open('Log/Config/'+str(nodeid)+'public_key.pem', 'rb').read())
        config_log = Config(str(host_port))
    
    except:
        nodeid = str(uuid.uuid4())
        config_log = Config(str(host_port))
        #Write nodeid to stable storage and initialize empty vote
        config_log.write(nodeid)

        private_key = SigningKey.generate()
        public_key = private_key.get_verifying_key()
        open('Log/Config/'+str(nodeid)+'public_key.pem',"wb+").write(public_key.to_pem())
        open('Log/Config/'+str(nodeid)+'private_key.pem',"wb+").write(private_key.to_pem())
        
            
    print(nodeid)
    
    
    node = Node(host_ip, host_port, nodeid, config_log, public_key, private_key)
    node.run_node(host_ip, host_port, connect_ip, connect_port, nodeid)

    reactor.run()


if __name__ == '__main__':
    main()