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

  const formData = new FormData();

  // Adiciona arquivos
  if (receptoraInput.files[0]) {
    formData.append("receptora", receptoraInput.files[0]);
  }

  if (doadoraInput.files[0]) {
    formData.append("doadora", doadoraInput.files[0]);
  }

  // Adiciona parâmetros
  formData.append("tamanho", document.getElementById("tamanho").value);
  formData.append("diferenca_absoluta", document.getElementById("diferenca").value);
  formData.append("bordas", document.getElementById("bordas").value);
  formData.append("media_cores", document.getElementById("media").value);

  // Envia para o backend
  fetch("/update", {
    method: "POST",
    body: formData
  })
    .then(response => response.json())
    .then(data => {
      console.log("Resposta do backend:", data);

        // Atualiza a imagem na página
        const preview = document.getElementById("preview");
        preview.src = "preview.png"+ "?t=" + new Date().getTime(); // Adiciona um timestamp para evitar cache


    })
    .catch(error => {
      console.error("Erro ao enviar dados:", error);
    });
});
