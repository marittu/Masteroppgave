import os
from smart_contract import Contract

class Settlement():
    """
    Self-enforcing mechanism for smart contract
    New object created for each settlement - objects automatically deleted when overwritten?
    Called by consensus leader with data for current period
    Data is a list of dicts in the form: 
        [{node: 'nodeid', produced:'amount of electricity produced', consumed:'amount of electricity consumed'},{node...}]
    nodes is a list of node objects - each objects has among other things a wallet and a nodeid  nodetype (e.g. prosumer, consumer, producer)
    """
    def __init__(self, data):
        self.data = data
        self.nodes = ['1a', '2b', '3c', '4d']
        self.wallet = Wallet()
        self.contract = Contract()

        
    def settle(self):
        #while self.data is not None:
            #itterate thorugh smart contracts
                #if prosumer/consumer in smart contracts has transaction data for period, settle and delete tx if completely settled

            #If still left over, assume excess electricity stored on battery, excess consumed from pure producer - delete tx
                 
        """
        Receives information from the system every minute about incomming and outgoing electricity for every node
        Delete data from list as it is settled
        For prosuming nodes: sold = produced - consumed

        for nodeinfo in data:
            find smart contracts for this node
            if not already settled in this period
            verify that producing party of contract has produced at least the amount of electricity 
            the consuming party has consumed:
                settle bill if true - include time of settlement


        """

        #self.update_wallet(str(data[0]))

    def update_wallet(self, data):
        """
        line = self.wallet.read().split(',')
        nodeid = data[0]
        amount = int(line[1]) + data[1] #append new bill
        bill = nodeid + ',' + amount
        """
        self.wallet.write(data)

class Wallet():

    def __init__(self):
        self.filename = 'Log/Wallet/wallet.txt'
        if not os.path.exists(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename))
            data = 'prosumer', 0, 'producer', 0
            self.write(data)

    def write(self, data):
        with open(self.filename, 'w') as f:
               f.write(data+'\n')
        f.close()

    def read(self):
        with open(self.filename, 'r') as f:
            line = f.readline().rstrip()

        return line



if __name__ == "__main__":
    
    
    data = [
    ['1a', 4, 1],
    ['2b', 0, 3],
    ['3c', 3, 0],
    ['4d', 3, 6],]
    
    settlement = Settlement(data)
    print(settlement.contract.read_contracts())
    settlement.settle()
