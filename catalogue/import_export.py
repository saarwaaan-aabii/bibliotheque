"""Lecture de livres en JSON / XML et export du catalogue en JSON (fichiers locaux)."""
import json
import xml.etree.ElementTree as ET

from django.db import transaction

from .forms import LivreForm
from .models import Auteur, Livre
from .serializers import LivreSerializer

CHAMPS = ("titre", "auteur_nom", "auteur_prenom", "isbn", "annee")


def lire_json(texte):
    """Texte JSON -> liste de dictionnaires Python. ValueError si le format est faux."""
    try:
        donnees = json.loads(texte)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON invalide : {exc}") from exc
    if not isinstance(donnees, list) or not all(isinstance(d, dict) for d in donnees):
        raise ValueError("Le JSON doit être une liste d'objets livre.")
    return [{champ: d.get(champ) for champ in CHAMPS} for d in donnees]


def lire_xml(texte):
    """Texte XML <livres><livre>...</livre></livres> -> liste de dictionnaires Python."""
    if "<!DOCTYPE" in texte or "<!ENTITY" in texte:
        raise ValueError("Les déclarations DOCTYPE/ENTITY ne sont pas acceptées.")
    try:
        racine = ET.fromstring(texte)
    except ET.ParseError as exc:
        raise ValueError(f"XML invalide : {exc}") from exc
    if racine.tag != "livres":
        raise ValueError("L'élément racine doit être <livres>.")
    return [{champ: livre.findtext(champ) for champ in CHAMPS} for livre in racine.findall("livre")]


@transaction.atomic
def importer_livres(livres):
    """Crée les livres (et leurs auteurs). Tout ou rien : une erreur annule tout l'import.

    Un ISBN déjà présent dans la base est ignoré. Retourne le nombre de livres créés.
    """
    crees = 0
    for position, livre in enumerate(livres, start=1):
        if livre["isbn"] and Livre.objects.filter(isbn=livre["isbn"]).exists():
            continue
        if not livre["auteur_nom"]:
            raise ValueError(f"Livre {position} : auteur_nom est obligatoire.")
        auteur, _ = Auteur.objects.get_or_create(
            nom=livre["auteur_nom"], prenom=livre["auteur_prenom"] or "")
        # Mêmes validations que le formulaire web (ISBN, année, champs obligatoires).
        form = LivreForm(data={"titre": livre["titre"], "auteur": auteur.pk,
                               "isbn": livre["isbn"], "annee": livre["annee"]})
        if not form.is_valid():
            raise ValueError(f"Livre {position} : {form.errors.as_text()}")
        form.save()
        crees += 1
    return crees


def exporter_json():
    """Catalogue complet -> texte JSON (mêmes champs que l'API)."""
    livres = Livre.objects.select_related("auteur")
    return json.dumps(LivreSerializer(livres, many=True).data, ensure_ascii=False, indent=2)
