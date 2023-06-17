from django.db import models
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder

# Create your models here.
class Store(models.Model):
    data = models.JSONField(encoder=DjangoJSONEncoder ,null=False)
    last_modify = models.DateTimeField(auto_now=True)
    modify_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='modify_by', null=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='owner', null=True)

    def __str__(self):
        return f"{self.id} - {self.data['Type']}"


class LoginLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.user) + ': ' + str(self.timestamp)


class Utility(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    date = models.DateField(null=False)
    water = models.FloatField(null=False, default=0.0)
    electric = models.FloatField(null=False, default=0.0)
    wash = models.FloatField(null=False, default=0.0)

    def __str__(self):
        return self.store


class Map(models.Model):
    store = models.OneToOneField(Store, on_delete=models.CASCADE)
    latlong = models.CharField(max_length=255)
    title = models.CharField(max_length=255, null=False)
    detail = models.TextField(null=True)

    def __str__(self) -> str:
        return self.title


class Map_img(models.Model):
    map = models.ForeignKey(Map, on_delete=models.CASCADE)
    img = models.ImageField(upload_to='uploads/%Y/%m/%d/')

    def __str__(self) -> str:
        return self.map.title