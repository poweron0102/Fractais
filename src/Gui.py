from EasyCells import Game

import Levels.gui

if __name__ == '__main__':
    GAME = Game(Levels.gui, "Spaceship", True, (1280, 720))
    GAME.run()
