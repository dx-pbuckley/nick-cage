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

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'this_should_be_configured')

# host = os.environ['HUBOT_REST_INTERFACE_DB_PORT_27017_TCP_ADDR']
# user = app.config['MONGO_DB_USER']
# passwd = app.config['MONGO_DB_PASSWD']
# uri = 'mongodb://%s:%s@%s:27017/?authSource=admin' % (user, passwd, host)
# client = MongoClient(uri)
# db = client[app.config['MONGO_DB_NAME']]
# where db name is chewbot
# db.chewbot.insert_one({'message': data, 'text': resp.text, 'status_code': resp.status_code,
#                               'headers': resp.headers.items()})

MONGO_URI = os.environ.get('MONGODB_URI', 'shouldda_set_that_mongodb_uri')
MG_API_KEY = os.environ.get('MAILGUN_API_KEY', 'shouldda_set_that_mg_api_key')
MG_DOMAIN = os.environ.get('MAILGUN_DOMAIN', 'shouldda_set_that_mg_domain')
MG_API_URL = "https://api:%s@api.mailgun.net/v3/%s" % (MG_API_KEY, MG_DOMAIN)

CLIENT = pymongo.MongoClient(MONGO_URI)
DB = CLIENT['em_addr']
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

TOP_HUNDRED_LIST = [
    { 'name': 'Anchorage', 'latlong': '456' },
    { 'name': 'Los Angeles', 'latlong': '789' },
    { 'name': 'New York City', 'latlong': '123'}
 ]

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


@app.route('/formulae/')
def my_form():
    """Render the website's form page."""
    return render_template('someform.html', top_hundred_cities=[x['name'] for x in TOP_HUNDRED_LIST], boph='zobeeeeee')


@app.route('/formulae/', methods=['POST'])
def my_form_post():
    emailaddy = request.form['emailaddress']
    city = request.form['zipcode']
    # processed_email = emailaddy.upper()
    # return send_sbemail(processed_email, zipcode)
    addys = DB.em_addr
    one_record = {'email': emailaddy, 'city': city }
    app.logger.info("Inserting into db: %s, %s" % (one_record['email'], one_record['city']))
    addy_id = addys.insert_one(one_record)
    return "Sent to: %s in: %s (with id: %s)" % (emailaddy, city, addy_id)


@app.route('/bulkup/')
def bulk_form():
    """Render the bulk send form page."""
    return render_template('bulkform.html')


@app.route('/bulkup/', methods=['POST'])
def bulk_form_post():
    send_bulk_emails()
    return "Sent a bunch"


@app.route('/jscheck/')
def js_form():
    """Render the website's form page."""
    return render_template('fakeform.html')


# just mah functionsz


def fetch_weather(city):
    return "55 and Sunny"


def subject_phrase_picker(city):
    weather = fetch_weather(city)
    return AVG_PAIR, weather


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
    collection = [
        { "email": "buckmeisterq@gmail.com",
          "city": "Salem"
        },
        { "email": "weatherapp+anc1@klaviyo1.com1",
          "city": "Anchorage"
        }
    ]
    for email in DB.em_addr.find(): # collection:
        send_sbemail(email['email'], email['city'])


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
