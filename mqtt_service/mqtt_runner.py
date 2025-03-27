import asyncio
import logging
import os
from django.conf import settings
from mqtt_service.mqtt_client import MqttService  # Import your MQTT service

logger = logging.getLogger(__name__)

async def main():
    broker = settings.MQTT_BROKER
    port = settings.MQTT_PORT
    username = settings.MQTT_USER
    password = settings.MQTT_PASS

    mqtt_service = MqttService(broker=broker, port=port)

    try:
        await mqtt_service.connect(username=username, password=password)
        logger.info("MQTT Service started successfully.")
    except Exception as e:
        logger.error(f"Failed to start MQTT service: {e}")

if __name__ == "__main__":
    asyncio.run(main())
