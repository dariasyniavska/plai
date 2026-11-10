from django.contrib import admin

from .models import Gear, MountainRange, Route, StartingPoint

admin.site.register(Route)
admin.site.register(MountainRange)
admin.site.register(StartingPoint)
admin.site.register(Gear)
