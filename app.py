import requests
import dateutil.parser as dp
from datetime import datetime, timedelta
from flask import Flask, render_template, request
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
table_headings = ("City", "Date", "Time", "Air Temperature", "Humidity")
today_date = datetime.strftime(datetime.now(), '%Y-%m-%d')
yesterday_date = datetime.strftime((datetime.now() - timedelta(1)), '%Y-%m-%d')
observation_period = yesterday_date + '/' + today_date
observation_metrics = 'relative_humidity,air_temperature'

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Weather(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(80), unique=False, nullable=False)
    date = db.Column(db.Date, unique=False, nullable=False)
    time = db.Column(db.Time, unique=False, nullable=False)
    air = db.Column(db.Float, unique=False, nullable=False)
    humid = db.Column(db.Float, unique=False, nullable=False)

    def __init__(self, city, date, time, air, humid):
        self.city = city
        self.date = date
        self.time = time
        self.air = air
        self.humid = humid


@app.route('/', methods=['GET'])
def weather_dashboard():
    city1 = read_city_data('SORTAVALA', yesterday_date)
    city2 = read_city_data('ST.PETERSBURG (VOEJKOVO) (26063-0)', yesterday_date)
    return render_template('index.html', headings=table_headings, data=city1, spbdata=city2)


@app.route('/', methods=['POST'])
def render_results():

    city1 = request.form['city1']
    city2 = request.form['city2']

    db_data = read_table(Weather)

    loaded_data = parse_observation_data(city1)
    loaded_data += parse_observation_data(city2)

    new_data = []

    for r in loaded_data:
        if r not in db_data:
            new_data.append(tuple(r))

    if len(new_data) == 0:
        print('No new data')
    else:
        print(new_data)
        write_to_db(new_data)

    return render_template("index.html")


# Get frost.met.no API key as CLIENTID
if "CLIENTID" in os.environ:
    client_id = os.environ.get('CLIENTID')
else:
    print("You need to set your frost.me.no ID in CLIENTID enviroment variable first.")


# Define endpoint and parameters
observations_url = 'https://frost.met.no/observations/v0.jsonld'
sources_url = 'https://frost.met.no/sources/v0.jsonld'


def check_request(request):
    # Check if the request worked, print out any errors
    json = request.json()
    if request.status_code == 200:
        print('Data retrieved from frost.met.no!')

    else:
        print('Error! Returned status code %s' % request.status_code)
        print('Message: %s' % json['error']['message'])
        print('Reason: %s' % json['error']['reason'])
    return


# Get SN from city name
def get_sn(city_name):

    if bool(' ' in city_name):
        split_string = city_name.split(' ')
        city_for_request = split_string[0] + '*'
        print(city_for_request)
    else:
        city_for_request = city_name

    parameters = {'name': city_for_request}
    print(parameters)
    r = requests.get(sources_url, parameters, auth=(client_id, ''))
    #check_request(r)
    json = r.json()
    data = json['data']

    for i in range(len(data)):
        sn = data[i]['id']
        return sn


def get_observations(city):
    sn = get_sn(city)
    parameters = dict(sources=sn, elements=observation_metrics, referencetime=observation_period)
    r = requests.get(observations_url, parameters, auth=(client_id, ''))
    #check_request(r)
    # Extract JSON data
    json = r.json()
    data = json['data']
    return data


def parse_observation_data(city):
    data = get_observations(city)
    result = []

    # parse data
    for i in range(len(data)):
        row = data[i]['observations']
        iso8601 = data[i]['referenceTime']
        date_iso = dp.parse(iso8601).date()
        time_iso = dp.parse(iso8601).time()

        for k in range(len(row)):
            param = row[k]['elementId']

            if param == 'air_temperature':
                air = row[k]['value']

            if param == 'relative_humidity':
                humid = row[k]['value']

        entry = (city, str(date_iso), str(time_iso), air, humid)
        result.append(tuple(entry))

    return result


def write_to_db(data):

    for item in data:
        city_name = item[0]
        date = item[1]
        time = item[2]
        temp = item[3]
        humid = item[4]

        entry = Weather(city_name, date, time, temp, humid)
        db.session.add(entry)

    db.session.commit()
    return


def read_table(table_name):
    data = []
    records = db.session.query(table_name)
    for r in records:
        data_row = (r.city, str(r.date), str(r.time), r.air, r.humid)
        data.append(data_row)
    return data


def read_city_data(city, date):
    data = []
    records = db.session.query(Weather).filter_by(city=city, date=date)
    for r in records:
        data_row = (r.city, r.date, r.time, r.air, r.humid)
        data.append(data_row)
    return data


if __name__ == '__main__':
    db.create_all()
    app.run()

