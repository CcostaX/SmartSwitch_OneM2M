# notification_handler.py
from flask import Flask, request

app = Flask(__name__)

@app.route('/notification_handler', methods=['POST'])
def handle_notification():
    print("Received notification:")
    print(request.get_json())
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
