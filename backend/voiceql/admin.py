from django.contrib import admin
from .models import sales

@admin.register(sales)
class SalesAdmin(admin.ModelAdmin):
    list_display = ("id" , "products" , "price")

# Register your models here.
