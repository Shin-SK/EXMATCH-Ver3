# payments/views.py

import stripe
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required  # ← これを追加
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from .models import Payment


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_ENDPOINT_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        user_id = session.get('client_reference_id')
        if not user_id:
            return HttpResponse(status=200)

        User = get_user_model()
        user = User.objects.get(id=user_id)

        # ★ metadata からプラン/オプションを取得
        plan_str = session['metadata'].get('plan') if 'metadata' in session else None
        option_str = session['metadata'].get('option') if 'metadata' in session else None

        # 万が一metadataに何も入っていないならデフォルト値を入れるとか
        plan_str = plan_str or 'standard_1m'
        option_str = option_str or None

        Payment.objects.create(
            user=user,
            plan=plan_str,
            option=option_str
        )

    return HttpResponse(status=200)


    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_ENDPOINT_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('client_reference_id')  # create_checkout_sessionでセットした
        if user_id:
            User = get_user_model()
            user = User.objects.get(id=user_id)
            Payment.objects.create(
                user=user,
                plan='standard_1m',  # 例
                option=None
            )
    return HttpResponse(status=200)



@login_required
@csrf_exempt
def create_checkout_session(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    if request.method == 'POST':
        plan = request.POST.get('plan')  # e.g. "standard_3m"
        option = request.POST.get('option')  # e.g. "plus_profile" or None

        # 1) ユーザーが選択したプランに対応するprice_idを決める
        if plan == 'standard_1m':
            price_id = "price_1R8unuF2VxVQdhvzddkOdfHL"
        elif plan == 'standard_3m':
            price_id = "price_1R8uoKF2VxVQdhvzg2uDmixR"
        elif plan == 'standard_6m':
            price_id = "price_1R8uohF2VxVQdhvzypM52FQE"
        elif plan == 'standard_12m':
            price_id = "price_1R8upoF2VxVQdhvzYWltu9rl"
        else:
            price_id = None

        # line_items の配列を作る
        line_items = []
        if price_id:
            line_items.append({
                "price": price_id,
                "quantity": 1,
            })

        # 2) オプションがあれば、さらにオプション用 price_id を追加
        if option == "plus_profile":
            option_price_id = "price_1R8uq0F2VxVQdhvzsk2LpQ3Z"
            line_items.append({
                "price": option_price_id,
                "quantity": 1,
            })

        # チェック: もしline_itemsが空なら何も購入しないことになる → 画面に戻すなど
        if not line_items:
            return redirect('payments:checkout_form')  # or エラーメッセージ

        # 3) Checkoutセッションを作成
        checkout_session = stripe.checkout.Session.create(
            success_url="http://127.0.0.1:8000/payments/success/?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://127.0.0.1:8000/payments/cancel/",
            payment_method_types=["card"],
            mode="subscription",
            line_items=line_items,
            client_reference_id=str(request.user.id),  # user.idを紐付け
			metadata={
				"plan": plan,        # e.g. "standard_3m"
				"option": option,    # e.g. "plus_profile"
		    }
        )

        return redirect(checkout_session.url, code=303)

    # GETアクセスなら単純にフォームを表示
    return render(request, 'payments/checkout_form.html')


	# payments/views.py
def payment_success(request):
    # ここで session_id などを取り出し、
    # Stripeに問い合わせして Paymentを作る or サンクスページを返す
    session_id = request.GET.get('session_id')
    # TODO: ここで sessionを stripe.checkout.Session.retrieve(session_id) し、statusを確認してもOK

    return render(request, 'payments/success.html')
