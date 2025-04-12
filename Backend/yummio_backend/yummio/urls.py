"""
URL configuration for yummio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
"""
URL configuration for the yummio app.
"""
from django.urls import path
from .views import index_view, root, signup, login, logout, history, items, find_restaurants,apply_filters
# from . import views

urlpatterns = [
  path('', index_view, name='index'),  # Serve frontend in production
    path('root/', root, name='root'),  # Optional root endpoint for testing
    path('api/signup/', signup, name='signup'),
    path('api/login/', login, name='login'),
    path('api/logout/', logout, name='logout'),
    path('api/history/', history, name='history'),
    path('api/items/', items, name='items'),
    path('api/restaurants/', find_restaurants, name='find_restaurants'),
    path('api/apply-filters/', apply_filters, name='apply_filters'),
]