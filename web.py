import os

from flask import Flask, render_template
from flask_socketio import SocketIO
from dotenv import load_dotenv

from  inventory_tool import read_inventory

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
socketio = SocketIO(app)

@app.route("/")
def index():
    inventory = read_inventory("inventory.csv")
    device_names = [device["Name"] for device in inventory]
    return render_template("index.html", devices=device_names)

if __name__ == "__main__":
    socketio.run(app, debug=True)