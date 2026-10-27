from django.contrib import admin
from .models import Route, MountainRange, StartingPoint, Gear

admin.site.register(Route)
admin.site.register(MountainRange)
admin.site.register(StartingPoint)
admin.site.register(Gear)
