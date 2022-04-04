"""CourseProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views
from django.contrib.auth import views as auth

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.Login, name ='login'),
    path('logout/', auth.LogoutView.as_view(template_name ='user/logout.html'), name ='logout'),
    path('register/', views.register, name ='register'),
    path('password_reset/done/', auth.PasswordResetDoneView.as_view(template_name='password/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth.PasswordResetConfirmView.as_view(template_name="password/password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset/done/', auth.PasswordResetCompleteView.as_view(template_name='password/password_reset_complete.html'), name='password_reset_complete'),
    path('password_reset/', views.password_reset_request, name ='password_reset'),
    path('myapp1/<str:coin_name>', views.detail, name='detail'),
    path('config/', views.stripe_config),
    path('create-checkout-session/', views.create_checkout_session),
    path('success/', views.SuccessView),
    path('cancelled/', views.CancelledView),
    path('orders/', views.orderHistory,name="orders"),
    path('portfolio/', views.portfoilio, name="portfolio"),

]

