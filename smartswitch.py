import requests
import json
import time
import discoverIP
import paho.mqtt.client as mqtt

smartswitch_instance_value = 0
lightbulb1_instance_value = 0
lightbulb2_instance_value = 0

# Constants
CSE_BASE = 'http://localhost:8080/cse-in'
ORIGINATOR = 'CAdmin'

cse_host = 'localhost'
cse_port = '8080'
cse_base = 'your_cse_base_name'
api_key = 'your_api_key'
remote_cse_id = 'remote_cse_id'
remote_cse_url = 'http://remote_cse_host:remote_cse_port'

url = f'http://{cse_host}:{cse_port}/{cse_base}'


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

#define the request body 
request_body_AE_smartswitch = {
    "m2m:ae": {
        "api": "N.smartswitch",
        "poa": ["http://192.168.1.2:8080/smartswitch"],
        "rn": "smartswitch",
        "srv": ["3"],
        "rr": False
    }
}

request_body_AE_lightbulb1 = {
    "m2m:ae": {
        "api": "N.lightbulb1",
        "poa": ["http://192.168.1.3:8080/lightbulb1"],
        "rn": "lightbulb1",
        "srv": ["3"],
        "rr": False
    }
}

request_body_AE_lightbulb2 = {
    "m2m:ae": {
        "api": "N.lightbulb2",
        "poa": ["http://192.168.1.4:8080/lightbulb2"],
        "rn": "lightbulb2",
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

current_time = time.localtime()
date_str = time.strftime("%Y-%m-%d %H:%M:%S", current_time)

request_body_instance_smartswitch = {
     "m2m:cin": {
        "cnf": "text/plain:0",
        "con": "{\"controlledLight\": \"lightbulb1\"}",
        "rn": "smartswitch-instance_" + str(smartswitch_instance_value) + ""
    }
}

request_body_instance_lightbulb1 = {
    "m2m:cin": {
        "cnf": "text/plain:0",
        "con": "{\"state\": \"off\"}",
        "rn": "lightbulb1-instance_" + str(lightbulb1_instance_value) + ""
    }
}

request_body_instance_lightbulb2 = {
    "m2m:cin": {
        "cnf": "text/plain:0",
        "con": "{\"state\": \"off\"}",
        "rn": "lightbulb2-instance_" + str(lightbulb2_instance_value) + ""
    }
}

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

def get_latest_instance(get_container_length, name):
    latest_date = "20220424T154923,183229"
    latest_instance = ""
    for i in range(0, get_container_length):
        state = f"{CSE_BASE}/{name}/state/{name}-instance_" + str(i)
        creationDate = get_CSE_IN(state)['m2m:cin']['ct']
        for i in range(len(creationDate)):
            if creationDate[i] > latest_date[i]:
                latest_date = creationDate    
                latest_instance = get_CSE_IN(state)
    return latest_instance

def change_value_smartswitch(latest_instance):
    if latest_instance:
        current_state = json.loads(latest_instance['m2m:cin']['con'])

        if current_state['controlledLight'] == 'lightbulb1':
            current_state['controlledLight'] = 'lightbulb2'
        elif current_state['controlledLight'] == 'lightbulb2':
            current_state['controlledLight'] = 'lightbulb1'
        else:
            print("Invalid controlledLight value")

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









#Define the AE, container and container instance  URLs
smart_switch_AE = f"{CSE_BASE}"
lightbulb1_AE = f"{CSE_BASE}"
lightbulb2_AE = f"{CSE_BASE}"

smart_switch_Container = f"{CSE_BASE}/smartswitch"
lightbulb1_Container = f"{CSE_BASE}/lightbulb1"
lightbulb2_Container = f"{CSE_BASE}/lightbulb2"

smart_switch_Instance = f"{CSE_BASE}/smartswitch/state"
lightbulb1_Instance = f"{CSE_BASE}/lightbulb1/state"
lightbulb2_Instance = f"{CSE_BASE}/lightbulb2/state"

smart_switch_state_url = f"{CSE_BASE}/smartswitch/state/smartswitch-instance_" + str(smartswitch_instance_value)
lightbulb1_state_url = f"{CSE_BASE}/lightbulb1/state/lightbulb1-instance_" + str(lightbulb1_instance_value)
lightbulb2_state_url = f"{CSE_BASE}/lightbulb2/state/lightbulb2-instance_" + str(lightbulb2_instance_value)

request_body_AE_smartswitch = {
    "m2m:ae": {
        "api": "N.smartswitch",
        "poa": ["http://192.168.1.2:8080/smartswitch"],
        "rn": "smartswitch",
        "srv": ["3"],
        "rr": False
    }
}




#  Main loop
if __name__ == '__main__':

    localIP = discoverIP.get_local_ip()
    print(localIP)
    ips = discoverIP.discoverIPS()
    for ip in ips:
        print(ip)
    
    #get the smart switch and lightbulbs AE if already existed
    if get_CSE_IN(smart_switch_Container) is not None:
        delete_application_entity(smart_switch_Container)
        request_body_AE_smartswitch["m2m:ae"]["poa"] = "http://" + localIP + "/smartswitch"
        create_application_entity(smart_switch_AE, request_body_AE_smartswitch)
    if get_CSE_IN(lightbulb1_Container) is not None:
       delete_application_entity(lightbulb1_Container)
    if get_CSE_IN(lightbulb2_Container) is not None:
        delete_application_entity(lightbulb2_Container)



    
    #create application entity for smart switch and lightbulbs
    create_application_entity(smart_switch_AE, request_body_AE_smartswitch)
    create_application_entity(lightbulb1_AE, request_body_AE_lightbulb1)
    create_application_entity(lightbulb2_AE, request_body_AE_lightbulb2)

    #create a container for each AE
    create_container(smart_switch_Container, request_body_container)
    create_container(lightbulb1_Container, request_body_container)
    create_container(lightbulb2_Container, request_body_container)

    #create a container instance for each AE container
    create_container_instance(smart_switch_Instance, request_body_instance_smartswitch)
    create_container_instance(lightbulb1_Instance, request_body_instance_lightbulb1)
    create_container_instance(lightbulb2_Instance, request_body_instance_lightbulb2)


 #-----------------------------------TEST X: WITH BUTTONS--------------------------------------------------#


    while True:
        print("Press '1' for ON/OFF, '2' for changing the controlled lightbulb, 'q' to quit")
        button_press = input()
        
        get_container_length = int(repr(get_CSE_IN(smart_switch_Instance)['m2m:cnt']['cni']))
        latest_instance = get_latest_instance(get_container_length, "smartswitch")
        request_body_instance_smartswitch["m2m:cin"]["con"]
        if button_press == '1':
            current_state = json.loads(latest_instance['m2m:cin']['con'])

            if current_state['controlledLight'] == 'lightbulb1':
                get_container_length = int(repr(get_CSE_IN(lightbulb1_Instance)['m2m:cnt']['cni']))
                latest_instance = get_latest_instance(get_container_length, "lightbulb1")
                lightbulb_instance_name_value = get_container_length
                request_body_instance_lightbulb1["m2m:cin"]["con"] = json.dumps(change_value_lightbulb(latest_instance))
                request_body_instance_lightbulb1["m2m:cin"]["rn"] = "lightbulb1-instance_" + str(lightbulb_instance_name_value)
                create_container_instance(lightbulb1_Instance, request_body_instance_lightbulb1)
            elif current_state['controlledLight'] == 'lightbulb2':
                get_container_length = int(repr(get_CSE_IN(lightbulb2_Instance)['m2m:cnt']['cni']))
                latest_instance = get_latest_instance(get_container_length, "lightbulb2")
                lightbulb_instance_name_value = get_container_length
                request_body_instance_lightbulb2["m2m:cin"]["con"] = json.dumps(change_value_lightbulb(latest_instance))
                request_body_instance_lightbulb2["m2m:cin"]["rn"] = "lightbulb2-instance_" + str(lightbulb_instance_name_value)
                create_container_instance(lightbulb2_Instance, request_body_instance_lightbulb2)
            else:
                print("Error changing lightbulb")
        elif button_press == '2':
            get_container_length = int(repr(get_CSE_IN(smart_switch_Instance)['m2m:cnt']['cni']))
            latest_instance = get_latest_instance(get_container_length, "smartswitch")
            smartswitch_instance_name_value = get_container_length
            request_body_instance_smartswitch["m2m:cin"]["con"] = json.dumps(change_value_smartswitch(latest_instance))
            request_body_instance_smartswitch["m2m:cin"]["rn"] = "smartswitch-instance_" + str(smartswitch_instance_name_value)
            create_container_instance(smart_switch_Instance, request_body_instance_smartswitch)
        elif button_press == 'q':
            break
        else:
            print("Invalid input. Try again.")
