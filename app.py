import json
from pydoc import source_synopsis
import requests
from datetime import datetime, timedelta
import os
import sys


# Get CLIENTID from enviroment variable
if "CLIENTID" in os.environ:    
    client_id = os.environ.get('CLIENTID')
else:
    print("You need to set your frost.me.no ID in CLIENTID enviroment variable first.")
    sys.exit()

# Set variable for referencetime parameter in API call
today = datetime.strftime(datetime.now(), '%Y-%m-%d')
yesterday = datetime.strftime((datetime.now() - timedelta(1)), '%Y-%m-%d')
reference_time = yesterday + '/' + today

# Metrics to monitor
metrics = 'relative_humidity,air_temperature'
# Cities to compare
city1 = 'SORTAVALA'
city2 = 'ST.PETERSBURG (VOEJKOVO) (26063-0)'

# Define endpoint and parameters
observations_url = 'https://frost.met.no/observations/v0.jsonld'
sources_url = 'https://frost.met.no/sources/v0.jsonld'

def check_request(request):
    # Check if the request worked, print out any errors
    json = request.json()
    if request.status_code == 200:
        data = json['data']
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
        id = data[i]['id']
        name = data[i]['name']
        
    return id,name


def get_observations(city, time_period, metrics):
    
    sn = get_sn(city)[0]
    print(sn)
    #city_name = get_sn(city)[0]
    print(metrics)
    print(time_period)
    parameters = {
        'sources': sn,
        'elements': metrics, 
        'referencetime': time_period
    }

    r = requests.get(observations_url, parameters, auth=(client_id,''))
    #check_request(r)
    # Extract JSON data
    json = r.json()
    data = json['data']
    # parse json data
    for i in range(len(data)):
        row = data[i]['observations']
        data_datetime = data[i]['referenceTime']
        time = (data_datetime.split('T')[1]).split('.')[0]
        date = (data_datetime.split('T')[0])
        for k in range(len(row)):
            param1 = row[k]['elementId']
            if param1 == 'air_temperature':
                val = row[k]['value']
                unit = row[k]['unit']
                print(f"{sn} {date} {time} {param1} {val} {unit}")
    
get_observations(city1,reference_time,metrics)