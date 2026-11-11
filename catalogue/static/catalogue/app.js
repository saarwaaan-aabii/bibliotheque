// Afficher / masquer : chaque bouton .toggle contrôle le bloc nommé par son aria-controls.
document.querySelectorAll(".toggle").forEach(function (bouton) {
  bouton.addEventListener("click", function () {
    const bloc = document.getElementById(bouton.getAttribute("aria-controls"));
    bloc.hidden = !bloc.hidden;
    bouton.setAttribute("aria-expanded", bloc.hidden ? "false" : "true");
    bouton.textContent = bloc.hidden ? "Afficher l'historique" : "Masquer l'historique";
  });
});

// AJAX : vérifier la disponibilité du livre choisi, sans recharger la page.
const zone = document.getElementById("disponibilite");
const choix = document.getElementById("id_livre");
let derniere = 0; // numéro de la dernière demande : les réponses plus anciennes sont ignorées

if (zone && choix) {
  choix.addEventListener("change", function () {
    const demande = ++derniere;
    if (!choix.value) {
      zone.textContent = "";
      return;
    }
    zone.textContent = "Vérification…";
    fetch(zone.dataset.url.replace("/0/", "/" + choix.value + "/"))
      .then(function (reponse) {
        if (!reponse.ok) {
          throw new Error("HTTP " + reponse.status);
        }
        return reponse.json();
      })
      .then(function (donnees) {
        if (demande !== derniere) return;
        zone.textContent = donnees.disponible
          ? "Disponible — l'enregistrement vérifiera à nouveau."
          : "Déjà emprunté.";
      })
      .catch(function () {
        if (demande !== derniere) return;
        zone.textContent = "Impossible de vérifier la disponibilité. Réessayez.";
      });
  });
  // Livre déjà choisi (lien « Emprunter » de la page détail) : vérifier tout de suite.
  if (choix.value) {
    choix.dispatchEvent(new Event("change"));
  }
}
