"""Données fictives pour tester l'application (chargées par `migrate`)."""
from datetime import date

from django.db import migrations

AUTEURS = [
    ("Hugo", "Victor"),
    ("Camus", "Albert"),
    ("Sand", "George"),
]

LIVRES = [
    # (titre, nom de l'auteur, isbn, année)
    ("Les Misérables", "Hugo", "9782070409228", 1862),
    ("Notre-Dame de Paris", "Hugo", "9782253009689", 1831),
    ("L'Étranger", "Camus", "9782070360024", 1942),
    ("La Peste", "Camus", "9782070360420", 1947),
    ("La Mare au diable", "Sand", "9782253004318", 1846),
]

ADHERENTS = [
    ("Martin", "Alice", "alice.martin@example.test"),
    ("Durand", "Karim", "karim.durand@example.test"),
]

EMPRUNTS = [
    # (isbn du livre, email de l'adhérent, date d'emprunt, date de retour)
    ("9782070360024", "alice.martin@example.test", date(2026, 11, 2), None),            # en cours
    ("9782070409228", "karim.durand@example.test", date(2026, 10, 1), date(2026, 10, 20)),  # rendu
]


def charger(apps, schema_editor):
    Auteur = apps.get_model("catalogue", "Auteur")
    Livre = apps.get_model("catalogue", "Livre")
    Adherent = apps.get_model("catalogue", "Adherent")
    Emprunt = apps.get_model("catalogue", "Emprunt")

    auteurs = {nom: Auteur.objects.create(nom=nom, prenom=prenom) for nom, prenom in AUTEURS}
    for titre, nom_auteur, isbn, annee in LIVRES:
        Livre.objects.create(titre=titre, auteur=auteurs[nom_auteur], isbn=isbn, annee=annee)
    for nom, prenom, email in ADHERENTS:
        Adherent.objects.create(nom=nom, prenom=prenom, email=email)
    for isbn, email, debut, retour in EMPRUNTS:
        Emprunt.objects.create(
            livre=Livre.objects.get(isbn=isbn),
            adherent=Adherent.objects.get(email=email),
            date_emprunt=debut,
            date_retour=retour,
        )


def supprimer(apps, schema_editor):
    apps.get_model("catalogue", "Emprunt").objects.all().delete()
    apps.get_model("catalogue", "Livre").objects.filter(isbn__in=[l[2] for l in LIVRES]).delete()
    apps.get_model("catalogue", "Auteur").objects.filter(nom__in=[a[0] for a in AUTEURS]).delete()
    apps.get_model("catalogue", "Adherent").objects.filter(email__in=[a[2] for a in ADHERENTS]).delete()


class Migration(migrations.Migration):
    dependencies = [("catalogue", "0001_initial")]
    operations = [migrations.RunPython(charger, supprimer)]
