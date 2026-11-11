from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from .forms import EmpruntForm, LivreForm
from .import_export import exporter_json
from .models import Emprunt, Livre


def livre_liste(request):
    livres = Livre.objects.select_related("auteur")
    q = request.GET.get("q", "").strip()
    if q:
        livres = livres.filter(Q(titre__icontains=q) | Q(auteur__nom__icontains=q))
    return render(request, "catalogue/livre_liste.html", {"livres": livres, "q": q})


def livre_detail(request, pk):
    livre = get_object_or_404(Livre, pk=pk)
    emprunt_en_cours = livre.emprunts.filter(date_retour__isnull=True).first()
    return render(request, "catalogue/livre_detail.html", {
        "livre": livre,
        "emprunt_en_cours": emprunt_en_cours,
    })


@never_cache
@require_GET
def livre_disponibilite(request, pk):
    """Lecture seule, pour l'appel AJAX : n'emprunte et ne réserve rien."""
    livre = get_object_or_404(Livre, pk=pk)
    return JsonResponse({"disponible": livre.disponible})


@require_GET
def livres_export_json(request):
    """Télécharge le catalogue au format JSON."""
    response = HttpResponse(exporter_json(), content_type="application/json; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="livres.json"'
    return response


def livre_form(request, pk=None):
    """Création (pk=None) ou modification d'un livre."""
    livre = get_object_or_404(Livre, pk=pk) if pk else None
    form = LivreForm(request.POST or None, instance=livre)
    if request.method == "POST" and form.is_valid():
        livre = form.save()
        messages.success(request, f"Livre « {livre} » enregistré.")
        return redirect("livre_detail", pk=livre.pk)
    return render(request, "catalogue/form.html", {
        "form": form,
        "titre_page": "Modifier le livre" if pk else "Nouveau livre",
    })


@require_POST
def livre_supprimer(request, pk):
    livre = get_object_or_404(Livre, pk=pk)
    livre.delete()
    messages.success(request, f"Livre « {livre} » supprimé.")
    return redirect("livre_liste")


def emprunt_creer(request):
    form = EmpruntForm(request.POST or None, initial={"livre": request.GET.get("livre")})
    if request.method == "POST" and form.is_valid():
        emprunt = form.save()
        messages.success(request, f"Emprunt enregistré : {emprunt}.")
        return redirect("livre_detail", pk=emprunt.livre.pk)
    return render(request, "catalogue/form.html", {"form": form, "titre_page": "Nouvel emprunt"})


@require_POST
def emprunt_retour(request, pk):
    emprunt = get_object_or_404(Emprunt, pk=pk)
    if emprunt.date_retour:
        messages.error(request, "Ce livre a déjà été rendu.")
    else:
        emprunt.date_retour = timezone.now().date()
        emprunt.save()
        messages.success(request, f"Retour enregistré : {emprunt.livre}.")
    return redirect("livre_detail", pk=emprunt.livre.pk)
