from django.contrib import admin
from .models import Product, Category, Profile  # Импортируем Profile

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'manufacture_date', 'storage_temperature', 'is_opened')
    list_filter = ('category', 'storage_temperature', 'is_opened')
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'default_shelf_life_days')

# ОБЯЗАТЕЛЬНО ДЛЯ ДИПЛОМА: вывод профилей в админку
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'telegram_chat_id')
    search_fields = ('user__username', 'telegram_chat_id')

