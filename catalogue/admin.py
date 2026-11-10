from django.contrib import admin

from .models import Adherent, Auteur, Emprunt, Livre

admin.site.register([Auteur, Livre, Adherent, Emprunt])
