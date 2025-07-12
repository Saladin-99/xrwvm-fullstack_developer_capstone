# from django.contrib import admin
# from .models import related models

from django.contrib import admin
from .models import CarMake, CarModel

class CarModelInline(admin.StackedInline):
    model = CarModel
    extra = 1
    fields = ('name', 'type', 'year', 'dealer_id', 'engine', 'base_price', 'is_featured')

@admin.register(CarMake)
class CarMakeAdmin(admin.ModelAdmin):
    list_display = ('name', 'founded_year', 'headquarters', 'created_at')
    list_filter = ('founded_year', 'created_at')
    search_fields = ('name', 'description')
    inlines = [CarModelInline]

@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'car_make', 'type', 'year', 'base_price', 'is_featured', 'created_at')
    list_filter = ('car_make', 'type', 'year', 'is_featured')
    search_fields = ('name', 'car_make__name', 'engine')
    date_hierarchy = 'created_at'
    list_editable = ('is_featured',)
