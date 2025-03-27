# Django Import's
from django.db import models
from django.conf import settings

# Default Package Import's
import uuid

class Topic(models.Model):
    """
    🔥 Represents an MQTT topic that users can publish messages to and subscribe to.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=255, unique=True) 

    is_group = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  

    def __str__(self):
        return self.name

class Subscription(models.Model):
    """
    🔥 Represents a user's subscription to an MQTT topic.
    🔥 Ensures a user can subscribe to a topic only once.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="subscriptions"
    )   
    topic = models.ForeignKey(
        Topic, on_delete=models.SET_NULL, related_name="subscriptions"
    )   

    subscribed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        unique_together = ('user', 'topic')

    def __str__(self):
        return f"{self.user.username} -> {self.topic.name}"
    
class Message(models.Model):
    """🔥 Represents messages published to MQTT topics."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    content = models.TextField(blank=True, null=True)

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="sent_message", on_delete=models.SET_NULL  
    )  
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="received_message", on_delete=models.SET_NULL  
    ) 
    topic = models.ForeignKey(
        Topic,  blank=False, null=False, related_name="message", on_delete=models.SET_NULL
    )  

    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)    

    def __str__(self):
        return f"{self.topic.name}: {self.sender.first_name} → {self.receiver.first_name}"

     
