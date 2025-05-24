import os
import shutil

import pygame as pg

from Fragmentos import get_fragmentos, save_fragmentos, SaveImage, LoadImage
from Features.Edge import *
from Features.Color import replace, covert_to_YUV

pg.init()


if __name__ == "__main__":
    print("Hello, World!")

    screen = pg.display.set_mode((800, 600))

    img_1 = LoadImage("outputFrag/fragmentos_6_4.png")

    img_1 = grayscale(img_1)
    #img_1 = gaussian_blur(img_1)
    img_1 = sobel(img_1)



    save_array_as_image(img_1, "output", "imgout.png")
