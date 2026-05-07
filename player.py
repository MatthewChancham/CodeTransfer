import json
import random
import math
import time
from constants import *
from utils import clamp, distance
from items import InventoryItem, ConsumableItem, Item

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
        self.stat_points=5; self.skill_points=1; self.gen_skill_points=1
        self.skills=[]; self.unlocked_skills=[]
        self.tree_unlocked = set()   # skill names manually unlocked via skill tree
        self.passive_toggles = {}    # passive name -> True/False (on/off)
        self.skill_page = 1          # active hotbar page (1=slots1-5, 2=slots6-10, 3=slots11-15)
        
        # NEW: Inventory system - MUST BE BEFORE update_stats()
        self.coins = 50
        self.inventory = []
        self.equipped_items = []
        self.soulbound_items = []
        self.last_soulbound_upgrade_level = 0
        self.chest_items = []   # items stored in the house chest
        self.hotbar_items = [None, None, None]   # consumable hotbar (T/Y/U) — persisted on save
        self.weapon_skills = []  # skills granted by equipped weapon (shown in weapon skill bar)
        
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
        # Wild Shape state
        self.wild_shape_form = None
        self._ws_saved_skills = None
        self._ws_stat_bonuses = {}
        # Wild Shape form-slot assignments (slot 1-5 → form name or None)
        self.wild_shape_form_slots = {1: None, 2: None, 3: None, 4: None, 5: None}
        # Form Points — currency to unlock forms and upgrade form skills
        self.form_points = 0
        # Set of form names the player has unlocked
        self.unlocked_forms = set()
        # Per-form skill level: form_name -> int (1 = only first skill, 2 = first two, etc.)
        self.form_skill_levels = {}
        # Armour shield system
        self.shield = 0
        self.max_shield = 0
        self.shield_regen_rate = 2.0
        self.shield_charges = 30       # Stone Shield offhand charges
        self._shield_charge_regen = 0.0  # accumulator for regen
            
    def update_stats(self):
        """Calculate stats including equipment and soulbound item bonuses"""
        # Base stats from character
        self.max_hp = 50 + self.vitality * 10
        if not hasattr(self, 'hp'):
            self.hp = self.max_hp   # first-time initialisation only
        self.max_mana = 20 + self.intelligence * 10
        if not hasattr(self, 'mana'):
            self.mana = self.max_mana   # first-time initialisation only
        self.base_speed = 4.5 + self.agility * 0.05
        self.speed = self.base_speed
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

        # Reset shield to recalculate from armour items
        old_max_shield = getattr(self, 'max_shield', 0)
        self.max_shield = 0

        # Reset item constitution bonus — accumulated fresh each call to prevent stacking
        self._item_con_bonus = 0

        def _apply_stat(stat, value):
            if stat == 'strength':
                self.atk += value
            elif stat == 'vitality':
                bonus_hp = value * 10
                self.max_hp += bonus_hp
                # NOTE: do NOT touch self.hp here — update_stats is called every tick,
                # so adding bonus_hp to hp each call caused instant regeneration.
                # hp is clamped to the final max_hp after all items are processed.
                self.vit += value
                self.hp_regen += value * 0.07
            elif stat == 'agility':
                self.base_speed += value * 0.15
                self.speed = self.base_speed
            elif stat == 'intelligence':
                bonus_mana = value * 10
                self.max_mana += bonus_mana
                # NOTE: do NOT touch self.mana here — same reason as vitality/hp above.
            elif stat == 'wisdom':
                self.wis += value
                self.mana_regen += value * 0.15
            elif stat == 'will':
                self.mag += value
            elif stat == 'constitution':
                # Accumulate item con bonus separately — never modify self.constitution
                # directly here to prevent stacking on repeated update_stats calls
                self._item_con_bonus += value
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

        # (passive stat bonuses are handled by dedicated passive toggles only)

        # ── Quick Learner: cooldown reduction + speed ─────────────────────────
        _tu_ql = getattr(self, 'tree_unlocked', set())
        _ql_cd  = 1.0   # cumulative CD multiplier
        _ql_spd = 0.0   # cumulative speed bonus fraction
        if 'Quick Learner I'   in _tu_ql: _ql_cd -= 0.05; _ql_spd += 0.05
        if 'Quick Learner II'  in _tu_ql: _ql_cd -= 0.08; _ql_spd += 0.08
        if 'Quick Learner III' in _tu_ql: _ql_cd -= 0.12; _ql_spd += 0.12
        if 'Quick Learner IV'  in _tu_ql: _ql_cd -= 0.15; _ql_spd += 0.15
        if _ql_cd < 1.0:
            for sk in getattr(self, 'unlocked_skills', []):
                sk['cooldown_mod'] = min(sk.get('cooldown_mod', 1.0), _ql_cd)
        if _ql_spd > 0:
            self.speed = getattr(self, 'base_speed', self.speed) * (1.0 + _ql_spd)

        # Apply soulbound item bonuses ONLY if they're not already equipped
        for item in self.soulbound_items:
            item_id = id(item)
            if item_id in counted_items:
                continue  # Skip if already counted from equipped_items
            counted_items.add(item_id)
            for stat, value in item.stats.items():
                _apply_stat(stat, value)

        # Clamp hp/mana to final maximums (including all item bonuses).
        # Must happen AFTER all equipped and soulbound items are processed.
        self.hp   = min(self.hp,   self.max_hp)
        self.mana = min(self.mana, self.max_mana)

        # Kinetic Shell passive: add energy shield proportional to vitality (BEFORE clamping)
        kinetic_active = ('Kinetic Shell' in getattr(self, 'tree_unlocked', set())
                          and getattr(self, 'passive_toggles', {}).get('Kinetic Shell', True))
        kinetic_bonus  = (self.vitality * 5) if kinetic_active else 0
        if kinetic_active:
            self.max_shield += kinetic_bonus

        # Mage Armour passive: shield proportional to mag (will-based)
        mage_armour_active = ('Mage Armour' in getattr(self, 'tree_unlocked', set())
                              and getattr(self, 'passive_toggles', {}).get('Mage Armour', True))
        mage_armour_bonus  = (self.mag * 5) if mage_armour_active else 0
        if mage_armour_active:
            self.max_shield += mage_armour_bonus

        # Barkskin passive: shield proportional to wis (wisdom-based)
        barkskin_active = ('Barkskin' in getattr(self, 'tree_unlocked', set())
                           and getattr(self, 'passive_toggles', {}).get('Barkskin', True))
        barkskin_bonus  = (self.wis * 5) if barkskin_active else 0
        if barkskin_active:
            self.max_shield += barkskin_bonus

        # Clamp shield: if shield newly appeared, fill to full; else keep current
        if self.max_shield > 0 and old_max_shield == 0:
            self.shield = self.max_shield
        elif kinetic_active and not getattr(self, '_kinetic_shell_initialized', False):
            # One-time fill when Kinetic Shell is first activated — never again so normal
            # combat damage is not instantly undone.
            self._kinetic_shell_initialized = True
            self.shield = min(kinetic_bonus, self.max_shield)
        else:
            self.shield = min(getattr(self, 'shield', 0), self.max_shield)

        # ── Haste buff: adds speed proportional to agi bonus ─────────────────
        _haste_agi = getattr(self, '_haste_agi_bonus', 0)
        if _haste_agi > 0 and time.time() < getattr(self, '_haste_end', 0):
            self.speed += _haste_agi * 0.15   # same coefficient as agility in _apply_stat

        # ── Rage buff: adds speed + atk from agi/str bonuses ─────────────────
        _rage_end = getattr(self, '_rage_end', 0)
        if time.time() < _rage_end:
            _rage_agi = getattr(self, '_rage_agi_bonus', 0)
            _rage_str = getattr(self, '_rage_str_bonus', 0)
            self.speed += _rage_agi * 0.15
            self.atk   += _rage_str

        # ── Fatigue debuff: halve speed if active ────────────────────────────
        if getattr(self, '_fatigue_active', False):
            if time.time() < getattr(self, '_fatigue_end', 0):
                self.speed *= 0.5
    def update_equipped_skills(self):
        """Populate weapon_skills from the equipped weapon only.
        Skills from rings/amulets are intentionally ignored — they no longer grant active skills.
        """
        # Do NOT modify skills while in Wild Shape — form skills are active
        if getattr(self, 'wild_shape_form', None):
            return
        # Remove any legacy item-granted entries from unlocked_skills (clean up old saves)
        self.unlocked_skills = [sk for sk in self.unlocked_skills if not sk.get('from_item')]

        # Skill cooldown mapping (kept for weapon skills)
        skill_cooldowns = {
            'Flame Strike': 1.0, 'Fire Breath': 0.12, 'Spear Throw': 1.5,
            'Mana Bolt': 0.5, 'Ice Arrow': 1.5, 'Lightning Bolt': 1,
            'Life Drain': 4.0, 'Blink': 2.0, 'Backstab': 2.0,
            'Thousand Cuts': 3.0, 'Dragon Strike': 8.0, 'Time Warp': 10.0,
            'Mana Beam': 4.0, 'Dark Slash': 1.0, 'Shield': 6.0, 'Heal': 2.0,
            'Arrow Shot': 0.5, 'Heated Discharge': 6.0, 'Permafrost Burst': 6.0,
            'Teleport': 2.0, 'Invisibility': 12.0, 'Orbiting Blade': 10.0,
            'Fire Storm': 30.0, 'Homing Arrow Pair': 2.0,
            'Scorching Ray': 4.0, 'Ray of Frost': 4.0,
        }

        # Preserve cooldown timers across refreshes
        _prev_map = {sk['name']: sk.get('last_used', 0)
                     for sk in getattr(self, 'weapon_skills', [])}

        # Build weapon_skills from the WEAPON slot only
        self.weapon_skills = []
        weapon_item = next((it for it in self.equipped_items if it.item_type == 'weapon'), None)
        if weapon_item:
            for skill_name in weapon_item.skills:
                if skill_name in self.item_skill_functions:
                    self.weapon_skills.append({
                        'name':       skill_name,
                        'skill':      self.item_skill_functions[skill_name],
                        'cooldown':   skill_cooldowns.get(skill_name, 2.0),
                        'last_used':  _prev_map.get(skill_name, 0),
                    })
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
            base_ang = math.atan2(_my - player.y, _mx - player.x)
            # Tight fan of 5 leaves — small spread, long range (life=2.8)
            leaf_colors = ['#228B22', '#32CD32', '#006400', '#7CFC00', '#3CB371']
            spreads = [-0.09, -0.04, 0.0, 0.04, 0.09]
            for i, offset in enumerate(spreads):
                ang = base_ang + offset
                speed = random.uniform(7.0, 8.5)
                col = leaf_colors[i % len(leaf_colors)]
                game.spawn_projectile(player.x, player.y, ang, speed, 2.8, 8, col, player.atk*2, stype='leaf')

        def entangling_roots(player, game):
            """Slam roots into the ground — triangular spike particles erupt in a zone,
            entangle all enemies inside for 4s and deal a tiny thorn damage."""
            if player.mana < 20:
                return
            player.mana -= 20
            mx, my = game.get_mouse_world_pos()
            zone_r = 90
            num_roots = 22
            for i in range(num_roots):
                ang   = random.uniform(0, 2 * math.pi)
                dist  = random.uniform(0, zone_r)
                rx    = mx + math.cos(ang) * dist
                ry    = my + math.sin(ang) * dist
                # Each root: a triangular spike shooting upward
                root_ang = random.uniform(-math.pi * 0.85, -math.pi * 0.15)  # mostly upward
                rp = Particle(rx, ry, size=random.randint(6, 14),
                              color=random.choice(['#228B22','#556B2F','#8B4513','#6B8E23']),
                              life=random.uniform(1.0, 1.8),
                              rtype='root_tri', angle=root_ang,
                              radius=random.randint(20, 45))
                rp._origin_x = rx
                rp._origin_y = ry
                game.particles.append(rp)
            # Entangle enemies in zone — only a tiny damage tick (wis * 0.5)
            for e in list(game.room.enemies):
                if distance((mx, my), (e.x, e.y)) <= zone_r + e.size:
                    e._entangled_until = time.time() + 4.0
                    e._entangled_spd   = e.spd
                    e.spd = 0
                    game.damage_enemy(e, 0.01)

        def grasping_vines(player, game):
            """Shoot a thorny vine that latches onto the nearest enemy to the cursor —
            an animated segmented vine line reaches from the player to the target,
            pins it for 6s. No damage."""
            if player.mana < 25:
                return
            if not game.room.enemies:
                return
            player.mana -= 25
            mx, my = game.get_mouse_world_pos()
            target = min(game.room.enemies,
                         key=lambda e: distance((mx, my), (e.x, e.y)))
            # Pin the target
            target._grasped       = True
            target._grasped_until = time.time() + 6.0
            target._grasped_spd   = target.spd
            target.spd            = 0
            # Spawn a single long-lived vine-track particle that draws the full vine line
            vp = Particle(player.x, player.y, size=4,
                          color='#228B22',
                          life=6.0,
                          rtype='grasping_vine_track',
                          angle=0, radius=0)
            vp._player = player
            vp._target = target
            game.particles.append(vp)

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

            for _si, _start_angle in enumerate([0.0, math.pi]):
                sentry = Summoned(
                    "Sentry",
                    hp=30 + player.mag,
                    atk=5 + player.mag,
                    spd=3 + player.mag / 20,
                    x=player.x + 40,
                    y=player.y,
                    duration=15 + player.mag,
                    role="orbit",
                    owner=player,
                    mana_upkeep=1
                )
                sentry.size          = 7
                sentry._orbit_angle  = _start_angle
                sentry._orbit_radius = 45
                sentry._orbit_speed  = 3.2
                sentry.skills.append({
                    'skill': lightbolt,
                    'name': 'lightbolt',
                    'cooldown': 0.4,
                    'last_used': 0
                })
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
            duration = 25.0
            tick_ms  = 10          # 10 ms ticks → very dense particle trail

            def apply_aura_buffs():
                player._aura_con_bonus = player.constitution * 5
                player._aura_agi_bonus = player.agility * 2
                if not hasattr(player, 'active_buffs'):
                    player.active_buffs = []
                player.active_buffs = [b for b in player.active_buffs
                                       if b.get('name') != 'Lingering Aura']
                player.active_buffs.append({
                    'emoji': '🔥',
                    'name': 'Lingering Aura',
                    'desc': f'+{player._aura_con_bonus} CON  +{player._aura_agi_bonus} AGI',
                    'end': time.time() + duration,
                    'duration': duration,
                    'con': player._aura_con_bonus,
                    'agi': player._aura_agi_bonus,
                })

            def remove_aura_buffs():
                player._aura_con_bonus = 0
                player._aura_agi_bonus = 0
                if hasattr(player, 'active_buffs'):
                    player.active_buffs = [b for b in player.active_buffs
                                           if b.get('name') != 'Lingering Aura']

            def rapid_tick():
                if time.time() >= player._rapid_end:
                    player._rapid_active = False
                    remove_aura_buffs()
                    return
                game.spawn_particle(player.x, player.y, 35, 'yellow', life=0.5, rtype='aura_behind')
                # ── Damage nearby enemies (aura circle) ──────────────────────
                for e in list(game.room.enemies):
                    if distance((player.x, player.y), (e.x, e.y)) < 50:
                        game.damage_enemy(e, player.atk / 2)

                # ── Beam line damage: STR-based, along equipped weapon direction ─
                _beq = next((it for it in player.equipped_items if it.item_type == 'weapon'), None)
                if _beq:
                    _ba = getattr(player, 'angle', 0)
                    _blen = 106
                    _bstart = 36
                    for _be in list(game.room.enemies):
                        # Point-to-segment distance
                        _bex = player.x + math.cos(_ba) * _bstart
                        _bey = player.y + math.sin(_ba) * _bstart
                        _btx = player.x + math.cos(_ba) * (_bstart + _blen)
                        _bty = player.y + math.sin(_ba) * (_bstart + _blen)
                        _dx = _btx - _bex; _dy = _bty - _bey
                        _t  = max(0, min(1, ((_be.x-_bex)*_dx + (_be.y-_bey)*_dy) / (_dx*_dx+_dy*_dy+1e-9)))
                        _cx = _bex + _t*_dx; _cy = _bey + _t*_dy
                        if distance((_be.x, _be.y), (_cx, _cy)) <= _be.size + 9:
                            game.damage_enemy(_be, player.strength * 0.3)

                # ── Delete enemy projectiles within aura radius ────────────────
                for proj in list(game.projectiles):
                    if getattr(proj, 'owner', None) != player:
                        if distance((player.x, player.y), (proj.x, proj.y)) <= 30 + proj.radius:
                            game.projectiles.remove(proj)

                game.after(tick_ms, rapid_tick)

            if not getattr(player, "_rapid_active", False):
                player._rapid_active = True
                player._rapid_end    = time.time() + duration
                apply_aura_buffs()
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
                        # Cyan magic_burst on hit
                        for _ in range(18):
                            _ba = random.uniform(0, 2*math.pi)
                            game.spawn_particle(e.x + math.cos(_ba)*random.uniform(4,18),
                                                e.y + math.sin(_ba)*random.uniform(4,18),
                                                random.uniform(3,8), random.choice(['cyan','#aaffff','white']),
                                                life=random.uniform(0.25,0.45), rtype='magic_burst')
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
                        # Red magic_burst on hit
                        for _ in range(18):
                            _ba = random.uniform(0, 2*math.pi)
                            game.spawn_particle(e.x + math.cos(_ba)*random.uniform(4,18),
                                                e.y + math.sin(_ba)*random.uniform(4,18),
                                                random.uniform(3,8), random.choice(['#ff4444','#ff2200','#ff8866']),
                                                life=random.uniform(0.25,0.45), rtype='magic_burst')


            # Damage enemies in arc
        def _apply_poison_infusion(player, game, enemy):
            """Apply tiered poison to enemy if player has Poison Infusion unlocked."""
            if 'Poison Infusion' not in getattr(player, 'tree_unlocked', set()):
                return
            now_pi = time.time()
            cur_tier   = getattr(enemy, '_poison_tier', 0)
            cur_until  = getattr(enemy, '_poison_until', 0)
            still_active = cur_until > now_pi
            if still_active and cur_tier == 1:
                new_tier = 2; duration = 10.0; dps_pct = 0.03
            elif still_active and cur_tier >= 2:
                new_tier = 3; duration = 15.0; dps_pct = 0.05
            else:
                new_tier = 1; duration = 5.0;  dps_pct = 0.02
            enemy._poison_tier  = new_tier
            enemy._poison_until = now_pi + duration
            enemy._poison_dps   = enemy.max_hp * dps_pct

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
                        _apply_poison_infusion(player, game, e)
                        # Purple magic_burst on hit
                        for _ in range(20):
                            _ba = random.uniform(0, 2*math.pi)
                            game.spawn_particle(e.x + math.cos(_ba)*random.uniform(4,20),
                                                e.y + math.sin(_ba)*random.uniform(4,20),
                                                random.uniform(3,9), random.choice(['#cc44ff','#9922dd','#ff88ff']),
                                                life=random.uniform(0.28,0.5), rtype='magic_burst')

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
            game.spawn_projectile(player.x, player.y, ang, 8, 10, 10, 'cyan', player.mag, 'player', ptype='icicle', stype='icicle')

        def hydro_shot(player, game):
            if player.mana < 15: return
            player.mana -= 15
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            proj = game.spawn_projectile(player.x, player.y, ang, 9, 10, 11,
                                         '#44aaff', player.mag * 7, 'player',
                                         ptype='hydro_shot', stype='hydro_shot')
            if proj:
                proj._travel_angle = ang

        def firebolt(player, game):
            if player.mana < 8: return
            player.mana -= 8
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            proj = game.spawn_projectile(player.x, player.y, ang, 11, 6, 8,
                                         'orange', player.mag * 4, 'player',
                                         ptype='firebolt', stype='firebolt')

        def icebolt(player, game):
            if player.mana < 8: return
            player.mana -= 8
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            proj = game.spawn_projectile(player.x, player.y, ang, 11, 6, 8,
                                         'cyan', player.mag * 4, 'player',
                                         ptype='icebolt', stype='icebolt')

        def aqua_missile(player, game):
            if player.mana < 10: return
            player.mana -= 10
            def _spawn():
                _mx, _my = game.get_mouse_world_pos()
                _base_ang = math.atan2(_my - player.y, _mx - player.x)
                for _i in range(6):
                    _spread = (_i - 2.5) * 0.12   # fan spread across 6 shots
                    _ang = _base_ang + _spread
                    proj = game.spawn_projectile(player.x, player.y, _ang, 10, 8, 7,
                                                 '#00ccff', player.mag * 5, 'player',
                                                 ptype='aqua_missile', stype='aqua_missile')
                    if proj:
                        proj._spiral_t = _i * 0.8
                        proj._base_angle = _ang
            _spawn()
            game.after(350, _spawn)
            game.after(700, _spawn)


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

        def holyflame(player, game):
            if player.mana < 15: return
            player.mana -= 15
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            proj = game.spawn_projectile(player.x, player.y, ang, 9, 10, 12, '#ffdd00',
                                         player.mag * 10, 'player', ptype='holyflame', stype='hf_proj')

        def blackflame(player, game):
            if player.mana < 15: return
            player.mana -= 15
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            proj = game.spawn_projectile(player.x, player.y, ang, 9, 10, 12, '#660033',
                                         player.mag * 10, 'player', ptype='blackflame', stype='bf_proj')

        def halo_of_radiance(player, game):
            duration  = 10.0
            tick_ms   = 80
            radius    = 60
            ray_count = 8
            if not hasattr(player, '_halo_angle'):
                player._halo_angle = 0.0

            def halo_tick():
                if time.time() >= player._halo_end:
                    player._halo_active = False
                    return
                player._halo_angle += 0.08
                # Daze + damage enemies in radius
                for e in list(game.room.enemies):
                    if distance((player.x, player.y), (e.x, e.y)) < radius:
                        game.damage_enemy(e, player.mag * 0.5)
                        e._dazed_until = time.time() + 0.3
                # Spawn rotating god-ray particles
                for _ri in range(ray_count):
                    _ra = player._halo_angle + _ri * (2 * math.pi / ray_count)
                    for _rd in range(3):
                        _dist = 20 + _rd * 14
                        _px = player.x + math.cos(_ra) * _dist
                        _py = player.y + math.sin(_ra) * _dist
                        _col = random.choice(['#ffee00', '#ffffff', '#ffdd44', '#ffffaa'])
                        game.spawn_particle(_px, _py, random.uniform(3, 7), _col,
                                            life=0.12, rtype='magic_burst')
                game.after(tick_ms, halo_tick)

            if not getattr(player, '_halo_active', False):
                player._halo_active = True
                player._halo_end = time.time() + duration
                halo_tick()

        def circle_of_life(player, game):
            _mx, _my = game.get_mouse_world_pos()
            duration = 5.0
            radius   = 55
            tick_ms  = 200
            heal_per_tick = max(1, player.mag * 0.4)
            end_time = time.time() + duration
            # Store circle zones on game for rendering
            if not hasattr(game, '_life_circles'):
                game._life_circles = []
            circle = {'x': _mx, 'y': _my, 'r': radius, 'end': end_time}
            game._life_circles.append(circle)

            def life_tick():
                if time.time() >= end_time:
                    if circle in getattr(game, '_life_circles', []):
                        game._life_circles.remove(circle)
                    return
                # Heal any player inside
                if distance((player.x, player.y), (_mx, _my)) < radius:
                    player.hp = min(player.max_hp, player.hp + heal_per_tick)
                # Green upward particles — light-green, rising (life_spark rtype)
                for _ in range(10):
                    _px = _mx + random.uniform(-radius * 0.85, radius * 0.85)
                    _py = _my + random.uniform(-radius * 0.85, radius * 0.85)
                    game.spawn_particle(_px, _py, random.uniform(1.5, 3), '#44ff88',
                                        life=random.uniform(0.5, 1.0), rtype='life_spark')
                game.after(tick_ms, life_tick)

            life_tick()
        def arrow_shot(player, game):
            if player.mana < 1 or not game.room.enemies: return
            player.mana -= 1
            _mx, _my = game.get_mouse_world_pos()
            ang = math.atan2(_my - player.y, _mx - player.x)
            game.spawn_projectile(player.x, player.y, ang, 6, 3, 8, 'brown', player.atk*2, owner='player', stype='arrow')

        def homing_arrow_pair(player, game):
            """Arcane Longbow skill: fire one orange and one cyan homing arrow at enemies."""
            if player.mana < 8 or not game.room.enemies: return
            player.mana -= 8
            target = min(game.room.enemies, key=lambda e: distance((player.x,player.y),(e.x,e.y)))
            ang = math.atan2(target.y - player.y, target.x - player.x)
            # Orange homing — flame explosion on hit
            p1 = game.spawn_projectile(player.x, player.y, ang + 0.15, 5, 6, 10,
                                       'orange', player.atk * 3, owner='player',
                                       ptype='player_homing_fire', stype='arrow')
            if p1:
                p1._home_target = target
                p1._home_strength = 0.09
            # Cyan homing — fired 0.8s later via enemy
            p2 = game.spawn_projectile(player.x, player.y, ang - 0.15, 5, 6, 10,
                                       'cyan', player.atk * 2.5, owner='player',
                                       ptype='player_homing_frost', stype='arrow')
            if p2:
                p2._home_target = target
                p2._home_strength = 0.09
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
            if player.mana < 4:
                return
            player.mana -= 4

            # Fan of 5 arrows centred on the mouse direction
            _mx, _my = game.get_mouse_world_pos()
            base_ang = math.atan2(_my - player.y, _mx - player.x)
            spread   = math.radians(20)   # 20° between each arrow
            num      = 5
            offsets  = [spread * (i - (num - 1) / 2) for i in range(num)]

            for offset in offsets:
                ang = base_ang + offset
                game.spawn_projectile(
                    player.x, player.y,
                    ang,
                    7,       # speed
                    3,       # life
                    8,       # radius
                    'brown', # color
                    player.atk * 2,
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

        def scorching_ray(player, game):
            """Pyromancer soulbound beam: sustained fire channel identical to Ignis scorching ray."""
            if player.mana < 20:
                return
            player.mana -= 20
            if not hasattr(game, 'player_beam') or game.player_beam is None:
                _mmx, _mmy = game.get_mouse_world_pos()
                angle = math.atan2(_mmy - player.y, _mmx - player.x)
                beam = Beam(player.x, player.y, angle, 380, '#ff4400', 8, owner=player)
                beam._beam_type = 'scorching_ray'
                game.player_beam = beam
                game.beam_active_until = time.time() + 3.0 + player.mag / 15

        def ray_of_frost(player, game):
            """Cryomancer soulbound beam: sustained ice channel with frost particles and chill."""
            if player.mana < 20:
                return
            player.mana -= 20
            if not hasattr(game, 'player_beam') or game.player_beam is None:
                _mmx, _mmy = game.get_mouse_world_pos()
                angle = math.atan2(_mmy - player.y, _mmx - player.x)
                beam = Beam(player.x, player.y, angle, 380, '#88eeff', 8, owner=player)
                beam._beam_type = 'ray_of_frost'
                game.player_beam = beam
                game.beam_active_until = time.time() + 3.0 + player.mag / 15

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

        def ice_breath(player, game):
            """Activate 5-second frost breath channel — streams ice toward cursor."""
            if player.mana < 10:
                return
            player._ice_breath_end  = time.time() + 5.0
            player._ice_breath_tick = 0.0

        def fire_storm(player, game):
            """Ignis's flame swirl — three rotating fire rings, 4s duration. CD: 30s."""
            if player.mana < 40:
                return
            player.mana -= 40
            player._fire_storm_end   = time.time() + 4.0
            player._fire_storm_start = time.time()

        def mana_barrier(player, game):
            """Toggle a directional mana barrier near the cursor. Drains mana, rotates with cursor."""
            if not getattr(player, '_mana_barrier_active', False):
                if player.mana < 5:
                    return
                player._mana_barrier_active = True
                player._mana_barrier_range  = 130  # max distance from player
                tick_ms = 16  # ~60fps

                def barrier_tick():
                    if player.mana <= 0 or not getattr(player, '_mana_barrier_active', False):
                        player._mana_barrier_active = False
                        return
                    player.mana -= 0.5  # drain per tick

                    # Update angle toward cursor
                    _mx, _my = game.get_mouse_world_pos()
                    dx = _mx - player.x
                    dy = _my - player.y
                    dist = math.hypot(dx, dy)
                    if dist < 1:
                        dist = 1
                    # Clamp barrier position to max range
                    clamped = min(dist, player._mana_barrier_range)
                    bx = player.x + (dx / dist) * clamped
                    by = player.y + (dy / dist) * clamped
                    angle = math.atan2(dy, dx)
                    player._mana_barrier_state = (bx, by, angle)

                    # Block enemy projectiles that intersect the barrier line
                    half_len = 22
                    # Barrier is a line segment perpendicular to player-cursor
                    perp = angle + math.pi / 2
                    bx1 = bx + math.cos(perp) * half_len
                    by1 = by + math.sin(perp) * half_len
                    bx2 = bx - math.cos(perp) * half_len
                    by2 = by - math.sin(perp) * half_len
                    for proj in list(game.projectiles):
                        if proj.owner == 'player':
                            continue
                        px, py = proj.x, proj.y
                        # Simple point-to-segment distance check
                        seg_dx = bx2 - bx1; seg_dy = by2 - by1
                        seg_len_sq = seg_dx**2 + seg_dy**2
                        if seg_len_sq > 0:
                            t = max(0, min(1, ((px-bx1)*seg_dx + (py-by1)*seg_dy) / seg_len_sq))
                            nx = bx1 + t*seg_dx; ny = by1 + t*seg_dy
                            if math.hypot(px-nx, py-ny) < getattr(proj, 'radius', 5) + 8:
                                game.projectiles.remove(proj)

                    # Block enemies from crossing barrier line
                    for e in list(game.room.enemies):
                        ex, ey = e.x, e.y
                        seg_dx = bx2 - bx1; seg_dy = by2 - by1
                        seg_len_sq = seg_dx**2 + seg_dy**2
                        if seg_len_sq > 0:
                            t2 = max(0, min(1, ((ex-bx1)*seg_dx + (ey-by1)*seg_dy) / seg_len_sq))
                            near_x = bx1 + t2*seg_dx; near_y = by1 + t2*seg_dy
                            dist_to_bar = math.hypot(ex-near_x, ey-near_y)
                            if dist_to_bar < e.size + 10:
                                # Push enemy back away from barrier
                                push_dx = ex - near_x; push_dy = ey - near_y
                                push_len = math.hypot(push_dx, push_dy)
                                if push_len > 0:
                                    push_f = (e.size + 12 - dist_to_bar) / push_len * 2
                                    e.x += push_dx * push_f
                                    e.y += push_dy * push_f

                    # Spawn a visual barrier particle each tick
                    bar_p = Particle(bx, by, half_len, '#66aaff', life=0.04,
                                     rtype='shield', outline=True)
                    bar_p._barrier_angle = angle
                    game.particles.append(bar_p)

                    game.after(tick_ms, barrier_tick)

                barrier_tick()
            else:
                player._mana_barrier_active = False

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
            _mx, _my = game.get_mouse_world_pos()
            angle = math.atan2(_my - player.y, _mx - player.x)
            blink_dist = 500
            # Dense small burst at departure
            for i in range(35):
                ang2 = random.uniform(0, 2 * math.pi)
                ring_r = random.uniform(3, 18)
                game.spawn_particle(player.x + math.cos(ang2) * ring_r,
                                    player.y + math.sin(ang2) * ring_r,
                                    random.uniform(2, 5), '#cc44ff',
                                    life=random.uniform(0.2, 0.45))
            player.x += math.cos(angle) * blink_dist
            player.y += math.sin(angle) * blink_dist
            player.x = clamp(player.x, 0, WINDOW_W)
            player.y = clamp(player.y, 0, WINDOW_H)
            # Dense small burst at arrival
            for i in range(35):
                ang2 = random.uniform(0, 2 * math.pi)
                ring_r = random.uniform(3, 18)
                game.spawn_particle(player.x + math.cos(ang2) * ring_r,
                                    player.y + math.sin(ang2) * ring_r,
                                    random.uniform(2, 5), '#cc44ff',
                                    life=random.uniform(0.2, 0.45))

        def teleport(player, game):
            """Single-click teleport directly to the mouse cursor position."""
            _mx, _my = game.get_mouse_world_pos()
            old_x, old_y = player.x, player.y
            # Dense small burst at departure
            for i in range(35):
                ang2 = random.uniform(0, 2 * math.pi)
                ring_r = random.uniform(3, 18)
                game.spawn_particle(old_x + math.cos(ang2) * ring_r,
                                    old_y + math.sin(ang2) * ring_r,
                                    random.uniform(2, 5), '#cc44ff',
                                    life=random.uniform(0.2, 0.45))
            player.x = clamp(_mx, player.size, WINDOW_W - player.size)
            player.y = clamp(_my, player.size, WINDOW_H - player.size)
            # Dense small burst at arrival
            for i in range(35):
                ang2 = random.uniform(0, 2 * math.pi)
                ring_r = random.uniform(3, 18)
                game.spawn_particle(player.x + math.cos(ang2) * ring_r,
                                    player.y + math.sin(ang2) * ring_r,
                                    random.uniform(2, 5), '#cc44ff',
                                    life=random.uniform(0.2, 0.45))

        def invisibility(player, game):
            """All enemies in room wander. Breaks on any skill/item use."""
            now = time.time()
            player._invisible = True
            player._invisible_end = now + 12.0   # visual/logic duration cap
            if not hasattr(player, 'active_buffs'):
                player.active_buffs = []
            player.active_buffs.append({
                'emoji': '👁',
                'name': 'Invisibility',
                'desc': 'Enemies wander. Breaks on skill/item use.',
                'end': now + 12.0,
                'duration': 12.0,
                'str': 0, 'agi': 0, 'wil': 0,
            })
            for e in game.room.enemies:
                e._forced_wander = True
                e._forced_wander_end = now + 30.0  # enemies wander until broken

        def mage_armour(player, game):
            """Passive — handled by update_stats. This stub satisfies skill-list requirements."""
            pass

        def analysis(player, game):
            """Active [R]: inspect nearest enemy, show floating info above them for 4s."""
            if not game.room.enemies:
                return
            target = min(game.room.enemies,
                         key=lambda e: math.hypot(e.x - player.x, e.y - player.y))
            skill_names = [s.get('name', '?') for s in getattr(target, 'skills', [])]
            skills_text = '  |  '.join(skill_names) if skill_names else 'None'
            lines = [
                f"[ {target.name} ]",
                f"HP {int(target.hp)}/{int(target.max_hp)}   ATK {getattr(target,'atk','?')}   SPD {getattr(target,'spd','?')}",
                f"Skills: {skills_text}",
            ]
            # Store on game so it can be drawn in the render loop
            if not hasattr(game, '_analysis_displays'):
                game._analysis_displays = []
            game._analysis_displays.append({
                'target': target,
                'lines':  lines,
                'until':  time.time() + 4.0,
            })

        def barkskin(player, game):
            """Passive — handled by update_stats. This stub satisfies skill-list requirements."""
            pass

        def chi_propulsion(player, game):
            """Animate player forward step-by-step; trail particles flow toward monk; bolt-impact burst on arrival."""
            _mx, _my = game.get_mouse_world_pos()
            angle = math.atan2(_my - player.y, _mx - player.x)
            dash_dist = 120 + player.vit * 2
            start_x, start_y = player.x, player.y
            end_x = clamp(start_x + math.cos(angle) * dash_dist, player.size, WINDOW_W - player.size)
            end_y = clamp(start_y + math.sin(angle) * dash_dist, player.size, WINDOW_H - player.size)

            steps = 14        # number of frames
            delay_ms = 22     # ms per frame → ~300 ms total, visibly slow

            def step(i):
                if i > steps:
                    # Impact burst — small scattered dots like mana/light bolt hit
                    for _ in range(8):
                        ang2 = random.uniform(0, 2 * math.pi)
                        r    = random.uniform(4, 14)
                        game.spawn_particle(player.x + math.cos(ang2) * r,
                                            player.y + math.sin(ang2) * r,
                                            random.uniform(2, 4), 'cyan', life=0.2)
                    return

                t = i / steps
                player.x = start_x + (end_x - start_x) * t
                player.y = start_y + (end_y - start_y) * t
                player.x = clamp(player.x, player.size, WINDOW_W - player.size)
                player.y = clamp(player.y, player.size, WINDOW_H - player.size)

                # Trail dot left behind the monk — size shrinks with progress so
                # later dots are smaller, making the tail look like it converges
                trail_size = random.uniform(3, 6) * (1.0 - t * 0.6)
                tp = Particle(player.x - math.cos(angle) * 8,
                              player.y - math.sin(angle) * 8,
                              max(1.5, trail_size), 'cyan', life=0.18, rtype='basic')
                game.particles.append(tp)

                game.after(delay_ms, lambda i=i: step(i + 1))

            step(1)

        def flurry_of_blows(player, game):
            """8 chi strikes scattered as a random cloud in the aimed direction."""
            _mx, _my = game.get_mouse_world_pos()
            base_angle = math.atan2(_my - player.y, _mx - player.x)
            num_strikes = 8
            forward_reach = 180   # how far ahead the cloud extends
            spread_radius = 75    # random scatter width of the cloud

            for _ in range(num_strikes):
                fwd  = random.uniform(35, forward_reach)
                side = random.uniform(-spread_radius, spread_radius)
                perp = base_angle + math.pi / 2

                spawn_x = player.x + math.cos(base_angle) * fwd + math.cos(perp) * side
                spawn_y = player.y + math.sin(base_angle) * fwd + math.sin(perp) * side

                strike_angle = base_angle + random.uniform(-0.45, 0.45)
                blade = Particle(spawn_x, spawn_y, 22, 'cyan', life=0.35,
                                 rtype='blade1_fwd', angle=strike_angle)
                game.particles.append(blade)

                for e in list(game.room.enemies):
                    if distance((spawn_x, spawn_y), (e.x, e.y)) <= 45:
                        game.damage_enemy(e, player.vit * 0.8)

        def iron_guard(player, game):
            """Toggle: multiply constitution by 10, rapidly drain HP. Shows as buff; player turns grey-metallic."""
            tick_ms = 10
            hp_drain_per_tick = 0.8   # ~80 HP/s

            def guard_tick():
                if player.hp <= 1 or not getattr(player, '_iron_guard_active', False):
                    if getattr(player, '_iron_guard_active', False):
                        _deactivate_iron_guard()
                    return
                player.hp = max(1, player.hp - hp_drain_per_tick)
                game.after(tick_ms, guard_tick)

            def _deactivate_iron_guard():
                player._iron_guard_active = False
                orig = getattr(player, '_iron_guard_orig_con', max(1, player.constitution // 10))
                player.constitution = orig
                saved_hp = player.hp          # preserve the drained HP value
                player.update_stats()
                player.hp = min(saved_hp, player.max_hp)   # clamp but don't let vitality bonuses add HP back
                if hasattr(player, 'active_buffs'):
                    player.active_buffs = [b for b in player.active_buffs
                                           if b.get('name') != 'Iron Guard']

            if not getattr(player, '_iron_guard_active', False):
                player._iron_guard_active = True
                player._iron_guard_orig_con = player.constitution
                player.constitution = player.constitution * 10
                player.update_stats()
                # Register as active buff so it appears on the HUD and stats panel
                if not hasattr(player, 'active_buffs'):
                    player.active_buffs = []
                # Remove any stale Iron Guard entry first
                player.active_buffs = [b for b in player.active_buffs
                                        if b.get('name') != 'Iron Guard']
                player.active_buffs.append({
                    'emoji': '🛡',
                    'name':  'Iron Guard',
                    'desc':  f'CON ×10 ({player.constitution})  |  HP draining',
                    'end':   float('inf'),   # permanent toggle — no expiry
                    'duration': 1,
                    'str': 0, 'agi': 0, 'wil': 0,
                    'con': player._iron_guard_orig_con * 9,   # bonus = orig*10 - orig = orig*9
                })
                guard_tick()
            else:
                _deactivate_iron_guard()
        
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
        def orbiting_blade(player, game):
            """Summon 3 greatsword projectiles that orbit the player for 3s then launch toward enemies / mouse."""
            num_blades = 3
            orbit_dur  = 3.0

            if not hasattr(player, '_orbit_blades'):
                player._orbit_blades = []

            # Start the first blade angled toward the mouse so the visual feels intentional
            _mx, _my = game.get_mouse_world_pos()
            start_angle = math.atan2(_my - player.y, _mx - player.x)

            for i in range(num_blades):
                player._orbit_blades.append({
                    'angle':    start_angle + (2 * math.pi / num_blades) * i,
                    'launched': False,
                    'spawn_t':  time.time(),
                    'dur':      orbit_dur,
                })

        # Store item skill functions for lookup
        # ── Haste (Rogue) ──────────────────────────────────────────────────────
        def haste(player, game):
            """Rogue buff: AGI×3 for 20 s. Emits light-blue wind particles. CD: 40 s."""
            _ht_dur   = 20.0
            _ht_bonus = player.agility * 2   # extra agility on top of base (×3 total)
            player._haste_agi_bonus = _ht_bonus
            player._haste_end       = time.time() + _ht_dur

            if not hasattr(player, 'active_buffs'):
                player.active_buffs = []
            player.active_buffs = [b for b in player.active_buffs if b.get('name') != 'Haste']
            player.active_buffs.append({
                'emoji': '💨', 'name': 'Haste',
                'desc': f'AGI ×3 (+{_ht_bonus})',
                'end': player._haste_end,
            })

            def _haste_tick():
                if time.time() >= player._haste_end:
                    player._haste_agi_bonus = 0
                    if hasattr(player, 'active_buffs'):
                        player.active_buffs = [b for b in player.active_buffs if b.get('name') != 'Haste']
                    return
                # Light-blue wind particles floating upward — multiple per tick
                for _ in range(3):
                    _ox = random.uniform(-player.size * 1.2, player.size * 1.2)
                    _oy = random.uniform(-player.size * 0.5, player.size * 0.5)
                    game.spawn_particle(player.x + _ox,
                                        player.y + _oy,
                                        random.uniform(3, 8),
                                        random.choice(['#88ddff', '#aaeeff', '#ccf5ff', 'white']),
                                        life=random.uniform(0.5, 1.1), rtype='magic_burst')
                game.after(40, _haste_tick)

            _haste_tick()

        # ── Rage (Warrior) ─────────────────────────────────────────────────────
        def rage(player, game):
            """Warrior buff: AGI×2, STR×5 for 10 s; then Fatigue (-50% AGI) for 10 s. CD: 40 s."""
            _rg_dur    = 10.0
            _ft_dur    = 10.0
            _rg_agi    = player.agility          # extra agi (×2 total)
            _rg_str    = player.strength * 4     # extra str (×5 total)
            player._rage_agi_bonus = _rg_agi
            player._rage_str_bonus = _rg_str
            player._fatigue_active = False
            player._rage_end       = time.time() + _rg_dur

            if not hasattr(player, 'active_buffs'):
                player.active_buffs = []
            player.active_buffs = [b for b in player.active_buffs
                                   if b.get('name') not in ('Rage', 'Fatigue')]
            player.active_buffs.append({
                'emoji': '⚔️', 'name': 'Rage',
                'desc': f'AGI ×2 (+{_rg_agi})  STR ×5 (+{_rg_str})',
                'end': player._rage_end,
            })
            # Rage visual: red burst on cast
            for _ in range(22):
                _ra = random.uniform(0, 2*math.pi)
                game.spawn_particle(player.x + math.cos(_ra)*random.uniform(5,25),
                                    player.y + math.sin(_ra)*random.uniform(5,25),
                                    random.uniform(5,12), random.choice(['#ff2200','#ff6600','#ffaa00']),
                                    life=random.uniform(0.4, 0.7), rtype='magic_burst')

            def _rage_tick():
                if time.time() >= player._rage_end:
                    return
                for _ in range(2):
                    _ra = random.uniform(0, 2*math.pi)
                    game.spawn_particle(player.x + math.cos(_ra)*random.uniform(4,player.size*1.5),
                                        player.y + math.sin(_ra)*random.uniform(4,player.size*1.5),
                                        random.uniform(3,7), random.choice(['#ff2200','#ff6600']),
                                        life=random.uniform(0.3, 0.6), rtype='magic_burst')
                game.after(60, _rage_tick)

            _rage_tick()

            def _apply_fatigue():
                player._rage_agi_bonus = 0
                player._rage_str_bonus = 0
                player._fatigue_active = True
                player._fatigue_end    = time.time() + _ft_dur
                if hasattr(player, 'active_buffs'):
                    player.active_buffs = [b for b in player.active_buffs if b.get('name') != 'Rage']
                player.active_buffs.append({
                    'emoji': '😩', 'name': 'Fatigue',
                    'desc': 'AGI −50%',
                    'end': player._fatigue_end,
                    'duration': _ft_dur,
                    'color': '#cc8844', 'bar_color': '#884422',
                })

            def _clear_fatigue():
                player._fatigue_active = False
                if hasattr(player, 'active_buffs'):
                    player.active_buffs = [b for b in player.active_buffs if b.get('name') != 'Fatigue']

            game.after(int(_rg_dur * 1000), _apply_fatigue)
            game.after(int((_rg_dur + _ft_dur) * 1000), _clear_fatigue)

        # ── Lunge (Warrior) ────────────────────────────────────────────────────
        def lunge(player, game):
            """Dash toward cursor, slash enemies on the path, leave a fading red stippled trail."""
            _mx, _my  = game.get_mouse_world_pos()
            _la       = math.atan2(_my - player.y, _mx - player.x)
            _ldist    = 140 + player.agility * 1.5
            _sx, _sy  = player.x, player.y
            _ex = clamp(_sx + math.cos(_la) * _ldist, player.size, WINDOW_W - player.size)
            _ey = clamp(_sy + math.sin(_la) * _ldist, player.size, WINDOW_H - player.size)

            # Enemies hit tracking (so one lunge doesn't double-damage the same enemy)
            _hit_set = set()

            _steps = 16
            _delay = 18   # ms per frame

            def _lunge_step(i):
                if i > _steps:
                    # Arrival burst
                    for _ in range(10):
                        _ba = random.uniform(0, 2*math.pi)
                        game.spawn_particle(player.x + math.cos(_ba)*random.uniform(4,14),
                                            player.y + math.sin(_ba)*random.uniform(4,14),
                                            random.uniform(3,7), '#ff3300',
                                            life=0.25, rtype='magic_burst')
                    return

                t = i / _steps
                player.x = clamp(_sx + (_ex - _sx) * t, player.size, WINDOW_W - player.size)
                player.y = clamp(_sy + (_ey - _sy) * t, player.size, WINDOW_H - player.size)

                # Fading red trail — thick stippled line segment from start to current pos
                _alpha = 1.0 - t   # fades as we move forward (older = more faded)
                _trail = Particle(_sx + (_ex - _sx) * (i - 1) / _steps,
                                  _sy + (_ey - _sy) * (i - 1) / _steps,
                                  size=14, color='#cc1100',
                                  life=0.35 * _alpha + 0.05, rtype='lunge_trail',
                                  angle=_la)
                _trail._lunge_end_x = player.x
                _trail._lunge_end_y = player.y
                game.particles.append(_trail)

                # Damage enemies touching the path
                _dmg = player.atk * 3
                for e in list(game.room.enemies):
                    if id(e) in _hit_set:
                        continue
                    if distance((player.x, player.y), (e.x, e.y)) <= player.size + e.size + 8:
                        _hit_set.add(id(e))
                        game.damage_enemy(e, _dmg)
                        # Red magic_burst on each hit enemy
                        for _ in range(8):
                            _ba = random.uniform(0, 2*math.pi)
                            game.spawn_particle(e.x + math.cos(_ba)*random.uniform(4,14),
                                                e.y + math.sin(_ba)*random.uniform(4,14),
                                                random.uniform(3,7), '#ff2200',
                                                life=0.28, rtype='magic_burst')

                game.after(_delay, lambda i=i: _lunge_step(i + 1))

            _lunge_step(1)

        self.item_skill_functions = {
            'Flame Strike': flame_strike,
            'Fire Breath': fire_breath,
            'Ice Breath': ice_breath,
            'Mana Barrier': mana_barrier,
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
            'Permafrost Burst': permafrost_burst,  # NEW
            'Teleport': teleport,
            'Invisibility': invisibility,
            'Orbiting Blade': orbiting_blade,
            'Homing Arrow Pair': homing_arrow_pair,
            'Fire Storm': fire_storm,
            'Hydro Shot': hydro_shot,
            'Firebolt':   firebolt,
            'Icebolt':    icebolt,
            'Aqua Missile': aqua_missile,
            'Scorching Ray': scorching_ray,
            'Ray of Frost':  ray_of_frost,
        }
        # Assign skills based on class
        self.skills.clear()
        if self.class_name=='Mage':
            self.skills.append({'skill': mana_bolt,      'name':'Mana Bolt',      'key':1,'level':1,'cooldown':0.5, 'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': mana_barrier,   'name':'Mana Barrier',   'key':0,'level':1,'cooldown':0.5, 'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': fireball,       'name':'Fireball',       'key':0,'level':1,'cooldown':3, 'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': fire_breath,    'name':'Fire Breath',    'key':0,'level':1,'cooldown':1.0, 'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': icicle,         'name':'Icicle',         'key':0,'level':1,'cooldown':1.5, 'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': ice_breath,     'name':'Ice Breath',     'key':0,'level':1,'cooldown':1.0, 'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': hydro_shot,     'name':'Hydro Shot',     'key':0,'level':1,'cooldown':1.5, 'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': firebolt,       'name':'Firebolt',       'key':0,'level':1,'cooldown':0.6, 'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': icebolt,        'name':'Icebolt',        'key':0,'level':1,'cooldown':0.6, 'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': aqua_missile,   'name':'Aqua Missile',   'key':0,'level':1,'cooldown':2.0, 'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': mana_shield,    'name':'Mana Bubble',    'key':0,'level':1,'cooldown':1,   'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': chain_lightning,'name':'Chain Lightning','key':0,'level':10,'cooldown':3,  'last_used':0,'cooldown_mod':1.0})
        elif self.class_name=='Warrior':
            self.skills.append({'skill': strike,'name':'Strikes','key':1,'level':1,'cooldown':0.2,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': ground_pound,'name':'Ground Pound','key':0,'level':1,'cooldown':0.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': strike_projection,'name':'Strike Projection','key':0,'level':1,'cooldown':0.3,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': lingering_aura_of_valour,'name':'Lingering Aura of Valour','key':0,'level':1,'cooldown':20,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': lunge,'name':'Lunge','key':0,'level':1,'cooldown':1.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': rage,'name':'Rage','key':0,'level':1,'cooldown':40.0,'last_used':0,'cooldown_mod':1.0})
        elif self.class_name=='Rogue':
            self.skills.append({'skill': dark_slash,'name':'Dark Slash','key':1,'level':1,'cooldown':0.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': shadow_dagger,'name':'Shadow Dagger','key':0,'level':1,'cooldown':0.4,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': blink,'name':'Blink','key':0,'level':1,'cooldown':0.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': thousand_cuts,'name':'Thousand Cuts','key':0,'level':1,'cooldown':3,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': teleport,'name':'Teleport','key':0,'level':1,'cooldown':2.0,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': invisibility,'name':'Invisibility','key':0,'level':1,'cooldown':12.0,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': blackflame,'name':'Blackflame','key':0,'level':1,'cooldown':3,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': haste,'name':'Haste','key':0,'level':1,'cooldown':40.0,'last_used':0,'cooldown_mod':1.0})
        elif self.class_name=='Cleric':
            self.skills.append({'skill': light_bolt,'name':'Light Bolt','key':1,'level':1,'cooldown':0.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': minor_heal,'name':'Minor Heal','key':0,'level':1,'cooldown':1,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': laser,'name':'Light Beam','key':0,'level':1,'cooldown':2,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': summon_sentry,'name':'Summon Range Sentry','key':0,'level':1,'cooldown':2,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': holyflame,'name':'Holyflame','key':0,'level':1,'cooldown':4,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': halo_of_radiance,'name':'Halo of Radiance','key':0,'level':1,'cooldown':10.0,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': circle_of_life,'name':'Circle of Life','key':0,'level':1,'cooldown':12.0,'last_used':0,'cooldown_mod':1.0})
        elif self.class_name=='Druid':
            self.skills.append({'skill': thorn_whip,'name':'Thorn Whip','key':1,'level':1,'cooldown':0.4,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': summon_wolf,'name':'Summon Wolf','key':0,'level':1,'cooldown':1,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': leaf_shot,'name':'Leaf Shot','key':0,'level':1,'cooldown':0.8,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': lashing_vines,'name':'Lashing Vines','key':0,'level':1,'cooldown':2,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': entangling_roots,'name':'Entangling Roots','key':0,'level':1,'cooldown':8.0,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': grasping_vines,'name':'Grasping Vines','key':0,'level':1,'cooldown':12.0,'last_used':0,'cooldown_mod':1.0})
        elif self.class_name=='Monk':
            self.skills.append({'skill': chi_strike,'name':'Chi Strike','key':1,'level':1,'cooldown':0.2,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': chi_blast,'name':'Chi Blast','key':0,'level':1,'cooldown':1.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': ground_pound,'name':'Ground Pound','key':0,'level':1,'cooldown':0.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': thousand_cuts,'name':'Thousand Cuts','key':0,'level':1,'cooldown':3,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': chi_propulsion,'name':'Chi Propulsion','key':0,'level':1,'cooldown':0.7,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': flurry_of_blows,'name':'Flurry of Blows','key':0,'level':1,'cooldown':1.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': iron_guard,'name':'Iron Guard','key':0,'level':1,'cooldown':1,'last_used':0,'cooldown_mod':1.0})
        elif self.class_name=='Ranger':
            self.skills.append({'skill': arrow_shot,'name':'Arrow Shot','key':1,'level':1,'cooldown':0.5,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': multishot,'name':'Multishot','key':0,'level':5,'cooldown':1,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': fire_trap,'name':'Fire Trap','key':0,'level':10,'cooldown':1,'last_used':0,'cooldown_mod':1.0})
            self.skills.append({'skill': frost_trap,'name':'Frost Trap','key':0,'level':10,'cooldown':1,'last_used':0,'cooldown_mod':1.0})

    
    def gain_xp(self, amount, game=None):
        self.xp += amount
        leveled = False
        levels_gained = 0

        _EVOLVE_LEVELS = {10, 25, 40}
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            levels_gained += 1
            self.stat_points += 2
            self.skill_points += 1
            self.xp_to_next = int(self.xp_to_next * 1.3)
            if self.level % 2 == 0:
                self.gen_skill_points = getattr(self, 'gen_skill_points', 0) + 1
            _FORM_POINT_GRANTS = {5: 3, 10: 2, 15: 5, 20: 5}
            if self.class_name == 'Druid' and self.level in _FORM_POINT_GRANTS:
                self.form_points += _FORM_POINT_GRANTS[self.level]

            # Apply class growth
            growth = CLASS_STAT_GROWTH.get(self.class_name, {})
            for stat, value in growth.items():
                setattr(self, stat, getattr(self, stat) + value)

            # Check soulbound evolution at EVERY level inside the loop so that
            # jumping past a milestone (e.g. 9→11) never skips the evolution.
            if self.level in _EVOLVE_LEVELS and self.level > self.last_soulbound_upgrade_level:
                self.upgrade_soulbound_items()
                self.last_soulbound_upgrade_level = self.level

            leveled = True

        # Update player stats after leveling
        if leveled:
            self.update_stats()
            self.unlock_skills()
            # last_soulbound_upgrade_level is already maintained inside the loop above

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
        # Do NOT modify unlocked_skills while in Wild Shape — form skills are active
        if getattr(self, 'wild_shape_form', None):
            return
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
        # Register general-tree active skills (e.g. Analysis) when tree-unlocked
        _general_active_map = {
            'Analysis': {'skill': None, 'name': 'Analysis', 'key': 0, 'level': 1,
                         'cooldown': 1.0, 'last_used': 0, 'cooldown_mod': 1.0},
        }
        for gname, gsk_template in _general_active_map.items():
            if gname in self.tree_unlocked:
                already = any(s['name'] == gname for s in self.unlocked_skills)
                if not already:
                    import types
                    # Resolve the actual function from self.skills or build a stub
                    fn = next((s['skill'] for s in self.skills if s['name'] == gname), None)
                    if fn is None:
                        def _analysis_fn(player, game, _n=gname):
                            if not game.room.enemies:
                                return
                            target = min(game.room.enemies,
                                         key=lambda e: math.hypot(e.x - player.x, e.y - player.y))
                            skill_names = [s.get('name', '?') for s in getattr(target, 'skills', [])]
                            skills_text = '  |  '.join(skill_names) if skill_names else 'None'
                            lines = [
                                f"[ {target.name} ]",
                                f"HP {int(target.hp)}/{int(target.max_hp)}   ATK {getattr(target,'atk','?')}",
                                f"Skills: {skills_text}",
                            ]
                            if not hasattr(game, '_analysis_displays'):
                                game._analysis_displays = []
                            game._analysis_displays.append({
                                'target': target,
                                'lines':  lines,
                                'until':  time.time() + 4.0,
                            })
                        fn = _analysis_fn
                    new_sk = dict(gsk_template)
                    new_sk['skill'] = fn
                    self.unlocked_skills.append(new_sk)
                    self.skills.append(new_sk)

    def get_tree_node(self, skill_name):
        """Return the skill tree node dict for a skill name (class tree first, then general)."""
        for node in SKILL_TREES.get(self.class_name, []):
            if node['name'] == skill_name:
                return node
        for node in GENERAL_SKILL_TREE:
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
        # Check level requirement
        level_req = node.get('level_req', 0)
        if self.level < level_req:
            return False, f"Requires Level {level_req} (you are Level {self.level})."
        # Check prerequisites are in tree_unlocked
        # Special case: Magnetic Field chain — previous tier is removed on upgrade,
        # so treat "had previous tier" as satisfied if we're in the chain
        _MF_CHAIN = ['Magnetic Field I', 'Magnetic Field II', 'Magnetic Field III']
        unlocked_set = getattr(self, 'tree_unlocked', set())
        for prereq in node['prereq']:
            if prereq in unlocked_set:
                continue
            # MF upgrade: prereq was consumed (removed) when a later tier was already unlocked
            if prereq in _MF_CHAIN and skill_name in _MF_CHAIN:
                prereq_idx = _MF_CHAIN.index(prereq)
                skill_idx  = _MF_CHAIN.index(skill_name)
                # Allow only if the previous tier was consumed (already upgraded past it)
                already_has_later = any(t in unlocked_set for t in _MF_CHAIN[prereq_idx:skill_idx])
                if already_has_later:
                    continue
            return False, f"Requires: {prereq}"
        # Check correct point pool
        _is_general = any(n['name'] == skill_name for n in GENERAL_SKILL_TREE)
        if _is_general:
            if getattr(self, 'gen_skill_points', 0) < node['cost']:
                return False, f"Need {node['cost']} General SP (have {getattr(self, 'gen_skill_points', 0)})."
        else:
            if self.skill_points < node['cost']:
                return False, f"Need {node['cost']} SP (have {self.skill_points})."
        return True, ""

    def unlock_tree_skill(self, skill_name):
        """Spend skill points to unlock a skill from the tree. Returns True on success."""
        ok, reason = self.can_unlock_tree_skill(skill_name)
        if not ok:
            return False
        node = self.get_tree_node(skill_name)
        _is_general = any(n['name'] == skill_name for n in GENERAL_SKILL_TREE)
        if _is_general:
            self.gen_skill_points = getattr(self, 'gen_skill_points', 0) - node['cost']
        else:
            self.skill_points -= node['cost']
        if not hasattr(self, 'tree_unlocked'):
            self.tree_unlocked = set()
        # Magnetic Field: remove the previous tier when the next is unlocked
        _MF_CHAIN = ['Magnetic Field I', 'Magnetic Field II', 'Magnetic Field III']
        if skill_name in _MF_CHAIN:
            idx = _MF_CHAIN.index(skill_name)
            if idx > 0:
                prev = _MF_CHAIN[idx - 1]
                self.tree_unlocked.discard(prev)
                self.passive_toggles.pop(prev, None)
        self.tree_unlocked.add(skill_name)
        # ── Pyromancer / Cryomancer subclass special handling ─────────────────
        if skill_name == 'Pyromancer':
            self._grant_mage_subclass('Pyromancer')
        elif skill_name == 'Cryomancer':
            self._grant_mage_subclass('Cryomancer')
        # For active skills, immediately add to unlocked_skills
        if node['type'] == 'active':
            self.unlock_skills()
        else:
            # Passive: recalculate stats
            self.update_stats()
        return True

    def _grant_mage_subclass(self, subclass):
        """Handle Pyromancer or Cryomancer subclass unlock.
        - Replaces Mana Bolt with Firebolt (Pyromancer) or Icebolt (Cryomancer)
        - Grants a new soulbound staff with Scorching Ray or Ray of Frost
        """
        is_pyro = (subclass == 'Pyromancer')
        # ── Replace Mana Bolt in unlocked_skills with the bolt variant ─────────
        replacement = 'Firebolt' if is_pyro else 'Icebolt'
        self.unlocked_skills = [
            sk for sk in self.unlocked_skills if sk.get('name') != 'Mana Bolt'
        ]
        # Ensure Firebolt / Icebolt are in tree_unlocked so unlock_skills picks them
        self.tree_unlocked.add(replacement)
        self.unlock_skills()

        # ── Build the new soulbound staff ──────────────────────────────────────
        if is_pyro:
            staff_name  = 'Staff of Flame'
            staff_stats = {'intelligence': 4, 'wisdom': 4, 'will': 3}
            staff_skill = ['Scorching Ray']
        else:
            staff_name  = 'Staff of Frost'
            staff_stats = {'intelligence': 4, 'wisdom': 4, 'will': 3}
            staff_skill = ['Ray of Frost']

        # Remove old Mage soulbound weapon (Novice Staff / Arcane Staff etc.)
        old_sb_weapon = None
        for item in list(self.inventory):
            if getattr(item, 'soulbound', False) and item.item_type == 'weapon':
                old_sb_weapon = item
                # Unequip if equipped
                if item in self.equipped_items:
                    self.equipped_items.remove(item)
                self.inventory.remove(item)
                break

        # Create and add new soulbound staff
        new_staff = InventoryItem(
            name=staff_name,
            item_type='weapon',
            rarity='Legendary',
            stats=staff_stats,
            skills=staff_skill,
            soulbound=True,
            weapon_type='staff',
            description=f'{"Scorching Ray" if is_pyro else "Ray of Frost"}: Channel a {"fire" if is_pyro else "frost"} beam toward your cursor.',
        )
        self.inventory.append(new_staff)
        self.soulbound_items = [it for it in self.inventory if getattr(it, 'soulbound', False)]
        self.update_stats()
        self.update_equipped_skills()
        self._inv_version = getattr(self, '_inv_version', 0) + 1
        self._soulbound_evolved = True
        print(f"⭐ Subclass {subclass} unlocked! Gained {staff_name} with {staff_skill[0]}!")

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
            "gen_skill_points": getattr(self, "gen_skill_points", 0),
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
            ],
            "shield_charges": getattr(self, "shield_charges", 30),
            "form_points": getattr(self, "form_points", 0),
            "unlocked_forms": list(getattr(self, "unlocked_forms", set())),
            "form_skill_levels": getattr(self, "form_skill_levels", {}),
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
        p.gen_skill_points = data.get('gen_skill_points', 0)
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
        # Re-populate skills
        p.populate_skills()
        p.active_skill_effects = data.get('active_skill_effects', {})
        # IMPORTANT: restore tree_unlocked BEFORE update_stats so that passive
        # shields (Mage Armour, Barkskin, Kinetic Shell) are included in the calc.
        p.tree_unlocked = set(data.get('tree_unlocked', []))
        p.update_stats()
        # Unlock the saved skills by name
        saved_skills = data.get('unlocked_skills',[])
        for sk in p.skills:
            if sk['name'] in saved_skills:
                p.unlocked_skills.append(sk)
        # Restore item-granted skills from equipped items (soulbound weapon etc.)
        # This must happen AFTER unlocked_skills is populated so keys can be restored below
        # Pass saved active-skill data so update_equipped_skills can seed keybinds/cooldown_mods
        # for item-granted skills that don't exist in unlocked_skills yet.
        _saved_active_for_load = {
            act['name']: act for act in data.get("active_skills", [])
        }
        # Pre-populate _saved_item_overrides on the player so update_equipped_skills picks them up
        # even though unlocked_skills is empty at this point.
        p._item_skill_overrides_seed = _saved_active_for_load
        p.update_equipped_skills()
        del p._item_skill_overrides_seed  # clean up temporary attribute
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
        p.shield_charges = data.get("shield_charges", 30)
        p.form_points = data.get("form_points", 0)
        p.unlocked_forms = set(data.get("unlocked_forms", []))
        p.form_skill_levels = data.get("form_skill_levels", {})
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

