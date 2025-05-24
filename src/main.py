import os
import shutil

import pygame as pg

from Fragmentos import get_fragmentos, save_fragmentos, SaveImage, LoadImage
from Features.Edge import *
from Features.Color import replace

pg.init()


if __name__ == "__main__":
    print("Hello, World!")

    screen = pg.display.set_mode((800, 600))

    img_1 = LoadImage("imgs/frieren_1.png")
    img_2 = LoadImage("imgs/frieren_2.png")

    fragmentos_1 = get_fragmentos(img_1, 32)
    fragmentos_2 = get_fragmentos(img_2, 32)

    replaced_img = replace(fragmentos_1, fragmentos_2, yuv=True)

    SaveImage(replaced_img, "imgs/replaced.png")
