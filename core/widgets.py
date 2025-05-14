# core/widgets.py
from django import forms

class CustomRadio(forms.RadioSelect):
    template_name = "core/widgets/customRadio.html"
