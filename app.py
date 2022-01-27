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

# Define endpoint and parameters
endpoint = 'https://frost.met.no/observations/v0.jsonld'
parameters = {
    'sources': 'SN2606300,SN2280200',
    'elements': 'relative_humidity,air_temperature',#'mean(air_temperature P1D),sum(precipitation_amount P1D),mean(wind_speed P1D)',
    'referencetime': reference_time
}

# Issue an HTTP GET request
r = requests.get(endpoint, parameters, auth=(client_id,''))
# Extract JSON data
json = r.json()

# Check if the request worked, print out any errors
if r.status_code == 200:
    data = json['data']
    print('Data retrieved from frost.met.no!')
    print(data)
else:
    print('Error! Returned status code %s' % r.status_code)
    print('Message: %s' % json['error']['message'])
    print('Reason: %s' % json['error']['reason'])
