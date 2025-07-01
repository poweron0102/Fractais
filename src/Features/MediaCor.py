from numba import float32, njit, cuda
import numpy as np


@njit
def comp_imgs_media_cor(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Compara a similaridade entre duas imagens com base na diferença de suas médias de cor.
    :param img1: A primeira imagem.
    :param img2: A segunda imagem.
    :return: A similaridade entre as duas imagens (0 a 1).
    """
    # Calcula a média de cor para cada canal (RGB) para ambas as imagens
    media1 = np.mean(img1.astype(np.float32), axis=(0, 1))
    media2 = np.mean(img2.astype(np.float32), axis=(0, 1))

    # Calcula a diferença absoluta entre as médias de cor
    diff_medias = np.abs(media1 - media2)

    # A diferença máxima possível para cada canal é 255
    max_diff_channel = 255.0

    # Normaliza a soma das diferenças das médias para obter uma medida de similaridade
    # Soma das diferenças (ex: R_diff + G_diff + B_diff)
    sum_diff_medias = np.sum(diff_medias)

    # O valor máximo possível para a soma das diferenças das médias é 3 * 255
    max_total_diff = 3 * max_diff_channel

    # A similaridade é 1 menos a proporção da diferença total
    similarity = 1.0 - (sum_diff_medias / max_total_diff)

    return similarity

@cuda.jit(device=True)
def cu_comp_imgs_media_cor(img1, img2):
    """
    Compara a similaridade entre duas imagens na GPU com base na diferença de suas médias de cor.
    Esta é uma 'device function'.
    :param img1: A primeira imagem (um fragmento 3D).
    :param img2: A segunda imagem (um fragmento 3D).
    :return: A similaridade entre as duas imagens.
    """
    height, width, channels = img1.shape

    # Acumuladores para as somas dos canais de cor
    sum1_r = 0.0
    sum1_g = 0.0
    sum1_b = 0.0
    sum2_r = 0.0
    sum2_g = 0.0
    sum2_b = 0.0

    num_pixels = float32(height * width)

    for y in range(height):
        for x in range(width):
            sum1_r += float32(img1[y, x, 0])
            sum1_g += float32(img1[y, x, 1])
            sum1_b += float32(img1[y, x, 2])

            sum2_r += float32(img2[y, x, 0])
            sum2_g += float32(img2[y, x, 1])
            sum2_b += float32(img2[y, x, 2])

    # Calcular as médias
    media1_r = sum1_r / num_pixels
    media1_g = sum1_g / num_pixels
    media1_b = sum1_b / num_pixels

    media2_r = sum2_r / num_pixels
    media2_g = sum2_g / num_pixels
    media2_b = sum2_b / num_pixels

    # Calcular a diferença absoluta entre as médias dos canais
    diff_r = abs(media1_r - media2_r)
    diff_g = abs(media1_g - media2_g)
    diff_b = abs(media1_b - media2_b)

    # Somar as diferenças e normalizar
    total_diff_medias = diff_r + diff_g + diff_b
    max_total_diff = float32(3.0 * 255.0) # 3 canais * 255 (diferença máxima por canal)

    similarity = 1.0 - (total_diff_medias / max_total_diff)
    return similarity
