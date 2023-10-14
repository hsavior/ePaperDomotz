#!/usr/bin/python3
# -*- coding:utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for
import json

app = Flask(__name__)

# Load configuration from updateScreen.conf
config = {}
try:
    with open('updateScreen.conf', 'r') as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    print("Configuration file 'updateScreen.conf' not found.")

@app.route('/')
def index():
    return render_template('index.html', config=config)

@app.route('/update_config', methods=['POST'])
def update_config():
    new_config = {
        "api_key": request.form['api_key'],
        "agent_id": request.form['agent_id'],
        "api_url": request.form['api_url'],
    }

    # Update the config dictionary and save it to config.json
    config.update(new_config)
    with open('updateScreen.conf', 'w') as config_file:
        json.dump(config, config_file, indent=4)

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
