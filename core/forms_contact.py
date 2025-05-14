# core/forms_contact.py
from django import forms
from django_contact_form.forms import ContactForm

class ContactFormWithSubject(ContactForm):
    """件名フィールド付きのお問い合わせフォーム"""

    subject = forms.CharField(label="件名", max_length=100)

    # 件名をメールに反映させる
    def get_message_dict(self):
        msg_dict = super().get_message_dict()
        msg_dict["subject"] = self.cleaned_data["subject"]
        return msg_dict
