document.addEventListener("DOMContentLoaded", () => {
  // --- Manipuladores de upload de imagem ---
  const receptoraInput = document.getElementById("receptora");
  const doadoraInput = document.getElementById("doadora");
  const receptoraPreview = document.getElementById("receptoraPreview");
  const doadoraPreview = document.getElementById("doadoraPreview");

  receptoraInput.addEventListener("change", (event) => {
    previewImage(event.target.files[0], "receptoraPreview");
  });

  doadoraInput.addEventListener("change", (event) => {
    previewImage(event.target.files[0], "doadoraPreview");
  });

  // Permite clicar na área de preview para selecionar o arquivo
  receptoraPreview.addEventListener("click", () => receptoraInput.click());
  doadoraPreview.addEventListener("click", () => doadoraInput.click());

  // --- Função de Preview da Imagem ---
  function previewImage(file, elementId) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const preview = document.getElementById(elementId);
      preview.style.backgroundImage = `url(${e.target.result})`;
    };
    reader.readAsDataURL(file);
  }

  // --- Lógica de Drag and Drop ---
  function setupDragAndDrop(previewId, inputId) {
    const dropZone = document.getElementById(previewId);
    const input = document.getElementById(inputId);

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
        input.files = e.dataTransfer.files; // Associa o arquivo ao input
        previewImage(file, previewId);
      }
    });
  }

  setupDragAndDrop("receptoraPreview", "receptora");
  setupDragAndDrop("doadoraPreview", "doadora");

  // --- Atualização dos valores dos sliders ---
  const pesoCorSlider = document.getElementById("peso_cor");
  const pesoVggSlider = document.getElementById("peso_vgg");
  const pesoCorValue = document.getElementById("pesoCorValue");
  const pesoVggValue = document.getElementById("pesoVggValue");

  pesoCorSlider.addEventListener("input", (e) => {
  const pesoCor = parseFloat(e.target.value);
  const pesoVgg = 1 - pesoCor;
  pesoCorValue.textContent = pesoCor.toFixed(1);
  pesoVggSlider.value = pesoVgg.toFixed(1);
  pesoVggValue.textContent = pesoVgg.toFixed(1);
});

pesoVggSlider.addEventListener("input", (e) => {
  const pesoVgg = parseFloat(e.target.value);
  const pesoCor = 1 - pesoVgg;
  pesoVggValue.textContent = pesoVgg.toFixed(1);
  pesoCorSlider.value = pesoCor.toFixed(1);
  pesoCorValue.textContent = pesoCor.toFixed(1);
});


  // --- Botão de Update ---
  const updateBtn = document.getElementById("updateBtn");
  updateBtn.addEventListener("click", () => {
    // Verifica se ambas as imagens foram selecionadas
    if (!receptoraInput.files[0] || !doadoraInput.files[0]) {
      alert("Por favor, selecione a imagem receptora e a doadora.");
      return;
    }

    const startTime = Date.now();
    updateBtn.disabled = true;
    updateBtn.textContent = "Processando...";

    const formData = new FormData();
    formData.append("receptora", receptoraInput.files[0]);
    formData.append("doadora", doadoraInput.files[0]);
    formData.append("tamanho", document.getElementById("tamanho").value);
    // Envia 'true' ou 'false' com base no estado do checkbox
    formData.append("yuv", document.getElementById("yuv").checked);
    // Envia os novos valores dos pesos
    formData.append("peso_cor", pesoCorSlider.value);
    formData.append("peso_vgg", pesoVggSlider.value);

    // Envia para o backend
    fetch("/update", {
      method: "POST",
      body: formData
    })
    .then(response => {
      if (!response.ok) {
          throw new Error(`Erro na rede: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      console.log("Resposta do backend:", data);
      const elapsedTime = ((Date.now() - startTime) / 1000).toFixed(2);

      // Atualiza a imagem de preview na página
      const preview = document.getElementById("preview");
      // Adiciona um timestamp para evitar o cache da imagem pelo navegador
      preview.src = `preview.png?t=${new Date().getTime()}`;

      // Toca um som de notificação
      const audio = new Audio("/notification.mp3");
      audio.play();

      // Exibe uma mensagem de sucesso
      alert(`Atualização concluída! Tempo gasto: ${Math.floor(elapsedTime / 60)}m ${Math.round(elapsedTime % 60)}s.`);
    })
    .catch(error => {
      console.error("Erro ao enviar dados:", error);
      alert(`Ocorreu um erro: ${error.message}. Verifique o console para mais detalhes.`);
    })
    .finally(() => {
        // Reabilita o botão após a conclusão
        updateBtn.disabled = false;
        updateBtn.textContent = "Update";
    });
  });

  // --- Tema Claro/Escuro ---
  const toggleBtn = document.getElementById("toggleThemeBtn");
  function setTheme(dark) {
    document.body.classList.toggle("dark", dark);
    toggleBtn.textContent = dark ? "☀️ Modo Claro" : "🌙 Modo Escuro";
    localStorage.setItem("darkTheme", dark ? "true" : "false");
  }

  toggleBtn.addEventListener("click", () => {
    const isDark = document.body.classList.contains("dark");
    setTheme(!isDark);
  });

  // Inicializa o tema salvo no localStorage
  setTheme(localStorage.getItem("darkTheme") === "true");
});
