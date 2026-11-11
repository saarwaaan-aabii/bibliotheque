from django.utils import timezone
from rest_framework import serializers

from .models import Livre


class LivreSerializer(serializers.ModelSerializer):
    auteur_nom = serializers.StringRelatedField(source="auteur", read_only=True)
    disponible = serializers.BooleanField(read_only=True)

    class Meta:
        model = Livre
        fields = ["id", "titre", "auteur", "auteur_nom", "isbn", "annee", "disponible"]

    # Mêmes règles que LivreForm : l'API ne doit pas accepter ce que le formulaire refuse.
    def validate_isbn(self, value):
        isbn = value.replace("-", "").strip()
        if not isbn.isdigit() or len(isbn) not in (10, 13):
            raise serializers.ValidationError("L'ISBN doit contenir 10 ou 13 chiffres.")
        return isbn

    def validate_annee(self, value):
        if value and value > timezone.now().year:
            raise serializers.ValidationError("L'année ne peut pas être dans le futur.")
        return value
