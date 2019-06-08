"""
Flask Documentation:     http://flask.pocoo.org/docs/
Jinja2 Documentation:    http://jinja.pocoo.org/2/documentation/
Werkzeug Documentation:  http://werkzeug.pocoo.org/documentation/

This file creates your application.
"""

import os
import requests
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)

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

client = MongoClient(MONGO_URI)
db = client['emailaddresses']

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
    return render_template('someform.html')

@app.route('/formulae/', methods=['POST'])
def my_form_post():
    emailaddy = request.form['emailaddress']
    zipcode = request.form['zipcode']
    processed_email = emailaddy.upper()
    return send_sbemail(processed_email, zipcode)

@app.route('/jscheck/')
def js_form():
    """Render the website's form page."""
    return render_template('fakeform.html')

# just mah functionsz
# mailgun doc/example as ruby
# require 'rest-client'

# RestClient.post API_URL+"/messages",
#     :from => "ev@example.com",
#     :to => "ev@mailgun.net",
#     :subject => "This is subject",
#     :text => "Text body",
#     :html => "<b>HTML</b> version of the body!"
def send_sbemail(email_addy, zipcode):
    mpayload = {'from': 'Excited User <mailgun@%s>' % (MG_DOMAIN),
                'to': '%s' % (email_addy),
                'subject': 'test %s from mailgun heroku app' % (zipcode),
                'text': 'test body of mailgun message from heroku yep yep yeppers',
                'html': '<b>HTML</b> body of test mailgun message as hitmal'
    }
    respo = requests.post(MG_API_URL + "/messages", params=mpayload)
    return "Sent to: %s in: %s" % (email_addy, zipcode)

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
