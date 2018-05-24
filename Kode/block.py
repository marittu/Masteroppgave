import hashlib
import time

class Block():
    def __init__(self, index = 0, previous_hash = None, timestamp = 0, transactions = None, new_hash = None):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions#[]
        self.new_hash = new_hash

    def add_transaction(self, transactions):
        for tx in transactions:
            self.transactions.append(tx)

    def get_hash(self):
        new_hash = str(self.index)+str(self.previous_hash)+str(self.timestamp)+str(self.transactions)
        return str(hashlib.sha256(new_hash.encode('utf-8')).hexdigest())        

    def print_block(self):
        print('Index: \t\t', self.index)
        print('Previous hash: \t', self.previous_hash)
        print('Timestamp: \t', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(self.timestamp))))
        print('Transactions: \t', self.transactions)
        print('Hash: \t\t', self.new_hash, '\n')
        


    def validate_block(self, neighbour_block):
        """
        Validate block based on the latest commited block in the chain
        """
        if self.index != neighbour_block.index + 1:
            return False
        if self.previous_hash != neighbour_block.new_hash:
            return False
        if self.new_hash != self.get_hash():
            return False

        return True

    def propose_block(self, head_block):
        """
        Propose a new block to the chain, given the latest block in the chain
        """
        self.index = head_block.index + 1
        self.previous_hash = head_block.new_hash
        self.timestamp = time.time() 
        self.new_hash = self.get_hash()

    def assert_equal(self, other_block):
        #Raise exception instead
        if self.index != other_block.index:
            return False

        if self.previous_hash != other_block.previous_hash:
            return False
            
        if self.new_hash != other_block.new_hash:
            return False
        if set(self.transactions) != set(other_block.transactions):
            return False
        if self.timestamp != other_block.timestamp:
            return False

        return True     

    def get_genesis(self):
        """
        Hard coded genesis block, same for all nodes
        """
        genesis = Block()
        genesis.index = 1
        genesis.previous_hash = 0
        genesis.timestamp = 0
        genesis.new_hash = genesis.get_hash()
        return genesis




#Unittests to ensure correct behaviour 

"""
class InvalidBlock(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class InvalidBlockchain(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

try:
    block.validate()
except InvalidBlock as ex:
    raise InvalidBlockchain("Invalid blockchain at block {} caused by: {}".format(i, str(ex)))
"""