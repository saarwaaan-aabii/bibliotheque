from django.test import TestCase

from .forms import EmpruntForm, LivreForm
from .models import MAX_EMPRUNTS, Adherent, Emprunt, Livre


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
