import cv2
import numpy as np


def remover_ruido_espectral(caminho_imagem_entrada: str, raio_corte: int):
    img = cv2.imread(caminho_imagem_entrada, cv2.IMREAD_GRAYSCALE)

    dft = np.fft.fft2(img.astype(float))
    dft_shift = np.fft.fftshift(dft)

    linhas, colunas = img.shape
    centro_linha, centro_coluna = linhas // 2, colunas // 2

    mascara = np.zeros((linhas, colunas), np.uint8)
    cv2.circle(mascara, (centro_coluna, centro_linha), raio_corte, 1, thickness=-1)

    dft_shift_filtrado = dft_shift * mascara

    f_ishift = np.fft.ifftshift(dft_shift_filtrado)
    img_reconstruida = np.fft.ifft2(f_ishift)
    img_reconstruida = np.abs(img_reconstruida)

    img_normalizada = cv2.normalize(img_reconstruida, None, 0, 255, cv2.NORM_MINMAX)
    img_final = img_normalizada.astype(np.uint8)

    cv2.imwrite("img_out.png", img_final)


entrada = input("Digite o caminho da imagem de entrada: ")
raio = int(input("Digite o raio do filtro passa-baixa circular: "))

remover_ruido_espectral(entrada, raio)
