"""
Flask Documentation:     http://flask.pocoo.org/docs/
Jinja2 Documentation:    http://jinja.pocoo.org/2/documentation/
Werkzeug Documentation:  http://werkzeug.pocoo.org/documentation/

This file creates your application.
"""

import os
import requests
from flask import Flask, render_template, request, redirect, url_for
import pymongo
import json

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'this_should_be_configured')

MONGODB_URI = os.environ.get('MONGODB_URI', 'shouldda_set_that_mongodb_uri')
MG_API_KEY = os.environ.get('MAILGUN_API_KEY', 'shouldda_set_that_mg_api_key')
MG_DOMAIN = os.environ.get('MAILGUN_DOMAIN', 'shouldda_set_that_mg_domain')
MG_API_URL = "https://api:%s@api.mailgun.net/v3/%s" % (MG_API_KEY, MG_DOMAIN)

WEATHERBIT_API_KEY = os.environ.get('WEATHERBIT_API_KEY', 'shouldda_set_that_wb_api_key')
WEATHERBIT_API_URL = 'https://api.weatherbit.io/v2.0/current'
WEATHERBIT_FORECAST_URL = 'https://api.weatherbit.io/v2.0/forecast/daily'

CLIENT = pymongo.MongoClient(MONGODB_URI)
DB = CLIENT['heroku_xncgtv8c']
# not right, everything matches email including "com" etc
# DB.em_addr.create_index([('email', pymongo.TEXT)], unique=True)

# sunny or +5 degrees
NICE_PAIR = { "subject": "It's nice out! Enjoy a discount on us.",
              "phrasing": "Hope you are enjoying the" }
# either precipitating or 5 degrees cooler than the average
NOTNICE_PAIR = { "subject": "Not so nice out? That's okay, enjoy a discount on us.",
                 "phrasing": "Take a break from the" }
AVG_PAIR = { "subject": "Enjoy a discount on us.",
             "phrasing": "Fine with the" }

with open('static/top100cities.json') as f:
    TOP_HUNDRED_LIST = json.load(f)

# TOP_HUNDRED_LIST = [ 'Bahstin', 'Nawyawk', 'Zebbs' ]

###
# Routing for your application.
###

@app.route('/')
def home():
    """Render website's home page."""
    return render_template('home.html')


@app.route('/about/')
def about():
    """Render the website's about page."""
    return render_template('about.html')


@app.route('/signup/')
def my_form():
    """Render the emailform page."""
    return render_template('emailform.html', top_hundred_cities=[x['name'] for x in TOP_HUNDRED_LIST])


@app.route('/signup/', methods=['POST'])
def my_form_post():
    emailaddy = request.form['emailaddress']
    city = request.form['city_name']
    # processed_email = emailaddy.upper()
    # return send_sbemail(processed_email, city_name)
    # addys = DB.em_addr # too many levels deep???
    one_record = {'email': emailaddy, 'city': city }
    app.logger.info("Inserting into db: %s / %s from client %s \n: record email %s, city %s" % (DB, DB.emaddrcol, CLIENT, one_record['email'], one_record['city']))
    DB.emaddrcol.insert_one(one_record)
    return "You are signed up with email: %s and city: %s!" % (emailaddy, city)


@app.route('/admin/')
def bulk_form():
    """Render the bulk send form page."""
    return render_template('bulkform.html')


@app.route('/admin/', methods=['POST'])
def bulk_form_post():
    total_sent = send_bulk_emails()
    return "%s emails sent" % (total_sent)


@app.route('/jscheck/')
def js_form():
    """testing some js malarkey"""
    return render_template('fakeform.html')


# just mah functionsz

def farenheit(ctemp):
    return round(9.0/5.0 * ctemp + 32)


def avg_based_on_forecast(city):
    """ calc the avg based on next 16 day forecast """
    wparams = { 'city': city,
                'key': WEATHERBIT_API_KEY
    }
    resp = requests.get(WEATHERBIT_FORECAST_URL, params=wparams)
    alltemps = [farenheit(x['temp']) for x in json.loads(resp.text)['data']]
    return round(sum(alltemps) / len(alltemps))


def fetch_weather(city):
    wparams = { 'city': city,
                'key': WEATHERBIT_API_KEY
    }
    resp = requests.get(WEATHERBIT_API_URL, params=wparams)
    # this works, need to likely raise for status, validate city (or pre-validate on the intake?)
    full_weather = json.loads(resp.text)
    app.logger.info("Got full_weather: %s" % (full_weather))
    weather_dict = {
        'temp': farenheit(full_weather['data'][0]['temp']),
        'conditions': full_weather['data'][0]['weather']['description'].lower(),
        'precip': full_weather['data'][0]['precip'],
        'forecast_temp': avg_based_on_forecast(city)
    }
    return weather_dict


def subject_phrase_picker(city):
    weather = fetch_weather(city)
    if weather['precip'] or weather['precip'] > 0 or weather['temp'] <= (weather['forecast_temp'] - 5):
        phrase = NOTNICE_PAIR
    elif weather['temp'] >= (weather['forecast_temp'] + 5):
        phrase = NICE_PAIR
    else:
        phrase = AVG_PAIR
    return phrase, "%s and %s" % (weather['temp'], weather['conditions'])


def send_sbemail(email_addy, city):
    given_pair, weather = subject_phrase_picker(city)
    mailtext = '%s %s weather in %s!' % ( given_pair['phrasing'], weather, city)
    mpayload = {'from': 'Excited User <mailgun@%s>' % (MG_DOMAIN),
                'to': '%s' % (email_addy),
                'subject': given_pair['subject'],
                'text': mailtext,
                'html': '<b>HTML</b> body of test mailgun message as hitmal'
    }
    # uncomment to really send the email
    # respo = requests.post(MG_API_URL + "/messages", params=mpayload)
    app.logger.info("Sent %s to: %s!" % (mailtext, email_addy))
    return "Sent %s to: %s!" % (mailtext, email_addy)


def send_bulk_emails():
    """ Send the emails out """
    email_count = 0
    for email in DB.emaddrcol.find(): # collection:
        send_sbemail(email['email'], email['city'])
        email_count += 1
    return email_count

###
# The functions below should be applicable to all Flask apps.
###

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=600'
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
