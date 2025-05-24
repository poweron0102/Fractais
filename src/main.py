import os
import shutil

import pygame as pg

from Fragmentos import get_fragmentos, save_fragmentos, SaveImage, LoadImage
from Features.Edge import *
from Features.Color import replace

pg.init()
screen = pg.display.set_mode((800, 600))


def main1():
    print("Hello, World!")

    img_1 = LoadImage("imgs/frieren_1.png")
    img_2 = LoadImage("imgs/frieren_2.png")

    fragmentos_1 = get_fragmentos(img_1, 32)
    fragmentos_2 = get_fragmentos(img_2, 32)

    replaced_img = replace(fragmentos_1, fragmentos_2, yuv=True)

    SaveImage(replaced_img, "imgs/replaced.png")


def main2():
    num_imgs = len(os.listdir("imgs/frames_bad_apple/"))

    future: int = 100

    for i in range(num_imgs):
        img_1 = LoadImage(f"imgs/frames_bad_apple/{i+1:03d}.jpg")
        img_2 = LoadImage(f"imgs/frames_bad_apple/{((i + future) % num_imgs) + 1:03d}.jpg")

        fragmentos_1 = get_fragmentos(img_1, 16)
        fragmentos_2 = get_fragmentos(img_2, 16)

        replaced_img = replace(fragmentos_1, fragmentos_2, yuv=True)

        screen.fill((0, 0, 0))
        screen.blit(pg.surfarray.make_surface(replaced_img), (0, 0))
        pg.display.flip()


if __name__ == "__main__":
    main2()
