import os

import numpy as np
import pygame as pg


from numba import njit
from Features.Color import replace, covert_to_YUV

def save_array_as_image(array: np.ndarray, output_dir: str, img_name: str = "img.png"):
    # create the folder if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    
    filename = f"{output_dir}/{img_name}"
    # img = pg.surfarray.make_surface(array)
    # pg.image.save(img, filename)
    pg.image.save(pg.surfarray.make_surface(array), filename)

# Gausian blur
def gaussian_blur(img: np.ndarray) -> np.ndarray:
    # OBS .: Acho que vai ter que dividir por 16 depois
    kernel = np.array([1, 2, 1], dtype=np.uint8)
    kernel = kernel / np.sum(kernel)
    height, width, _ = img.shape

    imgB = np.zeros((height + 2, width + 2, 3), dtype=np.uint8)
    imgB[1:height + 1, 1:width+1, :] = img
     
    for c in range(2): # for each color channel
        for i in range(1, height+1):
            for j in range(1, width+1):
                imgB[i, j] = (imgB[i, j-1] * kernel[0] + imgB[i, j] * kernel[1] + imgB[i, j+1] * kernel[2])
                imgB[i, j] = (imgB[i-1, j] * kernel[0] + imgB[i, j] * kernel[1] + imgB[i+1, j] * kernel[2])
    
    return imgB[1:height +1, 1:width+1]

# grayscale
def grayscale(img: np.ndarray) -> np.ndarray:
    img_yuv = covert_to_YUV(img)

    img_gray = np.zeros_like(img, dtype=np.uint8)

    img_gray[:, :, 0] = img_yuv[:, :, 0]
    img_gray[:, :, 1] = img_yuv[:, :, 0]
    img_gray[:, :, 2] = img_yuv[:, :, 0]

    return img_gray
# Sobel

@njit
def convolve(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    kernel_height, kernel_width = kernel.shape
    height, width, _ = img.shape

    img_convolved = np.zeros((height + 2, width + 2, 3), dtype=np.uint32)
    img_convolved2 = img_convolved.copy()
    img_convolved2[1:height + 1, 1:width + 1, :] = img

    for i in range(1, img.shape[0] +1):
        for j in range(1, img.shape[1] +1):
            sum = 0
            for m in range(kernel_height):
                for n in range(kernel_width):
                    x = i + m - kernel_height // 2
                    y = j + n - kernel_width // 2
                    sum += img_convolved2[x, y, 0] * kernel[m, n]
            img_convolved[i, j, :] = sum

    return img_convolved[1:height +1, 1:width +1]

# @njit
def sobel(img: np.ndarray) -> np.ndarray:
    kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    kernel_y = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]])

    img_x = convolve(img, kernel_x)
    img_y = convolve(img, kernel_y)

    img_sobel = np.sqrt(img_x ** 2 + img_y ** 2)

    # Give a hue based on the angle
    # img_sobel = angle_to_color(np.arctan2(img_y, img_x))

    img_sobel = np.clip(img_sobel, 0, 255).astype(np.uint8)

    return img_sobel

def angle_to_color(angle: np.ndarray) -> np.ndarray:
    pass