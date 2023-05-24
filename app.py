from flask import Flask, render_template, jsonify
import p2p_smartswitch

app = Flask(__name__)

switch_bulb_state = "off"
lightbulbs_state = ["off", "off", "off"]


@app.route('/')
def index():
    return render_template('index.html', switch_bulb_state=switch_bulb_state, lightbulbs_state=lightbulbs_state)


@app.route('/values')
def get_values():
    global switch_bulb_state
    global lightbulbs_state

    switch_bulb_state = p2p_smartswitch.switch_bulb_state
    lightbulbs_state = ["on", "on", "on"]

    return jsonify(switch_bulb_state=switch_bulb_state, lightbulbs_state=lightbulbs_state)


if __name__ == '__main__':
    app.run(port=8082)
