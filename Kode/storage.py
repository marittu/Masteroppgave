from twisted.internet.defer import Deferred
#TODO: MAKE DEFERRED
class Log():
    def __init__(self, port):
        self.filename = 'Log/'+port+'.txt'

        self.voted_for = None #update on stable storage   
        self.current_term = 0 #update on stable storage        
        self.last_log_index = 1 #highest log entry known, not yet commited (latest validated propose_block), 1 because node_id at 0
        self.last_log_term = 0 #term of last_log_index
        self.last_commited = 0 #highest log entry applied to state machine (index of head_block)
    
    """
    def open_file(self):
        with open(self.filename, 'a') as self.f:
            d = Deferred()
        return d

    def _write(self, data):
        self.f.write(data)


    def write(self, data):
        d = self.open_file()
        d.addCallback(self._write, data)
        d.addErrback(print("err"))
        
        self.f.close()

    def read(self):
        with open(self.filename, 'r') as f:
            line = f.readline()

        print(line)
        f.close()
    """

    def write(self, data):
        with open(self.filename, 'a') as f:
                f.write(data+'\n')
        f.close()

    def read(self):
        with open(self.filename, 'r') as f:
            line = f.readline()

        print(line)
        f.close()
        
class Blockchain_log():
    def __init__(self):
        pass

class ConsumedEnergy():
    def __init__(self):
        oass