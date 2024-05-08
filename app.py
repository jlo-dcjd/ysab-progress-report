from flask import Flask, request, render_template, jsonify
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv
import datetime
import os
import pytz
import pandas as pd
import re

load_dotenv() 

mongo_uri = os.getenv("MONGO_URI")
db_name = os.getenv("DB_NAME")

app = Flask(__name__)

cluster = MongoClient(mongo_uri)
db = cluster[db_name]
collection = db['progress_reports']

def get_program_list():
    cluster = MongoClient(mongo_uri)
    db = cluster[db_name]
    collection = db['ysab']
    # Retrieve all records from the collection
    cursor = collection.find()
    # Convert the cursor to a list of dictionaries
    records = list(cursor)
    # Create a Pandas DataFrame
    df = pd.DataFrame(records)
    cluster.close()
    return df.title.to_list()

# pre-populate fields auto
def get_app_list():
    cluster = MongoClient(mongo_uri)
    db = cluster[db_name]
    collection = db['ysab']
    # Retrieve all records from the collection
    cursor = collection.find()
    # Convert the cursor to a list of dictionaries
    records = list(cursor)
    # Create a Pandas DataFrame
    df = pd.DataFrame(records)
    df['app_record'] = pd.concat([df.timestamp.str[:10], df[['name', 'app_title', 'email', 'phone', 'title', 'amount', 'output1', 'output2', 'output3', 'output4', 'output5', 'target1', 'target2', 'target3', 'target4', 'target5', 'outcome1', 'outcome2', 'outcome3', 'outcome4', 'outcome5', 'target1.1', 'target2.1', 'target3.1', 'target4.1', 'target5.1']].astype(str)], axis=1).apply(lambda row: ' : '.join(row), axis=1)
    cluster.close()
    return df.app_record.to_list()

def get_prog_report_num():
    cluster = MongoClient(mongo_uri)
    db = cluster[db_name]
    collection = db['progress_reports']
    # Retrieve all records from the collection
    cursor = collection.find()
    # Convert the cursor to a list of dictionaries
    records = list(cursor)
    # Create a Pandas DataFrame
    df = pd.DataFrame(records)
    cluster.close()
    return df.shape[0] + 1

def progress_report_id(report_period):
    year = datetime.datetime.now().year
    application_number = get_prog_report_num()
    project_name = str(request.form.get('title'))
    project_abbreviation = re.sub(r'[^a-zA-Z0-9\s]', '', project_name)
    project_abbreviation = "".join(word[0] for word in project_abbreviation.split())
    funding = 'YSAB'
    # form type - A: application M: progress report mid-term F: progress report final
    form_type = str(report_period)
    # Generate unique ID
    unique_id = f"{year}-{application_number:03d}-{project_abbreviation}-{funding}-{form_type}"
    return unique_id

@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('index.html', dropdown_items = get_program_list(), app_list = get_app_list())

@app.route('/submit_form', methods=['POST'])
def submit_form():
        try:     
            # Get form data
            form_data = request.form.to_dict()
            name = request.form.get('name')
            email = request.form.get('email')
            form_id = progress_report_id(request.form.get('reporting_period'))

            #timestamp
            central_timezone = pytz.timezone('America/Chicago')
            current_time = datetime.datetime.now(central_timezone)
            timestamp = current_time.strftime("%m-%d-%Y %H:%M")
            
            form_data = {'_id': form_id, 'timestamp': timestamp, **form_data}

            # Insert data into MongoDB
            collection.insert_one(form_data)

            # return jsonify({'success': True, 'message': 'Form data submitted successfully'})
            return render_template('confirmation.html', name=name, email=email)
        except Exception as e:
            # return jsonify({'success': False, 'error': str(e)})
             return render_template('error.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=False)
