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
| 9 | Terminal : `python manage.py test` | 13 tests, dont les 2 règles métier. GitHub Actions les relance à chaque pull request. | `tests.py`, `.github/workflows/tests.yml` |

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

## En cas de problème pendant la démo

| Problème | Solution |
|---|---|
| `no such table` | `python manage.py migrate` |
| Les données ont été modifiées | supprimer `db.sqlite3`, puis `python manage.py migrate` |
| Port 8000 déjà utilisé | `python manage.py runserver 8001` |
| `ModuleNotFoundError: django` | utiliser le Python du `.venv` (voir README) |
