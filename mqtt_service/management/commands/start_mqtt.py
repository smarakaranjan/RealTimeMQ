# Django Imports
from django.core.management.base import BaseCommand
from django.conf import settings

# App Imports
from mqtt_service.mqtt_client import MqttService

# Package Imports
import asyncio

class Command(BaseCommand):
    help = "Starts the MQTT service"

    def handle(self, *args, **kwargs):
        asyncio.run(self.start_mqtt())

    async def start_mqtt(self):
        mqtt_service = MqttService(broker = settings.MQTT_BROKER, port = settings.MQTT_PORT)
        await mqtt_service.connect(username = settings.MQTT_USER, password = settings.MQTT_PASSWORD)
