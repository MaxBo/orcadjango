from django import forms

class InjectableValueForm(forms.Form):
    value = forms.CharField(label='Value', max_length=100)