from django import forms
from django.utils import timezone

from .models import Emprunt, Livre


class LivreForm(forms.ModelForm):
    class Meta:
        model = Livre
        fields = ["titre", "auteur", "isbn", "annee"]

    def clean_isbn(self):
        isbn = self.cleaned_data["isbn"].replace("-", "").strip()
        if not isbn.isdigit() or len(isbn) not in (10, 13):
            raise forms.ValidationError("L'ISBN doit contenir 10 ou 13 chiffres.")
        return isbn

    def clean_annee(self):
        annee = self.cleaned_data.get("annee")
        if annee and annee > timezone.now().year:
            raise forms.ValidationError("L'année ne peut pas être dans le futur.")
        return annee


class EmpruntForm(forms.ModelForm):
    """La méthode Emprunt.clean() (règles métier) est appelée automatiquement."""

    class Meta:
        model = Emprunt
        fields = ["livre", "adherent"]
