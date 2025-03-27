# Django Import's
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

# App Import's
def get_topic_model():
    return apps.get_model('mqtt_service', 'Topic')

def get_message_model():
    return apps.get_model('mqtt_service', 'Message')


# Default Package Import's
import logging
import asyncio
from asgiref.sync import async_to_sync, sync_to_async
import paho.mqtt.client as mqtt

# Initialize Logger
logger = logging.getLogger(__name__)

class MqttService:
    
    def __init__(self, broker: str, port: int = 1883):
        """
        Initializes the MQTT service.

        Args:
            broker (str): The MQTT broker address.
            port (int, optional): The MQTT broker port (default: 1883).
        """
        self.broker = broker
        self.port = port
        self.client = mqtt.Client()
        
        # Attach event handlers
        self.client.on_connect = self.on_connect  
        self.client.on_message = self.on_message  

    async def get_user(self, id: int):
        """
        Fetches a user by ID asynchronously.

        Args:
            id (int): The ID of the user to fetch.

        Returns:
            User object if found, None otherwise.
        """
        user_model = get_user_model()
        try:
            return await asyncio.to_thread(user_model.objects.get, id=id)
        except ObjectDoesNotExist:
            logger.warning(f"User with ID {id} not found.")
            return None 

    async def connect(self, username: str, password: str):
        """
        Asynchronously connects to the MQTT broker.

        Args:
            username (str): The MQTT username.
            password (str): The MQTT password.

        Returns:
            None
        """
        self.client.username_pw_set(username, password)
        
        # Run connect_async in a separate thread to avoid blocking
        await asyncio.to_thread(self.client.connect_async, self.broker, self.port, 60)
        
        self.client.loop_start()  # Start the loop in a non-blocking way

    def on_connect(self, client, userdata, flags, rc):
        """
        Callback function triggered when the MQTT client connects to the broker.

        Args:
            client: The MQTT client instance.
            userdata: User-defined data (not used in this case).
            flags: Response flags sent by the broker.
            rc (int): Connection result code. 0 means success.

        Returns:
            None
        """
        if rc == 0:
            logger.info("Connected to MQTT broker successfully.")
            async_to_sync(self.subscribe_all)()
        else:
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")
           
    async def subscribe(self, topic: str):
        """
        Subscribes to a given MQTT topic.

        Args:
            topic (str): The MQTT topic to subscribe to.
        
        Returns:
            None
        """
        await asyncio.to_thread(self.client.subscribe, topic)
         
    async def subscribe_all(self):
        """
        Subscribes to all active topics in the database in batch mode.
        """
        try:
            Topic = get_topic_model()

            # ✅ Run ORM query properly in async context
            subscriptions = await sync_to_async(
                lambda: list(Topic.objects.filter(is_active=True).values_list("id", flat=True))
            )()

            if subscriptions:
                topics = [(str(topic_id), 0) for topic_id in subscriptions]  # QoS = 0

                # ✅ Ensure the subscribe call runs in a non-async context
                result, _ = await sync_to_async(self.client.subscribe)(topics)

                if result == 0:
                    logger.info(f"Successfully subscribed to {len(subscriptions)} topics.")
                else:
                    logger.warning(f"Batch subscription failed with return code: {result}")

            else:
                logger.info("No active topics found to subscribe.")

        except Exception as e:
            logger.error(f"Error in subscribe_all: {e}")
         
    async def publish(self, topic, message, qos=0):
        """
        Publishes a message to the given MQTT topic.

        Args:
            topic (str): The MQTT topic to publish to.
            message (str): The message content to send.
            qos (int): Quality of Service level (default: 0).
                    - 0: At most once (fire and forget)
                    - 1: At least once (acknowledged delivery)
                    - 2: Exactly once (ensured delivery)
        """
        try:
            # Publish the message asynchronously in a separate thread
            result = await asyncio.to_thread(self.client.publish, topic, message, qos)

            # Log success or failure
            if result.rc == 0:
                logging.info(f"Message published to {topic}: {message}")
            else:
                logging.warning(f"Failed to publish message to {topic}, MQTT return code: {result.rc}")

        except Exception as e:
            logging.error(f"Error publishing message to {topic}: {e}")

    async def notification(self, message, user=None, qos=0):
        """
        Publishes a notification message to a specific user or broadcasts to all users if no user is provided.

        Args:
            message: The message content to send.
            user: The recipient user object. If None, the message is broadcasted to all users.
            qos: Quality of Service level (default: 0).
        """
        try:
            if user:
                # Send notification to a single user
                topic = f"notification/{user.id}"
                result = await asyncio.to_thread(self.client.publish, topic, message, qos)

                if result.rc == 0:
                    logging.info(f"✅ Notification sent to {user.id} on topic {topic}")
                else:
                    logging.warning(f"⚠️ Failed to send notification to {user.id}, MQTT return code: {result.rc}")

            else:
                # Broadcast to all active users
                user_model = get_user_model()
                users = await asyncio.to_thread(lambda: list(user_model.objects.filter(is_active=True)))

                # Publish the message to all users concurrently
                tasks = [asyncio.to_thread(self.client.publish, f"notification/{u.id}", message, qos) for u in users]
                results = await asyncio.gather(*tasks)

                for user, result in zip(users, results):
                    if result.rc == 0:
                        logging.info(f"✅ Broadcast notification sent to {user.id} on topic notification/{user.id}")
                    else:
                        logging.warning(f"⚠️ Failed to send broadcast notification to {user.id}, MQTT return code: {result.rc}")

        except Exception as e:
            logging.error(f"❌ Error sending notification: {e}")

    
    async def handle_incoming_message(self, data):
        """
        Asynchronously processes the received MQTT message.

        - Extracts topic and message payload.
        - Ensures the topic exists in the database.
        - Fetches sender and receiver from the database asynchronously.
        - Stores the message asynchronously.

        Args:
            data: The received MQTT message containing topic and payload.
        """
        
        Topic = get_topic_model()
        Message = get_message_model()

        topic_id = data.topic
        payload = data.payload.decode()  # Convert binary payload to string
         
        try:
            # Ensure the topic exists in the database, create it if necessary
            topic, _ = await asyncio.to_thread(Topic.objects.get_or_create, id=topic_id)

            # Parse the payload (assuming it's JSON)
            import json
            payload_data = json.loads(payload)

            # Fetch the sender and receiver asynchronously
            sender = await self.get_user(payload_data.get("sender"))
            receiver = await self.get_user(payload_data.get("receiver"))
            message = payload_data.get("message")
             
            # Store the message asynchronously in the database
            await asyncio.to_thread(
                Message.objects.create, topic=topic, content=message, sender=sender, receiver=receiver
            )

            # 🔹 Send notification to receiver
            if receiver:
                await self.notification(f"New message from {sender.first_name}: {message}", receiver)
            else:
                await self.notification(f"New message from {sender.first_name}: {message}")

            logger.info(f"✅ Message stored successfully: {payload_data.get('message')} (Topic: {topic_id})")

        except json.JSONDecodeError:
            logger.warning(f"❌ Failed to decode message payload: {payload}")

        except Exception as e:
            logger.warning(f"❌ Error processing MQTT message: {e}")

    def on_message(self, client, user, data):
        """
        Handles incoming MQTT messages synchronously (required by Paho MQTT).

        - Calls the async function `handle_incoming_message` in the event loop.
        - Ensures thread-safety when running async code inside a sync function.

        Args:
            client: The MQTT client instance.
            user: User data associated with the MQTT client (not used here).
            data: The received MQTT message containing topic and payload.
        """
        try:
            # Try to get the running event loop
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # If no running loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run the async function in the event loop safely
        loop.run_until_complete(self.handle_incoming_message(data))

 


 
