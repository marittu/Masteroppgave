from storage import clean_string
from datetime import datetime
import os, json

def settle(transaction, time):
    """
    Receives information from the system every minute about 
    incomming and outgoing electricity for every node    
    """
    price = 1
    contracts = _get_contracts()
    transactions = _format_transactions(transaction)   
    for contract in contracts:
        seller_credit = producer_seller = buyer_credit = producer_buyer = 0
        seller = contract[0]
        buyer = contract[1]
        seller_consumed = float(transactions[seller][0])
        seller_produced = float(transactions[seller][1].replace('-',''))
        buyer_consumed = float(transactions[buyer][0])
        buyer_produced = float(transactions[buyer][1].replace('-',''))

        seller_sold = seller_produced - seller_consumed
        buyer_bought = max(buyer_consumed - buyer_produced, 0)
        
        
        if seller_sold < 0:
            producer_seller = max(seller_consumed - seller_produced, 0)
            producer_buyer = buyer_bought

        elif seller_sold == 0 and buyer_consumed > 0:
            producer_buyer = buyer_bought

        else:
            if seller_sold - buyer_bought > 0:
                #Excess assumed stored on battery
                seller_credit = buyer_bought
                buyer_credit = buyer_bought
            else:
                seller_credit = seller_sold
                buyer_credit = min(seller_sold, buyer_bought)
                producer_buyer = max(buyer_bought - seller_sold, 0)


        seller_credit = seller_credit * price
        producer_seller = producer_seller * price
        buyer_credit = buyer_credit * price
        producer_buyer = producer_buyer * price
        

        seller_file = 'Log/Settlement/'+str(seller)+'.txt'
        buyer_file =  'Log/Settlement/'+str(buyer)+'.txt'
        seller_settlement =_read_settlement(seller_file)
        buyer_settlement = _read_settlement(buyer_file)

        if not seller_settlement:
            seller_settlement = {buyer: seller_credit, 'Producer': -producer_seller}     
        else:
           seller_settlement[buyer] += seller_credit
  
           seller_settlement['Producer'] -= producer_seller
  
        if not buyer_settlement:
            buyer_settlement = {seller: -buyer_credit, 'Producer': -producer_buyer}
        else:
  
            buyer_settlement[seller] -= buyer_credit
            buyer_settlement['Producer'] -= producer_buyer
        
        for key in buyer_settlement:
            buyer_settlement[key] = round(buyer_settlement[key], 3)
        
        for key in seller_settlement:
            seller_settlement[key] = round(seller_settlement[key],3)
        
        _write_settlement(seller_file, time, seller_settlement)
        _write_settlement(buyer_file, time, buyer_settlement)
        #print("seller", seller_settlement)
        #print("buyer", buyer_settlement)


def _get_contracts():
    contracts = []
    with open('Log/Contract/contract.txt', 'r') as f:
         for l in f:
                line = l.split(',')
                contract = clean_string(line).split(',')
                contracts.append(contract)

    return contracts


def _format_transactions(transaction):
    transactions = {}
    for tx in transaction:
        transactions.update({tx[0]: [tx[1], tx[2]]})

    return transactions



            
def _read_settlement(filename):
    if not os.path.exists(filename):
        open(filename, 'w+')
        return None
    
    with open(filename, 'r') as f:
        line = f.readline().split(';')
    tx = line[1].rstrip().replace('\'', '\"')
    
    tx = json.loads(tx)
    return tx
    #one line for each settlement, return list of dicts

def _write_settlement(filename, time, data):
    try:    
        with open(filename, 'r+') as f:
        
            content = f.read()
            f.seek(0, 0)
            f.write(str(time) + '; ' + str(data).rstrip('\r\n') + '\n' + content)
    except:
        with open(filename, 'a+') as f:
            f.write(str(data)+'\n')
    

if __name__ == "__main__":
    t = datetime(2018, 5, 21, 1, 23)
    tx = [['48cb4cc3-d841-498e-8601-c8794be40dc4', '0.5', '-0.6'], ['b5417b5a-d049-4ab1-ad4e-2150d2c8914e', '0.2', '-0'], ['274b2397-508c-419d-aa75-d0a909a80dd1', '0', '-5.6'], ['712b259d-3d24-431e-b4b8-e091b3a38ad6', '1.2', '-0']]
    tx2  = [['48cb4cc3-d841-498e-8601-c8794be40dc4', '0.6', '-0.5'], ['b5417b5a-d049-4ab1-ad4e-2150d2c8914e', '0', '-0.1'], ['274b2397-508c-419d-aa75-d0a909a80dd1', '-0.5', '0.5'], ['712b259d-3d24-431e-b4b8-e091b3a38ad6', '5', '-0.6']]
    tx3 = [['48cb4cc3-d841-498e-8601-c8794be40dc4','0','-0.127'],['b5417b5a-d049-4ab1-ad4e-2150d2c8914e','3.747','-0'],['274b2397-508c-419d-aa75-d0a909a80dd1','0','-0.062'],['712b259d-3d24-431e-b4b8-e091b3a38ad6','6.791','-0.498']]
    tx4 = [['48cb4cc3-d841-498e-8601-c8794be40dc4','0','-0.024'],['b5417b5a-d049-4ab1-ad4e-2150d2c8914e','0','-0'],['274b2397-508c-419d-aa75-d0a909a80dd1','0','-0.185'],['712b259d-3d24-431e-b4b8-e091b3a38ad6','5.353', '-0.093']]
    settle(tx, t)
    settle(tx2, t)
    settle(tx3, t)
    settle(tx4, t)