import pickle, random, time

def send_hello(conn, nodeid, host_ip, hostport, public_key):
    msg = {
        'msgtype': 'hello', 
        'nodeid': nodeid, 
        'host_ip': host_ip,
        'hostport': hostport,
        'public_key': public_key
    } 
    send_msg(conn, msg)

def send_hello_ack(conn, nodeid, host_ip, hostport, public_key):
    msg = {
        'msgtype': 'ack', 
        'nodeid': nodeid, 
        'host_ip': host_ip,
        'hostport': hostport,
        'public_key': public_key
    } 
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


def send_transaction_to_leader(leader_conn, nodeid, tx):
        msg = {
            'msgtype': 'tx',
            'nodeid': nodeid,
            'time': tx[0],
            'consumed': tx[1],
            'produced': tx[2]
        }

        send_to_conn(msg, leader_conn)

def append_entries(conn, current_term, nodeid, index, prev_term, commit_index, propose_block, block_term, block_index):
    msg = {
        'msgtype': 'append_entries', 
        'term': current_term,
        'leaderid': nodeid, 
        'prev_index': index, #index of prev proposed block
        'prev_term': prev_term,   #term of prev proposed block
        'leader_commit': commit_index, #Index of proposed block ready for commiting to chain
        'propose_block': propose_block,
        'block_term': block_term,
        'block_index': block_index
    } 
    
    send_to_conn(msg, conn)
        
        

def respond_to_append_entries(conn, nodeid, success, current_term, last_log_term, last_log_index):
    msg = { 
            'msgtype': 'respond_append_entries', 
            'nodeid': nodeid, 
            'success': success,
            'current_term': current_term,
            'last_term': last_log_term,
            'last_index': last_log_index
        }

    send_to_conn(msg, conn)

def request_votes(connections, nodeid, current_term, last_log_index, last_log_term):
    msg = {
        'msgtype': 'request_vote', 
        'term': current_term, 
        'candidate_id': nodeid, 
        'last_log_index': last_log_index, 
        'last_log_term': last_log_term
    }
    broadcast_to_followers(msg, connections, nodeid)

def respond_request_vote(conn, vote_granted, nodeid, current_term):
        msg = {
                'msgtype': 'respond_request_vote', 
                'vote_granted': vote_granted,
                'node': nodeid,
                'term': current_term
        }

        send_to_conn(msg, conn) 

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