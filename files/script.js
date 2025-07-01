/**
 * @file script.js
 * @description Lógica principal para a interface do Editor de Mosaico com IA.
 * Organizado em um objeto 'MosaicEditor' para encapsular estado, elementos DOM e funcionalidades.
 */

document.addEventListener("DOMContentLoaded", () => {
  /**
   * @namespace MosaicEditor
   * @description Objeto principal que encapsula toda a lógica da aplicação.
   */
  const MosaicEditor = {
    /**
     * @property {object} state - Armazena o estado dinâmico da aplicação, como os arquivos de imagem.
     */
    state: {
      receptora: { file: null },
      doadora: { file: null }
    },

    /**
     * @property {object} elements - Cache dos elementos DOM para evitar consultas repetidas.
     */
    elements: {},

    /**
     * Inicializa a aplicação, buscando elementos DOM e vinculando eventos.
     */
    init() {
      this.cacheDomElements();
      this.bindEvents();
      this.initializeTheme();
    },

    /**
     * Busca todos os elementos DOM necessários e os armazena no objeto `elements`.
     */
    cacheDomElements() {
      this.elements = {
        // Painéis
        body: document.body,
        // Previews e Inputs de Imagem
        receptoraPreview: document.getElementById("receptoraPreview"),
        doadoraPreview: document.getElementById("doadoraPreview"),
        receptoraInput: document.getElementById("receptora"),
        doadoraInput: document.getElementById("doadora"),
        receptoraDim: document.querySelector("#receptoraPreview .image-dimension-display"),
        doadoraDim: document.querySelector("#doadoraPreview .image-dimension-display"),
        previewImg: document.getElementById("preview"),
        // Botões de Ferramentas
        btnResizeReceptora: document.getElementById('resize-receptora'),
        btnResizeDoadora: document.getElementById('resize-doadora'),
        btnGrayscaleReceptora: document.getElementById('grayscale-receptora'),
        btnGrayscaleDoadora: document.getElementById('grayscale-doadora'),
        btnMatchColorReceptora: document.getElementById('match-color-receptora'),
        btnMatchColorDoadora: document.getElementById('match-color-doadora'),
        // Parâmetros
        tamanhoInput: document.getElementById("tamanho"),
        yuvCheckbox: document.getElementById("yuv"),
        pesoDifImagensSlider: document.getElementById("peso_dif_imagens"), // Renomeado
        pesoVggSlider: document.getElementById("peso_vgg"),
        pesoSobelSlider: document.getElementById("peso_sobel"),
        pesoMediaCorSlider: document.getElementById("peso_media_cor"), // Novo slider
        pesoDifImagensValue: document.getElementById("pesoDifImagensValue"), // Renomeado
        pesoVggValue: document.getElementById("pesoVggValue"),
        pesoSobelValue: document.getElementById("pesoSobelValue"),
        pesoMediaCorValue: document.getElementById("pesoMediaCorValue"), // Novo valor de exibição
        // Botões Principais
        updateBtn: document.getElementById("updateBtn"),
        toggleThemeBtn: document.getElementById("toggleThemeBtn")
      };
    },

    /**
     * Centraliza a vinculação de todos os ouvintes de eventos.
     */
    bindEvents() {
      // Inputs de imagem (clique, arrastar e soltar)
      this.setupImageSlot('receptora');
      this.setupImageSlot('doadora');

      // Sliders de parâmetros
      this.setupWeightSliders();

      // Botões de ferramentas
      this.elements.btnResizeReceptora.addEventListener('click', () => this.tools.resize('receptora', 'doadora'));
      this.elements.btnResizeDoadora.addEventListener('click', () => this.tools.resize('doadora', 'receptora'));
      this.elements.btnGrayscaleReceptora.addEventListener('click', () => this.tools.grayscale('receptora'));
      this.elements.btnGrayscaleDoadora.addEventListener('click', () => this.tools.grayscale('doadora'));
      this.elements.btnMatchColorReceptora.addEventListener('click', () => this.tools.matchColor('receptora', 'doadora'));
      this.elements.btnMatchColorDoadora.addEventListener('click', () => this.tools.matchColor('doadora', 'receptora'));

      // Botões de ação principal
      this.elements.updateBtn.addEventListener("click", this.handleUpdate.bind(this));
      this.elements.toggleThemeBtn.addEventListener("click", () => this.setTheme(!this.elements.body.classList.contains("dark")));
    },

    /**
     * Configura um slot de imagem (receptora ou doadora) para aceitar arquivos via
     * clique ou arrastar e soltar (drag and drop).
     * @param {'receptora'|'doadora'} slot - O nome do slot a ser configurado.
     */
    setupImageSlot(slot) {
        const previewEl = this.elements[`${slot}Preview`];
        const inputEl = this.elements[`${slot}Input`];

        previewEl.addEventListener("click", () => inputEl.click());
        inputEl.addEventListener("change", (event) => {
            const file = event.target.files[0];
            if (file) this.updateImageState(slot, file);
        });

        previewEl.addEventListener("dragover", (e) => {
            e.preventDefault();
            previewEl.classList.add("dragover");
        });
        previewEl.addEventListener("dragleave", () => previewEl.classList.remove("dragover"));
        previewEl.addEventListener("drop", (e) => {
            e.preventDefault();
            previewEl.classList.remove("dragover");
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith("image/")) {
                inputEl.files = e.dataTransfer.files;
                this.updateImageState(slot, file);
            }
        });
    },

    /**
     * Configura os sliders de peso para atualizar seus valores de exibição de forma independente.
     */
    setupWeightSliders() {
        const {
            pesoDifImagensSlider, pesoVggSlider, pesoSobelSlider, pesoMediaCorSlider, // Adicionado pesoMediaCorSlider
            pesoDifImagensValue, pesoVggValue, pesoSobelValue, pesoMediaCorValue // Adicionado pesoMediaCorValue
        } = this.elements;

        const setupSlider = (slider, display) => {
            slider.addEventListener('input', () => {
                display.textContent = parseFloat(slider.value).toFixed(1);
            });
        };

        setupSlider(pesoDifImagensSlider, pesoDifImagensValue);
        setupSlider(pesoVggSlider, pesoVggValue);
        setupSlider(pesoSobelSlider, pesoSobelValue);
        setupSlider(pesoMediaCorSlider, pesoMediaCorValue); // Configurar novo slider
    },

    /**
     * Atualiza o estado e o preview de um slot de imagem.
     * @param {'receptora'|'doadora'} slot - O slot da imagem.
     * @param {File} file - O arquivo de imagem.
     */
    async updateImageState(slot, file) {
        this.state[slot].file = file;
        const previewEl = this.elements[`${slot}Preview`];
        previewEl.style.backgroundImage = `url(${URL.createObjectURL(file)})`;

        try {
            const img = await this.helpers.fileToImage(file);
            const dimDisplay = this.elements[`${slot}Dim`];
            const dimensions = `${img.width}x${img.height}`;
            previewEl.title = `Dimensões: ${dimensions}`;
            dimDisplay.textContent = dimensions;
        } catch (error) {
            console.error("Erro ao ler dimensões da imagem:", error);
        }
    },

    /**
     * Substitui o arquivo e o preview de um slot com um novo blob de imagem gerado.
     * @param {'receptora'|'doadora'} slot - O slot a ser atualizado.
     * @param {Blob} blob - O novo blob de imagem.
     */
    updateImageFromBlob(slot, blob) {
        const originalFile = this.state[slot].file;
        const newFile = new File([blob], originalFile.name, { type: 'image/png', lastModified: Date.now() });
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(newFile);
        this.elements[`${slot}Input`].files = dataTransfer.files;
        this.updateImageState(slot, newFile);
    },

    // --- Lógica de Ferramentas ---
    tools: {
      async resize(sourceSlot, targetSlot) {
        const sourceFile = MosaicEditor.state[sourceSlot].file;
        const targetFile = MosaicEditor.state[targetSlot].file;
        if (!sourceFile || !targetFile) {
          alert("Ambas as imagens devem ser selecionadas.");
          return;
        }
        const [sourceImg, targetImg] = await Promise.all([
          MosaicEditor.helpers.fileToImage(sourceFile),
          MosaicEditor.helpers.fileToImage(targetFile)
        ]);
        const canvas = MosaicEditor.helpers.createCanvas(targetImg.width, targetImg.height);
        canvas.getContext('2d').drawImage(sourceImg, 0, 0, targetImg.width, targetImg.height);
        const blob = await MosaicEditor.helpers.canvasToBlob(canvas);
        MosaicEditor.updateImageFromBlob(sourceSlot, blob);
      },
      async grayscale(slot) {
        const file = MosaicEditor.state[slot].file;
        if (!file) return;
        const img = await MosaicEditor.helpers.fileToImage(file);
        const canvas = MosaicEditor.helpers.createCanvas(img.width, img.height);
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        for (let i = 0; i < data.length; i += 4) {
          const avg = (data[i] + data[i + 1] + data[i + 2]) / 3;
          data[i] = data[i + 1] = data[i + 2] = avg;
        }
        ctx.putImageData(imageData, 0, 0);
        const blob = await MosaicEditor.helpers.canvasToBlob(canvas);
        MosaicEditor.updateImageFromBlob(slot, blob);
      },
      async matchColor(sourceSlot, targetSlot) {
          const sourceFile = MosaicEditor.state[sourceSlot].file;
          const targetFile = MosaicEditor.state[targetSlot].file;
          if (!sourceFile || !targetFile) {
              alert("Ambas as imagens devem ser selecionadas.");
              return;
          }
          const [sourceImg, targetImg] = await Promise.all([
              MosaicEditor.helpers.fileToImage(sourceFile),
              MosaicEditor.helpers.fileToImage(targetFile)
          ]);
          const sourceHist = MosaicEditor.helpers._getHistogram(sourceImg);
          const targetHist = MosaicEditor.helpers._getHistogram(targetImg);
          const sourceCDF = MosaicEditor.helpers._getCDF(sourceHist);
          const targetCDF = MosaicEditor.helpers._getCDF(targetHist);
          const lut = MosaicEditor.helpers._createLUT(sourceCDF, targetCDF);
          const canvas = MosaicEditor.helpers.createCanvas(sourceImg.width, sourceImg.height);
          const ctx = canvas.getContext('2d');
          ctx.drawImage(sourceImg, 0, 0);
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const data = imageData.data;
          for (let i = 0; i < data.length; i += 4) {
              data[i] = lut[0][data[i]];
              data[i + 1] = lut[1][data[i + 1]];
              data[i + 2] = lut[2][data[i + 2]];
          }
          ctx.putImageData(imageData, 0, 0);
          const blob = await MosaicEditor.helpers.canvasToBlob(canvas);
          MosaicEditor.updateImageFromBlob(sourceSlot, blob);
      }
    },

    // --- Funções de Ajuda (Helpers) ---
    helpers: {
      fileToImage: (file) => new Promise((resolve, reject) => {
        const img = new Image();
        const url = URL.createObjectURL(file);
        img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
        img.onerror = (err) => { URL.revokeObjectURL(url); reject(err); };
        img.src = url;
      }),
      canvasToBlob: (canvas) => new Promise(resolve => canvas.toBlob(resolve, 'image/png')),
      createCanvas: (width, height) => {
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        return canvas;
      },
      _getHistogram(img) {
          const canvas = this.createCanvas(img.width, img.height);
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0);
          const imageData = ctx.getImageData(0, 0, img.width, img.height).data;
          const hist = [new Array(256).fill(0), new Array(256).fill(0), new Array(256).fill(0)];
          for (let i = 0; i < imageData.length; i += 4) {
              hist[0][imageData[i]]++;
              hist[1][imageData[i+1]]++;
              hist[2][imageData[i+2]]++;
          }
          return hist;
      },
      _getCDF(hist) {
          const cdf = [new Array(256), new Array(256), new Array(256)];
          for (let c = 0; c < 3; c++) {
              let sum = 0;
              for (let i = 0; i < 256; i++) {
                  sum += hist[c][i];
                  cdf[c][i] = sum;
              }
              const total = cdf[c][255];
              for (let i = 0; i < 256; i++) {
                  cdf[c][i] = Math.round(255 * cdf[c][i] / total);
              }
          }
          return cdf;
      },
      _createLUT(sourceCDF, targetCDF) {
          const lut = [new Array(256), new Array(256), new Array(256)];
          for (let c = 0; c < 3; c++) {
              let j = 0;
              for (let i = 0; i < 256; i++) {
                  while (j < 255 && targetCDF[c][j] < sourceCDF[c][i]) {
                      j++;
                  }
                  lut[c][i] = j;
              }
          }
          return lut;
      }
    },

    // --- Ações Principais ---
    handleUpdate() {
        if (!this._validateUpdate()) return;
        const formData = this._buildFormData();
        const startTime = Date.now();
        this.elements.updateBtn.disabled = true;
        this.elements.updateBtn.textContent = "Processando...";

        fetch("/update", { method: "POST", body: formData })
        .then(response => {
            if (!response.ok) throw new Error(`Erro na rede: ${response.statusText}`);
            return response.json();
        })
        .then(data => {
            console.log("Resposta do backend:", data);
            const elapsedTime = ((Date.now() - startTime) / 1000).toFixed(2);
            this.elements.previewImg.src = `preview.png?t=${new Date().getTime()}`;
            new Audio("/notification.mp3").play();
            alert(`Atualização concluída! Tempo: ${Math.floor(elapsedTime / 60)}m ${Math.round(elapsedTime % 60)}s.`);
        })
        .catch(error => {
            console.error("Erro ao enviar dados:", error);
            alert(`Ocorreu um erro: ${error.message}.`);
        })
        .finally(() => {
            this.elements.updateBtn.disabled = false;
            this.elements.updateBtn.textContent = "Update";
        });
    },

    _validateUpdate() {
      if (!this.state.receptora.file || !this.state.doadora.file) {
        alert("Por favor, selecione ambas as imagens.");
        return false;
      }
      return true;
    },

    _buildFormData() {
      const formData = new FormData();
      formData.append("receptora", this.state.receptora.file);
      formData.append("doadora", this.state.doadora.file);
      formData.append("tamanho", this.elements.tamanhoInput.value);
      formData.append("yuv", this.elements.yuvCheckbox.checked);
      formData.append("peso_dif_imagens", this.elements.pesoDifImagensSlider.value); // Renomeado
      formData.append("peso_vgg", this.elements.pesoVggSlider.value);
      formData.append("peso_sobel", this.elements.pesoSobelSlider.value);
      formData.append("peso_media_cor", this.elements.pesoMediaCorSlider.value); // Adicionado novo peso
      return formData;
    },

    // --- Tema ---
    setTheme(isDark) {
        this.elements.body.classList.toggle("dark", isDark);
        this.elements.toggleThemeBtn.textContent = isDark ? "☀️ Modo Claro" : "🌙 Modo Escuro";
        localStorage.setItem("darkTheme", isDark);
    },

    initializeTheme() {
        const savedTheme = localStorage.getItem("darkTheme") === "true";
        this.setTheme(savedTheme);
    }
  };

  MosaicEditor.init();
});