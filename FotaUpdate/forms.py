from django import forms
from django.views.generic import TemplateView

from .Azurefunctions import get_list_of_all_devices


class LoginForm(forms.Form):
    username = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'placeholder': 'password', 'type':'password'}))


class UpdateForm(forms.Form):
    device_ids = forms.ChoiceField(widget=forms.Select(attrs={"onChange": 'myFunction()'}), label="Device ID")

    def __init__(self, *args, **kwargs):
        super(UpdateForm, self).__init__(*args, **kwargs)
        list_ids = []
        list_ids = get_list_of_all_devices()
        result = []
        result.append(("Select device id", "Select device id"))
        for i in list_ids:
            device_ids_tuple = ()
            device_ids_tuple = device_ids_tuple + (str(i), str(i))
            result.append(device_ids_tuple)
        self.fields['device_ids'].choices = result


class UpdateCurrentDetails(forms.Form):
    latest_version = forms.CharField(max_length=200)
    browse_file = forms.FileField()


