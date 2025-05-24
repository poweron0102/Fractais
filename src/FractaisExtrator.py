import os

import pygame as pg
from numba import njit
import numpy as np


@njit
def get_kernels(img: np.ndarray, kernel_size: int) -> np.ndarray:
    """
    Extracts the kernels from the image.
    :param img: The image to extract the kernels from.
    :param kernel_size: The size of the kernels.
    :return: The kernels.
    """
    height, width, _ = img.shape
    kernels = np.zeros((height // kernel_size, width // kernel_size, kernel_size, kernel_size, 3), dtype=np.uint8)

    for i in range(0, height - kernel_size + 1, kernel_size):
        for j in range(0, width - kernel_size + 1, kernel_size):
            kernels[i // kernel_size][j // kernel_size] = img[i:i + kernel_size, j:j + kernel_size]

    return kernels


def save_kernels(kernels: np.ndarray, output_dir: str):
    """
    Saves the kernels to the output directory.
    :param kernels: The kernels to save.
    :param kernel_size: The size of the kernels.
    :param output_dir: The output directory.
    """
    # create the folder if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    for i in range(kernels.shape[0]):
        for j in range(kernels.shape[1]):
            kernel = kernels[i][j]
            filename = f"{output_dir}/kernel_{i}_{j}.png"
            pg.image.save(pg.surfarray.make_surface(kernel), filename)
