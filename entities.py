import random
import math
import time
from constants import *
from utils import clamp, distance, resolve_overlap
from items import InventoryItem, ConsumableItem, MAP_ITEM, SHOP_ITEMS, CONSUMABLE_SHOP_ITEMS

class Projectile:
    def __init__(self,x,y,angle,speed,life,radius,color,damage,owner='player', ptype='normal', stype='basic'):
        self.x=x; self.y=y; self.angle=angle; self.speed=speed;
        self.life=life; self.radius=radius; self.color=color; self.damage=damage; self.owner=owner
        self.ptype = ptype; self.stype = stype;self.spawn_time = time.time();
        self.stopped = False   # NEW FLAG
    def update(self,dt,game):
        # ── Homing projectiles: steer toward target ──────────────────────────
        if self.ptype in ('homing_fire', 'homing_frost') and hasattr(self, '_home_target'):
            _ht = self._home_target
            if _ht and hasattr(_ht, 'x'):
                _ha = math.atan2(_ht.y - self.y, _ht.x - self.x)
                # Smooth angular steering
                _diff = (_ha - self.angle + math.pi) % (2*math.pi) - math.pi
                self.angle += _diff * getattr(self, '_home_strength', 0.08)
        self.x += math.cos(self.angle)*self.speed
        self.y += math.sin(self.angle)*self.speed
        self.life -= dt

        # ── Ignis meteor: fire trail ──────────────────────────────────────────
        if self.ptype == 'ignis_meteor' and getattr(self, '_trail', False):
            for _ in range(3):
                _ta = self.angle + math.pi + random.uniform(-0.4, 0.4)
                _td = random.uniform(4, self.radius * 1.2)
                game.particles.append(Particle(
                    self.x + math.cos(_ta)*_td,
                    self.y + math.sin(_ta)*_td,
                    random.uniform(4, 9),
                    random.choice(['#ff2200','#ff5500','#ff8800','#ffcc00','orange']),
                    life=random.uniform(0.15, 0.35),
                    rtype='flame', owner=None))

        # ── Homing steering for arcane arrows ───────────────────────────────
        if self.ptype in ('homing_fire', 'homing_frost', 'player_homing_fire', 'player_homing_frost'):
            tgt = getattr(self, '_home_target', None)
            # Retarget if current target is dead or gone
            if tgt and hasattr(tgt, 'hp') and tgt.hp <= 0:
                tgt = None
                self._home_target = None
            if tgt is None and self.owner in ('player', 'summon') and game.room.enemies:
                # Retarget nearest living enemy
                living = [e for e in game.room.enemies if e.hp > 0]
                if living:
                    self._home_target = min(living,
                        key=lambda e: math.hypot(e.x-self.x, e.y-self.y))
                    tgt = self._home_target
            if tgt and hasattr(tgt, 'x'):
                _want = math.atan2(tgt.y - self.y, tgt.x - self.x)
                _diff = (_want - self.angle + math.pi) % (2*math.pi) - math.pi
                self.angle += _diff * getattr(self, '_home_strength', 0.08)
            # Trail particles
            trail_col = 'orange' if 'fire' in self.ptype else 'cyan'
            game.spawn_particle(self.x, self.y, random.uniform(3,7), trail_col,
                                life=0.25, rtype='flame' if 'fire' in self.ptype else 'frost')

        if self.ptype == 'firebolt':
            # Tight flame cluster around the bolt — no long trailing tail
            for _ in range(3):
                _ox = random.uniform(-4, 4)
                _oy = random.uniform(-4, 4)
                game.spawn_particle(self.x + _ox, self.y + _oy,
                                    random.uniform(2, 5),
                                    random.choice(['orange','red','yellow']),
                                    life=0.08, rtype='flame')

        if self.ptype == 'icebolt':
            # Tight frost cluster around the bolt — no long trailing tail
            for _ in range(3):
                _ox = random.uniform(-4, 4)
                _oy = random.uniform(-4, 4)
                game.spawn_particle(self.x + _ox, self.y + _oy,
                                    random.uniform(2, 5),
                                    random.choice(['cyan','white','#aaffff']),
                                    life=0.08, rtype='frost')

        if self.ptype == 'aqua_missile':
            # Gentle homing
            if game.room.enemies:
                _tgt = min(game.room.enemies, key=lambda e: math.hypot(e.x-self.x, e.y-self.y))
                _want = math.atan2(_tgt.y - self.y, _tgt.x - self.x)
                _diff = (_want - self.angle + math.pi) % (2*math.pi) - math.pi
                self.angle += _diff * 0.05
            # Spiral droplet trail
            self._spiral_t = getattr(self, '_spiral_t', 0.0) + 0.35
            _perp = self.angle + math.pi / 2
            _offset = math.sin(self._spiral_t) * 8
            game.spawn_particle(
                self.x + math.cos(_perp)*_offset,
                self.y + math.sin(_perp)*_offset,
                random.uniform(2, 5),
                random.choice(['#00aaff','#44ccff','white']),
                life=0.25, rtype='magic_burst')

        # ── Smoke bomb: explode on wall hit or life end ──────────────────────
        if self.ptype == 'smoke_bomb':
            hit_wall = (self.x<0 or self.x>WINDOW_W or self.y<0 or self.y>WINDOW_H)
            if self.life <= 0 or hit_wall:
                self._explode_smoke(game)
                self.life = 0
                return
        # ── Magma bomb: leave lava pool on wall hit or life expiry ────────────
        if self.ptype == 'magma_bomb':
            hit_wall = (self.x < 0 or self.x > WINDOW_W or self.y < 0 or self.y > WINDOW_H)
            if hit_wall or self.life <= 0:
                if not hasattr(game, 'lava_pools'):
                    game.lava_pools = []
                game.lava_pools.append(LavaPool(self.x, self.y, radius=40, damage=self.damage*0.5, duration=7.0))
                for _ in range(20):
                    ang2 = random.uniform(0, 2*math.pi)
                    r2   = random.uniform(0, 30)
                    game.spawn_particle(self.x+math.cos(ang2)*r2, self.y+math.sin(ang2)*r2,
                                        random.uniform(4,12),
                                        random.choice(['#ff4500','#cc2200','#ff6600','#ffaa00']),
                                        life=random.uniform(0.3,0.9), rtype='fire_puff')
                self.life = 0
                return
        if self.x<0 or self.x>WINDOW_W or self.y<0 or self.y>WINDOW_H: self.life=0; return
        if not self.stopped:
            self.x += math.cos(self.angle) * self.speed
            self.y += math.sin(self.angle) * self.speed
        # lifetime check
        if time.time() - self.spawn_time > self.life:
            self.alive = False

        # ── Enemy projectiles hit wolf / summons ──────────────────────────────
        if self.owner == 'enemy':
            for s in list(game.summons):
                if distance((self.x, self.y), (s.x, s.y)) <= self.radius + s.size:
                    s.hp -= self.damage
                    if s.hp <= 0 and s in game.summons:
                        game.summons.remove(s)
                    # Small hit flash
                    game.spawn_particle(self.x, self.y, 5, '#ff4444',
                                        life=0.15, rtype='magic_burst')
                    self.life = 0
                    return
        # Enemy icicle projectile hitting the player
        # Enemy icicle projectile hitting the player
        if self.owner == 'enemy' and self.ptype == 'icicle':
            if distance((self.x, self.y), (game.player.x, game.player.y)) <= self.radius + game.player.size:

                # Damage player using your existing system
                game.player.hp -= self.damage

                # Frost explosion AoE (same style as player icicle)
                _aoe_r = 80
                _ix, _iy = self.x, self.y

                for _ in range(22):
                    _fa = random.uniform(0, 2 * math.pi)
                    _fr = random.uniform(0, _aoe_r)

                    _fp = Particle(
                        _ix + math.cos(_fa) * _fr,
                        _iy + math.sin(_fa) * _fr,
                        random.randint(5, 11),
                        random.choice(['white','cyan','#aaffff','#00ddff']),
                        life=random.uniform(0.5, 1.1),
                        rtype='frost',
                        owner='enemy'
                    )
                    _fp._frozen_ids = set()
                    game.particles.append(_fp)

                # Remove projectile
                if self in game.projectiles:
                    game.projectiles.remove(self)

                return


        if self.owner == 'summon' or self.owner == 'player':
            for e in list(game.room.enemies):
                if distance((self.x,self.y),(e.x,e.y))<=self.radius+e.size:
                    # ── Stone Guardian shield: block projectiles from the front ──
                    if getattr(e, '_is_guardian', False) and getattr(e, '_shield_blocks', True):
                        _sa = getattr(e, '_shield_angle', 0)
                        _proj_ang = math.atan2(self.y - e.y, self.x - e.x)
                        _adiff = abs((_proj_ang - _sa + math.pi) % (2*math.pi) - math.pi)
                        if _adiff < math.pi * 0.45:   # ~80° frontal arc blocked
                            # Deflect — spark effect
                            for _ in range(8):
                                _sa2 = random.uniform(0, 2*math.pi)
                                game.spawn_particle(self.x+math.cos(_sa2)*6,
                                                    self.y+math.sin(_sa2)*6,
                                                    random.uniform(2,5), '#ccccff',
                                                    life=0.2, rtype='magic_burst')
                            self.life = 0
                            return
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

                    elif self.ptype == 'player_homing_fire':
                        # Flame explosion on enemy hit
                        game.damage_enemy(e, self.damage)
                        for _ in range(25):
                            _ang = random.uniform(0, 2*math.pi)
                            _r   = random.uniform(0, self.radius * 2.5)
                            game.spawn_particle(
                                self.x+math.cos(_ang)*_r, self.y+math.sin(_ang)*_r,
                                random.uniform(4,10),
                                random.choice(['orange','red','yellow','#ff6600']),
                                life=random.uniform(0.4,0.9), rtype='flame', owner=None)
                        self.life = 0; return

                    elif self.ptype == 'player_homing_frost':
                        # Frost burst on enemy hit
                        game.damage_enemy(e, self.damage)
                        for _ in range(20):
                            _ang = random.uniform(0, 2*math.pi)
                            _r   = random.uniform(0, self.radius * 2)
                            game.spawn_particle(
                                self.x+math.cos(_ang)*_r, self.y+math.sin(_ang)*_r,
                                random.uniform(3,9),
                                random.choice(['cyan','white','#aaffff','#00ddff']),
                                life=random.uniform(0.3,0.6), rtype='frost', owner=None)
                        self.life = 0; return

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

                    elif self.ptype == 'holyflame':
                        # Direct hit triggers AoE
                        if distance((self.x, self.y), (e.x, e.y)) <= e.size + self.radius:
                            _aoe_r = 70
                            _hf_cols = ['#ffdd00', '#ffffff', '#ffee55', '#ffffaa', '#ffcc00']
                            _daze_end = time.time() + 2.5
                            for _ae in list(game.room.enemies):
                                if distance((self.x, self.y), (_ae.x, _ae.y)) <= _aoe_r:
                                    game.damage_enemy(_ae, self.damage * 0.5)
                                    _ae._dazed_until = max(getattr(_ae, '_dazed_until', 0), _daze_end)
                            for _ in range(140):
                                ang2 = random.uniform(0, 2*math.pi)
                                r2   = random.uniform(0, _aoe_r)
                                _p   = Particle(self.x + math.cos(ang2)*r2,
                                                self.y + math.sin(ang2)*r2,
                                                random.uniform(6, 12),
                                                random.choice(_hf_cols),
                                                life=1, owner='player', rtype='holy_flame')
                                game.particles.append(_p)
                            if self in game.projectiles:
                                game.projectiles.remove(self)
                            return

                    elif self.ptype == 'blackflame':
                        if distance((self.x, self.y), (e.x, e.y)) <= e.size + self.radius:
                            _aoe_r = 70
                            _bf_cols = ['#330022', '#660033', '#990044', '#aa0055', '#cc0066']
                            for _ae in list(game.room.enemies):
                                if distance((self.x, self.y), (_ae.x, _ae.y)) <= _aoe_r:
                                    game.damage_enemy(_ae, self.damage)
                                    _now_bf = time.time()
                                    _ae._poison_tier  = max(getattr(_ae, '_poison_tier', 0), 1)
                                    _ae._poison_until = _now_bf + 5.0
                                    _ae._poison_dps   = _ae.max_hp * 0.02
                            for _ in range(140):
                                ang2 = random.uniform(0, 2*math.pi)
                                r2   = random.uniform(0, _aoe_r)
                                _p   = Particle(self.x + math.cos(ang2)*r2,
                                                self.y + math.sin(ang2)*r2,
                                                random.uniform(6, 12),
                                                random.choice(_bf_cols),
                                                life=1, owner='player', rtype='black_flame')
                                game.particles.append(_p)
                            if self in game.projectiles:
                                game.projectiles.remove(self)
                            return
                    if self.ptype == 'hydro_shot':
                        if distance((self.x, self.y), (e.x, e.y)) <= e.size + self.radius:
                            _aoe_r = 90
                            _water_cols = ['#0077cc','#00aaff','#44ccff','#99ddff','#ffffff']
                            _now_h = time.time()
                            game.damage_enemy(e, self.damage)
                            e._wet_tier  = min(5, max(getattr(e, '_wet_tier', 0), 1))
                            e._wet_until = _now_h + 10.0 + 2.0 * e._wet_tier
                            # Large burst — many small magic_burst particles radiating outward
                            for _ in range(280):
                                _a2 = random.uniform(0, 2*math.pi)
                                # Weighted to outer ring for burst feel
                                _r2 = _aoe_r * (0.3 + 0.7 * random.random()**0.5)
                                _wp = Particle(self.x + math.cos(_a2)*_r2,
                                               self.y + math.sin(_a2)*_r2,
                                               random.uniform(3, 8),
                                               random.choice(_water_cols),
                                               life=random.uniform(0.3, 0.9),
                                               owner='player', rtype='magic_burst')
                                game.particles.append(_wp)
                            # Single master puddle particle (handles both draw & wet tick)
                            _pp = Particle(self.x, self.y, _aoe_r,
                                           '#0077cc', life=6.0, owner='player', rtype='water_puddle')
                            _pp._puddle_x  = self.x
                            _pp._puddle_y  = self.y
                            _pp._puddle_r  = _aoe_r
                            _pp._next_tick = _now_h + 1.0
                            # Pre-generate irregular polygon points (lava-pool style)
                            _num_puddle_pts = random.randint(10, 14)
                            _pp._poly_angles = [(2*math.pi/_num_puddle_pts)*_pi2 + random.uniform(-0.25,0.25)
                                                for _pi2 in range(_num_puddle_pts)]
                            _pp._poly_radii  = [_aoe_r * random.uniform(0.55, 1.1)
                                                for _ in range(_num_puddle_pts)]
                            game.particles.append(_pp)
                            if self in game.projectiles:
                                game.projectiles.remove(self)
                            return
                    if self.ptype == 'firebolt':
                        for e in list(game.room.enemies):
                            if distance((self.x, self.y), (e.x, e.y)) <= e.size + self.radius:
                                game.damage_enemy(e, self.damage)
                                for _ in range(30):
                                    _a = random.uniform(0, 2*math.pi)
                                    _r = random.uniform(0, 35)
                                    game.particles.append(Particle(
                                        self.x + math.cos(_a)*_r, self.y + math.sin(_a)*_r,
                                        random.uniform(3, 8),
                                        random.choice(['orange','red','yellow','#ff6600']),
                                        life=random.uniform(0.3, 0.7), owner='player', rtype='flame'))
                                if self in game.projectiles: game.projectiles.remove(self)
                                return
                    if self.ptype == 'icebolt':
                        for e in list(game.room.enemies):
                            if distance((self.x, self.y), (e.x, e.y)) <= e.size + self.radius:
                                game.damage_enemy(e, self.damage)
                                e._frozen_until = max(getattr(e, '_frozen_until', 0), time.time() + 1.5)
                                for _ in range(30):
                                    _a = random.uniform(0, 2*math.pi)
                                    _r = random.uniform(0, 35)
                                    game.particles.append(Particle(
                                        self.x + math.cos(_a)*_r, self.y + math.sin(_a)*_r,
                                        random.uniform(3, 8),
                                        random.choice(['cyan','white','#aaffff','#00ddff']),
                                        life=random.uniform(0.3, 0.6), owner='player', rtype='frost'))
                                if self in game.projectiles: game.projectiles.remove(self)
                                return
                    if self.ptype == 'aqua_missile':
                        for e in list(game.room.enemies):
                            if distance((self.x, self.y), (e.x, e.y)) <= e.size + self.radius:
                                game.damage_enemy(e, self.damage)
                                e._wet_tier  = min(5, max(getattr(e, '_wet_tier', 0), 1))
                                e._wet_until = time.time() + 10.0 + 2.0 * e._wet_tier
                                for _ in range(70):
                                    _a = random.uniform(0, 2*math.pi)
                                    _r = 10 + 40 * random.random()**0.4   # weighted outer ring
                                    game.particles.append(Particle(
                                        self.x + math.cos(_a)*_r, self.y + math.sin(_a)*_r,
                                        random.uniform(3, 7),
                                        random.choice(['#00aaff','#44ccff','#99ddff','white','#aaeeff']),
                                        life=random.uniform(0.25, 0.7), owner='player', rtype='magic_burst'))
                                if self in game.projectiles: game.projectiles.remove(self)
                                return
                    if self.ptype == 'icicle':
                        for e in list(game.room.enemies):
                            if distance((self.x, self.y), (e.x, e.y)) <= e.size + self.radius:
                                # Damage only the directly hit enemy
                                game.damage_enemy(e, self.damage)
                                # Spawn frost particles in a wide AoE around impact —
                                # the frost system freezes anything they touch once.
                                _aoe_r = 80
                                _ix, _iy = self.x, self.y
                                for _ in range(22):
                                    _fa  = random.uniform(0, 2 * math.pi)
                                    _fr  = random.uniform(0, _aoe_r)
                                    _fp  = Particle(
                                        _ix + math.cos(_fa) * _fr,
                                        _iy + math.sin(_fa) * _fr,
                                        random.randint(5, 11),
                                        random.choice(['white','cyan','#aaffff','#00ddff']),
                                        life=random.uniform(0.5, 1.1),
                                        rtype='frost', owner='player'
                                    )
                                    _fp._frozen_ids = set()
                                    game.particles.append(_fp)
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
                            # Lightning: shocked effect + bigger burst
                            if self.stype == 'lightning':
                                e._shocked_until = time.time() + 1.0
                                _bc = 'yellow'
                                num_burst = 30
                            else:
                                num_burst = 20
                            for _ in range(num_burst):
                                _ba  = random.uniform(0, 2*math.pi)
                                _br  = random.uniform(2, self.radius * 2.5)
                                _bx  = self.x + math.cos(_ba)*_br
                                _by  = self.y + math.sin(_ba)*_br
                                _bp  = Particle(_bx, _by,
                                                random.uniform(2, 7), _bc,
                                                life=random.uniform(0.15, 0.4),
                                                rtype='magic_burst', owner=None)
                                game.particles.append(_bp)
                        # Poison Infusion: apply tiered poison for shadow dagger
                        if self.stype == 'dagger' and self.owner == 'player':
                            # Purple magic_burst on dagger impact
                            for _ in range(20):
                                _ba = random.uniform(0, 2*math.pi)
                                _br = random.uniform(4, self.radius * 3.0)
                                _bp = Particle(self.x + math.cos(_ba)*_br,
                                               self.y + math.sin(_ba)*_br,
                                               random.uniform(3, 9),
                                               random.choice(['#cc44ff','#9922dd','#ff88ff']),
                                               life=random.uniform(0.28, 0.5),
                                               rtype='magic_burst', owner=None)
                                game.particles.append(_bp)
                            _owner_p = getattr(self, '_owner_ref', None) or game.player
                            if 'Poison Infusion' in getattr(_owner_p, 'tree_unlocked', set()):
                                _now_pi2 = time.time()
                                _cur_tier2  = getattr(e, '_poison_tier', 0)
                                _cur_until2 = getattr(e, '_poison_until', 0)
                                _still2 = _cur_until2 > _now_pi2
                                if _still2 and _cur_tier2 == 1:
                                    e._poison_tier = 2; e._poison_until = _now_pi2 + 10.0; e._poison_dps = e.max_hp * 0.03
                                elif _still2 and _cur_tier2 >= 2:
                                    e._poison_tier = 3; e._poison_until = _now_pi2 + 15.0; e._poison_dps = e.max_hp * 0.05
                                else:
                                    e._poison_tier = 1; e._poison_until = _now_pi2 + 5.0;  e._poison_dps = e.max_hp * 0.02
                        self.life=0; return
        if self.owner=='enemy':
            p=game.player
            if distance((self.x,self.y),(p.x,p.y))<=self.radius+p.size:
                # ── Stone Shield offhand: consume a charge to block projectile ─
                _has_offhand = any(it.item_type == 'offhand' for it in p.equipped_items)
                if _has_offhand and getattr(p, 'shield_charges', 0) > 0:
                    # Only block if projectile hits the shield face
                    _sfx = getattr(p, '_shield_face_x', p.x)
                    _sfy = getattr(p, '_shield_face_y', p.y)
                    _sfw = getattr(p, '_shield_face_sw', 14)
                    _sfa = getattr(p, '_shield_face_ang', 0)
                    if distance((self.x, self.y), (_sfx, _sfy)) <= self.radius + _sfw:
                        # Check projectile is coming from in front of shield
                        _proj_ang = math.atan2(p.y - self.y, p.x - self.x)
                        _face_fwd = _sfa + math.pi   # shield faces outward
                        _adiff    = abs((_proj_ang - _face_fwd + math.pi) % (2*math.pi) - math.pi)
                        if _adiff < math.pi * 0.6:   # ~108° frontal arc
                            p.shield_charges -= 1
                            for _ in range(10):
                                _ba2 = random.uniform(0, 2*math.pi)
                                game.spawn_particle(
                                    self.x+math.cos(_ba2)*8, self.y+math.sin(_ba2)*8,
                                    random.uniform(3,7), '#aaaadd',
                                    life=0.2, rtype='magic_burst')
                            self.life = 0
                            return
                # ── Homing fire arrow: AoE fireball explosion ─────────────────
                if self.ptype == 'homing_fire':
                    for _ in range(30):
                        ang2 = random.uniform(0, 2*math.pi)
                        r2   = random.uniform(0, self.radius*3)
                        fp   = Particle(self.x+math.cos(ang2)*r2, self.y+math.sin(ang2)*r2,
                                        random.uniform(5,12),
                                        random.choice(['orange','red','yellow','#ff6600']),
                                        life=random.uniform(0.4,1.0), rtype='flame', owner=None)
                        game.particles.append(fp)
                    game.damage_player(self.damage)
                    self.life=0; return
                # ── Homing frost arrow: burst of frost particles ───────────────
                elif self.ptype == 'homing_frost':
                    for _ in range(24):
                        ang3 = random.uniform(0, 2*math.pi)
                        r3   = random.uniform(0, self.radius*2.5)
                        fp2  = Particle(self.x+math.cos(ang3)*r3, self.y+math.sin(ang3)*r3,
                                        random.uniform(4,10),
                                        random.choice(['cyan','white','#aaffff','#00ddff']),
                                        life=random.uniform(0.3,0.7), rtype='frost', owner='enemy')
                        game.particles.append(fp2)
                    game.damage_player(self.damage)
                    self.life=0; return
                # ── Ignis meteor: explode when close to player ────────────────
                if self.ptype == 'ignis_meteor':
                    _exp_r = getattr(self, '_explode_range', 75)
                    if distance((self.x, self.y), (p.x, p.y)) <= _exp_r + p.size:
                        # Dense burst of small fire particles (bomb style)
                        for _ in range(150):
                            _ea = random.uniform(0, 2*math.pi)
                            _er = random.uniform(0, _exp_r * 1.2)
                            _ec = random.choice(['orange','red','#ff6600','yellow',
                                                 '#ff3300','white','#ff8800'])
                            game.particles.append(Particle(
                                self.x+math.cos(_ea)*_er,
                                self.y+math.sin(_ea)*_er,
                                random.uniform(3, 10), _ec,
                                life=random.uniform(0.4, 1.0),
                                rtype='fire_puff', owner=None))
                        # Larger lingering flame blobs
                        for _ in range(25):
                            _ea2 = random.uniform(0, 2*math.pi)
                            _er2 = random.uniform(0, _exp_r * 0.7)
                            game.particles.append(Particle(
                                self.x+math.cos(_ea2)*_er2,
                                self.y+math.sin(_ea2)*_er2,
                                random.uniform(8, 18),
                                random.choice(['orange','red','#ff6600']),
                                life=random.uniform(0.6, 1.4),
                                rtype='flame', owner=None))
                        # Shockwave ring
                        _sw = Particle(self.x, self.y, 8, 'orange', life=0.4,
                                       rtype='shockwave', outline=True)
                        _sw.expansion_speed = 10
                        _sw.max_radius = _exp_r
                        _sw.damage = 0
                        _sw.cx = self.x; _sw.cy = self.y
                        _sw.owner = None
                        game.particles.append(_sw)
                        game.damage_player(self.damage)
                        self.life = 0
                        return
                    return
                # Fire projectiles burst into flame particles on impact
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
                elif self.ptype == 'lava_proj':
                    # Lava spray hit: burst of lava particles
                    for _ in range(14):
                        ang2 = random.uniform(0, 2*math.pi)
                        r2   = random.uniform(0, self.radius*2.0)
                        fp   = Particle(self.x+math.cos(ang2)*r2, self.y+math.sin(ang2)*r2,
                                        random.uniform(3,8),
                                        random.choice(['#ff4500','#cc2200','#ff6600','#ff8800']),
                                        life=random.uniform(0.2,0.5), rtype='fire_puff', owner=None)
                        game.particles.append(fp)
                    # Leave a small lava puddle
                    if not hasattr(game, 'lava_pools'):
                        game.lava_pools = []
                    game.lava_pools.append(LavaPool(self.x, self.y, radius=18, damage=self.damage*0.4, duration=4.0))
                    game.damage_player(self.damage)
                elif self.ptype == 'magma_bomb':
                    # Magma bomb hit: large explosion + big lava pool
                    for _ in range(30):
                        ang2 = random.uniform(0, 2*math.pi)
                        r2   = random.uniform(0, self.radius*4)
                        fp   = Particle(self.x+math.cos(ang2)*r2, self.y+math.sin(ang2)*r2,
                                        random.uniform(5,14),
                                        random.choice(['#ff4500','#cc2200','#ff6600','#ff8800','#ffaa00']),
                                        life=random.uniform(0.4,1.2), rtype='fire_puff', owner=None)
                        game.particles.append(fp)
                    if not hasattr(game, 'lava_pools'):
                        game.lava_pools = []
                    game.lava_pools.append(LavaPool(self.x, self.y, radius=45, damage=self.damage*0.6, duration=7.0))
                    game.damage_player(self.damage)
                elif self.stype == 'lightning':
                    # Shocked: player glows yellow for 1.5s
                    game.player._shocked_until = time.time() + 1.5
                    for _ in range(22):
                        _ba = random.uniform(0, 2*math.pi)
                        _br = random.uniform(2, self.radius*2.5)
                        game.particles.append(Particle(
                            self.x+math.cos(_ba)*_br, self.y+math.sin(_ba)*_br,
                            random.uniform(2,6), 'yellow',
                            life=random.uniform(0.15,0.4), rtype='magic_burst', owner=None))
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

class LavaPool:
    """
    A persistent lava puddle left by Ignismancer attacks.
    Drawn as an irregular organic blob (not a perfect circle).
    Damages the player and enemies that stand in it.
    """
    def __init__(self, x, y, radius=35, damage=5, duration=6.0):
        self.x = x
        self.y = y
        self.base_radius = radius
        self.damage = damage
        self.duration = duration
        self.age = 0.0
        self._damage_tick = 0.0   # cooldown between damage ticks
        # Generate random blob shape offsets for organic look
        num_pts = random.randint(10, 16)
        self._angles = [(2 * math.pi / num_pts) * i + random.uniform(-0.2, 0.2)
                        for i in range(num_pts)]
        self._radii  = [radius * random.uniform(0.6, 1.35) for _ in range(num_pts)]
        # Wobble phase offsets
        self._wobble  = [random.uniform(0, 2 * math.pi) for _ in range(num_pts)]
        self._wobble_spd = [random.uniform(1.5, 3.0) for _ in range(num_pts)]

    @property
    def alive(self):
        return self.age < self.duration

    def update(self, dt, game):
        self.age += dt
        self._damage_tick += dt
        # Damage player every 0.4 s if standing in pool
        if self._damage_tick >= 0.4:
            self._damage_tick = 0.0
            p = game.player
            if math.hypot(p.x - self.x, p.y - self.y) < self.base_radius * 0.9:
                game.damage_player(self.damage)

    def draw(self, canvas):
        """Draw organic lava blob using polygon."""
        t = self.age
        fade = max(0.0, 1.0 - self.age / self.duration)
        # Build polygon points with time-based wobble
        pts = []
        for i, (ang, rad) in enumerate(zip(self._angles, self._radii)):
            wobble = math.sin(t * self._wobble_spd[i] + self._wobble[i]) * 4
            r = (rad + wobble) * fade
            pts.append(self.x + math.cos(ang) * r)
            pts.append(self.y + math.sin(ang) * r)
        if len(pts) >= 6:
            # Dark lava base
            canvas.create_polygon(pts, fill='#990000', outline='', smooth=True)
            # Bright orange overlay (slightly smaller)
            inner = []
            for i in range(0, len(pts), 2):
                cx2 = self.x + (pts[i] - self.x) * 0.7
                cy2 = self.y + (pts[i+1] - self.y) * 0.7
                inner.append(cx2); inner.append(cy2)
            if len(inner) >= 6:
                canvas.create_polygon(inner, fill='#cc4400', outline='', smooth=True)
            # Hot glow core
            core_r = max(3, self.base_radius * 0.3 * fade)
            canvas.create_oval(self.x-core_r, self.y-core_r,
                               self.x+core_r, self.y+core_r,
                               fill='#ff8800', outline='')


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
                    if not hasattr(self, '_burst_ids'): self._burst_ids = set()
                    eid = id(e)
                    if eid not in self._burst_ids:
                        self._burst_ids.add(eid)
                        for _ in range(18):
                            _ba = random.uniform(0, 2*math.pi)
                            game.spawn_particle(
                                e.x + math.cos(_ba)*random.uniform(4,20),
                                e.y + math.sin(_ba)*random.uniform(4,20),
                                random.uniform(3,9), random.choice(['#cc44ff','#9922dd','#ff88ff']),
                                life=random.uniform(0.28,0.5), rtype='magic_burst')
        if self.rtype == "blade1":
            for e in list(game.room.enemies):
                if distance((self.x, self.y), (e.x, e.y)) <= self.size:
                    game.damage_enemy(e, game.player.atk * 2.0)
        if self.rtype == "eblade":
            # Check if player is inside the particle radius
            if distance((self.x, self.y), (game.player.x, game.player.y)) <= self.size:
                game.damage_player(self.damage)
        if self.rtype == "enemy_slash":
            # Crescent hit check — damage player once per particle life
            if not getattr(self, '_enemy_slash_hit', False):
                p2 = game.player
                dist_p = distance((self.x, self.y), (p2.x, p2.y))
                if dist_p <= self.size + p2.size:
                    arc_w = math.pi * 0.7
                    adiff = (math.atan2(p2.y-self.y, p2.x-self.x)
                             - self.angle + 2*math.pi) % (2*math.pi)
                    if adiff <= arc_w/2 or adiff >= 2*math.pi - arc_w/2:
                        game.damage_player(self.damage)
                        kb = getattr(self, '_knockback', 0)
                        if kb > 0:
                            kbsrc = getattr(self, '_knockback_src', (self.x, self.y))
                            dx_kb = p2.x - kbsrc[0]; dy_kb = p2.y - kbsrc[1]
                            d_kb = math.hypot(dx_kb, dy_kb)
                            if d_kb > 0:
                                p2.x += dx_kb/d_kb * kb
                                p2.y += dy_kb/d_kb * kb
                        self._enemy_slash_hit = True
        if self.rtype == "enemy_slash_dark":
            # Ensure spawn-position anchor exists
            if not hasattr(self, 'cx'):
                self.cx = self.x
            if not hasattr(self, 'cy'):
                self.cy = self.y
            # Sweep animation: crescent rotates ±0.5 rad around spawn point
            total_life = getattr(self, '_total_life', None)
            if total_life is None:
                self._total_life = self.life + self.age
                total_life = self._total_life
                self._base_size = self.size
            if total_life > 0:
                progress = self.age / total_life
                sweep_range = 1.0
                self._sweep_offset = -sweep_range / 2 + sweep_range * progress
                grow = min(progress * 2, 1.0)
                self.size = self._base_size * (1.0 + 0.45 * grow)
                swept_angle = self.angle + self._sweep_offset
                orbit_dist = self._base_size * 0.9
                self.x = self.cx + math.cos(swept_angle) * orbit_dist
                self.y = self.cy + math.sin(swept_angle) * orbit_dist
            # Damage player once per particle
            if self.damage > 0 and not getattr(self, '_slash_dark_hit', False):
                p2 = game.player
                dist_p = distance((self.x, self.y), (p2.x, p2.y))
                if dist_p <= self.size + p2.size:
                    arc_w = math.pi * 0.85
                    adiff = (math.atan2(p2.y - self.y, p2.x - self.x)
                             - self.angle + 2*math.pi) % (2*math.pi)
                    if adiff <= arc_w/2 or adiff >= 2*math.pi - arc_w/2:
                        game.damage_player(self.damage)
                        # Apply knockback if stored
                        kb = getattr(self, '_knockback', 0)
                        if kb > 0:
                            kbsrc = getattr(self, '_knockback_src', (self.cx, self.cy))
                            dx_kb = p2.x - kbsrc[0]
                            dy_kb = p2.y - kbsrc[1]
                            d_kb = math.hypot(dx_kb, dy_kb)
                            if d_kb > 0:
                                p2.x += dx_kb / d_kb * kb
                                p2.y += dy_kb / d_kb * kb
                        self._slash_dark_hit = True
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
            self.y -= 0.4
            self.size *= 0.94
            self.color = random.choice(['orange','red','yellow','#ff6600'])
        elif self.rtype == "holy_puff":
            self.y -= 0.4
            self.size *= 0.94
            # color preserved — do NOT override
        elif self.rtype == "black_puff":
            self.y -= 0.4
            self.size *= 0.94
            # color preserved — do NOT override


        elif self.rtype == "magic_burst":
            # Small spark — just shrink, no damage
            self.size *= 0.88

        elif self.rtype == "water_puddle":
            _now_wp = time.time()
            if _now_wp >= getattr(self, '_next_tick', 0):
                self._next_tick = _now_wp + 1.0
                _pr = getattr(self, '_puddle_r', 90)
                _px = getattr(self, '_puddle_x', self.x)
                _py = getattr(self, '_puddle_y', self.y)
                for _we in list(game.room.enemies):
                    if distance((_we.x, _we.y), (_px, _py)) <= _pr:
                        # Increment tier each tick, capped at 5
                        _cur_tier = getattr(_we, '_wet_tier', 0)
                        _tier = min(5, _cur_tier + 1)
                        _we._wet_tier  = _tier
                        _we._wet_until = _now_wp + 10.0 + 2.0 * _tier

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

        elif self.rtype == "holy_flame":
            # Like flame but flickers yellow/white — used by Holyflame skill
            self.y -= 0.5
            self.size *= 0.97
            self.color = random.choice(['#ffdd00','#ffffff','#ffee55','#ffffaa','#ffcc00'])

        elif self.rtype == "black_flame":
            # Like flame but flickers dark purple/red — used by Blackflame skill
            self.y -= 0.5
            self.size *= 0.97
            self.color = random.choice(['#330022','#660033','#990044','#aa0055','#cc0066'])

        elif self.rtype == "life_spark":
            # Green spark that drifts upward — for Circle of Life
            self.y -= 0.8
            self.x += math.sin(getattr(self, 'age', 0) * 3.1) * 0.4
            self.age = getattr(self, 'age', 0) + 0.07

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
        if self.rtype == "root_spike":
            # Grow upward from origin then fade — stays in place
            if not hasattr(self, '_total_life'):
                self._total_life = self.life + self.age
            progress = self.age / self._total_life
            grow     = min(1.0, progress * 2.5)
            self.x   = self._origin_x + math.cos(self.angle) * self.radius * grow
            self.y   = self._origin_y + math.sin(self.angle) * self.radius * grow

        if self.rtype == "vine_wrap":
            # Orbit gently around the grasped target
            tgt = getattr(self, '_target', None)
            if tgt is not None:
                t   = getattr(self, '_seg_t', 0)
                orb = math.sin(time.time() * 6 + t * math.pi * 2) * 8
                self.x = tgt.x + math.cos(t * math.pi * 2) * (tgt.size + 6 + orb)
                self.y = tgt.y + math.sin(t * math.pi * 2) * (tgt.size + 6 + orb)

        if self.rtype == "wind_stipple":
            # Drift forward along travel angle
            self.x += math.cos(self.angle) * self.radius * dt * 0.8
            self.y += math.sin(self.angle) * self.radius * dt * 0.8

        if self.rtype == "root_tri":
            # Grow upward from origin then fade — same as root_spike
            if not hasattr(self, '_total_life'):
                self._total_life = self.life + self.age
            progress = self.age / self._total_life
            grow     = min(1.0, progress * 2.5)
            self.x   = self._origin_x + math.cos(self.angle) * self.radius * grow
            self.y   = self._origin_y + math.sin(self.angle) * self.radius * grow

        if self.rtype == "grasping_vine_track":
            # Expire when the target is no longer grasped or is dead
            tgt = getattr(self, '_target', None)
            if tgt is None or not getattr(tgt, '_grasped', False) or getattr(tgt, 'hp', 1) <= 0:
                self.life = 0


        if self.rtype in ("branch", "leaf"):
            px, py = game.player.x, game.player.y
            progress = self.age / self.life
            if progress < 0.5:
                reach = self.radius * (progress * 2)
            else:
                reach = self.radius * (2 - progress * 2)
            reach = max(0, reach)
            swing = math.sin(progress * math.pi - math.pi/2) * 0.3
            angle = self.angle + swing
            self.x = px + math.cos(angle) * reach
            self.y = py + math.sin(angle) * reach
            # Damage each enemy at most once per whip swing (tracked by id set)
            if not hasattr(self, '_hit_ids'):
                self._hit_ids = set()
            for e in list(game.room.enemies):
                if id(e) not in self._hit_ids and distance((self.x, self.y), (e.x, e.y)) <= self.size + e.size:
                    game.damage_enemy(e, game.player.wis * 2.5)
                    self._hit_ids.add(id(e))

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
                    if not hasattr(self, '_burst_ids'): self._burst_ids = set()
                    eid = id(e)
                    if eid not in self._burst_ids:
                        self._burst_ids.add(eid)
                        burst_col = random.choice(['cyan','#aaffff','white']) if self.color == 'cyan' else random.choice(['#ff4444','#ff8888','#ffaaaa'])
                        for _ in range(18):
                            _ba = random.uniform(0, 2*math.pi)
                            game.spawn_particle(
                                e.x + math.cos(_ba)*random.uniform(4,18),
                                e.y + math.sin(_ba)*random.uniform(4,18),
                                random.uniform(3,8), burst_col,
                                life=random.uniform(0.25,0.45), rtype='magic_burst')

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

        elif self.rtype == "enemy_slash":
            # Static fallback crescent — only used if inline loop misses it
            radius = self.size * 2.0
            offset = self.size * 0.65
            canvas.create_oval(self.x-radius, self.y-radius, self.x+radius, self.y+radius,
                               fill='#888888', outline='#888888')
            canvas.create_oval(self.x-radius+offset, self.y-radius,
                               self.x+radius+offset, self.y+radius,
                               fill=background_color, outline=background_color)
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
        if getattr(self, '_shop_open', False):
            return   # freeze while trading

        now = time.time()
        if now - self.last_move > random.uniform(2, 5):
            # New wander target near home, clamped to town interior
            tx = clamp(self.home_x + random.randint(-80, 80), 360, 1040)
            ty = clamp(self.home_y + random.randint(-80, 80), 320, 800)
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

        # Hard-clamp so NPCs stay inside the oval town area
        self.x = clamp(self.x, 360, 1040)
        self.y = clamp(self.y, 320, 800)

    def update_indoor(self, dt, wall, room_w, room_h, furn_rects=None):
        """Wander within the interior room, avoiding walls and furniture."""
        if getattr(self, '_shop_open', False):
            return   # freeze while trading
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
            self._player_level_hint = player_level
            spawn_boss_for_room(self, dungeon_id)

        # Treasure room directly below boss room — locked until boss is defeated (ALL dungeons)
        if row == 1 and col == 4:
            self._is_treasure_room = True
            # Unique epic item per dungeon
            _treasure_items = {
                1: random.choice([
                       InventoryItem('Iron Warden\'s Blade','weapon','Epic',
                           stats={'strength':8,'vitality':5,'agility':3},
                           skills=['Orbiting Blade'], price=0, weapon_type='sword'),
                       InventoryItem('Arcane Longbow','weapon','Epic',
                           stats={'agility':8,'intelligence':6,'wisdom':4},
                           skills=['Homing Arrow Pair'], price=0, weapon_type='bow'),
                       InventoryItem('Stone Shield','offhand','Epic',
                           stats={'vitality':8,'constitution':6,'strength':3},
                           skills=[], price=0, weapon_type=None),
                   ]),
                2: InventoryItem('Emberstave of Ignis','weapon','Legendary',
                       stats={'intelligence':18,'wisdom':10,'strength':5},
                       skills=['Fireball','Fire Breath','Fire Storm'], price=0, weapon_type='ignis_staff'),
                3: InventoryItem('Frost Wand','weapon','Epic',
                       stats={'intelligence':10,'wisdom':6,'will':4},
                       skills=[], price=0, weapon_type='wand'),
                4: InventoryItem('Shadow Scythe','weapon','Epic',
                       stats={'strength':9,'agility':6,'intelligence':5},
                       skills=[], price=0, weapon_type='scythe'),
            }
            _item = _treasure_items.get(dungeon_id,
                        InventoryItem('Gold Ring','ring','Rare',stats={'strength':5},skills=[],price=0))
            self.decorations.append({
                'type':'treasure_chest','x':WINDOW_W//2,'y':WINDOW_H//2,
                'opened':False,'coins':800,'items':[_item]
            })
    
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
            'x': 250, 'y': 220,
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
            'x': 550, 'y': 210,
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
            'x': 1010, 'y': 220,
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
            'x': 215, 'y': 460,
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
            'x': 470, 'y': 440,
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
            'x': 930, 'y': 500,
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
            'x': 290, 'y': 770,
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
            'x': 640, 'y': 790,
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

        self.npcs.append(indoor_npc("Eldrin",  625, 270, 'librarian',  self.get_librarian_items()))
        self.npcs.append(indoor_npc("Gorak",  1075, 285, 'blacksmith', self.get_blacksmith_items()))
        self.npcs.append(indoor_npc("Mystara", 255, 550, 'enchanter',  self.get_enchanter_items()))
        self.npcs.append(indoor_npc("Zephyr",  525, 485, 'alchemist',  self.get_alchemist_items()))
        self.npcs.append(indoor_npc("Berta",  1000, 548, 'chef',       self.get_chef_items()))
        self.npcs.append(indoor_npc("Gemma",   340, 813, 'jeweler',    self.get_jeweler_items()))
        self.npcs.append(indoor_npc("Marcus",  700, 835, 'trader',     self.get_trader_items()))

        # Oryn stays OUTSIDE — sells the map near the fountain
        self.npcs.append(NPC("Oryn", TOWN_CX + 80, TOWN_CY - 60, 'villager', [MAP_ITEM]))

        # Villagers
        for i in range(8):
            self.npcs.append(NPC(
                f"Villager {i+1}",
                random.randint(390, 1000),
                random.randint(350, 790),
                'villager'
            ))
        
        # === CIRCULAR OVAL FOREST BOUNDARY ===
        # Define dungeon entrance gaps (kept for collision walls below)
        dungeon1_gap = {'y_start': 350, 'y_end': 500, 'side': 'left'}
        dungeon2_gap = {'y_start': 200, 'y_end': 300, 'side': 'right'}
        dungeon3_gap = {'y_start': 750, 'y_end': 850, 'side': 'right'}
        dungeon4_gap = {'x_start': 600, 'x_end': 800, 'side': 'bottom'}

        # Forest colour constants — unified so wall and edge particles match
        FOREST_COL = '#3a6e1e'   # slightly lighter forest fill
        EDGE_COL   = '#3a6b24'   # canopy blob colour (slightly lighter, same family)
        # TOWN_CX, TOWN_CY, OVAL_A, OVAL_B are module-level constants (top of file)

        # Angles (in radians) from centre to each dungeon portal, plus half-gap width
        _dgaps = [
            (math.atan2(0,    -1),   0.13),   # D1 west  — matches GW=90
            (math.atan2(-350, 1150), 0.11),   # D2 NE
            (math.atan2( 350, 1150), 0.11),   # D3 SE
            (math.atan2( 950,  0),   0.13),   # D4 south
        ]
        def _in_dgap(ang):
            a = ang % (2 * math.pi)
            for center_a, half in _dgaps:
                ca = center_a % (2 * math.pi)
                d  = abs(a - ca); d = min(d, 2 * math.pi - d)
                if d < half:
                    return True
            return False

        # TOP FOREST WALL (no gaps needed here)
        self.decorations.append({
            'type': 'forest_wall',
            'x': TOWN_X_START - FOREST_THICKNESS,
            'y': TOWN_Y_START - FOREST_THICKNESS,
            'width': (TOWN_X_END - TOWN_X_START) + FOREST_THICKNESS * 2,
            'height': FOREST_THICKNESS,
            'color': FOREST_COL,
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
            'color': FOREST_COL,
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
            'color': FOREST_COL,
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
            'color': FOREST_COL,
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
            'color': FOREST_COL,
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
            'color': FOREST_COL,
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
            'color': FOREST_COL,
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
            'color': FOREST_COL,
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
            'color': FOREST_COL,
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
            'color': FOREST_COL,
            'collision_rect': (dungeon2_x + 50, dungeon2_gap['y_start'],
                              dungeon2_x + 50 + FOREST_THICKNESS, dungeon2_gap['y_end'])
        })

        # Dungeon 3 path cap — sits just beyond the Ice Cavern clearing (TOWN_CX+3200)
        dungeon3_x = TOWN_CX + 3400
        self.decorations.append({
            'type': 'forest_wall',
            'x': dungeon3_x,
            'y': dungeon3_gap['y_start'],
            'width': FOREST_THICKNESS,
            'height': dungeon3_gap['y_end'] - dungeon3_gap['y_start'],
            'color': FOREST_COL,
            'collision_rect': (dungeon3_x, dungeon3_gap['y_start'],
                              dungeon3_x + FOREST_THICKNESS, dungeon3_gap['y_end'])
        })
        # Corridor channel — top and bottom walls guiding player from forest to clearing
        _corridor_x0 = TOWN_X_END + FOREST_THICKNESS
        _corridor_x1 = dungeon3_x
        _chan_thick   = 80
        for _cy_base, _cy_dir in ((dungeon3_gap['y_start'], -1), (dungeon3_gap['y_end'], 1)):
            self.decorations.append({
                'type': 'forest_wall',
                'x': _corridor_x0,
                'y': _cy_base + _cy_dir * _chan_thick if _cy_dir == 1 else _cy_base - _chan_thick,
                'width': _corridor_x1 - _corridor_x0,
                'height': _chan_thick,
                'color': FOREST_COL,
                'collision_rect': (
                    _corridor_x0,
                    _cy_base - _chan_thick if _cy_dir == -1 else _cy_base,
                    _corridor_x1,
                    _cy_base if _cy_dir == -1 else _cy_base + _chan_thick,
                )
            })

        # Dungeon 4 path cap (bottom side)
        dungeon4_y = TOWN_Y_END + 150
        self.decorations.append({
            'type': 'forest_wall',
            'x': dungeon4_gap['x_start'],
            'y': dungeon4_y + 50,
            'width': dungeon4_gap['x_end'] - dungeon4_gap['x_start'],
            'height': FOREST_THICKNESS,
            'color': FOREST_COL,
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
            'color': FOREST_COL,
            'collision_rect': (TOWN_X_START - FOREST_THICKNESS, TOWN_Y_START - FOREST_THICKNESS,
                              TOWN_X_START, TOWN_Y_START)
        })

        self.decorations.append({
            'type': 'forest_wall',
            'x': TOWN_X_END,
            'y': TOWN_Y_START - FOREST_THICKNESS,
            'width': FOREST_THICKNESS,
            'height': FOREST_THICKNESS,
            'color': FOREST_COL,
            'collision_rect': (TOWN_X_END, TOWN_Y_START - FOREST_THICKNESS,
                              TOWN_X_END + FOREST_THICKNESS, TOWN_Y_START)
        })

        self.decorations.append({
            'type': 'forest_wall',
            'x': TOWN_X_START - FOREST_THICKNESS,
            'y': TOWN_Y_END,
            'width': FOREST_THICKNESS,
            'height': FOREST_THICKNESS,
            'color': FOREST_COL,
            'collision_rect': (TOWN_X_START - FOREST_THICKNESS, TOWN_Y_END,
                              TOWN_X_START, TOWN_Y_END + FOREST_THICKNESS)
        })

        self.decorations.append({
            'type': 'forest_wall',
            'x': TOWN_X_END,
            'y': TOWN_Y_END,
            'width': FOREST_THICKNESS,
            'height': FOREST_THICKNESS,
            'color': FOREST_COL,
            'collision_rect': (TOWN_X_END, TOWN_Y_END,
                              TOWN_X_END + FOREST_THICKNESS, TOWN_Y_END + FOREST_THICKNESS)
        })
        # === CIRCULAR OVAL FOREST EDGES — dense blobs matching background colour ===
        EDGE_COL = FOREST_COL   # same colour as solid forest wall
        for _deg in range(0, 360, 4):          # every 4° = ~90 blobs
            _ang = math.radians(_deg)
            if _in_dgap(_ang):
                continue
            _r = 1.0 + random.uniform(-0.03, 0.03)
            _ex = TOWN_CX + OVAL_A * math.cos(_ang) * _r + random.randint(-6, 6)
            _ey = TOWN_CY + OVAL_B * math.sin(_ang) * _r + random.randint(-6, 6)
            self.decorations.append({'type': 'forest_edge', 'x': _ex, 'y': _ey,
                                     'size': random.randint(38, 52), 'color': EDGE_COL})

        # === DUNGEON CLEARINGS — far outside the oval; forest gap leads to them ===
        dungeon_clearings = [
            {'x': TOWN_CX - 1450, 'y': TOWN_CY,         'id': 1, 'name': '🌲 Forest Temple', 'color': '#228B22'},
            {'x': TOWN_CX + 1450, 'y': TOWN_CY - 380,  'id': 2, 'name': '🌋 Volcano',        'color': '#FF4500'},
            {'x': TOWN_CX + 3200, 'y': TOWN_CY + 420,  'id': 3, 'name': '❄️ Ice Cavern',     'color': '#00CED1'},
            {'x': TOWN_CX,        'y': TOWN_CY + 1200, 'id': 4, 'name': '👻 Shadow Realm',   'color': '#8B008B'},
        ]
        # Extra scenic clearing to the left of the Ice Cavern (no dungeon, purely decorative)
        _ice_left_clearing = {
            'x': TOWN_CX + 2650, 'y': TOWN_CY + 180,
            'id': None, 'name': '', 'color': '#a8d8f0',
        }
        for _dc in dungeon_clearings:
            _dc_rad = 280 if _dc['id'] == 3 else 140  # Ice Cavern gets a much larger clearing
            self.decorations.append({
                'type': 'dungeon_clearing',
                'x':          _dc['x'],
                'y':          _dc['y'],
                'dungeon_id': _dc['id'],
                'name':       _dc['name'],
                'color':      _dc['color'],
                'radius':     _dc_rad,
            })
            # Dense ring of canopy blobs framing the clearing — type clearing_edge
            _blob_r = _dc_rad + 8
            for _da in range(0, 360, 12):
                _ar = math.radians(_da)
                _cr = _blob_r + random.randint(-10, 10)
                self.decorations.append({
                    'type':  'clearing_edge',
                    'x':     _dc['x'] + math.cos(_ar) * _cr + random.randint(-8, 8),
                    'y':     _dc['y'] + math.sin(_ar) * _cr + random.randint(-8, 8),
                    'size':  random.randint(35, 55),
                    'color': '#4a8030',
                })


        # Left scenic clearing next to Ice Cavern — moved up, larger
        _ilc = _ice_left_clearing
        _ilc_rad = 220
        self.decorations.append({
            'type': 'plain_clearing',
            'x': _ilc['x'], 'y': _ilc['y'],
            'radius': _ilc_rad,
            'color': '#c8e8f8',   # icy pale blue-white
        })
        for _da in range(0, 360, 12):
            _ar = math.radians(_da)
            _cr = _ilc_rad + 8 + random.randint(-10, 10)
            self.decorations.append({
                'type':  'clearing_edge',
                'x':     _ilc['x'] + math.cos(_ar) * _cr + random.randint(-8, 8),
                'y':     _ilc['y'] + math.sin(_ar) * _cr + random.randint(-8, 8),
                'size':  random.randint(35, 55),
                'color': '#4a8030',
            })

        # === DECORATIONS WITH COLLISION ===
        self.decorations.append({
            'type': 'fountain',
            'x': TOWN_CX, 'y': TOWN_CY,
            'size': 40,
            'has_collision': True,
            'water_particles': []
        })
        
        lamp_positions = [(430, 380), (850, 380), (420, 660), (850, 660)]
        for lx, ly in lamp_positions:
            self.decorations.append({
                'type': 'lamp',
                'x': lx, 'y': ly,
                'size': 12,
                'has_collision': True
            })
        
        
        # dungeon portals → now rendered as dungeon_clearing (see block above)
        
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
        """Epic and Legendary items, plus Warp Scroll (tower exclusive)"""
        warp = next((ci for ci in CONSUMABLE_SHOP_ITEMS if ci.subtype == 'warp_scroll'), None)
        base = [item for item in SHOP_ITEMS if item.rarity in ['Epic', 'Legendary']]
        if warp:
            base = base + [warp]
        return base
    
    def get_alchemist_items(self):
        """Potions and elixirs"""
        return list(CONSUMABLE_SHOP_ITEMS)

    def get_tower_items(self):
        """Tower-specific consumables — includes the Warp Scroll"""
        warp = next((c for c in CONSUMABLE_SHOP_ITEMS if c.subtype == 'warp_scroll'), None)
        base = list(CONSUMABLE_SHOP_ITEMS)
        if warp and warp not in base:
            base.append(warp)
        return base
    
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

# ---------- Wild Shape Window ----------
class WildShapeWindow:
    """
    Form-selection UI for Wild Shape. Similar layout to the Skill Management window.
    Shows all available forms as cards; clicking one transforms the player.
    Can be embedded into an existing tab via embed_in_frame().
    """
    C_BG       = '#0a120a'
    C_HDR      = '#0f1f0f'
    C_CARD     = '#152015'
    C_CARD_HOV = '#1e3020'
    C_GOLD     = '#ffd700'
    C_GREEN    = '#66cc66'
    C_ACTIVE   = '#33ff66'

    CATEGORY_COLORS = {
        'Beast':     '#c8a832',
        'Elemental': '#4090e0',
        'Monster':   '#c03030',
    }

    def __init__(self, game_frame, player):
        """Open as a standalone Toplevel."""
        self.gf     = game_frame
        self.player = player
        self.win = tk.Toplevel(game_frame)
        self.win.title("Wild Shape — Choose a Form")
        self.win.configure(bg=self.C_BG)
        self.win.resizable(True, True)
        self.win.geometry("860x640")
        self._build_ui(self.win)

    @classmethod
    def embed_in_frame(cls, frame, game_frame, player):
        obj = object.__new__(cls)
        obj.gf     = game_frame
        obj.player = player
        obj.win    = frame
        obj._build_ui(frame)
        return obj

    def _build_ui(self, container):
        # Header
        hdr = tk.Frame(container, bg=self.C_HDR)
        hdr.pack(fill='x', side='top')

        # Show current form status
        form = getattr(self.player, 'wild_shape_form', None)
        status_text = f"🐾  Currently transformed: {form}" if form else "🐾  Not transformed — click a form to shapeshift"
        status_col  = self.C_ACTIVE if form else '#aaaaaa'
        tk.Label(hdr, text="🌿  Wild Shape — Form Selection",
                 font=("Arial", 14, "bold"), bg=self.C_HDR, fg=self.C_GOLD).pack(side='left', padx=14, pady=8)
        self._status_lbl = tk.Label(hdr, text=status_text,
                                     font=("Arial", 10), bg=self.C_HDR, fg=status_col)
        self._status_lbl.pack(side='left', padx=10)

        if form:
            exit_btn = tk.Button(hdr, text="⬅  Exit Form  (or press 6)",
                                  font=("Arial", 10, "bold"),
                                  bg='#442222', fg='#ffaaaa', relief='flat', padx=10,
                                  command=lambda: [self.gf.exit_wild_shape(),
                                                   self._refresh(container)])
            exit_btn.pack(side='right', padx=14, pady=6)

        # Scrollable canvas for form cards
        outer = tk.Frame(container, bg=self.C_BG)
        outer.pack(fill='both', expand=True, padx=8, pady=6)
        vsb = tk.Scrollbar(outer, orient='vertical')
        vsb.pack(side='right', fill='y')
        self._canvas = tk.Canvas(outer, bg=self.C_BG, highlightthickness=0,
                                  yscrollcommand=vsb.set)
        self._canvas.pack(side='left', fill='both', expand=True)
        vsb.config(command=self._canvas.yview)
        self._canvas.bind('<MouseWheel>',
                          lambda e: self._canvas.yview_scroll(int(-1*(e.delta/120)), 'units'))

        scroll_frame = tk.Frame(self._canvas, bg=self.C_BG)
        self._canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
        scroll_frame.bind("<Configure>",
                          lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))

        # Build form cards grouped by category
        categories = {}
        for form_data in WILD_SHAPE_FORMS:
            cat = form_data['category']
            categories.setdefault(cat, []).append(form_data)

        current_form = getattr(self.player, 'wild_shape_form', None)
        unlocked_forms = getattr(self.player, 'unlocked_forms', set())

        for cat_name, forms in categories.items():
            cat_col = self.CATEGORY_COLORS.get(cat_name, '#888888')
            # Category header
            cat_hdr = tk.Frame(scroll_frame, bg=self.C_BG)
            cat_hdr.pack(fill='x', padx=4, pady=(12, 4))
            tk.Label(cat_hdr, text=f"── {cat_name} Forms ──",
                     font=("Arial", 12, "bold"), bg=self.C_BG, fg=cat_col).pack(side='left', padx=6)

            # Cards in a flow layout (2 per row)
            row_frame = None
            for idx, fd in enumerate(forms):
                if idx % 2 == 0:
                    row_frame = tk.Frame(scroll_frame, bg=self.C_BG)
                    row_frame.pack(fill='x', padx=4, pady=2)

                is_active   = (current_form == fd['name'])
                is_unlocked = fd['name'] in unlocked_forms
                card_bg     = '#1a3a1a' if is_active else (self.C_CARD if is_unlocked else '#100e0e')
                card_outline = self.C_ACTIVE if is_active else (cat_col if is_unlocked else '#442222')

                card = tk.Frame(row_frame, bg=card_bg, relief='solid', bd=2,
                                highlightbackground=card_outline, highlightthickness=2)
                card.pack(side='left', padx=6, pady=4, ipadx=8, ipady=6, fill='y')

                # Top row: icon + name + CD
                top = tk.Frame(card, bg=card_bg)
                top.pack(fill='x', padx=4, pady=(4, 2))
                tk.Label(top, text=fd['icon'] if is_unlocked else '🔒', font=("Arial", 20),
                         bg=card_bg).pack(side='left')
                name_col = self.C_ACTIVE if is_active else (self.C_GOLD if is_unlocked else '#554444')
                tk.Label(top, text=fd['name'],
                         font=("Arial", 12, "bold"), bg=card_bg, fg=name_col).pack(side='left', padx=6)
                tk.Label(top, text=f"CD: {fd['cd']}s",
                         font=("Arial", 9), bg=card_bg, fg='#888888').pack(side='right', padx=4)

                # Description
                tk.Label(card, text=fd['desc'], font=("Arial", 9),
                         bg=card_bg, fg='#aaccaa' if is_unlocked else '#554444', wraplength=340, justify='left').pack(anchor='w', padx=4, pady=2)

                if is_unlocked:
                    # Show only unlocked skills
                    skill_lvl = getattr(self.player, 'form_skill_levels', {}).get(fd['name'], 1)
                    unlocked_skill_names = [s['name'] for s in fd['form_skills'][:skill_lvl]]
                    skills_txt = "  ·  ".join(unlocked_skill_names)
                    tk.Label(card, text=f"Skills: {skills_txt}",
                             font=("Arial", 8, "italic"), bg=card_bg, fg='#778877').pack(anchor='w', padx=4)

                    # Activate / active indicator
                    if is_active:
                        tk.Label(card, text="✅  ACTIVE FORM",
                                 font=("Arial", 9, "bold"), bg=card_bg, fg=self.C_ACTIVE).pack(pady=(6, 2))
                    else:
                        def _make_enter(f=fd):
                            def _do():
                                self.gf.enter_wild_shape(f['name'])
                                # Close window so the player can play
                                try:
                                    top_win = card.winfo_toplevel()
                                    if isinstance(top_win, tk.Toplevel):
                                        top_win.destroy()
                                except Exception:
                                    pass
                            return _do
                        btn = tk.Button(card, text=f"  Transform  →  {fd['name']}  ",
                                        font=("Arial", 9, "bold"),
                                        bg='#225522', fg='#aaffaa', relief='flat',
                                        activebackground='#336633', cursor='hand2',
                                        command=_make_enter())
                        btn.pack(pady=(6, 2))
                else:
                    tk.Label(card, text="🔒  Not unlocked — visit Wild Shape Forms tab to unlock",
                             font=("Arial", 8, "italic"), bg=card_bg, fg='#664444').pack(anchor='w', padx=4, pady=(4,2))

        # Footer hint
        footer = tk.Frame(container, bg='#0d180d')
        footer.pack(fill='x', side='bottom')
        tk.Label(footer,
                 text="Press  6  while in a form to revert  •  Form skills replace your hotbar immediately",
                 font=("Arial", 8, "italic"), bg='#0d180d', fg='#557755').pack(pady=4)

    def _refresh(self, container):
        for w in container.winfo_children():
            w.destroy()
        self._build_ui(container)


# ---------- General Skill Tree Window ----------
class GeneralSkillTreeWindow:
    """
    Visual tree for the class-independent GENERAL_SKILL_TREE.
    Embeds into an existing frame via embed_in_frame().
    """
    CW, CH    = 1280, 560
    TIER_Y    = {1: 80, 2: 210, 3: 340, 4: 470}
    BRANCH_X  = {'left': 130, 'center': 370, 'extra': 610, 'right': 850, 'far_right': 1130, 'water': 1090}
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

    def __init__(self, game_frame, player):
        self.gf     = game_frame
        self.player = player
        self.tree   = GENERAL_SKILL_TREE
        self._node_coords = {}
        self.win = tk.Toplevel(game_frame)
        self.win.title("General Skills")
        self.win.configure(bg=self.C_BG)
        self.win.resizable(False, False)
        self._build_ui(self.win)

    @classmethod
    def embed_in_frame(cls, frame, game_frame, player, dialog_parent):
        obj = object.__new__(cls)
        obj.gf     = game_frame
        obj.player = player
        obj.tree   = GENERAL_SKILL_TREE
        obj._node_coords = {}
        obj.win    = dialog_parent
        obj._build_ui(frame)
        return obj

    def _build_ui(self, container):
        hdr = tk.Frame(container, bg='#1a1a2e')
        hdr.pack(fill='x', side='top')
        tk.Label(hdr, text="🧠  General  Skills",
                 font=("Arial", 14, "bold"), bg='#1a1a2e', fg='#aaddff').pack(side='left', padx=14, pady=7)
        tk.Label(hdr, text="Available to ALL classes  •  1 General SP every 2 levels",
                 font=("Arial", 9, "italic"), bg='#1a1a2e', fg='#556677').pack(side='left', padx=4)
        self.sp_label = tk.Label(hdr, text=f"General SP: {getattr(self.player, 'gen_skill_points', 0)}",
                                  font=("Arial", 11, "bold"), bg='#1a1a2e', fg='#aaffaa')
        self.sp_label.pack(side='right', padx=14)

        canvas_frame = tk.Frame(container, bg=self.C_BG)
        canvas_frame.pack(side='top', padx=6, pady=4, fill='both', expand=True)
        sb_v = tk.Scrollbar(canvas_frame, orient='vertical')
        sb_v.pack(side='right', fill='y')
        sb_h = tk.Scrollbar(canvas_frame, orient='horizontal')
        sb_h.pack(side='bottom', fill='x')
        self.canvas = tk.Canvas(canvas_frame, width=min(self.CW, 1100), height=self.CH,
                                bg=self.C_BG, highlightthickness=0,
                                yscrollcommand=sb_v.set,
                                xscrollcommand=sb_h.set,
                                scrollregion=(0, 0, self.CW, self.CH))
        self.canvas.pack(side='left', fill='both', expand=True)
        sb_v.config(command=self.canvas.yview)
        sb_h.config(command=self.canvas.xview)
        self.canvas.bind('<MouseWheel>',
                         lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), 'units'))
        self.canvas.bind('<Shift-MouseWheel>',
                         lambda e: self.canvas.xview_scroll(int(-1*(e.delta/120)), 'units'))
        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<Motion>',   self._on_hover)

        info_outer = tk.Frame(container, bg='#1a1a2e')
        info_outer.pack(side='top', fill='x', padx=6, pady=(0, 6))
        self.info_label = tk.Label(info_outer,
                                   text="Hover a node to see details.  Click an available node to unlock.",
                                   font=("Arial", 9), bg='#1a1a2e', fg='#aaaaaa',
                                   wraplength=self.CW - 20, justify='left')
        self.info_label.pack(anchor='w', padx=8, pady=5)
        self._draw()

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

    def _draw(self):
        c = self.canvas
        c.delete('all')
        self._node_coords.clear()
        by_name = {n['name']: n for n in self.tree}

        # Grid lines
        for y in self.TIER_Y.values():
            c.create_line(60, y, self.CW - 10, y, fill='#1a1a30', width=1)

        # Column headers
        c.create_text(self.BRANCH_X['left'],      22, text="— IDENTIFY —",
                      font=("Arial", 10, "bold"), fill='#556677')
        c.create_text(self.BRANCH_X['center'],    22, text="— SKILLS —",
                      font=("Arial", 10, "bold"), fill='#556677')
        c.create_text(self.BRANCH_X['extra'],     22, text="— MAGNETIC FIELD —",
                      font=("Arial", 10, "bold"), fill='#5599bb')
        c.create_text(self.BRANCH_X['right'],     22, text="— UTILITY —",
                      font=("Arial", 10, "bold"), fill='#335566')
        c.create_text(self.BRANCH_X['far_right'], 22, text="— QUICK LEARNER —",
                      font=("Arial", 10, "bold"), fill='#44bb44')

        # Tier labels
        tier_labels = {1: "Tier 1", 2: "Tier 2", 3: "Tier 3", 4: "Tier 4"}
        for t, lbl in tier_labels.items():
            if t in self.TIER_Y:
                c.create_text(35, self.TIER_Y[t], text=lbl,
                              font=("Arial", 8), fill='#555577', justify='center')

        # Connector lines
        for node in self.tree:
            nx, ny = self._node_pos(node)
            for prereq_name in node['prereq']:
                if prereq_name in by_name:
                    pn = by_name[prereq_name]
                    px, py = self._node_pos(pn)
                    pstate  = self._node_state(pn)
                    nstate  = self._node_state(node)
                    lc = self.C_LINE_ON if pstate == 'unlocked' and nstate != 'locked' else self.C_LINE_OFF
                    c.create_line(px, py, nx, ny, fill=lc, width=3, dash=(7, 4))

        # Nodes
        r = self.NODE_R
        for node in self.tree:
            nx, ny = self._node_pos(node)
            color  = self._node_color(node)
            state  = self._node_state(node)
            c.create_oval(nx-r, ny-r, nx+r, ny+r, fill=color,
                          outline='#ffffff' if state == 'unlocked' else '#666688', width=2)
            label = node['name']
            parts = label.split()
            display = '\n'.join([' '.join(parts[:2]), ' '.join(parts[2:])]) if len(parts) > 2 else label
            txt_col = self.C_TEXT_DARK if state == 'unlocked' else self.C_TEXT_LIT
            c.create_text(nx, ny, text=display, fill=txt_col,
                          font=('Arial', 8, 'bold'), justify='center', width=r*2-4)
            if node['cost'] > 0 and state != 'unlocked':
                c.create_text(nx, ny + r + 10, text=f"{node['cost']} GSP",
                              font=('Arial', 7), fill='#aaaaaa')
            self._node_coords[node['name']] = (nx, ny)

    def _find_node(self, x, y):
        r = self.NODE_R
        for name, (nx, ny) in self._node_coords.items():
            if math.hypot(x - nx, y - ny) <= r:
                return next((n for n in self.tree if n['name'] == name), None)
        return None

    def _on_hover(self, event):
        node = self._find_node(event.x, event.y)
        if node:
            state = self._node_state(node)
            cost_str = f"{node['cost']} GSP" if node['cost'] > 0 else "Free"
            prereq_str = ', '.join(node['prereq']) if node['prereq'] else 'None'
            self.info_label.config(
                text=f"[{state.upper()}]  {node['name']}  ({node['type'].capitalize()}, {cost_str})  "
                     f"Prereq: {prereq_str}\n{node['desc']}"
            )
        else:
            self.info_label.config(text="Hover a node to see details.  Click an available node to unlock.")

    def _on_click(self, event):
        node = self._find_node(event.x, event.y)
        if not node:
            return
        ok, reason = self.player.can_unlock_tree_skill(node['name'])
        if not ok:
            self.info_label.config(text=f"Cannot unlock: {reason}", fg='#ff6666')
            return
        cost = node['cost']
        gsp  = getattr(self.player, 'gen_skill_points', 0)
        msg  = (f"Unlock  '{node['name']}'  for {cost} General Skill Point(s)?\n\n"
                f"{node['desc']}\n\n"
                f"You currently have  {gsp}  General SP.")
        if tk.messagebox.askyesno("Unlock General Skill", msg, parent=self.win):
            if self.player.unlock_tree_skill(node['name']):
                self._draw()
                self.sp_label.config(text=f"General SP: {getattr(self.player, 'gen_skill_points', 0)}")
                self.info_label.config(
                    text=f"✅ '{node['name']}' unlocked!   "
                         f"Remaining General SP: {getattr(self.player, 'gen_skill_points', 0)}",
                    fg='#aaffaa')
                if hasattr(self.gf, 'refresh_active_skills'):
                    self.gf.refresh_active_skills()
                # Auto-jump to the newly unlocked skill management page
                if node['name'] == 'Keen Mind' and hasattr(self.gf, '_jump_to_skill_mgmt_page'):
                    self.gf._jump_to_skill_mgmt_page(2)
                elif node['name'] == 'Cognitive Expansion' and hasattr(self.gf, '_jump_to_skill_mgmt_page'):
                    self.gf._jump_to_skill_mgmt_page(3)
                elif node['name'] == 'Wild Shape' and hasattr(self.gf, '_jump_to_skill_mgmt_page'):
                    self.gf._jump_to_skill_mgmt_page('wild_shape')
            else:
                self.info_label.config(
                    text="Could not unlock — check GSP or prerequisites.", fg='#ff6666')
class SkillTreeWindow:
    """
    Visual skill tree. Can be opened standalone (creates its own Toplevel)
    or embedded into an existing frame via embed_in_frame().
    """
    # ── Layout & colour constants ───────────────────────────────────────────
    CW, CH    = 1260, 820
    TIER_Y    = {1: 65, 2: 195, 3: 325, 4: 455, 5: 585, 6: 715,
                 7: 845, 8: 975}
    BRANCH_X  = {'center': 370, 'left': 150, 'right': 590, 'extra': 830, 'far_right': 1070, 'water': 1070}
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

        # Canvas + scrollbars (vertical and horizontal)
        canvas_frame = tk.Frame(container, bg=self.C_BG)
        canvas_frame.pack(side='top', padx=6, pady=4, fill='both', expand=True)
        sb_v = tk.Scrollbar(canvas_frame, orient='vertical')
        sb_v.pack(side='right', fill='y')
        sb_h = tk.Scrollbar(canvas_frame, orient='horizontal')
        sb_h.pack(side='bottom', fill='x')
        self.canvas = tk.Canvas(canvas_frame,
                                width=min(self.CW, 900), height=min(self.CH, 500),
                                bg=self.C_BG, highlightthickness=0,
                                yscrollcommand=sb_v.set,
                                xscrollcommand=sb_h.set,
                                scrollregion=(0, 0, self.CW, self.CH))
        self.canvas.pack(side='left', fill='both', expand=True)
        sb_v.config(command=self.canvas.yview)
        sb_h.config(command=self.canvas.xview)
        self.canvas.bind('<MouseWheel>',
                         lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), 'units'))
        self.canvas.bind('<Shift-MouseWheel>',
                         lambda e: self.canvas.xview_scroll(int(-1*(e.delta/120)), 'units'))
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
            if node['name'] == 'Identify':
                return '#9966cc'   # purple for universal skill
            return self.C_PASSIVE if node['type'] == 'passive' else self.C_UNLOCKED
        if s == 'available' and node['name'] == 'Identify':
            return '#553377'       # darker purple when available but not yet unlocked
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
        # Extra branch label (Chain Lightning for Mage / Nature spells for Druid)
        if any(n.get('branch') == 'extra' for n in self.tree):
            if self.player.class_name == 'Druid':
                c.create_text(self.BRANCH_X['extra'], 22, text="— NATURE MAGIC —",
                              font=("Arial", 10, "bold"), fill='#336633')
                c.create_text(self.BRANCH_X['extra'], 38, text="(Control spells)",
                              font=("Arial", 8, "italic"), fill='#558855')
            else:
                c.create_text(self.BRANCH_X['extra'], 22, text="— EXTRA BRANCH —",
                              font=("Arial", 10, "bold"), fill='#665533')
                c.create_text(self.BRANCH_X['extra'], 38, text="(Lv.10+ required)",
                              font=("Arial", 8, "italic"), fill='#886644')

        # Tier labels (left margin)
        tier_labels = {1: "Tier 1\n(Free)", 2: "Tier 2\n1 SP",
                       3: "Tier 3\n1 SP",   4: "Tier 4\n2 SP",
                       5: "Tier 5\n2 SP",   6: "Tier 6\n3 SP"}
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
        # ex, ey should already be canvas-space (scroll-adjusted)
        for node in self.tree:
            nx, ny = self._node_coords.get(node['name'], (-999, -999))
            if math.hypot(ex - nx, ey - ny) <= self.NODE_R + 5:
                return node
        return None

    def _on_hover(self, event):
        node = self._node_at(self.canvas.canvasx(event.x),
                             self.canvas.canvasy(event.y))
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
        node = self._node_at(self.canvas.canvasx(event.x),
                             self.canvas.canvasy(event.y))
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
                # Auto-jump to the newly unlocked skill management page
                if node['name'] == 'Keen Mind' and hasattr(self.gf, '_jump_to_skill_mgmt_page'):
                    self.gf._jump_to_skill_mgmt_page(2)
                elif node['name'] == 'Cognitive Expansion' and hasattr(self.gf, '_jump_to_skill_mgmt_page'):
                    self.gf._jump_to_skill_mgmt_page(3)
                elif node['name'] == 'Wild Shape' and hasattr(self.gf, '_jump_to_skill_mgmt_page'):
                    self.gf._jump_to_skill_mgmt_page('wild_shape')
            else:
                self.info_label.config(
                    text="Could not unlock — check SP or prerequisites.")
