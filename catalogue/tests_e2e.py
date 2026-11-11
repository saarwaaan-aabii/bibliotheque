"""Tests de bout en bout : un vrai navigateur exécute le JavaScript contre un vrai serveur Django.

Nécessite : pip install -r requirements-dev.txt  puis  playwright install chromium
Sans Playwright installé, ces tests sont ignorés (skip).
"""
import os
import unittest

from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from .models import Livre

try:
    from playwright.sync_api import expect, sync_playwright
except ImportError:
    sync_playwright = None


@unittest.skipIf(sync_playwright is None, "Playwright n'est pas installé (requirements-dev.txt)")
class NavigateurTests(StaticLiveServerTestCase):
    serialized_rollback = True  # garde les données fictives de la migration entre les tests

    @classmethod
    def setUpClass(cls):
        # Playwright (API synchrone) tourne dans une boucle asyncio : Django doit l'autoriser.
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()

    def setUp(self):
        # Navigateur démarré pour chaque test, après le rechargement des données fictives par Django.
        self.playwright = sync_playwright().start()
        self.navigateur = self.playwright.chromium.launch()
        self.page = self.navigateur.new_page()

    def tearDown(self):
        self.navigateur.close()
        self.playwright.stop()

    def test_afficher_masquer_historique(self):
        livre = Livre.objects.get(titre="Les Misérables")
        self.page.goto(f"{self.live_server_url}/livres/{livre.pk}/")
        bouton = self.page.locator("button.toggle")
        historique = self.page.locator("#historique")
        expect(historique).to_be_hidden()

        bouton.click()
        expect(historique).to_be_visible()
        expect(historique).to_contain_text("Karim Durand")
        expect(bouton).to_have_attribute("aria-expanded", "true")
        expect(bouton).to_have_text("Masquer l'historique")

        bouton.click()
        expect(historique).to_be_hidden()
        expect(bouton).to_have_attribute("aria-expanded", "false")

    def test_disponibilite_ajax_sans_rechargement(self):
        self.page.goto(f"{self.live_server_url}/emprunts/nouveau/")
        url_avant = self.page.url
        zone = self.page.locator("#disponibilite")

        self.page.select_option("#id_livre", label="L'Étranger")
        expect(zone).to_have_text("Déjà emprunté.")

        self.page.select_option("#id_livre", label="La Peste")
        expect(zone).to_have_text("Disponible — l'enregistrement vérifiera à nouveau.")
        self.assertEqual(self.page.url, url_avant)  # aucune navigation : tout s'est fait en AJAX
