# payments/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
	path('paymentform/', views.create_checkout_session, name='checkout_form'),
	path('success/', views.payment_success, name='payment_success'),

]
