import os

import numpy as np
import pygame as pg

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
        for i in range(1, height-1):
            for j in range(1, width-1):
                imgB[i, j] = (imgB[i, j-1] * kernel[0] + imgB[i, j] * kernel[1] + imgB[i, j+1] * kernel[2])
                imgB[i, j] = (imgB[i-1, j] * kernel[0] + imgB[i, j] * kernel[1] + imgB[i+1, j] * kernel[2])
    
    return imgB[1:height + 1, 1:width + 1]
# Grayscale
def grayscale(img: np.ndarray) -> np.ndarray:
    rgbSence = np.array([0.2989, 0.5870, 0.1140], dtype=np.float32)
    imgG = np.zeros((img.shape[0:2]), dtype=np.float32)
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            imgG[i, j] = np.dot(img[i, j], rgbSence)
            print(img[i, j])

    return imgG.astype(np.uint8)


# Sobel