import json
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from .forms import EmpruntForm, LivreForm
from .import_export import exporter_json, importer_livres, lire_json, lire_xml
from .models import MAX_EMPRUNTS, Adherent, Auteur, Emprunt, Livre


class RegleMetierEmpruntTests(TestCase):
    """Règles métier de Emprunt.clean(), vérifiées côté serveur via le formulaire."""

    def test_livre_deja_emprunte_refuse(self):
        # Dans les données fictives, « L'Étranger » est emprunté par Alice.
        livre = Livre.objects.get(titre="L'Étranger")
        karim = Adherent.objects.get(email="karim.durand@example.test")
        form = EmpruntForm(data={"livre": livre.pk, "adherent": karim.pk})
        self.assertFalse(form.is_valid())
        self.assertIn("Ce livre est déjà emprunté.", form.non_field_errors())

    def test_limite_emprunts_simultanes(self):
        karim = Adherent.objects.get(email="karim.durand@example.test")
        disponibles = [livre for livre in Livre.objects.all() if livre.disponible]
        for livre in disponibles[:MAX_EMPRUNTS]:
            Emprunt.objects.create(livre=livre, adherent=karim)
        form = EmpruntForm(data={"livre": disponibles[MAX_EMPRUNTS].pk, "adherent": karim.pk})
        self.assertFalse(form.is_valid())
        self.assertIn(f"Cet adhérent a déjà {MAX_EMPRUNTS} emprunts en cours.", form.non_field_errors())


class LivreFormTests(TestCase):
    def test_isbn_invalide_refuse(self):
        livre = Livre.objects.first()
        form = LivreForm(data={"titre": "Test", "auteur": livre.auteur.pk, "isbn": "12-AB"})
        self.assertFalse(form.is_valid())
        self.assertIn("L'ISBN doit contenir 10 ou 13 chiffres.", form.errors["isbn"])


class PagesTests(TestCase):
    def test_liste_des_livres(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Les Misérables")
        self.assertContains(response, "Emprunté")

    def test_recherche_par_titre_ou_auteur(self):
        response = self.client.get("/", {"q": "  camus  "})
        self.assertEqual([livre.titre for livre in response.context["livres"]], ["L'Étranger", "La Peste"])
        response = self.client.get("/", {"q": "misérables"})
        self.assertEqual([livre.titre for livre in response.context["livres"]], ["Les Misérables"])

    def test_disponibilite_json(self):
        etranger = Livre.objects.get(titre="L'Étranger")
        peste = Livre.objects.get(titre="La Peste")
        self.assertEqual(self.client.get(f"/livres/{etranger.pk}/disponibilite/").json(), {"disponible": False})
        self.assertEqual(self.client.get(f"/livres/{peste.pk}/disponibilite/").json(), {"disponible": True})
        self.assertEqual(self.client.get("/livres/9999/disponibilite/").status_code, 404)
        self.assertEqual(self.client.post(f"/livres/{peste.pk}/disponibilite/").status_code, 405)


class ApiLivresTests(TestCase):
    def test_liste_et_detail(self):
        response = self.client.get("/api/livres/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), Livre.objects.count())
        etranger = Livre.objects.get(titre="L'Étranger")
        data = self.client.get(f"/api/livres/{etranger.pk}/").json()
        self.assertEqual(data["auteur_nom"], "Albert Camus")
        self.assertFalse(data["disponible"])
        self.assertEqual(self.client.get("/api/livres/9999/").status_code, 404)

    def test_creation_valide_et_invalide(self):
        auteur = Livre.objects.first().auteur
        livre = {"titre": "Nouveau", "auteur": auteur.pk, "isbn": "2-07-036002-4", "annee": 2000}
        response = self.client.post("/api/livres/", livre, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["isbn"], "2070360024")
        self.assertTrue(Livre.objects.filter(isbn="2070360024").exists())

        invalide = {"titre": "", "auteur": 9999, "isbn": "12-AB"}
        response = self.client.post("/api/livres/", invalide, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()), {"titre", "auteur", "isbn"})

    def test_detail_en_lecture_seule(self):
        livre = Livre.objects.first()
        response = self.client.delete(f"/api/livres/{livre.pk}/")
        self.assertEqual(response.status_code, 405)


class ImportExportTests(TestCase):
    DONNEES = Path(settings.BASE_DIR) / "donnees"

    def test_lecture_json_et_xml_en_objets_python(self):
        depuis_json = lire_json((self.DONNEES / "livres.json").read_text(encoding="utf-8"))
        depuis_xml = lire_xml((self.DONNEES / "livres.xml").read_text(encoding="utf-8"))
        self.assertEqual(depuis_json[0]["titre"], "Germinal")
        self.assertEqual(depuis_xml[1], {"titre": "Madame Bovary", "auteur_nom": "Flaubert",
                                         "auteur_prenom": "Gustave", "isbn": "9782070413119", "annee": "1857"})
        self.assertEqual(importer_livres(depuis_json + depuis_xml), 4)
        self.assertEqual(importer_livres(depuis_json), 0)  # ISBN déjà présents : ignorés
        self.assertEqual(Livre.objects.get(isbn="9782253009375").auteur.nom, "Maupassant")

    def test_fichiers_invalides_refuses(self):
        for texte in ["{pas du json", '{"titre": "seul"}']:
            with self.assertRaises(ValueError):
                lire_json(texte)
        for texte in ["<livres><livre>", "<autres/>", '<!DOCTYPE x [<!ENTITY a "b">]><livres/>']:
            with self.assertRaises(ValueError):
                lire_xml(texte)

    def test_import_tout_ou_rien(self):
        avant = (Livre.objects.count(), Auteur.objects.count())
        livres = [
            {"titre": "Valide", "auteur_nom": "Nouvel", "auteur_prenom": "", "isbn": "1234567890", "annee": 2000},
            {"titre": "ISBN faux", "auteur_nom": "Autre", "auteur_prenom": "", "isbn": "12-AB", "annee": 2000},
        ]
        with self.assertRaises(ValueError):
            importer_livres(livres)
        self.assertEqual((Livre.objects.count(), Auteur.objects.count()), avant)

    def test_export_json(self):
        donnees = json.loads(exporter_json())
        self.assertEqual(len(donnees), Livre.objects.count())
        self.assertEqual(donnees[0]["titre"], "L'Étranger")
        response = self.client.get("/livres/export.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json; charset=utf-8")
        self.assertIn("attachment", response["Content-Disposition"])
