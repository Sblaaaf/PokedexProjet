"""
URL configuration for pokeApp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from pokedex import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add/<int:pokemon_id>/', views.add_to_team, name='add_to_team'),
    path('remove/<int:member_index>/', views.remove_team_member, name='remove_team_member'),
    path('clear/', views.clear_team, name='clear_team'),
    path('combat/', views.combat, name='combat'),
    path('attack/', views.attack_turn, name='attack_turn'),
    path('switch/<int:index>/', views.switch_pokemon, name='switch_pokemon'),
    path('reset_combat/', views.reset_combat, name='reset_combat'),
]