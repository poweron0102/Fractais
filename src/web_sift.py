import os
import shutil
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
import cv2
import numpy as np

from src.Features.Dif import replace
from src.Fragmentos import SaveImage, get_fragmentos, LoadImage


def replace_with_sift(receptora_img, doadora_img, fragmentos_receptora):
    """
    Substitui fragmentos da imagem receptora por fragmentos correspondentes
    da imagem doadora, alinhados usando SIFT e homografia.

    Args:
        receptora_img (np.array): A imagem que receberá os fragmentos.
        doadora_img (np.array): A imagem que fornecerá os fragmentos.
        fragmentos_receptora (list): Lista de objetos de fragmento da imagem receptora.
        min_match_count (int): Número mínimo de correspondências para calcular a homografia.

    Returns:
        np.array: A imagem receptora modificada.
    """
    print("Iniciando substituição com SIFT...")
    sift = cv2.SIFT_create()

    gray_r = cv2.cvtColor(receptora_img, cv2.COLOR_BGR2GRAY)
    gray_d = cv2.cvtColor(doadora_img, cv2.COLOR_BGR2GRAY)
    kp_r, des_r = sift.detectAndCompute(gray_r, None)
    kp_d, des_d = sift.detectAndCompute(gray_d, None)

    if des_r is None or des_d is None:
        print("Não foi possível encontrar descritores em uma ou ambas as imagens.")
        return receptora_img

    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des_r, des_d, k=2)

    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

    print(f"Encontrados {len(good_matches)} bons matches.")

    src_pts = np.float32([kp_r[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp_d[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)

    if H is None:
        print("Não foi possível calcular a homografia.")
        return receptora_img

    h, w, _ = receptora_img.shape
    doadora_warped = cv2.warpPerspective(doadora_img, H, (w, h))

    output_img = receptora_img.copy()

    for frag in fragmentos_receptora:
        x, y, tamanho = frag.x, frag.y, frag.tamanho
        output_img[y:y + tamanho, x:x + tamanho] = doadora_warped[y:y + tamanho, x:x + tamanho]

    print("Substituição com SIFT concluída.")

    # Salva uma imagem de depuração com as correspondências desenhadas
    matched_img = cv2.drawMatches(
        receptora_img,
        kp_r,
        doadora_warped,
        kp_d,
        good_matches,
        None,
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
    )
    SaveImage(matched_img, "imgs/matches.png")

    return output_img


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
    if os.path.exists("files/index.html"):
        return FileResponse("files/index.html")
    return HTMLResponse("<h1>Erro: files/index.html não encontrado.</h1>")


@app.get("/style.css")
async def css():
    if os.path.exists("files/style.css"):
        return FileResponse("files/style.css")
    return HTMLResponse("/* Erro: files/style.css não encontrado */", media_type="text/css")


@app.get("/script.js")
async def js():
    if os.path.exists("files/script.js"):
        return FileResponse("files/script.js")
    return HTMLResponse("console.error('Erro: files/script.js não encontrado');", media_type="application/javascript")


@app.get("/favicon.ico")
async def favicon():
    if os.path.exists("files/favicon.png"):
        return FileResponse("files/favicon.png")
    return {"error": "Favicon não encontrado"}


# ----------- API /update -----------

@app.post("/update")
async def update(
        receptora: Optional[UploadFile] = File(None),
        doadora: Optional[UploadFile] = File(None),
        method: str = Form(...),
        yuv: bool = Form(True),
        tamanho: int = Form(...),
        diferenca_absoluta: int = Form(...),
        bordas: int = Form(...),
        media_cores: int = Form(...)
):
    print("Recebendo parâmetros...")
    print(f"""
    Método: {method}
    Tamanho do Fragmento: {tamanho}
    --- Parâmetros (Cor) ---
    YUV: {yuv}
    Diferenca Absoluta: {diferenca_absoluta}
    Bordas: {bordas}
    Media Cores: {media_cores}
    """)

    # Cria os diretórios necessários se não existirem
    for dir_path in ["uploads", "imgs"]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    path_r, path_d = None, None
    # Salva as imagens recebidas
    if receptora and receptora.filename:
        path_r = f"uploads/{receptora.filename}"
        with open(path_r, "wb") as f:
            shutil.copyfileobj(receptora.file, f)

    if doadora and doadora.filename:
        path_d = f"uploads/{doadora.filename}"
        with open(path_d, "wb") as f:
            shutil.copyfileobj(doadora.file, f)

    if path_r and path_d:
        print("Processando imagens...")
        img_1 = LoadImage(path_r)
        img_2 = LoadImage(path_d)

        if img_1 is None or img_2 is None:
            return {"status": "error", "msg": "Não foi possível carregar uma ou ambas as imagens."}

        fragmentos_1 = get_fragmentos(img_1, tamanho)

        replaced_img = None
        # Escolhe o método de processamento com base no parâmetro 'method'
        if method == 'color':
            print("Usando método de substituição por cor.")
            fragmentos_2 = get_fragmentos(img_2, tamanho)
            replaced_img = replace(fragmentos_1, fragmentos_2, yuv=yuv)
        elif method == 'sift':
            print("Usando método de substituição por feature matching (SIFT).")
            replaced_img = replace_with_sift(img_1, img_2, fragmentos_1)
        else:
            return {"status": "error", "msg": f"Método de processamento '{method}' inválido."}

        if replaced_img is not None:
            SaveImage(replaced_img, "imgs/preview.png")
            print("Imagens processadas e salvas.")
            return {"status": "ok", "msg": "Processamento concluído!"}
        else:
            return {"status": "error", "msg": "Falha no processamento da imagem."}

    return {"status": "error", "msg": "É necessário fazer o upload de ambas as imagens."}


# ----------- APIs de Visualização -----------

@app.get("/preview.png")
async def get_preview():
    preview_path = "imgs/preview.png"
    if os.path.exists(preview_path):
        return FileResponse(preview_path, media_type="image/png")
    return {"error": "Preview não encontrado"}


@app.get("/matches.png")
async def get_matches():
    """Endpoint para servir a imagem de depuração com as correspondências SIFT."""
    matches_path = "imgs/matches.png"
    if os.path.exists(matches_path):
        return FileResponse(matches_path, media_type="image/png")
    return {"error": "Imagem de matches não encontrada"}
