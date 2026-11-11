from rest_framework import generics

from .models import Livre
from .serializers import LivreSerializer


class LivreListeAPI(generics.ListCreateAPIView):
    """GET : liste des livres. POST : création d'un livre (201, ou 400 si invalide)."""
    queryset = Livre.objects.select_related("auteur")
    serializer_class = LivreSerializer


class LivreDetailAPI(generics.RetrieveAPIView):
    """GET : détail d'un livre (404 s'il n'existe pas)."""
    queryset = Livre.objects.select_related("auteur")
    serializer_class = LivreSerializer
