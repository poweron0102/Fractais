import numpy as np
from numba import njit
from scipy.optimize import linear_sum_assignment

from Fragmentos import Image, FragmentGrid, Fragment


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
def comp_imgs(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Compares two images.
    :param img1: The first image.
    :param img2: The second image.
    :return: The similarity between the two images.
    """
    # Calculate the difference between the two images
    diff = np.abs(img1 - img2)

    # Calculate the similarity
    similarity = 1 - np.sum(diff) / (img1.shape[0] * img1.shape[1] * 3 * 255)
    return similarity


def replace(fragmentos_1: FragmentGrid, fragmentos_2: FragmentGrid, yuv: bool = False) -> Image:
    """
    Substitui cada fragmento de fragmentos_1 pelo fragmento mais semelhante (sem repetições)
    usando emparelhamento ótimo via Hungarian Algorithm.
    """
    h, w, fh, fw, _ = fragmentos_1.shape
    n = h * w

    # Achata os grids
    frag1_flat = fragmentos_1.reshape((n, fh, fw, 3))
    frag2_flat = fragmentos_2.reshape((n, fh, fw, 3))

    if yuv:
        frag1_flat = np.array([covert_to_YUV(f) for f in frag1_flat])
        frag2_flat_proc = np.array([covert_to_YUV(f) for f in frag2_flat])
    else:
        frag2_flat_proc = frag2_flat

    # Monta matriz de custo (n x n)
    cost_matrix = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        for j in range(n):
            cost_matrix[i, j] = 1.0 - comp_imgs(frag1_flat[i], frag2_flat_proc[j])  # erro = 1 - similaridade

    # Resolve o problema de atribuição
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    # Reconstrói imagem com os melhores fragmentos únicos
    output = np.zeros((h * fh, w * fw, 3), dtype=np.uint8)
    for idx, frag_idx in zip(row_ind, col_ind):
        i, j = divmod(idx, w)
        output[i*fh:(i+1)*fh, j*fw:(j+1)*fw] = frag2_flat[frag_idx]

    return output


