from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.products_list, name='products_list'),
    path('add/', views.add_product, name='add_product'),
    
    # Теперь оба маршрута вызывают кастомные функции из views.py
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
