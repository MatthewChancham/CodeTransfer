import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tk_messagebox
import os
import json
import random
import math
import time
from constants import *
from utils import clamp, distance, resolve_overlap
from music import music_start, music_stop
from player import Player
from items import Item, InventoryItem, ConsumableItem, SHOP_ITEMS, CoinParticle, WeaponParticle
from entities import Room, Particle, SpawnPoint, NPC, SkillTreeWindow, GeneralSkillTreeWindow, Projectile
from enemies import Boss, bomb_explode

def _make_settings_overlay(parent):
    """Create a settings overlay window."""
    overlay = tk.Toplevel(parent)
    overlay.title("Settings")
    overlay.geometry("300x200")
    overlay.configure(bg='#1a1a2e')
    overlay.resizable(False, False)
    
    # Settings options (placeholder)
    tk.Label(overlay, text="Settings", font=("Arial", 14, "bold"), 
             bg='#1a1a2e', fg='white').pack(pady=10)
    tk.Label(overlay, text="Game settings will appear here.", 
             bg='#1a1a2e', fg='#999').pack(pady=20)
    
    tk.Button(overlay, text="Close", bg='#2a2a4e', fg='white',
              command=overlay.destroy).pack(pady=10)
    
    return overlay

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

        # ── Settings button (top-right corner of game canvas) ──────────────────
        self._dungeon_settings_overlay = None
        def _toggle_dungeon_settings():
            if self._dungeon_settings_overlay and self._dungeon_settings_overlay.winfo_exists():
                self._dungeon_settings_overlay.destroy()
                self._dungeon_settings_overlay = None
            else:
                self._dungeon_settings_overlay = _make_settings_overlay(_cv_frame)
        _settings_btn = tk.Button(_cv_frame, text="⚙️", font=("Arial", 13),
                                  bg='#1a1a2e', fg='white', activebackground='#2a2a4e',
                                  bd=0, padx=5, pady=3, cursor='hand2',
                                  command=_toggle_dungeon_settings)
        _settings_btn.place(x=WINDOW_W - 42, y=4)

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
        self.bind("e", lambda e: self.rotate_beam(-2))   # rotate beam left (also E = Analysis)
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
        self.active_hotbar_slot = 1  # which slot (1-5) is selected; slot 1 = weapon display
        # Item hotbar (4 slots for consumables, T/Y/U/R) — restore from saved data if available
        saved_hb = getattr(player, '_saved_hotbar', [None, None, None]) or [None, None, None]
        self.hotbar_items = []
        for slot_data in saved_hb:
            if slot_data is None:
                self.hotbar_items.append(None)
            elif slot_data.get('consumable'):
                self.hotbar_items.append(ConsumableItem.from_dict(slot_data))
            else:
                self.hotbar_items.append(InventoryItem.from_dict(slot_data))
        # Ensure exactly 4 slots
        while len(self.hotbar_items) < 3:
            self.hotbar_items.append(None)
        self.hotbar_items = self.hotbar_items[:3]
        self.active_item_slot = 0                # 0,1,2  (T/Y/U)
        self._weapon_slot_active = True          # True when R is pressed (weapon slot highlighted)
        self.active_weapon_skill_slot = 0        # which of the 3 weapon skill slots is selected (Z/X)
        # Coin particles (world-space)
        self.coin_particles = []
        # Weapon particles (world-space pickups)
        self.weapon_particles = []
        # Boss-defeated flags per dungeon — unlocks treasure room below boss room
        self.boss_defeated = {}
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
                'offhand':    '#446688',
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
            ("chestplate", "👕",   "Chest Armour"),
            ("offhand",    "🛡",   "Offhand / Shield"),
            ("leggings",   "👖",  "Leggings"),
            ("boots",      "👢",  "Boots"),
            ("gloves",     "🧤",  "Gloves"),
            ("ring",       "💍",  "Ring"),
            ("necklace",   "📿",  "Necklace"),
            ("map",        "📜",  "Map"),
        ]
        N_EQ = len(EQ_SLOTS)

        # Canvas size
        EQ_W  = STEP + GAP + 128         # equipment slot + label column (wider to avoid overlap)
        BAG_W = GRID_C * STEP + GAP
        HB_W  = (1 + 3) * STEP + GAP     # weapon slot + 3 item slots
        WIN_W = EQ_W + GAP*2 + BAG_W + 20
        TOP   = 36                        # space for coin/stat bar at top
        WIN_H = max(N_EQ * STEP + 120, GRID_R * STEP + 220) + TOP + STEP + 16  # extra row for trash slot

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
                'chestplate': '👕',  'leggings':   "👖",
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
            elif key[0] == 'trash':
                # Trash slot: bottom-right of bag panel, pushed well below the hotbar row
                x0 = EQ_W + GAP + (GRID_C - 1) * STEP
                y0 = TOP + GAP + GRID_R * STEP + GAP*3 + 28 + STEP*2 + GAP*4
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
                           text="HOTBAR  [R=weapon · T/Y/U=items]  —  Z/X+RClick=weapon skills",
                           fill="#8888aa", font=("Arial",8), anchor='w')

            # Weapon slot (far-left of hotbar, key 'wep')
            wkey = ('wep', 0)
            x0, y0, x1, y1 = slot_rect(wkey)
            weap = get_eq_item('weapon')
            sel  = selected_key[0] == wkey
            bg_  = C_SEL if sel else "#2a1a2e"
            cv.create_rectangle(x0, y0, x1, y1, fill=bg_, outline="#ffcc44", width=2)
            cv.create_text((x0+x1)//2, y0-4, text="R / WEP", fill="#ffcc44",
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
                item = self.hotbar_items[i] if i < len(self.hotbar_items) else None
                sel  = selected_key[0] == key
                active = (not getattr(self,'_weapon_slot_active',False)) and (i == self.active_item_slot)
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

            # ── Trash / Discard slot ──────────────────────────────────────────
            tx0, ty0, tx1, ty1 = slot_rect(('trash', 0))
            t_sel = selected_key[0] == ('trash', 0)
            t_col = '#5a1010' if not t_sel else '#aa2222'
            cv.create_rectangle(tx0, ty0, tx1, ty1,
                                fill=t_col, outline='#cc3333', width=2)
            cv.create_text((tx0+tx1)//2, (ty0+ty1)//2,
                           text="🗑", font=("Arial", 22), fill='#ff4444')
            cv.create_text((tx0+tx1)//2, ty0 - 4,
                           text="DISCARD", fill="#cc4444",
                           font=("Arial", 7, "bold"), anchor='s')
            cv.create_text(tx0 - 6, (ty0+ty1)//2,
                           text="← drag item here to delete",
                           fill="#884444", font=("Arial", 7), anchor='e')

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
            # Item hotbar slots T/Y/U (offset by STEP because of wep slot)
            for i in range(3):
                key = ('hb', i)
                x0,y0,x1,y1 = slot_rect(key)
                x0+=STEP; x1+=STEP
                if x0<=mx<=x1 and y0<=my<=y1:
                    return key
            # Trash slot
            x0,y0,x1,y1 = slot_rect(('trash', 0))
            if x0<=mx<=x1 and y0<=my<=y1:
                return ('trash', 0)
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

            # ── Discard / Trash slot ─────────────────────────────────────────
            if dst_type == 'trash':
                # Soulbound items can never be deleted
                if getattr(src_item, 'soulbound', False):
                    tkinter.messagebox.showwarning(
                        "Cannot Discard",
                        f'"{src_item.name}" is Soulbound and cannot be discarded.')
                    return False
                # Confirmation prompt so the player can't do it by accident
                confirmed = tkinter.messagebox.askyesno(
                    "Discard Item",
                    f'Are you sure you want to permanently discard\n"{src_item.name}"?\n\nThis cannot be undone.',
                    icon='warning')
                if not confirmed:
                    return False
                # Remove from wherever it currently lives
                if src_type == 'eq':
                    self.player.unequip_item(src_item)
                    if src_item in self.player.inventory:
                        self.player.inventory.remove(src_item)
                elif src_type == 'bag':
                    if src_item in self.player.inventory:
                        self.player.inventory.remove(src_item)
                elif src_type == 'hb':
                    self.hotbar_items[src[1]] = None
                elif src_type == 'wep':
                    self.player.unequip_item(src_item)
                    if src_item in self.player.inventory:
                        self.player.inventory.remove(src_item)
                return True

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
            if self.dead:
                return
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
        # ── Prevent double-opening the same shop ─────────────────────────────
        if getattr(self, '_npc_shop_open', False):
            return
        # Track which NPC's shop is currently open
        self._npc_shop_open = True
        self._npc_shop_npc  = npc   # remember who owns the open shop
        npc._shop_open = True       # freeze the NPC while trading

        shop_win = tk.Toplevel(self)
        shop_win.title(f"{npc.name}'s Shop")
        shop_win.geometry("700x600")
        shop_win.configure(bg="#1a1a1a")

        # ── Close helper ─────────────────────────────────────────────────────
        def _close_shop(event=None):
            self._npc_shop_open = False
            self._npc_shop_npc  = None
            npc._shop_open = False  # unfreeze NPC
            try:
                shop_win.destroy()
            except Exception:
                pass

        shop_win.protocol("WM_DELETE_WINDOW", _close_shop)
        # Keypress on the MAIN window closes the shop
        _close_bind_id = self.bind("<Key>", lambda e: _close_shop(), add=True)
        shop_win.bind("<Key>", lambda e: _close_shop())

        def _on_shop_destroy(event=None):
            self._npc_shop_open = False
            self._npc_shop_npc  = None
            try:
                self.unbind("<Key>", _close_bind_id)
            except Exception:
                pass
        shop_win.bind("<Destroy>", _on_shop_destroy)

        # Hint at bottom
        tk.Label(shop_win, text="Press any key to close  •  Walk away to auto-close",
                 bg="#1a1a1a", fg="#555555", font=("Arial", 9, "italic")).pack(side='bottom', pady=4)

        # ── Coins display ─────────────────────────────────────────────────────
        coin_frame = tk.Frame(shop_win, bg="#2a2a2a")
        coin_frame.pack(fill='x', pady=10, padx=10)

        # Keep a reference to every (button, item) pair so we can refresh affordability
        _buy_buttons = []   # list of (tk.Button, shop_item)

        def _refresh_shop_ui():
            """Update coin label and grey-out / restore buy buttons."""
            try:
                if not shop_win.winfo_exists():
                    return
            except Exception:
                return
            # Coin label
            for w in coin_frame.winfo_children():
                w.destroy()
            tk.Label(coin_frame, text=f"💰 Your Coins: {self.player.coins}",
                     font=("Arial", 16, "bold"), bg="#2a2a2a", fg="gold").pack()
            # Button affordability
            for btn, shop_item in _buy_buttons:
                try:
                    if not btn.winfo_exists():
                        continue
                    if self.player.coins >= shop_item.price:
                        btn.config(bg='#5cb85c', fg='white', state='normal',
                                   text=f"Buy\n{shop_item.price} 💰")
                    else:
                        btn.config(bg='#222222', fg='#555555', state='disabled',
                                   text=f"Buy\n{shop_item.price} 💰")
                except Exception:
                    pass

        _refresh_shop_ui()

        # ── Auto-close when player walks too far ─────────────────────────────
        SHOP_CLOSE_DISTANCE = 350   # generous — prevents instant-close on open

        def _shop_npc_pos():
            """Return the relevant (x,y) for the NPC — indoor_x/y when indoors."""
            if self.current_interior:
                return npc.indoor_x, npc.indoor_y
            return npc.x, npc.y

        def _check_distance():
            try:
                if not shop_win.winfo_exists():
                    return
                nx_, ny_ = _shop_npc_pos()
                dist = math.hypot(self.player.x - nx_, self.player.y - ny_)
                if dist > SHOP_CLOSE_DISTANCE:
                    _close_shop()
                    return
                # Also close if the player has left the building entirely
                if npc.indoor and not self.current_interior:
                    _close_shop()
                    return
                shop_win.after(200, _check_distance)
            except Exception:
                pass

        shop_win.after(200, _check_distance)

        # ── Shop items ────────────────────────────────────────────────────────
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
                tk.Label(item_frame, text=item.name,
                         font=("Arial", 14, "bold"),
                         bg="#2a2a2a", fg=item.get_color()).pack(anchor='w', padx=10, pady=5)
                tk.Label(item_frame, text=item.get_description(),
                         font=("Arial", 10), bg="#2a2a2a", fg="white",
                         justify='left').pack(anchor='w', padx=10, pady=2)

                # Buy button — starts grey if unaffordable
                can_afford = self.player.coins >= item.price
                buy_btn = tk.Button(
                    item_frame,
                    text=f"Buy\n{item.price} 💰",
                    bg='#5cb85c' if can_afford else '#222222',
                    fg='white'   if can_afford else '#555555',
                    font=("Arial", 11, "bold"),
                    state='normal' if can_afford else 'disabled',
                    width=8
                )
                buy_btn.pack(side='right', padx=10, pady=10)
                _buy_buttons.append((buy_btn, item))

                def make_buy_callback(shop_item, btn_ref):
                    def callback():
                        if self.player.coins < shop_item.price:
                            return   # button should already be disabled; safety check
                        self.player.coins -= shop_item.price
                        # Consumables: stack if same item exists, else place fresh
                        if isinstance(shop_item, ConsumableItem):
                            stacked = False
                            for idx in range(3):
                                hb = self.hotbar_items[idx]
                                if hb is not None and hb.name == shop_item.name:
                                    hb.count += 1
                                    stacked = True; break
                            if not stacked:
                                for it in self.player.inventory:
                                    if isinstance(it, ConsumableItem) and it.name == shop_item.name:
                                        it.count += 1
                                        stacked = True; break
                            if not stacked:
                                placed = False
                                for idx in range(3):
                                    if self.hotbar_items[idx] is None:
                                        new_c = ConsumableItem.from_dict(shop_item.to_dict())
                                        new_c.count = 1
                                        self.hotbar_items[idx] = new_c
                                        placed = True; break
                                if not placed:
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
                        # Refresh all buttons + coin label after every purchase
                        _refresh_shop_ui()
                    return callback

                buy_btn.config(command=make_buy_callback(item, buy_btn))

    def enter_dungeon(self, dungeon_id):
        """Switch from town to dungeon"""
        print(f"DEBUG: Attempting to enter dungeon {dungeon_id}")
        
        self.dungeon_id = dungeon_id
        print(f"DEBUG: self.dungeon_id set to {self.dungeon_id}")
        
        self.room_row = 0
        self.room_col = 0
        self.dungeon = {}
        # Reset boss-defeated flag for this dungeon so the treasure-room door
        # starts locked again on every fresh entry.
        self.boss_defeated[dungeon_id] = False
        self.room = self.get_room(0, 0)
        
        print(f"DEBUG: Room created with dungeon_id = {self.room.row}, is_town = {getattr(self.room, 'is_town', False)}")
        print(f"DEBUG: Room has {len(self.room.enemies)} enemies")
        
        self.player.x = WINDOW_W // 2
        self.player.y = WINDOW_H // 2
        
        self.projectiles.clear()
        self.particles.clear()
        
        # Dungeon — no camera offset
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

    def _jump_to_skill_mgmt_page(self, page_num):
        """Ensure the new skill-management page tab exists and is selected.

        Always sets _pending_page_select so open_combined_skill_page() knows
        which tab to jump to (covers both open and closed-window cases).

        If the window is currently open, schedule a full rebuild via after(80)
        so it fires after the current click-event fully finishes.  Rebuilding is
        the only reliably race-free approach — notebook.select() called in the
        same tick as notebook.insert() can be silently overridden by Tkinter's
        internal notebook event queue.  The rebuilt window finds _pending_page_select
        and auto-selects the correct tab.
        """
        self._pending_page_select = page_num

        win = getattr(self, '_combined_win', None)
        if win is None:
            return
        try:
            if not win.winfo_exists():
                return
        except Exception:
            return

        # Window is open — rebuild it after the click event finishes
        def _rebuild():
            try:
                w = getattr(self, '_combined_win', None)
                if w is not None and w.winfo_exists():
                    w.destroy()
                self._combined_win = None
            except Exception:
                pass
            # _pending_page_select is still set; open_combined_skill_page honours it
            self.open_combined_skill_page()

        self.after(80, _rebuild)

    def open_combined_skill_page(self):
        """Open a single tabbed window: Inventory + Skill Tree + Skill Management."""
        win = tk.Toplevel(self)
        self._combined_win = win
        win.title("Inventory & Skills")
        win.geometry("920x800")
        win.configure(bg="#0d0d1a")

        def on_win_close():
            self._combined_win = None
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", on_win_close)

        notebook = ttk.Notebook(win)
        notebook.pack(fill='both', expand=True, padx=6, pady=6)

        # ── Wild Shape management tab builder ─────────────────────────────────
        def _build_wild_shape_mgmt(container):
            for w in container.winfo_children():
                w.destroy()
            p_ws = self.player
            BG     = '#0a120a'
            HDR_BG = '#0f1f0f'
            CARD   = '#152015'
            GOLD   = '#ffd700'
            container.configure(bg=BG)

            # Form-cost lookup by category
            _FORM_COSTS = {'Beast': 2, 'Elemental': 3, 'Monster': 6}

            # Header
            hdr = tk.Frame(container, bg=HDR_BG)
            hdr.pack(fill='x', padx=6, pady=(6,0))
            tk.Label(hdr, text='🐾  Wild Shape — Form Assignments',
                     font=('Arial', 13, 'bold'), bg=HDR_BG, fg=GOLD).pack(side='left', padx=10, pady=6)
            fp_label = tk.Label(hdr,
                     text=f'🔮 Form Points: {p_ws.form_points}',
                     font=('Arial', 10, 'bold'), bg=HDR_BG, fg='#88ffcc')
            fp_label.pack(side='right', padx=10)
            tk.Label(hdr,
                     text='Assign forms to slots 1-5 • Press 6 in-game to open the form hotbar • Press the slot key to transform',
                     font=('Arial', 8, 'italic'), bg=HDR_BG, fg='#779977').pack(side='left', padx=6)

            outer = tk.Frame(container, bg=BG)
            outer.pack(fill='both', expand=True, padx=6, pady=6)

            # Left side: 5 slot assignment rows
            left = tk.Frame(outer, bg=BG, width=300)
            left.pack(side='left', fill='y', padx=(0,6))
            left.pack_propagate(False)

            tk.Label(left, text='⌨  Slot Assignments', font=('Arial', 11, 'bold'),
                     bg=BG, fg='#aaffaa').pack(pady=(6,4), anchor='w', padx=6)

            slot_vars = {}   # slot -> StringVar
            slot_frames = {}

            def rebuild_slots():
                for w in left.winfo_children():
                    try:
                        if hasattr(w, '_slot_row'):
                            w.destroy()
                    except Exception:
                        pass

            def _make_clear(slot):
                def _do():
                    p_ws.wild_shape_form_slots[slot] = None
                    refresh_all()
                return _do

            slot_row_frames = []

            def build_slot_rows():
                for f in slot_row_frames:
                    try: f.destroy()
                    except Exception: pass
                slot_row_frames.clear()

                for slot_n in range(1, 6):
                    form_name = p_ws.wild_shape_form_slots.get(slot_n)
                    fd = next((f for f in WILD_SHAPE_FORMS if f['name'] == form_name), None) if form_name else None

                    row = tk.Frame(left, bg='#1a2a1a' if fd else '#111a11',
                                   relief='solid', bd=1)
                    row.pack(fill='x', padx=6, pady=3, ipady=4)
                    slot_row_frames.append(row)

                    col = fd['color'] if fd else '#336633'
                    # Slot number badge
                    tk.Label(row, text=f' {slot_n} ', font=('Arial', 13, 'bold'),
                             bg='#223322', fg='#aaffaa', relief='flat').pack(side='left', padx=(4,8))

                    if fd:
                        tk.Label(row, text=fd['icon'], font=('Arial', 16),
                                 bg='#1a2a1a').pack(side='left')
                        tk.Label(row, text=fd['name'], font=('Arial', 10, 'bold'),
                                 bg='#1a2a1a', fg=col).pack(side='left', padx=4)
                        tk.Button(row, text='✕ Clear', font=('Arial', 8),
                                  bg='#3a1515', fg='#ff8888', relief='flat',
                                  cursor='hand2', command=_make_clear(slot_n)).pack(side='right', padx=4)
                    else:
                        tk.Label(row, text='— empty —', font=('Arial', 9, 'italic'),
                                 bg='#111a11', fg='#446644').pack(side='left', padx=4)
                        tk.Label(row, text='← click a form →', font=('Arial', 8),
                                 bg='#111a11', fg='#335533').pack(side='right', padx=4)

            build_slot_rows()

            # Right side: form picker (scroll)
            right = tk.Frame(outer, bg=BG)
            right.pack(side='left', fill='both', expand=True)

            tk.Label(right, text='📋  Available Forms  (click to assign to next free slot)',
                     font=('Arial', 11, 'bold'), bg=BG, fg='#aaffaa').pack(pady=(6,4), anchor='w', padx=6)

            vsb2 = tk.Scrollbar(right, orient='vertical')
            vsb2.pack(side='right', fill='y')
            cv2  = tk.Canvas(right, bg=BG, highlightthickness=0, yscrollcommand=vsb2.set)
            cv2.pack(side='left', fill='both', expand=True)
            vsb2.config(command=cv2.yview)
            cv2.bind('<MouseWheel>', lambda e2: cv2.yview_scroll(int(-1*(e2.delta/120)), 'units'))

            sf2 = tk.Frame(cv2, bg=BG)
            cv2.create_window((0,0), window=sf2, anchor='nw')
            sf2.bind('<Configure>', lambda e2: cv2.configure(scrollregion=cv2.bbox('all')))

            CAT_COLORS = {'Beast': '#c8a832', 'Elemental': '#4090e0', 'Monster': '#c03030'}
            cats = {}
            for fd2 in WILD_SHAPE_FORMS:
                cats.setdefault(fd2['category'], []).append(fd2)

            form_card_frames = []

            def _make_assign(fd_ref):
                def _do():
                    if fd_ref['name'] not in getattr(p_ws, 'unlocked_forms', set()):
                        return
                    # Assign to first free slot
                    for s in range(1, 6):
                        if p_ws.wild_shape_form_slots.get(s) is None:
                            p_ws.wild_shape_form_slots[s] = fd_ref['name']
                            refresh_all()
                            return
                    # All slots full — assign to slot 5 (overwrite last)
                    p_ws.wild_shape_form_slots[5] = fd_ref['name']
                    refresh_all()
                return _do

            def _make_unlock(fd_ref):
                cost = _FORM_COSTS.get(fd_ref['category'], 2)
                def _do():
                    if fd_ref['name'] in getattr(p_ws, 'unlocked_forms', set()):
                        return
                    if p_ws.form_points < cost:
                        tk.messagebox.showwarning("Not Enough Form Points",
                            f"Unlocking {fd_ref['name']} costs {cost} Form Points.\n"
                            f"You have {p_ws.form_points}.", parent=container.winfo_toplevel())
                        return
                    p_ws.form_points -= cost
                    p_ws.unlocked_forms.add(fd_ref['name'])
                    p_ws.form_skill_levels[fd_ref['name']] = 1
                    fp_label.config(text=f'🔮 Form Points: {p_ws.form_points}')
                    refresh_all()
                return _do

            def _make_upgrade(fd_ref):
                def _do():
                    fname = fd_ref['name']
                    if fname not in getattr(p_ws, 'unlocked_forms', set()):
                        return
                    current_lvl = p_ws.form_skill_levels.get(fname, 1)
                    max_lvl = len(fd_ref['form_skills'])
                    if current_lvl >= max_lvl:
                        tk.messagebox.showinfo("Max Level", f"{fname} skills are fully upgraded!", parent=container.winfo_toplevel())
                        return
                    if p_ws.form_points < 1:
                        tk.messagebox.showwarning("Not Enough Form Points",
                            f"Upgrading a form skill costs 1 Form Point.\n"
                            f"You have {p_ws.form_points}.", parent=container.winfo_toplevel())
                        return
                    p_ws.form_points -= 1
                    p_ws.form_skill_levels[fname] = current_lvl + 1
                    fp_label.config(text=f'🔮 Form Points: {p_ws.form_points}')
                    refresh_all()
                return _do

            def build_form_cards():
                for f2 in form_card_frames:
                    try: f2.destroy()
                    except Exception: pass
                form_card_frames.clear()

                assigned_names = set(v for v in p_ws.wild_shape_form_slots.values() if v)
                unlocked = getattr(p_ws, 'unlocked_forms', set())

                for cat_name, forms in cats.items():
                    cat_col = CAT_COLORS.get(cat_name, '#888888')
                    unlock_cost = _FORM_COSTS.get(cat_name, 2)
                    chdr = tk.Frame(sf2, bg=BG)
                    chdr.pack(fill='x', padx=4, pady=(10,2))
                    form_card_frames.append(chdr)
                    tk.Label(chdr, text=f'── {cat_name} ──  ({unlock_cost} FP to unlock)', font=('Arial', 10, 'bold'),
                             bg=BG, fg=cat_col).pack(side='left', padx=4)

                    for fd3 in forms:
                        is_unlocked = fd3['name'] in unlocked
                        is_assigned = fd3['name'] in assigned_names
                        cbg  = '#1a3520' if is_assigned else (CARD if is_unlocked else '#100e0e')
                        card = tk.Frame(sf2, bg=cbg, relief='solid', bd=1,
                                        highlightbackground=cat_col if is_unlocked else '#442222', highlightthickness=1)
                        card.pack(fill='x', padx=6, pady=2, ipady=3)
                        form_card_frames.append(card)

                        # Icon + name
                        top2 = tk.Frame(card, bg=cbg)
                        top2.pack(fill='x', padx=4)
                        tk.Label(top2, text=fd3['icon'] if is_unlocked else '🔒', font=('Arial', 16),
                                 bg=cbg).pack(side='left')
                        fg_col = '#88ff88' if is_assigned else (fd3['color'] if is_unlocked else '#554444')
                        tk.Label(top2, text=fd3['name'], font=('Arial', 10, 'bold'),
                                 bg=cbg, fg=fg_col).pack(side='left', padx=4)
                        if is_assigned:
                            slot_num = next((s for s,n in p_ws.wild_shape_form_slots.items() if n==fd3['name']), '?')
                            tk.Label(top2, text=f'[Slot {slot_num}]', font=('Arial', 8),
                                     bg=cbg, fg='#88ff88').pack(side='left')

                        if is_unlocked:
                            # Show skill level and upgrade info
                            skill_lvl = p_ws.form_skill_levels.get(fd3['name'], 1)
                            max_lvl   = len(fd3['form_skills'])
                            unlocked_skills = fd3['form_skills'][:skill_lvl]
                            skills_preview  = '  ·  '.join(s['name'] for s in unlocked_skills)
                            locked_count    = max_lvl - skill_lvl
                            lock_str        = f'  +{locked_count} locked' if locked_count > 0 else '  (all unlocked)'
                            tk.Label(card, text=f"CD {fd3['cd']}s   |   {skills_preview}{lock_str}",
                                     font=('Arial', 8), bg=cbg, fg='#779977').pack(anchor='w', padx=4)
                            # Buttons row
                            btn_row = tk.Frame(card, bg=cbg)
                            btn_row.pack(fill='x', padx=4, pady=(2,0))
                            if not is_assigned:
                                tk.Button(btn_row, text='+ Assign to slot',
                                          font=('Arial', 8, 'bold'),
                                          bg='#224422', fg='#aaffaa', relief='flat',
                                          cursor='hand2',
                                          command=_make_assign(fd3)).pack(side='left', padx=(0,4))
                            if skill_lvl < max_lvl:
                                next_skill = fd3['form_skills'][skill_lvl]['name']
                                tk.Button(btn_row, text=f'⬆ Unlock "{next_skill}" (1 FP)',
                                          font=('Arial', 8, 'bold'),
                                          bg='#1a2a4a', fg='#88ccff', relief='flat',
                                          cursor='hand2',
                                          command=_make_upgrade(fd3)).pack(side='left', padx=2)
                        else:
                            # Locked form — show unlock button
                            tk.Label(card, text=f"Locked — costs {unlock_cost} Form Points to unlock",
                                     font=('Arial', 8, 'italic'), bg=cbg, fg='#664444').pack(anchor='w', padx=4)
                            tk.Button(card, text=f'🔓 Unlock ({unlock_cost} FP)',
                                      font=('Arial', 8, 'bold'),
                                      bg='#3a2200', fg='#ffaa44', relief='flat',
                                      cursor='hand2',
                                      command=_make_unlock(fd3)).pack(side='right', padx=4, pady=(2,2))

            build_form_cards()

            def refresh_all():
                build_slot_rows()
                build_form_cards()

        # ── Tab 1: Inventory (grid) ──────────────────────────────────────────
        inv_tab = tk.Frame(notebook, bg="#0e0e1c")
        notebook.add(inv_tab, text="  🎒  Inventory  ")
        self._build_inv_canvas(inv_tab)
        self._inv_tab_frame = inv_tab  # keep ref so we can rebuild on tab switch

        # ── Tab 2: Class Skill Tree ───────────────────────────────────────────
        tree_tab = tk.Frame(notebook, bg="#0d0d1a")
        notebook.add(tree_tab, text="  🌿  Skill Tree  ")
        stw = SkillTreeWindow.embed_in_frame(tree_tab, self, self.player, win)

        # ── Tab 3: General Skill Tree ─────────────────────────────────────────
        gen_tab = tk.Frame(notebook, bg="#0d0d1a")
        notebook.add(gen_tab, text="  🧠  General Skills  ")
        gtw = GeneralSkillTreeWindow.embed_in_frame(gen_tab, self, self.player, win)

        # ── Tab (Druid only): Wild Shape Forms ───────────────────────────────
        _ws_tab_ref = [None]
        if self.player.class_name == 'Druid' and 'Wild Shape' in getattr(self.player, 'tree_unlocked', set()):
            ws_tab = tk.Frame(notebook, bg='#0a120a')
            notebook.add(ws_tab, text="  🐾  Wild Shape  ")
            _build_wild_shape_mgmt(ws_tab)
            _ws_tab_ref[0] = ws_tab

        # ── Tab 4: Passive Skills ─────────────────────────────────────────────
        passive_tab = tk.Frame(notebook, bg="#1a1a2e")
        notebook.add(passive_tab, text="  🔷  Passive Skills  ")

        def build_passive_tab(container):
            for w in container.winfo_children():
                w.destroy()
            p_player = self.player
            tree_nodes = list(SKILL_TREES.get(p_player.class_name, [])) + list(GENERAL_SKILL_TREE)
            unlocked_passives = [n for n in tree_nodes
                                 if n['type'] == 'passive' and n['name'] in p_player.tree_unlocked]

            hdr2 = tk.Frame(container, bg="#1a1a2e")
            hdr2.pack(fill='x', padx=10, pady=8)
            tk.Label(hdr2, text="🔷  Unlocked Passive Skills",
                     font=("Arial", 14, "bold"), bg="#1a1a2e", fg="#88ccff").pack(side='left')
            tk.Label(hdr2, text="(always active unless toggled off — no hotbar slot needed)",
                     font=("Arial", 9, "italic"), bg="#1a1a2e", fg="#556677").pack(side='left', padx=8)

            pscr = tk.Canvas(container, bg="#1a1a2e", highlightthickness=0)
            psb  = tk.Scrollbar(container, orient="vertical", command=pscr.yview)
            psf  = tk.Frame(pscr, bg="#1a1a2e")
            psf.bind("<Configure>", lambda e2: pscr.configure(scrollregion=pscr.bbox("all")))
            pscr.create_window((0,0), window=psf, anchor="nw")
            pscr.configure(yscrollcommand=psb.set)
            psb.pack(side="right", fill="y")
            pscr.pack(side="left", fill="both", expand=True, padx=10, pady=4)
            pscr.bind("<MouseWheel>", lambda ev: pscr.yview_scroll(int(-1*(ev.delta/120)), 'units'))

            if not unlocked_passives:
                tk.Label(psf, text="No passive skills unlocked yet.\nUnlock them in the Skill Tree tab.",
                         font=("Arial", 11, "italic"), bg="#1a1a2e", fg="#666677",
                         justify='center').pack(pady=40)
            else:
                for node in unlocked_passives:
                    row2 = tk.Frame(psf, bg="#1e1e3a", padx=12, pady=8,
                                    relief="groove", bd=1)
                    row2.pack(fill="x", padx=6, pady=4)
                    is_on = p_player.passive_toggles.get(node['name'], True)
                    hf2 = tk.Frame(row2, bg="#1e1e3a")
                    hf2.pack(fill="x")
                    toggle_txt = " TOGGLEABLE"
                    badge_col  = "#2a6a2a" if is_on else "#6a2a2a"
                    tk.Label(hf2, text="🔷 " + node['name'],
                             font=("Arial", 12, "bold"), bg="#1e1e3a", fg="#aaddff").pack(side='left')
                    tk.Label(hf2, text=f"T{node['tier']}", font=("Arial", 9),
                             bg="#334455", fg="#88bbdd", padx=4).pack(side='left', padx=6)
                    status_lbl = tk.Label(hf2, text="ON" if is_on else "OFF",
                                          font=("Arial", 9, "bold"),
                                          bg=badge_col, fg="white", padx=6)
                    status_lbl.pack(side='right', padx=4)
                    tk.Label(row2, text=node['desc'], font=("Arial", 9),
                             bg="#1e1e3a", fg="#aaaacc",
                             wraplength=500, justify='left').pack(anchor='w', pady=(4,0))
                    # Toggle button — available for every passive skill
                    _SHIELD_PASSIVES = {'Kinetic Shell', 'Mage Armour', 'Barkskin'}
                    def _make_passive_toggle(nm, lbl_ref, row_ref, updates_armour=False):
                        def _do():
                            cur = p_player.passive_toggles.get(nm, True)
                            p_player.passive_toggles[nm] = not cur
                            new_on = not cur
                            lbl_ref.config(text="ON" if new_on else "OFF",
                                           bg="#2a6a2a" if new_on else "#6a2a2a")
                            # Recalculate armour / shield stats immediately
                            if updates_armour:
                                p_player.update_stats()
                        return _do
                    tk.Button(row2, text="Toggle On/Off",
                              font=("Arial", 9), bg="#334455", fg="white",
                              command=_make_passive_toggle(
                                  node['name'], status_lbl, row2,
                                  updates_armour=(node['name'] in _SHIELD_PASSIVES))
                              ).pack(anchor='e', pady=(4,0))

        build_passive_tab(passive_tab)

        # ── Identical Skill Management tabs — one per unlocked page ──────────
        has_keen_now   = 'Keen Mind'           in getattr(self.player, 'tree_unlocked', set())
        has_cogex_now  = 'Cognitive Expansion' in getattr(self.player, 'tree_unlocked', set())
        has_master_now = ('Master of Skills'   in getattr(self.player, 'tree_unlocked', set())
                          and self.player.passive_toggles.get('Master of Skills', True))

        # refs list so auto_refresh can trigger rebuilds
        _page_tab_refresh_refs = []

        def _build_full_page_mgmt(container, page_num, refresh_refs):
            """Skill management tab — one per page, identical layout to open_skill_page."""
            for w in container.winfo_children():
                w.destroy()

            p_player   = self.player
            start_slot = (page_num - 1) * 5 + 1   # global key for slot 1 on this page
            BG = "#1a1a1a"
            container.configure(bg=BG)

            # ── Active Skills (Keybinds) ──────────────────────────────────────
            active_box = tk.Frame(container, bg="#2a2a2a")
            active_box.pack(pady=10, padx=15, fill="x")

            tk.Label(active_box,
                     text=f"Active Skills — Page {page_num}  (Keys {start_slot}–{start_slot+4})",
                     font=("Arial", 14, "bold"),
                     bg="#2a2a2a", fg="#b0b0b0").pack(pady=5)

            active_frame = tk.Frame(active_box, bg="#2a2a2a")
            active_frame.pack(pady=5, fill="x")

            # keep ref for page 1 so refresh_active_skills() still works
            if page_num == 1:
                self.active_frame = active_frame

            cd_labels = []   # (label_widget, skill_dict)

            def build_active_rows(af=active_frame):
                for w in af.winfo_children():
                    w.destroy()
                nonlocal cd_labels
                cd_labels = []
                for slot in range(1, 6):
                    g_key = start_slot + slot - 1
                    row = tk.Frame(af, bg="#2a2a2a", padx=8, pady=5)
                    row.pack(fill="x", pady=3)

                    tk.Label(row, text=str(slot),
                             font=("Arial", 12, "bold"),
                             bg="#2a2a2a", fg="#b0b0b0", width=3
                             ).pack(side="left", padx=(0, 10))

                    assigned = next((sk for sk in p_player.unlocked_skills
                                     if sk.get("key") == g_key), None)
                    if assigned:
                        tk.Label(row, text=assigned['name'],
                                 font=("Arial", 12, "bold"),
                                 bg="#2a2a2a", fg="#b0b0b0"
                                 ).pack(side="left")
                        info_lbl = tk.Label(row, text="",
                                            font=("Arial", 10),
                                            bg="#2a2a2a", fg="#808080")
                        info_lbl.pack(side="right")
                        cd_labels.append((info_lbl, assigned))
                    else:
                        tk.Label(row, text="Empty",
                                 font=("Arial", 11, "italic"),
                                 bg="#2a2a2a", fg="#555555"
                                 ).pack(side="left")

            build_active_rows()

            # Live cooldown ticker
            def _tick(af=active_frame):
                try:
                    if not af.winfo_exists():
                        return
                    now = time.time()
                    for lbl, sk in cd_labels:
                        if not lbl.winfo_exists():
                            continue
                        base_cd   = sk.get('cooldown', 0)
                        mod       = sk.get('cooldown_mod', 1.0)
                        eff_cd    = base_cd * mod
                        remaining = eff_cd - (now - sk.get('last_used', 0))
                        if remaining <= 0:
                            lbl.config(
                                text=f"Key: {sk['key']}  |  Base CD: {base_cd:.6f}s  |  Trained CD: {eff_cd:.6f}s",
                                fg="#44ff88")
                        else:
                            lbl.config(
                                text=f"Key: {sk['key']}  |  Base CD: {base_cd:.6f}s  |  Trained CD: {eff_cd:.6f}s  |  ⏳ {remaining:.6f}s",
                                fg="#ff8844")
                    af.after(50, _tick)
                except Exception:
                    pass

            _tick()

            # ── Divider ───────────────────────────────────────────────────────
            tk.Frame(container, bg="#333333", height=2).pack(fill="x", pady=10)

            # ── Unlocked Skills (scrollable) ──────────────────────────────────
            unlocked_box = tk.Frame(container, bg="#2a2a2a")
            unlocked_box.pack(pady=10, padx=15, fill="both", expand=True)

            tk.Label(unlocked_box, text="Unlocked Skills",
                     font=("Arial", 14, "bold"),
                     bg="#2a2a2a", fg="#b0b0b0").pack(pady=5)

            canvas = tk.Canvas(unlocked_box, bg="#2a2a2a", highlightthickness=0)
            scrollbar = tk.Scrollbar(unlocked_box, orient="vertical",
                                     command=canvas.yview)
            sf_holder = [None]

            def rebuild(canvas=canvas, sf_holder=sf_holder,
                        page_num=page_num, start_slot=start_slot,
                        build_active_rows=build_active_rows):
                try:
                    if not canvas.winfo_exists():
                        return
                except Exception:
                    return
                if sf_holder[0]:
                    sf_holder[0].destroy()

                sf = tk.Frame(canvas, bg="#2a2a2a")
                sf_holder[0] = sf
                sf.bind("<Configure>",
                        lambda e: canvas.configure(
                            scrollregion=canvas.bbox("all")))
                canvas.create_window((0, 0), window=sf, anchor="nw")

                active_skills = [sk for sk in p_player.unlocked_skills
                                 if sk.get('type', 'active') != 'passive']

                for i, sk in enumerate(active_skills):
                    row = tk.Frame(sf, bg="#3a3a3a", padx=10, pady=10)
                    row.grid(row=i // 2, column=i % 2,
                             padx=10, pady=10, sticky="nsew")

                    tk.Label(row, text=sk['name'],
                             anchor="center",
                             font=("Arial", 11, "bold"),
                             bg="#3a3a3a", fg="#b0b0b0"
                             ).pack(fill="x", pady=(0, 5))

                    btn_frame = tk.Frame(row, bg="#3a3a3a")
                    btn_frame.pack()
                    for slot in range(1, 6):
                        g_key   = start_slot + slot - 1
                        is_here = (sk.get('key', 0) == g_key)
                        _sbg    = "#226622" if is_here else "#4a4a4a"

                        def _make_cb(s=slot, skill=sk, pg=page_num,
                                     bar=build_active_rows):
                            def _cb():
                                self.assign_skill(skill, s, pg)
                                rebuild()
                                try:
                                    bar()
                                except Exception:
                                    pass
                            return _cb

                        tk.Button(btn_frame, text=str(slot), width=3,
                                  font=("Arial", 10, "bold"),
                                  bg=_sbg, fg="#b0b0b0",
                                  activebackground="#5a5a5a",
                                  activeforeground="#b0b0b0",
                                  command=_make_cb()
                                  ).pack(side="left", padx=2)

                sf.grid_columnconfigure(0, weight=1)
                sf.grid_columnconfigure(1, weight=1)

            refresh_refs.append(rebuild)
            rebuild()

            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            canvas.bind('<MouseWheel>',
                        lambda ev: canvas.yview_scroll(
                            int(-1*(ev.delta/120)), 'units'))

        # Page 1 — always present
        mgmt_tab = tk.Frame(notebook, bg="#1a1a1a")
        notebook.add(mgmt_tab, text="  ⌨  Skill Page 1  ")
        _build_full_page_mgmt(mgmt_tab, 1, _page_tab_refresh_refs)

        # Store notebook + tab refs so _jump_to_skill_mgmt_page() can switch tabs directly
        self._skill_notebook   = notebook
        self._skill_mgmt_tabs  = {1: mgmt_tab}
        self._skill_page_build = _build_full_page_mgmt
        self._skill_page_refs  = _page_tab_refresh_refs

        if has_keen_now:
            keen_tab = tk.Frame(notebook, bg="#1a1a1a")
            notebook.add(keen_tab, text="  ⌨  Skill Page 2  ")
            _build_full_page_mgmt(keen_tab, 2, _page_tab_refresh_refs)
            self._skill_mgmt_tabs[2] = keen_tab

        if has_cogex_now:
            cogex_tab = tk.Frame(notebook, bg="#1a1a1a")
            notebook.add(cogex_tab, text="  ⌨  Skill Page 3  ")
            _build_full_page_mgmt(cogex_tab, 3, _page_tab_refresh_refs)
            self._skill_mgmt_tabs[3] = cogex_tab

        if has_master_now:
            master_tab = tk.Frame(notebook, bg="#1a1a1a")
            notebook.add(master_tab, text="  ⌨  Skill Page 4  ")
            _build_full_page_mgmt(master_tab, 4, _page_tab_refresh_refs)
            self._skill_mgmt_tabs[4] = master_tab

        # Track which page tabs have been added
        _page_tabs_added = [has_keen_now, has_cogex_now, has_master_now]   # [page2, page3, page4]
        def on_tab_changed(event):
            sel  = notebook.select()
            tabs = notebook.tabs()
            if sel == tabs[0]:   # Inventory
                if getattr(self.player, '_soulbound_evolved', False):
                    for w in inv_tab.winfo_children(): w.destroy()
                    self._build_inv_canvas(inv_tab)
                    self.player._soulbound_evolved = False
            elif sel == tabs[1]:   # Class Skill Tree
                stw._draw()
                stw.sp_label.config(text=f"Skill Points: {self.player.skill_points}")
            elif sel == tabs[2]:   # General Skill Tree
                gtw._draw()
                gtw.sp_label.config(text=f"General SP: {getattr(self.player, 'gen_skill_points', 0)}")
            elif sel == tabs[3]:   # Passive Skills
                build_passive_tab(passive_tab)
        notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

        # ── Live-refresh loop ─────────────────────────────────────────────────
        _last_tree_hash  = [None]
        _last_gen_hash   = [None]
        _last_mgmt_hash  = [None]

        def _tree_state_hash():
            return (self.player.skill_points, frozenset(self.player.tree_unlocked))

        def _mgmt_state_hash():
            return tuple((sk.get('name',''), sk.get('key', 0))
                         for sk in self.player.unlocked_skills)

        def auto_refresh():
            try:
                if not win.winfo_exists():
                    return
                sel  = notebook.select()
                tabs = notebook.tabs()

                # Dynamically add page tabs when newly unlocked mid-session
                has_keen_live   = 'Keen Mind'           in getattr(self.player, 'tree_unlocked', set())
                has_cogex_live  = 'Cognitive Expansion' in getattr(self.player, 'tree_unlocked', set())
                has_master_live = ('Master of Skills'   in getattr(self.player, 'tree_unlocked', set())
                                   and self.player.passive_toggles.get('Master of Skills', True))
                if has_keen_live and 2 not in self._skill_mgmt_tabs:
                    _page_tabs_added[0] = True
                    _new_keen = tk.Frame(notebook, bg="#2a2a2a")
                    notebook.insert(len(notebook.tabs()), _new_keen,
                                    text="  ⌨  Skill Page 2  ")
                    _build_full_page_mgmt(_new_keen, 2, _page_tab_refresh_refs)
                    self._skill_mgmt_tabs[2] = _new_keen
                if has_cogex_live and 3 not in self._skill_mgmt_tabs:
                    _page_tabs_added[1] = True
                    _new_cogex = tk.Frame(notebook, bg="#2a2a2a")
                    notebook.insert(len(notebook.tabs()), _new_cogex,
                                    text="  ⌨  Skill Page 3  ")
                    _build_full_page_mgmt(_new_cogex, 3, _page_tab_refresh_refs)
                    self._skill_mgmt_tabs[3] = _new_cogex
                if has_master_live and 4 not in self._skill_mgmt_tabs:
                    _page_tabs_added[2] = True
                    _new_master = tk.Frame(notebook, bg="#2a2a2a")
                    notebook.insert(len(notebook.tabs()), _new_master,
                                    text="  ⌨  Skill Page 4  ")
                    _build_full_page_mgmt(_new_master, 4, _page_tab_refresh_refs)
                    self._skill_mgmt_tabs[4] = _new_master

                # ── Pending page-jump (set by _jump_to_skill_mgmt_page) ───────
                # Runs from the main-loop poll so it's safely outside any click
                # handler that triggered the skill unlock.
                pending = getattr(self, '_pending_page_select', None)
                if pending == 'wild_shape':
                    # Rebuild the window so the Wild Shape tab appears then select it
                    try:
                        w = getattr(self, '_combined_win', None)
                        if w is not None and w.winfo_exists():
                            w.destroy()
                        self._combined_win = None
                    except Exception:
                        pass
                    self._pending_page_select = None
                    self.open_combined_skill_page()
                    return
                if pending is not None and pending in self._skill_mgmt_tabs:
                    try:
                        _t = self._skill_mgmt_tabs[pending]
                        if _t.winfo_exists():
                            notebook.select(_t)
                            self._pending_page_select = None
                    except Exception as _je:
                        print(f"[auto_refresh] page-jump error: {_je}")

                # Re-fetch tabs after any potential insertions above
                tabs = notebook.tabs()
                sel  = notebook.select()

                if len(tabs) > 1 and sel == tabs[1]:   # Class Skill Tree
                    h = _tree_state_hash()
                    if h != _last_tree_hash[0]:
                        stw._draw()
                        stw.sp_label.config(text=f"Skill Points: {self.player.skill_points}")
                        _last_tree_hash[0] = h
                elif len(tabs) > 2 and sel == tabs[2]:  # General Skill Tree
                    h = _tree_state_hash()
                    if h != _last_gen_hash[0]:
                        gtw._draw()
                        gtw.sp_label.config(text=f"General SP: {getattr(self.player, 'gen_skill_points', 0)}")
                        _last_gen_hash[0] = h
                else:
                    # Refresh skill-page tabs' scroll lists when assignments change
                    h = _mgmt_state_hash()
                    if h != _last_mgmt_hash[0]:
                        for fn in _page_tab_refresh_refs:
                            try:
                                fn()
                            except Exception:
                                pass
                        _last_mgmt_hash[0] = h
            except Exception:
                pass
            # Always reschedule — even if an exception occurred above the loop
            # must not stop or the new skill-page tabs will never appear.
            try:
                if win.winfo_exists():
                    win.after(150, auto_refresh)
            except Exception:
                pass

        # ── Honour any pending page-jump that was set while the window was closed ─
        # (When the window is open, auto_refresh handles this within 150 ms instead.)
        _initial_pending = getattr(self, '_pending_page_select', None)
        if _initial_pending is not None and _initial_pending in self._skill_mgmt_tabs:
            _tab_to_select = self._skill_mgmt_tabs[_initial_pending]
            win.after(200, lambda t=_tab_to_select:
                notebook.select(t) if notebook.winfo_exists() and t.winfo_exists() else None)
            self._pending_page_select = None

        auto_refresh()


    def open_skill_tree(self):
        """Open the visual skill tree window for the current player."""
        SkillTreeWindow(self, self.player)

    def open_wild_shape_window(self):
        """Open the Wild Shape form-selection window."""
        if getattr(self, '_wild_shape_win', None):
            try:
                if self._wild_shape_win.winfo_exists():
                    self._wild_shape_win.lift()
                    return
            except Exception:
                pass
        win = tk.Toplevel(self)
        win.title("Wild Shape — Choose a Form")
        win.geometry("860x660")
        win.configure(bg='#0a120a')
        self._wild_shape_win = win
        win.protocol("WM_DELETE_WINDOW", lambda: setattr(self, '_wild_shape_win', None) or win.destroy())
        WildShapeWindow.embed_in_frame(win, self, self.player)

    def _make_wild_shape_skills(self, form_name):
        """Build skill-dicts for a Wild Shape form using real, fully-implemented functions."""
        form_data = next((f for f in WILD_SHAPE_FORMS if f['name'] == form_name), None)
        if not form_data:
            return []

        result = []

        # ── Standalone real skill functions ──────────────────────────────────
        # Each is a self-contained (player, game) function with proper visuals.

        def _ws_fireball(p, g):
            """Real fireball — fire projectile toward mouse, explodes on hit."""
            if p.mana < 15: return
            p.mana -= 15
            mx, my = g.get_mouse_world_pos()
            ang = math.atan2(my - p.y, mx - p.x)
            g.spawn_projectile(p.x, p.y, ang, 8, 10, 12, 'orange',
                               p.wis * 8, 'player', ptype='fireball', stype='fire_proj')

        def _ws_icicle(p, g):
            """Real icicle — ice spike toward mouse, freezes on hit."""
            if p.mana < 15: return
            p.mana -= 15
            mx, my = g.get_mouse_world_pos()
            ang = math.atan2(my - p.y, mx - p.x)
            g.spawn_projectile(p.x, p.y, ang, 8, 10, 10, 'cyan',
                               p.wis * 6, 'player', ptype='icicle', stype='bolt1')

        def _ws_lightning_bolt(p, g):
            """Real lightning bolt — fast piercing bolt toward mouse, shocks."""
            if p.mana < 20: return
            p.mana -= 20
            mx, my = g.get_mouse_world_pos()
            ang = math.atan2(my - p.y, mx - p.x)
            g.spawn_projectile(p.x, p.y, ang, 15, 2, 12, 'yellow',
                               p.wis * 5, 'player', stype='lightning')

        def _ws_aoe_burst(color, radius=130, stun_dur=0.0):
            """Factory: AoE burst in a radius, optional stun."""
            def _fn(p, g, _c=color, _r=radius, _sd=stun_dur):
                if p.mana < 12: return
                p.mana -= 12
                dmg = max(1, p.wis * random.uniform(1.5, 2.5))
                for e in list(g.room.enemies):
                    if math.hypot(e.x - p.x, e.y - p.y) < _r:
                        g.damage_enemy(e, dmg)
                        if _sd > 0:
                            e._stun_until = time.time() + _sd
                for _ in range(22):
                    ang2 = random.uniform(0, 2*math.pi)
                    d    = random.uniform(15, _r)
                    g.particles.append(Particle(
                        p.x + math.cos(ang2)*d, p.y + math.sin(ang2)*d,
                        size=random.randint(5, 11), color=_c,
                        life=random.uniform(0.35, 0.8), rtype='basic'))
            return _fn

        def _ws_cone(color, arc=0.6, length=160):
            """Factory: cone attack toward mouse."""
            def _fn(p, g, _c=color, _a=arc, _l=length):
                if p.mana < 12: return
                p.mana -= 12
                mx, my = g.get_mouse_world_pos()
                base_ang = math.atan2(my - p.y, mx - p.x)
                dmg = max(1, p.wis * random.uniform(2.0, 3.5))
                for e in list(g.room.enemies):
                    dx, dy = e.x - p.x, e.y - p.y
                    dist   = math.hypot(dx, dy)
                    if dist < _l:
                        e_ang = math.atan2(dy, dx)
                        diff  = abs((e_ang - base_ang + math.pi) % (2*math.pi) - math.pi)
                        if diff < _a:
                            g.damage_enemy(e, dmg)
                for _ in range(28):
                    spread = random.uniform(-_a, _a)
                    d      = random.uniform(20, _l)
                    g.particles.append(Particle(
                        p.x + math.cos(base_ang + spread)*d,
                        p.y + math.sin(base_ang + spread)*d,
                        size=random.randint(4, 10), color=_c,
                        life=random.uniform(0.3, 0.7), rtype='basic'))
            return _fn

        def _ws_heal(heal_mult=3):
            """Factory: heal the player for wis * mult."""
            def _fn(p, g, _m=heal_mult):
                if p.mana < 10: return
                p.mana -= 10
                heal = max(5, int(p.wis * _m))
                p.hp  = min(p.max_hp, p.hp + heal)
                for _ in range(14):
                    ang2 = random.uniform(0, 2*math.pi)
                    d    = random.uniform(10, 45)
                    g.particles.append(Particle(
                        p.x + math.cos(ang2)*d, p.y + math.sin(ang2)*d,
                        size=random.randint(4, 8), color='#88ff88',
                        life=random.uniform(0.5, 1.1), rtype='basic'))
            return _fn

        def _ws_dash_strike(color, dmg_mult=3):
            """Factory: dash toward nearest enemy and hit hard."""
            def _fn(p, g, _c=color, _dm=dmg_mult):
                if p.mana < 10: return
                p.mana -= 10
                if not g.room.enemies: return
                target = min(g.room.enemies,
                             key=lambda e: math.hypot(e.x - p.x, e.y - p.y))
                ang    = math.atan2(target.y - p.y, target.x - p.x)
                p.x    = max(-2000, min(8000, target.x - math.cos(ang)*28))
                p.y    = max(-2000, min(8000, target.y - math.sin(ang)*28))
                g.damage_enemy(target, max(1, p.wis * _dm))
                for _ in range(10):
                    a2 = random.uniform(0, 2*math.pi)
                    g.particles.append(Particle(
                        p.x + math.cos(a2)*14, p.y + math.sin(a2)*14,
                        size=random.randint(4, 9), color=_c,
                        life=random.uniform(0.25, 0.55), rtype='basic'))
            return _fn

        def _ws_melee(color, dmg_mult=2, aoe=False, aoe_r=80):
            """Factory: melee swing, optionally AoE."""
            def _fn(p, g, _c=color, _dm=dmg_mult, _aoe=aoe, _r=aoe_r):
                if p.mana < 6: return
                p.mana -= 6
                mx, my = g.get_mouse_world_pos()
                base_ang = math.atan2(my - p.y, mx - p.x)
                dmg = max(1, p.wis * _dm)
                if _aoe:
                    for e in list(g.room.enemies):
                        if math.hypot(e.x - p.x, e.y - p.y) < _r:
                            g.damage_enemy(e, dmg)
                else:
                    if not g.room.enemies: return
                    target = min(g.room.enemies,
                                 key=lambda e: math.hypot(e.x - p.x, e.y - p.y))
                    if math.hypot(target.x - p.x, target.y - p.y) < 90:
                        g.damage_enemy(target, dmg)
                for _ in range(8):
                    spread = random.uniform(-0.45, 0.45)
                    d      = random.uniform(18, 55)
                    g.particles.append(Particle(
                        p.x + math.cos(base_ang + spread)*d,
                        p.y + math.sin(base_ang + spread)*d,
                        size=random.randint(5, 12), color=_c,
                        life=random.uniform(0.2, 0.5), rtype='basic'))
            return _fn

        def _ws_projectile(color, speed=9, dmg_mult=2, ptype='basic', stype='bolt1'):
            """Factory: aimed projectile toward mouse."""
            def _fn(p, g, _c=color, _sp=speed, _dm=dmg_mult, _pt=ptype, _st=stype):
                if p.mana < 8: return
                p.mana -= 8
                mx, my = g.get_mouse_world_pos()
                ang = math.atan2(my - p.y, mx - p.x)
                g.spawn_projectile(p.x, p.y, ang, _sp, 3.0, 10, _c,
                                   max(1, p.wis * _dm), 'player', ptype=_pt, stype=_st)
            return _fn

        def _ws_fear(p, g):
            """Dragon Roar: fear all enemies for 4s — they flee from player."""
            if p.mana < 20: return
            p.mana -= 20
            for e in list(g.room.enemies):
                e._fear_until  = time.time() + 4.0
                e._fear_from_x = p.x
                e._fear_from_y = p.y
            for _ in range(20):
                ang2 = random.uniform(0, 2*math.pi)
                d    = random.uniform(20, 110)
                g.particles.append(Particle(
                    p.x + math.cos(ang2)*d, p.y + math.sin(ang2)*d,
                    size=random.randint(6, 14), color='#ff4400',
                    life=random.uniform(0.5, 1.2), rtype='basic'))

        def _ws_venom_spray(p, g):
            """Hydra venom — poison all nearby enemies for 6s."""
            if p.mana < 14: return
            p.mana -= 14
            for e in list(g.room.enemies):
                if math.hypot(e.x - p.x, e.y - p.y) < 160:
                    e._poison_until  = time.time() + 6.0
                    e._poison_dps    = max(1, p.wis * 0.8)
                    g.damage_enemy(e, max(1, p.wis))
            for _ in range(16):
                ang2 = random.uniform(0, 2*math.pi)
                d    = random.uniform(10, 160)
                g.particles.append(Particle(
                    p.x + math.cos(ang2)*d, p.y + math.sin(ang2)*d,
                    size=random.randint(4, 9), color='#44dd44',
                    life=random.uniform(0.4, 0.9), rtype='basic'))

        def _ws_teleport_bolt(p, g):
            """Storm Surge — teleport to mouse position with lightning effect."""
            if p.mana < 18: return
            p.mana -= 18
            old_x, old_y = p.x, p.y
            mx, my = g.get_mouse_world_pos()
            p.x, p.y = mx, my
            # Trail particles
            steps = 12
            for i in range(steps):
                t = i / steps
                g.particles.append(Particle(
                    old_x + (mx - old_x)*t + random.uniform(-12,12),
                    old_y + (my - old_y)*t + random.uniform(-12,12),
                    size=random.randint(4,8), color='#aaccff',
                    life=random.uniform(0.2, 0.5), rtype='basic'))

        def _ws_shield_buff(color, duration=3.0, mult=8):
            """Factory: temporary shield equal to wis * mult."""
            def _fn(p, g, _c=color, _d=duration, _m=mult):
                if p.mana < 10: return
                p.mana -= 10
                bonus = int(p.wis * _m)
                p.shield = min(getattr(p, 'max_shield', 0) + bonus,
                               getattr(p, 'max_shield', 0) + bonus)
                p.max_shield = max(getattr(p, 'max_shield', 0), p.shield)
                for _ in range(12):
                    ang2 = random.uniform(0, 2*math.pi)
                    g.particles.append(Particle(
                        p.x + math.cos(ang2)*20, p.y + math.sin(ang2)*20,
                        size=random.randint(4, 8), color=_c,
                        life=random.uniform(0.4, 0.8), rtype='basic'))
            return _fn

        def _ws_regen(p, g):
            """Hydra Regenerate — rapid HP regen over 3s via buff."""
            if p.mana < 16: return
            p.mana -= 16
            if not hasattr(p, 'active_buffs'):
                p.active_buffs = []
            total_heal = int(p.wis * 10)
            p.active_buffs.append({
                'name': 'Regen', 'emoji': '💚', 'desc': 'Rapid regeneration',
                'end': time.time() + 3.0, 'duration': 3.0,
                'str': 0, 'agi': 0, 'wil': 0, 'con': 0,
                '_regen_per_s': total_heal / 3.0,
            })

        # ── Map skill name → function ────────────────────────────────────────
        # Used below to assign the right fn to each form skill slot.
        _SKILL_MAP = {
            # Fire Elemental
            'Fireball':       _ws_fireball,
            'Fire Burst':     _ws_aoe_burst('#ff6600', radius=140),
            'Immolate':       _ws_aoe_burst('#ff3300', radius=160, stun_dur=0),
            # Earth Elemental
            'Rock Throw':     _ws_projectile('#8b6030', speed=7, dmg_mult=3),
            'Earthquake':     _ws_aoe_burst('#886633', radius=180, stun_dur=1.2),
            'Stone Skin':     _ws_shield_buff('#8b6030', duration=2.0, mult=10),
            # Storm Elemental
            'Lightning Bolt': _ws_lightning_bolt,
            'Thunderclap':    _ws_aoe_burst('#80b0ff', radius=120, stun_dur=0.8),
            'Storm Surge':    _ws_teleport_bolt,
            # Water Elemental
            'Water Wave':     _ws_cone('#30a0e0', arc=0.5, length=180),
            'Tidal Surge':    _ws_aoe_burst('#4080cc', radius=150),
            'Healing Tide':   _ws_heal(heal_mult=5),
            # Ice Elemental
            'Icicle':         _ws_icicle,
            'Blizzard':       _ws_aoe_burst('#88eeff', radius=160, stun_dur=1.5),
            'Ice Armour':     _ws_shield_buff('#88eeff', duration=4.0, mult=8),
            # Eagle
            'Dive':           _ws_dash_strike('#c8a832', dmg_mult=2),
            'Talon Strike':   _ws_melee('#c8a832', dmg_mult=2),
            'Eagle Screech':  _ws_aoe_burst('#ffe060', radius=100, stun_dur=1.5),
            # Leopard
            'Pounce':         _ws_dash_strike('#d4a020', dmg_mult=3),
            'Claw Swipe':     _ws_melee('#d4a020', dmg_mult=1.5),
            'Feral Roar':     _ws_aoe_burst('#cc8800', radius=110, stun_dur=0),
            # Unicorn
            'Horn Charge':    _ws_dash_strike('#e070e0', dmg_mult=4),
            'Healing Light':  _ws_heal(heal_mult=3),
            'Purifying Aura': _ws_heal(heal_mult=6),
            # Turtle
            'Shell Bash':     _ws_melee('#4a9a4a', dmg_mult=2),
            'Withdraw':       _ws_shield_buff('#4a9a4a', duration=3.0, mult=12),
            'Tail Sweep':     _ws_melee('#4a9a4a', dmg_mult=1.5, aoe=True, aoe_r=100),
            # Dragon
            'Dragon Claw':    _ws_melee('#c03030', dmg_mult=6),
            'Dragon Fire':    _ws_cone('#ff4400', arc=0.65, length=200),
            'Dragon Roar':    _ws_fear,
            'Wing Buffet':    _ws_aoe_burst('#cc5500', radius=160),
            # Hydra
            'Hydra Bite':     _ws_melee('#206050', dmg_mult=1, aoe=False),
            'Venom Spray':    _ws_venom_spray,
            'Regenerate':     _ws_regen,
            'Tail Lash':      _ws_aoe_burst('#30806a', radius=90, stun_dur=1.0),
        }

        # Determine how many skills are available based on form_skill_levels
        skill_level = getattr(self.player, 'form_skill_levels', {}).get(form_name, 1)

        for i, fs in enumerate(form_data['form_skills']):
            if i >= skill_level:
                break  # only show skills up to the unlocked level
            sname = fs['name']
            fn    = _SKILL_MAP.get(sname)
            if fn is None:
                # Fallback: basic projectile in form colour
                fn = _ws_projectile(form_data.get('color', '#aaffaa'))

            result.append({
                'skill':        fn,
                'name':         sname,
                'key':          i + 1,
                'level':        1,
                'cooldown':     fs.get('cooldown', 1.0),
                'last_used':    0,
                'cooldown_mod': 1.0,
            })
        return result

    def enter_wild_shape(self, form_name):
        """Transform the player into the given Wild Shape form."""
        p = self.player
        form_data = next((f for f in WILD_SHAPE_FORMS if f['name'] == form_name), None)
        if not form_data:
            return
        # Block if form hasn't been unlocked with Form Points
        if form_name not in getattr(p, 'unlocked_forms', set()):
            return

        # Save original skills (copy list so unlock_skills can't clobber it)
        p._ws_saved_skills = list(p.unlocked_skills)

        # Apply stat scaling: set listed stats equal to wisdom
        p._ws_stat_bonuses = {}
        wis = p.wisdom
        _BUFF_SHORT = {
            'strength': 'str', 'agility': 'agi', 'will': 'wil',
            'constitution': 'con', 'vitality': 'vit',
            'intelligence': 'int', 'wisdom': 'wis',
        }
        buff_kwargs = {k: 0 for k in _BUFF_SHORT.values()}
        scaled_stats = []
        for stat in form_data.get('stat_scaling', []):
            old_val = getattr(p, stat, 0)
            p._ws_stat_bonuses[stat] = old_val
            gain = wis - old_val
            setattr(p, stat, wis)
            short = _BUFF_SHORT.get(stat)
            if short and gain != 0:
                buff_kwargs[short] = gain
            scaled_stats.append(f"{stat.title()}→{wis}")
        p.update_stats()

        # Push the scaling into active_buffs so the stats panel shows it
        if not hasattr(p, 'active_buffs'):
            p.active_buffs = []
        # Remove any previous Wild Shape buff
        p.active_buffs = [b for b in p.active_buffs if b.get('name') != 'Wild Shape']
        icon = form_data.get('icon', '🐾')
        desc_text = ', '.join(scaled_stats) if scaled_stats else 'No stat scaling'
        p.active_buffs.append({
            'name':     'Wild Shape',
            'emoji':    icon,
            'desc':     desc_text,
            'end':      float('inf'),   # permanent until exit
            'duration': float('inf'),
            **buff_kwargs,
        })

        # Replace hotbar with form skills
        form_skills = self._make_wild_shape_skills(form_name)
        p.unlocked_skills = form_skills

        p.wild_shape_form = form_name
        print(f"[Wild Shape] Entered form: {form_name}")

    def exit_wild_shape(self):
        """Revert to human form and restore original skills + stats."""
        p = self.player
        if not getattr(p, 'wild_shape_form', None):
            return

        # Restore stats
        for stat, old_val in getattr(p, '_ws_stat_bonuses', {}).items():
            setattr(p, stat, old_val)
        p.update_stats()

        # Remove Wild Shape buff from active_buffs
        if hasattr(p, 'active_buffs'):
            p.active_buffs = [b for b in p.active_buffs if b.get('name') != 'Wild Shape']

        # Restore skills
        if p._ws_saved_skills is not None:
            p.unlocked_skills = p._ws_saved_skills
            p._ws_saved_skills = None

        p.wild_shape_form = None
        p._ws_stat_bonuses = {}
        print("[Wild Shape] Exited form.")



    def refresh_active_skills(self):
        """Rebuild the active-skills display for Page 1 only.
        Page 2 / Page 3 each have their own tab with its own build_active_rows closure."""
        try:
            if not self.active_frame.winfo_exists():
                return
        except Exception:
            return

        for w in self.active_frame.winfo_children():
            w.destroy()

        p            = self.player
        key_to_skill = {sk.get('key', 0): sk for sk in p.unlocked_skills if sk.get('key', 0) > 0}
        cd_labels    = []

        # Always render only page 1 slots (keys 1-5).
        # Pages 2 and 3 live in their own notebook tabs, each with their own build_active_rows.
        for display_slot in range(1, 6):
            global_key = display_slot          # page 1 → keys 1-5
            row = tk.Frame(self.active_frame, bg="#2a2a2a", padx=8, pady=4)
            row.pack(fill="x", pady=2)

            tk.Label(row, text=f"{display_slot}", font=("Arial", 12, "bold"),
                     bg="#2a2a2a", fg="#b0b0b0", width=3).pack(side="left", padx=(0, 6))

            assigned_skill = key_to_skill.get(global_key)
            if assigned_skill:
                tk.Label(row, text=assigned_skill['name'],
                         font=("Arial", 12, "bold"), bg="#2a2a2a", fg="#b0b0b0").pack(side="left")
                info_label = tk.Label(row, text="", font=("Arial", 9),
                                       bg="#2a2a2a", fg="#808080")
                info_label.pack(side="right")
                cd_labels.append((info_label, assigned_skill))
            else:
                tk.Label(row, text="Empty", font=("Arial", 11, "italic"),
                         bg="#2a2a2a", fg="#444444").pack(side="left")

        # Live cooldown ticker
        def _tick_cooldowns():
            try:
                if not self.active_frame.winfo_exists():
                    return
                now = time.time()
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


    def assign_skill(self, skill, slot, page=1):
        """
        Assign a skill to display slot 1-5 on page 1-3.
        Stores key = slot + (page-1)*5 so every slot is globally unique (1-15).
        """
        global_key = slot + (page - 1) * 5
        # Clear any skill already occupying this global key
        for sk in self.player.unlocked_skills:
            if sk.get("key") == global_key:
                sk["key"] = 0
                sk["assigned_slot"] = None

        # Assign this skill to the chosen page + slot
        skill["key"]           = global_key
        skill["assigned_slot"] = global_key

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
            else:
                # ESC in dungeon: toggle the save/exit overlay
                self._show_dungeon_esc_panel = not getattr(self, '_show_dungeon_esc_panel', False)
        if e.keysym.lower() == 'o':
            self.toggle_combined_page()   # O = combined window (Inventory + Skill Tree + Skills)

        # Q — quit to desktop (works any time the ESC panel is showing)
        if e.keysym.lower() == 'q' and getattr(self, '_show_dungeon_esc_panel', False):
            try:
                self.master.destroy()
            except Exception:
                import sys; sys.exit(0)

        # E = Analysis skill (or beam rotate left if beam active and Analysis not available)
        # NOTE: the 'e' key also has an early handler above for interior interaction;
        # the Analysis / beam-rotate fires only in-dungeon so there is no conflict.
        if e.keysym.lower() == 'e':
            p = self.player
            analysis_sk = next((sk for sk in p.unlocked_skills if sk.get('name') == 'Analysis'), None)
            if analysis_sk and not self.dead and self.dungeon_id > 0:
                now_e = time.time()
                cd_e = analysis_sk.get('cooldown', 1.0)
                if now_e - analysis_sk.get('last_used', 0) >= cd_e:
                    if analysis_sk.get('skill'):
                        analysis_sk['skill'](p, self)
                    analysis_sk['last_used'] = now_e
            elif hasattr(self, "player_beam") and self.player_beam:
                self.player_beam.rotate(-0.05)

        # R = highlight weapon slot  |  T/Y/U = consumable slots 0/1/2
        if e.keysym.lower() == 'r':
            self._weapon_slot_active = True
        if e.keysym.lower() == 't':
            self._weapon_slot_active = False
            if hasattr(self, "player_beam") and self.player_beam:
                self.player_beam.rotate(0.05)   # beam rotate if active
            else:
                self.active_item_slot = 0
        if e.keysym.lower() == 'y':
            self._weapon_slot_active = False
            self.active_item_slot = 1
        if e.keysym.lower() == 'u':
            self._weapon_slot_active = False
            self.active_item_slot = 2

        if e.keysym.lower() == 'c':
            # Don't process C while a shop window is open
            if not getattr(self, '_npc_shop_open', False):
                if self.current_interior:
                    pass   # handled inside the draw/update loop when indoors
                elif self.nearby_npc:
                    self.interact_with_npc(self.nearby_npc)
                elif self.nearby_dungeon and self.dungeon_id == 0:
                    # Only allow dungeon entry from town (dungeon_id 0)
                    # Prevents 'C' from resetting the dungeon when already inside one
                    print(f"Entering dungeon {self.nearby_dungeon['dungeon_id']}")
                    self.enter_dungeon(self.nearby_dungeon['dungeon_id'])

        # E = interact with chest / objects indoors
        if e.keysym.lower() == 'e':
            self.keys['e'] = True

        # 1-5 selects skill hotbar slot (or triggers Wild Shape form if WS hotbar active)
        if e.keysym in ('1','2','3','4','5'):
            slot = int(e.keysym)
            p = self.player
            # Wild Shape hotbar mode: pressing 1-5 transforms into the assigned form
            if getattr(self, '_ws_hotbar_active', False) and not getattr(p, 'wild_shape_form', None):
                form_name = p.wild_shape_form_slots.get(slot)
                if form_name:
                    self.enter_wild_shape(form_name)
                    self._ws_hotbar_active = False  # auto-close WS hotbar on transform
                return
            self.active_hotbar_slot = slot

        # 6 — Wild Shape hotbar toggle (Druid) or cycle skill pages
        if e.keysym == '6':
            p = self.player
            has_wild_shape = ('Wild Shape' in getattr(p, 'tree_unlocked', set()))
            if p.class_name == 'Druid' and has_wild_shape:
                if getattr(p, 'wild_shape_form', None):
                    # Already transformed -> exit form, return to skill hotbar
                    self.exit_wild_shape()
                    self._ws_hotbar_active = False
                else:
                    # Toggle the Wild Shape form hotbar on/off
                    self._ws_hotbar_active = not getattr(self, '_ws_hotbar_active', False)
                return
            # Normal behaviour: cycle skill pages
            has_keen   = ('Keen Mind'           in getattr(p, 'tree_unlocked', set())
                         and p.passive_toggles.get('Keen Mind', True))
            has_cogex  = ('Cognitive Expansion' in getattr(p, 'tree_unlocked', set())
                         and p.passive_toggles.get('Cognitive Expansion', True))
            has_master = ('Master of Skills'    in getattr(p, 'tree_unlocked', set())
                         and p.passive_toggles.get('Master of Skills', True))
            max_page  = 4 if has_master else (3 if has_cogex else (2 if has_keen else 1))
            cur_page  = getattr(p, 'skill_page', 1)
            p.skill_page = (cur_page % max_page) + 1

        # Z / X — cycle weapon skill bar slot left / right
        if e.keysym.lower() in ('z', 'x'):
            ws  = getattr(self.player, 'weapon_skills', [])
            n   = max(len(ws), 1)
            cur = getattr(self, 'active_weapon_skill_slot', 0)
            if e.keysym.lower() == 'z':
                self.active_weapon_skill_slot = (cur - 1) % n
            else:
                self.active_weapon_skill_slot = (cur + 1) % n

    def on_canvas_click(self, event):
        # ── ESC panel: copy-button click ─────────────────────────────────────
        if getattr(self, '_show_dungeon_esc_panel', False):
            btn = getattr(self, '_esc_copy_btn', None)
            if btn:
                bx0, by0, bx1, by1 = btn
                if bx0 <= event.x <= bx1 and by0 <= event.y <= by1:
                    code = getattr(self, '_esc_panel_code', '')
                    if code:
                        try:
                            self.clipboard_clear()
                            self.clipboard_append(code)
                            self._esc_code_copied = True
                            # Reset the "Copied!" label after 2 s
                            self.after(2000, lambda: setattr(self, '_esc_code_copied', False))
                        except Exception:
                            pass
                    return
            return   # Swallow all other clicks while panel is open

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
        # Skills are dungeon-only — can't fire in town
        if self.dungeon_id == 0:
            return
        p = self.player
        now = time.time()
        _cd_reduction = 0.999 if 'Quick Learner IV' in getattr(p, 'tree_unlocked', set()) else 0.9995

        # Wild Shape active: form skills are keyed 1-5 directly (no page offset)
        if getattr(p, 'wild_shape_form', None):
            for sk in p.unlocked_skills:
                if sk.get('key') == self.active_hotbar_slot:
                    base_cd = sk.get('cooldown', 0)
                    mod = sk.get('cooldown_mod', 1.0)
                    effective_cd = base_cd * mod
                    last_used = sk.get('last_used', 0)
                    if effective_cd <= 0 or now - last_used >= effective_cd:
                        sk['skill'](p, self)
                        sk['last_used'] = now
                        sk['cooldown_mod'] = max(0.2, mod * _cd_reduction)
                    break
            return
        page   = getattr(p, 'skill_page', 1)
        offset = (page - 1) * 5
        for sk in p.unlocked_skills:
            if sk.get('key') == self.active_hotbar_slot + offset:
                base_cd = sk.get('cooldown', 0)
                mod = sk.get('cooldown_mod', 1.0)
                effective_cd = base_cd * mod
                last_used = sk.get('last_used', 0)
                if effective_cd <= 0 or now - last_used >= effective_cd:
                    sk['skill'](p, self)
                    sk['last_used'] = now
                    sk['cooldown_mod'] = max(0.2, mod * _cd_reduction)
                    # Break invisibility when any skill is used (except Teleport/Invisibility)
                    if sk['name'] not in ('Invisibility', 'Teleport'):
                        self._break_invisibility()
                break

    def on_mouse_move(self, event):
        """Track mouse position for hotbar tooltips (non-spammy)."""
        self.mouse_pos = (event.x, event.y)

    def _break_invisibility(self):
        """End invisibility buff and restore enemy normal AI."""
        p = self.player
        if not getattr(p, '_invisible', False):
            return
        p._invisible = False
        p._invisible_end = 0
        p._invisible_from_potion = False
        # Remove the invisibility buff display
        if hasattr(p, 'active_buffs'):
            p.active_buffs = [b for b in p.active_buffs if b.get('name') != 'Invisibility']
        # Release forced wander on all enemies
        for e in self.room.enemies:
            e._forced_wander = False
            e._forced_wander_end = 0

    def on_right_click(self, event):
        """Right-click behaviour depends on active hotbar slot:
        - R (weapon slot) active → fire selected weapon skill
        - T/Y/U (consumable slot) active → use that consumable
        """
        if self.dead:
            return

        wep_active = getattr(self, '_weapon_slot_active', False)

        if wep_active:
            # ── Weapon slot selected: fire weapon skill ──────────────────────
            p  = self.player
            ws = getattr(p, 'weapon_skills', [])
            if not ws:
                return
            slot = getattr(self, 'active_weapon_skill_slot', 0)
            if 0 <= slot < len(ws):
                sk  = ws[slot]
                now = time.time()
                cd  = sk.get('cooldown', 2.0)
                if now - sk.get('last_used', 0) >= cd:
                    try:
                        sk['skill'](p, self)
                    except Exception:
                        pass
                    sk['last_used'] = now
                    if sk['name'] not in ('Invisibility', 'Teleport'):
                        self._break_invisibility()
        else:
            # ── Consumable slot selected: use that item ──────────────────────
            slot = self.active_item_slot
            if slot >= len(self.hotbar_items):
                return
            item = self.hotbar_items[slot]
            if item is None:
                return
            used = item.use(self.player)
            if used:
                item.count -= 1
                if item.count <= 0:
                    self.hotbar_items[slot] = None
                if not (hasattr(item, 'subtype') and item.subtype == 'invisibility_potion'):
                    self._break_invisibility()

    def draw_hotbar(self):
        """Skill hotbar: top-left of game canvas (only when outdoors).
        Consumable hotbar: right panel (map_canvas), always drawn."""
        self._draw_consumable_hotbar()
        if not self.current_interior:
            self._draw_skill_hotbar()

    def _draw_skill_hotbar(self):
        """Draw the 5-slot skill hotbar on the game canvas (top-left).
        When Wild Shape hotbar is active (_ws_hotbar_active) draw the form slots instead.
        When transformed draw the form skill slots."""
        p   = self.player
        now = time.time()

        slot_size = 44
        gap       = 6
        start_x   = 10
        y_skill   = 80   # restored default position

        ws_form      = getattr(p, 'wild_shape_form', None)
        ws_hb_active = getattr(self, '_ws_hotbar_active', False)

        # ── Wild Shape FORM hotbar (press 6 to open, press 1-5 to transform) ──
        if ws_hb_active and not ws_form:
            # Banner
            banner_w = 5*(slot_size+gap) + 80
            self.canvas.create_rectangle(start_x - 2, y_skill - 24,
                                         start_x + banner_w, y_skill - 4,
                                         fill='#0a2a0a', outline='#44cc44', width=1)
            self.canvas.create_text(start_x + banner_w//2, y_skill - 14,
                                    text='🐾  WILD SHAPE  —  press 1-5 to transform, 6 to cancel',
                                    fill='#66ff66', font=('Arial', 8, 'bold'))
            # Draw form slots
            for i in range(1, 6):
                x = start_x + (i-1)*(slot_size+gap)
                form_name = p.wild_shape_form_slots.get(i)
                fd = next((f for f in WILD_SHAPE_FORMS if f['name'] == form_name), None) if form_name else None
                col = fd['color'] if fd else '#336633'
                bg  = '#1a3a1a' if fd else '#0f1f0f'
                self.canvas.create_rectangle(x, y_skill, x+slot_size, y_skill+slot_size,
                                             fill=bg, outline=col, width=2)
                if fd:
                    self.canvas.create_text(x+slot_size//2, y_skill+slot_size//2-8,
                                            text=fd['icon'], font=('Arial', 14))
                    short = fd['name'][:7]+'…' if len(fd['name'])>8 else fd['name']
                    self.canvas.create_text(x+slot_size//2, y_skill+slot_size-8,
                                            text=short, fill=col,
                                            font=('Arial', 6, 'bold'), width=slot_size-2)
                else:
                    self.canvas.create_text(x+slot_size//2, y_skill+slot_size//2,
                                            text='—', fill='#446644', font=('Arial', 12))
                self.canvas.create_text(x+6, y_skill+6, text=str(i),
                                        fill='#aaffaa', font=('Arial', 7, 'bold'))
            return

        # ── Transformed: show form skills hotbar ──────────────────────────────
        if ws_form:
            form_data = next((f for f in WILD_SHAPE_FORMS if f['name'] == ws_form), None)
            icon  = form_data['icon'] if form_data else '🐾'
            color = form_data.get('color', '#33ff66') if form_data else '#33ff66'
            banner_w = 5*(slot_size+gap) + 50
            self.canvas.create_rectangle(start_x - 2, y_skill - 24,
                                         start_x + banner_w, y_skill - 4,
                                         fill='#0a1a0a', outline=color, width=1)
            self.canvas.create_text(start_x + banner_w//2, y_skill - 14,
                                    text=f"{icon}  {ws_form.upper()}  —  press 6 to revert",
                                    fill=color, font=('Arial', 8, 'bold'))
            # Form skill slots
            slot_skill = {}
            for sk in p.unlocked_skills:
                k = sk.get('key', 0)
                if 1 <= k <= 5:
                    slot_skill[k] = sk
            for i in range(1, 6):
                x        = start_x + (i-1)*(slot_size+gap)
                selected = (i == self.active_hotbar_slot)
                bg       = '#1a3a1a' if selected else '#112211'
                outline  = color if selected else '#226622'
                lw       = 3 if selected else 1
                self.canvas.create_rectangle(x, y_skill, x+slot_size, y_skill+slot_size,
                                             fill=bg, outline=outline, width=lw)
                sk = slot_skill.get(i)
                if sk:
                    elapsed   = now - sk.get('last_used', 0)
                    cd        = sk.get('cooldown', 0) * sk.get('cooldown_mod', 1.0)
                    if cd > 0 and elapsed < cd:
                        frac      = 1.0 - elapsed / cd
                        overlay_h = int(slot_size * frac)
                        self.canvas.create_rectangle(x, y_skill, x+slot_size,
                                                     y_skill+overlay_h,
                                                     fill='#000000', stipple='gray50', outline='')
                    short = sk['name'][:8]+'…' if len(sk['name'])>9 else sk['name']
                    self.canvas.create_text(x+slot_size//2, y_skill+slot_size//2,
                                            text=short, fill='#aaffaa',
                                            font=('Arial', 7, 'bold'), width=slot_size-4)
                self.canvas.create_text(x+6, y_skill+6, text=str(i),
                                        fill='#aaffaa', font=('Arial', 7, 'bold'))
            return

        # ── Normal skill hotbar ────────────────────────────────────────────────
        has_keen = ('Keen Mind' in getattr(p, 'tree_unlocked', set())
                    and p.passive_toggles.get('Keen Mind', True))
        if has_keen:
            self.canvas.create_text(start_x + 2, y_skill - 10,
                                    text=f"Page {p.skill_page}  [6]",
                                    fill='#aaaaff', font=('Arial', 7, 'bold'), anchor='w')
        # Show Wild Shape hint if unlocked but hotbar not active
        elif p.class_name == 'Druid' and 'Wild Shape' in getattr(p, 'tree_unlocked', set()):
            self.canvas.create_text(start_x + 2, y_skill - 10,
                                    text='6 = Wild Shape', fill='#44aa44',
                                    font=('Arial', 7, 'bold'), anchor='w')

        page   = getattr(p, 'skill_page', 1)
        offset = (page - 1) * 5
        slot_skill = {}
        for sk in p.unlocked_skills:
            k = sk.get('key', 0)
            if offset + 1 <= k <= offset + 5:
                slot_skill[k - offset] = sk

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
                elapsed   = now - sk.get('last_used', 0)
                cd        = sk.get('cooldown', 0) * sk.get('cooldown_mod', 1.0)
                if cd > 0 and elapsed < cd:
                    frac      = 1.0 - elapsed / cd
                    overlay_h = int(slot_size * frac)
                    self.canvas.create_rectangle(x, y_skill, x+slot_size,
                                                 y_skill+overlay_h,
                                                 fill='#000000', stipple='gray50', outline='')
                short = sk['name'][:8]+'…' if len(sk['name'])>9 else sk['name']
                self.canvas.create_text(x+slot_size//2, y_skill+slot_size//2,
                                        text=short, fill='white',
                                        font=('Arial', 7, 'bold'), width=slot_size-4)
            num_color = '#000000' if selected else '#aaaaaa'
            self.canvas.create_text(x+6, y_skill+6, text=str(i),
                                    fill=num_color, font=('Arial', 7, 'bold'))


    def _draw_consumable_hotbar(self):
        """Draw hotbar on map_canvas:
        Row 1 (top):    [R=weapon | T | Y | U]  — 4 slots, weapon first
        Row 2 (bottom): weapon skill bar — 3 slots (Z/X cycle, RClick to fire)
        """
        mc  = self.map_canvas
        pw  = mc.winfo_width() or 200
        ph  = mc.winfo_height() or 600
        now = time.time()

        ss  = 40   # slot size
        gap = 5
        p   = self.player

        # ── Row 1: main hotbar — starts at ph - ss*2 - gap - 8 (room for skill bar below) ──
        wep_active = getattr(self, '_weapon_slot_active', False)
        iy = ph - ss*2 - gap - 22  # top row: leave space for skill bar + label below

        # ITEMS label above row 1
        mc.create_text(pw//2, iy - 14, text='ITEMS', fill='#888888',
                       font=('Arial', 7, 'bold'))

        total_iw = 4*ss + 3*gap
        ix0      = (pw - total_iw) // 2

        # Slot 0: Weapon (R key)
        wx = ix0
        weap = next((it for it in p.equipped_items if it.item_type == 'weapon'), None)
        w_sel = wep_active
        mc.create_rectangle(wx, iy, wx+ss, iy+ss,
                            fill='#2a1a2e' if w_sel else '#1a0e1e',
                            outline='#ffcc44' if w_sel else '#884488', width=3 if w_sel else 2)
        mc.create_text(wx+6, iy+7, text='R', fill='#ffcc44' if w_sel else '#aa66aa',
                       font=('Arial', 7, 'bold'))
        if weap:
            emoji_w = {'sword':'⚔','dagger':'🗡','bow':'🏹','staff':'🪄',
                        'spear':'🔱','wand':'🪄','hand':'👊','quarterstaff':'🪄'}.get(
                            getattr(weap,'weapon_type','sword'), '⚔')
            mc.create_text(wx+ss//2, iy+ss//2-4, text=emoji_w, font=('Arial', 13))
            short = weap.name[:6]+'…' if len(weap.name)>7 else weap.name
            mc.create_text(wx+ss//2, iy+ss-8, text=short, fill='#ddccff',
                           font=('Arial', 5, 'bold'))
            if getattr(weap, 'soulbound', False):
                mc.create_text(wx+ss-6, iy+6, text='★', fill='#FFD700',
                               font=('Arial', 7, 'bold'))
        else:
            mc.create_text(wx+ss//2, iy+ss//2, text='⚔', font=('Arial', 14),
                           fill='#554466')

        # Slots 1-3: Consumables (T/Y/U)
        labels = ['T', 'Y', 'U']
        for i in range(3):
            x   = ix0 + (i+1)*(ss+gap)
            sel = (not wep_active) and (i == self.active_item_slot)
            ol  = '#aaaaaa' if sel else '#666688'
            lw  = 3 if sel else 1
            mc.create_rectangle(x, iy, x+ss, iy+ss,
                                 fill='#3a3a7c' if sel else '#ffffff',
                                 outline=ol, width=lw)
            item = self.hotbar_items[i] if i < len(self.hotbar_items) else None
            if item:
                emoji = item.get_emoji() if hasattr(item, 'get_emoji') else '?'
                mc.create_oval(x+ss-9, iy+2, x+ss-2, iy+9,
                               fill=item.get_color(), outline='')
                cnt = getattr(item, 'count', 1)
                mc.create_text(x+ss//2, iy+ss//2, text=emoji, font=('Arial', 14))
                if cnt > 1:
                    mc.create_text(x+ss-4, iy+ss-4, text=str(cnt),
                                   fill='#111111', font=('Arial', 7, 'bold'), anchor='se')
            lbl_c = '#ffffff' if sel else '#555577'
            mc.create_text(x+6, iy+7, text=labels[i], fill=lbl_c,
                           font=('Arial', 7, 'bold'))

        # ── Row 2: weapon skill bar ───────────────────────────────────────────
        ws        = getattr(p, 'weapon_skills', [])
        active_ws = getattr(self, 'active_weapon_skill_slot', 0)
        wss       = ss - 2          # slightly smaller
        wg        = 4
        total_ww  = 3*wss + 2*wg
        wx0       = (pw - total_ww) // 2
        wy        = iy + ss + gap   # directly below main hotbar


        for idx in range(3):
            x   = wx0 + idx*(wss+wg)
            sel = (idx == active_ws)
            sk  = ws[idx] if idx < len(ws) else None
            mc.create_rectangle(x, wy, x+wss, wy+wss,
                                fill='#3a2a00' if sel else '#1e1408',
                                outline='#ffcc44' if sel else ('#886633' if sk else '#332211'),
                                width=3 if sel else 1)
            if sk:
                elapsed = now - sk.get('last_used', 0)
                cd      = sk.get('cooldown', 2.0)
                if cd > 0 and elapsed < cd:
                    frac      = 1.0 - elapsed / cd
                    overlay_h = int(wss * frac)
                    mc.create_rectangle(x, wy, x+wss, wy+overlay_h,
                                        fill='#000000', stipple='gray50', outline='')
                short = sk['name'][:7]+'…' if len(sk['name'])>8 else sk['name']
                mc.create_text(x+wss//2, wy+wss//2,
                               text=short, fill='#ffdd88',
                               font=('Arial', 6, 'bold'), width=wss-4)
            else:
                mc.create_text(x+wss//2, wy+wss//2, text='—',
                               fill='#443322', font=('Arial', 9))
            mc.create_text(x+4, wy+wss-6, text=str(idx+1),
                           fill='#aa8844' if sel else '#554422',
                           font=('Arial', 6, 'bold'))



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

        # Virtual Map passive required for dungeon minimap
        _has_virtual_map = ('Virtual Map' in getattr(self.player, 'tree_unlocked', set())
                            and self.player.passive_toggles.get('Virtual Map', True))


        # Reserve bottom area for consumable hotbar + buff list
        ITEM_H   = 110    # main hotbar (40) + weapon skill bar (38) + labels + gaps
        buffs    = getattr(self.player, 'active_buffs', [])
        now      = time.time()
        buffs    = [b for b in buffs if b['end'] > now]

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

        def _remaining(b):
            r = b['end'] - now
            return r if r != float('inf') else None   # None = permanent


        all_display = ([{'emoji': b.get('emoji', '✨'), 'name': b.get('name', ''), 'desc': b.get('desc', ''),
                         'remaining': _remaining(b), 'duration': b.get('duration', 30),
                         'color':     b.get('color',     '#ffd700'),
                         'bar_color': b.get('bar_color', '#44aa44')}
                        for b in buffs] + debuff_rows)

        # Reserve enough vertical space for ALL rows so nothing overlaps the hotbar
        ROW_H    = 50     # matches ROW_H2 in the draw block below
        LABEL_H  = 18 if all_display else 0
        BUFF_H   = len(all_display) * ROW_H + LABEL_H
        bottom_reserved = ITEM_H + BUFF_H + 8

        mc.create_line(0, 0, 0, ph, fill='#333355', width=2)
        mc.create_text(pw//2, 12, text='MAP', fill='#888888', font=('Arial', 10, 'bold'))

        if not self._player_has_map() and not (self.dungeon_id != 0 and _has_virtual_map):
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
            area_bottom = ph - ITEM_H - 34
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
                time_label = 'ACTIVE' if remaining is None else f'{remaining:.1f}s'
                mc.create_text(pw-5, by2 + 8,
                               text=time_label,
                               fill=entry['color'], font=('Arial', 7, 'bold'), anchor='e')
                # ── desc on row 2 ────────────────────────────────────────────
                mc.create_text(28, by2 + 21,
                               text=entry['desc'][:22],
                               fill='#888899', font=('Arial', 6), anchor='w')
                # ── timer bar on row 3 ───────────────────────────────────────
                frac  = 1.0 if remaining is None else min(1.0, remaining / max(1, entry['duration']))
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



    def damage_player(self,amount, attacker=None):
        if self.dead: return
        p = self.player
        # Wet debuff reduces attacker damage
        if attacker is not None:
            amount = amount * getattr(attacker, '_wet_dmg_mult', 1.0)
        amount = max(0, amount - (p.constitution + getattr(p, '_item_con_bonus', 0)))
        # Kinetic Shell / Mage Armour: slowly regenerate shield between hits
        _shield_sources = ('Kinetic Shell', 'Mage Armour', 'Barkskin')
        if any(s in getattr(p, 'tree_unlocked', set()) for s in _shield_sources):
            if getattr(p, 'max_shield', 0) == 0:
                # max_shield wasn't calculated yet — recalc now
                p.update_stats()
            _last_hit = getattr(p, '_shield_hit_time', 0)
            if time.time() - _last_hit > 3.0:   # regen starts 3 s after last hit
                regen_rate = p.max_shield * 0.04  # 4 % per damage_player call ≈ steady regen
                p.shield = min(getattr(p, 'max_shield', 0),
                               getattr(p, 'shield', 0) + regen_rate)
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
            # Stop all active channelled/toggle skills on death
            p._mana_barrier_active = False
            p._mana_shield_active = False
            p._fire_breath_end = 0
            p._ice_breath_end = 0
            if hasattr(p, '_rapid_active'):
                p._rapid_active = False
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
        # Mark bombs as player-killed so they still give rewards on death
        if getattr(e, '_is_bomb', False) and amount > 0:
            e._killed_by_player = True
        # ── Phase-3 immunity: GreatSword boss takes no damage WHILE SPINNING ──
        if isinstance(e, Boss) and getattr(e, 'boss_type', '') == 'GreatSword':
            hp_frac = e.hp / e.max_hp
            if hp_frac <= 0.15:
                # Immune during spin; damageable during the 1.5s pause
                now = time.time()
                if now < getattr(e, 'gs_p3_pause_until', 0):
                    pass   # in pause window → take damage normally
                else:
                    return  # still spinning → fully immune

        e.hp -= amount
        # ── Poison Infusion: apply tiered poison on ANY hit if unlocked ──────
        # Skip if this call comes from the DoT tick itself (avoids infinite poison)
        if (amount > 0
                and not getattr(e, '_poison_dot_tick', False)
                and 'Poison Infusion' in getattr(self.player, 'tree_unlocked', set())):
            _now_pi = time.time()
            if _now_pi - getattr(e, '_pi_last_hit', 0) >= 0.5:
                e._pi_last_hit = _now_pi
                _cur_tier  = getattr(e, '_poison_tier', 0)
                _cur_until = getattr(e, '_poison_until', 0)
                _still_active = _cur_until > _now_pi
                if _still_active and _cur_tier == 1:
                    _new_tier = 2; _pi_dur = 10.0; _pi_dps = 0.03
                elif _still_active and _cur_tier >= 2:
                    _new_tier = 3; _pi_dur = 15.0; _pi_dps = 0.05
                else:
                    _new_tier = 1; _pi_dur = 5.0;  _pi_dps = 0.02
                e._poison_tier  = _new_tier
                e._poison_until = _now_pi + _pi_dur
                e._poison_dps   = e.max_hp * _pi_dps
        if e.hp <= 0 and e in self.room.enemies:
            # ── Ignis the Burning: phase 4 phoenix transition ─────────────────
            if (isinstance(e, Boss) and getattr(e, 'boss_type', '') == 'FireLord'
                    and getattr(e, 'ignis_phase', 4) < 4):
                e.ignis_phase        = 4
                e.ignis_phase4_start = time.time()
                e.hp                 = max(1, int(e._ignis_true_max_hp * 0.05))
                e.size               = 11     # small phoenix bird
                e.color              = '#ffcc00'
                e.spd                = 4.5
                e.ignis_bird_dir       = random.uniform(0, 2*math.pi)
                e.ignis_bird_turn_time = 0.0
                # Burst of fire particles on transformation
                for _ in range(35):
                    _ta = random.uniform(0, 2*math.pi)
                    _tr = random.uniform(5, 40)
                    self.spawn_particle(
                        e.x+math.cos(_ta)*_tr, e.y+math.sin(_ta)*_tr,
                        random.uniform(5,13),
                        random.choice(['#ff2200','#ff6600','#ffcc00','#ffff88']),
                        life=random.uniform(0.4,1.0), rtype='flame', owner='enemy')
                return   # don't remove — phase 4 takes over

            # ── Bomb Creeper: trigger explosion on death ──────────────────────
            if getattr(e, '_is_bomb', False):
                bomb_explode(e, self)
            if not getattr(e, '_no_reward', False):
                coins_total = max(1, int(e.max_hp / 10))
                num_coins = random.randint(1, min(5, coins_total))
                base_val = coins_total // num_coins
                remainder = coins_total - base_val * num_coins
                for i in range(num_coins):
                    val = base_val + (1 if i == 0 and remainder > 0 else 0)
                    self.coin_particles.append(CoinParticle(e.x, e.y, val))
                self.player.gain_xp(e.max_hp*2)
            # ── Flag boss defeated so treasure room unlocks ───────────────────
            if isinstance(e, Boss) and getattr(e, 'boss_type', '') == 'GreatSword':
                self.boss_defeated[self.dungeon_id] = True
            if isinstance(e, Boss) and getattr(e, 'boss_type', '') == 'FireLord':
                self.boss_defeated[self.dungeon_id] = True
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
                if not isinstance(e, Boss):
                    e.spd = 0
            else:
                if not isinstance(e, Boss):
                    e.spd = e.base_spd
            # Wet: -20% speed & damage per tier (applies to all enemy types including Bosses)
            if getattr(e, '_wet_until', 0) > now_freeze:
                _wt = getattr(e, '_wet_tier', 1)
                # Bosses are more resistant — only tier 3+ slows them and effect is halved
                if isinstance(e, Boss):
                    if _wt >= 3:
                        _wet_mult = max(0.6, 1.0 - 0.1 * _wt)
                        e._wet_dmg_mult = _wet_mult
                    else:
                        e._wet_dmg_mult = 1.0
                else:
                    _wet_mult = max(0.2, 1.0 - 0.2 * _wt)
                    e.spd = e.spd * _wet_mult
                    e._wet_dmg_mult = _wet_mult
            else:
                e._wet_dmg_mult = 1.0
            # Gradual drift back from door — move 4% toward target each frame
            if hasattr(e, '_drift_target_x'):
                _dx = e._drift_target_x - e.x
                _dy = e._drift_target_y - e.y
                if abs(_dx) < 1 and abs(_dy) < 1:
                    del e._drift_target_x, e._drift_target_y
                else:
                    e.x += _dx * 0.04
                    e.y += _dy * 0.04

        # ── Indoor NPC wander — runs every frame when player is inside a building ──
        if self.current_interior:
            wall = 24
            indoor_npc_name = self.current_interior.get('indoor_npc_name')
            if indoor_npc_name:
                for npc in self.room.npcs:
                    if npc.name == indoor_npc_name:
                        npc.update_indoor(dt, wall, WINDOW_W, WINDOW_H)
                        break
        
        # Apply frost debuffs — each frost particle freezes each entity AT MOST ONCE.
        # Once applied, _freeze_done is set so the particle is skipped every frame after.
        now_t = time.time()
        for part in self.particles:
            if part.rtype != "frost" or getattr(part, '_freeze_done', False):
                continue
            if not hasattr(part, '_frozen_ids'):
                part._frozen_ids = set()

            if part.owner == "player":
                for e in self.room.enemies:
                    eid = id(e)
                    if eid not in part._frozen_ids:
                        if distance((e.x, e.y), (part.x, part.y)) <= part.size + e.size:
                            e._frozen_until = now_t + 10.0
                            e._freeze_ice_spawned = False
                            part._frozen_ids.add(eid)
                            part._freeze_done = True   # one freeze per particle, then done
                            break  # stop checking more enemies for this particle

            elif part.owner == "enemy":
                p2 = self.player
                pid = id(p2)
                if pid not in part._frozen_ids:
                    if distance((p2.x, p2.y), (part.x, part.y)) <= part.size + p2.size:
                        p2._frozen_until = now_t + 10.0
                        p2._freeze_ice_spawned = False
                        part._frozen_ids.add(pid)
                        part._freeze_done = True

        # Unfreeze entities whose freeze has expired
        for e in self.room.enemies:
            if hasattr(e, '_frozen_until') and now_t >= e._frozen_until:
                e._frozen_until = 0
                e._freeze_ice_spawned = False
        p3 = self.player
        if hasattr(p3, '_frozen_until') and now_t >= p3._frozen_until:
            p3._frozen_until = 0
            p3._freeze_ice_spawned = False

        # ── Poison Infusion: tick poison damage on enemies ───────────────────
        for _pe in list(self.room.enemies):
            _pu = getattr(_pe, '_poison_until', 0)
            if _pu > now_t:
                _dps = getattr(_pe, '_poison_dps', 0)
                if _dps > 0:
                    _pe._poison_dot_tick = True   # exempt: skip infusion re-apply
                    self.damage_enemy(_pe, _dps * dt)
                    _pe._poison_dot_tick = False
                    # Green poison particle occasionally
                    if random.random() < 0.15:
                        self.spawn_particle(_pe.x + random.uniform(-8,8),
                                            _pe.y + random.uniform(-8,8),
                                            random.uniform(3,6), '#44ff44',
                                            life=0.4, rtype='magic_burst')

        # ── Wet drip particles on wet enemies ───────────────────────────────
        for _we in list(self.room.enemies):
            if getattr(_we, '_wet_until', 0) > now_t:
                if random.random() < 0.35:
                    _drip = Particle(
                        _we.x + random.uniform(-_we.size * 0.7, _we.size * 0.7),
                        _we.y + random.uniform(-_we.size * 0.3, _we.size * 0.3),
                        random.uniform(2, 4),
                        random.choice(['#00aaff', '#44ccff', '#0077cc', '#aaddff']),
                        life=random.uniform(0.5, 1.0), rtype='water_drip')
                    _drip._vy = random.uniform(28, 55)   # pixels/sec downward
                    _drip._vx = random.uniform(-4, 4)
                    self.particles.append(_drip)

        # ── Move water drip particles downward ───────────────────────────────
        for _dp in self.particles:
            if _dp.rtype == 'water_drip':
                _dp.y += getattr(_dp, '_vy', 40) * dt
                _dp.x += getattr(_dp, '_vx', 0) * dt

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
                e.update(self)
                # ── Arcane Archer: delayed orange homing arrow ─────────────────
                if getattr(e, '_pending_fire_arrow', 0) and time.time() >= e._pending_fire_arrow:
                    e._pending_fire_arrow = 0
                    _arcane_homing_orange_slow(e, self)
                # ── Stone Guardian: return to home position when player is far ──
                if getattr(e, '_is_guardian', False):
                    hx = getattr(e, '_home_x', e.x)
                    hy = getattr(e, '_home_y', e.y)
                    dist_to_player = distance((e.x, e.y), (self.player.x, self.player.y))
                    dist_to_home   = distance((e.x, e.y), (hx, hy))
                    if dist_to_player > 180 and dist_to_home > 20:
                        # Walk back home
                        _hdx = hx - e.x; _hdy = hy - e.y
                        _hd  = math.hypot(_hdx, _hdy)
                        e.x += (_hdx/_hd) * e.spd * 1.5
                        e.y += (_hdy/_hd) * e.spd * 1.5
                # ── Stone Guardian shield blocks incoming enemy projectiles ─────
                # (checked in projectile collision, shield_angle stored on enemy)
        # ── Post-skill enemy death check ────────────────────────────────────────
        # Skills (fire_slash, rock_throw, etc.) may reduce e.hp directly via
        # damage_enemy() but particles/callbacks run outside the normal hit loop.
        # Sweep here so no enemy stays alive at <=0 hp.
        for _de in list(self.room.enemies):
            if _de.hp <= 0 and _de in self.room.enemies:
                # ── Ignis phase-4 transition (post-skill sweep) ───────────────
                if (isinstance(_de, Boss) and getattr(_de, 'boss_type', '') == 'FireLord'
                        and getattr(_de, 'ignis_phase', 4) < 4):
                    _de.ignis_phase        = 4
                    _de.ignis_phase4_start = time.time()
                    _de.hp                 = max(1, int(_de._ignis_true_max_hp * 0.05))
                    _de.size               = 11
                    _de.color              = '#ffcc00'
                    _de.spd                = 4.5
                    _de.ignis_bird_dir       = random.uniform(0, 2*math.pi)
                    _de.ignis_bird_turn_time = 0.0
                    for _ in range(35):
                        _ta = random.uniform(0, 2*math.pi)
                        _tr = random.uniform(5, 40)
                        self.spawn_particle(
                            _de.x+math.cos(_ta)*_tr, _de.y+math.sin(_ta)*_tr,
                            random.uniform(5,13),
                            random.choice(['#ff2200','#ff6600','#ffcc00','#ffff88']),
                            life=random.uniform(0.4,1.0), rtype='flame', owner='enemy')
                    continue   # don't remove
                if getattr(_de, '_is_bomb', False):
                    bomb_explode(_de, self)
                if not getattr(_de, '_no_reward', False):
                    _ct = max(1, int(_de.max_hp / 10))
                    _nc = random.randint(1, min(5, _ct))
                    _bv = _ct // _nc
                    for _ci in range(_nc):
                        self.coin_particles.append(CoinParticle(_de.x, _de.y, _bv))
                    self.player.gain_xp(_de.max_hp * 2)
                if isinstance(_de, Boss) and getattr(_de, 'boss_type', '') == 'GreatSword':
                    self.boss_defeated[self.dungeon_id] = True
                if isinstance(_de, Boss) and getattr(_de, 'boss_type', '') == 'FireLord':
                    self.boss_defeated[self.dungeon_id] = True
                if _de in self.room.enemies:
                    self.room.enemies.remove(_de)

        for p in list(self.projectiles): p.update(dt,self)
        # ── Flush pending skill callbacks (e.g. triple-shot delays) ────────────
        _now_cb = time.time()
        if hasattr(self, '_pending_callbacks') and self._pending_callbacks:
            _still_pending = []
            for _cb in self._pending_callbacks:
                _fire_t, _fn = _cb[0], _cb[1]
                _args = _cb[2:]
                if _now_cb >= _fire_t:
                    try:
                        _fn(self, *_args)
                    except Exception:
                        pass
                else:
                    _still_pending.append(_cb)
            self._pending_callbacks = _still_pending
        for proj in list(self.projectiles):
            if getattr(proj, 'ptype', '') == 'boss_heal':
                boss_ref = getattr(proj, 'boss_ref', None)
                if boss_ref and boss_ref in self.room.enemies:
                    if distance((proj.x, proj.y), (boss_ref.x, boss_ref.y)) < boss_ref.size + proj.radius:
                        boss_ref.hp = min(boss_ref.max_hp, boss_ref.hp + proj.heal_amt)
                        proj.life = 0   # consume the bolt
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
            elif getattr(_fp, 'ptype', '') == 'holyflame':
                for _ in range(2):
                    _ta = _fp.angle + random.uniform(-0.5, 0.5)
                    _td = random.uniform(0, _fp.radius)
                    _tx = _fp.x + math.cos(_ta)*_td
                    _ty = _fp.y + math.sin(_ta)*_td
                    _tp = Particle(_tx, _ty, random.uniform(3,7),
                                   random.choice(['#ffdd00','#ffffff','#ffee55','#ffffaa']),
                                   life=0.25, rtype='holy_puff', owner=None)
                    self.particles.append(_tp)
            elif getattr(_fp, 'ptype', '') == 'blackflame':
                for _ in range(2):
                    _ta = _fp.angle + random.uniform(-0.5, 0.5)
                    _td = random.uniform(0, _fp.radius)
                    _tx = _fp.x + math.cos(_ta)*_td
                    _ty = _fp.y + math.sin(_ta)*_td
                    _tp = Particle(_tx, _ty, random.uniform(3,7),
                                   random.choice(['#330022','#660033','#990044','#aa0055']),
                                   life=0.25, rtype='black_puff', owner=None)
                    self.particles.append(_tp)
        self.projectiles=[p for p in self.projectiles if p.life>0]
        for part in self.particles: part.update(dt, self)
        self.particles=[p for p in self.particles if p.life>0]
        # Update lava pools
        if not hasattr(self, 'lava_pools'):
            self.lava_pools = []
        for lp in list(self.lava_pools):
            lp.update(dt, self)
        self.lava_pools = [lp for lp in self.lava_pools if lp.alive]
        # Tick coin particles
        _MF_RADII = {
            'Magnetic Field I':   250,
            'Magnetic Field II':  600,
            'Magnetic Field III': 1100,
        }
        _unlocked = getattr(self.player, 'tree_unlocked', set())
        _mag_radius = 0
        for _mf_name, _mf_r in _MF_RADII.items():
            if _mf_name in _unlocked and self.player.passive_toggles.get(_mf_name, True):
                _mag_radius = max(_mag_radius, _mf_r)
        _mag_active = _mag_radius > 0
        _MAGNET_SPEED  = 180   # pixels/sec pull speed

        self.coin_particles = [cp for cp in self.coin_particles if cp.update(dt)]

        # Magnetic Field: pull coins toward player
        if _mag_active:
            for cp in self.coin_particles:
                cdx = self.player.x - cp.x; cdy = self.player.y - cp.y
                cd = math.hypot(cdx, cdy)
                if 0 < cd < _mag_radius:
                    step = min(_MAGNET_SPEED * dt, cd)
                    cp.x += (cdx / cd) * step
                    cp.y += (cdy / cd) * step

        # Tick weapon particles and check for pickup
        for wp in list(self.weapon_particles):
            if not wp.update(dt):
                self.weapon_particles.remove(wp)
                continue
            # Magnetic Field: pull dropped items toward player
            if _mag_active:
                wdx = self.player.x - wp.x; wdy = self.player.y - wp.y
                wd = math.hypot(wdx, wdy)
                if 0 < wd < _mag_radius:
                    step = min(_MAGNET_SPEED * dt, wd)
                    wp.x += (wdx / wd) * step
                    wp.y += (wdy / wd) * step
            if not wp.update(dt):
                self.weapon_particles.remove(wp)
                continue
            if distance((self.player.x, self.player.y), (wp.x, wp.y)) < self.player.size + wp.size + 8:
                self.player.add_item_to_inventory(wp.item)
                self.player.update_equipped_skills()
                self.weapon_particles.remove(wp)
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
                _beam_type = getattr(self.player_beam, '_beam_type', 'mana_beam')
                for e in list(self.room.enemies):
                    beam_end_x = self.player_beam.origin_x + math.cos(self.player_beam.angle) * self.player_beam.current_length
                    beam_end_y = self.player_beam.origin_y + math.sin(self.player_beam.angle) * self.player_beam.current_length
                    
                    dist_to_beam = self.point_to_line_distance(
                        e.x, e.y,
                        self.player_beam.origin_x, self.player_beam.origin_y,
                        beam_end_x, beam_end_y
                    )
                    
                    if dist_to_beam < e.size + self.player_beam.size/2:
                        if _beam_type == 'scorching_ray':
                            self.damage_enemy(e, self.player.mag * dt * 2)   # mag×2/s
                        elif _beam_type == 'ray_of_frost':
                            self.damage_enemy(e, self.player.mag * dt * 1.5)  # mag×1.5/s
                            # Apply chill: slow 30% for 1.5s
                            e._wet_tier  = max(getattr(e, '_wet_tier', 0), 2)
                            e._wet_until = max(getattr(e, '_wet_until', 0), time.time() + 1.5)
                        else:
                            self.damage_enemy(e, self.player.mag * dt * 5)
                # ── Scorching Ray: scatter fire particles along beam ─────────
                if _beam_type == 'scorching_ray' and self.player_beam.current_length > 0:
                    _br  = self.player_beam.current_length
                    _bax = self.player_beam.angle
                    _perp_sr = _bax + math.pi / 2
                    for _ in range(8):
                        _cd  = random.uniform(0, _br)
                        _off = random.uniform(-5, 5)
                        _col = random.choice(['#ff4400','#ff6600','#ffaa00','#ffff44','#ffffff'])
                        self.spawn_particle(
                            self.player_beam.origin_x + math.cos(_bax)*_cd + math.cos(_perp_sr)*_off,
                            self.player_beam.origin_y + math.sin(_bax)*_cd + math.sin(_perp_sr)*_off,
                            random.uniform(3, 8), _col,
                            life=random.uniform(0.08, 0.18), rtype='flame', owner='player')
                # ── Ray of Frost: scatter ice particles along beam ───────────
                elif _beam_type == 'ray_of_frost' and self.player_beam.current_length > 0:
                    _br  = self.player_beam.current_length
                    _bax = self.player_beam.angle
                    _perp_rf = _bax + math.pi / 2
                    for _ in range(8):
                        _cd  = random.uniform(0, _br)
                        _off = random.uniform(-5, 5)
                        _col = random.choice(['#88eeff','#aaffff','cyan','#00ccff','#ffffff'])
                        self.spawn_particle(
                            self.player_beam.origin_x + math.cos(_bax)*_cd + math.cos(_perp_rf)*_off,
                            self.player_beam.origin_y + math.sin(_bax)*_cd + math.sin(_perp_rf)*_off,
                            random.uniform(3, 7), _col,
                            life=random.uniform(0.08, 0.18), rtype='frost', owner='player')
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
                if deco['type'] in ('dungeon_entrance', 'dungeon_clearing'):
                    if distance((self.player.x, self.player.y), (deco['x'], deco['y'])) < 200:
                        self.nearby_dungeon = deco
                        break
    def switch_room(self, new_row, new_col, new_x, new_y):
        _old_room = self.room

        self.room_row = new_row
        self.room_col = new_col
        self.player.x, self.player.y = new_x, new_y
        self.room = self.get_room(self.room_row, self.room_col)
        # Clear return-to-centre on enemies already in this room so they
        # immediately chase the player instead of ignoring them on entry.
        for _ne in self.room.enemies:
            _ne._return_to_centre_until = 0
            _ne._room_entered_at = time.time()   # suppress retreat for 1s on entry
        self.particles.clear()
        self.projectiles.clear()
        self.coin_particles.clear()   # coins belong to the old room
        if hasattr(self, 'lava_pools'):
            self.lava_pools.clear()   # lava pools belong to the old room
        if hasattr(self, '_life_circles'):
            self._life_circles.clear()  # circle of life zones belong to the old room
        # Clear queued skill callbacks (e.g. triple-shot delays) so they don't
        # fire into the new room after the elemental that cast them is gone.
        self._pending_callbacks = []

        # If the player is currently invisible, force enemies in the NEW room
        # into the wander state too — otherwise invisibility breaks on room entry.
        if getattr(self.player, '_invisible', False):
            wander_end = getattr(self.player, '_invisible_end', 0) + 18.0
            for e in self.room.enemies:
                e._forced_wander     = True
                e._forced_wander_end = wander_end

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

        # Recalculate speed every tick so Haste/Rage/Fatigue are always current
        p.update_stats()

        # ── Ice Cavern (dungeon 3) cold debuff — applied after update_stats ──
        # update_stats() rebuilds speed from scratch so we can safely modify it here
        # without any stacking risk.
        if self.dungeon_id == 3:
            _eq_names = {it.name for it in p.equipped_items}
            _has_fleece = 'Thick Fleece' in _eq_names
            _has_shoes  = 'Ice Shoes'    in _eq_names
            if _has_fleece:
                _cavern_debuff = None                      # fully protected
            elif _has_shoes:
                _cavern_debuff = 'chilling'                # partial: −20 flat AGI penalty
                p.speed = max(0.5, p.speed - 20 * 0.05)   # 1 AGI = 0.05 speed
            else:
                _cavern_debuff = 'freezing'                # bare: AGI ×0.3
                p.speed = max(0.5, p.speed * 0.3)
        else:
            _cavern_debuff = None

        # Sync debuff badge into active_buffs so the HUD reflects the current state
        if not hasattr(p, 'active_buffs'):
            p.active_buffs = []
        p.active_buffs = [b for b in p.active_buffs
                          if b.get('source') != 'cavern_cold']
        if _cavern_debuff == 'freezing':
            p.active_buffs.append({'name': '🥶 Freezing', 'end': float('inf'),
                                   'source': 'cavern_cold', 'emoji': '🥶',
                                   'desc': 'AGI ×0.3 — wear Thick Fleece',
                                   'duration': 1, 'color': '#88ddff', 'bar_color': '#0066cc'})
        elif _cavern_debuff == 'chilling':
            p.active_buffs.append({'name': '❄️ Chilling', 'end': float('inf'),
                                   'source': 'cavern_cold', 'emoji': '❄️',
                                   'desc': 'AGI −20 — wear Thick Fleece',
                                   'duration': 1, 'color': '#aaeeff', 'bar_color': '#3399bb'})

        # Shield regen — only after 4 s since last hit, very slow
        if getattr(p,'max_shield',0) > 0:
            last_hit = getattr(p,'_shield_hit_time',0)
            if now - last_hit >= 4.0:
                p.shield = min(p.max_shield, p.shield + p.shield_regen_rate * dt)

        # Stone Shield offhand charge regen — 1 charge per 2 seconds if shield equipped
        _has_offhand = any(it.item_type == 'offhand' for it in p.equipped_items)
        if _has_offhand and getattr(p, 'shield_charges', 30) < 30:
            p._shield_charge_regen = getattr(p, '_shield_charge_regen', 0) + dt
            while p._shield_charge_regen >= 2.0:
                p._shield_charge_regen -= 2.0
                p.shield_charges = min(30, p.shield_charges + 1)

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
        # Expire buff display list (float('inf') end = permanent toggle, never remove)
        if hasattr(p, 'active_buffs'):
            p.active_buffs = [b for b in p.active_buffs if b['end'] > now]

        # ── Invisibility expiry ───────────────────────────────────────────────
        if getattr(p, '_invisible', False) and now >= getattr(p, '_invisible_end', 0):
            self._break_invisibility()

        # ── Invisibility potion: apply forced wander to enemies once ─────────
        if getattr(p, '_invisible', False) and getattr(p, '_invisible_from_potion', False):
            p._invisible_from_potion = False  # apply only once
            invis_end = getattr(p, '_invisible_end', now + 20.0)
            for e in self.room.enemies:
                e._forced_wander = True
                e._forced_wander_end = invis_end

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

        # ── Ice Breath channel: continuous frost particles for 5 seconds ─────
        if getattr(p, '_ice_breath_end', 0) > now:
            p._ice_breath_tick = getattr(p, '_ice_breath_tick', 0) + dt
            mana_cost = 15 * dt
            if p.mana < mana_cost:
                p._ice_breath_end = 0
            else:
                p.mana -= mana_cost
                _mx, _my = self.get_mouse_world_pos()
                ang = math.atan2(_my - p.y, _mx - p.x)
                spread = 0.35
                for _ in range(16):
                    delta = random.uniform(-spread, spread)
                    dist  = random.uniform(18, 140)
                    px2   = p.x + math.cos(ang + delta) * dist
                    py2   = p.y + math.sin(ang + delta) * dist
                    fr = Particle(
                        px2, py2,
                        random.uniform(4, 9),
                        random.choice(['cyan', '#00ccff', '#aaddff', '#66eeff', 'white']),
                        life=random.uniform(0.3, 0.6),
                        rtype='frost',
                        owner='player'
                    )
                    fr.damage = p.mag * 0.10
                    self.particles.append(fr)

        # ── Fire Storm: three rotating flame rings around player ─────────────
        if getattr(p, '_fire_storm_end', 0) > now:
            _fs_t = now - getattr(p, '_fire_storm_start', now)
            for (_sr, _rot, _count, _lmin, _lmax) in [
                (p.size+35,  3.5, 6, 0.28, 0.55),
                (p.size+68, -2.3, 5, 0.26, 0.50),
                (p.size+100, 1.8, 4, 0.22, 0.42),
            ]:
                for _si in range(_count):
                    _sa = (_rot*_fs_t + _si*(2*math.pi/_count)) % (2*math.pi)
                    fl = Particle(
                        p.x + math.cos(_sa)*(_sr+random.uniform(-6,6)),
                        p.y + math.sin(_sa)*(_sr+random.uniform(-6,6)),
                        random.uniform(6,13),
                        random.choice(['#ff2200','#ff6600','#ffaa00','#ffcc00','#ffff44']),
                        life=random.uniform(_lmin,_lmax), rtype='flame', owner='player')
                    fl.damage = p.mag * 0.20
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

        # ── Orbiting Blade: spin blades then launch at nearest enemy ─────────
        if hasattr(p, '_orbit_blades') and p._orbit_blades:
            spin_speed = 3.5
            now_o = time.time()
            for blade in list(p._orbit_blades):
                blade['angle'] += spin_speed * dt
                elapsed = now_o - blade['spawn_t']
                if elapsed >= blade['dur'] and not blade['launched']:
                    blade['launched'] = True
                    ox = p.x + math.cos(blade['angle']) * 90
                    oy = p.y + math.sin(blade['angle']) * 90
                    # Launch at nearest enemy if any, otherwise toward mouse
                    if self.room.enemies:
                        target = min(self.room.enemies,
                                     key=lambda e: distance((p.x, p.y), (e.x, e.y)))
                        ang = math.atan2(target.y - oy, target.x - ox)
                    else:
                        _mx, _my = self.get_mouse_world_pos()
                        ang = math.atan2(_my - oy, _mx - ox)
                    self.spawn_projectile(ox, oy, ang, 14, 4, 22,
                                          '#aaaaff', p.atk * 3.0, 'player',
                                          stype='greatsword_proj')
                    p._orbit_blades.remove(blade)

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
                if hasattr(self, 'lava_pools'):
                    self.lava_pools.clear()   # lava pools gone on respawn
                p.die()
                p.hp = p.max_hp; p.mana = p.max_mana
                # Restore energy shield to full on respawn
                if getattr(p, 'max_shield', 0) > 0:
                    p.shield = p.max_shield
                # Clear ALL buffs, debuffs and skill effects on respawn
                p.active_buffs = []
                p.active_skill_effects = {}
                p._frozen_until = 0
                p._freeze_ice_spawned = False
                p.speed = getattr(p, 'base_speed', p.speed)
                # Clear haste / rage stat boosts so effects don't persist
                p._haste_agi_bonus = 0
                p._haste_end       = 0
                p._rage_end        = 0
                p._rage_agi_bonus  = 0
                p._rage_str_bonus  = 0
                for _attr in ('_slow_end_time', '_bleed_end', '_poison_end',
                              '_burn_end', '_stun_end', '_silence_end',
                              '_invincible_until', '_invisible_until',
                              '_invisible_end'):
                    if hasattr(p, _attr):
                        setattr(p, _attr, 0)
                p._invisible = False
                p._invisible_from_potion = False
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

            # WASD — frozen players cannot move
            if getattr(p, '_frozen_until', 0) > time.time():
                p.speed = 0
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
        # Outdoor movement — frozen players cannot move
        if getattr(p, '_frozen_until', 0) > time.time():
            p.speed = 0
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
            
            # Check decoration collisions (fountain, lamps, trees — NOT forest_wall)
            if check_collision(p.x, p.y, p.size, self.room.decorations):
                p.x = old_x
                p.y = old_y

            # Oval forest boundary — stop at wall unless inside a corridor segment
            _dx = p.x - TOWN_CX
            _dy = p.y - TOWN_CY
            _od = math.hypot(_dx / OVAL_A, _dy / OVAL_B)
            if _od > 0.97:
                _GW_HALF = 55   # half corridor width + margin
                _in_corridor = False
                _world_segs = [
                    (math.atan2(0,    -1),   -80,  300,  950),
                    (math.atan2(-350, 1150),  60,  280, 1000),
                    (math.atan2( 350, 1150), -60,  280, 2700),  # Ice Cavern — extended to reach clearing at +3200
                    (math.atan2( 950,  0),    80,  300,  800),
                ]
                # Also define clearing positions (player near clearing = always allowed)
                _clearings = [
                    (TOWN_CX - 1450, TOWN_CY,        140,  40),
                    (TOWN_CX + 1450, TOWN_CY - 380,  140,  40),
                    (TOWN_CX + 3200, TOWN_CY + 420,  280, 200),  # Ice Cavern — generous margin to bridge diagonal path end
                    (TOWN_CX + 2650, TOWN_CY + 180,  220,  40),  # Left scenic clearing
                    (TOWN_CX,        TOWN_CY + 1200, 140,  40),
                ]
                for _cx2, _cy2, _cr2, _cm in _clearings:
                    if math.hypot(p.x - _cx2, p.y - _cy2) < _cr2 + _cm:
                        _in_corridor = True
                        break
                if not _in_corridor:
                    for _wga, _wgbend, _wgbend_at, _wglen in _world_segs:
                        _wperp = _wga + math.pi / 2
                        _ws1x = TOWN_CX + math.cos(_wga) * OVAL_A * 0.87
                        _ws1y = TOWN_CY + OVAL_B / OVAL_A * math.sin(_wga) * OVAL_A * 0.87
                        _wm1x = _ws1x + math.cos(_wga) * _wgbend_at
                        _wm1y = _ws1y + math.sin(_wga) * _wgbend_at
                        _wm2x = _wm1x + math.cos(_wperp) * _wgbend
                        _wm2y = _wm1y + math.sin(_wperp) * _wgbend
                        _we2x = _wm2x + math.cos(_wga) * (_wglen - _wgbend_at)
                        _we2y = _wm2y + math.sin(_wga) * (_wglen - _wgbend_at)
                        for _wx0, _wy0, _wx1, _wy1 in [(_ws1x,_ws1y,_wm1x,_wm1y),
                                                         (_wm1x,_wm1y,_wm2x,_wm2y),
                                                         (_wm2x,_wm2y,_we2x,_we2y)]:
                            _segdx = _wx1-_wx0; _segdy = _wy1-_wy0
                            _seglen2 = math.hypot(_segdx, _segdy)
                            if _seglen2 < 1: continue
                            _ux2 = _segdx/_seglen2; _uy2 = _segdy/_seglen2
                            _proj2 = (_dx+TOWN_CX-_wx0)*_ux2 + (_dy+TOWN_CY-_wy0)*_uy2
                            _perp2 = abs((-(_dy+TOWN_CY-_wy0)*_ux2 + (_dx+TOWN_CX-_wx0)*_uy2))
                            if -_GW_HALF < _proj2 < _seglen2+_GW_HALF and _perp2 < _GW_HALF:
                                _in_corridor = True
                                break
                        if _in_corridor:
                            break
                # Ice Cavern connector road — vertical strip bridging path end to clearing bottom only
                if not _in_corridor:
                    if abs(p.x - (TOWN_CX + 3200)) < 90 and (TOWN_CY + 700) < p.y < (TOWN_CY + 920):
                        _in_corridor = True
                if not _in_corridor:
                    p.x = old_x
                    p.y = old_y
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
                            if (deco.get('type') in ('dungeon_entrance', 'dungeon_clearing')
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
                    # Boss room (0,4): bottom only opens after boss defeated
                    if self.room_row == 0 and self.room_col == 4:
                        if not self.boss_defeated.get(self.dungeon_id, False):
                            p.y = WINDOW_H - wall_thickness - player_size
                            return
                    opening_x_start = WINDOW_W // 2 - opening_size // 2
                    opening_x_end = opening_x_start + opening_size
                    if p.x < opening_x_start or p.x > opening_x_end:
                        p.y = WINDOW_H - wall_thickness - player_size

            # Left wall collision
            if p.x - player_size < wall_thickness:
                if self.room_col == 0:  # Solid wall
                    p.x = wall_thickness + player_size
                elif self.room_col == 4 and self.room_row == 1:
                    # Treasure room — left wall always solid (closed off)
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
                elif self.room_row == 1 and self.room_col == 3:
                    # Solid wall — treasure room is not accessible from row 1 col 3
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
                    # Block entry to treasure room (row 1, col 4) from row 1 col 3
                    if self.room_row == 1 and self.room_col == 3:
                        p.x = WINDOW_W - wall_thickness - player_size
                    else:
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
        self._drawn_puddles = set()   # reset per-frame puddle dedup
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
                        if self.keys.get('c') and not getattr(self, '_npc_shop_open', False):
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
            # === NORMAL TOWN VIEW ===
            # Dark forest fills entire canvas first
            self.canvas.create_rectangle(0, 0, WINDOW_W + 400, WINDOW_H + 400,
                                         fill='#2a5810', outline='')



            # Oval town clearing — lighter grass inside
            _tcx = TOWN_CX - cam_x
            _tcy = TOWN_CY - cam_y
            self.canvas.create_oval(_tcx - OVAL_A, _tcy - OVAL_B,
                                    _tcx + OVAL_A, _tcy + OVAL_B,
                                    fill='#4a8030', outline='')
            # Draw forest corridor gaps — rounded lines = smooth corners, no jagged joints
            _GCOL = '#4a8030'
            _GW = 90
            _gap_segs = [
                (math.atan2(0,    -1),   -80,  300, 950),
                (math.atan2(-350, 1150),  60,  280, 1000),
                (math.atan2( 350, 1150), -60,  280, 2700),   # dungeon 3 — matches collision length
                (math.atan2( 950,  0),    80,  300, 800),
            ]
            for _gi, (_ga, _gbend, _gbend_at, _glen) in enumerate(_gap_segs):
                _perp_a = _ga + math.pi / 2
                _s1x = _tcx + math.cos(_ga) * OVAL_A * 0.87
                _s1y = _tcy + OVAL_B / OVAL_A * math.sin(_ga) * OVAL_A * 0.87
                _m1x = _s1x + math.cos(_ga) * _gbend_at
                _m1y = _s1y + math.sin(_ga) * _gbend_at
                _m2x = _m1x + math.cos(_perp_a) * _gbend
                _m2y = _m1y + math.sin(_perp_a) * _gbend
                _e2x = _m2x + math.cos(_ga) * (_glen - _gbend_at)
                _e2y = _m2y + math.sin(_ga) * (_glen - _gbend_at)
                self.canvas.create_line(
                    _s1x, _s1y, _m1x, _m1y, _m2x, _m2y, _e2x, _e2y,
                    fill=_GCOL, width=_GW,
                    joinstyle='round', capstyle='round', smooth=False
                )
                # ── Ice corridor gradient overlay (dungeon 3 only) ──────────
                if _gi == 2:
                    _STEPS = 18
                    for _si in range(_STEPS):
                        _t0 = _si       / _STEPS
                        _t1 = (_si + 1) / _STEPS
                        # Interpolate along the 3-segment polyline
                        def _lerp_path(t, s1x=_s1x, s1y=_s1y, m1x=_m1x, m1y=_m1y,
                                       m2x=_m2x, m2y=_m2y, e2x=_e2x, e2y=_e2y):
                            segs = [(s1x,s1y,m1x,m1y),(m1x,m1y,m2x,m2y),(m2x,m2y,e2x,e2y)]
                            total = sum(math.hypot(b-a,d-c) for a,c,b,d in segs)
                            want  = t * total
                            for ax,ay,bx,by in segs:
                                seg_len = math.hypot(bx-ax, by-ay)
                                if want <= seg_len or seg_len == 0:
                                    u = want / seg_len if seg_len else 0
                                    return ax + (bx-ax)*u, ay + (by-ay)*u
                                want -= seg_len
                            return e2x, e2y
                        px0, py0 = _lerp_path(_t0)
                        px1, py1 = _lerp_path(_t1)
                        # Ease-in: gradient starts gently, accelerates to white
                        _blend = _t0 ** 1.6
                        _gr = int(0x4a + (0xff - 0x4a) * _blend)
                        _gg = int(0x80 + (0xff - 0x80) * _blend)
                        _gb = int(0x30 + (0xff - 0x30) * _blend)
                        _grad_col = f'#{_gr:02x}{_gg:02x}{_gb:02x}'
                        self.canvas.create_line(px0, py0, px1, py1,
                                                fill=_grad_col, width=_GW - 4,
                                                capstyle='round')
                    # ── Connector road: from actual path end straight up to ice clearing ──
                    _ice_clear_sx = (TOWN_CX + 3200) - cam_x
                    _ice_clear_sy = (TOWN_CY + 420)  - cam_y
                    # Draw connector from path end to clearing centre
                    self.canvas.create_line(
                        _e2x, _e2y,
                        _ice_clear_sx, _ice_clear_sy,
                        fill='#c8e8ff', width=_GW, capstyle='round', joinstyle='round')
                    self.canvas.create_line(
                        _e2x, _e2y,
                        _ice_clear_sx, _ice_clear_sy,
                        fill='#e4f4ff', width=_GW - 18, capstyle='round', joinstyle='round')



            # ── PRE-PASS: draw dungeon clearings BELOW everything else ──────
            for deco in self.room.decorations:
                if deco['type'] == 'plain_clearing':
                    _pc_cx  = deco['x'] - cam_x
                    _pc_cy  = deco['y'] - cam_y
                    _pc_rad = deco.get('radius', 160)
                    _pc_col = deco.get('color', '#c8e8f8')
                    self.canvas.create_oval(_pc_cx-_pc_rad-8, _pc_cy-_pc_rad-8,
                                            _pc_cx+_pc_rad+8, _pc_cy+_pc_rad+8,
                                            fill=_pc_col, outline='#a0c8e0', width=2)
                    self.canvas.create_oval(_pc_cx-_pc_rad+18, _pc_cy-_pc_rad+18,
                                            _pc_cx+_pc_rad-18, _pc_cy+_pc_rad-18,
                                            fill='#e4f4ff', outline='#b8d8f0', width=1)
                    for _eb in self.room.decorations:
                        if _eb.get('type') != 'clearing_edge':
                            continue
                        if math.hypot(_eb['x'] - deco['x'], _eb['y'] - deco['y']) > _pc_rad + 70:
                            continue
                        _ex = _eb['x'] - cam_x
                        _ey = _eb['y'] - cam_y
                        _es = _eb['size']
                        self.canvas.create_oval(_ex-_es, _ey-_es, _ex+_es, _ey+_es,
                                                fill='#c0dff0', outline='')
                    continue
                if deco['type'] != 'dungeon_clearing':
                    continue
                cx   = deco['x'] - cam_x
                cy   = deco['y'] - cam_y
                rad  = deco.get('radius', 140)
                col  = deco['color']
                now_t = time.time()
                _is_ice = deco.get('dungeon_id') == 3
                # Path = gap in the forest blob ring (no drawn path here)
                # Outer clearing — wide grass circle (snow for ice cavern)
                _outer_fill   = '#e8f4fc' if _is_ice else '#4a8030'
                _outer_out    = '#c8e4f4' if _is_ice else '#3a6820'
                _inner_fill   = '#f4faff' if _is_ice else '#8a7040'
                _inner_out    = '#d8eef8' if _is_ice else '#6a5030'
                _cobble_fill  = '#c8dce8' if _is_ice else '#7a7060'
                _cobble_out   = '#a0b8c8' if _is_ice else '#4a4840'
                _cobble_stone = '#b0c8d8' if _is_ice else '#6a6050'
                _tree_trunk   = '#4a3010'
                _tree_canopy  = '#b8e0f4' if _is_ice else '#4a8030'
                _tree_hilite  = '#d8f0ff' if _is_ice else '#5a9838'
                self.canvas.create_oval(cx-rad-8, cy-rad-8, cx+rad+8, cy+rad+8,
                                        fill=_outer_fill, outline=_outer_out, width=2)
                # Inner worn dirt area
                self.canvas.create_oval(cx-rad+18, cy-rad+18, cx+rad-18, cy+rad-18,
                                        fill=_inner_fill, outline=_inner_out, width=2)
                # Central cobblestone circle (like map ref)
                self.canvas.create_oval(cx-28, cy-28, cx+28, cy+28,
                                        fill=_cobble_fill, outline=_cobble_out, width=3)
                for _ci in range(8):
                    _ca = _ci * math.pi / 4
                    _cr = 18
                    self.canvas.create_oval(
                        cx+math.cos(_ca)*_cr-5, cy+math.sin(_ca)*_cr-5,
                        cx+math.cos(_ca)*_cr+5, cy+math.sin(_ca)*_cr+5,
                        fill=_cobble_stone, outline='#444', width=1)
                # Portal arch
                _pulse = abs(math.sin(now_t * 2)) * 6
                self.canvas.create_rectangle(cx-20, cy-44, cx-10, cy+8,
                                             fill='#686060', outline='#333', width=2)
                self.canvas.create_rectangle(cx+10, cy-44, cx+20, cy+8,
                                             fill='#686060', outline='#333', width=2)
                self.canvas.create_polygon(cx-22, cy-42, cx+22, cy-42,
                                           cx+14, cy-62, cx, cy-72, cx-14, cy-62,
                                           fill='#787070', outline='#333', width=2)
                self.canvas.create_oval(cx-12, cy-56-int(_pulse/2),
                                        cx+12, cy+2,
                                        fill=col, outline='', stipple='gray50')
                self.canvas.create_oval(cx-7, cy-48, cx+7, cy, fill=col, outline='')
                # Trees + framing blobs around clearing edge
                for _ti in range(8):
                    _ta = _ti * math.pi / 4 + 0.2
                    _tr = rad - 4 + random.randint(-6, 6)
                    _tx = cx + math.cos(_ta) * _tr
                    _ty = cy + math.sin(_ta) * _tr
                    self.canvas.create_rectangle(_tx-3, _ty-4, _tx+3, _ty+6,
                                                 fill=_tree_trunk, outline='')
                    self.canvas.create_oval(_tx-10, _ty-18, _tx+10, _ty-2,
                                            fill=_tree_canopy, outline=_outer_out, width=1)
                    self.canvas.create_oval(_tx-7, _ty-14, _tx+7, _ty-6,
                                            fill=_tree_hilite, outline='')
                # Clearing_edge blobs (framing forest ring around this clearing)
                for _eb in self.room.decorations:
                    if _eb.get('type') != 'clearing_edge':
                        continue
                    _edist = math.hypot(_eb['x'] - deco['x'], _eb['y'] - deco['y'])
                    if _edist > rad + 70:
                        continue
                    _ex = _eb['x'] - cam_x
                    _ey = _eb['y'] - cam_y
                    _es = _eb['size']
                    _eb_col = '#c0dff0' if _is_ice else _eb['color']
                    self.canvas.create_oval(_ex-_es, _ey-_es, _ex+_es, _ey+_es,
                                            fill=_eb_col, outline='')
                # Dungeon info panel when nearby
                if self.nearby_dungeon and self.nearby_dungeon == deco:
                    _did  = deco.get('dungeon_id', 1)
                    _dnames = {1: 'Forest Dungeon', 2: 'Volcano Dungeon',
                               3: 'Ice Cavern',     4: 'Shadow Realm'}
                    _dcolors = {1: '#88cc66', 2: '#ff6633', 3: '#88ddff', 4: '#bb66ff'}
                    _dstars  = {1: 1, 2: 2, 3: 2, 4: 3}
                    _dname   = _dnames.get(_did, f'Dungeon {_did}')
                    _dcolor  = _dcolors.get(_did, '#ffffff')
                    _stars   = _dstars.get(_did, 1)
                    _star_str = '★' * _stars + '☆' * (5 - _stars)
                    _pw, _ph = 220, 80
                    _px = cx - _pw // 2
                    _py = cy - 180
                    self.canvas.create_rectangle(_px-2, _py-2, _px+_pw+2, _py+_ph+2,
                                                 fill='#0a0a1a', outline=_dcolor, width=2)
                    self.canvas.create_rectangle(_px, _py, _px+_pw, _py+26,
                                                 fill='#1a1a3a', outline='')
                    self.canvas.create_text(_px+_pw//2, _py+13,
                                            text=_dname, fill=_dcolor,
                                            font=('Arial', 13, 'bold'))
                    self.canvas.create_text(_px+_pw//2, _py+44,
                                            text=f'{_star_str}  Difficulty',
                                            fill='#ffcc44', font=('Arial', 10))
                    self.canvas.create_text(_px+_pw//2, _py+65,
                                            text='Press  C  to Enter',
                                            fill='#ffffff', font=('Arial', 10, 'italic'))

            # === MEDIEVAL COBBLESTONE ROADS ===
            sc = self.canvas
            _road_y  = 550 - cam_y
            _road_x0 = 220 - cam_x
            _road_x1 = 1040 - cam_x
            _vroad_x = WINDOW_W // 2 - cam_x
            _vroad_y0 = 280 - cam_y
            _vroad_y1 = 820 - cam_y
            # Horizontal road — fill + kerbs + joints PERPENDICULAR to travel (vertical lines)
            sc.create_rectangle(_road_x0, _road_y-36, _road_x1, _road_y+40, fill='#7a6e56', outline='')
            sc.create_rectangle(_road_x0, _road_y-33, _road_x1, _road_y+37, fill='#8a7e64', outline='')
            sc.create_line(_road_x0, _road_y-36, _road_x1, _road_y-36, fill='#5a5040', width=2)
            sc.create_line(_road_x0, _road_y+40, _road_x1, _road_y+40, fill='#5a5040', width=2)
            for _rj in range(int((_road_x1 - _road_x0) // 24)):
                _jx = int(_road_x0 + _rj * 24 + (12 if _rj % 2 else 0))
                sc.create_line(_jx, _road_y-36, _jx, _road_y+40, fill='#5a5040', width=1)
            # Vertical road — fill + kerbs + joints PERPENDICULAR to travel (horizontal lines)
            sc.create_rectangle(_vroad_x-36, _vroad_y0, _vroad_x+40, _vroad_y1, fill='#7a6e56', outline='')
            sc.create_rectangle(_vroad_x-33, _vroad_y0, _vroad_x+37, _vroad_y1, fill='#8a7e64', outline='')
            sc.create_line(_vroad_x-36, _vroad_y0, _vroad_x-36, _vroad_y1, fill='#5a5040', width=2)
            sc.create_line(_vroad_x+40, _vroad_y0, _vroad_x+40, _vroad_y1, fill='#5a5040', width=2)
            for _vj in range(int((_vroad_y1 - _vroad_y0) // 24)):
                _jy = int(_vroad_y0 + _vj * 24 + (12 if _vj % 2 else 0))
                sc.create_line(_vroad_x-36, _jy, _vroad_x+40, _jy, fill='#5a5040', width=1)
            # Building connector paths — narrow, joints horizontal only
            for b in self.room.buildings:
                _bcx  = b['x'] + b['width'] // 2 - cam_x
                _bct  = (b['y'] + b['height']) - cam_y
                _bcb  = 550 - cam_y
                sc.create_line(_bcx, _bct, _bcx, _bcb, fill='#7a6e56', width=26)
                sc.create_line(_bcx, _bct, _bcx, _bcb, fill='#9a8e72', width=18)
                sc.create_line(_bcx-13, _bct, _bcx-13, _bcb, fill='#5a5040', width=1)
                sc.create_line(_bcx+13, _bct, _bcx+13, _bcb, fill='#5a5040', width=1)
                for _cs2 in range(int(abs(_bcb - _bct) // 20)):
                    _csy2 = min(_bct, _bcb) + _cs2 * 20 + (10 if _cs2 % 2 else 0)
                    sc.create_line(_bcx-13, _csy2, _bcx+13, _csy2, fill='#5a5040', width=1)
                        # Draw buildings first (background layer)
                        # Draw buildings first (background layer)
            cv = self.canvas
            for building in self.room.buildings:
                bx = building['x'] - cam_x
                by = building['y'] - cam_y
                bw = building['width']
                bh = building['height']
                btype   = building['type']
                pattern = building.get('pattern', 'brick')
                _now_b  = time.time()

                # ── helpers ──────────────────────────────────────────────────
                def _gothic_window(wx, wy, ww=14, wh=22, glow=False):
                    """Pointed gothic arch window."""
                    # Frame
                    cv.create_rectangle(wx, wy+wh//3, wx+ww, wy+wh,
                                        fill='#3a2a12', outline='#1a1008', width=1)
                    # Pointed arch top
                    cv.create_polygon(wx, wy+wh//3, wx+ww, wy+wh//3,
                                      wx+ww//2, wy,
                                      fill='#3a2a12', outline='#1a1008')
                    # Glass pane
                    gc = '#ffe8a0' if glow else '#b0c8e0'
                    cv.create_rectangle(wx+2, wy+wh//3+2, wx+ww-2, wy+wh-2, fill=gc, outline='')
                    cv.create_polygon(wx+2, wy+wh//3+2, wx+ww-2, wy+wh//3+2,
                                      wx+ww//2, wy+3, fill=gc, outline='')
                    # Mullion cross
                    cv.create_line(wx+ww//2, wy, wx+ww//2, wy+wh, fill='#1a1008', width=1)
                    cv.create_line(wx, wy+wh//2, wx+ww, wy+wh//2, fill='#1a1008', width=1)

                def _arched_door(dx, dy, dw, dh):
                    """Rounded arched door."""
                    cv.create_rectangle(dx, dy+dh//4, dx+dw, dy+dh,
                                        fill='#3a1e08', outline='#1a0e04', width=2)
                    cv.create_arc(dx, dy, dx+dw, dy+dh//2,
                                  start=0, extent=180, fill='#3a1e08', outline='#1a0e04', width=2)
                    # Iron studs
                    for _si in range(2):
                        for _sj in range(3):
                            cv.create_oval(dx+4+_si*(dw-10), dy+dh//4+6+_sj*(dh//4),
                                           dx+8+_si*(dw-10), dy+dh//4+10+_sj*(dh//4),
                                           fill='#888', outline='')
                    # Door ring handle
                    cv.create_arc(dx+dw//2-5, dy+dh//2,
                                  dx+dw//2+5, dy+dh//2+12,
                                  start=0, extent=180, outline='#aaa', width=2, style='arc')

                def _half_timber(bx, by, bw, bh, wall_col):
                    """Half-timber facade: plaster fill + dark wood beams."""
                    cv.create_rectangle(bx, by, bx+bw, by+bh,
                                        fill='#c8b89a', outline='#2a1a08', width=2)
                    # Horizontal beams every ~quarter height
                    for _i in range(1, 4):
                        _ty = by + (_i * bh) // 4
                        cv.create_line(bx, _ty, bx+bw, _ty, fill='#2a1a08', width=3)
                    # Diagonal braces
                    cv.create_line(bx, by+bh//2, bx+bw//2, by, fill='#2a1a08', width=3)
                    cv.create_line(bx+bw, by+bh//2, bx+bw//2, by, fill='#2a1a08', width=3)
                    cv.create_line(bx, by+bh, bx+bw//2, by+bh//2, fill='#2a1a08', width=3)
                    cv.create_line(bx+bw, by+bh, bx+bw//2, by+bh//2, fill='#2a1a08', width=3)
                    # Vertical corner posts
                    cv.create_line(bx, by, bx, by+bh, fill='#2a1a08', width=4)
                    cv.create_line(bx+bw, by, bx+bw, by+bh, fill='#2a1a08', width=4)

                def _stone_wall(bx, by, bw, bh):
                    """Stone block wall."""
                    cv.create_rectangle(bx, by, bx+bw, by+bh,
                                        fill='#888070', outline='#333', width=2)
                    row_h = max(12, bh // 5)
                    for _ri in range(bh // row_h + 1):
                        _ry = by + _ri * row_h
                        off = ((_ri % 2) * bw) // 4
                        block_w = bw // 3
                        for _ci in range(-1, 5):
                            _rx = bx + _ci * block_w + off
                            if _rx < bx+bw and _rx+block_w > bx:
                                cv.create_rectangle(max(bx,_rx), _ry,
                                                    min(bx+bw,_rx+block_w), min(by+bh,_ry+row_h),
                                                    outline='#555550', width=1)

                def _steep_roof(bx, by, bw, rcol, steep=1.0):
                    """Regular buildings: plaster gable with thick tile-slope edges."""
                    peak_y = by - int(bw * 0.65 * steep)
                    overhang = 8
                    # Gable wall fill (same plaster as facade)
                    cv.create_polygon(bx - overhang, by,
                                      bx + bw + overhang, by,
                                      bx + bw//2, peak_y,
                                      fill='#c8b89a', outline='')
                    # Half-timber braces in gable
                    cv.create_line(bx, by, bx + bw//2, peak_y + 10, fill='#2a1a08', width=3)
                    cv.create_line(bx + bw, by, bx + bw//2, peak_y + 10, fill='#2a1a08', width=3)
                    # Left slope edge — THICK
                    cv.create_polygon(
                        bx - overhang, by,
                        bx + bw//2, peak_y,
                        bx + bw//2, peak_y + 20,
                        bx - overhang, by + 22,
                        fill=rcol, outline='#1a1008', width=2)
                    # Right slope edge — THICK
                    cv.create_polygon(
                        bx + bw + overhang, by,
                        bx + bw//2, peak_y,
                        bx + bw//2, peak_y + 20,
                        bx + bw + overhang, by + 22,
                        fill=rcol, outline='#1a1008', width=2)
                    # Eave board
                    cv.create_rectangle(bx - overhang, by, bx + bw + overhang, by + 10,
                                        fill='#2a1808', outline='#1a1008', width=2)
                    # Ridge cap
                    cv.create_rectangle(bx + bw//2 - 7, peak_y - 2,
                                        bx + bw//2 + 7, peak_y + 22,
                                        fill='#2a1808', outline='#1a1008', width=2)

                def _filled_roof(bx, by, bw, rcol, steep=1.0):
                    """Tower/Forge: fully filled tile roof with support beams and window."""
                    peak_y = by - int(bw * 0.65 * steep)
                    cv.create_polygon(bx - 6, by + 2, bx + bw + 6, by + 2,
                                      bx + bw//2, peak_y,
                                      fill=rcol, outline='#1a1008', width=2)
                    # Horizontal tile rows
                    tile_rows = max(4, int(abs(by - peak_y) // 10))
                    for _ti in range(1, tile_rows):
                        frac = _ti / tile_rows
                        _ty  = int(peak_y + (by + 2 - peak_y) * frac)
                        _tx0 = int(bx + (bw//2) * (1 - frac)) - 6
                        _tx1 = int(bx + bw - (bw//2) * (1 - frac)) + 6
                        cv.create_line(_tx0, _ty, _tx1, _ty, fill='#1a1008', width=1)
                    # Diagonal support beams (rafters)
                    cv.create_line(bx + bw//4, by + 2, bx + bw//2, peak_y,
                                   fill='#1a1008', width=2)
                    cv.create_line(bx + bw*3//4, by + 2, bx + bw//2, peak_y,
                                   fill='#1a1008', width=2)
                    # Small gable window
                    _gw_y = peak_y + int(abs(by - peak_y) * 0.35)
                    _gw_x0 = int(bx + (bw//2) * (1 - 0.35)) - 6
                    _gw_x1 = int(bx + bw - (bw//2) * (1 - 0.35)) + 6
                    _gw_cx = (_gw_x0 + _gw_x1) // 2
                    cv.create_oval(_gw_cx - 8, _gw_y - 8, _gw_cx + 8, _gw_y + 8,
                                   fill='#ffe8a0', outline='#1a1008', width=2)
                    cv.create_line(_gw_cx, _gw_y - 8, _gw_cx, _gw_y + 8, fill='#1a1008', width=1)
                    cv.create_line(_gw_cx - 8, _gw_y, _gw_cx + 8, _gw_y, fill='#1a1008', width=1)
                    # Ridge cap
                    cv.create_rectangle(bx + bw//2 - 5, peak_y - 1,
                                        bx + bw//2 + 5, peak_y + 7,
                                        fill='#2a1808', outline='#1a1008', width=1)

                # ── TOWER (Enchanter) ─────────────────────────────────────────
                if btype == 'tower':
                    _stone_wall(bx, by, bw, bh)
                    # Crenellations (battlements) at top
                    merlons = 4
                    mw = bw // (merlons * 2)
                    for _m in range(merlons):
                        _mx = bx + _m * (bw // merlons)
                        cv.create_rectangle(_mx, by-18, _mx+mw, by,
                                            fill='#7a7060', outline='#333', width=1)
                    # Conical filled roof (pointed spire)
                    _filled_roof(bx, by-18, bw, building['roof_color'], steep=1.5)
                    # Flag
                    cv.create_line(bx+bw//2, by-18-int(bw*0.8), bx+bw//2, by-18-int(bw*0.8)-30,
                                   fill='#888', width=2)
                    cv.create_polygon(bx+bw//2, by-18-int(bw*0.8)-30,
                                      bx+bw//2+20, by-18-int(bw*0.8)-22,
                                      bx+bw//2, by-18-int(bw*0.8)-14,
                                      fill='#8B008B', outline='')
                    # Gothic slit windows stacked
                    for _wi in range(3):
                        _wy = by + 15 + _wi * (bh // 3)
                        _gothic_window(bx+bw//2-7, _wy, 14, 20,
                                       glow=(_wi == 1))
                    # Arched door
                    _dw, _dh = bw//3, bh//3
                    _arched_door(bx+bw//2-_dw//2, by+bh-_dh, _dw, _dh)

                # ── BLACKSMITH (Forge) ────────────────────────────────────────
                elif btype == 'blacksmith':
                    # Main half-timber hall
                    _half_timber(bx, by, bw, bh, '#c8b89a')
                    _filled_roof(bx, by, bw, building['roof_color'])
                    # Large stone chimney — left side, tall
                    _cx0 = bx + bw - 28
                    cv.create_rectangle(_cx0, by - 60, _cx0 + 22, by + bh,
                                        fill='#6a6258', outline='#3a3230', width=2)
                    # Stone texture on chimney
                    for _cr in range(5):
                        cv.create_line(_cx0, by-60+_cr*16, _cx0+22, by-60+_cr*16,
                                       fill='#4a4240', width=1)
                    # Chimney cap
                    cv.create_rectangle(_cx0-4, by-64, _cx0+26, by-58,
                                        fill='#3a3230', outline='#222', width=1)
                    # Animated smoke
                    for _si in range(5):
                        _off = (_now_b * 50 + _si * 18) % 80
                        _sx  = _cx0 + 11 + int(math.sin(_now_b + _si) * 3)
                        _sy  = by - 64 - _off
                        _ss  = 4 + int(_off // 16)
                        cv.create_oval(_sx-_ss, _sy-_ss, _sx+_ss, _sy+_ss,
                                       fill='#888', outline='', stipple='gray50')
                    # Forge opening — arched mouth with glow
                    _fw, _fh = 38, 44
                    _fx = bx + 12
                    _fy = by + bh - _fh
                    # Stone surround
                    cv.create_rectangle(_fx-4, _fy-4, _fx+_fw+4, by+bh+2,
                                        fill='#6a6258', outline='#3a3230', width=2)
                    # Arch opening
                    cv.create_rectangle(_fx, _fy+_fh//3, _fx+_fw, by+bh,
                                        fill='#1a1008', outline='')
                    cv.create_arc(_fx, _fy, _fx+_fw, _fy+_fh//1.5,
                                  start=0, extent=180, fill='#1a1008', outline='')
                    # Fire glow — animated flicker
                    _fl = 0.6 + abs(math.sin(_now_b * 5)) * 0.4
                    _fc = f'#{int(255*_fl):02x}{int(100*_fl):02x}00'
                    cv.create_oval(_fx+4, _fy+_fh//3+4, _fx+_fw-4, by+bh-2,
                                   fill='#ff6600', outline='', stipple='gray50')
                    cv.create_oval(_fx+8, _fy+_fh//3+8, _fx+_fw-8, by+bh-6,
                                   fill='#ffaa00', outline='')
                    # Anvil in front
                    _ax = bx + bw//2 + 10
                    _ay = by + bh
                    cv.create_polygon(_ax-12, _ay, _ax+12, _ay,
                                      _ax+16, _ay-12, _ax+6, _ay-16,
                                      _ax-6,  _ay-16, _ax-16, _ay-12,
                                      fill='#3a3a3a', outline='#222', width=1)
                    # Hammer on anvil
                    cv.create_line(_ax+2, _ay-18, _ax+10, _ay-28,
                                   fill='#7a6a50', width=4)
                    cv.create_rectangle(_ax+6, _ay-32, _ax+16, _ay-25,
                                        fill='#5a5a5a', outline='#333', width=1)
                    # Windows
                    for _wi in range(2):
                        _wx = bx + 16 + _wi * (bw - 50)
                        _gothic_window(_wx, by+14, 13, 20, glow=True)

                # ── HOUSE (Player's house) ────────────────────────────────────
                elif btype == 'house':
                    # Small lean-to extension on the right side
                    _ext_w, _ext_h = 30, int(bh * 0.6)
                    _ext_x = bx + bw
                    _ext_y = by + bh - _ext_h
                    _half_timber(_ext_x, _ext_y, _ext_w, _ext_h, '#c0a880')
                    # Extension roof (lower slope)
                    cv.create_polygon(_ext_x - 4, _ext_y + 2,
                                      _ext_x + _ext_w + 4, _ext_y + 2,
                                      _ext_x + _ext_w + 4, _ext_y - 10,
                                      _ext_x - 4, _ext_y - 24,
                                      fill=building['roof_color'], outline='#1a1008', width=1)
                    cv.create_rectangle(_ext_x-4, _ext_y, _ext_x+_ext_w+4, _ext_y+6,
                                        fill='#2a1808', outline='#1a1008', width=1)
                    # Main body
                    _half_timber(bx, by, bw, bh, building['color'])
                    _steep_roof(bx, by, bw, building['roof_color'])
                    # Windows
                    for _wi in range(2):
                        _wx = bx + 14 + _wi * (bw - 36)
                        _gothic_window(_wx, by+22, 14, 22)
                    # Arched door
                    _dw, _dh = bw//4, bh//3
                    _arched_door(bx+bw//2-_dw//2, by+bh-_dh, _dw, _dh)
                    # Flower boxes
                    for _wi in range(2):
                        _fbx = bx + 12 + _wi * (bw - 32)
                        cv.create_rectangle(_fbx, by+bh//2, _fbx+16, by+bh//2+6,
                                            fill='#5a3010', outline='#2a1008', width=1)
                        for _fi in range(3):
                            cv.create_oval(_fbx+2+_fi*5, by+bh//2-4,
                                           _fbx+7+_fi*5, by+bh//2+1,
                                           fill='#cc3366', outline='')

                # ── LIBRARY — stone hall with two side wings ──────────────────
                elif btype == 'library':
                    # Left wing
                    _ww, _wh = 32, int(bh * 0.75)
                    _wx0 = bx - _ww
                    _wy0 = by + bh - _wh
                    _half_timber(_wx0, _wy0, _ww, _wh, '#4a3020')
                    cv.create_polygon(_wx0-3, _wy0, _wx0+_ww+3, _wy0,
                                      _wx0+_ww//2, _wy0-20,
                                      fill='#3a2818', outline='#1a1008', width=1)
                    # Right wing
                    _half_timber(bx+bw, _wy0, _ww, _wh, '#4a3020')
                    cv.create_polygon(bx+bw-3, _wy0, bx+bw+_ww+3, _wy0,
                                      bx+bw+_ww//2, _wy0-20,
                                      fill='#3a2818', outline='#1a1008', width=1)
                    # Main body
                    _half_timber(bx, by, bw, bh, building['color'])
                    _steep_roof(bx, by, bw, building['roof_color'])
                    # Rose window (circular) in gable
                    _gp = by - int(bw * 0.65) + int(bw * 0.25)
                    cv.create_oval(bx+bw//2-12, _gp-12, bx+bw//2+12, _gp+12,
                                   fill='#ffeec0', outline='#2a1a08', width=2)
                    for _ri in range(6):
                        _ra = _ri * math.pi / 3
                        cv.create_line(bx+bw//2, _gp,
                                       bx+bw//2+int(math.cos(_ra)*11),
                                       _gp+int(math.sin(_ra)*11),
                                       fill='#2a1a08', width=1)
                    # Large central gothic window
                    _gothic_window(bx+bw//2-10, by+18, 20, 30, glow=True)
                    # Wing doors
                    _gothic_window(_wx0+5, _wy0+_wh//3, 12, 18)
                    _gothic_window(bx+bw+5, _wy0+_wh//3, 12, 18)
                    # Main arched door
                    _dw, _dh = bw//4, bh//3
                    _arched_door(bx+bw//2-_dw//2, by+bh-_dh, _dw, _dh)
                    cv.create_text(bx+bw//2, by-int(bw*0.65)-10,
                                   text=building['name'], fill='#ffd080', font=('Arial', 9, 'bold'))

                # ── BAKERY — M-shaped double gable + bread-sign extension ──────
                elif btype == 'inn':
                    # Small bread-extension on left
                    _ew, _eh = 28, 45
                    _half_timber(bx - _ew, by+bh-_eh, _ew, _eh, '#c8a060')
                    # Extension shed roof
                    cv.create_polygon(bx-_ew-4, by+bh-_eh+2, bx+4, by+bh-_eh+2,
                                      bx+4, by+bh-_eh-12, fill='#8a5c2a', outline='#1a1008', width=1)
                    # Bread symbol on extension
                    cv.create_oval(bx-_ew+5, by+bh-_eh+8, bx-5, by+bh-20,
                                   fill='#d4901a', outline='#8a5010', width=2)
                    cv.create_arc(bx-_ew+8, by+bh-_eh+10, bx-8, by+bh-22,
                                  start=20, extent=140, fill='#e8a830', outline='')
                    # Main body
                    _half_timber(bx, by, bw, bh, building['color'])
                    # M-shaped double-gable roof: two peaks
                    _peak1_x = bx + bw // 3
                    _peak2_x = bx + bw * 2 // 3
                    _peak_y  = by - int(bw * 0.38)
                    _valley_y = _peak_y + 20
                    _valley_x = bx + bw // 2
                    # Fill the whole gable area first (solid wall colour) so valley isn't hollow
                    cv.create_polygon(
                        bx-6, by+2,
                        bx+bw+6, by+2,
                        _peak2_x, _peak_y,
                        _valley_x, _valley_y,
                        _peak1_x, _peak_y,
                        fill='#c8b89a', outline='')
                    # Left outer slope (left edge → peak1) — THICK
                    cv.create_polygon(bx-6, by, _peak1_x, _peak_y,
                                      _peak1_x, _peak_y+16, bx-6, by+16,
                                      fill=building['roof_color'], outline='#1a1008', width=2)
                    # Valley inner-left slope (peak1 → valley)
                    cv.create_polygon(_peak1_x, _peak_y, _valley_x, _valley_y,
                                      _valley_x, _valley_y+16, _peak1_x, _peak_y+16,
                                      fill=building['roof_color'], outline='#1a1008', width=2)
                    # Valley inner-right slope (valley → peak2)
                    cv.create_polygon(_valley_x, _valley_y, _peak2_x, _peak_y,
                                      _peak2_x, _peak_y+16, _valley_x, _valley_y+16,
                                      fill=building['roof_color'], outline='#1a1008', width=2)
                    # Right outer slope (peak2 → right edge) — THICK
                    cv.create_polygon(_peak2_x, _peak_y, bx+bw+6, by,
                                      bx+bw+6, by+16, _peak2_x, _peak_y+16,
                                      fill=building['roof_color'], outline='#1a1008', width=2)
                    # Eave board
                    cv.create_rectangle(bx-6, by, bx+bw+6, by+10,
                                        fill='#2a1808', outline='#1a1008', width=2)
                    # Ridge caps on both peaks
                    for _rpx in [_peak1_x, _peak2_x]:
                        cv.create_rectangle(_rpx-6, _peak_y-2, _rpx+6, _peak_y+18,
                                            fill='#2a1808', outline='#1a1008', width=1)
                    for _wi in range(2):
                        _wx = bx + 14 + _wi * (bw - 40)
                        _gothic_window(_wx, by+22, 14, 22)
                    _dw, _dh = bw//4, bh//3
                    _arched_door(bx+bw//2-_dw//2, by+bh-_dh, _dw, _dh)
                    cv.create_text(bx+bw//2, _peak_y - 10,
                                   text=building['name'], fill='#ffd080', font=('Arial', 9, 'bold'))

                # ── SHOPS / ALCHEMIST / JEWELER / TRADER ─────────────────────
                elif btype == 'shop':
                    _half_timber(bx, by, bw, bh, building['color'])
                    _steep_roof(bx, by, bw, building['roof_color'])
                    _npc = building.get('indoor_npc_name', '')
                    # Alchemist: bubble cauldron symbol on wall
                    if _npc == 'Zephyr':
                        cv.create_oval(bx+bw-22, by+bh-28, bx+bw-6, by+bh-12,
                                       fill='#44cc44', outline='#228822', width=2)
                        cv.create_oval(bx+bw-19, by+bh-40, bx+bw-13, by+bh-34,
                                       fill='#88ee88', outline='')
                        _gothic_window(bx+14, by+22, 13, 20)
                        _gothic_window(bx+bw-28, by+22, 13, 20, glow=True)
                    # Jeweler: gem shape on wall
                    elif _npc == 'Gemma':
                        cv.create_polygon(bx+bw//2, by+18, bx+bw//2+10, by+28,
                                          bx+bw//2, by+42, bx+bw//2-10, by+28,
                                          fill='#ff88bb', outline='#cc4488', width=2)
                        cv.create_line(bx+bw//2-10, by+28, bx+bw//2+10, by+28,
                                       fill='#cc4488', width=1)
                        _gothic_window(bx+10, by+50, 12, 18)
                    # Trader: crossed swords on wall
                    elif _npc == 'Marcus':
                        cv.create_line(bx+bw//2-10, by+16, bx+bw//2+10, by+42,
                                       fill='#aaaaaa', width=3)
                        cv.create_line(bx+bw//2+10, by+16, bx+bw//2-10, by+42,
                                       fill='#aaaaaa', width=3)
                        _gothic_window(bx+10, by+50, 13, 20)
                        _gothic_window(bx+bw-24, by+50, 13, 20)
                    else:
                        _gothic_window(bx+12, by+22, 13, 20)
                        _gothic_window(bx+bw-26, by+22, 13, 20)
                    _dw, _dh = bw//4+2, bh//3
                    _arched_door(bx+bw//2-_dw//2, by+bh-_dh, _dw, _dh)
                    cv.create_text(bx+bw//2, by-int(bw*0.65)-10,
                                   text=building['name'], fill='#ffd080', font=('Arial', 9, 'bold'))

                # ── FALLBACK ─────────────────────────────────────────────────
                else:
                    _half_timber(bx, by, bw, bh, building['color'])
                    _steep_roof(bx, by, bw, building['roof_color'])
                    _dw, _dh = bw//4, bh//3
                    _arched_door(bx+bw//2-_dw//2, by+bh-_dh, _dw, _dh)
                    cv.create_text(bx+bw//2, by-int(bw*0.65)-10,
                                   text=building['name'], fill='#ffd080', font=('Arial', 9, 'bold'))

                # ── NO SHOP SIGNS — names shown as text labels above roof ────
            
            # ── Halo of Radiance: sun + rotating beams behind player ──────────
            if getattr(self.player, '_halo_active', False):
                _ha = getattr(self.player, '_halo_angle', 0.0)
                for _ri in range(8):
                    _ra = _ha + _ri * (math.pi / 4)
                    _bex = px + math.cos(_ra) * 90
                    _bey = py + math.sin(_ra) * 90
                    self.canvas.create_line(px, py, _bex, _bey, fill='#ffcc00', width=8, stipple='gray25')
                    self.canvas.create_line(px, py, _bex, _bey, fill='#ffee00', width=4, stipple='gray50')
                    self.canvas.create_line(px, py, _bex, _bey, fill='#ffffff', width=1, stipple='gray50')
                self.canvas.create_oval(px-22, py-22, px+22, py+22,
                                        fill='#ffee00', outline='#ffaa00', width=2)
                self.canvas.create_oval(px-13, py-13, px+13, py+13,
                                        fill='#ffffaa', outline='')
            # ── Lingering Aura circles (drawn here so they're behind player/weapon) ──
            for _ap in self.particles:
                if _ap.rtype == 'aura_behind':
                    _ar = _ap.size * max(0.1, _ap.life / 0.5)
                    self.canvas.create_oval(_ap.x-_ar, _ap.y-_ar, _ap.x+_ar, _ap.y+_ar,
                                            fill='yellow', outline='')
            # ── Lingering Aura beam (aura circle drawn via rtype='aura' particles) ──
            if getattr(self.player, '_rapid_active', False):
                _eq = next((it for it in self.player.equipped_items if it.item_type == 'weapon'), None)
                _wangle = getattr(self.player, 'angle', 0)
                if _eq and getattr(_eq, 'weapon_type', '') == 'spear':
                    _stx = getattr(self.player, '_spear_tip_x', self.player.x) - cam_x
                    _sty = getattr(self.player, '_spear_tip_y', self.player.y) - cam_y
                    _sbx = getattr(self.player, '_spear_base_x', self.player.x) - cam_x
                    _sby = getattr(self.player, '_spear_base_y', self.player.y) - cam_y
                    _sdx = _stx - _sbx;  _sdy = _sty - _sby
                    _slen = math.hypot(_sdx, _sdy) or 1
                    _snx = _sdx / _slen;  _sny = _sdy / _slen
                    _ex = _stx + _snx * 60;  _ey = _sty + _sny * 60
                    _perp = math.atan2(_sdy, _sdx) + math.pi / 2
                    _pcx = math.cos(_perp);  _pcy = math.sin(_perp)
                    self.canvas.create_line(_sbx, _sby, _ex, _ey, fill='yellow', width=6, capstyle='butt')
                    for _ in range(10):
                        _a = math.atan2(_sdy, _sdx) + random.uniform(-0.4, 0.4)
                        _d = random.uniform(2, 10)
                        self.canvas.create_oval(_ex+math.cos(_a)*_d-2, _ey+math.sin(_a)*_d-2,
                                                _ex+math.cos(_a)*_d+2, _ey+math.sin(_a)*_d+2,
                                                fill='#ffff88', outline='')
                    # Damage enemies in beam path (world coords)
                    _str_dmg = max(1, getattr(self.player, 'strength', 5))
                    _w_sbx = getattr(self.player, '_spear_base_x', self.player.x)
                    _w_sby = getattr(self.player, '_spear_base_y', self.player.y)
                    _w_ex  = _w_sbx + _snx * 60;  _w_ey = _w_sby + _sny * 60
                    _blen  = math.hypot(_w_ex-_w_sbx, _w_ey-_w_sby) or 1
                    for _be in list(self.room.enemies):
                        _bdx = _be.x - _w_sbx;  _bdy = _be.y - _w_sby
                        _bt  = max(0, _bdx*(_w_ex-_w_sbx)/_blen + _bdy*(_w_ey-_w_sby)/_blen)
                        _bpx = _w_sbx + (_w_ex-_w_sbx)/_blen*_bt
                        _bpy = _w_sby + (_w_ey-_w_sby)/_blen*_bt
                        if 0 <= _bt <= _blen and math.hypot(_be.x-_bpx, _be.y-_bpy) < _be.size + 4:
                            self.damage_enemy(_be, _str_dmg * 0.016)
                elif _eq:
                    _wbx = px + math.cos(_wangle) * 36
                    _wby = py + math.sin(_wangle) * 36
                    _wex = px + math.cos(_wangle) * 106
                    _wey = py + math.sin(_wangle) * 106
                    self.canvas.create_line(_wbx, _wby, _wex, _wey, fill='yellow', width=6, capstyle='butt')
                    for _ in range(10):
                        _a = _wangle + random.uniform(-0.4, 0.4)
                        _d = random.uniform(2, 10)
                        self.canvas.create_oval(_wex+math.cos(_a)*_d-2, _wey+math.sin(_a)*_d-2,
                                                _wex+math.cos(_a)*_d+2, _wey+math.sin(_a)*_d+2,
                                                fill='#ffff88', outline='')
                    _str_dmg2 = max(1, getattr(self.player, 'strength', 5))
                    _pw_bx = self.player.x + math.cos(_wangle) * 36
                    _pw_by = self.player.y + math.sin(_wangle) * 36
                    _pw_ex = self.player.x + math.cos(_wangle) * 106
                    _pw_ey = self.player.y + math.sin(_wangle) * 106
                    _wblen = math.hypot(_pw_ex-_pw_bx, _pw_ey-_pw_by) or 1
                    for _be2 in list(self.room.enemies):
                        _bdx2 = _be2.x - _pw_bx;  _bdy2 = _be2.y - _pw_by
                        _bt2  = max(0, _bdx2*(_pw_ex-_pw_bx)/_wblen + _bdy2*(_pw_ey-_pw_by)/_wblen)
                        _bpx2 = _pw_bx + (_pw_ex-_pw_bx)/_wblen*_bt2
                        _bpy2 = _pw_by + (_pw_ey-_pw_by)/_wblen*_bt2
                        if 0 <= _bt2 <= _wblen and math.hypot(_be2.x-_bpx2, _be2.y-_bpy2) < _be2.size + 4:
                            self.damage_enemy(_be2, _str_dmg2 * 0.016)
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

                # Arcane Longbow gets its own visual type in town too
                if equipped_weapon.name == 'Arcane Longbow':
                    weapon_visual = 'arcane_bow'
                
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
                elif weapon_visual == 'ignis_staff':
                    weapon_item.color = '#DAA520'
                    weapon_item.gem_color = '#FFD700'
                elif weapon_visual == 'wand':
                    weapon_item.color = 'purple'
                    weapon_item.gem_color = 'yellow'
                elif weapon_visual == 'dagger':
                    weapon_item.color = 'purple'
                elif equipped_weapon and equipped_weapon.name == 'Arcane Longbow':
                    weapon_item.color = '#8844cc'
                    weapon_item.gem_color = '#cc88ff'
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
                if weapon_visual in ("spear", "staff", "ignis_staff", "sword", "dagger", "quarterstaff", "katana", "axe", "scythe"):
                    weapon_item.draw(self.canvas)

            # ── Stone Shield offhand draw ─────────────────────────────────────
            _shield_item = next((it for it in self.player.equipped_items
                                 if it.item_type == 'offhand'), None)
            if _shield_item:
                _mx, _my = self.get_mouse_world_pos()
                _face_ang  = math.atan2(_my - self.player.y, _mx - self.player.x)
                _sh_ang    = _face_ang - math.pi * 0.55   # left of weapon
                _sh_dist   = 20
                _shx = px + math.cos(_sh_ang) * _sh_dist
                _shy = py + math.sin(_sh_ang) * _sh_dist
                _perp_s = _sh_ang + math.pi / 2
                _sw_s = 26; _sd_s = 7   # half-width, depth — wide but thin
                # Shield face points (trapezoid top-view)
                _sh_pts = [
                    _shx + math.cos(_perp_s)*_sw_s,       _shy + math.sin(_perp_s)*_sw_s,
                    _shx + math.cos(_perp_s)*_sw_s*0.6 + math.cos(_sh_ang)*_sd_s,
                    _shy + math.sin(_perp_s)*_sw_s*0.6 + math.sin(_sh_ang)*_sd_s,
                    _shx - math.cos(_perp_s)*_sw_s*0.6 + math.cos(_sh_ang)*_sd_s,
                    _shy - math.sin(_perp_s)*_sw_s*0.6 + math.sin(_sh_ang)*_sd_s,
                    _shx - math.cos(_perp_s)*_sw_s,       _shy - math.sin(_perp_s)*_sw_s,
                ]
                _charges = getattr(self.player, 'shield_charges', 30)
                _sh_col  = '#8888bb' if _charges > 0 else '#445566'
                self.canvas.create_polygon(_sh_pts, fill=_sh_col, outline='#ccddff', width=2)
                # Highlight stripe
                self.canvas.create_line(
                    _shx - math.cos(_perp_s)*_sw_s*0.4, _shy - math.sin(_perp_s)*_sw_s*0.4,
                    _shx + math.cos(_perp_s)*_sw_s*0.4, _shy + math.sin(_perp_s)*_sw_s*0.4,
                    fill='#ddeeff', width=2)
                # Charge bar — drawn in front of shield face (in the _sh_ang direction)
                _bar_cx = _shx + math.cos(_sh_ang) * (_sd_s + 5)
                _bar_cy = _shy + math.sin(_sh_ang) * (_sd_s + 5)
                _blen   = 22   # bar half-length along perp
                _bar_x0 = _bar_cx - math.cos(_perp_s) * _blen
                _bar_y0 = _bar_cy - math.sin(_perp_s) * _blen
                _bar_x1 = _bar_cx + math.cos(_perp_s) * _blen
                _bar_y1 = _bar_cy + math.sin(_perp_s) * _blen
                self.canvas.create_line(_bar_x0, _bar_y0, _bar_x1, _bar_y1,
                                        fill='#333355', width=4, capstyle='round')
                _fill_f = max(0, min(1, _charges / 30))
                if _fill_f > 0:
                    _fx1 = _bar_x0 + (_bar_x1-_bar_x0)*_fill_f
                    _fy1 = _bar_y0 + (_bar_y1-_bar_y0)*_fill_f
                    _col_bar = '#6688ff' if _fill_f > 0.3 else '#ff4444'
                    self.canvas.create_line(_bar_x0, _bar_y0, _fx1, _fy1,
                                            fill=_col_bar, width=4, capstyle='round')
                # Charge count text
                self.canvas.create_text(_bar_cx + math.cos(_sh_ang)*8,
                                        _bar_cy + math.sin(_sh_ang)*8,
                                        text=str(_charges), fill='white',
                                        font=('Arial', 7, 'bold'))
                # Store shield face world position for projectile collision
                self.player._shield_face_x = _shx + self.camera_x
                self.player._shield_face_y = _shy + self.camera_y
                self.player._shield_face_ang = _sh_ang
                self.player._shield_face_sw  = _sw_s + 4

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
            ws_form_name = getattr(self.player, 'wild_shape_form', None)
            ws_fd        = next((f for f in WILD_SHAPE_FORMS if f['name'] == ws_form_name), None) if ws_form_name else None
            if getattr(self.player, '_iron_guard_active', False):
                player_color = '#888888'
            elif ws_fd:
                player_color = ws_fd['color']
            else:
                player_color = CLASS_COLORS.get(self.player.class_name, "cyan")

            # ── Shocked: yellow glow BEHIND player (drawn before body) ────────
            if getattr(self.player, '_shocked_until', 0) > time.time():
                _ss = size + 12
                # Outer soft glow — two expanding rings
                for _ring in range(3):
                    _ro = _ring * 6
                    self.canvas.create_oval(
                        px - _ss - _ro, py - _ss - _ro,
                        px + _ss + _ro, py + _ss + _ro,
                        fill='', outline='#ffff00', width=2, stipple='gray50'
                    )
                # Filled yellow halo (behind everything else)
                self.canvas.create_oval(
                    px - _ss, py - _ss, px + _ss, py + _ss,
                    fill='#ffff44', outline='', stipple='gray25'
                )
                self.canvas.create_text(px, py - _ss - 8,
                                        text='⚡ SHOCKED',
                                        fill='#ffff00', font=('Arial', 8, 'bold'))

            # White outline
            self.canvas.create_oval(px-size-2, py-size-2, px+size+2, py+size+2, fill='white')
            # Colored body
            self.canvas.create_oval(px-size, py-size, px+size, py+size, fill=player_color)

            # Iron Guard: metallic ring highlights over the body
            if getattr(self.player, '_iron_guard_active', False):
                # Outer steel ring
                self.canvas.create_oval(px-size-1, py-size-1, px+size+1, py+size+1,
                                        fill='', outline='#cccccc', width=2)
                # Inner bright highlight arc (simulate light reflection)
                self.canvas.create_arc(px-size+2, py-size+2, px+size-2, py+size-2,
                                       start=40, extent=110,
                                       style='arc', outline='white', width=3)

            # Wild shape: draw form icon; normal: draw name initial
            if ws_fd:
                # Glowing ring in form colour
                self.canvas.create_oval(px-size-5, py-size-5, px+size+5, py+size+5,
                                        fill='', outline=ws_fd['color'], width=3)
                self.canvas.create_text(px, py, text=ws_fd['icon'],
                                        font=('Arial', 14), fill='white')
            else:
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

            # ── Frost particles — orbit player when Chilling or Freezing ──────
            _now_frost = time.time()
            _cavern_buffs = {b.get('name','') for b in getattr(self.player,'active_buffs',[])}
            _is_freezing = any('Freezing' in n for n in _cavern_buffs)
            _is_chilling = any('Chilling' in n for n in _cavern_buffs)
            if _is_freezing or _is_chilling:
                _frost_count = 8 if _is_freezing else 3
                _frost_r     = size + 14
                if not hasattr(self, '_frost_angle'):
                    self._frost_angle = 0.0
                self._frost_angle += 0.04
                for _fi in range(_frost_count):
                    _fa = self._frost_angle + (_fi * 2 * math.pi / _frost_count)
                    _fx2 = px + math.cos(_fa) * _frost_r
                    _fy2 = py + math.sin(_fa) * _frost_r
                    _fs2 = 4.0 if _is_freezing else 3.0
                    # 6-pointed crystal
                    for _arm_a in (_fa, _fa + math.pi/3, _fa + 2*math.pi/3):
                        _ax2 = math.cos(_arm_a) * _fs2
                        _ay2 = math.sin(_arm_a) * _fs2
                        self.canvas.create_line(
                            _fx2-_ax2, _fy2-_ay2, _fx2+_ax2, _fy2+_ay2,
                            fill='#aaeeff' if _is_chilling else '#ddf4ff', width=2)


            if getattr(self.player, '_invisible', False):
                _rinv = size + 8
                self.canvas.create_oval(px-_rinv, py-_rinv, px+_rinv, py+_rinv,
                                        fill='#8844ff', outline='#cc88ff',
                                        width=2, stipple='gray25')
                _rem_inv = max(0, getattr(self.player, '_invisible_end', 0) - time.time())
                self.canvas.create_text(px, py - _rinv - 8,
                                        text=f"👁 {_rem_inv:.1f}s",
                                        fill='#cc88ff', font=('Arial', 8, 'bold'))

            # Draw weapons that go ON TOP of player body (like bow)
            if weapon_item and equipped_weapon and hasattr(equipped_weapon, 'weapon_type'):
                if weapon_item.item_type == 'arcane_bow':
                    weapon_item.draw(self.canvas)
                elif equipped_weapon.weapon_type not in ("spear", "staff", "ignis_staff", "sword", "dagger", "quarterstaff", "katana", "axe", "scythe"):
                    weapon_item.draw(self.canvas)

            # ── Orbiting Blade: draw spinning swords around the player ─────────
            if hasattr(self.player, '_orbit_blades') and self.player._orbit_blades:
                for blade in self.player._orbit_blades:
                    if not blade.get('launched', False):
                        orb_x = px + math.cos(blade['angle']) * 90
                        orb_y = py + math.sin(blade['angle']) * 90
                        orb = Item(orb_x, orb_y, 'greatsword', '#aaaaff', 22)
                        orb.angle = blade['angle'] + math.pi / 2
                        orb.draw(self.canvas)
                        # Soft glow ring
                        self.canvas.create_oval(
                            orb_x - 14, orb_y - 14, orb_x + 14, orb_y + 14,
                            fill='', outline='#6688ff', width=1
                        )

    # Continue with summons drawing...
            for s in self.summons:
                s.draw(self.canvas)
                # Numerical HP — only visible with Identify passive
                if ('Identify' in getattr(self.player, 'tree_unlocked', set())
                        and self.player.passive_toggles.get('Identify', True)
                        and s.max_hp > 0):
                    _sb_w = max(s.size * 2, 36)
                    _sb_x = s.x - _sb_w // 2
                    _sb_y = s.y - s.size - 8
                    # Green HP bar
                    self.canvas.create_rectangle(_sb_x, _sb_y, _sb_x + _sb_w, _sb_y + 4,
                                                 fill='#1a3300', outline='')
                    _frac = max(0.0, s.hp / s.max_hp)
                    self.canvas.create_rectangle(_sb_x, _sb_y, _sb_x + int(_sb_w * _frac), _sb_y + 4,
                                                 fill='#44ff44', outline='')
                    # Numeric text above bar
                    self.canvas.create_text(
                        s.x, s.y - s.size - 18,
                        text=f'{int(s.hp)} / {int(s.max_hp)}',
                        fill='#aaffaa', font=('Arial', 7, 'bold')
                    )
            if self.room.spawn_point:
                self.room.spawn_point.draw(self.canvas)
            for e in self.room.enemies:
                ex, ey = e.x, e.y

                # ── Healer Totem ─────────────────────────────────────────────
                if getattr(e, '_immobile', False):
                    ts = e.size
                    # Stone pillar base
                    self.canvas.create_rectangle(ex-ts//2, ey-ts, ex+ts//2, ey+ts,
                                                 fill='#555555', outline='#333333', width=2)
                    # Glowing crystal on top
                    self.canvas.create_oval(ex-ts, ey-ts*2, ex+ts, ey-ts*0.2,
                                            fill='#22cc44', outline='#44ff88', width=2)
                    self.canvas.create_oval(ex-ts//2, ey-ts*1.7, ex+ts//2, ey-ts*0.5,
                                            fill='#88ffaa', outline='')
                    # Pulsing ring
                    pulse = abs(math.sin(time.time() * 3)) * 4
                    self.canvas.create_oval(ex-ts-pulse, ey-ts*2-pulse,
                                            ex+ts+pulse, ey-ts*0.2+pulse,
                                            fill='', outline='#44ff88', width=1)
                    continue


            # Draw decorations
            for deco in self.room.decorations:
                if deco['type'] == 'forest_wall':
                    pass  # Collision only — visual handled by dark bg + oval grass cutout

                elif deco['type'] == 'forest_edge':
                    x    = deco['x'] - cam_x
                    y    = deco['y'] - cam_y
                    size = deco['size']
                    # Lighten forest wall near Ice Cavern — matches the road gradient style
                    _ice_edge_dist = math.hypot(deco['x'] - (TOWN_CX + 3200),
                                                deco['y'] - (TOWN_CY + 420))
                    _ice_fade_r = 900
                    if _ice_edge_dist < _ice_fade_r:
                        # Power curve — stays dark far out, ramps sharply near clearing
                        _t = (1.0 - _ice_edge_dist / _ice_fade_r) ** 1.8
                        # Dark forest #2a5810  →  near-white icy #d8f0e0
                        _er  = int(0x2a + (0xd8 - 0x2a) * _t)
                        _eg  = int(0x58 + (0xf0 - 0x58) * _t)
                        _eb2 = int(0x10 + (0xe0 - 0x10) * _t)
                        _ecol = f'#{_er:02x}{_eg:02x}{_eb2:02x}'
                    else:
                        _ecol = '#2a5810'
                    self.canvas.create_oval(x - size, y - size,
                                            x + size, y + size,
                                            fill=_ecol, outline='')
                
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
                    now_f = time.time()

                    # ── Outer basin ───────────────────────────────────────
                    self.canvas.create_oval(x-size-14, y-size-14,
                                            x+size+14, y+size+14,
                                            fill='#7a6a50', outline='#4a3a28', width=3)
                    self.canvas.create_oval(x-size-8, y-size-8,
                                            x+size+8, y+size+8,
                                            fill='#4a7aaa', outline='#2a4a7a', width=2)
                    # Cobblestone rim detail
                    for _ri in range(8):
                        _ra = _ri * math.pi / 4 + now_f * 0.1
                        _rx = x + math.cos(_ra) * (size + 10)
                        _ry = y + math.sin(_ra) * (size + 10)
                        self.canvas.create_oval(_rx-5, _ry-5, _rx+5, _ry+5,
                                                fill='#8a7a60', outline='#5a4a38', width=1)
                    # ── Inner raised basin ────────────────────────────────
                    self.canvas.create_oval(x-size//2-6, y-size//2-6,
                                            x+size//2+6, y+size//2+6,
                                            fill='#8a7a60', outline='#4a3a28', width=2)
                    self.canvas.create_oval(x-size//2, y-size//2,
                                            x+size//2, y+size//2,
                                            fill='#5a8abb', outline='')
                    # ── Centre pillar — tall ornate column ────────────────
                    pole_top = y - size - 55   # much taller
                    self.canvas.create_polygon(
                        x-4, y,  x+4, y,
                        x+3, pole_top+8, x-3, pole_top+8,
                        fill='#9a8a70', outline='#4a3a28', width=1
                    )
                    # Decorative bands on pillar
                    for _pb in [0.25, 0.5, 0.75]:
                        _by = int(y + (pole_top - y) * _pb)
                        self.canvas.create_rectangle(x-6, _by-3, x+6, _by+3,
                                                     fill='#c0b090', outline='#5a4a28', width=1)
                    # Pillar top capital
                    self.canvas.create_oval(x-10, pole_top, x+10, pole_top+16,
                                            fill='#baa880', outline='#4a3a28', width=2)
                    # Small top basin on capital
                    self.canvas.create_oval(x-7, pole_top+4, x+7, pole_top+14,
                                            fill='#5a8abb', outline='#2a4a7a', width=1)
                    # ── Animated water arcs (8 jets from top capital) ─────
                    for _wi in range(8):
                        _wa = _wi * math.pi / 4
                        _phase = (_now_b * 1.4 + _wi * 0.125) % 1.0
                        # Draw each jet as a bezier-like curve using many small steps
                        _steps = 12
                        _prev_ax, _prev_ay = None, None
                        for _s in range(_steps + 1):
                            _t = _s / _steps
                            # Parabolic arc: out sideways, up then down
                            _arc_x = x + math.cos(_wa) * (size - 4) * _t
                            _arc_y = pole_top + 8 + (_t * (y - pole_top - 8)) - math.sin(math.pi * _t) * 32
                            # Shift by phase to animate flow
                            _t2 = (_t + _phase) % 1.0
                            _arc_x2 = x + math.cos(_wa) * (size - 4) * _t2
                            _arc_y2 = pole_top + 8 + (_t2 * (y - pole_top - 8)) - math.sin(math.pi * _t2) * 32
                            _ds = max(1, int(3 * (1 - _t2 * 0.6)))
                            _col = '#d0f0ff' if _t2 < 0.4 else '#80c8ee'
                            self.canvas.create_oval(_arc_x2-_ds, _arc_y2-_ds,
                                                    _arc_x2+_ds, _arc_y2+_ds,
                                                    fill=_col, outline='')
                    # ── Ripple rings on water surface ─────────────────────
                    for _ri2 in range(3):
                        _rp = (now_f * 0.8 + _ri2 * 0.33) % 1.0
                        _rr = int((size - 4) * _rp)
                        if _rr > 2:
                            self.canvas.create_oval(x-_rr, y-_rr//2,
                                                    x+_rr, y+_rr//2,
                                                    fill='', outline='#90c8ee',
                                                    width=1)
                
                elif deco['type'] == 'lamp':
                    lx = deco['x'] - cam_x
                    ly = deco['y'] - cam_y
                    now_l = time.time()
                    # ── Post shaft ──────────────────────────────────────────
                    self.canvas.create_rectangle(lx-3, ly, lx+3, ly+55,
                                                 fill='#2a2a2a', outline='#111', width=1)
                    # Base plate
                    self.canvas.create_rectangle(lx-8, ly+52, lx+8, ly+58,
                                                 fill='#1a1a1a', outline='#111', width=1)
                    # ── M-shaped cross-arm ───────────────────────────────────
                    # Horizontal bar
                    self.canvas.create_rectangle(lx-28, ly-4, lx+28, ly,
                                                 fill='#2a2a2a', outline='#111', width=1)
                    # Left arm droop (like an M tine)
                    self.canvas.create_line(lx-22, ly-4, lx-22, ly-14,
                                            fill='#2a2a2a', width=3)
                    # Right arm droop
                    self.canvas.create_line(lx+22, ly-4, lx+22, ly-14,
                                            fill='#2a2a2a', width=3)
                    # Centre top spike
                    self.canvas.create_line(lx, ly-4, lx, ly-20,
                                            fill='#2a2a2a', width=3)
                    self.canvas.create_polygon(lx-4, ly-20, lx+4, ly-20, lx, ly-28,
                                               fill='#2a2a2a', outline='')
                    # ── Left lantern ─────────────────────────────────────────
                    _flicker = int(abs(math.sin(now_l * 3.7 + 0.3)) * 3)
                    self.canvas.create_oval(lx-32-_flicker, ly-32-_flicker,
                                            lx-12+_flicker, ly-12+_flicker,
                                            fill='#ffcc44', outline='', stipple='gray25')
                    self.canvas.create_rectangle(lx-30, ly-30, lx-14, ly-14,
                                                 fill='#2a2a2a', outline='#888', width=1)
                    self.canvas.create_oval(lx-28, ly-28, lx-16, ly-16,
                                            fill='#FFD700', outline='')
                    self.canvas.create_line(lx-22, ly-30, lx-22, ly-14,
                                            fill='#1a1a1a', width=1)
                    self.canvas.create_line(lx-30, ly-22, lx-14, ly-22,
                                            fill='#1a1a1a', width=1)
                    # ── Right lantern ────────────────────────────────────────
                    self.canvas.create_oval(lx+12-_flicker, ly-32-_flicker,
                                            lx+32+_flicker, ly-12+_flicker,
                                            fill='#ffcc44', outline='', stipple='gray25')
                    self.canvas.create_rectangle(lx+14, ly-30, lx+30, ly-14,
                                                 fill='#2a2a2a', outline='#888', width=1)
                    self.canvas.create_oval(lx+16, ly-28, lx+28, ly-16,
                                            fill='#FFD700', outline='')
                    self.canvas.create_line(lx+22, ly-30, lx+22, ly-14,
                                            fill='#1a1a1a', width=1)
                    self.canvas.create_line(lx+14, ly-22, lx+30, ly-22,
                                            fill='#1a1a1a', width=1)
                
                elif deco['type'] in ('dungeon_clearing', 'plain_clearing'):
                    pass  # drawn in pre-pass above player layer
            
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
            # Draw background — Ice Cavern (dungeon 3) gets a bright icy palette
            if self.dungeon_id == 1:    # Forest
                _bg_col, _wall_col = '#1a2e1a', '#0d1a0d'
            elif self.dungeon_id == 2:  # Volcano
                _bg_col, _wall_col = '#3d2010', '#2a1508'
            elif self.dungeon_id == 3:  # Ice Cavern
                _bg_col, _wall_col = '#2e4a58', '#4a7a90'
            else:
                _bg_col, _wall_col = '#2a2a2a', '#505050'
            self.canvas.create_rectangle(0, 0, WINDOW_W, WINDOW_H, fill=_bg_col, outline='')
            
            # Set player coordinates (no camera offset in dungeons)
            px, py = self.player.x, self.player.y
            
            # Draw walls with openings
            wall_thickness = 20
            opening_size = 150

            # Top wall
            if self.room_row > 0:
                opening_x = WINDOW_W // 2 - opening_size // 2
                self.canvas.create_rectangle(0, 0, opening_x, wall_thickness, fill=_wall_col)
                self.canvas.create_rectangle(opening_x + opening_size, 0, WINDOW_W, wall_thickness, fill=_wall_col)
            else:
                # Solid top wall
                self.canvas.create_rectangle(0, 0, WINDOW_W, wall_thickness, fill=_wall_col)

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
            if self.room_row < ROOM_ROWS - 1:
                opening_x = WINDOW_W // 2 - opening_size // 2
                boss_defeated = self.boss_defeated.get(self.dungeon_id, False)
                is_boss_room = (self.room_row == 0 and self.room_col == 4)
                if is_boss_room and not boss_defeated:
                    # Locked — draw solid wall with a red gate indicator
                    self.canvas.create_rectangle(0, WINDOW_H - wall_thickness, WINDOW_W, WINDOW_H, fill=_wall_col)
                    self.canvas.create_rectangle(opening_x, WINDOW_H - wall_thickness - 8,
                                                 opening_x + opening_size, WINDOW_H,
                                                 fill='#8B0000', outline='#ff0000', width=2)
                    self.canvas.create_text(WINDOW_W // 2, WINDOW_H - wall_thickness // 2 - 4,
                                            text='🔒', fill='red', font=('Arial', 14))
                else:
                    self.canvas.create_rectangle(0, WINDOW_H - wall_thickness, opening_x, WINDOW_H, fill=_wall_col)
                    self.canvas.create_rectangle(opening_x + opening_size, WINDOW_H - wall_thickness, WINDOW_W, WINDOW_H, fill=_wall_col)
            else:
                self.canvas.create_rectangle(0, WINDOW_H - wall_thickness, WINDOW_W, WINDOW_H, fill=_wall_col)

            # Left wall
            if self.room_col > 0:
                # Treasure room (1,4): left wall always solid
                if self.room_row == 1 and self.room_col == 4:
                    self.canvas.create_rectangle(0, 0, wall_thickness, WINDOW_H, fill=_wall_col)
                else:
                    opening_y = WINDOW_H // 2 - opening_size // 2
                    self.canvas.create_rectangle(0, 0, wall_thickness, opening_y, fill=_wall_col)
                    self.canvas.create_rectangle(0, opening_y + opening_size, wall_thickness, WINDOW_H, fill=_wall_col)
            else:
                self.canvas.create_rectangle(0, 0, wall_thickness, WINDOW_H, fill=_wall_col)

            # Right wall
            if self.room_row == 1 and self.room_col == 3:
                # Solid — no passage to treasure room from here
                self.canvas.create_rectangle(WINDOW_W - wall_thickness, 0, WINDOW_W, WINDOW_H, fill=_wall_col)
            elif self.room_col < ROOM_COLS - 1:
                opening_y = WINDOW_H // 2 - opening_size // 2
                self.canvas.create_rectangle(WINDOW_W - wall_thickness, 0, WINDOW_W, opening_y, fill=_wall_col)
                self.canvas.create_rectangle(WINDOW_W - wall_thickness, opening_y + opening_size, WINDOW_W, WINDOW_H, fill=_wall_col)
            else:
                self.canvas.create_rectangle(WINDOW_W - wall_thickness, 0, WINDOW_W, WINDOW_H, fill=_wall_col)
            
            # Set player coordinates (no camera offset in dungeons)
            px, py = self.player.x, self.player.y

            # ── Halo of Radiance: sun + rotating beams behind player ──────────
            if getattr(self.player, '_halo_active', False):
                _ha = getattr(self.player, '_halo_angle', 0.0)
                for _ri in range(8):
                    _ra = _ha + _ri * (math.pi / 4)
                    _bex = px + math.cos(_ra) * 90
                    _bey = py + math.sin(_ra) * 90
                    self.canvas.create_line(px, py, _bex, _bey, fill='#ffcc00', width=8, stipple='gray25')
                    self.canvas.create_line(px, py, _bex, _bey, fill='#ffee00', width=4, stipple='gray50')
                    self.canvas.create_line(px, py, _bex, _bey, fill='#ffffff', width=1, stipple='gray50')
                self.canvas.create_oval(px-22, py-22, px+22, py+22,
                                        fill='#ffee00', outline='#ffaa00', width=2)
                self.canvas.create_oval(px-13, py-13, px+13, py+13,
                                        fill='#ffffaa', outline='')
            # ── Lingering Aura circles (drawn here so they're behind player/weapon) ──
            for _ap in self.particles:
                if _ap.rtype == 'aura_behind':
                    _ar = _ap.size * max(0.1, _ap.life / 0.5)
                    self.canvas.create_oval(_ap.x-_ar, _ap.y-_ar, _ap.x+_ar, _ap.y+_ar,
                                            fill='yellow', outline='')
            # ── Lingering Aura beam (aura circle drawn via rtype='aura' particles) ──
            if getattr(self.player, '_rapid_active', False):
                _eq = next((it for it in self.player.equipped_items if it.item_type == 'weapon'), None)
                _wangle = getattr(self.player, 'angle', 0)
                if _eq and getattr(_eq, 'weapon_type', '') == 'spear':
                    _stx = getattr(self.player, '_spear_tip_x', self.player.x)
                    _sty = getattr(self.player, '_spear_tip_y', self.player.y)
                    _sbx = getattr(self.player, '_spear_base_x', self.player.x)
                    _sby = getattr(self.player, '_spear_base_y', self.player.y)
                    _sdx = _stx - _sbx;  _sdy = _sty - _sby
                    _slen = math.hypot(_sdx, _sdy) or 1
                    _snx = _sdx / _slen;  _sny = _sdy / _slen
                    _ex = _stx + _snx * 60;  _ey = _sty + _sny * 60
                    _perp = math.atan2(_sdy, _sdx) + math.pi / 2
                    _pcx = math.cos(_perp);  _pcy = math.sin(_perp)
                    self.canvas.create_line(_sbx, _sby, _ex, _ey, fill='yellow', width=6, capstyle='butt')
                    for _ in range(10):
                        _a = math.atan2(_sdy, _sdx) + random.uniform(-0.4, 0.4)
                        _d = random.uniform(2, 10)
                        self.canvas.create_oval(_ex+math.cos(_a)*_d-2, _ey+math.sin(_a)*_d-2,
                                                _ex+math.cos(_a)*_d+2, _ey+math.sin(_a)*_d+2,
                                                fill='#ffff88', outline='')
                    # Damage enemies in beam path (world coords)
                    _str_dmg = max(1, getattr(self.player, 'strength', 5))
                    _w_sbx = getattr(self.player, '_spear_base_x', self.player.x)
                    _w_sby = getattr(self.player, '_spear_base_y', self.player.y)
                    _w_ex  = _w_sbx + _snx * 60;  _w_ey = _w_sby + _sny * 60
                    _blen  = math.hypot(_w_ex-_w_sbx, _w_ey-_w_sby) or 1
                    for _be in list(self.room.enemies):
                        _bdx = _be.x - _w_sbx;  _bdy = _be.y - _w_sby
                        _bt  = max(0, _bdx*(_w_ex-_w_sbx)/_blen + _bdy*(_w_ey-_w_sby)/_blen)
                        _bpx = _w_sbx + (_w_ex-_w_sbx)/_blen*_bt
                        _bpy = _w_sby + (_w_ey-_w_sby)/_blen*_bt
                        if 0 <= _bt <= _blen and math.hypot(_be.x-_bpx, _be.y-_bpy) < _be.size + 4:
                            self.damage_enemy(_be, _str_dmg * 0.016)
                elif _eq:
                    _wbx = px + math.cos(_wangle) * 36
                    _wby = py + math.sin(_wangle) * 36
                    _wex = px + math.cos(_wangle) * 106
                    _wey = py + math.sin(_wangle) * 106
                    self.canvas.create_line(_wbx, _wby, _wex, _wey, fill='yellow', width=6, capstyle='butt')
                    for _ in range(10):
                        _a = _wangle + random.uniform(-0.4, 0.4)
                        _d = random.uniform(2, 10)
                        self.canvas.create_oval(_wex+math.cos(_a)*_d-2, _wey+math.sin(_a)*_d-2,
                                                _wex+math.cos(_a)*_d+2, _wey+math.sin(_a)*_d+2,
                                                fill='#ffff88', outline='')
                    _str_dmg2 = max(1, getattr(self.player, 'strength', 5))
                    _pw_bx = self.player.x + math.cos(_wangle) * 36
                    _pw_by = self.player.y + math.sin(_wangle) * 36
                    _pw_ex = self.player.x + math.cos(_wangle) * 106
                    _pw_ey = self.player.y + math.sin(_wangle) * 106
                    _wblen = math.hypot(_pw_ex-_pw_bx, _pw_ey-_pw_by) or 1
                    for _be2 in list(self.room.enemies):
                        _bdx2 = _be2.x - _pw_bx;  _bdy2 = _be2.y - _pw_by
                        _bt2  = max(0, _bdx2*(_pw_ex-_pw_bx)/_wblen + _bdy2*(_pw_ey-_pw_by)/_wblen)
                        _bpx2 = _pw_bx + (_pw_ex-_pw_bx)/_wblen*_bt2
                        _bpy2 = _pw_by + (_pw_ey-_pw_by)/_wblen*_bt2
                        if 0 <= _bt2 <= _wblen and math.hypot(_be2.x-_bpx2, _be2.y-_bpy2) < _be2.size + 4:
                            self.damage_enemy(_be2, _str_dmg2 * 0.016)
            equipped_weapon = None
            weapon_item = None
            for item in self.player.equipped_items:
                if item.item_type == 'weapon':
                    equipped_weapon = item
                    break
            
            # NOW CREATE THE WEAPON - OUTSIDE THE LOOP
            if equipped_weapon:
                weapon_visual = getattr(equipped_weapon, 'weapon_type', 'sword')
                # Arcane Longbow gets its own special visual type
                if equipped_weapon.name == 'Arcane Longbow':
                    weapon_visual = 'arcane_bow'
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
                elif weapon_visual == 'ignis_staff':
                    weapon_item.color = '#DAA520'
                    weapon_item.gem_color = '#FFD700'
                elif weapon_visual == 'wand':
                    weapon_item.color = 'purple'
                    weapon_item.gem_color = 'yellow'
                elif weapon_visual == 'dagger':
                    weapon_item.color = 'purple'
                elif equipped_weapon and equipped_weapon.name == 'Arcane Longbow':
                    weapon_item.color = '#8844cc'
                    weapon_item.gem_color = '#cc88ff'
                elif weapon_visual == 'hand':
                    weapon_item.color = '#FFA500'
                elif weapon_visual == 'bow':
                    weapon_item.color = 'brown'
                        
                # Update weapon position to aim at mouse
                _wpx2, _wpy2 = self.get_mouse_world_pos()
                weapon_item.update(px, py, _wpx2, _wpy2)

                # Draw weapons that go UNDER the player
                if weapon_visual in ("spear", "staff", "ignis_staff", "sword", "dagger", "quarterstaff", "katana", "axe", "scythe"):
                    weapon_item.draw(self.canvas)

            # ── Circle of Life heal zones (ring only — player/particles visible inside) ──
            _now_cl2 = time.time()
            for _cl in list(getattr(self, '_life_circles', [])):
                _clr = _cl['r']
                _remaining2 = max(0, _cl['end'] - _now_cl2)
                _alpha_stip2 = 'gray50' if _remaining2 < 1.5 else ''
                self.canvas.create_oval(_cl['x'] - _clr, _cl['y'] - _clr,
                                        _cl['x'] + _clr, _cl['y'] + _clr,
                                        fill='', outline='#44ff88', width=3, stipple=_alpha_stip2)

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
            ws_form_name = getattr(self.player, 'wild_shape_form', None)
            ws_fd        = next((f for f in WILD_SHAPE_FORMS if f['name'] == ws_form_name), None) if ws_form_name else None
            if getattr(self.player, '_iron_guard_active', False):
                player_color = '#888888'
            elif ws_fd:
                player_color = ws_fd['color']
            else:
                player_color = CLASS_COLORS.get(self.player.class_name, "cyan")

            # White outline
            self.canvas.create_oval(px-size-2, py-size-2, px+size+2, py+size+2, fill='white')
            # Colored body
            self.canvas.create_oval(px-size, py-size, px+size, py+size, fill=player_color)

            # Iron Guard: metallic ring + highlight arc
            if getattr(self.player, '_iron_guard_active', False):
                self.canvas.create_oval(px-size-1, py-size-1, px+size+1, py+size+1,
                                        fill='', outline='#cccccc', width=2)
                self.canvas.create_arc(px-size+2, py-size+2, px+size-2, py+size-2,
                                       start=40, extent=110,
                                       style='arc', outline='white', width=3)

            # Wild shape: draw form icon; normal: draw name initial
            if ws_fd:
                self.canvas.create_oval(px-size-5, py-size-5, px+size+5, py+size+5,
                                        fill='', outline=ws_fd['color'], width=3)
                self.canvas.create_text(px, py, text=ws_fd['icon'],
                                        font=('Arial', 14), fill='white')
            else:
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
                if weapon_item.item_type == 'arcane_bow':
                    weapon_item.draw(self.canvas)
                elif equipped_weapon.weapon_type not in ("spear", "staff", "ignis_staff", "sword", "dagger", "quarterstaff", "katana", "axe", "scythe"):
                    weapon_item.draw(self.canvas)

            # ── Stone Shield offhand draw (dungeon) ───────────────────────────
            _dung_shield = next((it for it in self.player.equipped_items
                                 if it.item_type == 'offhand'), None)
            if _dung_shield:
                _mx_d, _my_d = self.get_mouse_world_pos()
                _face_ang_d  = math.atan2(_my_d - self.player.y, _mx_d - self.player.x)
                _sh_ang_d    = _face_ang_d - math.pi * 0.55
                _sh_dist_d   = 20
                _shx_d = px + math.cos(_sh_ang_d) * _sh_dist_d
                _shy_d = py + math.sin(_sh_ang_d) * _sh_dist_d
                _perp_d = _sh_ang_d + math.pi / 2
                _sw_d = 26; _sd_d = 7
                _sh_pts_d = [
                    _shx_d + math.cos(_perp_d)*_sw_d,             _shy_d + math.sin(_perp_d)*_sw_d,
                    _shx_d + math.cos(_perp_d)*_sw_d*0.6 + math.cos(_sh_ang_d)*_sd_d,
                    _shy_d + math.sin(_perp_d)*_sw_d*0.6 + math.sin(_sh_ang_d)*_sd_d,
                    _shx_d - math.cos(_perp_d)*_sw_d*0.6 + math.cos(_sh_ang_d)*_sd_d,
                    _shy_d - math.sin(_perp_d)*_sw_d*0.6 + math.sin(_sh_ang_d)*_sd_d,
                    _shx_d - math.cos(_perp_d)*_sw_d,             _shy_d - math.sin(_perp_d)*_sw_d,
                ]
                _charges_d = getattr(self.player, 'shield_charges', 30)
                _sh_col_d  = '#8888bb' if _charges_d > 0 else '#445566'
                self.canvas.create_polygon(_sh_pts_d, fill=_sh_col_d, outline='#ccddff', width=2)
                self.canvas.create_line(
                    _shx_d - math.cos(_perp_d)*_sw_d*0.4, _shy_d - math.sin(_perp_d)*_sw_d*0.4,
                    _shx_d + math.cos(_perp_d)*_sw_d*0.4, _shy_d + math.sin(_perp_d)*_sw_d*0.4,
                    fill='#ddeeff', width=2)
                _bar_cx_d = _shx_d + math.cos(_sh_ang_d) * (_sd_d + 5)
                _bar_cy_d = _shy_d + math.sin(_sh_ang_d) * (_sd_d + 5)
                _blen_d = 22
                _bar_x0_d = _bar_cx_d - math.cos(_perp_d) * _blen_d
                _bar_y0_d = _bar_cy_d - math.sin(_perp_d) * _blen_d
                _bar_x1_d = _bar_cx_d + math.cos(_perp_d) * _blen_d
                _bar_y1_d = _bar_cy_d + math.sin(_perp_d) * _blen_d
                self.canvas.create_line(_bar_x0_d, _bar_y0_d, _bar_x1_d, _bar_y1_d,
                                        fill='#333355', width=4, capstyle='round')
                _fill_f_d = max(0, min(1, _charges_d / 30))
                if _fill_f_d > 0:
                    _fx1_d = _bar_x0_d + (_bar_x1_d-_bar_x0_d)*_fill_f_d
                    _fy1_d = _bar_y0_d + (_bar_y1_d-_bar_y0_d)*_fill_f_d
                    _col_bar_d = '#6688ff' if _fill_f_d > 0.3 else '#ff4444'
                    self.canvas.create_line(_bar_x0_d, _bar_y0_d, _fx1_d, _fy1_d,
                                            fill=_col_bar_d, width=4, capstyle='round')
                self.canvas.create_text(_bar_cx_d + math.cos(_sh_ang_d)*8,
                                        _bar_cy_d + math.sin(_sh_ang_d)*8,
                                        text=str(_charges_d), fill='white',
                                        font=('Arial', 7, 'bold'))
                # Store shield face world position for projectile collision
                self.player._shield_face_x   = _shx_d
                self.player._shield_face_y   = _shy_d
                self.player._shield_face_ang = _sh_ang_d
                self.player._shield_face_sw  = _sw_d + 4

            if hasattr(self.player, '_orbit_blades') and self.player._orbit_blades:
                for blade in self.player._orbit_blades:
                    if not blade.get('launched', False):
                        orb_x = px + math.cos(blade['angle']) * 90
                        orb_y = py + math.sin(blade['angle']) * 90
                        orb = Item(orb_x, orb_y, 'greatsword', '#aaaaff', 22)
                        orb.angle = blade['angle'] + math.pi / 2
                        orb.draw(self.canvas)
                        self.canvas.create_oval(
                            orb_x - 14, orb_y - 14, orb_x + 14, orb_y + 14,
                            fill='', outline='#6688ff', width=1
                        )

        # NOW CONTINUE WITH THE REST (summons, spawn point, enemies, etc.)
        # This should be at the SAME indentation level as the town's "for s in self.summons:"
        for s in self.summons:
            s.draw(self.canvas)
            # Numerical HP — only visible with Identify passive
            if ('Identify' in getattr(self.player, 'tree_unlocked', set())
                    and self.player.passive_toggles.get('Identify', True)
                    and s.max_hp > 0):
                _sb_w = max(s.size * 2, 36)
                _sb_x = s.x - _sb_w // 2
                _sb_y = s.y - s.size - 8
                # Green HP bar
                self.canvas.create_rectangle(_sb_x, _sb_y, _sb_x + _sb_w, _sb_y + 4,
                                             fill='#1a3300', outline='')
                _frac = max(0.0, s.hp / s.max_hp)
                self.canvas.create_rectangle(_sb_x, _sb_y, _sb_x + int(_sb_w * _frac), _sb_y + 4,
                                             fill='#44ff44', outline='')
                # Numeric text above bar
                self.canvas.create_text(
                    s.x, s.y - s.size - 18,
                    text=f'{int(s.hp)} / {int(s.max_hp)}',
                    fill='#aaffaa', font=('Arial', 7, 'bold')
                )
        if self.room.spawn_point:
            self.room.spawn_point.draw(self.canvas)
        for e in self.room.enemies:
            ex, ey = e.x, e.y
            # ── Shocked: shake offset ─────────────────────────────────────────
            if hasattr(e, '_shocked_until') and e._shocked_until > time.time():
                ex += random.randint(-3, 3)
                ey += random.randint(-3, 3)

            # ── BOMB CREEPER — custom bomb visuals ────────────────────────────
            

            # Decide layering rules
            weapons_below = ("spear", "staff", "hand","sword")   # drawn BEFORE body
            weapons_above = ("bow")                      # drawn AFTER body

            # Bosses: draw their special body first
            if isinstance(e, Boss):
                # ── GreatSword Boss — full custom render ─────────────────────
                if e.boss_type == 'GreatSword':
                    hp_frac = e.hp / e.max_hp
                    bs = e.size

                    # Phase 3: spinning greatsword
                    if hp_frac <= 0.15:
                        sw_item = Item(ex, ey, 'greatsword', '#cc3333', 36)
                        sw_item.angle = getattr(e, 'gs_swing_angle', 0)
                        sw_item.draw(self.canvas)
                    else:
                        # Greatsword in hand — drawn BEFORE boss body
                        if e.item:
                            e.item.x = ex; e.item.y = ey
                            e.item.draw(self.canvas)

                    # Phase 2 orbital swords
                    if getattr(e, 'gs_orbital_active', False):
                        for sw in e.gs_orbital_swords:
                            if not sw['launched']:
                                orb_x = ex + math.cos(sw['angle']) * Boss.ORBITAL_RADIUS
                                orb_y = ey + math.sin(sw['angle']) * Boss.ORBITAL_RADIUS
                                orb = Item(orb_x, orb_y, 'greatsword', '#cc3333', 22)
                                orb.angle = sw['angle'] + math.pi/2
                                orb.draw(self.canvas)

                    # Boss body
                    if hp_frac <= 0.15:
                        body_col = '#550000'
                        pulse2 = abs(math.sin(time.time() * 5)) * 3
                        self.canvas.create_oval(ex-bs-3-pulse2, ey-bs-3-pulse2,
                                                ex+bs+3+pulse2, ey+bs+3+pulse2,
                                                fill='', outline='white', width=3)
                    elif hp_frac <= 0.60:
                        body_col = '#8B0000'
                    else:
                        body_col = '#cc3333'

                    self.canvas.create_oval(ex-bs-2, ey-bs-2, ex+bs+2, ey+bs+2, fill='#111111')
                    self.canvas.create_oval(ex-bs, ey-bs, ex+bs, ey+bs,
                                            fill=body_col, outline='#880000', width=2)

                    # Name + phase label only with Identify
                    _gs_has_id = ('Identify' in getattr(self.player, 'tree_unlocked', set())
                                  and self.player.passive_toggles.get('Identify', True))
                    if _gs_has_id:
                        phase_txt = ('⚔ Phase 3 — IMMUNE' if hp_frac <= 0.15
                                     else '⚔ Phase 2' if hp_frac <= 0.60 else '⚔ Phase 1')
                        self.canvas.create_text(ex, ey-bs-14, text=e.name,
                                                fill='white', font=('Arial', 9, 'bold'))
                        self.canvas.create_text(ex, ey-bs-26, text=phase_txt,
                                                fill='#ff6666', font=('Arial', 8))
                    continue

                boss_shapes = {
                    "IceGiant": ("diamond", "cyan"),
                    "ShadowWraith": ("triangle", "purple"),
                    "EarthTitan": ("oval", "brown"),
                }
                # ── Ignis the Burning — custom multi-phase render ─────────────
                if e.boss_type == 'FireLord':
                    _now_ig  = time.time()
                    _ig_phase = getattr(e, 'ignis_phase', 1)
                    _ig_sz    = e.size
                    hp_frac_ig = e.hp / max(getattr(e, '_ignis_true_max_hp', e.max_hp), 1)

                    # Identify check (used for HP bars + phase labels in phases 1-3)
                    _has_id = ('Identify' in getattr(self.player, 'tree_unlocked', set())
                               and self.player.passive_toggles.get('Identify', True))
                    # Analysis check (used for phase 4 info — requires active Analysis cast)
                    _analysed = any(
                        d['target'] is e for d in getattr(self, '_analysis_displays', [])
                        if d['until'] > _now_ig
                    )

                    if _ig_phase == 4:
                        # ── Phase 4: small phoenix bird ───────────────────────
                        _pulse = abs(math.sin(_now_ig * 8)) * 3
                        # Glowing aura
                        self.canvas.create_oval(
                            ex-_ig_sz-8-_pulse, ey-_ig_sz-8-_pulse,
                            ex+_ig_sz+8+_pulse, ey+_ig_sz+8+_pulse,
                            fill='', outline='#ffcc00', width=2)
                        # Bird body
                        self.canvas.create_oval(
                            ex-_ig_sz, ey-_ig_sz, ex+_ig_sz, ey+_ig_sz,
                            fill='#ff8800', outline='#ffcc00', width=2)
                        # Wing feathers
                        _bdir = getattr(e, 'ignis_bird_dir', 0)
                        _perp = _bdir + math.pi/2
                        for _ws in (-1, 1):
                            _wx = ex + math.cos(_perp)*_ws*_ig_sz*1.6
                            _wy = ey + math.sin(_perp)*_ws*_ig_sz*1.6
                            self.canvas.create_polygon(
                                [ex, ey, _wx-4, _wy-4, _wx+4, _wy+4],
                                fill='#ff4400', outline='')
                        # Bright eye
                        _ex2 = ex + math.cos(_bdir)*_ig_sz*0.4
                        _ey2 = ey + math.sin(_bdir)*_ig_sz*0.4
                        self.canvas.create_oval(_ex2-3, _ey2-3, _ex2+3, _ey2+3,
                                                fill='white', outline='')
                        self.canvas.create_oval(_ex2-1, _ey2-1, _ex2+1, _ey2+1,
                                                fill='black', outline='')
                        # Info ONLY if player has used Analysis on this entity
                        if _analysed:
                            _t4_elapsed = _now_ig - getattr(e, 'ignis_phase4_start', _now_ig)
                            _t4_remain  = max(0.0, 10.0 - _t4_elapsed)
                            self.canvas.create_text(ex, ey-_ig_sz-18,
                                text='🔥 Ignis — Phoenix Form',
                                fill='#ffcc00', font=('Arial', 9, 'bold'))
                            self.canvas.create_text(ex, ey-_ig_sz-7,
                                text=f'Revives in {_t4_remain:.1f}s' if _t4_remain > 0 else 'Reviving!',
                                fill='#ff8800', font=('Arial', 8))
                            # No HP bar in phoenix form
                    else:
                        # ── Phase 1-3: humanoid fire lord body ────────────────
                        _glow_cols = {1: '#ff4400', 2: '#ff6600', 3: '#ffcc00'}
                        _gc = _glow_cols.get(_ig_phase, '#ff4400')
                        _gpulse = abs(math.sin(_now_ig * 2.5)) * 6
                        self.canvas.create_oval(
                            ex-_ig_sz-10-_gpulse, ey-_ig_sz-10-_gpulse,
                            ex+_ig_sz+10+_gpulse, ey+_ig_sz+10+_gpulse,
                            fill='', outline=_gc, width=2)
                        # Draw fire staff
                        if hasattr(e, '_ignis_staff'):
                            e._ignis_staff.x = ex
                            e._ignis_staff.y = ey
                            _sang = math.atan2(self.player.y-ey, self.player.x-ex)
                            e._ignis_staff.angle = _sang
                            e._ignis_staff.draw(self.canvas)
                        # Body
                        _body_col = '#cc2200' if _ig_phase == 1 else ('#ff4400' if _ig_phase == 2 else '#ff8800')
                        self.canvas.create_oval(ex-_ig_sz-2, ey-_ig_sz-2,
                                                ex+_ig_sz+2, ey+_ig_sz+2,
                                                fill='#110000', outline='#cc2200', width=3)
                        self.canvas.create_oval(ex-_ig_sz, ey-_ig_sz,
                                                ex+_ig_sz, ey+_ig_sz,
                                                fill=_body_col, outline='')
                        # Lava cracks
                        _ncrack = 4 if _ig_phase < 3 else 8
                        for _ic in range(_ncrack):
                            _ica = (_now_ig * 0.9 + _ic * (2*math.pi/_ncrack)) % (2*math.pi)
                            _icx1 = ex + math.cos(_ica) * _ig_sz*0.28
                            _icy1 = ey + math.sin(_ica) * _ig_sz*0.28
                            _icx2 = ex + math.cos(_ica) * _ig_sz*0.88
                            _icy2 = ey + math.sin(_ica) * _ig_sz*0.88
                            self.canvas.create_line(_icx1,_icy1,_icx2,_icy2,
                                                    fill=random.choice(['#ff4500','#ff7700','#ffaa00']),
                                                    width=2)
                        # Bright core
                        _core = _ig_sz * 0.38
                        self.canvas.create_oval(ex-_core, ey-_core, ex+_core, ey+_core,
                                                fill='#ff8800', outline='')
                        self.canvas.create_oval(ex-_core*0.4, ey-_core*0.4,
                                                ex+_core*0.4, ey+_core*0.4,
                                                fill='#ffee00', outline='')
                        # ── Info only with Identify ───────────────────────────
                        if _has_id:
                            _phase_labels = {1: '🔥 Phase 1', 2: '🔥🔥 Phase 2', 3: '☄  Phase 3'}
                            self.canvas.create_text(ex, ey-_ig_sz-18,
                                text='Ignis the Burning',
                                fill='#ff8800', font=('Arial', 9, 'bold'))
                            self.canvas.create_text(ex, ey-_ig_sz-7,
                                text=_phase_labels.get(_ig_phase, ''),
                                fill=_gc, font=('Arial', 8))
                            # HP bar
                            _hbw = 70
                            _hbx = ex - _hbw//2
                            _hby = ey - _ig_sz - 28
                            self.canvas.create_rectangle(_hbx, _hby, _hbx+_hbw, _hby+6,
                                                         fill='#330000', outline='')
                            self.canvas.create_rectangle(_hbx, _hby,
                                                         _hbx+int(_hbw*hp_frac_ig), _hby+6,
                                                         fill=_gc, outline='')
                            self.canvas.create_text(ex, ey-_ig_sz-37,
                                text=f'{int(e.hp)}/{int(e.max_hp)}', fill='white',
                                font=('Arial', 8))
                    continue
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
                "Dark Mage": ("triangle", "cyan"),
                "Summoner": ("oval", "pink"),
                "Venom Lurker": ("oval", "lime"),
                "Healer": ("triangle", "yellow"),
            }

            # ── Arcane Archer custom draw ─────────────────────────────────────
            _has_identify = ('Identify' in getattr(self.player, 'tree_unlocked', set())
                             and self.player.passive_toggles.get('Identify', True))
            # Defined early so shocked-text guard below can use it
            _is_custom_drawn = (e.name in ('Arcane Archer', 'Stone Guardian', 'Flame Elemental')
                                or getattr(e, '_is_bomb', False)
                                or getattr(e, '_is_ignismancer', False))

            # ── Shocked: yellow glow + shake ─────────────────────────────────
            if hasattr(e, '_shocked_until') and e._shocked_until > time.time():
                _ss = e.size + 10
                # Yellow electric glow rings
                for _ring in range(2):
                    _ro = _ring * 5
                    self.canvas.create_oval(
                        ex - _ss - _ro, ey - _ss - _ro,
                        ex + _ss + _ro, ey + _ss + _ro,
                        fill='', outline='#ffff00', width=2, stipple='gray50'
                    )
                self.canvas.create_oval(
                    ex - _ss + 2, ey - _ss + 2,
                    ex + _ss - 2, ey + _ss - 2,
                    fill='#ffff44', outline='', stipple='gray25'
                )
                # Custom enemies add shocked into their own stacked label block below
                if _has_identify and not _is_custom_drawn:
                    self.canvas.create_text(ex, ey - e.size - 22,
                                            text='⚡ SHOCKED',
                                            fill='#ffff00', font=('Arial', 8, 'bold'))

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
                # Countdown timer — only visible with Identify
                if _has_identify:
                    self.canvas.create_text(ex, ey - _hs - 6,
                                            text=f"❄ {remaining_freeze:.1f}s",
                                            fill='#00eeff', font=('Arial', 8, 'bold'))


            if e.name == "Arcane Archer":
                _now_aa = time.time()
                _pulse = abs(math.sin(_now_aa * 3)) * 4
                # Arcane glow ring
                self.canvas.create_oval(ex-e.size-6-_pulse, ey-e.size-6-_pulse,
                                        ex+e.size+6+_pulse, ey+e.size+6+_pulse,
                                        fill='', outline='#8844cc', width=2, stipple='gray50')
                # Body — dark purple diamond
                pts = [ex, ey-e.size, ex+e.size, ey, ex, ey+e.size, ex-e.size, ey]
                self.canvas.create_polygon(pts, fill='#6622aa', outline='#cc88ff', width=2)
                # Eye glows
                self.canvas.create_oval(ex-5, ey-4, ex-1, ey, fill='#ff88ff', outline='')
                self.canvas.create_oval(ex+1, ey-4, ex+5, ey, fill='#ff88ff', outline='')
                # Long arcane bow — drawn perpendicular to facing direction
                _ba = math.atan2(self.player.y-ey, self.player.x-ex)
                _bow_len = e.size * 2.4
                _perp_b = _ba + math.pi / 2
                _bx1 = ex + math.cos(_ba)*4 + math.cos(_perp_b)*_bow_len
                _by1 = ey + math.sin(_ba)*4 + math.sin(_perp_b)*_bow_len
                _bx2 = ex + math.cos(_ba)*4 - math.cos(_perp_b)*_bow_len
                _by2 = ey + math.sin(_ba)*4 - math.sin(_perp_b)*_bow_len
                _bcx = ex + math.cos(_ba) * (e.size + 16)
                _bcy = ey + math.sin(_ba) * (e.size + 16)
                self.canvas.create_line(_bx1, _by1, _bcx, _bcy, _bx2, _by2,
                                        fill='#8844cc', width=4, smooth=True)
                self.canvas.create_line(_bx1, _by1, _bx2, _by2,
                                        fill='#cc88ff', width=1)
                for _bi in range(3):
                    _bt = (_bi + 0.5) / 3
                    _bgx = _bx1 + (_bx2-_bx1)*_bt
                    _bgy = _by1 + (_by2-_by1)*_bt
                    _bgp = abs(math.sin(_now_aa*4+_bi)) * 3
                    self.canvas.create_oval(_bgx-2-_bgp, _bgy-2-_bgp,
                                            _bgx+2+_bgp, _bgy+2+_bgp,
                                            fill='#cc88ff', outline='')
                # Name + HP
                self.canvas.create_text(ex, ey-e.size-14, text="Arcane Archer",
                                        fill='#cc88ff', font=('Arial', 8, 'bold'))
                if _has_identify:
                    self.canvas.create_text(ex, ey-e.size-26, text=f"{int(e.hp)}/{int(e.max_hp)}",
                                            fill='white', font=('Arial', 7))
                    # Status effects — drawn above HP, stacked so they never overlap
                    _aa_now = time.time(); _aa_ty = ey - e.size - 44
                    if hasattr(e, '_shocked_until') and e._shocked_until > _aa_now:
                        self.canvas.create_text(ex, _aa_ty, text='⚡ SHOCKED', fill='#ffff00', font=('Arial', 8, 'bold'))
                        _aa_ty -= 12
                    _aa_daze = max(getattr(e, '_smoke_until', 0), getattr(e, '_dazed_until', 0))
                    if _aa_daze > _aa_now:
                        self.canvas.create_text(ex, _aa_ty, text=f'💨 DAZED {_aa_daze-_aa_now:.1f}s', fill='#aaaaaa', font=('Arial', 8, 'bold'))
                        _aa_ty -= 12
                    if hasattr(e, '_poison_until') and e._poison_until > _aa_now:
                        _apt = getattr(e, '_poison_tier', 1); _atl = {1:'I',2:'II',3:'III'}.get(_apt,'I')
                        self.canvas.create_text(ex, _aa_ty, text=f'☠ POISON T{_atl} {e._poison_until-_aa_now:.1f}s', fill='#44ff44', font=('Arial', 8, 'bold'))
                        _aa_ty -= 12
                    if hasattr(e, '_wet_until') and e._wet_until > _aa_now:
                        _awt = getattr(e, '_wet_tier', 1)
                        self.canvas.create_text(ex, _aa_ty, text=f'💧 WET T{_awt} {e._wet_until-_aa_now:.1f}s', fill='#44ccff', font=('Arial', 8, 'bold'))
                continue

            # ── Stone Guardian custom draw ────────────────────────────────────
            if e.name == "Stone Guardian":
                _now_sg = time.time()
                # Draw sword on left side before body
                if e.item:
                    _sa2 = math.atan2(self.player.y-ey, self.player.x-ex)
                    _sw_ang = _sa2 + math.pi * 0.65   # offset left of facing direction
                    e.item.x = ex + math.cos(_sw_ang) * (e.size + 10)
                    e.item.y = ey + math.sin(_sw_ang) * (e.size + 10)
                    e.item.angle = _sw_ang + math.pi / 2
                    e.item.draw(self.canvas)
                # Stone body — dark grey hexagon
                pts_sg = [
                    ex,           ey - e.size,
                    ex+e.size*0.87, ey-e.size*0.5,
                    ex+e.size*0.87, ey+e.size*0.5,
                    ex,           ey + e.size,
                    ex-e.size*0.87, ey+e.size*0.5,
                    ex-e.size*0.87, ey-e.size*0.5,
                ]
                self.canvas.create_polygon(pts_sg, fill='#556655', outline='#aaaaaa', width=3)
                # Cracks texture
                self.canvas.create_line(ex-4, ey-e.size+4, ex+2, ey, fill='#888', width=1)
                self.canvas.create_line(ex+3, ey+2, ex-3, ey+e.size-4, fill='#888', width=1)
                # Eye slit
                self.canvas.create_rectangle(ex-6, ey-3, ex+6, ey+1, fill='#ff4400', outline='')
                # Shield — rotates to face player, top-view /‾‾\ shape
                _sa = math.atan2(self.player.y-ey, self.player.x-ex)
                e._shield_angle = _sa  # store for collision use
                _sh_dist = e.size + 12
                _shx = ex + math.cos(_sa) * _sh_dist
                _shy = ey + math.sin(_sa) * _sh_dist
                _perp = _sa + math.pi/2
                _sw = 18   # shield half-width
                _sd = 8    # shield depth
                _shield_pts = [
                    _shx + math.cos(_perp)*_sw,  _shy + math.sin(_perp)*_sw,
                    _shx + math.cos(_perp)*_sw - math.cos(_sa)*_sd,
                    _shy + math.sin(_perp)*_sw - math.sin(_sa)*_sd,
                    _shx - math.cos(_perp)*_sw - math.cos(_sa)*_sd,
                    _shy - math.sin(_perp)*_sw - math.sin(_sa)*_sd,
                    _shx - math.cos(_perp)*_sw,  _shy - math.sin(_perp)*_sw,
                ]
                self.canvas.create_polygon(_shield_pts, fill='#8888aa', outline='#ccccff', width=2)
                self.canvas.create_line(
                    _shx - math.cos(_perp)*_sw*0.5, _shy - math.sin(_perp)*_sw*0.5,
                    _shx + math.cos(_perp)*_sw*0.5, _shy + math.sin(_perp)*_sw*0.5,
                    fill='#ccccff', width=2)
                # Name + HP
                self.canvas.create_text(ex, ey-e.size-14, text="Stone Guardian",
                                        fill='#aaaaaa', font=('Arial', 8, 'bold'))
                if _has_identify:
                    self.canvas.create_text(ex, ey-e.size-26, text=f"{int(e.hp)}/{int(e.max_hp)}",
                                            fill='white', font=('Arial', 7))
                    # Status effects — stacked so they never overlap
                    _sg_now = time.time(); _sg_ty = ey - e.size - 44
                    if hasattr(e, '_shocked_until') and e._shocked_until > _sg_now:
                        self.canvas.create_text(ex, _sg_ty, text='⚡ SHOCKED', fill='#ffff00', font=('Arial', 8, 'bold'))
                        _sg_ty -= 12
                    _sg_daze = max(getattr(e, '_smoke_until', 0), getattr(e, '_dazed_until', 0))
                    if _sg_daze > _sg_now:
                        self.canvas.create_text(ex, _sg_ty, text=f'💨 DAZED {_sg_daze-_sg_now:.1f}s', fill='#aaaaaa', font=('Arial', 8, 'bold'))
                        _sg_ty -= 12
                    if hasattr(e, '_poison_until') and e._poison_until > _sg_now:
                        _spt = getattr(e, '_poison_tier', 1); _stl = {1:'I',2:'II',3:'III'}.get(_spt,'I')
                        self.canvas.create_text(ex, _sg_ty, text=f'☠ POISON T{_stl} {e._poison_until-_sg_now:.1f}s', fill='#44ff44', font=('Arial', 8, 'bold'))
                        _sg_ty -= 12
                    if hasattr(e, '_wet_until') and e._wet_until > _sg_now:
                        _swt = getattr(e, '_wet_tier', 1)
                        self.canvas.create_text(ex, _sg_ty, text=f'💧 WET T{_swt} {e._wet_until-_sg_now:.1f}s', fill='#44ccff', font=('Arial', 8, 'bold'))
                continue
            if getattr(e, '_is_bomb', False):
                _now_b2 = time.time()
                hp_frac_b = e.hp / max(e.max_hp, 1)
                # Subtle pulsing glow (danger indicator only)
                _pulse_r = abs(math.sin(_now_b2 * (4.0 + (1.0 - hp_frac_b) * 8))) * 3
                glow_col = '#ff2200' if hp_frac_b < 0.4 else '#ff6600'
                self.canvas.create_oval(
                    ex - e.size - 3 - _pulse_r, ey - e.size - 3 - _pulse_r,
                    ex + e.size + 3 + _pulse_r, ey + e.size + 3 + _pulse_r,
                    fill='', outline=glow_col, width=1
                )
                # Black bomb body (compact)
                self.canvas.create_oval(
                    ex - e.size - 1, ey - e.size - 1,
                    ex + e.size + 1, ey + e.size + 1,
                    fill='#111111', outline='#333333', width=1
                )
                self.canvas.create_oval(
                    ex - e.size, ey - e.size,
                    ex + e.size, ey + e.size,
                    fill='#1c1c1c', outline='#444444', width=1
                )
                # Small sheen highlight
                self.canvas.create_oval(
                    ex - e.size * 0.5, ey - e.size * 0.65,
                    ex - e.size * 0.05, ey - e.size * 0.2,
                    fill='#4a4a4a', outline=''
                )
                # Fuse
                _fbx = ex + 2; _fby = ey - e.size
                _fex = _fbx + 4; _fey = _fby - 8
                _fmx = _fbx + 5; _fmy = _fby - 4
                self.canvas.create_line(_fbx, _fby, _fmx, _fmy, _fex, _fey,
                                        fill='#8B6914', width=2, smooth=True)
                _ember_col = random.choice(['#ff4400', '#ff8800', '#ffcc00', 'orange'])
                _esz = 2 + int(abs(math.sin(_now_b2 * 14)) * 2)
                self.canvas.create_oval(_fex-_esz, _fey-_esz, _fex+_esz, _fey+_esz,
                                        fill=_ember_col, outline='')
                self.canvas.create_oval(_fex-1, _fey-1, _fex+1, _fey+1,
                                        fill='white', outline='')
                # HP text only with Identify passive
                if 'Identify' in getattr(self.player, 'tree_unlocked', set()) and self.player.passive_toggles.get('Identify', True):
                    health_text_b = f"{int(e.hp)}/{int(e.max_hp)}"
                    self.canvas.create_text(ex, ey - e.size - 10,
                                            text=health_text_b, fill='white')
                    # Status effects — stacked so they never overlap
                    _nb = time.time(); _ty_b = ey - e.size - 28
                    if hasattr(e, '_shocked_until') and e._shocked_until > _nb:
                        self.canvas.create_text(ex, _ty_b, text='⚡ SHOCKED', fill='#ffff00', font=('Arial', 8, 'bold'))
                        _ty_b -= 12
                    _bd = max(getattr(e, '_smoke_until', 0), getattr(e, '_dazed_until', 0))
                    if _bd > _nb:
                        self.canvas.create_text(ex, _ty_b, text=f'💨 DAZED {_bd-_nb:.1f}s', fill='#aaaaaa', font=('Arial', 8, 'bold'))
                        _ty_b -= 12
                    if hasattr(e, '_poison_until') and e._poison_until > _nb:
                        _bpt = getattr(e, '_poison_tier', 1); _btl = {1:'I',2:'II',3:'III'}.get(_bpt,'I')
                        self.canvas.create_text(ex, _ty_b, text=f'☠ POISON T{_btl} {e._poison_until-_nb:.1f}s', fill='#44ff44', font=('Arial', 8, 'bold'))
                        _ty_b -= 12
                    if hasattr(e, '_wet_until') and e._wet_until > _nb:
                        _bwt = getattr(e, '_wet_tier', 1)
                        self.canvas.create_text(ex, _ty_b, text=f'💧 WET T{_bwt} {e._wet_until-_nb:.1f}s', fill='#44ccff', font=('Arial', 8, 'bold'))
                continue   # skip generic enemy draw

            # ── IGNISMANCER — volcanic elemental boss-guardian ────────────────
            if getattr(e, '_is_ignismancer', False):
                _now_ig = time.time()
                _ig_sz = e.size
                hp_frac_ig = e.hp / max(e.max_hp, 1)
                # Lava glow ring
                _ig_pulse = abs(math.sin(_now_ig * 3)) * 5
                self.canvas.create_oval(
                    ex - _ig_sz - 8 - _ig_pulse, ey - _ig_sz - 8 - _ig_pulse,
                    ex + _ig_sz + 8 + _ig_pulse, ey + _ig_sz + 8 + _ig_pulse,
                    fill='', outline='#ff4400', width=2
                )
                # Dark volcanic body
                self.canvas.create_oval(
                    ex - _ig_sz - 2, ey - _ig_sz - 2,
                    ex + _ig_sz + 2, ey + _ig_sz + 2,
                    fill='#330800', outline='#cc3300', width=3
                )
                self.canvas.create_oval(
                    ex - _ig_sz, ey - _ig_sz,
                    ex + _ig_sz, ey + _ig_sz,
                    fill='#551100', outline=''
                )
                # Lava cracks (animated glow)
                for _ic in range(5):
                    _ica = (_now_ig * 0.8 + _ic * 1.26) % (2 * math.pi)
                    _icr1 = _ig_sz * 0.3; _icr2 = _ig_sz * 0.85
                    _icx1 = ex + math.cos(_ica) * _icr1
                    _icy1 = ey + math.sin(_ica) * _icr1
                    _icx2 = ex + math.cos(_ica) * _icr2
                    _icy2 = ey + math.sin(_ica) * _icr2
                    _icc  = random.choice(['#ff4500','#ff6600','#ff8800','#cc2200'])
                    self.canvas.create_line(_icx1, _icy1, _icx2, _icy2,
                                            fill=_icc, width=2)
                # Bright lava core
                _icore = _ig_sz * 0.4
                self.canvas.create_oval(
                    ex - _icore, ey - _icore, ex + _icore, ey + _icore,
                    fill='#ff8800', outline=''
                )
                self.canvas.create_oval(
                    ex - _icore*0.45, ey - _icore*0.45,
                    ex + _icore*0.45, ey + _icore*0.45,
                    fill='#ffee00', outline=''
                )
                # Name label always visible
                self.canvas.create_text(ex, ey - _ig_sz - 20,
                                        text="Ignismancer",
                                        fill='#ff8800', font=('Arial', 9, 'bold'))
                # Numeric HP — only when Identify passive is active (no bar)
                if ('Identify' in getattr(self.player, 'tree_unlocked', set())
                        and self.player.passive_toggles.get('Identify', True)):
                    self.canvas.create_text(
                        ex, ey - _ig_sz - 32,
                        text=f'HP  {int(e.hp):,} / {int(e.max_hp):,}',
                        fill='#ffcc88', font=('Arial', 8, 'bold'))
                # Lava staff (always visible)
                _sa = math.atan2(self.player.y - ey, self.player.x - ex)
                _staff_item = Item(ex, ey, 'staff', '#ff4400', 14)
                _staff_item.angle = _sa
                _staff_item.draw(self.canvas)
                # Status effects — stacked so they never overlap
                if ('Identify' in getattr(self.player, 'tree_unlocked', set())
                        and self.player.passive_toggles.get('Identify', True)):
                    _ig_now2 = time.time(); _ig_ty = ey - _ig_sz - 55
                    if hasattr(e, '_shocked_until') and e._shocked_until > _ig_now2:
                        self.canvas.create_text(ex, _ig_ty, text='⚡ SHOCKED', fill='#ffff00', font=('Arial', 8, 'bold'))
                        _ig_ty -= 12
                    _ig_daze = max(getattr(e, '_smoke_until', 0), getattr(e, '_dazed_until', 0))
                    if _ig_daze > _ig_now2:
                        self.canvas.create_text(ex, _ig_ty, text=f'💨 DAZED {_ig_daze-_ig_now2:.1f}s', fill='#aaaaaa', font=('Arial', 8, 'bold'))
                        _ig_ty -= 12
                    if hasattr(e, '_poison_until') and e._poison_until > _ig_now2:
                        _ipt = getattr(e, '_poison_tier', 1); _itl = {1:'I',2:'II',3:'III'}.get(_ipt,'I')
                        self.canvas.create_text(ex, _ig_ty, text=f'☠ POISON T{_itl} {e._poison_until-_ig_now2:.1f}s', fill='#44ff44', font=('Arial', 8, 'bold'))
                        _ig_ty -= 12
                    if hasattr(e, '_wet_until') and e._wet_until > _ig_now2:
                        _igwt = getattr(e, '_wet_tier', 1)
                        self.canvas.create_text(ex, _ig_ty, text=f'💧 WET T{_igwt} {e._wet_until-_ig_now2:.1f}s', fill='#44ccff', font=('Arial', 8, 'bold'))
                continue   # skip generic enemy draw

            if _has_identify:
                health_text = f"{int(e.hp)}/{int(e.max_hp)}"
                self.canvas.create_text(ex, ey - e.size - 10, text=health_text, fill='white')
            # ── Flame Elemental custom draw ───────────────────────────────────
            if e.name == "Flame Elemental":
                _now_fe = time.time()
                _fe_hp  = e.hp / max(e.max_hp, 1)
                _fe_r   = e.size
                # Outer slow pulsing glow ring
                _fe_glow = 3 + abs(math.sin(_now_fe * 2.5)) * 5
                self.canvas.create_oval(
                    ex-_fe_r-_fe_glow, ey-_fe_r-_fe_glow,
                    ex+_fe_r+_fe_glow, ey+_fe_r+_fe_glow,
                    fill='', outline='#ff6600', width=2)
                # Core body — orange/red/yellow layered circles (no particles, no lag)
                self.canvas.create_oval(ex-_fe_r, ey-_fe_r, ex+_fe_r, ey+_fe_r,
                                        fill='#cc2200', outline='')
                self.canvas.create_oval(ex-_fe_r*0.72, ey-_fe_r*0.72,
                                        ex+_fe_r*0.72, ey+_fe_r*0.72,
                                        fill='#ff4400', outline='')
                self.canvas.create_oval(ex-_fe_r*0.45, ey-_fe_r*0.45,
                                        ex+_fe_r*0.45, ey+_fe_r*0.45,
                                        fill='#ff8800', outline='')
                self.canvas.create_oval(ex-_fe_r*0.22, ey-_fe_r*0.22,
                                        ex+_fe_r*0.22, ey+_fe_r*0.22,
                                        fill='#ffcc00', outline='')
                # Flame tongues — 5 spikes radiating outward, animated via time
                _nf = 5
                for _fi in range(_nf):
                    _fa = (_now_fe * 1.8 + _fi * (2*math.pi/_nf))
                    _flen = _fe_r * (1.35 + 0.3 * abs(math.sin(_now_fe*3.1 + _fi*1.3)))
                    _fw   = _fe_r * 0.28
                    _ftx  = ex + math.cos(_fa) * _flen
                    _fty  = ey + math.sin(_fa) * _flen
                    _fla  = _fa + math.pi/2
                    _f_pts = [
                        ex + math.cos(_fa)*_fe_r*0.7 + math.cos(_fla)*_fw*0.5,
                        ey + math.sin(_fa)*_fe_r*0.7 + math.sin(_fla)*_fw*0.5,
                        _ftx, _fty,
                        ex + math.cos(_fa)*_fe_r*0.7 - math.cos(_fla)*_fw*0.5,
                        ey + math.sin(_fa)*_fe_r*0.7 - math.sin(_fla)*_fw*0.5,
                    ]
                    _fc = random.choice(['#ff4400','#ff6600','#ff8800','#ffaa00'])
                    self.canvas.create_polygon(_f_pts, fill=_fc, outline='')
                # Eyes — two white/yellow dots
                _ea = math.atan2(self.player.y-ey, self.player.x-ex)
                _eperp = _ea + math.pi/2
                for _es in [-0.35, 0.35]:
                    _ex2 = ex + math.cos(_ea)*_fe_r*0.35 + math.cos(_eperp)*_fe_r*_es
                    _ey2 = ey + math.sin(_ea)*_fe_r*0.35 + math.sin(_eperp)*_fe_r*_es
                    self.canvas.create_oval(_ex2-3, _ey2-3, _ex2+3, _ey2+3,
                                            fill='#ffff88', outline='')
                    self.canvas.create_oval(_ex2-1, _ey2-1, _ex2+1, _ey2+1,
                                            fill='white', outline='')
                # HP text
                if 'Identify' in getattr(self.player, 'tree_unlocked', set()) and self.player.passive_toggles.get('Identify', True):
                    self.canvas.create_text(ex, ey-_fe_r-10,
                        text=f"{int(e.hp)}/{int(e.max_hp)}", fill='white')
                    # Status effects
                    _fe_now2 = time.time(); _fe_ty = ey - _fe_r - 28
                    _fe_daze = max(getattr(e, '_smoke_until', 0), getattr(e, '_dazed_until', 0))
                    if _fe_daze > _fe_now2:
                        self.canvas.create_text(ex, _fe_ty, text=f'💨 DAZED {_fe_daze-_fe_now2:.1f}s', fill='#aaaaaa', font=('Arial', 8, 'bold'))
                        _fe_ty -= 12
                    if hasattr(e, '_poison_until') and e._poison_until > _fe_now2:
                        _fpt = getattr(e, '_poison_tier', 1); _ftl = {1:'I',2:'II',3:'III'}.get(_fpt,'I')
                        self.canvas.create_text(ex, _fe_ty, text=f'☠ POISON T{_ftl} {e._poison_until-_fe_now2:.1f}s', fill='#44ff44', font=('Arial', 8, 'bold'))
                        _fe_ty -= 12
                    if hasattr(e, '_wet_until') and e._wet_until > _fe_now2:
                        _fewt = getattr(e, '_wet_tier', 1)
                        self.canvas.create_text(ex, _fe_ty, text=f'💧 WET T{_fewt} {e._wet_until-_fe_now2:.1f}s', fill='#44ccff', font=('Arial', 8, 'bold'))
                continue

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

            # Health text — only visible with Identify passive (when toggled on)
            _has_identify = ('Identify' in getattr(self.player, 'tree_unlocked', set())
                             and self.player.passive_toggles.get('Identify', True))
            if _has_identify:
                health_text = f"{int(e.hp)}/{int(e.max_hp)}"
                self.canvas.create_text(ex, ey - e.size - 10, text=health_text, fill='white')

            # ── Shocked: yellow glow + shake ─────────────────────────────────
            if hasattr(e, '_shocked_until') and e._shocked_until > time.time():
                _ss = e.size + 10
                # Yellow electric glow rings
                for _ring in range(2):
                    _ro = _ring * 5
                    self.canvas.create_oval(
                        ex - _ss - _ro, ey - _ss - _ro,
                        ex + _ss + _ro, ey + _ss + _ro,
                        fill='', outline='#ffff00', width=2, stipple='gray50'
                    )
                self.canvas.create_oval(
                    ex - _ss + 2, ey - _ss + 2,
                    ex + _ss - 2, ey + _ss - 2,
                    fill='#ffff44', outline='', stipple='gray25'
                )

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
                # Countdown timer — only visible with Identify
                if _has_identify:
                    self.canvas.create_text(ex, ey - _hs - 6,
                                            text=f"❄ {remaining_freeze:.1f}s",
                                            fill='#00eeff', font=('Arial', 8, 'bold'))



            # ── Status text stack: shocked / dazed / poison — never overlap ────
            if _has_identify:
                _now_gst = time.time()
                _sy = ey - e.size - 22   # first slot: just above HP text
                if hasattr(e, '_shocked_until') and e._shocked_until > _now_gst:
                    self.canvas.create_text(ex, _sy, text='⚡ SHOCKED',
                                            fill='#ffff00', font=('Arial', 8, 'bold'))
                    _sy -= 12
                _daze_until = max(getattr(e, '_smoke_until', 0), getattr(e, '_dazed_until', 0))
                if _daze_until > _now_gst:
                    self.canvas.create_text(ex, _sy, text=f'💨 DAZED {_daze_until - _now_gst:.1f}s',
                                            fill='#aaaaaa', font=('Arial', 8, 'bold'))
                    _sy -= 12
                if hasattr(e, '_poison_until') and e._poison_until > _now_gst:
                    _pt    = e._poison_until - _now_gst
                    _ptier = getattr(e, '_poison_tier', 1)
                    _tlbl  = {1: 'I', 2: 'II', 3: 'III'}.get(_ptier, 'I')
                    self.canvas.create_text(ex, _sy, text=f'☠ POISON T{_tlbl} {_pt:.1f}s',
                                            fill='#44ff44', font=('Arial', 8, 'bold'))
                    _sy -= 12
                if hasattr(e, '_wet_until') and e._wet_until > _now_gst:
                    _wt_rem = e._wet_until - _now_gst
                    _wt_t   = getattr(e, '_wet_tier', 1)
                    self.canvas.create_text(ex, _sy, text=f'💧 WET T{_wt_t} {_wt_rem:.1f}s',
                                            fill='#44ccff', font=('Arial', 8, 'bold'))
                    _sy -= 12

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

        # ── Treasure room chest ──────────────────────────────────────────────
        if getattr(self.room, '_is_treasure_room', False):
            for deco in list(self.room.decorations):
                if deco.get('type') == 'treasure_chest':
                    cx, cy = deco['x'], deco['y']
                    # Draw chest
                    self.canvas.create_rectangle(cx-28, cy-16, cx+28, cy+18,
                                                 fill='#7a4a18', outline='#FFD700', width=3)
                    self.canvas.create_rectangle(cx-28, cy-16, cx+28, cy-2,
                                                 fill='#8B5e20', outline='#FFD700', width=2)
                    # Lock
                    self.canvas.create_oval(cx-6, cy-10, cx+6, cy+2,
                                            fill='#FFD700', outline='#B8860B', width=2)
                    self.canvas.create_rectangle(cx-4, cy-3, cx+4, cy+5,
                                                 fill='#FFD700', outline='#B8860B')
                    # Glow
                    _pulse = abs(math.sin(time.time() * 2.5)) * 6
                    self.canvas.create_oval(cx-34-_pulse, cy-22-_pulse,
                                            cx+34+_pulse, cy+24+_pulse,
                                            fill='', outline='#FFD700',
                                            width=2, stipple='gray50')
                    # Prompt + open
                    d_chest = distance((self.player.x, self.player.y), (cx, cy))
                    if d_chest < 80:
                        self.canvas.create_text(cx, cy - 36, text='F — Open Chest',
                                                fill='#FFD700', font=('Arial', 11, 'bold'))
                        if self.keys.get('f') or self.keys.get('e'):
                            self.keys['f'] = False; self.keys['e'] = False
                            # Remove chest from room so it disappears
                            self.room.decorations.remove(deco)
                            # Spray coin particles
                            coins_total = deco.get('coins', 800)
                            num_coins   = 20
                            val_each    = coins_total // num_coins
                            for _ in range(num_coins):
                                self.coin_particles.append(CoinParticle(cx, cy, val_each))
                            # Spawn weapon particle for each item
                            for it in deco.get('items', []):
                                self.weapon_particles.append(WeaponParticle(cx, cy, it))

            # Room flavour text
            self.canvas.create_text(WINDOW_W//2, 36,
                                    text="⚔  Warden's Vault  ⚔",
                                    fill='#FFD700', font=('Arial', 13, 'bold'))

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



        # ── Draw Analysis floating info above enemies ─────────────────────────
        if hasattr(self, '_analysis_displays'):
            now_a = time.time()
            self._analysis_displays = [d for d in self._analysis_displays if d['until'] > now_a]
            for disp in self._analysis_displays:
                tgt = disp['target']
                if not hasattr(tgt, 'x'):
                    continue
                tx, ty = tgt.x, tgt.y
                tsz = getattr(tgt, 'size', 16)
                fade = min(1.0, (disp['until'] - now_a) / 0.8)
                # Background panel
                max_w = max(len(ln) for ln in disp['lines']) * 6 + 16
                panel_h = len(disp['lines']) * 16 + 10
                px0 = tx - max_w // 2
                py0 = ty - tsz - panel_h - 42
                self.canvas.create_rectangle(px0 - 4, py0 - 4, px0 + max_w + 4, py0 + panel_h + 4,
                                             fill='#0a0a1a', outline='#3355aa', width=1)
                colors = ['#ffdd88', '#aaddff', '#88ccff']
                for i, line in enumerate(disp['lines']):
                    self.canvas.create_text(tx, py0 + 8 + i * 16, text=line,
                                            fill=colors[min(i, len(colors)-1)],
                                            font=('Arial', 8, 'bold' if i == 0 else 'normal'))
                # Arrow pointing to enemy
                self.canvas.create_line(tx, py0 + panel_h + 4, tx, ty - tsz - 2,
                                        fill='#3355aa', width=1, dash=(3, 3))

        # ── Draw lava pools (below everything else) ──────────────────────────
        if hasattr(self, 'lava_pools'):
            for _lp in self.lava_pools:
                _lp.draw(self.canvas)

        for proj in self.projectiles:
            x, y, r = proj.x, proj.y, proj.radius
            # Lava spray — tight hose droplets with short trail
            if proj.stype == 'lava_proj':
                trail_len = r * 2.2
                tx1 = x - math.cos(proj.angle) * trail_len
                ty1 = y - math.sin(proj.angle) * trail_len
                self.canvas.create_line(tx1, ty1, x, y,
                                        fill='#551100', width=max(2, int(r * 1.1)))
                self.canvas.create_line(tx1, ty1, x, y,
                                        fill='#ff4500', width=max(1, int(r * 0.6)))
                self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                        fill='#ff4500', outline='')
                self.canvas.create_oval(x - r*0.5, y - r*0.5,
                                        x + r*0.5, y + r*0.5,
                                        fill='#ffcc44', outline='')
                continue
            # Lava wave — solid glowing wall segment (tsunami style)
            if proj.stype == 'lava_wave':
                perp = proj.angle + math.pi / 2
                hw   = r * 1.9
                fd   = r * 0.55
                pts  = [
                    x + math.cos(perp)*hw + math.cos(proj.angle)*fd,
                    y + math.sin(perp)*hw + math.sin(proj.angle)*fd,
                    x - math.cos(perp)*hw + math.cos(proj.angle)*fd,
                    y - math.sin(perp)*hw + math.sin(proj.angle)*fd,
                    x - math.cos(perp)*hw - math.cos(proj.angle)*fd,
                    y - math.sin(perp)*hw - math.sin(proj.angle)*fd,
                    x + math.cos(perp)*hw - math.cos(proj.angle)*fd,
                    y + math.sin(perp)*hw - math.sin(proj.angle)*fd,
                ]
                self.canvas.create_polygon(pts, fill='#881100', outline='')
                hw2  = hw * 0.62
                pts2 = [
                    x + math.cos(perp)*hw2 + math.cos(proj.angle)*fd*0.55,
                    y + math.sin(perp)*hw2 + math.sin(proj.angle)*fd*0.55,
                    x - math.cos(perp)*hw2 + math.cos(proj.angle)*fd*0.55,
                    y - math.sin(perp)*hw2 + math.sin(proj.angle)*fd*0.55,
                    x - math.cos(perp)*hw2 - math.cos(proj.angle)*fd*0.55,
                    y - math.sin(perp)*hw2 - math.sin(proj.angle)*fd*0.55,
                    x + math.cos(perp)*hw2 - math.cos(proj.angle)*fd*0.55,
                    y + math.sin(perp)*hw2 - math.sin(proj.angle)*fd*0.55,
                ]
                self.canvas.create_polygon(pts2, fill='#ff4500', outline='')
                self.canvas.create_oval(x - r*0.45, y - r*0.45,
                                        x + r*0.45, y + r*0.45,
                                        fill='#ffcc00', outline='')
                continue
            # Magma bomb — larger glowing molten orb with dark crust
            if proj.stype == 'magma_bomb':
                self.canvas.create_oval(x-r*1.1, y-r*1.1, x+r*1.1, y+r*1.1,
                                        fill='#551100', outline='#cc3300', width=2)
                self.canvas.create_oval(x-r*0.75, y-r*0.75, x+r*0.75, y+r*0.75,
                                        fill='#cc4400', outline='')
                self.canvas.create_oval(x-r*0.4, y-r*0.4, x+r*0.4, y+r*0.4,
                                        fill='#ff8800', outline='')
                self.canvas.create_oval(x-r*0.18, y-r*0.18, x+r*0.18, y+r*0.18,
                                        fill='#ffee00', outline='')
                continue
            # Ignis meteor — fire_proj style flame cluster with a rock core
            if proj.ptype == 'ignis_meteor':
                _fire_colors = ['#ff2200','#ff4400','#ff6600','#ff8800','#ffaa00','orange','yellow']
                # Larger flame cluster (like fire_proj but bigger radius)
                for _fi in range(10):
                    _fa  = proj.angle + random.uniform(-0.8, 0.8)
                    _fd  = random.uniform(0, r * 1.5)
                    _fx  = x + math.cos(_fa)*_fd
                    _fy  = y + math.sin(_fa)*_fd
                    _fr  = random.uniform(r*0.4, r*0.9)
                    self.canvas.create_oval(_fx-_fr, _fy-_fr, _fx+_fr, _fy+_fr,
                                            fill=random.choice(_fire_colors), outline='')
                # Small dark rock core on top
                _cr = r * 0.55
                self.canvas.create_oval(x-_cr, y-_cr, x+_cr, y+_cr,
                                        fill='#5c2800', outline='#8B4513', width=1)
                # Glowing cracks on the rock
                _now_m = time.time()
                for _mc in range(3):
                    _mca = _now_m*2.0 + _mc*2.094
                    self.canvas.create_line(
                        x+math.cos(_mca)*_cr*0.2, y+math.sin(_mca)*_cr*0.2,
                        x+math.cos(_mca)*_cr*0.85, y+math.sin(_mca)*_cr*0.85,
                        fill='#ff8800', width=1)
                # Bright core centre
                self.canvas.create_oval(x-r*0.18, y-r*0.18, x+r*0.18, y+r*0.18,
                                        fill='white', outline='')
                continue
            # Fire projectile — drawn as a cluster of flame particles (no solid shape)
            if proj.stype == 'fire_proj' and proj.ptype != 'ignis_meteor':
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

            # ── Holyflame: same structure as fire_proj, yellow/white palette ──
            elif proj.stype == 'hf_proj':
                _hf_colors = ['#ffdd00', '#ffee55', '#ffcc00', '#ffffff', '#ffff88']
                for _fi in range(6):
                    _fa = proj.angle + random.uniform(-0.7, 0.7)
                    _fd = random.uniform(0, r * 1.2)
                    _fx = x + math.cos(_fa)*_fd
                    _fy = y + math.sin(_fa)*_fd
                    _fr = random.uniform(r*0.25, r*0.65)
                    self.canvas.create_oval(_fx-_fr, _fy-_fr, _fx+_fr, _fy+_fr,
                                            fill=random.choice(_hf_colors), outline='')
                self.canvas.create_oval(x-r*0.45, y-r*0.45, x+r*0.45, y+r*0.45,
                                        fill='#ffee00', outline='')

            # ── Blackflame: same structure as fire_proj, magenta/purple palette ─
            elif proj.stype == 'bf_proj':
                _bf_colors = ['#cc00ff', '#880099', '#ff00cc', '#550077', '#ff44ff']
                for _fi in range(6):
                    _fa = proj.angle + random.uniform(-0.7, 0.7)
                    _fd = random.uniform(0, r * 1.2)
                    _fx = x + math.cos(_fa)*_fd
                    _fy = y + math.sin(_fa)*_fd
                    _fr = random.uniform(r*0.25, r*0.65)
                    self.canvas.create_oval(_fx-_fr, _fy-_fr, _fx+_fr, _fy+_fr,
                                            fill=random.choice(_bf_colors), outline='')
                self.canvas.create_oval(x-r*0.45, y-r*0.45, x+r*0.45, y+r*0.45,
                                        fill='#cc00ff', outline='')
            elif proj.stype == 'hydro_shot':
                # Same teardrop as aqua_missile but larger trail (6 dots)
                _ang = getattr(proj, '_travel_angle', proj.angle)
                # Trail: 6 water dots fading behind the projectile
                for _ti in range(1, 7):
                    _td = _ti * 7
                    _tx = x - math.cos(_ang) * _td + random.uniform(-3, 3)
                    _ty = y - math.sin(_ang) * _td + random.uniform(-3, 3)
                    _tr = max(1, r * 0.55 * (1 - _ti * 0.13))
                    _tcol = random.choice(['#44aaff', '#00ccff', '#99ddff', '#aaeeff'])
                    self.canvas.create_oval(_tx - _tr, _ty - _tr, _tx + _tr, _ty + _tr,
                                            fill=_tcol, outline='')
                # Teardrop body — same geometry as aqua_missile
                _pts = []
                for _i in range(12):
                    _a = _i * (2*math.pi/12)
                    _lx = math.cos(_a) * r * 0.8
                    _ly = math.sin(_a) * r * 1.4
                    _rx2 = _lx*math.cos(_ang) - _ly*math.sin(_ang)
                    _ry2 = _lx*math.sin(_ang) + _ly*math.cos(_ang)
                    _pts += [x+_rx2, y+_ry2]
                self.canvas.create_polygon(_pts, fill='#0077cc', outline='#00ccff', width=1)
                self.canvas.create_oval(x-r*0.4, y-r*0.4, x+r*0.4, y+r*0.4,
                                        fill='#aaeeff', outline='')
            elif proj.stype == 'firebolt':
                # Tight flame cluster centred on the bolt tip — no sprawling trail
                _ang = proj.angle
                _fc = ['#ff2200','#ff6600','#ffaa00','orange','yellow']
                _tip_r = proj.radius * 1.2   # radius of head cluster
                # Head glow
                self.canvas.create_oval(x - _tip_r - 2, y - _tip_r - 2,
                                        x + _tip_r + 2, y + _tip_r + 2,
                                        fill='#ff4400', outline='')
                # Dense flame dots packed around the tip
                for _ in range(8):
                    _ox = random.uniform(-_tip_r, _tip_r)
                    _oy = random.uniform(-_tip_r, _tip_r)
                    _r2 = random.uniform(1.5, 3.5)
                    self.canvas.create_oval(x+_ox-_r2, y+_oy-_r2,
                                            x+_ox+_r2, y+_oy+_r2,
                                            fill=random.choice(_fc), outline='')
                # Bright white core
                self.canvas.create_oval(x-2, y-2, x+2, y+2, fill='white', outline='')
            elif proj.stype == 'icebolt':
                # Tight frost cluster centred on the bolt tip — no sprawling trail
                _ang = proj.angle
                _ic = ['#00ccff','cyan','#aaffff','#88eeff','white']
                _tip_r = proj.radius * 1.2
                # Head glow
                self.canvas.create_oval(x - _tip_r - 2, y - _tip_r - 2,
                                        x + _tip_r + 2, y + _tip_r + 2,
                                        fill='#00aacc', outline='')
                # Dense frost dots packed around the tip
                for _ in range(8):
                    _ox = random.uniform(-_tip_r, _tip_r)
                    _oy = random.uniform(-_tip_r, _tip_r)
                    _r2 = random.uniform(1.5, 3.5)
                    self.canvas.create_oval(x+_ox-_r2, y+_oy-_r2,
                                            x+_ox+_r2, y+_oy+_r2,
                                            fill=random.choice(_ic), outline='')
                # Bright white core
                self.canvas.create_oval(x-2, y-2, x+2, y+2, fill='white', outline='')
            elif proj.stype == 'aqua_missile':
                # Teardrop: elongated body + pointed tail
                _ang = proj.angle
                _perp = _ang + math.pi / 2
                _pts = []
                for _i in range(12):
                    _a = _i * (2*math.pi/12)
                    _lx = math.cos(_a) * r * 0.8
                    _ly = math.sin(_a) * r * 1.4
                    _rx2 = _lx*math.cos(_ang) - _ly*math.sin(_ang)
                    _ry2 = _lx*math.sin(_ang) + _ly*math.cos(_ang)
                    _pts += [x+_rx2, y+_ry2]
                self.canvas.create_polygon(_pts, fill='#0077cc', outline='#00ccff', width=1)
                self.canvas.create_oval(x-r*0.4, y-r*0.4, x+r*0.4, y+r*0.4,
                                        fill='#aaeeff', outline='')
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
                leaf_length = r * 3.8
                leaf_width  = r * 2.0
                stem_length = r * 1.0
                stem_width  = r * 0.28

                # Each leaf spins slightly as it travels for a tumbling feel
                spin = (time.time() * 4.5 + id(proj) * 0.7) % (2 * math.pi)
                draw_ang = proj.angle + math.sin(spin) * 0.35

                cos_a = math.cos(draw_ang)
                sin_a = math.sin(draw_ang)

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
                self.canvas.create_polygon(stem_points, fill='#5D4037')

                # --- LEAF BODY (pointed teardrop) ---
                lc = x + cos_a * (leaf_length * 0.12)
                ly_c = y + sin_a * (leaf_length * 0.12)
                tip_x = lc + cos_a * (leaf_length / 2)
                tip_y = ly_c + sin_a * (leaf_length / 2)
                base_x = lc - cos_a * (leaf_length / 2)
                base_y = ly_c - sin_a * (leaf_length / 2)
                dx = sin_a * (leaf_width / 2)
                dy = -cos_a * (leaf_width / 2)

                # Rounded widest point at ~40% from base
                mid_x = base_x + cos_a * leaf_length * 0.40
                mid_y = base_y + sin_a * leaf_length * 0.40

                leaf_points = [
                    base_x, base_y,
                    base_x + dx * 0.5, base_y + dy * 0.5,
                    mid_x + dx, mid_y + dy,
                    tip_x, tip_y,
                    mid_x - dx, mid_y - dy,
                    base_x - dx * 0.5, base_y - dy * 0.5,
                ]
                self.canvas.create_polygon(leaf_points, fill=proj.color, smooth=True)

                # --- MIDRIB VEIN ---
                self.canvas.create_line(
                    base_x, base_y, tip_x, tip_y,
                    fill='#ffffff', width=1, stipple='gray25'
                )

                # --- HIGHLIGHT (white edge stipple for sheen) ---
                h_offset = 0.30
                hl_x1 = base_x + cos_a * leaf_length * 0.15 + dx * h_offset
                hl_y1 = base_y + sin_a * leaf_length * 0.15 + dy * h_offset
                hl_x2 = mid_x + dx * 0.75
                hl_y2 = mid_y + dy * 0.75
                self.canvas.create_line(
                    hl_x1, hl_y1, hl_x2, hl_y2,
                    fill='#ffffff', width=1, stipple='gray50'
                )


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
                # Use _visual_angle for display if set (rapid-swing random rotation)
                angle = getattr(proj, '_visual_angle', proj.angle)
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

            elif proj.stype == 'greatsword_proj':
                # Flying greatsword — matches draw_greatsword (rectangular blade + tip)
                _a  = proj.angle
                _ca = math.cos(_a);  _sa = math.sin(_a)
                _pa = math.cos(_a + math.pi/2);  _ps = math.sin(_a + math.pi/2)
                _sz = r * 0.9
                # Anchor = crossguard, offset forward slightly from projectile centre
                _ox = x + _ca * _sz * 0.8;  _oy = y + _sa * _sz * 0.8
                _gx = _ox + _ca * 4;          _gy = _oy + _sa * 4
                # Dimensions (proportional to draw_greatsword)
                _hl = _sz * 1.4;  _bl = _sz * 3.8
                _bw = _sz * 0.35; _tl = _sz * 0.75; _gl = _sz * 1.6
                # Points
                _pom_x = _ox - _ca*(_hl+6);  _pom_y = _oy - _sa*(_hl+6)
                _end_x = _gx + _ca*_bl;       _end_y = _gy + _sa*_bl
                _tip_x = _end_x + _ca*_tl;   _tip_y = _end_y + _sa*_tl
                _r1x=_gx+_pa*_bw;    _r1y=_gy+_ps*_bw
                _r2x=_gx-_pa*_bw;    _r2y=_gy-_ps*_bw
                _r3x=_end_x-_pa*_bw;    _r3y=_end_y-_ps*_bw
                _r4x=_end_x+_pa*_bw;    _r4y=_end_y+_ps*_bw
                # Handle
                self.canvas.create_line(_pom_x+1,_pom_y+1,_gx+1,_gy+1,fill='#110800',width=9)
                self.canvas.create_line(_pom_x,_pom_y,_gx,_gy,fill='#2e1505',width=7)
                for _i in range(4):
                    _t=(_i+1)/5
                    _wx=_pom_x+(_gx-_pom_x)*_t; _wy=_pom_y+(_gy-_pom_y)*_t
                    self.canvas.create_line(_wx-_pa*4,_wy-_ps*4,_wx+_pa*4,_wy+_ps*4,fill='#6b3010',width=2)
                self.canvas.create_oval(_pom_x-5,_pom_y-5,_pom_x+5,_pom_y+5,fill='#666',outline='#333',width=2)
                # Crossguard
                _g1x=_gx+_pa*_gl; _g1y=_gy+_ps*_gl
                _g2x=_gx-_pa*_gl; _g2y=_gy-_ps*_gl
                self.canvas.create_line(_g1x+1,_g1y+1,_g2x+1,_g2y+1,fill='#222',width=8)
                self.canvas.create_line(_g1x,_g1y,_g2x,_g2y,fill='#777',width=6)
                self.canvas.create_line(_g1x,_g1y,_g2x,_g2y,fill='#ccc',width=2)
                # Blade rectangle
                self.canvas.create_polygon([_r1x,_r1y,_r4x,_r4y,_r3x,_r3y,_r2x,_r2y],
                                           fill='#6e6e6e',outline='#2a2a2a',width=2)
                # Centre highlight
                _hx0=_gx+_pa*_bw*0.2; _hy0=_gy+_ps*_bw*0.2
                _hx1=_end_x+_pa*_bw*0.2; _hy1=_end_y+_ps*_bw*0.2
                self.canvas.create_line(_hx0,_hy0,_hx1,_hy1,fill='#c0c0c0',width=2)
                self.canvas.create_line(_hx0,_hy0,_hx1,_hy1,fill='white',width=1)
                # Pointed tip
                self.canvas.create_polygon([_r4x,_r4y,_tip_x,_tip_y,_r3x,_r3y],
                                           fill='#8a8a8a',outline='#2a2a2a',width=1)
                self.canvas.create_line(_r4x,_r4y,_tip_x,_tip_y,fill='white',width=1)

            elif proj.stype == 'bolt1':
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
            # Icicle — sharp frosty shard with shimmering trail
            # Icicle — small, thin diamond-shaped shard
            # Icicle — tiny, thin diamond shard (no trail)
            if proj.stype == 'icicle':
                # Very small proportions
                length = r * 1.4       # short spike
                width  = r * 0.28      # very thin

                # Tip of the icicle
                tip_x = x + math.cos(proj.angle) * length
                tip_y = y + math.sin(proj.angle) * length

                # Perpendicular for width
                perp = proj.angle + math.pi / 2

                # Diamond shape (front tip → upper → back → lower)
                pts = [
                    tip_x, tip_y,  # front tip
                    x + math.cos(perp)*width, y + math.sin(perp)*width,  # upper edge
                    x - math.cos(proj.angle)*(length * 0.45),
                    y - math.sin(proj.angle)*(length * 0.45),            # back point
                    x - math.cos(perp)*width, y - math.sin(perp)*width   # lower edge
                ]

                # Outer icy shell
                self.canvas.create_polygon(pts, fill='#b7e9ff', outline='')

                # Inner tiny bright core
                core_pts = [
                    tip_x, tip_y,
                    x + math.cos(perp)*width*0.45, y + math.sin(perp)*width*0.45,
                    x - math.cos(proj.angle)*(length * 0.25),
                    y - math.sin(proj.angle)*(length * 0.25),
                    x - math.cos(perp)*width*0.45, y - math.sin(perp)*width*0.45
                ]
                self.canvas.create_polygon(core_pts, fill='#e9fbff', outline='')

                continue



        for part in self.particles:
            if part.rtype == "aura_behind":
                continue   # drawn before player body in pre-player sections above
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
            elif part.rtype == "holy_flame":
                # Teardrop shape like flame but with white/gold inner glow
                r = part.size
                tip_x, tip_y = part.x, part.y - r * 1.5
                self.canvas.create_polygon(
                    part.x - r, part.y, part.x + r, part.y, tip_x, tip_y,
                    fill=part.color, outline="")
                self.canvas.create_oval(
                    part.x - r*0.6, part.y - r*0.6, part.x + r*0.6, part.y + r*0.6,
                    fill='#ffffee', outline="")
            elif part.rtype == "black_flame":
                # Teardrop shape like flame but with dark red inner core
                r = part.size
                tip_x, tip_y = part.x, part.y - r * 1.5
                self.canvas.create_polygon(
                    part.x - r, part.y, part.x + r, part.y, tip_x, tip_y,
                    fill=part.color, outline="")
                self.canvas.create_oval(
                    part.x - r*0.6, part.y - r*0.6, part.x + r*0.6, part.y + r*0.6,
                    fill='#1a0011', outline="")
            elif part.rtype == "life_spark":
                # Small glowing green spark for Circle of Life
                r = max(1, part.size)
                self.canvas.create_oval(part.x-r, part.y-r, part.x+r, part.y+r,
                                        fill=part.color, outline='#ccffdd' if r > 2 else '')
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
            elif part.rtype in ("eblade", "enemy_slash"):
                # --- CLEAN TAPERED CRESCENT BLADE ---
                r = part.size * 1.5
                max_thickness = part.size * 0.45
                angle = part.angle
                cx, cy = part.x, part.y
                def rot(x, y):
                    return (cx + x*math.cos(angle) - y*math.sin(angle),
                            cy + x*math.sin(angle) + y*math.cos(angle))
                outer = []; inner = []
                for a in range(-70, 71, 10):
                    rad = math.radians(a)
                    outer.append(rot(math.cos(rad)*r, math.sin(rad)*r))
                    tf = 1 - abs(a)/70
                    inner.append(rot(math.cos(rad)*(r-max_thickness*tf),
                                     math.sin(rad)*(r-max_thickness*tf)))
                bp = []
                for x, y in outer + inner[::-1]: bp += [x, y]
                self.canvas.create_polygon(bp, fill=part.color, outline=part.color, width=1)

            elif part.rtype == "enemy_slash_dark":
                # --- ANIMATED SWEEPING CRESCENT (original style) ---
                r_d = part.size * 1.5
                mt_d = part.size * 0.5
                sw_d = getattr(part, '_sweep_offset', 0.0)
                ang_d = part.angle + sw_d
                cx_d, cy_d = part.x, part.y
                tl_d = getattr(part, '_total_life', max(part.life + part.age, 0.001))
                pr_d = part.age / tl_d
                al_d = max(0.0, 1.0 - max(0.0, (pr_d - 0.55) / 0.45))
                try:
                    rv_d = int(self.canvas.winfo_rgb(part.color)[0] / 256 * al_d)
                    gv_d = int(self.canvas.winfo_rgb(part.color)[1] / 256 * al_d)
                    bv_d = int(self.canvas.winfo_rgb(part.color)[2] / 256 * al_d)
                    dc_d = f"#{rv_d:02x}{gv_d:02x}{bv_d:02x}"
                    _lift = int(55 * al_d)
                    ic_d = f"#{min(255,rv_d+_lift):02x}{min(255,gv_d+_lift):02x}{min(255,bv_d+_lift):02x}"
                except Exception:
                    dc_d = part.color; ic_d = '#cccccc'
                def _rsd(x, y, _cx=cx_d, _cy=cy_d, _a=ang_d):
                    return (_cx + x*math.cos(_a) - y*math.sin(_a),
                            _cy + x*math.sin(_a) + y*math.cos(_a))
                o_d = []; i_d = []
                for a in range(-75, 76, 10):
                    rad = math.radians(a)
                    o_d.append(_rsd(math.cos(rad)*r_d, math.sin(rad)*r_d))
                    tf2 = 1 - (abs(a)/75)**0.7
                    i_d.append(_rsd(math.cos(rad)*(r_d-mt_d*tf2), math.sin(rad)*(r_d-mt_d*tf2)))
                bp_d = []
                for x, y in o_d + i_d[::-1]: bp_d += [x, y]
                if len(bp_d) >= 6:
                    self.canvas.create_polygon(bp_d, fill=dc_d, outline=dc_d, width=1)
                hr = r_d*0.72; hth = mt_d*0.22
                ho_d = []; hi_d = []
                for a in range(-55, 56, 15):
                    rad = math.radians(a)
                    ho_d.append(_rsd(math.cos(rad)*hr, math.sin(rad)*hr))
                    hi_d.append(_rsd(math.cos(rad)*(hr-hth), math.sin(rad)*(hr-hth)))
                hbp = []
                for x, y in ho_d + hi_d[::-1]: hbp += [x, y]
                if len(hbp) >= 6:
                    self.canvas.create_polygon(hbp, fill=ic_d, outline='', width=0)

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
            elif part.rtype == "lunge_trail":
                # Thick red stippled line from particle origin to its stored end point
                _lt_x2 = getattr(part, '_lunge_end_x', part.x + math.cos(part.angle)*14)
                _lt_y2 = getattr(part, '_lunge_end_y', part.y + math.sin(part.angle)*14)
                _lt_a  = max(0.0, part.life / 0.35)   # fade as life shrinks
                _lt_w  = max(2, int(12 * _lt_a))
                self.canvas.create_line(part.x, part.y, _lt_x2, _lt_y2,
                                        fill='#cc1100', width=_lt_w,
                                        capstyle='round', stipple='gray50')
                self.canvas.create_line(part.x, part.y, _lt_x2, _lt_y2,
                                        fill='#ff4422', width=max(1, _lt_w - 4),
                                        capstyle='round', stipple='gray75')
            elif part.rtype == "shield":
                if hasattr(part, '_barrier_angle'):
                    # Mana Barrier — draw as a glowing line segment perpendicular to angle
                    perp = part._barrier_angle + math.pi / 2
                    half = part.size
                    x1 = part.x + math.cos(perp) * half
                    y1 = part.y + math.sin(perp) * half
                    x2 = part.x - math.cos(perp) * half
                    y2 = part.y - math.sin(perp) * half
                    self.canvas.create_line(x1, y1, x2, y2, fill='#66aaff', width=5, capstyle='round')
                    self.canvas.create_line(x1, y1, x2, y2, fill='white',   width=2, capstyle='round')
                else:
                    # outlined circle (no fill) — mana bubble shield
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
            elif part.rtype == "holy_puff":
                # Cosmetic fire particle — fading glowing circle
                r = max(1, part.size)
                self.canvas.create_oval(part.x-r, part.y-r, part.x+r, part.y+r,
                                        fill=part.color, outline='')
            elif part.rtype == "black_puff":
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
                # Sparkling dot burst — larger than before
                r = max(2, part.size)
                self.canvas.create_oval(part.x-r, part.y-r, part.x+r, part.y+r,
                                        fill=part.color, outline='white' if r > 4 else '')
                if r > 6:
                    self.canvas.create_oval(part.x-r*0.4, part.y-r*0.4, part.x+r*0.4, part.y+r*0.4,
                                            fill='white', outline='')
            elif part.rtype == "water_burst":
                # Aqua burst dot — same size as magic_burst, just aqua-colored
                r = max(2, part.size)
                self.canvas.create_oval(part.x-r, part.y-r, part.x+r, part.y+r,
                                        fill=part.color, outline='#aaeeff' if r > 3 else '')
            elif part.rtype == "water_drip":
                # Falling water teardrop
                r = max(1, part.size)
                # Oval body
                self.canvas.create_oval(part.x - r, part.y - r*0.8,
                                        part.x + r, part.y + r*1.4,
                                        fill=part.color, outline='')
            elif part.rtype == "water_puddle":
                # Single master particle — draw irregular organic blob (lava-pool style)
                _px2 = getattr(part, '_puddle_x', part.x)
                _py2 = getattr(part, '_puddle_y', part.y)
                _puddle_key = (round(_px2, -1), round(_py2, -1))
                if not hasattr(self, '_drawn_puddles'):
                    self._drawn_puddles = set()
                if _puddle_key not in self._drawn_puddles:
                    self._drawn_puddles.add(_puddle_key)
                    _poly_angs = getattr(part, '_poly_angles', None)
                    _poly_rads = getattr(part, '_poly_radii', None)
                    if _poly_angs and _poly_rads:
                        # Slight time-based wobble so the puddle breathes
                        _t_now = part.age if hasattr(part, 'age') else 0
                        _pts_p = []
                        for _pa_i, (_pa, _pr_i) in enumerate(zip(_poly_angs, _poly_rads)):
                            _wob = math.sin(_t_now * 1.5 + _pa_i * 0.7) * 3
                            _r_w = _pr_i + _wob
                            _pts_p.append(_px2 + math.cos(_pa) * _r_w)
                            _pts_p.append(_py2 + math.sin(_pa) * _r_w * 0.55)
                        if len(_pts_p) >= 6:
                            # Single transparent layer — very see-through water
                            self.canvas.create_polygon(
                                _pts_p, fill='#0055cc', outline='#44aaff',
                                width=1, smooth=True, stipple='gray12')
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
            elif part.rtype == "root_spike":
                # Draw a jagged root spike from origin to current position
                ox = getattr(part, '_origin_x', part.x)
                oy = getattr(part, '_origin_y', part.y)
                self.canvas.create_line(ox, oy, part.x, part.y,
                                        fill=part.color, width=3, capstyle='round')
                # Tip knob
                self.canvas.create_oval(part.x-part.size*0.7, part.y-part.size*0.7,
                                        part.x+part.size*0.7, part.y+part.size*0.7,
                                        fill='#228B22', outline='')
            elif part.rtype == "root_tri":
                # Draw a solid upward-pointing triangle (spike) growing from origin
                ox = getattr(part, '_origin_x', part.x)
                oy = getattr(part, '_origin_y', part.y)
                # Triangle: base at origin, tip at current position
                base_half = part.size * 0.55
                cos_a = math.cos(part.angle + math.pi / 2)
                sin_a = math.sin(part.angle + math.pi / 2)
                bx1 = ox + cos_a * base_half
                by1 = oy + sin_a * base_half
                bx2 = ox - cos_a * base_half
                by2 = oy - sin_a * base_half
                tri_col = part.color
                dark_col = '#3B2507'
                self.canvas.create_polygon(
                    bx1, by1, bx2, by2, part.x, part.y,
                    fill=tri_col, outline=dark_col, width=1
                )
                # Highlight edge with stipple for texture
                self.canvas.create_line(bx1, by1, part.x, part.y,
                                        fill='#7CFC00', width=1, stipple='gray25')
            elif part.rtype == "grasping_vine_track":
                # Draw a segmented wobbly vine line from player to grasped target
                tgt = getattr(part, '_target', None)
                plr = getattr(part, '_player', None)
                if tgt is not None and plr is not None:
                    px, py = plr.x, plr.y
                    tx, ty = tgt.x, tgt.y
                    segs = 14
                    t_now = time.time()
                    pts = []
                    for i in range(segs + 1):
                        t = i / segs
                        # Wobbly offset perpendicular to the vine
                        dx = tx - px; dy = ty - py
                        perp_x = -dy; perp_y = dx
                        length = max(1, math.hypot(perp_x, perp_y))
                        perp_x /= length; perp_y /= length
                        wave = math.sin(t * math.pi * 3 + t_now * 5) * 9 * math.sin(t * math.pi)
                        wx = px + dx * t + perp_x * wave
                        wy = py + dy * t + perp_y * wave
                        pts.extend([wx, wy])
                    if len(pts) >= 4:
                        # Dark vine body
                        self.canvas.create_line(*pts, fill='#556B2F', width=5,
                                                smooth=True, capstyle='round')
                        # Bright green highlight
                        self.canvas.create_line(*pts, fill='#32CD32', width=2,
                                                smooth=True, capstyle='round',
                                                stipple='gray75')
                    # Small thorn nubs along the vine
                    for i in range(1, segs):
                        t = i / segs
                        dx2 = tx - px; dy2 = ty - py
                        nx = px + dx2 * t
                        ny = py + dy2 * t
                        if i % 3 == 0:
                            self.canvas.create_oval(nx-3, ny-3, nx+3, ny+3,
                                                    fill='#228B22', outline='')
            elif part.rtype == "vine_wrap":
                # Draw vine segment as a small oval
                self.canvas.create_oval(part.x-part.size, part.y-part.size,
                                        part.x+part.size, part.y+part.size,
                                        fill=part.color, outline='')
            elif part.rtype == "wind_stipple":
                # Short dashed streak in the travel direction — wind effect
                fade = max(0.0, part.life / max(0.001, getattr(part, '_orig_life', part.life + 0.001)))
                if not hasattr(part, '_orig_life'):
                    part._orig_life = part.life + 0.001
                streak_len = part.radius * fade
                cos_a = math.cos(part.angle)
                sin_a = math.sin(part.angle)
                x1 = part.x - cos_a * streak_len * 0.4
                y1 = part.y - sin_a * streak_len * 0.4
                x2 = part.x + cos_a * streak_len * 0.6
                y2 = part.y + sin_a * streak_len * 0.6
                # Main streak
                self.canvas.create_line(x1, y1, x2, y2,
                                        fill=part.color, width=1,
                                        stipple='gray50', capstyle='round')
                # Tiny dot at front for sparkle
                if fade > 0.5:
                    self.canvas.create_oval(x2-1, y2-1, x2+1, y2+1,
                                            fill='#ffffff', outline='')
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

        # ── Draw weapon particles (world-space → screen) ─────────────────
        for wp in self.weapon_particles:
            if self.dungeon_id == 0:
                sx = wp.x - self.camera_x
                sy = wp.y - self.camera_y
            else:
                sx, sy = wp.x, wp.y
            if -20 < sx < WINDOW_W + 20 and -20 < sy < WINDOW_H + 20:
                wp.draw(self.canvas, sx, sy)

        # ── Frost snow — world-anchored around Ice Cavern, spawns high, falls far ──
        if getattr(self, 'dungeon_id', 0) == 0:
            _ICE_CX  = TOWN_CX + 3200
            _ICE_CY  = TOWN_CY + 420
            _SNOW_R  = 1100         # horizontal spread radius around clearing centre
            _SPAWN_H = 400          # spawn just above the clearing, not way up high
            cam_x    = getattr(self, 'camera_x', 0)
            cam_y    = getattr(self, 'camera_y', 0)

            # Screen rect of the snow zone — skip all work if entirely off-screen
            _zone_sx = (_ICE_CX - _SNOW_R) - cam_x
            _zone_ex = (_ICE_CX + _SNOW_R) - cam_x
            _zone_sy = (_ICE_CY - _SPAWN_H) - cam_y
            _zone_ey = (_ICE_CY + 400)      - cam_y

            _dt_snow = getattr(self, '_last_snow_dt', 0.016)
            if not hasattr(self, '_snow_particles'):
                # Pre-populate: scatter flakes across the full fall range so they're
                # already visible the first time the player reaches the area
                self._snow_particles = []
                for _ in range(100):
                    _wx = _ICE_CX + random.randint(-_SNOW_R, _SNOW_R)
                    _edge_frac = abs(_wx - _ICE_CX) / _SNOW_R
                    if random.random() < _edge_frac ** 1.5:
                        continue
                    _wy = (_ICE_CY - _SPAWN_H) + random.randint(0, _SPAWN_H + 800)
                    self._snow_particles.append({
                        'wx': _wx, 'wy': _wy,
                        'vx': random.uniform(-18, 18),
                        'vy': random.uniform(160, 260),
                        'size': random.uniform(6.0, 13.0),
                        'life': random.uniform(4.0, 7.0),
                        'age':  random.uniform(0, 4.0),
                        'rot':  random.uniform(0, math.pi / 3),
                    })

            # Spawn 3 new flakes per frame — sparser further from centre
            for _ in range(3):
                _wx = _ICE_CX + random.randint(-_SNOW_R, _SNOW_R)
                # Reject flakes far from centre with increasing probability
                _edge_frac = abs(_wx - _ICE_CX) / _SNOW_R   # 0=centre, 1=edge
                if random.random() < _edge_frac ** 1.5:      # sparse at edges
                    continue
                _wy = _ICE_CY - _SPAWN_H
                self._snow_particles.append({
                    'wx': _wx, 'wy': _wy,
                    'vx': random.uniform(-18, 18),
                    'vy': random.uniform(160, 260),
                    'size': random.uniform(6.0, 13.0),
                    'life': random.uniform(4.0, 7.0),
                    'age':  0.0,
                    'rot':  random.uniform(0, math.pi / 3),
                })

            _dead_snow = []
            for _flake in self._snow_particles:
                _flake['age'] += _dt_snow
                if _flake['age'] >= _flake['life']:
                    _dead_snow.append(_flake)
                    continue
                _flake['wx'] += _flake['vx'] * _dt_snow
                _flake['wy'] += _flake['vy'] * _dt_snow
                # Convert world → screen
                _fx = _flake['wx'] - cam_x
                _fy = _flake['wy'] - cam_y
                # Only draw if on screen
                if _fx < -20 or _fx > WINDOW_W + 20 or _fy < -20 or _fy > WINDOW_H + 20:
                    continue
                _fs  = _flake['size']
                _rot = _flake['rot']
                for _arm_a in (_rot, _rot + math.pi/3, _rot + 2*math.pi/3):
                    _ax = math.cos(_arm_a) * _fs
                    _ay = math.sin(_arm_a) * _fs
                    self.canvas.create_line(
                        _fx - _ax, _fy - _ay, _fx + _ax, _fy + _ay,
                        fill='#dff4ff', width=2)
                    for _barfrac in (0.45, 0.72):
                        _bx = _fx + math.cos(_arm_a) * _fs * _barfrac
                        _by = _fy + math.sin(_arm_a) * _fs * _barfrac
                        _blen = _fs * 0.28
                        _perp_a = _arm_a + math.pi / 2
                        self.canvas.create_line(
                            _bx - math.cos(_perp_a)*_blen, _by - math.sin(_perp_a)*_blen,
                            _bx + math.cos(_perp_a)*_blen, _by + math.sin(_perp_a)*_blen,
                            fill='#c8eeff', width=1)
            for _flake in _dead_snow:
                if _flake in self._snow_particles:
                    self._snow_particles.remove(_flake)

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
    def draw_dungeon_esc_panel(self):
        """Draw the mid-screen Save / Exit overlay (ESC in dungeon)."""
        cv = self.canvas
        W, H = WINDOW_W, WINDOW_H

        # Dimmed backdrop
        cv.create_rectangle(0, 0, W, H, fill='#000000', stipple='gray50', outline='')

        # Panel — large centred box
        PW = min(W - 60, 860)
        PH = min(H - 40, 580)
        PX = (W - PW) // 2
        PY = (H - PH) // 2

        # Glow borders
        cv.create_rectangle(PX-4, PY-4, PX+PW+4, PY+PH+4,
                            fill='', outline='#331166', width=5)
        cv.create_rectangle(PX-2, PY-2, PX+PW+2, PY+PH+2,
                            fill='#07071a', outline='#6644cc', width=2)
        cv.create_rectangle(PX, PY, PX+PW, PY+PH, fill='#0d0d22', outline='')

        # Title bar
        cv.create_rectangle(PX, PY, PX+PW, PY+44, fill='#16163a', outline='')
        cv.create_line(PX, PY+44, PX+PW, PY+44, fill='#5533aa', width=1)
        cv.create_text(PX+PW//2, PY+22,
                       text='⏸   PAUSED  —  SAVE YOUR PROGRESS',
                       fill='#ddbbff', font=('Arial', 16, 'bold'))
        cv.create_text(PX+PW-16, PY+22, text='[ESC] close',
                       fill='#554477', font=('Arial', 9), anchor='e')

        # ── Generate / cache the save code ───────────────────────────────────
        try:
            import base64 as _b64, zlib as _zl, json as _jj
            self.player.hotbar_items = list(self.hotbar_items)  # sync GameFrame hotbar → player before serialising
            _raw  = _jj.dumps(self.player.to_dict(), separators=(',',':')).encode('utf-8')
            _code = _b64.urlsafe_b64encode(_zl.compress(_raw, 9)).decode('ascii')
        except Exception as _ex:
            _code = f"(error: {_ex})"
        self._esc_panel_code = _code

        # ── Player info block ─────────────────────────────────────────────────
        sy = PY + 60
        p  = self.player
        cv.create_text(PX + PW//2, sy,
                       text=f'{p.name}  •  {p.class_name}  •  Level {p.level}  •  '
                            f'HP {int(p.hp)}/{int(p.max_hp)}  •  {p.coins} 💰',
                       fill='#aaaadd', font=('Arial', 11))
        sy += 30

        # Divider
        cv.create_line(PX+50, sy, PX+PW-50, sy, fill='#2a2a55', width=1)
        sy += 22

        # ── Save code section ─────────────────────────────────────────────────
        cv.create_text(PX+PW//2, sy,
                       text='SAVE CODE',
                       fill='#aa88ff', font=('Arial', 13, 'bold'))
        sy += 22
        cv.create_text(PX+PW//2, sy,
                       text='Click  📋 Copy  below, then paste the code in the main menu to resume later.',
                       fill='#7777aa', font=('Arial', 10))
        sy += 26

        # Code preview box — shows only first + last 12 chars with •••  in between
        # so the player sees it's real without it filling the screen
        _preview_len = 18
        if len(_code) > _preview_len * 2:
            _preview = _code[:_preview_len] + '  • • • • • •  ' + _code[-_preview_len:]
        else:
            _preview = _code
        _box_h = 44
        cv.create_rectangle(PX+40, sy, PX+PW-40, sy+_box_h,
                            fill='#060614', outline='#443366', width=1)
        cv.create_text(PX+PW//2, sy+_box_h//2,
                       text=_preview, fill='#66ffcc', font=('Courier', 10))
        sy += _box_h + 16

        # ── COPY button ───────────────────────────────────────────────────────
        _bw, _bh = 220, 42
        _bx = PX + (PW - _bw) // 2
        _by = sy
        _copied = getattr(self, '_esc_code_copied', False)
        _bcol   = '#2d1a55' if not _copied else '#1a4a2a'
        _bedge  = '#9966ff' if not _copied else '#44cc77'
        cv.create_rectangle(_bx, _by, _bx+_bw, _by+_bh,
                            fill=_bcol, outline=_bedge, width=2)
        _blbl = '✓  Copied to clipboard!' if _copied else '📋  Copy Save Code'
        _bfc  = '#88ffbb' if _copied else '#ddbbff'
        cv.create_text(_bx+_bw//2, _by+_bh//2,
                       text=_blbl, fill=_bfc, font=('Arial', 12, 'bold'))
        self._esc_copy_btn = (_bx, _by, _bx+_bw, _by+_bh)
        sy += _bh + 24

        # Divider
        cv.create_line(PX+50, sy, PX+PW-50, sy, fill='#2a2a55', width=1)
        sy += 22

        # Auto-save note + progress info
        cv.create_text(PX+PW//2, sy,
                       text='✓  Game is also auto-saved to disk each time this panel opens.',
                       fill='#335533', font=('Arial', 10))
        sy += 30

        # Dungeon progress
        _dname = {1:'Forest Dungeon', 2:'Volcano Dungeon', 3:'Ice Cavern'}.get(
                  self.dungeon_id, f'Dungeon {self.dungeon_id}')
        _boss_done = self.boss_defeated.get(self.dungeon_id, False)
        _prog_txt  = f'Current run:  {_dname}  —  Boss {"✓ defeated" if _boss_done else "not yet defeated"}'
        cv.create_text(PX+PW//2, sy, text=_prog_txt, fill='#886699', font=('Arial', 10))
        sy += 30

        # Controls
        cv.create_text(PX+PW//2, sy,
                       text='Press  ESC  to resume playing     |     Press  Q  to quit to desktop',
                       fill='#9977cc', font=('Arial', 11, 'bold'))

        # Auto-save to disk
        try:
            if hasattr(self.master, 'save_player'):
                self.player.hotbar_items = list(self.hotbar_items)  # sync GameFrame hotbar → player before serialising
                self.master.save_player(self.player.to_dict())
        except Exception:
            pass

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

        # Outer frame — tall enough for stats + buffs + Wild Shape entry
        ws_form_name = getattr(p, 'wild_shape_form', None)
        panel_h = 580
        self.canvas.create_rectangle(100, 100, 720, panel_h, fill='#1a1a1a', outline='white', width=4)

        stats = ['strength','vitality','agility','constitution','intelligence','wisdom','will']
        stat_display_names = {
            'strength': 'STRENGTH', 'vitality': 'VITALITY',
            'agility': 'AGILITY', 'constitution': 'CONSTITUTION',
            'intelligence': 'INTELLIGENCE', 'wisdom': 'WISDOM', 'will': 'WILL'
        }

        # Map ALL 7 stats from buff short-keys
        BUFF_KEY_MAP = {
            'strength':     'str',
            'agility':      'agi',
            'will':         'wil',
            'constitution': 'con',
            'vitality':     'vit',
            'intelligence': 'int',
            'wisdom':       'wis',
        }
        buff_by_stat = {s: 0 for s in stats}
        # Wild Shape stat changes shown separately, not as buff
        ws_bonuses = getattr(p, '_ws_stat_bonuses', {})
        now = time.time()
        for buf in getattr(p, 'active_buffs', []):
            if buf['end'] > now:
                for full_stat, short_key in BUFF_KEY_MAP.items():
                    buff_by_stat[full_stat] += buf.get(short_key, 0)

        # Fixed column positions — no character-length guessing
        COL_NAME  = 130   # stat name + base value
        COL_EQUIP = 460   # item bonus  (+N)
        COL_BUFF  = 540   # buff bonus  [+N]
        COL_BTN   = 660   # + button

        y_start    = 120
        stat_height = 40

        for i, stat in enumerate(stats):
            buff_val  = buff_by_stat.get(stat, 0)
            # For constitution, self.constitution is base-only; item bonus is in _item_con_bonus
            base_val  = getattr(p, stat) - buff_val

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

        # ── Stat points + active buffs (including Wild Shape scaling) ─────────
        base_y     = y_start + len(stats) * stat_height + 10
        cursor_y   = base_y

        # Stat points line
        self.canvas.create_text(130, cursor_y, anchor='w',
                                text=f'Stat Points Available: {p.stat_points}',
                                fill='#aaaaaa', font=('Arial', 13))
        cursor_y += 22

        # Active buffs — Wild Shape buff is stored here too, shown first in its colour
        active_buffs = [b for b in getattr(p, 'active_buffs', []) if b['end'] > now]
        if active_buffs:
            self.canvas.create_text(130, cursor_y, anchor='w',
                                    text='Active Buffs:', fill='#44ff88',
                                    font=('Arial', 10, 'bold'))
            cursor_y += 18
            for j, buf in enumerate(active_buffs[:6]):
                remaining = buf['end'] - now
                time_str  = '∞ active' if remaining == float('inf') or remaining > 9000 else f'{remaining:.1f}s'
                # Choose colour: Wild Shape gets its form colour, others green
                is_ws  = buf.get('name') == 'Wild Shape'
                ws_fn  = getattr(p, 'wild_shape_form', None)
                if is_ws and ws_fn:
                    ws_fd3 = next((f for f in WILD_SHAPE_FORMS if f['name'] == ws_fn), None)
                    bc     = ws_fd3['color'] if ws_fd3 else '#33ff66'
                    # Extra detail line showing which stats were scaled
                    desc   = buf.get('desc', '')
                    detail = f"  ↳ {desc}" if desc else ''
                else:
                    bc     = '#44ff88'
                    detail = ''
                self.canvas.create_text(130, cursor_y, anchor='w',
                                        text=f"{buf['emoji']} {buf['name']}  [{time_str}]{detail}",
                                        fill=bc, font=('Arial', 9))
                cursor_y += 16
    def loop(self):
        self.poll_mouse_pos()          # update mouse once per frame, no event spam
        now=time.time(); dt=now-self.last_time; self.last_time=now
        self._last_snow_dt = min(dt, 0.05)  # clamp for snow physics
        self.update_camera()
        self.update_player(dt)
        self.update_entities(dt)
        self.draw()
        self.draw_hotbar()  # consumable hotbar always visible; skill hotbar hidden indoors
        if self.show_help:
            self.draw_help_panel()
        if getattr(self, '_show_dungeon_esc_panel', False) and self.dungeon_id != 0:
            self.draw_dungeon_esc_panel()
        if self.show_stats:
            self.draw_stats_panel()
        # ── Warp Scroll channelling tick ─────────────────────────────────
        if getattr(self.player, '_warp_scroll_active', False):
            _wt_now = time.time()
            elapsed_w = _wt_now - self.player._warp_scroll_start
            frac_w   = min(elapsed_w / 3.0, 1.0)
            # Circle is anchored at the cast position (world space)
            cx_w = self.player._warp_cx
            cy_w = self.player._warp_cy
            # Flat ground-level ellipse — wide, very short vertically
            RX = 70   # half-width  (world px)
            RY = 22   # half-height (flat perspective)
            sx_c = cx_w - self.camera_x   # screen centre
            sy_c = cy_w - self.camera_y
            # Outer glow ring
            self.canvas.create_oval(sx_c-RX, sy_c-RY, sx_c+RX, sy_c+RY,
                                    outline='#aa44ff', width=3)
            # Inner ring
            self.canvas.create_oval(sx_c-RX*2//3, sy_c-RY*2//3,
                                    sx_c+RX*2//3, sy_c+RY*2//3,
                                    outline='#dd88ff', width=2)
            # Rotating rune lines along the ellipse plane
            angle_base = elapsed_w * 1.5
            for k in range(6):
                ang = angle_base + k * math.pi / 3
                self.canvas.create_line(
                    sx_c, sy_c,
                    sx_c + int(RX * math.cos(ang)),
                    sy_c + int(RY * math.sin(ang)),
                    fill='#cc66ff', width=1)
            # Persistent inward-moving particles
            _wpts = getattr(self.player, '_warp_particles', [])
            # Spawn new ones at outer edge every few frames
            if random.random() < 0.4:
                ang_p = random.uniform(0, math.pi * 2)
                dist  = random.uniform(1.8, 3.2)   # multiples of RX/RY
                _wpts.append([
                    cx_w + RX * dist * math.cos(ang_p),   # world x
                    cy_w + RY * dist * math.sin(ang_p),   # world y
                ])
            # Move each particle toward circle centre and draw it
            PULL = 80   # world px per second
            new_wpts = []
            for wp2 in _wpts:
                dx2 = cx_w - wp2[0]; dy2 = cy_w - wp2[1]
                dist2 = math.hypot(dx2, dy2)
                if dist2 < 6:   # absorbed into circle
                    continue
                step2 = min(PULL * (dt + 0.016), dist2)
                wp2[0] += dx2 / dist2 * step2
                wp2[1] += dy2 / dist2 * step2
                # Draw at screen coords
                spx = wp2[0] - self.camera_x
                spy = wp2[1] - self.camera_y
                sz  = max(1, int(3 * (1 - dist2 / (RX * 3.5))))  # bigger near centre
                self.canvas.create_oval(spx-sz, spy-sz, spx+sz, spy+sz,
                                        fill='#ee99ff', outline='')
                new_wpts.append(wp2)
            self.player._warp_particles = new_wpts
            # Countdown text above circle
            self.canvas.create_text(sx_c, sy_c - RY - 14,
                                    text=f'Warping… {max(0.0, 3.0-elapsed_w):.1f}s',
                                    fill='#dd88ff', font=('Arial', 9, 'bold'))
            # Check player is still inside the circle before teleporting
            _pdx = self.player.x - cx_w
            _pdy = self.player.y - cy_w
            _in_circle = (_pdx/RX)**2 + (_pdy/RY)**2 <= 4.0  # 2x radius tolerance
            if not _in_circle:
                # Player stepped out — cancel
                self.player._warp_scroll_active = False
                self.player._warp_particles = []
            elif elapsed_w >= 3.0:
                self.player._warp_scroll_active = False
                self.player._warp_particles = []
                self.room_row = 0; self.room_col = 0
                self.room = self.get_room(0, 0)
                self.player.x = 400; self.player.y = 300
                # Clear all particles, projectiles and coins
                self.coin_particles.clear()
                self.weapon_particles.clear()
                self.projectiles.clear()
        self.after(16,self.loop)
        for enemy in self.room.enemies:
            if getattr(enemy, '_immobile', False):
                continue   # totems and fixed enemies never get pushed
            resolve_overlap(self.player, enemy)

        # Enemy vs enemy
        for i, e1 in enumerate(self.room.enemies):
            for j, e2 in enumerate(self.room.enemies):
                if i < j:  # avoid double-checking
                    if getattr(e1, '_immobile', False) or getattr(e2, '_immobile', False):
                        continue
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
        # Always start with a class chosen (default Warrior) so the normal
        # interface with save/load codes is shown immediately on first launch.
        if not self.selected_class:
            self.selected_class = "Warrior"
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
        self._settings_overlay = None   # reset ref each rebuild

        def toggle_settings():
            if self._settings_overlay and self._settings_overlay.winfo_exists():
                self._settings_overlay.destroy()
                self._settings_overlay = None
            else:
                self._settings_overlay = _make_settings_overlay(self.home_frame)

        # ── Settings button (top-right) ────────────────────────────────────────
        tk.Button(self.home_frame, text="⚙️", font=("Arial", 14),
                  bg='#2a2a3a', fg='white', activebackground='#3a3a5a',
                  bd=0, padx=6, pady=4, cursor='hand2',
                  command=toggle_settings
                  ).place(relx=1.0, rely=0.0, anchor='ne', x=-8, y=8)
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
                                bg='#4a4a4a', fg='white', activebackground='#5a5a5a',
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

        # Start New Game button
        def start_new_game():
            self.class_chosen = False
            self.selected_class = ''
            self.preview_player = Player(self.name_var.get() or "Hero", "Warrior")
            self.preview_player.unlock_skills()
            self.build_home()

        tk.Button(self.home_frame, text="⚔️ Start New Game", font=("Arial", 12, "bold"),
                  bg='#4a4a4a', fg='white', activebackground='#5a5a5a',
                  command=start_new_game, bd=0, padx=20, pady=8,
                  cursor='hand2').pack(pady=10)

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