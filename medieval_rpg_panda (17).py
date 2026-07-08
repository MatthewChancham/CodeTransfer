"""
Medieval RPG - Panda3D Prototype
--------------------------------
Pure-python Panda3D conversion of the Tkinter dungeon crawler (imagetest.py).

This pass covers:
  1) Player stat system (ported from imagetest19, with new speed/jump rules)
  2) An on-screen Stats page laid out like the Tkinter version
  3) A medieval town with 8 UNIQUE buildings matching imagetest19's
     create_town_layout() (Player's House, Library, Blacksmith, Enchanter
     Tower, Alchemist Shop, Bakery/Inn, Jeweler, General Trader) - same
     colors/silhouette ideas as the Tkinter drawing code, built from boxes
  4) A tall multi-tier fountain with 4 curved curtains of spraying water
  5) A dense (4x area), CHUNKED forest that streams in/out around the
     player so it doesn't tank performance, and forms a real forest wall
  6) Minecraft-style first-person camera: mouse-look + WASD + jump, with
     CollisionPolygon-based wall collision (fixes sink/climb glitches)
  7) An Esc pause/home screen with a single Play button

Run with plain python - Panda3D auto-installs itself the first time.
"""

import sys
import subprocess

# ---------------------------------------------------------------------------
# 1. Background Download Check (works out-of-the-box, no manual pip install)
# ---------------------------------------------------------------------------
try:
    import direct
    from direct.showbase.ShowBase import ShowBase
    from panda3d.core import WindowProperties
except ImportError:
    print("Panda3D not found. Fetching library automatically, please wait...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "panda3d"])
    from direct.showbase.ShowBase import ShowBase
    from panda3d.core import WindowProperties

import math
import random

from panda3d.core import (
    GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomTriangles,
    Geom, GeomNode, NodePath, Vec3, Vec4, Point3, AmbientLight, DirectionalLight,
    CollisionNode, CollisionPolygon, CollisionSphere, CollisionTraverser,
    CollisionHandlerPusher, TextNode, BitMask32, Fog,
)
from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectWaitBar, OnscreenText, DGG,
)
from direct.task import Task


# ===========================================================================
#  PRIMITIVE SHAPE HELPERS  ("default shapes" used to build every building)
# ===========================================================================

def make_box(w, h, d, color=(0.8, 0.8, 0.8, 1), name="box"):
    """
    Axis-aligned box centered on X/Y, sitting on Z=0..d (d = height).
    w = width (x), h = depth (y), d = height (z). This is the single
    "default shape" every wall, beam, roof panel, tree and prop uses.
    Rendered two-sided so nothing disappears from any viewing angle.
    """
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    vdata.setNumRows(24)

    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")
    color_w = GeomVertexWriter(vdata, "color")

    x, y = w / 2.0, h / 2.0
    z0, z1 = 0.0, d

    faces = [
        ([(-x, -y, z0), (x, -y, z0), (x, -y, z1), (-x, -y, z1)], (0, -1, 0)),
        ([(x, y, z0), (-x, y, z0), (-x, y, z1), (x, y, z1)], (0, 1, 0)),
        ([(-x, y, z0), (-x, -y, z0), (-x, -y, z1), (-x, y, z1)], (-1, 0, 0)),
        ([(x, -y, z0), (x, y, z0), (x, y, z1), (x, -y, z1)], (1, 0, 0)),
        ([(-x, -y, z1), (x, -y, z1), (x, y, z1), (-x, y, z1)], (0, 0, 1)),
        ([(-x, y, z0), (x, y, z0), (x, -y, z0), (-x, -y, z0)], (0, 0, -1)),
    ]

    tris = GeomTriangles(Geom.UHStatic)
    idx = 0
    for pts, n in faces:
        for p in pts:
            vertex.addData3(*p)
            normal.addData3(*n)
            color_w.addData4(*color)
        tris.addVertices(idx, idx + 1, idx + 2)
        tris.addVertices(idx, idx + 2, idx + 3)
        idx += 4

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    np = NodePath(node)
    np.setTwoSided(True)
    return np


def build_fog_wall(radius, height, color, segments=48, name="fog_wall"):
    """A large ring of flat, unlit, fog-colored quads surrounding the whole
    play area (town + forest), always loaded - never chunked/stashed.

    This exists to fix a structural limitation of the forest's chunk
    streaming: fog only tints geometry as it renders, it can never affect
    the empty background/sky behind it. When a distant tree chunk gets
    stashed out for performance, gaps between trunks can open a "window"
    straight through to the raw blue background, no matter how heavy the
    fog is. Since this wall's color is set to exactly match the fog's own
    color, it becomes visually indistinguishable from "fully fogged
    distance" at any range - up close it just IS that color (lighting is
    disabled so it can't get shaded lighter/darker), and further out the
    fog blends it into itself seamlessly. It quietly caps every sightline
    before it can ever reach the true sky.
    """
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    vdata.setNumRows(segments * 4)

    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")
    color_w = GeomVertexWriter(vdata, "color")
    tris = GeomTriangles(Geom.UHStatic)

    z0, z1 = -height * (2.0 / 16.0), height
    idx = 0
    for i in range(segments):
        a0 = i * math.tau / segments
        a1 = (i + 1) * math.tau / segments
        x0, y0 = radius * math.cos(a0), radius * math.sin(a0)
        x1, y1 = radius * math.cos(a1), radius * math.sin(a1)
        mid = (a0 + a1) / 2.0
        nx, ny = -math.cos(mid), -math.sin(mid)  # inward-facing
        for p in [(x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)]:
            vertex.addData3(*p)
            normal.addData3(nx, ny, 0)
            color_w.addData4(*color)
        tris.addVertices(idx, idx + 1, idx + 2)
        tris.addVertices(idx, idx + 2, idx + 3)
        idx += 4

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    np = NodePath(node)
    np.setTwoSided(True)
    np.setLightOff()
    return np


def make_gable_roof(w, d, ridge_h, color=(0.35, 0.18, 0.1, 1), name="roof"):
    """Closed triangular-prism gable roof, Z=0..ridge_h. 2 rectangular slant
    faces + 2 triangular gable ends - fully closed, two-sided."""
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")
    color_w = GeomVertexWriter(vdata, "color")

    x, y = w / 2.0, d / 2.0
    p_fl, p_fr = (-x, -y, 0), (x, -y, 0)
    p_bl, p_br = (-x, y, 0), (x, y, 0)
    p_rf, p_rb = (0, -y, ridge_h), (0, y, ridge_h)

    tris = GeomTriangles(Geom.UHStatic)
    idx = 0

    def add_quad(a, b, c, dd, n):
        nonlocal idx
        for p in (a, b, c, dd):
            vertex.addData3(*p); normal.addData3(*n); color_w.addData4(*color)
        tris.addVertices(idx, idx + 1, idx + 2)
        tris.addVertices(idx, idx + 2, idx + 3)
        idx += 4

    def add_tri(a, b, c, n):
        nonlocal idx
        for p in (a, b, c):
            vertex.addData3(*p); normal.addData3(*n); color_w.addData4(*color)
        tris.addVertices(idx, idx + 1, idx + 2)
        idx += 3

    ln = math.hypot(ridge_h, x)
    n_left = (-ridge_h / ln, 0, x / ln)
    n_right = (ridge_h / ln, 0, x / ln)

    add_quad(p_fl, p_rf, p_rb, p_bl, n_left)
    add_quad(p_fr, p_br, p_rb, p_rf, n_right)
    add_tri(p_fl, p_fr, p_rf, (0, -1, 0))
    add_tri(p_br, p_bl, p_rb, (0, 1, 0))

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    np = NodePath(node)
    np.setTwoSided(True)
    return np


def make_pyramid_roof(w, d, apex_h, color, name="pyroof"):
    """4-sided pyramid roof (used for the Enchanter Tower) - a single apex
    point instead of a ridge line."""
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")
    color_w = GeomVertexWriter(vdata, "color")

    x, y = w / 2.0, d / 2.0
    corners = [(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0)]
    apex = (0, 0, apex_h)

    tris = GeomTriangles(Geom.UHStatic)
    idx = 0
    for i in range(4):
        a = corners[i]
        b = corners[(i + 1) % 4]
        edge1 = Vec3(b[0] - a[0], b[1] - a[1], b[2] - a[2])
        edge2 = Vec3(apex[0] - a[0], apex[1] - a[1], apex[2] - a[2])
        n = edge1.cross(edge2)
        n.normalize()
        for p in (a, b, apex):
            vertex.addData3(*p); normal.addData3(n.x, n.y, n.z); color_w.addData4(*color)
        tris.addVertices(idx, idx + 1, idx + 2)
        idx += 3

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    np = NodePath(node)
    np.setTwoSided(True)
    return np


def make_cylinder(radius, height, color, segments=16, z0=0.0, top_cap=True,
                   bottom_cap=True, name="cyl"):
    """A vertical faceted cylinder from Z=z0..z0+height - side walls plus
    optional flat top/bottom caps. This is what actually reads as a round
    'bowl'/'column'/'post' shape instead of an obvious box, used for the
    fountain's basin+column and the streetlamp posts."""
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")
    color_w = GeomVertexWriter(vdata, "color")
    tris = GeomTriangles(Geom.UHStatic)

    z1 = z0 + height
    ring = [(radius * math.cos(math.tau * i / segments), radius * math.sin(math.tau * i / segments))
            for i in range(segments)]

    idx = 0
    for i in range(segments):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % segments]
        nx, ny = x0 + x1, y0 + y1
        nl = math.hypot(nx, ny) or 1.0
        nx, ny = nx / nl, ny / nl
        for p in [(x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)]:
            vertex.addData3(*p); normal.addData3(nx, ny, 0); color_w.addData4(*color)
        tris.addVertices(idx, idx + 1, idx + 2)
        tris.addVertices(idx, idx + 2, idx + 3)
        idx += 4

    if top_cap:
        for (x, y) in ring:
            vertex.addData3(x, y, z1); normal.addData3(0, 0, 1); color_w.addData4(*color)
        for i in range(1, segments - 1):
            tris.addVertices(idx, idx + i, idx + i + 1)
        idx += segments

    if bottom_cap:
        for (x, y) in ring:
            vertex.addData3(x, y, z0); normal.addData3(0, 0, -1); color_w.addData4(*color)
        for i in range(1, segments - 1):
            tris.addVertices(idx, idx + i + 1, idx + i)
        idx += segments

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    np = NodePath(node)
    np.setTwoSided(True)
    return np


def make_sphere(radius, color, lat_segments=8, lon_segments=12, name="sphere"):
    """A simple UV sphere, centered on its own origin. Used for enemy heads/
    bodies (kept deliberately simple/low-poly - a plain sphere or box, like
    the Tkinter game's flat oval/rectangle enemy shapes) and for the mana
    bolt projectile."""
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    vertex = GeomVertexWriter(vdata, "vertex")
    normal = GeomVertexWriter(vdata, "normal")
    color_w = GeomVertexWriter(vdata, "color")
    tris = GeomTriangles(Geom.UHStatic)

    verts = []
    for i in range(lat_segments + 1):
        theta = math.pi * i / lat_segments        # 0 (top) .. pi (bottom)
        for j in range(lon_segments):
            phi = math.tau * j / lon_segments
            x = math.sin(theta) * math.cos(phi)
            y = math.sin(theta) * math.sin(phi)
            z = math.cos(theta)
            verts.append((x, y, z))
            vertex.addData3(x * radius, y * radius, z * radius)
            normal.addData3(x, y, z)
            color_w.addData4(*color)

    def vid(i, j):
        return i * lon_segments + (j % lon_segments)

    for i in range(lat_segments):
        for j in range(lon_segments):
            a, b = vid(i, j), vid(i, j + 1)
            c, d = vid(i + 1, j), vid(i + 1, j + 1)
            tris.addVertices(a, c, d)
            tris.addVertices(a, d, b)

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    np = NodePath(node)
    np.setTwoSided(True)
    return np


CLASS_BASE_STATS = {
    'Warrior': {'strength': 1, 'vitality': 1, 'agility': 1, 'intelligence': 0, 'wisdom': 0, 'will': 0, 'constitution': 1, 'endurance': 1},
    'Mage':    {'strength': 0, 'vitality': 0, 'agility': 0, 'intelligence': 2, 'wisdom': 1, 'will': 1, 'constitution': 0, 'endurance': 0},
    'Rogue':   {'strength': 1, 'vitality': 0, 'agility': 1, 'intelligence': 1, 'wisdom': 0, 'will': 1, 'constitution': 0, 'endurance': 1},
    'Cleric':  {'strength': 0, 'vitality': 0, 'agility': 0, 'intelligence': 1, 'wisdom': 1, 'will': 2, 'constitution': 1, 'endurance': 0},
    'Druid':   {'strength': 0, 'vitality': 1, 'agility': 0, 'intelligence': 1, 'wisdom': 2, 'will': 0, 'constitution': 1, 'endurance': 0},
    'Monk':    {'strength': 0, 'vitality': 2, 'agility': 1, 'intelligence': 0, 'wisdom': 0, 'will': 0, 'constitution': 1, 'endurance': 1},
    'Ranger':  {'strength': 1, 'vitality': 0, 'agility': 1, 'intelligence': 1, 'wisdom': 0, 'will': 1, 'constitution': 0, 'endurance': 1},
}

STAT_DISPLAY_NAMES = {
    'strength': 'Strength', 'vitality': 'Vitality', 'agility': 'Agility',
    'intelligence': 'Intelligence', 'wisdom': 'Wisdom', 'will': 'Will',
    'constitution': 'Constitution', 'endurance': 'Endurance',
}
STAT_ORDER = ['strength', 'vitality', 'agility', 'intelligence', 'wisdom', 'will', 'constitution', 'endurance']

BASE_WALK_SPEED = 3.5
# imagetest19: self.base_speed = 3.5 + self.agility * 0.05  -> 5x less:
AGILITY_SPEED_COEFF = 0.05 / 5.0          # == 0.01 per agility point
SPRINT_MULTIPLIER = 2.2                    # sprint is 2.2x more "efficient"
BASE_JUMP_HEIGHT = 1.2
AGILITY_JUMP_COEFF = 0.01                  # agility now raises jump height
GRAVITY = 20.0

# Endurance: new stat, raises max stamina and stamina regen. Sprinting
# drains stamina; once it hits 0 you're forced back to walking speed until
# it regenerates.
BASE_MAX_STAMINA = 50.0
ENDURANCE_STAMINA_COEFF = 10.0            # +10 max stamina per endurance point
BASE_STAMINA_REGEN = 0.2
ENDURANCE_STAMINA_REGEN_COEFF = 0.12      # +stamina/sec regen per endurance point
STAMINA_SPRINT_DRAIN = 8.0                # stamina/sec consumed while sprinting

# Mana Bolt: the one player skill in this pass (everything else ignored
# per request). Left mouse click fires a small glowing sphere forward.
MANA_BOLT_COST = 10.0
MANA_BOLT_COOLDOWN = 0.4                  # seconds between casts
MANA_BOLT_SPEED = 42.0                    # units/sec
MANA_BOLT_LIFETIME = 2.0                  # seconds before it fizzles out
MANA_BOLT_HIT_RADIUS = 1.1
MANA_BOLT_BASE_DAMAGE = 8.0
MANA_BOLT_MAG_COEFF = 1.2                 # extra damage per point of MAG


class Player:
    def __init__(self, name='Hero', class_name='Warrior'):
        self.name = name
        self.class_name = class_name

        base = CLASS_BASE_STATS.get(class_name, CLASS_BASE_STATS['Warrior'])
        self.strength = 5 + base['strength']
        self.vitality = 5 + base['vitality']
        self.agility = 5 + base['agility']
        self.intelligence = 5 + base['intelligence']
        self.wisdom = 5 + base['wisdom']
        self.will = 5 + base['will']
        self.constitution = 3 + base['constitution']
        self.endurance = 5 + base.get('endurance', 0)

        self.level = 1
        self.xp = 0
        self.xp_to_next = 100
        self.stat_points = 5

        self.update_stats()
        self.hp = self.max_hp
        self.mana = self.max_mana
        self.stamina = self.max_stamina
        self.last_manabolt = -999.0

    def can_cast_manabolt(self, t):
        return (t - self.last_manabolt >= MANA_BOLT_COOLDOWN) and (self.mana >= MANA_BOLT_COST)

    def cast_manabolt(self, t):
        """Spend the mana/cooldown and return the projectile's damage.
        Caller is responsible for actually spawning the projectile."""
        self.mana -= MANA_BOLT_COST
        self.last_manabolt = t
        return MANA_BOLT_BASE_DAMAGE + self.mag * MANA_BOLT_MAG_COEFF

    def update_stats(self):
        self.max_hp = 50 + self.vitality * 10
        self.max_mana = 20 + self.intelligence * 10
        self.atk = 5 + self.strength
        self.mag = 2 + self.will
        self.vit = 2 + self.vitality
        self.wis = 2 + self.wisdom

        if self.class_name == 'Monk':
            self.hp_regen = 0.2 + self.vitality * 0.1
        elif self.class_name == 'Druid':
            self.hp_regen = 0.2 + self.wisdom * 0.15
        else:
            self.hp_regen = 0.2 + self.vitality * 0.07
        self.mana_regen = 0.1 + self.wisdom * 0.15

        # endurance -> stamina pool + regen
        self.max_stamina = BASE_MAX_STAMINA + self.endurance * ENDURANCE_STAMINA_COEFF
        self.stamina_regen = BASE_STAMINA_REGEN + self.endurance * ENDURANCE_STAMINA_REGEN_COEFF

        self.base_speed = BASE_WALK_SPEED + self.agility * AGILITY_SPEED_COEFF
        self.speed = self.base_speed
        self.sprint_speed = self.base_speed * SPRINT_MULTIPLIER
        self.jump_height = BASE_JUMP_HEIGHT + self.agility * AGILITY_JUMP_COEFF
        self.jump_velocity = math.sqrt(2 * GRAVITY * self.jump_height)

        self.hp = min(getattr(self, 'hp', self.max_hp), self.max_hp)
        self.mana = min(getattr(self, 'mana', self.max_mana), self.max_mana)
        self.stamina = min(getattr(self, 'stamina', self.max_stamina), self.max_stamina)

    def spend_stat_point(self, stat):
        if self.stat_points <= 0:
            return False
        setattr(self, stat, getattr(self, stat) + 1)
        self.stat_points -= 1
        self.update_stats()
        return True


# ===========================================================================
#  STATS PAGE  (DirectGUI layout mirroring the Tkinter panel structure)
# ===========================================================================

class StatsUI:
    def __init__(self, base, player):
        self.base = base
        self.player = player
        self.visible = False

        self.root = DirectFrame(frameColor=(0.05, 0.05, 0.06, 0.92),
                                 frameSize=(-1.1, 1.1, -0.8, 0.8), pos=(0, 0, 0))
        self.root.hide()

        left = DirectFrame(parent=self.root, frameColor=(0.07, 0.07, 0.07, 1),
                            frameSize=(-1.05, 0.05, -0.72, 0.72), pos=(0, 0, 0))
        self.stat_labels = {}
        self.stat_buttons = {}

        OnscreenText(parent=left, text="STAT", pos=(-0.95, 0.62), scale=0.035,
                     fg=(0.6, 0.6, 0.6, 1), align=TextNode.ALeft)

        row_h = 0.15
        top = 0.5
        for i, stat in enumerate(STAT_ORDER):
            y = top - i * row_h
            lbl = OnscreenText(parent=left, text="", pos=(-0.95, y), scale=0.045,
                                fg=(1, 1, 1, 1), align=TextNode.ALeft, mayChange=True)
            self.stat_labels[stat] = lbl
            btn = DirectButton(parent=left, text="+", scale=0.05, pos=(-0.15, 0, y - 0.015),
                                frameColor=(0.2, 0.2, 0.2, 1), text_fg=(1, 1, 1, 1),
                                command=self._on_plus, extraArgs=[stat])
            self.stat_buttons[stat] = btn

        self.points_label = OnscreenText(
            parent=left, text="", pos=(-0.95, top - len(STAT_ORDER) * row_h - 0.08),
            scale=0.04, fg=(0.7, 0.7, 0.7, 1), align=TextNode.ALeft, mayChange=True)

        right = DirectFrame(parent=self.root, frameColor=(0.06, 0.06, 0.09, 1),
                             frameSize=(0.1, 1.05, -0.72, 0.72), pos=(0, 0, 0))

        self.name_label = OnscreenText(parent=right, text="", pos=(0.18, 0.62), scale=0.05,
                                        fg=(1, 1, 1, 1), align=TextNode.ALeft, mayChange=True)
        self.class_label = OnscreenText(parent=right, text="", pos=(0.18, 0.54), scale=0.04,
                                         fg=(0.85, 0.85, 0.85, 1), align=TextNode.ALeft, mayChange=True)
        self.level_label = OnscreenText(parent=right, text="", pos=(0.18, 0.46), scale=0.04,
                                         fg=(0.55, 1, 0.75, 1), align=TextNode.ALeft, mayChange=True)

        self.xp_bar = DirectWaitBar(parent=right, range=100, value=0, pos=(0.61, 0, 0.36),
                                     frameSize=(-0.42, 0.42, -0.03, 0.03), barColor=(0.3, 0.65, 0.3, 1))
        self.xp_label = OnscreenText(parent=right, text="", pos=(0.61, 0.36), scale=0.03,
                                      fg=(1, 1, 1, 1), align=TextNode.ACenter, mayChange=True)

        derived_names = ["HP", "Mana", "Stamina", "ATK", "MAG", "Speed", "Sprint Speed", "Jump Height"]
        self.derived_labels = {}
        dy = 0.24
        for dname in derived_names:
            lbl = OnscreenText(parent=right, text="", pos=(0.18, dy), scale=0.038,
                                fg=(0.85, 0.85, 0.85, 1), align=TextNode.ALeft, mayChange=True)
            self.derived_labels[dname] = lbl
            dy -= 0.08

        self.refresh()

    def _on_plus(self, stat):
        if self.player.spend_stat_point(stat):
            self.refresh()

    def refresh(self):
        p = self.player
        for stat in STAT_ORDER:
            self.stat_labels[stat].setText(f"{STAT_DISPLAY_NAMES[stat]}: {getattr(p, stat)}")
            self.stat_buttons[stat]['state'] = 'normal' if p.stat_points > 0 else 'disabled'
        self.points_label.setText(f"Stat Points Available: {p.stat_points}")
        self.name_label.setText(f"Name: {p.name}")
        self.class_label.setText(f"Class: {p.class_name}")
        self.level_label.setText(f"Level: {p.level}")
        self.xp_bar['range'] = p.xp_to_next
        self.xp_bar['value'] = p.xp
        self.xp_label.setText(f"{p.xp}/{p.xp_to_next} XP")
        self.derived_labels["HP"].setText(f"HP: {p.hp}/{p.max_hp}")
        self.derived_labels["Mana"].setText(f"Mana: {p.mana}/{p.max_mana}")
        self.derived_labels["Stamina"].setText(f"Stamina: {p.stamina:.0f}/{p.max_stamina:.0f}")
        self.derived_labels["ATK"].setText(f"ATK: {p.atk}")
        self.derived_labels["MAG"].setText(f"MAG: {p.mag}")
        self.derived_labels["Speed"].setText(f"Speed: {p.speed:.2f}")
        self.derived_labels["Sprint Speed"].setText(f"Sprint Speed: {p.sprint_speed:.2f}")
        self.derived_labels["Jump Height"].setText(f"Jump Height: {p.jump_height:.2f}")

    def toggle(self):
        self.visible = not self.visible
        if self.visible:
            self.refresh()
            self.root.show()
        else:
            self.root.hide()


# ===========================================================================
#  HUD  -  always-on top-left Health/Mana/Stamina/EXP bars + level
# ===========================================================================

HUD_BAR_W = 0.26
HUD_BAR_X = -1.6
HUD_BORDER_PAD = 0.006
HUD_BAR_LEFT_EDGE = HUD_BAR_X - HUD_BAR_W - HUD_BORDER_PAD   # left edge of the framed hp/mp/sp/xp bars


class HUD:
    def __init__(self, player):
        self.player = player

        bar_w = HUD_BAR_W
        x = HUD_BAR_X
        y0 = 0.93
        row_h = 0.085
        xp_half_h = 0.008

        bar_defs = [
            ("hp", (0.75, 0.15, 0.15, 1), "HP"),
            ("mana", (0.2, 0.35, 0.85, 1), "MP"),
            ("stamina", (0.85, 0.75, 0.15, 1), "SP"),
        ]
        border_pad = HUD_BORDER_PAD
        self.bars = {}
        self.labels = {}
        self.frames = {}
        for i, (key, color, tag) in enumerate(bar_defs):
            y = y0 - i * row_h
            self.frames[key] = DirectFrame(
                pos=(x, 0, y),
                frameSize=(-bar_w - border_pad, bar_w + border_pad,
                           -0.022 - border_pad, 0.022 + border_pad),
                frameColor=(0.95, 0.95, 0.95, 1), relief=DGG.FLAT,
            )
            self.frames[key].setBin("fixed", 0)
            self.bars[key] = DirectWaitBar(
                parent=self.frames[key], range=100, value=100, pos=(0, 0, 0),
                frameSize=(-bar_w, bar_w, -0.022, 0.022),
                barColor=color, frameColor=(0.08, 0.08, 0.08, 0.85),
            )
            self.bars[key].setBin("fixed", 1)
            self.labels[key] = OnscreenText(
                pos=(x, y - 0.005), scale=0.026, fg=(1, 1, 1, 1),
                align=TextNode.ACenter, mayChange=True,
            )
            self.labels[key].setBin("fixed", 2)

        xp_y = y0 - len(bar_defs) * row_h
        self.frames["xp"] = DirectFrame(
            pos=(x, 0, xp_y),
            frameSize=(-bar_w - border_pad, bar_w + border_pad,
                       -xp_half_h - border_pad, xp_half_h + border_pad),
            frameColor=(0.95, 0.95, 0.95, 1), relief=DGG.FLAT,
        )
        self.frames["xp"].setBin("fixed", 0)
        self.bars["xp"] = DirectWaitBar(
            parent=self.frames["xp"], range=100, value=0, pos=(0, 0, 0),
            frameSize=(-bar_w, bar_w, -xp_half_h, xp_half_h),
            barColor=(0.35, 0.75, 0.35, 1), frameColor=(0.08, 0.08, 0.08, 0.85),
        )
        self.bars["xp"].setBin("fixed", 1)
        self.labels["xp"] = OnscreenText(
            pos=(x, xp_y - 0.004), scale=0.02, fg=(1, 1, 1, 1),
            align=TextNode.ACenter, mayChange=True,
        )
        self.labels["xp"].setBin("fixed", 2)

        self.refresh()

    def refresh(self):
        p = self.player
        self.bars["hp"]["range"] = p.max_hp
        self.bars["hp"]["value"] = p.hp
        self.labels["hp"].setText(f"{p.hp:.0f}/{p.max_hp:.0f}")

        self.bars["mana"]["range"] = p.max_mana
        self.bars["mana"]["value"] = p.mana
        self.labels["mana"].setText(f"{p.mana:.0f}/{p.max_mana:.0f}")

        self.bars["stamina"]["range"] = p.max_stamina
        self.bars["stamina"]["value"] = p.stamina
        self.labels["stamina"].setText(f"{p.stamina:.0f}/{p.max_stamina:.0f}")

        self.bars["xp"]["range"] = p.xp_to_next
        self.bars["xp"]["value"] = p.xp
        self.labels["xp"].setText(f"Lv {p.level} \u2014 {p.xp}/{p.xp_to_next} XP")


# ===========================================================================
#  SKILL HOTBAR  -  5 slots, top-left, matching the Tkinter game's hotbar:
#  numbered slots, a highlighted border on the selected slot, and a dark
#  cooldown overlay that wipes away from the bottom as the skill recovers.
#  Only slot 1 (Mana Bolt) does anything in this pass - the rest are
#  empty/reserved for future skills, per "ignore other skills" for now.
# ===========================================================================

class Hotbar:
    SLOT_W = 0.11
    GAP = 0.016

    def __init__(self, skill_names):
        """skill_names: list of 5 entries, each a skill name string or None
        for an empty slot."""
        self.skill_names = skill_names
        self.active_slot = 1  # 1-indexed, matches the Tkinter hotbar

        start_x = HUD_BAR_LEFT_EDGE + self.SLOT_W / 2
        y_center = 0.60

        self.frames = []
        self.overlays = []
        self.name_labels = []
        for i in range(5):
            cx = start_x + i * (self.SLOT_W + self.GAP)
            filled = skill_names[i] is not None

            frame = DirectFrame(
                frameColor=(0.55, 0.55, 0.55, 0.92) if filled else (0.25, 0.25, 0.25, 0.7),
                frameSize=(-self.SLOT_W / 2, self.SLOT_W / 2, -self.SLOT_W / 2, self.SLOT_W / 2),
                pos=(cx, 0, y_center),
                relief=DGG.RAISED, borderWidth=(0.004, 0.004),
            )
            frame.setBin("fixed", 0)
            self.frames.append(frame)

            OnscreenText(parent=frame, text=str(i + 1),
                         pos=(-self.SLOT_W / 2 + 0.018, self.SLOT_W / 2 - 0.028),
                         scale=0.022, fg=(0.05, 0.05, 0.05, 1), align=TextNode.ALeft)

            name = skill_names[i] or "-"
            name_label = OnscreenText(
                parent=frame, text=name, pos=(0, -0.015), scale=0.02,
                fg=(1, 1, 1, 1) if filled else (0.5, 0.5, 0.5, 1),
                align=TextNode.ACenter, wordwrap=6, mayChange=True,
            )
            self.name_labels.append(name_label)

            # cooldown wipe: anchored at the slot's top edge, scaled down
            # in Z as the cooldown elapses so it uncovers from the bottom
            overlay = DirectFrame(
                frameColor=(0, 0, 0, 0.68),
                frameSize=(-self.SLOT_W / 2, self.SLOT_W / 2, -1, 0),
                pos=(cx, 0, y_center + self.SLOT_W / 2),
            )
            overlay.setBin("fixed", 1)
            overlay.setScale(1, 1, 0.0001)
            overlay.hide()
            self.overlays.append(overlay)

        self._update_selection_visual()

    def _update_selection_visual(self):
        for i, frame in enumerate(self.frames):
            selected = (i + 1) == self.active_slot
            filled = self.skill_names[i] is not None
            frame["borderWidth"] = (0.007, 0.007) if selected else (0.004, 0.004)
            frame["frameColor"] = (
                (0.85, 0.85, 0.85, 0.95) if (selected and filled) else
                (0.6, 0.6, 0.6, 0.92) if filled else
                (0.35, 0.35, 0.35, 0.8) if selected else
                (0.25, 0.25, 0.25, 0.7)
            )

    def select_slot(self, slot):
        self.active_slot = slot
        self._update_selection_visual()

    def refresh_cooldowns(self, cooldown_fracs):
        """cooldown_fracs: dict of {slot_index_1_based: remaining_fraction
        (1.0 = just used, 0.0 = ready)}. Slots not present are hidden."""
        for i in range(5):
            slot = i + 1
            frac = cooldown_fracs.get(slot, 0.0)
            overlay = self.overlays[i]
            if frac > 0.001:
                overlay.setScale(1, 1, frac * self.SLOT_W)
                overlay.show()
            else:
                overlay.hide()


# ===========================================================================
#  COLLISION  -  CollisionPolygon walls (fixes sink-into-floor/climb-wall)
# ===========================================================================

WALL_MASK = BitMask32.bit(1)


def _rect_points(half_w, half_d):
    return [(-half_w, -half_d), (half_w, -half_d), (half_w, half_d), (-half_w, half_d)]


def _circle_points(radius, n=8):
    return [(radius * math.cos(math.tau * i / n), radius * math.sin(math.tau * i / n)) for i in range(n)]


def add_wall_colliders(parent_np, points_xy, height, name="col"):
    """A hollow vertical 'fence' of CollisionPolygon walls around the given
    footprint polygon. This is the well-tested Panda3D pattern for FPS wall
    sliding (CollisionSphere avatar vs CollisionPolygon walls) - unlike a
    single CollisionBox, every wall here has an exactly-horizontal normal,
    so the pusher can never produce a vertical push component. That is what
    caused the earlier sink-into-floor / climb-the-wall glitches."""
    cnode = CollisionNode(name)
    n = len(points_xy)
    for i in range(n):
        x0, y0 = points_xy[i]
        x1, y1 = points_xy[(i + 1) % n]
        poly = CollisionPolygon(
            Point3(x0, y0, 0), Point3(x1, y1, 0),
            Point3(x1, y1, height), Point3(x0, y0, height),
        )
        cnode.addSolid(poly)
    cnode.setIntoCollideMask(WALL_MASK)
    cnode.setFromCollideMask(0)
    return parent_np.attachNewNode(cnode)


# ===========================================================================
#  SHARED BUILDING PIECES
# ===========================================================================

BEAM_COLOR = (0.165, 0.10, 0.03, 1)     # matches reference '#2a1a08'
STONE_MORTAR = (0.24, 0.24, 0.24, 1)
GROUND_COLOR = (0.13, 0.40, 0.14, 1)
PATH_COLOR = (0.55, 0.47, 0.35, 1)
FOG_COLOR = (0.32, 0.45, 0.3, 1)          # shared by _setup_fog and the fog wall so they never drift apart


def _add_beam(parent, x, y, z, w, h, d, hpr=(0, 0, 0)):
    beam = make_box(w, h, d, BEAM_COLOR, "beam")
    beam.reparentTo(parent)
    beam.setPos(x, y, z)
    beam.setHpr(*hpr)


def _half_timber_facade(house, w, d, wall_h, style, front_extras=True):
    """Front/back half-timber framing: horizontal rails, corner posts, and
    either an X-brace or ladder pattern - matches the Tkinter _half_timber()
    beam layout (rails every quarter height + diagonal braces + corner
    posts)."""
    beam_t = 0.08
    for face_i, face_y in enumerate((-d / 2 - 0.01, d / 2 + 0.01)):
        _add_beam(house, 0, face_y, 0.05, w, beam_t, beam_t)
        _add_beam(house, 0, face_y, wall_h - 0.15, w, beam_t, beam_t)
        for vx in (-w / 2 + 0.25, w / 2 - 0.25):
            _add_beam(house, vx, face_y, 0, beam_t, beam_t, wall_h)
        if style % 2 == 0:
            _add_beam(house, 0, face_y, 0, beam_t, beam_t, wall_h)
            _add_beam(house, 0, face_y, wall_h * 0.55, w, beam_t, beam_t)
            diag_len = math.hypot(w / 2, wall_h * 0.5)
            ang = math.degrees(math.atan2(wall_h * 0.5, w / 2))
            _add_beam(house, -w / 4, face_y, wall_h * 0.28, diag_len, beam_t, beam_t, hpr=(0, 0, ang))
            _add_beam(house, w / 4, face_y, wall_h * 0.28, diag_len, beam_t, beam_t, hpr=(0, 0, -ang))
        else:
            for vx in (-w / 6, w / 6):
                _add_beam(house, vx, face_y, 0, beam_t, beam_t, wall_h)
            for frac in (0.33, 0.66):
                _add_beam(house, 0, face_y, wall_h * frac, w, beam_t, beam_t)
    for face_x in (-w / 2 - 0.01, w / 2 + 0.01):
        _add_beam(house, face_x, 0, 0, beam_t, d, wall_h)


def _add_door(house, w, d, wall_h, door_w=0.8, door_h=1.7, color=(0.30, 0.16, 0.08, 1)):
    face_y = -d / 2 - 0.02
    door_x = 0.0
    door = make_box(door_w, 0.1, door_h, color, "door")
    door.reparentTo(house)
    door.setPos(door_x, face_y, 0.02)
    cap = make_box(door_w * 0.7, 0.1, 0.18, (color[0] * 0.8, color[1] * 0.8, color[2] * 0.8, 1), "doorcap")
    cap.reparentTo(house)
    cap.setPos(door_x, face_y + 0.02, door_h + 0.02)
    return door_x


def _add_window(house, x, z, face_y, size=0.55, glow=False):
    glass = (1.0, 0.85, 0.5, 1) if glow else (0.15, 0.22, 0.28, 1)
    window = make_box(size, 0.1, size, glass, "window")
    window.reparentTo(house)
    window.setPos(x, face_y - 0.015, z)
    _add_beam(house, x, face_y - 0.03, z, size, 0.05, 0.05)
    _add_beam(house, x, face_y - 0.03, z, 0.05, 0.05, size)


def _add_flowerbox(house, x, z, face_y):
    fbox = make_box(0.6, 0.18, 0.16, (0.35, 0.19, 0.08, 1), "flowerbox")
    fbox.reparentTo(house)
    fbox.setPos(x, face_y - 0.1, z - 0.42)
    for fdx in (-0.18, 0.0, 0.18):
        flower = make_box(0.09, 0.09, 0.09, (0.75, 0.2, 0.35, 1), "flower")
        flower.reparentTo(house)
        flower.setPos(x + fdx, face_y - 0.12, z - 0.3)


def _add_hanging_sign(parent, x, y, wall_h, color, shape="square"):
    post = make_box(0.08, 0.08, wall_h * 0.55, BEAM_COLOR, "signpost")
    post.reparentTo(parent)
    post.setPos(x, y, 0)
    arm = make_box(0.7, 0.08, 0.08, BEAM_COLOR, "signarm")
    arm.reparentTo(parent)
    arm.setPos(x + 0.35, y, wall_h * 0.5)
    if shape == "diamond":
        board = make_box(0.4, 0.06, 0.4, color, "signboard")
        board.setH(45)
    else:
        board = make_box(0.5, 0.06, 0.35, color, "signboard")
    board.reparentTo(parent)
    board.setPos(x + 0.65, y, wall_h * 0.32)


def _add_stone_quoins(house, w, d, wall_h, color):
    """Alternating protruding corner blocks - the 3D stand-in for the
    reference's stone-block wall pattern (used on stone buildings)."""
    n_blocks = max(3, int(wall_h / 0.6))
    for cx, cy in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)):
        for i in range(n_blocks):
            z = i * (wall_h / n_blocks)
            protrude = 0.06 if i % 2 == 0 else 0.0
            block = make_box(0.35 + protrude, 0.35 + protrude, wall_h / n_blocks * 0.85, color, "quoin")
            block.reparentTo(house)
            block.setPos(cx, cy, z)


def _add_smoke_puffs(parent, x, y, z, color=(0.55, 0.55, 0.58, 0.55), count=4):
    """A few static soft smoke-puff cubes above a chimney (not animated -
    keeps things simple, still reads as smoke)."""
    puffs = []
    for i in range(count):
        size = 0.22 + i * 0.05
        puff = make_box(size, size, size, color, "smoke")
        puff.reparentTo(parent)
        puff.setTransparency(True)
        puff.setPos(x + random.uniform(-0.1, 0.15) * i, y + random.uniform(-0.1, 0.15) * i, z + i * 0.35)
        puffs.append(puff)
    return puffs


def _house_collider(house, w, d, wall_h, roof_h):
    add_wall_colliders(house, _rect_points(w / 2 + 0.05, d / 2 + 0.05), wall_h + roof_h, "house_col")


def build_streetlamp(parent, x, y, post_h=2.6):
    """A Victorian-style cast-iron streetlamp: round tapered post, a small
    crossbar/cage, and a warm glowing lantern on top. Purely a static prop
    (no moving parts) - the glow is just an unlit bright box so it reads
    as 'lit' without needing a real light source per lamp."""
    lamp = NodePath("streetlamp")
    lamp.reparentTo(parent)
    lamp.setPos(x, y, 0)

    post_color = (0.08, 0.08, 0.09, 1)
    post = make_cylinder(0.06, post_h, post_color, segments=8, name="lamp_post")
    post.reparentTo(lamp)

    base = make_cylinder(0.14, 0.12, post_color, segments=8, name="lamp_base")
    base.reparentTo(lamp)

    cage_r = 0.16
    cage = make_cylinder(cage_r, 0.34, (0.25, 0.22, 0.12, 0.55), segments=8,
                          z0=post_h, top_cap=True, bottom_cap=True, name="lamp_cage")
    cage.reparentTo(lamp)
    cage.setTransparency(True)

    glow = make_box(0.16, 0.16, 0.2, (1.0, 0.82, 0.45, 0.95), "lamp_glow")
    glow.reparentTo(lamp)
    glow.setTransparency(True)
    glow.setPos(0, 0, post_h + 0.07)
    glow.setLightOff()

    cap = make_cylinder(cage_r + 0.06, 0.08, post_color, segments=8,
                         z0=post_h + 0.34, name="lamp_cap")
    cap.reparentTo(lamp)

    add_wall_colliders(lamp, _circle_points(0.08, 6), post_h, "lamp_col")
    return lamp


# ===========================================================================
#  UNIQUE BUILDINGS  (matching imagetest19's create_town_layout() types)
# ===========================================================================

def build_player_house(parent, x, y, yaw):
    """'Your House' - brown timber cottage (#8B4513/#654321) with the small
    lean-to extension on the side, from the reference drawing."""
    w, d, wall_h, roof_h = 4.4, 3.6, 3.0, 1.8
    wall_color = (0.545, 0.271, 0.075, 1)
    roof_color = (0.396, 0.263, 0.129, 1)

    house = NodePath("house"); house.reparentTo(parent)
    house.setPos(x, y, 0); house.setH(yaw)

    make_box(w, d, wall_h, wall_color, "walls").reparentTo(house)
    _half_timber_facade(house, w, d, wall_h, style=0)
    door_x = _add_door(house, w, d, wall_h)
    _add_window(house, w / 2 - 0.5, wall_h * 0.55, -d / 2 - 0.02)
    _add_flowerbox(house, w / 2 - 0.5, wall_h * 0.55, -d / 2 - 0.02)

    roof = make_gable_roof(w + 0.6, d + 0.6, roof_h, roof_color, "roof")
    roof.reparentTo(house); roof.setZ(wall_h)
    _add_beam(house, 0, 0, wall_h + roof_h, d + 0.6, 0.16, 0.16)

    # lean-to extension on the right, with a single-slope (shed) roof
    ext_w, ext_d, ext_h = 1.5, d * 0.75, wall_h * 0.6
    ext = make_box(ext_w, ext_d, ext_h, wall_color, "lean_to")
    ext.reparentTo(house); ext.setPos(w / 2 + ext_w / 2, 0, 0)
    shed = make_box(ext_w + 0.3, ext_d + 0.3, 0.12, roof_color, "lean_to_roof")
    shed.reparentTo(house)
    shed.setPos(w / 2 + ext_w / 2, 0, ext_h)
    shed.setP(-12)

    chimney = make_box(0.4, 0.4, roof_h + 0.7, (0.45, 0.42, 0.4, 1), "chimney")
    chimney.reparentTo(house)
    chimney.setPos(-w / 2 + 0.6, d / 2 - 0.6, wall_h - 0.1)
    _add_smoke_puffs(house, -w / 2 + 0.6, d / 2 - 0.6, wall_h + roof_h + 0.6)

    _house_collider(house, w + ext_w, d, wall_h, roof_h)
    return house


def build_library(parent, x, y, yaw):
    """Library - brown/tan (#5C4033/#4A3428), twin side wings + a rose
    window on the front gable, matching the reference's wing layout."""
    w, d, wall_h, roof_h = 5.6, 4.0, 3.4, 2.1
    wall_color = (0.361, 0.251, 0.20, 1)
    roof_color = (0.29, 0.204, 0.157, 1)

    house = NodePath("house"); house.reparentTo(parent)
    house.setPos(x, y, 0); house.setH(yaw)

    make_box(w, d, wall_h, wall_color, "walls").reparentTo(house)
    _half_timber_facade(house, w, d, wall_h, style=1)
    _add_door(house, w, d, wall_h, door_w=1.0, door_h=1.9)
    _add_window(house, -w / 2 + 0.6, wall_h * 0.6, -d / 2 - 0.02, glow=True)
    _add_window(house, w / 2 - 0.6, wall_h * 0.6, -d / 2 - 0.02, glow=True)

    roof = make_gable_roof(w + 0.6, d + 0.6, roof_h, roof_color, "roof")
    roof.reparentTo(house); roof.setZ(wall_h)
    _add_beam(house, 0, 0, wall_h + roof_h, d + 0.6, 0.16, 0.16)

    # rose window: a diamond-oriented glowing pane with a cross mullion
    rose_z = wall_h + roof_h * 0.35
    rose = make_box(0.5, 0.08, 0.5, (1.0, 0.9, 0.55, 0.9), "rose_window")
    rose.setH(45)
    rose.reparentTo(house)
    rose.setPos(0, -d / 2 - 0.35, rose_z)
    rose.setTransparency(True)
    for hpr in ((0, 0, 0), (0, 0, 90)):
        beam = make_box(0.55, 0.05, 0.05, BEAM_COLOR, "beam")
        beam.reparentTo(house)
        beam.setPos(0, -d / 2 - 0.33, rose_z)
        beam.setHpr(*hpr)

    # twin side wings, each a smaller gabled block
    wing_w, wing_d, wing_h, wing_roof_h = 1.9, d * 0.85, wall_h * 0.72, roof_h * 0.65
    for side in (-1, 1):
        wing_x = side * (w / 2 + wing_w / 2)
        wing = make_box(wing_w, wing_d, wing_h, wall_color, "wing")
        wing.reparentTo(house)
        wing.setPos(wing_x, 0, 0)
        _add_beam(house, wing_x, -wing_d / 2 - 0.01, 0, wing_w, 0.08, wing_h)
        _add_beam(house, wing_x, wing_d / 2 + 0.01, 0, wing_w, 0.08, wing_h)
        wing_roof = make_gable_roof(wing_w + 0.4, wing_d + 0.4, wing_roof_h, roof_color, "wing_roof")
        wing_roof.reparentTo(house)
        wing_roof.setPos(wing_x, 0, wing_h)
        _add_window(house, wing_x, wing_h * 0.55, -wing_d / 2 - 0.02, size=0.4)

    total_half_w = w / 2 + wing_w + 0.3
    _house_collider(house, total_half_w * 2, max(d, wing_d), wall_h, roof_h)
    return house


def build_blacksmith(parent, x, y, yaw):
    """Blacksmith Forge - dark stone (#2C2C2C/#1A1A1A), stone quoins instead
    of timber beams, chimney w/ smoke, forge glow, and an anvil out front."""
    w, d, wall_h, roof_h = 4.6, 4.6, 3.0, 1.6
    wall_color = (0.173, 0.173, 0.173, 1)
    roof_color = (0.10, 0.10, 0.10, 1)
    stone_color = (0.42, 0.40, 0.38, 1)

    house = NodePath("house"); house.reparentTo(parent)
    house.setPos(x, y, 0); house.setH(yaw)

    make_box(w, d, wall_h, wall_color, "walls").reparentTo(house)
    _add_stone_quoins(house, w, d, wall_h, stone_color)

    # forge opening - dark inset with an orange glow
    forge_w, forge_h = 1.4, 1.5
    forge = make_box(forge_w, 0.1, forge_h, (0.06, 0.04, 0.02, 1), "forge_opening")
    forge.reparentTo(house)
    forge.setPos(0, -d / 2 - 0.02, 0.02)
    glow = make_box(forge_w * 0.6, 0.05, forge_h * 0.5, (1.0, 0.45, 0.05, 0.9), "forge_glow")
    glow.reparentTo(house)
    glow.setTransparency(True)
    glow.setPos(0, -d / 2 - 0.04, 0.1)

    # anvil out front
    anvil_base = make_box(0.3, 0.5, 0.35, (0.2, 0.2, 0.2, 1), "anvil_base")
    anvil_base.reparentTo(house)
    anvil_base.setPos(1.4, -d / 2 - 0.6, 0)
    anvil_top = make_box(0.55, 0.3, 0.15, (0.25, 0.25, 0.25, 1), "anvil_top")
    anvil_top.reparentTo(house)
    anvil_top.setPos(1.4, -d / 2 - 0.6, 0.35)

    roof = make_gable_roof(w + 0.5, d + 0.5, roof_h, roof_color, "roof")
    roof.reparentTo(house); roof.setZ(wall_h)

    chimney = make_box(0.5, 0.5, roof_h + 1.4, (0.3, 0.3, 0.3, 1), "chimney")
    chimney.reparentTo(house)
    chimney.setPos(w / 2 - 0.7, d / 2 - 0.7, wall_h - 0.1)
    _add_smoke_puffs(house, w / 2 - 0.7, d / 2 - 0.7, wall_h + roof_h + 1.4, count=5)

    _house_collider(house, w, d, wall_h, roof_h)
    return house


def build_enchanter_tower(parent, x, y, yaw):
    """Enchanter Tower - tall, narrow, purple/violet (#6B4C9A/#4A3368),
    stepped pyramid roof, glowing orb finial."""
    w, d, wall_h = 3.0, 3.0, 6.5
    roof_h = 2.4
    wall_color = (0.42, 0.30, 0.604, 1)
    roof_color = (0.29, 0.20, 0.408, 1)

    house = NodePath("house"); house.reparentTo(parent)
    house.setPos(x, y, 0); house.setH(yaw)

    make_box(w, d, wall_h, wall_color, "walls").reparentTo(house)
    _add_stone_quoins(house, w, d, wall_h, (0.35, 0.25, 0.5, 1))
    _add_door(house, w, d, wall_h, door_w=0.7, door_h=1.6, color=(0.2, 0.14, 0.3, 1))

    # tall glowing arched window partway up
    _add_window(house, 0, wall_h * 0.7, -d / 2 - 0.02, size=0.6, glow=True)
    _add_window(house, 0, wall_h * 0.4, d / 2 + 0.02, size=0.5, glow=True)

    roof = make_pyramid_roof(w + 0.4, d + 0.4, roof_h, roof_color, "roof")
    roof.reparentTo(house); roof.setZ(wall_h)

    orb = make_box(0.35, 0.35, 0.35, (0.75, 0.4, 1.0, 0.85), "orb")
    orb.reparentTo(house)
    orb.setTransparency(True)
    orb.setPos(0, 0, wall_h + roof_h + 0.2)

    # thin glowing rune squiggles winding partway up the side face,
    # echoing the reference image's carved/glowing markings on the tower.
    rune_color = (0.55, 0.85, 1.0, 0.85)
    for i in range(5):
        rz = 0.6 + i * 1.0
        rune = make_box(0.06, 0.06, 0.35 + (i % 2) * 0.15, rune_color, "rune")
        rune.reparentTo(house)
        rune.setTransparency(True)
        rune.setLightOff()
        rune.setPos(w / 2 + 0.015, (-1 if i % 2 else 1) * (d / 2 - 0.4), rz)
        rune.setH(random.uniform(-20, 20))

    _house_collider(house, w, d, wall_h, roof_h)
    return house


def build_alchemist_shop(parent, x, y, yaw):
    """Alchemist Shop - green (#228B22/#1B6B1B), has_sign=True, plus a
    giant 'bottle' silo beside the shop echoing the reference's bottle
    shape/glass-green theme."""
    w, d, wall_h, roof_h = 3.6, 3.2, 2.7, 1.5
    wall_color = (0.133, 0.545, 0.133, 1)
    roof_color = (0.106, 0.42, 0.106, 1)

    house = NodePath("house"); house.reparentTo(parent)
    house.setPos(x, y, 0); house.setH(yaw)

    make_box(w, d, wall_h, wall_color, "walls").reparentTo(house)
    _half_timber_facade(house, w, d, wall_h, style=1)
    _add_door(house, w, d, wall_h)
    _add_window(house, w / 2 - 0.45, wall_h * 0.55, -d / 2 - 0.02, size=0.45)

    roof = make_gable_roof(w + 0.5, d + 0.5, roof_h, roof_color, "roof")
    roof.reparentTo(house); roof.setZ(wall_h)

    # giant bottle: wide base -> narrow neck -> small cap, glassy teal-green
    bottle_x = w / 2 + 1.0
    bottle_color = (0.25, 0.55, 0.35, 0.75)
    bottle_base = make_box(0.9, 0.9, 1.6, bottle_color, "bottle_base")
    bottle_base.reparentTo(house)
    bottle_base.setTransparency(True)
    bottle_base.setPos(bottle_x, 0, 0)
    bottle_neck = make_box(0.4, 0.4, 0.8, bottle_color, "bottle_neck")
    bottle_neck.reparentTo(house)
    bottle_neck.setTransparency(True)
    bottle_neck.setPos(bottle_x, 0, 1.6)
    bottle_cap = make_box(0.5, 0.5, 0.25, (0.3, 0.18, 0.08, 1), "bottle_cap")
    bottle_cap.reparentTo(house)
    bottle_cap.setPos(bottle_x, 0, 2.4)

    # a few small potion bottles hanging under the front eave, like the
    # reference image's cluster of bottles clinging to the alchemist's wall.
    hang_colors = [(0.55, 0.85, 0.4, 0.8), (0.8, 0.35, 0.75, 0.75), (0.3, 0.65, 0.55, 0.8)]
    hang_xs = [-w / 2 + 0.4, -w / 2 + 1.0, -w / 2 + 1.6]
    for hx_, color in zip(hang_xs, hang_colors):
        cord = make_box(0.03, 0.03, 0.2, (0.25, 0.2, 0.12, 1), "cord")
        cord.reparentTo(house)
        cord.setPos(hx_, -d / 2 - 0.05, wall_h - 0.05)
        bottle = make_box(0.16, 0.16, 0.3, color, "hang_bottle")
        bottle.reparentTo(house)
        bottle.setTransparency(True)
        bottle.setPos(hx_, -d / 2 - 0.05, wall_h - 0.3)

    _add_hanging_sign(house, -w / 2 - 0.1, -d / 2 - 0.3, wall_h, (0.15, 0.4, 0.15, 1))

    _house_collider(house, w + 2.4, d, wall_h, roof_h)
    return house


def build_bakery_inn(parent, x, y, yaw):
    """Bakery/Inn - warm orange (#D2691E/#A0522D), has_sign=True, the
    largest footprint of the shops, with an oven chimney and outdoor tables."""
    w, d, wall_h, roof_h = 5.6, 4.2, 3.1, 1.8
    wall_color = (0.824, 0.412, 0.118, 1)
    roof_color = (0.627, 0.322, 0.176, 1)

    house = NodePath("house"); house.reparentTo(parent)
    house.setPos(x, y, 0); house.setH(yaw)

    make_box(w, d, wall_h, wall_color, "walls").reparentTo(house)
    _half_timber_facade(house, w, d, wall_h, style=0)
    _add_door(house, w, d, wall_h, door_w=1.0, door_h=1.8)
    for wx in (-w / 2 + 0.7, w / 2 - 0.7):
        _add_window(house, wx, wall_h * 0.55, -d / 2 - 0.02, glow=True)

    roof = make_gable_roof(w + 0.6, d + 0.6, roof_h, roof_color, "roof")
    roof.reparentTo(house); roof.setZ(wall_h)
    _add_beam(house, 0, 0, wall_h + roof_h, d + 0.6, 0.16, 0.16)

    chimney = make_box(0.45, 0.45, roof_h + 1.0, (0.5, 0.42, 0.35, 1), "chimney")
    chimney.reparentTo(house)
    chimney.setPos(w / 2 - 0.7, d / 2 - 0.7, wall_h - 0.1)
    _add_smoke_puffs(house, w / 2 - 0.7, d / 2 - 0.7, wall_h + roof_h + 1.0)

    _add_hanging_sign(house, -w / 2 - 0.1, -d / 2 - 0.3, wall_h, (0.55, 0.35, 0.15, 1))

    # a couple of outdoor tables
    for i, tx in enumerate((-1.2, 1.2)):
        table = make_box(0.7, 0.7, 0.45, (0.4, 0.25, 0.12, 1), "table")
        table.reparentTo(house)
        table.setPos(tx, -d / 2 - 1.3, 0)

    _house_collider(house, w, d, wall_h, roof_h)
    return house


def build_jeweler(parent, x, y, yaw):
    """Jeweler - pink (#DB7093/#C25876), has_sign=True, small shop with a
    diamond-shaped hanging sign."""
    w, d, wall_h, roof_h = 3.2, 3.0, 2.6, 1.4
    wall_color = (0.859, 0.439, 0.576, 1)
    roof_color = (0.761, 0.345, 0.463, 1)

    house = NodePath("house"); house.reparentTo(parent)
    house.setPos(x, y, 0); house.setH(yaw)

    make_box(w, d, wall_h, wall_color, "walls").reparentTo(house)
    _half_timber_facade(house, w, d, wall_h, style=1)
    _add_door(house, w, d, wall_h, door_w=0.7, door_h=1.5)
    _add_window(house, w / 2 - 0.4, wall_h * 0.55, -d / 2 - 0.02, size=0.4, glow=True)

    roof = make_gable_roof(w + 0.5, d + 0.5, roof_h, roof_color, "roof")
    roof.reparentTo(house); roof.setZ(wall_h)

    _add_hanging_sign(house, -w / 2 - 0.1, -d / 2 - 0.3, wall_h, (0.85, 0.85, 0.95, 1), shape="diamond")

    _house_collider(house, w, d, wall_h, roof_h)
    return house


def build_trader(parent, x, y, yaw):
    """General Trader - blue (#4682B4/#36648B), has_sign=True, with crates
    and barrels stacked outside suggesting trade goods."""
    w, d, wall_h, roof_h = 4.0, 3.4, 2.8, 1.5
    wall_color = (0.275, 0.51, 0.706, 1)
    roof_color = (0.212, 0.392, 0.545, 1)

    house = NodePath("house"); house.reparentTo(parent)
    house.setPos(x, y, 0); house.setH(yaw)

    make_box(w, d, wall_h, wall_color, "walls").reparentTo(house)
    _half_timber_facade(house, w, d, wall_h, style=0)
    _add_door(house, w, d, wall_h)
    _add_window(house, w / 2 - 0.45, wall_h * 0.55, -d / 2 - 0.02, size=0.45)

    roof = make_gable_roof(w + 0.5, d + 0.5, roof_h, roof_color, "roof")
    roof.reparentTo(house); roof.setZ(wall_h)

    _add_hanging_sign(house, -w / 2 - 0.1, -d / 2 - 0.3, wall_h, (0.2, 0.3, 0.45, 1))

    # crates + a barrel out front
    for i, (cx, cz, rot) in enumerate([(-1.3, 0, 10), (-1.6, 0.5, -8), (1.3, 0, 0)]):
        crate = make_box(0.5, 0.5, 0.5, (0.45, 0.32, 0.16, 1), "crate")
        crate.reparentTo(house)
        crate.setPos(cx, -d / 2 - 1.0, cz)
        crate.setH(rot)
    barrel = make_box(0.45, 0.45, 0.6, (0.35, 0.24, 0.12, 1), "barrel")
    barrel.reparentTo(house)
    barrel.setPos(1.6, -d / 2 - 1.0, 0)

    _house_collider(house, w, d, wall_h, roof_h)
    return house


# ===========================================================================
#  ENEMIES  -  Dungeon 1 / Bandit's Camp pool (Swordman, Spearman, Archer),
#  matching imagetest19's create_enemy_types_by_dungeon()[1] stats, built
#  from plain spheres/boxes (this world's version of the Tkinter game's
#  flat oval/hexagon/rectangle shapes).
# ===========================================================================

ENEMY_DETECT_RANGE = 22.0
ENEMY_MELEE_RANGE = 2.4
ENEMY_ARCHER_RANGE = 20.0
ENEMY_SWING_DURATION = 0.4
ARROW_SPEED = 26.0
ARROW_LIFETIME = 3.0
ARROW_HIT_RADIUS = 1.0


class Enemy3D:
    """A single active enemy: world position, stats copied straight from
    imagetest19's Dungeon 1 pool, a simple wander/chase/attack state
    machine, and references to the NodePaths GameApp needs to animate
    (weapon pivot for the melee swing, health bar for damage feedback)."""

    def __init__(self, name, hp, atk, spd, role, x, y, np, weapon_pivot, hp_bar_fg, home_np):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.spd = spd
        self.role = role            # "melee" or "ranged"
        self.x = x
        self.y = y
        self.np = np                 # root NodePath (position/heading)
        self.weapon_pivot = weapon_pivot
        self.hp_bar_fg = hp_bar_fg
        self.home_np = home_np       # NodePath removed on death (parent of everything)
        self.state = "idle"          # idle -> chase -> attack
        self.attacking = False
        self.swing_start = 0.0
        self.damage_applied = False
        self.last_attack = -999.0
        self.attack_cooldown = 1.3 if role == "melee" else 1.6
        self.alive = True


def _make_enemy_healthbar(parent, z, width=0.9):
    """A simple 2-box health bar (dark background + red fill) floating
    above the enemy's head, always facing the camera."""
    root = parent.attachNewNode("hp_bar_root")
    root.setPos(0, 0, z)
    root.setBillboardPointEye()

    bg = make_box(width, 0.03, 0.11, (0.15, 0.03, 0.03, 0.9), "hp_bg")
    bg.reparentTo(root)
    bg.setX(-width / 2)
    bg.setTransparency(True)

    fg_pivot = root.attachNewNode("hp_fg_pivot")
    fg_pivot.setPos(-width / 2, -0.01, 0)
    fg = make_box(width, 0.03, 0.09, (0.85, 0.15, 0.15, 1), "hp_fg")
    fg.reparentTo(fg_pivot)
    fg.setX(width / 2)
    fg.setTransparency(True)

    return fg_pivot


def _build_enemy_base(parent, x, y, yaw=0.0):
    """Shared root NodePath + collision-free positioning for every enemy
    type below (enemies push the player via the same wall-collision system
    as buildings is overkill for a mobile unit, so they're visual/AI only -
    the player can walk into them, matching a simple prototype's scope)."""
    root = NodePath("enemy")
    root.reparentTo(parent)
    root.setPos(x, y, 0)
    root.setH(yaw)
    return root


def build_arrow_model(parent):
    """A real-looking arrow: thin wooden shaft, a pale metal point at the
    front, and 2 angled fletching fins at the back - instead of one plain
    stretched box. Built along local +Y so it lines up with the H-heading
    math in _fire_arrow (forward = +Y at H=0)."""
    arrow = NodePath("arrow")

    shaft = make_box(0.035, 0.38, 0.035, (0.35, 0.22, 0.1, 1), "arrow_shaft")
    shaft.reparentTo(arrow)

    tip = make_box(0.05, 0.16, 0.05, (0.55, 0.55, 0.58, 1), "arrow_tip")
    tip.reparentTo(arrow)
    tip.setY(0.27)
    tip.setScale(1.0, 1.0, 1.0)
    tip_end = make_box(0.015, 0.06, 0.015, (0.55, 0.55, 0.58, 1), "arrow_tip_point")
    tip_end.reparentTo(arrow)
    tip_end.setY(0.38)

    for ang in (35, -35):
        fin = make_box(0.12, 0.09, 0.012, (0.88, 0.86, 0.8, 0.95), "arrow_fin")
        fin.reparentTo(arrow)
        fin.setTransparency(True)
        fin.setPos(0, -0.15, 0)
        fin.setR(ang)

    arrow.reparentTo(parent)
    return arrow


def build_swordman(parent, x, y):
    """Swordman - 60hp/5atk melee, oval-brown in the Tkinter version.
    Built as a sphere body + sphere head, brown, with a sword held out in
    front of the hand pivot so a yaw sweep actually traces a wide slash
    arc in front of the body, instead of just spinning in place."""
    root = _build_enemy_base(parent, x, y)
    brown = (0.45, 0.30, 0.16, 1)

    body = make_sphere(0.55, brown, name="body")
    body.reparentTo(root)
    body.setPos(0, 0, 0.75)
    body.setScale(1.0, 1.0, 1.3)

    head = make_sphere(0.28, (0.75, 0.6, 0.45, 1), name="head")
    head.reparentTo(root)
    head.setPos(0, 0, 1.55)

    pivot = root.attachNewNode("weapon_pivot")
    pivot.setPos(0.5, 0.1, 1.0)
    hilt = make_box(0.09, 0.22, 0.09, (0.25, 0.15, 0.06, 1), "sword_hilt")
    hilt.reparentTo(pivot)
    hilt.setPos(-0.045, -0.11, -0.045)
    blade = make_box(0.07, 0.85, 0.09, (0.75, 0.75, 0.8, 1), "sword_blade")
    blade.reparentTo(pivot)
    blade.setPos(-0.035, 0.1, -0.045)

    hp_bar = _make_enemy_healthbar(root, 2.05)

    enemy = Enemy3D("Swordman", 60, 5, 2.4, "melee", x, y, root, pivot, hp_bar, root)
    return enemy


def build_spearman(parent, x, y):
    """Spearman - 50hp/5atk melee, hexagon-brown in the Tkinter version.
    Sphere body (matching the other two enemy types) with a long spear on
    a forward-stab pivot."""
    root = _build_enemy_base(parent, x, y)
    brown = (0.40, 0.27, 0.15, 1)

    body = make_sphere(0.5, brown, name="body")
    body.reparentTo(root)
    body.setPos(0, 0, 0.7)
    body.setScale(1.0, 1.0, 1.2)

    head = make_sphere(0.26, (0.75, 0.6, 0.45, 1), name="head")
    head.reparentTo(root)
    head.setPos(0, 0, 1.55)

    pivot = root.attachNewNode("weapon_pivot")
    pivot.setPos(0.35, 0.15, 1.05)
    shaft = make_box(0.06, 1.5, 0.06, (0.35, 0.22, 0.1, 1), "spear_shaft")
    shaft.reparentTo(pivot)
    shaft.setY(0.55)
    tip = make_box(0.1, 0.3, 0.1, (0.7, 0.7, 0.75, 1), "spear_tip")
    tip.reparentTo(pivot)
    tip.setY(1.45)

    hp_bar = _make_enemy_healthbar(root, 2.05)

    enemy = Enemy3D("Spearman", 50, 5, 1.8, "melee", x, y, root, pivot, hp_bar, root)
    return enemy


def build_archer(parent, x, y):
    """Archer - 35hp/6atk ranged, rectangle-brown in the Tkinter version.
    Sphere body (matching the other two enemy types) with a proper curved
    bow (two short segmented "C" limbs meeting at a grip, plus a string)
    instead of the old two flat slabs that all met at one point."""
    root = _build_enemy_base(parent, x, y)
    brown = (0.42, 0.29, 0.16, 1)

    body = make_sphere(0.45, brown, name="body")
    body.reparentTo(root)
    body.setPos(0, 0, 0.85)
    body.setScale(1.0, 1.0, 1.45)

    head = make_sphere(0.25, (0.75, 0.6, 0.45, 1), name="head")
    head.reparentTo(root)
    head.setPos(0, 0, 1.72)

    pivot = root.attachNewNode("weapon_pivot")
    pivot.setPos(0.4, 0.05, 1.1)

    bow_wood = (0.32, 0.2, 0.1, 1)
    bow_grip = make_box(0.06, 0.06, 0.24, (0.25, 0.15, 0.08, 1), "bow_grip")
    bow_grip.reparentTo(pivot)
    bow_grip.setZ(-0.12)

    for direction in (1, -1):
        limb = make_box(0.045, 0.045, 0.42, bow_wood, "bow_limb")
        limb.reparentTo(pivot)
        limb.setZ(0.12 * direction)
        if direction > 0:
            limb.setP(-12)          # top limb: extends up, curves slightly forward
        else:
            limb.setP(180 + 12)     # bottom limb: flipped to extend down, mirrored curve

    string = make_box(0.012, 0.012, 0.92, (0.85, 0.82, 0.75, 0.9), "bow_string")
    string.reparentTo(pivot)
    string.setTransparency(True)
    string.setPos(0, -0.07, -0.46)

    hp_bar = _make_enemy_healthbar(root, 2.2)

    enemy = Enemy3D("Archer", 35, 6, 1.2, "ranged", x, y, root, pivot, hp_bar, root)
    return enemy


def build_campfire(parent, x, y):
    logs_color = (0.30, 0.19, 0.10, 1)
    for ang in (0, 60, 120):
        log = make_box(0.14, 1.0, 0.14, logs_color, "log")
        log.reparentTo(parent)
        log.setPos(x, y, 0.08)
        log.setH(ang)
    glow = make_box(0.35, 0.35, 0.5, (1.0, 0.5, 0.08, 0.85), "fire_glow")
    glow.reparentTo(parent)
    glow.setTransparency(True)
    glow.setPos(x, y, 0.25)


def build_tent(parent, x, y, yaw, color=(0.25, 0.5, 0.25, 1)):
    w, d, h, roof_h = 2.2, 2.6, 1.3, 1.1
    tent = NodePath("tent")
    tent.reparentTo(parent)
    tent.setPos(x, y, 0)
    tent.setH(yaw)
    base = make_box(w, d, h, color, "tent_base")
    base.reparentTo(tent)
    roof = make_gable_roof(w + 0.2, d + 0.2, roof_h, (color[0] * 0.8, color[1] * 0.8, color[2] * 0.8, 1), "tent_roof")
    roof.reparentTo(tent)
    roof.setZ(h)
    return tent


def build_portal_arch(parent, x, y, yaw, glow_color, name="portal"):
    """A simple stone archway with a glowing, semi-transparent 'pane' in
    the middle - the visual language for 'this is a teleporter'. Now only
    used for the dungeon-side return gate (the town-side entrance is the
    walkable camp/tent instead - see build_forest_camp)."""
    arch = NodePath(name)
    arch.reparentTo(parent)
    arch.setPos(x, y, 0)
    arch.setH(yaw)

    stone = (0.4, 0.38, 0.36, 1)
    for side in (-1, 1):
        pillar = make_box(0.4, 0.4, 2.7, stone, "portal_pillar")
        pillar.reparentTo(arch)
        pillar.setPos(side * 1.3, 0, 0)
    lintel = make_box(3.0, 0.5, 0.5, stone, "portal_lintel")
    lintel.reparentTo(arch)
    lintel.setPos(0, 0, 2.7)

    pane = make_box(2.1, 0.06, 2.2, glow_color, "portal_pane")
    pane.reparentTo(arch)
    pane.setTransparency(True)
    pane.setLightOff()
    pane.setPos(0, 0, 1.4)

    for side in (-1, 1):
        cx = side * 1.3
        half = 0.25
        pillar_pts = [(cx - half, -half), (cx + half, -half),
                      (cx + half, half), (cx - half, half)]
        add_wall_colliders(arch, pillar_pts, 2.7, "portal_col")
    return arch, pane


def build_chief_tent(parent, x, y, yaw, color=(0.55, 0.18, 0.16, 1)):
    """A bigger, fancier command tent for the walkable forest camp - pyramid
    roof, a banner pole + flag on top, and a dark entrance flap. Meant to
    read clearly as "this is the destination" at the end of the tree-free
    path, unlike the small plain tents used elsewhere."""
    w, d, h, roof_h = 4.2, 4.6, 2.0, 2.0
    tent = NodePath("chief_tent")
    tent.reparentTo(parent)
    tent.setPos(x, y, 0)
    tent.setH(yaw)

    base = make_box(w, d, h, color, "tent_base")
    base.reparentTo(tent)
    base.setPos(-w / 2, -d / 2, 0)

    trim = (color[0] * 0.6, color[1] * 0.6, color[2] * 0.6, 1)
    roof = make_pyramid_roof(w + 0.3, d + 0.3, roof_h, trim, "tent_roof")
    roof.reparentTo(tent)
    roof.setPos(0, 0, h)

    flap = make_box(1.1, 0.05, h * 0.85, (0.12, 0.08, 0.06, 1), "tent_flap")
    flap.reparentTo(tent)
    flap.setPos(-0.55, d / 2 + 0.01, 0)

    pole = make_box(0.08, 0.08, roof_h + 0.9, (0.3, 0.22, 0.12, 1), "banner_pole")
    pole.reparentTo(tent)
    pole.setPos(-0.04, -0.04, h)

    flag = make_box(0.05, 0.7, 0.45, (0.75, 0.15, 0.15, 1), "banner_flag")
    flag.reparentTo(tent)
    flag.setTransparency(True)
    flag.setPos(-0.025, 0.02, h + roof_h + 0.35)

    add_wall_colliders(tent, _rect_points(w / 2, d / 2), h, "tent_col")
    return tent


CAMP_POS = (0.0, 100.0)                # a real, walkable clearing inside the
                                        # forest - reached by following the
                                        # tree-free north path out from town
CAMP_CLEARING_R = 14.0
NORTH_CLEARING_LEN = CAMP_POS[1] + CAMP_CLEARING_R  # tree-free path stops
                                        # right at the clearing's far edge -
                                        # it does NOT continue past the camp
                                        # into the rest of the forest.

DUNGEON_1_POS = (0.0, 4000.0)          # the actual dungeon interior is still
                                        # its own separate space, entered by
                                        # walking up to the camp's tent and
                                        # pressing C (not a floating portal
                                        # arch anymore - see build_forest_camp)


def build_forest_camp(parent, avoid_boxes):
    """The Bandit's Camp entrance is now a real clearing inside the forest
    (no floating portal arch) - a circular patch with no trees (added to
    avoid_boxes below, and the approach path is kept clear up to here via
    NORTH_CLEARING_LEN), holding a campfire and a big chief's tent. Standing
    near the tent still offers 'Press C' to enter the actual dungeon, which
    remains a separate instanced space of its own."""
    cx, cy = CAMP_POS

    clearing = make_cylinder(CAMP_CLEARING_R, 0.05, (0.42, 0.34, 0.22, 1),
                              segments=28, name="camp_clearing")
    clearing.reparentTo(parent)
    clearing.setPos(cx, cy, 0.008)

    build_campfire(parent, cx, cy - 3.0)
    tent = build_chief_tent(parent, cx, cy + 3.5, 180)

    for (ox, oy, rot) in [(-5.5, -4.5, 15), (-4.7, -3.6, -20), (5.0, -5.5, 40)]:
        crate = make_box(0.55, 0.55, 0.55, (0.42, 0.30, 0.15, 1), "crate")
        crate.reparentTo(parent)
        crate.setPos(cx + ox, cy + oy, 0)
        crate.setH(rot)

    # keep the forest's procedural trees out of the whole clearing, not
    # just the narrow path strip
    avoid_boxes.append((cx, cy, CAMP_CLEARING_R + 2.0))

    return {"prompt_pos": (cx, cy + 3.0)}


# ---------------------------------------------------------------------------
#  DUNGEON  -  5x2 grid of 10 connected rooms (Bandit's Camp interior)
# ---------------------------------------------------------------------------

DUNGEON_ROOM_W = 12.0
DUNGEON_ROOM_D = 9.0
DUNGEON_CORR_LEN = 5.0
DUNGEON_CORR_W = 2.6
DUNGEON_WALL_H = 3.4
DUNGEON_WALL_T = 0.3
DUNGEON_WALL_COLOR = (0.32, 0.29, 0.27, 1)
DUNGEON_FLOOR_COLOR = (0.30, 0.26, 0.21, 1)


def _dungeon_wall_run(parent, axis, fixed_coord, center_along, half_extent,
                       gap_center=None, gap_width=0.0):
    """One straight, axis-aligned wall run (all dungeon rooms are plain
    rectangles, so no rotation math is needed anywhere here). axis='x'
    means the wall runs along X at Y=fixed_coord (a north/south wall);
    axis='y' means it runs along Y at X=fixed_coord (an east/west wall).
    An optional centered gap punches a doorway through to a neighbor."""
    if gap_width > 0:
        a0, a1 = center_along - half_extent, gap_center - gap_width / 2
        b0, b1 = gap_center + gap_width / 2, center_along + half_extent
        segments = [(a0, a1), (b0, b1)]
    else:
        segments = [(center_along - half_extent, center_along + half_extent)]

    for s0, s1 in segments:
        if s1 - s0 <= 0.01:
            continue
        seg_len = s1 - s0
        mid = (s0 + s1) / 2
        if axis == "x":
            wall = make_box(seg_len, DUNGEON_WALL_T, DUNGEON_WALL_H, DUNGEON_WALL_COLOR, "dwall")
            wall.reparentTo(parent)
            wall.setPos(mid - seg_len / 2, fixed_coord - DUNGEON_WALL_T / 2, 0)
            pts = [(mid - seg_len / 2, fixed_coord - DUNGEON_WALL_T / 2),
                   (mid + seg_len / 2, fixed_coord - DUNGEON_WALL_T / 2),
                   (mid + seg_len / 2, fixed_coord + DUNGEON_WALL_T / 2),
                   (mid - seg_len / 2, fixed_coord + DUNGEON_WALL_T / 2)]
        else:
            wall = make_box(DUNGEON_WALL_T, seg_len, DUNGEON_WALL_H, DUNGEON_WALL_COLOR, "dwall")
            wall.reparentTo(parent)
            wall.setPos(fixed_coord - DUNGEON_WALL_T / 2, mid - seg_len / 2, 0)
            pts = [(fixed_coord - DUNGEON_WALL_T / 2, mid - seg_len / 2),
                   (fixed_coord + DUNGEON_WALL_T / 2, mid - seg_len / 2),
                   (fixed_coord + DUNGEON_WALL_T / 2, mid + seg_len / 2),
                   (fixed_coord - DUNGEON_WALL_T / 2, mid + seg_len / 2)]
        add_wall_colliders(parent, pts, DUNGEON_WALL_H, "dwall_col")


def build_dungeon_room(parent, cx, cy, doors):
    """doors: dict with keys 'n','s','e','w' -> bool, whether a doorway
    connects to a neighboring room on that side."""
    hw, hd = DUNGEON_ROOM_W / 2, DUNGEON_ROOM_D / 2

    floor = make_box(DUNGEON_ROOM_W, DUNGEON_ROOM_D, 0.1, DUNGEON_FLOOR_COLOR, "dfloor")
    floor.reparentTo(parent)
    floor.setPos(cx - hw, cy - hd, -0.1)

    _dungeon_wall_run(parent, "x", cy + hd, cx, hw,
                       gap_center=cx if doors.get("n") else None,
                       gap_width=DUNGEON_CORR_W if doors.get("n") else 0.0)
    _dungeon_wall_run(parent, "x", cy - hd, cx, hw,
                       gap_center=cx if doors.get("s") else None,
                       gap_width=DUNGEON_CORR_W if doors.get("s") else 0.0)
    _dungeon_wall_run(parent, "y", cx + hw, cy, hd,
                       gap_center=cy if doors.get("e") else None,
                       gap_width=DUNGEON_CORR_W if doors.get("e") else 0.0)
    _dungeon_wall_run(parent, "y", cx - hw, cy, hd,
                       gap_center=cy if doors.get("w") else None,
                       gap_width=DUNGEON_CORR_W if doors.get("w") else 0.0)


def _build_corridor(parent, axis, a0, a1, cross_center):
    """A short straight corridor (floor + 2 side walls) filling the gap
    between two adjacent rooms' doorways. axis='x' runs the corridor along
    X (connecting east/west neighbors); axis='y' runs it along Y
    (connecting north/south neighbors)."""
    length = a1 - a0
    mid = (a0 + a1) / 2
    if axis == "x":
        floor = make_box(length, DUNGEON_CORR_W, 0.1, DUNGEON_FLOOR_COLOR, "corr_floor")
        floor.reparentTo(parent)
        floor.setPos(mid - length / 2, cross_center - DUNGEON_CORR_W / 2, -0.1)
        for side in (-1, 1):
            wy = cross_center + side * (DUNGEON_CORR_W / 2 + DUNGEON_WALL_T / 2)
            _dungeon_wall_run(parent, "x", wy, mid, length / 2)
    else:
        floor = make_box(DUNGEON_CORR_W, length, 0.1, DUNGEON_FLOOR_COLOR, "corr_floor")
        floor.reparentTo(parent)
        floor.setPos(cross_center - DUNGEON_CORR_W / 2, mid - length / 2, -0.1)
        for side in (-1, 1):
            wx = cross_center + side * (DUNGEON_CORR_W / 2 + DUNGEON_WALL_T / 2)
            _dungeon_wall_run(parent, "y", wx, mid, length / 2)


def build_dungeon_grid(parent, base_x, base_y):
    """The Bandit's Camp interior: a 5-column x 2-row grid of 10 connected
    rooms (instead of one open clearing), built far outside the forest as
    its own separate space - reached only by pressing C at the camp tent,
    not by walking. Every horizontally/vertically adjacent room pair gets
    a connecting corridor. Enemies are spread across several rooms, and a
    return gate sits in the far corner room."""
    cols, rows = 5, 2
    step_x = DUNGEON_ROOM_W + DUNGEON_CORR_LEN
    step_y = DUNGEON_ROOM_D + DUNGEON_CORR_LEN

    def center(col, row):
        return (base_x + col * step_x, base_y + row * step_y)

    void_w = cols * step_x + 20
    void_d = rows * step_y + 20
    void_ground = make_box(void_w, void_d, 0.3, (0.09, 0.07, 0.1, 1), "dungeon_void")
    void_ground.reparentTo(parent)
    void_ground.setPos(base_x + (cols - 1) * step_x / 2 - void_w / 2,
                        base_y + (rows - 1) * step_y / 2 - void_d / 2, -0.15)

    for col in range(cols):
        for row in range(rows):
            cx, cy = center(col, row)
            doors = {"e": col < cols - 1, "w": col > 0,
                     "n": row < rows - 1, "s": row > 0}
            build_dungeon_room(parent, cx, cy, doors)
            if col < cols - 1:
                cx2, _ = center(col + 1, row)
                _build_corridor(parent, "x", cx + DUNGEON_ROOM_W / 2, cx2 - DUNGEON_ROOM_W / 2, cy)
            if row < rows - 1:
                _, cy2 = center(col, row + 1)
                _build_corridor(parent, "y", cy + DUNGEON_ROOM_D / 2, cy2 - DUNGEON_ROOM_D / 2, cx)

    # a handful of enemies spread across different rooms, rather than
    # populating all 10 at once
    enemy_specs = [
        (build_swordman, 1, 0), (build_spearman, 2, 0), (build_archer, 3, 1),
        (build_swordman, 0, 1), (build_spearman, 4, 0), (build_archer, 2, 1),
    ]
    enemies = []
    for builder_fn, col, row in enemy_specs:
        cx, cy = center(col, row)
        ox = random.uniform(-DUNGEON_ROOM_W / 4, DUNGEON_ROOM_W / 4)
        oy = random.uniform(-DUNGEON_ROOM_D / 4, DUNGEON_ROOM_D / 4)
        enemies.append(builder_fn(parent, cx + ox, cy + oy))

    arrival_pos = center(0, 0)
    far_cx, far_cy = center(cols - 1, rows - 1)
    return_pos = (far_cx, far_cy - 2.5)
    return_arch, return_pane = build_portal_arch(
        parent, return_pos[0], return_pos[1], 0,
        glow_color=(0.55, 0.35, 0.9, 0.75), name="return_portal")

    return {
        "enemies": enemies,
        "arrival_pos": arrival_pos,
        "return_trigger_pos": return_pos,
        "return_pane": return_pane,
    }




# ===========================================================================
#  FOUNTAIN  -  taller, with 4 curving curtains of spray
# ===========================================================================

def build_fountain(parent, radius=2.3):
    """A simple, classic fountain: a round base bowl, a stone cylinder
    rising from its center, and 4 dense curtains of falling water-particle
    quads cascading straight down the column's N/E/S/W faces into the
    bowl. Nothing here spins or orbits - the only motion is particles
    falling and a very slight water-surface bob, animated in
    GameApp._update_fountain."""
    fountain = NodePath("fountain")
    fountain.reparentTo(parent)

    stone = (0.62, 0.62, 0.6, 1)
    water = (0.25, 0.55, 0.75, 0.85)
    drop_color = (0.65, 0.85, 0.97, 0.85)

    base_r = radius
    basin_h = 0.55
    basin = make_cylinder(base_r, basin_h, stone, segments=24, name="basin")
    basin.reparentTo(fountain)

    water_z = basin_h - 0.1
    water_disc = make_cylinder(base_r - 0.2, 0.1, water, segments=24,
                                z0=water_z, top_cap=True, bottom_cap=False, name="water")
    water_disc.reparentTo(fountain)
    water_disc.setTransparency(True)

    col_r = 0.55
    col_h = 1.9
    column = make_cylinder(col_r, col_h, stone, segments=16, z0=basin_h, name="column")
    column.reparentTo(fountain)

    # thin overflow lip at the top the water "spills" from - static, no cap
    lip_z = basin_h + col_h
    lip = make_cylinder(col_r + 0.12, 0.12, stone, segments=16, z0=lip_z, name="lip")
    lip.reparentTo(fountain)

    top_z = lip_z
    bottom_z = water_z + 0.05

    # 4 curtains of falling water, one per cardinal side, each a dense
    # grid of small particles (rows = vertical layers, cols = lateral
    # spread) so it reads as a sheet of falling water rather than a jet.
    sides = [0, 90, 180, 270]           # N/E/S/W
    lateral_spread = 24                  # degrees either side of the cardinal
    n_cols = 6
    n_rows = 9
    curtain_r = col_r + 0.08             # hugs the column's outer surface

    particles = []
    for side_ang in sides:
        for ci in range(n_cols):
            lat = -lateral_spread + (2 * lateral_spread) * ci / (n_cols - 1)
            ang = math.radians(side_ang + lat)
            for ri in range(n_rows):
                drop = make_box(0.08, 0.08, 0.16, drop_color, "droplet")
                drop.reparentTo(fountain)
                drop.setTransparency(True)
                phase0 = (ri / n_rows) + (ci / n_cols) * 0.11
                particles.append({"np": drop, "ang": ang, "phase0": phase0})

    add_wall_colliders(fountain, _circle_points(base_r + 0.15, 8), basin_h, "fountain_col")

    return {
        "water_disc": water_disc, "water_base_z": water_z,
        "particles": particles, "curtain_r": curtain_r,
        "top_z": top_z, "bottom_z": bottom_z,
    }


# ===========================================================================
#  TREES  -  faceted (not axis-cube), tall; built/collided per-chunk
# ===========================================================================

TREE_TRUNK_COLOR = (0.30, 0.19, 0.10, 1)
TREE_LEAF_VARIANTS = [
    (0.14, 0.38, 0.13, 1), (0.18, 0.44, 0.16, 1), (0.11, 0.32, 0.11, 1),
    (0.20, 0.40, 0.09, 1), (0.16, 0.36, 0.20, 1),
]
# fixed (unscaled) tier layout - deterministic so collision height can be
# computed analytically without re-walking randomised geometry
TREE_TRUNK_H = 3.2
TREE_TIERS = [
    (3.2, 1.6, TREE_TRUNK_H - 0.3),
    (2.6, 1.5, TREE_TRUNK_H + 1.1),
    (2.0, 1.4, TREE_TRUNK_H + 2.35),
    (1.3, 1.3, TREE_TRUNK_H + 3.5),
    (0.7, 1.1, TREE_TRUNK_H + 4.55),
]
TREE_BASE_HEIGHT = TREE_TIERS[-1][2] + TREE_TIERS[-1][1] - TREE_TRUNK_H + TREE_TRUNK_H  # top of last tier


def build_tree_visual(parent, x, y, scale):
    """Trunk (tapered, 2-part) + 5 shrinking foliage tiers. Each tier is
    TWO overlapping boxes (one rotated 45 degrees) so the silhouette reads
    as faceted/octagonal rather than an obvious flat-sided cube - this is
    what breaks the 'Minecraft block' look while still only using boxes."""
    tree = NodePath("tree")
    tree.reparentTo(parent)
    tree.setPos(x, y, 0)
    tree.setH(random.uniform(0, 360))
    tree.setScale(scale)

    leaf_color = random.choice(TREE_LEAF_VARIANTS)

    trunk1 = make_box(0.5, 0.5, 1.6, TREE_TRUNK_COLOR, "trunk")
    trunk1.reparentTo(tree)
    trunk2 = make_box(0.34, 0.34, 1.6, TREE_TRUNK_COLOR, "trunk")
    trunk2.reparentTo(tree)
    trunk2.setZ(1.6)

    for tw, th, tz in TREE_TIERS:
        jitter_h = random.uniform(-8, 8)
        c1 = make_box(tw, tw, th, leaf_color, "foliage")
        c1.reparentTo(tree); c1.setPos(0, 0, tz); c1.setH(jitter_h)
        c2 = make_box(tw * 0.82, tw * 0.82, th * 0.92, leaf_color, "foliage")
        c2.reparentTo(tree); c2.setPos(0, 0, tz + th * 0.05); c2.setH(jitter_h + 45)

    return tree


def build_tree_collision(parent, x, y, scale):
    pts = _circle_points(0.34 * scale, 8)
    cnode = CollisionNode("tree_col")
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        poly = CollisionPolygon(
            Point3(x0, y0, 0), Point3(x1, y1, 0),
            Point3(x1, y1, TREE_BASE_HEIGHT * scale), Point3(x0, y0, TREE_BASE_HEIGHT * scale),
        )
        cnode.addSolid(poly)
    cnode.setIntoCollideMask(WALL_MASK)
    cnode.setFromCollideMask(0)
    col_np = parent.attachNewNode(cnode)
    col_np.setPos(x, y, 0)
    return col_np


# ===========================================================================
#  CHUNKED FOREST  -  a huge (~20x the radius / ~400x the area of the
#  original), TRULY LAZY forest: chunks are only generated the first time
#  the player gets near them (not pre-built for the whole world at start),
#  then cached and stashed/unstashed as the player moves (Minecraft-style
#  chunk loading). This is what keeps a world this size sustainable: cost
#  scales with how much ground the player has actually explored, never
#  with the total size of the world.
# ===========================================================================

CHUNK_SIZE = 20.0
FOREST_LOAD_RADIUS = 78.0
FOREST_START_RADIUS = 27.0                 # matches the forest's inner_radius
FOREST_INNER_RADIUS = 27.0                 # town edge / where the forest begins
FOREST_OUTER_RADIUS = 112.0 * 20.0         # ~20x farther out than the original edge
FOG_WALL_RADIUS = FOREST_OUTER_RADIUS + 40.0  # backdrop wall pushed out to match
TREE_DENSITY = 0.036                       # trees per square unit (matches original forest's density)
TOWN_FOG_DENSITY = 0.012                   # light haze in the open town square
FOREST_FOG_DENSITY = 0.055                 # thick, near-opaque fog once you're under the trees


def _generate_chunk_trees(cx, cy, inner_radius, outer_radius, avoid_boxes):
    """Deterministically generate this chunk's tree positions on demand.
    Seeded per-chunk (instead of using the global `random` stream) so a
    chunk that gets freed and later regenerated always comes back looking
    identical - the world doesn't need to keep every chunk in memory
    forever to stay consistent."""
    seed = (cx * 92_821 + cy * 68_917 + 1_013) & 0xFFFFFFFF
    rng = random.Random(seed)

    x0, y0 = cx * CHUNK_SIZE, cy * CHUNK_SIZE
    area = CHUNK_SIZE * CHUNK_SIZE
    expected = TREE_DENSITY * area
    n = int(expected) + (1 if rng.random() < (expected - int(expected)) else 0)

    trees = []
    for _ in range(n):
        px = rng.uniform(x0, x0 + CHUNK_SIZE)
        py = rng.uniform(y0, y0 + CHUNK_SIZE)
        r = math.hypot(px, py)
        if r < inner_radius or r > outer_radius:
            continue

        if abs(px) < 3.5 and abs(py) < NORTH_CLEARING_LEN:
            continue
        if abs(py) < 3.5 and abs(px) < 36:
            continue

        too_close = False
        for (bx, by, brad) in avoid_boxes:
            if (px - bx) ** 2 + (py - by) ** 2 < brad ** 2:
                too_close = True
                break
        if too_close:
            continue

        trees.append((px, py, rng.uniform(0.9, 1.6)))

    return trees


def _build_forest_chunk(parent, key, inner_radius, outer_radius, avoid_boxes):
    """Build (or return None for) a single forest chunk's geometry. Only
    called the first time a chunk is needed - never for the whole world
    up front."""
    cx, cy = key
    trees = _generate_chunk_trees(cx, cy, inner_radius, outer_radius, avoid_boxes)
    if not trees:
        return None

    visual_root = NodePath(f"chunk_v_{cx}_{cy}")
    visual_root.reparentTo(parent)
    collision_root = NodePath(f"chunk_c_{cx}_{cy}")
    collision_root.reparentTo(parent)

    for (px, py, scale) in trees:
        build_tree_visual(visual_root, px, py, scale)
        build_tree_collision(collision_root, px, py, scale)

    # merge every tree in this chunk into as few draw calls as possible -
    # this (plus lazy generation + streaming) is what keeps a forest this
    # size from lagging.
    visual_root.flattenStrong()

    return {
        "visual": visual_root, "collision": collision_root,
        "center": ((cx + 0.5) * CHUNK_SIZE, (cy + 0.5) * CHUNK_SIZE),
        "tree_count": len(trees),
    }


def _add_spoke_path(parent, hx, hy, plaza_r, color, curb_color, width=2.2):
    """A straight paved spoke (with curbs) from the edge of the plaza out
    to just short of a building at (hx, hy), oriented to point straight at
    it. Skipped if the building is too close to the plaza to need one."""
    dist = math.hypot(hx, hy)
    start_r = plaza_r
    end_r = dist - 3.0
    length = end_r - start_r
    if length < 0.75:
        return
    ang_deg = math.degrees(math.atan2(hy, hx))
    mid_r = (start_r + end_r) / 2.0
    ang_rad = math.radians(ang_deg)
    mx, my = mid_r * math.cos(ang_rad), mid_r * math.sin(ang_rad)
    heading = ang_deg - 90.0

    spoke = make_box(width, length, 0.05, color, "spoke")
    spoke.reparentTo(parent)
    spoke.setPos(mx, my, 0.01); spoke.setH(heading)

    for sign in (-1, 1):
        curb = make_box(0.22, length + 0.6, 0.06, curb_color, "spoke_curb")
        curb.reparentTo(parent)
        curb.setPos(mx, my, 0.008)
        curb.setH(heading)
        curb.setX(curb.getX() + sign * (width / 2 + 0.1) * math.cos(ang_rad + math.pi / 2))
        curb.setY(curb.getY() + sign * (width / 2 + 0.1) * math.sin(ang_rad + math.pi / 2))


def build_town(render):
    town_root = NodePath("town")
    town_root.reparentTo(render)

    # Ground plane sized to cover the whole world (town + the now much
    # bigger forest) out to the fog wall - it's a single flat box regardless
    # of size, so this costs nothing extra to render, but without it the
    # player would walk off the edge of a 260-unit patch into a void long
    # before reaching the new tree line.
    ground_span = FOG_WALL_RADIUS * 2.2
    ground = make_box(ground_span, ground_span, 0.2, GROUND_COLOR, "ground")
    ground.reparentTo(town_root)
    ground.setPos(0, 0, -0.2)

    # Paved circular plaza around the fountain, curbed cross-roads, and
    # short spokes connecting the plaza out to each building's front door -
    # a rounder, more "finished" road network instead of two bare crossed
    # strips of color.
    PATH_CURB_COLOR = (0.36, 0.31, 0.22, 1)
    plaza_r = 9.0
    plaza = make_cylinder(plaza_r, 0.05, PATH_COLOR, segments=32, name="plaza")
    plaza.reparentTo(town_root); plaza.setZ(0.01)
    plaza_curb = make_cylinder(plaza_r + 0.25, 0.09, PATH_CURB_COLOR, segments=32,
                                top_cap=False, name="plaza_curb")
    plaza_curb.reparentTo(town_root); plaza_curb.setZ(0.005)

    path_w, path_len = 4.0, 68.0
    path_ns = make_box(path_w, path_len, 0.05, PATH_COLOR, "path_ns")
    path_ns.reparentTo(town_root); path_ns.setZ(0.01)
    path_ew = make_box(path_len, path_w, 0.05, PATH_COLOR, "path_ew")
    path_ew.reparentTo(town_root); path_ew.setZ(0.01)

    # thin raised curbs flanking both roads
    for sign in (-1, 1):
        curb_ns = make_box(0.25, path_len + 1, 0.07, PATH_CURB_COLOR, "curb_ns")
        curb_ns.reparentTo(town_root)
        curb_ns.setPos(sign * (path_w / 2 + 0.1), 0, 0.01)
        curb_ew = make_box(path_len + 1, 0.25, 0.07, PATH_CURB_COLOR, "curb_ew")
        curb_ew.reparentTo(town_root)
        curb_ew.setPos(0, sign * (path_w / 2 + 0.1), 0.01)

    fountain_handles = build_fountain(town_root)

    # streetlamps ringing the plaza
    n_plaza_lamps = 8
    lamp_r = plaza_r + 1.3
    for i in range(n_plaza_lamps):
        ang = math.tau * i / n_plaza_lamps
        build_streetlamp(town_root, lamp_r * math.cos(ang), lamp_r * math.sin(ang))

    # streetlamps spaced out along the 4 road arms, just off to each side
    for r in (16.0, 26.0):
        for sign_r in (-1, 1):
            build_streetlamp(town_root, sign_r * r, path_w / 2 + 0.7)
            build_streetlamp(town_root, sign_r * r, -(path_w / 2 + 0.7))
            build_streetlamp(town_root, path_w / 2 + 0.7, sign_r * r)
            build_streetlamp(town_root, -(path_w / 2 + 0.7), sign_r * r)

    # Permanent backdrop wall, well outside the forest - never chunked or
    # stashed, colored to exactly match the fog. Caps every horizontal
    # sightline before it can reach the true sky, so gaps opened up by the
    # forest's chunk streaming can't reveal blue in the distance.
    # Height must scale with radius, not stay fixed: a wall's *angular*
    # size in the camera's view is roughly height/radius, so a wall that
    # was tall enough at radius=122 becomes an invisible sliver once pushed
    # out to radius~2280 - that's what let the raw blue background back in
    # after the forest was extended. Keep the original ratio so it still
    # fills the same slice of the horizon.
    _fog_wall_height = FOG_WALL_RADIUS * (16.0 / 122.0)
    fog_wall = build_fog_wall(radius=FOG_WALL_RADIUS, height=_fog_wall_height, color=FOG_COLOR)
    fog_wall.reparentTo(town_root)

    # 8 unique buildings, positioned around the square (radial layout),
    # each matching a type/colors from imagetest19's create_town_layout()
    builders = [
        (build_player_house, -14, -14, 45),
        (build_library, 15, -15, -45),
        (build_blacksmith, -15, 15, 135),
        (build_enchanter_tower, 15, 15, -135),
        (build_alchemist_shop, -23, 0, 90),
        (build_bakery_inn, 24, 0, -90),
        (build_jeweler, 0, -23, 0),
        (build_trader, 0, 23, 180),
    ]
    house_avoid = [(0, 0, 3.6)]
    for builder_fn, hx, hy, hyaw in builders:
        builder_fn(town_root, hx, hy, hyaw)
        house_avoid.append((hx, hy, 6.5))
        _add_spoke_path(town_root, hx, hy, plaza_r, PATH_COLOR, PATH_CURB_COLOR)

    # Camp entrance: a real, walkable clearing out in the forest (no
    # floating portal arch) - reached by following the tree-free north
    # path. Standing near the chief's tent and pressing C is what actually
    # takes you into the dungeon (still its own separate space, now a 5x2
    # room grid instead of one open clearing).
    camp_info = build_forest_camp(town_root, house_avoid)

    dungeon = build_dungeon_grid(town_root, DUNGEON_1_POS[0], DUNGEON_1_POS[1])
    dungeon_enemies = dungeon["enemies"]
    portal_info = {
        "town_portal_pos": camp_info["prompt_pos"],
        "town_portal_pane": None,
        "town_arrival_pos": (CAMP_POS[0], CAMP_POS[1] - 6.0),
        "dungeon_arrival_pos": dungeon["arrival_pos"],
        "dungeon_return_pos": dungeon["return_trigger_pos"],
        "dungeon_return_pane": dungeon["return_pane"],
    }

    # Forest: inner radius unchanged (still starts right at the town's
    # edge), outer radius pushed out ~20x farther (FOREST_OUTER_RADIUS).
    # Nothing is built here up front - chunks are generated lazily by
    # _update_forest_streaming as the player actually explores toward them,
    # which is what makes a world this size sustainable.
    return town_root, fountain_handles, house_avoid, dungeon_enemies, portal_info


# ===========================================================================
#  MAIN APPLICATION  -  Minecraft-style first-person camera + collision
# ===========================================================================

KEY_MAP = {"forward": False, "back": False, "left": False, "right": False,
           "sprint": False, "jump": False}

MOUSE_SENSITIVITY = 0.15
EYE_HEIGHT = 1.8


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        props = WindowProperties()
        props.setTitle("Medieval RPG - Panda3D Prototype")
        self.win.requestProperties(props)

        self.disableMouse()

        self._setup_lighting()
        self._setup_fog()
        town_root, self.fountain, self.forest_avoid_boxes, self.enemies, self.portal_info = build_town(self.render)
        self.forest_parent = town_root
        self.projectiles = []
        # Lazy chunked forest state: chunk_cache maps (cx, cy) -> built
        # chunk record (or None if that chunk has no trees), only ever
        # populated for chunks the player has actually gotten close to.
        # loaded_keys is the subset currently unstashed/visible.
        self.forest_chunk_cache = {}
        self.loaded_chunk_keys = set()
        print(f"[town] forest ready - radius {FOREST_OUTER_RADIUS:.0f} units, "
              f"chunks generate lazily as you explore")
        print(f"[dungeon] Bandit's Camp at {DUNGEON_1_POS}, {len(self.enemies)} enemies placed")

        self.player = Player(name="Hero", class_name="Warrior")

        self.cam_yaw = 0.0
        self.cam_pitch = 0.0
        self.in_dungeon = False
        self.near_portal = False
        self.camera.setPos(0, -8, EYE_HEIGHT)
        self.camera.setHpr(self.cam_yaw, self.cam_pitch, 0)
        self.player_z_vel = 0.0
        self.on_ground = True

        self._setup_collision()
        self.stats_ui = StatsUI(self, self.player)
        self.hud = HUD(self.player)
        self.hotbar = Hotbar(["Mana Bolt", None, None, None, None])
        self._build_crosshair()
        self._build_portal_prompt()

        self.paused = False
        self._build_pause_menu()

        self._setup_input()
        self._center_mouse()
        self._update_forest_streaming()  # correct initial load state
        self.taskMgr.add(self._update, "update-task")

    def _setup_lighting(self):
        amb = AmbientLight("amb")
        amb.setColor(Vec4(0.45, 0.45, 0.5, 1))
        amb_np = self.render.attachNewNode(amb)
        self.render.setLight(amb_np)

        sun = DirectionalLight("sun")
        sun.setColor(Vec4(1.0, 0.95, 0.85, 1))
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(45, -55, 0)
        self.render.setLight(sun_np)

    def _setup_fog(self):
        """Distance fog masks chunk pop-in near the streaming radius and
        reinforces the enclosed-forest feel. Panda's exponential fog only
        tints actual scene geometry as a function of straight-line distance
        from the camera (it's radial/omnidirectional, not a height-based
        "vertical" gradient), and it never touches the background clear
        color - so the sky can stay blue while the fog itself is green.
        Density is adjusted at runtime in _update: light in the open town
        square, much heavier once the player is under the trees, so gaps
        between trunks don't reveal the sky far past the load radius."""
        self.fog = Fog("town_fog")
        self.fog.setColor(*FOG_COLOR[:3])
        self.fog.setExpDensity(TOWN_FOG_DENSITY)
        self.render.setFog(self.fog)
        self.setBackgroundColor(0.45, 0.68, 0.9)

        # Panda's default camera far-clip is only 1000 units. The fog wall
        # now sits out at FOG_WALL_RADIUS (~2280 with the extended forest),
        # so without this the camera clips the wall away before it ever
        # draws and you see straight through to the raw blue background -
        # the exact "blue horizon" bug the wall exists to prevent. Push the
        # far plane comfortably past the wall so it always renders.
        self.camLens.setFar(FOG_WALL_RADIUS * 1.5)

    def _setup_collision(self):
        """CollisionSphere on the player vs CollisionPolygon walls on every
        building/tree/fountain. Polygons are always exactly vertical, so
        the pusher can never generate a vertical push component - this is
        what fixes the earlier sink-into-floor / climb-the-wall glitches
        that CollisionBox produced at edges and corners."""
        self.cTrav = CollisionTraverser("player-trav")
        self.cTrav.setRespectPrevTransform(True)
        self.pusher = CollisionHandlerPusher()

        col_node = CollisionNode("player_col")
        col_node.addSolid(CollisionSphere(0, 0, 0, 0.4))
        col_node.setFromCollideMask(WALL_MASK)
        col_node.setIntoCollideMask(0)
        self.player_col_np = self.camera.attachNewNode(col_node)

        self.pusher.addCollider(self.player_col_np, self.camera)
        self.pusher.setHorizontal(True)
        self.cTrav.addCollider(self.player_col_np, self.pusher)

    def _build_pause_menu(self):
        self.pause_frame = DirectFrame(frameColor=(0.05, 0.05, 0.08, 0.85),
                                        frameSize=(-2, 2, -1.2, 1.2), pos=(0, 0, 0))
        OnscreenText(parent=self.pause_frame, text="Medieval RPG", pos=(0, 0.35),
                     scale=0.12, fg=(1, 1, 1, 1), align=TextNode.ACenter)
        DirectButton(parent=self.pause_frame, text="Play", scale=0.09, pos=(0, 0, 0),
                     frameColor=(0.2, 0.5, 0.25, 1), text_fg=(1, 1, 1, 1), command=self._resume)
        self.pause_frame.hide()

    def _toggle_pause(self):
        self._resume() if self.paused else self._pause()

    def _pause(self):
        self.paused = True
        props = WindowProperties()
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
        self.win.requestProperties(props)
        self.pause_frame.show()

    def _resume(self):
        self.paused = False
        self.pause_frame.hide()
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_confined)
        self.win.requestProperties(props)
        self._center_mouse()

    def _center_mouse(self):
        props = self.win.getProperties()
        self.center_x = props.getXSize() // 2
        self.center_y = props.getYSize() // 2
        self.win.movePointer(0, self.center_x, self.center_y)

    def _toggle_stats(self):
        """Opening the stats page shows the OS cursor (so you can click the
        +buttons) and releases mouse-look; closing it hides the cursor and
        re-locks mouse-look, same as normal gameplay."""
        if self.paused:
            return
        self.stats_ui.toggle()
        props = WindowProperties()
        if self.stats_ui.visible:
            props.setCursorHidden(False)
            props.setMouseMode(WindowProperties.M_absolute)
            self.win.requestProperties(props)
        else:
            props.setCursorHidden(True)
            props.setMouseMode(WindowProperties.M_confined)
            self.win.requestProperties(props)
            self._center_mouse()

    def _setup_input(self):
        for key, name in (("w", "forward"), ("s", "back"), ("a", "left"),
                           ("d", "right"), ("shift", "sprint"), ("space", "jump")):
            self.accept(key, KEY_MAP.__setitem__, [name, True])
            self.accept(f"{key}-up", KEY_MAP.__setitem__, [name, False])
        self.accept("p", self._toggle_stats)
        self.accept("escape", self._toggle_pause)
        self.accept("mouse1", self._cast_manabolt)
        self.accept("c", self._try_teleport)
        for slot in (1, 2, 3, 4, 5):
            self.accept(str(slot), self.hotbar.select_slot, [slot])

    def _build_portal_prompt(self):
        """Hidden by default; shown when standing near a portal arch,
        telling the player they can press C to use it."""
        self.portal_prompt = OnscreenText(
            text="", pos=(0, -0.35), scale=0.045,
            fg=(1, 0.95, 0.8, 1), align=TextNode.ACenter, mayChange=True)
        self.portal_prompt.hide()

    def _try_teleport(self):
        if self.paused or self.stats_ui.visible or not self.near_portal:
            return
        info = self.portal_info
        if not self.in_dungeon:
            self.camera.setPos(info["dungeon_arrival_pos"][0], info["dungeon_arrival_pos"][1], EYE_HEIGHT)
            self.in_dungeon = True
        else:
            self.camera.setPos(info["town_arrival_pos"][0], info["town_arrival_pos"][1], EYE_HEIGHT)
            self.in_dungeon = False
        self.player_z_vel = 0.0
        self.on_ground = True
        self.near_portal = False
        self.portal_prompt.hide()

    def _update_portal_prompt(self, t):
        info = self.portal_info
        cam = self.camera.getPos()
        if not self.in_dungeon:
            px, py = info["town_portal_pos"]
            prompt_text = "Press C to enter the dungeon"
            pane = info["town_portal_pane"]
        else:
            px, py = info["dungeon_return_pos"]
            prompt_text = "Press C to return to camp"
            pane = info["dungeon_return_pane"]

        dist = math.hypot(cam.x - px, cam.y - py)
        self.near_portal = dist < 3.2
        if self.near_portal:
            self.portal_prompt.setText(prompt_text)
            self.portal_prompt.show()
        else:
            self.portal_prompt.hide()

        # gentle pulsing glow on the active portal's pane so it reads as
        # "alive" rather than a plain colored pane - the camp side is a
        # tent now, not an arch, so it has no pane to pulse.
        if pane is not None:
            pulse = 0.55 + 0.2 * math.sin(t * 2.2)
            pane.setColor(0.55, 0.35, 0.9, pulse)

    def _build_crosshair(self):
        self.crosshair = OnscreenText(text="+", pos=(0, -0.02), scale=0.045,
                                       fg=(1, 1, 1, 0.85), align=TextNode.ACenter,
                                       mayChange=False)

    def _cast_manabolt(self):
        if self.paused or self.stats_ui.visible:
            return
        if self.hotbar.active_slot != 1:
            return  # only slot 1 (Mana Bolt) does anything right now
        t = globalClock.getFrameTime()
        p = self.player
        if not p.can_cast_manabolt(t):
            return
        dmg = p.cast_manabolt(t)

        yaw_rad = math.radians(self.cam_yaw)
        pitch_rad = math.radians(self.cam_pitch)
        fwd = Vec3(
            -math.sin(yaw_rad) * math.cos(pitch_rad),
            math.cos(yaw_rad) * math.cos(pitch_rad),
            math.sin(pitch_rad),
        )
        start = self.camera.getPos() + fwd * 0.6

        bolt = make_sphere(0.18, (0.35, 0.55, 1.0, 0.9), name="manabolt")
        bolt.reparentTo(self.render)
        bolt.setPos(start)
        bolt.setTransparency(True)
        bolt.setLightOff()

        self.projectiles.append({
            "np": bolt, "vel": fwd * MANA_BOLT_SPEED, "dmg": dmg,
            "owner": "player", "spawn_t": t, "lifetime": MANA_BOLT_LIFETIME,
            "hit_r": MANA_BOLT_HIT_RADIUS,
        })

    def _fire_arrow(self, enemy, target_pos, t):
        ex, ey = enemy.np.getX(), enemy.np.getY()
        ez = 1.1
        ang = math.atan2(target_pos.y - ey, target_pos.x - ex)
        vel = Vec3(math.cos(ang), math.sin(ang), 0) * ARROW_SPEED

        arrow = build_arrow_model(self.render)
        arrow.setPos(ex, ey, ez)
        # H=0 means "facing +Y" in this engine's convention (see the
        # movement code's fwd = (-sin H, cos H, 0)), so lining the arrow's
        # +Y shaft axis up with a math-angle `ang` needs H = deg(ang) - 90,
        # not deg(ang) directly - that missing -90 is why arrows were
        # flying in visually the wrong direction relative to how they
        # pointed.
        arrow.setH(math.degrees(ang) - 90)

        self.projectiles.append({
            "np": arrow, "vel": vel, "dmg": enemy.atk,
            "owner": "enemy", "spawn_t": t, "lifetime": ARROW_LIFETIME,
            "hit_r": ARROW_HIT_RADIUS,
        })

    def _update_mouse_look(self):
        if not self.mouseWatcherNode.hasMouse():
            return
        md = self.win.getPointer(0)
        dx = md.getX() - self.center_x
        dy = md.getY() - self.center_y
        if dx == 0 and dy == 0:
            return
        self.cam_yaw -= dx * MOUSE_SENSITIVITY
        self.cam_pitch -= dy * MOUSE_SENSITIVITY
        self.cam_pitch = max(-85, min(85, self.cam_pitch))
        self.camera.setHpr(self.cam_yaw, self.cam_pitch, 0)
        self.win.movePointer(0, self.center_x, self.center_y)

    def _update_fountain(self, t):
        f = self.fountain
        f["water_disc"].setZ(f["water_base_z"] + 0.025 * math.sin(t * 2.0))

        top_z, bottom_z = f["top_z"], f["bottom_z"]
        curtain_r = f["curtain_r"]
        fall_speed = 1.3
        for d in f["particles"]:
            phase = (t * fall_speed + d["phase0"]) % 1.0
            z = top_z - (top_z - bottom_z) * phase
            # tiny outward flare as it falls, like real water spreading
            # slightly on the way down - no orbiting, no rotation.
            r = curtain_r + 0.10 * phase
            ang = d["ang"]
            d["np"].setPos(r * math.cos(ang), r * math.sin(ang), z)
            fade = 1.0 - phase * 0.5
            d["np"].setColor(0.65, 0.85, 0.97, 0.85 * fade)

    def _update_forest_streaming(self):
        cam_pos = self.camera.getPos()
        cx, cy = cam_pos.x, cam_pos.y

        # Only ever look at chunks within the load radius of the player -
        # a fixed, small number of chunk-grid cells no matter how big the
        # overall forest is, so this scales with FOREST_LOAD_RADIUS, never
        # with FOREST_OUTER_RADIUS. Chunks are built (generated) the first
        # time they're requested here, then cached and just stashed/
        # unstashed after that.
        pcx = math.floor(cx / CHUNK_SIZE)
        pcy = math.floor(cy / CHUNK_SIZE)
        reach = int(math.ceil(FOREST_LOAD_RADIUS / CHUNK_SIZE)) + 1

        desired_keys = set()
        for dcx in range(-reach, reach + 1):
            for dcy in range(-reach, reach + 1):
                key = (pcx + dcx, pcy + dcy)
                ccx, ccy = (key[0] + 0.5) * CHUNK_SIZE, (key[1] + 0.5) * CHUNK_SIZE
                if math.hypot(ccx - cx, ccy - cy) < FOREST_LOAD_RADIUS:
                    center_dist = math.hypot(ccx, ccy)
                    if (FOREST_INNER_RADIUS - CHUNK_SIZE) < center_dist < (FOREST_OUTER_RADIUS + CHUNK_SIZE):
                        desired_keys.add(key)

        # Stash anything loaded that's no longer needed.
        for key in self.loaded_chunk_keys - desired_keys:
            rec = self.forest_chunk_cache.get(key)
            if rec is not None:
                rec["visual"].stash()
                rec["collision"].stash()
        self.loaded_chunk_keys &= desired_keys

        # Build (if new) and unstash anything newly needed.
        for key in desired_keys - self.loaded_chunk_keys:
            if key not in self.forest_chunk_cache:
                self.forest_chunk_cache[key] = _build_forest_chunk(
                    self.forest_parent, key, FOREST_INNER_RADIUS,
                    FOREST_OUTER_RADIUS, self.forest_avoid_boxes,
                )
            rec = self.forest_chunk_cache[key]
            if rec is not None:
                rec["visual"].unstash()
                rec["collision"].unstash()
            self.loaded_chunk_keys.add(key)

        # Fog density ramps up from the light town haze to a thick,
        # near-opaque forest fog as the player crosses the tree line, so
        # gaps between trunks don't reveal the sky/backdrop far past the
        # chunk streaming radius. Blended smoothly over a 10-unit band so
        # it isn't a jarring pop right at the boundary.
        dist_from_center = math.hypot(cx, cy)
        band = 5.0
        if dist_from_center <= FOREST_START_RADIUS - band:
            target_density = TOWN_FOG_DENSITY
        elif dist_from_center >= FOREST_START_RADIUS + band:
            target_density = FOREST_FOG_DENSITY
        else:
            tt = (dist_from_center - (FOREST_START_RADIUS - band)) / (2 * band)
            target_density = TOWN_FOG_DENSITY + (FOREST_FOG_DENSITY - TOWN_FOG_DENSITY) * tt
        self.fog.setExpDensity(target_density)

    def _update_enemies(self, dt, t):
        p = self.player
        cam_pos = self.camera.getPos()

        for en in self.enemies:
            if not en.alive:
                continue

            ex, ey = en.np.getX(), en.np.getY()
            dist = math.hypot(cam_pos.x - ex, cam_pos.y - ey)
            attack_range = ENEMY_MELEE_RANGE if en.role == "melee" else ENEMY_ARCHER_RANGE

            if en.state == "idle" and dist < ENEMY_DETECT_RANGE:
                en.state = "chase"
            elif en.state == "chase" and dist > ENEMY_DETECT_RANGE * 1.4:
                en.state = "idle"

            if en.state == "chase":
                ang = math.atan2(cam_pos.y - ey, cam_pos.x - ex)
                if dist > attack_range:
                    nx = ex + math.cos(ang) * en.spd * dt
                    ny = ey + math.sin(ang) * en.spd * dt
                    en.np.setPos(nx, ny, 0)
                en.np.setH(math.degrees(ang) - 90)

                if dist <= attack_range and not en.attacking and (t - en.last_attack) > en.attack_cooldown:
                    en.last_attack = t
                    en.attacking = True
                    en.swing_start = t
                    en.damage_applied = False
                    if en.role == "ranged":
                        self._fire_arrow(en, cam_pos, t)

            # melee animation + damage-on-impact: swordmen get a horizontal
            # swipe (weapon rotates through an arc), spearmen get a
            # straight forward-and-back stab (weapon translates along its
            # own forward axis) - previously both used the same rotation.
            if en.attacking:
                swing_t = t - en.swing_start
                if swing_t < ENEMY_SWING_DURATION:
                    frac = swing_t / ENEMY_SWING_DURATION
                    if en.name == "Spearman":
                        en.weapon_pivot.setY(0.6 * math.sin(frac * math.pi))
                    else:
                        en.weapon_pivot.setH(-70 + 140 * math.sin(frac * math.pi))
                    if en.role == "melee" and not en.damage_applied and frac > 0.45:
                        cur_dist = math.hypot(cam_pos.x - ex, cam_pos.y - ey)
                        if cur_dist <= ENEMY_MELEE_RANGE + 0.6:
                            p.hp = max(0.0, p.hp - en.atk)
                        en.damage_applied = True
                else:
                    en.attacking = False
                    en.weapon_pivot.setH(0)
                    en.weapon_pivot.setY(0)

            frac_hp = max(0.0, en.hp) / en.max_hp
            en.hp_bar_fg.setSx(max(0.001, frac_hp))

    def _update_projectiles(self, dt, t):
        cam_pos = self.camera.getPos()
        still_alive = []
        for proj in self.projectiles:
            age = t - proj["spawn_t"]
            if age > proj["lifetime"]:
                proj["np"].removeNode()
                continue

            new_pos = proj["np"].getPos() + proj["vel"] * dt
            proj["np"].setPos(new_pos)

            hit = False
            if proj["owner"] == "player":
                for en in self.enemies:
                    if not en.alive:
                        continue
                    ex, ey = en.np.getX(), en.np.getY()
                    if (new_pos.x - ex) ** 2 + (new_pos.y - ey) ** 2 <= proj["hit_r"] ** 2 \
                            and abs(new_pos.z - 1.1) < 1.4:
                        en.hp -= proj["dmg"]
                        if en.hp <= 0 and en.alive:
                            en.alive = False
                            en.home_np.removeNode()
                        hit = True
                        break
            else:  # enemy arrow vs player
                if (new_pos.x - cam_pos.x) ** 2 + (new_pos.y - cam_pos.y) ** 2 <= proj["hit_r"] ** 2:
                    self.player.hp = max(0.0, self.player.hp - proj["dmg"])
                    hit = True

            if hit or new_pos.z < 0:
                proj["np"].removeNode()
                continue
            still_alive.append(proj)
        self.projectiles = still_alive

    def _update(self, task):
        if self.paused:
            return Task.cont

        dt = globalClock.getDt()
        t = globalClock.getFrameTime()
        p = self.player

        if not self.stats_ui.visible:
            self._update_mouse_look()
        self._update_fountain(t)
        self._update_forest_streaming()
        self._update_enemies(dt, t)
        self._update_projectiles(dt, t)
        self._update_portal_prompt(t)

        # hp_regen/mana_regen are computed in Player._recompute_stats but
        # were never actually applied anywhere - that's why health and
        # mana weren't regenerating. Apply them here every frame.
        if p.hp < p.max_hp:
            p.hp = min(p.max_hp, p.hp + p.hp_regen * dt)
        if p.mana < p.max_mana:
            p.mana = min(p.max_mana, p.mana + p.mana_regen * dt)

        move_x = (1 if KEY_MAP["right"] else 0) - (1 if KEY_MAP["left"] else 0)
        move_y = (1 if KEY_MAP["forward"] else 0) - (1 if KEY_MAP["back"] else 0)

        # endurance -> stamina: sprinting only works (and only drains
        # stamina) while actually moving and at least 25% of max stamina
        # remains; otherwise it regenerates at stamina_regen/sec. Below the
        # 25% floor sprint is locked out entirely (not just "until 0"), so
        # players can't keep sprinting on fumes.
        is_sprinting = KEY_MAP["sprint"] and (move_x or move_y) and p.stamina >= p.max_stamina * 0.25
        speed = p.sprint_speed if is_sprinting else p.base_speed
        if is_sprinting:
            p.stamina = max(0.0, p.stamina - STAMINA_SPRINT_DRAIN * dt)
        else:
            p.stamina = min(p.max_stamina, p.stamina + p.stamina_regen * dt)

        if move_x or move_y:
            heading_rad = math.radians(self.cam_yaw)
            fwd = Vec3(-math.sin(heading_rad), math.cos(heading_rad), 0)
            right = Vec3(math.cos(heading_rad), math.sin(heading_rad), 0)
            move = (fwd * move_y + right * move_x)
            move.normalize()
            self.camera.setPos(self.camera.getPos() + move * speed * dt)

        self.hud.refresh()

        cd_remaining = MANA_BOLT_COOLDOWN - (t - p.last_manabolt)
        cd_frac = max(0.0, min(1.0, cd_remaining / MANA_BOLT_COOLDOWN))
        self.hotbar.refresh_cooldowns({1: cd_frac})

        if KEY_MAP["jump"] and self.on_ground:
            self.player_z_vel = p.jump_velocity
            self.on_ground = False

        if not self.on_ground:
            self.player_z_vel -= GRAVITY * dt
            new_z = self.camera.getZ() + self.player_z_vel * dt
            if new_z <= EYE_HEIGHT:
                new_z = EYE_HEIGHT
                self.player_z_vel = 0.0
                self.on_ground = True
            self.camera.setZ(new_z)

        # The pusher is horizontal-only, but tiny floating-point slop in the
        # wall polygon normals can still leak a fractional Z nudge into the
        # shove. Lock Z across the traversal (except while airborne, where
        # gravity/jump should keep controlling it) so bumping a wall while
        # pressing "w" can never be misread as vertical movement.
        z_before_collide = self.camera.getZ()
        self.cTrav.traverse(self.render)
        if self.on_ground:
            self.camera.setZ(z_before_collide)

        return Task.cont


if __name__ == "__main__":
    app = GameApp()
    app.run()
