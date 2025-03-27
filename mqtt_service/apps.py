# Django Imports
from django.apps import AppConfig
from django.conf import settings

# App Imports
from mqtt_service.mqtt_client import MqttService

# Default Package Imports
import asyncio
import logging
import threading

# Initialize Logger
logger = logging.getLogger(__name__)

class MqttServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mqtt_service'

    def ready(self):
        """
        Starts the MQTT service when the Django app is loaded.
        - Runs inside Django (development mode).
        - In production, MQTT should run as a separate service.
        """

        if not getattr(settings, "MQTT_AUTO_START", settings.DEBUG):
            logger.info("MQTT Service will not start inside Django (Production mode).")
            return  # Don't start inside Django in production.

        if not hasattr(self, "_mqtt_started"):  # Prevent multiple starts in dev
            self._mqtt_started = True
            thread = threading.Thread(target=self.run_mqtt_service, daemon=True)
            thread.start()

    def run_mqtt_service(self):
        """Runs the MQTT service in a dedicated event loop thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.start_mqtt_service())

    async def start_mqtt_service(self):
        """Starts the MQTT service asynchronously."""
        broker = getattr(settings, "MQTT_BROKER", "mqtt.example.com")
        port = getattr(settings, "MQTT_PORT", 1883)
        username = getattr(settings, "MQTT_USER", "your_user")
        password = getattr(settings, "MQTT_PASS", "your_pass")

        mqtt_service = MqttService(broker=broker, port=port)

        try:
            await mqtt_service.connect(username=username, password=password)
            logger.info("MQTT Service started successfully.")
        except Exception as e:
            logger.error(f"Failed to start MQTT service: {e}")
