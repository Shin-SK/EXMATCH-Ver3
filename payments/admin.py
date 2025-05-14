# payments/admin.py

from django.contrib import admin
from .models import Payment, PlanOption

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'option', 'purchased_at')
    list_filter = ('plan', 'option', 'purchased_at')

@admin.register(PlanOption)
class PlanOptionAdmin(admin.ModelAdmin):
    list_display = ('category', 'code', 'name', 'base_days', 'extra_days')
    list_filter = ('category', 'code')
