from django.urls import path, include
from rest_framework.routers import DefaultRouter
from mqtt_service.views import TopicViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register(r'topics', TopicViewSet)
router.register(r'subscriptions', SubscriptionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]