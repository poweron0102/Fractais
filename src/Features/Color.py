import numpy as np
from numba import njit, cuda, float32


@njit
def covert_to_YUV(img: np.ndarray) -> np.ndarray:
    """
    Converts the image to YUV color space.
    :param img: The image to convert.
    :return: The converted image.
    """
    # YUV conversion matrix
    yuv = np.zeros_like(img, dtype=np.uint8)
    yuv[..., 0] = 0.299 * img[..., 0] + 0.587 * img[..., 1] + 0.114 * img[..., 2]
    yuv[..., 1] = -0.14713 * img[..., 0] - 0.28886 * img[..., 1] + 0.436 * img[..., 2]
    yuv[..., 2] = 0.615 * img[..., 0] - 0.51499 * img[..., 1] - 0.10001 * img[..., 2]
    return yuv


@njit
def covert_to_RGB(yuv: np.ndarray) -> np.ndarray:
    """
    Converts the image from YUV to RGB color space.
    :param yuv: The image to convert.
    :return: The converted image.
    """
    # YUV conversion matrix
    rgb = np.zeros_like(yuv, dtype=np.uint8)
    rgb[..., 0] = yuv[..., 0] + 1.13983 * yuv[..., 2]
    rgb[..., 1] = yuv[..., 0] - 0.39465 * yuv[..., 1] - 0.58060 * yuv[..., 2]
    rgb[..., 2] = yuv[..., 0] + 2.03211 * yuv[..., 1]
    return rgb


@njit
def comp_imgs_dif(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Compares two images.
    :param img1: The first image.
    :param img2: The second image.
    :return: The similarity between the two images.
    """
    # Calculate the difference between the two images
    # diff = np.abs(img1 - img2)
    diff = np.abs(img1.astype(np.int32) - img2.astype(np.int32))

    # Calculate the similarity
    similarity = 1 - np.sum(diff) / (img1.shape[0] * img1.shape[1] * 3 * 255)
    return similarity


@cuda.jit(device=True)
def cu_comp_imgs_dif(img1, img2):
    """
    Compara duas imagens na GPU. Esta é uma 'device function'.
    :param img1: A primeira imagem (um fragmento 3D).
    :param img2: A segunda imagem (um fragmento 3D).
    :return: A similaridade entre as duas imagens.
    """
    # A forma (shape) da imagem é conhecida (ex: 64, 64, 3)
    height, width, channels = img1.shape

    # O valor máximo possível da soma das diferenças absolutas
    max_diff_sum = height * width * channels * 255.0

    # Acumulador para a soma das diferenças
    diff_sum = 0.0

    # Loop explícito, pois np.sum não é suportado da mesma forma em device functions
    for y in range(height):
        for x in range(width):
            for c in range(channels):
                # Usamos float32 para evitar overflow com uint8
                d = abs(float32(img1[y, x, c]) - float32(img2[y, x, c]))
                diff_sum += d

    # Calcula a similaridade
    similarity = 1.0 - (diff_sum / max_diff_sum)
    return similarity




