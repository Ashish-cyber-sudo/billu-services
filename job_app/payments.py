import stripe
import razorpay
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY
razor_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_stripe_payment_intent(amount_in_rupees, currency='inr'):
    # amount_in_rupees -> convert to paise/cents depending on currency
    amount = int(amount_in_rupees * 100)
    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency=currency,
        payment_method_types=['card'],
    )
    return intent


def create_razorpay_order(amount_in_rupees, currency='INR'):
    amount = int(amount_in_rupees * 100)  # rupees -> paise
    order = razor_client.order.create(dict(amount=amount, currency=currency, payment_capture='1'))
    return order
