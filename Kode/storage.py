from twisted.internet.defer import Deferred
from blockchain import Block
import time, os
from datetime import datetime

#TODO: MAKE DEFERRED
class Log():
    def __init__(self, port):
        self.f = None
        self.filename = 'Log/'+port+'.txt'
        """
        self.voted_for = None #update on stable storage   
        self.current_term = 0 #update on stable storage        
        self.last_log_index = 1 #highest log entry known, not yet commited (latest validated propose_block), 1 because node_id at 0
        self.last_log_term = 0 #term of last_log_index
        self.last_commited = 0 #highest log entry applied to state machine (index of head_block)
        """
    """
    def open_file(self):
        with open(self.filename, 'a') as self.f:
            d = Deferred()
        return d

    def _write(self):
        self.f.write('data')


    def write(self, data):
        d = self.open_file()
        d.addCallback(self._write)
        d.addErrback(print("err"))
        
        self.f.close()

    def read(self):
        with open(self.filename, 'r') as f:
            line = f.readline().rstrip()

        print(line)
        f.close()
    """

    def write(self, data):
        with open(self.filename, 'a') as f:
                f.write(data+'\n')
        f.close()

    def read(self):
        with open(self.filename, 'r') as f:
            line = f.readline().rstrip()

        print(line)
        f.close()

class Proposed_blocks_log():
    def __init__(self, port):
        self.port = port
        self.filename = 'Log/Blocks/'+str(port)+'_blocks.txt'

    def write(self, term, index, block):
        data = index, term, self.block_to_string(block) #Voted_for
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

    def block_to_string(self, block):
        string = {
            'Index': block.index,
            'Previous hash': block.previous_hash,
            'Timestamp': block.timestamp,#time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(block.timestamp))),
            'Transactions': block.transactions,
            'Block hash': block.new_hash,
        }
        return string

    def string_to_block(self, string):
        index = int(self.clean_string(string[0].split(':')[1:]))
        previous_hash = self.clean_string(string[1].split(':')[1:])
        timestamp = float(self.clean_string(string[2].split(':')[1:]))
        transactions = self.clean_string(string[3].split(':')[1:])
        new_hash = self.clean_string(string[4].split(':')[1:])
        return Block(index, previous_hash, timestamp, transactions, new_hash)

    def clean_string(self, string):
        strip = " '[]\"{}()\\n"
        new_string = str(string).translate(str.maketrans('', '', strip))
        return new_string

    """
    def get_vote(self):

    """

    def find_index_term(self, index, term):
        with open(self.filename, 'r') as f:
            for l in f:
                line = l.split(',')
                
                if int(self.clean_string(line[0])) < index: #the index is higher than the largest entry in the file
                    #print(line[0])
                    #print(index)
                    return None 

                if int(self.clean_string(line[0])) == int(index):
                    if int(self.clean_string(line[1])) == int(term):
                        print("FOUND MATCH")
                        return True
                    else:
                        print("NOT TERM MATCH")
                        return False

    def get_block_term_from_index(self, index):
        with open(self.filename, 'r') as f:
            for l in f:
                line = l.split(',')
                
                if int(self.clean_string(line[0])) == index:
                    block = self.string_to_block(line[2:])
                    block_term = int(self.clean_string(line[1]))
                if int(self.clean_string(line[0])) == index - 1:
                    prev_term = int(self.clean_string(line[1]))
                    return (prev_term, block_term, block)

    def update_index(self, num_lines):
        out_file = 'Log/Blocks/'+str(self.port)+'_blocks_temp.txt'
        with open(self.filename, 'r+') as f, open(out_file, 'w')as out:
            i = 0
            for line in f:
                if i < num_lines:
                    i += 1
                else:
                    out.write(line)

        os.remove(self.filename)
        os.rename(out_file, self.filename)            

    
class Blockchain_log():
    def __init__(self):
        pass

class Vote():
    """
    A log containing votes for each term
    For efficiency in reading, the newest votes are appended at the top of the log
    """
    def __init__(self, port):
        self.filename = 'Log/Vote/'+str(port)+'_votes.txt'

    def write(self, data):
       
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
            #.rstrip()
        #for line in reversed(list(open(self.filename))):
        #    print(line.rstrip())
        #    return(line.rstrip())
        #    break

class Config():
    """
    Log for persistent data such as nodeid
    TODO: Anything else? Necessary with own file?
    """
    def __init__(self, port):
        self.filename = 'Log/Config/'+str(port)+'_config.txt'

    def write(self, data):
        with open(self.filename, 'a') as f:
                f.write(data+'\n')
        f.close()

    def read(self):
        with open(self.filename, 'r') as f:
            line = f.readline().rstrip()

        return line


class ConsumedEnergy():
    def __init__(self):
        pass