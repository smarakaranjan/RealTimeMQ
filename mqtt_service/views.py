# DRF Import's
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

# Django Import's
from django.shortcuts import get_object_or_404

# App Import's
from mqtt_service.models import (Topic, Message, Subscription)
from mqtt_service.serializers import (TopicSerializer, MessageSerializer, SubscriptionSerializer)

# Default Package Import's
import logging

# Initialize Logger
logger = logging.getLogger(__name__)

class TopicViewSet(viewsets.ModelViewSet):
    """ CRUD operations for MQTT Topics """
    
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

    def create(self, request, *args, **kwargs):
        """ 🔥 Create a new topic """
        try:
            serializer = self.get_serializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response(
                {"error": "Error creating topic."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def retrieve(self, request, *args, **kwargs):
        """ 🔥 Retrieve a specific topic """
        try:
            instance = self.get_object()

            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"error": "Error retrieving topic."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def update(self, request, *args, **kwargs):
        """ 🔥 Update an existing topic """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response(
                {"error": "Error updating topic."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request, *args, **kwargs):
        """ 🔥 Delete a topic """
        try:

            instance = self.get_object()
            instance.delete()
            return Response({"message": "Topic deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            return Response(
                {"error": "Error deleting topic."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    🔥 Handles subscription CRUD operations.
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

    def create(self, request, *args, **kwargs):
        """
        🔥 Create a mqtt subscription.
        🔥 Automatically subscribe the user to the MQTT topic.
        """
        try:
            serializer = self.get_serializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'Subscribed successfully'}, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response(
                {'status': "Error subscribing to the topic."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, *args, **kwargs):
        """
        🔥 Retrieve a single subscription by ID.
        """
        try:

            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'status': "Error retrieving subscription."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """
        🔥 Unsubscribe the user from the topic.
        🔥 Delete the subscription to the topic.
        """
        try:
            subscription = self.get_object()
            subscription.delete()
            return Response({'status': 'Unsubscribed successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'status': "Error deleting subscription."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    @action(detail=False, methods=['get'])
    def user_subscriptions(self, request):
        """
        🔥 Retrieve all topics subscribed by the authenticated user.
        """
        try:
            subscriptions = Subscription.objects.filter(user=request.user)
            serializer = self.get_serializer(subscriptions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'status': "Error retrieving user subscriptions."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    @action(detail=True, methods=['get'])
    def topic_subscribers(self, request, pk=None):
        """
        🔥 Retrieve all users subscribed to a specific topic.
        """
        try:
            topic = get_object_or_404(Topic, pk=pk)
            subscriptions = Subscription.objects.filter(topic=topic)
            serializer = self.get_serializer(subscriptions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'status': "Error retrieving users subscribed to the topic."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class MessageViewSet(viewsets.ModelViewSet):
    """ 🔥 CRUD operations for messages with MQTT publishing """
    
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def create(self, request, *args, **kwargs):
        """ 🔥 Create and publish a new message """
        try:
             
            serializer = self.get_serializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")

            return Response({"error": "Error creating message."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        """ 🔥 Retrieve a specific message """
        try:

            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": "Error retrieving message."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        """ 🔥 Update an existing message """
        try:

            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": "Error updating message."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR,)

    def destroy(self, request, *args, **kwargs):
        """ 🔥 Delete a message """
        try:
            instance = self.get_object()
            instance.delete()

            return Response({"message": "Message deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            return Response({"error": "Error deleting message."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
