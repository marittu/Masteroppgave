import os
class Contract():
    """
    API callable from website where contracts created
    When new contract is made, it is passed to the node object for verification and storage in the blockchain
    """


    def __init__(self):
        self.filename = 'Log/Contract/contract.txt'
        if not os.path.exists(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename))
        self.duration = 0
        self.prosumer = None
        self.consumer = None
        self.minimum_consumption = 0

    def new_contract(self, prosumer, consumer, minimum_consumption, duration):
        self.prosumer = prosumer
        self.consumer = consumer
        self.minimum_consumption = minimum_consumption        
        self.duration = duration


    def sign_contract(self, prosumer_key, consumer_key):
        pass
        #Sign contract


    def store_contract(self):
        data = self.prosumer, self.consumer, self.minimum_consumption, self.duration
        with open(self.filename, 'a') as f:
                f.write(str(data)+'\n')
        f.close()

    def read_contracts(self):
        with open(self.filename, 'r') as f:
            line = f.readline().rstrip()

        return line



if __name__ == "__main__":
    contract1 = Contract()
    contract1.new_contract('1a', '2b', 1, 60)
    contract1.store_contract()

    contract2 = Contract()
    contract2.new_contract('3c', '4d', 1, 60)   
    contract2.store_contract()

