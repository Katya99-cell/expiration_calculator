from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Исправлено: вызываем функцию products_list и даем имя маршруту 'products_list'
    path('', views.products_list, name='products_list'),
    
    # Страница добавления нового продукта
    path('add/', views.add_product, name='add_product'),
    
    # Встроенные контроллеры авторизации Django
    path('login/', auth_views.LoginView.as_view(template_name='tracker/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]