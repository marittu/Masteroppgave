from flask import Flask, render_template
import csv
from datetime import time, datetime
import io
from plotly.offline import plot
import plotly.graph_objs as go
import pandas as pd

import pandas as pd
app = Flask(__name__)

def get_plot():
    img = io.BytesIO()
    time = []
    consumed = []
    produced = []
    with open('test1.csv') as data:
        next(data)
        for line in csv.reader(data):
            datetime_obj = datetime.strptime(line[0].strip(), '%d-%m-%y %H:%M')
            time.append(datetime_obj)
            consumed.append(line[1])
            produced.append(line[2])
    cons = go.Scatter(
        x = time,
        y = consumed,
        name = "Consumed Electricity",
        line = dict(color = '#17BECF'),
        opacity = 0.8
    )

    prod = go.Scatter(
        x = time,
        y = produced,
        name = "Produced Electricity",
        line = dict(color = '#7F7F7F'),
        opacity = 0.8
    )

    data = [cons,prod]
    layout = go.Layout(
        title='Electricity consumption and production',
        xaxis=dict(
            title='Time',
        ),
        yaxis=dict(
            title='kWh',
        )
    )
    fig = dict(data=data, layout=layout)
    return plot(fig, output_type='div')


@app.route('/')

def home():
   
    my_plot = get_plot()
    
    return render_template('home.html', my_plot=my_plot)

def get_table():
    sellers = pd.read_excel('availability.xlsx')
    sellers.set_index(['Producer'], inplace=True)
    sellers.index.name=None
    return sellers


@app.route('/contract/')

def contract():
    table = get_table()
    return render_template('contract.html', table=table.to_html())

if __name__ == '__main__':
    #home()
    app.run(debug=True)
