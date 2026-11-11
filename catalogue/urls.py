from django.urls import path

from . import api, views

urlpatterns = [
    path("", views.livre_liste, name="livre_liste"),
    path("livres/nouveau/", views.livre_form, name="livre_creer"),
    path("livres/<int:pk>/", views.livre_detail, name="livre_detail"),
    path("livres/<int:pk>/modifier/", views.livre_form, name="livre_modifier"),
    path("livres/<int:pk>/disponibilite/", views.livre_disponibilite, name="livre_disponibilite"),
    path("livres/<int:pk>/supprimer/", views.livre_supprimer, name="livre_supprimer"),
    path("livres/export.json", views.livres_export_json, name="livres_export_json"),
    path("emprunts/nouveau/", views.emprunt_creer, name="emprunt_creer"),
    path("emprunts/<int:pk>/retour/", views.emprunt_retour, name="emprunt_retour"),
    # API REST
    path("api/livres/", api.LivreListeAPI.as_view(), name="api_livre_liste"),
    path("api/livres/<int:pk>/", api.LivreDetailAPI.as_view(), name="api_livre_detail"),
]
