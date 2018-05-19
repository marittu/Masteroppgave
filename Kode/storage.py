from twisted.internet.defer import Deferred
from blockchain import Block
import time, os
from datetime import datetime

#TODO: MAKE DEFERRED
class Proposed_blocks_log():
    """
    File containing the proposed blocks from the leader
    """
    def __init__(self, port):
        self.port = port
        self.filename = 'Log/Blocks/'+str(port)+'_blocks.txt'
        if not os.path.exists(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename))

    def write(self, term, index, block):
        """
        Writes new entries to the top of the file
        Entrie consists of index, term and block
        """
        data = index, term, block_to_string(block) #Voted_for
        try:    
            with open(self.filename, 'r+') as f:
            
                content = f.read()
                f.seek(0, 0)
                f.write(str(data).rstrip('\r\n') + '\n' + content)
        except:
            with open(self.filename, 'a+') as f:
                f.write(str(data)+'\n')
    

    def read(self):
        with open(self.filename, 'r') as f:
            line = f.readline()
        return line 

    def find_index_term(self, index, term):
        """
        Returns True if there is an entry matching the given index and term. 
        Returns False if there is a match with index but not term
        Returns None if there is no entry at the index
        """
        with open(self.filename, 'r') as f:
            for l in f:
                line = l.split(',')
                if int(clean_string(line[0])) == int(index): 
                    if int(clean_string(line[1])) == int(term):
                        return True

                    else:
                        return False
        return None

    def get_block_term_from_index(self, index):
        """
        Gets block, term of block and term of previous block at a given index
        """
        with open(self.filename, 'r') as f:
            for l in f:
                line = l.split(',')
                #if index > int(clean_string(line[0])):
                #    return None
                if int(clean_string(line[0])) == index:
                    block = string_to_block(line[2:])
                    block_term = int(clean_string(line[1]))
                if int(clean_string(line[0])) == index - 1:
                    prev_term = int(clean_string(line[1]))
                    return (prev_term, block_term, block)

    def get_block(self, index):
        """
        Returns a block from a given index
        """
        with open(self.filename, 'r') as f:
            for l in f:
                line = l.split(',')
                if int(clean_string(line[0])) == index:
                    return string_to_block(line[2:])


    def update_index(self):
        """
        Node has entry not matching with the leader
        Deletes conflicting entry
        TODO: Somewhat inefficient way to do it 
        """
        out_file = 'Log/Blocks/'+str(self.port)+'_blocks_temp.txt'
        with open(self.filename, 'r+') as f, open(out_file, 'w')as out:
            i = 0
            for line in f:
                if i < 1:
                    i = 1
                else:
                    out.write(line)

        os.remove(self.filename)
        os.rename(out_file, self.filename)            

    
class Blockchain_log():
    """
    File containing blockchain of blocks validated by majority of network
    """
    def __init__(self, port):
        self.filename = 'Log/Blockchain/'+str(port)+'_blockchain.txt'
        if not os.path.exists(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename))

    def write(self, data):
        """
        Write new entries to the top of file
        """
        block = block_to_string(data)
        try:    
            with open(self.filename, 'r+') as f:
            
                content = f.read()
                f.seek(0, 0)
                f.write(str(block).rstrip('\r\n') + '\n' + content)
        except:
            with open(self.filename, 'a+') as f:
                f.write(str(block)+'\n')
    

    def read(self):
        """
        Gets latest entry from file
        """
        with open(self.filename, 'r') as f:
            line = f.readline()
            
        return line

    def last_index(self):
        """
        Index of last block added to Blockchain
        """
        block = string_to_block(self.read().split(','))
        return int(block.index)

class Vote():
    """
    A log containing votes for each term
    For efficiency in reading, the newest votes are appended at the top of the log
    """
    def __init__(self, port):
        self.filename = 'Log/Vote/'+str(port)+'_votes.txt'
        if not os.path.exists(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename))

    def write(self, data):
        """
        Writes data to the top of the file
        """
        try:    
            with open(self.filename, 'r+') as f:
            
                content = f.read()
                f.seek(0, 0)
                f.write(str(data).rstrip('\r\n') + '\n' + content)
        except:
            with open(self.filename, 'a+') as f:
                f.write(str(data)+'\n')
    

    def read(self):
        """
        Gets the latest entry from the file
        """
        with open(self.filename, 'r') as f:
            line = f.readline()
            
        return line 

    def get_term(self):
        vote = self.read().split(':')
        term = int(clean_string(vote[0]))
        return term

class Config():
    """
    Log for persistent data such as nodeid 
    """
    def __init__(self, port):
        self.filename = 'Log/Config/'+str(port)+'_config.txt'
        if not os.path.exists(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename))

    def write(self, data):
        with open(self.filename, 'a') as f:
                f.write(data+'\n')
        f.close()

    def read(self):
        with open(self.filename, 'r') as f:
            line = f.readline().rstrip()

        return line


def clean_string(string):
    """
    Strips string of all extra symbpls
    """
    strip = " '\'[]\"{}()\\n"
    new_string = str(string).translate(str.maketrans('', '', strip))
    return new_string

def block_to_string(block):
    """
    Converts a Block object to a string
    """
    string = {
        'Index': block.index,
        'Previous hash': block.previous_hash,
        'Timestamp': block.timestamp,
        'Transactions': block.transactions,
        'Block hash': block.new_hash,
    }
    return string

def string_to_block(string): 
    """
    Converts a string to a Block object
    """
    index = int(clean_string(string[0].split(':')[1:]))
    previous_hash = clean_string(string[1].split(':')[1:])
    timestamp = float(clean_string(string[2].split(':')[1:]))
    transactions = clean_string(string[3].split(':')[1:])
    new_hash = clean_string(string[4].split(':')[1:])
    
    return Block(index, previous_hash, timestamp, transactions, new_hash)