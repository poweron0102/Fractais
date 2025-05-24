import pygame as pg

from src.FractaisExtrator import get_kernels, save_kernels

pg.init()


if __name__ == "__main__":
    print("Hello, World!")
    screen = pg.display.set_mode((800, 600))

    img = pg.image.load("imgs/frieren.png").convert()
    img_array = pg.surfarray.array3d(img)

    kernels = get_kernels(img_array, 32)
    save_kernels(kernels, "output")

