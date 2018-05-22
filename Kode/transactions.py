import csv
from datetime import datetime, timedelta
def get_transaction(filename, time):

    tx = []
    with open(filename) as data:
        next(data)
        for line in csv.reader(data):
            date = datetime.strptime(line[0], '%d-%m-%y %H:%M')
            tx.append([date, line[1], line[2]])
    
    if time == 0:
        return tx[0]

    else:
        for line in tx:
            
            if line[0] - time == timedelta(minutes = 1):
                return line
