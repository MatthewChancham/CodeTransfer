import random
import math
import time
from constants import *
from utils import clamp, distance
from items import Item
from entities import Particle

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
        # Bomb Creeper has no hand item — its body IS the bomb (drawn specially)
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

        # ── Stone Guardian: always return to guard home position ─────────────
        if getattr(self, '_is_guardian', False):
            self._shield_angle = math.atan2(player.y - self.y, player.x - self.x)
            hx, hy = self._home_x, self._home_y
            dist_home = distance((self.x, self.y), (hx, hy))
            dist_player = distance((self.x, self.y), (player.x, player.y))
            # Only leave home if player comes close
            if dist_player < 140:
                dx = player.x - self.x; dy = player.y - self.y
                d = math.hypot(dx, dy)
                if d > 0:
                    self.x += (dx/d) * self.spd
                    self.y += (dy/d) * self.spd
                for sk in self.skills:
                    if now - sk.get('last_used',0) >= sk.get('cooldown',1):
                        sk['skill'](self, game)
                        sk['last_used'] = now
            elif dist_home > 8:
                # Return to home
                dx = hx - self.x; dy = hy - self.y
                d = math.hypot(dx, dy)
                if d > 0:
                    self.x += (dx/d) * self.spd * 1.4
                    self.y += (dy/d) * self.spd * 1.4
            return
        # ── BOMB CREEPER: dedicated fast-dodging proximity-exploding AI ──────
        if getattr(self, '_is_bomb', False) and not getattr(self, '_already_exploded', False):
            d_player = distance((self.x, self.y), (player.x, player.y))

            # Explode if within contact range — no XP or coins (it ran into you)
            if d_player <= self.size + player.size + 20:
                bomb_explode(self, game)
                self.hp = 0
                if self in game.room.enemies:
                    # No reward — the bomb kamikaze'd, player didn't kill it
                    game.room.enemies.remove(self)
                return

            # Extremely aggressive dodge — sidestep player shots AND circle the player
            dodge_cooldown = getattr(self, '_bomb_dodge_cooldown', 0.18)
            last_dodge     = getattr(self, '_last_bomb_dodge', 0)
            can_dodge = (now - last_dodge) >= dodge_cooldown

            dodged = False
            if can_dodge:
                for proj in game.projectiles:
                    if proj.owner == "player":
                        pd = distance((self.x, self.y), (proj.x, proj.y))
                        if pd < 130:
                            # Dodge perpendicular, randomly to left or right
                            dodge_ang = proj.angle + random.choice([-math.pi/2, math.pi/2])
                            # Large dodge step
                            step = self.spd * 6
                            nx = clamp(self.x + math.cos(dodge_ang) * step, self.size, WINDOW_W - self.size)
                            ny = clamp(self.y + math.sin(dodge_ang) * step, self.size, WINDOW_H - self.size)
                            self.x, self.y = nx, ny
                            self._last_bomb_dodge = now
                            dodged = True
                            break

            # Chase player in a zigzag pattern when not dodging
            if not dodged:
                ang_to_player = math.atan2(player.y - self.y, player.x - self.x)
                # Add a sinusoidal weave to make it harder to hit
                weave = math.sin(now * 8.0 + id(self) * 0.001) * 0.6
                move_ang = ang_to_player + weave
                step = self.spd
                self.x = clamp(self.x + math.cos(move_ang) * step, self.size, WINDOW_W - self.size)
                self.y = clamp(self.y + math.sin(move_ang) * step, self.size, WINDOW_H - self.size)

            # (fuse ember particles are drawn directly on the sprite — no active particles)

            # Clamp to boundaries
            self.x = clamp(self.x, self.size, WINDOW_W - self.size)
            self.y = clamp(self.y, self.size, WINDOW_H - self.size)
            return   # skip generic enemy AI
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

        # ── DAZED state: enemy stumbles slowly, cannot attack ─────────────────
        if getattr(self, '_dazed_until', 0) > now:
            if not hasattr(self, '_daze_wander_target') or \
               distance((self.x, self.y), self._daze_wander_target) < 15:
                angle = random.uniform(0, 2 * math.pi)
                dist  = random.uniform(20, 60)
                self._daze_wander_target = (
                    clamp(self.x + math.cos(angle) * dist, self.size, WINDOW_W - self.size),
                    clamp(self.y + math.sin(angle) * dist, self.size, WINDOW_H - self.size),
                )
            dx = self._daze_wander_target[0] - self.x
            dy = self._daze_wander_target[1] - self.y
            d  = math.hypot(dx, dy)
            if d > 1:
                self.x += (dx / d) * self.spd * 0.3   # shuffle at 30% speed
                self.y += (dy / d) * self.spd * 0.3
            if self.item:
                self.item.update(self.x, self.y, player.x, player.y)
            return   # skip all normal AI while dazed

        # ── IMMOBILE (totems etc.) — must come before return-to-centre ─────
        if getattr(self, '_immobile', False):
            if self.item:
                self.item.update(self.x, self.y, player.x, player.y)
            for sk in self.skills:
                if now - sk.get('last_used', 0) >= sk.get('cooldown', 1):
                    sk['skill'](self, game)
                    sk['last_used'] = now
            return

        # ── RETURN TO CENTRE: player left the room — drift back for 4 s ─────
        if getattr(self, '_return_to_centre_until', 0) > now:
            _cx = getattr(self, '_return_centre_x', WINDOW_W // 2)
            _cy = getattr(self, '_return_centre_y', WINDOW_H // 2)
            _rdx = _cx - self.x; _rdy = _cy - self.y
            _rd  = math.hypot(_rdx, _rdy)
            if _rd > 4:
                self.x += (_rdx / _rd) * self.spd * 4.5
                self.y += (_rdy / _rd) * self.spd * 4.5
            if self.item:
                self.item.update(self.x, self.y, player.x, player.y)
            return
        # ── FORCED WANDER state: Invisibility skill — enemies wander aimlessly ──
        if getattr(self, '_forced_wander', False):
            if getattr(self, '_forced_wander_end', 0) <= now:
                self._forced_wander = False
            else:
                if not hasattr(self, '_invis_wander_target') or \
                   distance((self.x, self.y), self._invis_wander_target) < 20:
                    angle = random.uniform(0, 2 * math.pi)
                    dist  = random.uniform(50, 150)
                    self._invis_wander_target = (
                        clamp(self.x + math.cos(angle) * dist, self.size, WINDOW_W - self.size),
                        clamp(self.y + math.sin(angle) * dist, self.size, WINDOW_H - self.size),
                    )
                dx = self._invis_wander_target[0] - self.x
                dy = self._invis_wander_target[1] - self.y
                d  = math.hypot(dx, dy)
                if d > 1:
                    self.x += (dx / d) * self.spd * 0.5
                    self.y += (dy / d) * self.spd * 0.5
                if self.item:
                    self.item.update(self.x, self.y, player.x, player.y)
                return   # skip all normal AI while invisible
        # ── Entangling Roots: enemy is rooted ────────────────────────────────
        if getattr(self, '_entangled_until', 0) > now:
            self.spd = 0
            # Thorn tick damage
            if now - getattr(self, '_entangle_tick', 0) >= 0.5:
                game.damage_enemy(self, max(1, player.wis))
                self._entangle_tick = now
            if self.item:
                self.item.update(self.x, self.y, player.x, player.y)
            return
        elif getattr(self, '_entangled_until', 0) > 0:
            self.spd = getattr(self, '_entangled_spd', self.base_spd)
            self._entangled_until = 0

        # ── Grasping Vines: enemy is pinned and follows mouse ─────────────────
        if getattr(self, '_grasped', False):
            if now > getattr(self, '_grasped_until', 0):
                self._grasped = False
                self.spd = getattr(self, '_grasped_spd', self.base_spd)
            else:
                mx, my = game.get_mouse_world_pos()
                self.x = mx + random.uniform(-4, 4)
                self.y = my + random.uniform(-4, 4)
                if self.item:
                    self.item.update(self.x, self.y, player.x, player.y)
                return

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
            _just_entered = now - getattr(self, '_room_entered_at', 0) < 1.0
            if self.hp <= self.max_hp / 2 and not _just_entered:
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
        
        # --- attack summons on contact ---
        for s in list(game.summons):
            sd = distance((self.x, self.y), (s.x, s.y))
            if sd <= self.size + s.size + 4:
                last_shit = getattr(self, '_last_summon_hit', 0)
                if now - last_shit >= 0.6:
                    s.hp -= max(1, self.atk)
                    self._last_summon_hit = now
                    if s.hp <= 0:
                        if s in game.summons:
                            game.summons.remove(s)

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
        opening_size   = 150
        enemy_size     = self.size
        nudge          = 3   # pixels per frame — gradual, not instant

        door_cx   = WINDOW_W // 2
        door_cy   = WINDOW_H // 2
        door_half = opening_size // 2

        # Top wall
        if self.y - enemy_size < wall_thickness:
            if self.room_row == 0:
                self.y = min(self.y + nudge, wall_thickness + enemy_size)
            elif not (door_cx - door_half <= self.x <= door_cx + door_half):
                self.y = min(self.y + nudge, wall_thickness + enemy_size)

        # Bottom wall
        if self.y + enemy_size > WINDOW_H - wall_thickness:
            if self.room_row == ROOM_ROWS - 1:
                self.y = max(self.y - nudge, WINDOW_H - wall_thickness - enemy_size)
            elif not (door_cx - door_half <= self.x <= door_cx + door_half):
                self.y = max(self.y - nudge, WINDOW_H - wall_thickness - enemy_size)

        # Left wall
        if self.x - enemy_size < wall_thickness:
            if self.room_col == 0:
                self.x = min(self.x + nudge, wall_thickness + enemy_size)
            elif not (door_cy - door_half <= self.y <= door_cy + door_half):
                self.x = min(self.x + nudge, wall_thickness + enemy_size)

        # Right wall
        if self.x + enemy_size > WINDOW_W - wall_thickness:
            if self.room_col == ROOM_COLS - 1:
                self.x = max(self.x - nudge, WINDOW_W - wall_thickness - enemy_size)
            elif not (door_cy - door_half <= self.y <= door_cy + door_half):
                self.x = max(self.x - nudge, WINDOW_W - wall_thickness - enemy_size)

        # Update room tracking
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
            if self.level % 2 == 0:
                self.gen_skill_points = getattr(self, 'gen_skill_points', 0) + 1
            # Grant Form Points at milestone levels
            _FORM_POINT_GRANTS = {5: 3, 10: 2, 15: 5, 20: 5}
            if self.class_name == 'Druid' and self.level in _FORM_POINT_GRANTS:
                self.form_points = getattr(self, 'form_points', 0) + _FORM_POINT_GRANTS[self.level]

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
    """Shoot 3 consecutive fireballs in quick succession using a queued callback."""
    ang = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)

    def _shoot_one(gm, ex, ey, a):
        gm.spawn_projectile(ex, ey, a, 6, 2, 15, 'orange', enemy.atk * 2,
                            'enemy', ptype='fire_proj', stype='fire_proj')

    # Fire 3 shots: immediate, +0.18 s, +0.36 s
    _shoot_one(game, enemy.x, enemy.y, ang)
    if not hasattr(game, '_pending_callbacks'):
        game._pending_callbacks = []
    _t = time.time()
    for _delay in (0.18, 0.36):
        game._pending_callbacks.append((_t + _delay, _shoot_one, enemy.x, enemy.y, ang))

def ice_spikes(enemy, game):
    """Shoot 3 consecutive fireballs in quick succession using a queued callback."""
    ang = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)

    def _shoot_one(gm, ex, ey, a):
        gm.spawn_projectile(ex, ey, a, 6, 2, 15, 'orange', enemy.atk * 2,
                            'enemy', ptype='icicle', stype='icicle')

    # Fire 3 shots: immediate, +0.18 s, +0.36 s
    _shoot_one(game, enemy.x, enemy.y, ang)
    if not hasattr(game, '_pending_callbacks'):
        game._pending_callbacks = []
    _t = time.time()
    for _delay in (0.18, 0.36):
        game._pending_callbacks.append((_t + _delay, _shoot_one, enemy.x, enemy.y, ang))
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
    game.spawn_projectile(enemy.x, enemy.y, ang, 20, 2.5, 10, 'purple', enemy.atk * 2, 'enemy',ptype='icicle', stype="icicle")

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
    """Single grey animated crescent right beside the enemy — used by Swordman."""
    if not game.player:
        return
    arc_radius = 36
    ang = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)
    offset = enemy.size + 1
    ox = enemy.x + math.cos(ang) * offset
    oy = enemy.y + math.sin(ang) * offset
    blade = Particle(ox, oy, arc_radius, '#888888', life=0.38,
                     rtype='enemy_slash_dark', angle=ang, damage=enemy.atk * 3)
    blade.cx = ox
    blade.cy = oy
    # Pre-position to sweep start (-0.5 rad) so no stray dot on first frame
    blade._sweep_offset = -0.5
    blade._total_life   = blade.life
    blade._base_size    = arc_radius
    blade.x = ox + math.cos(ang - 0.5) * arc_radius * 0.9
    blade.y = oy + math.sin(ang - 0.5) * arc_radius * 0.9
    game.particles.append(blade)

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

def bomb_explode(enemy, game):
    """Bomb enemy detonation — big fire explosion, AoE damage to player."""
    if getattr(enemy, '_already_exploded', False):
        return
    enemy._already_exploded = True
    # Proximity-triggered explosions (bomb ran into player) give no reward.
    # Reward is only given when the player actively damaged the bomb to 0 hp.
    if not getattr(enemy, '_killed_by_player', False):
        enemy._no_reward = True

    ex, ey = enemy.x, enemy.y
    radius = 55   # smaller blast radius

    # Dense burst of small fire particles
    for _ in range(150):
        ang = random.uniform(0, 2 * math.pi)
        r   = random.uniform(0, radius * 1.2)
        px  = ex + math.cos(ang) * r
        py  = ey + math.sin(ang) * r
        sz  = random.uniform(3, 10)
        col = random.choice(['orange', 'red', '#ff6600', 'yellow', '#ff3300', 'white'])
        life = random.uniform(0.4, 1.0)
        p = Particle(px, py, sz, col, life=life, rtype='fire_puff', owner=None)
        game.particles.append(p)

    # A few large lingering flame blobs for visual impact
    for _ in range(25):
        ang = random.uniform(0, 2 * math.pi)
        r   = random.uniform(0, radius * 0.7)
        px  = ex + math.cos(ang) * r
        py  = ey + math.sin(ang) * r
        p2 = Particle(px, py, random.uniform(8, 18),
                      random.choice(['orange', 'red', '#ff6600']),
                      life=random.uniform(0.6, 1.4), rtype='flame', owner=None)
        game.particles.append(p2)

    # Expanding shockwave ring
    shockwave = Particle(ex, ey, 8, 'orange', life=0.4, rtype='shockwave', outline=True)
    shockwave.expansion_speed = 10
    shockwave.max_radius = radius
    shockwave.damage = enemy.atk * 4
    shockwave.cx = ex
    shockwave.cy = ey
    shockwave.owner = None   # visual only — damage handled below
    game.particles.append(shockwave)

    # Deal damage + knockback to player if inside radius
    d = distance((ex, ey), (game.player.x, game.player.y))
    if d <= radius:
        dmg = enemy.atk * 4 * max(0.2, 1.0 - d / radius)
        game.damage_player(dmg)
        if d > 1:
            kang = math.atan2(game.player.y - ey, game.player.x - ex)
            push = (radius - d) * 0.5
            game.player.x += math.cos(kang) * push
            game.player.y += math.sin(kang) * push

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
            lambda x, y: _make_bomb_creeper(x, y),
            lambda x, y: _make_bomb_creeper(x, y),
            lambda x, y: _make_bomb_creeper(x, y),
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
                    {"skill": ice_spikes, "name": "Ice Spike", "tags": ["magic"], "cooldown": 2.0, "last_used": 0},
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

def _make_bomb_creeper(x, y):
    """Factory for the Bomb Creeper enemy — explosive, fast, and dodges constantly."""
    e = Enemy("Bomb Creeper", 40, 16, 5.5, x, y, role="melee", skills=[])
    e.size = 11   # small — looks like a compact bomb
    e.base_spd = 5.5
    e._is_bomb       = True
    e._already_exploded = False
    e._bomb_dodge_cooldown = 0.18
    e._last_bomb_dodge     = 0
    return e
def _arcane_basic_arrow(enemy, game):
    ang = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)
    game.spawn_projectile(enemy.x, enemy.y, ang, 7, 4, 7, '#aa88ff', enemy.atk*1.5,
                          owner='enemy', stype='arrow')

def _arcane_multishot(enemy, game):
    ang = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)
    for spread in [-0.35, -0.12, 0.12, 0.35]:
        game.spawn_projectile(enemy.x, enemy.y, ang+spread, 6, 4, 7, '#aa88ff', enemy.atk,
                              owner='enemy', stype='arrow')

def _arcane_homing_orange(enemy, game):
    """Homing fireball arrow — explodes on hit."""
    p = game.spawn_projectile(enemy.x, enemy.y,
        math.atan2(game.player.y-enemy.y, game.player.x-enemy.x),
        4, 6, 10, 'orange', enemy.atk*3, owner='enemy', ptype='homing_fire', stype='arrow')
    if p:
        p._home_target = game.player
        p._home_strength = 0.08

def _arcane_homing_cyan(enemy, game):
    """Homing frost arrow — bursts into frost on hit."""
    p = game.spawn_projectile(enemy.x, enemy.y,
        math.atan2(game.player.y-enemy.y, game.player.x-enemy.x),
        4, 6, 10, 'cyan', enemy.atk*2.5, owner='enemy', ptype='homing_frost', stype='arrow')
    if p:
        p._home_target = game.player
        p._home_strength = 0.08

def _arcane_homing_pair(enemy, game):
    # Cyan fires immediately; orange fires 1s later via a pending attack flag
    _arcane_homing_cyan(enemy, game)
    enemy._pending_fire_arrow = time.time() + 1.0   # orange fires 1s later

def _arcane_homing_orange_slow(enemy, game):
    """Slower homing fireball arrow."""
    p = game.spawn_projectile(enemy.x, enemy.y,
        math.atan2(game.player.y-enemy.y, game.player.x-enemy.x),
        2.5, 7, 12, 'orange', enemy.atk*3.5, owner='enemy', ptype='homing_fire', stype='arrow')
    if p:
        p._home_target = game.player
        p._home_strength = 0.06

def _make_arcane_archer(x, y, scale=1.0):
    e = Enemy("Arcane Archer", int(120*scale), int(14*scale), 1.5, x, y, role="ranged",
              skills=[
                  {"skill": _arcane_basic_arrow,  "name": "Arcane Arrow", "tags": ["ranged"], "cooldown": 0.3,  "last_used": 0},
                  {"skill": _arcane_multishot,     "name": "Multishot",   "tags": ["ranged"], "cooldown": 3.5,  "last_used": 0},
                  {"skill": _arcane_homing_pair,   "name": "Homing Pair", "tags": ["ranged"], "cooldown": 7.0,  "last_used": 0},
              ])
    e.color = '#8844cc'
    e.size = 14
    e._freeze_immune = True   # arcane-enchanted — cannot be frozen
    return e

# ── Stone Guardian attack + factory ────────────────────────────────────────
def _guardian_slash(enemy, game):
    """Stone Guardian slash — animated sweeping grey crescent + heavy knockback."""
    if not game.player:
        return
    arc_radius = 55
    ang = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)
    # Spawn right beside the guardian's body edge
    offset = enemy.size + 6
    ox = enemy.x + math.cos(ang) * offset
    oy = enemy.y + math.sin(ang) * offset
    # Use enemy_slash_dark rtype so it gets the full sweep animation.
    # Grey colour distinguishes it visually from the purple boss version.
    blade = Particle(ox, oy, arc_radius, '#cccccc', life=0.42,
                     rtype='enemy_slash_dark', angle=ang, damage=enemy.atk * 4)
    blade.cx = ox
    blade.cy = oy
    blade._knockback = 90
    blade._knockback_src = (enemy.x, enemy.y)
    # Pre-position to sweep start so no stray dot on first frame
    blade._sweep_offset = -0.5
    blade._total_life   = blade.life
    blade._base_size    = arc_radius
    blade.x = ox + math.cos(ang - 0.5) * arc_radius * 0.9
    blade.y = oy + math.sin(ang - 0.5) * arc_radius * 0.9
    game.particles.append(blade)

def _make_stone_guardian(x, y, scale=1.0):
    e = Enemy("Stone Guardian", int(350*scale), int(18*scale), 1.2, x, y, role="melee",
              skills=[
                  {"skill": _guardian_slash, "name": "Stone Slash", "tags": ["melee"], "cooldown": 0.3, "last_used": 0},
              ])
    e.color = '#888880'
    e.size  = 20
    e._home_x = x
    e._home_y = y
    e._is_guardian = True
    e._shield_angle = 0.0
    e._shield_blocks = True
    # Sword item — carried on left side
    e.item = Item(x - 18, y, 'sword', '#aaaaaa', 18, owner=e)
    return e

# ── Ignismancer attack functions ────────────────────────────────────────────
def _ignismancer_lava_spray(enemy, game):
    """Pulsed lava stream — 3 rapid bursts of 5 droplets each, like a pressurised hose."""
    if not game.player:
        return

    def _spray_pulse(g, en):
        if not g.player or en not in g.room.enemies:
            return
        ang = math.atan2(g.player.y - en.y, g.player.x - en.x)
        for _ in range(5):
            spread = random.uniform(-0.12, 0.12)
            speed  = random.uniform(6.0, 8.5)
            size   = random.uniform(3, 6)
            g.spawn_projectile(
                en.x, en.y, ang + spread, speed, 3.0, size,
                '#ff4500', en.atk * 1.1, 'enemy',
                ptype='lava_proj', stype='lava_proj'
            )

    # Fire first burst immediately, then queue two more in rapid succession
    _spray_pulse(game, enemy)
    if not hasattr(game, '_pending_callbacks'):
        game._pending_callbacks = []
    t_now = time.time()
    game._pending_callbacks.append((t_now + 0.13, _spray_pulse, enemy))
    game._pending_callbacks.append((t_now + 0.26, _spray_pulse, enemy))


def _ignismancer_magma_bomb(enemy, game):
    """Launch a magma bomb that leaves a lava puddle on impact."""
    if not game.player:
        return
    ang = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)
    game.spawn_projectile(
        enemy.x, enemy.y, ang, 4, 5, 14,
        '#cc2200', enemy.atk * 2.5, 'enemy',
        ptype='magma_bomb', stype='magma_bomb'
    )


def _ignismancer_lava_wave(enemy, game):
    """Send a sine-wave-shaped lava front sweeping across the arena toward the player."""
    if not game.player:
        return
    ang      = math.atan2(game.player.y - enemy.y, game.player.x - enemy.x)
    perp_ang = ang + math.pi / 2
    count    = 22          # number of projectiles across the wave
    spread   = 320         # total lateral width in pixels
    speed    = 2.6         # slow and ominous
    amp      = 45          # sine-wave fore/aft amplitude in pixels
    for i in range(count):
        t       = i / (count - 1)          # 0.0 → 1.0 across the front
        lateral = (t - 0.5) * spread       # position along perpendicular axis
        sine_d  = math.sin(t * math.pi * 2.5) * amp   # wavy fore/aft offset
        ox = math.cos(perp_ang) * lateral + math.cos(ang) * sine_d
        oy = math.sin(perp_ang) * lateral + math.sin(ang) * sine_d
        game.spawn_projectile(
            enemy.x + ox, enemy.y + oy,
            ang, speed, 6, 12,
            '#cc3300', enemy.atk * 1.4, 'enemy',
            ptype='lava_proj', stype='lava_wave'
        )

def _make_ignismancer(x, y, scale=1.0):
    """Factory for the Ignismancer — fire/lava elemental that guards the volcano entrance."""
    e = Enemy("Ignismancer", int(500 * scale), int(20 * scale), 1.4, x, y, role="ranged",
              skills=[
                  {"skill": _ignismancer_lava_spray, "name": "Lava Spray",  "tags": ["ranged"], "cooldown": 1.2, "last_used": 0},
                  {"skill": _ignismancer_magma_bomb,  "name": "Magma Bomb",  "tags": ["ranged"], "cooldown": 3.5, "last_used": 0},
                  {"skill": _ignismancer_lava_wave,   "name": "Lava Wave",   "tags": ["ranged"], "cooldown": 5.0, "last_used": 0},
              ])
    e.color = '#ff4500'
    e.size  = 22
    # NOTE: _is_guardian intentionally NOT set — Ignismancer uses standard ranged AI
    # so it maintains distance from the player and continuously fires lava skills,
    # instead of guarding a fixed home position.
    e._shield_angle = 0.0
    e._shield_blocks = False
    e._is_ignismancer = True
    return e


def spawn_enemies_for_dungeon(room, dungeon_id, player_level, count=6):
    # Boss room (col 4) only gets the boss + totems from spawn_boss_for_room
    if room.col == 4:
        return
    # Treasure room (row 1, col 4) has no regular enemies
    if room.row == 1 and room.col == 4:
        return

    enemy_pools = create_enemy_types_by_dungeon()
    pool = enemy_pools.get(dungeon_id, [])

    scale_factor = 1 + player_level * 0.2

    def _spawn(et, x, y):
        e = et(x, y)
        e.max_hp = int(e.max_hp * scale_factor)
        e.hp = e.max_hp
        e.atk = int(e.atk * scale_factor)
        e.spd *= (1 + player_level * 0.02)
        room.enemies.append(e)

    # ── Dungeon 1 col==3: pre-boss room — Arcane Archer + Stone Guardian ──
    if dungeon_id == 1 and room.col == 3 and room.row == 0:
        # Stone Guardian blocks the right-wall door opening (leads to boss room col 4)
        # Door opening is centred at x=WINDOW_W-wall(20), y=WINDOW_H//2 => guard at x~W-60
        _gx = WINDOW_W - 65
        _gy = WINDOW_H // 2
        sg = _make_stone_guardian(_gx, _gy, scale_factor)
        sg._home_x = _gx
        sg._home_y = _gy
        room.enemies.append(sg)
        # Arcane Archer further back, same height
        aa = _make_arcane_archer(WINDOW_W - 160, WINDOW_H // 2 - 80, scale_factor)
        room.enemies.append(aa)
        room.enemies.append(aa)
        # Regular enemies fill the rest of the room
        for _ in range(4):
            if not pool: break
            et = random.choice(pool)
            _spawn(et, random.randint(80, WINDOW_W-80), random.randint(200, WINDOW_H-80))
        return

    # ── Dungeon 2 col==3: Volcano pre-boss room — IGNISMANCER ONLY, no other spawns ──
    if dungeon_id == 2 and room.col == 3 and room.row == 0:
        ignis = _make_ignismancer(WINDOW_W // 2, WINDOW_H // 2, scale_factor)
        ignis._home_x = WINDOW_W // 2
        ignis._home_y = WINDOW_H // 2
        room.enemies.append(ignis)
        # NO other enemies spawn in this room
        return

    # ── Dungeon 1: guarantee 1 of each type (swordman, spearman, archer) ──
    if dungeon_id == 1 and pool:
        for et in pool:           # one of each type first
            _spawn(et, random.randint(80, WINDOW_W-80), random.randint(80, WINDOW_H-80))
        extra = count - len(pool)  # then fill the rest randomly
        for _ in range(max(0, extra)):
            _spawn(random.choice(pool),
                   random.randint(80, WINDOW_W-80), random.randint(80, WINDOW_H-80))
        return

    # ── All other dungeons: random from pool ──
    for _ in range(count):
        if not pool: break
        et = random.choice(pool)
        _spawn(et, random.randint(50, WINDOW_W-50), random.randint(50, WINDOW_H-50))



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
            # ── Ignis the Burning — 4-phase fire boss ────────────────────────
            self.max_hp = 4000
            self.hp     = self.max_hp
            self._ignis_true_max_hp = 4000   # used for phase-4 5% calc
            self.atk    = 35
            self.size   = 22
            self.spd    = 1.8
            self.color  = '#ff4400'
            self.skills = []   # all driven by _update_ignis FSM

            # Phase tracking (1-4)
            self.ignis_phase          = 1
            self.ignis_phase4_start   = 0.0
            self.ignis_swirl_until    = 0.0

            # Per-skill last-used timers
            self.ignis_last_fireball  = 0.0
            self.ignis_last_breath    = 0.0
            self.ignis_last_flamepound= 0.0
            self.ignis_last_swirl     = 0.0

            # Phase-4 erratic bird flight
            self.ignis_bird_dir       = random.uniform(0, 2*math.pi)
            self.ignis_bird_turn_time = 0.0

            # Visual staff held by Ignis
            self._ignis_staff = Item(self.x, self.y, 'ignis_staff', '#ff2200', 28, owner=self)
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
        elif self.boss_type == 'GreatSword':
            # ---------- Dungeon 1 boss: The Iron Warden ----------
            self.max_hp  = 3500
            self.hp      = self.max_hp
            self.atk     = 55
            self.size    = 20          # smaller than default Boss
            self.spd     = 2.2
            self.color   = '#cc3333'
            self.skills  = []          # skills are driven by the FSM below

            # Weapon — greatsword sized for this boss (size multiplier applied at draw time)
            self.item = Item(self.x, self.y, 'greatsword', '#aaaaaa', 36, owner=self)

            # ── Finite-state machine state ────────────────────────────────────
            # States: 'idle','swing','charge','spin_swords','rapid_swing','phase3_spin'
            self.gs_state        = 'idle'
            self.gs_state_end    = 0.0     # when current timed state expires
            self.gs_last_swing   = 0.0
            self.gs_last_charge  = 0.0
            self.gs_last_spin    = 0.0
            self.gs_last_rapid   = 0.0
            self.gs_anim_busy    = False   # True while an animation is playing

            # Swing animation
            self.gs_swing_angle  = 0.0    # current sword rotation offset
            self.gs_swing_dir    = 1      # +1 / -1
            self.gs_swing_hit    = False  # did we already deal damage this swing?

            # Phase 3
            self.gs_p3_spin_angle = 0.0
            self.gs_p3_spinning   = True
            self.gs_p3_spin_until = 0.0
            self.gs_p3_pause_until= 0.0

            # Orbital swords (phase 2)
            self.gs_orbital_swords  = []  # list of dicts {angle, launched, proj_spawned}
            self.gs_orbital_active  = False
            self.gs_orbital_start   = 0.0
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
        if self.boss_type == 'GreatSword':
            self._update_greatsword(dt, game)
            return
        if self.boss_type == 'FireLord':
            self._update_ignis(dt, game)
            return

        # Generic boss movement / skills (all other bosses unchanged)
        player = game.player
        ang = math.atan2(player.y - self.y, player.x - self.x)
        self.x += math.cos(ang) * self.spd
        self.y += math.sin(ang) * self.spd

        now = time.time()
        for sk in self.skills:
            last_used = self.last_used_skill_time.get(sk['skill'], 0)
            if now - last_used >= sk['cooldown']:
                sk['skill'](game)
                self.last_used_skill_time[sk['skill']] = now
        self.x = clamp(self.x, self.size, WINDOW_W - self.size)
        self.y = clamp(self.y, self.size, WINDOW_H - self.size)

    # ─────────────────────────────────────────────────────────────────────────
    # IGNIS THE BURNING FSM
    # ─────────────────────────────────────────────────────────────────────────
    def _update_ignis(self, dt, game):
        now    = time.time()
        player = game.player

        # ── Phase 4 (phoenix bird) ────────────────────────────────────────────
        if self.ignis_phase == 4:
            self._update_ignis_phase4(dt, game, now, player)
            return

        # ── Phase transitions ─────────────────────────────────────────────────
        hp_frac = self.hp / max(self._ignis_true_max_hp, 1)
        if self.ignis_phase == 1 and hp_frac <= 0.66:
            self.ignis_phase = 2
            self.spd = 2.2
        elif self.ignis_phase == 2 and hp_frac <= 0.33:
            self.ignis_phase = 3
            self.spd = 2.5

        phase = self.ignis_phase

        # ── Movement — always chase player ────────────────────────────────────
        ang = math.atan2(player.y - self.y, player.x - self.x)
        self.x += math.cos(ang) * self.spd
        self.y += math.sin(ang) * self.spd
        self.x = clamp(self.x, self.size, WINDOW_W - self.size)
        self.y = clamp(self.y, self.size, WINDOW_H - self.size)

        # Keep staff glued to boss
        if hasattr(self, '_ignis_staff'):
            self._ignis_staff.x     = self.x
            self._ignis_staff.y     = self.y
            self._ignis_staff.angle = ang

        d_player = distance((self.x, self.y), (player.x, player.y))

        # ── Fireball / Meteor ─────────────────────────────────────────────────
        fb_cd = 2.5 if phase == 1 else (1.5 if phase == 2 else 1.1)
        if now - self.ignis_last_fireball >= fb_cd:
            self.ignis_last_fireball = now
            if phase < 3:
                self._ignis_fireball(game)
            else:
                self._ignis_meteor_fireball(game)

        # ── Fire Breath ───────────────────────────────────────────────────────
        # Phase 1: sustained short cone, player must be close.
        # Phase 2/3: sustained thin scorching ray, no distance requirement.
        if phase == 1:
            if not getattr(self, '_ignis_breath_until', 0) > now:
                if d_player <= 100 and now - self.ignis_last_breath >= 3.5:
                    self.ignis_last_breath   = now
                    self._ignis_breath_until = now + 2.0
            if getattr(self, '_ignis_breath_until', 0) > now:
                self._ignis_fire_breath(game, 95, dense=False)
        else:
            breath_cd = 3.0 if phase == 2 else 2.2
            if not getattr(self, '_ignis_breath_until', 0) > now:
                if now - self.ignis_last_breath >= breath_cd:
                    self.ignis_last_breath   = now
                    self._ignis_breath_until = now + 2.5
            if getattr(self, '_ignis_breath_until', 0) > now:
                self._ignis_fire_breath(game, 340 if phase == 2 else 420, dense=True)

        # ── Flame Ground Pound (phase 2+) ─────────────────────────────────────
        if phase >= 2 and d_player <= 130 and now - self.ignis_last_flamepound >= 5.0:
            self.ignis_last_flamepound = now
            self._ignis_flame_pound(game, player)

        # ── Phase-3 dense flame swirl (phase 3+) ─────────────────────────────
        if phase >= 3:
            if now - self.ignis_last_swirl >= 6.0:
                self.ignis_last_swirl  = now
                self.ignis_swirl_until = now + 3.5
            if now < self.ignis_swirl_until:
                # Inner ring (original behaviour)
                for _si in range(5):
                    _sa = (now * 3.0 + _si * 1.257) % (2 * math.pi)
                    _sr = self.size + 28 + random.uniform(-6, 6)
                    game.spawn_particle(
                        self.x + math.cos(_sa) * _sr,
                        self.y + math.sin(_sa) * _sr,
                        random.uniform(5, 12),
                        random.choice(['#ff2200','#ff6600','#ff9900','#ffcc00']),
                        life=random.uniform(0.25, 0.55),
                        rtype='flame', owner='enemy')
                # Mid ring — slightly further out, counter-rotating
                for _si in range(5):
                    _sa = -(now * 2.2 + _si * 1.257) % (2 * math.pi)
                    _sr = self.size + 58 + random.uniform(-6, 6)
                    game.spawn_particle(
                        self.x + math.cos(_sa) * _sr,
                        self.y + math.sin(_sa) * _sr,
                        random.uniform(5, 11),
                        random.choice(['#ff2200','#ff6600','#ff9900','#ffcc00']),
                        life=random.uniform(0.25, 0.5),
                        rtype='flame', owner='enemy')
                # Outer ring — furthest, slower
                for _si in range(4):
                    _sa = (now * 1.6 + _si * 1.571) % (2 * math.pi)
                    _sr = self.size + 90 + random.uniform(-8, 8)
                    game.spawn_particle(
                        self.x + math.cos(_sa) * _sr,
                        self.y + math.sin(_sa) * _sr,
                        random.uniform(4, 10),
                        random.choice(['#ff4400','#ff7700','#ffaa00']),
                        life=random.uniform(0.2, 0.45),
                        rtype='flame', owner='enemy')

    def _update_ignis_phase4(self, dt, game, now, player):
        """Phoenix-bird form: small, fast, erratic for 10 s then revives."""
        elapsed = now - self.ignis_phase4_start

        # ── Auto-revive after 10 s if still alive ────────────────────────────
        if elapsed >= 10.0:
            self.ignis_phase          = 1
            self.hp                   = self._ignis_true_max_hp
            self.size                 = 22
            self.spd                  = 1.8
            self.color                = '#ff4400'
            self.ignis_last_fireball  = now
            self.ignis_last_breath    = now
            self.ignis_last_flamepound= now
            self.ignis_last_swirl     = now
            return

        # Flee directly away from player, slight wobble
        _flee_ang = math.atan2(self.y - player.y, self.x - player.x)
        if now >= self.ignis_bird_turn_time:
            self.ignis_bird_dir       = _flee_ang + random.uniform(-0.4, 0.4)
            self.ignis_bird_turn_time = now + random.uniform(0.15, 0.35)

        bird_spd = 4.5
        self.x += math.cos(self.ignis_bird_dir) * bird_spd
        self.y += math.sin(self.ignis_bird_dir) * bird_spd
        self.x  = clamp(self.x, self.size, WINDOW_W - self.size)
        self.y  = clamp(self.y, self.size, WINDOW_H - self.size)

        # Trail fire particles
        if random.random() < 0.5:
            game.spawn_particle(self.x, self.y,
                                random.uniform(3, 7),
                                random.choice(['#ff4400','#ff8800','#ffcc00']),
                                life=random.uniform(0.15, 0.4),
                                rtype='flame', owner='enemy')

    # ── Ignis skill: normal fireball spread ───────────────────────────────────
    def _ignis_fireball(self, game):
        player = game.player
        ang = math.atan2(player.y - self.y, player.x - self.x)
        for delta in (-0.22, 0.0, 0.22):
            game.spawn_projectile(self.x, self.y, ang + delta,
                                  6, 3, 10, '#ff4400',
                                  self.atk * 8, 'enemy',
                                  ptype='fire_proj', stype='fire_proj')

    # ── Ignis skill: phase-3 meteor fireball (slow, explodes near player) ────
    def _ignis_meteor_fireball(self, game):
        player = game.player
        ang = math.atan2(player.y - self.y, player.x - self.x)
        proj = game.spawn_projectile(self.x, self.y, ang,
                                     7, 8, 16, '#cc2200',
                                     self.atk * 18, 'enemy',
                                     ptype='ignis_meteor', stype='fire_proj')
        if proj:
            proj._ignis_owner   = self
            proj._explode_range = 75
            proj._trail         = True   # draw fire trail each frame

    # ── Ignis skill: fire breath ─────────────────────────────────────────────
    def _ignis_fire_breath(self, game, breath_range, dense=False):
        """Phase 1 (dense=False): sustained short wide cone toward player.
        Phase 2/3 (dense=True): thin scorching-ray beam, long range, no spread.
        Called every frame while the breath channel is active.
        """
        player = game.player
        ang    = math.atan2(player.y - self.y, player.x - self.x)

        if not dense:
            # ── Phase 1: short wide cone ──────────────────────────────────────
            steps   = max(1, int(breath_range / 16))
            spreads = (-0.28, -0.14, 0.0, 0.14, 0.28)
            for step in range(1, steps + 1):
                for spread in spreads:
                    fa = ang + spread + random.uniform(-0.06, 0.06)
                    fd = step * 16 + random.uniform(-5, 5)
                    game.spawn_particle(
                        self.x + math.cos(fa) * fd,
                        self.y + math.sin(fa) * fd,
                        random.uniform(5, 11),
                        random.choice(['#ff2200','#ff4400','#ff6600','#ff8800','#ffaa00']),
                        life=random.uniform(0.18, 0.42),
                        rtype='flame', owner='enemy')
            # Damage player if in cone
            if distance((self.x, self.y), (player.x, player.y)) <= breath_range:
                pa   = math.atan2(player.y - self.y, player.x - self.x)
                diff = abs((pa - ang + math.pi) % (2*math.pi) - math.pi)
                if diff < 0.55:
                    game.damage_player(self.atk * 1.2)
        else:
            # ── Phase 2/3: scorching ray — random scatter, no dotted gaps ──
            perp_ang = ang + math.pi / 2
            for _ in range(10):
                _cd  = random.uniform(0, breath_range)
                _off = random.uniform(-4, 4)
                col  = random.choice(['#ff4400','#ff6600','#ffaa00','#ffff44','#ffffff'])
                game.spawn_particle(
                    self.x + math.cos(ang) * _cd + math.cos(perp_ang) * _off,
                    self.y + math.sin(ang) * _cd + math.sin(perp_ang) * _off,
                    random.uniform(4, 9), col,
                    life=random.uniform(0.12, 0.26),
                    rtype='flame', owner='enemy')
            # Damage player if inside the narrow beam
            if distance((self.x, self.y), (player.x, player.y)) <= breath_range:
                pa   = math.atan2(player.y - self.y, player.x - self.x)
                diff = abs((pa - ang + math.pi) % (2*math.pi) - math.pi)
                if diff < 0.18:
                    game.damage_player(self.atk * 2.2)

    # ── Ignis skill: flame ground pound — AoE flame + player knockback ───────
    def _ignis_flame_pound(self, game, player):
        # Expanding ring of flame particles
        for _fp in range(40):
            _fa = random.uniform(0, 2 * math.pi)
            _fr = random.uniform(20, 130)
            game.spawn_particle(
                self.x + math.cos(_fa) * _fr,
                self.y + math.sin(_fa) * _fr,
                random.uniform(5, 13),
                random.choice(['#ff2200','#ff5500','#ff8800','#ffcc00']),
                life=random.uniform(0.3, 0.8),
                rtype='flame', owner='enemy')
        # Shockwave ring visual
        sw = Particle(self.x, self.y, size=20, color='#ff5500', life=0.45,
                      rtype='shockwave', outline=True)
        sw.expansion_speed = 10
        sw.max_radius      = 130
        sw.damage          = 0
        game.particles.append(sw)
        # Knockback player if in range
        d = distance((self.x, self.y), (player.x, player.y))
        if d < 130:
            game.damage_player(self.atk * 3)
            kb_ang  = math.atan2(player.y - self.y, player.x - self.x)
            push    = (130 - d) * 1.2
            player.x += math.cos(kb_ang) * push
            player.y += math.sin(kb_ang) * push

    # ─────────────────────────────────────────────────────────────────────────
    # GREATSWORD BOSS FSM
    # ─────────────────────────────────────────────────────────────────────────
    def _update_greatsword(self, dt, game):
        player = game.player
        now    = time.time()
        hp_frac = self.hp / self.max_hp

        # ── Always keep greatsword item positioned on boss ────────────────────
        if self.item:
            aim_x = player.x
            aim_y = player.y
            self.item.x = self.x
            self.item.y = self.y
            base_angle = math.atan2(aim_y - self.y, aim_x - self.x)
            # Apply swing offset during animation
            self.item.angle = base_angle + self.gs_swing_angle

        # ── Phase 3 (≤15% HP) — no damage taken, endless spin with 8s cycles ─
        if hp_frac <= 0.15:
            self._gs_phase3(dt, game, now, player)
            return

        # ── Resolve ongoing timed state ───────────────────────────────────────
        if self.gs_state == 'swing':
            self._gs_do_swing(dt, game, now, player)
            return

        if self.gs_state == 'charge':
            self._gs_do_charge(dt, game, now, player)
            return

        if self.gs_state == 'rapid_swing':
            self._gs_do_rapid_swing(dt, game, now, player)
            return

        # ── Idle: move toward player ──────────────────────────────────────────
        d = distance((self.x, self.y), (player.x, player.y))
        ang = math.atan2(player.y - self.y, player.x - self.x)
        if d > 60:
            self.x += math.cos(ang) * self.spd
            self.y += math.sin(ang) * self.spd

        self.x = clamp(self.x, self.size, WINDOW_W - self.size)
        self.y = clamp(self.y, self.size, WINDOW_H - self.size)

        # ── Orbital swords (phase 2 passive) ─────────────────────────────────
        if hp_frac <= 0.60:
            self._gs_orbital_update(dt, game, now, player)

        # ── Decide next attack (only when not animating) ──────────────────────
        if self.gs_anim_busy:
            return

        # Phase 1 & 2 attacks
        swing_cd  = 2.8
        charge_cd = 5.5
        rapid_cd  = 7.0   # phase 2 only

        # Swing — close range
        if d < 200 and now - self.gs_last_swing >= swing_cd:
            self._start_swing(now, player)
            return

        # Charge — when player is far
        if d >= 200 and now - self.gs_last_charge >= charge_cd:
            self._start_charge(now, player)
            return

        # Rapid swing barrage (phase 2 only)
        if hp_frac <= 0.60 and now - self.gs_last_rapid >= rapid_cd:
            self._start_rapid_swing(now, player)
            return

        # Summon orbital swords (phase 2 only, every 12s)
        if hp_frac <= 0.60 and not self.gs_orbital_active and \
                now - self.gs_last_spin >= 12.0:
            self._start_orbital(now)

    # ── Swing ────────────────────────────────────────────────────────────────
    def _start_swing(self, now, player):
        self.gs_state      = 'swing'
        self.gs_anim_busy  = True
        self.gs_last_swing = now
        self.gs_swing_dir  = 1
        self.gs_swing_angle = -1.4    # start left of center
        self.gs_swing_hit   = False
        self.gs_state_end   = now + 0.55

    def _gs_do_swing(self, dt, game, now, player):
        sweep_speed = 5.5   # radians per second
        self.gs_swing_angle += sweep_speed * dt * self.gs_swing_dir

        # Greatsword reach: boss size + blade length (size*3.8) + forward offset (size*0.8)
        sword_reach = self.size + self.size * 3.8 + self.size * 0.8   # ≈ 220 px at size=40

        # Hit detection window (mid-arc, angle between -0.3 and +1.0)
        if not self.gs_swing_hit and -0.3 <= self.gs_swing_angle <= 1.0:
            # Check if player is within the swept arc using sword reach
            d = distance((self.x, self.y), (game.player.x, game.player.y))
            if d < sword_reach:
                ang_to_player = math.atan2(game.player.y - self.y, game.player.x - self.x)
                base_ang      = math.atan2(game.player.y - self.y, game.player.x - self.x)
                # Player is within reach — apply hefty damage
                game.damage_player(self.atk * 5.0)
                self.gs_swing_hit = True
            # Delete player projectiles caught in the swing sweep
            for proj in list(game.projectiles):
                if proj.owner in ('player', 'summon'):
                    if distance((self.x, self.y), (proj.x, proj.y)) < sword_reach + 20:
                        game.projectiles.remove(proj)

        # End of swing
        if now >= self.gs_state_end:
            self.gs_swing_angle = 0.0
            self.gs_state = 'idle'
            self.gs_anim_busy = False

    # ── Charge ───────────────────────────────────────────────────────────────
    def _start_charge(self, now, player):
        self.gs_state       = 'charge'
        self.gs_anim_busy   = True
        self.gs_last_charge = now
        ang = math.atan2(player.y - self.y, player.x - self.x)
        self.gs_charge_vx   = math.cos(ang) * 26    # much faster
        self.gs_charge_vy   = math.sin(ang) * 26
        self.gs_state_end   = now + 0.85             # longer duration = further travel
        self.gs_charge_hit  = False

    def _gs_do_charge(self, dt, game, now, player):
        self.x += self.gs_charge_vx
        self.y += self.gs_charge_vy
        self.x = clamp(self.x, self.size, WINDOW_W - self.size)
        self.y = clamp(self.y, self.size, WINDOW_H - self.size)

        if not self.gs_charge_hit:
            d = distance((self.x, self.y), (player.x, player.y))
            if d < self.size + player.size + 40:   # wider hit window
                ang = math.atan2(player.y - self.y, player.x - self.x)
                player.x += math.cos(ang) * 200
                player.y += math.sin(ang) * 200
                player.x = clamp(player.x, player.size, WINDOW_W - player.size)
                player.y = clamp(player.y, player.size, WINDOW_H - player.size)
                game.damage_player(self.atk * 3.5)
                self.gs_charge_hit = True

        if now >= self.gs_state_end:
            self.gs_state = 'idle'
            self.gs_anim_busy = False

    # ── Rapid swing (phase 2) ────────────────────────────────────────────────
    def _start_rapid_swing(self, now, player):
        self.gs_state       = 'rapid_swing'
        self.gs_anim_busy   = True
        self.gs_last_rapid  = now
        self.gs_swing_angle = -math.pi / 2
        self.gs_rapid_stage = 0       # counts rotations
        self.gs_state_end   = now + 2.4
        self.gs_rapid_next  = now + 0.0

    def _gs_do_rapid_swing(self, dt, game, now, player):
        sweep_speed = 18.0   # very fast spin
        self.gs_swing_angle += sweep_speed * dt

        # Fire 3 large grey slashes per rotation (every 120°)
        threshold = math.pi * 2 / 3
        while self.gs_swing_angle >= self.gs_rapid_stage * threshold + threshold:
            self.gs_rapid_stage += 1
            if self.gs_rapid_stage > 9:   # max 9 bursts in 2.4s
                break
            ang = math.atan2(player.y - self.y, player.x - self.x)
            # 3 slashes per burst — each gets a random tilt ±90° around the aim direction
            # so they look like tumbling blades, not a uniform soundwave pattern
            for _ in range(3):
                game.spawn_projectile(self.x, self.y, ang, 13, 3.0, 30,
                                      '#888888', self.atk * 2.0, 'enemy',
                                      stype='slash')
                p2 = game.projectiles[-1]

                # REAL spread (movement direction)
                spread = math.radians(20)   # total 10° cone (±5°)
                p2.angle = ang + random.uniform(-spread * 0.5, spread * 0.5)

                # VISUAL spread (appearance only)
                p2._visual_angle = ang + random.uniform(-math.radians(15), math.radians(15))


        if now >= self.gs_state_end:
            self.gs_swing_angle = 0.0
            self.gs_state = 'idle'
            self.gs_anim_busy = False

    # ── Orbital swords (phase 2) ──────────────────────────────────────────────
    def _start_orbital(self, now):
        self.gs_orbital_active = True
        self.gs_last_spin      = now
        self.gs_orbital_start  = now
        angles = [0, 2*math.pi/3, 4*math.pi/3]
        self.gs_orbital_swords = [{'angle': a, 'launched': False} for a in angles]

    ORBITAL_RADIUS = 130   # how far swords orbit from the boss

    def _gs_orbital_update(self, dt, game, now, player):
        if not self.gs_orbital_active:
            return
        elapsed = now - self.gs_orbital_start
        spin_speed = 2.4   # rad/s

        for sw in self.gs_orbital_swords:
            sw['angle'] += spin_speed * dt
            if elapsed >= 2.8 and not sw['launched']:
                # Launch from current orbital position, aimed at player
                ox = self.x + math.cos(sw['angle']) * self.ORBITAL_RADIUS
                oy = self.y + math.sin(sw['angle']) * self.ORBITAL_RADIUS
                ang = math.atan2(player.y - oy, player.x - ox)
                proj = game.spawn_projectile(
                    ox, oy, ang, 16, 4, 24,
                    '#888888', self.atk * 2.5, 'enemy',
                    stype='greatsword_proj'
                )
                if proj:
                    proj._gs_angle = sw['angle']   # store spin angle for drawing
                sw['launched'] = True

        if all(s['launched'] for s in self.gs_orbital_swords):
            self.gs_orbital_active = False
            self.gs_orbital_swords = []

    # ── Phase 3 ───────────────────────────────────────────────────────────────
    def _gs_phase3(self, dt, game, now, player):
        """Endless spin, immune to damage. Pauses 1.5s every 8s."""
        # Ensure we don't accidentally take damage — handled in damage_enemy override
        if not hasattr(self, '_gs_p3_init'):
            self._gs_p3_init     = True
            self.gs_p3_spinning  = True
            self.gs_p3_spin_until  = now + 8.0
            self.gs_p3_pause_until = 0.0
            self.gs_swing_angle  = 0.0

        if now < getattr(self, 'gs_p3_pause_until', 0):
            # Paused — drift slowly toward player
            d = distance((self.x, self.y), (player.x, player.y))
            if d > 50:
                ang = math.atan2(player.y - self.y, player.x - self.x)
                self.x += math.cos(ang) * 0.8
                self.y += math.sin(ang) * 0.8
            return

        # Spinning
        self.gs_swing_angle += 18.0 * dt   # very fast spin (was 9.0)

        # Delete any player projectiles that touch the boss
        for proj in list(game.projectiles):
            if proj.owner in ('player', 'summon'):
                if distance((self.x, self.y), (proj.x, proj.y)) < self.size + proj.radius + 40:
                    game.projectiles.remove(proj)

        # Hit player on contact — high phase-3 damage
        if distance((self.x, self.y), (player.x, player.y)) < self.size + player.size + 30:
            game.damage_player(self.atk * 2.5)   # was 0.8

        # Move toward player — much faster
        ang = math.atan2(player.y - self.y, player.x - self.x)
        self.x += math.cos(ang) * self.spd * 2.0   # was 0.7
        self.y += math.sin(ang) * self.spd * 2.0
        self.x = clamp(self.x, self.size, WINDOW_W - self.size)
        self.y = clamp(self.y, self.size, WINDOW_H - self.size)

        # Cycle: 8s spin → 1.5s pause → repeat
        if now >= getattr(self, 'gs_p3_spin_until', 0):
            self.gs_p3_pause_until = now + 1.5
            self.gs_p3_spin_until  = now + 1.5 + 8.0
        
def spawn_boss_for_room(room, dungeon_id):
    boss_x, boss_y = WINDOW_W//2, WINDOW_H//2
    boss_types = {
        1: 'GreatSword',
        2: 'FireLord',
        3: 'IceGiant',
        4: 'ShadowWraith'
    }
    boss_name = ('Valon the Warden'  if dungeon_id == 1 else
                 'Ignis the Burning' if dungeon_id == 2 else
                 f"Dungeon {dungeon_id} Boss")
    boss_type = boss_types.get(dungeon_id, 'Generic')
    boss = Boss(boss_name, boss_x, boss_y, boss_type)
    room.enemies.append(boss)

    # Dungeon 1 — spawn 4 immobile healer totems at corners (inset from walls)
    if dungeon_id == 1:
        margin = 90
        corners = [
            (margin,          margin),
            (WINDOW_W-margin, margin),
            (margin,          WINDOW_H-margin),
            (WINDOW_W-margin, WINDOW_H-margin),
        ]
        def make_healer_bolt(totem_ref, boss_ref):
            def healer_bolt(totem, game):
                if not boss_ref or boss_ref.hp <= 0:
                    return
                ang = math.atan2(boss_ref.y - totem.y, boss_ref.x - totem.x)
                proj = game.spawn_projectile(
                    totem.x, totem.y, ang,
                    3, 6, 7, '#44ff88',
                    0, 'enemy', stype='bolt1'
                )
                if proj:
                    proj.ptype    = 'boss_heal'
                    proj.heal_amt = boss_ref.max_hp * 0.015   # scales with boss max HP
                    proj.boss_ref = boss_ref
            return healer_bolt

        player_level = getattr(room, '_player_level_hint', 1)
        totem_hp = int(500 * (1.15 ** (player_level - 1)))

        for cx, cy in corners:
            totem = Enemy("Healer Totem", totem_hp, 0, 0, cx, cy, role="melee", skills=[])
            totem.base_spd      = 0
            totem.spd           = 0
            totem._immobile     = True
            totem._no_reward    = True   # flag: skip coins and XP on death
            totem.size          = 12
            totem.color         = '#22cc44'
            heal_fn = make_healer_bolt(totem, boss)
            totem.skills = [{"skill": heal_fn, "name": "Heal Bolt", "tags": ["support"],
                             "cooldown": 0.9, "last_used": 0}]
            room.enemies.append(totem)
