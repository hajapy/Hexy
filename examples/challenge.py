import sys
sys.path.append("..")

import numpy as np
import hexy as hx
import pygame as pg

from example_hex import ExampleHex
from example_hex import make_hex_surface

COL_IDX = np.random.randint(0, 4, (7 ** 3))
COLORS = np.array([
    [244, 98, 105],  # red
    [251, 149, 80],  # orange
    [141, 207, 104],  # green
    [53, 111, 163],  # water blue
    [85, 163, 193],  # sky blue
])


class Selection:
    class Type:
        POINT = 0 
        RING = 1
        DISK = 2
        LINE = 3

        @staticmethod
        def to_string(selection_type):
            if selection_type == Selection.Type.DISK:
                return "disk"
            elif selection_type == Selection.Type.RING:
                return "ring"
            elif selection_type == Selection.Type.LINE:
                return "line"
            else:
                return "point"


    @staticmethod
    def get_selection(selection_type, cube_mouse, rad, clicked_hex=None):
            if selection_type == Selection.Type.DISK:
                return hx.get_disk(cube_mouse, rad)
            elif selection_type == Selection.Type.RING:
                return hx.get_ring(cube_mouse, rad)
            elif selection_type == Selection.Type.LINE:
                return hx.get_hex_line(clicked_hex, cube_mouse)
            else:
                return cube_mouse.copy()


class ExampleHexMap():
    def __init__(self, n=2, size=(600, 600), hex_radius=22, caption="ExampleHexMap"):
        assert n > 1
        self.caption = caption
        self.size = np.array(size)
        self.width, self.height = self.size
        self.center = self.size / 2

        self.hex_radius = hex_radius
        self.hex_apothem = hex_radius * np.sqrt(3) / 2
        self.hex_offset = np.array([self.hex_radius * np.sqrt(3) / 2, self.hex_radius])

        self.hex_map = hx.HexMap()
        self.max_coord = n - 1
        
        self.selected_hex_image = make_hex_surface(
                (128, 128, 128, 160), 
                self.hex_radius, 
                (255, 255, 255), 
                hollow=True)
        
        self.rad = 1
        self.selection_type = 1
        self.clicked_hex = np.array([0, 0, 0])

        # Get all possible coordinates within `self.max_coord` as radius.
        coords = hx.get_spiral(np.array((0, 0, 0)), 1, self.max_coord)

        # Convert coords to axial coordinates, create hexes and randomly filter out some hexes.
        hexes = []        
        axial_coords = hx.cube_to_axial(coords)

        for i, axial in enumerate(axial_coords):
            colo = list(COLORS[COL_IDX[i % len(COL_IDX)]])
            colo.append(255)
            hexes.append(ExampleHex(axial, colo, hex_radius))
            hexes[-1].set_value(i)  # the number at the center of the hex

        self.hex_map[np.array(axial_coords)] = hexes

        self.main_surf = None
        self.font = None
        self.clock = None
        self.init_pg()

    def init_pg(self):
        pg.init()
        self.main_surf = pg.display.set_mode(self.size)
        pg.display.set_caption(self.caption)

        pg.font.init()
        self.font = pg.font.SysFont("monospace", 14, True)
        self.clock = pg.time.Clock()

    def handle_events(self):
        running = True
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False

        return running

    def main_loop(self):
        running = self.handle_events()
        return running

    def draw(self):
        # show all hexes
        hexagons = list(self.hex_map.values())
        hex_positions = np.array([hexagon.get_draw_position() for hexagon in hexagons])
        sorted_idxs = np.argsort(hex_positions[:,1])
        for idx in sorted_idxs:
            self.main_surf.blit(hexagons[idx].image, hex_positions[idx] + self.center)

        # draw values of hexes
        for hexagon in self.hex_map.values():
            text = self.font.render(str(hexagon.value), False, (0, 0, 0))
            text.set_alpha(160)
            text_pos = hexagon.get_position() + self.center
            text_pos -= (text.get_width() / 2, text.get_height() / 2)
            self.main_surf.blit(text, text_pos)

        mouse_pos = np.array([np.array(pg.mouse.get_pos()) - self.center])
        cube_mouse = hx.pixel_to_cube(mouse_pos, self.hex_radius)

        # choose either ring or disk
        rad_hex = Selection.get_selection(self.selection_type, cube_mouse, self.rad, self.clicked_hex)

        rad_hex_axial = hx.cube_to_axial(rad_hex)
        hexes = self.hex_map[rad_hex_axial]

        list(map(lambda hexagon: 
                self.main_surf.blit(
                    self.selected_hex_image, hexagon.get_draw_position() + self.center), 
                hexes))

        # draw hud
        self.selection_type

        fps_text = self.font.render(" FPS: " + str(int(self.clock.get_fps())), True, (50, 50, 50))
        n_text = self.font.render(" N: " + str(self.max_coord + 1), True, (50, 50, 50))

        self.main_surf.blit(fps_text, (5, 0))
        self.main_surf.blit(n_text, (5, 15))

        # Update screen
        pg.display.update()
        self.main_surf.fill(COLORS[-1])
        self.clock.tick(30)

    def quit_app(self):
        pg.quit()


if __name__ == '__main__':
    ehm = ExampleHexMap(int(sys.argv[1]))
    while ehm.main_loop():
        ehm.draw()
    ehm.quit_app()
