from flask import Flask, render_template, jsonify, request
import p2p_smartswitch

app = Flask(__name__)

switch_current_bulb = "none"
switch_bulb_state = "off"
lightbulbs_state = ["off", "off", "off"]




@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', switch_bulb_state=switch_bulb_state, lightbulbs_state=lightbulbs_state)


@app.route('/update_state', methods=['GET', 'POST'])
def update_state():
    global switch_current_bulb
    global switch_bulb_state
    global lightbulbs_state

    switch_current_bulb = request.form.get('current')
    switch_bulb_state = request.form.get('state')

    lightbulbs_state[0] = switch_bulb_state

    print(lightbulbs_state)

    return jsonify(switch_current_bulb=switch_current_bulb, switch_bulb_state=switch_bulb_state, lightbulbs_state=lightbulbs_state)

@app.route('/values')
def get_values():
    global switch_current_bulb
    global switch_bulb_state
    global lightbulbs_state

    return jsonify(switch_current_bulb=switch_current_bulb, switch_bulb_state=switch_bulb_state, lightbulbs_state=lightbulbs_state)


if __name__ == '__main__':
    app.run(port=8082)
