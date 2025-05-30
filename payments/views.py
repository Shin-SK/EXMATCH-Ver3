# payments/views.py

import stripe
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required  # ← これを追加
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from .models import Payment
from django.utils import timezone
from dateutil.relativedelta import relativedelta


PLAN_INFO = {
    "standard_1m":  {"base": 1,  "bonus": 0},
    "standard_3m":  {"base": 3,  "bonus": 1},
    "standard_6m":  {"base": 6,  "bonus": 2},
    "standard_12m": {"base": 12, "bonus": 3},
}


PLAN_PRICE = {
    "standard_1m":  "price_1RULAqF2VxVQdhvzNmvjRz2r",
    "standard_3m":  "price_1RULBvF2VxVQdhvzrMiGvso0",
    "standard_6m":  "price_1RULCHF2VxVQdhvzsTm6FEOh",
    "standard_12m": "price_1RULCcF2VxVQdhvzINZZl5J2",
}


OPTION_PRICE = {
    "plus_1m":  "price_1RULF5F2VxVQdhvzHBZWRc3k",
    "plus_3m":  "price_1RULauF2VxVQdhvzQzMvi6Bk",
    "plus_6m":  "price_1RULbEF2VxVQdhvzCMzwEIR4",
    "plus_12m": "price_1RULcOF2VxVQdhvz70SxEK2y",
}

OPTION_PRICE_HALF = {
    "plus_1m":  "price_1RULgPF2VxVQdhvzGVbPEQ1H",
    "plus_3m":  "price_1RULgxF2VxVQdhvzvfswn8sQ",
    "plus_6m":  "price_1RULhKF2VxVQdhvz3qapsGo4",
    "plus_12m": "price_1RULhqF2VxVQdhvzimcNHgte",
}

@csrf_exempt
def stripe_webhook(request):
    print("Webhook hit!", timezone.now())
    try:
        event = stripe.Webhook.construct_event(
            request.body,
            request.META.get("HTTP_STRIPE_SIGNATURE"),
            settings.STRIPE_ENDPOINT_SECRET,
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        s = event["data"]["object"]

        # ▼▼ デバッグ用 --------------------------
        plan  = s["metadata"].get("plan")
        print("Webhook OK:", plan, timezone.now())   # ★ ここに 1 行
        # ▲▲ ------------------------------------
    
        user_id = s.get("client_reference_id")
        if not user_id:
            return HttpResponse(status=200)

        User  = get_user_model()
        user  = User.objects.get(id=user_id)

        plan   = s["metadata"].get("plan") or "standard_1m"
        option = s["metadata"].get("option") or None

        # ---------- 決済レコード ----------
        Payment.objects.create(user=user, plan=plan, option=option)

        # ---------- 期間計算 ----------
        info          = PLAN_INFO.get(plan, {"base": 1, "bonus": 0})
        bonus_months  = info["bonus"] if settings.CAMPAIGN_BONUS_ACTIVE else 0
        total_months  = info["base"] + bonus_months

        profile = user.userprofile
        profile.plan         = "standard"
        profile.plan_expiry  = timezone.now() + relativedelta(months=total_months)
        profile.save()

    return HttpResponse(status=200)



@login_required
@csrf_exempt
def create_checkout_session(request):

    stripe.api_key = settings.STRIPE_SECRET_KEY

    if request.method != "POST":
        return render(request, "payments/checkout_form.html")

    plan   = request.POST.get("plan")            # 例: standard_3m
    option = request.POST.get("option") or None  # 例: plus_3m

    # ──① line_items にプラン価格を追加 ─────────────────────
    line_items = []
    plan_price_id = PLAN_PRICE.get(plan)
    if plan_price_id:
        line_items.append({"price": plan_price_id, "quantity": 1})

    # ──② ★ここだけ差し替え★  オプション価格テーブルを決定
    opt_table = (
        OPTION_PRICE_HALF if getattr(settings, "OPTION_DISCOUNT_ACTIVE", False)
        else OPTION_PRICE
    )

    if option:
        opt_price_id = opt_table.get(option)
        if opt_price_id:
            line_items.append({"price": opt_price_id, "quantity": 1})

    # ──③ 以降は元のまま ──────────────────────────────────
    if not line_items:
        return redirect("payments:checkout_form")

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        customer_email=request.user.email,
        client_reference_id=str(request.user.id),
        line_items=line_items,
        success_url=request.build_absolute_uri(
            "/payments/success/?session_id={CHECKOUT_SESSION_ID}"
        ),
        cancel_url=request.build_absolute_uri("/payments/cancel/"),
        metadata={"plan": plan or "", "option": option or ""},
    )
    return redirect(session.url, code=303)

def payment_success(request):
    # ここで session_id などを取り出し、
    # Stripeに問い合わせして Paymentを作る or サンクスページを返す
    session_id = request.GET.get('session_id')

    return render(request, 'payments/success.html')
