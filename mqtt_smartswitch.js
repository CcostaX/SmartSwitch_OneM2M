const mqtt = require('mqtt');

//const mqttBrokerUrl = 'mqtt://localhost:1883';
const mqttBrokerUrl = 'http://192.168.1.91:1883';
const mqttOptions = {
  clientId: 'mqtt-client-id',
};

const mqttClient = mqtt.connect(mqttBrokerUrl, mqttOptions);

let rooms = {};

mqttClient.on('connect', () => {
  console.log('Connected to MQTT broker');
});

mqttClient.on('message', (topic, message) => {
  const { room, data } = JSON.parse(message);

  if (!rooms[room]) {
    rooms[room] = { clients: new Set() };
    console.log(`Created new room: ${room}`);
  }

  rooms[room].clients.forEach(client => {
    client.send(data);
  });
});

mqttClient.subscribe('room/+/message');

mqttClient.on('error', (error) => {
  console.log(`MQTT Error: ${error}`);
});

const WebSocket = require('ws');

const server = new WebSocket.Server({ port: 8080 });

server.on('connection', (ws) => {
  ws.on('message', (message) => {
    const { room, data } = JSON.parse(message);

    if (!rooms[room]) {
      rooms[room] = { clients: new Set() };
      console.log(`Created new room: ${room}`);
    }

    if (!rooms[room].clients.has(ws)) {
      console.log(`Client joined room ${room}`);
      const welcomeMessage = `${data} has joined room ${room}!`;
      const publishTopic = `room/${room}/message`;
      mqttClient.publish(publishTopic, welcomeMessage);
    }

    rooms[room].clients.add(ws);
    console.log(`Received message from Python client in room ${room}: ${data}`);

    rooms[room].clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(data);
      } else {
        rooms[room].clients.delete(client);
      }
    });
  });

  ws.on('close', () => {
    for (let room in rooms) {
      rooms[room].clients.delete(ws);
    }
  });
});
