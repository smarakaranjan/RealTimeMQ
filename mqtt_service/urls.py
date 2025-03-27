from django.urls import path, include
from rest_framework.routers import DefaultRouter
from mqtt_service.views import TopicViewSet, SubscriptionViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'topics', TopicViewSet)
router.register(r'subscriptions', SubscriptionViewSet)
router.register(r'message', MessageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]