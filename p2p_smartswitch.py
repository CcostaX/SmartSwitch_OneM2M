import requests
import json
import time
import discoverIP
import paho.mqtt.client as mqtt
import re
from flask import Flask, render_template, jsonify, request
from multiprocessing import Process

app = Flask(__name__)

switch_current_bulb = "none"
switch_bulb_state = False

#get current time
current_time = time.localtime()
date_str = time.strftime("%Y-%m-%d %H:%M:%S", current_time)

#-------------------------------------------------------------------------#
# Constants
CSE_BASE = 'http://localhost:8000/cse-in'
ORIGINATOR = 'CAdmin'

#define the request header
HEADERS_GET = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-M2M-Origin': 'CAdmin',
    'X-M2M-RI': 'j7c9cmjc41',
    'X-M2M-RVI': '3',
    'rcn': '4' 
}

HEADERS_AE = {
    'Content-Type': 'application/json;ty=2',
    'Accept': 'application/json',
    'X-M2M-RI': 'unehu0e70j',
    'X-M2M-RVI': '3'
}

HEADERS_Container = {
    'Content-Type': 'application/json;ty=3',
    'Accept': 'application/json',
    'X-M2M-Origin': 'CAdmin',
    'X-M2M-RI': 'x2mqr3v0es',
    'X-M2M-RVI': '3'
}

HEADERS_Instance = {
    'Content-Type': 'application/json;ty=4',
    'Accept': 'application/json',
    'X-M2M-Origin': 'CAdmin',
    'X-M2M-RI': '5fr1znt75fb',
    'X-M2M-RVI': '3'
}

HEADERS_Subscription = {
    'Content-Type': 'application/json;ty=23',
    'Accept': 'application/json',
    'X-M2M-Origin': 'CAdmin',
    'X-M2M-RI': 'ysge7e8sxy',
    'X-M2M-RVI': '3'
}
#-------------------------------------------------------------------------#



#define the request body 
request_body_AE_smartswitch = {
    "m2m:ae": {
        "api": "N.smartswitch",
        "poa": ["http://172.22.196.204:8000/cse-in/smartswitch"],
        "rn": "smartswitch",
        "srv": ["3"],
        "rr": False
    }
}

request_body_AE_lightbulb = {
    "m2m:ae": {
        "api": "N.lightbulb",
        "poa": ["http://192.168.1.3:8000/cse-in/lightbulb"],
        "rn": "lightbulb",
        "srv": ["3"],
        "rr": False
    }
}

request_body_container = {
     "m2m:cnt": {
        "mbs": 10000,
        "mni": 10,
        "rn": "state"
    }
}

request_body_instance_smartswitch = {
     "m2m:cin": {
        "cnf": "text/plain:0",
        "con": "{\"controlledLight\": \"lightbulb1\"}",
        "rn": "smartswitch-instance_0"
    }
}

request_body_instance_lightbulb = {
    "m2m:cin": {
        "cnf": "text/plain:0",
        "con": "{\"state\": \"off\"}",
        "rn": "lightbulb-instance_0"
    }
}

request_body_subscription = {
    "m2m:sub": {
        "enc": {
            "net": [
                1,
                2,
                3,
                4
            ]
        },
        "nu": [
            "http://192.168.1.3:8000/bulb"
        ],
        "rn": "switch"
    }
}

#-------------------------------------------------------------------------#


# Define helper functions for getting and creating resources
def get_resource(url):
    response = requests.get(url, headers=HEADERS_Instance)
    if response.status_code == 200:
        resource = response.json()
    
        if 'm2m:cin' in resource and 'la' in resource['m2m:cin']:
            latest_cin_url = resource['m2m:cin']['la']
            return get_resource(latest_cin_url)
        elif 'm2m:cin' in resource and 'con' in resource['m2m:cin']:
            return json.loads(resource['m2m:cin']['con'])
        elif 'm2m:cnt' in resource:  
            latest_cin_url = url + "/" + resource['m2m:cnt']['ri'] + "/la"  # Construct the latest 'm2m:cin' URL using 'ri'
            return get_resource(latest_cin_url)  # Call get_resource with the latest 'm2m:cin' URL
        else:
            return resource
    else:
        print(f"Error: {response.status_code}")
        return None
    
# GET AE, Container or Container Instance
def get_CSE_IN(url):
    response = requests.get(url, headers=HEADERS_GET)
    if response.status_code == 200:  # 200 - OK
        return response.json()
    else:
        print(f"Error getting resource: {response.status_code}")
        return None

def get_latest_instance(url, get_container_length, name):
    latest_date = "20220424T154923,183229"
    latest_instance = ""
    for i in range(0, get_container_length):
        state = f"{url}/{name}-instance_" + str(i)
        creationDate = get_CSE_IN(state)['m2m:cin']['ct']
        for i in range(len(creationDate)):
            if creationDate[i] > latest_date[i]:
                latest_date = creationDate    
                latest_instance = get_CSE_IN(state)
    return latest_instance

def change_value_smartswitch(latest_instance, smartswitch_instance_name_value):
    if latest_instance:
        current_state = json.loads(latest_instance['m2m:cin']['con'])
        current_state['controlledLight'] = "lightbulb" + str(smartswitch_instance_name_value)
        return current_state
    else:
        print("No latest instance found")

def change_value_lightbulb(latest_instance):
    if latest_instance:
        current_state = json.loads(latest_instance['m2m:cin']['con'])

        if current_state['state'] == 'off':
            current_state['state'] = 'on'
        elif current_state['state'] == 'on':
            current_state['state'] = 'off'
        else:
            print("Invalid state value")

        return current_state

    else:
        print("No latest instance found")

# Application Entity (POST, DELETE)
def create_application_entity(url, data):
    response = requests.post(url, headers=HEADERS_AE, data=json.dumps(data))
    if response.status_code == 201:  # 201 Created
        print("Created successfully")
        return json.loads(response.text)
    else:
        print(f"Error creating resource: {response.status_code}")
        return None
    
def delete_application_entity(url):
    response = requests.delete(url, headers=HEADERS_GET)
    if response.status_code == 200 or response.status_code == 204:
        print(f"Resource at {url} deleted successfully.")
    else:
        print(f"Error deleting resource: {response.status_code}")


# Container (POST)
def create_container(url, data):
    response = requests.post(url, headers=HEADERS_Container, data=json.dumps(data))
    if response.status_code == 201:  # 201 Created
        print("Created successfully")
        return json.loads(response.text)
    else:
        print(f"Error creating resource: {response.status_code}")
        return None
    
# Container Instance (POST, DELETE)
def create_container_instance(url, data):
    response = requests.post(url, headers=HEADERS_Instance, data=json.dumps(data))
    if response.status_code == 201:  # 201 Created
        print("Created successfully")
        return json.loads(response.text)
    else:
        print(f"Error creating resource: {response.status_code}")
        return None

    
def delete_container_instance(url):
    response = requests.delete(url, headers=HEADERS_GET)
    if response.status_code == 200 or response.status_code == 204:
        print(f"Resource at {url} deleted successfully.")
    else:
        print(f"Error deleting resource: {response.status_code}")

# subscription (POST)
def create_subscription(url, data):
    response = requests.post(url, headers=HEADERS_Subscription, data=json.dumps(data))
    if response.status_code == 201:  # 201 Created
        print("Created successfully")
        return json.loads(response.text)
    else:
        print(f"Error creating resource: {response.status_code}")
        print(response.text)
        return None
#-------------------------------------------------------------------------#



#MQTT
#-------------------------------------------------------------------------#
# Define MQTT client
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print('Connected to MQTT broker')
  
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        print(f"Topic: {msg.topic} Message: {payload}")

        if ("Change lightbulb state" in payload and (role == "lightbulb" or role == "bulb")):
            get_container_length = int(repr(get_CSE_IN(lightbulb_Instance)['m2m:cnt']['cni']))
            latest_instance = get_latest_instance(lightbulb_Instance, get_container_length, "lightbulb")
            lightbulb_instance_name_value = get_container_length
            request_body_instance_lightbulb["m2m:cin"]["con"] = json.dumps(change_value_lightbulb(latest_instance))
            request_body_instance_lightbulb["m2m:cin"]["rn"] = "lightbulb-instance_" + str(lightbulb_instance_name_value)
            create_container_instance(lightbulb_Instance, request_body_instance_lightbulb)
            client.publish("lightbulb" + str(lightbulbCT), request_body_instance_lightbulb["m2m:cin"]["con"])
        else:
            print("Change lightbulb")

            switch_bulb_state = json.loads(request_body_instance_lightbulb["m2m:cin"]["con"])["state"]
            requests.post('http://127.0.0.1:8082/update_state', data={'state': switch_bulb_state})    
    except json.JSONDecodeError:
        print(f"Topic: {msg.topic} Message: {msg.payload} is not a valid JSON")



#---------------------------------------------------------------------------------------------------------------#

#  MAIN LOOP
if __name__ == '__main__':
    localIP = discoverIP.get_local_ip()
    print(localIP)
    CSE_BASE = "http://" + localIP + ":8000/cse-in"

    #Get role
    role = discoverIP.attributeRole()

    # MQTT Broker URL and Port
    broker_url = localIP
    broker_port = 1883 

    # Set the callback functions
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to the MQTT broker
    client.connect(broker_url, broker_port, keepalive=60)
    
    #Connect to HTML page
    page_state = False
    try:
        response = requests.get('http://127.0.0.1:8082')
        if response.status_code == 200:
            page_state = True
            print('Smart switch Page is open')

            #update HTML page with current values
            switch_current_bulb = "lightbulb1"
            requests.post('http://127.0.0.1:8082/update_state', data={'current': switch_current_bulb})      
        else:
            print('Failed to update state')
    except requests.exceptions.ConnectionError:
        print('Connection to the server failed. Unable to determine page state.')
    
    #SMARTSWITCH
    if (role == "smartswitch" or role == "switch"):
        client.loop_start()
        #get the smart switch and lightbulbs AE if already existed
        smart_switch_Container = f"{CSE_BASE}/smartswitch"
        if get_CSE_IN(smart_switch_Container) is not None:
            delete_application_entity(smart_switch_Container) 

        #create application entity
        smart_switch_AE = f"{CSE_BASE}"
        request_body_AE_smartswitch["m2m:ae"]["poa"] = [CSE_BASE + "/smartswitch"]
        create_application_entity(smart_switch_AE, request_body_AE_smartswitch)

        #create a container
        smart_switch_Container = f"{CSE_BASE}/smartswitch"
        create_container(smart_switch_Container, request_body_container)

        #create a container instance
        smart_switch_Instance = f"{CSE_BASE}/smartswitch/state"
        create_container_instance(smart_switch_Instance, request_body_instance_smartswitch)

        

        client.subscribe("switch")
        #client.publish("switch", json.dumps(request_body_instance_smartswitch["m2m:cin"]["con"]))

        #create subscription
        #request_body_subscription["m2m:sub"]["nu"] = ["http://" + "localhost" + ":1400/monitor"]
       #request_body_subscription["m2m:sub"]["rn"] = role
       # print(request_body_subscription)
        #create_subscription(smart_switch_Instance, request_body_subscription)
        

        ips = discoverIP.discoverIPS()
        ips_onem2m = []
        lightbulb_Container = f"{CSE_BASE}/lightbulb"
        n_of_bulbs = 0
        for ip in ips:
            n_of_bulbs += 1
            print(ip)
            try:
                #Verify if the lightbulb container exists and subscribe to the respective lightbulb
                lightbulb_container = "http://" + ip + ":8000/cse-in/lightbulb"
                if get_CSE_IN(lightbulb_container) is not None:         
                    #get the creation date of lightbulb
                    get_lightbulb_ct = get_CSE_IN(lightbulb_container)['m2m:ae']['ct'].replace(",", "")
                    #append to array of lightbulbs
                    ips_onem2m.append(get_lightbulb_ct)
                    #
                    client.subscribe("lightbulb" + get_lightbulb_ct)
            except requests.exceptions.RequestException as e:
                print("Error:", e)
        if (len(ips_onem2m) > 0):
            while True:
                print("Press '1' for ON/OFF, '2' for changing the controlled lightbulb, 'q' to quit")
                button_press = input()
                
                smart_switch_Instance = f"{CSE_BASE}/smartswitch/state"   
                get_container_length = int(repr(get_CSE_IN(smart_switch_Instance)['m2m:cnt']['cni']))
                latest_instance = get_latest_instance(smart_switch_Instance, get_container_length, "smartswitch")

                if button_press == '1':
                    current_state = json.loads(latest_instance['m2m:cin']['con'])

                    # Extract the number of the current_state of the lightbubl
                    number = re.findall(r'\d+', current_state['controlledLight'])[0]
                    #get the ct date of the respective lightbulb
                    lightbulbCT = ips_onem2m[int(number)-1]
                    #send a message to the respective lightbulb to change his state
                    client.publish("lightbulb" + str(lightbulbCT), "Change lightbulb state")
                elif button_press == '2':
                    get_container_length = int(repr(get_CSE_IN(smart_switch_Instance)['m2m:cnt']['cni']))
                    latest_instance = get_latest_instance(smart_switch_Instance, get_container_length, "smartswitch")
                    smartswitch_instance_name_value = get_container_length

                    #verify if exists more than 1 lightbulb
                    if (get_container_length > 0):              
                        if (get_container_length > smartswitch_instance_name_value):
                            #move to the next lightbulb
                            request_body_instance_smartswitch["m2m:cin"]["con"] = json.dumps(change_value_smartswitch(latest_instance, smartswitch_instance_name_value+1))          
                        elif (get_container_length == smartswitch_instance_name_value):
                            #go back to lightbulb1 (first lightbulb)
                            request_body_instance_smartswitch["m2m:cin"]["con"] = json.dumps(change_value_smartswitch(latest_instance, 1))

                        #create container instance
                        request_body_instance_smartswitch["m2m:cin"]["rn"] = "smartswitch-instance_" + str(get_container_length)
                        create_container_instance(smart_switch_Instance, request_body_instance_smartswitch)

                        #update HTML page with current values
                        switch_current_bulb = json.loads(request_body_instance_smartswitch["m2m:cin"]["con"])["controlledLight"]
                        requests.post('http://127.0.0.1:8082/update_state', data={'current': switch_current_bulb})                      
                    else:
                        print("Only 1 lightbulb is available")
                elif button_press == 'q':
                    break
                else:
                    print("Invalid input. Try again.")
        else:
            print("No lightbulbs available")

    elif(role == "lightbulb" or role == "bulb"):     #LIGHTBULB
        lightbulb_AE = f"{CSE_BASE}"
        lightbulb_container = f"{CSE_BASE}/lightbulb"
        lightbulb_Instance = f"{CSE_BASE}/lightbulb/state"

        if get_CSE_IN(lightbulb_container) is not None:
            delete_application_entity(lightbulb_container)

        #create application entity for smart switch and lightbulbs  
        request_body_AE_lightbulb["m2m:ae"]["poa"] = [CSE_BASE + "/lightbulb"]
        create_application_entity(lightbulb_AE, request_body_AE_lightbulb)

        #create a container for each AE
        create_container(lightbulb_container, request_body_container)

        #create a container instance for each AE container
        create_container_instance(lightbulb_Instance, request_body_instance_lightbulb)

        #extract the last number of the local ip and subscribe to the respective lightbulb
        lightbulbCT = get_CSE_IN(lightbulb_container)['m2m:ae']['ct'].replace(",", "")
        print("lightbulb" + lightbulbCT)
        client.subscribe("lightbulb" + lightbulbCT)
        client.loop_forever()
    # Clean up when done
    client.loop_stop()
    client.disconnect()


