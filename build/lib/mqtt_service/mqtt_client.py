# Django Import's
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

# App Import's
from mqtt_service.models import Topic, Message

# Default Package Import's
import logging
import asyncio
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

            # Ensure we are inside an event loop
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.subscribe_all())  # Non-blocking subscription
            except RuntimeError:
                asyncio.run(self.subscribe_all())  # Manually start event loop if none exists

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
            # Fetch active topic IDs asynchronously
            subscriptions = await asyncio.to_thread(Topic.objects.filter(is_active=True).values_list, "id", flat=True)

            if subscriptions:
                topics = [(str(topic_id), 0) for topic_id in subscriptions]  # QoS = 0

                # Subscribe to all topics in a batch
                result, _ = await asyncio.to_thread(self.client.subscribe, topics)

                # Log success or failure
                if result == 0:
                    logging.info(f"Successfully subscribed to {len(subscriptions)} topics.")
                else:
                    logging.warning(f"Batch subscription failed with return code: {result}")

            else:
                logging.info("No active topics found to subscribe.")

        except Exception as e:
            logging.error(f"Error in subscribe_all: {e}")
         
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
            user: The recipient user object. If None, the message is broadcasted to all users.
            message: The message content to send.
            qos: Quality of Service level (default: 0).
                - 0: At most once (fire and forget)
                - 1: At least once (acknowledged delivery)
                - 2: Exactly once (ensured delivery)
        """
        try:
            if user:
                # Send notification to a single user
                topic = f"notification/{user.id}"
                result = await asyncio.to_thread(self.client.publish, topic, message, qos)

                # Log success or failure
                if result.rc == 0:
                    logging.info(f"Notification sent to {user.id} on topic {topic}")
                else:
                    logging.warning(
                        f"Failed to send notification to {user.id}, MQTT return code: {result.rc}"
                    )

            else:
                # Broadcast to all active users
                user_model = get_user_model()
                users = await asyncio.to_thread(user_model.objects.filter, is_active=True)

                # Publish the message to all users concurrently
                tasks = [asyncio.to_thread(self.client.publish, f"notification/{u.id}", message, qos) for u in users]
                results = await asyncio.gather(*tasks)

                # Log results for each user
                for user, result in zip(users, results):
                    if result.rc == 0:
                        logging.info(
                            f"Broadcast notification sent to {user.id} on topic notification/{user.id}"
                        )
                    else:
                        logging.warning(
                            f"Failed to send broadcast notification to {u.id}, MQTT return code: {result.rc}"
                        )
        except Exception as e:
            logging.error(f"Error sending notification: {e}")  

    

    async def on_message(self, client, user, data):
        """
        Handles incoming MQTT messages.

        - Extracts the topic and message payload from the MQTT message.
        - Ensures the topic exists in the database (creates it if necessary).
        - Fetches the sender and receiver user objects asynchronously.
        - Stores the message in the database using Django ORM.

        Args:
            client: The MQTT client instance.
            user: User data associated with the MQTT client (not used here).
            data: The received MQTT message containing topic and payload.
        """
    
        # Extract topic ID and message payload from the received MQTT message
        topic = data.topic
        payload = data.payload.decode()  # Convert the binary payload to a string

        # Ensure the topic exists in the database, create it if it doesn’t exist
        topic, _ = await asyncio.to_thread(Topic.objects.get_or_create, id=topic)

        # Fetch the sender and receiver user objects asynchronously from the database
        sender = await self.get_user(payload.sender_id)
        receiver = await self.get_user(payload.receiver_id)

        # Store the received message in the database asynchronously
        await asyncio.to_thread(
            Message.objects.create, topic=topic, message=payload.message, sender=sender, receiver=receiver
        )


 
