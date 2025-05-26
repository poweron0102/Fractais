import io
import os
from typing import NewType

import numpy as np
from numba import njit
from PIL import Image
from fastapi import UploadFile

ImageType = NewType('ImageType', np.ndarray[np.uint8])  # Uma imagem completa
Fragment = NewType('Fragment', np.ndarray[np.uint8])  # Um único fragmento (ex: 16x16x3)
FragmentGrid = NewType('FragmentGrid', np.ndarray[np.uint8])  # Grid de fragmentos: (N, M, 16, 16, 3)


def LoadImage(img_path: str) -> ImageType:
    """
    Loads an image from the given path using Pillow.
    :param img_path: The path to the image.
    :return: The loaded image as a numpy array.
    """
    with Image.open(img_path) as img:
        img = img.convert('RGB')
        return np.array(img)


def FromWeb(img: UploadFile) -> ImageType:
    """
    Converts an image from a web upload to a numpy array using Pillow.
    :param img: The image to convert.
    :return: The converted image as a numpy array.
    """
    image_data = io.BytesIO(img.file.read())
    with Image.open(image_data) as img:
        img = img.convert('RGB')
        return np.array(img)


def SaveImage(img: ImageType, output_path: str):
    """
    Saves the image to the given path using Pillow.
    :param img: The image to save as a numpy array.
    :param output_path: The path to save the image to.
    """
    Image.fromarray(img).save(output_path)


@njit
def get_fragmentos(img: ImageType, fragmentos_size: int) -> FragmentGrid:
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


def save_fragmentos(fragmentos: FragmentGrid, output_dir: str):
    """
    Saves the fragmentos to the output directory using Pillow.
    :param fragmentos: The kernels to save.
    :param output_dir: The output directory.
    """
    os.makedirs(output_dir, exist_ok=True)

    for i in range(fragmentos.shape[0]):
        for j in range(fragmentos.shape[1]):
            kernel = fragmentos[i][j]
            filename = f"{output_dir}/fragmentos_{i}_{j}.png"
            Image.fromarray(kernel).save(filename)


@njit
def img_from_fragmentos(fragmentos: FragmentGrid) -> ImageType:
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