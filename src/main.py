import pygame as pg

from Fragmentos import get_fragmentos, save_fragmentos

pg.init()


if __name__ == "__main__":
    print("Hello, World!")
    screen = pg.display.set_mode((800, 600))

    img = pg.image.load("imgs/frieren.png").convert()
    img_array = pg.surfarray.array3d(img)

    fragmentos = get_fragmentos(img_array, 128)
    save_fragmentos(fragmentos, "output")

