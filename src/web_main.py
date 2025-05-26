import os
import shutil
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from src.Fragmentos import get_fragmentos, SaveImage, LoadImage
from src.Features.Color import replace

# import pygame as pg

# pg.init()
# screen = pg.display.set_mode((1, 1), pg.NOFRAME)

app = FastAPI()

# Permite acesso do frontend local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# ----------- ROTEAMENTO DE ARQUIVOS -----------

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
        diferenca_absoluta: int = Form(...),
        bordas: int = Form(...),
        media_cores: int = Form(...)
):
    print("Recebendo parâmetros...")
    print(f"""
    YUV: {yuv}
    Tamanho: {tamanho}
    Diferenca Absoluta: {diferenca_absoluta}
    Bordas: {bordas}
    Media Cores: {media_cores}
    """)

    # Verifica se o diretório de uploads existe, caso contrário, cria
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    # Salva imagens recebidas
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
        img_1 = LoadImage(f"uploads/{receptora.filename}")
        img_2 = LoadImage(f"uploads/{doadora.filename}")

        fragmentos_1 = get_fragmentos(img_1, tamanho)
        fragmentos_2 = get_fragmentos(img_2, tamanho)

        replaced_img = replace(fragmentos_1, fragmentos_2, yuv=yuv)

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
