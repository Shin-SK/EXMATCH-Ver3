# core/api_contact.py（新規）
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import serializers, status
from rest_framework.response import Response
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

SUBJECT_CHOICES = (
    ("general", "ご意見・ご要望"),
    ("bug",     "不具合の報告"),
    ("billing", "決済/課金について"),
    ("other",   "その他"),
)

class ContactSerializer(serializers.Serializer):
    email   = serializers.EmailField()
    name    = serializers.CharField(max_length=100)
    subject = serializers.ChoiceField(choices=SUBJECT_CHOICES)
    message = serializers.CharField(max_length=2000)

class ContactAPI(APIView):
    permission_classes = [AllowAny]          # 未ログインもOK
    # throttle_scope = "contact"             # レート制限使うなら有効化（settings側設定が必要）

    def post(self, request):
        ser = ContactSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        subject_label = dict(SUBJECT_CHOICES).get(d["subject"], d["subject"])
        ctx = { **d, "subject_label": subject_label, "now": timezone.now() }

        # テンプレは既存のものを再利用（なければ簡易本文でもOK）
        body_admin = render_to_string("emails/contact_admin.txt", ctx)
        body_user  = render_to_string("emails/contact_user.txt",  ctx)

        # EMAIL_BACKEND=post_office.EmailBackend ならキュー投入されます
        admin = EmailMessage(
            subject=f"[問い合わせ] {subject_label}",
            body=body_admin,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_EMAIL],
            reply_to=[d["email"]],
        )
        admin.send()

        user = EmailMessage(
            subject="【EXMATCH】お問い合わせを受け付けました",
            body=body_user,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[d["email"]],
        )
        user.send()

        return Response({"ok": True}, status=status.HTTP_200_OK)
