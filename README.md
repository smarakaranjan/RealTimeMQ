Django MQTT Chat & Notification Plugin 🌌💬

A pluggable Django app for real-time chat and notifications using MQTT (Eclipse Mosquitto) as the broker. This package allows scalable, asynchronous communication without relying on WebSockets or Django Channels.

🚀 Features

✅ Full MQTT Support (via Paho-MQTT)
✅ Asynchronous & Scalable (Fully async-based)
✅ Easy Integration (Plug & Play with any Django project)
✅ JWT Authentication for MQTT Clients
✅ Message Storage in the database
✅ Topic-based Subscription & Messaging

🛠 Installation

1⃣ Install via GitHub

pip install https://github.com/smarakaranjan/RealTimeMQ.git

(Replace your-username with your actual GitHub username)

2⃣ Add to INSTALLED_APPS in settings.py

INSTALLED_APPS = [
    # Other apps...
    "mqtt_service",
]

3⃣ Run Migrations

python manage.py migrate mqtt_service

4⃣ Configure Environment Variables

Create a .env file in your Django project and add the following (or modify .env.example provided):

MQTT_BROKER=mqtt.example.com
MQTT_PORT=1883
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password
MQTT_TLS_ENABLED=True  # Set to False if not using TLS

5⃣ Run the Django Server

Start your Django application, and the MQTT service will start automatically. 🎉

python manage.py runserver

🔧 Usage

✅ Publishing Messages

You can publish messages using the MqttService class:

from mqtt_service.mqtt_client import MqttService

mqtt_service = MqttService()
await mqtt_service.publish(topic="chat/general", message="Hello, MQTT!")

✅ Subscribing to Topics

All active topics are automatically subscribed when the Django app starts.

To manually subscribe to a topic:

await mqtt_service.subscribe("chat/general")

✅ Sending Notifications

To send a notification to a specific user or broadcast:

await mqtt_service.notification(message="New update available!", user=user_instance)

⚡ Running in Production

For production, ensure you have a proper .env setup with an external Mosquitto MQTT broker and use a process manager like Supervisor or Systemd to keep the service running.

 

