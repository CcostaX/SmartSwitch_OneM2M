from flask import Flask, render_template, jsonify, request
import p2p_smartswitch
import re
import subprocess
import os
import requests
import discoverIP

app = Flask(__name__)

switch_current_bulb = "none"
switch_bulb_state = "off"
lightbulbs_state = []
lightbulbs_number = "0"

global user_input
user_input = "0"


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', switch_bulb_state=switch_bulb_state, lightbulbs_state=lightbulbs_state)

@app.route('/update_state', methods=['GET', 'POST'])
def update_state():
    global switch_current_bulb
    global switch_bulb_state
    global lightbulbs_state

    if (request.form.get('current') is not None):
        switch_current_bulb = request.form.get('current')

    if(request.form.get('state') is not None and request.form.get('state') != "Change lightbulb state"):
        switch_bulb_state = request.form.get('state')

    current_bulb_number = int(re.search(r'\d+', switch_current_bulb).group())

    lightbulbs_state[current_bulb_number-1] = switch_bulb_state

    return jsonify(switch_current_bulb=switch_current_bulb, switch_bulb_state=switch_bulb_state, lightbulbs_state=lightbulbs_state)

@app.route('/initialize_bulbs', methods=['POST'])
def initialize_bulbs():
    global lightbulbs_state
    global lightbulbs_number

    if(request.form.get('state') is not None and request.form.get('state') != "Change lightbulb state"):
        switch_bulb_state = request.form.get('state')

    print(switch_bulb_state)
    lightbulbs_state.append(switch_bulb_state)

    return jsonify(switch_current_bulb=switch_current_bulb, switch_bulb_state=switch_bulb_state, lightbulbs_state=lightbulbs_state)


@app.route('/values')
def get_values():
    global switch_current_bulb
    global switch_bulb_state
    global lightbulbs_state
    global user_input

    return jsonify(switch_current_bulb=switch_current_bulb, switch_bulb_state=switch_bulb_state, lightbulbs_state=lightbulbs_state)


@app.route('/handle_input', methods=['POST'])
def handle_input():
    global user_input
    user_input = request.form['input']

    if user_input == '1':
        print("change state of lightbulb")
    elif user_input == '2':
        print("Change lightbulb action")
    return user_input

@app.route('/get_input', methods=['GET'])
def get_input():
    global user_input

    return user_input

@app.route('/update_input', methods=['POST'])
def update_input():
    global user_input

    user_input = "0"
    return ""

@app.route('/lightbulb/<lightbulbCT>', methods=['POST'])
def receive_message(lightbulbCT):
    #message = request.json
    message = request.form.get('message')
    # Process the received message as needed
    print(message)
    return "Message received successfully!"

if __name__ == '__main__':
    localIP = discoverIP.get_local_ip()
    app.run(host=localIP, port=8082)
