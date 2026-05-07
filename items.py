import random
import math
import time
from constants import *
from utils import clamp, distance

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
        elif self.item_type == 'arcane_bow':
            self.draw_arcane_bow(canvas)
        elif self.item_type == 'staff':
            self.draw_staff(canvas)
        elif self.item_type == 'ignis_staff':
            self.draw_ignis_staff(canvas)
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
        elif self.item_type == 'greatsword':
            self.draw_greatsword(canvas)

    def draw_greatsword(self, canvas):
        """Large two-handed sword — rectangular blade body with a proper tip, large crossguard.
        The origin (self.x/y) is at the grip centre; blade extends forward."""
        # Offset the entire sword forward so the boss grips the handle, not the blade
        forward_offset = self.size * 0.8
        cx = self.x + math.cos(self.angle) * forward_offset
        cy = self.y + math.sin(self.angle) * forward_offset

        handle_len  = self.size * 1.4
        blade_len   = self.size * 3.8
        blade_w     = self.size * 0.32   # half-width of rectangular blade body
        tip_len     = self.size * 0.7    # length of the pointed tip section
        guard_len   = self.size * 1.6    # crossguard half-length

        ca = math.cos(self.angle);  sa = math.sin(self.angle)
        pa = math.cos(self.angle + math.pi/2);  ps = math.sin(self.angle + math.pi/2)

        # Key points
        pom_x  = cx - ca * (handle_len + 8)
        pom_y  = cy - sa * (handle_len + 8)
        guard_x = cx + ca * 4
        guard_y = cy + sa * 4
        blade_end_x = guard_x + ca * blade_len       # end of rectangular part
        blade_end_y = guard_y + sa * blade_len
        tip_x  = blade_end_x + ca * tip_len          # actual point
        tip_y  = blade_end_y + sa * tip_len

        # ── Handle ──────────────────────────────────────────────────────────
        canvas.create_line(pom_x+1, pom_y+1, guard_x+1, guard_y+1,
                           fill='#110800', width=11)
        canvas.create_line(pom_x, pom_y, guard_x, guard_y,
                           fill='#2e1505', width=9)
        canvas.create_line(pom_x, pom_y, guard_x, guard_y,
                           fill='#4a2208', width=7)
        # Grip wrapping
        for i in range(5):
            t = (i + 1) / 6
            wx = pom_x + (guard_x - pom_x) * t
            wy = pom_y + (guard_y - pom_y) * t
            canvas.create_line(wx - pa*6, wy - ps*6, wx + pa*6, wy + ps*6,
                               fill='#6b3010', width=2)
        # Pommel
        canvas.create_oval(pom_x-7, pom_y-7, pom_x+7, pom_y+7,
                           fill='#666666', outline='#333333', width=2)
        canvas.create_oval(pom_x-4, pom_y-4, pom_x+4, pom_y+4,
                           fill='#bbbbbb', outline='')

        # ── Crossguard ──────────────────────────────────────────────────────
        g1x = guard_x + pa * guard_len;  g1y = guard_y + ps * guard_len
        g2x = guard_x - pa * guard_len;  g2y = guard_y - ps * guard_len
        canvas.create_line(g1x+1, g1y+1, g2x+1, g2y+1, fill='#222222', width=10)
        canvas.create_line(g1x,   g1y,   g2x,   g2y,   fill='#777777', width=8)
        canvas.create_line(g1x,   g1y,   g2x,   g2y,   fill='#cccccc', width=3)
        for gx, gy in [(g1x, g1y), (g2x, g2y)]:
            canvas.create_oval(gx-5, gy-5, gx+5, gy+5,
                               fill='#aaaaaa', outline='#444444', width=2)

        # ── Blade (rectangular body + pointed tip) ───────────────────────────
        # Four corners of the rectangular blade section
        r1x = guard_x + pa * blade_w;      r1y = guard_y + ps * blade_w
        r2x = guard_x - pa * blade_w;      r2y = guard_y - ps * blade_w
        r3x = blade_end_x - pa * blade_w;  r3y = blade_end_y - ps * blade_w
        r4x = blade_end_x + pa * blade_w;  r4y = blade_end_y + ps * blade_w

        # Rectangular body
        canvas.create_polygon([r1x, r1y, r4x, r4y, r3x, r3y, r2x, r2y],
                              fill='#6e6e6e', outline='#2a2a2a', width=2)
        # Flat top surface highlight (lighter strip down the centre)
        c1x = guard_x + pa * blade_w * 0.2;   c1y = guard_y + ps * blade_w * 0.2
        c2x = blade_end_x + pa * blade_w * 0.2; c2y = blade_end_y + ps * blade_w * 0.2
        canvas.create_line(c1x, c1y, c2x, c2y, fill='#c0c0c0', width=3)
        canvas.create_line(c1x, c1y, c2x, c2y, fill='white',   width=1)

        # Pointed tip section
        canvas.create_polygon([r4x, r4y, tip_x, tip_y, r3x, r3y],
                              fill='#8a8a8a', outline='#2a2a2a', width=2)
        # Tip edge highlight
        canvas.create_line(r4x, r4y, tip_x, tip_y, fill='#e8e8e8', width=2)
        canvas.create_line(r4x, r4y, tip_x, tip_y, fill='white',   width=1)

        # Blood groove (narrow line down blade centre)
        gv1x = guard_x + ca * 12;  gv1y = guard_y + sa * 12
        gv2x = blade_end_x - ca*4; gv2y = blade_end_y - sa*4
        canvas.create_line(gv1x, gv1y, gv2x, gv2y, fill='#383838', width=2)
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

    def draw_ignis_staff(self, canvas):
        """Gold fire-staff: shaft, spear tip, prong cradle, exact engine flame at tip."""
        import time as _time
        now = _time.time()

        staff_len = self.size * 3.2
        cx = self.x + math.cos(self.angle) * 6
        cy = self.y + math.sin(self.angle) * 6
        bx = cx - math.cos(self.angle) * staff_len * 0.30
        by = cy - math.sin(self.angle) * staff_len * 0.30
        hx = cx + math.cos(self.angle) * staff_len * 0.70
        hy = cy + math.sin(self.angle) * staff_len * 0.70

        ca = math.cos(self.angle); sa = math.sin(self.angle)
        pa = math.cos(self.angle + math.pi/2); ps = math.sin(self.angle + math.pi/2)

        # ── Gold shaft ──
        canvas.create_line(bx+2, by+2, hx+2, hy+2, fill='#3a2800', width=9)
        canvas.create_line(bx, by, hx, hy, fill='#B8860B', width=8)
        canvas.create_line(bx, by, hx, hy, fill='#DAA520', width=5)
        canvas.create_line(bx, by, hx, hy, fill='#FFD700', width=2)
        canvas.create_line(bx, by, hx, hy, fill='#FFFACD', width=1)

        # ── Flat diamond bands ──
        for i in range(1, 5):
            t  = i / 5
            rx = bx + (hx - bx) * t; ry = by + (hy - by) * t
            sz = 5 if i % 2 == 0 else 3
            pts = [rx+pa*sz, ry+ps*sz, rx+ca*sz, ry+sa*sz,
                   rx-pa*sz, ry-ps*sz, rx-ca*sz, ry-sa*sz]
            canvas.create_polygon(*pts, fill='#FF8C00', outline='#B8860B', width=1)

        # ── Flame size (matches engine particle, no pulse — steady like live flames) ──
        fl_r = self.size * 0.55

        # ── Spear tip (elongated diamond) ──
        tl = self.size * 1.2; tw = self.size * 0.26
        canvas.create_polygon(
            hx+2,                    hy+2,
            hx+pa*tw-ca*(tl*0.35)+2, hy+ps*tw-sa*(tl*0.35)+2,
            hx+ca*tl+2,              hy+sa*tl+2,
            hx-pa*tw-ca*(tl*0.35)+2, hy-ps*tw-sa*(tl*0.35)+2,
            fill='#3a2800', outline='')
        canvas.create_polygon(
            hx,                    hy,
            hx+pa*tw-ca*(tl*0.35), hy+ps*tw-sa*(tl*0.35),
            hx+ca*tl,              hy+sa*tl,
            hx-pa*tw-ca*(tl*0.35), hy-ps*tw-sa*(tl*0.35),
            fill='#B8860B', outline='#FFD700', width=2)
        canvas.create_polygon(
            hx, hy,
            hx+pa*(tw*0.5)-ca*(tl*0.3), hy+ps*(tw*0.5)-sa*(tl*0.3),
            hx+ca*tl,                    hy+sa*tl,
            hx-pa*(tw*0.5)-ca*(tl*0.3), hy-ps*(tw*0.5)-sa*(tl*0.3),
            fill='#FFD700', outline='')

        # ── Side prongs cradling the flame ──
        for side in (-1, 1):
            p0x = hx + ca*(tl*0.30) + pa*side*(tw*1.2)
            p0y = hy + sa*(tl*0.30) + ps*side*(tw*1.2)
            p1x = hx + ca*(tl*0.62) + pa*side*(fl_r+6)
            p1y = hy + sa*(tl*0.62) + ps*side*(fl_r+6)
            p2x = hx + ca*(tl*1.05) + pa*side*(fl_r*0.7)
            p2y = hy + sa*(tl*1.05) + ps*side*(fl_r*0.7)
            canvas.create_line(p0x+1,p0y+1,p1x+1,p1y+1, fill='#3a2800', width=7, capstyle='round')
            canvas.create_line(p1x+1,p1y+1,p2x+1,p2y+1, fill='#3a2800', width=4, capstyle='round')
            canvas.create_line(p0x,p0y,p1x,p1y, fill='#B8860B', width=6, capstyle='round')
            canvas.create_line(p1x,p1y,p2x,p2y, fill='#B8860B', width=3, capstyle='round')
            canvas.create_line(p0x,p0y,p1x,p1y, fill='#FFD700', width=2, capstyle='round')
            canvas.create_line(p1x,p1y,p2x,p2y, fill='#FFD700', width=1, capstyle='round')
            canvas.create_oval(p2x-3,p2y-3,p2x+3,p2y+3, fill='#FFD700', outline='#FF8C00')

        # ── Flame tip — EXACT engine flame particle, rotated to point forward ──
        # Engine draws: base (x-r,y)/(x+r,y) tip (x, y-r*1.5)
        # We rotate: "up" (-y) -> staff forward (ca,sa); "horizontal" (x) -> perp (pa,ps)
        # Flame base sits at shaft end (hx,hy), tip extends forward along staff
        fl_col = 'orange' if (int(now * 12) % 2 == 0) else 'yellow'
        f_base_l = (hx - pa*fl_r, hy - ps*fl_r)   # left base corner
        f_base_r = (hx + pa*fl_r, hy + ps*fl_r)   # right base corner
        f_tip    = (hx + ca*fl_r*1.5, hy + sa*fl_r*1.5)  # tip (forward)
        canvas.create_polygon(
            f_base_l[0], f_base_l[1],
            f_base_r[0], f_base_r[1],
            f_tip[0],    f_tip[1],
            fill=fl_col, outline='')
        # Inner glow oval centred at base, r*0.6 — exactly as engine does it
        canvas.create_oval(
            hx - fl_r*0.6, hy - fl_r*0.6,
            hx + fl_r*0.6, hy + fl_r*0.6,
            fill='yellow', outline='')

        # ── Angular pommel ──
        px2 = bx-ca*5; py2 = by-sa*5
        pts_pom = [px2+pa*4,py2+ps*4, px2+ca*7,py2+sa*7, px2-pa*4,py2-ps*4, px2-ca*7,py2-sa*7]
        canvas.create_polygon(*pts_pom, fill='#B8860B', outline='#FFD700', width=1)
        canvas.create_polygon(*pts_pom[:6], fill='#FFD700', outline='')

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

        # Store base/tip for Lingering Aura
        if self.owner:
            self.owner._spear_base_x = shaft_end_x
            self.owner._spear_base_y = shaft_end_y
            self.owner._spear_tip_x  = tip_base_x + math.cos(self.angle) * tip_len
            self.owner._spear_tip_y  = tip_base_y + math.sin(self.angle) * tip_len

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

    def draw_arcane_bow(self, canvas):
        """Arcane Longbow — glowing purple/teal magical bow with runes and energy string."""
        bow_len = self.size * 2.0          # longer than normal bow
        perp_angle = self.angle + math.pi / 2

        forward_offset = 6
        bow_center_x = self.x + math.cos(self.angle) * forward_offset
        bow_center_y = self.y + math.sin(self.angle) * forward_offset

        top_x = bow_center_x - math.cos(perp_angle) * (bow_len / 2)
        top_y = bow_center_y - math.sin(perp_angle) * (bow_len / 2)
        bot_x = bow_center_x + math.cos(perp_angle) * (bow_len / 2)
        bot_y = bow_center_y + math.sin(perp_angle) * (bow_len / 2)

        curve_offset = 22
        mid_x = bow_center_x + math.cos(self.angle) * curve_offset
        mid_y = bow_center_y + math.sin(self.angle) * curve_offset

        # ── Outer glow pass ─────────────────────────────────────────────────
        canvas.create_line(top_x, top_y, mid_x, mid_y, bot_x, bot_y,
                           fill='#6600aa', width=11, smooth=True)
        canvas.create_line(top_x, top_y, mid_x, mid_y, bot_x, bot_y,
                           fill='#aa44ff', width=8, smooth=True)

        # ── Core limb (dark arcane wood) ────────────────────────────────────
        canvas.create_line(top_x, top_y, mid_x, mid_y, bot_x, bot_y,
                           fill='#1a002a', width=6, smooth=True)
        canvas.create_line(top_x, top_y, mid_x, mid_y, bot_x, bot_y,
                           fill='#3a0060', width=4, smooth=True)

        # ── Rune dots along the limb ────────────────────────────────────────
        for t in [0.2, 0.4, 0.6, 0.8]:
            rx = top_x + (bot_x - top_x) * t
            ry = top_y + (bot_y - top_y) * t
            # Slight push toward mid
            rx += (mid_x - bow_center_x) * 0.3 * (1 - abs(t - 0.5) * 2)
            ry += (mid_y - bow_center_y) * 0.3 * (1 - abs(t - 0.5) * 2)
            canvas.create_oval(rx - 4, ry - 4, rx + 4, ry + 4,
                               fill='#cc66ff', outline='#ffffff', width=1)
            canvas.create_oval(rx - 2, ry - 2, rx + 2, ry + 2,
                               fill='white', outline='')

        # ── Tip caps (glowing orbs at bow ends) ─────────────────────────────
        for tx2, ty2 in [(top_x, top_y), (bot_x, bot_y)]:
            canvas.create_oval(tx2 - 6, ty2 - 6, tx2 + 6, ty2 + 6,
                               fill='#9933ff', outline='#ddaaff', width=2)
            canvas.create_oval(tx2 - 3, ty2 - 3, tx2 + 3, ty2 + 3,
                               fill='white', outline='')

        # ── Energy bowstring (teal glowing line) ────────────────────────────
        canvas.create_line(top_x, top_y, bot_x, bot_y,
                           fill='#003344', width=4)
        canvas.create_line(top_x, top_y, bot_x, bot_y,
                           fill='#00ccff', width=2)
        canvas.create_line(top_x, top_y, bot_x, bot_y,
                           fill='#aaffff', width=1)

        # ── Arcane arrow (glowing cyan shaft) ───────────────────────────────
        arrow_len = self.size * 1.3
        arrow_end_x = self.x + math.cos(self.angle) * arrow_len
        arrow_end_y = self.y + math.sin(self.angle) * arrow_len
        arrow_start_x = self.x - math.cos(self.angle) * 5
        arrow_start_y = self.y - math.sin(self.angle) * 5

        canvas.create_line(arrow_start_x, arrow_start_y, arrow_end_x, arrow_end_y,
                           fill='#004466', width=5)
        canvas.create_line(arrow_start_x, arrow_start_y, arrow_end_x, arrow_end_y,
                           fill='#00ccff', width=3)
        canvas.create_line(arrow_start_x, arrow_start_y, arrow_end_x, arrow_end_y,
                           fill='#aaffff', width=1)

        # Glowing arrowhead
        tip_perp = self.angle + math.pi / 2
        tip_left_x  = arrow_end_x + math.cos(tip_perp) * 5
        tip_left_y  = arrow_end_y + math.sin(tip_perp) * 5
        tip_right_x = arrow_end_x - math.cos(tip_perp) * 5
        tip_right_y = arrow_end_y - math.sin(tip_perp) * 5
        tip_point_x = arrow_end_x + math.cos(self.angle) * 11
        tip_point_y = arrow_end_y + math.sin(self.angle) * 11
        canvas.create_polygon([tip_point_x, tip_point_y,
                               tip_left_x, tip_left_y,
                               tip_right_x, tip_right_y],
                              fill='#00eeff', outline='#aaffff', width=1)

        # ── Centre grip ─────────────────────────────────────────────────────
        canvas.create_oval(bow_center_x - 7, bow_center_y - 7,
                           bow_center_x + 7, bow_center_y + 7,
                           fill='#220044', outline='#aa44ff', width=2)
        canvas.create_oval(bow_center_x - 4, bow_center_y - 4,
                           bow_center_x + 4, bow_center_y + 4,
                           fill='#9933ff', outline='')


    def draw_staff(self, canvas):
        staff_len = self.size * 3

        # Move the staff forward along the aim direction
        forward_offset = 5
        center_x = self.x + math.cos(self.angle) * forward_offset
        center_y = self.y + math.sin(self.angle) * forward_offset

        back_fraction  = 0.35
        front_fraction = 0.65
        staff_end_x = center_x - math.cos(self.angle) * staff_len * back_fraction
        staff_end_y = center_y - math.sin(self.angle) * staff_len * back_fraction
        sphere_x    = center_x + math.cos(self.angle) * staff_len * front_fraction
        sphere_y    = center_y + math.sin(self.angle) * staff_len * front_fraction

        # Small wood tip extending above the sphere
        tip_len = staff_len * 0.18
        tip_x = sphere_x + math.cos(self.angle) * tip_len
        tip_y = sphere_y + math.sin(self.angle) * tip_len

        # --- Shaft shadow ---
        canvas.create_line(staff_end_x+2, staff_end_y+2, sphere_x+2, sphere_y+2,
                           fill='#1a0d00', width=8)
        # --- Shaft outer (dark wood) ---
        canvas.create_line(staff_end_x, staff_end_y, sphere_x, sphere_y,
                           fill='#5C3310', width=7)
        # --- Shaft inner highlight (lighter grain) ---
        canvas.create_line(staff_end_x, staff_end_y, sphere_x, sphere_y,
                           fill='#8B5A2B', width=4)
        # --- Wood grain lines along shaft ---
        perp_cos = math.cos(self.angle + math.pi / 2)
        perp_sin = math.sin(self.angle + math.pi / 2)
        for t in (0.2, 0.45, 0.7):
            gx = staff_end_x + (sphere_x - staff_end_x) * t
            gy = staff_end_y + (sphere_y - staff_end_y) * t
            canvas.create_line(gx - perp_cos * 2, gy - perp_sin * 2,
                               gx + perp_cos * 2, gy + perp_sin * 2,
                               fill='#3B1F08', width=1)

        # --- Magic sphere (small orb at the top of the shaft) ---
        sphere_r = 7
        gem_col = getattr(self, 'gem_color', '#44aaff')
        # Outer glow
        canvas.create_oval(sphere_x - sphere_r - 4, sphere_y - sphere_r - 4,
                           sphere_x + sphere_r + 4, sphere_y + sphere_r + 4,
                           fill='', outline=gem_col, width=1, stipple='gray25')
        # Mid glow
        canvas.create_oval(sphere_x - sphere_r - 2, sphere_y - sphere_r - 2,
                           sphere_x + sphere_r + 2, sphere_y + sphere_r + 2,
                           fill='', outline=gem_col, width=1, stipple='gray50')
        # Sphere body
        canvas.create_oval(sphere_x - sphere_r, sphere_y - sphere_r,
                           sphere_x + sphere_r, sphere_y + sphere_r,
                           fill=gem_col, outline='white', width=1)
        # Specular highlight
        canvas.create_oval(sphere_x - sphere_r * 0.45, sphere_y - sphere_r * 0.55,
                           sphere_x + sphere_r * 0.15, sphere_y + sphere_r * 0.05,
                           fill='white', outline='')

        # --- Short wood tip above sphere ---
        canvas.create_line(sphere_x, sphere_y, tip_x, tip_y,
                           fill='#5C3310', width=5)
        canvas.create_line(sphere_x, sphere_y, tip_x, tip_y,
                           fill='#8B5A2B', width=3)
        # Rounded tip cap
        canvas.create_oval(tip_x - 3, tip_y - 3, tip_x + 3, tip_y + 3,
                           fill='#5C3310', outline='#3B1F08', width=1)

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
        """Draw beam: darkened core, near-white edge flanks, tip particles that hug the beam."""
        if not hasattr(self, '_tip_anim_t'):
            self._tip_anim_t = 0.0
        self._tip_anim_t += 0.15

        end_x = self.origin_x + math.cos(self.angle) * self.current_length
        end_y = self.origin_y + math.sin(self.angle) * self.current_length

        perp_cos = math.cos(self.angle + math.pi / 2)
        perp_sin = math.sin(self.angle + math.pi / 2)

        _btype = getattr(self, '_beam_type', 'mana_beam')

        if _btype == 'scorching_ray':
            # Scorching Ray: hot orange/red core with outer glow
            canvas.create_line(self.origin_x, self.origin_y, end_x, end_y,
                               fill='#ff2200', width=self.size + 4, capstyle='butt')
            canvas.create_line(self.origin_x, self.origin_y, end_x, end_y,
                               fill='#ff6600', width=self.size, capstyle='butt')
            canvas.create_line(self.origin_x, self.origin_y, end_x, end_y,
                               fill='#ffcc00', width=max(2, self.size // 3), capstyle='butt')
        elif _btype == 'ray_of_frost':
            # Ray of Frost: icy blue/cyan core with pale glow
            canvas.create_line(self.origin_x, self.origin_y, end_x, end_y,
                               fill='#0044aa', width=self.size + 4, capstyle='butt')
            canvas.create_line(self.origin_x, self.origin_y, end_x, end_y,
                               fill='#00aaff', width=self.size, capstyle='butt')
            canvas.create_line(self.origin_x, self.origin_y, end_x, end_y,
                               fill='#aaffff', width=max(2, self.size // 3), capstyle='butt')
        else:
            # Default mana beam
            canvas.create_line(self.origin_x, self.origin_y, end_x, end_y,
                               fill=self.color, width=self.size, capstyle='butt')

        # Tip particles — full beam width, beam colour, extruding forward
        if self.current_length >= self.max_length * 0.70:
            if _btype == 'scorching_ray':
                _tip_cols = ['#ff4400','#ff6600','#ffaa00','#ffff44','#ffffff']
            elif _btype == 'ray_of_frost':
                _tip_cols = ['#88eeff','#aaffff','cyan','#00ccff','#ffffff']
            else:
                _tip_cols = [self.color]
            for _s in range(30):
                _fd  = min(40, max(0, random.expovariate(1 / 7)))
                _lat = random.uniform(-self.size * 0.5, self.size * 0.5)
                _tr  = random.uniform(0.8, max(1.5, self.size * 0.18))
                _tpx = end_x + math.cos(self.angle)*_fd + perp_cos*_lat
                _tpy = end_y + math.sin(self.angle)*_fd + perp_sin*_lat
                canvas.create_oval(_tpx-_tr, _tpy-_tr, _tpx+_tr, _tpy+_tr,
                                   fill=random.choice(_tip_cols), outline='')


    def lighten_color(self, color):
        if color == 'red':    return '#ff6666'
        if color == 'blue':   return '#6666ff'
        if color == 'green':  return '#66ff66'
        if color == 'yellow': return '#ffffaa'
        return color

    def _near_white(self, color):
        if color == 'red':    return '#ffcccc'
        if color == 'blue':   return '#ccccff'
        if color == 'green':  return '#ccffcc'
        if color == 'yellow': return '#fffff0'
        return '#ffffff'

    def _darken_color(self, color):
        _map = {'yellow': '#886600', 'gold': '#775500', 'cyan': '#006666',
                'blue': '#001188', 'red': '#880000', 'green': '#005500',
                'white': '#888888', 'orange': '#883300', 'purple': '#440066'}
        if color in _map:
            return _map[color]
        if color.startswith('#') and len(color) == 7:
            try:
                r = int(color[1:3], 16) // 2
                g = int(color[3:5], 16) // 2
                b = int(color[5:7], 16) // 2
                return f'#{r:02x}{g:02x}{b:02x}'
            except ValueError:
                pass
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
    
    def __init__(self, name, item_type, rarity, stats=None, skills=None, soulbound=False, price=0, weapon_type=None, description=''):
        self.name = name
        self.item_type = item_type  # 'ring', 'necklace', 'armor', 'weapon', etc.
        self.rarity = rarity
        self.stats = stats or {}  # {'strength': 5, 'vitality': 3}
        self.skills = skills or []  # list of skill names this item grants
        self.soulbound = soulbound
        self.price = price
        self.weapon_type = weapon_type  # 'sword', 'spear', 'bow', 'staff', etc.
        self.description = description
            
    
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
            'weapon_type': self.weapon_type,  # ADD THIS
            'description': self.description
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
            weapon_type=data.get('weapon_type'),  # ADD THIS
            description=data.get('description', '')
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
                 skills=['Teleport'],
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
    # ── Ice Cavern cold-protection gear (sold by blacksmith) ─────────────────
    InventoryItem('Ice Shoes',    'boots',      'Uncommon', {'armour': 4, 'agility': 2},
                  price=350, description='Insulated soles — reduces Freezing to Chilling in the Ice Cavern.'),
    InventoryItem('Thick Fleece', 'chestplate', 'Uncommon', {'armour': 8, 'vitality': 3},
                  price=500, description='Heavy wool lining — grants full cold immunity in the Ice Cavern.'),
]
SHOP_ITEMS.extend(ARMOUR_ITEMS)



# ── ConsumableItem: usable potions / food ─────────────────────────────────────
class ConsumableItem:
    EMOJI = {
        'health_potion': '🧪', 'mana_potion': '💧',
        'elixir': '✨', 'bread': '🍞', 'meat': '🍖', 'stew': '🍲',
        'smoke_bomb': '💨', 'invisibility_potion': '👁', 'warp_scroll': '📜',
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
        if self.subtype == 'warp_scroll':
            import time as _time2
            player._warp_scroll_start  = _time2.time()
            player._warp_scroll_active = True
            player._warp_cx            = player.x   # anchor circle at cast position
            player._warp_cy            = player.y
            player._warp_particles     = []
            return True
        if self.subtype == 'smoke_bomb':
            # Flag the game to throw a smoke bomb projectile toward the mouse
            player._throw_smoke_bomb = True
            return True
        if self.subtype == 'invisibility_potion':
            now = time.time
            import time as _time
            now = _time.time()
            player._invisible = True
            player._invisible_end = now + 20.0
            player._invisible_from_potion = True
            if not hasattr(player, 'active_buffs'):
                player.active_buffs = []
            player.active_buffs.append({
                'emoji': '👁',
                'name': 'Invisibility',
                'desc': 'Enemies wander. Breaks on skill/item use.',
                'end': now + 20.0,
                'duration': 20.0,
                'str': 0, 'agi': 0, 'wil': 0,
            })
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
    ConsumableItem("Potion of Invisibility", "invisibility_potion", "Rare", price=200,
                   description="Enemies in the room enter a wander state for 20s. Breaks immediately if you use any skill or item."),
    ConsumableItem("Warp Scroll", "warp_scroll", "Rare", price=180,
                   description="After a 3-second channelling circle, teleports you to the entrance (0,0) of the current dungeon. Cannot be used in combat."),
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

class WeaponParticle:
    """Floating weapon pickup that bobs in place until the player walks over it."""
    def __init__(self, x, y, item):
        self.x = x + random.randint(-30, 30)
        self.y = y + random.randint(-30, 30)
        self.item = item          # InventoryItem to grant on pickup
        self.lifetime = 60.0     # disappears after 60s if not picked up
        self.size = 14
        self._bob = random.uniform(0, math.pi * 2)
        self._spin = random.uniform(0, math.pi * 2)

    def update(self, dt):
        self.lifetime -= dt
        self._bob   += dt * 2.5
        self._spin  += dt * 1.8
        return self.lifetime > 0

    def draw(self, canvas, sx, sy):
        by = math.sin(self._bob) * 3
        # Glow ring
        pulse = abs(math.sin(self._bob * 0.8)) * 4
        canvas.create_oval(sx - self.size - pulse, sy - self.size - pulse + by,
                           sx + self.size + pulse, sy + self.size + pulse + by,
                           fill='', outline='#aa66ff', width=2)
        # Sword silhouette (tiny) centred on particle
        _a = self._spin
        _ca = math.cos(_a); _sa = math.sin(_a)
        _pa = math.cos(_a + math.pi/2); _ps = math.sin(_a + math.pi/2)
        # Blade
        _bx1 = sx + _ca * 12 + by*0; _by1 = sy + _sa * 12 + by
        _bx2 = sx - _ca * 8;         _by2 = sy - _sa * 8 + by
        canvas.create_line(_bx2, _by2, _bx1, _by1, fill='#cccccc', width=4)
        canvas.create_line(_bx2, _by2, _bx1, _by1, fill='white',   width=2)
        # Guard
        _gx = sx - _ca * 2; _gy = sy - _sa * 2 + by
        canvas.create_line(_gx - _pa*7, _gy - _ps*7, _gx + _pa*7, _gy + _ps*7,
                           fill='#aaaaaa', width=3)
        # Rarity glow dot
        canvas.create_oval(sx - 4, sy - 4 + by, sx + 4, sy + 4 + by,
                           fill='#a335ee', outline='#cc66ff', width=1)
        # Name label
        canvas.create_text(sx, sy - self.size - 10 + by,
                           text=self.item.name, fill='#cc88ff',
                           font=('Arial', 7, 'bold'))

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

        elif self.role == "orbit":
            # Orbit around the player at a fixed radius, attacking nearby enemies
            _ospd = getattr(self, '_orbit_speed', 1.8)
            self._orbit_angle = getattr(self, '_orbit_angle', 0.0) + _ospd * dt
            _orad = getattr(self, '_orbit_radius', 60)
            self.x = player.x + math.cos(self._orbit_angle) * _orad
            self.y = player.y + math.sin(self._orbit_angle) * _orad

            # Fire at enemies via skills
            for sk in self.skills:
                if time.time() - sk['last_used'] >= sk['cooldown']:
                    if game.room.enemies:
                        sk['skill'](self, game)
                        sk['last_used'] = time.time()
                        break

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
