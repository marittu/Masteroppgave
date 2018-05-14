import csv

if __name__ == "__main__":
    contract = ['B', 'A', '1526293567.00469', '1526393567.00469']
    minu = 1.0
    bill = 0
    producer_bill = 0
    price = 0.5
    with open ('Testdata\8002.csv') as csvfile:
        with open ('Testdata\8001.csv') as csvfile2:
            next(csvfile)
            next(csvfile2)
           
            node1 = csvfile.readline()[0]
            node2 = csvfile2.readline()[0]
           
            list1 = csv.reader(csvfile)
            list2 = csv.reader(csvfile2)
            
            if node1 == contract[0]:
                prosumer = [list(map(float, x)) for x in list1]
                consumer = [list(map(float, x)) for x in list2]

            else:
                prosumer = [list(map(float, x)) for x in list2]
                consumer = [list(map(float, x)) for x in list1]

            for pro, con in zip(prosumer, consumer):
                sold = round((pro[2] - pro[1]), 3)
                bought = round((con[1] - con[2]), 3)
             
                if pro[0] == minu and con[0] == minu:
                    
                    if sold == bought:
                        bill += sold * price

                    elif sold > bought:
                        bill += bought*price
                        #assume excess on battery

                    else:
                        bill += sold*price
                        producer_bill += (bought-sold)*price
                
                print('Min', minu, 'Bill: ', round(bill, 3))
                print('Min', minu, 'Producer bill: ', round(producer_bill, 3))                        
                minu += 1
