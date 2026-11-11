# Démonstration — Bibliothèque

Scénario d'environ 5 minutes pour montrer l'application et expliquer les choix techniques.
Pas de support à préparer : le site dans le navigateur, le code dans l'éditeur, un terminal.

## Préparation

Suivre l'installation du [README](README.md), puis repartir d'une base propre (données fictives de départ) :

```bash
python manage.py migrate
python manage.py runserver
```

Garder ouverts : le navigateur sur http://127.0.0.1:8000/, l'éditeur de code et un second terminal.

## Scénario

| # | Montrer | Dire | Code |
|---|---|---|---|
| 1 | Page d'accueil `/` | Une bibliothèque : 4 modèles (`Auteur`, `Livre`, `Adherent`, `Emprunt`) reliés par des `ForeignKey`. Les données viennent d'une migration de données. | `catalogue/models.py`, `migrations/0002_donnees_fictives.py` |
| 2 | Rechercher `camus` | Recherche par titre **ou** nom d'auteur : paramètre `?q=`, `icontains` et `Q(...) \| Q(...)`. | `views.py` → `livre_liste` |
| 3 | « + Nouveau livre » avec l'ISBN `12-AB` | Validation côté serveur : le formulaire refuse, le message s'affiche à côté du champ. | `forms.py` → `clean_isbn` |
| 4 | Détail d'un livre → « Afficher l'historique » | Afficher/masquer en JavaScript : `hidden` et `aria-expanded`, aucune requête serveur. | `static/catalogue/app.js` |
| 5 | « Nouvel emprunt » → choisir *L'Étranger*, puis *La Peste* | Appel AJAX avec `fetch()` : « Déjà emprunté » / « Disponible », sans recharger la page. | `app.js`, `views.py` → `livre_disponibilite` |
| 6 | Choisir *L'Étranger* et valider quand même | Refusé par le serveur : c'est la **règle métier**. L'AJAX n'est qu'une indication. | `models.py` → `Emprunt.clean()` |
| 7 | Ouvrir `/api/livres/`, puis `/api/livres/999/` | API REST avec DRF : liste, détail, création (formulaire en bas de page), erreurs 400 et 404. | `serializers.py`, `api.py` |
| 8 | Terminal : `python manage.py importer_livres donnees/livres.xml` | Lecture XML → dictionnaires Python → objets `Livre`. Tout ou rien avec `transaction.atomic`. Puis « Exporter en JSON » sur l'accueil. | `import_export.py` |
| 9 | Terminal : `python manage.py test` | 15 tests : 13 tests Django (dont les 2 règles métier) et 2 tests de bout en bout dans un vrai navigateur. GitHub Actions les relance à chaque pull request. | `tests.py`, `tests_e2e.py`, `.github/workflows/tests.yml` |

## Les tests de bout en bout (e2e) expliqués

### Pourquoi ces tests ?

Les tests de `tests.py` utilisent `self.client` : un faux navigateur qui envoie des requêtes et lit le HTML,
mais **n'exécute pas le JavaScript**. Ils ne peuvent donc pas vérifier que le bouton « Afficher
l'historique » marche, ni que `fetch()` affiche bien le résultat.

Un test **de bout en bout** (e2e, *end-to-end*) teste toute la chaîne, comme un vrai visiteur :

```
navigateur (Chromium) ──clic──► JavaScript (app.js) ──fetch()──► serveur Django ──► base de données
        ▲                                                                              │
        └──────────────────── affichage du résultat dans la page ◄────────────────────┘
```

### Ce que vérifient les 2 tests (`catalogue/tests_e2e.py`)

| Test | Étapes |
|---|---|
| `test_afficher_masquer_historique` | ouvrir *Les Misérables* → l'historique est caché → clic → visible, contient « Karim Durand », `aria-expanded="true"`, texte « Masquer l'historique » → clic → caché à nouveau |
| `test_disponibilite_ajax_sans_rechargement` | ouvrir « Nouvel emprunt » → choisir *L'Étranger* → « Déjà emprunté. » → choisir *La Peste* → « Disponible… » → l'URL n'a pas changé (donc pas de rechargement : c'est bien de l'AJAX) |

### Les outils

| Outil | Rôle |
|---|---|
| **Playwright** | pilote un vrai navigateur Chromium depuis Python : ouvrir une page, cliquer, choisir une option, lire le texte |
| **`StaticLiveServerTestCase`** (Django) | démarre un **vrai serveur Django** pendant le test, avec une base de test et les fichiers statiques (`app.js`) |
| **`expect(...)`** (Playwright) | vérifie l'état de la page et **attend** automatiquement que le JavaScript ait fini (la réponse de `fetch()` arrive après un court délai) |

### Lecture d'un test

```python
def test_disponibilite_ajax_sans_rechargement(self):
    self.page.goto(f"{self.live_server_url}/emprunts/nouveau/")   # ① ouvrir la page
    url_avant = self.page.url
    zone = self.page.locator("#disponibilite")

    self.page.select_option("#id_livre", label="L'Étranger")       # ② agir comme un visiteur
    expect(zone).to_have_text("Déjà emprunté.")                    # ③ vérifier (attend la réponse)

    self.page.select_option("#id_livre", label="La Peste")
    expect(zone).to_have_text("Disponible — l'enregistrement vérifiera à nouveau.")
    self.assertEqual(self.page.url, url_avant)                     # pas de rechargement de page
```

Même structure que les autres tests : **préparer**, **agir**, **vérifier**.

### Trois détails techniques

1. **`serialized_rollback = True`** : le serveur de test vide la base après chaque test. Cette option
   demande à Django de **recharger les données fictives** avant chaque test.
2. **Le navigateur démarre dans `setUp`** (pour chaque test) : Playwright lance une boucle `asyncio`, et
   Django doit avoir rechargé les données **avant** qu'elle démarre (`DJANGO_ALLOW_ASYNC_UNSAFE` autorise
   Django à fonctionner à côté de cette boucle).
3. **Test ignoré si Playwright manque** (`@unittest.skipIf`) : avec seulement `requirements.txt`,
   `python manage.py test` affiche `OK (skipped=2)` au lieu d'échouer.

### Installation et lancement

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python manage.py test
```

`requirements-dev.txt` = `requirements.txt` + Playwright : l'application elle-même n'a **pas** de
dépendance en plus. Dans GitHub Actions, la CI installe Playwright et Chromium, puis lance les 15 tests.

### Preuve que les tests servent à quelque chose

En cassant volontairement `app.js` (le bouton, puis l'URL du `fetch()`), chacun des 2 tests **échoue**.
Ils détectent donc une vraie panne du JavaScript, qu'aucun test de `tests.py` ne verrait.

## Questions possibles et réponses

**Où est la règle métier ?**
Dans `Emprunt.clean()` : un livre déjà emprunté est refusé, et un adhérent ne peut pas avoir plus de
3 emprunts en cours. Elle est appelée par `form.is_valid()`, donc vérifiée côté serveur.

**Pourquoi la règle ne s'applique-t-elle qu'à la création ?**
`clean()` s'arrête si l'emprunt existe déjà (`if self.pk`). Sinon, enregistrer un retour serait bloqué :
le livre est justement encore « emprunté » à ce moment-là.

**Pourquoi revérifier au serveur si le JavaScript affiche « Disponible » ?**
Vérifier n'est pas réserver : quelqu'un peut emprunter le livre entre la vérification et l'envoi.
Et le serveur ne doit jamais faire confiance au navigateur (le JavaScript peut être désactivé ou contourné).

**Pourquoi GET pour la disponibilité et POST pour supprimer ?**
GET ne fait que lire, sans effet sur les données. Tout ce qui modifie (supprimer, enregistrer un retour)
passe par POST, protégé par le jeton CSRF. Un GET sur `/livres/<id>/supprimer/` renvoie 405.

**À quoi sert le serializer ?**
Il transforme un `Livre` en JSON (sortie de l'API) et valide les données reçues (entrée) :
ISBN, année, auteur existant, ISBN unique. `auteur_nom` et `disponible` sont en lecture seule.

**Pourquoi `transaction.atomic` dans l'import ?**
Tout ou rien : si un livre du fichier est invalide, aucun livre ni auteur n'est créé.
On ne se retrouve jamais avec un import à moitié fait.

**Comment le JSON et le XML deviennent-ils des objets Python ?**
`json.loads` et `xml.etree.ElementTree` lisent le texte ; on obtient une liste de dictionnaires,
puis chaque dictionnaire devient un `Livre` validé par `LivreForm`.

**Pourquoi `select_related("auteur")` ?**
Pour charger l'auteur de chaque livre dans la même requête SQL, au lieu d'une requête par livre.

**Que se passe-t-il si on supprime un livre ?**
`on_delete=CASCADE` : ses emprunts sont supprimés aussi. C'est indiqué dans les limites du README.

**Pourquoi `fetch()` et pas jQuery ?**
Le cahier des charges demande `fetch()` ; il est intégré au navigateur, donc aucune bibliothèque à ajouter.

**Quelle différence entre les tests de `tests.py` et ceux de `tests_e2e.py` ?**
`tests.py` teste le serveur (formulaires, vues, API) sans navigateur : c'est rapide, mais le JavaScript
n'est pas exécuté. `tests_e2e.py` ouvre un vrai navigateur et teste le JavaScript et le serveur ensemble,
comme un visiteur.

**Pourquoi Playwright est-il dans `requirements-dev.txt` et pas dans `requirements.txt` ?**
Il ne sert qu'aux tests. Pour utiliser l'application, `requirements.txt` suffit ; sans Playwright, les
2 tests sont simplement ignorés.

## En cas de problème pendant la démo

| Problème | Solution |
|---|---|
| `no such table` | `python manage.py migrate` |
| Les données ont été modifiées | supprimer `db.sqlite3`, puis `python manage.py migrate` |
| Port 8000 déjà utilisé | `python manage.py runserver 8001` |
| `ModuleNotFoundError: django` | utiliser le Python du `.venv` (voir README) |
