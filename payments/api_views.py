# payments/api_views.py
import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# 既存の価格テーブルを使い回し
from .views import PLAN_PRICE, OPTION_PRICE, OPTION_PRICE_HALF

class PaymentsCheckoutAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        plan = (request.data.get("plan") or "").strip()
        options = request.data.get("options") or []
        if isinstance(options, str):
            options = [options]
        if not plan or plan not in PLAN_PRICE:
            return Response({"detail": "invalid plan"}, status=status.HTTP_400_BAD_REQUEST)

        line_items = [{"price": PLAN_PRICE[plan], "quantity": 1}]

        # 割引中はハーフのテーブルを使用
        opt_table = OPTION_PRICE_HALF if getattr(settings, "OPTION_DISCOUNT_ACTIVE", False) else OPTION_PRICE
        for opt in options:
            pid = opt_table.get(opt)
            if pid:
                line_items.append({"price": pid, "quantity": 1})

        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            customer_email=request.user.email or None,
            client_reference_id=str(request.user.id),
            line_items=line_items,
            success_url=f"{settings.FRONTEND_BASE_URL}/plan/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_BASE_URL}/plan/checkout",
            metadata={"plan": plan, "option": (options[0] if options else "")},
        )
        return Response({"url": session.url}, status=status.HTTP_201_CREATED)
