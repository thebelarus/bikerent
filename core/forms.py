from django.forms import ModelForm
from . import models
from django import forms
from leaflet.forms.fields import PointField
from leaflet.forms.widgets import LeafletWidget
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm 
from captcha.fields import CaptchaField

class LoginForm(AuthenticationForm):
    captcha = CaptchaField(generator='captcha.helpers.math_challenge', label='Капча')
        

class RegisterForm(UserCreationForm):
    captcha = CaptchaField(generator='captcha.helpers.math_challenge', label='Капча')
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(RegisterForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class RegisterProfileForm(UserCreationForm):
    captcha = CaptchaField(generator='captcha.helpers.math_challenge')
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(RegisterForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user        

class BikeReviewsForm(ModelForm):
    class Meta:
        model = models.BikeReviews
        fields = '__all__'


class BrandForm(ModelForm):
    class Meta:
        model = models.BikeBrand
        fields = '__all__'


class BikeModelForm(ModelForm):
    class Meta:
        model = models.BikeModel
        fields = '__all__'


class BikeForm(ModelForm):
    class Meta:
        model = models.Bike
        fields = '__all__' 


class CashInviteForm(ModelForm):
    expired = forms.BooleanField(required=False, label='Использован')
    class Meta:
        model = models.CashInvite
        fields = '__all__' 


class NameCashInviteForm(forms.Form):
    name = forms.CharField(max_length = 50, label='Инвайт')


class TripForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        self.fields['bike'].queryset = models.BikeCurrentLocation.objects.filter(load=False, valide=True)

    class Meta:
        model = models.Trip
        # fields = ('bike',)    
        fields = ('bike','user','end') 
        widgets = {
        'user': forms.HiddenInput(),
        'end': forms.HiddenInput(),
        } 

class BoolForm(forms.Form):
    end = forms.BooleanField(required=False, label='Закончить поездку?')


class UserLocationForm(ModelForm):
    class Meta:
        model = models.UserLocation
        fields = '__all__'  
LEAFLET_WIDGET_ATTRS = {
    'map_height': '600px',
    'map_width': '50%',
    'display_raw': 'true',
    'map_srid': 4326,
}

class BikeCurrentLocationForm(ModelForm):
    class Meta:
        model = models.BikeCurrentLocation
        fields = ('bike','location','load','valide')
        widgets = {'location': LeafletWidget(attrs=LEAFLET_WIDGET_ATTRS)}
