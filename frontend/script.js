// Connexion au serveur Socket.IO
const socket = io("https://pari-en-ligne.onrender"); // adresse du serveur en ligne

// Fenêtres
const inscriptionDiv = document.getElementById("inscription");
const mainDiv = document.getElementById("main");
const matchList = document.getElementById("matchList");
const pariDialog = document.getElementById("pariDialog");

let username = "";

// Valider inscription
document.getElementById("valider").addEventListener("click", () => {
  username = document.getElementById("username").value.trim();
  if (username) {
    inscriptionDiv.classList.add("hidden");
    mainDiv.classList.remove("hidden");
    fetchMatchs();
  }
});

// Recevoir matchs en temps réel
socket.on("nouveau_match", (match) => {
  ajouterMatch(match);
});

// Ajouter un match à la liste
function ajouterMatch(match) {
  const li = document.createElement("li");
  li.textContent = `${match.equipe1} vs ${match.equipe2}`;

  const btn = document.createElement("button");
  btn.textContent = "Parier";
  btn.addEventListener("click", () => ouvrirPariDialog(match));

  li.appendChild(btn);
  matchList.appendChild(li);
}

// Ouvrir boîte de dialogue pari
function ouvrirPariDialog(match) {
  pariDialog.classList.remove("hidden");

  // Nettoyer les anciens événements
  const buttons = pariDialog.querySelectorAll(".pariBtn");
  buttons.forEach(b => {
    b.onclick = () => {
      const choix = b.getAttribute("data-choice");
      alert(`${username} a parié sur ${choix} pour ${match.equipe1} vs ${match.equipe2}`);
      pariDialog.classList.add("hidden");

      // Envoyer le pari au serveur via fetch
      fetch("https://pari-en-ligne.onrender/parier", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nom: username, match: match, choix: choix })
      })
      .then(res => res.json())
      .then(data => console.log(data))
      .catch(err => console.error("Erreur serveur :", err));
    }
  });
}

// Récupérer matchs déjà publiés
function fetchMatchs() {
  fetch("https://pari-en-ligne.onrender/list_matchs")
    .then(res => res.json())
    .then(data => {
      data.forEach(match => ajouterMatch(match));
    })
    .catch(err => console.error("Erreur récupération matchs :", err));
}
