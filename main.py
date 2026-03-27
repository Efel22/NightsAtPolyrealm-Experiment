from ursina import *
from code.world.world import world
from code.entity.player.playerdata import (
    setup, setup_combat,
    update_player, handle_input
)

app = Ursina()       # Intialize URSINA
setup(world)         # Player is created here, after Ursina starts existing
setup_combat()


# -- Game loop -------------------------------------------------------------
def update():
    update_player(time.dt, world)

def input(key):
    if key == 'escape':
        mouse.locked  = not mouse.locked
        mouse.visible = not mouse.visible
        quit()
    handle_input(key)

app.run() 



