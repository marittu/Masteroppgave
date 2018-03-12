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
        print('Hash: \t\t', self.new_hash)

class Blockchain():
    def __init__(self):
        self.chain = []
        self.nodes = set()

    def add_block(self, block):
        if len(self.chain) > 0:#Not genesis block
            block.index = self.chain[-1].index + 1
            block.previous_hash = self.chain[-1].new_hash
            block.timestamp = time.time()
            block.new_hash = block.get_hash()
        self.chain.append(block)
        #TODO - validate block before adding

    def print_chain(self):
        for block in self.chain:
            block.print_block()
            print()

class Transactions():
    def __init__(self):
        self.sender = None
        self.receiver = None
        self.amount = None

def create_genesis():
    genesis = Block()
    genesis.index = 0
    genesis.previous_hash = 0
    genesis.timestamp = 0
    genesis.new_hash = genesis.get_hash()
    return genesis


if __name__ == "__main__":
    genesis = create_genesis()
    blockchain = Blockchain()
    blockchain.add_block(genesis)
       
    first = Block()
    second = Block(1,2,3)
    #if consensus: blockchain.add_block(block)
    blockchain.add_block(first)
    blockchain.add_block(second)
    
    blockchain.print_chain()
#Unittests to ensure correct behaviour 