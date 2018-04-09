import hashlib
import time

class Block():
    def __init__(self, *args):
        self.index = None
        self.previous_hash = None
        self.timestamp = None
        self.transactions = []
        self.new_hash = None
        if args:
            for arg in args:
                self.transactions.append(arg)


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
        TODO: validate transactions in block
        """

        if self.index != neighbour_block.index + 1:
            return False
        if self.previous_hash != neighbour_block.new_hash:
            return False
        if self.new_hash != self.get_hash():
            return False
        #Make sure time between two blocks is not more than 60 seconds unless genesis
        if neighbour_block.index != 0:
            if (self.timestamp - neighbour_block.timestamp) > 60:
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


class Blockchain():
    def __init__(self):
        self.blockchain = []      
        self.genesis = self.create_genesis()
        self.add_block(self.genesis)

    def create_genesis(self):
        """
        Hard coded genesis block, same for all nodes
        """
        genesis = Block()
        genesis.index = 0
        genesis.previous_hash = 0
        genesis.timestamp = 0
        genesis.new_hash = genesis.get_hash()
        return genesis

    def get_head_block(self):
        return self.blockchain[-1]


    def add_block(self, block):
        """
        Adds new block to the blockchain
        """
        
        self.blockchain.append(block)

    def validate_blockchain(self):
        #Validate chain of only two blocks
        if len(self.blockchain) < 3:
            if self.blockchain[0].assert_equal(self.genesis) and self.blockchain[1].validate_block(self.genesis):
                return True

        prev_block = self.blockchain[-2] #Second to last block
        for block in self.blockchain[len(self.blockchain)-1::-1]: #itterate in reverse
            if not block.validate_block(prev_block):
                return False
            prev_block = self.blockchain[prev_block.index -1]
            if prev_block == self.genesis:
                return True
        
        return False #Gensis not reached - invalid

    def head_block_in_chain(self, head_block):
        for block in self.blockchain:
            if block.assert_equal(head_block):
                return True
        return False
        

    def print_chain(self):
        for block in self.blockchain:
            block.print_block()
            print()

    def send_blockchain_from_headblock(self, head_block):
        pass

class Transactions():
    def __init__(self):
        self.sender = None
        self.receiver = None
        self.amount = None




if __name__ == "__main__":
    blockchain = Blockchain()
       
    first = Block()
    second = Block(1,2,3)
    #if consensus: blockchain.add_block(block)
    blockchain.add_block(first)
    blockchain.add_block(second)
    
    blockchain.print_chain()
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