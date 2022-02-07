import requests
import dateutil.parser as dp
from datetime import datetime, timedelta
from flask import Flask, render_template, request
import os
from flask_sqlalchemy import SQLAlchemy

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
    data = []
    records = db.session.query(Weather).filter_by(date=yesterday_date)
    for r in records:
        data_row = (r.city, r.date, r.time, r.air, r.humid)
        data.append(data_row)
    return render_template('index.html', headings=table_headings, data=data)


@app.route('/', methods=['POST'])
def render_results():
    city1 = request.form['city1']
    # city2 = request.form['city2']
    city2 = 'ST.PETERSBURG*'

    write_to_db(city1)
    write_to_db(city2)

    return render_template("index.html")


# Get frost.met.no API key as CLIENTID
if "CLIENTID" in os.environ:
    client_id = os.environ.get('CLIENTID')
else:
    print("You need to set your frost.me.no ID in CLIENTID enviroment variable first.")
    #sys.exit()

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
    parameters = {'name': city_name}
    r = requests.get(sources_url, parameters, auth=(client_id, ''))
    check_request(r)
    json = r.json()
    data = json['data']

    for i in range(len(data)):
        sn = data[i]['id']
        return sn


def get_observations(city):
    sn = get_sn(city)
    parameters = dict(sources=sn, elements=observation_metrics, referencetime=observation_period)
    r = requests.get(observations_url, parameters, auth=(client_id, ''))
    check_request(r)
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


def write_to_db(city):
    data = parse_observation_data(city)

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


if __name__ == '__main__':
    db.create_all()
    app.run()
