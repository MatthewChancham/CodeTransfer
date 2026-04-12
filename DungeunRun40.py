import tkinter as tk
from tkinter import ttk, messagebox as tk_messagebox
import tkinter.messagebox
import random, math, time, json, os
import ctypes
from tkinter import ttk
# Fix blurry text on high-DPI displays while maintaining proper size
try:
    # Force highest DPI awareness (Per-Monitor V2)
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# Get the DPI scaling factor
try:
    dpi = ctypes.windll.user32.GetDpiForSystem()
    SCALE_FACTOR = dpi / 75
except:
    SCALE_FACTOR = 0.8

# Get screen dimensions so we can cap the game viewport to fit
try:
    _screen_w = ctypes.windll.user32.GetSystemMetrics(0)  # SM_CXSCREEN
    _screen_h = ctypes.windll.user32.GetSystemMetrics(1)  # SM_CYSCREEN
except:
    _screen_w, _screen_h = 1920, 1080

# ---------- Config ----------
# ---------- Config ----------
# The game viewport must fit inside the screen (leave room for taskbar + map panel).
# WINDOW_W / WINDOW_H are the game world viewport — NOT the full window size.
_MAP_RESERVE = 300   # rough space reserved for the map panel on the right
_TASKBAR     = 100   # title bar + taskbar height — generous to keep hotbar on screen
WINDOW_W = min(int(1100 * SCALE_FACTOR), _screen_w - _MAP_RESERVE)
WINDOW_H = min(int(750  * SCALE_FACTOR), _screen_h - _TASKBAR)

# NEW: Define town area clearly
TOWN_X_START = 100
TOWN_Y_START = 100
TOWN_X_END = 1300
TOWN_Y_END = 1000
FOREST_THICKNESS = 1200
# World is bigger than town to have forest all around
# World is bigger than town to have forest all around
# World is bigger than town to have forest all around
WORLD_X_MIN = TOWN_X_START - FOREST_THICKNESS - 300  # Extend left for dungeon 1
WORLD_Y_MIN = TOWN_Y_START - FOREST_THICKNESS - 300  # Extend up 
WORLD_WIDTH = TOWN_X_END + FOREST_THICKNESS + 300    # Extend right for dungeons 2 & 3
WORLD_HEIGHT = TOWN_Y_END + FOREST_THICKNESS + 300   # Extend down for dungeon 4  # Extend up for dungeons
WORLD_WIDTH = TOWN_X_END + 5000
WORLD_HEIGHT = TOWN_Y_END + 5000

# Forest settings
  # How deep the forest extends
ROOM_ROWS = 2
ROOM_COLS = 5
MAX_SKILLS = 30
SAVE_FILE = "player_save.json"
ROOM_W = WINDOW_W // ROOM_COLS
ROOM_H = WINDOW_H // ROOM_ROWS
MAP_PANEL_W = 165   # mini-map strip to the right of the game canvas
MAP_SIZE    = 145   # usable square inside the panel
MAP_PAD     = 10    # padding around the map square
# ---------- Class-based automatic stat growth ----------
CLASS_STAT_GROWTH = {
    'Warrior': {'strength': 1, 'vitality': 1, 'agility': 1, 'intelligence': 0, 'wisdom': 0, 'will': 0, 'constitution': 1},
    'Mage':    {'strength': 0, 'vitality': 0, 'agility': 0, 'intelligence': 2, 'wisdom': 1, 'will': 1, 'constitution': 0},
    'Rogue':   {'strength': 1, 'vitality': 0, 'agility': 1, 'intelligence': 1, 'wisdom': 0, 'will': 1, 'constitution': 0},
    'Cleric':  {'strength': 0, 'vitality': 0, 'agility': 0, 'intelligence': 1, 'wisdom': 1, 'will': 2, 'constitution': 1},
    'Druid':   {'strength': 0, 'vitality': 1, 'agility': 0, 'intelligence': 1, 'wisdom': 2, 'will': 0, 'constitution': 1},
    'Monk':    {'strength': 0, 'vitality': 2, 'agility': 1, 'intelligence': 0, 'wisdom': 0, 'will': 0, 'constitution': 1},
    'Ranger':  {'strength': 1, 'vitality': 0, 'agility': 1, 'intelligence': 1, 'wisdom': 0, 'will': 1, 'constitution': 0},
}

# ---------- Skill Trees ----------
# Each node: name, tier (1-4), prereqs (list), cost (SP), skill_type ('active'/'passive'),
#            desc, branch ('left'/'right'/'center'), passive_bonus (dict or None)
SKILL_TREES = {
    'Warrior': [
        {'name': 'Strikes',                 'tier': 1, 'prereq': [],                        'cost': 0, 'type': 'active',  'desc': 'Quick weapon strike at the nearest enemy.',                    'branch': 'center', 'passive': None},
        {'name': 'Ground Pound',            'tier': 2, 'prereq': ['Strikes'],               'cost': 3, 'type': 'active',  'desc': 'Slam the ground — AoE damage + knockback to all nearby foes.', 'branch': 'left',   'passive': None},
        {'name': 'Strike Projection',       'tier': 3, 'prereq': ['Ground Pound'],          'cost': 5, 'type': 'active',  'desc': 'A powerful forward fist blast dealing heavy damage.',           'branch': 'left',   'passive': None},
        {'name': 'Lingering Aura of Valour','tier': 4, 'prereq': ['Strike Projection'],     'cost': 8, 'type': 'active',  'desc': 'Radiate a damaging aura that also blocks enemy projectiles.',   'branch': 'left',   'passive': None},
        {'name': 'Iron Constitution',       'tier': 2, 'prereq': ['Strikes'],               'cost': 1, 'type': 'passive', 'desc': 'PASSIVE: +15 Max HP, +2 Vitality.',                             'branch': 'right',  'passive': None},
        {'name': 'Battle Hardened',         'tier': 3, 'prereq': ['Iron Constitution'],     'cost': 1, 'type': 'passive', 'desc': 'PASSIVE: +5 Strength.',                                         'branch': 'right',  'passive': None},
        {'name': "Warlord's Might",         'tier': 4, 'prereq': ['Battle Hardened'],       'cost': 2, 'type': 'passive', 'desc': 'PASSIVE: +8 Strength, +10 Max HP.',                               'branch': 'right',  'passive': None},
        {'name': 'Kinetic Shell',           'tier': 2, 'prereq': ['Strikes'],               'cost': 2, 'type': 'passive', 'desc': 'PASSIVE: Gain an energy shield equal to Vitality×5. Taking damage restores Mana equal to half the damage absorbed.', 'branch': 'center', 'passive': None},
    ],
    'Mage': [
        {'name': 'Mana Bolt',               'tier': 1, 'prereq': [],                        'cost': 0, 'type': 'active',  'desc': 'A fast mana projectile at the nearest enemy.',                  'branch': 'center', 'passive': None},
        {'name': 'Fireball',                'tier': 2, 'prereq': ['Mana Bolt'],             'cost': 6, 'type': 'active',  'desc': 'Explosive fireball — deals AoE fire damage on impact.',         'branch': 'left',   'passive': None},
        {'name': 'Icicle',                  'tier': 3, 'prereq': ['Fireball'],              'cost': 6, 'type': 'active',  'desc': 'Ice spike that shatters on impact with frost AoE.',             'branch': 'left',   'passive': None},
        {'name': 'Chain Lightning',         'tier': 4, 'prereq': ['Icicle'],                'cost': 7, 'type': 'active',  'desc': 'Lightning bolt that chains between up to 5 enemies.',           'branch': 'left',   'passive': None},
        {'name': 'Mana Bubble',             'tier': 2, 'prereq': ['Mana Bolt'],             'cost': 5, 'type': 'passive', 'desc': 'PASSIVE: +15 Max Mana, +2 Intelligence.',                       'branch': 'right',  'passive': None},
        {'name': 'Arcane Mind',             'tier': 3, 'prereq': ['Mana Bubble'],           'cost': 1, 'type': 'active',  'desc': 'Toggle a mana-powered shield that repels enemies and projectiles.', 'branch': 'right', 'passive': None},
        {'name': 'Mana Surge',              'tier': 4, 'prereq': ['Arcane Mind'],           'cost': 2, 'type': 'passive', 'desc': 'PASSIVE: +4 Intelligence, +4 Wisdom, +2 Mana Regen.',           'branch': 'right',  'passive': None},
    ],
    'Rogue': [
        {'name': 'Dark Slash',              'tier': 1, 'prereq': [],                        'cost': 0, 'type': 'active',  'desc': 'A shadowy slice dealing damage to nearby foes.',                'branch': 'center', 'passive': None},
        {'name': 'Shadow Dagger',           'tier': 2, 'prereq': ['Dark Slash'],            'cost': 3, 'type': 'active',  'desc': 'Hurl a shadowy dagger at high speed.',                          'branch': 'left',   'passive': None},
        {'name': 'Blink',                   'tier': 3, 'prereq': ['Shadow Dagger'],         'cost': 6, 'type': 'active',  'desc': 'Teleport a great distance toward the nearest enemy.',           'branch': 'left',   'passive': None},
        {'name': 'Thousand Cuts',           'tier': 4, 'prereq': ['Blink'],                 'cost': 7, 'type': 'active',  'desc': 'Unleash a rapid flurry of slashes on a single target.',         'branch': 'left',   'passive': None},
        {'name': 'Fleet Foot',              'tier': 2, 'prereq': ['Dark Slash'],            'cost': 1, 'type': 'passive', 'desc': 'PASSIVE: +2 Agility, +10% Move Speed.',                         'branch': 'right',  'passive': None},
        {'name': 'Poison Edge',             'tier': 3, 'prereq': ['Fleet Foot'],            'cost': 1, 'type': 'passive', 'desc': 'PASSIVE: +3 Agility, +3 Strength.',                              'branch': 'right',  'passive': None},
        {'name': 'Shadow Mastery',          'tier': 4, 'prereq': ['Poison Edge'],           'cost': 2, 'type': 'passive', 'desc': 'PASSIVE: +5 Agility, +8 Strength.',                               'branch': 'right',  'passive': None},
    ],
    'Cleric': [
        {'name': 'Light Bolt',              'tier': 1, 'prereq': [],                        'cost': 0, 'type': 'active',  'desc': 'A bolt of focused holy light.',                                 'branch': 'center', 'passive': None},
        {'name': 'Minor Heal',              'tier': 2, 'prereq': ['Light Bolt'],            'cost': 5, 'type': 'active',  'desc': 'Restore HP equal to your magic power.',                         'branch': 'left',   'passive': None},
        {'name': 'Light Beam',              'tier': 3, 'prereq': ['Minor Heal'],            'cost': 5, 'type': 'active',  'desc': 'Summon a rotating beam of holy light for 3 seconds.',           'branch': 'left',   'passive': None},
        {'name': 'Summon Range Sentry',     'tier': 4, 'prereq': ['Light Beam'],            'cost': 6, 'type': 'active',  'desc': 'Summon a sentry that fires holy bolts at all enemies.',         'branch': 'left',   'passive': None},
        {'name': 'Holy Fortitude',          'tier': 2, 'prereq': ['Light Bolt'],            'cost': 1, 'type': 'passive', 'desc': 'PASSIVE: +15 Max HP, +2 Vitality.',                             'branch': 'right',  'passive': None},
        {'name': 'Blessed Aura',            'tier': 3, 'prereq': ['Holy Fortitude'],        'cost': 1, 'type': 'passive', 'desc': 'PASSIVE: +2 Will, +2 Wisdom, improved HP Regen.',               'branch': 'right',  'passive': None},
        {'name': 'Divine Grace',            'tier': 4, 'prereq': ['Blessed Aura'],          'cost': 2, 'type': 'passive', 'desc': 'PASSIVE: +4 Will, +4 Wisdom, +15 Max Mana.',                    'branch': 'right',  'passive': None},
    ],
    'Druid': [
        {'name': 'Thorn Whip',              'tier': 1, 'prereq': [],                        'cost': 0, 'type': 'active',  'desc': 'Lash nearby enemies with a thorny vine.',                       'branch': 'center', 'passive': None},
        {'name': 'Summon Wolf',             'tier': 2, 'prereq': ['Thorn Whip'],            'cost': 5, 'type': 'active',  'desc': 'Summon a loyal wolf that attacks enemies for you.',              'branch': 'left',   'passive': None},
        {'name': 'Leaf Shot',               'tier': 3, 'prereq': ['Summon Wolf'],           'cost': 1, 'type': 'active',  'desc': 'Fire a barrage of razor-sharp leaves at an enemy.',             'branch': 'left',   'passive': None},
        {'name': 'Lashing Vines',           'tier': 4, 'prereq': ['Leaf Shot'],             'cost': 5, 'type': 'active',  'desc': 'Erupt vines in all directions, lashing nearby foes.',           'branch': 'left',   'passive': None},
        {"name": "Nature's Resilience",     'tier': 2, 'prereq': ['Thorn Whip'],            'cost': 1, 'type': 'passive', 'desc': "PASSIVE: +15 Max HP, +2 Wisdom.",                               'branch': 'right',  'passive': None},
        {'name': 'Wild Growth',             'tier': 3, "prereq": ["Nature's Resilience"],   'cost': 1, 'type': 'passive', 'desc': 'PASSIVE: +3 Wisdom, +2 Vitality, improved HP Regen.',           'branch': 'right',  'passive': None},
        {'name': 'Ancient Bond',            'tier': 4, 'prereq': ['Wild Growth'],           'cost': 2, 'type': 'passive', 'desc': 'PASSIVE: +5 Wisdom, +5 Intelligence, +15 Max Mana.',            'branch': 'right',  'passive': None},
    ],
    'Monk': [
        {'name': 'Chi Strike',              'tier': 1, 'prereq': [],                        'cost': 0, 'type': 'active',  'desc': 'Unleash a quick chi-powered slice at the enemy.',               'branch': 'center', 'passive': None},
        {'name': 'Chi Blast',               'tier': 2, 'prereq': ['Chi Strike'],            'cost': 5, 'type': 'active',  'desc': 'Blast chi energy forward in a focused burst.',                  'branch': 'left',   'passive': None},
        {'name': 'Ground Pound',            'tier': 3, 'prereq': ['Chi Blast'],             'cost': 1, 'type': 'active',  'desc': 'Slam the earth with chi force, knocking back all enemies.',     'branch': 'left',   'passive': None},
        {'name': 'Thousand Cuts',           'tier': 4, 'prereq': ['Ground Pound'],          'cost': 2, 'type': 'active',  'desc': 'Chi-empowered rapid strike flurry on one target.',              'branch': 'left',   'passive': None},
        {'name': 'Iron Body',               'tier': 2, 'prereq': ['Chi Strike'],            'cost': 1, 'type': 'passive', 'desc': 'PASSIVE: +20 Max HP, +3 Vitality.',                             'branch': 'right',  'passive': None},
        {'name': 'Inner Peace',             'tier': 3, 'prereq': ['Iron Body'],             'cost': 1, 'type': 'passive', 'desc': 'PASSIVE: +2 Vitality, +4 Constitution, improved HP Regen.',     'branch': 'right',  'passive': None},
        {'name': 'Transcendence',           'tier': 4, 'prereq': ['Inner Peace'],           'cost': 2, 'type': 'passive', 'desc': 'PASSIVE: +5 Vitality, +5 Constitution, +30 Max HP.',            'branch': 'right',  'passive': None},
    ],
    'Ranger': [
        {'name': 'Arrow Shot',              'tier': 1, 'prereq': [],                        'cost': 0, 'type': 'active',  'desc': 'Fire a swift arrow at the nearest enemy.',                      'branch': 'center', 'passive': None},
        {'name': 'Multishot',               'tier': 2, 'prereq': ['Arrow Shot'],            'cost': 5, 'type': 'active',  'desc': 'Fire arrows at up to 3 enemies simultaneously.',                'branch': 'left',   'passive': None},
        {'name': 'Fire Trap',               'tier': 3, 'prereq': ['Multishot'],             'cost': 3, 'type': 'active',  'desc': 'Place a fire trap that ignites enemies on contact.',            'branch': 'left',   'passive': None},
        {'name': 'Frost Trap',              'tier': 4, 'prereq': ['Fire Trap'],             'cost': 3, 'type': 'active',  'desc': 'Place a frost trap that freezes and slows enemies.',            'branch': 'left',   'passive': None},
        {'name': 'Eagle Eye: Auto-Aim',      'tier': 2, 'prereq': ['Arrow Shot'],            'cost': 1, 'type': 'passive', 'desc': 'PASSIVE TOGGLE: All shots automatically lock onto the nearest enemy instead of following the mouse.', 'branch': 'right', 'passive': None},
        {"name": "Hunter's Mark",           'tier': 3, 'prereq': ["Eagle Eye: Auto-Aim"],  'cost': 1, 'type': 'passive', 'desc': 'PASSIVE TOGGLE: Enemies take 20% more damage from your attacks.',                                       'branch': 'right', 'passive': None},
        {'name': 'Lethal Precision',        'tier': 4, "prereq": ["Hunter's Mark"],         'cost': 2, 'type': 'passive', 'desc': 'PASSIVE TOGGLE: Every 3rd shot deals double damage.',                                                   'branch': 'right', 'passive': None},
    ],
}

# ---------- Utilities ----------
def clamp(v,a,b): return max(a,min(b,v))
def distance(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def check_collision(x, y, size, decorations):
    """Check if position collides with any decoration that has collision"""
    for deco in decorations:
        if not deco.get('has_collision'):
            continue
        
        dx = x - deco['x']
        dy = y - deco['y']
        dist = math.hypot(dx, dy)
        
        if dist < size + deco.get('size', 20):
            return True
    
    # Check forest walls using collision_rect
    for deco in decorations:
        if deco.get('type') == 'forest_wall' and 'collision_rect' in deco:
            x1, y1, x2, y2 = deco['collision_rect']
            if (x - size < x2 and x + size > x1 and
                y - size < y2 and y + size > y1):
                return True
    
    return False
def resolve_overlap(a, b):
    """Push objects a and b apart if overlapping."""
    dx = b.x - a.x
    dy = b.y - a.y
    dist = math.hypot(dx, dy)
    min_dist = a.size + b.size

    if dist < min_dist and dist > 0:
        overlap = min_dist - dist
        nx, ny = dx / dist, dy / dist
        a.x -= nx * overlap / 2
        a.y -= ny * overlap / 2
        b.x += nx * overlap / 2
        b.y += ny * overlap / 2
# ---------- Player ----------
class Player:
    # In Player.__init__, reorder the initialization:

    def __init__(self,name='Hero',class_name='Warrior'):
        self.name=name; self.class_name=class_name
        self.x=WINDOW_W//2; self.y=WINDOW_H//2; self.size=16
        
        # Base stats - Monk gets different starting stats
        if class_name == 'Monk':
            self.strength=5; self.vitality=10; self.agility=5  # +5 VIT
            self.intelligence=-1000; self.wisdom=0; self.will=0; self.constitution=5
        else:
            self.strength=5; self.vitality=5; self.agility=5
            self.intelligence=5; self.wisdom=5; self.will=5; self.constitution=3
        
        self.level=1; self.xp=0; self.xp_to_next=100
        self.stat_points=5; self.skill_points=0
        self.skills=[]; self.unlocked_skills=[]
        self.tree_unlocked = set()   # skill names manually unlocked via skill tree
        self.passive_toggles = {}    # passive name -> True/False (on/off)
        
        # NEW: Inventory system - MUST BE BEFORE update_stats()
        self.coins = 50
        self.inventory = []
        self.equipped_items = []
        self.soulbound_items = []
        self.last_soulbound_upgrade_level = 0
        self.chest_items = []   # items stored in the house chest
        self.hotbar_items = [None, None, None]   # consumable hotbar (T/Y/U) — persisted on save
        
        # Give starting soulbound item FIRST
        self.give_starting_item()
        
        # NOW populate skills and update stats
        self.populate_skills()
        self.update_equipped_skills()  # ADD THIS LINE
        self.update_stats()
        self.hp = self.max_hp
        self.mana = self.max_mana
        self.active_skill_effects = {}
        self.item = None
        # Armour shield system
        self.shield = 0
        self.max_shield = 0
        self.shield_regen_rate = 2.0   # HP of shield restored per second (very slow)
            
    def update_stats(self):
        """Calculate stats including equipment and soulbound item bonuses"""
        # Base stats from character
        self.max_hp = 50 + self.vitality * 10
        self.hp = min(getattr(self, 'hp', self.max_hp), self.max_hp)
        self.max_mana = 20 + self.intelligence * 10
        self.mana = min(getattr(self, 'mana', self.max_mana), self.max_mana)
        self.base_speed = 2 + self.agility * 0.15
        self.speed = self.base_speed
        self.atk = 5 + self.strength
        self.mag = 2 + self.will
        self.vit = 2 + self.vitality
        self.wis = 2 + self.wisdom
        self.hp_regen = 0.2 + self.vitality * 0.07
        if self.class_name == 'Monk':
            self.hp_regen = 0.2 + self.vitality * 0.1
        if self.class_name == 'Druid':
            self.hp_regen = 0.2 + self.wisdom * 0.15
        else:
            self.hp_regen = 0.2 + self.vitality * 0.07
        self.mana_regen = 0.1 + self.wisdom * 0.15

        # Reset shield to recalculate from armour items
        old_max_shield = getattr(self, 'max_shield', 0)
        self.max_shield = 0

        def _apply_stat(stat, value):
            if stat == 'strength':
                self.atk += value
            elif stat == 'vitality':
                bonus_hp = value * 10
                self.max_hp += bonus_hp
                self.hp = min(self.hp + bonus_hp, self.max_hp)
                self.vit += value
                self.hp_regen += value * 0.07
            elif stat == 'agility':
                self.base_speed += value * 0.15
                self.speed = self.base_speed
            elif stat == 'intelligence':
                bonus_mana = value * 10
                self.max_mana += bonus_mana
                self.mana = min(self.mana + bonus_mana, self.max_mana)
            elif stat == 'wisdom':
                self.wis += value
                self.mana_regen += value * 0.15
            elif stat == 'will':
                self.mag += value
            elif stat == 'constitution':
                self.constitution += value
            elif stat == 'armour':
                self.max_shield += value * 10  # each armour point = 10 shield HP

        # Create a set to track which items we've already counted
        counted_items = set()

        # Add bonuses from equipped items
        for item in self.equipped_items:
            item_id = id(item)
            if item_id in counted_items:
                continue
            counted_items.add(item_id)
            for stat, value in item.stats.items():
                _apply_stat(stat, value)

        # (passive stat bonuses removed — passives are now behaviour toggles)

        # Apply soulbound item bonuses ONLY if they're not already equipped
        for item in self.soulbound_items:
            item_id = id(item)
            if item_id in counted_items:
                continue  # Skip if already counted from equipped_items
            counted_items.add(item_id)
            for stat, value in item.stats.items():
                _apply_stat(stat, value)

        # Kinetic Shell passive: add energy shield proportional to vitality (BEFORE clamping)
        kinetic_active = 'Kinetic Shell' in getattr(self, 'tree_unlocked', set())
        kinetic_bonus  = (self.vitality * 5) if kinetic_active else 0
        if kinetic_active:
            self.max_shield += kinetic_bonus

        # Clamp shield: if shield newly appeared, fill to full; else keep current
        if self.max_shield > 0 and old_max_shield == 0:
            self.shield = self.max_shield
        elif kinetic_active and getattr(self, 'shield', 0) < kinetic_bonus:
            # First time Kinetic Shell is detected — fill to the kinetic portion
            self.shield = min(kinetic_bonus, self.max_shield)
        else:
            self.shield = min(getattr(self, 'shield', 0), self.max_shield)
    def update_equipped_skills(self):
        """Add skills from equipped items"""
        # Remove item-granted skills first
        self.unlocked_skills = [sk for sk in self.unlocked_skills if not sk.get('from_item')]
        
        # Skill cooldown mapping
        skill_cooldowns = {
            'Flame Strike': 1.0,
            'Fire Breath': 0.12,
            'Spear Throw': 1.5,
            'Mana Bolt': 0.5,
            'Ice Arrow': 1.5,
            'Lightning Bolt': 1,
            'Life Drain': 4.0,
            'Blink': 2.0,
            'Backstab': 2.0,
            'Thousand Cuts': 3.0,
            'Dragon Strike': 8.0,
            'Time Warp': 10.0,
            'Mana Beam': 4.0,
            'Dark Slash': 1.0,
            'Shield': 6.0,
            'Heal': 2.0,
            'Arrow Shot': 0.5,
            'Heated Discharge': 6.0,
            'Permafrost Burst': 6.0
        }
        
        # Add skills from ALL equipped items (including soulbound)
        for item in self.equipped_items:
            print(f"DEBUG: Checking item {item.name} for skills: {item.skills}")
            for skill_name in item.skills:
                if skill_name in self.item_skill_functions:
                    skill_func = self.item_skill_functions[skill_name]
                    cooldown = skill_cooldowns.get(skill_name, 2.0)  # Default to 2.0 if not specified
                    new_skill = {
                        'skill': skill_func,
                        'name': skill_name,
                        'key': 0,  # Unassigned by default
                        'level': self.level,
                        'cooldown': cooldown,  # Use specific cooldown
                        'last_used': 0,
                        'cooldown_mod': 1.0,
                        'from_item': True  # Mark as item skill
                    }
                    self.unlocked_skills.append(new_skill)
                    print(f"DEBUG: Added skill {skill_name} from {item.name}")
    def equip_item(self, item):
        """Equip an item - only one item per type allowed"""
        if item not in self.inventory:
            return False
        
        # Unequip any item of the same type
        for equipped in list(self.equipped_items):
            if equipped.item_type == item.item_type:
                self.unequip_item(equipped)
        
        # Add to equipped list (both soulbound and regular items)
        self.equipped_items.append(item)
        
        self.update_stats()
        self.update_equipped_skills()
        return True
    def unequip_item(self, item):
        """Unequip an item"""
        if item in self.equipped_items:
            self.equipped_items.remove(item)
            self.update_stats()
            self.update_equipped_skills()  # ADD THIS LINE
            return True
        return False
            
    def add_item_to_inventory(self, item):
        """Add item to inventory"""
        self.inventory.append(item)
        # Track soulbound items for permanent bonuses
        if item.soulbound and item not in self.soulbound_items:
            self.soulbound_items.append(item)
    
    def remove_item_from_inventory(self, item):
        """Remove item from inventory"""
        if item in self.inventory:
            if item in self.equipped_items:
                self.unequip_item(item)
            self.inventory.remove(item)
            return True
        return False
    
    def die(self):
        """Called when player dies — lose 10% of coins."""
        penalty = max(1, int(self.coins * 0.10))
        self.coins = max(0, self.coins - penalty)
    def give_starting_item(self):
        """Give each class a soulbound weapon"""
        starting_items = {
            'Warrior': {'name': 'Iron Spear', 'type': 'weapon', 'rarity': 'Common', 
                       'stats': {'strength': 1, 'vitality': 1}, 'skills': [], 'weapon_type': 'spear'},
            'Mage': {'name': 'Novice Staff', 'type': 'weapon', 'rarity': 'Common',
                    'stats': {'intelligence': 1, 'wisdom': 1}, 'skills': [], 'weapon_type': 'staff'},
            'Rogue': {'name': 'Shadow Dagger', 'type': 'weapon', 'rarity': 'Common',
                     'stats': {'agility': 1, 'strength': 1}, 'skills': [], 'weapon_type': 'dagger'},
            'Cleric': {'name': 'Holy Staff', 'type': 'weapon', 'rarity': 'Common',
                      'stats': {'will': 1, 'wisdom': 1}, 'skills': [], 'weapon_type': 'wand'},
            'Druid': {'name': 'Nature Staff', 'type': 'weapon', 'rarity': 'Common',
                     'stats': {'wisdom': 1, 'intelligence': 1}, 'skills': [], 'weapon_type': 'quarterstaff'},
            'Monk': {'name': 'Blessed Fists', 'type': 'weapon', 'rarity': 'Common',
                    'stats': {'vitality': 2}, 'skills': [], 'weapon_type': 'hand'},
            'Ranger': {'name': 'Hunter\'s Bow', 'type': 'weapon', 'rarity': 'Common',
                      'stats': {'agility': 1, 'strength': 1}, 'skills': [], 'weapon_type': 'bow'}
        }
        
        item_data = starting_items.get(self.class_name)
        if item_data:
            item = InventoryItem(
                name=item_data['name'],
                item_type=item_data['type'],
                rarity=item_data['rarity'],
                stats=item_data['stats'],
                skills=item_data['skills'],
                soulbound=True,
                weapon_type=item_data.get('weapon_type')
            )
            self.inventory.append(item)
            self.soulbound_items.append(item)
            # Soulbound weapon is NOT auto-equipped on fresh start.
            # It will only be equipped if it was saved in equipped_items from a previous session.
    def populate_skills(self):
        def howl(summon, game):
            if not game.room.enemies:
                return

            owner = summon.owner if summon.owner else game.player
            target = min(game.room.enemies, key=lambda e: distance((summon.x, summon.y), (e.x, e.y)))
            angle_center = math.atan2(target.y - summon.y, target.x - summon.x)

            # Base parameters for Wi-Fi style slashes
            speed = 5
            life = 2.0
            damage = owner.wis / 2

            # Fire three slash projectiles with small size and spacing
            for i in range(3):
                radius = 6   # keep them thin
                length = 12 + i * 15   # short reach, spaced out (12, 27, 42)
                spawn_x = summon.x + math.cos(angle_center) * length
                spawn_y = summon.y + math.sin(angle_center) * length

                game.spawn_projectile(
                    spawn_x, spawn_y,
                    angle_center,
                    speed,
                    life,
                    radius,
                    "gray",
                    damage,
                    owner="summon",
                    stype="slash"   # reuse your slash projectile type
                )
        def lightbolt(summon, game):
            if not game.room.enemies:
                return

            owner = summon.owner if summon.owner else game.player
            target = min(game.room.enemies, key=lambda e: distance((summon.x, summon.y), (e.x, e.y)))
            angle_center = math.atan2(target.y - summon.y, target.x - summon.x)

            # Bolt parameters
            speed = 7
            life = 1.5
            damage = owner.mag
            radius = 5  # small, fast bolt

            # Spawn slightly in front of the summon
            spawn_x = summon.x + math.cos(angle_center) * 10
            spawn_y = summon.y + math.sin(angle_center) * 10

            game.spawn_projectile(
                spawn_x, spawn_y,
                angle_center,
                speed,
                life,
                radius,
                "yellow",
                damage,
                owner="summon",
                stype="bolt1"
            )


        def strike_projection(player, game):
            if player.mana < 1 or not game.room.enemies: return
            player.mana -= 1
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            game.spawn_projectile(player.x, player.y, ang, 8, 0.3, 8, 'red', player.atk*3, stype='slash2')
        def leaf_shot(player, game):
            if player.mana < 5 or not game.room.enemies: return
            player.mana -= 5
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            game.spawn_projectile(player.x, player.y, ang, 6, 1.0, 8, 'green', player.atk*2, stype='leaf')

        def summon_wolf(player, game):
            if player.mana < 10:
                return
            player.mana -= 10

            wolf = Summoned(
                "Wolf",
                hp=30 + player.wis,
                atk=5 + player.wis,              # <-- fixed here
                spd=3 + player.wis / 20,
                x=player.x + 20,
                y=player.y + 20,
                duration=15 + player.wis,
                role="loyal",
                owner=player,
                mana_upkeep=2.5
            )

            wolf.skills.append({
                'skill': howl,
                'name': 'Howl',
                'cooldown': 0.8,
                'last_used': 0
            })

            # Add wolf to active summons
            game.summons.append(wolf)
        def summon_sentry(player, game):
            if player.mana < 10:
                return
            player.mana -= 10

            sentry = Summoned(
                "Sentry",
                hp=30 + player.mag,
                atk=5 + player.mag,              # <-- fixed here
                spd=3 + player.mag / 20,
                x=player.x + 20,
                y=player.y + 20,
                duration=15 + player.mag,
                role="loyal",
                owner=player,
                mana_upkeep=2
            )

            sentry.skills.append({
                'skill': lightbolt,
                'name': 'lightbolt',
                'cooldown': 0.4,
                'last_used': 0
            })

            # Add wolf to active summons
            game.summons.append(sentry)
        def laser(player, game):
            if player.mana < 30:
                return
            player.mana -= 30
            
            # Create or activate beam
            if not hasattr(game, 'player_beam') or game.player_beam is None:
                # Aim beam toward mouse
                _lmx, _lmy = game.get_mouse_world_pos()
                angle = math.atan2(_lmy - player.y, _lmx - player.x)
                
                game.player_beam = Beam(
                    player.x, player.y,
                    angle, 500, 'yellow', 12, owner=player
                )
                game.beam_active_until = time.time() + 3.0 + player.mag / 10# 3 second duration

        def fire_trap(player, game):
            if player.mana < 15 or not game.room.enemies:
                return
            player.mana -= 15
            trap = Particle(
                player.x, player.y,
                size=5,
                color="orange",
                life=100.0,
                rtype="trap",
                atype="firetrap",
                angle=0
            )
            game.particles.append(trap)
        def frost_trap(player, game):
            if player.mana < 15 or not game.room.enemies:
                return
            player.mana -= 15
            trap = Particle(
                player.x, player.y,
                size=5,
                color="cyan",
                life=100.0,
                rtype="trap",
                atype="frosttrap",
                angle=0
            )
            game.particles.append(trap)

        def minor_heal(player, game):
            if player.mana < 10:
                return
            player.mana -= 10
            heal_amount = player.mag
            player.hp = min(player.max_hp, player.hp + heal_amount)

            # Create diamond particles around the player
            for i in range(6):
                angle = (math.pi * 2 / 6) * i
                ring = 20
                px = player.x + math.cos(angle) * ring
                py = player.y + math.sin(angle) * ring

                diamond = Particle(
                    px, py,
                    size=8,
                    color="gold",
                    life=1.0,
                    rtype="diamond"
                )
                game.particles.append(diamond)


        def lingering_aura_of_valour(player, game):
            duration_ms = 3000   # 3 seconds
            tick_ms = 15         # update every 0.015s
            mana_cost_per_tick = 0.1

            def rapid_tick():
                if player.mana <= 0 or time.time() >= player._rapid_end:
                    player._rapid_active = False
                    return

                player.mana -= mana_cost_per_tick
                game.spawn_particle(player.x, player.y, 35, 'yellow', life=0.5, rtype="aura")

                # Damage nearby enemies
                for e in list(game.room.enemies):
                    if distance((player.x, player.y), (e.x, e.y)) < 50:
                        game.damage_enemy(e, player.atk / 2)

                # Delete projectiles that hit the shield radius
                for proj in list(game.projectiles):
                    d = distance((player.x, player.y), (proj.x, proj.y))
                    if d <= 30 + proj.radius:
                        game.projectiles.remove(proj)

                # Always reschedule next tick
                game.after(tick_ms, rapid_tick)

            if not getattr(player, "_rapid_active", False):
                player._rapid_active = True
                player._rapid_end = time.time() + (duration_ms / 1000.0)
                rapid_tick()


        def ground_pound(player, game):
            if player.mana < 10: 
                return
            player.mana -= 10

            # Shockwave parameters
            shockwave_radius = 20       # starting radius
            max_radius = 120            # how far the wave expands
            expansion_speed = 8         # pixels per frame
            damage = player.atk * 1.5

            # Create a particle that represents the expanding ring
            shockwave = Particle(
                player.x, player.y,
                size=shockwave_radius,
                color='white',
                life=0.5,               # short-lived visual
                rtype='shockwave',
                outline=True
            )
            shockwave.expansion_speed = expansion_speed
            shockwave.max_radius = max_radius
            shockwave.damage = damage
            game.particles.append(shockwave)

            # Apply immediate damage + knockback to enemies in range
            for e in list(game.room.enemies):
                d = distance((player.x, player.y), (e.x, e.y))
                if d < max_radius:
                    # Damage
                    game.damage_enemy(e, damage)

                    # Knockback
                    ang = math.atan2(e.y - player.y, e.x - player.x)
                    push_strength = (max_radius - d) * 2.5  # stronger if closer
                    e.x += math.cos(ang) * push_strength
                    e.y += math.sin(ang) * push_strength

        def thorn_whip(player, game):
            if player.mana < 5 or not game.room.enemies:
                return
            player.mana -= 5

            # Aim lash toward mouse
            _mx, _my = game.get_mouse_world_pos()
            angle_center = math.atan2(_my - player.y, _mx - player.x)

            # Parameters - LONGER duration and reach
            whip_life = 1.2        # Increased from 0.6 to 1.2 seconds
            whip_radius = 100      # Increased from 80 to 100

            # Branch tip that animates out and back
            branch = Particle(
                player.x, player.y,
                size=8, color='#8B4513',  # Slightly bigger tip
                life=whip_life,
                rtype='branch',
                angle=angle_center,
                radius=whip_radius
            )
            game.particles.append(branch)

            # More leaves spread along the whip for better visual
            for i in range(8):  # Increased from 5 to 8 leaves
                offset = i * 12  # Closer spacing
                angle_offset = random.uniform(-0.15, 0.15)  # Less variation
                leaf = Particle(
                    player.x, player.y,
                    size=4, color='#228B22',  # Slightly bigger leaves
                    life=whip_life,
                    rtype='leaf',
                    angle=angle_center + angle_offset,
                    radius=whip_radius - offset
                )
                game.particles.append(leaf)
        def lashing_vines(player, game):
            if player.mana < 15:
                return
            player.mana -= 15

            whip_life = 1.2
            base_radius = 100
            num_whips = 14

            for n in range(num_whips):
                angle_center = (2 * math.pi / num_whips) * n
                angle_center += random.uniform(-0.2, 0.2)

                whip_radius = base_radius + random.randint(-15, 15)

                # Branch tip at FULL LENGTH immediately
                branch = Particle(
                    player.x, player.y,
                    size=random.randint(5, 7),
                    color=random.choice(['#8B4513', '#7A3F1A', '#6E3A16']),
                    life=whip_life,
                    rtype='branch',
                    angle=angle_center,
                    radius=whip_radius   # <-- full length, no short branch
                )
                game.particles.append(branch)

                # Leaves along the vine
                num_leaves = random.randint(6, 10)
                for i in range(num_leaves):
                    # Start leaves closer to the player, spread outward
                    t = i / num_leaves
                    offset = whip_radius * (0.15 + t * 0.75)

                    angle_offset = random.uniform(-0.15, 0.15)

                    leaf = Particle(
                        player.x, player.y,
                        size=random.randint(3, 5),
                        color=random.choice(['#228B22', '#2E8B57', '#1F7A1F']),
                        life=whip_life,
                        rtype='leaf',
                        angle=angle_center + angle_offset,
                        radius=offset
                    )
                    game.particles.append(leaf)


    
        def chi_strike(player, game):
            if player.hp < 3 or not game.room.enemies:
                return
            player.hp -= 3

            # Aim toward mouse
            _mx, _my = game.get_mouse_world_pos()
            angle_center = math.atan2(_my - player.y, _mx - player.x)

            # Slash parameters
            arc_radius = 40     # how far the blade reaches
            arc_width = math.pi/3 # angular width of the slash
            px, py = player.x, player.y

            # Spawn blade particle WITH ANGLE
            size = arc_radius
            # Offset distance so the blade appears further out
            offset = arc_radius // 2   # half the radius forward
            spawn_x = px + math.cos(angle_center) * offset
            spawn_y = py + math.sin(angle_center) * offset

            # Spawn blade particle at the offset position
            blade_particle = Particle(spawn_x, spawn_y, 22, 'cyan', life=0.35, rtype='blade1_fwd', angle=angle_center)
            game.particles.append(blade_particle)

            for e in list(game.room.enemies):
                dx, dy = e.x - px, e.y - py
                dist = math.hypot(dx, dy)
                if dist <= arc_radius:
                    angle_to_enemy = math.atan2(dy, dx)
                    diff = (angle_to_enemy - angle_center + math.pi*2) % (math.pi*2)
                    if diff < arc_width/2 or diff > math.pi*2 - arc_width/2:
                        game.damage_enemy(e, 0)
            # Damage enemies in arc
        def strike(player, game):
            if player.mana < 2 or not game.room.enemies:
                return
            player.mana -= 2

            # Aim toward mouse
            _mx, _my = game.get_mouse_world_pos()
            angle_center = math.atan2(_my - player.y, _mx - player.x)

            # Slash parameters
            arc_radius = 30     # how far the blade reaches
            arc_width = math.pi/3 # angular width of the slash
            px, py = player.x, player.y

            # Spawn blade particle WITH ANGLE
            size = arc_radius
            # Offset distance so the blade appears further out
            offset = arc_radius // 1.5   # half the radius forward
            spawn_x = px + math.cos(angle_center) * offset
            spawn_y = py + math.sin(angle_center) * offset

            # Spawn blade particle at the offset position
            blade_particle = Particle(spawn_x, spawn_y, 22, 'red', life=0.35, rtype='blade1_fwd', angle=angle_center)
            game.particles.append(blade_particle)

            for e in list(game.room.enemies):
                dx, dy = e.x - px, e.y - py
                dist = math.hypot(dx, dy)
                if dist <= arc_radius:
                    angle_to_enemy = math.atan2(dy, dx)
                    diff = (angle_to_enemy - angle_center + math.pi*2) % (math.pi*2)
                    if diff < arc_width/2 or diff > math.pi*2 - arc_width/2:
                        game.damage_enemy(e, 0)


            # Damage enemies in arc
        def dark_slash(player, game):
            if player.mana < 2 or not game.room.enemies:
                return
            player.mana -= 2

            # Aim toward mouse
            _mx, _my = game.get_mouse_world_pos()
            angle_center = math.atan2(_my - player.y, _mx - player.x)

            # Slash parameters
            arc_radius = 24          # reach
            arc_width = math.pi / 3  # angular width

            # Offset origin forward so blade appears in front
            offset = arc_radius * 0.2
            origin_x = player.x + math.cos(angle_center) * offset
            origin_y = player.y + math.sin(angle_center) * offset

            # Spawn blade particle at the same origin used for damage math
            blade_particle = Particle(
                origin_x, origin_y,
                arc_radius,
                'purple',
                life=0.25,
                rtype='blade',
                angle=angle_center - 0.4,
                damage=0  # visual only
            )
            game.particles.append(blade_particle)

            # Damage enemies in the arc sector
            for e in list(game.room.enemies):
                dx, dy = e.x - origin_x, e.y - origin_y
                dist = math.hypot(dx, dy)
                if dist <= arc_radius + e.size:
                    angle_to_enemy = math.atan2(dy, dx)
                    diff = (angle_to_enemy - angle_center + 2 * math.pi) % (2 * math.pi)
                    if diff <= arc_width / 2 or diff >= 2 * math.pi - arc_width / 2:
                        game.damage_enemy(e, player.atk * 1.5)

        def fist_blast(player, game):
            if player.mana < 5 or not game.room.enemies: return
            player.mana -= 5
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            game.spawn_projectile(player.x, player.y, ang, 6, 1.0, 8, 'red', player.atk*2, stype='slash2')
        def chain_lightning(player, game):
            if player.mana < 5 or not game.room.enemies: return
            player.mana -= 5
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            game.spawn_projectile(player.x, player.y, ang, 10, 20, 10,
                      'yellow', player.mag*2,
                      owner='player', stype='lightning', ptype='chain')

        def shadow_dagger(player, game):
            if player.mana < 5 or not game.room.enemies: return
            player.mana -= 5
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            game.spawn_projectile(player.x, player.y, ang, 6, 3, 8, 'purple', player.mag*3, owner='player', stype='dagger')

        def fireball(player, game):
            if player.mana < 15 or not game.room.enemies: return
            player.mana -= 15
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            game.spawn_projectile(player.x, player.y, ang, 8, 10, 12, 'orange',
                                  player.mag * 8, 'player', ptype='fireball', stype='fire_proj')

        def icicle(player, game):
            if player.mana < 15 or not game.room.enemies: return
            player.mana -= 15
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            game.spawn_projectile(player.x, player.y, ang, 8, 10, 10, 'cyan', player.mag, 'player', ptype='icicle', stype='bolt1')


        def ice_shard(player, game):
            if player.mana < 15 or not game.room.enemies: return
            player.mana -= 15
            target = min(game.room.enemies, key=lambda e: distance((player.x, player.y), (e.x, e.y)))
            ang = math.atan2(target.y - player.y, target.x - player.x)
            game.spawn_projectile(player.x, player.y, ang, 6, 3, 8, 'cyan', player.mag*10)

        def mana_bolt(player, game):
            if player.mana < 3 or not game.room.enemies: return
            player.mana -= 3
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            game.spawn_projectile(player.x, player.y, ang, 6, 3, 8, 'cyan', player.mag*3, owner='player', stype='bolt1')
        def light_bolt(player, game):
            if player.mana < 3 or not game.room.enemies: return
            player.mana -= 3
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            game.spawn_projectile(player.x, player.y, ang, 15, 3, 8, 'yellow', player.mag*2, owner='player', stype='bolt1')
        def arrow_shot(player, game):
            if player.mana < 1 or not game.room.enemies: return
            player.mana -= 1
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            game.spawn_projectile(player.x, player.y, ang, 6, 3, 8, 'brown', player.atk*2, owner='player', stype='arrow')
        def chi_blast(player, game):
            if player.hp < 5 or not game.room.enemies: 
                return

            player.hp -= 5
            # Helper function to spawn a bolt
            def spawn_bolt():
                _mx, _my = game.get_mouse_world_pos()
                ang = math.atan2(_my - player.y, _mx - player.x)
                game.spawn_projectile(player.x, player.y, ang, 11, 3, 8, 'cyan', player.vit*2, owner='player', stype='bolt', ptype='chi_blast')

            # Shoot immediately
            spawn_bolt()

            # Schedule next two bolts after 0.5s and 1.0s
            game.after(500, spawn_bolt)   # 500 ms = 0.5 sec
            game.after(1000, spawn_bolt)  # 1000 ms = 1 sec

        def speed_boost(player, game):
            """Rogue skill: temporary speed buff"""
            if player.mana < 10:
                return
            player.mana -= 10
            
            duration = 5.0  # 5 seconds
            speed_multiplier = 3.0  # 3x speed
            
            # Calculate what base_speed SHOULD be based on current agility
            correct_base_speed = 2 + player.agility * 0.15
            
            # Apply speed boost
            player.base_speed = correct_base_speed * speed_multiplier
            player.speed = player.base_speed
            
            # Visual effect - cyan speed lines
            for _ in range(20):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(0, 30)
                px = player.x + math.cos(angle) * dist
                py = player.y + math.sin(angle) * dist
                game.spawn_particle(px, py, 8, 'purple', life=1.0)
            
            # Restore speed after duration
            def reset_speed():
                # Recalculate base speed from agility when restoring
                player.base_speed = 2 + player.agility * 0.15
                player.speed = player.base_speed
            
            game.after(int(duration * 1000), reset_speed)
        def mana_shield(player, game):
            tick_ms = 10         # update every 0.01s
            mana_cost_per_tick = 0.5

            def shield_tick():
                # stop if mana is gone or shield deactivated
                if player.mana <= 0 or not player._mana_shield_active:
                    player._mana_shield_active = False
                    return

                # drain mana
                player.mana -= mana_cost_per_tick

                # shield radius
                shield_radius = 40 + player.mag

                # spawn shield particle
                shield_particle = Particle(
                    player.x, player.y,
                    shield_radius,
                    'white',
                    life=0.1,
                    rtype="shield",
                    outline=True
                )
                game.particles.append(shield_particle)

                # push enemies away
                for e in game.room.enemies:
                    d = distance((player.x, player.y), (e.x, e.y))
                    min_dist = 40 + player.mag
                    if d < min_dist:
                        angle = math.atan2(e.y - player.y, e.x - player.x)
                        push_strength = (min_dist - d) * 2
                        e.x += math.cos(angle) * push_strength
                        e.y += math.sin(angle) * push_strength

                # delete projectiles that hit the shield
                for proj in list(game.projectiles):
                    d = distance((player.x, player.y), (proj.x, proj.y))
                    if d <= shield_radius + getattr(proj, "radius", 5):
                        game.projectiles.remove(proj)

                # always reschedule next tick
                game.after(tick_ms, shield_tick)

            # toggle shield on/off
            if not getattr(player, "_mana_shield_active", False):
                # activate
                player._mana_shield_active = True
                shield_tick()
            else:
                # deactivate if already active
                player._mana_shield_active = False

        def multishot(player, game):
            # Need at least 1 enemy
            if player.mana < 4 or not game.room.enemies: return
            player.mana -= 4
                

            # Pick up to 5 different enemies (closest first)
            enemies = sorted(
                game.room.enemies,
                key=lambda e: distance((player.x, player.y), (e.x, e.y))
            )[:3]

            # Fire an arrow at each target
            for enemy in enemies:
                ang = math.atan2(enemy.y - player.y, enemy.x - player.x)
                game.spawn_projectile(
                    player.x, player.y,
                    ang,
                    7,       # speed
                    3,       # life
                    8,       # radius
                    'brown', # color
                    player.atk * 2,  # damage
                    owner='player',
                    stype='arrow'
                )
        # Item-granted skills
        def mana_beam(player, game):
            if player.mana < 25:
                return
            player.mana -= 25
            
            # Create or activate beam
            if not hasattr(game, 'player_beam') or game.player_beam is None:
                # Aim beam toward mouse
                _mmx, _mmy = game.get_mouse_world_pos()
                angle = math.atan2(_mmy - player.y, _mmx - player.x)
                
                game.player_beam = Beam(
                    player.x, player.y,
                    angle, 400, 'cyan', 10, owner=player
                )
                game.beam_active_until = time.time() + 2.5 + player.mag / 15  # 2.5 second duration
        def flame_strike(player, game):
            if player.mana < 15 or not game.room.enemies:
                return
            player.mana -= 15
            
            _mx, _my = game.get_mouse_world_pos()
            angle_center = math.atan2(_my - player.y, _mx - player.x)
            
            # Fire slash visual effect - large arc
            arc_radius = 80
            num_particles = 40
            arc_width = math.pi / 6
            
            for i in range(num_particles):
                angle = angle_center - arc_width/2 + (i / (num_particles-1)) * arc_width
                x = player.x + math.cos(angle) * arc_radius * random.uniform(0.8, 1.2)
                y = player.y + math.sin(angle) * arc_radius * random.uniform(0.8, 1.2)
                
                # Create flame particles with varied life
                flame = Particle(
                    x, y, 
                    size=random.uniform(8, 15), 
                    color=random.choice(['orange', 'red', 'yellow']),
                    life=random.uniform(0.5, 1.0),
                    owner="player",
                    rtype="flame"
                )
                game.particles.append(flame)
            
            # Damage enemies in arc
            for e in list(game.room.enemies):
                dx = e.x - player.x
                dy = e.y - player.y
                dist = math.hypot(dx, dy)
                if dist <= arc_radius:
                    angle_to_enemy = math.atan2(dy, dx)
                    diff = (angle_to_enemy - angle_center + math.pi*2) % (math.pi*2)
                    if diff < arc_width/2 or diff > math.pi*2 - arc_width/2:
                        game.damage_enemy(e, player.atk * 3)

        def fire_breath(player, game):
            """Activate 5-second dragon breath channel — spawned each frame in update_player."""
            if player.mana < 10:
                return
            player._fire_breath_end  = time.time() + 5.0
            player._fire_breath_tick = 0.0   # accumulator for per-tick mana drain

        def spear_throw(player, game):
            """Throws a piercing spear that travels through all enemies."""
            if player.mana < 12:
                return
            player.mana -= 12
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            proj = game.spawn_projectile(
                player.x, player.y, ang,
                12, 4, 7, '#C0C0C0',
                player.atk * 4, 'player',
                ptype='spear_throw', stype='spear_throw'
            )
            if proj is not None:
                proj.pierce = True          # won't be removed on hit
                proj.hit_ids = set()        # track already-hit enemy ids

        def ice_arrow(player, game):
            if player.mana < 10 or not game.room.enemies:
                return
            player.mana -= 10
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            game.spawn_projectile(player.x, player.y, ang, 10, 3, 8, 'cyan', player.mag * 2, 'player', ptype='icicle', stype='bolt1')
        
        def lightning_bolt(player, game):
            if player.mana < 20 or not game.room.enemies:
                return
            player.mana -= 20
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            game.spawn_projectile(player.x, player.y, ang, 15, 2, 12, 'yellow', player.mag * 5, 'player', stype='lightning')
        
        def life_drain(player, game):
            if player.mana < 25:
                return
            player.mana -= 25
            
            # Find all enemies within range
            targets = []
            for e in game.room.enemies:
                if distance((player.x, player.y), (e.x, e.y)) < 200:
                    targets.append(e)
            
            if not targets:
                return
            
            total_damage = 0
            # Create beam particles to each target
            for e in targets:
                damage = player.atk * 2
                game.damage_enemy(e, damage)
                total_damage += damage
                
                # Create life drain beam effect
                num_segments = 10
                for i in range(num_segments):
                    t = i / num_segments
                    beam_x = player.x + (e.x - player.x) * t
                    beam_y = player.y + (e.y - player.y) * t
                    
                    beam_particle = Particle(
                        beam_x, beam_y,
                        size=random.uniform(4, 8),
                        color='red',
                        life=0.5,
                        rtype='basic'
                    )
                    game.particles.append(beam_particle)
            
            # Heal player
            heal_amount = total_damage // 2
            player.hp = min(player.max_hp, player.hp + heal_amount)
            
            # Healing particles around player
            for _ in range(8):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(0, 20)
                px = player.x + math.cos(angle) * dist
                py = player.y + math.sin(angle) * dist
                game.spawn_particle(px, py, 6, 'green', life=0.8)
        
        def blink(player, game):
            if player.mana < 30 or not game.room.enemies:
                return
            player.mana -= 30
            
            # Blink toward mouse
            _mx, _my = game.get_mouse_world_pos()
            angle = math.atan2(_my - player.y, _mx - player.x)
            
            # Longer blink distance
            blink_dist = 500
            
            # Blink particles at start position
            for _ in range(15):
                offset_x = player.x + random.uniform(-20, 20)
                offset_y = player.y + random.uniform(-20, 20)
                game.spawn_particle(offset_x, offset_y, random.uniform(8, 12), 'purple', life=0.5)
            
            # Move player
            player.x += math.cos(angle) * blink_dist
            player.y += math.sin(angle) * blink_dist
            player.x = clamp(player.x, 0, WINDOW_W)
            player.y = clamp(player.y, 0, WINDOW_H)
            
            # Blink particles at end position
            for _ in range(15):
                offset_x = player.x + random.uniform(-20, 20)
                offset_y = player.y + random.uniform(-20, 20)
                game.spawn_particle(offset_x, offset_y, random.uniform(8, 12), 'purple', life=0.5)
        
        def thousand_cuts(player, game):
            if player.mana < 20 or not game.room.enemies:
                return
            player.mana -= 20

            target = min(game.room.enemies, key=lambda e: distance((player.x, player.y), (e.x, e.y)))

            if distance((player.x, player.y), (target.x, target.y)) < 300:
                num_slashes = 10

                def spawn_slash():
                    # Small jitter so they overlap near the same spot
                    offset_x = random.uniform(-30, 30)
                    offset_y = random.uniform(-30, 30)

                    # Random angle each time â†’ looks chaotic like real cuts
                    slash_angle = random.uniform(0, 2 * math.pi)

                    slash = Particle(
                        target.x + offset_x,
                        target.y + offset_y,
                        size=random.uniform(50, 120),  # longer slashes
                        color=random.choice(['white', 'silver', 'gray']),
                        life=0.4,
                        rtype='slash_line',
                        angle=slash_angle
                    )
                    game.particles.append(slash)

                # spawn first slash immediately
                spawn_slash()

                # schedule the rest with randomâ€‘looking timing
                for i in range(1, num_slashes):
                    game.after(i * 40, spawn_slash)  # 40 ms apart â†’ rapid flurry


                
        
        def dragon_strike_item(player, game):
            if player.mana < 50:
                return
            player.mana -= 50
            
            if not game.room.enemies:
                return
            
            # Aim toward mouse
            _mx, _my = game.get_mouse_world_pos()
            angle_center = math.atan2(_my - player.y, _mx - player.x)
            
            # Dragon head parameters
            dragon_distance = 80
            dragon_x = player.x + math.cos(angle_center) * dragon_distance
            dragon_y = player.y + math.sin(angle_center) * dragon_distance
            arc_radius = 100
            arc_width = math.pi / 1.5
            
            # Draw dragon head with particles
            # Head outline
            for i in range(40):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(20, 35)
                px = dragon_x + math.cos(angle) * dist
                py = dragon_y + math.sin(angle) * dist
                game.spawn_particle(px, py, random.uniform(8, 15), 'orange', life=0.5)
            
            # Eyes
            eye_offset = 15
            for eye_side in [-1, 1]:
                eye_x = dragon_x + math.cos(angle_center + math.pi/2) * eye_offset * eye_side
                eye_y = dragon_y + math.sin(angle_center + math.pi/2) * eye_offset * eye_side
                game.spawn_particle(eye_x, eye_y, 8, 'red', life=0.7)
            
            # Jaw closing - create arc of particles
            for i in range(30):
                angle = angle_center - arc_width/2 + (i / 29) * arc_width
                x = dragon_x + math.cos(angle) * arc_radius
                y = dragon_y + math.sin(angle) * arc_radius
                game.spawn_particle(x, y, random.uniform(6, 12), 'red', life=0.6)
            
            # Damage enemies in arc
            for e in list(game.room.enemies):
                dx = e.x - dragon_x
                dy = e.y - dragon_y
                dist = math.hypot(dx, dy)
                
                if dist <= arc_radius:
                    angle_to_enemy = math.atan2(dy, dx)
                    diff = (angle_to_enemy - angle_center + math.pi*2) % (math.pi*2)
                    if diff < arc_width/2 or diff > math.pi*2 - arc_width/2:
                        game.damage_enemy(e, player.atk * 3)
        
        def time_warp(player, game):
            if player.mana < 40:
                return
            player.mana -= 40
            
            # Apply slow debuff to all enemies
            duration = 5.0
            end_time = time.time() + duration
            
            for e in game.room.enemies:
                # Store original speed if not already stored
                if not hasattr(e, '_original_spd'):
                    e._original_spd = e.spd
                
                # Apply slow
                e.spd = e._original_spd * 0.3
                e._slow_end_time = end_time
            
            # Visual effect - purple time particles
            for _ in range(50):
                x = random.uniform(0, WINDOW_W)
                y = random.uniform(0, WINDOW_H)
                game.spawn_particle(x, y, random.uniform(3, 6), 'purple', life=1.0)
            
            # Schedule cleanup
            def restore_speeds():
                for e in game.room.enemies:
                    if hasattr(e, '_original_spd') and hasattr(e, '_slow_end_time'):
                        if time.time() >= e._slow_end_time:
                            e.spd = e._original_spd
            
            game.after(int(duration * 1000), restore_speeds)
        def heated_discharge(player, game):
            if player.mana < 35:
                return
            player.mana -= 35
            
            # Spawn fire particles in area around player
            radius = 120
            num_particles = 60
            pushback_strength = 15
            
            for _ in range(num_particles):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(0, radius)
                px = player.x + math.cos(angle) * dist
                py = player.y + math.sin(angle) * dist
                
                flame = Particle(
                    px, py,
                    size=random.uniform(10, 18),
                    color=random.choice(['orange', 'red', 'yellow']),
                    life=random.uniform(0.8, 1.5),
                    owner="player",
                    rtype="flame"
                )
                game.particles.append(flame)
            
            # Damage and push back enemies
            for e in list(game.room.enemies):
                d = distance((player.x, player.y), (e.x, e.y))
                if d < radius:
                    # Damage
                    game.damage_enemy(e, player.mag * 2)
                    
                    # Pushback
                    if d > 0:
                        angle = math.atan2(e.y - player.y, e.x - player.x)
                        push = pushback_strength * (1 - d / radius)  # Stronger if closer
                        e.x += math.cos(angle) * push
                        e.y += math.sin(angle) * push
        
        def permafrost_burst(player, game):
            if player.mana < 35:
                return
            player.mana -= 35
            
            # Spawn ice particles in area around player
            radius = 120
            num_particles = 50
            pushback_strength = 15
            
            for _ in range(num_particles):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(0, radius)
                px = player.x + math.cos(angle) * dist
                py = player.y + math.sin(angle) * dist
                
                frost = Particle(
                    px, py,
                    size=random.randint(6, 12),
                    color=random.choice(['cyan', 'white', 'lightblue']),
                    life=random.uniform(1.0, 2.0),
                    owner="player",
                    rtype="frost"
                )
                game.particles.append(frost)
            
            # Damage, slow, and push back enemies
            for e in list(game.room.enemies):
                d = distance((player.x, player.y), (e.x, e.y))
                if d < radius:
                    # Damage
                    game.damage_enemy(e, player.mag * 2)
                    
                    # Slow effect
                    e.spd = e.base_spd * 0.2
                    
                    # Pushback
                    if d > 0:
                        angle = math.atan2(e.y - player.y, e.x - player.x)
                        push = pushback_strength * (1 - d / radius)
                        e.x += math.cos(angle) * push
                        e.y += math.sin(angle) * push
        # Store item skill functions for lookup
        # Store item skill functions for lookup
        self.item_skill_functions = {
            'Flame Strike': flame_strike,
            'Fire Breath': fire_breath,
            'Spear Throw': spear_throw,
            'Mana Bolt': mana_bolt,
            'Ice Arrow': ice_arrow,
            'Lightning Bolt': lightning_bolt,
            'Life Drain': life_drain,
            'Blink': blink,
            'Backstab': thousand_cuts,  # Changed name
            'Thousand Cuts': thousand_cuts,  # Add both for compatibility
            'Dragon Strike': dragon_strike_item,
            'Time Warp': time_warp,
            'Mana Beam': mana_beam,
            'Dark Slash': dark_slash,
            'Shield': mana_shield,
            'Heal': minor_heal,
            'Arrow Shot': arrow_shot,
            'Heated Discharge': heated_discharge,  # NEW
            'Permafrost Burst': permafrost_burst  # NEW
        }
        # Assign skills based on class
        self.skills.clear()
        if self.class_name=='Mage':
            self.skills.append({'skill': mana_bolt,'name':'Mana Bolt','key':1,'level':1,'cooldown':0.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': mana_shield,'name':'Mana Bubble','key':0,'level':1,'cooldown':1,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': fireball,'name':'Fireball','key':0,'level':1,'cooldown':1.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': icicle,'name':'Icicle','key':0,'level':1,'cooldown':1.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': chain_lightning,'name':'Chain Lightning','key':0,'level':1,'cooldown':2,'last_used':0,'cooldown_mod':1.0})
        elif self.class_name=='Warrior':
            self.skills.append({'skill': strike,'name':'Strikes','key':1,'level':1,'cooldown':0.2,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': ground_pound,'name':'Ground Pound','key':0,'level':1,'cooldown':0.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': strike_projection,'name':'Strike Projection','key':0,'level':1,'cooldown':0.3,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': lingering_aura_of_valour,'name':'Lingering Aura of Valour','key':0,'level':1,'cooldown':2,'last_used':0,'cooldown_mod':1.0})
        elif self.class_name=='Rogue':
            self.skills.append({'skill': dark_slash,'name':'Dark Slash','key':1,'level':1,'cooldown':0.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': shadow_dagger,'name':'Shadow Dagger','key':0,'level':1,'cooldown':0.4,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': blink,'name':'Blink','key':0,'level':1,'cooldown':3,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': thousand_cuts,'name':'Thousand Cuts','key':0,'level':1,'cooldown':3,'last_used':0,'cooldown_mod':1.0})
        elif self.class_name=='Cleric':
            self.skills.append({'skill': light_bolt,'name':'Light Bolt','key':1,'level':1,'cooldown':0.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': minor_heal,'name':'Minor Heal','key':0,'level':1,'cooldown':1,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': laser,'name':'Light Beam','key':0,'level':1,'cooldown':2,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': summon_sentry,'name':'Summon Range Sentry','key':0,'level':1,'cooldown':2,'last_used':0,'cooldown_mod':1.0})
        elif self.class_name=='Druid':
            self.skills.append({'skill': thorn_whip,'name':'Thorn Whip','key':1,'level':1,'cooldown':0.4,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': summon_wolf,'name':'Summon Wolf','key':0,'level':1,'cooldown':1,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': leaf_shot,'name':'Leaf Shot','key':0,'level':1,'cooldown':0.8,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': lashing_vines,'name':'Lashing Vines','key':0,'level':1,'cooldown':2,'last_used':0,'cooldown_mod':1.0})
        elif self.class_name=='Monk':
            self.skills.append({'skill': chi_strike,'name':'Chi Strike','key':1,'level':1,'cooldown':0.2,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': chi_blast,'name':'Chi Blast','key':0,'level':1,'cooldown':1.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': ground_pound,'name':'Ground Pound','key':0,'level':1,'cooldown':0.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': thousand_cuts,'name':'Thousand Cuts','key':0,'level':1,'cooldown':3,'last_used':0,'cooldown_mod':1.0})
        elif self.class_name=='Ranger':
            self.skills.append({'skill': arrow_shot,'name':'Arrow Shot','key':1,'level':1,'cooldown':0.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': multishot,'name':'Multishot','key':0,'level':5,'cooldown':1,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': fire_trap,'name':'Fire Trap','key':0,'level':10,'cooldown':1,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': frost_trap,'name':'Frost Trap','key':0,'level':10,'cooldown':1,'last_used':0,'cooldown_mod':1.0})

    
    def gain_xp(self, amount, game=None):
        self.xp += amount
        leveled = False
        levels_gained = 0

        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            levels_gained += 1
            self.stat_points += 2
            self.skill_points += 1
            self.xp_to_next = int(self.xp_to_next * 1.3)

            # Apply class growth
            growth = CLASS_STAT_GROWTH.get(self.class_name, {})
            for stat, value in growth.items():
                setattr(self, stat, getattr(self, stat) + value)

            leveled = True

        # Update player stats after leveling
        if leveled:
            self.update_stats()
            self.unlock_skills()
            # Upgrade soulbound items every 5 levels
            if self.level % 5 == 0 and self.level > self.last_soulbound_upgrade_level:
                self.upgrade_soulbound_items()
                self.last_soulbound_upgrade_level = self.level
            
            # Unlock soulbound skill every 10 levels
                    # Scale existing enemies in the current room once
                if game:
                    for e in game.room.enemies:
                        if isinstance(e, (Enemy, Boss)):
                            e.scale_with_player(self.level)
                    rescale_room_enemies(game.room, self.level)

        return leveled
    def upgrade_soulbound_items(self):
        """Evolve soulbound weapon at levels 10, 25, 40"""
        # Only evolve at specific levels
        if self.level not in [10, 25, 40]:
            return
        
        # Evolution data for each class
        evolutions = {
            'Warrior': {
                10: {'name': 'Iron Spear', 'stats': {'strength': 3, 'vitality': 3}, 'skills': ['Spear Throw']},
                25: {'name': 'Spear of Valour', 'stats': {'strength': 6, 'vitality': 6}, 'skills': ['Spear Throw', 'Life Drain']},
                40: {'name': 'Divine Spear', 'stats': {'strength': 10, 'vitality': 10}, 'skills': ['Spear Throw', 'Life Drain', 'Dragon Strike']}
            },
            'Mage': {
                10: {'name': 'Arcane Staff', 'stats': {'intelligence': 3, 'wisdom': 3}, 'skills': ['Mana Beam']},
                25: {'name': 'Staff of Power', 'stats': {'intelligence': 6, 'wisdom': 6}, 'skills': ['Lightning Bolt', 'Time Warp']},
                40: {'name': 'Staff of Eternity', 'stats': {'intelligence': 10, 'wisdom': 10}, 'skills': ['Lightning Bolt', 'Time Warp', 'Ice Arrow']}
            },
            'Rogue': {
                10: {'name': 'Assassin Dagger', 'stats': {'agility': 3, 'strength': 3}, 'skills': ['Thousand Cuts']},
                25: {'name': 'Void Dagger', 'stats': {'agility': 6, 'strength': 6}, 'skills': ['Thousand Cuts', 'Blink']},
                40: {'name': 'Eternal Blade', 'stats': {'agility': 10, 'strength': 10}, 'skills': ['Backstab', 'Blink', 'Life Drain']}
            },
            'Cleric': {
                10: {'name': 'Divine Staff', 'stats': {'will': 3, 'wisdom': 3}, 'skills': ['Lightning Bolt']},
                25: {'name': 'Staff of Blessing', 'stats': {'will': 6, 'wisdom': 6}, 'skills': ['Lightning Bolt', 'Life Drain']},
                40: {'name': 'Celestial Rod', 'stats': {'will': 10, 'wisdom': 10}, 'skills': ['Lightning Bolt', 'Life Drain', 'Time Warp']}
            },
            'Druid': {
                10: {'name': 'Grove Staff', 'stats': {'wisdom': 3, 'intelligence': 3}, 'skills': ['Ice Arrow']},
                25: {'name': 'Ancient Staff', 'stats': {'wisdom': 6, 'intelligence': 6}, 'skills': ['Ice Arrow', 'Lightning Bolt']},
                40: {'name': 'World Tree Branch', 'stats': {'wisdom': 10, 'intelligence': 10}, 'skills': ['Ice Arrow', 'Lightning Bolt', 'Flame Strike']}
            },
            'Monk': {
                10: {'name': 'Iron Fists', 'stats': {'vitality': 4}, 'skills': ['Flame Strike']},
                25: {'name': 'Dragon Fists', 'stats': {'vitality': 8}, 'skills': ['Flame Strike', 'Life Drain']},
                40: {'name': 'Fists of Heaven', 'stats': {'vitality': 12}, 'skills': ['Flame Strike', 'Life Drain', 'Dragon Strike']}
            },
            'Ranger': {
                10: {'name': 'Elven Bow', 'stats': {'agility': 3, 'strength': 3}, 'skills': ['Ice Arrow']},
                25: {'name': 'Bow of the Wild', 'stats': {'agility': 6, 'strength': 6}, 'skills': ['Ice Arrow', 'Flame Strike']},
                40: {'name': 'Master Longbow', 'stats': {'agility': 8, 'strength': 8}, 'skills': ['Ice Arrow', 'Lightning Bolt']}
            }
        }
        
        # Check if evolution exists for this level
        class_evolutions = evolutions.get(self.class_name, {})
        evolution_data = class_evolutions.get(self.level)
        
        if not evolution_data:
            return
        
        # Find and update the soulbound weapon in INVENTORY (the actual reference used)
        weapon = None
        for item in self.inventory:
            if item.soulbound and item.item_type == 'weapon':
                weapon = item
                break
        
        if not weapon:
            print("ERROR: No soulbound weapon found in inventory!")
            return
        
        # Update weapon properties
        weapon.name = evolution_data['name']
        weapon.stats = evolution_data['stats'].copy()
        weapon.skills = evolution_data['skills'].copy()
        
        print(f"⭐ {weapon.name} has evolved! New power unlocked!")
        print(f"⭐ New skills available: {', '.join(weapon.skills)}")
        
        # Update soulbound_items list to point to the correct weapon
        self.soulbound_items = [item for item in self.inventory if item.soulbound]
        
        # Force refresh equipped skills
        self.update_equipped_skills()
        
        # Always update stats
        self.update_stats()
        self._inv_version = getattr(self, '_inv_version', 0) + 1
        self._soulbound_evolved = True   # flag so UI can force-refresh
           
    def unlock_skills(self):
        """Auto-unlock tier-1 starter skills; tree skills are unlocked via spend_skill_point."""
        if not hasattr(self, 'tree_unlocked'):
            self.tree_unlocked = set()
        tree = SKILL_TREES.get(self.class_name, [])
        tier1_names = {node['name'] for node in tree if node['tier'] == 1}
        # Always mark tier-1 nodes as tree_unlocked so the tree UI shows them gold
        self.tree_unlocked.update(tier1_names)
        for sk in self.skills:
            if sk not in self.unlocked_skills and len(self.unlocked_skills) < MAX_SKILLS:
                # Auto-unlock tier-1 (free starter skill)
                if sk['name'] in tier1_names:
                    self.unlocked_skills.append(sk)
                # Also unlock active skills that have been tree-unlocked
                elif sk['name'] in self.tree_unlocked:
                    self.unlocked_skills.append(sk)

    def get_tree_node(self, skill_name):
        """Return the skill tree node dict for a skill name."""
        for node in SKILL_TREES.get(self.class_name, []):
            if node['name'] == skill_name:
                return node
        return None

    def can_unlock_tree_skill(self, skill_name):
        """Check whether the player can unlock this skill tree node."""
        node = self.get_tree_node(skill_name)
        if not node:
            return False, "Not in skill tree."
        if skill_name in getattr(self, 'tree_unlocked', set()):
            return False, "Already unlocked."
        # Check prerequisites are in tree_unlocked
        unlocked_set = getattr(self, 'tree_unlocked', set())
        for prereq in node['prereq']:
            if prereq not in unlocked_set:
                prereq_node = self.get_tree_node(prereq)
                return False, f"Requires: {prereq}"
        # Check skill points
        if self.skill_points < node['cost']:
            return False, f"Need {node['cost']} SP (have {self.skill_points})."
        return True, ""

    def unlock_tree_skill(self, skill_name):
        """Spend skill points to unlock a skill from the tree. Returns True on success."""
        ok, reason = self.can_unlock_tree_skill(skill_name)
        if not ok:
            return False
        node = self.get_tree_node(skill_name)
        self.skill_points -= node['cost']
        if not hasattr(self, 'tree_unlocked'):
            self.tree_unlocked = set()
        self.tree_unlocked.add(skill_name)
        # For active skills, immediately add to unlocked_skills
        if node['type'] == 'active':
            self.unlock_skills()
        else:
            # Passive: recalculate stats
            self.update_stats()
        return True


    def assign_weapon(self):
        """Assign appropriate weapon based on class"""
        if self.class_name == "Warrior":
            self.item = Item(self.x, self.y, 'spear', 'silver', 20, owner=self)
        elif self.class_name == "Mage":
            self.item = Item(self.x, self.y, 'staff', 'blue', 22, owner=self)
            self.item.gem_color = 'cyan'
        elif self.class_name == "Rogue":
            self.item = Item(self.x, self.y, 'dagger', 'purple', 18, owner=self)
        elif self.class_name == "Cleric":
            self.item = Item(self.x, self.y, 'wand', 'gold', 22, owner=self)
            self.item.gem_color = 'yellow'
        elif self.class_name == "Druid":
            self.item = Item(self.x, self.y, 'quarterstaff', 22, owner=self)
            self.item.gem_color = 'lime'
        elif self.class_name == "Monk":
            self.item = Item(self.x, self.y, 'hand', '#FFA500', 20, owner=self)
        elif self.class_name == "Ranger":
            self.item = Item(self.x, self.y, 'bow', 'brown', 18, owner=self)
    

    # Unlocking soulbound skill
    def to_dict(self):
        return {
            "name": self.name,
            "class_name": self.class_name,
            "level": self.level,
            "xp": self.xp,
            "xp_to_next": self.xp_to_next,
            "stat_points": self.stat_points,
            "skill_points": self.skill_points,
            "strength": self.strength,
            "vitality": self.vitality,
            "agility": self.agility,
            "intelligence": self.intelligence,
            "wisdom": self.wisdom,
            "will": self.will,
            "constitution": self.constitution,
            "hp": self.hp,
            "mana": self.mana,
            "coins": self.coins,
            "inventory": [item.to_dict() for item in self.inventory],
            "chest_items": [item.to_dict() for item in self.chest_items],
            "soulbound_items": [item.name for item in self.soulbound_items],
            "last_soulbound_upgrade_level": self.last_soulbound_upgrade_level,
            "equipped_items": [item.name for item in self.equipped_items],
            "unlocked_skills": [sk['name'] for sk in self.unlocked_skills],
            "active_skill_effects": self.active_skill_effects,
            "tree_unlocked": list(getattr(self, 'tree_unlocked', set())),
            "active_skills": [
                {
                    "name": sk['name'],
                    "key": sk['key'],
                    "cooldown": sk['cooldown'],
                    "last_used": sk['last_used'],
                    "cooldown_mod": sk.get('cooldown_mod', 1.0)
                }
                for sk in self.unlocked_skills
            ],
            "hotbar_items": [
                item.to_dict() if item is not None else None
                for item in getattr(self, 'hotbar_items', [None, None, None])
            ]
        }


    @classmethod
    def from_dict(cls, data):
        p = cls(name=data.get('name','Hero'), class_name=data.get('class_name','Warrior'))
        # Set base stats
        for stat in ['strength','vitality','agility','intelligence','wisdom','will','constitution']:
            if stat in data:
                setattr(p, stat, data[stat])
        p.level = data.get('level',1)
        p.xp = data.get('xp',0)
        p.xp_to_next = data.get('xp_to_next',100)
        p.stat_points = data.get('stat_points',5)
        p.skill_points = data.get('skill_points',0)
        p.coins = data.get('coins', 0)
        
        # Load inventory — preserve ConsumableItem vs InventoryItem distinction
        p.inventory.clear()
        for item_data in data.get('inventory', []):
            if item_data.get('consumable'):
                p.inventory.append(ConsumableItem.from_dict(item_data))
            else:
                p.inventory.append(InventoryItem.from_dict(item_data))
        # Load chest — same distinction
        p.chest_items = []
        for item_data in data.get('chest_items', []):
            if item_data.get('consumable'):
                p.chest_items.append(ConsumableItem.from_dict(item_data))
            else:
                p.chest_items.append(InventoryItem.from_dict(item_data))
        
        # Load equipped items
        equipped_names = data.get('equipped_items', [])
        for item in p.inventory:
            if item.name in equipped_names:
                p.equipped_items.append(item)
        # Load soulbound items
        soulbound_names = data.get('soulbound_items', [])
        for item in p.inventory:
            if item.name in soulbound_names:
                p.soulbound_items.append(item)
        p.last_soulbound_upgrade_level = data.get('last_soulbound_upgrade_level', 0)
        p.update_stats()
        # Re-populate skills
        p.populate_skills()
        p.active_skill_effects = data.get('active_skill_effects', {})
        p.tree_unlocked = set(data.get('tree_unlocked', []))
        # Unlock the saved skills by name
        saved_skills = data.get('unlocked_skills',[])
        for sk in p.skills:
            if sk['name'] in saved_skills:
                p.unlocked_skills.append(sk)
        # Restore item-granted skills from equipped items (soulbound weapon etc.)
        # This must happen AFTER unlocked_skills is populated so keys can be restored below
        p.update_equipped_skills()
        # Restore key/cooldown for all skills (class skills AND item skills)
        saved_active = data.get("active_skills", [])
        for act in saved_active:
            for sk in p.unlocked_skills:
                if sk["name"] == act["name"]:
                    sk["key"] = act.get("key", sk["key"])
                    sk["cooldown"] = act.get("cooldown", sk["cooldown"])
                    sk["last_used"] = act.get("last_used", sk.get("last_used", 0))
                    sk["cooldown_mod"] = act.get("cooldown_mod", 1.0)
        p.hp = min(data.get('hp', p.max_hp), p.max_hp)
        p.mana = min(data.get('mana', p.max_mana), p.max_mana)
        # Load saved hotbar (consumable items by index)
        p._saved_hotbar = data.get('hotbar_items', [None, None, None])
        return p
    def reset(self):
        """Reset character to level 1 and base stats."""
        # Reset core stats
        self.level = 1
        self.xp = 0
        self.xp_to_next = 100
        self.stat_points = 5
        self.skill_points = 0

        # Base stats
        if self.class_name == 'Monk':
            self.strength=5; self.vitality=10; self.agility=5
            self.intelligence=0; self.wisdom=0; self.will=0; self.constitution=3
        else:
            self.strength=5; self.vitality=5; self.agility=5
            self.intelligence=5; self.wisdom=5; self.will=5; self.constitution=3

        # Clear skills and repopulate for class
        self.skills.clear()
        self.unlocked_skills.clear()
        self.populate_skills()
        self.unlock_skills()
        
        # Reset inventory and equipment
        self.inventory.clear()
        self.equipped_items.clear()
        self.soulbound_items.clear()
        self.coins = 0
        
        # Reset soulbound upgrade tracking
        self.last_soulbound_upgrade_level = 0
        
        # Give fresh starting soulbound item
        self.give_starting_item()

        # Reset HP/Mana
        self.update_stats()
        self.hp = self.max_hp
        self.mana = self.max_mana
# ---------- Enemy/Boss/Projectile/Particle ----------
# ---------- Item System ----------

import math

class Item:
    def __init__(self, x, y, item_type='sword', color='gray', size=20, angle=0, owner=None):
        self.x = x
        self.y = y
        self.item_type = item_type
        self.color = color
        self.size = size
        self.angle = angle
        self.owner = owner
        self.gem_color = 'cyan'
        
    def update(self, owner_x, owner_y, target_x, target_y):
        """Update item position and rotation to face target"""
        self.x = owner_x
        self.y = owner_y
        self.angle = math.atan2(target_y - owner_y, target_x - owner_x)
    
    def draw(self, canvas):
        if self.item_type == 'sword':
            self.draw_sword(canvas)
        elif self.item_type == 'spear':
            self.draw_spear(canvas)
        elif self.item_type == 'bow':
            self.draw_bow(canvas)
        elif self.item_type == 'staff':
            self.draw_staff(canvas)
        elif self.item_type == 'hand':
            self.draw_hand(canvas)
        elif self.item_type == 'dagger':
            self.draw_dagger(canvas)
        elif self.item_type == 'wand':
            self.draw_wand(canvas)
        elif self.item_type == 'quarterstaff':
            self.draw_quarterstaff(canvas)
        elif self.item_type == 'axe':
            self.draw_axe(canvas)
        elif self.item_type == 'scythe':
            self.draw_scythe(canvas)
        elif self.item_type == 'katana':
            self.draw_katana(canvas)
    def draw_wand(self, canvas):
        """Shorter, thinner staff with small circular gem"""
        staff_len = self.size * 1.8  # shorter than staff
        
        forward_offset = 5
        center_x = self.x + math.cos(self.angle) * forward_offset
        center_y = self.y + math.sin(self.angle) * forward_offset
        
        back_fraction = 0.3
        front_fraction = 0.7
        staff_end_x = center_x - math.cos(self.angle) * staff_len * back_fraction
        staff_end_y = center_y - math.sin(self.angle) * staff_len * back_fraction
        gem_x = center_x + math.cos(self.angle) * staff_len * front_fraction
        gem_y = center_y + math.sin(self.angle) * staff_len * front_fraction
        
        # Very thin shaft
        canvas.create_line(staff_end_x+1, staff_end_y+1, gem_x+1, gem_y+1,
                           fill='#2F4F4F', width=4)
        canvas.create_line(staff_end_x, staff_end_y, gem_x, gem_y,
                           fill='#654321', width=3)
        canvas.create_line(staff_end_x, staff_end_y, gem_x, gem_y,
                           fill='#8B4513', width=2)
        
        # Small circular gem
        gem_radius = 5
        canvas.create_oval(gem_x - gem_radius, gem_y - gem_radius,
                          gem_x + gem_radius, gem_y + gem_radius,
                          fill=self.gem_color, outline='gold', width=1)
        # Inner glow
        canvas.create_oval(gem_x - gem_radius//2, gem_y - gem_radius//2,
                          gem_x + gem_radius//2, gem_y + gem_radius//2,
                          fill='white', outline='')

    def draw_quarterstaff(self, canvas):
        """Long wooden staff with metal caps - THINNER VERSION"""
        staff_len = self.size * 3.5
        
        forward_offset = 5
        center_x = self.x + math.cos(self.angle) * forward_offset
        center_y = self.y + math.sin(self.angle) * forward_offset
        
        end1_x = center_x - math.cos(self.angle) * staff_len * 0.5
        end1_y = center_y - math.sin(self.angle) * staff_len * 0.5
        end2_x = center_x + math.cos(self.angle) * staff_len * 0.5
        end2_y = center_y + math.sin(self.angle) * staff_len * 0.5
        
        # Main shaft - MUCH THINNER
        canvas.create_line(end1_x+1, end1_y+1, end2_x+1, end2_y+1,
                           fill='#2F4F4F', width=5)  # Shadow
        canvas.create_line(end1_x, end1_y, end2_x, end2_y,
                           fill='#654321', width=4)  # Outer wood
        canvas.create_line(end1_x, end1_y, end2_x, end2_y,
                           fill='#8B4513', width=2)  # Inner highlight
        
        # Metal caps on both ends - smaller
        for end_x, end_y in [(end1_x, end1_y), (end2_x, end2_y)]:
            canvas.create_oval(end_x-4, end_y-4, end_x+4, end_y+4,
                              fill='#C0C0C0', outline='#696969', width=1)
        
        # Grip wrapping in middle - smaller
        for i in range(-2, 3):
            wrap_x = center_x + math.cos(self.angle) * i * 6
            wrap_y = center_y + math.sin(self.angle) * i * 6
            canvas.create_oval(wrap_x-2, wrap_y-2, wrap_x+2, wrap_y+2,
                              fill='#654321', outline='')

    def draw_katana(self, canvas):
        """Elegant katana with subtle curvature and proper tip alignment"""
        import math

        # --- Base positions ---
        offset = 20
        start_x = self.x + math.cos(self.angle) * offset
        start_y = self.y + math.sin(self.angle) * offset

        blade_len = self.size * 2.5
        handle_len = self.size * 0.8

        blade_end_x = start_x + math.cos(self.angle) * blade_len
        blade_end_y = start_y + math.sin(self.angle) * blade_len

        handle_start_x = self.x - math.cos(self.angle) * handle_len
        handle_start_y = self.y - math.sin(self.angle) * handle_len

        # --- Handle (wrapped cord) ---
        canvas.create_line(
            handle_start_x, handle_start_y,
            start_x, start_y,
            fill='#1a1a1a', width=6
        )
        canvas.create_line(
            handle_start_x, handle_start_y,
            start_x, start_y,
            fill='#8B0000', width=4
        )

        # Handle wrap texture
        for i in range(6):
            t = i / 6
            wrap_x = handle_start_x + (start_x - handle_start_x) * t
            wrap_y = handle_start_y + (start_y - handle_start_y) * t
            canvas.create_oval(
                wrap_x - 2, wrap_y - 2,
                wrap_x + 2, wrap_y + 2,
                fill='#000000', outline=''
            )

        # --- Tsuba (guard) ---
        guard_size = 5
        perp = self.angle + math.pi / 2

        guard_pts = [
            start_x + math.cos(perp) * guard_size - math.cos(self.angle) * 2,
            start_y + math.sin(perp) * guard_size - math.sin(self.angle) * 2,
            start_x - math.cos(perp) * guard_size - math.cos(self.angle) * 2,
            start_y - math.sin(perp) * guard_size - math.sin(self.angle) * 2,
            start_x - math.cos(perp) * guard_size + math.cos(self.angle) * 2,
            start_y - math.sin(perp) * guard_size + math.sin(self.angle) * 2,
            start_x + math.cos(perp) * guard_size + math.cos(self.angle) * 2,
            start_y + math.sin(perp) * guard_size + math.sin(self.angle) * 2,
        ]

        canvas.create_polygon(
            guard_pts,
            fill='#D4AF37',
            outline='#8B6914',
            width=2
        )

        # --- Blade curve (subtle sori) ---
        curve_offset = blade_len * 0.12
        perp = self.angle - math.pi / 2

        mid_x = (start_x + blade_end_x) / 2 + math.cos(perp) * curve_offset
        mid_y = (start_y + blade_end_y) / 2 + math.sin(perp) * curve_offset

        # Quadratic BÃ©zier blade
        segments = 100
        points = []

        for i in range(segments + 1):
            t = i / segments
            x = (1 - t)**2 * start_x + 2 * (1 - t) * t * mid_x + t**2 * blade_end_x
            y = (1 - t)**2 * start_y + 2 * (1 - t) * t * mid_y + t**2 * blade_end_y
            points.extend([x, y])

        # --- Blade body (thin, katana-like) ---
        canvas.create_line(points, fill='#555555', width=6, smooth=True)   # spine
        canvas.create_line(points, fill='#E0E0E0', width=4, smooth=True)   # body
        canvas.create_line(points, fill='white', width=1, smooth=True)    # edge

        # --- Properly aligned tip ---
        x2, y2 = points[-2], points[-1]
        x1, y1 = points[-4], points[-3]
        tangent_angle = math.atan2(y2 - y1, x2 - x1)

        tip_len = 10
        tip_width = 3

        tip_x = blade_end_x + math.cos(tangent_angle) * tip_len
        tip_y = blade_end_y + math.sin(tangent_angle) * tip_len

        perp = tangent_angle + math.pi / 2

        left_x = blade_end_x + math.cos(perp) * tip_width
        left_y = blade_end_y + math.sin(perp) * tip_width
        right_x = blade_end_x - math.cos(perp) * tip_width
        right_y = blade_end_y - math.sin(perp) * tip_width

        canvas.create_polygon(
            [tip_x, tip_y, left_x, left_y, right_x, right_y],
            fill='#E0E0E0',
            outline='#888888'
        )


    def draw_axe(self, canvas):
        """Improved double-bit Viking axe"""
        import math

        # Base positioning
        offset = 15
        start_x = self.x + math.cos(self.angle) * offset
        start_y = self.y + math.sin(self.angle) * offset

        handle_len = self.size * 2.5
        blade_width = self.size * 1.2
        blade_height = self.size * 0.8

        # Handle endpoints
        handle_end_x = self.x - math.cos(self.angle) * handle_len * 0.4
        handle_end_y = self.y - math.sin(self.angle) * handle_len * 0.4
        
        # Axe head position (pushed forward)
        head_x = start_x + math.cos(self.angle) * (handle_len * 0.3)
        head_y = start_y + math.sin(self.angle) * (handle_len * 0.3)

        perp = self.angle + math.pi / 2

        # --- Draw Handle ---
        canvas.create_line(
            handle_end_x, handle_end_y, head_x, head_y,
            fill='#2F4F4F', width=10
        )
        canvas.create_line(
            handle_end_x, handle_end_y, head_x, head_y,
            fill='#654321', width=8
        )
        canvas.create_line(
            handle_end_x, handle_end_y, head_x, head_y,
            fill='#8B4513', width=6
        )

        # Pommel
        canvas.create_oval(
            handle_end_x - 7, handle_end_y - 7,
            handle_end_x + 7, handle_end_y + 7,
            fill='#B8860B', outline='#8B6914', width=2
        )

        # --- Draw Double Blades ---
        for side in [1, -1]:  # Top and bottom blades
            # Blade extends perpendicular to handle
            blade_tip_x = head_x + math.cos(perp) * blade_width * side
            blade_tip_y = head_y + math.sin(perp) * blade_width * side
            
            # Blade back edges (along handle direction)
            back_top_x = head_x + math.cos(self.angle) * blade_height
            back_top_y = head_y + math.sin(self.angle) * blade_height
            back_bot_x = head_x - math.cos(self.angle) * blade_height
            back_bot_y = head_y - math.sin(self.angle) * blade_height
            
            # Inner connection point (close to handle)
            inner_x = head_x + math.cos(perp) * (self.size * 0.25) * side
            inner_y = head_y + math.sin(perp) * (self.size * 0.25) * side

            # Create blade polygon (crescent shape)
            blade_points = [
                back_top_x, back_top_y,      # Back top
                blade_tip_x, blade_tip_y,    # Tip
                back_bot_x, back_bot_y,      # Back bottom
                inner_x, inner_y             # Inner connection
            ]

            # Draw blade with shadow
            canvas.create_polygon(
                blade_points,
                fill='#A9A9A9',
                outline='#696969',
                width=2
            )
            
            # Sharp edge highlight
            canvas.create_line(
                back_top_x, back_top_y,
                blade_tip_x, blade_tip_y,
                fill='#E0E0E0',
                width=3
            )
            canvas.create_line(
                back_top_x, back_top_y,
                blade_tip_x, blade_tip_y,
                fill='white',
                width=1
            )

    def draw_scythe(self, canvas):
        """Death's scythe with inward-curving blade"""
        import math

        handle_len = self.size * 3.2
        blade_len = self.size * 1.2  # smaller blade

        # Offset forward a bit
        forward_offset = 5
        center_x = self.x + math.cos(self.angle) * forward_offset
        center_y = self.y + math.sin(self.angle) * forward_offset

        # Handle positions
        handle_start_x = center_x - math.cos(self.angle) * handle_len * 0.5
        handle_start_y = center_y - math.sin(self.angle) * handle_len * 0.5
        handle_end_x = center_x + math.cos(self.angle) * handle_len * 0.5
        handle_end_y = center_y + math.sin(self.angle) * handle_len * 0.5

        # Draw handle
        canvas.create_line(handle_start_x+1, handle_start_y+1, handle_end_x+1, handle_end_y+1, fill='#2F4F4F', width=6)
        canvas.create_line(handle_start_x, handle_start_y, handle_end_x, handle_end_y, fill='#2C1810', width=5)
        canvas.create_line(handle_start_x, handle_start_y, handle_end_x, handle_end_y, fill='#3D2817', width=3)

        # Ferrule
        canvas.create_oval(handle_end_x-5, handle_end_y-5, handle_end_x+5, handle_end_y+5,
                           fill='#404040', outline='#202020', width=2)

        # --- INWARD CURVE FIX ---
        perp_angle = self.angle - math.pi / 2  # flipped inward

        # Control point (mid-curve)
        blade_mid_x = handle_end_x + math.cos(perp_angle) * blade_len * 0.55
        blade_mid_y = handle_end_y + math.sin(perp_angle) * blade_len * 0.55

        # End point (slightly rotated inward)
        blade_end_x = handle_end_x + math.cos(perp_angle + 0.25) * blade_len
        blade_end_y = handle_end_y + math.sin(perp_angle + 0.25) * blade_len

        # Quadratic bezier points
        segments = 15
        blade_points = []
        for i in range(segments + 1):
            t = i / segments
            x = (1-t)**2 * handle_end_x + 2*(1-t)*t * blade_mid_x + t**2 * blade_end_x
            y = (1-t)**2 * handle_end_y + 2*(1-t)*t * blade_mid_y + t**2 * blade_end_y
            blade_points.extend([x, y])

        # Blade shading
        canvas.create_line(blade_points, fill='#202020', width=10, smooth=True)
        canvas.create_line(blade_points, fill='#606060', width=8, smooth=True)
        canvas.create_line(blade_points, fill='#A0A0A0', width=6, smooth=True)

        # Inner sharp edge (offset inward)
        inner_points = []
        for i in range(segments + 1):
            t = i / segments
            x = (1-t)**2 * handle_end_x + 2*(1-t)*t * blade_mid_x + t**2 * blade_end_x
            y = (1-t)**2 * handle_end_y + 2*(1-t)*t * blade_mid_y + t**2 * blade_end_y

            # perpendicular to blade direction
            perp = math.atan2(blade_end_y - handle_end_y, blade_end_x - handle_end_x) - math.pi / 2
            x -= math.cos(perp) * 2
            y -= math.sin(perp) * 2

            inner_points.extend([x, y])

        canvas.create_line(inner_points, fill='white', width=2, smooth=True)

        # Sharp tip
        tip_angle = math.atan2(blade_end_y - blade_mid_y, blade_end_x - blade_mid_x)
        tip_len = 6
        tip_x = blade_end_x + math.cos(tip_angle) * tip_len
        tip_y = blade_end_y + math.sin(tip_angle) * tip_len
        perp_tip = tip_angle - math.pi / 2

        tip_pts = [
            tip_x, tip_y,
            blade_end_x + math.cos(perp_tip) * 3, blade_end_y + math.sin(perp_tip) * 3,
            blade_end_x - math.cos(perp_tip) * 3, blade_end_y - math.sin(perp_tip) * 3
        ]

        canvas.create_polygon(tip_pts, fill='#808080', outline='#606060')

    
    def draw_dagger(self, canvas):
        offset = 22  # closer to the body
        start_x = self.x + math.cos(self.angle) * offset
        start_y = self.y + math.sin(self.angle) * offset

        blade_len = self.size * 0.9   # shorter blade
        handle_len = self.size * 0.3  # smaller handle

        blade_end_x = start_x + math.cos(self.angle) * blade_len
        blade_end_y = start_y + math.sin(self.angle) * blade_len

        handle_start_x = self.x - math.cos(self.angle) * handle_len
        handle_start_y = self.y - math.sin(self.angle) * handle_len

        # Handle (slim but visible)
        canvas.create_line(handle_start_x, handle_start_y, start_x, start_y,
                           fill='#654321', width=6)
        canvas.create_line(handle_start_x, handle_start_y, start_x, start_y,
                           fill='#8B4513', width=4)

        # Pommel
        canvas.create_oval(handle_start_x-3, handle_start_y-3,
                           handle_start_x+3, handle_start_y+3,
                           fill='#FFD700', outline='#8B6914', width=1)

        # Tiny crossguard
        cross_angle = self.angle + math.pi/2
        cross_len = 6
        cx1 = start_x + math.cos(cross_angle) * cross_len
        cy1 = start_y + math.sin(cross_angle) * cross_len
        cx2 = start_x - math.cos(cross_angle) * cross_len
        cy2 = start_y - math.sin(cross_angle) * cross_len
        canvas.create_line(cx1, cy1, cx2, cy2, fill='#8B6914', width=3)

        # Blade shaft (much thicker)
        canvas.create_line(start_x+2, start_y+2, blade_end_x+2, blade_end_y+2,
                           fill='#404040', width=10)
        canvas.create_line(start_x, start_y, blade_end_x, blade_end_y,
                           fill='#c0c0c0', width=9)
        canvas.create_line(start_x, start_y, blade_end_x, blade_end_y,
                           fill='white', width=5)

        # Triangular tip (short but wide)
        tip_len = 5
        tip_x = blade_end_x + math.cos(self.angle) * tip_len
        tip_y = blade_end_y + math.sin(self.angle) * tip_len

        perp = self.angle + math.pi/2
        tip_width = 5  # extra wide tip
        left_x = blade_end_x + math.cos(perp) * tip_width
        left_y = blade_end_y + math.sin(perp) * tip_width
        right_x = blade_end_x - math.cos(perp) * tip_width
        right_y = blade_end_y - math.sin(perp) * tip_width

        canvas.create_polygon([tip_x, tip_y, left_x, left_y, right_x, right_y],
                              fill='#c0c0c0', outline='gray')

    def draw_sword(self, canvas):
        offset = 20
        start_x = self.x + math.cos(self.angle) * offset
        start_y = self.y + math.sin(self.angle) * offset

        blade_len = self.size * 2.0
        handle_len = self.size * 0.6

        blade_end_x = start_x + math.cos(self.angle) * blade_len
        blade_end_y = start_y + math.sin(self.angle) * blade_len

        handle_start_x = self.x - math.cos(self.angle) * handle_len
        handle_start_y = self.y - math.sin(self.angle) * handle_len

        # Handle
        canvas.create_line(handle_start_x, handle_start_y, start_x, start_y,
                           fill='#654321', width=7)
        canvas.create_line(handle_start_x, handle_start_y, start_x, start_y,
                           fill='#8B4513', width=5)

        # Pommel
        canvas.create_oval(handle_start_x-4, handle_start_y-4,
                           handle_start_x+4, handle_start_y+4,
                           fill='#FFD700', outline='#8B6914', width=2)

        # Crossguard
        cross_angle = self.angle + math.pi/2
        cross_len = 15
        cx1 = start_x + math.cos(cross_angle) * cross_len
        cy1 = start_y + math.sin(cross_angle) * cross_len
        cx2 = start_x - math.cos(cross_angle) * cross_len
        cy2 = start_y - math.sin(cross_angle) * cross_len
        canvas.create_line(cx1, cy1, cx2, cy2, fill='#8B6914', width=6)
        canvas.create_line(cx1, cy1, cx2, cy2, fill='#FFD700', width=4)

        # Blade shaft
        canvas.create_line(start_x+2, start_y+2, blade_end_x+2, blade_end_y+2,
                           fill='#404040', width=10)
        canvas.create_line(start_x, start_y, blade_end_x, blade_end_y,
                           fill='#c0c0c0', width=8)
        canvas.create_line(start_x, start_y, blade_end_x, blade_end_y,
                           fill='white', width=3)

        # --- Add a triangular tip to make it sharp ---
        tip_len = 10  # how far the point extends
        tip_x = blade_end_x + math.cos(self.angle) * tip_len
        tip_y = blade_end_y + math.sin(self.angle) * tip_len

        perp = self.angle + math.pi/2
        tip_width = 6
        left_x = blade_end_x + math.cos(perp) * tip_width
        left_y = blade_end_y + math.sin(perp) * tip_width
        right_x = blade_end_x - math.cos(perp) * tip_width
        right_y = blade_end_y - math.sin(perp) * tip_width

        canvas.create_polygon([tip_x, tip_y, left_x, left_y, right_x, right_y],
                              fill='#c0c0c0', outline='gray')

    def draw_spear(self, canvas):
        offset = 10
        start_x = self.x + math.cos(self.angle) * offset
        start_y = self.y + math.sin(self.angle) * offset

        shaft_len = self.size * 2.5
        tip_len   = self.size * 0.6   # shorter spear head

        shaft_end_x = self.x - math.cos(self.angle) * shaft_len * 0.4
        shaft_end_y = self.y - math.sin(self.angle) * shaft_len * 0.4

        tip_base_x = start_x + math.cos(self.angle) * shaft_len * 0.6
        tip_base_y = start_y + math.sin(self.angle) * shaft_len * 0.6

        # Shaft (thin pole)
        canvas.create_line(shaft_end_x, shaft_end_y, tip_base_x, tip_base_y,
                           fill='#654321', width=5)
        canvas.create_line(shaft_end_x, shaft_end_y, tip_base_x, tip_base_y,
                           fill='#8B4513', width=3)

        # Spear head tip (smaller)
        tip_x = tip_base_x + math.cos(self.angle) * tip_len
        tip_y = tip_base_y + math.sin(self.angle) * tip_len

        perp_angle = self.angle + math.pi/2
        side_len = 5   # narrower sides
        left_x = tip_base_x + math.cos(perp_angle) * side_len
        left_y = tip_base_y + math.sin(perp_angle) * side_len
        right_x = tip_base_x - math.cos(perp_angle) * side_len
        right_y = tip_base_y - math.sin(perp_angle) * side_len

        # Smaller leafâ€‘shaped spear head
        canvas.create_polygon(
            [tip_x, tip_y, left_x, left_y, tip_base_x, tip_base_y, right_x, right_y],
            fill='#C0C0C0', outline='#696969', width=2
        )

        # Center ridge line
        canvas.create_line(tip_x, tip_y, tip_base_x, tip_base_y,
                           fill='white', width=2)


        
    def draw_bow(self, canvas):
        bow_len = self.size * 1.7
        perp_angle = self.angle + math.pi/2

        # Move bow forward along aim direction
        forward_offset = 5
        bow_center_x = self.x + math.cos(self.angle) * forward_offset
        bow_center_y = self.y + math.sin(self.angle) * forward_offset

        # Swap top/bottom to correct inversion
        top_x = bow_center_x - math.cos(perp_angle) * (bow_len / 2)
        top_y = bow_center_y - math.sin(perp_angle) * (bow_len / 2)
        bot_x = bow_center_x + math.cos(perp_angle) * (bow_len / 2)
        bot_y = bow_center_y + math.sin(perp_angle) * (bow_len / 2)

        # Curve AWAY from the target (reverse sign vs. previous)
        curve_offset = 20
        mid_x = bow_center_x + math.cos(self.angle) * curve_offset
        mid_y = bow_center_y + math.sin(self.angle) * curve_offset

        # Bow limbs
        canvas.create_line(top_x+2, top_y+2, mid_x+2, mid_y+2, bot_x+2, bot_y+2,
                           fill='#2F4F4F', width=7, smooth=True)
        canvas.create_line(top_x, top_y, mid_x, mid_y, bot_x, bot_y,
                           fill='#654321', width=6, smooth=True)
        canvas.create_line(top_x, top_y, mid_x, mid_y, bot_x, bot_y,
                           fill='#8B4513', width=4, smooth=True)

        # Bowstring
        canvas.create_line(top_x, top_y, bot_x, bot_y, fill='#F5F5DC', width=3)

        # Arrow (centered on player so aim stays true)
        arrow_len = self.size * 1.2
        arrow_end_x = self.x + math.cos(self.angle) * arrow_len
        arrow_end_y = self.y + math.sin(self.angle) * arrow_len
        arrow_start_x = self.x - math.cos(self.angle) * 5
        arrow_start_y = self.y - math.sin(self.angle) * 5

        canvas.create_line(arrow_start_x, arrow_start_y, arrow_end_x, arrow_end_y,
                           fill='#8B4513', width=4)

        # Arrow tip
        tip_perp = self.angle + math.pi/2
        tip_len = 8
        tip_left_x = arrow_end_x + math.cos(tip_perp) * (tip_len / 2)
        tip_left_y = arrow_end_y + math.sin(tip_perp) * (tip_len / 2)
        tip_right_x = arrow_end_x - math.cos(tip_perp) * (tip_len / 2)
        tip_right_y = arrow_end_y - math.sin(tip_perp) * (tip_len / 2)
        tip_point_x = arrow_end_x + math.cos(self.angle) * 10
        tip_point_y = arrow_end_y + math.sin(self.angle) * 10
        canvas.create_polygon([tip_point_x, tip_point_y, tip_left_x, tip_left_y,
                               tip_right_x, tip_right_y], fill='gray')

        # Grip (moved forward with bow center)
        canvas.create_oval(bow_center_x-5, bow_center_y-5, bow_center_x+5, bow_center_y+5,
                           fill='#654321', outline='#8B4513', width=2)


    def draw_staff(self, canvas):
        staff_len = self.size * 3   # reduced from 3

        # Move the staff forward along the aim direction
        forward_offset = 5
        center_x = self.x + math.cos(self.angle) * forward_offset
        center_y = self.y + math.sin(self.angle) * forward_offset

        # Compute shaft endpoints relative to the forward-shifted center
        # Slightly bias toward the gem side so more of the staff is visible in front
        back_fraction = 0.35
        front_fraction = 0.65
        staff_end_x = center_x - math.cos(self.angle) * staff_len * back_fraction
        staff_end_y = center_y - math.sin(self.angle) * staff_len * back_fraction
        gem_x       = center_x + math.cos(self.angle) * staff_len * front_fraction
        gem_y       = center_y + math.sin(self.angle) * staff_len * front_fraction

        # Staff shaft shadow
        canvas.create_line(staff_end_x+2, staff_end_y+2, gem_x+2, gem_y+2,
                           fill='#2F4F4F', width=8)
        # Staff shaft outer
        canvas.create_line(staff_end_x, staff_end_y, gem_x, gem_y,
                           fill='#654321', width=7)
        # Staff shaft inner
        canvas.create_line(staff_end_x, staff_end_y, gem_x, gem_y,
                           fill='#8B4513', width=5)

        # Ornamental wrapping
        segments = 6
        for i in range(segments):
            t = i / segments
            wrap_x = staff_end_x + (gem_x - staff_end_x) * t
            wrap_y = staff_end_y + (gem_y - staff_end_y) * t
            canvas.create_oval(wrap_x-3, wrap_y-3, wrap_x+3, wrap_y+3,
                               fill='#FFD700', outline='#8B6914')

        # Gem diamond (shrunk slightly)
        gem_size = 8   # reduced from 15
        # Diamond points
        top_x = gem_x
        top_y = gem_y - gem_size
        right_x = gem_x + gem_size
        right_y = gem_y
        bottom_x = gem_x
        bottom_y = gem_y + gem_size
        left_x = gem_x - gem_size
        left_y = gem_y

        # Outer glow
        canvas.create_polygon(
            top_x, top_y-5, right_x+5, right_y, bottom_x, bottom_y+5, left_x-5, left_y,
            fill=self.gem_color, outline='', stipple='gray50'
        )
        # Middle glow
        canvas.create_polygon(
            top_x, top_y-2, right_x+2, right_y, bottom_x, bottom_y+2, left_x-2, left_y,
            fill=self.gem_color, outline=''
        )
        # Main diamond
        canvas.create_polygon(
            top_x, top_y, right_x, right_y, bottom_x, bottom_y, left_x, left_y,
            fill=self.gem_color, outline='gold', width=1
        )
        # Highlight inner diamond
        canvas.create_polygon(
            gem_x, gem_y - gem_size//2,
            gem_x + gem_size//2, gem_y,
            gem_x, gem_y + gem_size//2,
            gem_x - gem_size//2, gem_y,
            fill='white', outline=''
        )

    def draw_hand(self, canvas):
        """Two smaller fists placed on either side of the body"""
        arm_len = self.size * 1.2   # smaller arms
        fist_size = 6               # smaller fists

        # Perpendicular direction (left/right from facing angle)
        perp_angle = self.angle + math.pi/2

        # Offset distance from body center
        side_offset = 15

        # Loop for left and right hands
        for side in [-1, 1]:
            # Shoulder position offset to the side
            shoulder_x = self.x + math.cos(perp_angle) * side * side_offset
            shoulder_y = self.y + math.sin(perp_angle) * side * side_offset

            # Elbow extends outward
            elbow_x = shoulder_x + math.cos(self.angle) * arm_len * 0.5
            elbow_y = shoulder_y + math.sin(self.angle) * arm_len * 0.5

            # Fist extends farther outward
            fist_x = shoulder_x + math.cos(self.angle) * arm_len
            fist_y = shoulder_y + math.sin(self.angle) * arm_len

            # Upper arm
            canvas.create_line(shoulder_x, shoulder_y, elbow_x, elbow_y,
                               fill=self.color, width=8)

            # Elbow joint
            canvas.create_oval(elbow_x-4, elbow_y-4, elbow_x+4, elbow_y+4,
                               fill=self.color, outline='black', width=2)

            # Forearm
            canvas.create_line(elbow_x, elbow_y, fist_x, fist_y,
                               fill=self.color, width=7)

            # Fist
            canvas.create_oval(fist_x - fist_size, fist_y - fist_size,
                               fist_x + fist_size, fist_y + fist_size,
                               fill=self.color, outline='black', width=2)

            # Knuckles detail
            knuckle_perp = self.angle + math.pi/2
            for offset in [-3, 0, 3]:
                kx = fist_x + math.cos(knuckle_perp) * offset
                ky = fist_y + math.sin(knuckle_perp) * offset
                canvas.create_oval(kx-1, ky-1, kx+1, ky+1,
                                   fill='white', outline='black', width=1)

class Beam(Item):
    def __init__(self, x, y, angle, length, color='red', width=10, owner=None):
        super().__init__(x, y, 'beam', color, width, angle, owner)
        self.length = length
        self.max_length = length
        self.extending = True
        self.growth_speed = 15  # pixels per frame
        self.current_length = 0
        self.origin_x = x
        self.origin_y = y
        
    def update_origin(self, x, y):
        """Update beam origin to follow owner"""
        self.origin_x = x
        self.origin_y = y
    
    def rotate(self, delta_angle):
        """Rotate the beam by delta_angle"""
        self.angle += delta_angle
    def rotate_beam(self, delta_angle):
        if hasattr(self, "player_beam") and self.player_beam:
            self.player_beam.rotate(delta_angle)

    def update(self, dt):
        """Extend or retract beam"""
        if self.extending:
            self.current_length = min(self.current_length + self.growth_speed, self.max_length)
            if self.current_length >= self.max_length:
                self.extending = False

        
    def draw(self, canvas):
        """Draw beam from origin"""
        end_x = self.origin_x + math.cos(self.angle) * self.current_length
        end_y = self.origin_y + math.sin(self.angle) * self.current_length
        
        # Draw beam with gradient effect (multiple lines)
        for i in range(3):
            width = self.size - i * 2
            alpha_color = self.color if i == 0 else self.lighten_color(self.color)
            canvas.create_line(self.origin_x, self.origin_y, end_x, end_y,
                             fill=alpha_color, width=max(1, width))
    
    def lighten_color(self, color):
        """Simple color lightening for visual effect"""
        if color == 'red':
            return '#ff6666'
        elif color == 'blue':
            return '#6666ff'
        elif color == 'green':
            return '#66ff66'
        return color
# Add after the Item class
class InventoryItem:
    """Items that can be bought, equipped, and provide stat/skill buffs"""
    
    RARITY_COLORS = {
        'Common': '#9d9d9d',
        'Uncommon': '#1eff00',
        'Rare': '#0070dd',
        'Epic': '#a335ee',
        'Legendary': '#ff8000'
    }
    
    def __init__(self, name, item_type, rarity, stats=None, skills=None, soulbound=False, price=0, weapon_type=None):
        self.name = name
        self.item_type = item_type  # 'ring', 'necklace', 'armor', 'weapon', etc.
        self.rarity = rarity
        self.stats = stats or {}  # {'strength': 5, 'vitality': 3}
        self.skills = skills or []  # list of skill names this item grants
        self.soulbound = soulbound
        self.price = price
        self.weapon_type = weapon_type  # 'sword', 'spear', 'bow', 'staff', etc.
            
    
    def get_color(self):
        return self.RARITY_COLORS.get(self.rarity, '#ffffff')
    
    def get_description(self):
        """Generate item description"""
        lines = []
        if self.soulbound:
            lines.append(f"[⭐ SOULBOUND: {self.name}]")
        if self.stats:
            for stat, value in self.stats.items():
                lines.append(f"+{value} {stat.upper()}")
        if self.skills:
            lines.append("Skills: " + ", ".join(self.skills))
        if self.soulbound:
            lines.append("[Bonuses always active]")
        return "\n".join(lines)
    
    def to_dict(self):
        return {
            'name': self.name,
            'item_type': self.item_type,
            'rarity': self.rarity,
            'stats': self.stats,
            'skills': self.skills,
            'soulbound': self.soulbound,
            'price': self.price,
            'weapon_type': self.weapon_type  # ADD THIS
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data['name'],
            item_type=data['item_type'],
            rarity=data['rarity'],
            stats=data.get('stats', {}),
            skills=data.get('skills', []),
            soulbound=data.get('soulbound', False),
            price=data.get('price', 0),
            weapon_type=data.get('weapon_type')  # ADD THIS
        )

# Shop inventory - add after InventoryItem class
SHOP_ITEMS = [
    # Common items
    InventoryItem('Iron Ring', 'ring', 'Common', {'strength': 2}, price=50),
    InventoryItem('Copper Necklace', 'necklace', 'Common', {'vitality': 2}, price=50),
    InventoryItem('Swift Band', 'ring', 'Common', {'agility': 2}, price=50),
    
    # Uncommon items
    InventoryItem('Steel Ring', 'ring', 'Uncommon', {'strength': 4, 'vitality': 2}, price=150),
    InventoryItem('Sage\'s Amulet', 'necklace', 'Uncommon', {'intelligence': 4, 'wisdom': 2}, price=150),
    InventoryItem('Hunter\'s Band', 'ring', 'Uncommon', {'agility': 5}, price=150),
    
    # Rare items
    InventoryItem('Titan Ring', 'ring', 'Rare', {'strength': 7, 'vitality': 5}, price=400),
    InventoryItem('Archmage Pendant', 'necklace', 'Rare', {'intelligence': 8, 'will': 4}, price=400),
    InventoryItem('Shadow Cloak Ring', 'ring', 'Rare', {'agility': 8, 'strength': 3}, price=400),
    
    # Epic items
    InventoryItem('Dragon Band', 'ring', 'Epic', {'strength': 12, 'vitality': 8, 'constitution': 3}, price=1000),
    InventoryItem('Celestial Amulet', 'necklace', 'Epic', {'intelligence': 12, 'wisdom': 8, 'will': 5}, price=1000),

]
# Additional shop items with skills
# Additional shop items with skills
SHOP_ITEMS.extend([
    InventoryItem('Flamethrower', 'weapon', 'Rare',
                 {'strength': 5, 'will': 4},
                 skills=['Fire Breath'],
                 price=550,
                 weapon_type='staff'),
    InventoryItem('Reinforced Bow', 'weapon', 'Uncommon', 
                 {'strength': 4, 'agility': 4}, 
                 skills=['Arrow Shot'], 
                 price=200, 
                 weapon_type='bow'),
    # Rare weapons with skills
    InventoryItem('Primordial blade', 'weapon', 'Rare', 
                 {'strength': 8, 'will': 5}, 
                 skills=['Thousand Cuts'], 
                 price=600, 
                 weapon_type='katana'),  # ALREADY HAS weapon_type
    
    InventoryItem('Frostbite Bow', 'weapon', 'Rare',
                 {'agility': 7, 'intelligence': 4},
                 skills=['Ice Arrow'],
                 price=600,
                 weapon_type='bow'),  # ALREADY HAS weapon_type
    
    InventoryItem('Wand of Lightning', 'weapon', 'Rare',
                 {'intelligence': 10, 'wisdom': 5},
                 skills=['Lightning Bolt'],
                 price=600,
                 weapon_type='wand'),  # ALREADY HAS weapon_type
    
    # Epic items with powerful skills
    InventoryItem('Ring of Vampirism', 'ring', 'Epic',
                 {'strength': 10, 'vitality': 10, 'will': 5},
                 skills=['Life Drain'],
                 price=1500),
    
    InventoryItem('Amulet of Teleportation', 'necklace', 'Epic',
                 {'agility': 12, 'intelligence': 8},
                 skills=['Blink'],
                 price=1500),
    InventoryItem('Amulet of Mana', 'necklace', 'Epic',
                 {'agility': 12, 'intelligence': 8},
                 skills=['Shield','Mana Bolt'],
                 price=1500),
    
    InventoryItem('Shadow Scythe', 'weapon', 'Epic',
                 {'agility': 15, 'strength': 10},
                 skills=['Dark Slash'],
                 price=1500,
                 weapon_type='scythe'),
])

# ── Armour items (sold by blacksmith) ────────────────────────────────────────
ARMOUR_ITEMS = [
    InventoryItem('Iron Helmet',     'helmet',     'Common',   {'armour': 3, 'vitality': 1}, price=120),
    InventoryItem('Iron Chestplate', 'chestplate', 'Common',   {'armour': 6, 'vitality': 2}, price=200),
    InventoryItem('Iron Leggings',   'leggings',   'Common',   {'armour': 4, 'vitality': 1}, price=160),
    InventoryItem('Iron Boots',      'boots',      'Common',   {'armour': 2, 'agility': 1},  price=100),
    InventoryItem('Iron Gauntlets',  'gloves',     'Common',   {'armour': 2, 'strength': 1}, price=100),
    InventoryItem('Steel Helmet',     'helmet',     'Uncommon', {'armour': 6, 'vitality': 2}, price=350),
    InventoryItem('Steel Chestplate', 'chestplate', 'Uncommon', {'armour': 12, 'vitality': 4}, price=600),
    InventoryItem('Steel Leggings',   'leggings',   'Uncommon', {'armour': 8, 'vitality': 3}, price=450),
    InventoryItem('Steel Boots',      'boots',      'Uncommon', {'armour': 5, 'agility': 2},  price=300),
    InventoryItem('Steel Gauntlets',  'gloves',     'Uncommon', {'armour': 5, 'strength': 2}, price=300),
    InventoryItem('Mithril Helmet',     'helmet',     'Rare', {'armour': 12, 'vitality': 4, 'agility': 2}, price=900),
    InventoryItem('Mithril Chestplate', 'chestplate', 'Rare', {'armour': 22, 'vitality': 7},              price=1500),
    InventoryItem('Mithril Leggings',   'leggings',   'Rare', {'armour': 16, 'vitality': 5},              price=1100),
    InventoryItem('Mithril Boots',      'boots',      'Rare', {'armour': 10, 'agility': 4},               price=800),
    InventoryItem('Dragon Helmet',     'helmet',     'Epic', {'armour': 20, 'vitality': 8, 'will': 3}, price=2500),
    InventoryItem('Dragon Chestplate', 'chestplate', 'Epic', {'armour': 38, 'vitality': 12},           price=4000),
    InventoryItem('Dragon Leggings',   'leggings',   'Epic', {'armour': 28, 'vitality': 9},            price=3000),
]
SHOP_ITEMS.extend(ARMOUR_ITEMS)



# ── ConsumableItem: usable potions / food ─────────────────────────────────────
class ConsumableItem:
    EMOJI = {
        'health_potion': '🧪', 'mana_potion': '💧',
        'elixir': '✨', 'bread': '🍞', 'meat': '🍖', 'stew': '🍲',
        'smoke_bomb': '💨',
    }
    RARITY_COLORS = {
        'Common':'#9d9d9d','Uncommon':'#1eff00','Rare':'#0070dd','Epic':'#a335ee',
    }
    def __init__(self, name, subtype, rarity="Common", price=0,
                 hp_restore=0, mana_restore=0,
                 str_boost=0, agi_boost=0, wil_boost=0, boost_duration=0,
                 description=""):
        self.name=name; self.item_type="consumable"; self.subtype=subtype
        self.rarity=rarity; self.price=price; self.hp_restore=hp_restore
        self.mana_restore=mana_restore
        self.str_boost=str_boost; self.agi_boost=agi_boost; self.wil_boost=wil_boost
        self.boost_duration=boost_duration; self.description=description
        self.soulbound=False; self.skills=[]; self.stats={}
        self.count = 1

    def get_emoji(self):
        return self.EMOJI.get(self.subtype,'🎒')

    def get_color(self):
        return self.RARITY_COLORS.get(self.rarity,'#ffffff')

    def get_description(self):
        parts=[]
        if self.hp_restore:    parts.append(f"+{self.hp_restore} HP")
        if self.mana_restore:  parts.append(f"+{self.mana_restore} Mana")
        if self.str_boost:     parts.append(f"+{self.str_boost} STR ({self.boost_duration}s)")
        if self.agi_boost:     parts.append(f"+{self.agi_boost} AGI ({self.boost_duration}s)")
        if self.wil_boost:     parts.append(f"+{self.wil_boost} WIL ({self.boost_duration}s)")
        if self.description:   parts.append(self.description)
        return "\n".join(parts) if parts else "Consumable"

    def use(self, player):
        if self.subtype == 'smoke_bomb':
            # Flag the game to throw a smoke bomb projectile toward the mouse
            player._throw_smoke_bomb = True
            return True
        if self.hp_restore:
            player.hp = min(player.max_hp, player.hp + self.hp_restore)
        if self.mana_restore:
            player.mana = min(player.max_mana, player.mana + self.mana_restore)
        if (self.str_boost or self.agi_boost or self.wil_boost) and self.boost_duration:
            end_t = time.time() + self.boost_duration
            # Apply stat boosts directly; store so update_player can remove them
            if self.str_boost:
                player.strength  += self.str_boost
                player._str_boost_val = getattr(player,'_str_boost_val',0) + self.str_boost
                player._str_boost_end = end_t
            if self.agi_boost:
                player.agility   += self.agi_boost
                player._agi_boost_val = getattr(player,'_agi_boost_val',0) + self.agi_boost
                player._agi_boost_end = end_t
            if self.wil_boost:
                player.will      += self.wil_boost
                player._wil_boost_val = getattr(player,'_wil_boost_val',0) + self.wil_boost
                player._wil_boost_end = end_t
            player.update_stats()
            # Record active buff for the HUD
            if not hasattr(player, 'active_buffs'):
                player.active_buffs = []
            player.active_buffs.append({
                'emoji': self.get_emoji(),
                'name':  self.name,
                'desc':  self.get_description().split('\n')[0],
                'end':   end_t,
                'duration': self.boost_duration,
                'str':   self.str_boost,
                'agi':   self.agi_boost,
                'wil':   self.wil_boost,
            })
        return True

    def to_dict(self):
        return {"consumable":True,"name":self.name,"item_type":self.item_type,
                "subtype":self.subtype,"rarity":self.rarity,"price":self.price,
                "hp_restore":self.hp_restore,"mana_restore":self.mana_restore,
                "str_boost":self.str_boost,"agi_boost":self.agi_boost,
                "wil_boost":self.wil_boost,
                "boost_duration":self.boost_duration,"description":self.description,
                "count":self.count}

    @classmethod
    def from_dict(cls,data):
        # Legacy support: convert old speed_boost/atk_boost to new fields
        agi_b = data.get("agi_boost", 0) or int(data.get("speed_boost", 0) * 20)
        str_b = data.get("str_boost", 0) or data.get("atk_boost", 0)
        obj = cls(name=data["name"],subtype=data.get("subtype","health_potion"),
                   rarity=data.get("rarity","Common"),price=data.get("price",0),
                   hp_restore=data.get("hp_restore",0),mana_restore=data.get("mana_restore",0),
                   str_boost=str_b, agi_boost=agi_b, wil_boost=data.get("wil_boost",0),
                   boost_duration=data.get("boost_duration",0),
                   description=data.get("description",""))
        obj.count = data.get("count", 1)
        return obj

# ── Map item (sold by Oryn the Cartographer) ──────────────────────────────
MAP_ITEM = InventoryItem("Dungeon Map", "map", "Uncommon", {}, price=120)

CONSUMABLE_SHOP_ITEMS = [
    ConsumableItem("Minor Health Potion","health_potion","Common",  price=20, hp_restore=50),
    ConsumableItem("Health Potion",      "health_potion","Uncommon",price=40, hp_restore=100),
    ConsumableItem("Major Health Potion","health_potion","Rare",    price=100,hp_restore=500),
    ConsumableItem("Minor Mana Potion",  "mana_potion",  "Common",  price=20, mana_restore=50),
    ConsumableItem("Mana Potion",        "mana_potion",  "Uncommon",price=40, mana_restore=100),
    ConsumableItem("Elixir of Power",    "elixir",       "Rare",    price=300,
                   hp_restore=200, mana_restore=200, str_boost=5, wil_boost=5, boost_duration=30),
    ConsumableItem("Bread",     "bread","Common",  price=5, hp_restore=15,
                   description="Restores a little HP."),
    ConsumableItem("Roast Meat","meat", "Uncommon",price=10, hp_restore=50,
                   agi_boost=2, boost_duration=20, description="+HP and brief AGI boost."),
    ConsumableItem("Hero Stew", "stew", "Rare",    price=150,
                   hp_restore=200, str_boost=8, wil_boost=8, boost_duration=60,
                   description="Full meal buff."),
    ConsumableItem("Smoke Bomb", "smoke_bomb", "Uncommon", price=50,
                   description="Throw at your feet — all nearby enemies enter a confused wander state for 5s, unable to attack."),
]

# ── CoinParticle: world-space coins dropped on enemy death ─────────────────────
class CoinParticle:
    def __init__(self,x,y,value):
        self.x=x+random.randint(-20,20); self.y=y+random.randint(-20,20)
        self.value=value; self.lifetime=45.0; self.size=7
        self._bob=random.uniform(0,math.pi*2)

    def update(self,dt):
        self.lifetime-=dt; self._bob+=dt*3.0
        return self.lifetime>0

    def draw(self,canvas,sx,sy):
        by=math.sin(self._bob)*2
        canvas.create_oval(sx-self.size,sy-self.size+by,sx+self.size,sy+self.size+by,
                           fill="#FFD700",outline="#B8860B",width=2)
        canvas.create_text(sx,sy+by,text="$",fill="#8B6914",font=("Arial",7,"bold"))

class Summoned:
    def __init__(self, name, hp, atk, spd, x, y, duration=10.0, role="loyal", owner=None, mana_upkeep=0.0):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.spd = spd
        self.x = x
        self.y = y
        self.size = 14
        self.role = role
        self.owner = owner        # reference to player or caster
        self.spawn_time = time.time()
        self.duration = duration  # how long it lasts
        self.state = "follow"     # default behavior
        self.attack_range = 40
        self.last_attack = 0
        self.attack_cooldown = 1.0
        self.room_row = y // ROOM_H
        self.room_col = x // ROOM_W
        self.skills = []
        self.mana_upkeep = mana_upkeep# list of skill dicts, same format as player


    def update(self, game, dt):
        # expire after duration
        if time.time() - self.spawn_time > self.duration:
            if self in game.summons:
                game.summons.remove(self)
            return
        if self.owner:
            # drain mana proportional to dt
            self.owner.mana -= self.mana_upkeep * dt
            if self.owner.mana <= 0:
                # despawn if player runs out
                if self in game.summons:
                    game.summons.remove(self)
                return
        player = game.player if self.owner is None else self.owner
        self.x = clamp(self.x, self.size, WINDOW_W - self.size)
        self.y = clamp(self.y, self.size, WINDOW_H - self.size)
        # --- Movement & attack based on role ---
        if self.role == "loyal":
            # Always stick close to player
            dx, dy = player.x - self.x, player.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 30:
                ang = math.atan2(dy, dx)
                self.x += math.cos(ang) * self.spd
                self.y += math.sin(ang) * self.spd

            # Loyal skill usage: very short range
            for sk in self.skills:
                if time.time() - sk['last_used'] >= sk['cooldown']:
                    for e in game.room.enemies:
                        if distance((player.x, player.y), (e.x, e.y)) < 500:
                            sk['skill'](self, game)
                            sk['last_used'] = time.time()
                            break

        elif self.role == "defense":
            # Stay near player, wider radius
            dx, dy = player.x - self.x, player.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 60:
                ang = math.atan2(dy, dx)
                self.x += math.cos(ang) * self.spd
                self.y += math.sin(ang) * self.spd

            # Attack enemies that approach player
            for e in game.room.enemies:
                if distance((player.x, player.y), (e.x, e.y)) < 80 and time.time() - self.last_attack >= self.attack_cooldown:
                    game.damage_enemy(e, self.atk)
                    self.last_attack = time.time()

            # Defense skill usage: medium range
            for sk in self.skills:
                if time.time() - sk['last_used'] >= sk['cooldown']:
                    for e in game.room.enemies:
                        if distance((player.x, player.y), (e.x, e.y)) < 100:
                            sk['skill'](self, game)
                            sk['last_used'] = time.time()
                            break

        elif self.role == "attack":
            if game.room.enemies:
                # Chase nearest enemy
                target = min(game.room.enemies, key=lambda e: distance((self.x, self.y), (e.x, e.y)))
                dx, dy = target.x - self.x, target.y - self.y
                dist = math.hypot(dx, dy)
                if dist > self.attack_range:
                    ang = math.atan2(dy, dx)
                    self.x += math.cos(ang) * self.spd
                    self.y += math.sin(ang) * self.spd
                elif time.time() - self.last_attack >= self.attack_cooldown:
                    game.damage_enemy(target, self.atk)
                    self.last_attack = time.time()

                # Attack skill usage: long range, anywhere in room
                for sk in self.skills:
                    if time.time() - sk['last_used'] >= sk['cooldown']:
                        sk['skill'](self, game)
                        sk['last_used'] = time.time()
            else:
                # No enemies â†’ follow player
                dx, dy = player.x - self.x, player.y - self.y
                dist = math.hypot(dx, dy)
                if dist > 50:
                    ang = math.atan2(dy, dx)
                    self.x += math.cos(ang) * self.spd
                    self.y += math.sin(ang) * self.spd

        else:
            # Default "melee" role
            dx, dy = player.x - self.x, player.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 50:
                ang = math.atan2(dy, dx)
                self.x += math.cos(ang) * self.spd
                self.y += math.sin(ang) * self.spd

            if game.room.enemies:
                target = min(game.room.enemies, key=lambda e: distance((self.x, self.y), (e.x, e.y)))
                d = distance((self.x, self.y), (target.x, target.y))
                if d <= self.attack_range and time.time() - self.last_attack >= self.attack_cooldown:
                    game.damage_enemy(target, self.atk)
                    self.last_attack = time.time()




    def draw(self, canvas):
        # Default appearance
        color = "lightblue"
        outline = "white"
        shape = "circle"

        # Appearance based on summon name
        if self.name.lower() == "sentry":
            color = "yellow"
            outline = "orange"
            shape = "circle"

        elif self.name.lower() == "wolf":
            color = "gray"
            outline = "white"
            shape = "wolf"


        # Draw shapes
        if shape == "circle":
            canvas.create_oval(
                self.x - self.size, self.y - self.size,
                self.x + self.size, self.y + self.size,
                fill=color, outline=outline
            )

        elif shape == "square":
            canvas.create_rectangle(
                self.x - self.size, self.y - self.size,
                self.x + self.size, self.y + self.size,
                fill=color, outline=outline
            )

        elif shape == "triangle":
            canvas.create_polygon(
                self.x, self.y - self.size,
                self.x - self.size, self.y + self.size,
                self.x + self.size, self.y + self.size,
                fill=color, outline=outline
            )

        elif shape == "wolf":
            canvas.create_oval(
                self.x - self.size*1.2, self.y - self.size*0.8,
                self.x + self.size*1.2, self.y + self.size*0.8,
                fill=color, outline=outline
            )

        elif shape == "glow":
            canvas.create_oval(
                self.x - self.size*1.6, self.y - self.size*1.6,
                self.x + self.size*1.6, self.y + self.size*1.6,
                outline=color, width=3
            )
            canvas.create_oval(
                self.x - self.size, self.y - self.size,
                self.x + self.size, self.y + self.size,
                fill=color, outline=outline
            )

        # Draw name label
        canvas.create_text(
            self.x, self.y - self.size - 10,
            text=self.name, fill="white"
        )


class Enemy:
    def __init__(self, name, hp, atk, spd, x, y, role="melee", skills=None):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.spd = spd
        self.base_spd = self.spd
        self.x = x
        self.y = y
        self.size = 16
        self.state = 'wander'
        self.wander_target = (x, y)
        self.last_move = time.time()
        self.attack_range = 50
        self.role = role 
        self.skills = skills or []  # list of dicts: {'skill':func,'cooldown':num,'last_used':time}
        self.attack_cooldown = 1.0
        self.last_attack = 0
        self.room_row = y // ROOM_H
        self.room_col = x // ROOM_W
        self.item = None  # weapon/item
        self.assign_weapon()
    def assign_weapon(self):
        """Assign appropriate weapon based on enemy name"""
        if self.name == "Swordman":
            self.item = Item(self.x, self.y, 'sword', 'silver', 20, owner=self)
        elif self.name == "Spearman":
            self.item = Item(self.x, self.y, 'spear', 'brown', 25, owner=self)
        elif self.name == "Archer":
            self.item = Item(self.x, self.y, 'bow', 'brown', 18, owner=self)
        elif self.name == "Dark Mage":
            self.item = Item(self.x, self.y, 'staff', 'purple', 22, owner=self)
            self.item.gem_color = 'purple'
        elif self.name == "Flame Elemental":
            self.item = Item(self.x, self.y, 'staff', 'orange', 22, owner=self)
            self.item.gem_color = 'orange'
        elif self.name == "Summoner":
            self.item = Item(self.x, self.y, 'staff', 'pink', 22, owner=self)
            self.item.gem_color = 'pink'
        elif self.name == "Healer":
            self.item = Item(self.x, self.y, 'staff', 'yellow', 22, owner=self)
            self.item.gem_color = 'yellow'
        elif self.name == "Ice Golem":
            self.item = Item(self.x, self.y, 'hand', 'cyan', 20, owner=self)
        elif self.name == "Fire Imp":
            self.item = Item(self.x, self.y, 'hand', 'orange', 15, owner=self)
        elif self.name == "Venom Lurker":
            self.item = Item(self.x, self.y, 'hand', 'lime', 18, owner=self)
        elif self.name == "Troll":
            self.item = Item(self.x, self.y, 'hand', 'darkgray', 25, owner=self)
    def dodge_projectiles(self, game):
        for proj in game.projectiles:
            if proj.owner == "player":
                d = distance((self.x, self.y), (proj.x, proj.y))
                if d < 60:
                    ang = proj.angle
                    dodge_ang = ang + random.choice([-math.pi/2, math.pi/2])
                    self.x += math.cos(dodge_ang) * self.spd * 10
                    self.y += math.sin(dodge_ang) * self.spd * 10


    # Add this method to your Enemy class
    def scale_with_player(self, player_level):
        scale_factor = 1 + player_level * 0.5
        self.max_hp = int(self.max_hp * scale_factor)
        self.hp = min(self.hp, self.max_hp)
        self.atk = int(self.atk * scale_factor)
        self.spd = self.spd * (1 + player_level * 0.02)
    def update(self, game):
        now = time.time()
        player = game.player
        # Only reset speed if NOT currently frozen — update_entities sets spd=0 for frozen enemies
        if not (hasattr(self, '_frozen_until') and self._frozen_until > now):
            self.spd = self.base_spd

        # ── SMOKE state: enemy wanders randomly and cannot attack ──────────────
        if getattr(self, '_smoke_until', 0) > now:
            if not hasattr(self, '_smoke_wander_target') or \
               distance((self.x, self.y), self._smoke_wander_target) < 20:
                angle = random.uniform(0, 2 * math.pi)
                dist  = random.uniform(40, 120)
                self._smoke_wander_target = (
                    clamp(self.x + math.cos(angle) * dist, self.size, WINDOW_W - self.size),
                    clamp(self.y + math.sin(angle) * dist, self.size, WINDOW_H - self.size),
                )
            dx = self._smoke_wander_target[0] - self.x
            dy = self._smoke_wander_target[1] - self.y
            d  = math.hypot(dx, dy)
            if d > 1:
                self.x += (dx / d) * self.spd * 0.6
                self.y += (dy / d) * self.spd * 0.6
            if self.item:
                self.item.update(self.x, self.y, player.x, player.y)
            return   # skip all normal AI while smoked
        # (old per-frame frost slow loop removed — freezing is handled once by update_entities)
        if self.item:
            self.item.update(self.x, self.y, player.x, player.y)
        # --- compute once per frame ---
        d = distance((self.x, self.y), (player.x, player.y))
        for sk in self.skills:
            if sk["skill"].__name__ == "dash_attack":
                if d > 100 and time.time() - sk["last_used"] >= sk["cooldown"]:
                    sk["skill"](self, game)
                    sk["last_used"] = time.time()
                    return  # skip normal movement this frame
        # --- smarter dodge: only occasionally, and weaker ---
        if hasattr(self, "_last_dodge_time"):
            can_dodge = (now - self._last_dodge_time) > 0.2
        else:
            self._last_dodge_time = 0
            can_dodge = True

        if can_dodge:
            for proj in game.projectiles:
                if proj.owner == "player":
                    pd = distance((self.x, self.y), (proj.x, proj.y))
                    if pd < 100:
                        dodge_ang = proj.angle + random.choice([-math.pi/2, math.pi/2])
                        self.x += math.cos(dodge_ang) * (self.spd * 3)
                        self.y += math.sin(dodge_ang) * (self.spd * 3)
                        self._last_dodge_time = now
                        break
        # --- if player is dead, return to center of room ---

        # --- role-based movement ---
        if self.role == "melee":
            if self.hp <= self.max_hp / 2:
                # retreat
                ang = math.atan2(self.y - player.y, self.x - player.x)
                self.x += math.cos(ang) * (self.spd)
                self.y += math.sin(ang) * (self.spd)
                for sk in self.skills:
                    if sk.get("name") == "Self Heal" and now - sk.get("last_used", 0) >= sk.get("cooldown", 1):
                        sk["skill"](self, game)
                        sk["last_used"] = now
                        break
            else:
                # chase until close
                if d > self.attack_range:
                    ang = math.atan2(player.y - self.y, player.x - self.x)
                    self.x += math.cos(ang) * self.spd
                    self.y += math.sin(ang) * self.spd

            # attack if in range
            if d <= self.attack_range:
                usable = [
                    sk for sk in self.skills
                    if "melee" in sk.get("tags", [])   # only melee skills
                    and now - sk.get("last_used", 0) >= sk.get("cooldown", 1)
                ]
                if usable:
                    chosen = random.choice(usable)
                    chosen["skill"](self, game)
                    chosen["last_used"] = now

        elif self.role in ("ranged", "magic", "support"):
            desired_range = self.attack_range + 750  # preferred spacing
            if d < desired_range:  # too close â†’ back away
                ang = math.atan2(self.y - player.y, self.x - player.x)
                self.x += math.cos(ang) * self.spd
                self.y += math.sin(ang) * self.spd
            elif d > desired_range:  # too far â†’ move closer
                ang = math.atan2(player.y - self.y, player.x - self.x)
                self.x += math.cos(ang) * self.spd
                self.y += math.sin(ang) * self.spd

            # attack with skills
            usable = [sk for sk in self.skills if now - sk.get("last_used", 0) >= sk.get("cooldown", 1)]
            if usable:
                chosen = random.choice(usable)
                chosen["skill"](self, game)
                chosen["last_used"] = now

            # shield if half health
            if self.hp <= self.max_hp / 2:
                for sk in self.skills:
                    if sk.get("name") == "Shield" and now - sk.get("last_used", 0) >= sk.get("cooldown", 1):
                        sk["skill"](self, game)
                        sk["last_used"] = now
                        break
        else:
            # FALLBACK: If role doesn't match anything, just chase the player
            if d > 50:
                ang = math.atan2(player.y - self.y, player.x - self.x)
                self.x += math.cos(ang) * self.spd
                self.y += math.sin(ang) * self.spd
        
        # --- passive contact damage (always active, own short cooldown) ---
        # This ensures the player CAN die even while using skills, since
        # skill-based melee damage may be on cooldown.
        contact_range = self.size + game.player.size + 2
        if d <= contact_range:
            last_contact = getattr(self, '_last_contact_dmg', 0)
            if now - last_contact >= 0.5:   # hits every 0.5 s when touching
                game.damage_player(max(1, self.atk // 2))
                self._last_contact_dmg = now

        # --- clamp to WINDOW boundaries (not room boundaries) ---
        # Clamp enemy inside its current room boundaries
        # --- Clamp enemy inside current room boundaries ---
        self.x = clamp(self.x, self.size, WINDOW_W - self.size)
        self.y = clamp(self.y, self.size, WINDOW_H - self.size)
        wall_thickness = 20
        opening_size = 150
        enemy_size = self.size

        # Top wall
        if self.y - enemy_size < wall_thickness:
            if self.room_row == 0:
                self.y = wall_thickness + enemy_size
            else:
                opening_x_start = WINDOW_W // 2 - opening_size // 2
                opening_x_end = opening_x_start + opening_size
                if self.x < opening_x_start or self.x > opening_x_end:
                    self.y = wall_thickness + enemy_size

        # Bottom wall
        if self.y + enemy_size > WINDOW_H - wall_thickness:
            if self.room_row == ROOM_ROWS - 1:
                self.y = WINDOW_H - wall_thickness - enemy_size
            else:
                opening_x_start = WINDOW_W // 2 - opening_size // 2
                opening_x_end = opening_x_start + opening_size
                if self.x < opening_x_start or self.x > opening_x_end:
                    self.y = WINDOW_H - wall_thickness - enemy_size

        # Left wall
        if self.x - enemy_size < wall_thickness:
            if self.room_col == 0:
                self.x = wall_thickness + enemy_size
            else:
                opening_y_start = WINDOW_H // 2 - opening_size // 2
                opening_y_end = opening_y_start + opening_size
                if self.y < opening_y_start or self.y > opening_y_end:
                    self.x = wall_thickness + enemy_size

        # Right wall
        if self.x + enemy_size > WINDOW_W - wall_thickness:
            if self.room_col == ROOM_COLS - 1:
                self.x = WINDOW_W - wall_thickness - enemy_size
            else:
                opening_y_start = WINDOW_H // 2 - opening_size // 2
                opening_y_end = opening_y_start + opening_size
                if self.y < opening_y_start or self.y > opening_y_end:
                    self.x = WINDOW_W - wall_thickness - enemy_size

                # Update room position tracking
                self.room_row = int(self.y // ROOM_H)
                self.room_col = int(self.x // ROOM_W)




    def gain_xp(self, amount, game=None):
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.stat_points += 2
            self.skill_points += 1
            self.xp_to_next = int(self.xp_to_next * 1.3)
            leveled = True
            growth = CLASS_STAT_GROWTH.get(self.class_name, {})
            for stat, value in growth.items():
                setattr(self, stat, getattr(self, stat) + value)

        self.update_stats()

        # Scale current enemies if game instance is passed
        if leveled and game:
            for e in game.room.enemies:
                if isinstance(e, Enemy):
                    e.scale_with_player(self.level)

        return leveled

def shield(caster, game):
    # Cooldown check
    if time.time() - getattr(caster, "last_shield", 0) < 5:  # 5s cooldown
        return

    caster.last_shield = time.time()

    # Shield parameters
    shield_radius = 40 + caster.atk
    duration = 3.0
    tick_ms = 100
    shield_id = id(caster)  # Unique ID for this shield

    def shield_tick():
        # Stop if caster is dead or not in room anymore
        if caster not in game.room.enemies:
            return
        
        # Expire if duration passed
        if time.time() >= caster._shield_end:
            caster._shield_active = False
            return

        # Spawn shield particle
        shield_particle = Particle(
            caster.x, caster.y,
            shield_radius,
            "blue",
            life=0.2,
            rtype="shield",
            outline=True
        )
        game.particles.append(shield_particle)

        # Block projectiles
        for proj in list(game.projectiles):
            d = distance((caster.x, caster.y), (proj.x, proj.y))
            if d <= shield_radius + getattr(proj, "radius", 5):
                if proj in game.projectiles:
                    game.projectiles.remove(proj)

        # Reschedule tick
        game.after(tick_ms, shield_tick)

    # Activate shield
    if not getattr(caster, "_shield_active", False):
        caster._shield_active = True
        caster._shield_end = time.time() + duration
        shield_tick()

# Enemy skills
def claw_slash(enemy, game):
    # Deals melee damage in a small radius with swipe effect
    arc_radius = 40
    num_particles = 8
    angle_center = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)
    arc_width = math.pi / 2
    for i in range(num_particles):
        angle = angle_center - arc_width/2 + (i / (num_particles-1)) * arc_width
        x = enemy.x + math.cos(angle) * arc_radius * random.uniform(0.8, 1.2)
        y = enemy.y + math.sin(angle) * arc_radius * random.uniform(0.8, 1.2)
        game.spawn_particle(x, y, random.uniform(5,10), 'green')
    # Deal damage to player if in arc
    if distance((enemy.x, enemy.y), (game.player.x, game.player.y)) <= arc_radius:
        game.damage_player(enemy.atk * 1.5)
def fire_slash(enemy, game):
    # Deals melee damage in a small radius with swipe effect
    arc_radius = 50
    num_particles = 50
    angle_center = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)
    arc_width = math.pi / 2
    for i in range(num_particles):
        angle = angle_center - arc_width/2 + (i / (num_particles-1)) * arc_width
        x = enemy.x + math.cos(angle) * arc_radius * random.uniform(0.8, 1.2)
        y = enemy.y + math.sin(angle) * arc_radius * random.uniform(0.8, 1.2)
        game.spawn_particle(x, y, random.uniform(5,10), 'orange', owner="enemy", rtype="flame")
    # Deal damage to player if in arc
    if distance((enemy.x, enemy.y), (game.player.x, game.player.y)) <= arc_radius:
        game.damage_player(enemy.atk * 1.5)

def fire_spit(enemy, game):
    ang = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)
    # Trail particles at spawn point
    for _ in range(5):
        px = enemy.x + random.uniform(-5, 5)
        py = enemy.y + random.uniform(-5, 5)
        fp = Particle(px, py, random.uniform(3,6), random.choice(['orange','red','yellow']),
                      life=0.4, rtype='fire_puff', owner=None)
        game.particles.append(fp)
    game.spawn_projectile(enemy.x, enemy.y, ang, 6, 2, 15, 'orange', enemy.atk * 2,
                          'enemy', ptype='fire_proj', stype='fire_proj')


def poison_cloud(enemy, game):
    radius = 50 + enemy.atk
    num_particles = 15
    for _ in range(num_particles):
        x = enemy.x + random.uniform(-radius, radius)
        y = enemy.y + random.uniform(-radius, radius)
        game.spawn_particle(x, y, random.uniform(4,8), 'green')
    if distance((enemy.x, enemy.y), (game.player.x, game.player.y)) <= radius:
        game.damage_player(enemy.atk * 2)

def dark_bolt(enemy, game):
    # Ranged rock projectile
    ang = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)
    game.spawn_projectile(enemy.x, enemy.y, ang, 20, 2.5, 10, 'purple', enemy.atk * 2, 'enemy', stype="bolt1")

def life_bolt(enemy, game):
    # If no enemies, do nothing
    if not game.room.enemies:
        return

    # Find enemy that lost the MOST health
    target = max(
        game.room.enemies,
        key=lambda e: (e.max_hp - e.hp)
    )

    # Compute angle toward that enemy
    ang = math.atan2(target.y - enemy.y, target.x - enemy.x)

    # Spawn projectile owned by enemy
    # damage value will be used as "healing"
    game.spawn_projectile(
        enemy.x, enemy.y,
        ang,                # angle toward the target
        20,                 # speed
        2.5,                # life
        10,                 # radius
        'yellow',           # color
        enemy.atk * 3,      # heal amount
        'enemy_lifebolt'    # special owner type
    )

def ice_blast(enemy, game):
    radius = 100
    num_particles = 30  # how many frost particles to spawn

    # spawn frosty particles randomly inside the area
    for i in range(num_particles):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, radius)  # random distance from center
        x = enemy.x + math.cos(angle) * dist
        y = enemy.y + math.sin(angle) * dist
        game.spawn_particle(x, y, random.uniform(4, 8), 'cyan', 0.8, rtype="frost", owner="enemy")

    # check if player is inside aura
    if distance((enemy.x, enemy.y), (game.player.x, game.player.y)) <= radius:
        # deal damage
        game.damage_player(enemy.atk)
        # Apply Frozen debuff directly — particles alone may not overlap the player
        game.player._frozen_until = time.time() + 3.0
        game.player._freeze_ice_spawned = False



def summon_minion(enemy, game):
    minionR = 0
    # Spawns a weak minion nearby
    x = enemy.x + random.randint(-30, 30)
    y = enemy.y + random.randint(-30, 30)
    minion = Enemy("Minion", 30, 4, 1.2, x, y)

    game.room.enemies.append(minion)

def dash_strike(enemy, game):
    """Enhanced dash skill: faster, more damage, and adds visual effect."""
    ang = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)
    
    # Dash movement: double speed
    dash_distance = enemy.spd * 20  # faster than normal
    enemy.x += math.cos(ang) * dash_distance
    enemy.y += math.sin(ang) * dash_distance

    # Visual effect: spawn trailing particles
    for _ in range(8):
        offset_x = enemy.x + random.uniform(-5, 5)
        offset_y = enemy.y + random.uniform(-5, 5)
        size = random.uniform(10, 10)
        game.spawn_particle(offset_x, offset_y, size, 'green')  # can be customized

    # Attack damage
    if distance((enemy.x, enemy.y), (game.player.x, game.player.y)) <= 25:
        damage = enemy.atk * 2.5  # stronger than before
        game.damage_player(damage)

def rock_throw(enemy, game):
    # Ranged rock projectile
    ang = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)
    game.spawn_projectile(enemy.x, enemy.y, ang, 10, 10, 30, 'brown', enemy.atk * 1.5, 'enemy')

def self_heal(enemy, game):
    """Heals the enemy with a visual particle effect."""
    heal_amount = enemy.atk * 2
    enemy.hp = min(enemy.max_hp, enemy.hp + heal_amount)

    # Spawn a burst of green particles around the enemy
    num_particles = 4
    radius = 0.5
    for _ in range(num_particles):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, radius)
        x = enemy.x + math.cos(angle) * dist
        y = enemy.y + math.sin(angle) * dist
        size = random.uniform(5, 10)
        game.spawn_particle(x, y, 0.2, 'green',  rtype="diamond")
# Enemy version of Strike
def enemy_strike(enemy, game):
    if not game.player: 
        return
    # Same mana check replaced with cooldown logic (enemies donâ€™t use mana)
    arc_radius = 30
    arc_width = math.pi / 3
    px, py = enemy.x, enemy.y

    # Angle toward player
    angle_center = math.atan2(game.player.y - py, game.player.x - px)

    # Spawn blade particle
    offset = arc_radius // 1
    spawn_x = px + math.cos(angle_center) * offset
    spawn_y = py + math.sin(angle_center) * offset
    blade_particle = Particle(spawn_x, spawn_y, 22, 'gray', life=0.35, rtype='eblade1_fwd', angle=angle_center, damage=enemy.atk*1.5)
    game.particles.append(blade_particle)

    # Damage player if inside arc
    dx, dy = game.player.x - px, game.player.y - py
    dist = math.hypot(dx, dy)
    if dist <= arc_radius:
        angle_to_player = math.atan2(dy, dx)
        diff = (angle_to_player - angle_center + math.pi*2) % (math.pi*2)
        if diff < arc_width/2 or diff > math.pi*2 - arc_width/2:
            game.damage_player(enemy.atk)
def dash_attack(enemy, game):
    # cooldown check
    if time.time() - enemy.last_attack < enemy.attack_cooldown:
        return

    # dash parameters
    dash_distance = 80
    dash_speed = 12
    target = game.player
    ang = math.atan2(target.y - enemy.y, target.x - enemy.x)

    # move enemy forward quickly
    enemy.x += math.cos(ang) * dash_distance
    enemy.y += math.sin(ang) * dash_distance

    # optional: damage if close enough after dash
    if distance((enemy.x, enemy.y), (target.x, target.y)) <= enemy.attack_range:
        game.damage_enemy(target, enemy.atk * 2)  # stronger hit

    enemy.last_attack = time.time()

# Enemy version of Dark Slash
def enemy_dark_slash(enemy, game):
    if not game.player:
        return

    arc_radius = 40
    arc_width = math.pi / 3

    px, py = enemy.x, enemy.y
    angle_center = math.atan2(game.player.y - py, game.player.x - px)

    offset = arc_radius // 2
    origin_x = px + math.cos(angle_center) * offset
    origin_y = py + math.sin(angle_center) * offset

    # Visual blade only (no per-frame damage)
    blade_particle = Particle(
        origin_x, origin_y,
        arc_radius, 'grey',
        life=0.4,
        rtype='eblade',
        angle=angle_center - 0.6,
        damage=0
    )
    game.particles.append(blade_particle)

    # Precise sector hit test (radius + player size, angle wedge)
    dx = game.player.x - origin_x
    dy = game.player.y - origin_y
    dist = math.hypot(dx, dy)
    if dist <= arc_radius + game.player.size:
        angle_to_player = math.atan2(dy, dx)
        diff = (angle_to_player - angle_center + 2 * math.pi) % (2 * math.pi)
        if diff <= arc_width / 2 or diff >= 2 * math.pi - arc_width / 2:
            game.damage_player(enemy.atk * 3)

# Enemy version of Arrow Shot
def enemy_arrow_shot(enemy, game):
    if not game.player:
        return
    ang = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)
    game.spawn_projectile(
        enemy.x, enemy.y,
        ang,
        6, 3, 8,
        'brown',
        enemy.atk * 2,
        owner='enemy',
        stype='arrow'
    )

def create_enemy_types_by_dungeon():
    return {
        1: [  # Dungeon 1: Forest
            lambda x, y: Enemy(
                "Swordman", 60, 5, 4, x, y, role="melee",
                skills=[
                    {"skill": enemy_dark_slash, "name": "Arc Slash", "tags": ["melee"], "cooldown": 0.5, "last_used": 0},
                    {"skill": self_heal, "name": "Self Heal", "tags": ["magic"], "cooldown": 1.5, "last_used": 0}
                ]
            ),
            lambda x, y: Enemy(
                "Spearman", 50, 5, 3, x, y, role="melee",
                skills=[
                    {"skill": enemy_strike, "name": "Strike", "tags": ["melee"], "cooldown": 0.5, "last_used": 0},
                    {"skill": dash_attack, "name": "Dash", "tags": ["support"], "cooldown": 2.0, "last_used": 0},
                    {"skill": self_heal, "name": "Self Heal", "tags": ["magic"], "cooldown": 1.5, "last_used": 0}
                    
                ]
            ),
            lambda x, y: Enemy(
                "Archer", 35, 6, 2.0, x, y, role="ranged",  # Changed from 3.0 to 2.0 for better ranged behavior
                skills=[
                    {"skill": enemy_arrow_shot, "name": "Arrow Shot", "tags": ["ranged"], "cooldown": 1.0, "last_used": 0}
                ]
            ),
        ],
        2: [  # Dungeon 2: Volcano
            lambda x, y: Enemy(
                "Fire Imp", 60, 8, 4.0, x, y, role="melee",
                skills=[
                    {"skill": fire_slash, "name": "Fire Slash", "tags": ["melee"], "cooldown": 1.0, "last_used": 0},
                    {"skill": self_heal, "name": "Self Heal", "tags": ["magic"], "cooldown": 1.5, "last_used": 0}
                ]
            ),
            lambda x, y: Enemy(
                "Flame Elemental", 50, 8, 1.5, x, y, role="magic",
                skills=[
                    {"skill": fire_spit, "name": "Fire Spit", "tags": ["magic"], "cooldown": 2.0, "last_used": 0}
                ]
            ),
            lambda x, y: Enemy(
                "Troll", 100, 12, 0.8, x, y, role="magic",
                skills=[
                    {"skill": rock_throw, "name": "Rock Throw", "tags": ["melee"], "cooldown": 5.0, "last_used": 0},
                    {"skill": self_heal, "name": "Self Heal", "tags": ["support"], "cooldown": 2.0, "last_used": 0}
                ]
            ),
        ],

        3: [  # Dungeon 3: Ice Cavern
            lambda x, y: Enemy(
                "Ice Golem", 100, 10, 0.6, x, y, role="melee",
                skills=[
                    {"skill": ice_blast, "name": "Ice Blast", "tags": ["melee"], "cooldown": 0.2, "last_used": 0},
                    {"skill": self_heal, "name": "Self Heal", "tags": ["magic"], "cooldown": 1.5, "last_used": 0}
                ]
            ),
            lambda x, y: Enemy(
                "Dark Mage", 40, 7, 1.2, x, y, role="magic",
                skills=[
                    {"skill": dark_bolt, "name": "Dark Bolt", "tags": ["magic"], "cooldown": 2.0, "last_used": 0},
                    {"skill": shield, "name": "Shield", "tags": ["magic"], "cooldown": 3.0, "last_used": 0}
                    
                ]
            ),
        ],

        4: [  # Dungeon 4: Shadow Realm
            lambda x, y: Enemy(
                "Summoner", 50, 5, 1.0, x, y, role="magic",
                skills=[
                    {"skill": dark_bolt, "name": "Dark Bolt", "tags": ["magic"], "cooldown": 0.9, "last_used": 0},
                    {"skill": summon_minion, "name": "Summon Minion", "tags": ["support"], "cooldown": 9.0, "last_used": 0}
                ]
            ),
            lambda x, y: Enemy(
                "Healer", 50, 8, 1.5, x, y, role="support",
                skills=[
                    {"skill": life_bolt, "name": "Life Bolt", "tags": ["support"], "cooldown": 0.7, "last_used": 0},
                    {"skill": self_heal, "name": "Self Heal", "tags": ["support"], "cooldown": 1, "last_used": 0}
                ]
            ),
            lambda x, y: Enemy(
                "Venom Lurker", 30, 10, 4.0, x, y, role="melee",
                skills=[
                    {"skill": poison_cloud, "name": "Poison Cloud", "tags": ["melee"], "cooldown": 0.3, "last_used": 0},
                    {"skill": dash_attack, "name": "Dash Attack", "tags": ["support"], "cooldown": 2.0, "last_used": 0},
                    {"skill": self_heal, "name": "Self Heal", "tags": ["magic"], "cooldown": 1.5, "last_used": 0}
                ]
            ),
        ],
    }


def spawn_enemies_for_dungeon(room, dungeon_id, player_level, count=6):
    enemy_pools = create_enemy_types_by_dungeon()
    pool = enemy_pools.get(dungeon_id, [])
    for _ in range(count):
        if not pool:
            break
        et = random.choice(pool)
        x = random.randint(50, WINDOW_W - 50)
        y = random.randint(50, WINDOW_H - 50)
        enemy = et(x, y)

        # Scale stats with player level
        scale_factor = 1 + player_level * 0.2
        enemy.max_hp = int(enemy.max_hp * scale_factor)
        enemy.hp = enemy.max_hp
        enemy.atk = int(enemy.atk * scale_factor)
        enemy.spd *= (1 + player_level * 0.02)

        room.enemies.append(enemy)



class Boss(Enemy):
    def __init__(self, name, x, y, boss_type='Generic', max_hp=500, atk=15, speed=1.2):
        super().__init__(name, max_hp, atk, speed, x, y)
        self.boss_type = boss_type
        self.size = 30
        self.color = 'orange'
        self.skills = []
        self.last_used_skill_time = {}
        self.init_by_type()

    def scale_with_player(self, player_level):
        scale_factor = 1 + player_level * 0.5  # Bosses scale slightly faster
        self.max_hp = int(self.max_hp * scale_factor)
        self.hp = min(self.hp, self.max_hp)
        self.atk = int(self.atk * scale_factor)
        self.spd = self.spd * (1 + player_level * 0.03)
    def init_by_type(self):
        """Assign stats and skills based on boss type"""
        if self.boss_type == 'FireLord':
            self.max_hp += 600
            self.hp = self.max_hp
            self.atk += 40
            self.size = 20
            self.fire_rate = 1.5
            self.skills = [
                {'skill': self.fireball_attack, 'cooldown': 2},
                {'skill': self.flame_wave, 'cooldown': 4},
                {'skill': self.heal, 'cooldown': 3}
            ]
        elif self.boss_type == 'IceGiant':
            self.max_hp += 800
            self.hp = self.max_hp
            self.atk += 60
            self.size = 25
            self.skills = [
                {'skill': self.ice_shard_attack, 'cooldown': 2},
                {'skill': self.freeze_aura, 'cooldown': 4},
                {'skill': self.heal, 'cooldown': 3}
            ]
        elif self.boss_type == 'ShadowWraith':
            self.max_hp += 500
            self.hp = self.max_hp
            self.atk += 60
            self.size = 10
            self.spd = 9
            self.skills = [
                {'skill': self.direball, 'cooldown': 2},
                {'skill': self.arcane_storm, 'cooldown': 4},
                {'skill': self.heal, 'cooldown': 3}
            ]
        elif self.boss_type == 'EarthTitan':
            self.max_hp += 900
            self.hp = self.max_hp
            self.atk += 80
            self.size = 30
            self.skills = [
                {'skill': self.rock_throw, 'cooldown': 3},
                {'skill': self.boss_shockwave, 'cooldown': 2},
                {'skill': self.heal, 'cooldown': 3}
            ]
    # ---------- Example Skills ----------
    def fireball_attack(self, game):
        """Shoots a spread of fireballs — rendered as fire particles, damage on impact"""
        player = game.player
        ang = math.atan2(player.y - self.y, player.x - self.x)
        for delta in [-0.2, 0, 0.2]:
            game.spawn_projectile(self.x, self.y, ang + delta, 6, 3, 10, 'orange',
                                  self.atk*10, 'enemy', ptype='fire_proj', stype='fire_proj')
    def direball(self, game):
        """Shoots a spread of fireballs"""
        player = game.player
        ang = math.atan2(player.y - self.y, player.x - self.x)
        for delta in [-0.2, 0, 0.2]:
            game.spawn_projectile(self.x, self.y, ang + delta, 6, 3, 20, 'purple', self.atk*5, 'enemy', stype="slash")
    def summon_minions(self, game):
        for _ in range(2):
            x = self.x + random.randint(-40, 40)
            y = self.y + random.randint(-40, 40)
            minion = Enemy("FlameElemental", 30, 5, 1.5, x, y)
            game.room.enemies.append(minion)
    def rock_throw(enemy, game):
        # Ranged rock projectile
        ang = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)
        game.spawn_projectile(enemy.x, enemy.y, ang, 10, 10, 40, 'brown', enemy.atk * 1.5, 'enemy')
    def boss_shockwave(boss, game):
        # Mana or cooldown check if needed
        # Shockwave parameters
        shockwave_radius = 30       # starting radius
        max_radius = 150            # how far the wave expands
        expansion_speed = 10        # pixels per frame
        damage = boss.atk * 2       # stronger than playerâ€™s version

        # Create a particle that represents the expanding ring
        shockwave = Particle(
            boss.x, boss.y,
            size=shockwave_radius,
            color='red',
            life=0.6,
            rtype='shockwave',
            outline=True
        )
        shockwave.expansion_speed = expansion_speed
        shockwave.max_radius = max_radius
        shockwave.damage = damage
        game.particles.append(shockwave)

        # Apply immediate damage + knockback to enemies in range (player + summons)
        targets = [game.player] + list(game.summons)
        for t in targets:
            d = distance((boss.x, boss.y), (t.x, t.y))
            if d < max_radius:
                game.damage_enemy(t, damage)  # or damage_player if you separate logic
                ang = math.atan2(t.y - boss.y, t.x - boss.x)
                push_strength = (max_radius - d) * 0.4
                t.x += math.cos(ang) * push_strength
                t.y += math.sin(ang) * push_strength

    def flame_wave(self, game):
        """AoE flame around boss"""
        for e in game.room.enemies:
            if e != self: continue
        for _ in range(50):
            x = self.x + random.uniform(-120,120)
            y = self.y + random.uniform(-120,120)
            game.spawn_particle(x, y, random.uniform(5,10), 'red',owner="enemy", rtype="flame")
        if distance((self.x,self.y),(game.player.x,game.player.y))<120:
            game.damage_player(self.atk*5)
    
    def ice_shard_attack(self, game):
        """Shoots shards in all directions"""
        num_shards = 8
        for i in range(num_shards):
            angle = i/num_shards*2*math.pi
            game.spawn_projectile(self.x, self.y, angle, 5, 2, 8, 'cyan', self.atk*5, 'enemy')

    def freeze_aura(self, game):
        """Freezes player if within range"""
        for _ in range(20):
            x = self.x + random.uniform(-120, 120)
            y = self.y + random.uniform(-120, 120)
            game.spawn_particle(x, y, random.uniform(5, 10), 'cyan', rtype="frost", owner="enemy")
        # Directly freeze player if within the particle spawn radius
        if distance((self.x, self.y), (game.player.x, game.player.y)) < 140:
            game.player._frozen_until = time.time() + 10.0
            game.player._freeze_ice_spawned = False
    def heal(enemy, game):
        """Heals the enemy with a visual particle effect."""
        heal_amount = enemy.atk * 20
        enemy.hp = min(enemy.max_hp, enemy.hp + heal_amount)

        # Spawn a burst of green particles around the enemy
        num_particles = 12
        radius = enemy.size + 10
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0, radius)
            x = enemy.x + math.cos(angle) * dist
            y = enemy.y + math.sin(angle) * dist
            size = random.uniform(5, 10)
            game.spawn_particle(x, y, size, 'yellow')

    def arcane_storm(self, game):
        player = game.player
        angle_center = math.atan2(player.y - self.y, player.x - self.x)
        num_proj = 10
        arc_width = math.pi / 2
        for i in range(num_proj):
            angle = angle_center - arc_width/2 + (i / (num_proj-1)) * arc_width
            game.spawn_projectile(self.x, self.y, angle, 5, 3, 8, 'purple', self.atk*10, 'enemy')

    def update(self, dt, game):
        """Move and use skills"""
        # Move towards player
        player = game.player
        ang = math.atan2(player.y - self.y, player.x - self.x)
        self.x += math.cos(ang) * self.spd
        self.y += math.sin(ang) * self.spd

        now = time.time()
        # Use skills
        for sk in self.skills:
            last_used = self.last_used_skill_time.get(sk['skill'], 0)
            if now - last_used >= sk['cooldown']:
                sk['skill'](game)
                self.last_used_skill_time[sk['skill']] = now
        self.x = clamp(self.x, self.size, WINDOW_W - self.size)
        self.y = clamp(self.y, self.size, WINDOW_H - self.size)
        
def spawn_boss_for_room(room, dungeon_id):
    boss_x, boss_y = WINDOW_W//2, WINDOW_H//2
    boss_types = {
        1: 'EarthTitan',
        2: 'FireLord',
        3: 'IceGiant',
        4: 'ShadowWraith'
    }
    boss_name = f"Dungeon {dungeon_id} Boss"
    boss_type = boss_types.get(dungeon_id, 'Generic')
    boss = Boss(boss_name, boss_x, boss_y, boss_type)
    room.enemies.append(boss)

class Projectile:
    def __init__(self,x,y,angle,speed,life,radius,color,damage,owner='player', ptype='normal', stype='basic'):
        self.x=x; self.y=y; self.angle=angle; self.speed=speed;
        self.life=life; self.radius=radius; self.color=color; self.damage=damage; self.owner=owner
        self.ptype = ptype; self.stype = stype;self.spawn_time = time.time();
        self.stopped = False   # NEW FLAG
    def update(self,dt,game):
        self.x += math.cos(self.angle)*self.speed
        self.y += math.sin(self.angle)*self.speed
        self.life -= dt
        # ── Smoke bomb: explode on wall hit or life end ──────────────────────
        if self.ptype == 'smoke_bomb':
            hit_wall = (self.x<0 or self.x>WINDOW_W or self.y<0 or self.y>WINDOW_H)
            if self.life <= 0 or hit_wall:
                self._explode_smoke(game)
                self.life = 0
                return
        if self.x<0 or self.x>WINDOW_W or self.y<0 or self.y>WINDOW_H: self.life=0; return
        if not self.stopped:
            self.x += math.cos(self.angle) * self.speed
            self.y += math.sin(self.angle) * self.speed
        # lifetime check
        if time.time() - self.spawn_time > self.life:
            self.alive = False

        if self.owner == 'summon' or self.owner == 'player':
            for e in list(game.room.enemies):
                if distance((self.x,self.y),(e.x,e.y))<=self.radius+e.size:
                    # ── Smoke bomb: explode on first enemy contact ─────────────
                    if self.ptype == 'smoke_bomb':
                        self._explode_smoke(game)
                        self.life = 0
                        return
                    # --- PIERCE: spear_throw damages each enemy only once, keeps flying ---
                    if getattr(self, 'pierce', False):
                        eid = id(e)
                        if eid not in getattr(self, 'hit_ids', set()):
                            self.hit_ids.add(eid)
                            game.damage_enemy(e, self.damage)
                            # Spark effect on pierce
                            for _ in range(8):
                                _ba = random.uniform(0, 2*math.pi)
                                _bp = Particle(self.x + math.cos(_ba)*6,
                                               self.y + math.sin(_ba)*6,
                                               random.uniform(2,5), '#aaaaaa',
                                               life=random.uniform(0.1, 0.25),
                                               rtype='magic_burst', owner=None)
                                game.particles.append(_bp)
                        continue  # spear keeps flying
                    if self.stype == "howl":
                        angle_deg = math.degrees(self.angle) % 360
                        arc_extent = 60
                        thickness = 6

                        for i in range(3):
                            radius = self.radius * (i + 2)
                            self.canvas.create_arc(
                                self.x - radius, self.y - radius,
                                self.x + radius, self.y + radius,
                                start=angle_deg - arc_extent / 2,
                                extent=arc_extent,
                                style="arc",
                                outline=self.color,
                                width=thickness
                            )

                    elif self.ptype == 'fireball':
                        for e in list(game.room.enemies):
                            if distance((self.x, self.y), (e.x, e.y)) <= e.size + self.radius:
                                game.damage_enemy(e, self.damage)

                                # spawn scattered flame particles on impact
                                for _ in range(140):
                                    ang = random.uniform(0, 2 * math.pi)       # random angle
                                    r = random.uniform(0, 70)                  # random radius
                                    px = e.x + math.cos(ang) * r
                                    py = e.y + math.sin(ang) * r
                                    size = random.uniform(6, 12)
                                    flame = Particle(px, py, size, "orange", life=1, owner="player", rtype="flame")
                                    game.particles.append(flame)
                                # remove projectile after hit
                                if self in game.projectiles:
                                    game.projectiles.remove(self)
                                break
                    if self.ptype == 'icicle':
                        for e in list(game.room.enemies):
                            if distance((self.x, self.y), (e.x, e.y)) <= e.size + self.radius:
                                # direct hit damage
                                game.damage_enemy(e, self.damage)

                                # ── FREEZE the enemy directly on impact ──────
                                e.spd = 0
                                e._frozen_until = time.time() + 10.0
                                e._freeze_ice_spawned = False   # allow ice cube to appear

                                # spawn scattered frost particles on impact
                                for _ in range(30):
                                    ang = random.uniform(0, 2 * math.pi)
                                    r = random.uniform(0, 70)
                                    px = e.x + math.cos(ang) * r
                                    py = e.y + math.sin(ang) * r
                                    size = random.randint(4, 8)

                                    frost = game.spawn_particle(
                                        px, py,
                                        size,
                                        random.choice(["white", "cyan"]),
                                        life=10,
                                        rtype="frost",
                                        owner="player"
                                    )
                                    game.particles.append(frost)

                                # remove projectile after hit
                                if self in game.projectiles:
                                    game.projectiles.remove(self)
                                break


                    if self.ptype == "chain":
                        game.damage_enemy(e,self.damage);
                        others = [enemy for enemy in game.room.enemies if enemy != e]
                        if others:
                            target = min(others, key=lambda en: distance((self.x, self.y), (en.x, en.y)))
                            ang = math.atan2(target.y - self.y, target.x - self.x)
                            game.spawn_projectile(self.x, self.y, ang,
                                                  self.speed, self.life, self.radius,
                                                  "yellow", self.damage,
                                                  owner=self.owner, stype="lightning", ptype="chain1")
                    if self.ptype == "chain1":
                        game.damage_enemy(e,self.damage);
                        others = [enemy for enemy in game.room.enemies if enemy != e]
                        if others:
                            target = min(others, key=lambda en: distance((self.x, self.y), (en.x, en.y)))
                            ang = math.atan2(target.y - self.y, target.x - self.x)
                            game.spawn_projectile(self.x, self.y, ang,
                                                  self.speed, self.life, self.radius,
                                                  "yellow", self.damage,
                                                  owner=self.owner, stype="lightning", ptype="chain2")
                    if self.ptype == "chain2":
                        game.damage_enemy(e,self.damage);
                        others = [enemy for enemy in game.room.enemies if enemy != e]
                        if others:
                            target = min(others, key=lambda en: distance((self.x, self.y), (en.x, en.y)))
                            ang = math.atan2(target.y - self.y, target.x - self.x)
                            game.spawn_projectile(self.x, self.y, ang,
                                                  self.speed, self.life, self.radius,
                                                  "yellow", self.damage,
                                                  owner=self.owner, stype="lightning", ptype="chain3")
                    if self.ptype == "chain3":
                        game.damage_enemy(e,self.damage);
                        others = [enemy for enemy in game.room.enemies if enemy != e]
                        if others:
                            target = min(others, key=lambda en: distance((self.x, self.y), (en.x, en.y)))
                            ang = math.atan2(target.y - self.y, target.x - self.x)
                            game.spawn_projectile(self.x, self.y, ang,
                                                  self.speed, self.life, self.radius,
                                                  "yellow", self.damage,
                                                  owner=self.owner, stype="lightning", ptype="chain4")
                    if self.ptype == "chain4":
                        game.damage_enemy(e,self.damage);
                        others = [enemy for enemy in game.room.enemies if enemy != e]
                        if others:
                            target = min(others, key=lambda en: distance((self.x, self.y), (en.x, en.y)))
                            ang = math.atan2(target.y - self.y, target.x - self.x)
                            game.spawn_projectile(self.x, self.y, ang,
                                                  self.speed, self.life, self.radius,
                                                  "yellow", self.damage,
                                                  owner=self.owner, stype="lightning")

                    else:
                        game.damage_enemy(e,self.damage)
                        # Chi Blast — big orange/white burst, more particles
                        if self.ptype == 'chi_blast':
                            for _ in range(28):
                                _ba  = random.uniform(0, 2*math.pi)
                                _br  = random.uniform(3, self.radius*3.0)
                                _bx  = self.x + math.cos(_ba)*_br
                                _by  = self.y + math.sin(_ba)*_br
                                _bp  = Particle(_bx, _by,
                                                random.uniform(3, 8),
                                                random.choice(['cyan','white','#aaffff','#00ddff']),
                                                life=random.uniform(0.2, 0.5),
                                                rtype='magic_burst', owner=None)
                                game.particles.append(_bp)
                        # Magical burst particles on impact (not fire/ice/chi_blast)
                        elif (self.stype in {'basic', 'bolt1', 'bolt', 'slash', 'slash2', 'lightning'}
                                and self.ptype not in {'fireball', 'icicle', 'fire_proj', 'chi_blast'}):
                            _bc = self.color
                            for _ in range(12):
                                _ba  = random.uniform(0, 2*math.pi)
                                _br  = random.uniform(2, self.radius*1.8)
                                _bx  = self.x + math.cos(_ba)*_br
                                _by  = self.y + math.sin(_ba)*_br
                                _bp  = Particle(_bx, _by,
                                                random.uniform(2, 5), _bc,
                                                life=random.uniform(0.15, 0.35),
                                                rtype='magic_burst', owner=None)
                                game.particles.append(_bp)
                        self.life=0; return
        if self.owner=='enemy':
            p=game.player
            if distance((self.x,self.y),(p.x,p.y))<=self.radius+p.size:
                # Fire projectiles burst into flame particles on impact (no direct hit damage from particle)
                if self.ptype == 'fire_proj':
                    for _ in range(18):
                        ang2 = random.uniform(0, 2*math.pi)
                        r2   = random.uniform(0, self.radius*2.5)
                        fx   = self.x + math.cos(ang2)*r2
                        fy   = self.y + math.sin(ang2)*r2
                        fp   = Particle(fx, fy, random.uniform(4,10),
                                        random.choice(['orange','red','yellow','#ff6600']),
                                        life=random.uniform(0.3,0.8), rtype='fire_puff', owner=None)
                        game.particles.append(fp)
                    game.damage_player(self.damage)
                else:
                    game.damage_player(self.damage)
                self.life=0; return
        elif self.owner == 'enemy_lifebolt':
            # home target = most injured enemy
            if game.room.enemies:
                target = max(
                    game.room.enemies,
                    key=lambda e: (e.max_hp - e.hp)
                )

                # Check collision with that target
                if distance((self.x, self.y), (target.x, target.y)) <= self.radius + target.size:
                    # Heal enemy instead of damage
                    target.hp = min(target.max_hp, target.hp + self.damage)
                    return
        def spawn_aoe_fire(self, game, target_enemy):
            """Spawn a big orange AoE circle at the enemy's position."""
            aoe_radius = 50  # size of explosion
            num_particles = 20

            # Damage all enemies in the AoE
            for e in list(game.room.enemies):
                if distance((target_enemy.x, target_enemy.y), (e.x, e.y)) <= aoe_radius:
                    game.damage_enemy(e, self.damage)

            # Spawn visual particles
            for _ in range(num_particles):
                angle = random.uniform(0, 2*math.pi)
                dist = random.uniform(0, aoe_radius)
                x = target_enemy.x + math.cos(angle) * dist
                y = target_enemy.y + math.sin(angle) * dist
                size = random.uniform(5, 15)
                game.spawn_particle(x, y, size, 'orange')

    def _explode_smoke(self, game):
        """Detonate the smoke bomb: apply wander state to nearby enemies and spawn a dense smoke cloud."""
        now = time.time()
        smoke_radius = 130
        for e in game.room.enemies:
            if distance((self.x, self.y), (e.x, e.y)) <= smoke_radius:
                e._smoke_until = now + 5.0
                e._smoke_wander_target = (e.x, e.y)
        # Dense smoke cloud particles centred on impact point
        SMOKE_COL = '#707070'   # single consistent grey
        for _ in range(55):
            ang  = random.uniform(0, 2 * math.pi)
            r    = random.uniform(5, smoke_radius * 0.5)
            sx   = self.x + math.cos(ang) * r
            sy   = self.y + math.sin(ang) * r
            sp   = Particle(sx, sy,
                            random.uniform(6, 11),
                            SMOKE_COL,
                            life=random.uniform(2.0, 3.5),
                            rtype='smoke_puff', owner=None)
            sp.age = random.uniform(0, 6.28)
            game.particles.append(sp)

class Particle:
    def __init__(self, x, y, size, color, life=0.5, rtype='basic', atype=None, angle=0.0, outline=False, radius=0, owner=None, damage=0):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.life = float(life)   # ensure numeric
        self.rtype = rtype
        self.atype = atype
        self.outline = outline
        self.owner = owner# 'basic' or 'blade'
        self.angle = angle
        self.age = 0# direction (used for blade rotation)
        self.radius = radius
        self.damage = damage
        self.cx = x          # origin center
        self.cy = y
        self.expansion_speed = getattr(self, "expansion_speed", 8)
        self.max_radius = getattr(self, "max_radius", 120)
        self._affected_ids = set()      # track which enemies already got hit
        self._prev_size = size

    def update(self, dt, game):
        self.life -= dt
        if self.rtype == "blade":
            for e in list(game.room.enemies):
                if distance((self.x, self.y), (e.x, e.y)) <= self.size:
                    game.damage_enemy(e, game.player.atk * 1.5)
        if self.rtype == "blade1":
            for e in list(game.room.enemies):
                if distance((self.x, self.y), (e.x, e.y)) <= self.size:
                    game.damage_enemy(e, game.player.atk * 2.0)
        if self.rtype == "eblade":
            # Check if player is inside the particle radius
            if distance((self.x, self.y), (game.player.x, game.player.y)) <= self.size:
                game.damage_player(self.damage)
        if self.rtype in ("eblade1", "eblade1_fwd"):
            if distance((self.x, self.y), (game.player.x, game.player.y)) <= self.size:
                game.damage_player(self.damage)
        # --- add this inside Particle.update() ---
        elif self.rtype == "frost":
            radius = self.size * 1.2
        elif self.rtype == "slash_line":
            for e in list(game.room.enemies):
                if distance((self.x, self.y), (e.x, e.y)) <= self.size:
                    game.damage_enemy(e, game.player.atk * 0.05)
            
        elif self.atype == "firetrap":
            # Check each enemy in the room
            for e in list(game.room.enemies):
                if distance((self.x, self.y), (e.x, e.y)) <= self.size + e.size:
                    # Enemy triggered the trap â†’ spawn flame particles
                    for _ in range(50):
                        ang = random.uniform(0, 2 * math.pi)   # random angle
                        r = random.uniform(0, 35)              # random radius
                        px = e.x + math.cos(ang) * r
                        py = e.y + math.sin(ang) * r
                        size = random.uniform(6, 12)

                        flame = Particle(
                            px, py,
                            size,
                            "orange",
                            life=1.5,
                            owner="player",
                            rtype="flame"
                        )
                        game.particles.append(flame)

                    # Optional: deal damage to the enemy
                    game.damage_enemy(e, game.player.mag * 2)  # adjust damage value as needed

                    # Remove the trap after it triggers
                    if self in game.particles:
                        game.particles.remove(self)

                    break   # stop after first enemy triggers
        elif self.atype == "frosttrap":
            # Check each enemy in the room
            for e in list(game.room.enemies):
                if distance((self.x, self.y), (e.x, e.y)) <= self.size + e.size:
                    # Directly freeze the enemy
                    e.spd = 0
                    e._frozen_until = time.time() + 10.0
                    e._freeze_ice_spawned = False

                    # Frost visual particles
                    for _ in range(15):
                        ang = random.uniform(0, 2 * math.pi)
                        r = random.uniform(0, 35)
                        px = e.x + math.cos(ang) * r
                        py = e.y + math.sin(ang) * r
                        size = random.randint(4, 8)
                        frost = game.spawn_particle(
                            px, py, size,
                            random.choice(["white", "cyan"]),
                            life=10,
                            rtype="frost",
                            owner="player"
                        )
                        game.particles.append(frost)

                    game.damage_enemy(e, game.player.mag * 2)
                    if self in game.particles:
                        game.particles.remove(self)
                    break

        elif self.rtype == "fire_puff":
            # Cosmetic only — rise, shrink, flicker; no damage
            self.y -= 0.4
            self.size *= 0.94
            self.color = random.choice(['orange','red','yellow','#ff6600'])

        elif self.rtype == "magic_burst":
            # Small spark — just shrink, no damage
            self.size *= 0.88

        elif self.rtype == "frozen_ice":
            # No movement — locked onto entity via _follow_entity; just fade out
            pass

        elif self.rtype == "flame":
            # simple animation: rise, shrink, flicker color
            self.y -= 0.5
            self.size *= 0.97
            self.color = "orange" if random.random() < 0.55 else "yellow"

            # damage enemies inside the flame radius
            if self.owner == "player":
                # damage enemies
                for e in list(game.room.enemies):
                    if distance((self.x, self.y), (e.x, e.y)) <= self.size:
                        game.damage_enemy(e, self.damage or game.player.mag * 0.035)
            elif self.owner == "enemy":
                # damage player
                if distance((self.x, self.y), (game.player.x, game.player.y)) <= self.size:
                    game.damage_player(self.damage or 5)

        if self.rtype == "shockwave":
            # expand radius
            self._prev_size = self.size
            self.size += self.expansion_speed
            if self.owner == "player":
                # ring hit: enemy gets affected when the wave reaches them
                for e in list(game.room.enemies):
                    eid = id(e)
                    if eid in self._affected_ids:
                        continue

                    d = distance((self.cx, self.cy), (e.x, e.y))
                    # consider enemy size so the ring "touches" them
                    if self._prev_size - e.size <= d <= self.size + e.size:
                        # damage
                        if self.damage > 0:
                            game.damage_enemy(e, self.damage)

                        # knockback outward from center
                        ang = math.atan2(e.y - self.cy, e.x - self.cx)
                        # stronger knockback nearer to the origin
                        push = max(6, (self.max_radius - d) * 0.25)
                        e.x += math.cos(ang) * push
                        e.y += math.sin(ang) * push

                        self._affected_ids.add(eid)

            # end when max radius is reached
            if self.size >= self.max_radius:
                return False

        # keep your existing branch/leaf animation etc.
        # keep your existing branch/leaf animation etc.
        if self.rtype in ("branch", "leaf"):
            for e in list(game.room.enemies):
                if distance((self.x, self.y), (e.x, e.y)) <= self.size:
                    game.damage_enemy(e, game.player.wis * 2)
            px, py = game.player.x, game.player.y
            progress = self.age / self.life
            # Extend out, then retract back to player (not past)
            if progress < 0.5:
                reach = self.radius * (progress * 2)
            else:
                # Retract: go from full radius back to 0
                reach = self.radius * (2 - progress * 2)
            
            # Clamp reach to never go negative (past player)
            reach = max(0, reach)
            
            swing = math.sin(progress * math.pi - math.pi/2) * 1
            angle = self.angle + swing
            self.x = px + math.cos(angle) * reach
            self.y = py + math.sin(angle) * reach

        # Forward lunge for eblade1_fwd (enemy strike) — fixed world lunge from spawn
        if self.rtype == "eblade1_fwd":
            total_life = getattr(self, '_total_life', None)
            if total_life is None:
                self._total_life = self.life + self.age
                total_life = self._total_life
                self._base_size = self.size
                self._start_x = self.x
                self._start_y = self.y
            progress = self.age / total_life
            travel = self._base_size * 1.5 * progress
            self.x = self._start_x + math.cos(self.angle) * (self._base_size * 0.5 + travel)
            self.y = self._start_y + math.sin(self.angle) * (self._base_size * 0.5 + travel)
            self.size = self._base_size

        # Forward lunge animation for blade1_fwd (strike skill) — stays attached to player
        if self.rtype == "blade1_fwd":
            total_life = getattr(self, '_total_life', None)
            if total_life is None:
                self._total_life = self.life + self.age
                total_life = self._total_life
                self._base_size = self.size
            progress = self.age / total_life
            px, py = game.player.x, game.player.y
            # Quick lunge forward
            travel = self._base_size * 1.8 * progress
            self.x = px + math.cos(self.angle) * (self._base_size * 0.5 + travel)
            self.y = py + math.sin(self.angle) * (self._base_size * 0.5 + travel)
            # Size stays fixed (no expansion)
            self.size = self._base_size
            for e in list(game.room.enemies):
                if distance((self.x, self.y), (e.x, e.y)) <= self.size:
                    dmg = game.player.vit if game.player.class_name == 'Monk' else game.player.atk
                    game.damage_enemy(e, dmg)

        # Sweep animation for blade/blade1/eblade1: rotate left->right, stays attached to player
        if self.rtype in ("blade", "blade1", "eblade1"):
            total_life = getattr(self, '_total_life', None)
            if total_life is None:
                self._total_life = self.life + self.age  # capture on first tick
                total_life = self._total_life
            if not hasattr(self, '_base_size'):
                self._base_size = self.size
            progress = self.age / total_life  # 0->1 over lifetime
            sweep_range = 1.0 if self.rtype == "blade" else 1.50  # blade gets tight quick arc
            self._sweep_offset = -sweep_range / 2 + sweep_range * progress
            grow = min(progress * 2, 1.0)
            self.size = self._base_size * (1.0 + 0.6 * grow)
            # Always orbit around the CURRENT player position
            px, py = game.player.x, game.player.y
            swept_angle = self.angle + self._sweep_offset
            orbit_dist = self._base_size * 1.2
            self.x = px + math.cos(swept_angle) * orbit_dist
            self.y = py + math.sin(swept_angle) * orbit_dist

        self.age += dt
        return self.life > 0

    def is_dead(self):
        return self.life <= 0

    def draw(self, canvas, background_color="white"):
        if self.rtype == "basic":
            # simple circle particle
            canvas.create_oval(
                self.x - self.size, self.y - self.size,
                self.x + self.size, self.y + self.size,
                fill=self.color, outline=""
            )

        elif self.rtype == "blade":
            # crescent particle
            radius = self.size * 2.0
            offset = self.size * 0.7

            # main circle
            canvas.create_oval(
                self.x - radius, self.y - radius,
                self.x + radius, self.y + radius,
                fill=self.color, outline=self.color
            )

            # cutout circle (to form crescent)
            canvas.create_oval(
                self.x - radius + offset, self.y - radius,
                self.x + radius + offset, self.y + radius,
                fill=background_color, outline=background_color
            )
import tkinter.messagebox as mb

class SpawnPoint:
    def __init__(self, x, y, radius=70):
        self.x = x
        self.y = y
        self.radius = radius
        self.is_active = False   # Track if this is the active spawn point
        self.protection_end_time = 0  # When protection expires
        self.player_was_inside = False  # Track if player was inside last frame

    def draw(self, canvas):
        # Blue if active, red if not
        color = "blue" if self.is_active else "red"
        
        canvas.create_oval(
            self.x - self.radius, self.y - self.radius,
            self.x + self.radius, self.y + self.radius,
            outline=color,width=3
        )
        canvas.create_oval(
            self.x - self.radius - 5, self.y - self.radius - 5,
            self.x + self.radius + 5, self.y + self.radius + 5,
            outline="white", width=2
        )

    def update(self, game):
        current_time = time.time()
        is_protected = current_time < self.protection_end_time
        if hasattr(self, 'is_exit_portal') and self.is_exit_portal:
            player_inside = distance((game.player.x, game.player.y), (self.x, self.y)) < self.radius
            if player_inside:
                # Return to town
                game.dungeon_id = 0
                game.room_row = 0
                game.room_col = 0
                game.dungeon = {}
                game.room = game.get_room(0, 0)
                game.player.x = WINDOW_W // 2
                game.player.y = WINDOW_H // 2
                game.projectiles.clear()
                game.particles.clear()
                print("Returned to town!")
            return
        # Block projectiles only during protection
        if is_protected:
            for proj in list(game.projectiles):
                if distance((proj.x, proj.y), (self.x, self.y)) < self.radius:
                    if proj in game.projectiles:
                        game.projectiles.remove(proj)

            # Push enemies back only during protection
            for e in list(game.room.enemies):
                if distance((e.x, e.y), (self.x, self.y)) < self.radius + e.size:
                    ang = math.atan2(e.y - self.y, e.x - self.x)
                    push_dist = self.radius + e.size + 5
                    e.x = self.x + math.cos(ang) * push_dist
                    e.y = self.y + math.sin(ang) * push_dist
                    e.x = clamp(e.x, e.size, WINDOW_W - e.size)
                    e.y = clamp(e.y, e.size, WINDOW_H - e.size)

        # Check if player is inside
        p = game.player
        player_inside = distance((p.x, p.y), (self.x, self.y)) < self.radius
        
        # Only set spawn when player enters (wasn't inside before, but is now)
        if player_inside and not self.player_was_inside:
            # Deactivate all other spawn points first
            for room_key, room in game.dungeon.items():
                if room.spawn_point:
                    room.spawn_point.is_active = False
            
            # Set this as active spawn
            self.is_active = True
            game.player_spawn_row = game.room_row
            game.player_spawn_col = game.room_col
            game.player_spawn_x = self.x
            game.player_spawn_y = self.y
            print(f"Spawn point set at room ({game.room_row}, {game.room_col})!")
        
        # Update tracking
        self.player_was_inside = player_inside
class NPC:
    def __init__(self, name, x, y, role, shop_items=None):
        self.name = name
        self.x = x
        self.y = y
        self.home_x = x   # remember spawn so wander stays local
        self.home_y = y
        self.role = role
        self.size = 16
        self.shop_items = shop_items or []
        self.interact_range = 60
        self.wander_target = (x, y)
        self.last_move = time.time()
        self.speed = 1.0
        self.indoor = False   # True → NPC lives inside a building, hidden outdoors
        # Indoor wander state (independent of outdoor position)
        self.indoor_x = 0
        self.indoor_y = 0
        self._indoor_target = (0, 0)
        self._indoor_last_move = 0

        self.colors = {
            'librarian': '#8B4513',
            'blacksmith': '#696969',
            'enchanter': '#9370DB',
            'alchemist': '#00FF00',
            'chef': '#FFD700',
            'jeweler': '#FF1493',
            'trader': '#4169E1',
            'villager': '#DEB887'
        }
        self.color = self.colors.get(role, '#DEB887')

    def update(self, dt, buildings=None):
        """NPCs wander near their home, obeying town bounds and building walls."""
        if self.indoor:
            return   # indoor NPCs never move

        now = time.time()
        if now - self.last_move > random.uniform(2, 5):
            # New wander target near home, clamped to town interior
            tx = clamp(self.home_x + random.randint(-80, 80),
                       TOWN_X_START + 40, TOWN_X_END - 40)
            ty = clamp(self.home_y + random.randint(-80, 80),
                       TOWN_Y_START + 40, TOWN_Y_END - 40)
            self.wander_target = (tx, ty)
            self.last_move = now

        dx = self.wander_target[0] - self.x
        dy = self.wander_target[1] - self.y
        dist = math.hypot(dx, dy)
        if dist > 5:
            nx = self.x + (dx / dist) * self.speed
            ny = self.y + (dy / dist) * self.speed

            # Building collision — don't walk through walls
            blocked = False
            if buildings:
                for b in buildings:
                    if (nx + self.size > b['x'] and nx - self.size < b['x'] + b['width'] and
                            ny + self.size > b['y'] and ny - self.size < b['y'] + b['height']):
                        blocked = True
                        break
            if not blocked:
                self.x = nx
                self.y = ny

        # Hard-clamp to town bounds so NPCs never escape into the forest
        self.x = clamp(self.x, TOWN_X_START + self.size, TOWN_X_END - self.size)
        self.y = clamp(self.y, TOWN_Y_START + self.size, TOWN_Y_END - self.size)

    def update_indoor(self, dt, wall, room_w, room_h, furn_rects=None):
        """Wander within the interior room, avoiding walls and furniture."""
        furn_rects = furn_rects or []
        now = time.time()
        margin = wall + self.size + 10

        def blocked(x, y):
            sz = self.size
            for fx1, fy1, fx2, fy2 in furn_rects:
                if x - sz < fx2 and x + sz > fx1 and y - sz < fy2 and y + sz > fy1:
                    return True
            return False

        # Pick a new target that isn't inside furniture
        if now - self._indoor_last_move > random.uniform(2, 4):
            for _ in range(20):
                tx = random.randint(margin, room_w - margin)
                ty = random.randint(margin, room_h - margin)
                if not blocked(tx, ty):
                    self._indoor_target = (tx, ty)
                    break
            self._indoor_last_move = now

        dx = self._indoor_target[0] - self.indoor_x
        dy = self._indoor_target[1] - self.indoor_y
        dist = math.hypot(dx, dy)
        if dist > 4:
            spd = self.speed * 1.2
            nx = self.indoor_x + (dx / dist) * spd
            ny = self.indoor_y + (dy / dist) * spd
            # Slide along walls/furniture
            if not blocked(nx, ny):
                self.indoor_x, self.indoor_y = nx, ny
            elif not blocked(nx, self.indoor_y):
                self.indoor_x = nx
            elif not blocked(self.indoor_x, ny):
                self.indoor_y = ny
            else:
                # Pick a new target next frame
                self._indoor_last_move = 0

        # Clamp to room
        wall_m = wall + self.size
        self.indoor_x = clamp(self.indoor_x, wall_m, room_w - wall_m)
        self.indoor_y = clamp(self.indoor_y, wall_m, room_h - wall_m)
    
    def draw(self, canvas, camera_x, camera_y):
        """Draw NPC on screen with camera offset"""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Body
        canvas.create_oval(
            screen_x - self.size, screen_y - self.size,
            screen_x + self.size, screen_y + self.size,
            fill=self.color, outline='black', width=2
        )
        
        # Name tag
        canvas.create_text(
            screen_x, screen_y - self.size - 15,
            text=self.name, fill='white',
            font=('Arial', 10, 'bold')
        )
# ---------- Room ----------
class Room:
    def __init__(self, row, col, dungeon_id=1, player_level=1):
        self.row = row
        self.col = col
        self.enemies = []
        self.npcs = []
        self.buildings = []  # Store building rectangles
        self.decorations = []  # Store decoration objects
        
        # TOWN LAYOUT (dungeon_id == 0)
        # TOWN LAYOUT (dungeon_id == 0)
        if dungeon_id == 0:
            self.spawn_point = None
            self.is_town = True  # Mark this as town
            self.create_town_layout()
            return
        
        # DUNGEON LAYOUT (dungeon_id > 0)
        # Exit portal in room (0,0)
        if row == 0 and col == 0:
            self.spawn_point = SpawnPoint(WINDOW_W//2, WINDOW_H//2)
            self.spawn_point.is_exit_portal = True
            self.spawn_point.radius = 50
        
        # Spawn point in non-boss rooms
        if not (row == 0 and col == 4):
            self.spawn_point = SpawnPoint(WINDOW_W//2, WINDOW_H//2)
        else:
            self.spawn_point = None
        
        # Starting room has no enemies
        if (row, col) == (0, 0):
            return
        
        depth = row + col
        spawn_enemies_for_dungeon(self, dungeon_id, player_level, count=4 + depth)
        
        # Spawn boss in boss room
        if row == 0 and col == 4:
            spawn_boss_for_room(self, dungeon_id)
    
    def create_town_layout(self):
        """Create a detailed town with buildings, NPCs, and decorations"""
        
        # === BUILDINGS === 
        # Player's house (top-left) - NO SIGN
        _house_chest = {
            'x': WINDOW_W//2 + 60, 'y': WINDOW_H//2 - 60,
            'opened': False, 'coins': 80,
            'items': [
                ConsumableItem('Health Potion','health_potion','Uncommon', price=40, hp_restore=100),
                ConsumableItem('Minor Mana Potion','mana_potion','Common', price=20, mana_restore=50),
            ]
        }
        self.buildings.append({
            'type': 'house',
            'x': 200, 'y': 200,
            'width': 120, 'height': 100,
            'color': '#8B4513',
            'roof_color': '#654321',
            'name': "Your House",
            'door_side': 'bottom',
            'pattern': 'brick',
            'has_sign': False,
            'interior': [],
            'rooms': [
                {'name': 'Living Room',  'floor': '#6b5040', 'wall': '#4a3020',
                 'doors': {'north': 1, 'east': 2}, 'chests': [], 'furniture': 'house_living'},
                {'name': 'Bedroom',      'floor': '#4a3a5a', 'wall': '#2d1060',
                 'doors': {'south': 0},             'chests': [], 'furniture': 'bedroom'},
                {'name': 'Kitchen',      'floor': '#5a4030', 'wall': '#3a2010',
                 'doors': {'west': 0, 'east': 3},   'chests': [], 'furniture': 'house_kitchen'},
                {'name': 'Storage Room', 'floor': '#3a3020', 'wall': '#2a2010',
                 'doors': {'west': 2},              'chests': [_house_chest], 'furniture': 'storage'},
            ],
        })
        
        # Library (top-center)
        self.buildings.append({
            'type': 'library',
            'x': 600, 'y': 200,
            'width': 150, 'height': 120,
            'color': '#5C4033',
            'roof_color': '#4A3428',
            'name': "📚 LIBRARY",
            'door_side': 'bottom',
            'pattern': 'brick',
            'has_sign': False,
            'shape': 'book',
            'indoor_npc_name': 'Eldrin',
            'interior': [
                {'type': 'rect', 'x': 10, 'y': 10, 'w': 40, 'h': 80, 'color': '#4A3428'},
                {'type': 'rect', 'x': 100, 'y': 10, 'w': 40, 'h': 80, 'color': '#4A3428'},
            ]
        })
        
        # Blacksmith Forge (top-right)
        self.buildings.append({
            'type': 'blacksmith',
            'x': 1000, 'y': 200,
            'width': 130, 'height': 130,
            'color': '#2C2C2C',
            'roof_color': '#1A1A1A',
            'name': "⚒️ FORGE",
            'door_side': 'bottom',
            'pattern': 'stone',
            'has_sign': False,
            'has_chimney': True,
            'indoor_npc_name': 'Gorak',
            'indoor_spawn_x': WINDOW_W // 2,  # spawn in the centre (open floor area)
            'indoor_spawn_y': WINDOW_H - 70,
            'interior': [],
        })
        
        # Enchanter Tower (center-left)
        self.buildings.append({
            'type': 'tower',
            'x': 200, 'y': 500,
            'width': 80, 'height': 180,
            'color': '#6B4C9A',
            'roof_color': '#4A3368',
            'name': "🔮 TOWER",
            'door_side': 'bottom',
            'pattern': 'stone',
            'has_sign': False,
            'shape': 'tower',
            'indoor_npc_name': 'Mystara',
            'interior': [
                {'type': 'oval', 'x': 20, 'y': 20, 'w': 40, 'h': 40, 'color': '#9370DB'},
                {'type': 'rect', 'x': 10, 'y': 100, 'w': 60, 'h': 60, 'color': '#4A3368'},
            ]
        })
        
        # Alchemist Shop (center) - HAS SIGN
        self.buildings.append({
            'type': 'shop',
            'x': 500, 'y': 480,
            'width': 110, 'height': 90,
            'color': '#228B22',
            'roof_color': '#1B6B1B',
            'name': "🧪 ALCHEMIST",
            'door_side': 'bottom',
            'pattern': 'wood',
            'has_sign': True,
            'shape': 'bottle',
            'indoor_npc_name': 'Zephyr',
            'interior': [
                {'type': 'rect', 'x': 10, 'y': 10, 'w': 30, 'h': 60, 'color': '#1B6B1B'},
                {'type': 'rect', 'x': 70, 'y': 10, 'w': 30, 'h': 60, 'color': '#1B6B1B'},
            ]
        })
        
        # Bakery/Inn (center-right) - HAS SIGN
        self.buildings.append({
            'type': 'inn',
            'x': 850, 'y': 480,
            'width': 140, 'height': 95,
            'color': '#D2691E',
            'roof_color': '#A0522D',
            'name': "🍞 BAKERY",
            'door_side': 'bottom',
            'pattern': 'wood',
            'has_sign': True,
            'shape': 'bread',
            'indoor_npc_name': 'Berta',
            'npc_room': 0,
            'interior': [],
            'indoor_spawn_x': WINDOW_W // 2,       # counter area — safe, below the kitchen wall
            'indoor_spawn_y': WINDOW_H - 70,
            'rooms': [
                {'name': 'Counter',  'floor': '#6b4a2a', 'wall': '#4a2800',
                 'doors': {'north': 1},            'chests': [], 'furniture': 'bakery_counter'},
                {'name': 'Kitchen',  'floor': '#5a3020', 'wall': '#3a1800',
                 'doors': {'south': 0, 'east': 2}, 'chests': [], 'furniture': 'bakery_kitchen'},
                {'name': 'Storage',  'floor': '#3a2a10', 'wall': '#2a1800',
                 'doors': {'west': 1},             'chests': [], 'furniture': 'bakery_storage'},
            ],
        })
        
        # Jeweler (bottom-left) - HAS SIGN
        self.buildings.append({
            'type': 'shop',
            'x': 220, 'y': 780,
            'width': 100, 'height': 85,
            'color': '#DB7093',
            'roof_color': '#C25876',
            'name': "💎 JEWELER",
            'door_side': 'bottom',
            'pattern': 'fancy',
            'has_sign': True,
            'shape': 'diamond',
            'indoor_npc_name': 'Gemma',
            'interior': [
                {'type': 'rect', 'x': 30, 'y': 30, 'w': 40, 'h': 30, 'color': '#C25876'},
            ]
        })
        
        # General Trader (bottom-center) - HAS SIGN
        self.buildings.append({
            'type': 'shop',
            'x': 600, 'y': 780,
            'width': 120, 'height': 90,
            'color': '#4682B4',
            'roof_color': '#36648B',
            'name': "🛒 TRADER",
            'door_side': 'bottom',
            'pattern': 'wood',
            'has_sign': True,
            'shape': 'store',
            'indoor_npc_name': 'Marcus',
            'interior': [
                {'type': 'rect', 'x': 10, 'y': 10, 'w': 40, 'h': 60, 'color': '#36648B'},
                {'type': 'rect', 'x': 70, 'y': 10, 'w': 40, 'h': 60, 'color': '#36648B'},
            ]
        })
        
        # === NPCs ===
        # Named shop NPCs live INSIDE their buildings — marked indoor=True
        # so they don't appear or wander in the overworld.
        def indoor_npc(name, x, y, role, items):
            npc = NPC(name, x, y, role, items)
            npc.indoor = True
            return npc

        self.npcs.append(indoor_npc("Eldrin",  675, 260, 'librarian',  self.get_librarian_items()))
        self.npcs.append(indoor_npc("Gorak",  1065, 265, 'blacksmith', self.get_blacksmith_items()))
        self.npcs.append(indoor_npc("Mystara", 240, 590, 'enchanter',  self.get_enchanter_items()))
        self.npcs.append(indoor_npc("Zephyr",  555, 525, 'alchemist',  self.get_alchemist_items()))
        self.npcs.append(indoor_npc("Berta",   920, 528, 'chef',       self.get_chef_items()))
        self.npcs.append(indoor_npc("Gemma",   270, 823, 'jeweler',    self.get_jeweler_items()))
        self.npcs.append(indoor_npc("Marcus",  660, 825, 'trader',     self.get_trader_items()))

        # Oryn stays OUTSIDE — sells the map near the fountain
        self.npcs.append(NPC("Oryn", 820, 390, 'villager', [MAP_ITEM]))

        # Villagers — spawn only in open areas, never inside a building footprint
        def _inside_building(nx, ny, margin=40):
            for b in self.buildings:
                bx1 = b['x'] - margin
                by1 = b['y'] - margin
                bx2 = b['x'] + b['width']  + margin
                by2 = b['y'] + b['height'] + margin
                if bx1 <= nx <= bx2 and by1 <= ny <= by2:
                    return True
            return False

        for i in range(8):
            for _ in range(50):   # up to 50 attempts per villager
                vx = random.randint(300, 1100)
                vy = random.randint(300, 900)
                if not _inside_building(vx, vy):
                    break
            self.npcs.append(NPC(f"Villager {i+1}", vx, vy, 'villager'))
        
        # === OPTIMIZED FOREST BOUNDARY ===
        # Define dungeon 1 entrance gap
        # === OPTIMIZED FOREST BOUNDARY WITH DUNGEON GAPS ===
        # Define all dungeon entrance gaps
        dungeon1_gap = {'y_start': 350, 'y_end': 500, 'side': 'left'}    # Left side
        dungeon2_gap = {'y_start': 200, 'y_end': 300, 'side': 'right'}   # Right side (top)
        dungeon3_gap = {'y_start': 750, 'y_end': 850, 'side': 'right'}   # Right side (bottom)
        dungeon4_gap = {'x_start': 600, 'x_end': 800, 'side': 'bottom'}  # Bottom side

        # TOP FOREST WALL (no gaps needed here)
        self.decorations.append({
            'type': 'forest_wall',
            'x': TOWN_X_START - FOREST_THICKNESS,
            'y': TOWN_Y_START - FOREST_THICKNESS,
            'width': (TOWN_X_END - TOWN_X_START) + FOREST_THICKNESS * 2,
            'height': FOREST_THICKNESS,
            'color': '#2d5016',
            'collision_rect': (TOWN_X_START - FOREST_THICKNESS, TOWN_Y_START - FOREST_THICKNESS,
                              TOWN_X_END + FOREST_THICKNESS, TOWN_Y_START)
        })

        # BOTTOM FOREST WALL - Split for dungeon 4 gap
        # Left part (before gap)
        self.decorations.append({
            'type': 'forest_wall',
            'x': TOWN_X_START - FOREST_THICKNESS,
            'y': TOWN_Y_END,
            'width': dungeon4_gap['x_start'] - TOWN_X_START + FOREST_THICKNESS,
            'height': FOREST_THICKNESS,
            'color': '#2d5016',
            'collision_rect': (TOWN_X_START - FOREST_THICKNESS, TOWN_Y_END,
                              dungeon4_gap['x_start'], TOWN_Y_END + FOREST_THICKNESS)
        })

        # Right part (after gap)
        self.decorations.append({
            'type': 'forest_wall',
            'x': dungeon4_gap['x_end'],
            'y': TOWN_Y_END,
            'width': TOWN_X_END - dungeon4_gap['x_end'] + FOREST_THICKNESS,
            'height': FOREST_THICKNESS,
            'color': '#2d5016',
            'collision_rect': (dungeon4_gap['x_end'], TOWN_Y_END,
                              TOWN_X_END + FOREST_THICKNESS, TOWN_Y_END + FOREST_THICKNESS)
        })

        # LEFT FOREST WALL - Split for dungeon 1 gap
        # Top part (above gap)
        self.decorations.append({
            'type': 'forest_wall',
            'x': TOWN_X_START - FOREST_THICKNESS,
            'y': TOWN_Y_START - FOREST_THICKNESS,
            'width': FOREST_THICKNESS,
            'height': dungeon1_gap['y_start'] - TOWN_Y_START + FOREST_THICKNESS,
            'color': '#2d5016',
            'collision_rect': (TOWN_X_START - FOREST_THICKNESS, TOWN_Y_START - FOREST_THICKNESS,
                              TOWN_X_START, dungeon1_gap['y_start'] - 10)
        })

        # Bottom part (below gap)
        self.decorations.append({
            'type': 'forest_wall',
            'x': TOWN_X_START - FOREST_THICKNESS,
            'y': dungeon1_gap['y_end'],
            'width': FOREST_THICKNESS,
            'height': TOWN_Y_END - dungeon1_gap['y_end'] + FOREST_THICKNESS,
            'color': '#2d5016',
            'collision_rect': (TOWN_X_START - FOREST_THICKNESS, dungeon1_gap['y_end'] + 10,
                              TOWN_X_START, TOWN_Y_END + FOREST_THICKNESS)
        })

        # RIGHT FOREST WALL - Split for dungeon 2 and 3 gaps
        # Top part (above dungeon 2)
        self.decorations.append({
            'type': 'forest_wall',
            'x': TOWN_X_END,
            'y': TOWN_Y_START - FOREST_THICKNESS,
            'width': FOREST_THICKNESS,
            'height': dungeon2_gap['y_start'] - TOWN_Y_START + FOREST_THICKNESS,
            'color': '#2d5016',
            'collision_rect': (TOWN_X_END, TOWN_Y_START - FOREST_THICKNESS,
                              TOWN_X_END + FOREST_THICKNESS, dungeon2_gap['y_start'] - 10)
        })

        # Middle part (between dungeons 2 and 3)
        self.decorations.append({
            'type': 'forest_wall',
            'x': TOWN_X_END,
            'y': dungeon2_gap['y_end'],
            'width': FOREST_THICKNESS,
            'height': dungeon3_gap['y_start'] - dungeon2_gap['y_end'],
            'color': '#2d5016',
            'collision_rect': (TOWN_X_END, dungeon2_gap['y_end'] + 10,
                              TOWN_X_END + FOREST_THICKNESS, dungeon3_gap['y_start'] - 10)
        })

        # Bottom part (below dungeon 3)
        self.decorations.append({
            'type': 'forest_wall',
            'x': TOWN_X_END,
            'y': dungeon3_gap['y_end'],
            'width': FOREST_THICKNESS,
            'height': TOWN_Y_END - dungeon3_gap['y_end'] + FOREST_THICKNESS,
            'color': '#2d5016',
            'collision_rect': (TOWN_X_END, dungeon3_gap['y_end'] + 10,
                              TOWN_X_END + FOREST_THICKNESS, TOWN_Y_END + FOREST_THICKNESS)
        })

        # === FOREST WALL CAPS (blocking paths beyond 50 pixels from dungeon) ===

        # Dungeon 1 path cap (left side)
        dungeon1_x = TOWN_X_START - 200
        self.decorations.append({
            'type': 'forest_wall',
            'x': dungeon1_x - 50 - FOREST_THICKNESS,
            'y': dungeon1_gap['y_start'],
            'width': FOREST_THICKNESS,
            'height': dungeon1_gap['y_end'] - dungeon1_gap['y_start'],
            'color': '#2d5016',
            'collision_rect': (dungeon1_x - 50 - FOREST_THICKNESS, dungeon1_gap['y_start'],
                              dungeon1_x - 50, dungeon1_gap['y_end'])
        })

        # Dungeon 2 path cap (right side)
        dungeon2_x = TOWN_X_END + 150
        self.decorations.append({
            'type': 'forest_wall',
            'x': dungeon2_x + 50,
            'y': dungeon2_gap['y_start'],
            'width': FOREST_THICKNESS,
            'height': dungeon2_gap['y_end'] - dungeon2_gap['y_start'],
            'color': '#2d5016',
            'collision_rect': (dungeon2_x + 50, dungeon2_gap['y_start'],
                              dungeon2_x + 50 + FOREST_THICKNESS, dungeon2_gap['y_end'])
        })

        # Dungeon 3 path cap (right side)
        dungeon3_x = TOWN_X_END + 150
        self.decorations.append({
            'type': 'forest_wall',
            'x': dungeon3_x + 50,
            'y': dungeon3_gap['y_start'],
            'width': FOREST_THICKNESS,
            'height': dungeon3_gap['y_end'] - dungeon3_gap['y_start'],
            'color': '#2d5016',
            'collision_rect': (dungeon3_x + 50, dungeon3_gap['y_start'],
                              dungeon3_x + 50 + FOREST_THICKNESS, dungeon3_gap['y_end'])
        })

        # Dungeon 4 path cap (bottom side)
        dungeon4_y = TOWN_Y_END + 150
        self.decorations.append({
            'type': 'forest_wall',
            'x': dungeon4_gap['x_start'],
            'y': dungeon4_y + 50,
            'width': dungeon4_gap['x_end'] - dungeon4_gap['x_start'],
            'height': FOREST_THICKNESS,
            'color': '#2d5016',
            'collision_rect': (dungeon4_gap['x_start'], dungeon4_y + 50,
                              dungeon4_gap['x_end'], dungeon4_y + 50 + FOREST_THICKNESS)
        })

        # CORNERS (keep these)
        self.decorations.append({
            'type': 'forest_wall',
            'x': TOWN_X_START - FOREST_THICKNESS,
            'y': TOWN_Y_START - FOREST_THICKNESS,
            'width': FOREST_THICKNESS,
            'height': FOREST_THICKNESS,
            'color': '#1B5E20',
            'collision_rect': (TOWN_X_START - FOREST_THICKNESS, TOWN_Y_START - FOREST_THICKNESS,
                              TOWN_X_START, TOWN_Y_START)
        })

        self.decorations.append({
            'type': 'forest_wall',
            'x': TOWN_X_END,
            'y': TOWN_Y_START - FOREST_THICKNESS,
            'width': FOREST_THICKNESS,
            'height': FOREST_THICKNESS,
            'color': '#1B5E20',
            'collision_rect': (TOWN_X_END, TOWN_Y_START - FOREST_THICKNESS,
                              TOWN_X_END + FOREST_THICKNESS, TOWN_Y_START)
        })

        self.decorations.append({
            'type': 'forest_wall',
            'x': TOWN_X_START - FOREST_THICKNESS,
            'y': TOWN_Y_END,
            'width': FOREST_THICKNESS,
            'height': FOREST_THICKNESS,
            'color': '#1B5E20',
            'collision_rect': (TOWN_X_START - FOREST_THICKNESS, TOWN_Y_END,
                              TOWN_X_START, TOWN_Y_END + FOREST_THICKNESS)
        })

        self.decorations.append({
            'type': 'forest_wall',
            'x': TOWN_X_END,
            'y': TOWN_Y_END,
            'width': FOREST_THICKNESS,
            'height': FOREST_THICKNESS,
            'color': '#1B5E20',
            'collision_rect': (TOWN_X_END, TOWN_Y_END,
                              TOWN_X_END + FOREST_THICKNESS, TOWN_Y_END + FOREST_THICKNESS)
        })
        # === FOREST EDGES (wavy circles) ===
        # Top edge - BOTH sides
        # === FOREST EDGES (wavy circles) ===
        # Top edge - BOTH sides (full width, no gaps)
        for x in range(TOWN_X_START - FOREST_THICKNESS, TOWN_X_END + FOREST_THICKNESS, 40):
            # Outside edge
            self.decorations.append({
                'type': 'forest_edge',
                'x': x + random.randint(-15, 15),
                'y': TOWN_Y_START - FOREST_THICKNESS + random.randint(-10, 10),
                'size': random.randint(25, 45),
                'color': '#3a6b24'
            })
            # Inside edge
            self.decorations.append({
                'type': 'forest_edge',
                'x': x + random.randint(-15, 15),
                'y': TOWN_Y_START + random.randint(-10, 10),
                'size': random.randint(25, 45),
                'color': '#3a6b24'
            })

        # Bottom edge - BOTH sides, SKIP dungeon 4 gap
        for x in range(TOWN_X_START - FOREST_THICKNESS, TOWN_X_END + FOREST_THICKNESS, 40):
            # Skip the dungeon 4 gap area
            if dungeon4_gap['x_start'] - 50 <= x <= dungeon4_gap['x_end'] + 50:
                continue
            
            # Outside edge
            self.decorations.append({
                'type': 'forest_edge',
                'x': x + random.randint(-15, 15),
                'y': TOWN_Y_END + FOREST_THICKNESS + random.randint(-10, 10),
                'size': random.randint(25, 45),
                'color': '#3a6b24'
            })
            # Inside edge
            self.decorations.append({
                'type': 'forest_edge',
                'x': x + random.randint(-15, 15),
                'y': TOWN_Y_END + random.randint(-10, 10),
                'size': random.randint(25, 45),
                'color': '#3a6b24'
            })

        # Left edge - BOTH sides, SKIP dungeon 1 gap
        for y in range(TOWN_Y_START - FOREST_THICKNESS, TOWN_Y_END + FOREST_THICKNESS, 40):
            # Skip the dungeon 1 gap area
            if dungeon1_gap['y_start'] - 50 <= y <= dungeon1_gap['y_end'] + 50:
                continue
            
            # Outside edge
            self.decorations.append({
                'type': 'forest_edge',
                'x': TOWN_X_START - FOREST_THICKNESS + random.randint(-10, 10),
                'y': y + random.randint(-15, 15),
                'size': random.randint(25, 45),
                'color': '#3a6b24'
            })
            # Inside edge
            self.decorations.append({
                'type': 'forest_edge',
                'x': TOWN_X_START + random.randint(-10, 10),
                'y': y + random.randint(-15, 15),
                'size': random.randint(25, 45),
                'color': '#3a6b24'
            })

        # Right edge - BOTH sides, SKIP dungeon 2 and 3 gaps
        for y in range(TOWN_Y_START - FOREST_THICKNESS, TOWN_Y_END + FOREST_THICKNESS, 40):
            # Skip the dungeon 2 gap area
            if dungeon2_gap['y_start'] - 50 <= y <= dungeon2_gap['y_end'] + 50:
                continue
            # Skip the dungeon 3 gap area
            if dungeon3_gap['y_start'] - 50 <= y <= dungeon3_gap['y_end'] + 50:
                continue
            
            # Outside edge
            self.decorations.append({
                'type': 'forest_edge',
                'x': TOWN_X_END + FOREST_THICKNESS + random.randint(-10, 10),
                'y': y + random.randint(-15, 15),
                'size': random.randint(25, 45),
                'color': '#3a6b24'
            })
            # Inside edge
            self.decorations.append({
                'type': 'forest_edge',
                'x': TOWN_X_END + random.randint(-10, 10),
                'y': y + random.randint(-15, 15),
                'size': random.randint(25, 45),
                'color': '#3a6b24'
            })

        # === FOREST EDGES FOR PATH CAPS (blocks at 50 pixels from dungeon) ===

        # Dungeon 1 path cap edges (left side)
        dungeon1_x = TOWN_X_START - 200
        for y in range(dungeon1_gap['y_start'], dungeon1_gap['y_end'], 40):
            # Cap wall edge
            self.decorations.append({
                'type': 'forest_edge',
                'x': dungeon1_x - 50 + random.randint(-10, 10),
                'y': y + random.randint(-15, 15),
                'size': random.randint(25, 45),
                'color': '#3a6b24'
            })

        # Dungeon 2 path cap edges (right side)
        dungeon2_x = TOWN_X_END + 150
        for y in range(dungeon2_gap['y_start'], dungeon2_gap['y_end'], 40):
            self.decorations.append({
                'type': 'forest_edge',
                'x': dungeon2_x + 50 + random.randint(-10, 10),
                'y': y + random.randint(-15, 15),
                'size': random.randint(25, 45),
                'color': '#3a6b24'
            })

        # Dungeon 3 path cap edges (right side)
        dungeon3_x = TOWN_X_END + 150
        for y in range(dungeon3_gap['y_start'], dungeon3_gap['y_end'], 40):
            self.decorations.append({
                'type': 'forest_edge',
                'x': dungeon3_x + 50 + random.randint(-10, 10),
                'y': y + random.randint(-15, 15),
                'size': random.randint(25, 45),
                'color': '#3a6b24'
            })

        # Dungeon 4 path cap edges (bottom side)
        dungeon4_y = TOWN_Y_END + 150
        for x in range(dungeon4_gap['x_start'], dungeon4_gap['x_end'], 40):
            self.decorations.append({
                'type': 'forest_edge',
                'x': x + random.randint(-15, 15),
                'y': dungeon4_y + 50 + random.randint(-10, 10),
                'size': random.randint(25, 45),
                'color': '#3a6b24'
            })
        
        # === DECORATIONS WITH COLLISION ===
        self.decorations.append({
            'type': 'fountain',
            'x': 700, 'y': 550,
            'size': 40,
            'has_collision': True,
            'water_particles': []
        })
        
        lamp_positions = [(400, 350), (800, 350), (400, 650), (900, 650)]
        for lx, ly in lamp_positions:
            self.decorations.append({
                'type': 'lamp',
                'x': lx, 'y': ly,
                'size': 12,
                'has_collision': True
            })
        
        
        # Dungeon portals - FIXED POSITIONS
        dungeon_entrances = [
            {'x': TOWN_X_START - 200, 'y': 425, 'id': 1, 'name': '🌲 Forest Temple', 'color': '#228B22'},
            {'x': TOWN_X_END + 150, 'y': 250, 'id': 2, 'name': '🌋 Volcano', 'color': '#FF4500'},
            {'x': TOWN_X_END + 150, 'y': 800, 'id': 3, 'name': '❄️ Ice Cavern', 'color': '#00CED1'},
            {'x': 700, 'y': TOWN_Y_END + 150, 'id': 4, 'name': '👻 Shadow Realm', 'color': '#8B008B'}
        ]
        
        for entrance in dungeon_entrances:
            self.decorations.append({
                'type': 'dungeon_entrance',
                'x': entrance['x'],
                'y': entrance['y'],
                'dungeon_id': entrance['id'],
                'name': entrance['name'],
                'color': entrance['color'],
                'size': 40
            })
        
        # Roads
        self.roads = []
        if self.is_town:
            self.roads.append({
                'x1': TOWN_X_START, 'y1': WINDOW_H // 2,
                'x2': TOWN_X_END, 'y2': WINDOW_H // 2,
                'width': 80
            })
            
            self.roads.append({
                'x1': WINDOW_W // 2, 'y1': TOWN_Y_START,
                'x2': WINDOW_W // 2, 'y2': TOWN_Y_END,
                'width': 80
            })
            
            for b in self.buildings:
                bx_center = b['x'] + b['width'] // 2
                self.roads.append({
                    'x1': bx_center, 'y1': b['y'] + b['height'],
                    'x2': bx_center, 'y2': WINDOW_H // 2,
                    'width': 40
                })
    def get_librarian_items(self):
        """Books that give skill scrolls"""
        return [item for item in SHOP_ITEMS if item.skills][:3]
    
    def get_blacksmith_items(self):
        """Weapons and armour"""
        weapons = [item for item in SHOP_ITEMS if item.item_type == 'weapon']
        armour  = [item for item in SHOP_ITEMS if item.item_type in
                   ('helmet','chestplate','leggings','boots','gloves')]
        return weapons + armour
    
    def get_enchanter_items(self):
        """Epic and Legendary items"""
        return [item for item in SHOP_ITEMS if item.rarity in ['Epic', 'Legendary']]
    
    def get_alchemist_items(self):
        """Potions and elixirs"""
        return list(CONSUMABLE_SHOP_ITEMS)
    
    def get_trader_items(self):
        """General trader — weapons, rings/necklaces, and special items like Flamethrower & Smoke Bomb"""
        flamethrower = next((i for i in SHOP_ITEMS if i.name == 'Flamethrower'), None)
        smoke_bomb = next((c for c in CONSUMABLE_SHOP_ITEMS if c.name == 'Smoke Bomb'), None)
        base = SHOP_ITEMS[:10]
        extras = []
        if flamethrower and flamethrower not in base:
            extras.append(flamethrower)
        if smoke_bomb:
            extras.append(smoke_bomb)
        return base + extras
    
    def get_chef_items(self):
        """Food items (no potions, no smoke bombs)"""
        return [c for c in CONSUMABLE_SHOP_ITEMS if c.subtype in ('bread','meat','stew')]
    
    def get_jeweler_items(self):
        """Rings and necklaces"""
        return [item for item in SHOP_ITEMS if item.item_type in ['ring', 'necklace']]

# ---------- Skill Tree Window ----------
class SkillTreeWindow:
    """
    Visual skill tree. Can be opened standalone (creates its own Toplevel)
    or embedded into an existing frame via embed_in_frame().
    """
    # ── Layout & colour constants ───────────────────────────────────────────
    CW, CH    = 860, 510
    TIER_Y    = {1: 65, 2: 195, 3: 325, 4: 455}
    BRANCH_X  = {'center': 430, 'left': 195, 'right': 665}
    NODE_R    = 34

    C_UNLOCKED  = '#ffd700'
    C_AVAILABLE = '#4caf50'
    C_LOCKED    = '#444455'
    C_PASSIVE   = '#5c9bd6'
    C_TEXT_DARK = '#111111'
    C_TEXT_LIT  = '#eeeeee'
    C_BG        = '#0d0d1a'
    C_LINE_ON   = '#ffd700'
    C_LINE_OFF  = '#2a2a44'

    # ── Construction ───────────────────────────────────────────────────────
    def __init__(self, game_frame, player):
        """Open as a standalone Toplevel."""
        self.gf     = game_frame
        self.player = player
        self.tree   = SKILL_TREES.get(player.class_name, [])
        self._node_coords = {}

        self.win = tk.Toplevel(game_frame)
        self.win.title(f"Skill Tree  —  {player.class_name}")
        self.win.configure(bg=self.C_BG)
        self.win.resizable(False, False)
        self._build_ui(self.win)

    @classmethod
    def embed_in_frame(cls, frame, game_frame, player, dialog_parent):
        """
        Build the skill tree UI *inside* an existing tk.Frame.
        Returns the controller object so bindings stay alive.
        """
        obj = object.__new__(cls)
        obj.gf     = game_frame
        obj.player = player
        obj.tree   = SKILL_TREES.get(player.class_name, [])
        obj._node_coords = {}
        obj.win    = dialog_parent   # used only for messagebox parent
        obj._build_ui(frame)
        return obj

    # ── UI builder (shared by both modes) ─────────────────────────────────
    def _build_ui(self, container):
        """Create all widgets inside *container* (Toplevel or Frame)."""
        # Header row
        hdr = tk.Frame(container, bg='#1a1a2e')
        hdr.pack(fill='x', side='top')
        tk.Label(hdr,
                 text=f"⚔  {self.player.class_name}  Skill Tree",
                 font=("Arial", 14, "bold"),
                 bg='#1a1a2e', fg='#ffd700').pack(side='left', padx=14, pady=7)
        self.sp_label = tk.Label(hdr,
                                  text=f"Skill Points: {self.player.skill_points}",
                                  font=("Arial", 11, "bold"),
                                  bg='#1a1a2e', fg='#aaffaa')
        self.sp_label.pack(side='right', padx=14)

        # Canvas
        self.canvas = tk.Canvas(container,
                                width=self.CW, height=self.CH,
                                bg=self.C_BG, highlightthickness=0)
        self.canvas.pack(side='top', padx=6, pady=4)
        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<Motion>',   self._on_hover)

        # Info bar at the bottom
        info_outer = tk.Frame(container, bg='#1a1a2e')
        info_outer.pack(side='top', fill='x', padx=6, pady=(0, 6))
        self.info_label = tk.Label(info_outer,
                                   text="Hover a node to see details.  Click an available node to unlock.",
                                   font=("Arial", 9), bg='#1a1a2e', fg='#aaaaaa',
                                   wraplength=self.CW - 20, justify='left')
        self.info_label.pack(anchor='w', padx=8, pady=5)

        self._draw()

    # ── Helpers ────────────────────────────────────────────────────────────
    def _node_pos(self, node):
        return self.BRANCH_X[node['branch']], self.TIER_Y[node['tier']]

    def _node_state(self, node):
        if node['name'] in getattr(self.player, 'tree_unlocked', set()):
            return 'unlocked'
        ok, _ = self.player.can_unlock_tree_skill(node['name'])
        return 'available' if ok else 'locked'

    def _node_color(self, node):
        s = self._node_state(node)
        if s == 'unlocked':
            return self.C_PASSIVE if node['type'] == 'passive' else self.C_UNLOCKED
        return self.C_AVAILABLE if s == 'available' else self.C_LOCKED

    def _line_color(self, fn, tn):
        return (self.C_LINE_ON
                if self._node_state(fn) == 'unlocked' and self._node_state(tn) != 'locked'
                else self.C_LINE_OFF)

    # ── Drawing ────────────────────────────────────────────────────────────
    def _draw(self):
        c = self.canvas
        c.delete('all')
        self._node_coords.clear()

        by_name = {n['name']: n for n in self.tree}

        # Background grid lines
        for y in self.TIER_Y.values():
            c.create_line(80, y, self.CW - 10, y, fill='#1a1a30', width=1)

        # Column header labels
        c.create_text(self.BRANCH_X['left'],  22, text="— ACTIVE SKILLS —",
                      font=("Arial", 10, "bold"), fill='#556677')
        c.create_text(self.BRANCH_X['right'], 22, text="— PASSIVE SKILLS —",
                      font=("Arial", 10, "bold"), fill='#335566')

        # Tier labels (left margin)
        tier_labels = {1: "Tier 1\n(Free)", 2: "Tier 2\n1 SP",
                       3: "Tier 3\n1 SP",   4: "Tier 4\n2 SP"}
        for t, lbl in tier_labels.items():
            c.create_text(42, self.TIER_Y[t], text=lbl,
                          font=("Arial", 8), fill='#555577', justify='center')

        # Connector lines (drawn before nodes so nodes sit on top)
        for node in self.tree:
            nx, ny = self._node_pos(node)
            for prereq_name in node['prereq']:
                if prereq_name in by_name:
                    pn = by_name[prereq_name]
                    px, py = self._node_pos(pn)
                    lc = self._line_color(pn, node)
                    c.create_line(px, py, nx, ny, fill=lc, width=3, dash=(7, 4))

        # Nodes
        for node in self.tree:
            nx, ny = self._node_pos(node)
            self._node_coords[node['name']] = (nx, ny)
            self._draw_node(node, nx, ny)

    def _draw_node(self, node, cx, cy):
        c     = self.canvas
        r     = self.NODE_R
        col   = self._node_color(node)
        state = self._node_state(node)

        # Outer glow for available nodes
        if state == 'available':
            c.create_oval(cx-r-7, cy-r-7, cx+r+7, cy+r+7,
                          outline='#55ee55', width=2, dash=(4, 3))

        # Main filled circle
        outline_col = '#aaaaaa' if state != 'locked' else '#333344'
        c.create_oval(cx-r, cy-r, cx+r, cy+r,
                      fill=col, outline=outline_col, width=2)

        # Text inside node
        if state == 'locked':
            c.create_text(cx, cy - 8, text='🔒', font=("Arial", 13), fill='#666677')
            c.create_text(cx, cy + 12, text=node['name'][:11],
                          font=("Arial", 7), fill='#666677', width=r*2 - 6)
        else:
            # Word-wrap name into up to 3 short lines
            words, lines, cur = node['name'].split(), [], ""
            for w in words:
                if len(cur) + len(w) + 1 <= 11:
                    cur = (cur + " " + w).strip()
                else:
                    if cur: lines.append(cur)
                    cur = w
            if cur: lines.append(cur)
            text = "\n".join(lines[:3])
            fg = self.C_TEXT_DARK if state == 'unlocked' else self.C_TEXT_LIT
            c.create_text(cx, cy, text=text,
                          font=("Arial", 8, "bold"), fill=fg,
                          width=r*2 - 8, justify='center')

        # SP cost badge (bottom-right)
        cost = node['cost']
        if cost > 0 and state != 'unlocked':
            bx, by = cx + r - 7, cy + r - 7
            badge_col = '#882222' if state == 'locked' else '#1a6622'
            c.create_oval(bx-11, by-11, bx+11, by+11,
                          fill=badge_col, outline='#111111', width=1)
            c.create_text(bx, by, text=str(cost),
                          font=("Arial", 9, "bold"), fill='white')

        # "P" badge for passives (top-left)
        if node['type'] == 'passive' and state != 'locked':
            c.create_oval(cx-r-2, cy-r-2, cx-r+14, cy-r+14,
                          fill='#224466', outline='#335577')
            c.create_text(cx-r+6, cy-r+6, text='P',
                          font=("Arial", 7, "bold"), fill='#88ccff')

    # ── Interaction ────────────────────────────────────────────────────────
    def _node_at(self, ex, ey):
        for node in self.tree:
            nx, ny = self._node_coords.get(node['name'], (-999, -999))
            if math.hypot(ex - nx, ey - ny) <= self.NODE_R + 5:
                return node
        return None

    def _on_hover(self, event):
        node = self._node_at(event.x, event.y)
        if not node:
            self.info_label.config(
                text="Hover a node to see details.  Click an available node to unlock.")
            return
        state = self._node_state(node)
        _, reason = self.player.can_unlock_tree_skill(node['name'])
        kind  = "🗡 Active"  if node['type'] == 'active'  else "✨ Passive"
        cost  = f"{node['cost']} SP" if node['cost'] else "Free"
        prereq_str = ", ".join(node['prereq']) if node['prereq'] else "None"
        status_map = {
            'unlocked':  "✅ Unlocked",
            'available': f"🟢 Available — click to unlock ({cost})",
            'locked':    f"🔴 Locked  ({reason})",
        }
        self.info_label.config(
            text=f"{kind}  ▸  {node['name']}   [{status_map[state]}]\n"
                 f"{node['desc']}   |  Requires: {prereq_str}")

    def _on_click(self, event):
        node = self._node_at(event.x, event.y)
        if not node:
            return
        state = self._node_state(node)
        if state == 'unlocked':
            self.info_label.config(text=f"'{node['name']}' is already unlocked.")
            return
        if state == 'locked':
            _, reason = self.player.can_unlock_tree_skill(node['name'])
            self.info_label.config(text=f"🔴 Cannot unlock yet:  {reason}")
            return
        # Available — ask to confirm
        cost = node['cost']
        msg  = (f"Unlock  '{node['name']}'  for {cost} Skill Point(s)?\n\n"
                f"{node['desc']}\n\n"
                f"You currently have  {self.player.skill_points}  SP.")
        if tk.messagebox.askyesno("Unlock Skill", msg, parent=self.win):
            if self.player.unlock_tree_skill(node['name']):
                self._draw()
                self.sp_label.config(
                    text=f"Skill Points: {self.player.skill_points}")
                self.info_label.config(
                    text=f"✅ '{node['name']}' unlocked!   "
                         f"Remaining SP: {self.player.skill_points}")
                # Refresh the hotbar display immediately
                if hasattr(self.gf, 'refresh_active_skills'):
                    self.gf.refresh_active_skills()
            else:
                self.info_label.config(
                    text="Could not unlock — check SP or prerequisites.")


# ---------- GameFrame: playable game ----------
class GameFrame(tk.Frame):
    def __init__(self,parent,player,on_quit_to_menu,dungeon_id=1):
        super().__init__(parent, bg='black')
        self.parent = parent
        self.player = player
        self.on_quit_to_menu = on_quit_to_menu
        self.dungeon_id = dungeon_id
                # Camera system
        # Camera system
        self.camera_x = 0
        self.camera_y = 0

        # Interior system
        self.current_interior = None  # Which building player is inside

        # Interaction system
        self.nearby_npc = None
        self.nearby_dungeon = None

        # ── Layout ─────────────────────────────────────────────────────────────
        # Game canvas: fixed WINDOW_W × WINDOW_H — this is where the game renders.
        # Wrap it in a black frame so any space below WINDOW_H stays black (no white sliver).
        # Map canvas:  fills all remaining space to the right of the game canvas.
        # Clicking EITHER canvas fires the active skill.
        _cv_frame = tk.Frame(self, bg='black')
        _cv_frame.pack(side='left', fill='y')
        self.canvas = tk.Canvas(_cv_frame, width=WINDOW_W, height=WINDOW_H,
                                bg="black", highlightthickness=0)
        self.canvas.pack(side='top', anchor='nw')
        # Black filler covers any vertical gap below the fixed-size canvas
        tk.Frame(_cv_frame, bg='black').pack(side='top', fill='both', expand=True)

        self.map_canvas = tk.Canvas(self, bg='black', highlightthickness=0)
        self.map_canvas.pack(side='left', fill='both', expand=True)

        self.keys = {}
        self.room_row=0; self.room_col=0
        self.dungeon={}
        self.room=self.get_room(0,0)
        self.projectiles=[]; self.particles=[]
        self.mouse_pos=(WINDOW_W//2,WINDOW_H//2)
        self.show_stats=False
        self.show_help=False       # H key → help/tutorial overlay
        self._help_tab = 0         # which help tab is active (0-4)
        self.dead=False; self.respawn_time=0; self.respawn_delay=5
        self._combined_win = None   # track the combined inventory/skills window
        # ── Indoor room state ──────────────────────────────────────────────────
        self._outdoor_px = 0
        self._outdoor_py = 0
        self.current_interior_room = 0
        self._interior_layout_cache = {}   # building name → (walls, objects)
        self.bind("r", lambda e: self.rotate_beam(-2))   # rotate beam left
        self.bind("t", lambda e: self.rotate_beam(2))    # rotate beam right
        self.bind_all('<KeyPress>', self.on_key_down)
        self.bind_all('<KeyRelease>', self.on_key_up)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<Button-3>', self.on_right_click)
        self.canvas.bind('<Motion>', self.on_mouse_move)
        # Map canvas also fires skill on click (so clicking anywhere fires the skill)
        self.map_canvas.bind('<Button-1>', self.on_canvas_click)
        self.map_canvas.bind('<Button-3>', self.on_right_click)
        # Mouse position is polled each frame in loop() instead of using
        # a <Motion> event, which would flood the tkinter event queue and
        # cause severe lag.
        self.player = player
        self.summons = []
        self.player_spawn_row = 0
        self.player_spawn_col = 0
        self.player_spawn_x = WINDOW_W // 2
        self.player_spawn_y = WINDOW_H // 2
        self.player_beam = None  # player's beam
        self.beam_rotation_speed = 0.05  # radians per frame
        self.active_hotbar_slot = 1  # which slot (1-5) is selected
        # Item hotbar (3 slots for consumables, T/Y/U) — restore from saved data if available
        saved_hb = getattr(player, '_saved_hotbar', [None, None, None]) or [None, None, None]
        self.hotbar_items = []
        for slot_data in saved_hb:
            if slot_data is None:
                self.hotbar_items.append(None)
            elif slot_data.get('consumable'):
                self.hotbar_items.append(ConsumableItem.from_dict(slot_data))
            else:
                self.hotbar_items.append(InventoryItem.from_dict(slot_data))
        # Ensure exactly 3 slots
        while len(self.hotbar_items) < 3:
            self.hotbar_items.append(None)
        self.hotbar_items = self.hotbar_items[:3]
        self.active_item_slot = 0                # 0,1,2
        # Coin particles (world-space)
        self.coin_particles = []
        # Inventory UI state
        self._inv_win = None
        self._inv_selected = None     # slot key of selected item
        self._tooltip_text = ''


        self.last_time=time.time()
        self.after(16,self.loop)
    # In GameFrame.__init__(), add:
    def update_camera(self):
        """Camera follows player with tighter zoom"""
        if self.dungeon_id == 0:  # Town only
            # Camera tries to center on player with TIGHTER zoom
            target_camera_x = self.player.x - WINDOW_W // 2
            target_camera_y = self.player.y - WINDOW_H // 2
            
            # Much smoother camera movement (increased from 0.1 to 0.15)
            self.camera_x += (target_camera_x - self.camera_x) * 1
            self.camera_y += (target_camera_y - self.camera_y) * 1
    def poll_mouse_pos(self):
        """Poll mouse position once per frame — avoids flooding the event queue
        that <Motion> binding causes, which was making the game laggy."""
        try:
            cx = self.canvas.winfo_pointerx() - self.canvas.winfo_rootx()
            cy = self.canvas.winfo_pointery() - self.canvas.winfo_rooty()
            self.mouse_pos = (cx, cy)
        except Exception:
            pass  # keep last known position if winfo fails

    def get_mouse_world_pos(self):
        """Return mouse position in world coordinates.
        If Ranger has Eagle Eye: Auto-Aim toggled on, snaps to nearest enemy."""
        p = self.player
        if (p.class_name == 'Ranger'
                and 'Eagle Eye: Auto-Aim' in p.tree_unlocked
                and p.passive_toggles.get('Eagle Eye: Auto-Aim', True)
                and self.room.enemies):
            target = min(self.room.enemies,
                         key=lambda e: distance((p.x, p.y), (e.x, e.y)))
            return target.x, target.y
        mx, my = self.mouse_pos
        if self.dungeon_id == 0:
            return mx + self.camera_x, my + self.camera_y
        return mx, my

    def open_inventory(self):
        """Open inventory window"""
        inv_win = tk.Toplevel(self)
        inv_win.title("Inventory")
        inv_win.geometry("600x500")
        inv_win.configure(bg="#1a1a1a")
        
        # Coins display at the top
        coin_frame = tk.Frame(inv_win, bg="#2a2a2a")
        coin_frame.pack(fill='x', pady=10, padx=10)
        tk.Label(coin_frame, text=f"💰 Coins: {self.player.coins}", 
                font=("Arial", 16, "bold"), bg="#2a2a2a", fg="gold").pack()
        
        # Create scrollable frame
        canvas = tk.Canvas(inv_win, bg="#1a1a1a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(inv_win, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1a1a1a")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Display items
        if not self.player.inventory:
            tk.Label(scrollable_frame, text="Inventory is empty", 
                    font=("Arial", 14), bg="#1a1a1a", fg="gray").pack(pady=20)
        else:
            for item in self.player.inventory:
                item_frame = tk.Frame(scrollable_frame, bg="#2a2a2a", bd=2, relief="groove")
                item_frame.pack(fill='x', pady=5, padx=5)
                
                # Item name with rarity color
                name_text = item.name
                if item.soulbound:
                    name_text += " ⭐"  # Star indicator for soulbound
                name_label = tk.Label(item_frame, text=name_text, 
                                     font=("Arial", 14, "bold"),
                                     bg="#2a2a2a", fg=item.get_color())
                name_label.pack(anchor='w', padx=10, pady=5)
                
                # Item description
                desc_text = item.get_description()
                if item.soulbound:
                    desc_text += "\n[Soulbound: Stats apply even when unequipped]"
                desc_label = tk.Label(item_frame, text=desc_text,
                                     font=("Arial", 10), bg="#2a2a2a", fg="white",
                                     justify='left')
                desc_label.pack(anchor='w', padx=10, pady=2)
                
                # Button container
                button_frame = tk.Frame(item_frame, bg="#2a2a2a")
                button_frame.pack(side='right', padx=10, pady=5)
                
                # Equip/Unequip button (for ALL items including soulbound)
                is_equipped = item in self.player.equipped_items
                btn_text = "Unequip" if is_equipped else "Equip"
                btn_color = "#c9302c" if is_equipped else "#5cb85c"

                def make_equip_callback(itm):
                    def callback():
                        if itm in self.player.equipped_items:
                            self.player.unequip_item(itm)
                        else:
                            self.player.equip_item(itm)
                        inv_win.destroy()
                        self.open_inventory()
                    return callback

                equip_btn = tk.Button(button_frame, text=btn_text, bg=btn_color,
                                     fg="white", font=("Arial", 10, "bold"),
                                     command=make_equip_callback(item))
                equip_btn.pack(side='left', padx=5)

                # Sell button (only for non-soulbound items)
                if not item.soulbound:
                    sell_price = max(1, item.price // 2)
                    
                    def make_sell_callback(itm, price):
                        def callback():
                            self.player.coins += price
                            self.player.remove_item_from_inventory(itm)
                            inv_win.destroy()
                            self.open_inventory()
                        return callback
                    
                    sell_btn = tk.Button(button_frame, text=f"Sell ({sell_price}💰)",
                                        bg="#f0ad4e", fg="white",
                                        font=("Arial", 10, "bold"),
                                        command=make_sell_callback(item, sell_price))
                    sell_btn.pack(side='left', padx=5)

    # ─────────────────────────────────────────────────────────────────────────
    # GRID INVENTORY  (press I to open)
    # ─────────────────────────────────────────────────────────────────────────
    def open_grid_inventory(self):
        """Open grid inventory as standalone Toplevel (press I)."""
        # Toggle: close if already open
        if hasattr(self, '_inv_win') and self._inv_win:
            try:
                if self._inv_win.winfo_exists():
                    self._inv_win.destroy()
                    self._inv_win = None
                    return
            except Exception:
                pass

        win = tk.Toplevel(self)
        self._inv_win = win
        win.title("Inventory")
        win.resizable(False, False)
        win.configure(bg="#111122")
        win.protocol("WM_DELETE_WINDOW", lambda: self._close_inv_win())
        self._build_inv_canvas(win)

    def _build_inv_canvas(self, container_win):
        """Build the canvas-based grid inventory inside container_win (Toplevel or Frame)."""
        win = container_win   # alias so inner closures still work

        # ── Layout constants ──────────────────────────────────────────────────
        SLOT     = 58       # cell size in px
        GAP      = 4        # gap between cells
        STEP     = SLOT + GAP
        EQ_COLS  = 1        # equipment panel is 1 column wide
        GRID_C   = 4        # main bag is 4×4
        GRID_R   = 4

        C_BG     = "#0e0e1c"
        C_PANEL  = "#16162a"
        C_SLOT   = "#3a3a5a"   # empty slot — medium-dark so it's clearly distinct from items
        C_SEL    = "#8888dd"   # selected slot
        C_BORDER = "#6666bb"
        C_TEXT   = "#e8e8ff"   # bright label text
        # Slot backgrounds when OCCUPIED — bright enough that dark emoji stands out
        TYPE_BG = {
            'weapon':     '#7a3535',   # warm red
            'helmet':     '#2a4a70',   # steel blue
            'chestplate': '#2a4a70',
            'leggings':   '#2a4a70',
            'boots':      '#2a4a70',
            'gloves':     '#2a4a70',
            'ring':       '#5a2a7a',   # purple
            'necklace':   '#5a2a7a',
            'consumable': '#2a6a2a',   # green
            'default':    '#404060',
        }

        # Equipment slot definitions (left column)
        EQ_SLOTS = [
            ("weapon",     "⚔️",  "Weapon"),
            ("helmet",     "🪖",  "Helmet"),
            ("chestplate", "🛡",   "Chestplate"),
            ("leggings",   "👖",  "Leggings"),
            ("boots",      "👢",  "Boots"),
            ("gloves",     "🧤",  "Gloves"),
            ("ring",       "💍",  "Ring"),
            ("necklace",   "📿",  "Necklace"),
            ("map",        "📜",  "Map"),
        ]
        N_EQ = len(EQ_SLOTS)

        # Canvas size
        EQ_W  = STEP + GAP + 80          # equipment label column
        BAG_W = GRID_C * STEP + GAP
        HB_W  = (1 + 3) * STEP + GAP     # weapon slot + 3 item slots
        WIN_W = EQ_W + GAP*2 + BAG_W + 20
        TOP   = 36                        # space for coin/stat bar at top
        WIN_H = max(N_EQ * STEP + 120, GRID_R * STEP + 220) + TOP

        is_toplevel = hasattr(win, 'geometry')   # False when embedded in a notebook tab

        if is_toplevel:
            win.geometry(f"{WIN_W}x{WIN_H+60}")

        # ── Top info bar (standalone only) ────────────────────────────────────
        top = None
        if is_toplevel:
            top = tk.Frame(win, bg=C_PANEL)
            top.pack(fill='x')
            tk.Label(top, text=f"💰  {self.player.coins} coins",
                     bg=C_PANEL, fg="#FFD700", font=("Arial",11,"bold")).pack(side='left',padx=10,pady=6)
            tk.Label(top, text=f"🗡  {self.player.name}  Lv {self.player.level}  |  "
                               f"HP {int(self.player.hp)}/{int(self.player.max_hp)}",
                     bg=C_PANEL, fg=C_TEXT, font=("Arial",10)).pack(side='left',padx=8)

        # ── Main canvas ───────────────────────────────────────────────────────
        cv = tk.Canvas(win, width=WIN_W, height=WIN_H,
                       bg=C_BG, highlightthickness=0)
        cv.pack(fill='both', expand=True)

        # ── Tooltip label (attached to the real top-level window) ─────────────
        _tip_root = win if is_toplevel else win.winfo_toplevel()
        tip_var = tk.StringVar()
        tip_lbl = tk.Label(_tip_root, textvariable=tip_var,
                           bg="#222244", fg="white",
                           font=("Arial",9), justify='left',
                           relief='solid', bd=1, wraplength=240)
        tip_lbl.place_forget()

        # State
        selected_key  = [None]   # ('eq', slot_type) | ('bag', index) | ('hb', index)
        hover_key     = [None]

        # ── Helpers ───────────────────────────────────────────────────────────
        def item_emoji(item):
            if item is None:
                return ""
            if hasattr(item, 'get_emoji'):          # ConsumableItem
                return item.get_emoji()
            TYPE_EMOJI = {
                'weapon':     "⚔️",  'helmet':     "🪖",
                'chestplate': '🛡',  'leggings':   "👖",
                'boots':      "👢",  'gloves':     "🧤",
                'ring':       "💍",  'necklace':   "📿",
                'consumable': "🧪",
            }
            wtype_emoji = {
                'bow': "🏹", 'staff': "🪄", 'dagger': "🗡",
                'wand': "🪄", 'spear': "🔱", 'scythe': "⚔️",
            }
            wt = getattr(item, 'weapon_type', None)
            if wt and wt in wtype_emoji:
                return wtype_emoji[wt]
            return TYPE_EMOJI.get(item.item_type, "📦")

        def item_color(item):
            if item is None: return C_TEXT
            # Brighter versions of rarity colours for readability on dark slots
            BRIGHT = {
                '#9d9d9d': '#d0d0d0',   # Common → light grey
                '#1eff00': '#88ff66',   # Uncommon → bright green
                '#0070dd': '#55aaff',   # Rare → bright blue
                '#a335ee': '#dd88ff',   # Epic → bright purple
                '#ff8000': '#ffaa44',   # Legendary → bright orange
                '#ffffff': '#ffffff',
            }
            base = item.get_color()
            return BRIGHT.get(base, base)

        def slot_bg(item):
            """Tinted background for occupied slots, darker for empty."""
            if item is None: return C_SLOT
            return TYPE_BG.get(getattr(item,'item_type','default'), TYPE_BG['default'])

        def draw_item_icon(cx, cy, item, size=20):
            """Draw a bright rarity-colour disc + emoji centred at (cx,cy).
            On Windows, tkinter ignores fill= for emoji so the disc is the
            primary visual indicator that the slot is occupied."""
            col = item_color(item)
            r = size // 2 + 5
            # Glow ring
            cv.create_oval(cx-r-2, cy-r-2, cx+r+2, cy+r+2,
                           fill='', outline=col, width=2)
            # Solid disc
            cv.create_oval(cx-r, cy-r, cx+r, cy+r, fill=col, outline='')
            # Emoji centred exactly on disc
            cv.create_text(cx, cy, text=item_emoji(item),
                           font=("Arial", size), anchor='center')
            # Stack count badge bottom-right
            cnt = getattr(item,'count',1)
            if cnt > 1:
                bx, by = cx+r-2, cy+r-2
                cv.create_oval(bx-8, by-8, bx+8, by+8, fill='#111122', outline='')
                cv.create_text(bx, by, text=str(cnt), fill='white',
                               font=('Arial',7,'bold'), anchor='center')

        def get_eq_item(slot_type):
            """Return equipped item for a slot type, or None."""
            if slot_type == 'weapon':
                for it in self.player.inventory:
                    if it in self.player.equipped_items and it.item_type == 'weapon':
                        return it
                return None
            for it in self.player.equipped_items:
                if it.item_type == slot_type:
                    return it
            return None

        def bag_items():
            """Return list of non-equipped, non-consumable inventory items (up to 16)."""
            result = []
            for it in self.player.inventory:
                if it not in self.player.equipped_items:
                    result.append(it)
            return result[:GRID_C * GRID_R]

        def slot_rect(key):
            """Return (x0,y0,x1,y1) for a given slot key."""
            if key[0] == 'eq':
                idx = next(i for i,(t,_,_) in enumerate(EQ_SLOTS) if t == key[1])
                x0 = GAP
                y0 = TOP + GAP + idx * STEP
                return x0, y0, x0+SLOT, y0+SLOT
            elif key[0] == 'bag':
                idx = key[1]
                col = idx % GRID_C
                row = idx // GRID_C
                x0 = EQ_W + GAP + col * STEP
                y0 = TOP + GAP + row * STEP
                return x0, y0, x0+SLOT, y0+SLOT
            elif key[0] == 'hb':
                idx = key[1]
                x0 = EQ_W + GAP + idx * STEP
                y0 = TOP + GAP + GRID_R * STEP + GAP*3 + 28
                return x0, y0, x0+SLOT, y0+SLOT
            elif key[0] == 'wep':
                x0 = EQ_W + GAP
                y0 = TOP + GAP + GRID_R * STEP + GAP*3 + 28
                return x0, y0, x0+SLOT, y0+SLOT
            return 0,0,0,0

        def get_item_at(key):
            if key[0] == 'eq':
                return get_eq_item(key[1])
            elif key[0] == 'bag':
                items = bag_items()
                return items[key[1]] if key[1] < len(items) else None
            elif key[0] == 'hb':
                return self.hotbar_items[key[1]]
            elif key[0] == 'wep':
                return get_eq_item('weapon')
            return None

        def tooltip_text(item):
            if item is None: return ""
            cnt = getattr(item,'count',1)
            name_line = f"{item.name}" + (f"  (x{cnt})" if cnt > 1 else "")
            lines = [name_line,
                     f"[{item.rarity}]  {item.item_type.capitalize()}"]
            desc = item.get_description()
            if desc:
                lines.append(desc)
            if getattr(item,'soulbound',False):
                lines.append("★ Soulbound")
            return "\n".join(lines)

        # ── Draw ─────────────────────────────────────────────────────────────
        def redraw():
            cv.delete('all')

            # Left panel background
            cv.create_rectangle(0, 0, EQ_W, WIN_H, fill=C_PANEL, outline='')

            # ── Top stat/coin bar (always visible even when embedded) ───────
            cv.create_rectangle(0, 0, WIN_W, TOP, fill='#0d0d20', outline='')
            cv.create_line(0, TOP, WIN_W, TOP, fill='#444466', width=1)
            shld_txt = (f'  🛡 {int(self.player.shield)}/{int(self.player.max_shield)}'
                        if self.player.max_shield else '')
            cv.create_text(8, TOP//2, anchor='w',
                           text=f'💰 {self.player.coins} coins   '
                                f'❤ {int(self.player.hp)}/{int(self.player.max_hp)}{shld_txt}   '
                                f'Lv {self.player.level}',
                           fill='#e8e8ff', font=('Arial', 9, 'bold'))

            # Section label for bag only (EQUIPMENT label removed — it overlapped slots)
            cv.create_text(EQ_W + GAP + BAG_W//2 - GAP, TOP + GAP//2, text="BAG  (4×4)",
                           fill="#aaaadd", font=("Arial",8,"bold"), anchor='n')

            # ── Equipment slots ───────────────────────────────────────────────
            for i, (slot_type, icon, label) in enumerate(EQ_SLOTS):
                key = ('eq', slot_type)
                x0, y0, x1, y1 = slot_rect(key)
                item = get_eq_item(slot_type)
                sel  = selected_key[0] == key
                bg_  = C_SEL if sel else slot_bg(item)
                border_col = '#aaaaee' if sel else ('#7777bb' if item else C_BORDER)
                cv.create_rectangle(x0, y0, x1, y1, fill=bg_, outline=border_col, width=2)
                if item:
                    draw_item_icon((x0+x1)//2, (y0+y1)//2, item, size=20)
                    short = item.name[:9]+"…" if len(item.name)>10 else item.name
                    cv.create_text((x0+x1)//2, y1-7,
                                   text=short, fill='white',
                                   font=("Arial",7,"bold"))
                else:
                    cv.create_text((x0+x1)//2, (y0+y1)//2,
                                   text=icon, font=("Arial",22), fill="#8888aa")
                # Label on the right of slot
                cv.create_text(x1+6, (y0+y1)//2,
                               text=label, fill="#ccccee",
                               font=("Arial",9,"bold"), anchor='w')

            # ── Bag grid ─────────────────────────────────────────────────────
            items_in_bag = bag_items()
            for idx in range(GRID_C * GRID_R):
                key = ('bag', idx)
                x0, y0, x1, y1 = slot_rect(key)
                item = items_in_bag[idx] if idx < len(items_in_bag) else None
                sel  = selected_key[0] == key
                bg_  = C_SEL if sel else slot_bg(item)
                border_col = '#aaaaee' if sel else ('#666699' if item else '#3a3a5a')
                cv.create_rectangle(x0, y0, x1, y1, fill=bg_, outline=border_col, width=1)
                if item:
                    draw_item_icon((x0+x1)//2, (y0+y1)//2, item, size=20)
                    short = item.name[:9]+"…" if len(item.name)>10 else item.name
                    cv.create_text((x0+x1)//2, y1-7,
                                   text=short, fill='white',
                                   font=("Arial",7,"bold"))

            # ── Hotbar row (at bottom of bag panel) ───────────────────────────
            hb_y = TOP + GAP + GRID_R * STEP + GAP*3
            cv.create_text(EQ_W + GAP + BAG_W//2 - GAP, hb_y,
                           text="HOTBAR  (T / Y / U)  —  right-click in game to use",
                           fill="#8888aa", font=("Arial",8), anchor='w')

            # Weapon slot (far-left of hotbar, key 'wep')
            wkey = ('wep', 0)
            x0, y0, x1, y1 = slot_rect(wkey)
            weap = get_eq_item('weapon')
            sel  = selected_key[0] == wkey
            bg_  = C_SEL if sel else "#2a1a2e"
            cv.create_rectangle(x0, y0, x1, y1, fill=bg_, outline="#884488", width=2)
            cv.create_text((x0+x1)//2, y0-4, text="WEP", fill="#aa66aa",
                           font=("Arial",7,"bold"), anchor='s')
            if weap:
                draw_item_icon((x0+x1)//2, (y0+y1)//2, weap, size=20)
                short = weap.name[:7]+"…" if len(weap.name)>8 else weap.name
                cv.create_text((x0+x1)//2, y1-9,
                               text=short, fill='white', font=("Arial",6,"bold"))
                if getattr(weap,'soulbound',False):
                    cv.create_text((x0+x1)//2, y0+8, text="★",
                                   fill="#FFD700", font=("Arial",9))
            else:
                cv.create_text((x0+x1)//2, (y0+y1)//2, text="⚔️",
                               font=("Arial",22), fill="#9988aa")

            for i in range(3):
                key = ('hb', i)
                x0, y0, x1, y1 = slot_rect(key)
                # Offset: hotbar slots go right of weapon slot
                x0 += STEP; x1 += STEP
                item = self.hotbar_items[i]
                sel  = selected_key[0] == key
                active = (i == self.active_item_slot)
                base_bg = slot_bg(item) if item else C_SLOT
                if active: base_bg = '#3a3a7c'
                bg_  = C_SEL if sel else base_bg
                out_ = '#ffffff' if active else ('#aaaaff' if sel else '#5555aa')
                cv.create_rectangle(x0, y0, x1, y1, fill=bg_, outline=out_, width=2 if active else 1)
                lbl = ['T','Y','U'][i]
                cv.create_text(x0+8, y0+8, text=lbl, fill='#ffffff' if active else '#aaaadd',
                               font=("Arial",8,"bold"))
                if item:
                    draw_item_icon((x0+x1)//2, (y0+y1)//2, item, size=20)
                    short = item.name[:7]+"…" if len(item.name)>8 else item.name
                    cv.create_text((x0+x1)//2, y1-9, text=short,
                                   fill='white', font=("Arial",7,"bold"))

            # Selection hint
            if selected_key[0]:
                cv.create_text(WIN_W//2, WIN_H-14,
                               text="Click another slot to move  |  Right-click to unequip/remove",
                               fill="#9999cc", font=("Arial",8))
            else:
                cv.create_text(WIN_W//2, WIN_H-14,
                               text="Click a slot to select  |  O or I to close",
                               fill="#777799", font=("Arial",8))

        # ── Hit-testing ───────────────────────────────────────────────────────
        def key_at(mx, my):
            # Equipment slots
            for i, (slot_type,_,_) in enumerate(EQ_SLOTS):
                key = ('eq', slot_type)
                x0,y0,x1,y1 = slot_rect(key)
                if x0<=mx<=x1 and y0<=my<=y1:
                    return key
            # Bag slots
            for idx in range(GRID_C*GRID_R):
                key = ('bag', idx)
                x0,y0,x1,y1 = slot_rect(key)
                if x0<=mx<=x1 and y0<=my<=y1:
                    return key
            # Weapon hotbar slot
            x0,y0,x1,y1 = slot_rect(('wep',0))
            if x0<=mx<=x1 and y0<=my<=y1:
                return ('wep',0)
            # Item hotbar slots (offset by STEP because of wep slot)
            for i in range(3):
                key = ('hb', i)
                x0,y0,x1,y1 = slot_rect(key)
                x0+=STEP; x1+=STEP
                if x0<=mx<=x1 and y0<=my<=y1:
                    return key
            return None

        # ── Click handler ─────────────────────────────────────────────────────
        def on_click(event):
            key = key_at(event.x, event.y)
            if key is None:
                selected_key[0] = None
                redraw(); return

            prev = selected_key[0]

            # No selection yet — select this slot (if it has an item)
            if prev is None:
                if get_item_at(key) is not None:
                    selected_key[0] = key
                redraw(); return

            # Same slot clicked — deselect
            if prev == key:
                selected_key[0] = None
                redraw(); return

            # Try to move/equip/swap between slots
            src_item = get_item_at(prev)
            dst_item = get_item_at(key)

            if src_item is None:
                selected_key[0] = None
                redraw(); return

            moved = try_move(prev, key, src_item, dst_item)
            selected_key[0] = None
            redraw()

        def try_move(src, dst, src_item, dst_item):
            """Move src_item into dst slot.  Returns True on success."""
            src_type, dst_type = src[0], dst[0]

            # ── bag → equipment slot ─────────────────────────────────────────
            if src_type == 'bag' and dst_type == 'eq':
                needed = dst[1]
                if src_item.item_type == needed or (needed=='weapon' and src_item.item_type=='weapon'):
                    if dst_item:
                        self.player.unequip_item(dst_item)
                    self.player.equip_item(src_item)
                    return True
            # ── equipment slot → bag ─────────────────────────────────────────
            elif src_type == 'eq' and dst_type == 'bag':
                self.player.unequip_item(src_item)
                return True
            # ── bag → hotbar ─────────────────────────────────────────────────
            elif src_type == 'bag' and dst_type == 'hb':
                if isinstance(src_item, ConsumableItem):
                    existing = self.hotbar_items[dst[1]]
                    if existing is not None and existing.name == src_item.name:
                        existing.count += src_item.count
                        self.player.remove_item_from_inventory(src_item)
                    else:
                        self.hotbar_items[dst[1]] = src_item
                        self.player.remove_item_from_inventory(src_item)
                    return True
            # ── hotbar → bag ─────────────────────────────────────────────────
            elif src_type == 'hb' and dst_type == 'bag':
                if dst_item is None:
                    self.player.add_item_to_inventory(src_item)
                    self.hotbar_items[src[1]] = None
                    return True
            # ── hotbar → hotbar ───────────────────────────────────────────────
            elif src_type == 'hb' and dst_type == 'hb':
                self.hotbar_items[src[1]], self.hotbar_items[dst[1]] = \
                    self.hotbar_items[dst[1]], self.hotbar_items[src[1]]
                return True
            # ── bag → bag ────────────────────────────────────────────────────
            elif src_type == 'bag' and dst_type == 'bag':
                items = [it for it in self.player.inventory
                         if it not in self.player.equipped_items]
                # Just re-order in player.inventory via remove/insert logic
                if src_item in self.player.inventory:
                    self.player.inventory.remove(src_item)
                    if dst_item and dst_item in self.player.inventory:
                        idx = self.player.inventory.index(dst_item)
                        self.player.inventory.insert(idx, src_item)
                    else:
                        self.player.inventory.append(src_item)
                return True
            # ── wep slot → bag ───────────────────────────────────────────────
            elif src_type == 'wep' and dst_type == 'bag':
                if not getattr(src_item,'soulbound',False):
                    self.player.unequip_item(src_item)
                    return True
            # ── bag → wep slot ───────────────────────────────────────────────
            elif src_type == 'bag' and dst_type == 'wep':
                if src_item.item_type == 'weapon':
                    if dst_item and not getattr(dst_item,'soulbound',False):
                        self.player.unequip_item(dst_item)
                    self.player.equip_item(src_item)
                    return True
            return False

        def on_right_click_inv(event):
            key = key_at(event.x, event.y)
            if key is None: return
            item = get_item_at(key)
            if item is None: return
            ktype = key[0]
            if ktype == 'eq':
                if not getattr(item,'soulbound',False):
                    self.player.unequip_item(item)
            elif ktype == 'hb':
                self.hotbar_items[key[1]] = None
            elif ktype == 'wep':
                if not getattr(item,'soulbound',False):
                    self.player.unequip_item(item)
            selected_key[0] = None
            redraw()

        # ── Hover tooltip ─────────────────────────────────────────────────────
        def on_motion(event):
            key = key_at(event.x, event.y)   # may be None if cursor not over a slot
            if key != hover_key[0]:
                hover_key[0] = key
                item = get_item_at(key) if key is not None else None
                if item:
                    tip_var.set(tooltip_text(item))
                    tip_lbl.place(x=event.x+12, y=event.y+12)
                else:
                    tip_lbl.place_forget()
            else:
                # Keep tooltip positioned under cursor while still on same slot
                if hover_key[0] is not None and get_item_at(hover_key[0]):
                    tip_lbl.place(x=event.x+12, y=event.y+12)

        def on_leave(event):
            tip_lbl.place_forget()
            hover_key[0] = None

        cv.bind('<Button-1>', on_click)
        cv.bind('<Button-3>', on_right_click_inv)
        cv.bind('<Motion>',   on_motion)
        cv.bind('<Leave>',    on_leave)

        redraw()

        # Refresh every 500 ms so equipped items, coins etc. stay current
        def periodic_refresh():
            try:
                if win.winfo_exists():
                    # Update top bar (standalone window only)
                    if top is not None:
                        for w in top.winfo_children():
                            w.destroy()
                        shld = (f'  |  🛡 {int(self.player.shield)}/{int(self.player.max_shield)}'
                                if self.player.max_shield else '')
                        tk.Label(top, text=f"💰  {self.player.coins} coins",
                                 bg=C_PANEL, fg="#FFD700",
                                 font=("Arial",11,"bold")).pack(side='left',padx=10,pady=6)
                        tk.Label(top,
                                 text=f"🗡  {self.player.name}  Lv {self.player.level}  |  "
                                      f"HP {int(self.player.hp)}/{int(self.player.max_hp)}{shld}",
                                 bg=C_PANEL, fg=C_TEXT,
                                 font=("Arial",10)).pack(side='left',padx=8)
                    redraw()
                    win.after(500, periodic_refresh)
            except Exception:
                pass

        win.after(500, periodic_refresh)

    def _close_inv_win(self):
        if self._inv_win:
            try:
                self._inv_win.destroy()
            except Exception:
                pass
            self._inv_win = None

    def rotate_beam(self, delta_angle):
        if hasattr(self, "player_beam") and self.player_beam:
            self.player_beam.rotate(delta_angle)
    def interact_with_npc(self, npc):
        """Open shop window for NPC"""
        shop_win = tk.Toplevel(self)
        shop_win.title(f"{npc.name}'s Shop")
        shop_win.geometry("700x600")
        shop_win.configure(bg="#1a1a1a")

        # Track that a shop is open so dungeon entry is blocked while buying
        self._npc_shop_open = True
        def _close_shop(event=None):
            self._npc_shop_open = False
            try:
                shop_win.destroy()
            except Exception:
                pass
        shop_win.protocol("WM_DELETE_WINDOW", _close_shop)
        # Bind any keypress on the MAIN window to close the shop
        _close_bind_id = self.bind("<Key>", lambda e: _close_shop(), add=True)
        # Also close if a key is pressed while the shop window itself has focus
        shop_win.bind("<Key>", lambda e: _close_shop())
        # Clean up binding when shop is destroyed
        def _on_shop_destroy(event=None):
            self._npc_shop_open = False
            try:
                self.unbind("<Key>", _close_bind_id)
            except Exception:
                pass
        shop_win.bind("<Destroy>", _on_shop_destroy)

        # Hint at bottom
        tk.Label(shop_win, text="Press any key to close shop",
                 bg="#1a1a1a", fg="#555555", font=("Arial", 9, "italic")).pack(side='bottom', pady=4)

        # Coins display
        coin_frame = tk.Frame(shop_win, bg="#2a2a2a")
        coin_frame.pack(fill='x', pady=10, padx=10)
        
        def update_coins():
            for widget in coin_frame.winfo_children():
                widget.destroy()
            tk.Label(coin_frame, text=f"💰 Your Coins: {self.player.coins}", 
                    font=("Arial", 16, "bold"), bg="#2a2a2a", fg="gold").pack()
        
        update_coins()
        
        # Shop items
        canvas = tk.Canvas(shop_win, bg="#1a1a1a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(shop_win, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1a1a1a")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Display NPC's items
        if not npc.shop_items:
            tk.Label(scrollable_frame, text=f"{npc.name} has nothing to sell right now.", 
                    font=("Arial", 14), bg="#1a1a1a", fg="gray").pack(pady=20)
        else:
            for item in npc.shop_items:
                item_frame = tk.Frame(scrollable_frame, bg="#2a2a2a", bd=2, relief="groove")
                item_frame.pack(fill='x', pady=5, padx=5)
                
                # Item info
                name_label = tk.Label(item_frame, text=item.name, 
                                     font=("Arial", 14, "bold"),
                                     bg="#2a2a2a", fg=item.get_color())
                name_label.pack(anchor='w', padx=10, pady=5)
                
                desc_label = tk.Label(item_frame, text=item.get_description(),
                                     font=("Arial", 10), bg="#2a2a2a", fg="white",
                                     justify='left')
                desc_label.pack(anchor='w', padx=10, pady=2)
                
                # Buy button
                def make_buy_callback(shop_item):
                    def callback():
                        if self.player.coins < shop_item.price:
                            import tkinter.messagebox as mb
                            mb.showwarning('Not Enough Coins',
                                f'You need {shop_item.price} coins but only have {self.player.coins}')
                            return
                        self.player.coins -= shop_item.price
                        # Consumables: stack if same item exists, else place fresh
                        if isinstance(shop_item, ConsumableItem):
                            # 1) stack onto matching hotbar slot
                            stacked = False
                            for idx in range(3):
                                hb = self.hotbar_items[idx]
                                if hb is not None and hb.name == shop_item.name:
                                    hb.count += 1
                                    stacked = True; break
                            if not stacked:
                                # 2) stack onto matching bag item
                                for it in self.player.inventory:
                                    if isinstance(it, ConsumableItem) and it.name == shop_item.name:
                                        it.count += 1
                                        stacked = True; break
                            if not stacked:
                                # 3) empty hotbar slot
                                placed = False
                                for idx in range(3):
                                    if self.hotbar_items[idx] is None:
                                        new_c = ConsumableItem.from_dict(shop_item.to_dict())
                                        new_c.count = 1
                                        self.hotbar_items[idx] = new_c
                                        placed = True; break
                                if not placed:
                                    # 4) bag
                                    new_c = ConsumableItem.from_dict(shop_item.to_dict())
                                    new_c.count = 1
                                    self.player.add_item_to_inventory(new_c)
                        else:
                            new_item = InventoryItem(
                                name=shop_item.name,
                                item_type=shop_item.item_type,
                                rarity=shop_item.rarity,
                                stats=shop_item.stats.copy(),
                                skills=shop_item.skills.copy(),
                                soulbound=False,
                                price=shop_item.price,
                                weapon_type=getattr(shop_item, 'weapon_type', None)
                            )
                            self.player.add_item_to_inventory(new_item)
                        update_coins()
                    return callback
                
                buy_btn = tk.Button(item_frame, text=f"Buy\n{item.price} 💰",
                                   bg='#5cb85c', fg='white',
                                   font=("Arial", 11, "bold"),
                                   command=make_buy_callback(item),
                                   width=8)
                buy_btn.pack(side='right', padx=10, pady=10)

    def enter_dungeon(self, dungeon_id):
        """Switch from town to dungeon"""
        print(f"DEBUG: Attempting to enter dungeon {dungeon_id}")
        
        self.dungeon_id = dungeon_id
        print(f"DEBUG: self.dungeon_id set to {self.dungeon_id}")
        
        self.room_row = 0
        self.room_col = 0
        self.dungeon = {}
        self.room = self.get_room(0, 0)
        
        print(f"DEBUG: Room created with dungeon_id = {self.room.row}, is_town = {getattr(self.room, 'is_town', False)}")
        print(f"DEBUG: Room has {len(self.room.enemies)} enemies")
        
        self.player.x = WINDOW_W // 2
        self.player.y = WINDOW_H // 2
        
        self.projectiles.clear()
        self.particles.clear()
        
        self.camera_x = 0
        self.camera_y = 0
        # Refresh item-granted skills so soulbound/equipped item skills persist
        self.player.update_equipped_skills()
    def toggle_combined_page(self):
        """Open the combined window, or close it if already open (toggle)."""
        if self._combined_win is not None:
            try:
                if self._combined_win.winfo_exists():
                    self._combined_win.destroy()
                    self._combined_win = None
                    return
            except Exception:
                pass
        self.open_combined_skill_page()

    def open_combined_skill_page(self):
        """Open a single tabbed window: Inventory + Skill Tree + Skill Management."""
        win = tk.Toplevel(self)
        self._combined_win = win
        win.title("Inventory & Skills")
        win.geometry("920x720")
        win.configure(bg="#0d0d1a")

        def on_win_close():
            self._combined_win = None
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", on_win_close)

        notebook = ttk.Notebook(win)
        notebook.pack(fill='both', expand=True, padx=6, pady=6)

        # ── Tab 1: Inventory (grid) ──────────────────────────────────────────
        inv_tab = tk.Frame(notebook, bg="#0e0e1c")
        notebook.add(inv_tab, text="  🎒  Inventory  ")
        self._build_inv_canvas(inv_tab)
        self._inv_tab_frame = inv_tab  # keep ref so we can rebuild on tab switch

        # ── Tab 2: Skill Tree ─────────────────────────────────────────────────
        tree_tab = tk.Frame(notebook, bg="#0d0d1a")
        notebook.add(tree_tab, text="  🌿  Skill Tree  ")
        stw = SkillTreeWindow.embed_in_frame(tree_tab, self, self.player, win)

        # ── Tab 3: Skill Management ───────────────────────────────────────────
        mgmt_tab = tk.Frame(notebook, bg="#2a2a2a")
        notebook.add(mgmt_tab, text="  ⌨  Skill Management  ")

        active_box = tk.Frame(mgmt_tab, bg="#2a2a2a")
        active_box.pack(pady=10, padx=15, fill="x")
        tk.Label(active_box, text="Active Skills (Hotbar Slots 1-5)",
                 font=("Arial", 14, "bold"), bg="#2a2a2a", fg="#b0b0b0").pack(pady=5)
        self.active_frame = tk.Frame(active_box, bg="#2a2a2a")
        self.active_frame.pack(pady=5, fill="x")
        self.refresh_active_skills()

        tk.Frame(mgmt_tab, bg="#333333", height=2).pack(fill="x", pady=8)

        # ── Passive toggle section ────────────────────────────────────────────
        passive_box = tk.Frame(mgmt_tab, bg="#2a2a2a")
        passive_box.pack(pady=4, padx=15, fill="x")
        tk.Label(passive_box, text="Passive Skills (Toggle On/Off)",
                 font=("Arial", 14, "bold"), bg="#2a2a2a", fg="#b0b0b0").pack(pady=5)
        passive_inner = tk.Frame(passive_box, bg="#2a2a2a")
        passive_inner.pack(fill="x")

        def rebuild_passive_toggles():
            for w in passive_inner.winfo_children(): w.destroy()
            tree = SKILL_TREES.get(self.player.class_name, [])
            passives = [n for n in tree if n['type'] == 'passive'
                        and n['name'] in self.player.tree_unlocked]
            if not passives:
                tk.Label(passive_inner, text="No passive skills unlocked yet.",
                         font=("Arial", 10, "italic"), bg="#2a2a2a", fg="#666666").pack()
                return
            for node in passives:
                pname = node['name']
                is_on = self.player.passive_toggles.get(pname, True)
                row = tk.Frame(passive_inner, bg="#3a3a3a", padx=8, pady=6)
                row.pack(fill="x", pady=3)
                tk.Label(row, text=pname, font=("Arial", 11, "bold"),
                         bg="#3a3a3a", fg="#b0b0b0", width=22,
                         anchor="w").pack(side="left")
                tk.Label(row, text=node['desc'], font=("Arial", 8),
                         bg="#3a3a3a", fg="#888888",
                         wraplength=300, justify="left").pack(side="left", padx=8)
                def make_toggle(name):
                    def toggle():
                        cur = self.player.passive_toggles.get(name, True)
                        self.player.passive_toggles[name] = not cur
                        rebuild_passive_toggles()
                    return toggle
                btn_text = "ON" if is_on else "OFF"
                btn_col  = "#2a7a2a" if is_on else "#7a2a2a"
                tk.Button(row, text=btn_text, bg=btn_col, fg="white",
                          font=("Arial", 10, "bold"), width=5,
                          command=make_toggle(pname)).pack(side="right")

        rebuild_passive_toggles()

        tk.Frame(mgmt_tab, bg="#333333", height=2).pack(fill="x", pady=8)

        # ── Unlocked active skills (scrollable) ───────────────────────────────
        unlocked_box = tk.Frame(mgmt_tab, bg="#2a2a2a")
        unlocked_box.pack(pady=4, padx=15, fill="both", expand=True)
        tk.Label(unlocked_box, text="Active Skills (Assign to Slot)",
                 font=("Arial", 14, "bold"), bg="#2a2a2a", fg="#b0b0b0").pack(pady=5)

        sc2 = tk.Canvas(unlocked_box, bg="#2a2a2a", highlightthickness=0)
        sb2 = tk.Scrollbar(unlocked_box, orient="vertical", command=sc2.yview)
        sf2_holder = [None]  # mutable ref so rebuild_skills can swap the frame

        def rebuild_skills_list():
            if sf2_holder[0]:
                sf2_holder[0].destroy()
            sf2 = tk.Frame(sc2, bg="#2a2a2a")
            sf2_holder[0] = sf2
            sf2.bind("<Configure>", lambda e: sc2.configure(scrollregion=sc2.bbox("all")))
            sc2.create_window((0, 0), window=sf2, anchor="nw")
            active_skills = [sk for sk in self.player.unlocked_skills
                             if sk.get('type', 'active') != 'passive']
            for i, sk in enumerate(active_skills):
                row = tk.Frame(sf2, bg="#3a3a3a", padx=10, pady=10)
                row.grid(row=i//2, column=i % 2, padx=10, pady=10, sticky="nsew")
                tk.Label(row, text=sk['name'], anchor="center",
                         font=("Arial", 11, "bold"), bg="#3a3a3a",
                         fg="#b0b0b0").pack(fill="x", pady=(0, 5))
                bf = tk.Frame(row, bg="#3a3a3a")
                bf.pack()
                for slot in range(1, 6):
                    tk.Button(bf, text=str(slot), width=3,
                              font=("Arial", 10, "bold"),
                              bg="#4a4a4a", fg="#b0b0b0",
                              activebackground="#5a5a5a",
                              command=lambda s=slot, skill=sk: (
                                  self.assign_skill(skill, s),
                                  rebuild_skills_list()
                              )).pack(side="left", padx=2)
            sf2.grid_columnconfigure(0, weight=1)
            sf2.grid_columnconfigure(1, weight=1)

        rebuild_skills_list()
        sc2.configure(yscrollcommand=sb2.set)
        sc2.pack(side="left", fill="both", expand=True)
        sb2.pack(side="right", fill="y")

        # ── Tab change handler — refreshes every tab on switch ────────────────
        def on_tab_changed(event):
            sel  = notebook.select()
            tabs = notebook.tabs()
            if sel == tabs[0]:   # Inventory — rebuild if soulbound evolved
                if getattr(self.player, '_soulbound_evolved', False):
                    for w in inv_tab.winfo_children(): w.destroy()
                    self._build_inv_canvas(inv_tab)
                    self.player._soulbound_evolved = False
            elif sel == tabs[1]:   # Skill Tree
                stw._draw()
                stw.sp_label.config(text=f"Skill Points: {self.player.skill_points}")
            elif sel == tabs[2]:  # Skill Management — always rebuild so new skills show up
                self.refresh_active_skills()
                rebuild_skills_list()
                rebuild_passive_toggles()
        notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

        # ── Live-refresh loop for Skill Tree / Skill Management tabs ──────────
        # Use state hashes so we only redraw when something actually changed,
        # preventing constant flickering on the Skill Management tab.
        _last_tree_hash = [None]
        _last_mgmt_hash = [None]

        def _tree_state_hash():
            return (self.player.skill_points,
                    frozenset(self.player.tree_unlocked))

        def _mgmt_state_hash():
            key_map = tuple((sk.get('name',''), sk.get('key', 0))
                            for sk in self.player.unlocked_skills)
            toggles = tuple(sorted(self.player.passive_toggles.items()))
            return (key_map, toggles)

        def auto_refresh():
            try:
                if not win.winfo_exists():
                    return
                sel  = notebook.select()
                tabs = notebook.tabs()
                if len(tabs) > 1 and sel == tabs[1]:   # Skill Tree tab
                    h = _tree_state_hash()
                    if h != _last_tree_hash[0]:
                        stw._draw()
                        stw.sp_label.config(text=f"Skill Points: {self.player.skill_points}")
                        _last_tree_hash[0] = h
                elif len(tabs) > 2 and sel == tabs[2]:  # Skill Management tab
                    h = _mgmt_state_hash()
                    if h != _last_mgmt_hash[0]:
                        rebuild_skills_list()
                        rebuild_passive_toggles()
                        _last_mgmt_hash[0] = h
                win.after(500, auto_refresh)
            except Exception:
                pass

        auto_refresh()


    def open_skill_tree(self):
        """Open the visual skill tree window for the current player."""
        SkillTreeWindow(self, self.player)

    def open_skill_page(self):
        # Create a new window
        win = tk.Toplevel(self)
        win.title("Skill Management")
        win.geometry("700x600")
        win.configure(bg="#1a1a1a")  # dark background

        # --- Top: Active skills ---
        active_box = tk.Frame(win, bg="#2a2a2a", bd=0, relief="flat")
        active_box.pack(pady=10, padx=15, fill="x")

        tk.Label(active_box, text="Active Skills (Keybinds)",
                 font=("Arial", 14, "bold"),
                 bg="#2a2a2a", fg="#b0b0b0").pack(pady=5)

        self.active_frame = tk.Frame(active_box, bg="#2a2a2a")
        self.active_frame.pack(pady=5, fill="x")
        self.refresh_active_skills()

        # --- Divider line ---
        divider = tk.Frame(win, bg="#333333", height=2)
        divider.pack(fill="x", pady=10)

        # --- Bottom: Unlocked skills with scroll ---
        unlocked_box = tk.Frame(win, bg="#2a2a2a", bd=0, relief="flat")
        unlocked_box.pack(pady=10, padx=15, fill="both", expand=True)

        tk.Label(unlocked_box, text="Unlocked Skills",
                 font=("Arial", 14, "bold"),
                 bg="#2a2a2a", fg="#b0b0b0").pack(pady=5)

        # Scrollable Canvas
        canvas = tk.Canvas(unlocked_box, bg="#2a2a2a", highlightthickness=0)
        scrollbar = tk.Scrollbar(unlocked_box, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#2a2a2a")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Grid for unlocked skills inside scrollable frame
        for i, sk in enumerate(self.player.unlocked_skills):
            row = tk.Frame(scrollable_frame, bg="#3a3a3a", padx=10, pady=10)
            row.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="nsew")

            # Skill name
            name_label = tk.Label(row, text=sk['name'],
                                  anchor="center", font=("Arial", 11, "bold"),
                                  bg="#3a3a3a", fg="#b0b0b0")
            name_label.pack(fill="x", pady=(0, 5))

            # Slot buttons
            btn_frame = tk.Frame(row, bg="#3a3a3a")
            btn_frame.pack()
            for slot in range(1, 6):
                b = tk.Button(btn_frame, text=str(slot),
                              width=3,
                              font=("Arial", 10, "bold"),
                              bg="#4a4a4a", fg="#b0b0b0",
                              activebackground="#5a5a5a",
                              activeforeground="#b0b0b0",
                              command=lambda s=slot, skill=sk: self.assign_skill(skill, s))
                b.pack(side="left", padx=2)

        scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(1, weight=1)



    def refresh_active_skills(self):
        # Clear old widgets
        for w in self.active_frame.winfo_children():
            w.destroy()

        # Track (label_widget, skill_dict) for live cooldown ticking
        cd_labels = []

        # Show slots 1-5 on the Y axis
        for slot in range(1, 6):
            row = tk.Frame(self.active_frame, bg="#2a2a2a", padx=8, pady=5)
            row.pack(fill="x", pady=3)

            # Slot number label on the left
            slot_label = tk.Label(row,
                                  text=str(slot),
                                  font=("Arial", 12, "bold"),
                                  bg="#2a2a2a", fg="#b0b0b0", width=3)
            slot_label.pack(side="left", padx=(0, 10))

            # Find skill assigned to this slot (if any)
            assigned_skill = None
            for sk in self.player.unlocked_skills:
                if sk.get("key") == slot:
                    assigned_skill = sk
                    break

            if assigned_skill:
                # Skill name
                name_label = tk.Label(row,
                                      text=assigned_skill['name'],
                                      font=("Arial", 12, "bold"),
                                      bg="#2a2a2a", fg="#b0b0b0")
                name_label.pack(side="left")

                # Live cooldown info label (updated by ticker below)
                info_label = tk.Label(row,
                                      text="",
                                      font=("Arial", 10),
                                      bg="#2a2a2a", fg="#808080")
                info_label.pack(side="right")
                cd_labels.append((info_label, assigned_skill))
            else:
                # Empty slot placeholder
                empty_label = tk.Label(row,
                                       text="Empty",
                                       font=("Arial", 11, "italic"),
                                       bg="#2a2a2a", fg="#555555")
                empty_label.pack(side="left")

        # Live cooldown ticker - refreshes every 50ms
        def _tick_cooldowns():
            try:
                if not self.active_frame.winfo_exists():
                    return
                now = time.time()
                p = self.player
                for lbl, sk in cd_labels:
                    if not lbl.winfo_exists():
                        continue
                    base_cd   = sk.get('cooldown', 0)
                    mod       = sk.get('cooldown_mod', 1.0)
                    eff_cd    = base_cd * mod
                    last_used = sk.get('last_used', 0)
                    remaining = eff_cd - (now - last_used)

                    if remaining <= 0:
                        lbl.config(
                            text=f"Key: {sk['key']}  |  Base CD: {base_cd:.6f}s  |  Trained CD: {eff_cd:.6f}s",
                            fg="#44ff88")
                    else:
                        lbl.config(
                            text=f"Key: {sk['key']}  |  Base CD: {base_cd:.6f}s  |  Trained CD: {eff_cd:.6f}s  |  ⏳ {remaining:.6f}s",
                            fg="#ff8844")
                self.active_frame.after(50, _tick_cooldowns)
            except Exception:
                pass

        _tick_cooldowns()


    def assign_skill(self, skill, slot):
        """
        Assign a skill to a specific slot (1â€“5) and update its keybind.
        """
        # First, clear any skill already in this slot
        for sk in self.player.unlocked_skills:
            if sk.get("assigned_slot") == slot:
                sk["assigned_slot"] = None
                sk["key"] = 0  # reset keybind

        # Assign this skill to the chosen slot
        skill["assigned_slot"] = slot
        skill["key"] = slot   # update keybind to match slot number

        # Refresh the active skills display
        self.refresh_active_skills()

    # ── Interior room layout ───────────────────────────────────────────────────
    def _get_interior_layout(self, building):
        key = building.get('name', building.get('type', ''))
        if key in self._interior_layout_cache:
            return self._interior_layout_cache[key]

        W, H  = WINDOW_W, WINDOW_H
        ow    = 30    # outer wall (thicker for nicer look)
        iw    = 16    # inner divider
        dg    = 100   # door gap
        btype = building.get('type', '')
        walls = []
        objs  = []

        # Exit safe-zone — nothing collides here
        DX0, DX1, DY0 = W//2-60, W//2+60, H-ow-200

        def safe(x,y,w,h): return not(x<DX1 and x+w>DX0 and y+h>DY0)
        def col(x,y,w,h):  return (x,y,x+w,y+h)
        def lbl(t,x,y,c='#888888'): return {'type':'label','x':x,'y':y,'text':t,'color':c}
        def conly(x,y,w,h): return {'type':'collision_only','collision':col(x,y,w,h)}

        BC = ['#8B1A1A','#1A3A8B','#1A6B1A','#8B7A1A','#6B1A6B','#1A6B6B','#8B4A1A','#4A1A8B']

        # ── HOUSE ─────────────────────────────────────────────────────────
        if btype == 'house':
            midY, midX = H//2, W//2
            door_y = ow + int((midY-ow)*0.65)
            walls += [(ow,midY,midX-dg//2,midY+iw),(midX+dg//2,midY,W-ow,midY+iw),
                      (midX,ow,midX+iw,door_y),(midX,door_y+dg,midX+iw,midY)]
            for t,x,y in [('BEDROOM',midX//2+ow,ow+16),('STORAGE',midX+(W-ow-midX)//2,ow+16),
                           ('KITCHEN',midX//2+ow,midY+iw+16),('LIVING ROOM',midX+(W-ow-midX)//2,midY+iw+16)]:
                objs.append(lbl(t,x,y,'#aaaaaa'))
            bw,bh=200,110
            objs+=[{'type':'bed','x':ow+40,'y':ow+50,'w':bw,'h':bh,'collision':col(ow+40,ow+50,bw,bh)},
                   {'type':'wardrobe','x':ow+260,'y':ow+45,'w':50,'h':60,'collision':col(ow+260,ow+45,50,60)},
                   {'type':'nightstand','x':ow+250,'y':ow+80,'w':50,'h':50},
                   {'type':'candle','x':ow+274,'y':ow+74},
                   {'type':'rug','x':ow+40,'y':ow+175,'w':240,'h':100,'color':'#8B2222'},
                   {'type':'chest','x':midX+40,'y':ow+50,'w':90,'h':70,'collision':col(midX+40,ow+50,90,70)}]
            for si in range(3):
                objs+=[{'type':'wall_shelf','x':midX+160,'y':ow+35+si*65,'w':W-ow-midX-175,'h':16,'collision':col(midX+160,ow+35+si*65,W-ow-midX-175,16)}]
            ky=midY+iw
            # Kitchen: rectangular wall-stove instead of circular stone_stove
            objs+=[{'type':'kitchen_counter','x':ow+20,'y':ky+25,'w':130,'h':75,'collision':col(ow+20,ky+25,130,75)},
                   {'type':'pot','x':ow+85,'y':ky+18},
                   {'type':'kitchen_counter','x':ow+165,'y':ky+25,'w':165,'h':65,'collision':col(ow+165,ky+25,165,65)},
                   {'type':'dining_table','x':ow+35,'y':ky+185,'w':160,'h':85,'collision':col(ow+35,ky+185,160,85)},
                   {'type':'chair','x':ow+45,'y':ky+278,'w':45,'h':45,'collision':col(ow+45,ky+278,45,45)},
                   {'type':'chair','x':ow+120,'y':ky+278,'w':45,'h':45,'collision':col(ow+120,ky+278,45,45)}]
            lx,ly=midX,midY+iw
            objs+=[{'type':'fireplace','x':W-ow-160,'y':ly+25,'w':135,'h':110,'collision':col(W-ow-160,ly+25,135,110)},
                   {'type':'rug','x':lx+35,'y':ly+95,'w':300,'h':165,'color':'#1a3a6a'},
                   {'type':'couch','x':lx+35,'y':ly+125,'w':275,'h':80,'collision':col(lx+35,ly+100,275,110)},
                   {'type':'coffee_table','x':lx+145,'y':ly+225,'w':85,'h':50,'collision':col(lx+145,ly+225,85,50)},
                   {'type':'candle','x':lx+187,'y':ly+218}]

        # ── LIBRARY ────────────────────────────────────────────────────────
        elif btype == 'library':
            SW = 160  # shelf unit depth — tall and prominent
            # Full-width bookcase along TOP wall only — books face the player (vertical spines)
            objs.append({'type':'bookcase_unit','x':ow,'y':ow,'w':W-ow*2,'h':SW,'side':'back'})
            objs.append(conly(ow,ow,W-ow*2,SW))

            # Four reading desks spread around the room, well clear of exit zone and circle
            desk_configs = [
                (ow+30,          ow+SW+30),        # top-left
                (W-ow-160,       ow+SW+30),        # top-right
                (ow+30,          H*2//3),           # bottom-left
                (W-ow-160,       H*2//3),           # bottom-right
            ]
            for dx,dy in desk_configs:
                if safe(dx, dy, 130, 75):
                    objs+=[{'type':'reading_desk','x':dx,'y':dy,'w':130,'h':75,'collision':col(dx,dy,130,75)},
                           {'type':'candle','x':dx+110,'y':dy-10},
                           {'type':'open_book','x':dx+12,'y':dy+10,'w':80,'h':50}]

            # Magic circle — large, centred (drawn BEFORE candles so candles appear on top)
            objs.append({'type':'magic_circle_floor','x':W//2,'y':H//2,'r':130})

            # Candles on floor framing the circle — added AFTER magic circle so they draw on top
            # Candles placed at radius ~190 evenly around the circle — well clear of r=130
            import math as _m
            for _i in range(6):
                _a = _i * _m.pi / 3 - _m.pi / 2   # 6 evenly spaced, starting at top
                _cx = W//2 + int(_m.cos(_a) * 190)
                _cy = H//2 + int(_m.sin(_a) * 190)
                objs.append({'type':'candle','x':_cx,'y':_cy})

        # ── BLACKSMITH ─────────────────────────────────────────────────────
        elif btype == 'blacksmith':
            RW = 36  # rack depth — thicker, more visible

            # ── TOP wall weapon rack (horizontal, full width) ──────────────
            objs+=[{'type':'weapon_rack_h','x':ow,'y':ow,'w':W-ow*2,'h':RW},
                   conly(ow,ow,W-ow*2,RW)]
            wpns_t=['sword','axe','spear','sword','axe','sword','axe','spear','sword','axe']
            sp=(W-ow*2-60)//len(wpns_t)
            for wi,wt in enumerate(wpns_t):
                objs.append({'type':'hung_weapon','x':ow+30+wi*sp,'y':ow+RW//2,'weapon':wt,'orient':'v'})

            # ── LEFT wall weapon rack (vertical, full height below top rack) ─
            objs+=[{'type':'weapon_rack_v','x':ow,'y':ow+RW,'w':RW,'h':H-ow*2-RW},
                   conly(ow,ow+RW,RW,H-ow*2-RW)]
            wpns_l=['sword','axe','spear','sword','axe','spear','sword']
            spl=(H-ow*2-RW-60)//len(wpns_l)
            for wi,wt in enumerate(wpns_l):
                objs.append({'type':'hung_weapon','x':ow+RW//2,'y':ow+RW+30+wi*spl,'weapon':wt,'orient':'h'})

            # ── RIGHT wall weapon rack (vertical, full height below top rack) ─
            objs+=[{'type':'weapon_rack_v','x':W-ow-RW,'y':ow+RW,'w':RW,'h':H-ow*2-RW},
                   conly(W-ow-RW,ow+RW,RW,H-ow*2-RW)]
            wpns_r=['axe','spear','sword','axe','sword','spear','axe']
            for wi,wt in enumerate(wpns_r):
                objs.append({'type':'hung_weapon','x':W-ow-RW//2,'y':ow+RW+30+wi*spl,'weapon':wt,'orient':'h'})

            # ── Central forge fire pit ─────────────────────────────────────
            fx,fy=W//2,H//2-20
            objs+=[{'type':'open_forge','x':fx,'y':fy,'r':90},conly(fx-95,fy-50,190,130)]

            # ── Sales counter bottom-right ────────────────────────────────
            cw2=W//3-ow-10
            if safe(W-ow-cw2-10,H-ow-80,cw2,65):
                objs+=[{'type':'counter','x':W-ow-cw2-10,'y':H-ow-80,'w':cw2,'h':65,
                         'collision':col(W-ow-cw2-10,H-ow-80,cw2,65)}]

        # ── TOWER (unchanged) ─────────────────────────────────────────────
        elif btype == 'tower':
            ps=32
            for px,py in [(ow+20,ow+20),(W-ow-ps-20,ow+20),(ow+20,H-ow-ps-20),(W-ow-ps-20,H-ow-ps-20)]:
                objs+=[{'type':'stone_pillar','x':px,'y':py,'w':ps,'h':ps,'collision':col(px,py,ps,ps)}]
            objs+=[{'type':'crystal_stand','x':W-ow-90,'y':ow+60,'w':65,'h':80,'collision':col(W-ow-90,ow+60,65,80)},
                   {'type':'candle','x':W-ow-57,'y':ow+55},
                   {'type':'candle','x':W-ow-57,'y':H-ow-60},
                   {'type':'reading_desk','x':ow+35,'y':H//2-30,'w':110,'h':60,'collision':col(ow+35,H//2-30,110,60)},
                   {'type':'candle','x':ow+85,'y':H//2-35}]

        # ── ALCHEMIST ─────────────────────────────────────────────────────
        elif btype == 'shop' and building.get('indoor_npc_name') == 'Zephyr':
            # Cauldrons spread across the room
            cdata=[(W//4+10,     H//2-30, 70, '#00dd44'),
                   (W*3//5,      H//2-50, 55, '#aa00ff'),
                   (W//4+10,     H*2//3,  45, '#00cc33'),
                   (W*3//5,      H*2//3,  40, '#8800ff')]
            for cx3,cy3,cr,lc in cdata:
                if not(cx3-cr<DX1 and cx3+cr>DX0 and cy3+cr>DY0):
                    objs+=[{'type':'big_cauldron','x':cx3,'y':cy3,'r':cr,'liq_color':lc},
                           conly(cx3-cr-10,cy3-cr//2,cr*2+20,cr+60)]
            # Worktable with mortar and candle — top area
            wx,wy=W//2-80,ow+25
            objs+=[{'type':'worktable','x':wx,'y':wy,'w':160,'h':65,'collision':col(wx,wy,160,65)},
                   {'type':'mortar','x':wx+80,'y':wy-14},{'type':'candle','x':wx+140,'y':wy-6}]

        # ── JEWELER ────────────────────────────────────────────────────────
        elif btype == 'shop' and building.get('indoor_npc_name') == 'Gemma':
            # Bed — large, top-right
            bw,bh=220,115
            objs+=[{'type':'bed','x':W-ow-bw-20,'y':ow+25,'w':bw,'h':bh,'collision':col(W-ow-bw-20,ow+25,bw,bh)},
                   {'type':'candle','x':W-ow-35,'y':ow+22}]
            # Shelving unit top-left
            objs+=[{'type':'shelf_cabinet','x':ow,'y':ow,'w':80,'h':H*2//5},conly(ow,ow,80,H*2//5)]
            gem_c=['#ff4444','#4444ff','#44ff44','#ff44ff','#ffff44','#44ffff']
            for ri in range(4):
                for ji in range(2):
                    objs.append({'type':'gem_display','x':ow+20+ji*35,'y':ow+20+ri*55,'color':gem_c[(ri*2+ji)%6],'name':''})
            # Large safe — bottom-left, NOT near door
            objs+=[{'type':'safe','x':ow+20,'y':H-ow-150},conly(ow+20,H-ow-155,100,140)]
            # Workbench with tools
            objs+=[{'type':'worktable','x':ow+90,'y':ow+25,'w':200,'h':70,'collision':col(ow+90,ow+25,200,70)},
                   {'type':'candle','x':ow+275,'y':ow+20}]
            for gi,gc in enumerate(gem_c[:5]):
                objs.append({'type':'gem_display','x':ow+105+gi*36,'y':ow+15,'color':gc,'name':''})
            # Gem display counter split around exit
            seg1_w=W//2-70-ow-30
            objs+=[{'type':'gem_counter','x':ow+30,'y':H-ow-90,'w':seg1_w,'h':65,'collision':col(ow+30,H-ow-90,seg1_w,65)}]
            seg2_x=W//2+70
            seg2_w=W-ow-30-seg2_x
            objs+=[{'type':'gem_counter','x':seg2_x,'y':H-ow-90,'w':seg2_w,'h':65,'collision':col(seg2_x,H-ow-90,seg2_w,65)}]
            for gi,gc in enumerate(gem_c[:3]):
                objs.append({'type':'gem_display','x':ow+45+gi*(seg1_w-20)//3,'y':H-ow-105,'color':gc,'name':gem_c[gi]})
            for gi,gc in enumerate(gem_c[3:]):
                objs.append({'type':'gem_display','x':seg2_x+15+gi*(seg2_w-20)//3,'y':H-ow-105,'color':gc,'name':gem_c[gi+3]})
            objs.append({'type':'lantern','x':W//2,'y':ow+60})

        # ── TRADER ─────────────────────────────────────────────────────────
        elif btype == 'shop' and building.get('indoor_npc_name') == 'Marcus':
            # ── Back wall shelf — full width, weapons + misc on display ──
            BW=85
            objs+=[{'type':'shelf_cabinet','x':ow,'y':ow,'w':W-ow*2,'h':BW},
                   conly(ow,ow,W-ow*2,BW)]
            # Weapons displayed on back shelf (alternating)
            wpn_types=['sword','axe','spear','sword','axe','spear','sword','axe']
            sp2=(W-ow*2-40)//len(wpn_types)
            for wi,wt in enumerate(wpn_types):
                objs.append({'type':'hung_weapon','x':ow+20+wi*sp2,'y':ow+BW//2,'weapon':wt,'orient':'v'})
            # ── Long trading counter just below back shelf ────────────────
            tc_y=ow+BW+20; tc_h=60; tc_w=W-ow*2-40
            objs+=[{'type':'shop_counter','x':ow+20,'y':tc_y,'w':tc_w,'h':tc_h,
                    'collision':col(ow+20,tc_y,tc_w,tc_h)}]
            # ── Small cauldron left side, mid-room ───────────────────────
            cd_x=ow+70; cd_y=H//2+20
            objs+=[{'type':'big_cauldron','x':cd_x,'y':cd_y,'r':38,'liq_color':'#44ff88'},
                   conly(cd_x-48,cd_y-24,96,80)]
            # ── Small cauldron right side, mid-room ──────────────────────
            cd2_x=W-ow-70; cd2_y=H//2+20
            objs+=[{'type':'big_cauldron','x':cd2_x,'y':cd2_y,'r':38,'liq_color':'#aa44ff'},
                   conly(cd2_x-48,cd2_y-24,96,80)]
            # ── Central map table with open scroll ───────────────────────
            mt_w=160; mt_h=90
            mt_x=W//2-mt_w//2; mt_y=H//2-10
            objs+=[{'type':'map_table','x':mt_x,'y':mt_y,'w':mt_w,'h':mt_h,
                    'collision':col(mt_x,mt_y,mt_w,mt_h)},
                   {'type':'open_scroll','x':mt_x+10,'y':mt_y+8,'w':mt_w-20,'h':mt_h-16},
                   {'type':'candle','x':mt_x+8,        'y':mt_y-10},
                   {'type':'candle','x':mt_x+mt_w-12,  'y':mt_y-10}]
            # ── Crate stack top-right corner ──────────────────────────────
            objs+=[{'type':'crate_stack','x':W-ow-115,'y':ow+BW+tc_h+35,'w':90,'h':100,
                    'collision':col(W-ow-115,ow+BW+tc_h+35,90,100)}]
            # ── Sack beside crates ────────────────────────────────────────
            objs.append({'type':'sack','x':W-ow-145,'y':ow+BW+tc_h+55,
                         'collision':col(W-ow-173,ow+BW+tc_h+13,56,75)})

        # ── BAKERY ─────────────────────────────────────────────────────────
        elif btype == 'inn':
            # Dividing wall: kitchen (top 45%) / serving area (bottom 55%)
            divY=int(H*0.42); dxg=int(W*0.28)
            walls+=[(ow,divY,dxg-dg//2,divY+iw),(dxg+dg//2,divY,W-ow,divY+iw)]
            objs.append(lbl('KITCHEN',W//2,ow+14,'#888888'))
            objs.append(lbl('SERVING',W//2,divY+iw+14,'#888888'))
            # Two large arch ovens side by side at the back of the kitchen
            oven_w=(W-ow*2-40)//2
            oven_h=divY-ow-55
            for oi in range(2):
                ox2=ow+15+oi*(oven_w+10)
                objs+=[{'type':'arch_oven','x':ox2,'y':ow+10,'w':oven_w,'h':oven_h,'collision':col(ox2,ow+10,oven_w,oven_h)}]
            # Prep counter just above the divider wall
            pc_y=divY-60
            objs+=[{'type':'kitchen_counter','x':ow+20,'y':pc_y,'w':W-ow*2-40,'h':45,'collision':col(ow+20,pc_y,W-ow*2-40,45)}]
            # Sacks of ingredients in kitchen corners (between ovens and prep counter)
            for bx4,by4 in [(ow+15,pc_y-80),(W-ow-55,pc_y-80)]:
                objs.append({'type':'sack','x':bx4,'y':by4,'collision':col(bx4-28,by4-42,56,75)})
            # Serving counter — spans full width just below divider
            ctr_w=W-ow*2-60
            objs+=[{'type':'bakery_counter','x':ow+30,'y':divY+iw+25,'w':ctr_w,'h':55,'collision':col(ow+30,divY+iw+25,ctr_w,55)},
                   {'type':'bread_display','x':ow+60,'y':divY+iw+10},
                   {'type':'bread_display','x':W//2-30,'y':divY+iw+10},
                   {'type':'bread_display','x':W-ow-140,'y':divY+iw+10},
                   {'type':'candle','x':ow+32,'y':divY+iw+16},
                   {'type':'candle','x':W-ow-44,'y':divY+iw+16}]
            # Seating area — three small tables with chairs in bottom half
            seat_y=H-ow-220
            for tx2 in [ow+35, W//2-55, W-ow-175]:
                if safe(tx2,seat_y,110,65):
                    objs+=[{'type':'dining_table','x':tx2,'y':seat_y,'w':110,'h':65,'collision':col(tx2,seat_y,110,65)},
                            {'type':'chair','x':tx2+8,'y':seat_y+70,'w':36,'h':36,'collision':col(tx2+8,seat_y+70,36,36)},
                            {'type':'chair','x':tx2+66,'y':seat_y+70,'w':36,'h':36,'collision':col(tx2+66,seat_y+70,36,36)},
                            {'type':'candle','x':tx2+85,'y':seat_y-6}]

        self._interior_layout_cache[key] = (walls, objs)
        return walls, objs

    def open_chest(self):
        """Open the house chest inventory window."""
        win = tk.Toplevel(self)
        win.title("House Chest")
        win.geometry("620x500")
        win.configure(bg="#1a1210")
        win.resizable(False, False)

        SLOT = 56; GAP = 4; COLS = 5
        C_BG  = "#0e0c0a"; C_SLOT = "#3a2a1a"; C_SEL = "#8a6a4a"; C_TEXT = "#e8d8b8"

        tk.Label(win, text="🏠 House Chest",
                 bg="#1a1210", fg="#FFD700",
                 font=("Arial", 16, "bold")).pack(pady=(10,4))
        tk.Label(win, text="Click to move items between chest and inventory",
                 bg="#1a1210", fg="#888888", font=("Arial", 9)).pack()

        cv = tk.Canvas(win, bg=C_BG, highlightthickness=0)
        cv.pack(fill='both', expand=True, padx=10, pady=8)

        selected = [None]   # ('chest', idx) or ('inv', idx)

        def redraw():
            cv.delete('all')
            W2 = cv.winfo_width() or 580
            # ── Chest grid ──
            cv.create_text(8, 6, text="CHEST", fill="#aaa888",
                           font=("Arial", 9, "bold"), anchor='nw')
            chest_rows = math.ceil(max(len(self.player.chest_items), 10) / COLS)
            for i in range(chest_rows * COLS):
                col = i % COLS; row = i // COLS
                x0 = 6 + col*(SLOT+GAP); y0 = 22 + row*(SLOT+GAP)
                sel = selected[0] == ('chest', i)
                cv.create_rectangle(x0,y0,x0+SLOT,y0+SLOT,
                                    fill=C_SEL if sel else C_SLOT,
                                    outline="#6a4a2a",width=2)
                if i < len(self.player.chest_items):
                    it = self.player.chest_items[i]
                    cv.create_text(x0+SLOT//2, y0+SLOT//2,
                                   text=it.name[:8], fill=it.get_color(),
                                   font=("Arial", 8, "bold"), width=SLOT-4, justify='center')
            chest_h = 22 + chest_rows*(SLOT+GAP) + 10

            # ── Inventory grid ──
            inv_items = [it for it in self.player.inventory if it not in self.player.equipped_items]
            cv.create_text(8, chest_h+4, text="INVENTORY", fill="#aaaaaa",
                           font=("Arial", 9, "bold"), anchor='nw')
            inv_rows = math.ceil(max(len(inv_items), 10) / COLS)
            for i in range(inv_rows * COLS):
                col = i % COLS; row = i // COLS
                x0 = 6 + col*(SLOT+GAP); y0 = chest_h+20 + row*(SLOT+GAP)
                sel = selected[0] == ('inv', i)
                cv.create_rectangle(x0,y0,x0+SLOT,y0+SLOT,
                                    fill=C_SEL if sel else C_SLOT,
                                    outline="#555566",width=2)
                if i < len(inv_items):
                    it = inv_items[i]
                    cv.create_text(x0+SLOT//2, y0+SLOT//2,
                                   text=it.name[:8], fill=it.get_color(),
                                   font=("Arial", 8, "bold"), width=SLOT-4, justify='center')

        def on_click(event):
            W2 = cv.winfo_width() or 580
            chest_rows = math.ceil(max(len(self.player.chest_items), 10) / COLS)
            chest_h = 22 + chest_rows*(SLOT+GAP) + 10
            inv_items = [it for it in self.player.inventory if it not in self.player.equipped_items]

            def slot_at(mx, my, y_start):
                col = (mx - 6) // (SLOT+GAP)
                row = (my - y_start) // (SLOT+GAP)
                if 0 <= col < COLS and row >= 0:
                    return row*COLS + col
                return None

            # Which section was clicked?
            if event.y < chest_h:
                idx = slot_at(event.x, event.y, 22)
                if idx is None: return
                src = ('chest', idx)
            else:
                idx = slot_at(event.x, event.y, chest_h+20)
                if idx is None: return
                src = ('inv', idx)

            if selected[0] is None:
                # First click — select
                if src[0]=='chest' and src[1] < len(self.player.chest_items):
                    selected[0] = src
                elif src[0]=='inv' and src[1] < len(inv_items):
                    selected[0] = src
            else:
                # Second click — move item
                prev = selected[0]
                selected[0] = None
                if prev == src:
                    redraw(); return
                # chest → inv
                if prev[0]=='chest' and prev[1]<len(self.player.chest_items):
                    item = self.player.chest_items.pop(prev[1])
                    self.player.add_item_to_inventory(item)
                # inv → chest
                elif prev[0]=='inv' and prev[1]<len(inv_items):
                    item = inv_items[prev[1]]
                    self.player.remove_item_from_inventory(item)
                    self.player.chest_items.append(item)
            redraw()

        cv.bind('<Button-1>', on_click)
        win.bind('<Configure>', lambda e: redraw())
        win.after(100, redraw)


    def get_room(self, row, col):
        key = (row, col)
        if key not in self.dungeon:
            self.dungeon[key] = Room(row, col, self.dungeon_id, player_level=self.player.level)
        return self.dungeon[key]

    def on_key_down(self, e):
        self.keys[e.keysym] = True

        if e.keysym.lower() == 'p':
            self.show_stats = not self.show_stats
        if e.keysym.lower() == 'h':
            self.show_help = not self.show_help
        if e.keysym == 'Escape':
            if self.dungeon_id == 0:
                self.on_quit_to_menu()
            # ESC is disabled inside dungeons to prevent accidental exit
        if e.keysym.lower() == 'o':
            self.toggle_combined_page()   # O = combined window (Inventory + Skill Tree + Skills)

        # Beam rotation (R only; T/Y/U now used for item hotbar)
        if e.keysym.lower() == 'r':
            if hasattr(self, "player_beam") and self.player_beam:
                self.player_beam.rotate(-0.05)

        # T / Y / U select item hotbar slots 0, 1, 2
        if e.keysym.lower() == 't':
            if hasattr(self, "player_beam") and self.player_beam:
                self.player_beam.rotate(0.05)   # beam rotate if active
            else:
                self.active_item_slot = 0
        if e.keysym.lower() == 'y':
            self.active_item_slot = 1
        if e.keysym.lower() == 'u':
            self.active_item_slot = 2

        if e.keysym.lower() == 'c':
            # Don't process C while a shop window is open
            if not getattr(self, '_npc_shop_open', False):
                if self.current_interior:
                    pass   # handled inside the draw/update loop when indoors
                elif self.nearby_npc:
                    self.interact_with_npc(self.nearby_npc)
                elif self.nearby_dungeon:
                    print(f"Entering dungeon {self.nearby_dungeon['dungeon_id']}")
                    self.enter_dungeon(self.nearby_dungeon['dungeon_id'])

        # E = interact with chest / objects indoors
        if e.keysym.lower() == 'e':
            self.keys['e'] = True

        # 1-5 selects skill hotbar slot
        if e.keysym in ('1','2','3','4','5'):
            self.active_hotbar_slot = int(e.keysym)

    def on_canvas_click(self, event):
        """Left-click: fire the active hotbar skill, or spend a stat point."""
        # Help overlay tab switching takes first priority
        if self.show_help:
            self._help_tab_click(event)
            return
        # Stat panel click (takes priority when stats panel is open)
        if self.show_stats and self.player.stat_points > 0:
            self.handle_stat_click(event)
            return

        # Fire the skill assigned to the active hotbar slot
        if self.dead:
            return
        p = self.player
        now = time.time()
        for sk in p.unlocked_skills:
            if sk.get('key') == self.active_hotbar_slot:
                base_cd = sk.get('cooldown', 0)
                mod = sk.get('cooldown_mod', 1.0)
                effective_cd = base_cd * mod
                last_used = sk.get('last_used', 0)
                if effective_cd <= 0 or now - last_used >= effective_cd:
                    sk['skill'](p, self)
                    sk['last_used'] = now
                    sk['cooldown_mod'] = max(0.2, mod * 0.9995)
                break

    def on_mouse_move(self, event):
        """Track mouse position for hotbar tooltips (non-spammy)."""
        self.mouse_pos = (event.x, event.y)

    def on_right_click(self, event):
        """Right-click: use the item in the active item hotbar slot."""
        if self.dead:
            return
        slot = self.active_item_slot
        item = self.hotbar_items[slot]
        if item is None:
            return
        used = item.use(self.player)
        if used:
            item.count -= 1
            if item.count <= 0:
                self.hotbar_items[slot] = None

    def draw_hotbar(self):
        """Skill hotbar: top-left of game canvas (only when outdoors).
        Consumable hotbar: right panel (map_canvas), always drawn."""
        self._draw_consumable_hotbar()
        if not self.current_interior:
            self._draw_skill_hotbar()

    def _draw_skill_hotbar(self):
        """Draw the 5-slot skill hotbar on the game canvas (top-left)."""
        p   = self.player
        now = time.time()

        slot_size = 44
        gap       = 6
        start_x   = 10
        y_skill   = 80

        slot_skill = {}
        for sk in p.unlocked_skills:
            k = sk.get('key', 0)
            if 1 <= k <= 5:
                slot_skill[k] = sk

        for i in range(1, 6):
            x        = start_x + (i-1)*(slot_size+gap)
            selected = (i == self.active_hotbar_slot)
            bg       = '#dddddd' if selected else '#555555'
            outline  = '#ffffff' if selected else '#888888'
            lw       = 3 if selected else 1
            self.canvas.create_rectangle(x, y_skill, x+slot_size, y_skill+slot_size,
                                         fill=bg, outline=outline, width=lw)
            sk = slot_skill.get(i)
            if sk:
                elapsed = now - sk.get('last_used', 0)
                cd      = sk.get('cooldown', 0) * sk.get('cooldown_mod', 1.0)
                if cd > 0 and elapsed < cd:
                    frac     = 1.0 - elapsed / cd
                    overlay_h = int(slot_size * frac)
                    self.canvas.create_rectangle(x, y_skill, x+slot_size,
                                                 y_skill+overlay_h,
                                                 fill='#000000', stipple='gray50', outline='')
                name  = sk['name']
                short = name[:8] + '…' if len(name) > 9 else name
                self.canvas.create_text(x+slot_size//2, y_skill+slot_size//2,
                                        text=short, fill='white',
                                        font=('Arial', 7, 'bold'), width=slot_size-4)
            num_color = '#000000' if selected else '#aaaaaa'
            self.canvas.create_text(x+6, y_skill+6, text=str(i),
                                    fill=num_color, font=('Arial', 7, 'bold'))

    def _draw_consumable_hotbar(self):
        """Draw the 3-slot consumable hotbar on the map_canvas (always visible)."""
        mc  = self.map_canvas
        pw  = mc.winfo_width() or 200
        ph  = mc.winfo_height() or 600

        item_slot_size = 44
        item_gap       = 6
        labels         = ['T', 'Y', 'U']
        total_iw       = 3*item_slot_size + 2*item_gap
        ix0            = (pw - total_iw) // 2    # centred in panel
        iy             = ph - item_slot_size - 8  # bottom of panel

        mc.create_text(pw//2, iy-14, text='ITEMS', fill='#888888',
                       font=('Arial', 7, 'bold'))

        for i in range(3):
            x   = ix0 + i*(item_slot_size+item_gap)
            sel = (i == self.active_item_slot)
            ol  = '#aaaaaa' if sel else '#666688'
            lw  = 3 if sel else 1
            mc.create_rectangle(x, iy, x+item_slot_size, iy+item_slot_size,
                                 fill='#ffffff', outline=ol, width=lw)
            item = self.hotbar_items[i]
            if item:
                emoji = item.get_emoji() if hasattr(item, 'get_emoji') else '?'
                mc.create_oval(x+item_slot_size-9, iy+2,
                               x+item_slot_size-2, iy+9,
                               fill=item.get_color(), outline='')
                cnt = getattr(item, 'count', 1)
                mc.create_text(x+item_slot_size//2, iy+item_slot_size//2,
                               text=emoji, font=('Arial', 14))
                if cnt > 1:
                    mc.create_text(x+item_slot_size-4, iy+item_slot_size-4,
                                   text=str(cnt), fill='#111111',
                                   font=('Arial', 7, 'bold'), anchor='se')
            lbl_c = '#333333' if sel else '#555577'
            mc.create_text(x+6, iy+7, text=labels[i],
                           fill=lbl_c, font=('Arial', 7, 'bold'))


    def _player_has_map(self):
        return any(it.item_type == 'map' for it in self.player.equipped_items)

    def draw_minimap(self):
        """Draw the mini-map on the dedicated map_canvas panel."""
        mc = self.map_canvas
        mc.delete('all')

        pw = mc.winfo_width()
        ph = mc.winfo_height()
        if pw < 2:
            return

        # Reserve bottom area for consumable hotbar + buff list
        ITEM_H   = 66     # item slots + ITEMS label
        buffs    = getattr(self.player, 'active_buffs', [])
        now      = time.time()
        buffs    = [b for b in buffs if now < b['end']]

        # Build full display list: buffs + frozen debuff
        frozen_until    = getattr(self.player, '_frozen_until', 0)
        frozen_remaining = frozen_until - now if frozen_until > now else 0
        debuff_rows = []
        if frozen_remaining > 0:
            debuff_rows.append({
                'emoji': '❄', 'name': 'FROZEN', 'desc': 'Cannot move!',
                'remaining': frozen_remaining, 'duration': 10.0,
                'color': '#00eeff', 'bar_color': '#0099cc',
            })

        all_display = ([{'emoji': b['emoji'], 'name': b['name'], 'desc': b['desc'],
                         'remaining': b['end'] - now, 'duration': b.get('duration', 30),
                         'color': '#ffd700', 'bar_color': '#44aa44'}
                        for b in buffs] + debuff_rows)

        # Reserve enough vertical space for ALL rows so nothing overlaps the hotbar
        ROW_H    = 50     # matches ROW_H2 in the draw block below
        LABEL_H  = 18 if all_display else 0
        BUFF_H   = len(all_display) * ROW_H + LABEL_H
        bottom_reserved = ITEM_H + BUFF_H + 8

        mc.create_line(0, 0, 0, ph, fill='#333355', width=2)
        mc.create_text(pw//2, 12, text='MAP', fill='#888888', font=('Arial', 10, 'bold'))

        if not self._player_has_map():
            mc.create_text(pw//2, (ph - bottom_reserved)//2 + 20,
                           text='No map\nequipped',
                           fill='#444466', font=('Arial', 10), justify='center')
        else:
            ms = min(pw - MAP_PAD*2, ph - bottom_reserved - MAP_PAD*4 - 24)
            if ms >= 10:
                mx2 = (pw - ms)//2
                my2 = 24
                if self.dungeon_id == 0:
                    self._draw_minimap_town(mx2, my2, ms, mc)
                else:
                    self._draw_minimap_dungeon(mx2, my2, ms, mc)

        # ── Active buff/debuff display — stacks UPWARD from above the hotbar ─
        if all_display:
            ROW_H2   = 50   # taller rows so everything fits
            area_bottom = ph - ITEM_H - 4
            label_y     = area_bottom - len(all_display) * ROW_H2 - 6
            mc.create_text(pw//2, label_y, text='ACTIVE EFFECTS',
                           fill='#666688', font=('Arial', 7, 'bold'))
            for i, entry in enumerate(all_display):
                remaining = entry['remaining']
                by2 = area_bottom - (i + 1) * ROW_H2
                bg_fill = '#0d1a22' if entry['color'] == '#00eeff' else '#12121e'
                # background card
                mc.create_rectangle(3, by2+1, pw-3, by2+ROW_H2-2,
                                    fill=bg_fill, outline='#2a2a44', width=1)
                # ── Left column: big emoji icon ──────────────────────────────
                mc.create_text(14, by2 + ROW_H2//2, text=entry['emoji'],
                               font=('Arial', 16), anchor='center')
                # ── Right column: name + timer on row 1 ─────────────────────
                mc.create_text(28, by2 + 8,
                               text=entry['name'][:15],
                               fill=entry['color'], font=('Arial', 7, 'bold'), anchor='w')
                mc.create_text(pw-5, by2 + 8,
                               text=f"{remaining:.1f}s",
                               fill=entry['color'], font=('Arial', 7, 'bold'), anchor='e')
                # ── desc on row 2 ────────────────────────────────────────────
                mc.create_text(28, by2 + 21,
                               text=entry['desc'][:22],
                               fill='#888899', font=('Arial', 6), anchor='w')
                # ── timer bar on row 3 ───────────────────────────────────────
                frac  = min(1.0, remaining / max(1, entry['duration']))
                bar_x = 28; bar_w2 = pw - 34
                mc.create_rectangle(bar_x, by2+33, bar_x+bar_w2, by2+40,
                                    fill='#222233', outline='')
                mc.create_rectangle(bar_x, by2+33, bar_x+int(bar_w2*frac), by2+40,
                                    fill=entry['bar_color'], outline='')


    def _draw_minimap_town(self, mx, my, ms, mc):
        """Mini-map for the town overworld."""
        wx0 = TOWN_X_START - 300
        wy0 = TOWN_Y_START - 300
        wx1 = TOWN_X_END   + 300
        wy1 = TOWN_Y_END   + 300
        ww  = wx1 - wx0
        wh  = wy1 - wy0
        sx  = ms / ww
        sy  = ms / wh

        def tx(wx): return int(mx + (wx - wx0) * sx)
        def ty(wy): return int(my + (wy - wy0) * sy)

        # Grass background
        mc.create_rectangle(mx, my, mx+ms, my+ms,
                             fill='#1a4a1a', outline='#ffffff', width=1)

        # Town area outline
        mc.create_rectangle(
            tx(TOWN_X_START), ty(TOWN_Y_START),
            tx(TOWN_X_END),   ty(TOWN_Y_END),
            fill='', outline='#3a7a3a', width=1
        )

        # Buildings (brown)
        for b in self.room.buildings:
            bx0 = tx(b['x']); by0 = ty(b['y'])
            bx1 = tx(b['x']+b['width']); by1 = ty(b['y']+b['height'])
            if bx1 > bx0 and by1 > by0:
                mc.create_rectangle(bx0, by0, bx1, by1, fill='#8B4513', outline='')

        # NPCs (yellow dots)
        for npc in self.room.npcs:
            nx = tx(npc.x); ny = ty(npc.y)
            if mx <= nx <= mx+ms and my <= ny <= my+ms:
                mc.create_oval(nx-2, ny-2, nx+2, ny+2, fill='#FFD700', outline='')

        # Player (blue dot)
        ppx = tx(self.player.x); ppy = ty(self.player.y)
        mc.create_oval(ppx-3, ppy-3, ppx+3, ppy+3,
                       fill='#4488ff', outline='white', width=1)

    def _draw_minimap_dungeon(self, mx, my, ms, mc):
        """Mini-map for dungeon — shows full room grid."""
        rows = ROOM_ROWS
        cols = ROOM_COLS
        cw = ms // cols
        ch = (ms - 20) // rows

        for row in range(rows):
            for col in range(cols):
                rx = mx + col * cw
                ry = my + row * ch
                key = (row, col)
                explored = key in self.dungeon
                is_current = (row == self.room_row and col == self.room_col)

                room_fill = '#111111' if explored else '#0a0a0a'
                if is_current:
                    room_fill = '#1a1a2e'
                mc.create_rectangle(rx+1, ry+1, rx+cw-1, ry+ch-1,
                                    fill=room_fill, outline='')

                # Walls
                if row == 0:
                    mc.create_line(rx, ry, rx+cw, ry, fill='white', width=1)
                else:
                    gap = cw // 3
                    mc.create_line(rx, ry, rx+gap, ry, fill='white', width=1)
                    mc.create_line(rx+cw-gap, ry, rx+cw, ry, fill='white', width=1)

                if row == rows - 1:
                    mc.create_line(rx, ry+ch, rx+cw, ry+ch, fill='white', width=1)
                else:
                    gap = cw // 3
                    mc.create_line(rx, ry+ch, rx+gap, ry+ch, fill='white', width=1)
                    mc.create_line(rx+cw-gap, ry+ch, rx+cw, ry+ch, fill='white', width=1)

                if col == 0:
                    mc.create_line(rx, ry, rx, ry+ch, fill='white', width=1)
                else:
                    gap = ch // 3
                    mc.create_line(rx, ry, rx, ry+gap, fill='white', width=1)
                    mc.create_line(rx, ry+ch-gap, rx, ry+ch, fill='white', width=1)

                if col == cols - 1:
                    mc.create_line(rx+cw, ry, rx+cw, ry+ch, fill='white', width=1)
                else:
                    gap = ch // 3
                    mc.create_line(rx+cw, ry, rx+cw, ry+gap, fill='white', width=1)
                    mc.create_line(rx+cw, ry+ch-gap, rx+cw, ry+ch, fill='white', width=1)

                if is_current:
                    mc.create_rectangle(rx+1, ry+1, rx+cw-1, ry+ch-1,
                                        fill='', outline='#5555ff', width=1)

                if explored and key != (self.room_row, self.room_col):
                    room_obj = self.dungeon.get(key)
                    if room_obj:
                        boss_drawn = False
                        for e in room_obj.enemies[:6]:
                            ex = rx + 2 + int((e.x / WINDOW_W) * (cw - 4))
                            ey = ry + 2 + int((e.y / WINDOW_H) * (ch - 4))
                            if isinstance(e, Boss):
                                mc.create_oval(ex-3, ey-3, ex+3, ey+3,
                                               fill='#ff0000', outline='white', width=1)
                                boss_drawn = True
                            else:
                                mc.create_oval(ex-1, ey-1, ex+1, ey+1,
                                               fill='#ff3333', outline='')
                        # Always draw boss even if it falls beyond the [:6] cap
                        if not boss_drawn:
                            for e in room_obj.enemies:
                                if isinstance(e, Boss):
                                    ex = rx + 2 + int((e.x / WINDOW_W) * (cw - 4))
                                    ey = ry + 2 + int((e.y / WINDOW_H) * (ch - 4))
                                    mc.create_oval(ex-3, ey-3, ex+3, ey+3,
                                                   fill='#ff0000', outline='white', width=1)
                                    break

                if is_current:
                    boss_drawn_cur = False
                    for e in self.room.enemies[:8]:
                        ex = rx + 2 + int((e.x / WINDOW_W) * (cw - 4))
                        ey = ry + 2 + int((e.y / WINDOW_H) * (ch - 4))
                        if isinstance(e, Boss):
                            mc.create_oval(ex-4, ey-4, ex+4, ey+4,
                                           fill='#ff0000', outline='white', width=2)
                            boss_drawn_cur = True
                        else:
                            mc.create_oval(ex-1, ey-1, ex+1, ey+1,
                                           fill='#ff3333', outline='')
                    if not boss_drawn_cur:
                        for e in self.room.enemies:
                            if isinstance(e, Boss):
                                ex = rx + 2 + int((e.x / WINDOW_W) * (cw - 4))
                                ey = ry + 2 + int((e.y / WINDOW_H) * (ch - 4))
                                mc.create_oval(ex-4, ey-4, ex+4, ey+4,
                                               fill='#ff0000', outline='white', width=2)
                                break
                    ppx = rx + 2 + int((self.player.x / WINDOW_W) * (cw - 4))
                    ppy = ry + 2 + int((self.player.y / WINDOW_H) * (ch - 4))
                    mc.create_oval(ppx-2, ppy-2, ppx+2, ppy+2,
                                   fill='#4488ff', outline='white', width=1)

        mc.create_text(
            mx + ms//2, my + rows*ch + 8,
            text=f'Room ({self.room_row},{self.room_col})',
            fill='#5555aa', font=('Arial', 9)
        )

    def point_to_line_distance(self, px, py, x1, y1, x2, y2):
        """Calculate distance from point (px, py) to line segment (x1,y1)-(x2,y2)"""
        line_len_sq = (x2 - x1)**2 + (y2 - y1)**2
        if line_len_sq == 0:
            return math.hypot(px - x1, py - y1)
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_len_sq))
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        return math.hypot(px - proj_x, py - proj_y)

    def on_key_up(self,e): self.keys[e.keysym]=False

    def spawn_projectile(self, x, y, angle, speed, life, radius, color, damage, owner="player", ptype='normal', stype="basic"):
        proj = Projectile(x, y, angle, speed, life, radius, color, damage,
                          owner=owner, stype=stype, ptype=ptype)
        self.projectiles.append(proj)
        return proj
    def spawn_particle(self, x, y, size, color,
                       life=1, rtype="basic", owner=None):
        p = Particle(x, y, size, color, life, rtype, owner)
        self.particles.append(p)
        return p



    def damage_player(self,amount):
        if self.dead: return
        p = self.player
        amount = max(0, amount - p.constitution)
        # Kinetic Shell safety: if the skill is active but shield is empty, refill it
        if 'Kinetic Shell' in getattr(p, 'tree_unlocked', set()):
            if getattr(p, 'max_shield', 0) == 0:
                p.max_shield = p.vitality * 5
                p.shield = p.max_shield
            elif p.shield <= 0:
                pass  # shield depleted naturally; mana gain only triggers when shield absorbs
        # Shield absorbs damage first
        if getattr(p, 'max_shield', 0) > 0 and p.shield > 0:
            absorbed = min(p.shield, amount)
            p.shield -= absorbed
            amount -= absorbed
            p._shield_hit_time = time.time()
            # Kinetic Shell: gain mana equal to half the absorbed damage
            if absorbed > 0 and 'Kinetic Shell' in getattr(p, 'tree_unlocked', set()):
                p.mana = min(p.max_mana, p.mana + absorbed * 0.5)
        p.hp -= amount
        if p.hp <= 0:
            self.dead=True
            self.respawn_time=self.respawn_delay
            print("You died! Respawning...")
            # Clear all buffs and debuffs on death
            p.active_buffs = []
            p._frozen_until = 0
            p._freeze_ice_spawned = False
            p.speed = p.base_speed
            # Remove any frozen_ice particles attached to the player
            self.particles = [pt for pt in self.particles
                              if not (pt.rtype == 'frozen_ice'
                                      and getattr(pt, '_follow_entity', None) is p)]

    def damage_enemy(self, e, amount):
        e.hp -= amount
        if e.hp <= 0 and e in self.room.enemies:
            # Drop coin particles instead of awarding coins directly
            coins_total = max(1, int(e.max_hp / 10))
            num_coins = random.randint(1, min(5, coins_total))
            base_val = coins_total // num_coins
            remainder = coins_total - base_val * num_coins
            for i in range(num_coins):
                val = base_val + (1 if i == 0 and remainder > 0 else 0)
                self.coin_particles.append(CoinParticle(e.x, e.y, val))
            self.player.gain_xp(e.max_hp*2)
            self.room.enemies.remove(e)
    def update_entities(self,dt):
        now_freeze = time.time()
        # Reset speeds, but frozen entities stay frozen
        if getattr(self.player, '_frozen_until', 0) > now_freeze:
            self.player.speed = 0
        else:
            self.player.speed = self.player.base_speed
        for e in self.room.enemies:
            if getattr(e, '_frozen_until', 0) > now_freeze:
                e.spd = 0
            else:
                e.spd = e.base_spd

        # ── Indoor NPC wander — runs every frame when player is inside a building ──
        if self.current_interior:
            wall = 24
            indoor_npc_name = self.current_interior.get('indoor_npc_name')
            if indoor_npc_name:
                for npc in self.room.npcs:
                    if npc.name == indoor_npc_name:
                        npc.update_indoor(dt, wall, WINDOW_W, WINDOW_H)
                        break
        
        # Apply frost debuffs — frost particles freeze entities ONCE on first contact
        now_t = time.time()
        for part in self.particles:
            if part.rtype != "frost":
                continue
            if not hasattr(part, '_frozen_ids'):
                part._frozen_ids = set()   # tracks entity ids already frozen by this particle

            if part.owner == "player":
                for e in list(self.room.enemies):
                    eid = id(e)
                    if eid not in part._frozen_ids:
                        if distance((e.x, e.y), (part.x, part.y)) <= part.size + e.size:
                            # Apply freeze ONCE
                            e._frozen_until = now_t + 10.0
                            e._freeze_ice_spawned = False
                            part._frozen_ids.add(eid)

            elif part.owner == "enemy":
                p2 = self.player
                pid = id(p2)
                if pid not in part._frozen_ids:
                    if distance((p2.x, p2.y), (part.x, part.y)) <= part.size + p2.size:
                        p2._frozen_until = now_t + 10.0
                        p2._freeze_ice_spawned = False
                        part._frozen_ids.add(pid)

        # Unfreeze entities whose freeze has expired
        for e in self.room.enemies:
            if hasattr(e, '_frozen_until') and now_t >= e._frozen_until:
                e._frozen_until = 0
                e._freeze_ice_spawned = False
        p3 = self.player
        if hasattr(p3, '_frozen_until') and now_t >= p3._frozen_until:
            p3._frozen_until = 0
            p3._freeze_ice_spawned = False

        # Keep frozen_ice particles locked onto their entity
        for part in self.particles:
            if part.rtype == 'frozen_ice' and hasattr(part, '_follow_entity'):
                ent = part._follow_entity
                part.x = ent.x
                part.y = ent.y
        for e in list(self.room.enemies):
            if isinstance(e, Boss):
                e.update(dt, self)
            else:
                e.update(self)  # <--- CHANGE TO: e.update(self)
        for p in list(self.projectiles): p.update(dt,self)
        # Cosmetic fire particles — glow around fire projectiles each frame
        for _fp in self.projectiles:
            if getattr(_fp, 'ptype', '') == 'fire_proj' or getattr(_fp, 'stype', '') == 'fire_proj':
                for _ in range(2):
                    _ta = _fp.angle + random.uniform(-0.5, 0.5)
                    _td = random.uniform(0, _fp.radius)
                    _tx = _fp.x + math.cos(_ta)*_td
                    _ty = _fp.y + math.sin(_ta)*_td
                    _tp = Particle(_tx, _ty, random.uniform(3,7),
                                   random.choice(['orange','red','#ff6600']),
                                   life=0.25, rtype='fire_puff', owner=None)
                    self.particles.append(_tp)
        self.projectiles=[p for p in self.projectiles if p.life>0]
        for part in self.particles: part.update(dt, self)
        self.particles=[p for p in self.particles if p.life>0]
        # Tick coin particles
        self.coin_particles = [cp for cp in self.coin_particles if cp.update(dt)]
        self.player.unlock_skills()
        for s in list(self.summons):
            s.update(self, dt)
        if self.room.spawn_point:
            self.room.spawn_point.update(self)
        # Update beam
        if hasattr(self, 'player_beam') and self.player_beam:
            self.player_beam.update(dt)
            self.player_beam.update_origin(self.player.x, self.player.y)
            # Aim beam toward mouse
            _bm_wx, _bm_wy = self.get_mouse_world_pos()
            self.player_beam.angle = math.atan2(_bm_wy - self.player.y, _bm_wx - self.player.x)
            
            # Check if beam duration expired
            if hasattr(self, 'beam_active_until') and time.time() >= self.beam_active_until:
                self.player_beam = None
            
            # Damage enemies
            if self.player_beam and self.player_beam.current_length > 0:
                for e in list(self.room.enemies):
                    beam_end_x = self.player_beam.origin_x + math.cos(self.player_beam.angle) * self.player_beam.current_length
                    beam_end_y = self.player_beam.origin_y + math.sin(self.player_beam.angle) * self.player_beam.current_length
                    
                    dist_to_beam = self.point_to_line_distance(
                        e.x, e.y,
                        self.player_beam.origin_x, self.player_beam.origin_y,
                        beam_end_x, beam_end_y
                    )
                    
                    if dist_to_beam < e.size + self.player_beam.size/2:
                        self.damage_enemy(e, self.player.mag * dt * 5)
        if self.player.hp > 0 and self.player_beam:
            self.player_beam.update(dt)
            self.player_beam.update_origin(self.player.x, self.player.y)
            _bm2_wx, _bm2_wy = self.get_mouse_world_pos()
            self.player_beam.angle = math.atan2(_bm2_wy - self.player.y, _bm2_wx - self.player.x)
        else:
            self.player_beam = None
            self.beam_active_until = 0

        # --- Summon vs summon ---
        for i, s1 in enumerate(self.summons):
            for j, s2 in enumerate(self.summons):
                if i < j:
                    resolve_overlap(s1, s2)

        # --- Summon vs player ---
        for s in self.summons:
            resolve_overlap(s, self.player)

        # --- Summon vs enemy ---
        for s in self.summons:
            for e in self.room.enemies:
                resolve_overlap(s, e)
        if self.dungeon_id == 0:
            # Update NPCs — pass building list so they can avoid walls
            for npc in self.room.npcs:
                npc.update(dt, buildings=self.room.buildings)
            # Nearby NPC detection — only outdoor NPCs (indoor ones are inside buildings)
            self.nearby_npc = None
            for npc in self.room.npcs:
                if npc.indoor:
                    continue
                if distance((self.player.x, self.player.y), (npc.x, npc.y)) < 80:
                    self.nearby_npc = npc
                    break
            
            # Check for nearby dungeon entrances (using WORLD coordinates)
            self.nearby_dungeon = None
            for deco in self.room.decorations:
                if deco['type'] == 'dungeon_entrance':
                    if distance((self.player.x, self.player.y), (deco['x'], deco['y'])) < 80:
                        self.nearby_dungeon = deco
                        break
    def switch_room(self, new_row, new_col, new_x, new_y):
        self.room_row = new_row
        self.room_col = new_col
        self.player.x, self.player.y = new_x, new_y
        self.room = self.get_room(self.room_row, self.room_col)
        self.particles.clear()
        self.projectiles.clear()
        self.coin_particles.clear()   # coins belong to the old room
        
        # Reposition summons
        for s in self.summons:
            s.room_row = self.room_row
            s.room_col = self.room_col
            s.x = self.player.x + 20
            s.y = self.player.y + 20

    def update_player(self,dt):
        p=self.player
        now=time.time()
        p.hp=min(p.max_hp, p.hp+p.hp_regen*dt)
        p.mana=min(p.max_mana, p.mana+p.mana_regen*dt)

        # Shield regen — only after 4 s since last hit, very slow
        if getattr(p,'max_shield',0) > 0:
            last_hit = getattr(p,'_shield_hit_time',0)
            if now - last_hit >= 4.0:
                p.shield = min(p.max_shield, p.shield + p.shield_regen_rate * dt)

        # Expire temporary stat boosts from consumables
        stats_changed = False
        for attr, val_attr, end_attr in [
            ('strength', '_str_boost_val', '_str_boost_end'),
            ('agility',  '_agi_boost_val', '_agi_boost_end'),
            ('will',     '_wil_boost_val', '_wil_boost_end'),
        ]:
            val = getattr(p, val_attr, 0)
            if val and now >= getattr(p, end_attr, 0):
                setattr(p, attr, getattr(p, attr) - val)
                setattr(p, val_attr, 0)
                stats_changed = True
        if stats_changed:
            p.update_stats()
        # Expire buff display list
        if hasattr(p, 'active_buffs'):
            p.active_buffs = [b for b in p.active_buffs if now < b['end']]

        # ── Fire Breath channel: continuous flame particles for 5 seconds ──────
        if getattr(p, '_fire_breath_end', 0) > now:
            p._fire_breath_tick = getattr(p, '_fire_breath_tick', 0) + dt
            # Drain 15 mana/second; cancel if mana runs out
            mana_cost = 15 * dt
            if p.mana < mana_cost:
                p._fire_breath_end = 0
            else:
                p.mana -= mana_cost
                # Spawn a burst of flame particles every frame
                _mx, _my = self.get_mouse_world_pos()
                ang = math.atan2(_my - p.y, _mx - p.x)
                spread = 0.4
                for _ in range(16):
                    delta  = random.uniform(-spread, spread)
                    dist   = random.uniform(18, 140)
                    px2    = p.x + math.cos(ang + delta) * dist
                    py2    = p.y + math.sin(ang + delta) * dist
                    fl = Particle(
                        px2, py2,
                        random.uniform(4, 8),
                        random.choice(['orange', 'red', '#ff4400', '#ff6600', 'yellow']),
                        life=random.uniform(0.3, 0.6),
                        rtype='flame',
                        owner='player'
                    )
                    fl.damage = p.atk * 0.15
                    self.particles.append(fl)

        # ── Smoke Bomb: throw a projectile toward the mouse cursor ────────────
        if getattr(p, '_throw_smoke_bomb', False):
            p._throw_smoke_bomb = False
            _mx, _my = self.get_mouse_world_pos()
            ang = math.atan2(_my - p.y, _mx - p.x)
            proj = self.spawn_projectile(
                p.x, p.y, ang,
                9, 2.5, 10, '#888888',
                0, 'player',
                ptype='smoke_bomb', stype='smoke_bomb'
            )
            proj.hit_ids = set()

        # Coin particle collection
        for cp in list(self.coin_particles):
            dist = math.hypot(cp.x - p.x, cp.y - p.y)
            if dist < p.size + cp.size + 4:
                p.coins += cp.value
                self.coin_particles.remove(cp)

        # Universal death trigger — catches HP drops from ANY source (skills, direct hp-=, etc.)
        if not self.dead and p.hp <= 0:
            self.dead = True
            self.respawn_time = self.respawn_delay
            print("You died! Respawning...")
            # Clear all buffs and debuffs on death
            p.active_buffs = []
            p._frozen_until = 0
            p._freeze_ice_spawned = False
            p.speed = p.base_speed
            # Remove any frozen_ice particles attached to the player
            self.particles = [pt for pt in self.particles
                              if not (pt.rtype == 'frozen_ice'
                                      and getattr(pt, '_follow_entity', None) is p)]

        if self.dead:
            self.respawn_time -= dt
            if self.respawn_time<=0:
                self.particles.clear()
                self.projectiles.clear()
                self.coin_particles.clear()   # clear coin particles (wallet coins are kept)
                p.die()
                p.hp = p.max_hp; p.mana = p.max_mana
                # Restore energy shield to full on respawn
                if getattr(p, 'max_shield', 0) > 0:
                    p.shield = p.max_shield
                self.dead=False
                if hasattr(self, "player_beam"):
                    self.player_beam = None
                    self.beam_active_until = 0
                
                # Respawn at saved spawn point
                self.room_row = self.player_spawn_row
                self.room_col = self.player_spawn_col
                self.room = self.get_room(self.room_row, self.room_col)
                p.x = self.player_spawn_x
                p.y = self.player_spawn_y
                self.room.spawn_point.protection_end_time = time.time() + 2.0
                print(f"Respawned at room ({self.room_row}, {self.room_col})!")
            return
        
        # Store position before movement
        old_x, old_y = p.x, p.y

        # === INDOOR MOVEMENT ============================================
        if self.current_interior:
            building = self.current_interior
            ow = 24        # outer wall
            W, H  = WINDOW_W, WINDOW_H
            dg = 90        # door gap width (must match _get_interior_layout)
            exit_x0, exit_x1 = W//2 - dg//2, W//2 + dg//2

            # WASD
            if self.keys.get('w') or self.keys.get('Up'):    p.y -= p.speed
            if self.keys.get('s') or self.keys.get('Down'):  p.y += p.speed
            if self.keys.get('a') or self.keys.get('Left'):  p.x -= p.speed
            if self.keys.get('d') or self.keys.get('Right'): p.x += p.speed

            # Exit via bottom wall gap
            if p.y + p.size >= H - ow and exit_x0 < p.x < exit_x1:
                self.current_interior = None
                p.x = building['x'] + building['width'] // 2
                p.y = building['y'] + building['height'] + p.size + 8
                return

            # Wall + furniture collision using layout
            walls, objs_list = self._get_interior_layout(building)
            furn_rects = [o['collision'] for o in objs_list if 'collision' in o]
            all_rects  = walls + furn_rects
            sz = p.size

            def overlaps_wall(x, y):
                for wx1,wy1,wx2,wy2 in all_rects:
                    if wx1 < x+sz and x-sz < wx2 and wy1 < y+sz and y-sz < wy2:
                        return True
                return False

            if overlaps_wall(p.x, p.y):
                # Try axis-separated sliding
                if not overlaps_wall(p.x, old_y):
                    p.y = old_y
                elif not overlaps_wall(old_x, p.y):
                    p.x = old_x
                else:
                    p.x, p.y = old_x, old_y

            # Outer walls clamp
            p.x = clamp(p.x, ow + sz, W - ow - sz)
            p.y = clamp(p.y, ow + sz, H - ow - sz)

            # Chest interaction (F key or E key)
            if self.keys.get('f') or self.keys.get('e'):
                _, objs = self._get_interior_layout(building)
                for obj in objs:
                    if obj.get('type') == 'chest':
                        d = math.hypot(p.x - obj['x'] - 40, p.y - obj['y'] - 30)
                        if d < 80:
                            self.keys['f'] = False
                            self.keys['e'] = False
                            self.open_chest()
                            break

            # Update indoor NPC with furniture awareness
            npc_room = building.get('npc_room', 0)
            indoor_npc_name = building.get('indoor_npc_name')
            if indoor_npc_name:
                for npc in self.room.npcs:
                    if npc.name == indoor_npc_name:
                        npc.update_indoor(0, ow, W, H, furn_rects=furn_rects)
                        break
            return   # skip all outdoor logic
        # ================================================================
        # ========================================================================
        # Outdoor movement
        if self.keys.get('w') or self.keys.get('Up'):
            p.y -= p.speed
        if self.keys.get('s') or self.keys.get('Down'):
            p.y += p.speed
        if self.keys.get('a') or self.keys.get('Left'):
            p.x -= p.speed
        if self.keys.get('d') or self.keys.get('Right'):
            p.x += p.speed
        
        # Check if player actually moved (pressed a key)
        # Check if player actually moved (pressed a key)
        # Check if player actually moved (pressed a key)
        player_moved = (p.x != old_x or p.y != old_y)
        
        # === TOWN COLLISION DETECTION ===
        # === TOWN COLLISION DETECTION ===
        # === TOWN COLLISION DETECTION ===
        # === TOWN COLLISION DETECTION ===
        if self.dungeon_id == 0:
            # Check building collisions
            for building in self.room.buildings:
                bx, by = building['x'], building['y']
                bw, bh = building['width'], building['height']
                door_side = building.get('door_side', 'bottom')
                door_width = bw // 3
                
                if (p.x + p.size > bx and p.x - p.size < bx + bw and
                    p.y + p.size > by and p.y - p.size < by + bh):
                    
                    door_rect = None
                    if door_side == 'bottom':
                        door_rect = (bx + bw//2 - door_width//2, by + bh - 10,
                                    bx + bw//2 + door_width//2, by + bh + 10)
                    elif door_side == 'top':
                        door_rect = (bx + bw//2 - door_width//2, by - 10,
                                    bx + bw//2 + door_width//2, by + 10)
                    elif door_side == 'left':
                        door_rect = (bx - 10, by + bh//2 - door_width//2,
                                    bx + 10, by + bh//2 + door_width//2)
                    elif door_side == 'right':
                        door_rect = (bx + bw - 10, by + bh//2 - door_width//2,
                                    bx + bw + 10, by + bh//2 + door_width//2)
                    
                    if door_rect:
                        dx1, dy1, dx2, dy2 = door_rect
                        if (p.x + p.size > dx1 and p.x - p.size < dx2 and
                            p.y + p.size > dy1 and p.y - p.size < dy2):
                            # ── Enter building ──────────────────────────────
                            self._outdoor_px = p.x
                            self._outdoor_py = p.y
                            self.current_interior = building
                            self.current_interior_room = 0   # always start in room 0
                            # Spawn player near bottom-centre of the room
                            p.x = building.get('indoor_spawn_x', WINDOW_W // 2)
                            p.y = building.get('indoor_spawn_y', WINDOW_H - 60)
                            # Initialise indoor NPC position
                            indoor_npc_name = building.get('indoor_npc_name')
                            if indoor_npc_name:
                                for npc in self.room.npcs:
                                    if npc.name == indoor_npc_name:
                                        # Use the building's indoor_spawn as the NPC start so
                                        # it doesn't land inside furniture (e.g. Berta in the oven).
                                        npc_sx = building.get('indoor_spawn_x', WINDOW_W // 2)
                                        npc_sy = building.get('indoor_spawn_y', WINDOW_H - 60)
                                        npc.indoor_x = npc_sx
                                        npc.indoor_y = npc_sy
                                        npc._indoor_target = (npc_sx, npc_sy)
                                        break
                            return   # skip decoration check and world clamping
                    
                    p.x = old_x
                    p.y = old_y
            
            # Check decoration collisions (fountain, lamps, trees)
            if check_collision(p.x, p.y, p.size, self.room.decorations):
                p.x = old_x
                p.y = old_y
            
            # Expanded world boundaries
            # Expanded world boundaries
            # Expanded world boundaries
            p.x = clamp(p.x, WORLD_X_MIN + p.size, WORLD_WIDTH - p.size)
            p.y = clamp(p.y, WORLD_Y_MIN + p.size, WORLD_HEIGHT - p.size)
        # Wall collision detection (DUNGEON ONLY)
        
        # === DUNGEON WALL COLLISION ===
        elif self.dungeon_id > 0:
            wall_thickness = 20
            opening_size = 150
            player_size = p.size

            # Top wall collision
            # Top wall collision
            if p.y - player_size < wall_thickness:
                # SPECIAL CASE: Exit in dungeon room (0,0)
                if self.room_row == 0 and self.room_col == 0 and self.dungeon_id > 0:
                    opening_x_start = WINDOW_W // 2 - opening_size // 2
                    opening_x_end = opening_x_start + opening_size
                    if opening_x_start < p.x < opening_x_end:
                        # Player is in the green exit area - let them through!
                        print("Exiting dungeon!")

                        prev_dungeon_id = self.dungeon_id   # remember before reset

                        # ── Reset state ─────────────────────────────────────
                        self.dungeon_id = 0
                        self.room_row = 0
                        self.room_col = 0
                        self.dungeon = {}
                        self.room = self.get_room(0, 0)
                        self.projectiles.clear()
                        self.particles.clear()
                        self.summons.clear()
                        self.player_beam = None
                        self.beam_active_until = 0
                        if self.dead:
                            self.dead = False
                            p.hp = max(1, p.max_hp // 4)

                        # ── Find the matching portal in the town decorations ─
                        # Spawn 90 px away from it in the direction of the town
                        # centre so the player doesn't immediately re-enter.
                        portal_deco = None
                        for deco in self.room.decorations:
                            if (deco.get('type') == 'dungeon_entrance'
                                    and deco.get('dungeon_id') == prev_dungeon_id):
                                portal_deco = deco
                                break

                        if portal_deco:
                            px_world = portal_deco['x']
                            py_world = portal_deco['y']
                            # Push the spawn point 90 px towards the town centre
                            town_cx = (TOWN_X_START + TOWN_X_END) // 2
                            town_cy = (TOWN_Y_START + TOWN_Y_END) // 2
                            ang = math.atan2(town_cy - py_world, town_cx - px_world)
                            exit_x = int(px_world + math.cos(ang) * 90)
                            exit_y = int(py_world + math.sin(ang) * 90)
                        else:
                            # Fallback — centre of town
                            exit_x = (TOWN_X_START + TOWN_X_END) // 2
                            exit_y = (TOWN_Y_START + TOWN_Y_END) // 2

                        p.x = exit_x
                        p.y = exit_y
                        self.camera_x = exit_x - WINDOW_W // 2
                        self.camera_y = exit_y - WINDOW_H // 2
                        return
                    else:
                        # Outside exit area - block them
                        p.y = wall_thickness + player_size
                elif self.room_row == 0:  # Regular solid wall
                    p.y = wall_thickness + player_size
                else:  # Check if in opening
                    opening_x_start = WINDOW_W // 2 - opening_size // 2
                    opening_x_end = opening_x_start + opening_size
                    if p.x < opening_x_start or p.x > opening_x_end:
                        p.y = wall_thickness + player_size
            # Bottom wall collision
            if p.y + player_size > WINDOW_H - wall_thickness:
                if self.room_row == ROOM_ROWS - 1:  # Solid wall
                    p.y = WINDOW_H - wall_thickness - player_size
                else:  # Check if in opening
                    opening_x_start = WINDOW_W // 2 - opening_size // 2
                    opening_x_end = opening_x_start + opening_size
                    if p.x < opening_x_start or p.x > opening_x_end:
                        p.y = WINDOW_H - wall_thickness - player_size

            # Left wall collision
            if p.x - player_size < wall_thickness:
                if self.room_col == 0:  # Solid wall
                    p.x = wall_thickness + player_size
                else:  # Check if in opening
                    opening_y_start = WINDOW_H // 2 - opening_size // 2
                    opening_y_end = opening_y_start + opening_size
                    if p.y < opening_y_start or p.y > opening_y_end:
                        p.x = wall_thickness + player_size

            # Right wall collision
            if p.x + player_size > WINDOW_W - wall_thickness:
                if self.room_col == ROOM_COLS - 1:  # Solid wall
                    p.x = WINDOW_W - wall_thickness - player_size
                else:  # Check if in opening
                    opening_y_start = WINDOW_H // 2 - opening_size // 2
                    opening_y_end = opening_y_start + opening_size
                    if p.y < opening_y_start or p.y > opening_y_end:
                        p.x = WINDOW_W - wall_thickness - player_size
            
            # Room transitions - only trigger if player is actively moving
            margin = 10
            
            if player_moved:
                if p.x < 0 and self.room_col > 0:
                    self.switch_room(self.room_row, self.room_col - 1, WINDOW_W - margin, p.y)
                    return  # Skip clamping this frame since we switched rooms
                elif p.x > WINDOW_W and self.room_col < ROOM_COLS - 1:
                    self.switch_room(self.room_row, self.room_col + 1, margin, p.y)
                    return
                elif p.y < 0 and self.room_row > 0:
                    self.switch_room(self.room_row - 1, self.room_col, p.x, WINDOW_H - margin)
                    return
                elif p.y > WINDOW_H and self.room_row < ROOM_ROWS - 1:
                    self.switch_room(self.room_row + 1, self.room_col, p.x, margin)
                    return
            
            # Clamp inside current room (only if we didn't switch rooms)
            p.x = clamp(p.x, 0, WINDOW_W)
            p.y = clamp(p.y, 0, WINDOW_H)

        # Hotbar: 1-5 selects a slot; left-click fires the selected skill (handled in on_canvas_click)

    def handle_stat_click(self, event):
        if not self.show_stats or self.player.stat_points <= 0:
            return
        
        mx, my = event.x, event.y
        stat_y_start = 120
        stat_height = 40  # matches the new spacing in draw_stats_panel
        stats = ['strength','vitality','agility','constitution','intelligence','wisdom','will']
        
        for i, stat in enumerate(stats):
            btn_x = 660
            btn_y = stat_y_start + i * stat_height
            btn_w, btn_h = 28, 28

            if btn_x < mx < btn_x + btn_w and btn_y < my < btn_y + btn_h:
                setattr(self.player, stat, getattr(self.player, stat) + 1)
                self.player.stat_points -= 1
                self.player.update_stats()
                break  # stop after one click is processed

    def draw(self):
        self.canvas.delete('all')
        # Full black background — eliminates any white gap at bottom or sides
        self.canvas.create_rectangle(0, 0, WINDOW_W + 200, WINDOW_H + 200, fill='black', outline='')

        # Update camera
        if self.dungeon_id == 0:
            self.update_camera()
            cam_x, cam_y = self.camera_x, self.camera_y
        else:
            cam_x, cam_y = 0, 0
        
        # === TOWN RENDERING ===

# === TOWN RENDERING ===

        if self.dungeon_id == 0:
            px, py = self.player.x - cam_x, self.player.y - cam_y
            
            # === INTERIOR VIEW ===
            if self.current_interior:
                building = self.current_interior
                btype    = building.get('type','')
                npc_id   = building.get('indoor_npc_name','')
                cv       = self.canvas
                now      = time.time()
                W, H     = WINDOW_W, WINDOW_H
                ow       = 30
                dg       = 100

                walls_list, objs = self._get_interior_layout(building)

                # ── Animated helpers ──────────────────────────────────
                def fire(cx,cy,fw=40,fh=55,t=0):
                    fl=abs(math.sin(t*7))*7
                    cv.create_polygon(cx-fw//2,cy,cx+fw//2,cy,cx+fw//3,cy-fh//2,cx,cy-fh-int(fl),cx-fw//3,cy-fh//2,fill='#FF5500',outline='')
                    cv.create_polygon(cx-fw//3,cy,cx+fw//3,cy,cx,cy-fh//2-int(fl),fill='#FFD700',outline='')
                    cv.create_oval(cx-7,cy-fh//3,cx+7,cy-fh//3+12,fill='#fff8e0',outline='')

                def glow(cx,cy,r,col,t=0,speed=2):
                    pr=r+int(abs(math.sin(t*speed))*8)
                    cv.create_oval(cx-pr,cy-pr,cx+pr,cy+pr,fill='',outline=col,width=2,stipple='gray50')
                    cv.create_oval(cx-r,cy-r,cx+r,cy+r,fill='',outline=col,width=1)

                def bubble(cx,cy,phase,col='#88ffaa'):
                    by=cy-int(phase*55); br=max(1,int(7*(1-phase*0.6)))
                    cv.create_oval(cx-br,by-br,cx+br,by+br,fill=col,outline='white',width=1)

                def lantern_draw(cx,cy,t=0):
                    gr=32+int(math.sin(t*2.5)*6)
                    cv.create_oval(cx-gr,cy-gr,cx+gr,cy+gr,fill='#ffcc44',outline='',stipple='gray25')
                    cv.create_rectangle(cx-12,cy-22,cx+12,cy+16,fill='#2a2a2a',outline='#888',width=1)
                    cv.create_oval(cx-9,cy-18,cx+9,cy+12,fill='#FFD700',outline='')
                    cv.create_line(cx,cy-22,cx,cy-36,fill='#888',width=3)

                # ── Floor ────────────────────────────────────────────
                floor_map = {
                    'house':       ('#5a4030','#4a3a20'),
                    'library':     ('#3a2a18','#2e2010'),
                    'blacksmith':  ('#1e1e14','#171710'),
                    'tower':       ('#12102a','#0e0c22'),
                    'inn':         ('#3a2a18','#2e2010'),
                }
                alch_npc = btype=='shop' and npc_id=='Zephyr'
                if alch_npc:
                    cv.create_rectangle(0,0,W,H,fill='#081a0a',outline='')
                    # Green tinted floor planks
                    for py2 in range(0,H,28):
                        cv.create_line(0,py2,W,py2,fill='#0d2a10',width=1)
                else:
                    f1,f2=floor_map.get(btype,('#3a3030','#302828'))
                    cv.create_rectangle(0,0,W,H,fill=f1,outline='')
                    # Floor boards
                    for py2 in range(0,H,30):
                        cv.create_line(0,py2,W,py2,fill=f2,width=1)

                # ── Outer walls ──────────────────────────────────────
                wall_col={'house':'#5c3a20','library':'#6b4520','blacksmith':'#1a1a0e',
                          'tower':'#2a1060','inn':'#4a2800'}.get(btype,'#4a3020')
                if alch_npc: wall_col='#1a3a1a'
                for rect in [(0,0,W,ow),(0,H-ow,W,H),(0,0,ow,H),(W-ow,0,W,H)]:
                    cv.create_rectangle(*rect,fill=wall_col,outline='')
                # Wall trim
                for rect in [(ow,ow,W-ow,ow+6),(ow,H-ow-6,W-ow,H-ow),(ow,ow,ow+6,H-ow),(W-ow-6,ow,W-ow,H-ow)]:
                    cv.create_rectangle(*rect,fill='#2a1a0a',outline='')

                # ── Inner divider walls ──────────────────────────────
                for wx1,wy1,wx2,wy2 in walls_list:
                    cv.create_rectangle(wx1,wy1,wx2,wy2,fill=wall_col,outline='')

                # ── Exit gap ─────────────────────────────────────────
                ex0,ex1=W//2-dg//2,W//2+dg//2
                cv.create_rectangle(ex0,H-ow,ex1,H,fill=f1 if not alch_npc else '#081a0a',outline='')
                # Door frame
                cv.create_rectangle(ex0-4,H-ow-2,ex0,H,fill='#5c3a20',outline='')
                cv.create_rectangle(ex1,H-ow-2,ex1+4,H,fill='#5c3a20',outline='')
                cv.create_text(W//2,H-ow//2,text='EXIT',fill='#ffd080',font=('Arial',8,'bold'))

                # Building name
                cv.create_text(W//2,ow//2,text=building.get('name',''),fill='#ffd700',font=('Arial',13,'bold'))

                # ── Draw each furniture object ────────────────────────
                for obj in objs:
                    ot=obj.get('type')
                    ox,oy=obj.get('x',0),obj.get('y',0)
                    ow2,oh2=obj.get('w',0),obj.get('h',0)

                    if ot=='collision_only': pass

                    elif ot=='label':
                        cv.create_text(ox,oy,text=obj.get('text',''),fill=obj.get('color','#888'),font=('Arial',9,'bold'))

                    # ── BOOKCASE UNIT — the detailed shelving ─────────
                    elif ot in ('bookcase_unit','shelf_cabinet'):
                        side=obj.get('side','left')
                        # Rich varied palette — dark AND light spines like the reference image
                        BOOK_COLS=[
                            '#8B1A1A','#B02020','#1A3A8B','#2850AA','#1A6B1A','#2A8B2A',
                            '#8B7A1A','#AA9A20','#6B1A6B','#8B2A8B','#1A6B6B','#2A8B8B',
                            '#8B4A1A','#C06020','#4A1A8B','#6A3AAB',
                            '#C8A060','#D4B87A','#6A8080','#5A7070',  # lighter aged books
                            '#A03030','#304080','#306030','#807020',
                        ]
                        if side in ('left','right','back') or ot=='shelf_cabinet':
                            # ── 3-D SIDE BOOKCASE ────────────────────────────────────
                            cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#1a0e04',outline='')
                            FRAME='#2e1a06'; FRAME_LT='#5a3812'; FRAME_SH='#180e02'
                            frame_t=6
                            cv.create_rectangle(ox,oy,ox+frame_t,oy+oh2,fill=FRAME,outline='')
                            cv.create_rectangle(ox,oy,ox+frame_t-1,oy+oh2,fill=FRAME_LT,outline='')
                            cv.create_rectangle(ox+ow2-frame_t,oy,ox+ow2,oy+oh2,fill=FRAME_SH,outline='')
                            cv.create_rectangle(ox,oy,ox+ow2,oy+frame_t,fill=FRAME_LT,outline='')
                            cv.create_rectangle(ox,oy+oh2-frame_t,ox+ow2,oy+oh2,fill=FRAME_SH,outline='')
                            cap=8
                            cv.create_polygon(ox,oy, ox+ow2,oy, ox+ow2-cap,oy-cap, ox+cap,oy-cap,
                                              fill='#7a5020',outline='#3a2010',width=1)
                            # Fewer, taller bays
                            shelf_spacing=max(55,oh2//4)
                            n_shelves=oh2//shelf_spacing
                            for shi in range(n_shelves):
                                sy=oy+shi*shelf_spacing
                                bay_h=shelf_spacing-frame_t
                                cv.create_rectangle(ox+frame_t,sy+bay_h,ox+ow2-frame_t,sy+bay_h+frame_t,fill='#4a2e0c',outline='')
                                cv.create_rectangle(ox+frame_t,sy+bay_h,ox+ow2-frame_t,sy+bay_h+2,fill='#7a5820',outline='')
                                cv.create_rectangle(ox+frame_t,sy+bay_h+frame_t-2,ox+ow2-frame_t,sy+bay_h+frame_t,fill='#1a0e04',outline='')
                                cv.create_rectangle(ox+frame_t,sy+bay_h+frame_t,ox+ow2-frame_t,sy+bay_h+frame_t+4,fill='#140a02',outline='')
                                book_floor=sy+bay_h-2
                                bx=ox+frame_t+3
                                # Use a per-book hash for independent width, height and colour
                                book_idx=0
                                while bx < ox+ow2-frame_t-6:
                                    # unique seed per book
                                    seed=(shi*97+book_idx*53+int(ox)*7+int(oy)*3)&0xFFFF
                                    # width: 10-22 px — varied
                                    bw_b=10+seed%13
                                    bw_b=min(bw_b,ox+ow2-frame_t-6-bx)
                                    if bw_b<6: break
                                    # height: dramatic variation — 40% to 95% of bay
                                    h_frac=0.40+((seed>>4)%12)*0.05   # 0.40..0.95
                                    bh_b=max(8,min(int(bay_h*h_frac),bay_h-4))
                                    bc=BOOK_COLS[seed%len(BOOK_COLS)]
                                    by_b=book_floor-bh_b
                                    cv.create_rectangle(bx,by_b,bx+bw_b,book_floor,fill=bc,outline='#0a0604',width=1)
                                    cv.create_line(bx+1,by_b+1,bx+1,book_floor-1,fill='#886644',width=1)
                                    if bw_b>=10:
                                        cv.create_line(bx+2,by_b+5,bx+bw_b-2,by_b+5,fill='#998866',width=1)
                                        if bh_b>20:
                                            cv.create_line(bx+2,by_b+10,bx+bw_b-2,by_b+10,fill='#776644',width=1)
                                    cv.create_rectangle(bx,by_b,bx+bw_b,by_b+3,fill='#e8d8b0',outline='')
                                    bx+=bw_b+2
                                    book_idx+=1
                        else:  # top / horizontal shelf (seen from above)
                            # ── 3-D TOP BOOKCASE ─────────────────────────────────────
                            cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#1a0e04',outline='')
                            FRAME='#2e1a06'; FRAME_LT='#5a3812'; FRAME_SH='#180e02'
                            frame_t=6
                            cv.create_rectangle(ox,oy,ox+ow2,oy+frame_t,fill=FRAME_LT,outline='')
                            cv.create_rectangle(ox,oy+oh2-frame_t,ox+ow2,oy+oh2,fill=FRAME_SH,outline='')
                            cv.create_rectangle(ox,oy,ox+frame_t,oy+oh2,fill=FRAME_LT,outline='')
                            cv.create_rectangle(ox+ow2-frame_t,oy,ox+ow2,oy+oh2,fill=FRAME_SH,outline='')
                            # top surface cap
                            cap=8
                            cv.create_polygon(ox,oy, ox+ow2,oy, ox+ow2-cap,oy-cap, ox+cap,oy-cap,
                                              fill='#7a5020',outline='#3a2010',width=1)
                            col_spacing=max(32,ow2//10)
                            n_bays=ow2//col_spacing
                            for shi in range(n_bays):
                                sx=ox+shi*col_spacing
                                bay_w=col_spacing-frame_t
                                # vertical divider
                                cv.create_rectangle(sx+bay_w,oy+frame_t,sx+bay_w+frame_t,oy+oh2-frame_t,fill=FRAME,outline='')
                                cv.create_rectangle(sx+bay_w,oy+frame_t,sx+bay_w+1,oy+oh2-frame_t,fill=FRAME_LT,outline='')
                                # books standing upright in bay (seen from front edge)
                                by2=oy+frame_t+2
                                book_seed2=shi*17+int(oy)
                                while by2 < oy+oh2-frame_t-4:
                                    bh2=max(7,min(14,oy+oh2-frame_t-4-by2))
                                    bw2=bay_w-2
                                    bc2=BOOK_COLS[(book_seed2+by2)%16]
                                    cv.create_rectangle(sx+frame_t+1,by2,sx+frame_t+1+bw2,by2+bh2,fill=bc2,outline='#0a0604',width=1)
                                    cv.create_rectangle(sx+frame_t+1,by2,sx+frame_t+1+bw2,by2+2,fill='#e8d8b0',outline='')
                                    if bw2>=8:
                                        cv.create_line(sx+frame_t+3,by2+4,sx+frame_t+bw2-2,by2+4,fill='#998866',width=1)
                                    by2+=bh2+1

                    elif ot=='weapon_rack_h':
                        cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#3a2808',outline='#1a1208',width=2)
                        # Metal hooks
                        for hi in range(0,ow2,40):
                            hx=ox+hi+20
                            cv.create_oval(hx-4,oy+oh2-6,hx+4,oy+oh2+2,fill='#888',outline='#444')

                    elif ot=='weapon_rack_v':
                        cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#3a2808',outline='#1a1208',width=2)
                        for hi in range(0,oh2,40):
                            hy=oy+hi+20
                            cv.create_oval(ox+ow2-6,hy-4,ox+ow2+2,hy+4,fill='#888',outline='#444')

                    elif ot=='hung_weapon':
                        wx,wy=ox,oy
                        wt=obj.get('weapon','sword')
                        orient=obj.get('orient','v')
                        if orient=='v':  # hanging down
                            if wt=='sword':
                                cv.create_line(wx,wy-30,wx,wy+35,fill='#aaaaaa',width=5)
                                cv.create_line(wx-14,wy-4,wx+14,wy-4,fill='#888',width=4)
                                cv.create_polygon(wx-3,wy-30,wx+3,wy-30,wx,wy-50,fill='#cccccc',outline='#888')
                                cv.create_oval(wx-5,wy+30,wx+5,wy+40,fill='#8B4513',outline='#5a2a00')
                            elif wt=='axe':
                                cv.create_line(wx,wy-25,wx,wy+30,fill='#8B4513',width=6)
                                cv.create_polygon(wx-18,wy-25,wx+6,wy-35,wx+6,wy-5,wx-12,wy-5,fill='#888',outline='#555',width=2)
                            elif wt=='spear':
                                cv.create_line(wx,wy-45,wx,wy+45,fill='#8B4513',width=4)
                                cv.create_polygon(wx-5,wy-45,wx+5,wy-45,wx,wy-65,fill='#aaa',outline='#777')
                        else:  # horizontal
                            if wt=='sword':
                                cv.create_line(wx-35,wy,wx+35,wy,fill='#aaaaaa',width=5)
                                cv.create_line(wx-4,wy-14,wx-4,wy+14,fill='#888',width=4)
                                cv.create_polygon(wx-35,wy-3,wx-35,wy+3,wx-55,wy,fill='#cccccc',outline='#888')
                            elif wt=='axe':
                                cv.create_line(wx-30,wy,wx+30,wy,fill='#8B4513',width=6)
                                cv.create_polygon(wx+20,wy-18,wx+35,wy-4,wx+20,wy+6,wx+10,wy-2,fill='#888',outline='#555',width=2)
                            elif wt=='spear':
                                cv.create_line(wx-45,wy,wx+45,wy,fill='#8B4513',width=4)
                                cv.create_polygon(wx+45,wy-5,wx+45,wy+5,wx+65,wy,fill='#aaa',outline='#777')

                    elif ot=='open_forge':
                        r=obj.get('r',90)
                        rh=r//2   # ellipse half-height (top-down perspective)
                        wall=14   # visible wall thickness
                        # ── 3-D raised stone wall ─────────────────────────
                        # Shadow/base beneath wall (gives depth illusion)
                        cv.create_oval(ox-r-4,oy-rh+wall+4,ox+r+4,oy+rh+wall+4,fill='#1a1408',outline='')
                        # Outer wall face (front-facing, darker = vertical surface)
                        cv.create_oval(ox-r,oy-rh+wall,ox+r,oy+rh+wall,fill='#2a2418',outline='#111008',width=3)
                        # Stone blocks on front wall face
                        for si2 in range(10):
                            a2=si2*math.pi/5
                            if math.sin(a2)>-0.1:  # only front-facing stones
                                sx2=ox+int(math.cos(a2)*(r-6))
                                sy2=oy+rh+wall-8+int(math.sin(a2)*(rh-4))
                                cv.create_rectangle(sx2-10,sy2-5,sx2+10,sy2+4,fill='#3a3225',outline='#1a1412',width=1)
                        # Top surface of wall ring (lit face — lighter)
                        cv.create_oval(ox-r,oy-rh,ox+r,oy+rh,fill='#4a4232',outline='#5a5242',width=3)
                        # Individual stone block highlights on top surface
                        for si2 in range(14):
                            a2=si2*math.pi/7
                            sx2=ox+int(math.cos(a2)*(r*0.88))
                            sy2=oy+int(math.sin(a2)*(rh*0.88))
                            cv.create_oval(sx2-9,sy2-6,sx2+9,sy2+6,fill='#5a5038',outline='#2a2818',width=1)
                            # Lit top highlight on each stone
                            cv.create_oval(sx2-6,sy2-4,sx2+4,sy2+1,fill='#6a6045',outline='')
                        # ── Fire pit interior ─────────────────────────────
                        ir=r-wall-4
                        irh=rh-wall//2-2
                        # Pit floor (deep charcoal)
                        cv.create_oval(ox-ir,oy-irh,ox+ir,oy+irh,fill='#0e0600',outline='')
                        # Glowing embers bed
                        for ei in range(14):
                            a=now*0.4+ei*0.449
                            ex2=ox+int(math.cos(a)*(ir-12))
                            ey2=oy+int(math.sin(a)*(irh-8))
                            ec=['#cc1100','#ee3300','#ff5500','#ff8800','#ffaa00'][ei%5]
                            cv.create_oval(ex2-6,ey2-4,ex2+6,ey2+4,fill=ec,outline='')
                        # Inner glow halo
                        glow(ox,oy,ir-8,'#ff4400',now,speed=2)
                        # Fire tongues rising from centre
                        for fi in range(5):
                            ang2=fi*1.2566+now*0.3
                            fx2=ox+int(math.cos(ang2)*(ir-22))
                            fy2=oy+int(math.sin(ang2)*(irh-14))
                            fire(fx2,fy2,fw=28,fh=42,t=now+fi*0.3)

                    elif ot=='arch_oven':
                        # Stone surround
                        cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#4a4a3a',outline='#2a2a1a',width=4)
                        # Brick rows
                        for ri2 in range(oh2//20):
                            for ci2 in range(ow2//32):
                                off2=16 if ri2%2 else 0
                                bx2=ox+4+ci2*32+off2; by2=oy+4+ri2*20
                                if bx2+26<ox+ow2-4:
                                    cv.create_rectangle(bx2,by2,bx2+26,by2+16,fill='#5a4a38',outline='#3a2a1a',width=1)
                        # Arch opening — large
                        aw=int(ow2*0.6); ah=int(oh2*0.55)
                        ax2=ox+ow2//2-aw//2; ay2=oy+oh2-ah-10
                        # Stone arch frame
                        cv.create_arc(ax2-8,ay2-8,ax2+aw+8,ay2+ah,start=0,extent=180,fill='#333322',outline='#222211',width=4)
                        # Dark interior
                        cv.create_arc(ax2,ay2,ax2+aw,ay2+ah,start=0,extent=180,fill='#110600',outline='')
                        cv.create_rectangle(ax2,ay2+ah//2,ax2+aw,ay2+ah,fill='#110600',outline='')
                        # Fire inside
                        fire(ax2+aw//2,ay2+ah,fw=aw-16,fh=ah-8,t=now)
                        # Orange glow reflecting on stone
                        glow(ax2+aw//2,ay2+ah//2,aw//2,'#ff6600',now,speed=3)

                    elif ot=='big_cauldron':
                        r=obj.get('r',50)
                        lc=obj.get('liq_color','#44ff44')
                        # Tripod legs
                        for la in [math.pi*0.25,math.pi*0.75,math.pi*1.5]:
                            lx2=ox+int(math.cos(la)*(r-6)); ly2=oy+int(math.sin(la)*(r//2))
                            cv.create_line(int(lx2),int(ly2),int(lx2)+int(math.cos(la)*12),int(ly2)+int(math.sin(la)*20)+r//2,fill='#555',width=6)
                        # Main bowl
                        cv.create_oval(ox-r,oy-r//2,ox+r,oy+r//2,fill='#1a1a1a',outline='#555',width=4)
                        # Rim
                        cv.create_oval(ox-r-2,oy-r//2-6,ox+r+2,oy-r//2+8,fill='#2a2a2a',outline='#666',width=3)
                        # Side handles
                        for hx2 in [ox-r-10,ox+r+10]:
                            cv.create_oval(hx2-9,oy-r//4-9,hx2+9,oy-r//4+9,fill='#333',outline='#666',width=2)
                        # Bubbling liquid
                        lc2=lc
                        cv.create_oval(ox-r+7,oy-r//2+8,ox+r-7,oy+r//4,fill=lc2,outline='')
                        # Surface sheen
                        cv.create_oval(ox-r+12,oy-r//2+10,ox+r-12,oy-r//2+22,fill='',outline='#aaaaaa',width=2)
                        # Bubbles rising
                        for bi2 in range(6):
                            ph=(now*0.7+bi2*0.17)%1.0
                            bubble(ox-r//2+bi2*(r//3),oy-r//4,ph,col=lc)
                        # Steam wisps
                        for si3 in range(3):
                            sa=now*2+si3*2.094
                            sv=int(abs(math.sin(now*3+si3))*18)
                            cv.create_oval(ox+int(math.cos(sa)*r//3)-6,oy-r//2-sv-8,
                                           ox+int(math.cos(sa)*r//3)+6,oy-r//2-sv,
                                           fill='#666666',outline='')
                        # Fire under cauldron
                        fire(ox,oy+r//2+10,fw=r,fh=r//2,t=now)

                    elif ot=='magic_circle_floor':
                        r=obj.get('r',120)
                        pulse=abs(math.sin(now*1.2))*12
                        # Glowing outer rings
                        for ri3,ro,rw in [(r+int(pulse),'#001122',1),(r,'#003366',2),(r-18,'#0055aa',3)]:
                            cv.create_oval(ox-ri3,oy-ri3,ox+ri3,oy+ri3,fill='',outline=ro,width=rw)
                        # Inner fill
                        cv.create_oval(ox-r,oy-r,ox+r,oy+r,fill='#00050f',outline='')
                        # Rotating pentagram
                        rot=now*0.2
                        pts5=[]
                        for k in range(5):
                            a5=rot+k*2*math.pi/5-math.pi/2
                            pts5.append((ox+int(math.cos(a5)*r),oy+int(math.sin(a5)*r)))
                        for k in range(5):
                            p1=pts5[k]; p2=pts5[(k+2)%5]
                            cv.create_line(p1[0],p1[1],p2[0],p2[1],fill='#00aaff',width=2)
                        # Inner pentagon glow
                        for k in range(5):
                            cv.create_line(pts5[k][0],pts5[k][1],pts5[(k+1)%5][0],pts5[(k+1)%5][1],fill='#004488',width=1)
                        # Rune marks rotating opposite
                        rune_r=r-25
                        for k in range(8):
                            a8=-now*0.4+k*math.pi/4
                            rx3=ox+int(math.cos(a8)*rune_r); ry3=oy+int(math.sin(a8)*rune_r)
                            cv.create_text(rx3,ry3,text=['✦','★','◆','⬡','✧','◇','⬟','◈'][k],fill='#0088cc',font=('Arial',10))
                        # Centre glow
                        cg=18+int(pulse*0.5)
                        cv.create_oval(ox-cg,oy-cg,ox+cg,oy+cg,fill='#001a33',outline='#00ddff',width=3)
                        cv.create_oval(ox-8,oy-8,ox+8,oy+8,fill='#88eeff',outline='')

                    elif ot=='bed':
                        # Headboard
                        cv.create_rectangle(ox,oy,ox+ow2,oy+28,fill='#5c3010',outline='#3a1a08',width=3)
                        cv.create_rectangle(ox+8,oy+4,ox+ow2-8,oy+22,fill='#7a4018',outline='#3a1a08',width=1)
                        # Mattress
                        cv.create_rectangle(ox,oy+28,ox+ow2,oy+oh2,fill='#c8c0a0',outline='#888870',width=2)
                        # Pillow(s)
                        n_pil=max(1,ow2//110)
                        pil_w=ow2//n_pil-16
                        for pi2 in range(n_pil):
                            px2=ox+8+pi2*(ow2//n_pil)
                            cv.create_rectangle(px2,oy+32,px2+pil_w,oy+32+pil_w//2,fill='#ffffff',outline='#cccccc',width=1)
                        # Blanket
                        cv.create_polygon(ox,oy+50,ox+ow2,oy+50,ox+ow2,oy+oh2,ox,oy+oh2,fill='#5a3a7a',outline='#3a2050',width=2)
                        # Blanket fold
                        cv.create_polygon(ox,oy+50,ox+ow2,oy+50,ox+ow2,oy+65,ox,oy+68,fill='#7a5a9a',outline='#3a2050',width=1)
                        # Footboard
                        cv.create_rectangle(ox,oy+oh2-14,ox+ow2,oy+oh2,fill='#5c3010',outline='#3a1a08',width=2)

                    elif ot=='wardrobe':
                        cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#5c3010',outline='#3a1a08',width=3)
                        # Two door panels
                        mid=ox+ow2//2
                        cv.create_line(mid,oy+4,mid,oy+oh2-4,fill='#3a1a08',width=2)
                        for dx2 in [ox+4,mid+4]:
                            cv.create_rectangle(dx2,oy+8,dx2+ow2//2-10,oy+oh2-8,fill='#6a3818',outline='#3a1a08',width=1)
                        # Handles
                        cv.create_oval(mid-10,oy+oh2//2-6,mid-2,oy+oh2//2+6,fill='#FFD700',outline='#DAA520',width=1)
                        cv.create_oval(mid+2,oy+oh2//2-6,mid+10,oy+oh2//2+6,fill='#FFD700',outline='#DAA520',width=1)

                    elif ot=='chest':
                        has=bool(self.player.chest_items)
                        cc='#c8940a' if has else '#8B6914'; lc2='#FFD700' if has else '#A0804A'
                        # Main body
                        cv.create_rectangle(ox,oy+22,ox+ow2,oy+oh2,fill=cc,outline='#5a3a00',width=3)
                        # Lid
                        cv.create_rectangle(ox,oy,ox+ow2,oy+24,fill=lc2,outline='#5a3a00',width=3)
                        # Metal bands
                        cv.create_line(ox,oy+oh2//2,ox+ow2,oy+oh2//2,fill='#5a3a00',width=3)
                        # Lock
                        cv.create_rectangle(ox+ow2//2-8,oy+14,ox+ow2//2+8,oy+oh2//2,fill='#888',outline='#444',width=2)
                        cv.create_oval(ox+ow2//2-5,oy+18,ox+ow2//2+5,oy+28,fill='#555',outline='#333')
                        # Sparkle
                        if has:
                            for si4 in range(5):
                                a4=now*2+si4*1.257
                                cv.create_oval(ox+ow2//2+int(math.cos(a4)*36)-3,oy+oh2//2+int(math.sin(a4)*24)-3,
                                               ox+ow2//2+int(math.cos(a4)*36)+3,oy+oh2//2+int(math.sin(a4)*24)+3,
                                               fill='#FFD700',outline='')
                        d=math.hypot(self.player.x-(ox+ow2//2),self.player.y-(oy+oh2//2))
                        if d<90:
                            cv.create_text(ox+ow2//2,oy-16,text='F / E to Open',fill='#FFD700',font=('Arial',11,'bold'))

                    elif ot=='fireplace':
                        # Stone surround
                        cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#4a4030',outline='#2a2010',width=4)
                        # Brick pattern
                        for ri4 in range(oh2//18):
                            for ci3 in range(ow2//26):
                                off3=13 if ri4%2 else 0
                                cv.create_rectangle(ox+3+ci3*26+off3,oy+3+ri4*18,ox+3+ci3*26+off3+21,oy+3+ri4*18+14,fill='#6a4a30',outline='#2a2010',width=1)
                        # Opening
                        fw2=int(ow2*0.6); fh2=int(oh2*0.55)
                        fx2=ox+ow2//2-fw2//2; fy2=oy+oh2-fh2-8
                        cv.create_rectangle(fx2,fy2,fx2+fw2,fy2+fh2,fill='#100500',outline='#888',width=3)
                        fire(fx2+fw2//2,fy2+fh2,fw=fw2-10,fh=fh2-8,t=now)
                        # Mantle
                        cv.create_rectangle(ox-8,oy+oh2-fh2-18,ox+ow2+8,oy+oh2-fh2-6,fill='#6a4a30',outline='#2a2010',width=2)

                    elif ot=='couch':
                        cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#8B4513',outline='#5a2a00',width=2)
                        cv.create_rectangle(ox,oy-32,ox+ow2,oy,fill='#a0522d',outline='#5a2a00',width=2)
                        for ax3 in [ox,ox+ow2-24]:
                            cv.create_rectangle(ax3,oy-32,ax3+24,oy+oh2,fill='#7a3a10',outline='#5a2a00',width=2)
                        # Cushion lines
                        for cx3 in range(ox+24,ox+ow2-24,ow2//4):
                            cv.create_line(cx3,oy-28,cx3,oy,fill='#5a2a00',width=2)

                    elif ot in ('reading_desk','desk','map_table','dining_table','worktable','kitchen_counter','coffee_table','shop_counter','bakery_counter'):
                        # Rich wooden desk/table
                        top_h=16
                        cv.create_rectangle(ox,oy,ox+ow2,oy+top_h,fill='#8B5e3c',outline='#3a2010',width=2)
                        cv.create_rectangle(ox,oy,ox+ow2,oy+4,fill='#a07050',outline='')  # highlight
                        # Table body
                        cv.create_rectangle(ox+4,oy+top_h,ox+ow2-4,oy+oh2,fill='#7a4a28',outline='#3a2010',width=2)
                        # Legs
                        for lx3 in [ox+6,ox+ow2-18]:
                            cv.create_rectangle(lx3,oy+oh2-20,lx3+12,oy+oh2,fill='#5c3010',outline='#2a1008',width=1)
                        if ot=='shop_counter' or ot=='bakery_counter':
                            # Display items on top
                            for ci4 in range(min(6,ow2//50)):
                                itx=ox+15+ci4*(ow2-30)//6
                                cv.create_oval(itx-10,oy-18,itx+10,oy,fill=['#D2691E','#FFD700','#FF8C00','#CD853F','#D2691E','#FF8C00'][ci4%6],outline='#8B4513',width=1)

                    elif ot=='open_book':
                        cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#f0e8d0',outline='#8B5e3c',width=2)
                        cv.create_line(ox+ow2//2,oy,ox+ow2//2,oy+oh2,fill='#8B5e3c',width=2)
                        for ly3 in range(oy+8,oy+oh2-6,8):
                            cv.create_line(ox+5,ly3,ox+ow2//2-3,ly3,fill='#888870',width=1)
                            cv.create_line(ox+ow2//2+3,ly3,ox+ow2-5,ly3,fill='#888870',width=1)

                    elif ot=='wall_shelf':
                        cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#8B5e3c',outline='#3a2010',width=2)
                        cv.create_rectangle(ox,oy,ox+ow2,oy+5,fill='#a07050',outline='')

                    elif ot in ('stone_stove','stove'):
                        cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#2a2a2a',outline='#1a1a1a',width=3)
                        for ki3 in range(2):
                            for kj2 in range(2):
                                kx3=ox+12+ki3*40; ky3=oy+12+kj2*35
                                cv.create_oval(kx3,ky3,kx3+24,ky3+24,fill='#444',outline='#666',width=2)
                                cv.create_oval(kx3+4,ky3+4,kx3+20,ky3+20,fill='#333',outline='')
                        cv.create_rectangle(ox+8,oy+oh2-45,ox+ow2-8,oy+oh2-5,fill='#1a0a00',outline='#666',width=2)
                        fire(ox+ow2//2,oy+oh2-6,fw=ow2-24,fh=35,t=now)

                    elif ot=='pot':
                        lc3=['#44ff44','#33dd33','#55ff55'][int(now*4)%3]
                        # Pot body
                        cv.create_oval(ox-22,oy-14,ox+22,oy+22,fill='#1a1a1a',outline='#555',width=3)
                        # Rim
                        cv.create_oval(ox-22,oy-18,ox+22,oy-8,fill='#2a2a2a',outline='#666',width=2)
                        # Bubbling liquid inside
                        cv.create_oval(ox-16,oy-14,ox+16,oy+10,fill=lc3,outline='')
                        # Side handles
                        cv.create_oval(ox-30,oy-8,ox-20,oy+4,fill='#333',outline='#666',width=2)
                        cv.create_oval(ox+20,oy-8,ox+30,oy+4,fill='#333',outline='#666',width=2)
                        for bi3 in range(3):
                            ph=(now*0.9+bi3*0.33)%1.0
                            bubble(ox-8+bi3*8,oy-4,ph,col='#88ffaa')

                    elif ot=='candle':
                        cv.create_rectangle(ox-5,oy,ox+5,oy+20,fill='#fffacd',outline='#daa520',width=1)
                        cv.create_oval(ox-3,oy+16,ox+3,oy+22,fill='#c8a000',outline='')
                        fire(ox,oy,fw=12,fh=18,t=now+ox*0.1)

                    elif ot=='lantern':
                        lantern_draw(ox,oy,t=now)

                    elif ot=='barrel':
                        cv.create_oval(ox-28,oy-40,ox+28,oy+40,fill='#6B3010',outline='#3a1a00',width=3)
                        for hr5 in [-16,0,16]:
                            cv.create_line(ox-28,oy+hr5,ox+28,oy+hr5,fill='#3a1a00',width=3)
                        cv.create_oval(ox-18,oy-28,ox+18,oy+28,fill='',outline='#8B4513',width=1)

                    elif ot=='sack':
                        cv.create_oval(ox-28,oy-42,ox+28,oy+42,fill='#c8a060',outline='#8B7040',width=3)
                        cv.create_line(ox,oy-42,ox,oy-55,fill='#8B7040',width=4)
                        cv.create_oval(ox-9,oy-60,ox+9,oy-47,fill='#8B7040',outline='#5a4020',width=2)
                        for xi in range(-20,21,10):
                            cv.create_line(ox+xi,oy-36,ox+xi+4,oy+36,fill='#a08050',width=1)

                    elif ot in ('gem_counter','display_counter'):
                        # Glass display case
                        cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#1a2a3a',outline='#4488aa',width=3)
                        cv.create_rectangle(ox+3,oy+3,ox+ow2-3,oy+oh2//2,fill='#223344',outline='#6699bb',width=1)
                        # Glass glint
                        cv.create_line(ox+8,oy+5,ox+8,oy+oh2//2-3,fill='#6688aa',width=2)

                    elif ot=='gem_display':
                        gc=obj.get('color','#ff4444'); gn=obj.get('name','')
                        cv.create_polygon(ox,oy,ox+16,oy+12,ox,oy+24,ox-16,oy+12,fill=gc,outline='white',width=1)
                        cv.create_polygon(ox,oy,ox+16,oy+12,ox,oy+14,ox-16,oy+12,fill='white',outline='',stipple='gray25')
                        if gn:
                            cv.create_text(ox,oy+32,text=gn,fill='#aaaaaa',font=('Arial',7))
                        for si5 in range(4):
                            a5=now*2.5+si5*1.571
                            cv.create_oval(ox+int(math.cos(a5)*20)-2,oy+12+int(math.sin(a5)*12)-2,
                                           ox+int(math.cos(a5)*20)+2,oy+12+int(math.sin(a5)*12)+2,fill=gc,outline='')

                    elif ot in ('wall_weapon','floor_weapon','hung_weapon'):
                        pass  # handled above for hung_weapon; floor_weapon:
                    
                    elif ot=='floor_weapon':
                        wx2,wy2=ox,oy; ang2=obj.get('angle',0.2); wt2=obj.get('weapon','sword')
                        ca,sa=math.cos(ang2),math.sin(ang2)
                        def rfl(dx,dy): return wx2+dx*ca-dy*sa,wy2+dx*sa+dy*ca
                        if wt2=='sword':
                            cv.create_line(*rfl(-35,0),*rfl(35,0),fill='#aaaaaa',width=5)
                            cv.create_line(*rfl(-8,-10),*rfl(-8,10),fill='#888',width=4)
                            cv.create_polygon(*rfl(33,-4),*rfl(33,4),*rfl(50,0),fill='#cccccc',outline='#888')
                        elif wt2=='axe':
                            cv.create_line(*rfl(-28,0),*rfl(28,0),fill='#8B4513',width=6)
                            cv.create_polygon(*rfl(18,-18),*rfl(32,-4),*rfl(18,8),*rfl(8,-2),fill='#888',outline='#555',width=2)
                        elif wt2=='spear':
                            cv.create_line(*rfl(-45,0),*rfl(45,0),fill='#8B4513',width=4)
                            cv.create_polygon(*rfl(43,-5),*rfl(43,5),*rfl(62,0),fill='#aaa',outline='#777')

                    elif ot=='anvil':
                        cv.create_rectangle(ox-15,oy+45,ox+75,oy+70,fill='#333',outline='#111',width=3)
                        cv.create_polygon(ox-10,oy+45,ox+70,oy+45,ox+55,oy+8,ox+5,oy+8,fill='#444',outline='#111',width=3)
                        cv.create_polygon(ox+55,oy+20,ox+55,oy+35,ox+100,oy+32,fill='#444',outline='#111',width=2)
                        cv.create_rectangle(ox+5,oy+8,ox+55,oy+22,fill='#666',outline='#111',width=2)

                    elif ot=='coal_pile':
                        for ci5 in range(12):
                            a=ci5*0.524; r2=22+ci5%3*8
                            cx4=ox+int(math.cos(a)*r2*0.7); cy4=oy+int(math.sin(a)*r2*0.4)
                            cv.create_oval(cx4-7,cy4-5,cx4+7,cy4+5,fill='#1a1a1a',outline='#111')

                    elif ot=='stone_pillar':
                        cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#4a3a6a',outline='#2a1a4a',width=3)
                        cv.create_rectangle(ox+4,oy+4,ox+ow2-4,oy+12,fill='#6a5a8a',outline='')
                        cv.create_rectangle(ox+4,oy+oh2-12,ox+ow2-4,oy+oh2-4,fill='#6a5a8a',outline='')

                    elif ot=='crystal_stand':
                        cv.create_rectangle(ox+ow2//4,oy+oh2-20,ox+ow2*3//4,oy+oh2,fill='#5a3a7a',outline='#3a2050',width=2)
                        gp=int(abs(math.sin(now*1.5))*14)
                        cv.create_oval(ox-gp,oy-gp,ox+ow2+gp,oy+ow2+gp,fill='',outline='#6622aa',width=2)
                        cv.create_oval(ox+4,oy+4,ox+ow2-4,oy+ow2-4,fill='#220033',outline='#8833ff',width=4)
                        for i3 in range(3):
                            a3=now*2+i3*2.094
                            cv.create_oval(ox+ow2//2+int(math.cos(a3)*16)-8,oy+ow2//2+int(math.sin(a3)*16)-8,
                                           ox+ow2//2+int(math.cos(a3)*16)+8,oy+ow2//2+int(math.sin(a3)*16)+8,fill='#cc66ff',outline='')

                    elif ot=='safe':
                        cv.create_rectangle(ox-50,oy-65,ox+50,oy+55,fill='#484848',outline='#222',width=5)
                        cv.create_rectangle(ox-44,oy-59,ox+44,oy+49,fill='#3a3a3a',outline='#1a1a1a',width=2)
                        # Combination dial
                        cv.create_oval(ox-22,oy-22,ox+22,oy+22,fill='#2a2a2a',outline='#888',width=3)
                        for ti2 in range(12):
                            ta=ti2*math.pi/6
                            cv.create_oval(ox+int(math.cos(ta)*16)-2,oy+int(math.sin(ta)*16)-2,
                                           ox+int(math.cos(ta)*16)+2,oy+int(math.sin(ta)*16)+2,fill='#aaa',outline='')
                        da=now*0.5
                        cv.create_line(ox,oy,ox+int(math.cos(da)*14),oy+int(math.sin(da)*14),fill='#fff',width=2)
                        # Handle bar
                        cv.create_rectangle(ox+34,oy-10,ox+50,oy+10,fill='#666',outline='#888',width=2)
                        # Corner rivets
                        for rx4,ry4 in [(ox-44,oy-59),(ox+36,oy-59),(ox-44,oy+41),(ox+36,oy+41)]:
                            cv.create_oval(rx4-4,ry4-4,rx4+4,ry4+4,fill='#888',outline='')

                    elif ot=='mortar':
                        cv.create_oval(ox-22,oy-14,ox+22,oy+26,fill='#888',outline='#555',width=3)
                        cv.create_oval(ox-16,oy-8,ox+16,oy+18,fill='#666',outline='')
                        cv.create_line(ox+10,oy-22,ox+24,oy-42,fill='#888',width=5)
                        cv.create_oval(ox+20,oy-48,ox+30,oy-36,fill='#aaa',outline='#777',width=1)

                    elif ot=='open_scroll':
                        cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#ddd0a0',outline='#8B7040',width=2)
                        cv.create_rectangle(ox-5,oy,ox+5,oy+oh2,fill='#8B7040',outline='#5a4020',width=2)
                        cv.create_rectangle(ox+ow2-5,oy,ox+ow2+5,oy+oh2,fill='#8B7040',outline='#5a4020',width=2)
                        for ly4 in range(oy+8,oy+oh2-6,10):
                            cv.create_line(ox+8,ly4,ox+ow2-8,ly4,fill='#8B7040',width=1)
                        # X mark
                        cx5,cy5=ox+ow2//2,oy+oh2//2
                        cv.create_line(cx5-12,cy5-12,cx5+12,cy5+12,fill='#cc2222',width=3)
                        cv.create_line(cx5+12,cy5-12,cx5-12,cy5+12,fill='#cc2222',width=3)

                    elif ot=='bread_display':
                        for bi4 in range(3):
                            bx3=ox+bi4*50
                            cv.create_oval(bx3-22,oy-14,bx3+22,oy+18,fill='#D2691E',outline='#8B4513',width=2)
                            cv.create_oval(bx3-16,oy-20,bx3+16,oy-4,fill='#D2691E',outline='#8B4513',width=2)
                            for xi2 in range(-14,15,9):
                                cv.create_line(bx3+xi2,oy-18,bx3+xi2+3,oy+16,fill='#A0522D',width=1)

                    elif ot=='bread_loaf':
                        cv.create_oval(ox-24,oy-12,ox+24,oy+20,fill='#D2691E',outline='#8B4513',width=2)
                        cv.create_oval(ox-18,oy-18,ox+18,oy-2,fill='#D2691E',outline='#8B4513',width=2)
                        for xi3 in range(-14,15,9):
                            cv.create_line(ox+xi3,oy-16,ox+xi3+3,oy+18,fill='#A0522D',width=1)

                    elif ot in ('worktable','shelf_item'):
                        if ot=='shelf_item':
                            sc=obj.get('color','#cc4444')
                            cv.create_oval(ox-10,oy-14,ox+10,oy+10,fill=sc,outline='#333',width=1)
                            cv.create_rectangle(ox-4,oy-22,ox+4,oy-12,fill='#aaa',outline='#555',width=1)
                        else:
                            cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#8B5e3c',outline='#3a2010',width=2)
                            cv.create_rectangle(ox,oy,ox+ow2,oy+8,fill='#a07050',outline='')

                    elif ot=='potion_large':
                        pc=obj.get('color','#4488ff')
                        cv.create_oval(ox-14,oy-8,ox+14,oy+22,fill=pc,outline='#222',width=2)
                        cv.create_rectangle(ox-7,oy-20,ox+7,oy-6,fill='#aaa',outline='#555',width=1)
                        cv.create_rectangle(ox-8,oy-28,ox+8,oy-18,fill='#8B4513',outline='#5a2a00',width=1)
                        if (now*3+ox)%1 < 0.5:
                            cv.create_oval(ox-4,oy+8,ox+4,oy+16,fill='white',outline='')

                    elif ot=='rug':
                        cv.create_oval(ox,oy,ox+ow2,oy+oh2,fill=obj.get('color','#8B0000'),outline='#600000',width=3)
                        cv.create_oval(ox+16,oy+12,ox+ow2-16,oy+oh2-12,fill='',outline='#cc2222',width=2)
                        cv.create_oval(ox+32,oy+22,ox+ow2-32,oy+oh2-22,fill='',outline='#aa1111',width=1)

                    elif ot=='nightstand':
                        cv.create_rectangle(ox,oy,ox+ow2,oy+oh2,fill='#5c3010',outline='#3a1a08',width=2)
                        cv.create_line(ox,oy+oh2//2,ox+ow2,oy+oh2//2,fill='#3a1a08',width=2)
                        cv.create_oval(ox+ow2//2-5,oy+oh2//4-5,ox+ow2//2+5,oy+oh2//4+5,fill='#FFD700',outline='#DAA520')

                    elif ot=='crate_stack':
                        # Stack of crates
                        cw3=ow2; ch3=oh2//3
                        for ci6 in range(3):
                            cy3b=oy+oh2-(ci6+1)*ch3
                            cv.create_rectangle(ox+ci6*4,cy3b,ox+cw3-ci6*4,cy3b+ch3,fill='#8B5e3c',outline='#3a2010',width=2)
                            cv.create_line(ox+cw3//2+ci6*4,cy3b,ox+cw3//2+ci6*4,cy3b+ch3,fill='#3a2010',width=1)
                            cv.create_line(ox+ci6*4,cy3b+ch3//2,ox+cw3-ci6*4,cy3b+ch3//2,fill='#3a2010',width=1)

                    elif ot=='tower_magic_circle':
                        pass  # drawn separately below

                # ── Tower animated elements ───────────────────────────
                if btype=='tower':
                    mcx,mcy=W//2,H//2+20
                    for rad,col2 in [(120,'#220044'),(95,'#330066'),(70,'#440088')]:
                        cv.create_oval(mcx-rad,mcy-rad,mcx+rad,mcy+rad,fill='',outline=col2,width=3)
                    for i4 in range(8):
                        ang4=now*1.2+i4*math.pi/4
                        rns=['✦','★','◆','⬡','⬟','✧','⬢','◇']
                        cv.create_text(mcx+int(math.cos(ang4)*95),mcy+int(math.sin(ang4)*95),text=rns[i4],fill='#aa44ff',font=('Arial',13))
                    pl=abs(math.sin(now*2))*24
                    cv.create_oval(mcx-32-int(pl),mcy-32-int(pl),mcx+32+int(pl),mcy+32+int(pl),fill='#220044',outline='#8833ff',width=3)
                    for i5,oc in enumerate(['#ff44ff','#44ffff','#ffff44','#ff6644']):
                        ag5=now*0.8+i5*math.pi/2
                        cv.create_oval(W//2+int(math.cos(ag5)*175)-11,H//2+int(math.sin(ag5)*125)-11,
                                       W//2+int(math.cos(ag5)*175)+11,H//2+int(math.sin(ag5)*125)+11,
                                       fill=oc,outline='white',width=1)

                # ── Indoor NPC — scaled up 2x ─────────────────────────
                indoor_npc=None
                npc_n=building.get('indoor_npc_name')
                if npc_n:
                    for npc in self.room.npcs:
                        if npc.name==npc_n: indoor_npc=npc; break
                if indoor_npc:
                    nx,ny=int(indoor_npc.indoor_x),int(indoor_npc.indoor_y)
                    NR=28  # bigger radius indoors
                    cv.create_oval(nx-NR,ny-NR,nx+NR,ny+NR,fill=indoor_npc.color,outline='white',width=3)
                    cv.create_oval(nx-NR+4,ny-NR+4,nx-NR+14,ny-NR+14,fill='white',outline='')  # eye
                    cv.create_oval(nx+NR-14,ny-NR+4,nx+NR-4,ny-NR+14,fill='white',outline='')
                    cv.create_text(nx,ny,text=indoor_npc.name[0].upper(),fill='black',font=('Arial',14,'bold'))
                    cv.create_text(nx,ny-NR-18,text=indoor_npc.name,fill='white',font=('Arial',11,'bold'))
                    if math.hypot(self.player.x-nx,self.player.y-ny)<90:
                        cv.create_text(nx,ny+NR+22,text='C to Talk',fill='yellow',font=('Arial',12,'bold'))
                        if self.keys.get('c'):
                            self.keys['c']=False
                            self.interact_with_npc(indoor_npc)

                # ── Player — scaled up indoors ────────────────────────
                plr=self.player; PR=22
                pc={'Warrior':'#cc2222','Mage':'#2244cc','Rogue':'#882299','Cleric':'#cccc22',
                    'Druid':'#228822','Monk':'#cc7722','Ranger':'#884422'}.get(plr.class_name,'#aaaaaa')
                # Shadow
                cv.create_oval(plr.x-PR+4,plr.y+PR-6,plr.x+PR+4,plr.y+PR+6,fill='#333333',outline='',stipple='gray50')
                # Body glow if buffed
                if getattr(plr,'active_buffs',[]):
                    cv.create_oval(plr.x-PR-5,plr.y-PR-5,plr.x+PR+5,plr.y+PR+5,fill='',outline='#44ff88',width=2,stipple='gray50')
                cv.create_oval(plr.x-PR-2,plr.y-PR-2,plr.x+PR+2,plr.y+PR+2,fill='white',outline='')
                cv.create_oval(plr.x-PR,plr.y-PR,plr.x+PR,plr.y+PR,fill=pc,outline='')
                cv.create_oval(plr.x-8,plr.y-PR+3,plr.x+8,plr.y-PR+14,fill='white',outline='')  # highlight
                cv.create_text(plr.x,plr.y,text=plr.name[0].upper(),fill='white',font=('Arial',12,'bold'))
                cv.create_text(plr.x,plr.y-PR-18,text=plr.name,fill='white',font=('Arial',9,'bold'))

                cv.create_text(W//2,H-ow-18,text='Walk to bottom gap to exit',fill='#666655',font=('Arial',9))
                return   # skip normal rendering
            
            # === NORMAL TOWN VIEW ===
            # Draw bright green grass background
            # === NORMAL TOWN VIEW ===
            # Draw bright green grass background
            self.canvas.create_rectangle(0, 0, WINDOW_W, WINDOW_H, fill='#7EC850', outline='')
            
            self.canvas.create_line(
                0 - cam_x, 550 - cam_y, 
                1200 - cam_x, 550 - cam_y, 
                fill='#3d3d3d', width=80
            )

            # 2. Building Connectors: Connects every building to the main road
            for b in self.room.buildings:
                bx_center = b['x'] + b['width'] // 2
                # Draws a vertical path from the building bottom to the center road
                self.canvas.create_line(
                    bx_center - cam_x, (b['y'] + b['height']) - cam_y,
                    bx_center - cam_x, 550 - cam_y,
                    fill='#3d3d3d', width=40
                )
            # Draw buildings first (background layer)
                        # Draw buildings first (background layer)
                        # Draw buildings first (background layer)
            for building in self.room.buildings:
                bx = building['x'] - cam_x
                by = building['y'] - cam_y
                bw = building['width']
                bh = building['height']
                pattern = building.get('pattern', 'brick')
                shape = building.get('shape', 'normal')
                
                # Draw building body based on shape
                if shape == 'tower':
                    # Tall tower shape
                    self.canvas.create_rectangle(bx, by, bx + bw, by + bh, 
                                                fill=building['color'], outline='black', width=3)
                elif shape == 'anvil':
                    # Anvil shape for blacksmith
                    self.canvas.create_polygon(
                        bx + bw*0.3, by,
                        bx + bw*0.7, by,
                        bx + bw, by + bh*0.7,
                        bx + bw, by + bh,
                        bx, by + bh,
                        bx, by + bh*0.7,
                        fill=building['color'], outline='black', width=3
                    )
                elif shape == 'book':
                    # Book shape for library
                    self.canvas.create_rectangle(bx, by, bx + bw, by + bh,
                                                fill=building['color'], outline='black', width=3)
                    # Book spine
                    self.canvas.create_rectangle(bx, by, bx + 15, by + bh,
                                                fill='#4A3428', outline='black', width=2)
                else:
                    # Normal rectangle
                    self.canvas.create_rectangle(bx, by, bx + bw, by + bh, 
                                                fill=building['color'], outline='black', width=3)
                
                # Draw pattern ONLY for buildings that should have it
                if pattern == 'brick' and building['type'] in ['house', 'library']:
                    brick_color = '#654321'
                    # Bigger bricks: only 3 horizontal rows
                    for i in range(3):
                        y_pos = by + (bh // 4) * (i + 1)
                        self.canvas.create_line(bx, y_pos, bx + bw, y_pos,
                                              fill=brick_color, width=2)
                    # Fewer vertical dividers: only 2 columns, offset per row
                    for i in range(3):
                        for j in range(3):
                            x_pos = bx + (bw // 3) * j + (bw // 6 if i % 2 else 0)
                            y_start = by + (bh // 4) * i
                            y_end   = by + (bh // 4) * (i + 1)
                            if x_pos < bx + bw:
                                self.canvas.create_line(x_pos, y_start, x_pos, y_end,
                                                      fill=brick_color, width=2)
                elif pattern == 'stone' and building['type'] in ['tower', 'blacksmith']:
                    # Large stone blocks
                    for i in range(3):
                        for j in range(2):
                            stone_x = bx + (bw // 3) * i
                            stone_y = by + (bh // 2) * j
                            self.canvas.create_rectangle(stone_x, stone_y, 
                                                        stone_x + bw//3, stone_y + bh//2,
                                                        outline='#2F4F4F', width=2)
                elif pattern == 'wood' and building['type'] in ['shop', 'inn']:
                    # Wood planks (vertical)
                    for i in range(6):
                        plank_x = bx + (bw // 6) * i
                        self.canvas.create_line(plank_x, by, plank_x, by + bh,
                                              fill='#4A3428', width=2)
                
                # Draw roof (triangle for most, flat for tower)
                if building['type'] == 'tower':
                    # Cone roof
                    roof_points = [
                        bx, by,
                        bx + bw//2, by - 40,
                        bx + bw, by
                    ]
                    self.canvas.create_polygon(roof_points, fill=building['roof_color'], outline='black', width=2)
                else:
                    # Triangle roof
                    roof_points = [
                        bx, by,
                        bx + bw//2, by - 30,
                        bx + bw, by
                    ]
                    self.canvas.create_polygon(roof_points, fill=building['roof_color'], outline='black', width=2)
                
                # Draw CHIMNEY for blacksmith with ANIMATED SMOKE
                if building.get('has_chimney'):
                    chimney_x = bx + bw - 30
                    chimney_y = by - 30
                    chimney_w = 20
                    chimney_h = 40
                    
                    # Chimney body
                    self.canvas.create_rectangle(chimney_x, chimney_y, 
                                                chimney_x + chimney_w, chimney_y + chimney_h,
                                                fill='#3a3a3a', outline='black', width=2)
                    # Chimney top cap
                    self.canvas.create_rectangle(chimney_x - 3, chimney_y, 
                                                chimney_x + chimney_w + 3, chimney_y + 8,
                                                fill='#2a2a2a', outline='black', width=2)
                    
                    # ANIMATED SMOKE PUFFS
                    current_time = time.time()
                    for i in range(5):
                        offset = (current_time * 50 + i * 20) % 100
                        smoke_x = chimney_x + chimney_w//2 + random.randint(-5, 5)
                        smoke_y = chimney_y - offset
                        smoke_size = 4 + offset//20
                        
                        self.canvas.create_oval(smoke_x - smoke_size, smoke_y - smoke_size,
                                               smoke_x + smoke_size, smoke_y + smoke_size,
                                               fill='gray', outline='', stipple='gray50')
                
                # Draw door
                door_w = bw // 4
                door_h = bh // 3
                door_x = bx + bw//2 - door_w//2
                door_y = by + bh - door_h
                self.canvas.create_rectangle(door_x, door_y, door_x + door_w, door_y + door_h,
                                            fill='#654321', outline='black', width=2)
                # Door knob
                self.canvas.create_oval(door_x + door_w - 8, door_y + door_h//2 - 3,
                                       door_x + door_w - 4, door_y + door_h//2 + 3,
                                       fill='#FFD700', outline='black')
                
                # Draw windows
                window_size = 15
                if building['type'] == 'tower':
                    # Tower windows vertically stacked
                    for i in range(3):
                        wx = bx + bw//2 - window_size//2
                        wy = by + 20 + i * 50
                        self.canvas.create_rectangle(wx, wy, wx + window_size, wy + window_size,
                                                    fill='#87CEEB', outline='black', width=2)
                        # Window panes
                        self.canvas.create_line(wx, wy + window_size//2, wx + window_size, wy + window_size//2, fill='black')
                        self.canvas.create_line(wx + window_size//2, wy, wx + window_size//2, wy + window_size, fill='black')
                else:
                    # Regular building - 2 windows
                    for i in range(2):
                        wx = bx + 20 + i * (bw - 40 - window_size)
                        wy = by + 30
                        self.canvas.create_rectangle(wx, wy, wx + window_size, wy + window_size,
                                                    fill='#87CEEB', outline='black', width=2)
                        # Window panes
                        self.canvas.create_line(wx, wy + window_size//2, wx + window_size, wy + window_size//2, fill='black')
                        self.canvas.create_line(wx + window_size//2, wy, wx + window_size//2, wy + window_size, fill='black')
                
                # Shop sign board - ONLY for buildings with has_sign=True
                if building.get('has_sign'):
                    # Adjust sign size based on building
                    if building['type'] == 'library':
                        sign_board_w = bw * 1.0
                        sign_font = 10
                    else:
                        sign_board_w = bw * 0.8
                        sign_font = 10
                    
                    sign_board_h = 40
                    sign_x = bx + bw//2 - sign_board_w//2
                    sign_y = by - 15  # Just above roof
                    
                    # Sign chains/ropes
                    self.canvas.create_line(sign_x + 10, sign_y, sign_x + 10, by, fill='#4A3428', width=3)
                    self.canvas.create_line(sign_x + sign_board_w - 10, sign_y, sign_x + sign_board_w - 10, by, fill='#4A3428', width=3)
                    
                    # Wooden board background
                    self.canvas.create_rectangle(sign_x, sign_y, sign_x + sign_board_w, sign_y + sign_board_h,
                                                fill='#8B4513', outline='#654321', width=3)
                    
                    # Inner decorative border
                    self.canvas.create_rectangle(sign_x + 5, sign_y + 5, sign_x + sign_board_w - 5, sign_y + sign_board_h - 5,
                                                outline='#FFD700', width=2)
                    
                    # Building name in bold
                    self.canvas.create_text(sign_x + sign_board_w//2, sign_y + sign_board_h//2, 
                                           text=building['name'],
                                           fill='#FFD700', font=('Arial', sign_font, 'bold'))
            
            # Draw decorations
            equipped_weapon = None
            weapon_item = None

            for item in self.player.equipped_items:
                if item.item_type == 'weapon':
                    equipped_weapon = item
                    break

            # Create weapon visual from equipped weapon
            # Create weapon visual from equipped weapon
            if equipped_weapon:
                # Get weapon_type, default to 'sword' if missing
                weapon_visual = getattr(equipped_weapon, 'weapon_type', None)
                
                if not weapon_visual:
                    print(f"WARNING: {equipped_weapon.name} has no weapon_type! Defaulting to sword")
                    weapon_visual = 'sword'
                
                # Create Item object for drawing
                weapon_item = Item(px, py, weapon_visual, 'silver', 20, owner=self.player)
                
                # Set special colors for different weapon types
                if weapon_visual == 'staff':
                    if self.player.class_name == 'Mage':
                        weapon_item.color = 'blue'
                        weapon_item.gem_color = 'cyan'
                    elif self.player.class_name == 'Cleric':
                        weapon_item.color = 'gold'
                        weapon_item.gem_color = 'yellow'
                    elif self.player.class_name == 'Druid':
                        weapon_item.color = 'green'
                        weapon_item.gem_color = 'lime'
                elif weapon_visual == 'wand':
                    weapon_item.color = 'purple'
                    weapon_item.gem_color = 'yellow'
                elif weapon_visual == 'dagger':
                    weapon_item.color = 'purple'
                elif weapon_visual == 'hand':
                    weapon_item.color = '#FFA500'
                elif weapon_visual == 'bow':
                    weapon_item.color = 'brown'
                elif weapon_visual == 'sword':
                    weapon_item.color = 'silver'
                elif weapon_visual == 'katana':
                    weapon_item.color = 'silver'
                elif weapon_visual == 'axe':
                    weapon_item.color = 'silver'
                elif weapon_visual == 'scythe':
                    weapon_item.color = 'gray'
                elif weapon_visual == 'quarterstaff':
                    weapon_item.color = 'brown'
                        
                # Update weapon position to aim at mouse
                _wpx, _wpy = self.get_mouse_world_pos()
                weapon_item.update(px, py, _wpx, _wpy)

                # Draw weapons that go UNDER the player body
                if weapon_visual in ("spear", "staff", "sword", "dagger", "quarterstaff", "katana", "axe", "scythe"):
                    weapon_item.draw(self.canvas)

            # Draw player body
            CLASS_COLORS = {
                "Warrior": "red",
                "Mage": "blue",
                "Rogue": "purple",
                "Cleric": "yellow",
                "Druid": "green",
                "Monk": "orange",
                "Ranger": "brown",
            }

            size = 12
            player_color = CLASS_COLORS.get(self.player.class_name, "cyan")

            # White outline
            self.canvas.create_oval(px-size-2, py-size-2, px+size+2, py+size+2, fill='white')
            # Colored body
            self.canvas.create_oval(px-size, py-size, px+size, py+size, fill=player_color)

            # First character of player name (uppercase)
            initial = self.player.name[0].upper()
            self.canvas.create_text(px, py, text=initial, fill='black', font=('Helvetica', 10, 'bold'))

            # ── Frozen ice cube overlay on player ─────────────────────────────
            if getattr(self.player, '_frozen_until', 0) > time.time():
                _rfz = self.player._frozen_until - time.time()
                _hs2 = size + 12
                self.canvas.create_rectangle(
                    px - _hs2, py - _hs2, px + _hs2, py + _hs2,
                    fill='#88ccff', outline='#aaddff', width=3, stipple='gray25'
                )
                self.canvas.create_rectangle(
                    px - _hs2 + 4, py - _hs2 + 4, px + _hs2 - 4, py + _hs2 - 4,
                    fill='', outline='#cceeff', width=1
                )
                self.canvas.create_text(px, py - _hs2 - 6,
                                        text=f"❄ {_rfz:.1f}s",
                                        fill='#00eeff', font=('Arial', 8, 'bold'))

            # Draw weapons that go ON TOP of player body (like bow)
            if weapon_item and equipped_weapon and hasattr(equipped_weapon, 'weapon_type'):
                if equipped_weapon.weapon_type not in ("spear", "staff", "sword", "dagger", "quarterstaff", "katana", "axe", "scythe"):
                    weapon_item.draw(self.canvas)

    # Continue with summons drawing...
            for s in self.summons:
                s.draw(self.canvas)
            if self.room.spawn_point:
                self.room.spawn_point.draw(self.canvas)
            for e in self.room.enemies:
                ex, ey = e.x, e.y

                # Decide layering rules
                weapons_below = ("spear", "staff", "hand","sword")   # drawn BEFORE body
                weapons_above = ("bow")                      # drawn AFTER body


            # Draw decorations
            for deco in self.room.decorations:
                if deco['type'] == 'forest_wall':
                    # Draw solid forest rectangle
                    x = deco['x'] - cam_x
                    y = deco['y'] - cam_y
                    self.canvas.create_rectangle(
                        x, y,
                        x + deco['width'], y + deco['height'],
                        fill=deco['color'], outline=''
                    )
                
                elif deco['type'] == 'forest_edge':
                    # Draw wavy edge circles
                    x = deco['x'] - cam_x
                    y = deco['y'] - cam_y
                    size = deco['size']
                    self.canvas.create_oval(
                        x - size, y - size,
                        x + size, y + size,
                        fill=deco['color'], outline=''
                    )
                
                elif deco['type'] == 'tree':
                    x = deco['x'] - cam_x
                    y = deco['y'] - cam_y
                    size = deco['size']
                    tree_style = deco.get('tree_style', 'oak')
                    
                    # Trunk
                    self.canvas.create_rectangle(x-6, y-size//2, x+6, y+size//2,
                                                fill='#654321', outline='#4A3428', width=2)
                    # Canopy
                    self.canvas.create_oval(x-size, y-size*1.8, x+size, y-size*0.4,
                                          fill='#2d5016', outline='#1B5E20', width=2)
                    self.canvas.create_oval(x-size*0.7, y-size*1.6, x+size*0.7, y-size*0.6,
                                          fill='#3a6b24', outline='#1B5E20', width=2)
                
                elif deco['type'] == 'fountain':
                    x = deco['x'] - cam_x
                    y = deco['y'] - cam_y
                    size = deco['size']
                    
                    # Stone base
                    self.canvas.create_oval(x-size, y-size, x+size, y+size,
                                           fill='#708090', outline='#2F4F4F', width=3)
                    # Water pool
                    self.canvas.create_oval(x-size+8, y-size+8, x+size-8, y+size-8,
                                           fill='#4682B4', outline='')
                    # Center pillar
                    self.canvas.create_rectangle(x-6, y-35, x+6, y,
                                                 fill='#87CEEB', outline='#4682B4', width=1)
                    
                    # Animated water spray
                    current_time = time.time()
                    for i in range(12):
                        phase = (current_time * 2 + i * 0.5) % 3.0
                        angle = (i / 12) * 2 * math.pi
                        
                        if phase < 1.5:
                            height = 35 + phase * 25
                            dist = phase * 15
                            opacity = 1.0
                        else:
                            fall_time = phase - 1.5
                            height = 35 + 37.5 - fall_time * 30
                            dist = 22.5 - fall_time * 5
                            opacity = 0.7
                        
                        px = x + math.cos(angle) * dist
                        py = y - height
                        
                        color = '#B0E0E6' if opacity > 0.8 else '#87CEEB'
                        droplet_size = 2.5 if opacity > 0.8 else 2
                        self.canvas.create_oval(px-droplet_size, py-droplet_size,
                                               px+droplet_size, py+droplet_size,
                                               fill=color, outline='')
                
                elif deco['type'] == 'lamp':
                    x = deco['x'] - cam_x
                    y = deco['y'] - cam_y
                    # Lamp post
                    self.canvas.create_rectangle(x-4, y, x+4, y+50, fill='#1C1C1C', outline='')
                    self.canvas.create_rectangle(x-8, y-5, x+8, y, fill='#1C1C1C', outline='')
                    # Glass lamp
                    self.canvas.create_oval(x-10, y-25, x+10, y-5, fill='#FFD700', outline='#DAA520', width=2)
                    self.canvas.create_oval(x-6, y-21, x+6, y-9, fill='#FFFF99', outline='')
                
                elif deco['type'] == 'dungeon_entrance':
                    x = deco['x'] - cam_x
                    y = deco['y'] - cam_y
                    size = deco['size']
                    # Portal
                    self.canvas.create_oval(x-size, y-size, x+size, y+size, fill='', outline=deco['color'], width=6)
                    self.canvas.create_oval(x-size+8, y-size+8, x+size-8, y+size-8, fill=deco['color'], stipple='gray50')
                    self.canvas.create_oval(x-size//2, y-size//2, x+size//2, y+size//2, fill=deco['color'], outline='')
                    self.canvas.create_text(x, y-size-20, text=deco['name'], fill='white', font=('Arial', 14, 'bold'))
                    
                    if self.nearby_dungeon and self.nearby_dungeon == deco:
                        self.canvas.create_text(x, y+size+20, text='Press C to Enter', fill='yellow', font=('Arial', 12, 'bold'))
            
            # Draw NPCs — only outdoor ones (indoor NPCs appear inside their buildings)
            for npc in self.room.npcs:
                if npc.indoor:
                    continue
                npc_x = npc.x - cam_x
                npc_y = npc.y - cam_y
                
                # NPC body
                self.canvas.create_oval(
                    npc_x - npc.size, npc_y - npc.size,
                    npc_x + npc.size, npc_y + npc.size,
                    fill=npc.color, outline='black', width=2
                )
                
                # NPC name tag
                self.canvas.create_text(
                    npc_x, npc_y - npc.size - 15,
                    text=npc.name, fill='white',
                    font=('Arial', 10, 'bold')
                )
                
                # Show interaction prompt if nearby
                if self.nearby_npc and self.nearby_npc == npc:
                    self.canvas.create_text(
                        npc_x, npc_y + npc.size + 15,
                        text='Press C to Talk',
                        fill='yellow', font=('Arial', 10, 'bold')
                    )
            
            # Set player coordinates with camera offset for town
            
        else:
            # === DUNGEON RENDERING ===
            # Draw dark gray background FIRST
            self.canvas.create_rectangle(0, 0, WINDOW_W, WINDOW_H, fill='#2a2a2a', outline='')
            
            # Set player coordinates (no camera offset in dungeons)
            px, py = self.player.x, self.player.y
            
            # Draw walls with openings
            wall_thickness = 20
            opening_size = 150

            # Top wall
            if self.room_row > 0:
                opening_x = WINDOW_W // 2 - opening_size // 2
                self.canvas.create_rectangle(0, 0, opening_x, wall_thickness, fill='#505050')
                self.canvas.create_rectangle(opening_x + opening_size, 0, WINDOW_W, wall_thickness, fill='#505050')
            else:
                # Solid top wall
                self.canvas.create_rectangle(0, 0, WINDOW_W, wall_thickness, fill='#505050')

            # GREEN EXIT LINE - Draw AFTER walls (on top)
            if self.room_row == 0 and self.room_col == 0:
                exit_x_start = WINDOW_W // 2 - opening_size // 2
                exit_x_end = exit_x_start + opening_size
                # Draw bright green exit
                self.canvas.create_rectangle(exit_x_start, 0, exit_x_end, wall_thickness, 
                                             fill='#00ff00', outline='')
                self.canvas.create_text(WINDOW_W // 2, wall_thickness // 2, 
                                       text='EXIT', fill='black', 
                                       font=('Arial', 12, 'bold'))

            # Bottom wall (continue with rest of walls...)
            if self.room_row < ROOM_ROWS - 1:            # Bottom wall
                    if self.room_row < ROOM_ROWS - 1:
                        opening_x = WINDOW_W // 2 - opening_size // 2
                        self.canvas.create_rectangle(0, WINDOW_H - wall_thickness, opening_x, WINDOW_H, fill='#505050')
                        self.canvas.create_rectangle(opening_x + opening_size, WINDOW_H - wall_thickness, WINDOW_W, WINDOW_H, fill='#505050')
                    else:
                        self.canvas.create_rectangle(0, WINDOW_H - wall_thickness, WINDOW_W, WINDOW_H, fill='#505050')

            # Left wall
            if self.room_col > 0:
                opening_y = WINDOW_H // 2 - opening_size // 2
                self.canvas.create_rectangle(0, 0, wall_thickness, opening_y, fill='#505050')
                self.canvas.create_rectangle(0, opening_y + opening_size, wall_thickness, WINDOW_H, fill='#505050')
            else:
                self.canvas.create_rectangle(0, 0, wall_thickness, WINDOW_H, fill='#505050')

            # Right wall
            if self.room_col < ROOM_COLS - 1:
                opening_y = WINDOW_H // 2 - opening_size // 2
                self.canvas.create_rectangle(WINDOW_W - wall_thickness, 0, WINDOW_W, opening_y, fill='#505050')
                self.canvas.create_rectangle(WINDOW_W - wall_thickness, opening_y + opening_size, WINDOW_W, WINDOW_H, fill='#505050')
            else:
                self.canvas.create_rectangle(WINDOW_W - wall_thickness, 0, WINDOW_W, WINDOW_H, fill='#505050')
            
            # Set player coordinates (no camera offset in dungeons)
            px, py = self.player.x, self.player.y
            
            # Find equipped weapon - OUTSIDE THE LOOP
            equipped_weapon = None
            weapon_item = None
            for item in self.player.equipped_items:
                if item.item_type == 'weapon':
                    equipped_weapon = item
                    break
            
            # NOW CREATE THE WEAPON - OUTSIDE THE LOOP
            if equipped_weapon:
                weapon_visual = getattr(equipped_weapon, 'weapon_type', 'sword')
                weapon_item = Item(px, py, weapon_visual, 'silver', 20, owner=self.player)
                
                # Set colors
                if weapon_visual == 'staff':
                    if self.player.class_name == 'Mage':
                        weapon_item.color = 'blue'
                        weapon_item.gem_color = 'cyan'
                    elif self.player.class_name == 'Cleric':
                        weapon_item.color = 'gold'
                        weapon_item.gem_color = 'yellow'
                    elif self.player.class_name == 'Druid':
                        weapon_item.color = 'green'
                        weapon_item.gem_color = 'lime'
                elif weapon_visual == 'wand':
                    weapon_item.color = 'purple'
                    weapon_item.gem_color = 'yellow'
                elif weapon_visual == 'dagger':
                    weapon_item.color = 'purple'
                elif weapon_visual == 'hand':
                    weapon_item.color = '#FFA500'
                elif weapon_visual == 'bow':
                    weapon_item.color = 'brown'
                        
                # Update weapon position to aim at mouse
                _wpx2, _wpy2 = self.get_mouse_world_pos()
                weapon_item.update(px, py, _wpx2, _wpy2)

                # Draw weapons that go UNDER the player
                if weapon_visual in ("spear", "staff", "sword", "dagger", "quarterstaff", "katana", "axe", "scythe"):
                    weapon_item.draw(self.canvas)

            # Draw player body
            CLASS_COLORS = {
                "Warrior": "red",
                "Mage": "blue",
                "Rogue": "purple",
                "Cleric": "yellow",
                "Druid": "green",
                "Monk": "orange",
                "Ranger": "brown",
            }

            size = 12
            player_color = CLASS_COLORS.get(self.player.class_name, "cyan")

            # White outline
            self.canvas.create_oval(px-size-2, py-size-2, px+size+2, py+size+2, fill='white')
            # Colored body
            self.canvas.create_oval(px-size, py-size, px+size, py+size, fill=player_color)

            # First character of player name
            initial = self.player.name[0].upper()
            self.canvas.create_text(px, py, text=initial, fill='black', font=('Helvetica', 10, 'bold'))

            # ── Frozen ice cube overlay on player (dungeon) ───────────────────
            if getattr(self.player, '_frozen_until', 0) > time.time():
                _rfz2 = self.player._frozen_until - time.time()
                _hs3  = size + 12
                self.canvas.create_rectangle(
                    px - _hs3, py - _hs3, px + _hs3, py + _hs3,
                    fill='#88ccff', outline='#aaddff', width=3, stipple='gray25'
                )
                self.canvas.create_rectangle(
                    px - _hs3 + 4, py - _hs3 + 4, px + _hs3 - 4, py + _hs3 - 4,
                    fill='', outline='#cceeff', width=1
                )
                self.canvas.create_text(px, py - _hs3 - 6,
                                        text=f"❄ {_rfz2:.1f}s",
                                        fill='#00eeff', font=('Arial', 8, 'bold'))

            # Draw weapons that go ON TOP of player body (like bow)
            if weapon_item and equipped_weapon and hasattr(equipped_weapon, 'weapon_type'):
                if equipped_weapon.weapon_type not in ("spear", "staff", "sword", "dagger", "quarterstaff", "katana", "axe", "scythe"):
                    weapon_item.draw(self.canvas)

        # NOW CONTINUE WITH THE REST (summons, spawn point, enemies, etc.)
        # This should be at the SAME indentation level as the town's "for s in self.summons:"
        for s in self.summons:
            s.draw(self.canvas)
        if self.room.spawn_point:
            self.room.spawn_point.draw(self.canvas)
        for e in self.room.enemies:
            ex, ey = e.x, e.y

            # Decide layering rules
            weapons_below = ("spear", "staff", "hand","sword")   # drawn BEFORE body
            weapons_above = ("bow")                      # drawn AFTER body

            # Bosses: draw their special body first
            if isinstance(e, Boss):
                boss_shapes = {
                    "FireLord": ("rectangle", "orange"),
                    "IceGiant": ("diamond", "cyan"),
                    "ShadowWraith": ("triangle", "purple"),
                    "EarthTitan": ("oval", "brown"),
                }
                outline_width = 3
                outline_color = "white"
                shape, color = boss_shapes.get(e.boss_type, ("oval", "orange"))
                size = e.size

                # Body first
                if shape == "oval":
                    self.canvas.create_oval(
                        ex-size, ey-size, ex+size, ey+size,
                        fill=color, outline=outline_color, width=outline_width
                    )
                elif shape == "rectangle":
                    self.canvas.create_rectangle(
                        ex-size, ey-size, ex+size, ey+size,
                        fill=color, outline=outline_color, width=outline_width
                    )
                elif shape == "triangle":
                    points = [ex, ey-size, ex+size, ey+size, ex-size, ey+size]
                    self.canvas.create_polygon(
                        points, fill=color, outline=outline_color, width=outline_width
                    )
                elif shape == "diamond":
                    points = [ex, ey-size, ex+size, ey, ex, ey+size, ex-size, ey]
                    self.canvas.create_polygon(
                        points, fill=color, outline=outline_color, width=outline_width
                    )

                # Boss health name is drawn after the loop elsewhere
                # Draw bow AFTER body if boss has one
                if e.item and e.item.item_type in weapons_above:
                    e.item.draw(self.canvas)
                elif e.item and e.item.item_type in weapons_below:
                    # If you ever want some boss weapons beneath, draw them before body (move above body block)
                    pass
                # Skip normal enemy body code
                continue

            # ---------- Normal enemies ----------
            enemy_shapes = {
                "Swordman": ("oval", "brown"),
                "Spearman": ("hexagon", "brown"),
                "Archer": ("rectangle", "brown"),
                "Fire Imp": ("triangle", "orange"),
                "Flame Elemental": ("diamond", "red"),
                "Troll": ("rectangle", "darkgray"),
                "Ice Golem": ("square", "cyan"),
                "Dark Mage": ("triangle", "purple"),
                "Summoner": ("oval", "pink"),
                "Venom Lurker": ("oval", "lime"),
                "Healer": ("triangle", "yellow"),
            }
            shape, color = enemy_shapes.get(e.name, ("oval", "gray"))

            # 1) Draw weapons that should be beneath the body
            if e.item and e.item.item_type in weapons_below:
                e.item.draw(self.canvas)

            # 2) Draw the enemy body
            if shape == "oval":
                self.canvas.create_oval(ex-e.size, ey-e.size, ex+e.size, ey+e.size, fill=color)
            elif shape == "rectangle":
                self.canvas.create_rectangle(ex-e.size, ey-e.size, ex+e.size, ey+e.size, fill=color)
            elif shape == "triangle":
                points = [ex, ey-e.size, ex+e.size, ey+e.size, ex-e.size, ey+e.size]
                self.canvas.create_polygon(points, fill=color)
            elif shape == "square":
                self.canvas.create_rectangle(ex-e.size, ey-e.size, ex+e.size, ey+e.size, fill=color)
            elif shape == "diamond":
                points = [ex, ey-e.size, ex+e.size, ey, ex, ey+e.size, ex-e.size, ey]
                self.canvas.create_polygon(points, fill=color)
            elif shape == "hexagon":
                points = [
                    ex, ey-e.size,
                    ex+e.size*0.87, ey-e.size*0.5,
                    ex+e.size*0.87, ey+e.size*0.5,
                    ex, ey+e.size,
                    ex-e.size*0.87, ey+e.size*0.5,
                    ex-e.size*0.87, ey-e.size*0.5
                ]
                self.canvas.create_polygon(points, fill=color)

            # Health text
            health_text = f"{int(e.hp)}/{int(e.max_hp)}"
            self.canvas.create_text(ex, ey - e.size - 10, text=health_text, fill='white')

            # ── Frozen: ice cube outline with stipple so sprite shows through ──
            if hasattr(e, '_frozen_until') and e._frozen_until > time.time():
                remaining_freeze = e._frozen_until - time.time()
                _hs = e.size + 12
                # Stippled fill so the sprite body is still visible through the ice
                self.canvas.create_rectangle(
                    ex - _hs, ey - _hs, ex + _hs, ey + _hs,
                    fill='#88ccff', outline='#aaddff', width=3, stipple='gray25'
                )
                # Bright inner border
                self.canvas.create_rectangle(
                    ex - _hs + 4, ey - _hs + 4, ex + _hs - 4, ey + _hs - 4,
                    fill='', outline='#cceeff', width=1
                )
                # Countdown timer above the cube
                self.canvas.create_text(ex, ey - _hs - 6,
                                        text=f"❄ {remaining_freeze:.1f}s",
                                        fill='#00eeff', font=('Arial', 8, 'bold'))

            # ── Smoked: floating text only (no body overlay) ─────────────────
            if hasattr(e, '_smoke_until') and e._smoke_until > time.time():
                remaining_smoke = e._smoke_until - time.time()
                self.canvas.create_text(ex, ey - e.size - 22,
                                        text=f'💨 DAZED {remaining_smoke:.1f}s',
                                        fill='#aaaaaa', font=('Arial', 8, 'bold'))

            # 3) Draw weapons that should sit on top of the body (bow)
            if e.item and e.item.item_type in weapons_above:
                e.item.draw(self.canvas)

            
        boss_in_room = None
        for e in self.room.enemies:
            if isinstance(e, Boss):
                boss_in_room = e
                break
        # Draw player beam if active
        if self.player_beam:
            self.player_beam.draw(self.canvas)
        if boss_in_room:
            # Draw boss health bar at top
            bar_width = 400
            bar_height = 20
            x0 = (WINDOW_W - bar_width)//2
            y0 = 20
            hp_frac = boss_in_room.hp / boss_in_room.max_hp if boss_in_room.max_hp else 0
            self.canvas.create_rectangle(x0, y0, x0+bar_width, y0+bar_height, fill='gray')
            self.canvas.create_rectangle(x0, y0, x0 + int(bar_width*hp_frac), y0+bar_height, fill='red')
            self.canvas.create_text(WINDOW_W//2, y0 + bar_height//2, text=f"{boss_in_room.name}", fill='white', font=('Arial','12','bold'))

        def shade_color(color, factor):
            """
            Works with both hex (#RRGGBB) and Tkinter named colors.
            """
            # Convert named color to RGB
            r, g, b = self.canvas.winfo_rgb(color)  # returns 0-65535
            r = int(r / 65535 * 255)
            g = int(g / 65535 * 255)
            b = int(b / 65535 * 255)

            # Apply factor
            r = min(255, max(0, int(r * factor)))
            g = min(255, max(0, int(g * factor)))
            b = min(255, max(0, int(b * factor)))

            return f'#{r:02x}{g:02x}{b:02x}'



        for proj in self.projectiles:
            x, y, r = proj.x, proj.y, proj.radius
            # Fire projectile — drawn as a cluster of flame particles (no solid shape)
            if proj.stype == 'fire_proj':
                _fire_colors = ['orange','red','yellow','#ff6600','#ff4400']
                for _fi in range(6):
                    _fa  = proj.angle + random.uniform(-0.7, 0.7)
                    _fd  = random.uniform(0, r * 1.2)
                    _fx  = x + math.cos(_fa)*_fd
                    _fy  = y + math.sin(_fa)*_fd
                    _fr  = random.uniform(r*0.25, r*0.65)
                    self.canvas.create_oval(_fx-_fr, _fy-_fr, _fx+_fr, _fy+_fr,
                                            fill=random.choice(_fire_colors), outline='')
                # bright core
                self.canvas.create_oval(x-r*0.45, y-r*0.45, x+r*0.45, y+r*0.45,
                                        fill='white', outline='')
            elif proj.stype == 'basic':
                # Simple circle
                self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=proj.color)
            if proj.stype == 'spear_throw':
                # Draw identical to the player-held spear item
                angle = proj.angle
                px, py = proj.x, proj.y
                shaft_len = 28
                tip_len   = 10
                tip_base_x = px + math.cos(angle) * shaft_len * 0.6
                tip_base_y = py + math.sin(angle) * shaft_len * 0.6
                shaft_end_x = px - math.cos(angle) * shaft_len * 0.4
                shaft_end_y = py - math.sin(angle) * shaft_len * 0.4
                # Shaft
                self.canvas.create_line(shaft_end_x, shaft_end_y, tip_base_x, tip_base_y,
                                        fill='#654321', width=5)
                self.canvas.create_line(shaft_end_x, shaft_end_y, tip_base_x, tip_base_y,
                                        fill='#8B4513', width=3)
                # Spear head
                tip_x = tip_base_x + math.cos(angle) * tip_len
                tip_y = tip_base_y + math.sin(angle) * tip_len
                perp = angle + math.pi/2
                lx = tip_base_x + math.cos(perp) * 5
                ly = tip_base_y + math.sin(perp) * 5
                rx = tip_base_x - math.cos(perp) * 5
                ry = tip_base_y - math.sin(perp) * 5
                self.canvas.create_polygon([tip_x, tip_y, lx, ly, tip_base_x, tip_base_y, rx, ry],
                                           fill='#C0C0C0', outline='#696969', width=2)
                self.canvas.create_line(tip_x, tip_y, tip_base_x, tip_base_y,
                                        fill='white', width=2)
            if proj.stype == 'smoke_bomb':
                bx, by = proj.x, proj.y
                # Dark charcoal sphere
                self.canvas.create_oval(bx-10, by-10, bx+10, by+10,
                                        fill='#2a2a2a', outline='#555555', width=2)
                # Fuse spark on top
                self.canvas.create_oval(bx-3, by-13, bx+3, by-7,
                                        fill='#ffaa00', outline='')
                self.canvas.create_oval(bx-2, by-16, bx+2, by-12,
                                        fill='#ff6600', outline='')
            if proj.stype == 'arrow':
                angle = proj.angle
                x, y = proj.x, proj.y
                r = proj.radius  # base radius
                scale = 0.4  # shrink factor

                # ----- Arrow tip (triangle) -----
                tip_length = r * 4 * scale
                tip = [
                    x + math.cos(angle) * tip_length, y + math.sin(angle) * tip_length,  # tip point
                    x - math.cos(angle + math.pi/6) * tip_length/2, y - math.sin(angle + math.pi/6) * tip_length/2,  # left base
                    x - math.cos(angle - math.pi/6) * tip_length/2, y - math.sin(angle - math.pi/6) * tip_length/2   # right base
                ]
                self.canvas.create_polygon(tip, fill='gray')  # tip gray

                # ----- Arrow shaft (rectangle) -----
                shaft_length = tip_length * 1.5
                shaft_width = r / 2 * scale
                perp_angle = angle + math.pi / 2
                corners = [
                    x - math.cos(perp_angle) * shaft_width - math.cos(angle) * shaft_length, y - math.sin(perp_angle) * shaft_width - math.sin(angle) * shaft_length - 1,
                    x + math.cos(perp_angle) * shaft_width - math.cos(angle) * shaft_length, y + math.sin(perp_angle) * shaft_width - math.sin(angle) * shaft_length + 1,
                    x + math.cos(perp_angle) * shaft_width, y + math.sin(perp_angle) * shaft_width,
                    x - math.cos(perp_angle) * shaft_width, y - math.sin(perp_angle) * shaft_width
                ]
                self.canvas.create_polygon(corners, fill=proj.color)

                # ----- Fletching at the back -----
                fletch_length = r * 3 * scale
                fletch_width = r * scale
                back_x = x - math.cos(angle) * shaft_length
                back_y = y - math.sin(angle) * shaft_length

                fletch_angles = [-math.pi/8, 0, math.pi/8]
                for fa in fletch_angles:
                    ftip_x = back_x - math.cos(angle + fa) * fletch_length
                    ftip_y = back_y - math.sin(angle + fa) * fletch_length
                    base1_x = back_x - math.cos(angle + fa + math.pi/2) * fletch_width/2
                    base1_y = back_y - math.sin(angle + fa + math.pi/2) * fletch_width/2
                    base2_x = back_x + math.cos(angle + fa + math.pi/2) * fletch_width/2
                    base2_y = back_y + math.sin(angle + fa + math.pi/2) * fletch_width/2
                    self.canvas.create_polygon([ftip_x, ftip_y, base1_x, base1_y, base2_x, base2_y], fill='white')
            elif proj.stype == 'leaf':
                # Leaf proportions
                leaf_length = r * 3.5
                leaf_width  = r * 1.8
                stem_length = r * 0.9
                stem_width  = r * 0.25

                cos_a = math.cos(proj.angle)
                sin_a = math.sin(proj.angle)

                # --- STEM ---
                sx1 = x - cos_a * stem_length
                sy1 = y - sin_a * stem_length
                sx2 = x
                sy2 = y

                sdx = sin_a * stem_width / 2
                sdy = -cos_a * stem_width / 2

                stem_points = [
                    sx1 - sdx, sy1 - sdy,
                    sx1 + sdx, sy1 + sdy,
                    sx2 + sdx, sy2 + sdy,
                    sx2 - sdx, sy2 - sdy
                ]
                self.canvas.create_polygon(stem_points, fill=proj.color)

                # --- LEAF BODY ---
                # Leaf center slightly forward
                cx = x + cos_a * (leaf_length * 0.15)
                cy = y + sin_a * (leaf_length * 0.15)

                # Tip of leaf
                tip_x = cx + cos_a * (leaf_length / 2)
                tip_y = cy + sin_a * (leaf_length / 2)

                # Base of leaf
                base_x = cx - cos_a * (leaf_length / 2)
                base_y = cy - sin_a * (leaf_length / 2)

                # Perpendicular offset for width
                dx = sin_a * (leaf_width / 2)
                dy = -cos_a * (leaf_width / 2)

                # Curved leaf shape (teardrop)
                leaf_points = [
                    base_x, base_y,               # back point
                    base_x + dx, base_y + dy,     # right curve
                    tip_x, tip_y,                 # tip
                    base_x - dx, base_y - dy      # left curve
                ]

                self.canvas.create_polygon(leaf_points, fill=proj.color, smooth=True)


            elif proj.stype == "lightning":
                strands = 1        # number of lightning strands
                segments = 50      # length of each strand
                for s in range(strands):
                    points = []
                    dx = math.cos(proj.angle) * (proj.radius * 12 / segments)
                    dy = math.sin(proj.angle) * (proj.radius * 12 / segments)
                    px, py = proj.x, proj.y
                    for i in range(segments):
                        offset_x = random.uniform(-8, 8)
                        offset_y = random.uniform(-8, 8)
                        points.append((px + dx * i + offset_x, py + dy * i + offset_y))
                    # flicker: sometimes skip drawing this strand
                    if random.random() < 0.85:   # 80% chance to draw
                        for i in range(len(points) - 1):
                            x1, y1 = points[i]
                            x2, y2 = points[i + 1]
                            self.canvas.create_line(x1, y1, x2, y2,
                                                    fill="yellow", width=4)
            elif proj.stype == "howl":
                arc_extent = 90   # cone width
                thickness = 6

                # Tkinter arc angles: 0Â° = right, CCW positive
                start_angle = -math.degrees(proj.angle)

                for i in range(3):
                    radius = proj.radius * (i + 2)
                    self.canvas.create_arc(
                        proj.x - radius, proj.y - radius,
                        proj.x + radius, proj.y + radius,
                        start=start_angle - arc_extent / 2,
                        extent=arc_extent,
                        style="arc",
                        outline=proj.color,
                        width=thickness
                    )



            elif proj.stype == 'dagger':
                angle = proj.angle
                size = r * 3

                base = proj.color
                dark = shade_color(base, 0.6)
                mid  = shade_color(base, 0.85)
                light = shade_color(base, 1.25)

                offset = size * 0.3
                sx = x + math.cos(angle) * offset
                sy = y + math.sin(angle) * offset

                blade_len = size * 1.2
                handle_len = size * 0.4

                bx = sx + math.cos(angle) * blade_len
                by = sy + math.sin(angle) * blade_len

                hx = x - math.cos(angle) * handle_len
                hy = y - math.sin(angle) * handle_len

                # Handle
                self.canvas.create_line(
                    hx, hy, sx, sy,
                    fill=dark,
                    width=4
                )

                # Pommel
                self.canvas.create_oval(
                    hx-3, hy-3,
                    hx+3, hy+3,
                    fill=mid,
                    outline=dark
                )

                # Crossguard
                perp = angle + math.pi / 2
                cg = 6
                self.canvas.create_line(
                    sx + math.cos(perp)*cg, sy + math.sin(perp)*cg,
                    sx - math.cos(perp)*cg, sy - math.sin(perp)*cg,
                    fill=dark,
                    width=3
                )

                # Blade shaft
                self.canvas.create_line(
                    sx, sy, bx, by,
                    fill=mid,
                    width=8
                )
                self.canvas.create_line(
                    sx, sy, bx, by,
                    fill=light,
                    width=5
                )

                # Blade tip
                tip_len = 6
                tx = bx + math.cos(angle) * tip_len
                ty = by + math.sin(angle) * tip_len

                tw = 5
                lx = bx + math.cos(perp) * tw
                ly = by + math.sin(perp) * tw
                rx = bx - math.cos(perp) * tw
                ry = by - math.sin(perp) * tw

                self.canvas.create_polygon(
                    tx, ty,
                    lx, ly,
                    rx, ry,
                    fill=light,
                    outline=dark
                )

            elif proj.stype == 'bolt':
                # Bolt body size
                length = r * 4
                width = r * 1.0

                # Center line endpoints
                x1 = x - math.cos(proj.angle) * length / 2
                y1 = y - math.sin(proj.angle) * length / 2
                x2 = x + math.cos(proj.angle) * length / 2
                y2 = y + math.sin(proj.angle) * length / 2

                # Perpendicular offset for width
                dx = math.sin(proj.angle) * width / 2
                dy = -math.cos(proj.angle) * width / 2

                # Rectangle body
                body_points = [
                    x1 - dx, y1 - dy,
                    x1 + dx, y1 + dy,
                    x2 + dx, y2 + dy,
                    x2 - dx, y2 - dy
                ]
                self.canvas.create_polygon(body_points, fill=proj.color, outline=proj.color)

                # Rounded tip (rotated semicircle)
                radius = width / 2
                segments = 10  # smoother tip

                tip_points = []

                # Generate semicircle points from -90° to +90° relative to projectile angle
                for i in range(segments + 1):
                    local_angle = proj.angle + math.radians(-90 + (180 * i / segments))
                    px = x2 + math.cos(local_angle) * radius
                    py = y2 + math.sin(local_angle) * radius
                    tip_points.append(px)
                    tip_points.append(py)

                # Add the two front rectangle corners to close the shape
                tip_points += [x2 + dx, y2 + dy, x2 - dx, y2 - dy]

                self.canvas.create_polygon(tip_points, fill=proj.color, outline=proj.color)

            elif proj.stype == 'slash':
                # --- CLEAN TAPERED CRESCENT BLADE ---
                r = proj.radius * 1.5
                max_thickness = proj.radius * 0.45   # thick in the middle
                angle = proj.angle
                cx, cy = proj.x, proj.y

                # Rotation helper
                def rot(x, y):
                    return (
                        cx + x * math.cos(angle) - y * math.sin(angle),
                        cy + x * math.sin(angle) + y * math.cos(angle)
                    )

                outer = []
                inner = []

                # Build outer arc and thin inner arc
                for a in range(-70, 71, 10):
                    rad = math.radians(a)

                    # Outer arc point
                    ox = math.cos(rad) * r
                    oy = math.sin(rad) * r
                    outer.append(rot(ox, oy))

                    # Taper thickness from center â†’ ends
                    taper_factor = 1 - abs(a) / 70   # 1 at center, 0 at tips
                    thickness = max_thickness * taper_factor

                    # Inner arc point (closer to the outer arc near the tips)
                    ix = math.cos(rad) * (r - thickness)
                    iy = math.sin(rad) * (r - thickness)
                    inner.append(rot(ix, iy))

                # Combine into a single crescent polygon
                blade_points = []
                for x, y in outer + inner[::-1]:
                    blade_points += [x, y]

                self.canvas.create_polygon(
                    blade_points,
                    fill=proj.color,
                    outline=proj.color,
                    width=1
                )
            elif proj.stype == 'slash2':
                # --- CLEAN TAPERED CRESCENT BLADE ---
                r = proj.radius * 2
                max_thickness = proj.radius * 3   # thick in the middle
                angle = proj.angle
                cx, cy = proj.x, proj.y

                # Rotation helper
                def rot(x, y):
                    return (
                        cx + x * math.cos(angle) - y * math.sin(angle),
                        cy + x * math.sin(angle) + y * math.cos(angle)
                    )

                outer = []
                inner = []

                # Build outer arc and thin inner arc
                for a in range(-70, 71, 10):
                    rad = math.radians(a)

                    # Outer arc point
                    ox = math.cos(rad) * r
                    oy = math.sin(rad) * r
                    outer.append(rot(ox, oy))

                    # Taper thickness from center â†’ ends
                    taper_factor = 1 - abs(a) / 70   # 1 at center, 0 at tips
                    thickness = max_thickness * taper_factor

                    # Inner arc point (closer to the outer arc near the tips)
                    ix = math.cos(rad) * (r - thickness)
                    iy = math.sin(rad) * (r - thickness)
                    inner.append(rot(ix, iy))

                # Combine into a single crescent polygon
                blade_points = []
                for x, y in outer + inner[::-1]:
                    blade_points += [x, y]

                self.canvas.create_polygon(
                    blade_points,
                    fill=proj.color,
                    outline=proj.color,
                    width=1
                )

            elif proj.stype == 'bolt1':
                # Even smaller rectangle
                length = r * 2.5      # shorter body
                width = r * 0.6       # narrower body

                # Center line endpoints
                x1 = x - math.cos(proj.angle) * length / 2
                y1 = y - math.sin(proj.angle) * length / 2
                x2 = x + math.cos(proj.angle) * length / 2
                y2 = y + math.sin(proj.angle) * length / 2

                # Perpendicular offset for width
                dx = math.sin(proj.angle) * width / 2
                dy = -math.cos(proj.angle) * width / 2

                # Rectangle points
                points = [
                    x1 - dx, y1 - dy,
                    x1 + dx, y1 + dy,
                    x2 + dx, y2 + dy,
                    x2 - dx, y2 - dy
                ]
                self.canvas.create_polygon(points, fill=proj.color)

                # Rounded nose at the front (same width as rectangle)
                radius = width / 2     # diameter = rectangle width
                bbox = [
                    x2 - radius, y2 - radius,
                    x2 + radius, y2 + radius
                ]
                start_angle = math.degrees(proj.angle) - 90
                self.canvas.create_arc(bbox, start=start_angle, extent=180,
                                       fill=proj.color, outline=proj.color)


        for part in self.particles:
            if part.rtype == "basic":
                self.canvas.create_oval(
                    part.x - part.size, part.y - part.size,
                    part.x + part.size, part.y + part.size,
                    fill=part.color
                )
            if part.rtype == "aura":
                self.canvas.create_oval(
                    part.x - part.size, part.y - part.size,
                    part.x + part.size, part.y + part.size,
                    fill=part.color,                # no fill, just outline
                    outline=part.color,     # outline in particle color
                    width=2                 # thickness of the outline
                )



            elif part.rtype == "trap":
                size = part.size
                ang = getattr(part, "angle", 0)

                # Equilateral triangle: 3 points spaced 120Â° apart
                p1 = (part.x + math.cos(ang) * size,
                      part.y + math.sin(ang) * size)
                p2 = (part.x + math.cos(ang + 2*math.pi/3) * size,
                      part.y + math.sin(ang + 2*math.pi/3) * size)
                p3 = (part.x + math.cos(ang + 4*math.pi/3) * size,
                      part.y + math.sin(ang + 4*math.pi/3) * size)

                self.canvas.create_polygon(p1, p2, p3,
                                      fill=part.color,
                                      outline="white",
                                      width=2)
            elif part.rtype == "diamond":
                # Simple, static diamond centered at the particle's position.
                s = part.size
                cx, cy = part.x, part.y

                points = [
                    cx,     cy - s,  # top
                    cx + s, cy,      # right
                    cx,     cy + s,  # bottom
                    cx - s, cy       # left
                ]
                self.canvas.create_polygon(points, fill="yellow", outline="gold", width=2)
            # --- inside GameFrame.draw(), in the loop: for part in self.particles ---
            elif part.rtype == "flame":
                r = part.size
                tip_x = part.x
                tip_y = part.y - r * 1.5

                # body (teardrop polygon)
                self.canvas.create_polygon(
                    part.x - r, part.y,      # left base
                    part.x + r, part.y,      # right base
                    tip_x, tip_y,            # tip
                    fill=part.color, outline=""
                )

                # inner glow
                self.canvas.create_oval(
                    part.x - r * 0.6, part.y - r * 0.6,
                    part.x + r * 0.6, part.y + r * 0.6,
                    fill="yellow", outline=""
                )
            elif part.rtype == "slash_line":
                # Draw slash line
                line_len = part.size
                x1 = part.x - math.cos(part.angle) * line_len / 2
                y1 = part.y - math.sin(part.angle) * line_len / 2
                x2 = part.x + math.cos(part.angle) * line_len / 2
                y2 = part.y + math.sin(part.angle) * line_len / 2
                
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=part.color,
                    width=3
                )
            elif part.rtype == "frost":
                # size and center
                s = part.size
                cx, cy = part.x, part.y

                # flicker color each frame
                color = "white" if random.random() < 0.5 else "cyan"

                # per-frame rotation (visual only)
                ang = (time.time() * 2.0) % (2 * math.pi)

                def rot(px, py):
                    rx = cx + px * math.cos(ang) - py * math.sin(ang)
                    ry = cy + px * math.sin(ang) + py * math.cos(ang)
                    return rx, ry

                # arms: cross + diagonals (snowflake star)
                arms = [
                    ((-s, 0), (s, 0)),          # horizontal
                    ((0, -s), (0, s)),          # vertical
                    ((-0.75*s, -0.75*s), (0.75*s, 0.75*s)),   # diag 1
                    ((0.75*s, -0.75*s), (-0.75*s, 0.75*s)),   # diag 2
                ]

                # draw arms
                for (ax1, ay1), (ax2, ay2) in arms:
                    x1, y1 = rot(ax1, ay1)
                    x2, y2 = rot(ax2, ay2)
                    self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)

                # subtle inner glow like flameâ€™s oval, but cyan/white
                glow_r = s * 0.5
                self.canvas.create_oval(
                    cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r,
                    fill="light cyan" if color == "cyan" else "white", outline=""
                )


            elif part.rtype == "blade":
                # --- ANIMATED SWEEPING CRESCENT ---
                r = part.size * 1.5
                max_thickness = part.size * 0.45
                sweep_off = getattr(part, "_sweep_offset", 0.0)
                angle = part.angle + sweep_off
                cx, cy = part.x, part.y
                total_life = getattr(part, "_total_life", max(part.life + part.age, 0.001))
                progress = part.age / total_life
                alpha = max(0.0, 1.0 - max(0.0, (progress - 0.6) / 0.4))
                try:
                    rv = int(self.canvas.winfo_rgb(part.color)[0] / 256 * alpha)
                    gv = int(self.canvas.winfo_rgb(part.color)[1] / 256 * alpha)
                    bv = int(self.canvas.winfo_rgb(part.color)[2] / 256 * alpha)
                    draw_color = f"#{rv:02x}{gv:02x}{bv:02x}"
                except Exception:
                    draw_color = part.color
                def _rot(x, y, _cx=cx, _cy=cy, _a=angle):
                    return (_cx + x * math.cos(_a) - y * math.sin(_a),
                            _cy + x * math.sin(_a) + y * math.cos(_a))
                outer_pts, inner_pts = [], []
                for a in range(-70, 71, 10):
                    rad = math.radians(a)
                    outer_pts.append(_rot(math.cos(rad) * r, math.sin(rad) * r))
                    tf = 1 - abs(a) / 70
                    th = max_thickness * tf
                    inner_pts.append(_rot(math.cos(rad) * (r - th), math.sin(rad) * (r - th)))
                bp = []
                for x, y in outer_pts + inner_pts[::-1]:
                    bp += [x, y]
                self.canvas.create_polygon(bp, fill=draw_color, outline=draw_color, width=1)
            elif part.rtype == "eblade":
                # --- CLEAN TAPERED CRESCENT BLADE ---
                r = part.size * 1.5
                max_thickness = part.size * 0.45   # thick in the middle
                angle = part.angle
                cx, cy = part.x, part.y

                # Rotation helper
                def rot(x, y):
                    return (
                        cx + x * math.cos(angle) - y * math.sin(angle),
                        cy + x * math.sin(angle) + y * math.cos(angle)
                    )

                outer = []
                inner = []

                # Build outer arc and thin inner arc
                for a in range(-70, 71, 10):
                    rad = math.radians(a)

                    # Outer arc point
                    ox = math.cos(rad) * r
                    oy = math.sin(rad) * r
                    outer.append(rot(ox, oy))

                    # Taper thickness from center â†’ ends
                    taper_factor = 1 - abs(a) / 70   # 1 at center, 0 at tips
                    thickness = max_thickness * taper_factor

                    # Inner arc point (closer to the outer arc near the tips)
                    ix = math.cos(rad) * (r - thickness)
                    iy = math.sin(rad) * (r - thickness)
                    inner.append(rot(ix, iy))

                # Combine into a single crescent polygon
                blade_points = []
                for x, y in outer + inner[::-1]:
                    blade_points += [x, y]

                self.canvas.create_polygon(
                    blade_points,
                    fill=part.color,
                    outline=part.color,
                    width=1
                )
            elif part.rtype == "blade1":
                # --- ANIMATED SWEEPING CRESCENT ---
                r = part.size * 0.4
                max_thickness = part.size * 0.4
                sweep_off = getattr(part, "_sweep_offset", 0.0)
                angle = part.angle + sweep_off
                cx, cy = part.x, part.y
                total_life = getattr(part, "_total_life", max(part.life + part.age, 0.001))
                progress = part.age / total_life
                alpha = max(0.0, 1.0 - max(0.0, (progress - 0.6) / 0.4))
                try:
                    rv = int(self.canvas.winfo_rgb(part.color)[0] / 256 * alpha)
                    gv = int(self.canvas.winfo_rgb(part.color)[1] / 256 * alpha)
                    bv = int(self.canvas.winfo_rgb(part.color)[2] / 256 * alpha)
                    draw_color = f"#{rv:02x}{gv:02x}{bv:02x}"
                except Exception:
                    draw_color = part.color
                def _rot(x, y, _cx=cx, _cy=cy, _a=angle):
                    return (_cx + x * math.cos(_a) - y * math.sin(_a),
                            _cy + x * math.sin(_a) + y * math.cos(_a))
                outer_pts, inner_pts = [], []
                for a in range(-70, 71, 10):
                    rad = math.radians(a)
                    outer_pts.append(_rot(math.cos(rad) * r, math.sin(rad) * r))
                    tf = 1 - abs(a) / 70
                    th = max_thickness * tf
                    inner_pts.append(_rot(math.cos(rad) * (r - th), math.sin(rad) * (r - th)))
                bp = []
                for x, y in outer_pts + inner_pts[::-1]:
                    bp += [x, y]
                self.canvas.create_polygon(bp, fill=draw_color, outline=draw_color, width=1)
            elif part.rtype == "blade1_fwd":
                # --- FORWARD LUNGING CRESCENT (strike) ---
                r = part.size * 0.5
                max_thickness = part.size * 0.5
                angle = part.angle
                cx, cy = part.x, part.y
                total_life = getattr(part, "_total_life", max(part.life + part.age, 0.001))
                progress = part.age / total_life
                alpha = max(0.0, 1.0 - max(0.0, (progress - 0.5) / 0.5))
                try:
                    rv = int(self.canvas.winfo_rgb(part.color)[0] / 256 * alpha)
                    gv = int(self.canvas.winfo_rgb(part.color)[1] / 256 * alpha)
                    bv = int(self.canvas.winfo_rgb(part.color)[2] / 256 * alpha)
                    draw_color = f"#{rv:02x}{gv:02x}{bv:02x}"
                except Exception:
                    draw_color = part.color
                def _rot_fwd(x, y, _cx=cx, _cy=cy, _a=angle):
                    return (_cx + x * math.cos(_a) - y * math.sin(_a),
                            _cy + x * math.sin(_a) + y * math.cos(_a))
                outer_pts, inner_pts = [], []
                for a in range(-70, 71, 10):
                    rad = math.radians(a)
                    outer_pts.append(_rot_fwd(math.cos(rad) * r, math.sin(rad) * r))
                    tf = 1 - abs(a) / 70
                    th = max_thickness * tf
                    inner_pts.append(_rot_fwd(math.cos(rad) * (r - th), math.sin(rad) * (r - th)))
                bp = []
                for x, y in outer_pts + inner_pts[::-1]:
                    bp += [x, y]
                self.canvas.create_polygon(bp, fill=draw_color, outline=draw_color, width=1)
            elif part.rtype == "eblade1_fwd":
                # --- FORWARD LUNGING CRESCENT (enemy strike) ---
                r = part.size * 0.5
                max_thickness = part.size * 0.5
                angle = part.angle
                cx, cy = part.x, part.y
                total_life = getattr(part, "_total_life", max(part.life + part.age, 0.001))
                progress = part.age / total_life
                alpha = max(0.0, 1.0 - max(0.0, (progress - 0.5) / 0.5))
                try:
                    rv = int(self.canvas.winfo_rgb(part.color)[0] / 256 * alpha)
                    gv = int(self.canvas.winfo_rgb(part.color)[1] / 256 * alpha)
                    bv = int(self.canvas.winfo_rgb(part.color)[2] / 256 * alpha)
                    draw_color = f"#{rv:02x}{gv:02x}{bv:02x}"
                except Exception:
                    draw_color = part.color
                def _rot_efwd(x, y, _cx=cx, _cy=cy, _a=angle):
                    return (_cx + x * math.cos(_a) - y * math.sin(_a),
                            _cy + x * math.sin(_a) + y * math.cos(_a))
                outer_pts, inner_pts = [], []
                for a in range(-70, 71, 10):
                    rad = math.radians(a)
                    outer_pts.append(_rot_efwd(math.cos(rad) * r, math.sin(rad) * r))
                    tf = 1 - abs(a) / 70
                    th = max_thickness * tf
                    inner_pts.append(_rot_efwd(math.cos(rad) * (r - th), math.sin(rad) * (r - th)))
                bp = []
                for x, y in outer_pts + inner_pts[::-1]:
                    bp += [x, y]
                self.canvas.create_polygon(bp, fill=draw_color, outline=draw_color, width=1)
            elif part.rtype == "eblade1":
                # --- ANIMATED SWEEPING CRESCENT ---
                r = part.size * 0.4
                max_thickness = part.size * 0.4
                sweep_off = getattr(part, "_sweep_offset", 0.0)
                angle = part.angle + sweep_off
                cx, cy = part.x, part.y
                total_life = getattr(part, "_total_life", max(part.life + part.age, 0.001))
                progress = part.age / total_life
                alpha = max(0.0, 1.0 - max(0.0, (progress - 0.6) / 0.4))
                try:
                    rv = int(self.canvas.winfo_rgb(part.color)[0] / 256 * alpha)
                    gv = int(self.canvas.winfo_rgb(part.color)[1] / 256 * alpha)
                    bv = int(self.canvas.winfo_rgb(part.color)[2] / 256 * alpha)
                    draw_color = f"#{rv:02x}{gv:02x}{bv:02x}"
                except Exception:
                    draw_color = part.color
                def _rot(x, y, _cx=cx, _cy=cy, _a=angle):
                    return (_cx + x * math.cos(_a) - y * math.sin(_a),
                            _cy + x * math.sin(_a) + y * math.cos(_a))
                outer_pts, inner_pts = [], []
                for a in range(-70, 71, 10):
                    rad = math.radians(a)
                    outer_pts.append(_rot(math.cos(rad) * r, math.sin(rad) * r))
                    tf = 1 - abs(a) / 70
                    th = max_thickness * tf
                    inner_pts.append(_rot(math.cos(rad) * (r - th), math.sin(rad) * (r - th)))
                bp = []
                for x, y in outer_pts + inner_pts[::-1]:
                    bp += [x, y]
                self.canvas.create_polygon(bp, fill=draw_color, outline=draw_color, width=1)
            elif part.rtype == "shield":
                # outlined circle (no fill)
                self.canvas.create_oval(
                    part.x - part.size, part.y - part.size,
                    part.x + part.size, part.y + part.size,
                    outline=part.color, width=2
                )
            elif part.rtype == "fire_puff":
                # Cosmetic fire particle — fading glowing circle
                r = max(1, part.size)
                self.canvas.create_oval(part.x-r, part.y-r, part.x+r, part.y+r,
                                        fill=part.color, outline='')
            elif part.rtype == "smoke_puff":
                # Drift upward, gentle sway, fixed size
                part.y  -= 0.35
                part.x  += math.sin(part.age * 2.1) * 0.25
                part.age = getattr(part, 'age', 0) + 0.05
                r = max(1, part.size)
                self.canvas.create_oval(part.x-r, part.y-r, part.x+r, part.y+r,
                                        fill='#707070', outline='', stipple='gray75')
            elif part.rtype == "magic_burst":
                # Small sparkling dot burst
                r = max(1, part.size)
                self.canvas.create_oval(part.x-r, part.y-r, part.x+r, part.y+r,
                                        fill=part.color, outline='white' if r > 3 else '')
            elif part.rtype == "frozen_ice":
                # Ice cube drawn around the entity — thick bright outline + stippled fill
                hs = int(part.size)
                cx2, cy2 = int(part.x), int(part.y)
                # Outer fill layer — stippled light-blue (see-through effect)
                self.canvas.create_rectangle(
                    cx2 - hs, cy2 - hs, cx2 + hs, cy2 + hs,
                    fill='#00ccff', outline='', stipple='gray50'
                )
                # Bright solid border so it is always visible
                self.canvas.create_rectangle(
                    cx2 - hs, cy2 - hs, cx2 + hs, cy2 + hs,
                    outline='#00eeff', fill='', width=4
                )
                # Inner bright ring
                self.canvas.create_rectangle(
                    cx2 - hs + 5, cy2 - hs + 5, cx2 + hs - 5, cy2 + hs - 5,
                    outline='#aaffff', fill='', width=1
                )
                # Corner icicle crystals
                for _icx, _icy in [(cx2-hs, cy2-hs),(cx2+hs, cy2-hs),
                                    (cx2-hs, cy2+hs),(cx2+hs, cy2+hs)]:
                    self.canvas.create_oval(_icx-4, _icy-4, _icx+4, _icy+4,
                                            fill='#ffffff', outline='#00ddff', width=1)
            elif part.rtype == "branch":
                # Draw the whip line from player to animated position
                self.canvas.create_line(
                    self.player.x, self.player.y,
                    part.x, part.y,
                    fill=part.color, width=5, smooth=True
                )
                # Draw tip circle
                self.canvas.create_oval(
                    part.x - part.size, part.y - part.size,
                    part.x + part.size, part.y + part.size,
                    fill=part.color, outline=""
                )
            elif part.rtype == "leaf":
                # Draw small leaf at animated position
                self.canvas.create_oval(
                    part.x - part.size, part.y - part.size,
                    part.x + part.size, part.y + part.size,
                    fill=part.color, outline=""
                )
            elif part.rtype == "shockwave":
                # Draw a layered expanding ring centered on the particle
                self.canvas.create_oval(
                    part.x - part.size, part.y - part.size,
                    part.x + part.size, part.y + part.size,
                    outline="white", width=6
                )
                self.canvas.create_oval(
                    part.x - part.size, part.y - part.size,
                    part.x + part.size, part.y + part.size,
                    outline="yellow", width=3
                )


        # ── Mini-map panel (right strip) ──────────────────────────────────
        self.draw_minimap()

        # ── Draw coin particles (world-space → screen) ──────────────────
        for cp in self.coin_particles:
            if self.dungeon_id == 0:
                sx = cp.x - self.camera_x
                sy = cp.y - self.camera_y
            else:
                sx, sy = cp.x, cp.y
            if -20 < sx < WINDOW_W + 20 and -20 < sy < WINDOW_H + 20:
                cp.draw(self.canvas, sx, sy)

        # HUD: HP/Mana/XP
        BAR_X, BAR_W, BAR_H = 10, 200, 20

        # --- HP bar: grey background → red HP → white shield ON TOP of red ---
        self.canvas.create_rectangle(BAR_X, 10, BAR_X + BAR_W, 10 + BAR_H, fill='#3a3a3a')
        hpw = int((self.player.hp / self.player.max_hp) * BAR_W) if self.player.max_hp else 0
        self.canvas.create_rectangle(BAR_X, 10, BAR_X + hpw, 10 + BAR_H, fill='#cc2222')
        # Shield covers the HP bar from the left, like a white skin over red
        if getattr(self.player, 'max_shield', 0) > 0:
            shp = self.player
            # Shield fills the same left-to-right region as HP, capped at the HP width
            shield_frac = shp.shield / shp.max_shield if shp.max_shield else 0
            shw = int(min(shield_frac, 1.0) * hpw)   # covers UP TO hpw pixels
            if shw > 0:
                # Draw with slight transparency feel using a lighter shade + thin border
                self.canvas.create_rectangle(BAR_X, 10,
                                             BAR_X + shw, 10 + BAR_H,
                                             fill='#cce8ff', outline='')
                # Subtle inner shimmer line
                self.canvas.create_rectangle(BAR_X, 10,
                                             BAR_X + shw, 10 + 4,
                                             fill='#ffffff', outline='')
            # Shield label right of bar
            self.canvas.create_text(BAR_X + BAR_W + 4, 10, anchor='nw',
                                    text=f'🛡 {int(shp.shield)}/{int(shp.max_shield)}',
                                    fill='#aaddff', font=('Arial', 7, 'bold'))
        hp_text = f"{int(self.player.hp)}/{int(self.player.max_hp)}"
        self.canvas.create_text(BAR_X + BAR_W // 2, 10 + BAR_H // 2,
                                text=hp_text, fill='white', font=('Agency FB', 10, 'bold'))

        # --- Mana bar ---
        self.canvas.create_rectangle(BAR_X, 35, BAR_X + BAR_W, 55, fill='#3a3a3a')
        mw = int((self.player.mana / self.player.max_mana) * BAR_W) if self.player.max_mana else 0
        self.canvas.create_rectangle(BAR_X, 35, BAR_X + mw, 55, fill='#2255cc')
        mana_text = f"{int(self.player.mana)}/{int(self.player.max_mana)}"
        self.canvas.create_text(BAR_X + BAR_W // 2, 45,
                                text=mana_text, fill='white', font=('Agency FB', 10, 'bold'))

        # --- XP bar ---
        self.canvas.create_rectangle(BAR_X, 60, BAR_X + BAR_W, 70, fill='#3a3a3a')
        xpw = int((self.player.xp / self.player.xp_to_next) * BAR_W) if self.player.xp_to_next else 0
        self.canvas.create_rectangle(BAR_X, 60, BAR_X + xpw, 70, fill='#22aa22')
        self.canvas.create_text(220, 60, text=f'LV {self.player.level}', fill='white', anchor='nw')



        # ── Death screen overlay ─────────────────────────────────────────────
        if self.dead:
            cw = WINDOW_W
            ch = WINDOW_H
            # Dark red semi-transparent overlay (simulate with stipple)
            self.canvas.create_rectangle(0, 0, cw, ch,
                                         fill='#1a0000', stipple='gray50', outline='')
            self.canvas.create_rectangle(0, 0, cw, ch,
                                         fill='#3a0000', stipple='gray25', outline='')
            # Pulsing red border effect (4 nested rectangles)
            for offset, col in [(0, '#8b0000'), (6, '#cc0000'), (12, '#ff2222'), (18, '#ff6666')]:
                self.canvas.create_rectangle(offset, offset, cw - offset, ch - offset,
                                             outline=col, width=3)
            # "YOU DIED" title
            self.canvas.create_text(cw // 2 + 3, ch // 2 - 77,
                                    text="YOU DIED", fill='#3a0000',
                                    font=('Impact', 56, 'bold'))
            self.canvas.create_text(cw // 2, ch // 2 - 80,
                                    text="YOU DIED", fill='#ff2222',
                                    font=('Impact', 56, 'bold'))
            # Respawning countdown
            secs_left = max(0, self.respawn_time)
            self.canvas.create_text(cw // 2 + 2, ch // 2 + 2,
                                    text=f"Respawning in  {secs_left:.1f}s...",
                                    fill='#1a0000', font=('Arial', 20, 'bold'))
            self.canvas.create_text(cw // 2, ch // 2,
                                    text=f"Respawning in  {secs_left:.1f}s...",
                                    fill='#ffaaaa', font=('Arial', 20, 'bold'))
            # Item loss warning
            self.canvas.create_text(cw // 2 + 1, ch // 2 + 41,
                                    text="You will lose 10% of your coins!",
                                    fill='#3a0000', font=('Arial', 13))
            self.canvas.create_text(cw // 2, ch // 2 + 40,
                                    text="You will lose 10% of your coins!",
                                    fill='#ff8888', font=('Arial', 13))

    # ── Help / Tutorial overlay ──────────────────────────────────────────────
    def draw_help_panel(self):
        """Draw the Help & Tutorial overlay (toggled with H)."""
        cv  = self.canvas
        W, H = WINDOW_W, WINDOW_H
        p   = self.player

        # ── Semi-transparent dark backdrop ───────────────────────────────────
        cv.create_rectangle(0, 0, W, H, fill='#000000', stipple='gray50', outline='')
        cv.create_rectangle(0, 0, W, H, fill='#000020', stipple='gray25', outline='')

        # ── Panel frame ──────────────────────────────────────────────────────
        PX, PY, PW, PH = 40, 30, W - 80, H - 60
        cv.create_rectangle(PX-2, PY-2, PX+PW+2, PY+PH+2,
                            fill='#0a0a1a', outline='#6644cc', width=3)
        cv.create_rectangle(PX, PY, PX+PW, PY+PH, fill='#0f0f22', outline='')

        # ── Title bar ────────────────────────────────────────────────────────
        cv.create_rectangle(PX, PY, PX+PW, PY+28, fill='#1a1a3a', outline='')
        cv.create_text(PX+PW//2, PY+14, text='📖  HOW TO PLAY',
                       fill='#ccaaff', font=('Arial', 13, 'bold'))
        cv.create_text(PX+PW-10, PY+14, text='[H] close',
                       fill='#555577', font=('Arial', 8), anchor='e')

        # ── Tab bar ──────────────────────────────────────────────────────────
        TAB_LABELS = ['⚔ Stats', '✨ Skills', '🗺 Dungeon', '⌨ Keybinds', '💡 Tips']
        TAB_Y  = PY + 28
        TAB_H  = 26
        TW     = PW // len(TAB_LABELS)
        for idx, label in enumerate(TAB_LABELS):
            tx0 = PX + idx * TW
            tx1 = tx0 + TW
            active = (idx == self._help_tab)
            bg  = '#2a1a4a' if active else '#141428'
            ol  = '#8866dd' if active else '#333355'
            cv.create_rectangle(tx0, TAB_Y, tx1, TAB_Y+TAB_H, fill=bg, outline=ol, width=1)
            fc  = '#ddbbff' if active else '#666688'
            cv.create_text((tx0+tx1)//2, TAB_Y+TAB_H//2, text=label,
                           fill=fc, font=('Arial', 9, 'bold' if active else 'normal'))

        # ── Content area ─────────────────────────────────────────────────────
        CY = TAB_Y + TAB_H + 8   # top of content
        CX = PX + 18
        CW = PW - 36
        LH = 19   # line height

        def heading(text, y):
            cv.create_text(CX, y, text=text, fill='#aa88ff',
                           font=('Arial', 10, 'bold'), anchor='nw')
            cv.create_line(CX, y+14, CX+CW, y+14, fill='#333355', width=1)
            return y + 20

        def row(label, value, y, label_col='#8888aa', val_col='#ddddff'):
            cv.create_text(CX, y, text=label, fill=label_col,
                           font=('Arial', 9), anchor='nw')
            cv.create_text(CX+180, y, text=value, fill=val_col,
                           font=('Arial', 9), anchor='nw')
            return y + LH

        def para(text, y, col='#aaaacc', wrap=CW):
            cv.create_text(CX, y, text=text, fill=col, font=('Arial', 9),
                           anchor='nw', width=wrap)
            # Estimate lines for offset
            chars_per_line = max(1, wrap // 6)
            lines = max(1, len(text) // chars_per_line + text.count('\n') + 1)
            return y + lines * (LH - 2) + 4

        tab = self._help_tab

        # ── TAB 0: STATS ─────────────────────────────────────────────────────
        if tab == 0:
            y = CY
            y = heading('Primary Stats — what each stat does', y)
            stat_info = [
                ('STRENGTH',     f'{p.strength}',  'Increases physical attack damage (+1 ATK per point)'),
                ('VITALITY',     f'{p.vitality}',  'Increases max HP (+10 HP) and HP regeneration'),
                ('AGILITY',      f'{p.agility}',   'Increases movement speed (+0.15 speed per point)'),
                ('INTELLIGENCE', f'{p.intelligence}','Increases max Mana (+10 Mana per point)'),
                ('WISDOM',       f'{p.wisdom}',    'Increases magic power and mana regeneration'),
                ('WILL',         f'{p.will}',      'Increases magical damage output'),
                ('CONSTITUTION', f'{p.constitution}','Defensive stat — affects shield and damage reduction'),
            ]
            for stat, val, desc in stat_info:
                if y > PY + PH - 30:
                    break
                cv.create_text(CX,       y, text=stat,  fill='#ffdd88', font=('Arial', 8, 'bold'), anchor='nw')
                cv.create_text(CX+130,   y, text=f'[{val}]', fill='#88ffbb', font=('Arial', 8, 'bold'), anchor='nw')
                cv.create_text(CX+165,   y, text=desc,  fill='#aaaacc', font=('Arial', 8), anchor='nw', width=CW-165)
                y += LH + 2

            y += 6
            if y < PY + PH - 60:
                y = heading('Derived Stats', y)
                y = row('Max HP',         f'{int(p.max_hp)}',          y)
                y = row('Max Mana',       f'{int(p.max_mana)}',        y)
                y = row('ATK (Physical)', f'{int(p.atk)}',             y)
                y = row('MAG (Spell)',    f'{int(p.mag)}',             y)
                y = row('Speed',          f'{p.speed:.2f}',            y)
                y = row('HP Regen/s',     f'{p.hp_regen:.2f}',         y)
                y = row('Mana Regen/s',   f'{p.mana_regen:.2f}',       y)

            y += 6
            if y < PY + PH - 50:
                y = heading('Levelling Up', y)
                y = para('Each level-up grants 3 Stat Points and 1 Skill Point.\n'
                         'Stat Points are spent in the Stats panel (P).\n'
                         f'Your class ({p.class_name}) also gains automatic stats each level.', y)

        # ── TAB 1: SKILLS ────────────────────────────────────────────────────
        elif tab == 1:
            y = CY
            y = heading(f'{p.class_name} Skill Tree  —  Skill Points: {p.skill_points}', y)
            tree = SKILL_TREES.get(p.class_name, [])
            col_a, col_b = CX, CX + CW//2
            for i, node in enumerate(tree):
                if y > PY + PH - 30:
                    break
                unlocked = node['name'] in p.tree_unlocked
                name_col = '#88ff88' if unlocked else ('#ffdd44' if node['cost'] == 0 else '#aaaacc')
                status   = '✔' if unlocked else ('FREE' if node['cost'] == 0 else f'{node["cost"]} SP')
                stype    = '⚡' if node['type'] == 'active' else '🔷'
                cv.create_text(col_a, y, text=f'T{node["tier"]} {stype} {node["name"]}',
                               fill=name_col, font=('Arial', 8, 'bold'), anchor='nw')
                cv.create_text(col_b, y, text=f'[{status}]  {node["desc"][:55]}',
                               fill='#888899', font=('Arial', 7), anchor='nw', width=CW//2-4)
                y += LH + 1

            y += 8
            if y < PY + PH - 80:
                y = heading('How the Skill Hotbar Works', y)
                y = para('Open O → Skills tab to assign unlocked skills to slots 1-5.\n'
                         'Left-click (or press the matching number key) to fire the selected skill.\n'
                         'Active skills consume Mana and have cooldowns shown by the grey overlay.\n'
                         'Passive skills are always-on (or toggled) — they do NOT appear on the hotbar.', y)

            if y < PY + PH - 50:
                y = heading('Legend', y)
                y = row('⚡  Active',  'Costs Mana, fires on click / key', y)
                y = row('🔷  Passive', 'Always active — stat or behaviour bonus', y)
                y = row('T1-T4',       'Tier — unlock higher tiers via prereqs', y)

        # ── TAB 2: DUNGEON ───────────────────────────────────────────────────
        elif tab == 2:
            y = CY
            y = heading('Town & Overworld', y)
            y = para('You start in the Town. Explore it to find shops, the Inn, the Blacksmith,\n'
                     'the Library, the Mage Tower, and your House. Talk to NPCs with [C] when nearby.', y)

            y = heading('Entering Dungeons', y)
            y = para('Walk into the forest past the town border to find dungeon portals marked with coloured\n'
                     'pillars. Press [C] when the "Enter Dungeon" prompt appears. There are 4 dungeons\n'
                     'of increasing difficulty arranged around the town.', y)

            y = heading('Dungeon Rooms', y)
            y = para('Each dungeon has a grid of rooms (2 rows × 5 cols). Move between rooms by walking\n'
                     'to the edge of the screen. Clear all enemies to unlock doors to the next room.\n'
                     'The final room contains a powerful boss.', y)

            if y < PY + PH - 80:
                y = heading('Dungeons at a Glance', y)
                dungeon_data = [
                    ('Dungeon 1 — West Forest',  'Lvl 1–5',  'Slimes, Goblins',      'Green drops, starter loot'),
                    ('Dungeon 2 — East Forest',  'Lvl 5–10', 'Skeletons, Orcs',       'Better weapons & armour'),
                    ('Dungeon 3 — North Forest', 'Lvl 10–20','Demons, Dark Knights',  'Rare & Epic gear'),
                    ('Dungeon 4 — South Forest', 'Lvl 20+',  'Dragons, Lich',         'Legendary drops'),
                ]
                headers = ['Location', 'Rec. Level', 'Enemies', 'Reward']
                hx = [CX, CX+150, CX+230, CX+360]
                for hdr, hpos in zip(headers, hx):
                    cv.create_text(hpos, y, text=hdr, fill='#aa88ff',
                                   font=('Arial', 8, 'bold'), anchor='nw')
                y += LH
                cv.create_line(CX, y, CX+CW, y, fill='#333355', width=1)
                y += 4
                for name, lvl, enemies, reward in dungeon_data:
                    if y > PY + PH - 22:
                        break
                    for text, hpos in zip([name, lvl, enemies, reward], hx):
                        cv.create_text(hpos, y, text=text, fill='#aaaacc',
                                       font=('Arial', 8), anchor='nw')
                    y += LH

        # ── TAB 3: KEYBINDS ──────────────────────────────────────────────────
        elif tab == 3:
            y = CY
            binds = [
                ('Movement',   [
                    ('W / A / S / D',  'Move up / left / down / right'),
                    ('(or Arrow Keys)','Alternative movement'),
                ]),
                ('Combat',     [
                    ('Left Click',     'Fire active skill / spend stat point'),
                    ('Right Click',    'Use consumable in active item slot'),
                    ('1 – 5',          'Select skill hotbar slot'),
                    ('T / Y / U',      'Select consumable hotbar slot 0 / 1 / 2'),
                    ('R',              'Rotate beam skill (when active)'),
                ]),
                ('UI & Menus', [
                    ('H',              'Open / close this Help screen'),
                    ('O',              'Open Inventory + Skill Tree window'),
                    ('P',              'Open / close Stats panel (spend stat points)'),
                    ('C',              'Interact with NPC / enter dungeon / talk'),
                    ('E',              'Interact with objects indoors (chest, etc.)'),
                    ('Escape',         'Return to main menu (Town only)'),
                ]),
                ('Indoors',    [
                    ('Walk to EXIT',   'Leave a building (bottom of the room)'),
                    ('C',              'Talk to indoor NPC / open shop'),
                    ('E',              'Open / interact with chest'),
                    ('T / Y / U',      'Item hotbar still works while shopping'),
                ]),
            ]
            col_key = CX
            col_val = CX + 175
            for section, keys in binds:
                if y > PY + PH - 40:
                    break
                y = heading(section, y)
                for k, v in keys:
                    if y > PY + PH - 22:
                        break
                    # Key badge
                    kw = 160
                    cv.create_rectangle(col_key-2, y-1, col_key+kw, y+LH-3,
                                        fill='#1e1e3a', outline='#444466', width=1)
                    cv.create_text(col_key+kw//2, y+LH//2-2, text=k,
                                   fill='#eecc88', font=('Arial', 8, 'bold'))
                    cv.create_text(col_val, y, text=v,
                                   fill='#aaaacc', font=('Arial', 9), anchor='nw')
                    y += LH + 2

        # ── TAB 4: TIPS ──────────────────────────────────────────────────────
        elif tab == 4:
            y = CY
            y = heading('Beginner Tips', y)
            tips = [
                ('💰', 'Coins',      'Visit the Bakery for cheap HP potions early on. The Blacksmith sells powerful gear.'),
                ('⚔', 'Combat',     'Stand still when firing skills — moving while casting can mis-aim projectiles.'),
                ('📦', 'Hotbar',     'Drag consumables from your Inventory (O) to the T/Y/U hotbar slots. Right-click to use.'),
                ('✨', 'Skills',     'Unlock your class\'s free Tier-1 skill first — it costs 0 SP and is your main damage tool.'),
                ('🗡', 'Equip',      'Always equip your best weapon. Your equipped Soulbound item is permanent and grows with you.'),
                ('🏠', 'Your House', 'Your house has a chest — store extra items there to keep your inventory clean.'),
                ('🗺', 'Map',        'Equip a Map item to reveal the mini-map on the right panel. Very helpful in dungeons.'),
                ('❤', 'Regen',      'HP and Mana regenerate passively. Rest in town between dungeon runs to recover.'),
                ('📈', 'Levelling',  'Focus one stat — Vitality for tanky builds, Intelligence+Wisdom for Mage, Agility for Rogue.'),
                ('⚠', 'Death',      'Dying costs 10% of your coins but you keep all items. Use potions before you get too low!'),
            ]
            for emoji, title, tip in tips:
                if y > PY + PH - 26:
                    break
                cv.create_text(CX,      y, text=emoji,            fill='#ffffff',  font=('Arial', 10),         anchor='nw')
                cv.create_text(CX+22,   y, text=title+':',        fill='#ffdd88',  font=('Arial', 9, 'bold'),  anchor='nw')
                cv.create_text(CX+100,  y, text=tip,              fill='#aaaacc',  font=('Arial', 8),          anchor='nw', width=CW-100)
                y += LH + 3

            if y < PY + PH - 60:
                y += 6
                y = heading(f'Your Character: {p.name}  [{p.class_name}  Lv.{p.level}]', y)
                class_descs = {
                    'Warrior': 'Melee powerhouse — high HP and physical damage. Stack Strength and Vitality.',
                    'Mage':    'Spell caster — fragile but devastating AoE. Stack Intelligence and Wisdom.',
                    'Rogue':   'Fast striker — burst damage and mobility. Stack Agility and Strength.',
                    'Cleric':  'Holy support — healing and bolts. Stack Will and Wisdom for spell power.',
                    'Druid':   'Nature magic — pets and area spells. Stack Wisdom and Vitality.',
                    'Monk':    'Chi fighter — powerful but HP-hungry. Stack Vitality and Constitution.',
                    'Ranger':  'Archer — ranged attacks and traps. Stack Agility and Intelligence.',
                }
                para(class_descs.get(p.class_name, ''), y)

        # ── Tab click detection: record hit boxes for on_canvas_click ────────
        self._help_tab_rects = []
        for idx in range(len(TAB_LABELS)):
            tx0 = PX + idx * TW
            tx1 = tx0 + TW
            self._help_tab_rects.append((tx0, TAB_Y, tx1, TAB_Y + TAB_H))

    def _help_tab_click(self, event):
        """Switch help tab when the user clicks a tab header."""
        if not self.show_help:
            return
        rects = getattr(self, '_help_tab_rects', [])
        for idx, (x0, y0, x1, y1) in enumerate(rects):
            if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                self._help_tab = idx
                return

# Inventory button hint
    def draw_stats_panel(self):
        p = self.player

        # Outer frame
        self.canvas.create_rectangle(100, 100, 720, 530, fill='#1a1a1a', outline='white', width=4)

        stats = ['strength','vitality','agility','constitution','intelligence','wisdom','will']
        stat_display_names = {
            'strength': 'STRENGTH', 'vitality': 'VITALITY',
            'agility': 'AGILITY', 'constitution': 'CONSTITUTION',
            'intelligence': 'INTELLIGENCE', 'wisdom': 'WISDOM', 'will': 'WILL'
        }

        # Collect active buff amounts per stat
        buff_by_stat = {'strength': 0, 'agility': 0, 'will': 0}
        now = time.time()
        for buf in getattr(p, 'active_buffs', []):
            if now < buf['end']:
                buff_by_stat['strength'] += buf.get('str', 0)
                buff_by_stat['agility']  += buf.get('agi', 0)
                buff_by_stat['will']     += buf.get('wil', 0)

        # Fixed column positions — no character-length guessing
        COL_NAME  = 130   # stat name + base value
        COL_EQUIP = 460   # item bonus  (+N)
        COL_BUFF  = 540   # buff bonus  [+N]
        COL_BTN   = 660   # + button

        y_start    = 120
        stat_height = 40

        for i, stat in enumerate(stats):
            buff_val  = buff_by_stat.get(stat, 0)
            base_val  = getattr(p, stat) - buff_val   # clean base without transient buff

            equip_bonus = 0
            for item in p.equipped_items:
                equip_bonus += item.stats.get(stat, 0)
            for item in p.soulbound_items:
                equip_bonus += item.stats.get(stat, 0)

            y = y_start + i * stat_height

            # Row background
            self.canvas.create_rectangle(120, y, 710, y + 30, fill='#111111')

            # STAT NAME: base value  — white
            self.canvas.create_text(COL_NAME, y + 15, anchor='w',
                                    text=f'{stat_display_names[stat]}: {base_val}',
                                    fill='white', font=('Arial', 13, 'bold'))

            # Equipment bonus — gold, at fixed column
            if equip_bonus > 0:
                self.canvas.create_text(COL_EQUIP, y + 15, anchor='w',
                                        text=f'(+{equip_bonus})',
                                        fill='#FFD700', font=('Arial', 13))

            # Buff bonus — green, at fixed column
            if buff_val > 0:
                self.canvas.create_text(COL_BUFF, y + 15, anchor='w',
                                        text=f'[+{buff_val}]',
                                        fill='#44ff88', font=('Arial', 13, 'italic'))

            # + button
            if p.stat_points > 0:
                self.canvas.create_rectangle(COL_BTN, y + 2, COL_BTN + 28, y + 28,
                                             fill='#333333', outline='white', width=1)
                self.canvas.create_text(COL_BTN + 14, y + 15,
                                        text='+', fill='white', font=('Arial', 14, 'bold'))

        # Column headers
        self.canvas.create_text(COL_NAME,  112, anchor='w', text='STAT',
                                fill='#888888', font=('Arial', 9))
        self.canvas.create_text(COL_EQUIP, 112, anchor='w', text='ITEM',
                                fill='#888888', font=('Arial', 9))
        self.canvas.create_text(COL_BUFF,  112, anchor='w', text='BUFF',
                                fill='#888888', font=('Arial', 9))

        # Stat points — single line
        self.canvas.create_text(130, y_start + len(stats)*stat_height + 10,
                                anchor='w',
                                text=f'Stat Points Available: {p.stat_points}',
                                fill='#aaaaaa', font=('Arial', 13))

        # Active buffs summary
        active_buffs = [b for b in getattr(p, 'active_buffs', []) if now < b['end']]
        if active_buffs:
            bby = y_start + len(stats)*stat_height + 34
            self.canvas.create_text(130, bby, anchor='w',
                                    text='Active Buffs:', fill='#44ff88',
                                    font=('Arial', 10, 'bold'))
            for j, buf in enumerate(active_buffs[:3]):
                remaining = buf['end'] - now
                self.canvas.create_text(130, bby + 16 + j*16, anchor='w',
                                        text=f"{buf['emoji']} {buf['name']}  {remaining:.0f}s",
                                        fill='#44ff88', font=('Arial', 9))
    def loop(self):
        self.poll_mouse_pos()          # update mouse once per frame, no event spam
        now=time.time(); dt=now-self.last_time; self.last_time=now
        self.update_camera()
        self.update_player(dt)
        self.update_entities(dt)
        self.draw()
        self.draw_hotbar()  # consumable hotbar always visible; skill hotbar hidden indoors
        if self.show_help:
            self.draw_help_panel()
        if self.show_stats:
            self.draw_stats_panel()
        self.after(16,self.loop)
        for enemy in self.room.enemies:
            resolve_overlap(self.player, enemy)

        # Enemy vs enemy
        for i, e1 in enumerate(self.room.enemies):
            for j, e2 in enumerate(self.room.enemies):
                if i < j:  # avoid double-checking
                    resolve_overlap(e1, e2)
# ---------- Main window with Home Screen ----------
class MainApp(tk.Tk):
    SAVE_FILE = "player_save.json"
    
    CLASS_INFO = {
        'Warrior': {'emoji': '⚔️', 'color': '#d32f2f', 'desc': 'Master of melee combat\nHigh HP and physical damage'},
        'Mage': {'emoji': '🔮', 'color': '#1976d2', 'desc': 'Wields elemental magic\nPowerful spells and mana'},
        'Rogue': {'emoji': '🗡', 'color': '#7b1fa2', 'desc': 'Swift and deadly striker\nHigh agility and burst damage'},
        'Cleric': {'emoji': '✨', 'color': '#fbc02d', 'desc': 'Holy warrior and healer\nSupport and light magic'},
        'Druid': {'emoji': '🍃', 'color': '#388e3c', 'desc': 'Nature\'s guardian\nSummons and natural magic'},
        'Monk': {'emoji': '👊', 'color': '#ff6f00', 'desc': 'Chi-powered fighter\nUses HP for devastating attacks'},
        'Ranger': {'emoji': '🏹', 'color': '#CD853F', 'desc': 'Expert archer and trapper\nRanged attacks and tactical skills'}
    }

    def reset_character(self):
        if not hasattr(self, 'preview_player'):
            return
        from tkinter import messagebox
        if messagebox.askyesno("Reset Character", "Are you sure you want to reset your character?"):
            self.preview_player.reset()
            self.class_chosen = False
            self.update_preview()
            self.build_home()
            self.save_player(self.preview_player.to_dict())

    def __init__(self):
        super().__init__()
        self.title("Dungeon LitRPG - Hub")
        self.geometry("1000x800")
        self.resizable(False, False)
        self.configure(bg='#0a0a0a')

        self.class_chosen = False

        self.player_data = self.load_player() or {"name": "Hero", "class_name": ""}
        self.selected_class = self.player_data.get("class_name", "")
        if self.selected_class:
            self.class_chosen = True

        self.name_var = tk.StringVar(value=self.player_data.get("name", "Hero"))
        self.preview_player = Player(self.name_var.get(), self.selected_class or "Warrior")
        self.preview_player.unlock_skills()

        self.home_frame = tk.Frame(self, bg='#1a1a1a')
        self.home_frame.pack(fill='both', expand=True)
        self.game_frame_container = None
        self._save_code_text = None   # initialised properly in build_home

        # Load saved player data if it exists
        if self.player_data.get("class_name"):
            try:
                self.preview_player = Player.from_dict(self.player_data)
            except Exception:
                pass  # keep the default preview_player created above

        self.build_home()
    # In MainApp class, ADD THIS METHOD (not inside build_home):
    def open_shop(self):
        """Open shop window"""
        shop_win = tk.Toplevel(self)
        shop_win.title("Shop")
        shop_win.geometry("700x600")
        shop_win.configure(bg="#1a1a1a")
        
        # Coins display
        coin_frame = tk.Frame(shop_win, bg="#2a2a2a")
        coin_frame.pack(fill='x', pady=10, padx=10)
        
        def update_coins():
            for widget in coin_frame.winfo_children():
                widget.destroy()
            tk.Label(coin_frame, text=f"💰 Your Coins: {self.preview_player.coins}", 
                    font=("Arial", 16, "bold"), bg="#2a2a2a", fg="gold").pack()
        
        update_coins()
        
        # Scrollable shop items
        canvas = tk.Canvas(shop_win, bg="#1a1a1a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(shop_win, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1a1a1a")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Display shop items by rarity
        for rarity in ['Common', 'Uncommon', 'Rare', 'Epic', 'Legendary']:
            rarity_items = [item for item in SHOP_ITEMS if item.rarity == rarity]
            if not rarity_items:
                continue
            
            # Rarity header
            rarity_label = tk.Label(scrollable_frame, text=f"━━━ {rarity} ━━━",
                                   font=("Arial", 14, "bold"),
                                   bg="#1a1a1a", fg=InventoryItem.RARITY_COLORS[rarity])
            rarity_label.pack(pady=(15, 5))
            
            for item in rarity_items:
                item_frame = tk.Frame(scrollable_frame, bg="#2a2a2a", bd=2, relief="groove")
                item_frame.pack(fill='x', pady=5, padx=10)
                
                # Item info
                info_frame = tk.Frame(item_frame, bg="#2a2a2a")
                info_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)
                
                name_label = tk.Label(info_frame, text=item.name,
                                     font=("Arial", 13, "bold"),
                                     bg="#2a2a2a", fg=item.get_color())
                name_label.pack(anchor='w')
                
                desc_label = tk.Label(info_frame, text=item.get_description(),
                                     font=("Arial", 10), bg="#2a2a2a", fg="white",
                                     justify='left')
                desc_label.pack(anchor='w', pady=2)
                
                # Buy button
                def make_buy_callback(shop_item):
                    def callback():
                        if self.preview_player.coins >= shop_item.price:
                            self.preview_player.coins -= shop_item.price
                            # Create new item instance (not soulbound)
                            new_item = InventoryItem(
                                name=shop_item.name,
                                item_type=shop_item.item_type,
                                rarity=shop_item.rarity,
                                stats=shop_item.stats.copy(),
                                skills=shop_item.skills.copy(),
                                soulbound=False,
                                price=shop_item.price,
                                weapon_type=getattr(shop_item, 'weapon_type', None)  # ADD THIS LINE
                            )
                            self.preview_player.add_item_to_inventory(new_item)
                            update_coins()
                            self.save_player(self.preview_player.to_dict())
                        else:
                            import tkinter.messagebox as mb
                            mb.showwarning("Not Enough Coins", 
                                          f"You need {shop_item.price} coins but only have {self.preview_player.coins}")
                    return callback
                
                buy_btn = tk.Button(item_frame, text=f"Buy\n{item.price} 💰",
                                   bg='#5cb85c', fg='white',
                                   font=("Arial", 11, "bold"),
                                   command=make_buy_callback(item),
                                   width=8)
                buy_btn.pack(side='right', padx=10, pady=10)
    def build_home(self):
        for w in self.home_frame.winfo_children(): w.destroy()
        
        # Header section
        header = tk.Frame(self.home_frame, bg='#1a1a1a', height=80)
        header.pack(fill='x', pady=(0, 20))
        header.pack_propagate(False)
        
        title = tk.Label(header, text="⚔️ DUNGEON LitRPG ⚔️", font=("Arial", 32, "bold"), 
                        bg='#1a1a1a', fg='#ffffff')
        title.pack(pady=20)

        # Character info section
        info_frame = tk.Frame(self.home_frame, bg='#2a2a2a', bd=2, relief='groove')
        info_frame.pack(pady=10, padx=50, fill='x')
        
        name_frame = tk.Frame(info_frame, bg='#2a2a2a')
        name_frame.pack(pady=15)
        
        tk.Label(name_frame, text="Hero Name:", font=("Arial", 14, "bold"), 
                bg='#2a2a2a', fg='#e0e0e0').pack(side='left', padx=(20, 10))
        name_entry = tk.Entry(name_frame, textvariable=self.name_var, font=("Arial", 14),
                             bg='#3a3a3a', fg='white', insertbackground='white', width=25, bd=2)
        name_entry.pack(side='left', padx=10)

        def confirm_name():
            new_name = self.name_var.get().strip()
            if not new_name:
                new_name = "Hero"
                self.name_var.set(new_name)
            if hasattr(self, 'preview_player') and self.preview_player:
                self.preview_player.name = new_name
                self.update_preview()
                self.save_player(self.preview_player.to_dict())

        confirm_btn = tk.Button(name_frame, text="✓ Confirm", font=("Arial", 11, "bold"),
                                bg='#3a6a3a', fg='white', activebackground='#4a8a4a',
                                bd=0, padx=10, pady=4, cursor='hand2',
                                command=confirm_name)
        confirm_btn.pack(side='left', padx=6)
        # Also confirm on Enter key in the name entry
        name_entry.bind('<Return>', lambda e: confirm_name())

        # Class selection area
        if not self.class_chosen:
            class_label = tk.Label(self.home_frame, text="Choose Your Class", 
                                  font=("Arial", 20, "bold"), bg='#1a1a1a', fg='#ffffff')
            class_label.pack(pady=(20, 10))
            
            classes_container = tk.Frame(self.home_frame, bg='#1a1a1a')
            classes_container.pack(pady=10)
            
            # Row 1: Warrior, Mage, Rogue, Cleric
            row1 = tk.Frame(classes_container, bg='#1a1a1a')
            row1.pack(pady=5)
            for cls in ['Warrior', 'Mage', 'Rogue', 'Cleric']:
                self.create_class_button(row1, cls)
            
            # Row 2: Druid, Monk, Ranger
            row2 = tk.Frame(classes_container, bg='#1a1a1a')
            row2.pack(pady=5)
            for cls in ['Druid', 'Monk', 'Ranger']:
                self.create_class_button(row2, cls)

        # Reset button
        reset_btn = tk.Button(self.home_frame, text="🔄 Reset Character", font=("Arial", 12, "bold"),
                             bg='#4a4a4a', fg='white', activebackground='#6a6a6a', 
                             command=self.reset_character, bd=0, padx=20, pady=8,
                             cursor='hand2')
        reset_btn.pack(pady=10)

        # Preview panel
        preview_frame = tk.Frame(self.home_frame, bg='#2d2d2d', bd=3, relief='ridge')
        preview_frame.pack(pady=15, fill='x', padx=40)
        
        preview_title = tk.Label(preview_frame, text="📊 Character Preview", 
                                font=("Arial", 16, "bold"), bg='#2d2d2d', fg='#ffd700')
        preview_title.pack(pady=10)
        
        self.preview_text = tk.Text(preview_frame, height=7, width=80, bg='#1a1a1a', 
                                   fg='white', font=("Courier", 11), bd=0)
        self.preview_text.pack(padx=15, pady=(0, 15))
        self.update_preview()

        # ── SAVE CODE PANEL (always visible — above start button) ────────────
        save_frame = tk.Frame(self.home_frame, bg='#1e1e2e', bd=2, relief='groove')
        save_frame.pack(pady=(10, 4), padx=50, fill='x')

        hdr_row = tk.Frame(save_frame, bg='#1e1e2e')
        hdr_row.pack(fill='x', padx=12, pady=(8, 2))
        tk.Label(hdr_row, text="💾  Save Code", font=("Arial", 13, "bold"),
                 bg='#1e1e2e', fg='#aad4ff').pack(side='left')
        tk.Label(hdr_row,
                 text="Saves ALL progress: stats, items, chest, skills, soulbound & more.",
                 font=("Arial", 8, "italic"), bg='#1e1e2e', fg='#666688').pack(side='left', padx=12)

        # ── Output row: auto-generated code + copy button ─────────────────────
        out_row = tk.Frame(save_frame, bg='#1e1e2e')
        out_row.pack(fill='x', padx=12, pady=2)
        tk.Label(out_row, text="Your code:", font=("Arial", 10),
                 bg='#1e1e2e', fg='#888888', width=10, anchor='w').pack(side='left')

        code_text = tk.Text(out_row, font=("Courier", 8), height=2,
                            bg='#0a0a1a', fg='#00ff88', insertbackground='white',
                            bd=1, relief='sunken', wrap='word', state='disabled')
        code_text.pack(side='left', fill='x', expand=True, padx=6)
        self._save_code_text = code_text   # kept so save_player() can auto-refresh it

        # Generate initial code
        try:
            initial_code = self.generate_save_code(self.preview_player.to_dict())
        except Exception:
            initial_code = "(no save yet)"
        code_text.config(state='normal')
        code_text.insert(tk.END, initial_code)
        code_text.config(state='disabled')

        def copy_code():
            try:
                c = code_text.get('1.0', tk.END).strip()
                self.clipboard_clear()
                self.clipboard_append(c)
                copy_btn.config(text="✅ Copied!", bg='#2a6a2a')
                self.after(1500, lambda: copy_btn.config(text="📋 Copy", bg='#2a5a2a'))
            except Exception:
                pass

        copy_btn = tk.Button(out_row, text="📋 Copy", font=("Arial", 9, "bold"),
                             bg='#2a5a2a', fg='white', activebackground='#3a7a3a',
                             bd=0, padx=8, pady=3, cursor='hand2', command=copy_code)
        copy_btn.pack(side='left', padx=4)

        def refresh_code():
            try:
                c = self.generate_save_code(self.preview_player.to_dict())
                code_text.config(state='normal')
                code_text.delete('1.0', tk.END)
                code_text.insert(tk.END, c)
                code_text.config(state='disabled')
            except Exception:
                pass

        tk.Button(out_row, text="⟳", font=("Arial", 9, "bold"),
                  bg='#3a3a3a', fg='white', activebackground='#555555',
                  bd=0, padx=6, pady=3, cursor='hand2',
                  command=refresh_code).pack(side='left', padx=2)

        tk.Frame(save_frame, bg='#333355', height=1).pack(fill='x', padx=12, pady=4)

        # ── Input row: paste code + load button ───────────────────────────────
        in_row = tk.Frame(save_frame, bg='#1e1e2e')
        in_row.pack(fill='x', padx=12, pady=(2, 8))
        tk.Label(in_row, text="Load code:", font=("Arial", 10),
                 bg='#1e1e2e', fg='#888888', width=10, anchor='w').pack(side='left')

        load_var = tk.StringVar()
        load_entry = tk.Entry(in_row, textvariable=load_var, font=("Courier", 9),
                              bg='#0a0a1a', fg='#ffdd88', insertbackground='white',
                              width=52, bd=1)
        load_entry.pack(side='left', padx=6, fill='x', expand=True)

        status_lbl = tk.Label(save_frame, text="", font=("Arial", 9, "italic"),
                              bg='#1e1e2e', fg='#aaffaa')
        status_lbl.pack(pady=(0, 4))

        def load_code():
            ok, msg = self.load_from_code(load_var.get())
            if ok:
                # build_home was already called inside load_from_code, so just flash
                pass
            else:
                status_lbl.config(text=f"❌ {msg}", fg='#ff6666')

        load_entry.bind('<Return>', lambda e: load_code())
        tk.Button(in_row, text="⬆ Load", font=("Arial", 9, "bold"),
                  bg='#2a2a6a', fg='white', activebackground='#3a3a8a',
                  bd=0, padx=10, pady=3, cursor='hand2',
                  command=load_code).pack(side='left', padx=4)

        # START GAME BUTTON (replaces dungeon selection)
        if self.class_chosen:
            start_btn = tk.Button(self.home_frame, text="🏰 START GAME", 
                                font=("Arial", 20, "bold"),
                                bg='#555555', fg='white', 
                                activebackground='#777777',
                                command=self.start_game,
                                bd=0, padx=40, pady=20, cursor='hand2')
            start_btn.pack(pady=(4, 16), side='bottom')
        
    def create_class_button(self, parent, class_name):
        info = self.CLASS_INFO[class_name]

        # Outer frame acts as the colored outline
        outline = tk.Frame(parent, bg=info['color'], bd=0)
        outline.pack(side='left', padx=10, pady=40)

        # Inner frame is the button background
        btn_frame = tk.Frame(outline, bg='#2d2d2d', bd=2, relief='solid',
                             width=180, height=120)   # fixed width & height
        btn_frame.pack(padx=2, pady=2)
        btn_frame.pack_propagate(False)  # prevent auto-resizing

        # Emoji + Class name (large font)
        title_label = tk.Label(btn_frame,
                               text=f"{info['emoji']} {class_name}",
                               font=("Arial", 17, "bold"),
                               bg='#2d2d2d', fg=info['color'])
        title_label.pack(pady=(5, 2))

        # Description (smaller font)
        desc_label = tk.Label(btn_frame,
                              text=info['desc'],
                              font=("Arial", 8),
                              bg='#2d2d2d', fg=info['color'],
                              justify='center', wraplength=160)
        desc_label.pack(pady=(0, 5))

        # Make the whole frame clickable
        def on_click(event=None):
            self.choose_class(class_name)

        btn_frame.bind("<Button-1>", on_click)
        title_label.bind("<Button-1>", on_click)
        desc_label.bind("<Button-1>", on_click)


    def choose_class(self, cls):
        self.selected_class = cls
        self.class_chosen = True  # mark that class has been chosen
        self.preview_player = Player(self.name_var.get(), cls)
        self.preview_player.unlock_skills()
        self.update_preview()
        # hide buttons
        # Rebuild home to hide class selection buttons
        self.build_home()

    def update_preview(self):
        p = self.preview_player
        lines = [
            f"Name: {p.name}",
            f"Class: {p.class_name}",
            f"Level: {p.level}  XP: {p.xp}/{p.xp_to_next}",
            f"HP: {p.max_hp}   Mana: {p.max_mana}",
            f"STR:{p.strength}  VIT:{p.vitality}  AGI:{p.agility}  CON:{p.constitution}  INT:{p.intelligence}  WIS:{p.wisdom}  WIL:{p.will}",
            "Unlocked Skills: " + (", ".join(sk['name'] for sk in p.unlocked_skills) if p.unlocked_skills else "(none)")
        ]
        self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert(tk.END, "\n".join(lines))

    def quit_to_menu(self):
        if self.game_frame_container:
            player = self.game_frame_container.player
            # Persist hotbar onto the player object so to_dict() captures it
            player.hotbar_items = list(self.game_frame_container.hotbar_items)
            self.save_player(player.to_dict())
            self.preview_player = player  # update preview with last played player
            self.game_frame_container.destroy()
            self.game_frame_container = None

        # Restore to normal home-screen size
        try:
            self.state('normal')
        except Exception:
            pass
        self.resizable(False, False)
        self.geometry("1000x800")
        self.home_frame.pack(fill='both', expand=True)
        self.build_home()
    def start_game(self):
        try:
            # Rebuild player from preview
            player = Player.from_dict(self.preview_player.to_dict())
            player.hp = player.max_hp
            player.mana = player.max_mana

            # Hide home frame
            self.home_frame.pack_forget()

            # Destroy any existing game frame
            if self.game_frame_container:
                self.game_frame_container.destroy()

            # Make root window fully black so no white slivers appear anywhere
            self.configure(bg='black')

            # Maximize the window so the map panel expands to fill all available space
            self.resizable(True, True)
            try:
                self.state('zoomed')          # Windows / some Linux WMs
            except Exception:
                try:
                    self.attributes('-zoomed', True)   # Linux GTK fallback
                except Exception:
                    self.geometry("1600x900")  # macOS / unsupported WM fallback

            # Create and pack the new game frame (dungeon_id=0 means Town)
            self.game_frame_container = GameFrame(
                self,
                player,
                on_quit_to_menu=self.quit_to_menu,
                dungeon_id=0  # 0 = Town
            )
            self.game_frame_container.pack(fill='both', expand=True)

            print("Started game in town successfully.")

        except Exception as e:
            print(f"Error starting game: {e}")
    def save_player(self, data):
        try:
            with open(self.SAVE_FILE, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print("Error saving player:", e)
        # Refresh the displayed save code if the widget exists
        try:
            if hasattr(self, '_save_code_text') and self._save_code_text.winfo_exists():
                code = self.generate_save_code(data)
                self._save_code_text.config(state='normal')
                self._save_code_text.delete('1.0', tk.END)
                self._save_code_text.insert(tk.END, code)
                self._save_code_text.config(state='disabled')
        except Exception:
            pass

    def generate_save_code(self, data=None):
        """Encode all player data as a compact base64 string."""
        import base64, zlib
        if data is None:
            data = self.preview_player.to_dict()
        raw = json.dumps(data, separators=(',', ':')).encode('utf-8')
        compressed = zlib.compress(raw, level=9)
        code = base64.urlsafe_b64encode(compressed).decode('ascii')
        return code

    def load_from_code(self, code):
        """Decode a save code back into player data and load it."""
        import base64, zlib
        code = code.strip()
        if not code:
            return False, "Empty code."
        try:
            compressed = base64.urlsafe_b64decode(code + '==')
            raw = zlib.decompress(compressed)
            data = json.loads(raw.decode('utf-8'))
            if 'name' not in data or 'class_name' not in data:
                return False, "Invalid save code (missing fields)."
            player = Player.from_dict(data)
            self.preview_player = player
            self.name_var.set(player.name)
            self.selected_class = player.class_name
            self.class_chosen = True
            self.save_player(data)
            self.update_preview()
            self.build_home()
            return True, "Save loaded successfully!"
        except Exception as e:
            return False, f"Failed to decode code: {e}"

    def load_player(self):
        if os.path.exists(self.SAVE_FILE):
            try:
                with open(self.SAVE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print("Error loading player:", e)
        return None

if __name__=="__main__":
    app = MainApp()
    app.mainloop()
