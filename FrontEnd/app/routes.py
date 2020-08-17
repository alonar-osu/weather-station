from flask import render_template
from flask import Response
from app import app
import pymysql
import io
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import pandas as pd
#import seaborn as sns
import numpy as np
import datetime
from flask import send_from_directory 



@app.route('/')

@app.route('/local')
def local():

    db = pymysql.connect("localhost", "alona", "raspas", "weather")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM weathervals ORDER BY datetime DESC LIMIT 1")
    row = cursor.fetchone()
    temp = str('{0:0.1f}'.format(row[1]))
    humid = str('{0:0.1f}'.format(row[2]))

    is_active = 0
    alarm = ''

    cursor.execute("SELECT * FROM alarms")
    numrows = cursor.rowcount
    for x in xrange(0, numrows):
        row = cursor.fetchone()
        is_active = row[4]
        sensor_type = row[1]
        trigger = row[2]
        threshold = row[3]        

        if is_active == 1:
            if sensor_type == 'humid':
                alarm = alarm + "Humidity is "
                if trigger == 'g':
                    alarm = alarm + "above " + str(threshold) + " % \n"
                else:
                    alarm = alarm + "below " + str(threshold) + " % \n"
            elif sensor_type == 'temp':
                alarm = alarm + "Temperature is "
                if trigger == 'g':
                    alarm = alarm + "above " + str(threshold) + " deg F \n"
                else:
                    alarm = alarm + "below " + str(threshold) + " deg F \n"

    if alarm == '':
        alarm = ' -- '
    
    weathervals = {'temp': temp, 'humid': humid, 'rain': 0, 'alarm': alarm}
    return render_template('local.html', title='My Weather', weathervals=weathervals)

@app.route('/show/<filename>')
def show_image(filename):
    return send_from_directory("../images", "picture.jpg")


@app.route('/chart.png')
def chart_png():
    chart = create_chart()
    output = io.BytesIO()
    FigureCanvas(chart).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

def create_chart():

    #code from jupyter
    df = pd.read_csv('http://127.0.0.1:82/data/') # read from server
    df.columns=['i', 'datetime', 'temp', 'humid', 'd']
    
    #config datetime as index
    f = '%Y-%m-%d %H:%M:%S'
    df['datetime'] = pd.to_datetime(df['datetime'], format=f, errors='coerce')
    df = df[df.datetime.notnull()]
    df = df.set_index('datetime')

    df['Year'] = df.index.year
    df['Month'] = df.index.month
    df['Hour'] = df.index.hour

    #select one day and plot
    fig = Figure()

    start, end = '2019-07-24','2019-07-24'

    df2 = df.loc[start:end, 'temp']
    df_h = pd.rolling_mean(df2, 60)

    #start, end = '2019-07-24', '2019-07-24'

    ax = fig.add_subplot(1,1,1)
    ax.plot(df2, marker='.', linestyle='-', linewidth=0.5, label='Hourly')
    ax.plot(df_h, marker='.', linestyle='-', label='1h Rolling Mean')

    ax.set_ylabel('deg F')
    ax.set_xlabel('Time sec')
    ax.legend()
   
    return fig
