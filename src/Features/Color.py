import numpy as np
from numba import njit

from src.Fragmentos import Image, FragmentGrid, Fragment


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


@njit
def replace(fragmentos_1: FragmentGrid, fragmentos_2: FragmentGrid, yuv: bool = False) -> Image:
    """
    Substitui cada fragmento de fragmentos_1 pelo fragmento mais semelhante de fragmentos_2.
    :param fragmentos_1: Fragmentos da imagem A.
    :param fragmentos_2: Fragmentos da imagem B.
    :param yuv: Se True, usa o espaço de cor YUV para comparar.
    :return: A nova imagem reconstruída.
    """
    h, w, fh, fw, _ = fragmentos_1.shape
    output = np.zeros((h * fh, w * fw, 3), dtype=np.uint8)

    # Pré-processa fragmentos_2 (em YUV se necessário)
    f2_proc = np.empty_like(fragmentos_2)
    for i in range(h):
        for j in range(w):
            f2_proc[i, j] = covert_to_YUV(fragmentos_2[i, j]) if yuv else fragmentos_2[i, j]

    for i in range(h):
        for j in range(w):
            frag1 = fragmentos_1[i, j]
            frag1_proc = covert_to_YUV(frag1) if yuv else frag1

            best_sim = -1.0
            best_match = fragmentos_2[0, 0]

            for m in range(h):
                for n in range(w):
                    frag2_proc = f2_proc[m, n]
                    sim = comp_imgs(frag1_proc, frag2_proc)
                    if sim > best_sim:
                        best_sim = sim
                        best_match = fragmentos_2[m, n]

            output[i*fh:(i+1)*fh, j*fw:(j+1)*fw] = best_match

    return output


