import requests
import dateutil.parser as dp
from datetime import datetime, timedelta
from flask import Flask, render_template, request
import os
import sys

app = Flask(__name__)


@app.route('/')
def weather_dashboard():
    return render_template('weather.html')


@app.route('/', methods=['POST'])
def render_results():
    city1 = request.form['city1']
    data = get_observations(city1)
    # data = get_sn(city1)
    return data


# Get CLIENTID from enviroment variable
if "CLIENTID" in os.environ:
    client_id = os.environ.get('CLIENTID')
else:
    print("You need to set your frost.me.no ID in CLIENTID enviroment variable first.")
    sys.exit()

# Define endpoint and parameters
observations_url = 'https://frost.met.no/observations/v0.jsonld'
sources_url = 'https://frost.met.no/sources/v0.jsonld'


def check_request(request):
    # Check if the request worked, print out any errors
    json = request.json()
    if request.status_code == 200:
        print('Data retrieved from frost.met.no!')

    else:
        print('Error! Returned status code %s' % r.status_code)
        print('Message: %s' % json['error']['message'])
        print('Reason: %s' % json['error']['reason'])
    return


# Get SN from city name
def get_sn(city_name):
    parameters = {
        'name': city_name
    }
    r = requests.get(sources_url, parameters, auth=(client_id, ''))
    check_request(r)

    json = r.json()
    data = json['data']

    for i in range(len(data)):
        sn = data[i]['id']

        return sn


city = 'SORTAVALA'


def get_observations(city):
    sn = get_sn(city)
    today_date = datetime.strftime(datetime.now(), '%Y-%m-%d')
    yesterday_date = datetime.strftime((datetime.now() - timedelta(1)), '%Y-%m-%d')
    period = yesterday_date + '/' + today_date
    metrics = 'relative_humidity,air_temperature'

    parameters = dict(sources=sn, elements=metrics, referencetime=period)

    r = requests.get(observations_url, parameters, auth=(client_id, ''))
    check_request(r)
    # Extract JSON data
    json = r.json()
    data = json['data']

    # parse json data
    for i in range(len(data)):
        row = data[i]['observations']
        iso8601 = data[i]['referenceTime']
        date = dp.parse(iso8601).date()
        time = dp.parse(iso8601).time()

        for k in range(len(row)):
            d = ""
            param = row[k]['elementId']

            if param == 'air_temperature':
                val = row[k]['value']
                unit = row[k]['unit']
                sys.stdout.write('{} {} {} {} {} {}\n'.format(city, sn, date, time, param, val))

            if param == 'relative_humidity':
                val = row[k]['value']
                unit = row[k]['unit']
                sys.stdout.write('{} {} {} {} {} {}\n'.format(city, sn, date, time, param, val))



    # return temp


get_observations(city)

# if __name__ == '__main__':
#    app.run()
