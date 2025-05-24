import pygame as pg

from Fragmentos import get_fragmentos, save_fragmentos
from Features.Edge import *

pg.init()


if __name__ == "__main__":
    print("Hello, World!")
    screen = pg.display.set_mode((800, 600))

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




