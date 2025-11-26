import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.apps import apps

# Booking = apps.get_model('job_app', 'Booking')
# ServiceRequest = apps.get_model('job_app', 'ServiceRequest')
# Profile = apps.get_model('job_app', 'Profile')

# ==============
# HELPERS
# ==============
@sync_to_async
def get_service_request(request_id):
    ServiceRequest = apps.get_model('job_app', 'ServiceRequest')
    return ServiceRequest.objects.get(id=request_id)

@sync_to_async
def update_service_request_status(request_id, status):
    ServiceRequest = apps.get_model('job_app', 'ServiceRequest')
    request = ServiceRequest.objects.get(id=request_id)
    request.status = status
    request.save()
    return request


@sync_to_async
def create_provider_booking(service_request, worker_profile, status):
    ProviderBooking = apps.get_model('job_app', 'ProviderBooking')
    booking = ProviderBooking.objects.create(
        service=service_request.service,
        seeker=service_request.seeker,
        provider=worker_profile,
        status=status,
    )
    return booking


@sync_to_async
def create_seeker_booking(service_request, status):
    SeekerBooking = apps.get_model('job_app', 'SeekerBooking')
    booking = SeekerBooking.objects.create(
        service=service_request.service,
        seeker=service_request.seeker,
        status=status,
    )
    return booking


class ProviderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.provider_id = self.scope["url_route"]["kwargs"]["provider_id"]
        self.group_name = f"provider_{self.provider_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"[WS CONNECTED] Provider {self.provider_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f"[WS DISCONNECTED] Provider {self.provider_id}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        request_id = data.get("request_id")

        if action in ["accept", "decline"] and request_id:
            status = "confirmed" if action == "accept" else "cancelled"

            # Update ServiceRequest
            service_request = await update_service_request_status(request_id, status)

            # Get provider Profile
            Profile = apps.get_model('job_app', 'Profile')
            worker_profile = await sync_to_async(Profile.objects.get)(id=self.provider_id)

            provider_booking = None
            seeker_booking = None

            if action == "accept":
                provider_booking = await create_provider_booking(service_request, worker_profile, status)
                seeker_booking = await create_seeker_booking(service_request, status)

            # Send confirmation back
            await self.send(text_data=json.dumps({
                "type": "booking_update",
                "request_id": request_id,
                "status": status,
                "provider_booking_id": provider_booking.id if provider_booking else None,
                "seeker_booking_id": seeker_booking.id if seeker_booking else None,
            }))
            print(f"[BOOKING UPDATED] Provider {self.provider_id} → {status}")

    async def incoming_request(self, event):
        await self.send(text_data=json.dumps({
            "type": "send_request",
            "request_id": event["request_id"],
            "service": event["service"],
            "seeker": event["seeker"],
            "phone": event["phone"],
            "location": event.get("location", "")
        }))
        print(f"[WS SENT TO PROVIDER {self.provider_id}] → {event}")

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.provider_id = self.scope["url_route"]["kwargs"]["provider_id"]
        self.group_name = f"provider_{self.provider_id}"

        await self.channel_layer.group_add(
            self.group_name, self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name, self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data["action"] in ["accept", "decline"]:
            request_id = data["request_id"]

            try:
                service_request = await sync_to_async(ServiceRequest.objects.get)(id=request_id)
            except ServiceRequest.DoesNotExist:
                return

            provider_profile = await sync_to_async(Profile.objects.get)(id=self.provider_id)

            if data["action"] == "accept":
                await create_or_update_booking(service_request, provider_profile, "Accepted")

            elif data["action"] == "decline":
                await create_or_update_booking(service_request, provider_profile, "Declined")



# ============================================
#  MAIN PROVIDER CONSUMER
# ============================================
# class ProviderConsumer(AsyncWebsocketConsumer):
    """
    Handles WebSocket connections for providers.
    Providers join a group based on their Profile ID, and receive incoming service requests.
    """

    async def connect(self):
        self.provider_id = self.scope["url_route"]["kwargs"]["provider_id"]
        self.group_name = f"provider_{self.provider_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        print(f"[WS CONNECTED] Provider {self.provider_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f"[WS DISCONNECTED] Provider {self.provider_id}")

    async def receive(self, text_data):
        """
        Handle messages sent by provider (Accept/Decline).
        """
        data = json.loads(text_data)
        print(f"[WS RECEIVE FROM PROVIDER {self.provider_id}] → {data}")

        action = data.get("action")
        request_id = data.get("request_id")

        if action in ["accept", "decline"] and request_id:
            status = "confirmed" if action == "accept" else "cancelled"

            # Update ServiceRequest
            service_request = await update_service_request_status(request_id, status)

            # Get provider Profile
            Profile = apps.get_model('job_app', 'Profile')
            worker_profile = await sync_to_async(Profile.objects.get)(id=self.provider_id)

            # Create/Update Booking
            booking = await create_or_update_booking(service_request, worker_profile, status)

            # Send confirmation back to provider
            await self.send(text_data=json.dumps({
                "type": "booking_update",
                "request_id": request_id,
                "status": status,
                "booking_id": booking.id
            }))

            print(f"[BOOKING UPDATED] Provider {self.provider_id} → {status}")

    async def incoming_request(self, event):
        """
        Handler called when send_requests() triggers group_send.
        """
        await self.send(text_data=json.dumps({
            "type": "send_request",
            "request_id": event["request_id"],
            "service": event["service"],
            "seeker": event["seeker"],
            "phone": event["phone"],
            "location": event.get("location", "")
        }))

        print(f"[WS SENT TO PROVIDER {self.provider_id}] → {event}")
