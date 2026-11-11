from django.urls import path

from . import views

urlpatterns = [
    path("", views.livre_liste, name="livre_liste"),
    path("livres/nouveau/", views.livre_form, name="livre_creer"),
    path("livres/<int:pk>/", views.livre_detail, name="livre_detail"),
    path("livres/<int:pk>/modifier/", views.livre_form, name="livre_modifier"),
    path("livres/<int:pk>/supprimer/", views.livre_supprimer, name="livre_supprimer"),
    path("emprunts/nouveau/", views.emprunt_creer, name="emprunt_creer"),
    path("emprunts/<int:pk>/retour/", views.emprunt_retour, name="emprunt_retour"),
]
