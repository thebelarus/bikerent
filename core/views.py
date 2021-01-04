from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.core.serializers import serialize
from django.urls import reverse_lazy
from . import models, forms
from django.contrib.auth.models import User
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import View
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm 
from django.contrib.gis.measure import Distance
from django.shortcuts import get_object_or_404
from django.contrib.gis.db.models.functions import GeometryDistance
from django.contrib.gis.geos import Point
import json
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin 
import secrets
from datetime import datetime, timezone
from django.db.models import Sum, Count
from django.db.models import CharField, Value

def base_view(request):
    return render(request, 'gps.html')


def calc_distance(point1, point2):
    point1.transform(3857)
    point2.transform(3857)    
    return point1.distance(point2)

# @csrf_exempt
def get_user_location(request):
    latitude = float(request.GET.get('latitude', None))
    longitude = float(request.GET.get('longitude', None))
    ref_location = Point(latitude, longitude, srid=4326)
       

    query = models.BikeCurrentLocation.objects.all().annotate(distance=GeometryDistance("location", ref_location)).order_by("distance")
    bikes_with_locations = serialize('geojson',query)
    # resp_obj = json.loads(bikes_with_locations)
    # i = 0
    # for eachobj in resp_obj['features']:
    #     # try:
    #     #     resp_obj['features'][i]['properties']['touristicarea'] = NaturalEarthMerged.objects.filter(fkprovince__adm1_cod_1=eachobj['properties']['adm1_cod_1'])[0].fktouristicarea.id
    #     # except:
    #     #     resp_obj['features'][i]['properties']['touristicarea'] = 0
    # # i = i+1
    # return JsonResponse(resp_obj)

    return HttpResponse(bikes_with_locations,content_type='json') 


def bike_update_location(request):
    token = request.GET.get('token', None)
    latitude = request.GET.get('latitude', None)
    longitude = request.GET.get('longitude', None)
    if token and latitude and longitude:
        bike = get_object_or_404(models.Bike, token=token)
        bikecurrentlocation = get_object_or_404(models.BikeCurrentLocation, bike=bike)      
        point = Point(float(latitude), float(longitude))
        bikecurrentlocation.location = point
        bikecurrentlocation.save()

        active_trip = models.Trip.objects.filter(bike=bikecurrentlocation, end=False)
        if active_trip.exists():
            trip = active_trip.first()
            if trip.user.profile.cash <= 0:
                bikecurrentlocation.load = False
                bikecurrentlocation.save()
                trip.end = True
                trip.datetime_rent_end = datetime.now()
                trip.save()
            else:
                datetime_now = datetime.now(timezone.utc)
                time_delta = datetime_now - trip.datetime_paid
                tokens_for_pay = int(time_delta.seconds/60)
                if tokens_for_pay > 0:
                    profile = models.Profile.objects.filter(user=trip.user).first()
                    profile.cash -= tokens_for_pay
                    profile.save()
                    trip.user.profile.cash -= tokens_for_pay
                    trip.datetime_paid = datetime_now
                    trip.cost += tokens_for_pay
                    trip.save()

            triplocation = models.TripLocation.objects.filter(name=trip).first()
            p1 = triplocation.start_point_location
            p1.transform(3857)
            p2 = point
            p2.transform(3857)
            distance = p1.distance(p2)
            triplocation.distance += distance
            triplocation.start_point_location = point
            triplocation.save() 
        return HttpResponse('true')
    return HttpResponse('false')


class BrandCreate(CreateView):
    model = models.BikeBrand
    fields = ['name']


class BrandUpdate(UpdateView):
    model = models.BikeBrand
    fields = ['name']


class BrandDelete(DeleteView):
    model = models.BikeBrand
    success_url = reverse_lazy('brand-list')


class BrandDetail(DetailView):
    model = models.BikeBrand


class BrandListView(ListView):

    model = models.BikeBrand
    paginate_by = 100  # if pagination is desired

class ModelCreate(CreateView):
    model = models.BikeModel
    fields = ['name']


class ModelUpdate(UpdateView):
    model = models.BikeModel
    fields = ['name']


class ModelDelete(DeleteView):
    model = models.BikeModel
    success_url = reverse_lazy('model-list')


class ModelDetail(DetailView):
    model = models.BikeModel


class ModelListView(ListView):

    model = models.BikeModel
    paginate_by = 100  # if pagination is desired


class BikeCreate(CreateView):
    model = models.Bike
    fields = '__all__'


class BikeUpdate(UpdateView):
    model = models.Bike
    fields = '__all__'


class BikeDelete(DeleteView):
    model = models.Bike
    success_url = reverse_lazy('bike-list')


class BikeDetail(DetailView):
    model = models.Bike


class BikeListView(ListView):
    model = models.Bike
    paginate_by = 100  # if pagination is desired


class TripCreate(CreateView):
    model = models.Trip
    form_class = forms.TripForm    

class TripUpdate(UpdateView):
    model = models.Trip


class TripDelete(DeleteView):
    model = models.Trip
    success_url = reverse_lazy('trip-list')


class TripDetail(DetailView):
    model = models.Trip


class TripListView(ListView):
    model = models.Trip
    paginate_by = 100  # if pagination is desired

class UserTripCreate(CreateView):
    model = models.Trip
    form_class = forms.TripForm   

def add_user_trip(request):
    message = ''
    if models.Trip.objects.filter(user=request.user, end=False).count() > 0:
        message = 'К сожалению Вы уже арендовади один велосипед!'
    elif  models.Profile.objects.filter(user=request.user).first().cash <= 0:
        message = 'К сожалению Вы у вас на счету недостаточно средств!'
    else:
        if request.method == 'POST':
            form = forms.TripForm(request.POST)
            form.fields['user'].initial = request.user
            form.fields['end'].initial = False

            if form.is_valid() and form.cleaned_data['user'] == request.user:
                load_satus = form.cleaned_data['end']
                bike =  models.BikeCurrentLocation.objects.get(pk = form.cleaned_data['bike'].id)
                if load_satus:
                    bike.load = False
                else:
                    bike.load = True
                bike.save()

                f = form.save()
                triplocation = models.TripLocation()
                triplocation.name = f
                triplocation.start_point_location = f.bike.location
                triplocation.save()

        return redirect('get_online_map')
    form = forms.TripForm(initial={'user':request.user})
    return render(request, 'core/trip_form.html', {'form': form,'message':message})  

def edit_user_trip(request, pk):
    instance = get_object_or_404(models.Trip, id=pk)
    if instance.end:
        message = 'Поездка уже завершена! Создать новую?'
        form = forms.TripForm(initial={'user':request.user})
        return render(request, 'core/trip_form.html', {'form': form,'message':message})  
    
    if request.method == 'POST':
        form = forms.BoolForm(request.POST)
        if form.is_valid() and form.cleaned_data['user']==request.user:
            load_satus = form.cleaned_data['end']
            bike =  models.BikeCurrentLocation.objects.get(pk = instance.bike.id)
            if load_satus:
                bike.load = False
                instance.end = True
            else:
                bike.load = True
                instance.end = False
            instance.datetime_rent_end =  datetime.now()
            bike.save()
            instance.save()
        return redirect('get_online_map')
    form = forms.BoolForm(initial={'end':instance.end})        
    return render(request, 'core/trip_form.html', {'form': form})       

def delete_user_trip(request, pk):
    instance = get_object_or_404(models.Trip, id=pk)
    bike =  models.BikeCurrentLocation.objects.get(pk = instance.bike.id)
    bike.load = False
    bike.save()
    instance.delete()
    return redirect('get_online_map')

class UserTripListView(TripListView):
    def get_queryset(self):
        return models.Trip.objects.filter(user=self.request.user)

class BikeCurrentLocationCreate(CreateView):
    model = models.BikeCurrentLocation
    form_class = forms.BikeCurrentLocationForm
    template_name = 'core/bikecurrentlocation_form.html'

class BikeCurrentLocationUpdate(UpdateView):
    model = models.BikeCurrentLocation
    form_class = forms.BikeCurrentLocationForm
    template_name = 'core/bikecurrentlocation_form.html'


class BikeCurrentLocationDelete(DeleteView):
    model = models.BikeCurrentLocation
    success_url = reverse_lazy('bike-current-location-list')


class BikeCurrentLocationDetail(DetailView):
    model = models.BikeCurrentLocation


class BikeCurrentLocationListView(ListView):
    model = models.BikeCurrentLocation
    paginate_by = 100  # if pagination is desired

@csrf_exempt
def get_bikescurrentlocations_data_for_admin(request):
    bikes_with_locations = serialize('geojson',models.BikeCurrentLocation.objects.all())
    return HttpResponse(bikes_with_locations,content_type='json')

@csrf_exempt
def get_bikescurrentlocations_data_for_user(request):
    latitude = float(request.GET.get('latitude'))
    longitude = float(request.GET.get('longitude'))
    ref_location = Point(longitude,latitude,srid=4326)
    from django.db.models import CharField, Value   
    distance_list = [item.distance  * 100 for item in models.BikeCurrentLocation.objects.filter(valide=True, load=False).annotate(distance=GeometryDistance("location", ref_location))]#.order_by("distance")
    bikes_with_locations = serialize('geojson',models.BikeCurrentLocation.objects.filter(valide=True, load=False))
    resp_obj = json.loads(bikes_with_locations)
    i = 0
    for eachobj in resp_obj['features']:
        resp_obj['features'][i]['properties']['distance'] = round(distance_list.pop(),2)
        i += 1
    return JsonResponse(resp_obj)

def get_online_map(request):
    '''Возвращаем главную страницу с картой'''
    return render(request, 'bike_map.html')

def user_register(request):
    '''Регистрация пользователя'''
    if request.method == "POST":
        form = forms.RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful." )
            return redirect("get_online_map")
        messages.error(request, "Unsuccessful registration. Invalid information.")
    form = forms.RegisterForm
    return render (request=request, template_name='registration/registration.html', context={"form":form})

def user_login(request):
    '''Логин пользователя, форма для логина и ссылки на регистрацию'''
    if request.method == "POST":
        form = forms.LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect("get_online_map")
            else:
                messages.error(request,"Invalid username or password.")
        else:
            messages.error(request,"Invalid username or password.")
    form = forms.LoginForm()
    return render(request=request, template_name="registration/login.html", context={"form":form})

def user_logout(request):
    '''Выход пользователя и редирект на главную страницу'''
    logout(request)
    messages.info(request, "You have successfully logged out.") 
    return redirect("get_online_map")

def generate_token(length = 50):
    '''Генерирация токена с длинной в 50 символов, согласно полю модели'''
    return secrets.token_urlsafe(length)[0:length]

def cash_invite_add(request):
    '''Отдаём, сохраняем форму с сгенерированным токеном'''
    if request.method == 'POST':
        form = forms.CashInviteForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect('cash_invite_list')
    form = forms.CashInviteForm(initial={'name':generate_token()})
    return render(request, 'core/cashinvite_add.html', {'form': form})      


class CashInviteUpdate(UpdateView):
    model = models.CashInvite


class CashInviteDelete(DeleteView):
    model = models.CashInvite
    success_url = reverse_lazy('cash_invite_list')


class CashInviteDetail(DetailView):
    model = models.CashInvite


class CashInviteListView(ListView):
    model = models.CashInvite
    paginate_by = 100  # if pagination is desired        

# @login_required
def get_user_profile(request):
    user_completed_distance = models.Trip.objects.filter(user=request.user).aggregate(Sum('trip__distance'))['trip__distance__sum'] or 0.00
    context = {'distance':user_completed_distance}
    return render(request, 'core/profile.html',{'context':context})


def get_rates(request):
    most_distance_completed_riders = models.Trip.objects.all().values('user__username').annotate(distance=Sum('trip__distance')).order_by('-distance')
    most_popular_bikes = models.Trip.objects.all().values('bike__bike__name').annotate(count=Count('bike')).order_by('-count')
    return render(request, 'core/rates.html',{'most_popular_bikes':most_popular_bikes,'most_distance_completed_riders':most_distance_completed_riders})

def get_user_active_rent(user):
    '''Получает незавершенную поездку пользователя'''
    return models.Trip.objects.filter(user=user, end=False, bike__load=True)

def is_user_active_rent_present(user):
    '''Возращает bool признак существует ли незавершенная поездка у пользователя'''
    if get_user_active_rent(user).exists():
        return True
    return False

def get_user_cash(user):
    '''Получаем текущий состояние счета в профиле пользователя'''
    profile = models.Profile.objects.filter(user=user)
    if profile.exists():
        current_profile = profile.first()
        return current_profile.cash
    return False


def get_base_user_data(request):
    if not request.user.is_authenticated:
        return JsonResponse({})
    user_cash = get_user_cash(request.user)
    is_active_rent_present = is_user_active_rent_present(request.user)
    return JsonResponse({'is_user_active_rent_present':is_active_rent_present,'user_cash':user_cash})

def trip_stop(request):
    trip= get_user_active_rent(request.user)
    if trip.exists():
        trip = trip.first()
        trip.end = True

        bike =  models.BikeCurrentLocation.objects.get(pk = trip.bike.id)
        bike.load = False
        trip.datetime_rent_end = datetime.now()
        bike.save()
        trip.save()
    return redirect('user-trip-list')


def quick_trip_create(request, pk):
    message = ''
    if models.Trip.objects.filter(user=request.user, end=False).count() > 0:
        message = 'Вы уже арендовади один велосипед!'
    else:
        if request.method == 'POST':
            form = forms.TripForm(request.POST)
            form.fields['user'].initial = request.user
            form.fields['bike'].initial = pk
            form.fields['end'].initial = False
            if form.is_valid():
                load_satus = form.cleaned_data['end']
                bike =  models.BikeCurrentLocation.objects.get(pk = form.cleaned_data['bike'].id)
                if load_satus:
                    bike.load = False
                else:
                    bike.load = True
                bike.save()
                f = form.save()
                triplocation = models.TripLocation()
                triplocation.name = f
                triplocation.start_point_location = f.bike.location
                triplocation.save()
            return redirect('get_online_map')
    form = forms.TripForm(initial={'user':request.user,'bike':pk,'end':False})
    return render(request, 'core/trip_form.html', {'form': form,'message':message})  

def get_cash_to_profile(request):
    if request.method == 'POST':

        form = forms.NameCashInviteForm(request.POST) 
        if form.is_valid():
            invite = form.cleaned_data.get('name')
            profile = get_object_or_404(models.Profile, user = request.user)
            cash_invite = get_object_or_404(models.CashInvite, name=invite)
            if not cash_invite.expired:
                profile.cash += cash_invite.cash
                cash_invite.expired = True   
                profile.save()
                cash_invite.save()
            return render(request, 'core/profile.html')

    form = forms.NameCashInviteForm()
    return render(request, 'core/cashinvite_add.html', {'form': form}) 