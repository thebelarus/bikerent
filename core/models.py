from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.gis.db.models import PointField

from django.db.models.signals import post_save
from django.dispatch import receiver

class BikeBrand(models.Model):
    name = models.CharField(unique = True, max_length = 30, verbose_name='name')
    
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('brand-detail', kwargs={'pk': self.pk})

class BikeModel(models.Model):
    name = models.CharField(unique = True, max_length = 30, verbose_name='name')
    
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('model-detail', kwargs={'pk': self.pk})

class Bike(models.Model):
    name = models.CharField(unique = True, max_length = 30, verbose_name='name')
    vin_code =  models.CharField(unique = True, max_length = 30, verbose_name='vin code')
    brand = models.ForeignKey(BikeBrand, on_delete=models.CASCADE, verbose_name='brand')
    model = models.ForeignKey(BikeModel, on_delete=models.CASCADE, verbose_name='model')
    token = models.CharField(unique = True, max_length = 30, verbose_name='token')

    def __str__(self):
        return '{}_{}_{}'.format(self.name, self.brand, self.model)  

    def get_absolute_url(self):
        return reverse('bike-detail', kwargs={'pk': self.pk})

class BikeReviews(models.Model):
    name = models.TextField( verbose_name='name')
    date = models.DateTimeField(auto_now_add=True, verbose_name='datetime')
    bike = models.ForeignKey(Bike, on_delete=models.CASCADE, verbose_name='bike')

    def __str__(self):
        return self.name    

    def get_absolute_url(self):
        return reverse('bike-review-detail', kwargs={'pk': self.pk})

class BikeCurrentLocation(models.Model):
    bike = models.OneToOneField(Bike, on_delete=models.CASCADE, verbose_name='bike')
    location = PointField(verbose_name='location')
    datetime = models.DateTimeField(auto_now_add=True, verbose_name='datetime')
    load = models.BooleanField(default=False)
    valide = models.BooleanField(default=True)

    def __str__(self):
        return '{}'.format(self.bike)      

    def get_absolute_url(self):
        return reverse('bike-current-location-detail', kwargs={'pk': self.pk})

class Trip(models.Model):
    bike = models.ForeignKey(BikeCurrentLocation, related_name='bike_location', on_delete=models.CASCADE, verbose_name='bike')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='user')
    datetime_rent_start = models.DateTimeField(auto_now_add=True, verbose_name='datetime rent start')
    end = models.BooleanField(default=False)
    datetime_rent_end = models.DateTimeField(null=True, blank=True, verbose_name='datetime rent end')
    cost = models.IntegerField(default=0)
    datetime_paid = models.DateTimeField(auto_now_add=True, verbose_name='datetime paid')


class TripLocation(models.Model):
    name = models.OneToOneField(Trip, related_name='trip', on_delete=models.CASCADE)        
    distance = models.IntegerField(default=0)
    start_point_location = PointField(verbose_name='start point location')

class CashInvite(models.Model):
    name = models.CharField(unique = True, max_length = 50, verbose_name='Инвайт код')
    cash = models.IntegerField(verbose_name='Токены')
    expired = models.BooleanField(default=False, verbose_name='Использован')

    def __str__(self):
        return '{}_{}'.format(self.name, self.cash)  

class UserLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='user')
    location = PointField(verbose_name='location')
    datetime = models.DateTimeField(auto_now_add=True, verbose_name='datetime')
        

class UserBikeLocation(UserLocation):
    bike = models.ForeignKey(Bike, on_delete=models.CASCADE, verbose_name='bike')


class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    cash = models.IntegerField(default=100)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


