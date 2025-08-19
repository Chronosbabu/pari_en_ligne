const socket = io();

socket.on("connect", () => {
    console.log("Connecté au serveur Socket.IO");
});

socket.on("nouveau_match", (match) => {
    const li = document.createElement("li");
    li.textContent = `${match.equipe1} vs ${match.equipe2}`;
    document.getElementById("matchsList").appendChild(li);
});

function registerUser() {
    const nom = document.getElementById("nom").value;
    const francs = parseInt(document.getElementById("francs").value) || 0;
    const dollars = parseInt(document.getElementById("dollars").value) || 0;

    fetch("/register", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({nom, francs, dollars})
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("registerResult").textContent = data.message;
    });
}

function publierMatch() {
    const equipe1 = document.getElementById("equipe1").value;
    const equipe2 = document.getElementById("equipe2").value;

    socket.emit("publier_match", {equipe1, equipe2});
}
