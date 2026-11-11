# Bibliothèque — Projet final E4 Full Stack Backend

Application web Django de **gestion de bibliothèque** (thème A) : catalogue de livres, auteurs,
adhérents et emprunts, avec règles métier, pages dynamiques, API REST et import/export JSON/XML.

Technologies : Python 3.12, Django, Django REST Framework, SQLite, HTML/CSS, JavaScript (`fetch()`).

## Fonctionnalités

| Domaine | Fonctionnalités |
|---|---|
| Modèles | `Auteur`, `Livre`, `Adherent`, `Emprunt` (3 `ForeignKey`), migrations, données fictives |
| CRUD | créer, lire, modifier et supprimer un livre ; créer un emprunt ; enregistrer un retour |
| Règles métier (côté serveur) | un livre déjà emprunté ne peut pas être emprunté à nouveau ; 3 emprunts en cours maximum par adhérent (`Emprunt.clean()`) |
| Formulaires | validation serveur : ISBN de 10 ou 13 chiffres, année pas dans le futur ; messages d'erreur |
| Templates | héritage de `base.html`, pages liste et détail, tags et filtres Django |
| Pages dynamiques | recherche par titre ou auteur ; afficher/masquer l'historique d'un livre ; vérification de disponibilité en AJAX (`fetch()`) sans rechargement |
| API REST | liste, détail et création de livres (DRF), validation par serializer, codes 200/201/400/404/405 |
| JSON / XML | import de livres depuis un fichier local `.json` ou `.xml` ; export du catalogue en JSON |
| Tests | 13 tests automatisés, lancés aussi par GitHub Actions à chaque pull request |

## Installation et lancement

Prérequis : Python 3.12 et Git. Toutes les commandes se lancent depuis la racine du dépôt.

```bash
git clone https://github.com/saarwaaan-aabii/bibliotheque.git
cd bibliotheque
```

**macOS / Linux**

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python manage.py migrate
./.venv/bin/python manage.py runserver
```

**Windows (PowerShell)**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Ouvrir ensuite http://127.0.0.1:8000/.

`migrate` crée la base SQLite **et** charge les données fictives (migration
`0002_donnees_fictives`) : 3 auteurs, 5 livres, 2 adhérents, 2 emprunts (dont *L'Étranger* en cours).

Pour utiliser l'administration (`/admin/`), créer d'abord un compte :

```bash
python manage.py createsuperuser
```

## Import et export JSON / XML

Deux fichiers d'exemple sont fournis dans `donnees/`.

```bash
python manage.py importer_livres donnees/livres.json
python manage.py importer_livres donnees/livres.xml
```

- Le fichier est lu (`json` / `xml.etree.ElementTree`) puis transformé en liste de dictionnaires Python,
  puis en objets `Auteur` et `Livre`.
- Chaque livre est validé comme dans le formulaire web. L'import est **tout ou rien** : une erreur
  annule tout. Un ISBN déjà présent est ignoré (on peut relancer la commande sans créer de doublon).
- Formats attendus : une liste d'objets JSON, ou `<livres><livre>…</livre></livres>` en XML, avec les
  champs `titre`, `auteur_nom`, `auteur_prenom`, `isbn`, `annee`.

**Export** : lien « Exporter en JSON » sur la page d'accueil, ou `GET /livres/export.json`.

## Tests

```bash
python manage.py test
```

13 tests dans `catalogue/tests.py` : règles métier des emprunts, validation de l'ISBN, page liste et
recherche, vue JSON de disponibilité, API (liste, détail, création, erreurs), import/export JSON/XML.

Les mêmes vérifications (`check`, `makemigrations --check`, `test`) sont lancées automatiquement par
GitHub Actions à chaque pull request (`.github/workflows/tests.yml`).

## Routes principales

| URL | Méthode | Page |
|---|---|---|
| `/` | GET | catalogue ; recherche avec `?q=` (titre ou nom d'auteur) |
| `/livres/nouveau/` | GET, POST | créer un livre |
| `/livres/<id>/` | GET | détail d'un livre, statut, historique des emprunts |
| `/livres/<id>/modifier/` | GET, POST | modifier un livre |
| `/livres/<id>/supprimer/` | POST | supprimer un livre |
| `/livres/<id>/disponibilite/` | GET | JSON `{"disponible": true/false}` utilisé par l'appel AJAX |
| `/livres/export.json` | GET | télécharger le catalogue en JSON |
| `/emprunts/nouveau/` | GET, POST | créer un emprunt (vérification AJAX de disponibilité) |
| `/emprunts/<id>/retour/` | POST | enregistrer le retour d'un emprunt |
| `/admin/` | GET, POST | administration Django |

## Endpoints API

| Méthode | URL | Réponse |
|---|---|---|
| GET | `/api/livres/` | **200** : liste des livres |
| POST | `/api/livres/` | **201** : livre créé ; **400** : données invalides (erreurs par champ) |
| GET | `/api/livres/<id>/` | **200** : détail ; **404** : livre inconnu |
| PUT, PATCH, DELETE | `/api/livres/<id>/` | **405** : non autorisé |

Exemple de création :

```bash
curl -X POST http://127.0.0.1:8000/api/livres/ \
  -H "Content-Type: application/json" \
  -d '{"titre": "La Chute", "auteur": 2, "isbn": "2070360083", "annee": 1956}'
```

Champs d'un livre : `id`, `titre`, `auteur` (id), `auteur_nom` (lecture seule), `isbn`, `annee`,
`disponible` (lecture seule). Dans un navigateur, `/api/livres/` affiche l'interface web de DRF.

## Organisation du code

```
config/                  réglages Django et routes racine
catalogue/
  models.py              modèles et règle métier (Emprunt.clean)
  forms.py               formulaires et validation
  views.py               pages HTML, vue JSON de disponibilité, export JSON
  api.py, serializers.py API REST (DRF)
  import_export.py       lecture JSON/XML, import, export
  management/commands/   commande importer_livres
  templates/, static/    templates HTML, CSS et JavaScript (app.js)
  migrations/            schéma et données fictives
  tests.py               tests automatisés
donnees/                 fichiers d'exemple livres.json et livres.xml
```

## Limites connues

- **Pas d'authentification** : tout visiteur peut créer, modifier ou supprimer des livres, et l'API
  accepte les créations sans compte. Ce n'est pas prévu pour un usage en production.
- Les **adhérents et auteurs** se gèrent uniquement dans l'administration Django (`/admin/`) ou par import.
- Supprimer un livre supprime aussi son historique d'emprunts (`on_delete=CASCADE`).
- Les règles d'emprunt sont vérifiées **à la création** d'un emprunt ; enregistrer un retour n'est pas bloqué.
- La vérification AJAX de disponibilité est **indicative** : l'enregistrement revérifie toujours côté serveur.
- Sans JavaScript, l'historique d'un livre reste masqué (le reste de l'application fonctionne).
- Le champ ISBN fait 13 caractères au maximum : un ISBN-13 saisi **avec tirets** est refusé (sans tirets, il est accepté).
- L'export est disponible en JSON seulement ; le XML est pris en charge en lecture (import).
- Base SQLite et serveur de développement uniquement ; aucun déploiement.
