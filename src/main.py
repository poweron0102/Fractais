import os
import shutil

import pygame as pg

from Fragmentos import get_fragmentos, save_fragmentos
from Features.Color import replace

pg.init()


if __name__ == "__main__":
    print("Hello, World!")

    screen = pg.display.set_mode((800, 600))

    img_1 = pg.image.load("imgs/frieren_1.png").convert()
    img_array_1 = pg.surfarray.array3d(img_1)

    img_2 = pg.image.load("imgs/frieren_2.png").convert()
    img_array_2 = pg.surfarray.array3d(img_2)

    fragmentos_1 = get_fragmentos(img_array_1, 32)
    fragmentos_2 = get_fragmentos(img_array_2, 32)

    replaced_img = replace(fragmentos_1, fragmentos_2, yuv=True)
    replaced_img = pg.surfarray.make_surface(replaced_img)
    pg.image.save(replaced_img, "imgs/replaced.png")



