document.getElementById("receptora").addEventListener("change", function (event) {
  previewImage(event.target.files[0], "receptoraPreview");
});

document.getElementById("doadora").addEventListener("change", function (event) {
  previewImage(event.target.files[0], "doadoraPreview");
});

function previewImage(file, elementId) {
  const reader = new FileReader();
  reader.onload = function (e) {
    const preview = document.getElementById(elementId);
    preview.style.backgroundImage = `url(${e.target.result})`;
    preview.style.backgroundSize = "contain";
    preview.style.backgroundRepeat = "no-repeat";
    preview.style.backgroundPosition = "center";
  };
  reader.readAsDataURL(file);
}



document.getElementById("updateBtn").addEventListener("click", function () {
  const receptoraInput = document.getElementById("receptora");
  const doadoraInput = document.getElementById("doadora");

  const date = new Date();

  const formData = new FormData();

  // Adiciona arquivos
  if (receptoraInput.files[0]) {
    formData.append("receptora", receptoraInput.files[0]);
  }

  if (doadoraInput.files[0]) {
    formData.append("doadora", doadoraInput.files[0]);
  }

  // Adiciona parâmetros
    formData.append("yuv", document.getElementById("yuv").value);
  formData.append("tamanho", document.getElementById("tamanho").value);
  formData.append("diferenca_absoluta", document.getElementById("diferenca").value);
  formData.append("bordas", document.getElementById("bordas").value);
  formData.append("media_cores", document.getElementById("media").value);


  const updateBtn = document.getElementById("updateBtn");
  updateBtn.disabled = true;

  // Envia para o backend
  fetch("/update", {
    method: "POST",
    body: formData
  })
    .then(response => response.json())
    .then(data => {
        console.log("Resposta do backend:", data);
        const elapsedTime = ((Date.now() - date.getTime()) / 1000).toFixed(2);
        // Atualiza a imagem na página
        const preview = document.getElementById("preview");
        preview.src = "preview.png"+ "?t=" + new Date().getTime(); // Adiciona um timestamp para evitar cache

        // Make a notification sound
        const audio = new Audio("/notification.mp3");
        audio.play();

        // espera o som terminar
        audio.addEventListener("ended", () => {
          // Exibe uma alerta de sucesso com o tempo em minutos e segundos da operação.
            alert(`Atualização concluída! Tempo gasto: ${Math.floor(elapsedTime / 60)} minutos e ${elapsedTime % 60} segundos.`);
        });
        updateBtn.disabled = false;
    })
    .catch(error => {
      console.error("Erro ao enviar dados:", error);
    });
});


function setupDragAndDrop(previewId, inputId) {
  const dropZone = document.getElementById(previewId);

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
      previewImage(file, previewId);
      document.getElementById(inputId).files = e.dataTransfer.files;
    }
  });
}

setupDragAndDrop("receptoraPreview", "receptora");
setupDragAndDrop("doadoraPreview", "doadora");

const toggleBtn = document.getElementById("toggleThemeBtn");

function setTheme(dark) {
  document.body.classList.toggle("dark", dark);
  toggleBtn.textContent = dark ? "☀️ Modo Claro" : "🌙 Modo Escuro";
  localStorage.setItem("darkTheme", dark);
}

toggleBtn.addEventListener("click", () => {
  const isDark = document.body.classList.contains("dark");
  setTheme(!isDark);
});

// Inicializa tema salvo
setTheme(localStorage.getItem("darkTheme") === "true");


