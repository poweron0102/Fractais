import os
import shutil
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from src.Fragmentos import get_fragmentos, SaveImage, LoadImage
from src.Replace import replace

app = FastAPI()

# Permite acesso do frontend local (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# ----------- ROTEAMENTO DE ARQUIVOS ESTÁTICOS -----------

@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("files/index.html")


@app.get("/style.css")
async def css():
    return FileResponse("files/style.css")


@app.get("/script.js")
async def js():
    return FileResponse("files/script.js")


@app.get("/favicon.ico")
async def favicon():
    return FileResponse("files/favicon.png")


@app.get("/notification.mp3")
async def notification():
    return FileResponse("files/notification.mp3")


# ----------- API /update -----------

@app.post("/update")
async def update(
        receptora: Optional[UploadFile] = File(None),
        doadora: Optional[UploadFile] = File(None),
        yuv: bool = Form(True),
        tamanho: int = Form(...),
        # Novos parâmetros para os pesos da similaridade
        peso_dif_imagens: float = Form(...), # Renomeado
        peso_vgg: float = Form(...),
        peso_sobel: float = Form(...),
        peso_media_cor: float = Form(...) # Novo peso para média de cor
):
    # Normaliza os pesos para que a soma seja 1, garantindo uma ponderação consistente.
    total_peso = peso_dif_imagens + peso_vgg + peso_sobel + peso_media_cor
    if total_peso > 0:
        peso_dif_imagens_norm = peso_dif_imagens / total_peso
        peso_vgg_norm = peso_vgg / total_peso
        peso_sobel_norm = peso_sobel / total_peso
        peso_media_cor_norm = peso_media_cor / total_peso
    else:  # Caso de emergência para evitar divisão por zero
        peso_dif_imagens_norm = 1.0
        peso_vgg_norm = 0.0
        peso_sobel_norm = 0.0
        peso_media_cor_norm = 0.0

    weights = (peso_dif_imagens_norm, peso_vgg_norm, peso_sobel_norm, peso_media_cor_norm) # Tupla atualizada

    print("Recebendo parâmetros...")
    print(f"""
    YUV: {yuv}
    Tamanho do fragmento: {tamanho}
    Pesos Normalizados (Dif Imagens, VGG, Sobel, Média Cor): {weights}
    """)

    # Verifica se o diretório de uploads existe, caso contrário, cria
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    # Salva as imagens recebidas no servidor
    path_r, path_d = None, None
    if receptora:
        path_r = f"uploads/{receptora.filename}"
        with open(path_r, "wb") as f:
            shutil.copyfileobj(receptora.file, f)

    if doadora:
        path_d = f"uploads/{doadora.filename}"
        with open(path_d, "wb") as f:
            shutil.copyfileobj(doadora.file, f)

    if receptora and doadora:
        print("Processando imagens...")
        img_1 = LoadImage(path_r)
        img_2 = LoadImage(path_d)

        print("Dividindo imagens em fragmentos...")
        fragmentos_1 = get_fragmentos(img_1, tamanho)
        fragmentos_2 = get_fragmentos(img_2, tamanho)

        print("Iniciando a substituição de fragmentos...")
        replaced_img = replace(fragmentos_1, fragmentos_2, weights=weights, yuv=yuv)

        # Salva a imagem resultante para preview
        SaveImage(replaced_img, "imgs/preview.png")
        print("Imagens processadas e salvas.")

    return {"status": "ok", "msg": "Imagens e parâmetros recebidos"}


# ----------- API /preview -----------

@app.get("/preview.png")
async def get_preview():
    print("Enviando preview...")
    preview_path = "imgs/preview.png"
    if os.path.exists(preview_path):
        return FileResponse(preview_path, media_type="image/png")
    return {"error": "Preview não encontrado"}