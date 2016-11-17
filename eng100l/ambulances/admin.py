from django.contrib import admin

# Register your models here.

from .models import Reporter, Ambulances

admin.site.register(Reporter)
admin.site.register(Ambulances)
