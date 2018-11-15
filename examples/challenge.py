import sys
sys.path.append("..")
from functools import lru_cache
from random import shuffle

import numpy as np
import hexy as hx
import pygame as pg

from example_hex import ExampleHex
from example_hex import make_hex_surface

COLORS = np.array([
    [244, 98, 105],  # red
    [251, 149, 80],  # orange
    [141, 207, 104],  # green
    [53, 111, 163],  # water blue
    [85, 163, 193],  # sky blue
])


make_hex_surface_cached = lru_cache(maxsize=None)(make_hex_surface)


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
            hexes.append(ExampleHex(axial, [255, 255, 255, 255], hex_radius))
            hexes[-1].set_value(i)  # the number at the center of the hex

        self.hex_map[np.array(axial_coords)] = hexes

        for hex in self.hex_map.values():
            nn = self.nn(hex)
            hex.coordination = len(nn)
            hex.value = hex.coordination + 1

        self.main_surf = None
        self.font = None
        self.clock = None
        self.energy = sum(v.value for v  in self.hex_map.values())
        self.valid = False
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

        for hexagon in hexes:
            self.main_surf.blit(self.selected_hex_image, hexagon.get_draw_position() + self.center)

        # draw hud
        fps_text = self.font.render(" FPS: " + str(int(self.clock.get_fps())), True, (50, 50, 50))
        n_text = self.font.render(" N: " + str(self.max_coord + 1), True, (50, 50, 50))
        energy_text = self.font.render(" ENERGY: " + str(self.energy), True, (50, 50, 50))
        valid_text = self.font.render(" VALID: " + str(self.valid), True, (50, 50, 50))

        self.main_surf.blit(fps_text, (5, 0))
        self.main_surf.blit(n_text, (5, 15))
        self.main_surf.blit(energy_text, (5, 30))
        self.main_surf.blit(valid_text, (5, 45))

        # Update screen
        pg.display.update()
        self.main_surf.fill(COLORS[-1])
        self.clock.tick(30)

    def update_values(self):
        hexes = list(self.hex_map.values())
        shuffle(hexes)
        for hex in hexes:
            nn = self.nn(hex)
            required_values = set(range(1, min(hex.value, len(nn))))
            to_drop = []
            for i, h in enumerate(nn):
                if h.value in required_values:
                    required_values.remove(h.value)
                    to_drop.append(i)
            for i in reversed(to_drop):
                nn.pop(i)

            required_values = list(required_values)
            shuffle(nn)
            shuffle(required_values)
            for i, r in enumerate(required_values):
                nn[i].value = r

            hex.color = list(COLORS[hex.value % len(COLORS)])
            hex.color.append(255)
            hex.image = make_hex_surface_cached(tuple(hex.color), hex.radius)

        self.energy = sum(v.value for v  in self.hex_map.values())

    @lru_cache(maxsize=None)
    def nn(self, hex: ExampleHex):
        rad_hex = Selection.get_selection(self.selection_type, hex.cube_coordinates, self.rad)
        rad_hex_axial = hx.cube_to_axial(rad_hex)
        return self.hex_map[rad_hex_axial]

    @staticmethod
    @lru_cache(maxsize=None)
    def _must_contain(n: int):
        must_contain = set(range(1, n))
        must_contain.add(1)
        return must_contain

    def is_valid(self):
        self.valid = False
        for hex in self.hex_map.values():
            nn = self.nn(hex)
            values = set(n.value for n in nn)
            must_have = self._must_contain(hex.value)
            if not must_have.issubset(values):
                return False
        self.valid = True
        return True

    def quit_app(self):
        pg.quit()


if __name__ == '__main__':
    n = 3 if len(sys.argv) == 1 else int(sys.argv[1])
    ehm = ExampleHexMap(n)
    while ehm.main_loop():
        ehm.draw()
        if not ehm.is_valid():
            ehm.update_values()
    ehm.quit_app()
