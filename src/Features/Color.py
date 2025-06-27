import numpy as np
from numba import njit
from scipy.optimize import linear_sum_assignment

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
    # diff = np.abs(img1 - img2)
    diff = np.abs(img1.astype(np.int32) - img2.astype(np.int32))

    # Calculate the similarity
    similarity = 1 - np.sum(diff) / (img1.shape[0] * img1.shape[1] * 3 * 255)
    return similarity





