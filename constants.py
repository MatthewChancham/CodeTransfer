import os
import json
import random
import math
import time
import ctypes

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
# Town centre and oval forest dimensions — used in both layout and draw()
TOWN_CX = (TOWN_X_START + TOWN_X_END) // 2   # 700
TOWN_CY = (TOWN_Y_START + TOWN_Y_END) // 2   # 550
OVAL_A  = 720   # horizontal semi-axis — forest ring comfortably beyond all buildings
OVAL_B  = 600   # vertical semi-axis
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
    # ══════════════════════════════════════════════════════════════════════════
    # WARRIOR  —  Strike → Ground Pound → 3 branches
    #   Branch 1 (left):   Strike Projection → Lunge
    #   Branch 2 (right):  Rage → Lingering Aura of Valour
    #   Branch 3 (extra):  Kinetic Shell  (standalone tier 3)
    # ══════════════════════════════════════════════════════════════════════════
    'Warrior': [
        {'name': 'Strikes',                 'tier': 1, 'prereq': [],               'cost': 0, 'type': 'active',  'desc': 'Quick weapon strike at the nearest enemy.',                                                                                                      'branch': 'center', 'passive': None},
        {'name': 'Ground Pound',            'tier': 2, 'prereq': ['Strikes'],      'cost': 1, 'type': 'active',  'desc': 'Slam the ground — AoE damage + knockback to all nearby foes.',                                                                                   'branch': 'center', 'passive': None},
        # Branch 1
        {'name': 'Strike Projection',       'tier': 3, 'prereq': ['Ground Pound'], 'cost': 3, 'type': 'active',  'desc': 'A powerful forward fist blast dealing heavy damage.',                                                                                             'branch': 'left',   'passive': None},
        {'name': 'Lunge',                   'tier': 4, 'prereq': ['Strike Projection'], 'cost': 2, 'type': 'active',  'desc': 'Lunge forward toward the cursor, slashing all enemies in the path for STR×3 damage. Leaves a fading red trail. CD: 1.5s.',                 'branch': 'left',   'passive': None},
        # Branch 2
        {'name': 'Rage',                    'tier': 3, 'prereq': ['Ground Pound'], 'cost': 1, 'type': 'active',  'desc': 'Enter a berserker rage: AGI×2, STR×5 for 10s. Afterwards suffer Fatigue: AGI −50% for 10s. CD: 40s.',                                           'branch': 'right',  'passive': None},
        {'name': 'Lingering Aura of Valour','tier': 4, 'prereq': ['Rage'],         'cost': 3, 'type': 'active',  'desc': 'Radiate a damaging aura that also blocks enemy projectiles.',                                                                                     'branch': 'right',  'passive': None},
        # Branch 3
        {'name': 'Kinetic Shell',           'tier': 3, 'prereq': ['Ground Pound'], 'cost': 2, 'type': 'passive', 'desc': 'PASSIVE: Gain an energy shield equal to Vitality×5. Taking damage restores Mana equal to half the damage absorbed.',                              'branch': 'extra',  'passive': None},
    ],
    # ══════════════════════════════════════════════════════════════════════════
    # MAGE  —  unchanged
    # ══════════════════════════════════════════════════════════════════════════
    'Mage': [
        {'name': 'Mana Bolt',               'tier': 1, 'prereq': [],                    'cost': 0, 'type': 'active',  'desc': 'A fast mana projectile at the nearest enemy.',                                                                                              'branch': 'center', 'passive': None},
        {'name': 'Firebolt',               'tier': 2, 'prereq': ['Mana Bolt'],         'cost': 2, 'type': 'active',  'desc': 'A bolt of condensed flame particles. Faster than Fireball, smaller AoE on hit.',                                                              'branch': 'left',   'passive': None},
        {'name': 'Icebolt',                'tier': 2, 'prereq': ['Mana Bolt'],         'cost': 2, 'type': 'active',  'desc': 'A bolt of swirling frost particles. Chills on hit, slowing the enemy briefly.',                                                               'branch': 'center', 'passive': None},
        {'name': 'Aqua Missile',           'tier': 2, 'prereq': ['Mana Bolt'],         'cost': 0, 'type': 'active',  'desc': 'Launch a spiralling stream of water droplets that homes slightly toward the nearest enemy. Applies Wet on hit.',                              'branch': 'far_right',  'passive': None},
        {'name': 'Mana Barrier',            'tier': 2, 'prereq': ['Mana Bolt'],         'cost': 0, 'type': 'active',  'desc': 'Summon a mana shield near your cursor (max range). Drains mana. Rotates with cursor. Blocks projectiles and stops enemies.',               'branch': 'right',  'passive': None},
        {'name': 'Fireball',                'tier': 3, 'prereq': ['Mana Barrier'],      'cost': 4, 'type': 'active',  'desc': 'Explosive fireball — deals AoE fire damage on impact.',                                                                                     'branch': 'left',   'passive': None},
        {'name': 'Fire Breath',             'tier': 4, 'prereq': ['Fireball'],          'cost': 1, 'type': 'active',  'desc': 'Channel dragon fire for 5s — streams flames toward cursor. Drains mana/s.',                                                                 'branch': 'left',   'passive': None},
        {'name': 'Icicle',                  'tier': 3, 'prereq': ['Mana Barrier'],      'cost': 4, 'type': 'active',  'desc': 'Ice spike that shatters on impact with frost AoE.',                                                                                         'branch': 'center', 'passive': None},
        {'name': 'Ice Breath',              'tier': 4, 'prereq': ['Icicle'],            'cost': 1, 'type': 'active',  'desc': 'Channel frost breath for 5s — streams ice toward cursor. Drains mana/s, freezes enemies.',                                                  'branch': 'center', 'passive': None},
        {'name': 'Mana Bubble',             'tier': 3, 'prereq': ['Mana Barrier'],      'cost': 3, 'type': 'active',  'desc': 'Toggle a mana bubble that repels all nearby enemies and absorbs incoming projectiles. Drains mana per second.',                             'branch': 'right',  'passive': None},
        {'name': 'Mage Armour',             'tier': 4, 'prereq': ['Mana Bubble'],       'cost': 2, 'type': 'passive', 'desc': 'PASSIVE: Manifest a magical shield equal to your Mag×5. Absorbs damage before HP.',                                                         'branch': 'right',  'passive': None},
        {'name': 'Chain Lightning',         'tier': 3, 'prereq': ['Mana Barrier'],      'cost': 4, 'type': 'active',  'desc': 'Lightning bolt that chains between up to 5 enemies. Shocks on hit. Requires Level 10.',                                                     'branch': 'extra',  'passive': None, 'level_req': 10},
        {'name': 'Hydro Shot',              'tier': 3, 'prereq': ['Mana Barrier'],      'cost': 0, 'type': 'active',  'desc': 'Fire a squished water bead at the cursor. On impact: large water burst + puddle. Enemies hit or in puddle gain Wet (−20% speed & damage per tier, +1 tier/s in puddle, lasts 10s+2s/tier). CD: 1.5s.', 'branch': 'far_right', 'passive': None},
        # ── Subclass unlocks (tier 5) ─────────────────────────────────────────
        {'name': 'Pyromancer',              'tier': 5, 'prereq': ['Fire Breath'],       'cost': 5, 'type': 'passive', 'desc': 'SUBCLASS — Pyromancer: Replaces Mana Bolt with Firebolt as your primary skill. Grants the Staff of Flame (soulbound weapon) whose beam skill is Scorching Ray — a sustained fire channel identical to Ignis\'s scorching ray that deals Mag×2/s and scorches all enemies in its path.', 'branch': 'left',      'passive': None},
        {'name': 'Cryomancer',              'tier': 5, 'prereq': ['Ice Breath'],        'cost': 5, 'type': 'passive', 'desc': 'SUBCLASS — Cryomancer: Replaces Mana Bolt with Icebolt as your primary skill. Grants the Staff of Frost (soulbound weapon) whose beam skill is Ray of Frost — a sustained ice channel with frost particles that deals Mag×1.5/s and chills every enemy it touches.', 'branch': 'center',    'passive': None},
    ],
    # ══════════════════════════════════════════════════════════════════════════
    # ROGUE  —  Dark Slash → Shadow Dagger → 3 branches
    #   Branch 1 (left):   Blink → Teleport
    #   Branch 2 (center): Poison Infusion → Blackflame
    #   Branch 3 (right):  Haste → Invisibility
    # ══════════════════════════════════════════════════════════════════════════
    'Rogue': [
        {'name': 'Dark Slash',              'tier': 1, 'prereq': [],                 'cost': 0, 'type': 'active',  'desc': 'A shadowy slice dealing damage to nearby foes.',                                                                                               'branch': 'center', 'passive': None},
        {'name': 'Shadow Dagger',           'tier': 2, 'prereq': ['Dark Slash'],     'cost': 2, 'type': 'active',  'desc': 'Hurl a shadowy dagger at high speed.',                                                                                                        'branch': 'center', 'passive': None},
        # Branch 1
        {'name': 'Blink',                   'tier': 3, 'prereq': ['Shadow Dagger'], 'cost': 4, 'type': 'active',  'desc': 'Teleport a great distance toward the nearest enemy.',                                                                                          'branch': 'left',   'passive': None},
        {'name': 'Teleport',                'tier': 4, 'prereq': ['Blink'],         'cost': 1, 'type': 'active',  'desc': 'Click anywhere to instantly teleport there. Purple particle burst on arrival. CD: 2s. Also granted by Amulet of Teleportation.',              'branch': 'left',   'passive': None},
        # Branch 2
        {'name': 'Poison Infusion',         'tier': 3, 'prereq': ['Shadow Dagger'], 'cost': 1, 'type': 'passive', 'desc': 'PASSIVE: Dark Slash and Shadow Dagger apply poison. Tier 1: 5s, 2% max HP/s. Reapply before expiry → Tier 2: 10s, 3%/s. Reapply again → Tier 3: 15s, 5%/s.', 'branch': 'center', 'passive': None},
        {'name': 'Blackflame',              'tier': 4, 'prereq': ['Poison Infusion'],'cost': 4, 'type': 'active',  'desc': 'Hurl a roiling ball of blackfire — purple/red projectile with dark flame particles. Deals Mag×10 AoE on impact and applies poison to all hit enemies. CD: 1.5s.', 'branch': 'center', 'passive': None},
        # Branch 3
        {'name': 'Haste',                   'tier': 3, 'prereq': ['Shadow Dagger'], 'cost': 2, 'type': 'active',  'desc': 'Enter a blur of speed: AGI×3 for 20s, emitting light-blue wind particles. CD: 40s.',                                                          'branch': 'right',  'passive': None},
        {'name': 'Invisibility',            'tier': 4, 'prereq': ['Haste'],         'cost': 4, 'type': 'active',  'desc': 'All enemies in the room enter a wander state. Breaks if you use any skill or item. CD: 12s. Also granted by Potion of Invisibility (20s).',  'branch': 'right',  'passive': None},
    ],
    # ══════════════════════════════════════════════════════════════════════════
    # CLERIC  —  Light Bolt → Minor Heal → 3 branches
    #   Branch 1 (left):   Light Beam → Summon Range Sentry
    #   Branch 2 (center): Halo of Radiance → Holyflame
    #   Branch 3 (right):  Circle of Life  (standalone tier 3)
    # ══════════════════════════════════════════════════════════════════════════
    'Cleric': [
        {'name': 'Light Bolt',              'tier': 1, 'prereq': [],               'cost': 0, 'type': 'active',  'desc': 'A bolt of focused holy light.',                                                                                                                   'branch': 'center', 'passive': None},
        {'name': 'Minor Heal',              'tier': 2, 'prereq': ['Light Bolt'],   'cost': 3, 'type': 'active',  'desc': 'Restore HP equal to your magic power.',                                                                                                          'branch': 'center', 'passive': None},
        # Branch 1
        {'name': 'Light Beam',              'tier': 3, 'prereq': ['Minor Heal'],   'cost': 2, 'type': 'active',  'desc': 'Summon a rotating beam of holy light for 3 seconds.',                                                                                            'branch': 'left',   'passive': None},
        {'name': 'Summon Range Sentry',     'tier': 4, 'prereq': ['Light Beam'],   'cost': 4, 'type': 'active',  'desc': 'Summon a sentry that orbits around you, firing holy bolts at all enemies.',                                                                      'branch': 'left',   'passive': None},
        # Branch 2
        {'name': 'Halo of Radiance',        'tier': 3, 'prereq': ['Minor Heal'],   'cost': 2, 'type': 'active',  'desc': 'Radiate a glowing yellow halo with rotating god rays. Dazes and deals continuous holy damage to nearby enemies for 4s. CD: 10s.',              'branch': 'center', 'passive': None},
        {'name': 'Holyflame',               'tier': 4, 'prereq': ['Halo of Radiance'], 'cost': 4, 'type': 'active',  'desc': 'Launch a blazing holy fireball — yellow/white projectile with divine flame particles. Deals Mag×10 AoE on impact. CD: 1.5s.',             'branch': 'center', 'passive': None},
        # Branch 3
        {'name': 'Circle of Life',          'tier': 3, 'prereq': ['Minor Heal'],   'cost': 3, 'type': 'active',  'desc': 'Place a circle of life at the cursor. Green particles drift upward; all players inside are gradually healed over 5s. CD: 12s.',               'branch': 'right',  'passive': None},
    ],
    # ══════════════════════════════════════════════════════════════════════════
    # DRUID  —  Thorn Whip → Summon Wolf → 3 branches
    #   Branch 1 (left):  Leaf Shot → Lashing Vines → Entangling Roots → Grasping Vines
    #   Branch 2 (extra): Barkskin  (standalone tier 3)
    #   Branch 3 (right): Wild Shape  (standalone tier 3)
    # ══════════════════════════════════════════════════════════════════════════
    'Druid': [
        # ── Tier 1 ──────────────────────────────────────────────────────────────
        {'name': 'Thorn Whip',              'tier': 1, 'prereq': [],               'cost': 0, 'type': 'active',  'desc': 'Lash nearby enemies with a thorny vine.',                                                                                                        'branch': 'center', 'passive': None},
        # ── Tier 2 ──────────────────────────────────────────────────────────────
        {'name': 'Summon Wolf',             'tier': 2, 'prereq': ['Thorn Whip'],   'cost': 2, 'type': 'active',  'desc': 'Summon a loyal wolf that attacks enemies for you.',                                                                                              'branch': 'center', 'passive': None},
        # ── Tier 3 — three independent branches ─────────────────────────────────
        {'name': 'Leaf Shot',               'tier': 3, 'prereq': ['Summon Wolf'],  'cost': 1, 'type': 'active',  'desc': 'Fire a barrage of razor-sharp leaves at an enemy.',                                                                                              'branch': 'left',   'passive': None},
        {'name': 'Barkskin',                'tier': 3, 'prereq': ['Summon Wolf'],  'cost': 3, 'type': 'passive', 'desc': 'PASSIVE: Natural armour shield equal to Wisdom×5. Scales with wis.',                                                                             'branch': 'extra',  'passive': None},
        {'name': 'Wild Shape',              'tier': 3, 'prereq': ['Summon Wolf'],  'cost': 2, 'type': 'active',  'desc': 'Transform into a beast, elemental, or monster form. Press 6 to open form selection or exit. New skills replace your hotbar while transformed.','branch': 'right',  'passive': None},
        # ── Tier 4-6 — Leaf Shot chain ──────────────────────────────────────────
        {'name': 'Lashing Vines',           'tier': 4, 'prereq': ['Leaf Shot'],    'cost': 1, 'type': 'active',  'desc': 'Erupt vines in all directions, lashing nearby foes.',                                                                                            'branch': 'left',   'passive': None},
        {'name': 'Entangling Roots',        'tier': 5, 'prereq': ['Lashing Vines'],'cost': 3, 'type': 'active',  'desc': 'Slam roots at target area. Enemies inside are rooted for 4s and take thorn damage.',                                                            'branch': 'left',   'passive': None},
        {'name': 'Grasping Vines',          'tier': 6, 'prereq': ['Entangling Roots'],'cost': 4, 'type': 'active','desc': 'Latch a vine onto the nearest enemy to cursor. Pins it and makes it follow your mouse for 6s.',                                                'branch': 'left',   'passive': None},
    ],
    # ══════════════════════════════════════════════════════════════════════════
    # MONK  —  Chi Strike → Chi Blast → 2 branches
    #   Branch 1 (left):   Chi Propulsion → Flurry of Blows
    #   Branch 2 (right):  Iron Guard  (standalone tier 3)
    # ══════════════════════════════════════════════════════════════════════════
    'Monk': [
        {'name': 'Chi Strike',              'tier': 1, 'prereq': [],               'cost': 0, 'type': 'active',  'desc': 'Unleash a quick chi-powered slice at the enemy.',                                                                                               'branch': 'center', 'passive': None},
        {'name': 'Chi Blast',               'tier': 2, 'prereq': ['Chi Strike'],   'cost': 5, 'type': 'active',  'desc': 'Blast chi energy forward in a focused burst.',                                                                                                  'branch': 'center', 'passive': None},
        # Branch 1
        {'name': 'Chi Propulsion',          'tier': 3, 'prereq': ['Chi Blast'],    'cost': 3, 'type': 'active',  'desc': 'Propel forward in the direction you are aiming with a surge of cyan chi energy. CD: 0.7s.',                                                    'branch': 'left',   'passive': None},
        {'name': 'Flurry of Blows',         'tier': 4, 'prereq': ['Chi Propulsion'],'cost': 5, 'type': 'active', 'desc': 'Summon 8 chi strikes simultaneously at fixed offsets around you. CD: 1.5s.',                                                                   'branch': 'left',   'passive': None},
        # Branch 2
        {'name': 'Iron Guard',              'tier': 3, 'prereq': ['Chi Blast'],    'cost': 7, 'type': 'active',  'desc': 'Toggle a buff that multiplies Constitution by 10 while rapidly draining HP. Same toggle mechanics as Mana Bubble.',                            'branch': 'right',  'passive': None},
    ],
    # ══════════════════════════════════════════════════════════════════════════
    # RANGER  —  Arrow Shot → Multishot → 2 branches
    #   Branch 1 (left):  Fire Trap → Frost Trap
    #   Branch 2 (right): Eagle Eye: Auto-Aim  (standalone tier 3)
    # ══════════════════════════════════════════════════════════════════════════
    'Ranger': [
        {'name': 'Arrow Shot',              'tier': 1, 'prereq': [],               'cost': 0, 'type': 'active',  'desc': 'Fire a swift arrow at the nearest enemy.',                                                                                                      'branch': 'center', 'passive': None},
        {'name': 'Multishot',               'tier': 2, 'prereq': ['Arrow Shot'],   'cost': 5, 'type': 'active',  'desc': 'Fire arrows at up to 3 enemies simultaneously.',                                                                                               'branch': 'center', 'passive': None},
        # Branch 1
        {'name': 'Fire Trap',               'tier': 3, 'prereq': ['Multishot'],    'cost': 3, 'type': 'active',  'desc': 'Place a fire trap that ignites enemies on contact.',                                                                                            'branch': 'left',   'passive': None},
        {'name': 'Frost Trap',              'tier': 4, 'prereq': ['Fire Trap'],    'cost': 3, 'type': 'active',  'desc': 'Place a frost trap that freezes and slows enemies.',                                                                                            'branch': 'left',   'passive': None},
        # Branch 2
        {'name': 'Eagle Eye: Auto-Aim',     'tier': 3, 'prereq': ['Multishot'],    'cost': 1, 'type': 'passive', 'desc': 'PASSIVE TOGGLE: All shots automatically lock onto the nearest enemy instead of following the mouse.',                                           'branch': 'right',  'passive': None},
    ],
}

# ---------- Wild Shape Forms ----------
# Each form: name, category, icon, stat_bonuses (applied while transformed),
#            wisdom_scaling (stat set to wisdom value), desc, skills (list of skill dicts)
WILD_SHAPE_FORMS = [
    # ── Beast Forms ─────────────────────────────────────────────────────────
    {
        'name': 'Eagle',       'category': 'Beast',
        'icon': '🦅', 'color': '#c8a832',
        'cd': 10,
        'stat_scaling': ['agility', 'intelligence'],   # set to wisdom value
        'desc': 'Soar as an eagle. Agility and Intelligence equal Wisdom. Swift dive attacks.',
        'form_skills': [
            {'name': 'Dive',          'cooldown': 2.0,  'desc': 'Dash forward dealing Wis damage.'},
            {'name': 'Talon Strike',  'cooldown': 0.5,  'desc': 'Rapid claw hit (Wis×2 dmg).'},
            {'name': 'Eagle Screech', 'cooldown': 8.0,  'desc': 'Stun all nearby enemies for 1.5s.'},
        ],
    },
    {
        'name': 'Leopard',     'category': 'Beast',
        'icon': '🐆', 'color': '#d4a020',
        'cd': 10,
        'stat_scaling': ['agility'],
        'stat_bonus': {'strength': 'wisdom'},          # strength = wisdom
        'desc': 'Become a leopard. Strength and Agility equal Wisdom. Pounce on prey.',
        'form_skills': [
            {'name': 'Pounce',        'cooldown': 1.5,  'desc': 'Leap at nearest enemy (Wis×3 dmg).'},
            {'name': 'Claw Swipe',    'cooldown': 0.4,  'desc': 'Quick melee (Wis×1.5 dmg).'},
            {'name': 'Feral Roar',    'cooldown': 10.0, 'desc': 'Reduce nearby enemy ATK by 50% for 4s.'},
        ],
    },
    {
        'name': 'Unicorn',     'category': 'Beast',
        'icon': '🦄', 'color': '#e070e0',
        'cd': 10,
        'stat_scaling': ['vitality', 'will'],
        'desc': 'Channel the unicorn. Vitality and Willpower equal Wisdom. Healing light.',
        'form_skills': [
            {'name': 'Horn Charge',   'cooldown': 2.0,  'desc': 'Charge forward, impaling foes (Wis×4).'},
            {'name': 'Healing Light', 'cooldown': 5.0,  'desc': 'Restore HP equal to Wis×3.'},
            {'name': 'Purifying Aura','cooldown': 12.0, 'desc': 'Heal self fully over 3s.'},
        ],
    },
    {
        'name': 'Turtle',      'category': 'Beast',
        'icon': '🐢', 'color': '#4a9a4a',
        'cd': 10,
        'stat_scaling': ['constitution'],
        'desc': 'Become a turtle. Constitution equals Wisdom. Near-impenetrable shell.',
        'form_skills': [
            {'name': 'Shell Bash',    'cooldown': 1.0,  'desc': 'Melee slam (Wis×2 dmg + knockback).'},
            {'name': 'Withdraw',      'cooldown': 8.0,  'desc': 'Reduce incoming damage by 80% for 3s.'},
            {'name': 'Tail Sweep',    'cooldown': 3.0,  'desc': 'AoE spin (Wis dmg to all nearby).'},
        ],
    },
    # ── Elemental Forms ──────────────────────────────────────────────────────
    {
        'name': 'Fire Elemental', 'category': 'Elemental',
        'icon': '🔥', 'color': '#ff6020',
        'cd': 15,
        'stat_scaling': ['intelligence', 'will'],
        'desc': 'Ignite as a Fire Elemental. Grants Fireball and fire skills.',
        'form_skills': [
            {'name': 'Fireball',      'cooldown': 1.0,  'desc': 'Explosive fire projectile (Mag×8 dmg).', 'proxy': 'fireball'},
            {'name': 'Fire Burst',    'cooldown': 3.0,  'desc': 'AoE fire explosion around you.'},
            {'name': 'Immolate',      'cooldown': 10.0, 'desc': 'Ignite all nearby enemies for 5s.'},
        ],
    },
    {
        'name': 'Earth Elemental', 'category': 'Elemental',
        'icon': '🪨', 'color': '#8b6030',
        'cd': 15,
        'stat_scaling': ['constitution', 'vitality'],
        'desc': 'Become stone. High defence. Hurl boulders and shake the earth.',
        'form_skills': [
            {'name': 'Rock Throw',    'cooldown': 0.8,  'desc': 'Heavy rock projectile (Wis×3 dmg).'},
            {'name': 'Earthquake',    'cooldown': 5.0,  'desc': 'Stun + dmg all enemies in large radius.'},
            {'name': 'Stone Skin',    'cooldown': 12.0, 'desc': 'Temporary 90% damage reduction for 2s.'},
        ],
    },
    {
        'name': 'Storm Elemental', 'category': 'Elemental',
        'icon': '⚡', 'color': '#80b0ff',
        'cd': 15,
        'stat_scaling': ['agility', 'intelligence'],
        'desc': 'Become the storm. Grants Lightning Bolt with shock effect.',
        'form_skills': [
            {'name': 'Lightning Bolt','cooldown': 0.8,  'desc': 'Piercing lightning (Mag×5 + shock).', 'proxy': 'lightning_bolt'},
            {'name': 'Thunderclap',   'cooldown': 4.0,  'desc': 'AoE shock burst around you.'},
            {'name': 'Storm Surge',   'cooldown': 10.0, 'desc': 'Teleport to cursor position in a bolt of lightning.'},
        ],
    },
    {
        'name': 'Water Elemental', 'category': 'Elemental',
        'icon': '💧', 'color': '#30a0e0',
        'cd': 15,
        'stat_scaling': ['wisdom', 'vitality'],
        'desc': 'Flow as water. Healing waves and tidal force.',
        'form_skills': [
            {'name': 'Water Wave',    'cooldown': 1.0,  'desc': 'Push + damage enemies in a line.'},
            {'name': 'Tidal Surge',   'cooldown': 5.0,  'desc': 'AoE knockback + Wis×2 damage.'},
            {'name': 'Healing Tide',  'cooldown': 10.0, 'desc': 'Restore Wis×5 HP.'},
        ],
    },
    {
        'name': 'Ice Elemental', 'category': 'Elemental',
        'icon': '❄️', 'color': '#88eeff',
        'cd': 15,
        'stat_scaling': ['intelligence', 'constitution'],
        'desc': 'Freeze the battlefield. Grants Icicle and freezing skills.',
        'form_skills': [
            {'name': 'Icicle',        'cooldown': 0.8,  'desc': 'Ice spike that freezes on hit.', 'proxy': 'icicle'},
            {'name': 'Blizzard',      'cooldown': 5.0,  'desc': 'AoE frost burst — freeze all nearby foes.'},
            {'name': 'Ice Armour',    'cooldown': 10.0, 'desc': 'Gain a shield equal to Wis×8.'},
        ],
    },
    # ── Monster Forms ────────────────────────────────────────────────────────
    {
        'name': 'Dragon',      'category': 'Monster',
        'icon': '🐉', 'color': '#c03030',
        'cd': 20,
        'stat_scaling': ['strength', 'vitality', 'constitution'],
        'desc': 'The mightiest form. All offensive stats equal Wisdom. Fire breath and claw.',
        'form_skills': [
            {'name': 'Dragon Claw',   'cooldown': 0.4,  'desc': 'Devastating melee (Wis×6 dmg).'},
            {'name': 'Dragon Fire',   'cooldown': 2.0,  'desc': 'Wide cone of dragonfire.'},
            {'name': 'Dragon Roar',   'cooldown': 8.0,  'desc': 'Fear all enemies — they flee for 4s.'},
            {'name': 'Wing Buffet',   'cooldown': 5.0,  'desc': 'AoE knockback in all directions.'},
        ],
    },
    {
        'name': 'Hydra',       'category': 'Monster',
        'icon': '🐍', 'color': '#206050',
        'cd': 20,
        'stat_scaling': ['strength', 'agility'],
        'desc': 'Multi-headed hydra. Many bites, venom, and regen.',
        'form_skills': [
            {'name': 'Hydra Bite',    'cooldown': 0.3,  'desc': 'Rapid bite (x3 hits, Wis dmg each).'},
            {'name': 'Venom Spray',   'cooldown': 3.0,  'desc': 'Poison all nearby enemies for 6s.'},
            {'name': 'Regenerate',    'cooldown': 12.0, 'desc': 'Rapidly heal Wis×10 HP over 3s.'},
            {'name': 'Tail Lash',     'cooldown': 2.0,  'desc': 'Knockback + stun nearest enemy.'},
        ],
    },
]

# ---------- General Skill Tree (class-independent) ----------
GENERAL_SKILL_TREE = [
    # ── Left branch: Identify / Analysis ────────────────────────────────────
    {'name': 'Identify',            'tier': 1, 'prereq': [],                        'cost': 1, 'type': 'passive', 'desc': 'PASSIVE: Reveal enemy HP bars and status effects.',                                                                                   'branch': 'left',    'passive': None},
    {'name': 'Analysis',            'tier': 2, 'prereq': ['Identify'],              'cost': 1, 'type': 'active',  'desc': 'ACTIVE [E]: Inspect the nearest enemy to reveal its name and full skill list.',                                                        'branch': 'left',    'passive': None},
    # ── Center-left branch: Keen Mind / Master of Skills ────────────────────
    {'name': 'Keen Mind',           'tier': 1, 'prereq': [],                        'cost': 2, 'type': 'passive', 'desc': 'PASSIVE: Unlocks a second skill page (slots 6-10). Press 6 in-game to switch between pages.',                                         'branch': 'center',  'passive': None},
    {'name': 'Cognitive Expansion', 'tier': 2, 'prereq': ['Keen Mind'],             'cost': 2, 'type': 'passive', 'desc': 'PASSIVE: Unlocks a third skill page (slots 11-15). Press 6 to cycle through all three pages.',                                         'branch': 'center',  'passive': None},
    {'name': 'Master of Skills',    'tier': 3, 'prereq': ['Cognitive Expansion'],   'cost': 8, 'type': 'passive', 'desc': 'PASSIVE: Unlocks a fourth skill page (slots 16-20). Press 6 to cycle through all four pages.',    'branch': 'center',  'passive': None},
    # ── Center-right branch: Magnetic Field ─────────────────────────────────
    {'name': 'Magnetic Field I',    'tier': 1, 'prereq': [],                        'cost': 1, 'type': 'passive', 'desc': 'PASSIVE: Coins and dropped items within 250 px are pulled toward you.',          'branch': 'extra',   'passive': None},
    {'name': 'Magnetic Field II',   'tier': 2, 'prereq': ['Magnetic Field I'],      'cost': 1, 'type': 'passive', 'desc': 'PASSIVE: Increases pull radius to 600 px.',                                      'branch': 'extra',   'passive': None},
    {'name': 'Magnetic Field III',  'tier': 3, 'prereq': ['Magnetic Field II'],     'cost': 2, 'type': 'passive', 'desc': 'PASSIVE: Increases pull radius to 1100 px — pulls from off-screen.',             'branch': 'extra',   'passive': None},
    # ── Right branch: Utility ────────────────────────────────────────────────
    {'name': 'Virtual Map',         'tier': 1, 'prereq': [],                        'cost': 1, 'type': 'passive', 'desc': 'PASSIVE: Enables the dungeon minimap overlay. Reveals rooms you have visited.',                                                        'branch': 'right',   'passive': None},
    # ── Far-right branch: Quick Learner ─────────────────────────────────────
    {'name': 'Quick Learner I',     'tier': 1, 'prereq': [],                        'cost': 2, 'type': 'passive', 'desc': 'PASSIVE: All skill cooldowns reduced by 5%. You also move 5% faster.',                                                                  'branch': 'far_right', 'passive': None},
    {'name': 'Quick Learner II',    'tier': 2, 'prereq': ['Quick Learner I'],        'cost': 3, 'type': 'passive', 'desc': 'PASSIVE: All skill cooldowns reduced by an additional 8%. Move speed +8%.',                                                             'branch': 'far_right', 'passive': None},
    {'name': 'Quick Learner III',   'tier': 3, 'prereq': ['Quick Learner II'],       'cost': 4, 'type': 'passive', 'desc': 'PASSIVE: All skill cooldowns reduced by an additional 12%. Move speed +12%.',                                                           'branch': 'far_right', 'passive': None},
    {'name': 'Quick Learner IV',    'tier': 4, 'prereq': ['Quick Learner III'],      'cost': 5, 'type': 'passive', 'desc': 'PASSIVE: All skill cooldowns reduced by an additional 15%. Move speed +15%. Your base cooldown reduction per cast increases to 0.1%.',   'branch': 'far_right', 'passive': None},
]

# ---------- Utilities ----------
def clamp(v,a,b): return max(a,min(b,v))
def distance(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def check_collision(x, y, size, decorations):
    """Check if position collides with any decoration that has collision"""
    for deco in decorations:
        if not deco.get('has_collision'):
            continue
        if deco.get('type') == 'forest_wall':
            continue   # oval boundary handled separately in update_player
        dx = x - deco['x']
        dy = y - deco['y']
        dist = math.hypot(dx, dy)
        if dist < size + deco.get('size', 20):
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
