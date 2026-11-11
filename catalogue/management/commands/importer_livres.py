from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from catalogue.import_export import importer_livres, lire_json, lire_xml


class Command(BaseCommand):
    help = "Importe des livres depuis un fichier local .json ou .xml"

    def add_arguments(self, parser):
        parser.add_argument("fichier")

    def handle(self, *args, **options):
        chemin = Path(options["fichier"])
        lecteurs = {".json": lire_json, ".xml": lire_xml}
        if chemin.suffix not in lecteurs:
            raise CommandError("Le fichier doit se terminer par .json ou .xml")
        try:
            livres = lecteurs[chemin.suffix](chemin.read_text(encoding="utf-8"))
            crees = importer_livres(livres)
        except (OSError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"{crees} livre(s) importé(s) sur {len(livres)}."))
