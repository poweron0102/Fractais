import os

import pygame as pg
from numba import njit
import numpy as np

from typing import NewType

Image = NewType('Image', np.ndarray[np.uint8])  # Uma imagem completa
Fragment = NewType('Fragment', np.ndarray[np.uint8])  # Um único fragmento (ex: 16x16x3)
FragmentGrid = NewType('FragmentGrid', np.ndarray[np.uint8])  # Grid de fragmentos: (N, M, 16, 16, 3)


@njit
def get_fragmentos(img: Image, fragmentos_size: int) -> FragmentGrid:
    """
    Extracts the fragmentos from the image.
    :param img: The image to extract the fragmentos from.
    :param fragmentos_size: The size of the fragmentos.
    :return: The fragmentos.
    """

    height, width, _ = img.shape
    kernels = np.zeros(
        (height // fragmentos_size, width // fragmentos_size, fragmentos_size, fragmentos_size, 3),
        dtype=np.uint8
    )

    for i in range(0, height - fragmentos_size + 1, fragmentos_size):
        for j in range(0, width - fragmentos_size + 1, fragmentos_size):
            kernels[i // fragmentos_size][j // fragmentos_size] = img[i:i + fragmentos_size, j:j + fragmentos_size]

    return kernels

def save_fragmentos(fragmentos: np.ndarray, output_dir: str):

def save_fragmentos(fragmentos: FragmentGrid, output_dir: str):
    """
    Saves the fragmentos to the output directory.
    :param fragmentos: The kernels to save.
    :param output_dir: The output directory.
    """

    # create the folder if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    for i in range(fragmentos.shape[0]):
        for j in range(fragmentos.shape[1]):
            kernel = fragmentos[i][j]
            filename = f"{output_dir}/fragmentos_{i}_{j}.png"
            pg.image.save(pg.surfarray.make_surface(kernel), filename)


@njit
def img_from_fragmentos(fragmentos: FragmentGrid) -> Image:
    """
    Reconstructs the image from the fragmentos.
    :param fragmentos: The fragmentos to reconstruct the image from.
    :return: The reconstructed image.
    """
    height, width, fragmentos_size, _, _ = fragmentos.shape
    img = np.zeros((height * fragmentos_size, width * fragmentos_size, 3), dtype=np.uint8)

    for i in range(height):
        for j in range(width):
            img[i * fragmentos_size:(i + 1) * fragmentos_size, j * fragmentos_size:(j + 1) * fragmentos_size] = \
                fragmentos[i][j]

    return img


# @njit
# def iter_fragmentos(fragmentos: FragmentGrid) -> Fragment:
#     """
#     Iterates over the fragmentos.
#     :param fragmentos: The fragmentos to iterate over.
#     :return: The iterator.
#     """
#
#     for i in range(fragmentos.shape[0]):
#         for j in range(fragmentos.shape[1]):
#             yield fragmentos[i][j]
