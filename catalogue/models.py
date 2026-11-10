from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

MAX_EMPRUNTS = 3  # nombre max d'emprunts en cours par adhérent


class Auteur(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return f"{self.prenom} {self.nom}".strip()


class Livre(models.Model):
    titre = models.CharField(max_length=200)
    auteur = models.ForeignKey(Auteur, on_delete=models.CASCADE, related_name="livres")
    isbn = models.CharField(max_length=13, unique=True)
    annee = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["titre"]

    def __str__(self):
        return self.titre

    @property
    def disponible(self):
        """Un livre est disponible s'il n'a aucun emprunt non rendu."""
        return not self.emprunts.filter(date_retour__isnull=True).exists()


class Adherent(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    def emprunts_en_cours(self):
        return self.emprunts.filter(date_retour__isnull=True)


class Emprunt(models.Model):
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name="emprunts")
    adherent = models.ForeignKey(Adherent, on_delete=models.CASCADE, related_name="emprunts")
    date_emprunt = models.DateField(default=timezone.now)
    date_retour = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-date_emprunt"]

    def __str__(self):
        return f"{self.livre} → {self.adherent}"

    def clean(self):
        """Règles métier vérifiées côté serveur (seulement à la création)."""
        if self.pk:
            return
        if self.livre_id and not self.livre.disponible:
            raise ValidationError("Ce livre est déjà emprunté.")
        if self.adherent_id and self.adherent.emprunts_en_cours().count() >= MAX_EMPRUNTS:
            raise ValidationError(f"Cet adhérent a déjà {MAX_EMPRUNTS} emprunts en cours.")
