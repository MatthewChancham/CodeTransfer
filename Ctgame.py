import sys
import subprocess
import importlib
import site

def ensure_package(import_name, pip_name=None):
    try:
        importlib.import_module(import_name)
        return
    except ImportError:
        pass

    if pip_name is None:
        pip_name = import_name

    subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
    importlib.reload(site)

    importlib.import_module(import_name)

ensure_package("direct", "panda3d")
ensure_package("panda3d", "panda3d")

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectButton, DirectFrame
from panda3d.core import (
    Vec3,
    TextNode,
    WindowProperties,
    NodePath,
    AmbientLight,
    DirectionalLight,
)

print("Panda3D is ready!")
import sys
import math

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    SPI_GETSTICKYKEYS = 0x003A
    SPI_SETSTICKYKEYS = 0x003B
    SKF_HOTKEYACTIVE = 0x00000004
    SKF_CONFIRMHOTKEY = 0x00000008
    SKF_HOTKEYSOUND = 0x00000010
    SKF_INDICATOR = 0x00000020
    SKF_AUDIBLEFEEDBACK = 0x00000040

    class STICKYKEYS(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwFlags", wintypes.DWORD)]

    def disable_sticky_keys_shortcut():
        sk = STICKYKEYS()
        sk.cbSize = ctypes.sizeof(STICKYKEYS)
        if not ctypes.windll.user32.SystemParametersInfoW(SPI_GETSTICKYKEYS, sk.cbSize, ctypes.byref(sk), 0):
            return False
        sk.dwFlags &= ~SKF_HOTKEYACTIVE
        sk.dwFlags &= ~SKF_CONFIRMHOTKEY
        sk.dwFlags &= ~SKF_HOTKEYSOUND
        sk.dwFlags &= ~SKF_INDICATOR
        sk.dwFlags &= ~SKF_AUDIBLEFEEDBACK
        return bool(ctypes.windll.user32.SystemParametersInfoW(SPI_SETSTICKYKEYS, sk.cbSize, ctypes.byref(sk), 0))

    disable_sticky_keys_shortcut()

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectButton, DirectFrame
from panda3d.core import (
    Vec3,
    TextNode,
    WindowProperties,
    NodePath,
    AmbientLight,
    DirectionalLight,
)


class Mover:
    def __init__(self, node, radius, stand_height, slide_height, ground_z):
        self.node = node
        self.radius = radius
        self.stand_height = stand_height
        self.slide_height = slide_height
        self.ground_z = ground_z
        self.floor_z = ground_z
        self.heading = 180.0
        self.air_velocity = 0.0
        self.on_ground = True
        self.is_sliding = False
        self.slide_timer = 0.0
        self.wall_contact = 0
        self.last_wall_contact = 0
        self.last_wall_contact_timer = 0.0
        self.wall_jump_timer = 0.0
        self.wall_jump_push = Vec3(0, 0, 0)
        self.wall_jump_push_timer = 0.0
        self.hanging = False
        self.hang_top_z = 0.0
        self.swinging = False
        self.swing_timer = 0.0
        self.swing_duration = 1.0
        self.swing_anchor = Vec3(0, 0, 0)
        self.swing_dir = Vec3(1, 0, 0)
        self.swing_side = Vec3(0, 1, 0)
        self.swing_radius = 5.0
        self.swing_start = Vec3(0, 0, 0)
        self.vaulting = False
        self.vault_timer = 0.0
        self.vault_velocity = Vec3(0, 0, 0)
        self.stuck_timer = 0.0

    def height(self):
        return self.slide_height if self.is_sliding else self.stand_height


class TagGame:
    def __init__(self, app, difficulty="Normal", role="Runner"):
        self.app = app
        self.difficulty = difficulty
        self.role = role

        self.solid_boxes = []
        self.platforms = []
        self.vault_boxes = []
        self.wall_jump_walls = []
        self.hiding_spots = []
        self.noise_traps = []
        self.monkey_bars = []
        self.rope_swings = []
        self.doors = []
        self.all_nodes = []

        self.keys = {"forward": False, "backward": False, "left": False, "right": False, "sprint": False, "interact": False}

        self.walk_speed = 11.5
        self.sprint_speed = 15.5
        self.slide_speed = 19.0
        self.ai_attack_range = 2.35
        self.apply_difficulty(difficulty)

        self.jump_velocity = 11.0
        self.gravity = 24.0
        self.slide_duration = 0.45

        self.max_stamina = 100.0
        self.stamina = 100.0
        self.sprint_stamina_cost = 24.0
        self.slide_stamina_cost = 18.0
        self.jump_stamina_cost = 10.0
        self.wall_jump_stamina_cost = 14.0
        self.swing_stamina_cost = 14.0
        self.vault_stamina_cost = 10.0
        self.stamina_recover_rate = 22.0
        self.exhausted = False

        self.cam_yaw = 180.0
        self.cam_pitch = 18.0
        self.cam_distance = 18.0
        self.cam_height = 3.0
        self.mouse_sensitivity = 0.13
        self.turn_speed = 760.0

        self.ground_z = 0.0
        self.player_radius = 0.72
        self.player_stand_height = 2.45
        self.player_slide_height = 1.05

        self.wall_jump_cooldown = 0.18
        self.wall_jump_up = 10.5
        self.wall_jump_side_speed = 14.5
        self.wall_slide_fall_speed = -2.2

        self.round_started = False
        self.countdown = 3.0
        self.start_gate_open = False
        self.game_over = False
        self.won = False
        self.time_left = 180.0 if role == "Runner" else 120.0

        self.ai_state = "guard"
        self.ai_memory_pos = Vec3(0, 0, 0)
        self.ai_search_timer = 0.0
        self.ai_investigate_timer = 0.0
        self.last_noise_pos = None
        self.last_noise_timer = 0.0

        self.replay_frames = []
        self.replay_playing = False
        self.replay_index = 0
        self.ghost_player = None
        self.ghost_ai = None

        self.setup_input()
        self.setup_mouse()
        self.setup_lighting()
        self.setup_scene()
        self.setup_characters()
        self.setup_doors()
        self.setup_arena()
        self.setup_ui()
        self.setup_minimap()

        self.reset_game()
        self.task = self.app.taskMgr.add(self.update, "update")

    def apply_difficulty(self, difficulty):
        if difficulty == "Easy":
            self.ai_speed = 8.5
            self.ai_view_distance = 30.0
            self.ai_view_angle = 80.0
            self.ai_hearing_radius = 11.0
            self.ai_prediction = 0.15
            self.ai_cutoff_strength = 0.12
            self.ai_search_time = 3.0
        elif difficulty == "Hard":
            self.ai_speed = 11.6
            self.ai_view_distance = 48.0
            self.ai_view_angle = 115.0
            self.ai_hearing_radius = 19.0
            self.ai_prediction = 1.1
            self.ai_cutoff_strength = 0.9
            self.ai_search_time = 7.0
        else:
            self.ai_speed = 10.2
            self.ai_view_distance = 38.0
            self.ai_view_angle = 96.0
            self.ai_hearing_radius = 15.0
            self.ai_prediction = 0.58
            self.ai_cutoff_strength = 0.5
            self.ai_search_time = 5.0

    def setup_input(self):
        self.app.accept("escape", sys.exit)
        self.app.accept("w", self.set_key, ["forward", True])
        self.app.accept("w-up", self.set_key, ["forward", False])
        self.app.accept("s", self.set_key, ["backward", True])
        self.app.accept("s-up", self.set_key, ["backward", False])
        self.app.accept("a", self.set_key, ["left", True])
        self.app.accept("a-up", self.set_key, ["left", False])
        self.app.accept("d", self.set_key, ["right", True])
        self.app.accept("d-up", self.set_key, ["right", False])
        self.app.accept("shift", self.set_key, ["sprint", True])
        self.app.accept("shift-up", self.set_key, ["sprint", False])
        self.app.accept("e", self.set_key, ["interact", True])
        self.app.accept("e-up", self.set_key, ["interact", False])
        self.app.accept("control", self.player_slide)
        self.app.accept("space", self.player_jump)
        self.app.accept("r", self.reset_game)

    def setup_mouse(self):
        props = WindowProperties()
        props.setCursorHidden(True)
        self.app.win.requestProperties(props)
        self.center_mouse()

    def center_mouse(self):
        if self.app.win:
            self.app.win.movePointer(0, self.app.win.getXSize() // 2, self.app.win.getYSize() // 2)

    def setup_lighting(self):
        ambient = AmbientLight("ambient")
        ambient.setColor((0.45, 0.45, 0.5, 1))
        ambient_np = self.app.render.attachNewNode(ambient)
        self.app.render.setLight(ambient_np)

        sun = DirectionalLight("main_light")
        sun.setColor((0.9, 0.85, 0.78, 1))
        sun_np = self.app.render.attachNewNode(sun)
        sun_np.setHpr(-35, -55, 0)
        self.app.render.setLight(sun_np)

    def set_key(self, key, value):
        self.keys[key] = value

    def make_box(self, pos, scale, color, solid=True, kind="solid", collision_scale=0.46):
        model = self.app.loader.loadModel("models/box")
        model.reparentTo(self.app.render)
        model.setPos(*pos)
        model.setScale(*scale)
        model.setColor(*color)
        self.all_nodes.append(model)

        visual = Vec3(*scale)
        box = {
            "node": model,
            "pos": Vec3(*pos),
            "visual_scale": visual,
            "size": visual * collision_scale,
            "kind": kind,
        }

        if solid:
            self.solid_boxes.append(box)

        return model, box

    def make_part(self, parent, pos, scale, color):
        part = self.app.loader.loadModel("models/box")
        part.reparentTo(parent)
        part.setPos(*pos)
        part.setScale(*scale)
        part.setColor(*color)
        return part

    def make_human(self, name, shirt, pants, skin, hair, neighbor=False):
        root = NodePath(name)
        root.reparentTo(self.app.render)
        self.all_nodes.append(root)

        self.make_part(root, (0, 0, 2.1), (0.42, 0.32, 0.42), skin)
        self.make_part(root, (0, 0, 1.45), (0.55, 0.34, 0.7), shirt)
        self.make_part(root, (-0.23, 0, 0.58), (0.2, 0.22, 0.7), pants)
        self.make_part(root, (0.23, 0, 0.58), (0.2, 0.22, 0.7), pants)
        self.make_part(root, (-0.54, 0, 1.45), (0.15, 0.16, 0.62), skin)
        self.make_part(root, (0.54, 0, 1.45), (0.15, 0.16, 0.62), skin)
        self.make_part(root, (0, 0, 2.43), (0.45, 0.34, 0.16), hair)

        if neighbor:
            self.make_part(root, (0, -0.34, 2.05), (0.28, 0.05, 0.06), (0.04, 0.02, 0.01, 1))
            self.make_part(root, (0, 0, 1.48), (0.64, 0.38, 0.2), (0.58, 0.03, 0.03, 1))
            self.make_part(root, (0, 0.36, 1.05), (0.5, 0.06, 0.5), (0.03, 0.025, 0.02, 1))

        return root

    def setup_scene(self):
        self.app.setBackgroundColor(0.05, 0.055, 0.06)
        self.app.camLens.setFov(80)

        self.floor, _ = self.make_box((0, 0, -0.5), (320, 320, 1), (0.56, 0.52, 0.45, 1), False, "floor")

        for pos, scale in [
            ((0, 155, 5), (320, 2, 10)),
            ((0, -155, 5), (320, 2, 10)),
            ((155, 0, 5), (2, 320, 10)),
            ((-155, 0, 5), (2, 320, 10)),
        ]:
            self.make_box(pos, scale, (0.025, 0.025, 0.03, 1), True, "wall", 0.5)

    def setup_characters(self):
        self.player = self.make_human("player_human", (0.08, 0.28, 0.95, 1), (0.04, 0.04, 0.09, 1), (0.86, 0.62, 0.42, 1), (0.05, 0.03, 0.02, 1))
        self.player_body = Mover(self.player, self.player_radius, self.player_stand_height, self.player_slide_height, self.ground_z)

        self.ai = self.make_human("neighbor_ai", (0.58, 0.08, 0.05, 1), (0.08, 0.1, 0.24, 1), (0.86, 0.58, 0.38, 1), (0.02, 0.015, 0.01, 1), True)
        self.ai_body = Mover(self.ai, 0.72, 2.45, 1.05, self.ground_z)

    def setup_doors(self):
        for pos in [(10, 0, 1.7), (-18, 0, 1.7), (4, 26, 1.7)]:
            door, _ = self.make_box(pos, (2.6, 0.6, 3.4), (0.55, 0.06, 0.04, 1), True, "door", 0.44)
            self.doors.append({"node": door, "open": False, "closed_h": door.getH(), "open_h": door.getH() + 90, "current_h": door.getH()})

        self.start_gate, self.start_gate_box = self.make_box((0, -6, 1.8), (12, 0.8, 3.6), (0.95, 0.05, 0.04, 1), True, "start_gate", 0.48)

    def setup_arena(self):
        red = (0.9, 0.04, 0.03, 1)
        dark = (0.018, 0.02, 0.025, 1)
        mat = (0.28, 0.28, 0.3, 1)
        blue = (0.12, 0.18, 0.72, 1)

        for pos, scale in [
            ((8, -14, 1.6), (8, 8, 1.0)),
            ((-14, 16, 2.35), (10, 6, 1.0)),
            ((20, -2, 3.55), (8, 8, 1.0)),
            ((-30, -8, 4.15), (12, 6, 1.0)),
            ((31, 19, 2.85), (10, 10, 1.0)),
            ((55, -18, 3.35), (12, 7, 1.0)),
            ((-58, 18, 3.15), (10, 8, 1.0)),
        ]:
            _, box = self.make_box(pos, scale, blue, True, "platform", 0.45)
            self.platforms.append(box)

        for pos, scale in [
            ((-6, 8, 0.45), (6, 1.6, 0.9)),
            ((14, -8, 0.45), (6, 1.6, 0.9)),
            ((-28, 22, 0.45), (8, 1.6, 0.9)),
        ]:
            self.make_box(pos, scale, red, True, "low", 0.42)

        for pos, scale in [
            ((-2, 18, 0.85), (6, 1.3, 1.7)),
            ((18, 18, 0.85), (5, 1.7, 1.7)),
            ((-22, -18, 0.85), (7, 1.5, 1.7)),
            ((46, 4, 0.85), (6, 1.5, 1.7)),
        ]:
            _, box = self.make_box(pos, scale, (0.75, 0.32, 0.16, 1), True, "vault", 0.42)
            self.vault_boxes.append(box)

        for pos, scale in [
            ((-35, 4, 0.9), (0.8, 18, 1.8)),
            ((35, -16, 0.9), (0.8, 16, 1.8)),
            ((8, 34, 0.9), (18, 0.8, 1.8)),
        ]:
            self.make_box(pos, scale, dark, True, "rail", 0.38)

        for pos, scale in [
            ((-12, -28, 1.75), (10, 8, 0.8)),
            ((24, 28, 1.75), (10, 8, 0.8)),
        ]:
            self.make_box(pos, scale, mat, True, "crawl_gap", 0.42)

        for pos, scale in [
            ((35, 0, 8), (2, 24, 16)),
            ((41, 0, 8), (2, 24, 16)),
            ((-42, 22, 6), (2, 20, 12)),
        ]:
            _, box = self.make_box(pos, scale, dark, True, "wall_jump", 0.46)
            self.wall_jump_walls.append(box)

        for pos, scale, direction in [
            ((-2, -46, 5.8), (18, 0.45, 0.35), Vec3(1, 0, 0)),
            ((18, -46, 5.8), (18, 0.45, 0.35), Vec3(1, 0, 0)),
            ((-52, 0, 5.5), (0.45, 18, 0.35), Vec3(0, 1, 0)),
        ]:
            _, box = self.make_box(pos, scale, dark, True, "monkey_bar", 0.28)
            box["direction"] = direction
            self.monkey_bars.append(box)

        for pos, swing_dir in [((52, 44, 6.0), Vec3(1, -1, 0)), ((-54, -44, 6.0), Vec3(1, 1, 0))]:
            self.make_box(pos, (0.45, 0.45, 8.5), dark, True, "rope_visual", 0.25)
            _, box = self.make_box((pos[0], pos[1], 1.35), (1.6, 1.6, 2.7), (0.45, 0.26, 0.12, 1), True, "rope", 0.35)
            box["anchor"] = Vec3(*pos)
            box["direction"] = swing_dir.normalized()
            self.rope_swings.append(box)

        for pos, fake in [((-18, 34, 1.5), False), ((30, -32, 1.5), True), ((-42, -34, 1.5), False), ((58, 34, 1.5), True)]:
            color = (0.1, 0.35, 0.18, 1) if not fake else (0.45, 0.12, 0.08, 1)
            _, box = self.make_box(pos, (6, 6, 3), color, True, "hide", 0.38)
            box["fake"] = fake
            self.hiding_spots.append(box)

        for pos in [(-8, -20, 0.12), (24, 8, 0.12), (-32, 10, 0.12)]:
            _, box = self.make_box(pos, (2.4, 2.4, 0.24), (1.0, 0.85, 0.15, 1), True, "noise", 0.35)
            box["triggered"] = False
            box["cooldown"] = 0.0
            self.noise_traps.append(box)

        for pos, scale in [
            ((-30, 34, 2), (1.6, 26, 4)),
            ((-18, 28, 2), (24, 1.6, 4)),
            ((18, -34, 2), (1.6, 26, 4)),
            ((30, -28, 2), (24, 1.6, 4)),
            ((0, 42, 2), (36, 1.6, 4)),
        ]:
            self.make_box(pos, scale, red, True, "route_wall", 0.46)

        for pos, scale in [
            ((0, 0, 7), (80, 0.35, 0.35)),
            ((0, 0, 7.4), (0.35, 80, 0.35)),
            ((-40, 40, 6.5), (0.35, 40, 0.35)),
            ((40, -40, 6.5), (40, 0.35, 0.35)),
        ]:
            self.make_box(pos, scale, red, True, "decor_beam", 0.25)

    def setup_ui(self):
        self.info = OnscreenText(
            text="WASD | Mouse | SHIFT sprint | CTRL slide | SPACE jump/vault/climb | E swing | R reset",
            pos=(0, 0.93),
            scale=0.038,
            fg=(1, 1, 1, 1),
            mayChange=True,
        )
        self.timer_text = OnscreenText(text="03:00", pos=(0, 0.82), scale=0.07, fg=(1, 1, 0, 1), mayChange=True, align=TextNode.ACenter)
        self.stamina_text = OnscreenText(text="Stamina 100", pos=(-1.28, 0.86), scale=0.05, fg=(0.35, 1, 0.55, 1), mayChange=True, align=TextNode.ALeft)
        self.ai_state_text = OnscreenText(text="", pos=(0, -0.92), scale=0.045, fg=(1, 0.75, 0.35, 1), mayChange=True, align=TextNode.ACenter)
        self.countdown_text = OnscreenText(text="", pos=(0, 0.05), scale=0.18, fg=(1, 1, 1, 1), mayChange=True, align=TextNode.ACenter)
        self.win_text = OnscreenText(text="", pos=(0, -0.1), scale=0.14, fg=(1, 0.2, 0.9, 1), mayChange=True, align=TextNode.ACenter)

    def setup_minimap(self):
        self.minimap = DirectFrame(frameColor=(0.02, 0.02, 0.025, 0.75), frameSize=(-0.18, 0.18, -0.18, 0.18), pos=(1.08, 0, 0.72))
        self.player_dot = DirectFrame(parent=self.minimap, frameColor=(0.1, 0.4, 1, 1), frameSize=(-0.012, 0.012, -0.012, 0.012))
        self.ai_dot = DirectFrame(parent=self.minimap, frameColor=(1, 0.1, 0.05, 1), frameSize=(-0.012, 0.012, -0.012, 0.012))

    def reset_game(self):
        self.game_over = False
        self.won = False
        self.round_started = False
        self.countdown = 3.0
        self.start_gate_open = False
        self.time_left = 180.0 if self.role == "Runner" else 120.0
        self.stamina = self.max_stamina
        self.exhausted = False
        self.ai_state = "guard"
        self.ai_memory_pos = Vec3(0, 0, 0)
        self.ai_search_timer = 0.0
        self.ai_investigate_timer = 0.0
        self.last_noise_pos = None
        self.last_noise_timer = 0.0
        self.replay_frames = []
        self.replay_playing = False
        self.replay_index = 0

        self.timer_text.setText("03:00" if self.role == "Runner" else "02:00")
        self.win_text.setText("")
        self.countdown_text.setText("3")

        if self.ghost_player:
            self.ghost_player.removeNode()
            self.ghost_player = None
        if self.ghost_ai:
            self.ghost_ai.removeNode()
            self.ghost_ai = None

        for key in self.keys:
            self.keys[key] = False

        if self.role == "Runner":
            self.reset_mover(self.player_body, Vec3(0, -14, self.ground_z), 180.0)
            self.reset_mover(self.ai_body, Vec3(28, 0, self.ground_z), 180.0)
        else:
            self.reset_mover(self.player_body, Vec3(28, 0, self.ground_z), 180.0)
            self.reset_mover(self.ai_body, Vec3(0, -14, self.ground_z), 180.0)

        self.player.setScale(1)
        self.ai.setScale(1)
        self.cam_yaw = 180.0
        self.cam_pitch = 18.0

        for door in self.doors:
            door["open"] = False
            door["current_h"] = door["closed_h"]
            door["node"].setH(door["closed_h"])
            if door.get("box") and door["box"] not in self.solid_boxes:
                self.solid_boxes.append(door["box"])

        self.start_gate.setPos(0, -6, 1.8)
        if self.start_gate_box not in self.solid_boxes:
            self.solid_boxes.append(self.start_gate_box)

        for trap in self.noise_traps:
            trap["triggered"] = False
            trap["cooldown"] = 0.0
            trap["node"].setColor(1.0, 0.85, 0.15, 1)

        self.center_mouse()

    def reset_mover(self, mover, pos, heading):
        mover.node.setPos(pos)
        mover.node.setH(heading)
        mover.heading = heading
        mover.air_velocity = 0.0
        mover.on_ground = True
        mover.floor_z = self.ground_z
        mover.is_sliding = False
        mover.slide_timer = 0.0
        mover.wall_contact = 0
        mover.last_wall_contact = 0
        mover.last_wall_contact_timer = 0.0
        mover.wall_jump_timer = 0.0
        mover.wall_jump_push = Vec3(0, 0, 0)
        mover.wall_jump_push_timer = 0.0
        mover.hanging = False
        mover.swinging = False
        mover.vaulting = False
        mover.stuck_timer = 0.0

    def angle_difference(self, a, b):
        return (a - b + 180.0) % 360.0 - 180.0

    def approach_angle(self, current, target, max_step):
        diff = self.angle_difference(target, current)
        if abs(diff) <= max_step:
            return target
        return current + max_step if diff > 0 else current - max_step

    def heading_to_forward(self, heading):
        h = math.radians(heading)
        return Vec3(math.sin(h), math.cos(h), 0)

    def heading_to_right(self, heading):
        h = math.radians(heading)
        return Vec3(math.cos(h), -math.sin(h), 0)

    def vector_to_heading(self, vec):
        return math.degrees(math.atan2(vec.x, vec.y))

    def update_mouse_camera_control(self):
        if not self.app.win:
            return
        pointer = self.app.win.getPointer(0)
        center_x = self.app.win.getXSize() // 2
        center_y = self.app.win.getYSize() // 2
        dx = pointer.getX() - center_x
        dy = pointer.getY() - center_y
        if dx != 0 or dy != 0:
            self.cam_yaw += dx * self.mouse_sensitivity
            self.cam_pitch -= dy * self.mouse_sensitivity
            self.cam_pitch = max(-5.0, min(55.0, self.cam_pitch))
            self.center_mouse()

    def actor_overlaps_box(self, box, pos, radius, height):
        p = box["pos"]
        s = box["size"]
        actor_bottom = pos.z
        actor_top = pos.z + height
        box_bottom = p.z - s.z
        box_top = p.z + s.z
        return abs(pos.x - p.x) < s.x + radius and abs(pos.y - p.y) < s.y + radius and actor_bottom < box_top and actor_top > box_bottom

    def blocked_by_solids(self, mover, next_pos, test_height=None):
        height = mover.height() if test_height is None else test_height

        for box in self.solid_boxes:
            if box["kind"] in ["platform", "crawl_gap", "monkey_bar"]:
                box_bottom = box["pos"].z - box["size"].z
                box_top = box["pos"].z + box["size"].z
                standing_on_top = mover.node.getZ() >= box_top - 0.25
                sliding_under = next_pos.z + height <= box_bottom
                if standing_on_top or sliding_under:
                    continue

            if box["kind"] == "door" and box.get("open", False):
                continue

            if self.actor_overlaps_box(box, next_pos, mover.radius, height):
                return True

        return False

    def find_floor_z(self, mover, pos):
        best = self.ground_z
        for platform in self.platforms:
            p = platform["pos"]
            s = platform["size"]
            top = p.z + s.z
            if abs(pos.x - p.x) < s.x + mover.radius and abs(pos.y - p.y) < s.y + mover.radius and pos.z >= top - 0.35:
                best = max(best, top)
        return best

    def find_ledge(self, mover):
        if mover.on_ground or mover.air_velocity >= 0 or mover.hanging:
            return None
        pos = mover.node.getPos()
        for platform in self.platforms:
            p = platform["pos"]
            s = platform["size"]
            top = p.z + s.z
            if not (pos.z + 0.5 < top < pos.z + mover.stand_height + 0.7):
                continue
            near_x = p.x - s.x - mover.radius < pos.x < p.x + s.x + mover.radius
            near_y = p.y - s.y - mover.radius < pos.y < p.y + s.y + mover.radius
            inside_x = p.x - s.x < pos.x < p.x + s.x
            inside_y = p.y - s.y < pos.y < p.y + s.y
            if near_x and near_y and not (inside_x and inside_y):
                return platform
        return None

    def grab_ledge_if_possible(self, mover):
        ledge = self.find_ledge(mover)
        if not ledge:
            return False
        top = ledge["pos"].z + ledge["size"].z
        mover.hanging = True
        mover.hang_top_z = top
        mover.air_velocity = 0.0
        mover.node.setZ(top - 1.25)
        return True

    def climb_ledge(self, mover):
        if not mover.hanging:
            return False
        mover.hanging = False
        mover.on_ground = True
        mover.air_velocity = 0.0
        mover.node.setZ(mover.hang_top_z)
        return True

    def move_mover_with_collision(self, mover, movement):
        start = mover.node.getPos()
        current = Vec3(start)

        next_x = Vec3(current.x + movement.x, current.y, current.z)
        if not self.blocked_by_solids(mover, next_x):
            current = next_x

        next_y = Vec3(current.x, current.y + movement.y, current.z)
        if not self.blocked_by_solids(mover, next_y):
            current = next_y

        mover.node.setPos(current)
        return (current - start).length()

    def spend_stamina(self, amount):
        self.stamina = max(0.0, self.stamina - amount)
        if self.stamina <= 1.0:
            self.exhausted = True

    def update_stamina(self, dt, is_moving):
        sprinting = self.keys["sprint"] and is_moving and self.player_body.on_ground and not self.player_body.is_sliding
        if sprinting and not self.exhausted:
            self.stamina = max(0.0, self.stamina - self.sprint_stamina_cost * dt)
            if self.stamina <= 1.0:
                self.exhausted = True
        else:
            recover = self.stamina_recover_rate * dt * (1.4 if not is_moving else 1.0)
            self.stamina = min(self.max_stamina, self.stamina + recover)
            if self.stamina >= 28.0:
                self.exhausted = False
        self.stamina_text.setText(f"Stamina {int(self.stamina):03d}")

    def update_mover_slide(self, mover, dt):
        if mover.slide_timer <= 0:
            return
        mover.slide_timer -= dt
        if mover.slide_timer <= 0:
            can_stand = not self.blocked_by_solids(mover, mover.node.getPos(), test_height=mover.stand_height)
            if can_stand:
                mover.is_sliding = False
                mover.node.setScale(1)
            else:
                mover.slide_timer = 0.08

    def update_mover_vertical(self, mover, dt):
        if mover.swinging or mover.vaulting or mover.hanging:
            return
        pos = mover.node.getPos()
        floor_z = self.find_floor_z(mover, pos)

        if not mover.on_ground:
            mover.air_velocity -= self.gravity * dt
            next_z = mover.node.getZ() + mover.air_velocity * dt
            mover.node.setZ(next_z)

            if self.grab_ledge_if_possible(mover):
                return

            if next_z <= floor_z:
                mover.node.setZ(floor_z)
                mover.floor_z = floor_z
                mover.on_ground = True
                mover.air_velocity = 0.0
                mover.wall_jump_push = Vec3(0, 0, 0)
                mover.wall_jump_push_timer = 0.0
        else:
            mover.floor_z = floor_z
            if mover.node.getZ() > mover.floor_z + 0.05:
                mover.on_ground = False
            else:
                mover.node.setZ(mover.floor_z)

    def wall_contact_check_for_mover(self, mover):
        pos = mover.node.getPos()
        for wall in self.wall_jump_walls:
            d = pos - wall["pos"]
            if abs(d.x) < wall["size"].x + mover.radius + 0.35 and abs(d.y) < wall["size"].y + mover.radius + 0.35 and abs(d.z) < wall["size"].z + 1.4:
                return 1 if pos.x < wall["pos"].x else -1
        return 0

    def update_wall_contact_memory(self, mover, dt):
        mover.wall_contact = self.wall_contact_check_for_mover(mover)
        if mover.wall_contact != 0:
            mover.last_wall_contact = mover.wall_contact
            mover.last_wall_contact_timer = 0.35
        elif mover.last_wall_contact_timer > 0:
            mover.last_wall_contact_timer -= dt
        else:
            mover.last_wall_contact = 0

    def get_camera_relative_move(self):
        forward = self.heading_to_forward(self.cam_yaw)
        right = self.heading_to_right(self.cam_yaw)
        move = Vec3(0, 0, 0)
        if self.keys["forward"]:
            move += forward
        if self.keys["backward"]:
            move -= forward
        if self.keys["left"]:
            move -= right
        if self.keys["right"]:
            move += right
        return move

    def nearest_vault_box(self, mover):
        pos = mover.node.getPos()
        best = None
        best_dist = 9999.0
        for box in self.vault_boxes:
            d = pos - box["pos"]
            d.z = 0
            dist = d.length()
            if dist < 2.7 and dist < best_dist:
                best = box
                best_dist = dist
        return best

    def try_vault(self, mover):
        box = self.nearest_vault_box(mover)
        if not box or not mover.on_ground:
            return False

        move = self.get_camera_relative_move()
        if mover is not self.player_body:
            move = self.ai_target_position() - mover.node.getPos()
            move.z = 0

        clean = move.length() > 0.01 and (mover.node.getPos() - box["pos"]).length() < 2.25
        if mover is self.player_body and self.stamina < self.vault_stamina_cost:
            clean = False

        if move.length() > 0:
            move.normalize()
        else:
            move = self.heading_to_forward(mover.heading)

        mover.vaulting = True
        mover.vault_timer = 0.25 if clean else 0.48
        mover.vault_velocity = move * (16.5 if clean else 5.0)
        mover.air_velocity = 5.0 if clean else 2.0
        mover.on_ground = False
        if mover is self.player_body and clean:
            self.spend_stamina(self.vault_stamina_cost)
        return True

    def try_jump(self, mover):
        if mover.hanging:
            return self.climb_ledge(mover)

        if self.try_vault(mover):
            return True

        has_wall = mover.wall_contact != 0 or mover.last_wall_contact_timer > 0
        wall_side = mover.wall_contact if mover.wall_contact != 0 else mover.last_wall_contact
        stamina_needed = self.wall_jump_stamina_cost if has_wall and not mover.on_ground else self.jump_stamina_cost

        if mover is self.player_body and self.stamina < stamina_needed:
            return False

        if has_wall and not mover.on_ground:
            mover.air_velocity = self.wall_jump_up
            mover.wall_jump_push = Vec3(-wall_side, 0, 0) * self.wall_jump_side_speed
            mover.wall_jump_push_timer = 0.28
            mover.wall_jump_timer = self.wall_jump_cooldown
            mover.heading = self.vector_to_heading(mover.wall_jump_push)
            mover.node.setH(mover.heading)
            if mover is self.player_body:
                self.spend_stamina(self.wall_jump_stamina_cost)
            return True

        if mover.on_ground:
            mover.air_velocity = self.jump_velocity
            mover.on_ground = False
            if mover is self.player_body:
                self.spend_stamina(self.jump_stamina_cost)
            return True

        return False

    def start_slide(self, mover):
        if mover.slide_timer <= 0 and mover.on_ground:
            if mover is self.player_body and self.stamina < self.slide_stamina_cost:
                return False
            mover.slide_timer = self.slide_duration
            mover.is_sliding = True
            mover.node.setScale(1, 1, 0.65)
            if mover is self.player_body:
                self.spend_stamina(self.slide_stamina_cost)
            return True
        return False

    def player_jump(self):
        if self.game_over or self.won or not self.round_started:
            return
        self.try_jump(self.player_body)

    def player_slide(self):
        if self.game_over or self.won or not self.round_started:
            return
        self.start_slide(self.player_body)

    def nearest_swing_target(self, mover):
        pos = mover.node.getPos()
        for bar in self.monkey_bars:
            d = pos - bar["pos"]
            if abs(d.x) < bar["visual_scale"].x + 1.5 and abs(d.y) < bar["visual_scale"].y + 1.5:
                if 2.0 < bar["pos"].z - pos.z < 6.0:
                    return bar
        for rope in self.rope_swings:
            if (pos - rope["pos"]).length() < 4.8:
                return rope
        return None

    def update_swinging(self, mover, dt):
        if mover.swinging:
            mover.swing_timer += dt
            t = min(1.0, mover.swing_timer / mover.swing_duration)
            arc = math.sin(t * math.pi)
            forward = mover.swing_dir * (mover.swing_radius * t * 1.8)
            side = mover.swing_side * math.sin(t * math.pi * 2.0) * 0.8
            height = math.sin(t * math.pi) * 1.6
            mover.node.setPos(mover.swing_start + forward + side)
            mover.node.setZ(max(2.4, mover.swing_start.z + height))
            mover.heading = self.vector_to_heading(mover.swing_dir)
            mover.node.setH(mover.heading)

            if t >= 1.0:
                mover.swinging = False
                mover.on_ground = False
                mover.air_velocity = 3.2
            return True

        if mover is self.player_body and self.keys["interact"] and self.stamina >= self.swing_stamina_cost:
            target = self.nearest_swing_target(mover)
            if target:
                direction = Vec3(target["direction"])
                if direction.length() > 0:
                    direction.normalize()
                mover.swinging = True
                mover.swing_timer = 0.0
                mover.swing_duration = 0.85 if target["kind"] == "monkey_bar" else 1.1
                mover.swing_start = Vec3(mover.node.getPos())
                mover.swing_anchor = target.get("anchor", target["pos"])
                mover.swing_dir = direction
                mover.swing_side = Vec3(-direction.y, direction.x, 0)
                mover.swing_radius = 6.0 if target["kind"] == "monkey_bar" else 8.0
                mover.hanging = False
                mover.on_ground = False
                self.spend_stamina(self.swing_stamina_cost)
                return True
        return False

    def update_vaulting(self, mover, dt):
        if not mover.vaulting:
            return False
        mover.vault_timer -= dt
        self.move_mover_with_collision(mover, mover.vault_velocity * dt)
        mover.node.setZ(mover.node.getZ() + mover.air_velocity * dt)
        mover.air_velocity -= self.gravity * 0.65 * dt
        if mover.vault_timer <= 0:
            mover.vaulting = False
            mover.on_ground = False
        return True

    def update_player(self, dt):
        if self.game_over or self.won or not self.round_started:
            return

        if self.player_body.hanging:
            self.update_stamina(dt, False)
            return

        if self.update_swinging(self.player_body, dt):
            self.update_stamina(dt, True)
            return

        if self.update_vaulting(self.player_body, dt):
            self.update_stamina(dt, True)
            return

        move = self.get_camera_relative_move()
        is_moving = move.length() > 0
        self.update_stamina(dt, is_moving)

        if is_moving:
            move.normalize()
            target_heading = self.vector_to_heading(move)
            self.player_body.heading = self.approach_angle(self.player_body.heading, target_heading, self.turn_speed * dt)
            self.player.setH(self.player_body.heading)
            sprinting = self.keys["sprint"] and not self.exhausted and self.player_body.on_ground
            speed = self.sprint_speed if sprinting else self.walk_speed
            if self.player_body.is_sliding:
                speed = self.slide_speed
            self.move_mover_with_collision(self.player_body, move * speed * dt)
        else:
            self.player_body.heading = self.approach_angle(self.player_body.heading, self.cam_yaw, self.turn_speed * dt)
            self.player.setH(self.player_body.heading)

        if self.player_body.wall_jump_push_timer > 0:
            self.player_body.wall_jump_push_timer -= dt
            self.move_mover_with_collision(self.player_body, self.player_body.wall_jump_push * dt)

        self.update_mover_slide(self.player_body, dt)

        if self.player_body.wall_jump_timer > 0:
            self.player_body.wall_jump_timer -= dt

        self.update_mover_vertical(self.player_body, dt)
        self.update_wall_contact_memory(self.player_body, dt)

        if self.player_body.wall_contact != 0 and not self.player_body.on_ground and self.player_body.wall_jump_timer <= 0:
            self.player_body.air_velocity = max(self.player_body.air_velocity, self.wall_slide_fall_speed)

        self.update_noise_traps(dt, is_moving)
        self.update_fake_hiding_spots()

    def is_player_hidden(self):
        pos = self.player.getPos()
        for spot in self.hiding_spots:
            d = pos - spot["pos"]
            d.z = 0
            if d.length() < 5.0:
                return not spot.get("fake", False)
        return False

    def update_fake_hiding_spots(self):
        pos = self.player.getPos()
        for spot in self.hiding_spots:
            if not spot.get("fake", False):
                continue
            d = pos - spot["pos"]
            d.z = 0
            if d.length() < 5.0:
                self.last_noise_pos = Vec3(spot["pos"])
                self.last_noise_timer = 2.0
                spot["node"].setColor(0.85, 0.04, 0.03, 1)

    def segment_hits_box_2d(self, start, end, box):
        if box["kind"] in ["platform", "low", "vault", "noise", "hide", "start_gate", "crawl_gap", "monkey_bar", "rope", "decor_beam"]:
            return False
        p = box["pos"]
        s = box["size"]
        for i in range(1, 18):
            t = i / 18.0
            sample = start + (end - start) * t
            if p.x - s.x <= sample.x <= p.x + s.x and p.y - s.y <= sample.y <= p.y + s.y:
                return True
        return False

    def has_line_of_sight_to_player(self):
        ai_pos = self.ai.getPos()
        player_pos = self.player.getPos()
        to_player = player_pos - ai_pos
        to_player.z = 0
        dist = to_player.length()

        if dist > self.ai_view_distance or dist <= 0.01:
            return False
        if self.is_player_hidden() and dist > 5.0:
            return False

        to_player.normalize()
        ai_forward = self.heading_to_forward(self.ai_body.heading)
        dot = max(-1.0, min(1.0, ai_forward.dot(to_player)))
        if math.degrees(math.acos(dot)) > self.ai_view_angle * 0.5:
            return False

        for box in self.solid_boxes:
            if self.segment_hits_box_2d(ai_pos, player_pos, box):
                return False
        return True

    def player_noise_radius(self):
        moving = self.get_camera_relative_move().length() > 0
        if self.player_body.is_sliding:
            return 18.0
        if self.keys["sprint"] and moving and not self.exhausted:
            return 16.0
        if moving:
            return 8.0
        return 0.0

    def update_noise_traps(self, dt, is_moving):
        if self.last_noise_timer > 0:
            self.last_noise_timer -= dt

        for trap in self.noise_traps:
            if trap["cooldown"] > 0:
                trap["cooldown"] -= dt
                if trap["cooldown"] <= 0:
                    trap["triggered"] = False
                    trap["node"].setColor(1.0, 0.85, 0.15, 1)

            if not trap["triggered"] and (self.player.getPos() - trap["pos"]).length() < 1.7 and is_moving:
                trap["triggered"] = True
                trap["cooldown"] = 8.0
                trap["node"].setColor(1.0, 0.15, 0.1, 1)
                self.last_noise_pos = Vec3(trap["pos"])
                self.last_noise_timer = 3.0

    def ai_hears_player(self):
        noise = self.player_noise_radius()
        return noise > 0 and (self.player.getPos() - self.ai.getPos()).length() <= min(noise, self.ai_hearing_radius)

    def update_ai_perception(self, dt):
        if self.role == "Chaser":
            self.ai_state = "flee"
            return

        if self.has_line_of_sight_to_player():
            self.ai_state = "chase"
            self.ai_memory_pos = Vec3(self.player.getPos())
            self.ai_search_timer = self.ai_search_time
            return

        if self.ai_hears_player():
            self.ai_state = "investigate"
            self.ai_memory_pos = Vec3(self.player.getPos())
            self.ai_investigate_timer = 2.5
            return

        if self.last_noise_timer > 0 and self.last_noise_pos and (self.last_noise_pos - self.ai.getPos()).length() < self.ai_hearing_radius * 1.7:
            self.ai_state = "investigate"
            self.ai_memory_pos = Vec3(self.last_noise_pos)
            self.ai_investigate_timer = 3.5
            return

        if self.ai_state == "chase":
            self.ai_search_timer -= dt
            if self.ai_search_timer <= 0:
                self.ai_state = "search"
        elif self.ai_state == "investigate":
            self.ai_investigate_timer -= dt
            if self.ai_investigate_timer <= 0:
                self.ai_state = "search"
                self.ai_search_timer = self.ai_search_time * 0.7
        elif self.ai_state == "search":
            self.ai_search_timer -= dt
            if self.ai_search_timer <= 0:
                self.ai_state = "patrol"

    def ai_target_position(self):
        if self.role == "Chaser":
            away = self.ai.getPos() - self.player.getPos()
            away.z = 0
            if away.length() < 0.01:
                away = Vec3(1, 0, 0)
            away.normalize()
            right = Vec3(-away.y, away.x, 0)
            weave = math.sin(globalClock.getFrameTime() * 1.7) * 12.0
            candidates = [
                self.ai.getPos() + away * 28.0 + right * weave,
                Vec3(-55, 28, 0),
                Vec3(55, -28, 0),
                Vec3(-35, -42, 0),
                Vec3(45, 42, 0),
            ]
            best = candidates[0]
            best_dist = -1
            for c in candidates:
                d = (c - self.player.getPos()).length()
                if d > best_dist:
                    best_dist = d
                    best = c
            return best

        if self.ai_state == "chase":
            prediction = self.heading_to_forward(self.player_body.heading) * self.ai_prediction * 4.0
            cutoff = self.heading_to_right(self.player_body.heading) * self.ai_cutoff_strength * 3.0
            return self.player.getPos() + prediction + cutoff

        if self.ai_state in ["investigate", "search"]:
            return self.ai_memory_pos

        patrol = [Vec3(-24, 22, 0), Vec3(28, 20, 0), Vec3(22, -26, 0), Vec3(-28, -24, 0), Vec3(0, 0, 0)]
        return patrol[int(globalClock.getFrameTime() / 4.0) % len(patrol)]

    def ai_should_slide(self, direction):
        if not self.ai_body.on_ground or self.ai_body.is_sliding:
            return False
        probe = self.ai.getPos() + direction * 1.3
        return self.blocked_by_solids(self.ai_body, probe, self.ai_body.stand_height) and not self.blocked_by_solids(self.ai_body, probe, self.ai_body.slide_height)

    def ai_should_jump(self, direction):
        if not self.ai_body.on_ground:
            return False
        probe = self.ai.getPos() + direction * 1.2
        for box in self.solid_boxes:
            if box["kind"] in ["wall", "low", "crawl_gap", "start_gate", "route_wall"]:
                continue
            if self.actor_overlaps_box(box, probe, self.ai_body.radius, self.ai_body.stand_height):
                top = box["pos"].z + box["size"].z
                if top > self.ai.getZ() + 0.3 and top <= self.ai.getZ() + 3.8:
                    return True
        return False

    def choose_ai_direction(self):
        ai_pos = self.ai.getPos()
        target = self.ai_target_position()
        direct = target - ai_pos
        direct.z = 0
        if direct.length() <= 0.001:
            return Vec3(0, 0, 0)

        direct.normalize()
        right = self.heading_to_right(self.vector_to_heading(direct))
        options = [direct, direct + right * 0.85, direct - right * 0.85, right, -right]
        best = direct
        best_score = -999999.0

        for option in options:
            if option.length() <= 0.001:
                continue
            option.normalize()
            probe = ai_pos + option * 1.25
            score = option.dot(direct)
            if self.blocked_by_solids(self.ai_body, probe):
                score -= 1.25
            if self.ai_should_slide(option):
                score += 0.4
            if score > best_score:
                best_score = score
                best = option

        return best

    def update_ai(self, dt):
        if self.game_over or self.won or not self.round_started:
            return

        self.update_ai_perception(dt)
        self.ai_state_text.setText(f"Role: {self.role} | AI: {self.ai_state.upper()}")

        if self.ai_body.hanging:
            self.climb_ledge(self.ai_body)

        if self.update_vaulting(self.ai_body, dt):
            return

        direction = self.choose_ai_direction()
        if direction.length() > 0:
            direction.normalize()
            if self.ai_should_slide(direction):
                self.start_slide(self.ai_body)
            if self.ai_should_jump(direction):
                self.try_jump(self.ai_body)

            target_heading = self.vector_to_heading(direction)
            self.ai_body.heading = self.approach_angle(self.ai_body.heading, target_heading, self.turn_speed * dt)
            self.ai.setH(self.ai_body.heading)
            speed = self.slide_speed if self.ai_body.is_sliding else self.ai_speed
            moved = self.move_mover_with_collision(self.ai_body, direction * speed * dt)

            if moved < 0.02:
                self.ai_body.stuck_timer += dt
            else:
                self.ai_body.stuck_timer = 0.0

            if self.ai_body.stuck_timer > 0.45 and self.ai_body.on_ground:
                self.try_jump(self.ai_body)
                self.ai_body.stuck_timer = 0.0

        if self.ai_body.wall_jump_push_timer > 0:
            self.ai_body.wall_jump_push_timer -= dt
            self.move_mover_with_collision(self.ai_body, self.ai_body.wall_jump_push * dt)

        self.update_mover_slide(self.ai_body, dt)

        if self.ai_body.wall_jump_timer > 0:
            self.ai_body.wall_jump_timer -= dt

        self.update_mover_vertical(self.ai_body, dt)
        self.update_wall_contact_memory(self.ai_body, dt)

        if self.ai_body.wall_contact != 0 and not self.ai_body.on_ground and self.ai_body.wall_jump_timer <= 0:
            self.ai_body.air_velocity = max(self.ai_body.air_velocity, self.wall_slide_fall_speed)

        distance = (self.ai.getPos() - self.player.getPos()).length()
        if self.role == "Runner" and distance < self.ai_attack_range:
            self.trigger_game_over("TAGGED")
        elif self.role == "Chaser" and distance < self.ai_attack_range:
            self.trigger_win("CAUGHT")

    def update_doors(self, dt):
        player_pos = self.player.getPos()
        for door in self.doors:
            distance = (player_pos - door["node"].getPos()).length()
            door["open"] = distance < 4.0
            target_h = door["open_h"] if door["open"] else door["closed_h"]
            door["current_h"] = self.approach_angle(door["current_h"], target_h, 180.0 * dt)
            door["node"].setH(door["current_h"])

    def update_camera(self):
        if self.replay_playing:
            target = (self.player.getPos() + self.ai.getPos()) * 0.5
            self.app.camera.setPos(target.x - 24, target.y - 24, target.z + 20)
            self.app.camera.lookAt(target)
            return

        target = self.player.getPos() + Vec3(0, 0, self.cam_height)
        yaw = math.radians(self.cam_yaw)
        pitch = math.radians(self.cam_pitch)
        forward = Vec3(math.sin(yaw), math.cos(yaw), 0)
        horizontal = self.cam_distance * math.cos(pitch)
        camera_pos = self.player.getPos() - forward * horizontal
        camera_pos.z = self.player.getZ() + self.cam_height + self.cam_distance * math.sin(pitch)
        self.app.camera.setPos(camera_pos)
        self.app.camera.lookAt(target)

    def update_minimap(self):
        def map_pos(world_pos):
            scale = 0.18 / 145.0
            return max(-0.17, min(0.17, world_pos.x * scale)), max(-0.17, min(0.17, world_pos.y * scale))

        px, pz = map_pos(self.player.getPos())
        ax, az = map_pos(self.ai.getPos())
        self.player_dot.setPos(px, 0, pz)
        self.ai_dot.setPos(ax, 0, az)

    def record_replay_frame(self):
        if self.game_over or self.won:
            return
        self.replay_frames.append((Vec3(self.player.getPos()), self.player.getH(), Vec3(self.ai.getPos()), self.ai.getH()))
        if len(self.replay_frames) > 150:
            self.replay_frames.pop(0)

    def start_replay(self):
        self.replay_playing = True
        self.replay_index = 0
        self.ghost_player, _ = self.make_box((0, 0, 0), (0.8, 0.8, 2.4), (0.15, 0.45, 1.0, 0.75), False, "ghost")
        self.ghost_ai, _ = self.make_box((0, 0, 0), (0.9, 0.9, 2.5), (1.0, 0.1, 0.05, 0.75), False, "ghost")

    def update_replay(self):
        if not self.replay_playing:
            return
        if self.replay_index >= len(self.replay_frames):
            self.replay_playing = False
            self.win_text.setText("Press R to restart")
            return

        p_pos, p_h, a_pos, a_h = self.replay_frames[self.replay_index]
        self.ghost_player.setPos(p_pos)
        self.ghost_player.setH(p_h)
        self.ghost_ai.setPos(a_pos)
        self.ghost_ai.setH(a_h)
        self.replay_index += 2

    def update_countdown(self, dt):
        if self.round_started:
            return
        self.countdown -= dt
        if self.countdown > 2.0:
            self.countdown_text.setText("3")
        elif self.countdown > 1.0:
            self.countdown_text.setText("2")
        elif self.countdown > 0.0:
            self.countdown_text.setText("1")
        else:
            self.countdown_text.setText("")
            self.open_start_gate()
            self.round_started = True

    def open_start_gate(self):
        if self.start_gate_open:
            return
        self.start_gate_open = True
        self.start_gate.setZ(7)
        if self.start_gate_box in self.solid_boxes:
            self.solid_boxes.remove(self.start_gate_box)

    def update_timer(self, dt):
        if self.game_over or self.won or not self.round_started:
            return
        self.time_left = max(0.0, self.time_left - dt)
        minutes = int(self.time_left) // 60
        seconds = int(self.time_left) % 60
        self.timer_text.setText(f"{minutes:02d}:{seconds:02d}")
        if self.time_left <= 0.0:
            if self.role == "Runner":
                self.trigger_win("YOU WIN")
            else:
                self.trigger_game_over("TIME UP")

    def trigger_game_over(self, label="TAGGED"):
        if not self.game_over:
            self.game_over = True
            self.countdown_text.setText(label)
            self.win_text.setText("Replay...")
            self.start_replay()

    def trigger_win(self, label="YOU WIN"):
        if not self.won:
            self.won = True
            self.game_over = True
            self.win_text.setText(label)
            self.countdown_text.setText("")
            self.win_task = self.app.taskMgr.doMethodLater(5.0, self.return_to_menu, "return_to_menu")

    def return_to_menu(self, task):
        self.destroy()
        self.app.start_menu()
        return Task.done

    def update(self, task):
        dt = min(globalClock.getDt(), 0.05)
        self.update_mouse_camera_control()
        self.update_countdown(dt)
        self.update_timer(dt)

        if not self.replay_playing:
            self.update_player(dt)
            self.update_ai(dt)
            self.record_replay_frame()
        else:
            self.update_replay()

        self.update_doors(dt)
        self.update_camera()
        self.update_minimap()
        return Task.cont

    def destroy(self):
        if hasattr(self, "task") and self.task:
            self.app.taskMgr.remove(self.task)
            self.task = None
        if self.win_task:
            self.app.taskMgr.remove(self.win_task)
            self.win_task = None
        for node in self.all_nodes:
            if node:
                node.removeNode()
        for ui in ["info", "timer_text", "stamina_text", "ai_state_text", "countdown_text", "win_text"]:
            if getattr(self, ui, None):
                getattr(self, ui).destroy()
        if hasattr(self, "minimap"):
            self.minimap.destroy()
        props = WindowProperties()
        props.setCursorHidden(False)
        self.app.win.requestProperties(props)


class MainMenu:
    def __init__(self, app):
        self.app = app
        self.difficulty = getattr(app, "difficulty", "Normal")
        self.role = getattr(app, "role", "Runner")

        props = WindowProperties()
        props.setCursorHidden(False)
        self.app.win.requestProperties(props)

        self.title = OnscreenText(text="Tag Arena", pos=(0, 0.62), scale=0.11, fg=(1, 1, 1, 1), align=TextNode.ACenter)
        self.subtitle = OnscreenText(
            text=f"Difficulty: {self.difficulty} | Role: {self.role}",
            pos=(0, 0.45),
            scale=0.055,
            fg=(0.85, 0.85, 0.85, 1),
            align=TextNode.ACenter,
            mayChange=True,
        )
        self.panel = DirectFrame(frameColor=(0.15, 0.15, 0.2, 0.9), frameSize=(-0.62, 0.62, -0.5, 0.38), pos=(0, 0, 0))

        self.play_button = DirectButton(text="Play", scale=0.075, pos=(0, 0, 0.24), parent=self.panel, command=self.start_game, frameColor=(0.2, 0.6, 0.2, 1), clickSound=None, rolloverSound=None)
        self.easy_button = DirectButton(text="Easy", scale=0.052, pos=(-0.31, 0, 0.07), parent=self.panel, command=self.set_difficulty, extraArgs=["Easy"], frameColor=(0.2, 0.45, 0.65, 1), clickSound=None, rolloverSound=None)
        self.normal_button = DirectButton(text="Normal", scale=0.052, pos=(0, 0, 0.07), parent=self.panel, command=self.set_difficulty, extraArgs=["Normal"], frameColor=(0.35, 0.45, 0.35, 1), clickSound=None, rolloverSound=None)
        self.hard_button = DirectButton(text="Hard", scale=0.052, pos=(0.31, 0, 0.07), parent=self.panel, command=self.set_difficulty, extraArgs=["Hard"], frameColor=(0.65, 0.25, 0.2, 1), clickSound=None, rolloverSound=None)
        self.runner_button = DirectButton(text="Runner", scale=0.055, pos=(-0.18, 0, -0.1), parent=self.panel, command=self.set_role, extraArgs=["Runner"], frameColor=(0.25, 0.5, 0.25, 1), clickSound=None, rolloverSound=None)
        self.chaser_button = DirectButton(text="Chaser", scale=0.055, pos=(0.18, 0, -0.1), parent=self.panel, command=self.set_role, extraArgs=["Chaser"], frameColor=(0.55, 0.35, 0.2, 1), clickSound=None, rolloverSound=None)
        self.quit_button = DirectButton(text="Quit", scale=0.065, pos=(0, 0, -0.31), parent=self.panel, command=sys.exit, frameColor=(0.65, 0.2, 0.2, 1), clickSound=None, rolloverSound=None)

    def update_subtitle(self):
        self.subtitle.setText(f"Difficulty: {self.difficulty} | Role: {self.role}")

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.app.difficulty = difficulty
        self.update_subtitle()

    def set_role(self, role):
        self.role = role
        self.app.role = role
        self.update_subtitle()

    def start_game(self):
        self.destroy()
        self.app.start_game()

    def destroy(self):
        self.title.destroy()
        self.subtitle.destroy()
        self.panel.destroy()


class Launcher(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.disableMouse()
        self.menu = None
        self.game = None
        self.difficulty = "Normal"
        self.role = "Runner"
        self.start_menu()

    def start_menu(self):
        self.menu = MainMenu(self)

    def start_game(self):
        self.game = TagGame(self, self.difficulty, self.role)


launcher = Launcher()
launcher.run()
