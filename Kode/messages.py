import pickle, random, time

def send_hello(conn, nodeid, hostport):
    msg = {
        'msgtype': 'hello', 
        'nodeid': nodeid, 
        'hostport': hostport
    } #Add IP?
    send_msg(conn, msg)

def send_hello_ack(conn, nodeid, hostport):
    msg = {
        'msgtype': 'ack', 
        'nodeid': nodeid, 
        'hostport': hostport
    } #Add IP?
    send_msg(conn, msg)  

def send_peers(conn, peers):
    msg = {
        'msgtype':'peer', 
        'peers': peers
    }
    send_msg(conn, msg)         
def send_ping(conn, nodeid):
    """
    Pings from both server and client side TODO fix better ping/pong
    """
    msg = {
        'msgtype':'ping', 
        'time':time.time(), 
        'nodeid': nodeid
    }
    send_msg(conn, msg)

def send_pong(conn, nodeid):
    msg = {
        'msgtype':'pong', 
        'time':time.time(), 
        'nodeid': nodeid
    }
    send_msg(conn, msg)


def send_msg(conn, msg):
    conn.sendString(pickle.dumps(msg))

def broadcast(msg, connections):
        for _, conn in connections.items():
            conn.sendString(pickle.dumps(msg))

def broadcast_to_followers(msg, connections, own_nodeid):
    for nodeid, conn in connections.items():
        if nodeid != own_nodeid:
            conn.sendString(pickle.dumps(msg))

    
def send_to_peer(msg, connections, own_connection):
    """
    Send a message to a ramdom connected peer that is not self
    """
    conn = own_connection
    n = len(connections) - 1 
    while conn == own_connection:
        peer = random.randint(0, n)
        conn = list(connections.values())[peer]

    conn.sendString(pickle.dumps(msg))

def send_to_conn(msg, conn):
    """
    Send message to a given connection
    """
    conn.sendString(pickle.dumps(msg))  