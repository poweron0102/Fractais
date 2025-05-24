import os
import shutil

import pygame as pg

from Fragmentos import get_fragmentos, save_fragmentos
from Features.Edge import *
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


    #img = pg.image.load("imgs/frieren.png").convert()
    fragImg = pg.image.load("outputFrag/fragmentos_6_4.png").convert()
    #img_array = pg.surfarray.array3d(img)
    fragImg_array = pg.surfarray.array3d(fragImg)

    img_blur1 = gaussian_blur(fragImg_array)
    img_blur2 = gaussian_blur(img_blur1)
    img_gray = grayscale(img_blur1)
    # fragmentos = get_fragmentos(img_array, 128)
    # save_fragmentos(fragmentos, "outputFrag")
    save_array_as_image(fragImg_array, "output", "original.png")
    save_array_as_image(img_blur1, "output", "blur1.png")
    save_array_as_image(img_blur2, "output", "blur2.png")
    save_array_as_image(img_gray, "output", "gray.png")




