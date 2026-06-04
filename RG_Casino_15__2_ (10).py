"""
╔══════════════════════════════════════════════════════╗
║       RG CASINO TOWN  — Full Edition                 ║
║  Texas Hold'em • Yahtzee • Dice Roll • The Arena     ║
║  Boss Encounters • Heist • Debt Interest • VIP+      ║
╚══════════════════════════════════════════════════════╝
"""
import tkinter as tk
from tkinter import font as tkfont
import random, math, time, datetime, string, json, base64
from collections import Counter
from itertools import combinations

W,H=1100,700; TOWN_W=1600; TOWN_H=1100
PLAYER_SPEED=7; PLAYER_R=12; HOTBAR_H=70
GOLD="#f5c518"; CREAM="#f5f0e8"; DARK="#1a1208"; RED_C="#c0392b"
GREEN_C="#27ae60"; BLUE_C="#2980b9"; PURPLE="#8e44ad"
SKINS={
    "default": {"name":"Default", "price":0,    "body":"#cc3333","legs":"#2255aa","hat":"#8B0000","face":"#e8c07a","stripe":GOLD,     "desc":"Classic look"},
    "shadow":  {"name":"Shadow",  "price":500,  "body":"#222222","legs":"#111111","hat":"#000000","face":"#333333","stripe":"#555555","desc":"Dark and mysterious"},
    "gold":    {"name":"Gold",    "price":2000, "body":"#c8960c","legs":"#8B6914","hat":"#5a3a00","face":"#f0d0a0","stripe":"#ffffff","desc":"For the wealthy"},
    "royal":   {"name":"Royal",   "price":1500, "body":"#4a0080","legs":"#2a0060","hat":"#1a0040","face":"#e8c07a","stripe":GOLD,     "desc":"Born to rule"},
    "neon":    {"name":"Neon",    "price":800,  "body":"#00cc44","legs":"#006622","hat":"#003311","face":"#aaffcc","stripe":"#00ff88","desc":"Stand out"},
    "crimson": {"name":"Crimson", "price":600,  "body":"#990000","legs":"#660000","hat":"#440000","face":"#e8c07a","stripe":"#ff4444","desc":"Pure danger"},
    "arctic":  {"name":"Arctic",  "price":1200, "body":"#aaddff","legs":"#6699bb","hat":"#334455","face":"#ddeeff","stripe":"#ffffff","desc":"Ice cold"},
    "inferno": {"name":"Inferno", "price":2500, "body":"#ff4400","legs":"#882200","hat":"#441100","face":"#f0a070","stripe":"#ffaa00","desc":"On fire"},
}
CARD_SKINS={
    "classic":  {"name":"Classic",  "price":0,    "back":"#8B0000","border":"#c0a000","face":"#ffffff","sym_b":"#111111","sym_r":"#cc0000","desc":"Standard red back"},
    "navy":     {"name":"Navy",     "price":400,  "back":"#001a66","border":"#4466ff","face":"#0a1a44","sym_b":"#aaccff","sym_r":"#ff9999","desc":"Cool navy blue"},
    "obsidian": {"name":"Obsidian", "price":800,  "back":"#0a0a0a","border":"#555555","face":"#111111","sym_b":"#eeeeee","sym_r":"#ff6666","desc":"Pitch black"},
    "emerald":  {"name":"Emerald",  "price":600,  "back":"#004400","border":"#00aa44","face":"#001a00","sym_b":"#88ffaa","sym_r":"#ffaaaa","desc":"Casino green"},
    "gilded":   {"name":"Gilded",   "price":1800, "back":"#5a3a00","border":"#f5c518","face":"#1a0e00","sym_b":"#f5c518","sym_r":"#ff9944","desc":"Gold leaf edges"},
    "royal":    {"name":"Royal",    "price":1200, "back":"#2a0060","border":"#cc88ff","face":"#120028","sym_b":"#cc88ff","sym_r":"#ff88cc","desc":"Purple velvet"},
    "crimson":  {"name":"Crimson",  "price":500,  "back":"#6a0000","border":"#ff4444","face":"#220000","sym_b":"#ffaaaa","sym_r":"#ffdddd","desc":"Deep crimson"},
    "arctic":   {"name":"Arctic",   "price":1000, "back":"#003366","border":"#88ddff","face":"#001428","sym_b":"#88ddff","sym_r":"#ffaaaa","desc":"Ice blue"},
}
DICE_SKINS={
    "classic":  {"name":"Classic",  "price":0,    "col":"#eeeeee","dot":"#111111","ol":"#cccccc","desc":"Ivory white"},
    "obsidian": {"name":"Obsidian", "price":500,  "col":"#111111","dot":"#eeeeee","ol":"#333333","desc":"Jet black"},
    "ruby":     {"name":"Ruby",     "price":700,  "col":"#880000","dot":"#ffffff","ol":"#cc0000","desc":"Deep ruby red"},
    "sapphire": {"name":"Sapphire", "price":700,  "col":"#001a88","dot":"#ffffff","ol":"#0033cc","desc":"Deep blue"},
    "gilded":   {"name":"Gilded",   "price":1500, "col":"#8B6914","dot":"#000000","ol":"#f5c518","desc":"Gold plated"},
    "jade":     {"name":"Jade",     "price":900,  "col":"#006633","dot":"#ffffff","ol":"#00aa44","desc":"Jade green"},
    "amethyst": {"name":"Amethyst", "price":1100, "col":"#4a0080","dot":"#ffffff","ol":"#8844cc","desc":"Purple crystal"},
    "bone":     {"name":"Bone",     "price":300,  "col":"#d4c8a0","dot":"#333333","ol":"#b8ac84","desc":"Antique bone"},
}
FELT="#1a5c2a"; FELT_L="#236b30"; ORANGE="#e67e22"
CARD_SUITS={"♠":"black","♥":"red","♦":"red","♣":"black"}
CARD_RANKS=["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
HORSE_NAMES=["Thunderhoof","Nightmare","Lucky Star","Ironmane","Shadowbolt"]
HORSE_COLS=["#e74c3c","#3498db","#f39c12","#2ecc71","#9b59b6"]
CHIP_VALS=[1,5,10,25,50,100,500]
POKER_RANK_ORDER={r:i for i,r in enumerate(CARD_RANKS)}
HAND_NAMES={8:"Straight Flush",7:"Four of a Kind",6:"Full House",5:"Flush",
            4:"Straight",3:"Three of a Kind",2:"Two Pair",1:"One Pair",0:"High Card"}
ENEMY_NAMES=["Brawler Bo","Iron Mike","The Crusher","El Diablo","Fat Tony"]
ENEMY_MAX_HP=[100,120,150,170,220]
INTEREST_INTERVAL=3; INTEREST_RATE=0.10

RESTAURANT_MENU=[
    ("Boiled Egg",      50,  15, "A simple egg. Restores a little HP."),
    ("BLT Sandwich",   150,  35, "Classic BLT. Hearty and filling."),
    ("Caesar Salad",   200,  45, "Fresh and crisp."),
    ("Full English",   400,  70, "The full works. Massive HP restore."),
    ("Bluefin Ravioli",900, 100, "Chef's finest. Full HP restore!"),
]

def round_rect(canvas,x1,y1,x2,y2,r=12,**kw):
    pts=[x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,x2,y2-r,x2,y2,x2-r,y2,x1+r,y2,x1,y2,x1,y2-r,x1,y1+r,x1,y1]
    return canvas.create_polygon(pts,smooth=True,**kw)

def card_value(rank):
    if rank in("J","Q","K"):return 10
    if rank=="A":return 11
    return int(rank)

def _eval_5card(hand5):
    ranks=sorted([POKER_RANK_ORDER[c[0]] for c in hand5],reverse=True)
    suits=[c[1] for c in hand5]; is_flush=len(set(suits))==1
    unique=sorted(set(ranks),reverse=True)
    is_straight=len(unique)==5 and(unique[0]-unique[4]==4)
    if not is_straight and set(unique)=={12,0,1,2,3}:
        is_straight=True; ranks=[3,2,1,0,12]
    cnt=Counter(ranks); groups=sorted(cnt.values(),reverse=True)
    rg=sorted(cnt.keys(),key=lambda r:(cnt[r],r),reverse=True)
    if is_flush and is_straight:return(8,ranks)
    if groups[0]==4:return(7,rg)
    if groups[:2]==[3,2]:return(6,rg)
    if is_flush:return(5,ranks)
    if is_straight:return(4,ranks)
    if groups[0]==3:return(3,rg)
    if groups[:2]==[2,2]:return(2,rg)
    if groups[0]==2:return(1,rg)
    return(0,ranks)

def best_poker_hand(cards):
    if len(cards)<=5:return _eval_5card(cards)
    best=None
    for combo in combinations(cards,5):
        s=_eval_5card(list(combo))
        if best is None or s>best:best=s
    return best

def yah_upper(d,n):return d.count(n)*n
def yah_3oak(d):return sum(d) if any(d.count(x)>=3 for x in d) else 0
def yah_4oak(d):return sum(d) if any(d.count(x)>=4 for x in d) else 0
def yah_fh(d):v=sorted(Counter(d).values());return 25 if v==[2,3] else 0
def yah_sm(d):
    s=sorted(set(d))
    return 30 if any(all(x in s for x in seq) for seq in [[1,2,3,4],[2,3,4,5],[3,4,5,6]]) else 0
def yah_lg(d):return 40 if sorted(set(d)) in [[1,2,3,4,5],[2,3,4,5,6]] else 0
def yah_yahtzee(d):return 50 if len(set(d))==1 else 0
def yah_chance(d):return sum(d)
YAHTZEE_CATS=[
    ("Ones",        lambda d:yah_upper(d,1)),("Twos",        lambda d:yah_upper(d,2)),
    ("Threes",      lambda d:yah_upper(d,3)),("Fours",       lambda d:yah_upper(d,4)),
    ("Fives",       lambda d:yah_upper(d,5)),("Sixes",       lambda d:yah_upper(d,6)),
    ("3 of a Kind", yah_3oak),              ("4 of a Kind", yah_4oak),
    ("Full House",  yah_fh),               ("Sm Straight",  yah_sm),
    ("Lg Straight", yah_lg),               ("YAHTZEE!",     yah_yahtzee),
    ("Chance",      yah_chance),
]

class CasinoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RG Casino Town"); self.resizable(False,False); self.configure(bg=DARK)
        self.money=1000; self.starting_money=1000; self.debt=0
        self.shady_borrowed=False; self.borrow_count=0
        self.games_played=0; self.wins=0; self.losses=0; self.ties=0
        self.total_bet=0; self.total_won=0; self.total_lost=0
        self.interest_games_since_borrow=0; self.boss_alert_level=0; self._pending_boss=False
        self.hotel_owned_rooms={}  # {room_id: floor} for purchased rooms
        self.figurine_collection=[]  # list of figurine ids owned
        self.figurine_display_f2=[]  # up to 10 slot ids placed on floor2 table
        self.figurine_display_f3=[]  # up to 30 slot ids placed on floor3 table
        self.vip_unlocked=False; self.arena_unlocked=False
        self.player_health=100; self.fight_stage=0
        self.enemy_hp=list(ENEMY_MAX_HP)
        self.fight_skills={"kick":False,"fire_blast":False,"block":False,"jump":False}
        self.creative_mode=False
        self.screen="title"; self._exit_cooldown=0; self._int_door_cooldown=0; self._in_shady=False
        self._fountain_frame=0; self._town_msg=""; self._town_msg_timer=0
        self._pending_after=[]
        self._heist_approach_cd=0; self._pending_heist_offer=False; self._loops_paused=False
        self.owned_skins={"default"}; self.equipped_skin="default"
        self.owned_card_skins={"classic"}; self.equipped_card_skin="classic"
        self.owned_dice_skins={"classic"}; self.equipped_dice_skin="classic"
        self._interior_loop_id=None   # tracks scheduled interior loop so it can be hard-cancelled
        self.px=800; self.py=600; self.keys=set(); self.cam_x=0; self.cam_y=0
        self.int_building=None; self.int_room=None; self.int_rooms={}
        self.int_px=W//2; self.int_py=420
        self.nearby_npc=None; self.npc_dialogue=""; self.dial_timer=0
        self.canvas=tk.Canvas(self,width=W,height=H,bg=DARK,highlightthickness=0); self.canvas.pack()
        # Persistent settings cog — created AFTER canvas.pack() so .lift() works
        self._cog_btn=tk.Button(self,text="⚙",font=tkfont.Font(family="Courier New",size=10,weight="bold"),
                                command=self._settings_screen,
                                bg="#2a2040",fg="#ddccff",relief="solid",bd=1,padx=3,pady=1,
                                activebackground="#44306a",activeforeground="#ffffff",
                                cursor="hand2")
        self._cog_btn.place(x=W-44,y=H-46)
        self._cog_btn.lift()
        self.fnt_title=tkfont.Font(family="Georgia",size=20,weight="bold")
        self.fnt_body =tkfont.Font(family="Georgia",size=13)
        self.fnt_small=tkfont.Font(family="Courier New",size=11)
        self.fnt_card =tkfont.Font(family="Georgia",size=16,weight="bold")
        self.fnt_huge =tkfont.Font(family="Georgia",size=30,weight="bold")
        self.fnt_btn  =tkfont.Font(family="Georgia",size=12,weight="bold")
        self._overlay_widgets=[]; self._hotbar_widgets=[]
        self.buildings=[
            dict(name="casino", x=400, y=200,w=200,h=160,col="#8B0000",roof="#600000",label="CASINO",     desc="Enter casino"),
            dict(name="stables",x=900, y=180,w=180,h=140,col="#7d5a3c",roof="#5a3e20",label="STABLES",    desc="Horse Racing"),
            dict(name="vip",    x=1200,y=450,w=170,h=150,col="#4a2060",roof="#2d0d4a",label="VIP LOUNGE", desc="Exclusive games"),
            dict(name="bank",   x=700, y=820,w=150,h=120,col="#1a3a5c",roof="#0f2340",label="BANK",       desc="Stats & balance"),
            dict(name="arena",  x=1000,y=680,w=190,h=155,col="#2a0000",roof="#1a0000",label="THE ARENA",  desc="Fight & Dine"),
            dict(name="shop",   x=370, y=860,w=120,h=95, col="#e8e0d0",roof="#2a7a5a",label="BOUTIQUE",   desc="Buy skins"),
            dict(name="den",    x=1380,y=100,w=145,h=120,col="#0a0a1a",roof="#220022",label="THE DEN",     desc="Cards & Dice"),
            dict(name="hotel",  x=1300,y=840,w=200,h=160,col="#c8b89a",roof="#8B6914",label="GRAND HOTEL",desc="Stay & relax"),
            dict(name="figshop",x=1210,y=100,w=160,h=130,col="#1a0028",roof="#440055",label="GUMBALL EMPORIUM",desc="Rare figurines"),
        ]
        # Shady alley is an outdoor area, not a building — placed away from roads
        self.shady_area=dict(x=80,y=680,w=180,h=150)  # world coords (bottom-left, clear of roads)
        self.bind("<KeyPress>",self._key_down); self.bind("<KeyRelease>",self._key_up)
        self.focus_set(); self._show_title()

    # ── TITLE / AGE GATE ────────────────────────────────
    def _show_title(self):
        self.screen="title"; c=self.canvas; c.delete("all"); self._clear_overlay()
        self._cog_btn.place_forget()
        c.create_rectangle(0,0,W,H,fill="#080400")
        for tx,ty,sym in [(70,70,"♠"),(W-70,70,"♥"),(70,H-70,"♦"),(W-70,H-70,"♣")]:
            c.create_text(tx,ty,text=sym,fill="#1e0a00",font=tkfont.Font(size=90),anchor="center")
        c.create_rectangle(16,16,W-16,H-16,outline=GOLD,width=3)
        c.create_text(W//2,125,text="RG  CASINO  TOWN",fill=GOLD,
                      font=tkfont.Font(family="Georgia",size=34,weight="bold"),anchor="center")
        c.create_text(W//2,178,text="Where fortune favours the bold",
                      fill="#c8a050",font=tkfont.Font(family="Georgia",size=14,slant="italic"),anchor="center")
        c.create_line(W//2-250,208,W//2+250,208,fill=GOLD,width=2)
        round_rect(c,W//2-290,236,W//2+290,498,r=18,fill="#100700",outline=GOLD,width=2)
        c.create_text(W//2,275,text="Age Verification Required",fill=GOLD,font=self.fnt_title,anchor="center")
        c.create_text(W//2,312,text="You must be 18 or older to enter.",fill=CREAM,font=self.fnt_body,anchor="center")
        c.create_text(W//2,352,text="Enter your year of birth:",fill=CREAM,font=self.fnt_body,anchor="center")
        self._year_var=tk.StringVar()
        ye=tk.Entry(self,textvariable=self._year_var,font=tkfont.Font(family="Georgia",size=16),
                    width=8,bg="#1e0f00",fg=GOLD,insertbackground=GOLD,
                    relief="flat",highlightthickness=2,highlightcolor=GOLD,justify="center")
        self.canvas.create_window(W//2,392,window=ye); self._overlay_widgets.append(ye); ye.focus_set()
        ye.bind("<Return>",lambda e:self._verify_age())
        eb=tk.Button(self,text="ENTER CASINO",command=self._verify_age,
                     font=tkfont.Font(family="Georgia",size=14,weight="bold"),
                     bg=GOLD,fg=DARK,activebackground="#c8a000",relief="flat",cursor="hand2",width=18)
        self.canvas.create_window(W//2,448,window=eb); self._overlay_widgets.append(eb)
        self._title_err_id=None
        c.create_text(W//2,H-16,text="Fictional game for entertainment only.",fill="#28180a",font=self.fnt_small)

    def _verify_age(self):
        try: year=int(self._year_var.get())
        except: self._title_error("Please enter a valid 4-digit year."); return
        today=datetime.date.today(); age=today.year-year
        if year==67:   # ── CREATIVE MODE ──
            self._activate_creative_mode(); return
        if year==1534:  # Bishop easter egg
            self._clear_overlay(); c=self.canvas; c.delete("all")
            c.create_rectangle(0,0,W,H,fill="#000")
            c.create_text(W//2,H//2,text="Welcome............. Bishop",fill=RED_C,font=self.fnt_huge,anchor="center")
            self.after(2500,self._start_town); return
        if year<1900 or year>today.year: self._title_error("Please enter a valid birth year.")
        elif age<18: self._underage_shutdown()
        else: self._start_town()

    def _activate_creative_mode(self):
        self.creative_mode=True
        self.money=999_999_999
        self.vip_unlocked=True
        self.arena_unlocked=True
        self.fight_skills={"kick":True,"fire_blast":True,"block":True,"jump":True}
        self._clear_overlay(); c=self.canvas; c.delete("all")
        # Flashy creative mode screen
        c.create_rectangle(0,0,W,H,fill="#000011")
        # Animated star burst
        for i in range(24):
            a=math.radians(i*15)
            x1=W//2+int(20*math.cos(a)); y1=H//2+int(20*math.sin(a))
            x2=W//2+int(320*math.cos(a)); y2=H//2+int(320*math.sin(a))
            col=["#ff4400","#ff8800","#ffcc00","#00ff88","#0088ff","#aa00ff"][i%6]
            c.create_line(x1,y1,x2,y2,fill=col,width=3)
        c.create_oval(W//2-180,H//2-180,W//2+180,H//2+180,fill="#000022",outline="#00ffcc",width=4)
        c.create_oval(W//2-140,H//2-140,W//2+140,H//2+140,fill="#000033",outline="#ffcc00",width=2)
        c.create_text(W//2,H//2-70,text="✦ CREATIVE MODE ✦",fill="#ffcc00",
                      font=tkfont.Font(family="Georgia",size=28,weight="bold"),anchor="center")
        c.create_text(W//2,H//2-20,text="All skills unlocked. Infinite money.",
                      fill="#00ffcc",font=tkfont.Font(family="Courier New",size=13),anchor="center")
        c.create_text(W//2,H//2+20,text="3.5× speed. All buildings unlocked. Near-invincible.",
                      fill="#00ffcc",font=tkfont.Font(family="Courier New",size=13),anchor="center")
        c.create_text(W//2,H//2+60,text=f"Balance: ${self.money:,}",
                      fill=GOLD,font=tkfont.Font(family="Georgia",size=16,weight="bold"),anchor="center")
        c.create_text(W//2,H//2+100,text="\"The house always wins... but you ARE the house.\"",
                      fill="#666",font=tkfont.Font(family="Georgia",size=10,slant="italic"),anchor="center")
        # Pulsing border
        for bw2,bc in [(6,"#ffcc00"),(12,"#ff8800"),(20,"#551a00")]:
            try: c.create_rectangle(bw2,bw2,W-bw2,H-bw2,fill="",outline=bc,width=2)
            except: pass
        self.after(2800,self._start_town)

    def _start_town(self):
        self._clear_overlay(); self.screen="town"
        self._cog_btn.place(x=W-44,y=H-46); self._cog_btn.lift()
        self._town_loop()

    def _title_error(self,msg):
        if self._title_err_id: self.canvas.delete(self._title_err_id)
        self._title_err_id=self.canvas.create_text(W//2,484,text=msg,fill=RED_C,font=self.fnt_small,anchor="center")

    def _underage_shutdown(self):
        self._clear_overlay(); c=self.canvas; c.delete("all")
        c.create_rectangle(0,0,W,H,fill="#1a0000")
        c.create_text(W//2,H//2-80,text="ACCESS DENIED",fill="#ff4444",
                      font=tkfont.Font(family="Georgia",size=38,weight="bold"),anchor="center")
        c.create_text(W//2,H//2-20,text="You must be 18 or older to enter.",
                      fill=CREAM,font=self.fnt_title,anchor="center")
        countdown_id=c.create_text(W//2,H//2+60,text="Closing in 5...",
                                   fill="#cc4444",font=self.fnt_body,anchor="center")
        bar_bg=c.create_rectangle(W//2-150,H//2+100,W//2+150,H//2+120,fill="#330000",outline="#660000",width=1)
        bar_fg=c.create_rectangle(W//2-150,H//2+100,W//2+150,H//2+120,fill="#cc0000",outline="")
        total=5
        def tick(remaining):
            if remaining<=0:
                self.destroy(); return
            c.itemconfig(countdown_id,text=f"Closing in {remaining}...")
            frac=remaining/total
            c.coords(bar_fg,W//2-150,H//2+100,W//2-150+int(300*frac),H//2+120)
            self.after(1000,lambda:tick(remaining-1))
        tick(total)

    # ── INPUT ────────────────────────────────────────────
    def _key_down(self,e):
        self.keys.add(e.keysym.lower())
        if e.keysym=="Escape":
            if self.screen=="interior": self._exit_interior()
            elif self.screen=="game":
                if getattr(self,"_in_shady",False): self._leave_shady()
                else: self._back_to_interior()
        elif e.keysym.lower()=="c" and self.screen=="interior":
            room=self.int_rooms.get(self.int_room,{})
            if room.get("has_tv"):
                if self._interior_loop_id:
                    try: self.after_cancel(self._interior_loop_id)
                    except: pass
                    self._interior_loop_id=None
                self.screen="game"; self._clear_overlay(); self._hotel_tv_screen()
            else:
                self._try_interact()
        elif e.keysym.lower()=="h" and getattr(self,"creative_mode",False):
            self._shady_heist_approach(lambda:None)
        elif e.keysym=="4" and getattr(self,"creative_mode",False):
            self.boss_alert_level=2; self.debt=max(self.debt,500); self._boss_encounter()
        elif e.keysym=="5" and getattr(self,"creative_mode",False):
            self.boss_alert_level=4; self.debt=max(self.debt,500); self._boss_encounter()

    def _key_up(self,e): self.keys.discard(e.keysym.lower())

    # ── POST-GAME STATS & EVENTS ─────────────────────────
    def _post_game(self,bet,result):
        self.games_played+=1; self.total_bet+=bet
        if result=="win":   self.wins+=1;   self.total_won+=bet
        elif result=="loss":self.losses+=1;  self.total_lost+=bet
        else:               self.ties+=1
        self._check_unlocks(); self._apply_interest_if_due()
        # Queue shady approach for after the game if debt can't be paid
        if self.debt>0 and self.money<self.debt and not self._pending_heist_offer:
            if random.randint(1,3)==1:
                self._pending_heist_offer=True

    def _check_unlocks(self):
        profit=self.money-self.starting_money
        if not self.vip_unlocked   and profit>=5000:  self.vip_unlocked=True
        if not self.arena_unlocked and profit>=10000: self.arena_unlocked=True

    def _apply_interest_if_due(self):
        if self.debt<=0: return
        self.interest_games_since_borrow+=1
        if self.interest_games_since_borrow>=INTEREST_INTERVAL:
            inc=max(1,int(self.debt*INTEREST_RATE))
            self.debt+=inc; self.interest_games_since_borrow=0; self.boss_alert_level+=1
            if self.boss_alert_level>=4 or random.randint(1,4)==1:
                self._pending_boss=True

    def _show_town_msg(self,text,ms=2500): self._town_msg=text; self._town_msg_timer=ms
    # ── TOWN LOOP ─────────────────────────────────────────
    def _town_loop(self):
        if self.screen!="town" or self._loops_paused: return
        self._fountain_frame+=1
        if self._town_msg_timer>0:
            self._town_msg_timer-=33
            if self._town_msg_timer<=0: self._town_msg=""
        self._move_player(); self._draw_town(); self._check_building_entry()
        # Shady approach in town: trigger when debt can't be paid
        if self.debt>0 and self.money<self.debt and self.screen=="town":
            if self._heist_approach_cd>0:
                self._heist_approach_cd-=1
            elif random.randint(1,220)==1:
                self._heist_approach_cd=540   # ~18 sec cooldown
                self._shady_heist_approach(lambda:None)
                return
        if getattr(self,"_pending_boss",False) and not self._loops_paused:
            self._pending_boss=False; self.after(700,self._boss_encounter); return
        self.after(33,self._town_loop)

    def _move_player(self):
        dx=dy=0
        spd=14 if getattr(self,'creative_mode',False) else PLAYER_SPEED
        if "w" in self.keys or "up"    in self.keys: dy-=spd
        if "s" in self.keys or "down"  in self.keys: dy+=spd
        if "a" in self.keys or "left"  in self.keys: dx-=spd
        if "d" in self.keys or "right" in self.keys: dx+=spd
        self.px=max(PLAYER_R,min(TOWN_W-PLAYER_R,self.px+dx))
        self.py=max(PLAYER_R,min(TOWN_H-PLAYER_R,self.py+dy))
        self.cam_x=max(0,min(TOWN_W-W,self.px-W//2))
        self.cam_y=max(0,min(TOWN_H-H,self.py-H//2))

    def _tw(self,x): return x-self.cam_x
    def _th(self,y): return y-self.cam_y

    def _check_building_entry(self):
        if time.time()<self._exit_cooldown: return
        # Check shady area proximity (outdoor — no building entry, open shady screen directly)
        sa=self.shady_area
        if abs(self.px-(sa["x"]+sa["w"]//2))<70 and abs(self.py-(sa["y"]+sa["h"]//2))<70:
            if time.time()>self._exit_cooldown:
                self._exit_cooldown=time.time()+1.0
                self._in_shady=True
                self.screen="game"; self._shady_screen()
            return
        for b in self.buildings:
            bx=b["x"]+b["w"]//2; by=b["y"]+b["h"]
            # Player must be walking up into the bottom edge of the building
            if abs(self.px-bx)<50 and 0<=self.py-by<40:
                self._enter_interior(b["name"]); return

    def _draw_town(self):
        c=self.canvas; c.delete("all")
        c.create_rectangle(0,0,W,H,fill="#1a3d12",outline="")
        pg=110
        for gx in range(-(self.cam_x%pg),W+pg,pg):
            for gy in range(-(self.cam_y%pg),H+pg,pg):
                v=((gx+self.cam_x)//pg*7919+(gy+self.cam_y)//pg*6271)%3
                c.create_oval(gx-38,gy-22,gx+38,gy+22,fill=("#163610","#1c4214","#152e0e")[v],outline="")
        self._draw_cobblestone(298,148,656,458)
        self._draw_cobblestone(848,148,1092,378)
        ry1,ry2=self._th(475),self._th(565)
        c.create_rectangle(0,ry1,W,ry2,fill="#1c1c26",outline="")
        c.create_line(0,ry1+2,W,ry1+2,fill="#3a3a55",width=2)
        c.create_line(0,ry2-2,W,ry2-2,fill="#3a3a55",width=2)
        for xi in range(-(self.cam_x%80),W+80,80):
            c.create_rectangle(xi+2,self._th(514),xi+44,self._th(526),fill="#d4a820",outline="")
        rx1,rx2=self._tw(678),self._tw(762)
        c.create_rectangle(rx1,0,rx2,H,fill="#1c1c26",outline="")
        c.create_line(rx1+2,0,rx1+2,H,fill="#3a3a55",width=2)
        c.create_line(rx2-2,0,rx2-2,H,fill="#3a3a55",width=2)
        for yi in range(-(self.cam_y%80),H+80,80):
            c.create_rectangle(self._tw(715),yi+2,self._tw(725),yi+44,fill="#d4a820",outline="")
        fsx,fsy=self._tw(590),self._th(510)
        if -70<fsx<W+70 and -70<fsy<H+70:
            t=self._fountain_frame
            c.create_oval(fsx-52,fsy-26,fsx+52,fsy+26,fill="#1e4a6a",outline="#3a8abf",width=3)
            c.create_oval(fsx-44,fsy-20,fsx+44,fsy+20,fill="#0d2d45",outline="")
            c.create_rectangle(fsx-4,fsy-24,fsx+4,fsy+2,fill="#9aabb8",outline="")
            for i,an in enumerate(range(0,360,60)):
                ra=math.radians(an); phase=t*0.09+i*0.8; jet_h=12+6*math.sin(phase)
                ex=fsx+int(18*math.cos(ra)); ey=fsy-22-jet_h+int(3*abs(math.sin(ra)))
                c.create_line(fsx,fsy-22,ex,ey,fill="#88ccee" if i%2==0 else "#aaddff",width=2)
            spray_h=18+int(7*math.sin(t*0.13))
            c.create_line(fsx,fsy-22,fsx,fsy-22-spray_h,fill="#ddeeff",width=3)
        for tx,ty in [(280,320),(1120,280),(830,680),(1320,680),(940,860),(80,380),(650,750),(360,600),(1060,550)]:
            self._draw_tree(tx,ty)
        for lx,ly in [(618,478),(722,478),(618,562),(722,562),(478,493),(858,493),(498,276),(398,620),(1002,616)]:
            self._draw_lamp(lx,ly)
        for b in self.buildings: self._draw_building(b)
        self._draw_shady_area()
        px,py=self._tw(self.px),self._th(self.py)
        sk=SKINS[self.equipped_skin]
        c.create_oval(px-PLAYER_R+3,py+PLAYER_R-1,px+PLAYER_R-3,py+PLAYER_R+5,fill="#111111",outline="")
        c.create_rectangle(px-5,py+4,px-1,py+PLAYER_R+4,fill=sk["legs"],outline=DARK,width=1)
        c.create_rectangle(px+1,py+4,px+5,py+PLAYER_R+4,fill=sk["legs"],outline=DARK,width=1)
        c.create_rectangle(px-8,py-4,px+8,py+5,fill=sk["body"],outline=DARK,width=1)
        c.create_rectangle(px-12,py-3,px-8,py+3,fill=sk["body"],outline=DARK,width=1)
        c.create_rectangle(px+8,py-3,px+12,py+3,fill=sk["body"],outline=DARK,width=1)
        c.create_oval(px-7,py-PLAYER_R-2,px+7,py-4,fill=sk["face"],outline=DARK,width=1)
        c.create_rectangle(px-10,py-PLAYER_R,px+10,py-PLAYER_R+3,fill=sk["hat"],outline=DARK)
        c.create_rectangle(px-6,py-PLAYER_R-9,px+6,py-PLAYER_R,fill=sk["hat"],outline=DARK)
        c.create_line(px-6,py-PLAYER_R-2,px+6,py-PLAYER_R-2,fill=sk["stripe"],width=2)
        self._draw_hud()
        self._draw_raffle_hud()
        if self._town_msg:
            c.create_text(W//2,H//2,text=self._town_msg,fill=RED_C,font=self.fnt_body,anchor="center")
        c.create_rectangle(0,H-26,W,H,fill="#06060a",outline="")
        c.create_text(W//2,H-13,text="WASD / Arrow Keys to move  |  Walk into a building to enter  |  ESC exits",fill="#6666aa",font=self.fnt_small)

    def _draw_cobblestone(self,wx1,wy1,wx2,wy2):
        c=self.canvas; sx1,sy1=self._tw(wx1),self._th(wy1); sx2,sy2=self._tw(wx2),self._th(wy2)
        if sx2<0 or sx1>W or sy2<0 or sy1>H: return
        c.create_rectangle(sx1,sy1,sx2,sy2,fill="#5a5048",outline="")
        cw,ch=30,18
        for row,yy in enumerate(range(sy1,sy2,ch)):
            off=(row%2)*(cw//2)
            for xx in range(sx1-off,sx2+cw,cw):
                v=(xx*3+yy*7)%4
                c.create_rectangle(xx+1,yy+1,min(xx+cw-1,sx2),min(yy+ch-1,sy2),
                                   fill=("#635848","#5a5040","#686050","#504840")[v],outline="#3a3028",width=1)

    def _draw_tree(self,tx,ty):
        c=self.canvas; sx,sy=self._tw(tx),self._th(ty)
        if not(-50<sx<W+50 and -50<sy<H+50): return
        c.create_rectangle(sx-5,sy,sx+5,sy+28,fill="#5a3e20",outline="#3a2008")
        c.create_oval(sx-18,sy+10,sx+18,sy+28,fill="#0d2010",outline="")
        c.create_oval(sx-26,sy-28,sx+26,sy+10,fill="#145a10",outline="#0a3a08",width=2)
        c.create_oval(sx-22,sy-36,sx+22,sy+2,fill="#1a7a18",outline="#0a4a08",width=2)
        c.create_oval(sx-14,sy-44,sx+14,sy-16,fill="#22941e",outline="#0a5a08",width=2)

    def _draw_lamp(self,lx,ly):
        c=self.canvas; sx,sy=self._tw(lx),self._th(ly)
        if not(0<sx<W): return
        lcx=sx+14; lcy=sy-62; lw=10; lh=13
        c.create_oval(lcx-20,lcy-20,lcx+20,lcy+20,fill="#665522",outline="")
        c.create_polygon(sx-5,sy+16,sx+5,sy+16,sx+3,sy-52,sx-3,sy-52,fill="#1e1c18",outline="#36322a",width=1)
        for ry in (sy-16,sy-32,sy-48):
            c.create_rectangle(sx-6,ry,sx+6,ry+4,fill="#2c2a24",outline="#4a4638")
        c.create_rectangle(sx-8,sy+8,sx+8,sy+18,fill="#1e1c18",outline="#36322a")
        hex_pts=[]
        for i in range(6):
            a=math.radians(i*60-90); hex_pts+=[lcx+int(lw*math.cos(a)),lcy+int(lh*math.sin(a))]
        c.create_polygon(hex_pts,fill="#1a1810",outline="#5a5228",width=2)
        for i in range(6):
            mid_a=math.radians(i*60-60)
            gx=lcx+int(lw*0.56*math.cos(mid_a)); gy=lcy+int(lh*0.56*math.sin(mid_a))
            c.create_oval(gx-3,gy-5,gx+3,gy+5,fill="#ffcc44",outline="")

    def _draw_building(self,b):
        c=self.canvas; x1=self._tw(b["x"]); y1=self._th(b["y"]); x2=x1+b["w"]; y2=y1+b["h"]
        if x2<-20 or x1>W+20 or y2<-20 or y1>H+20: return
        mx=(x1+x2)//2; name=b.get("name","")
        if name=="casino":
            c.create_rectangle(x1,y1,x2,y2,fill="#7a2020",outline="#3d0a0a",width=3)
            bw,bh=22,10
            for row,yy in enumerate(range(y1+2,y2-40,bh)):
                off=(row%2)*(bw//2)
                for xx in range(x1+2-off,x2+bw,bw):
                    c.create_rectangle(xx,yy,min(xx+bw-2,x2-2),yy+bh-2,fill="#8b2828",outline="#3d0a0a",width=1)
            for cx_ in [x1+18,x1+42,x2-42,x2-18]:
                c.create_rectangle(cx_-5,y1-5,cx_+5,y2,fill="#d4c090",outline="#9a8050",width=1)
                c.create_oval(cx_-7,y1-14,cx_+7,y1-4,fill="#d4c090",outline="#9a8050")
            c.create_polygon(x1-6,y1,mx,y1-48,x2+6,y1,fill="#c8a860",outline="#7a6030",width=2)
            c.create_rectangle(x1+8,y2-58,x2-8,y2-36,fill="#0a0028",outline="#ff00ff",width=2)
            c.create_text(mx,y2-47,text="ROYAL CASINO",fill="#ff55ff",font=self.fnt_small,anchor="center")
            for ddx in [mx-22,mx+2]:
                c.create_rectangle(ddx,y2-36,ddx+20,y2,fill="#3a1a00",outline=GOLD,width=2)
                c.create_arc(ddx,y2-36,ddx+20,y2-22,start=0,extent=180,fill="#5a2a00",outline=GOLD)
            c.create_rectangle(mx-72,y1-76,mx+72,y1-50,fill="#0a0020",outline=GOLD,width=2)
            c.create_text(mx,y1-63,text=b["label"],fill=GOLD,font=self.fnt_body,anchor="center")
        elif name=="arena":
            c.create_rectangle(x1,y1,x2,y2,fill="#3a1a00",outline="#1a0800",width=3)
            arch_step=(x2-x1-20)//4
            for ai in range(4):
                ax=x1+10+ai*arch_step+arch_step//2
                c.create_rectangle(ax-12,y1+10,ax+12,y2-30,fill="#1a0600",outline="#2a1000",width=1)
                c.create_arc(ax-12,y1+2,ax+12,y1+28,start=0,extent=180,fill="#1a0600",outline="#2a1000")
            c.create_polygon(x1-4,y1,mx,y1-52,x2+4,y1,fill="#2a1000",outline="#1a0600",width=2)
            c.create_rectangle(x1+20,y2-44,x2-20,y2-22,fill="#5a0000",outline=GOLD,width=2)
            c.create_text(mx,y2-33,text="THE ARENA",fill=GOLD,font=self.fnt_small,anchor="center")
            c.create_rectangle(mx-16,y2-22,mx+16,y2,fill="#0a0000",outline="#3a1000",width=2)
            c.create_rectangle(mx-78,y1-82,mx+78,y1-54,fill="#1a0000",outline=RED_C,width=2)
            c.create_text(mx,y1-68,text=b["label"],fill=RED_C,font=self.fnt_body,anchor="center")
        elif name=="bank":
            c.create_rectangle(x1,y1,x2,y2,fill="#b0a898",outline="#706858",width=3)
            for yy in range(y1,y2,16): c.create_line(x1,yy,x2,yy,fill="#908078",width=1)
            for cx_ in [x1+14,x1+32,x2-32,x2-14]:
                c.create_rectangle(cx_-4,y1-4,cx_+4,y2-20,fill="#d8d0c0",outline="#a09080",width=1)
                c.create_oval(cx_-6,y1-14,cx_+6,y1-3,fill="#d8d0c0",outline="#908070")
            c.create_polygon(x1-4,y1,mx,y1-38,x2+4,y1,fill="#c8c0b0",outline="#706858",width=2)
            c.create_rectangle(mx-14,y2-42,mx+14,y2,fill="#2a1800",outline=GOLD,width=2)
            c.create_arc(mx-14,y2-42,mx+14,y2-28,start=0,extent=180,fill="#3a2800",outline=GOLD)
            c.create_rectangle(mx-72,y1-72,mx+72,y1-48,fill="#1a0a00",outline=GOLD,width=2)
            c.create_text(mx,y1-60,text=b["label"],fill=GOLD,font=self.fnt_body,anchor="center")
        elif name=="shady":
            c.create_rectangle(x1,y1,x2,y2,fill="#1a1a28",outline="#2a2a3a",width=2)
            for cxy in [(x1+6,y2-30),(x1+6,y2-50),(x2-32,y2-30)]:
                c.create_rectangle(cxy[0],cxy[1],cxy[0]+22,cxy[1]+20,fill="#6a4a1a",outline="#3a2a08",width=2)
                c.create_line(cxy[0]+11,cxy[1],cxy[0]+11,cxy[1]+20,fill="#3a2a08")
                c.create_line(cxy[0],cxy[1]+10,cxy[0]+22,cxy[1]+10,fill="#3a2a08")
            c.create_rectangle(mx-16,y2-52,mx+16,y2,fill="#06060a",outline="#333",width=2)
            c.create_arc(mx-16,y2-52,mx+16,y2-38,start=0,extent=180,fill="#0a0a12",outline="#333")
            c.create_rectangle(mx-72,y1-72,mx+72,y1-46,fill="#0a0a14",outline="#cc2200",width=2)
            c.create_text(mx,y1-59,text=b["label"],fill="#cc2200",font=self.fnt_body,anchor="center")
        elif name=="vip":
            c.create_rectangle(x1,y1,x2,y2,fill="#3a1a5a",outline="#6a3a9a",width=3)
            for yy in [y1+18,y1+36,y2-20]: c.create_line(x1,yy,x2,yy,fill=GOLD,width=2)
            for wxx in [x1+14,x2-54]:
                c.create_rectangle(wxx,y1+44,wxx+38,y2-22,fill="#a0c8f0",outline=GOLD,width=2)
                c.create_oval(wxx,y1+20,wxx+38,y1+56,fill="#c0d8f8",outline=GOLD)
            c.create_rectangle(mx-14,y2-42,mx+14,y2,fill="#1a0030",outline=GOLD,width=2)
            c.create_oval(mx-14,y2-42,mx+14,y2-28,fill="#220040",outline=GOLD)
            c.create_rectangle(mx-72,y1-76,mx+72,y1-48,fill="#1a0040",outline=GOLD,width=2)
            c.create_text(mx,y1-62,text=b["label"],fill=GOLD,font=self.fnt_body,anchor="center")
        elif name=="stables":
            bh_=y2-y1; bw_=x2-x1
            c.create_rectangle(x1,y1,x2,y2,fill="#7B1818",outline="#3d0808",width=3)
            for bx_ in range(x1+16,x2,16): c.create_line(bx_,y1,bx_,y2,fill="#5a1010",width=1)
            c.create_line(x1,y1+48,x2,y1+48,fill="#5a1010",width=2)
            rh=int(bh_*0.44); si=int(bw_*0.24); pk=y1-rh-int(rh*0.90)
            c.create_polygon(x1-8,y1,x1+si,y1-rh,x2-si,y1-rh,x2+8,y1,fill="#4a2808",outline="#2a1000",width=2)
            c.create_polygon(x1+si,y1-rh,mx,pk,x2-si,y1-rh,fill="#321c04",outline="#1a0c00",width=2)
            loft_cy=(y1-rh+pk)//2
            c.create_rectangle(mx-9,loft_cy-7,mx+9,loft_cy+7,fill="#ffe090",outline="#3a1800",width=2)
            c.create_rectangle(mx-72,pk-28,mx+72,pk-4,fill="#3a1800",outline=GOLD,width=2)
            c.create_text(mx,pk-16,text=b["label"],fill=GOLD,font=self.fnt_body,anchor="center")
        elif name=="den":
            # ── The Den facade — dark card-shop ──────────────
            c.create_rectangle(x1,y1,x2,y2,fill="#0a0a1a",outline="#220044",width=2)
            # Brick texture
            for row2 in range(y1,y2,8):
                off=(row2//8%2)*14
                for bx5 in range(x1-off,x2,28):
                    c.create_rectangle(bx5,row2,min(bx5+26,x2),row2+7,fill="#0d0d22",outline="#080818",width=1)
            # Neon-style card suit symbols on facade
            for si,(sym,scol) in enumerate([("♠","#aa44ff"),("♥","#ff2244"),("♦","#ff2244"),("♣","#aa44ff")]):
                sx5=x1+14+si*(x2-x1-20)//4
                c.create_text(sx5,y1+int((y2-y1)*0.4),text=sym,fill=scol,
                              font=tkfont.Font(family="Georgia",size=12,weight="bold"))
            # Display window left
            dwx1=x1+6; dwx2=x1+int((x2-x1)*0.52); dwy1=y1+16; dwy2=y2-16
            c.create_rectangle(dwx1,dwy1,dwx2,dwy2,fill="#06061a",outline="#440066",width=2)
            # Mini card in window
            cx5=(dwx1+dwx2)//2-10; cy5=(dwy1+dwy2)//2
            c.create_rectangle(cx5,cy5-16,cx5+18,cy5+24,fill="#8B0000",outline="#c0a000",width=1)
            c.create_text(cx5+9,cy5+4,text="♠",fill="#c0a000",font=tkfont.Font(size=8))
            # Mini die in window
            dx5=cx5+22; dy5=cy5-12
            c.create_rectangle(dx5,dy5,dx5+18,dy5+18,fill="#eee",outline="#aaa",width=1)
            c.create_oval(dx5+5,dy5+5,dx5+9,dy5+9,fill="#111",outline="")
            c.create_oval(dx5+11,dy5+11,dx5+15,dy5+15,fill="#111",outline="")
            # Door right
            ddx=dwx2+int((x2-dwx2)*0.5); ddtop=y1+int((y2-y1)*0.4)
            c.create_rectangle(ddx-11,ddtop,ddx+11,y2,fill="#1a0033",outline="#440066",width=2)
            c.create_rectangle(ddx-7,ddtop+3,ddx+7,y2-3,fill="#0a001a",outline="#440066",width=1)
            c.create_oval(ddx+1,ddtop+(y2-ddtop)//2-2,ddx+6,ddtop+(y2-ddtop)//2+2,fill=GOLD,outline="")
            # Awning — red/black stripes
            aw_y2=y1-3; aw_h2=18
            for stripe in range((x2-x1)//10+1):
                sx6=x1+stripe*10
                col6="#440000" if stripe%2==0 else "#0a0a1a"
                c.create_polygon(sx6,aw_y2,min(sx6+10,x2),aw_y2,
                                 min(sx6+10,x2)+3,aw_y2+aw_h2,sx6-3,aw_y2+aw_h2,fill=col6,outline="")
            c.create_line(x1-4,aw_y2+aw_h2,x2+4,aw_y2+aw_h2,fill="#220000",width=2)
            # Sign
            c.create_rectangle(mx-52,y1-aw_h2-28,mx+52,y1-aw_h2-6,fill="#0a0018",outline="#aa44ff",width=2)
            c.create_text(mx,y1-aw_h2-17,text="♠ THE DEN ♠",fill="#cc88ff",
                          font=self.fnt_small,anchor="center")
        elif name=="shop":
            # ── Boutique facade ──────────────────────────────
            # Main facade — cream render
            c.create_rectangle(x1,y1,x2,y2,fill="#e8e0d0",outline="#c0b090",width=2)
            # Horizontal band courses
            for yy in range(y1,y2,10):
                c.create_line(x1,yy,x2,yy,fill="#ddd8c8",width=1)
            # Teal/green trim panels along top and bottom
            c.create_rectangle(x1,y1,x2,y1+14,fill="#2a7a5a",outline="#1a5a3a",width=1)
            c.create_rectangle(x1,y2-14,x2,y2,fill="#2a7a5a",outline="#1a5a3a",width=1)
            # Large display window left side
            wx1=x1+8; wy1=y1+18; wx2=x1+int((x2-x1)*0.55); wy2=y2-18
            c.create_rectangle(wx1,wy1,wx2,wy2,fill="#d0eeff",outline="#2a7a5a",width=3)
            c.create_line((wx1+wx2)//2,wy1,(wx1+wx2)//2,wy2,fill="#2a7a5a",width=2)
            c.create_line(wx1,(wy1+wy2)//2,wx2,(wy1+wy2)//2,fill="#2a7a5a",width=1)
            # Mannequins in window — small silhouettes
            for mxi,mcol in [(wx1+14,"#cc6688"),(wx1+34,"#5588cc")]:
                myc=(wy1+wy2)//2+2; s=0.55
                c.create_oval(mxi-int(5*s),myc-int(28*s),mxi+int(5*s),myc-int(14*s),fill="#e8c07a",outline="#c0a060",width=1)
                c.create_rectangle(mxi-int(7*s),myc-int(14*s),mxi+int(7*s),myc+int(10*s),fill=mcol,outline="#888",width=1)
                c.create_line(mxi-int(7*s),myc-int(8*s),mxi-int(16*s),myc+int(2*s),fill=mcol,width=3)
                c.create_line(mxi+int(7*s),myc-int(8*s),mxi+int(16*s),myc+int(2*s),fill=mcol,width=3)
                c.create_line(mxi-int(3*s),myc+int(10*s),mxi-int(3*s),myc+int(24*s),fill="#555",width=3)
                c.create_line(mxi+int(3*s),myc+int(10*s),mxi+int(3*s),myc+int(24*s),fill="#555",width=3)
            # Door right side — shorter, doesn't reach full building height
            dx=wx2+int((x2-wx2)*0.5); door_top=y1+int((y2-y1)*0.45)
            c.create_rectangle(dx-12,door_top,dx+12,y2,fill="#3a5a3a",outline="#2a7a5a",width=2)
            c.create_rectangle(dx-8,door_top+4,dx+8,y2-3,fill="#a8d8c8",outline="#2a7a5a",width=1)
            c.create_oval(dx+1,door_top+(y2-door_top)//2-3,dx+7,door_top+(y2-door_top)//2+3,fill=GOLD,outline="")
            # Striped awning
            aw_y=y1-4; aw_h=22
            for stripe in range((x2-x1)//12+1):
                sx_=x1+stripe*12
                col_="#2a7a5a" if stripe%2==0 else "#f5f0e8"
                c.create_polygon(sx_,aw_y, min(sx_+12,x2),aw_y,
                                 min(sx_+12,x2)+4,aw_y+aw_h, sx_-4,aw_y+aw_h,
                                 fill=col_,outline="")
            c.create_line(x1-6,aw_y+aw_h,x2+6,aw_y+aw_h,fill="#1a5a3a",width=2)
            # Sign above awning
            c.create_rectangle(mx-58,y1-aw_h-32,mx+58,y1-aw_h-8,fill="#1a4a2a",outline="#2a7a5a",width=2)
            c.create_text(mx,y1-aw_h-20,text="✦ BOUTIQUE ✦",fill="#f5e8c0",
                          font=self.fnt_small,anchor="center")
            # Flower boxes under window
            c.create_rectangle(wx1+2,wy2+1,wx2-2,wy2+10,fill="#8B4513",outline="#5a2a08",width=1)
            for fx in range(wx1+6,wx2-6,10):
                c.create_oval(fx-4,wy2-6,fx+4,wy2+4,fill=random.choice(["#ff6688","#ffaa44","#ff4466"]),outline="")
        elif name=="hotel":
            # ── Grand Hotel facade ──────────────────────────
            # Main facade — warm stone render
            c.create_rectangle(x1,y1,x2,y2,fill="#c8b89a",outline="#a09070",width=2)
            # Stone block courses
            for row2 in range(y1,y2,12):
                off=(row2//12%2)*20
                for bx5 in range(x1-off,x2,40):
                    c.create_rectangle(bx5+1,row2+1,min(bx5+39,x2-1),row2+11,
                                       fill="#cbbfa3" if (row2//12)%2==0 else "#c2b498",
                                       outline="#a09070",width=1)
            # Classical pilasters (4 tall columns)
            for px3 in [x1+16,x1+52,x2-52,x2-16]:
                c.create_rectangle(px3-5,y1-8,px3+5,y2,fill="#d8ccb0",outline="#b0a080",width=1)
                c.create_oval(px3-7,y1-18,px3+7,y1-6,fill="#d8ccb0",outline="#b0a080")
            # Cornice band at top
            c.create_rectangle(x1-4,y1-8,x2+4,y1+6,fill="#b8a880",outline="#907860",width=2)
            # Three sash windows with shutters
            for wi,wx3 in enumerate([x1+20,mx-20,x2-60]):
                wt=y1+20; wb=y2-32
                c.create_rectangle(wx3,wt,wx3+36,wb,fill="#d0e8f8",outline="#907860",width=2)
                c.create_line((wx3+wx3+36)//2,wt,(wx3+wx3+36)//2,wb,fill="#907860",width=1)
                c.create_line(wx3,(wt+wb)//2,wx3+36,(wt+wb)//2,fill="#907860",width=1)
                # Shutters
                c.create_rectangle(wx3-10,wt,wx3,wb,fill="#2a4a2a",outline="#1a3018",width=1)
                c.create_rectangle(wx3+36,wt,wx3+46,wb,fill="#2a4a2a",outline="#1a3018",width=1)
                for sy3 in range(wt+4,wb,8):
                    c.create_line(wx3-9,sy3,wx3-1,sy3,fill="#3a6030",width=1)
                    c.create_line(wx3+37,sy3,wx3+45,sy3,fill="#3a6030",width=1)
            # Double front doors — arched
            dx=mx; door_top=y2-58
            c.create_rectangle(dx-22,door_top,dx+22,y2,fill="#5a3010",outline=GOLD,width=2)
            c.create_arc(dx-22,door_top-14,dx+22,door_top+14,start=0,extent=180,fill="#6a3a14",outline=GOLD)
            c.create_rectangle(dx-20,door_top,dx,y2-2,fill="#3a1c08",outline="#4a2810",width=1)
            c.create_rectangle(dx,door_top,dx+20,y2-2,fill="#3a1c08",outline="#4a2810",width=1)
            # Door handles
            c.create_oval(dx-5,door_top+(y2-door_top)//2-4,dx-1,door_top+(y2-door_top)//2+4,fill=GOLD,outline="")
            c.create_oval(dx+1,door_top+(y2-door_top)//2-4,dx+5,door_top+(y2-door_top)//2+4,fill=GOLD,outline="")
            # Canopy / marquee
            c.create_polygon(dx-40,door_top-4,dx+40,door_top-4,dx+44,door_top+14,dx-44,door_top+14,
                             fill="#1a3a6a",outline="#0d2040",width=2)
            for ss in range(dx-38,dx+40,10):
                c.create_line(ss,door_top-4,ss+5,door_top+14,fill="#22508a",width=1)
            c.create_text(mx,door_top+6,text="HOTEL",fill="#e0d0b0",
                          font=tkfont.Font(family="Georgia",size=7,weight="bold"))
            # Topmost gable / pediment
            c.create_polygon(x1-4,y1-8,mx,y1-54,x2+4,y1-8,fill="#c0aa80",outline="#907860",width=2)
            c.create_oval(mx-12,y1-52,mx+12,y1-32,fill="#d0c090",outline=GOLD,width=1)
            # Sign board
            c.create_rectangle(mx-76,y1-84,mx+76,y1-56,fill="#1a3a6a",outline=GOLD,width=2)
            c.create_text(mx,y1-70,text="✦ GRAND HOTEL ✦",fill=GOLD,font=self.fnt_body,anchor="center")
        elif name=="figshop":
            # ── Gumball Emporium — dark collectors shop facade ──
            # Main brick body — deep plum
            c.create_rectangle(x1,y1,x2,y2,fill="#1a0028",outline="#440055",width=3)
            bw2,bh2=22,10
            for row2,yy2 in enumerate(range(y1+2,y2-36,bh2)):
                off2=(row2%2)*(bw2//2)
                for xx2 in range(x1+2-off2,x2+bw2,bw2):
                    c.create_rectangle(xx2,yy2,min(xx2+bw2-2,x2-2),yy2+bh2-2,
                                       fill="#220033" if row2%2==0 else "#1e002e",
                                       outline="#300044",width=1)
            # Two slim pilasters
            for px4 in [x1+12,x2-12]:
                c.create_rectangle(px4-4,y1-4,px4+4,y2,fill="#2a0040",outline="#550066",width=1)
                c.create_oval(px4-6,y1-14,px4+6,y1-2,fill="#2a0040",outline="#550066")
            # Three arched display windows showing gumball globes
            for wi2,wx4 in enumerate([x1+22,mx-20,x2-62]):
                wt2=y1+16; wb2=y2-38
                # Window frame
                c.create_rectangle(wx4,wt2,wx4+32,wb2,fill="#0d001a",outline="#663388",width=2)
                c.create_arc(wx4,wt2-14,wx4+32,wt2+10,start=0,extent=180,fill="#0d001a",outline="#663388")
                # Globe inside window
                c.create_oval(wx4+4,wt2+4,wx4+28,wt2+32,fill="#1a0030",outline="#883399",width=2)
                # Coloured ball dots inside globe
                for bi3,bcol3 in enumerate(["#cc2244","#2244cc","#22aa44","#cc8800","#aa22cc"]):
                    ba3=math.radians(bi3*72)
                    bx4=wx4+16+int(7*math.cos(ba3)); by4=wt2+18+int(5*math.sin(ba3))
                    c.create_oval(bx4-3,by4-3,bx4+3,by4+3,fill=bcol3,outline="")
            # Cornice band
            c.create_rectangle(x1-4,y1-4,x2+4,y1+8,fill="#2a0040",outline="#550066",width=2)
            # Triangular pediment
            c.create_polygon(x1-4,y1-4,mx,y1-44,x2+4,y1-4,fill="#1a0030",outline="#550066",width=2)
            # Arched door
            c.create_rectangle(mx-13,y2-42,mx+13,y2,fill="#0d0018",outline="#883399",width=2)
            c.create_arc(mx-13,y2-54,mx+13,y2-28,start=0,extent=180,fill="#110020",outline="#883399")
            c.create_oval(mx-3,y2-26,mx+3,y2-20,fill="#883399",outline="")
            # Neon sign strip
            c.create_rectangle(x1+8,y2-58,x2-8,y2-44,fill="#0a0018",outline="#aa44cc",width=2)
            sc3="#cc66ff" if int(time.time()*2)%2==0 else "#884499"
            c.create_text(mx,y2-51,text="GUMBALL EMPORIUM",fill=sc3,
                          font=tkfont.Font(family="Courier New",size=6,weight="bold"))
            # Sign board above pediment
            c.create_rectangle(mx-70,y1-68,mx+70,y1-46,fill="#0a0018",outline="#883399",width=2)
            c.create_text(mx,y1-57,text="✦ GUMBALL EMPORIUM ✦",fill="#cc66ff",
                          font=self.fnt_small,anchor="center")
        dist=math.hypot(self.px-(b["x"]+b["w"]//2),self.py-(b["y"]+b["h"]//2))
        if dist<120:
            c.create_rectangle(mx-70,y2+6,mx+70,y2+26,fill="#06060a",outline="#ffff44",width=1)
            c.create_text(mx,y2+16,text=f"► {b['desc']}",fill="#ffff55",font=self.fnt_small)

    def _draw_shady_area(self):
        c=self.canvas; sa=self.shady_area
        sx1=self._tw(sa["x"]); sy1=self._th(sa["y"])
        sx2=sx1+sa["w"]; sy2=sy1+sa["h"]
        if sx2<-20 or sx1>W+20 or sy2<-20 or sy1>H+20: return
        # No special grass — blends with town background (drawn over normal tiles)
        # Single mud patch
        c.create_oval(sx1+30,sy1+40,sx1+70,sy1+58,fill="#1e1a0c",outline="#141208",width=1)
        # 5 crates, corners + one centre-ish
        crate_data=[(sx1+8,sy1+8,30,24),(sx1+44,sy1+14,24,20),(sx2-42,sy1+10,32,26),(sx1+12,sy2-36,28,24),(sx2-38,sy2-32,30,24)]
        for cx5,cy5,cw5,ch5 in crate_data:
            c.create_rectangle(cx5+3,cy5+3,cx5+cw5+3,cy5+ch5+3,fill="#0a0804",outline="")
            c.create_rectangle(cx5,cy5,cx5+cw5,cy5+ch5,fill="#7a5018",outline="#3a2008",width=2)
            c.create_rectangle(cx5+2,cy5+2,cx5+cw5-2,cy5+ch5//3,fill="#9a6828",outline="")
            c.create_line(cx5,cy5+ch5//3,cx5+cw5,cy5+ch5//3,fill="#3a2008",width=1)
            c.create_line(cx5+cw5//2,cy5+ch5//3,cx5+cw5//2,cy5+ch5,fill="#3a2008",width=1)
            for nx5,ny5 in [(cx5+4,cy5+4),(cx5+cw5-6,cy5+4),(cx5+4,cy5+ch5-6),(cx5+cw5-6,cy5+ch5-6)]:
                c.create_oval(nx5-2,ny5-2,nx5+2,ny5+2,fill="#1a1008",outline="")
        # Flickering broken lamp — uses fountain_frame for timing
        lx5=sx1+sa["w"]//2; ly5=sy1+6
        c.create_line(lx5,ly5+55,lx5,ly5+6,fill="#302e24",width=3)
        c.create_line(lx5,ly5+6,lx5+14,ly5-6,fill="#302e24",width=3)
        # Flicker pattern: mostly off with occasional dim yellow flash
        ft=self._fountain_frame
        flicker_on=(ft%17<2) or (ft%31<1) or (ft%7<1 and ft%13>10)
        if flicker_on:
            lamp_col="#c8a830"; glow_col="#ffd84a"
        else:
            lamp_col="#2e2c1c"; glow_col=None
        c.create_oval(lx5+8,ly5-12,lx5+22,ly5,fill=lamp_col,outline="#3a3820",width=1)
        if flicker_on and glow_col:
            c.create_oval(lx5+2,ly5-18,lx5+28,ly5+6,fill="",outline=glow_col,width=1)
        # 3 shady guys
        guy_positions=[(sx1+sa["w"]//4,sy1+sa["h"]//2),(sx1+sa["w"]//2+8,sy1+sa["h"]//3+4),(sx2-sa["w"]//5,sy1+sa["h"]*2//3)]
        for (gx2,gy2),gc in zip(guy_positions,["#1e1e1e","#242420","#1a1a14"]):
            c.create_oval(gx2-8,gy2+10,gx2+8,gy2+16,fill="#0c0a04",outline="")
            c.create_line(gx2-4,gy2+8,gx2-5,gy2+16,fill=gc,width=3)
            c.create_line(gx2+2,gy2+8,gx2+3,gy2+16,fill=gc,width=3)
            c.create_oval(gx2-7,gy2-2,gx2+7,gy2+10,fill=gc,outline="#111",width=1)
            c.create_line(gx2+6,gy2+2,gx2+14,gy2+5,fill=gc,width=2)
            c.create_oval(gx2-5,gy2-12,gx2+5,gy2-2,fill="#8a6040",outline="#111",width=1)
            c.create_rectangle(gx2-7,gy2-14,gx2+7,gy2-10,fill=gc,outline="")
            c.create_oval(gx2-6,gy2-16,gx2+6,gy2-12,fill=gc,outline="")
        # Sign
        sxs=sx1+sa["w"]//2-36; sys2=sy2-20
        c.create_rectangle(sxs,sys2,sxs+72,sys2+16,fill="#1c1408",outline="#8B0000",width=2)
        c.create_text(sxs+36,sys2+8,text="SHADY ALLEY",fill="#cc2200",font=tkfont.Font(family="Courier New",size=8,weight="bold"))
        smx=(sx1+sx2)//2
        if math.hypot(self.px-(sa["x"]+sa["w"]//2),self.py-(sa["y"]+sa["h"]//2))<130:
            c.create_rectangle(smx-80,sy2+4,smx+80,sy2+22,fill="#06060a",outline="#cc2200",width=1)
            c.create_text(smx,sy2+13,text="► Borrow / Repay",fill="#cc2200",font=self.fnt_small)


    def _draw_hud(self):
        c=self.canvas
        round_rect(c,10,10,312,84,r=12,fill="#120800",outline=GOLD,width=2)
        c.create_text(52,34,text=f"Balance:  ${self.money:,}",fill=GOLD,font=self.fnt_body,anchor="w")
        debt_col=RED_C if self.debt>0 else "#555566"
        c.create_text(52,55,text=f"Debt: ${self.debt:,}",fill=debt_col,font=self.fnt_small,anchor="w")
        c.create_text(52,70,text=f"Played: {self.games_played}   W:{self.wins} L:{self.losses}",fill="#888899",font=self.fnt_small,anchor="w")
        if getattr(self,'creative_mode',False):
            round_rect(c,W-150,10,W-10,42,r=8,fill="#000022",outline="#00ffcc",width=2)
            c.create_text(W-80,26,text="✦ CREATIVE",fill="#00ffcc",
                          font=tkfont.Font(family="Courier New",size=9,weight="bold"),anchor="center")
        if self.debt>0:
            c.create_rectangle(W-160,6,W-6,32,fill="#330000",outline=RED_C,width=2)
            c.create_text(W-83,19,text="REPAY DEBT",fill=RED_C,font=self.fnt_small,anchor="center")
        if not self.vip_unlocked:
            need=max(0,5000-(self.money-self.starting_money))
            c.create_text(W-10,H-48,text=f"VIP: +${need:,} profit needed",fill="#555544",font=self.fnt_small,anchor="e")
        if not self.arena_unlocked:
            need=max(0,10000-(self.money-self.starting_money))
            c.create_text(W-10,H-32,text=f"Arena: +${need:,} profit needed",fill="#554444",font=self.fnt_small,anchor="e")

    def _draw_raffle_hud(self):
        """Persistent raffle countdown shown at top-centre on all screens."""
        end=getattr(self,"_raffle_end_time",None)
        if not end: return
        remaining=int(end-time.time())
        if remaining<=0: return
        c=self.canvas
        mins,secs=divmod(remaining,60)
        tix_list=getattr(self,"_raffle_tickets",[])
        if isinstance(tix_list,int): tix_list=[]
        tix_count=len(tix_list)
        txt=f"★ RAFFLE  {mins}:{secs:02d}  {tix_count} tkt{'s' if tix_count!=1 else ''} ★"
        tw=len(txt)*7+16
        cx=W//2
        round_rect(c,cx-tw//2,4,cx+tw//2,30,r=8,fill="#0a0020",outline=PURPLE,width=2)
        c.create_text(cx,17,text=txt,fill=GOLD,
                      font=tkfont.Font(family="Courier New",size=9,weight="bold"))

    # ── UI HELPERS ────────────────────────────────────────
    def _clear_overlay(self):
        for w in self._overlay_widgets:
            try: w.destroy()
            except: pass
        self._overlay_widgets.clear()

    def _hide_hotbar(self):
        for w in self._hotbar_widgets:
            try: w.destroy()
            except: pass
        self._hotbar_widgets.clear(); self.canvas.delete("hb_bg")

    def _make_entry(self,x,y,width=10,**kw):
        e=tk.Entry(self,font=self.fnt_body,width=width,bg="#2a1a00",fg=GOLD,
                   insertbackground=GOLD,relief="flat",highlightthickness=2,highlightcolor=GOLD,**kw)
        self.canvas.create_window(x,y,window=e); self._overlay_widgets.append(e); return e

    def _make_btn(self,x,y,text,cmd,col=GOLD,fg=DARK,w=120):
        b=tk.Button(self,text=text,command=cmd,font=self.fnt_btn,bg=col,fg=fg,
                    activebackground="#c8a000",activeforeground=DARK,relief="flat",cursor="hand2",width=w//10)
        self.canvas.create_window(x,y,window=b); self._overlay_widgets.append(b); return b

    def _draw_room_bg(self,title,col1="#1a0a00",col2="#2a1500"):
        c=self.canvas
        c.create_rectangle(0,0,W,H,fill=col1,outline="")
        for y in range(400,H,30):
            c.create_rectangle(0,y,W,y+30,fill="#2a1800" if (y//30)%2==0 else "#231400",outline="")
            for x in range(0,W,180): c.create_line(x,y,x,y+30,fill="#1a1000",width=1)
        c.create_rectangle(0,0,W,400,fill=col2,outline="")
        for y in range(0,400,60): c.create_line(0,y,W,y,fill="#1a1200",width=1)
        for x in range(0,W,120): c.create_line(x,0,x,400,fill="#1a1200",width=1)
        round_rect(c,W//2-220,10,W//2+220,60,r=10,fill=DARK,outline=GOLD,width=3)
        c.create_text(W//2,35,text=title,fill=GOLD,font=self.fnt_title,anchor="center")
        self._make_btn(W-78,30,"BACK",self._back_to_interior,col="#333",fg="#ccc",w=80)
        round_rect(c,10,10,230,50,r=8,fill=DARK,outline=GOLD,width=2)
        c.create_text(20,30,text=f"$ {self.money:,}",fill=GOLD,font=self.fnt_body,anchor="w",tags="bal_txt")

    def _leave_shady(self):
        self._cancel_pending_afters(); self._hide_hotbar(); self._clear_overlay()
        self._in_shady=False
        self.screen="town"; self._exit_cooldown=time.time()+1.5
        self.focus_set(); self._town_loop()

    def _back_to_interior(self):
        self._cancel_pending_afters(); self._hide_hotbar(); self._clear_overlay()
        self.screen="interior"
        if self.int_room=="dojo" or self.int_building=="arena":
            pass  # keep current room
        # Show shady approach if queued from post-game
        if self._pending_heist_offer:
            self._pending_heist_offer=False
            self._interior_loop()
            self.after(400,lambda:self._shady_heist_approach(lambda:None))
            return
        self._interior_loop()

    def _exit_interior(self):
        self._cancel_pending_afters(); self._hide_hotbar(); self._clear_overlay()
        self.screen="town"; self._exit_cooldown=time.time()+1.5
        b=next((bd for bd in self.buildings if bd["name"]==self.int_building),None)
        if b:
            self.px=b["x"]+b["w"]//2
            self.py=b["y"]+b["h"]+40
        self.focus_set(); self._town_loop()

    def _cancel_pending_afters(self):
        for aid in self._pending_after:
            try: self.after_cancel(aid)
            except: pass
        self._pending_after.clear()

    def _msg(self,text,col=GOLD,y=600,size=14):
        self.canvas.delete("msg_layer")
        self.canvas.create_text(W//2,y,text=text,fill=col,
                                font=tkfont.Font(family="Georgia",size=size,weight="bold"),
                                anchor="center",tags="msg_layer")

    def _refresh_balance_text(self):
        self.canvas.delete("bal_txt")
        self.canvas.create_text(20,30,text=f"$ {self.money:,}",fill=GOLD,font=self.fnt_body,anchor="w",tags="bal_txt")

    # ── CHIP HOTBAR ───────────────────────────────────────
    def _show_hotbar(self,on_deal):
        self._hide_hotbar(); c=self.canvas; HY=H-HOTBAR_H
        c.create_rectangle(0,HY,W,H,fill="#06060a",outline="",tags="hb_bg")
        c.create_line(0,HY,W,HY,fill=GOLD,width=2,tags="hb_bg")
        c.create_text(18,HY+14,text="BET",fill=GOLD,font=self.fnt_small,anchor="w",tags="hb_bg")
        c.create_line(72,HY+6,72,HY+HOTBAR_H-6,fill="#3a2800",width=1,tags="hb_bg")
        bet_state={"bet":0}
        bet_id=c.create_text(18,HY+46,text="$0",fill=GOLD,font=self.fnt_body,anchor="w",tags="hb_bg")
        deal_ref=[None]; chip_btns={}
        def refresh():
            bet=bet_state["bet"]; c.itemconfig(bet_id,text=f"${bet:,}")
            for val,btn in chip_btns.items():
                able=self.money-bet>=val
                btn.config(state="normal" if able else "disabled",
                           bg="#0a0800" if able else "#1a1a1a",fg=GOLD if able else "#444")
            if deal_ref[0]:
                deal_ref[0].config(state="normal" if bet_state["bet"]>0 else "disabled",
                                   bg="#0a2000" if bet_state["bet"]>0 else "#0a0a0a",
                                   fg=GOLD if bet_state["bet"]>0 else "#333")
        for i,val in enumerate(CHIP_VALS):
            cx=90+i*86; able=self.money>=val
            def make_add(v=val):
                def add():
                    if self.money-bet_state["bet"]>=v: bet_state["bet"]+=v; refresh()
                return add
            btn=tk.Button(self,text=f"${val}",command=make_add(),
                          font=tkfont.Font(family="Courier New",size=11,weight="bold"),
                          bg="#0a0800" if able else "#1a1a1a",fg=GOLD if able else "#444",
                          activebackground="#1a1400",activeforeground=GOLD,
                          width=5,height=2,relief="groove",cursor="hand2",
                          state="normal" if able else "disabled",disabledforeground="#444")
            c.create_window(cx,HY+36,window=btn); self._hotbar_widgets.append(btn); chip_btns[val]=btn
        def clear_bet(): bet_state["bet"]=0; refresh()
        clr=tk.Button(self,text="CLEAR",command=clear_bet,
                      font=tkfont.Font(family="Courier New",size=11,weight="bold"),
                      bg="#0a0800",fg=RED_C,activebackground="#1a0000",activeforeground=RED_C,
                      width=6,height=2,relief="groove",cursor="hand2")
        clr_x=90+len(CHIP_VALS)*86+22
        c.create_window(clr_x,HY+36,window=clr); self._hotbar_widgets.append(clr)
        def do_deal():
            if bet_state["bet"]>0: bet=bet_state["bet"]; self._hide_hotbar(); on_deal(bet)
        deal_btn=tk.Button(self,text="DEAL",command=do_deal,
                           font=tkfont.Font(family="Georgia",size=12,weight="bold"),
                           bg="#0a0a0a",fg="#333",activebackground="#1a2000",activeforeground=GOLD,
                           width=10,height=2,relief="groove",cursor="hand2",state="disabled")
        c.create_window(clr_x+112,HY+36,window=deal_btn)
        self._hotbar_widgets.append(deal_btn); deal_ref[0]=deal_btn; refresh()
    # ── INTERIOR SYSTEM ───────────────────────────────────
    def _enter_interior(self,building_name):
        if building_name=="vip" and not self.vip_unlocked:
            need=max(0,5000-(self.money-self.starting_money))
            self._show_town_msg(f"VIP Lounge locked! Need +${need:,} more profit."); return
        if building_name=="arena" and not self.arena_unlocked:
            need=max(0,10000-(self.money-self.starting_money))
            self._show_town_msg(f"The Arena is locked! Need +${need:,} more profit."); return
        self.screen="interior"; self.int_building=building_name
        spawn={"casino":(W//2,420),"stables":(W//2,400),
               "vip":(W//2,390),"bank":(W//2,480),"arena":(W//2,420),"hotel":(W//2,500)}
        self.int_px,self.int_py=spawn.get(building_name,(W//2,400))
        self.nearby_npc=None; self.npc_dialogue=""; self.dial_timer=0
        self._setup_interior(building_name); self._clear_overlay(); self._interior_loop()
        # ~1-in-5 chance shady guys ambush you on the way in when debt unpayable
        if self.debt>0 and self.money<self.debt and random.randint(1,5)==1:
            self.after(600,lambda:self._shady_heist_approach(lambda:None))

    def _setup_interior(self,name):
        builders={"casino":self._make_casino_rooms,"stables":self._make_stables_rooms,
                  "vip":self._make_vip_rooms,
                  "bank":self._make_bank_rooms,"arena":self._make_arena_rooms,
                  "shop":self._make_shop_rooms,"den":self._make_den_rooms,"hotel":self._make_hotel_rooms,
                  "figshop":self._make_figshop_rooms}
        self.int_rooms=builders[name](); self.int_room=list(self.int_rooms.keys())[0]

    def _interior_loop(self):
        if self.screen!="interior" or self._loops_paused: return
        self._move_int_player(); self._draw_interior()
        self._check_npc_proximity(); self._check_door_proximity()
        if self.dial_timer>0: self.dial_timer-=1
        if getattr(self,"_pending_boss",False) and not self._loops_paused:
            self._pending_boss=False
            self._interior_loop_id=self.after(700,self._boss_encounter); return
        self._interior_loop_id=self.after(33,self._interior_loop)

    def _move_int_player(self):
        dx=dy=0; speed=7
        if "w" in self.keys or "up"    in self.keys: dy-=speed
        if "s" in self.keys or "down"  in self.keys: dy+=speed
        if "a" in self.keys or "left"  in self.keys: dx-=speed
        if "d" in self.keys or "right" in self.keys: dx+=speed
        nx=max(18,min(W-18,self.int_px+dx)); ny=max(75,min(H-45,self.int_py+dy))
        room=self.int_rooms.get(self.int_room,{})
        for furn in room.get("furniture",[]):
            if furn.get("type") not in ("felt_table","counter"): continue
            fx1,fy1,fx2,fy2=furn["bounds"]; pr=16
            if (fx1-pr<nx<fx2+pr)and(fy1-pr<ny<fy2+pr):
                if not(fx1-pr<nx<fx2+pr and fy1-pr<self.int_py<fy2+pr): ny=self.int_py
                elif not(fx1-pr<self.int_px<fx2+pr and fy1-pr<ny<fy2+pr): nx=self.int_px
                else: nx,ny=self.int_px,self.int_py
        self.int_px,self.int_py=nx,ny

    def _draw_interior(self):
        c=self.canvas; c.delete("all")
        room=self.int_rooms.get(self.int_room,{})
        floor_col=room.get("floor","#2a1500"); wall_col=room.get("wall","#1a0500")
        c.create_rectangle(0,60,W,H-30,fill=floor_col)
        for y in range(60,H-30,28):
            c.create_rectangle(0,y,W,y+28,fill="#1a0000" if (y//28)%2==0 else "#150000",outline="")
            for x in range(0,W,180): c.create_line(x,y,x,y+28,fill="#0d0000",width=1)
        c.create_rectangle(0,0,W,140,fill=wall_col)
        c.create_line(0,60,W,60,fill="#3a1a00",width=3); c.create_line(0,130,W,130,fill="#3a1a00",width=3)
        for x in range(0,W,80): c.create_text(x+40,95,text="✦",fill="#2a0a00",font=tkfont.Font(size=20))
        round_rect(c,W//2-220,8,W//2+220,52,r=8,fill=DARK,outline=GOLD,width=2)
        c.create_text(W//2,30,text=room.get("title",""),fill=GOLD,font=self.fnt_title,anchor="center")
        dfn=room.get("decor_fn")
        if dfn: dfn(c)
        for furn in room.get("furniture",[]): self._draw_furniture(c,furn)
        for door in room.get("doors",[]):
            dx2,dy2,dw,dh=door["x"],door["y"],door["w"],door["h"]
            c.create_rectangle(dx2,dy2,dx2+dw,dy2+dh,fill=door.get("col","#333"),outline=GOLD,width=2)
            c.create_text(dx2+dw//2,dy2+dh//2,text=door["label"],fill=GOLD,font=self.fnt_small,anchor="center")
            m=25
            if dx2-m<=self.int_px<=dx2+dw+m and dy2-m<=self.int_py<=dy2+dh+m:
                c.create_rectangle(dx2-2,dy2-2,dx2+dw+2,dy2+dh+2,outline="#ffff44",width=2)
        for npc in room.get("npcs",[]): self._draw_npc(c,npc)
        # Live figurine display on hotel floor tables
        if self.int_building=="hotel":
            if self.int_room=="floor2":
                placed2=getattr(self,"figurine_display_f2",[])
                tx2=W//2; ty2=330
                for si,fid in enumerate(placed2[:10]):
                    sx=tx2-162+si*36; sy=ty2-10
                    self._draw_figurine(c,fid,sx,sy,size=18)
            elif self.int_room=="floor3":
                placed3=getattr(self,"figurine_display_f3",[])
                tx3=W//2; ty3=300
                for si,fid in enumerate(placed3[:30]):
                    col3=si%10; row3=si//10
                    sx=tx3-324+col3*72; sy=ty3-6+row3*8
                    self._draw_figurine(c,fid,sx,sy,size=14)
        # Live collection count on figshop board
        if self.int_building=="figshop" and self.int_room=="main":
            coll2=getattr(self,"figurine_collection",[])
            c.create_text(100,180,text=f"{len(coll2)}",fill="#ff88ff",
                          font=tkfont.Font(family="Georgia",size=22,weight="bold"))
            c.create_text(100,210,text="figurines",fill=CREAM,
                          font=tkfont.Font(family="Courier New",size=8))
            # Show last 3 acquired
            for i,fid in enumerate(reversed(coll2[-3:])):
                self._draw_figurine(c,fid,100,240+i*34,size=16)
        px,py=self.int_px,self.int_py
        sk=SKINS[self.equipped_skin]
        c.create_oval(px-10,py+14,px+10,py+20,fill="#0a0000",outline="")
        c.create_rectangle(px-5,py+4,px-1,py+16,fill=sk["legs"],outline=DARK,width=1)
        c.create_rectangle(px+1,py+4,px+5,py+16,fill=sk["legs"],outline=DARK,width=1)
        c.create_rectangle(px-9,py-6,px+9,py+6,fill=sk["body"],outline=DARK,width=1)
        c.create_rectangle(px-13,py-4,px-9,py+4,fill=sk["body"],outline=DARK,width=1)
        c.create_rectangle(px+9,py-4,px+13,py+4,fill=sk["body"],outline=DARK,width=1)
        c.create_oval(px-7,py-18,px+7,py-6,fill=sk["face"],outline=DARK,width=1)
        c.create_rectangle(px-10,py-20,px+10,py-17,fill=sk["hat"],outline=DARK)
        c.create_rectangle(px-7,py-28,px+7,py-20,fill=sk["hat"],outline=DARK)
        c.create_line(px-7,py-23,px+7,py-23,fill=sk["stripe"],width=1)
        if self.npc_dialogue and self.dial_timer>0:
            lines=self.npc_dialogue.split("\n"); bh2=20+len(lines)*22; bw2=340; tx=W//2; ty=158
            round_rect(c,tx-bw2//2,ty,tx+bw2//2,ty+bh2,r=10,fill="#1a0a00",outline=GOLD,width=2)
            for i,ln in enumerate(lines):
                c.create_text(tx,ty+14+i*22,text=ln,fill=CREAM,font=self.fnt_small,anchor="center")
        if self.nearby_npc:
            c.create_rectangle(W//2-120,H-76,W//2+120,H-52,fill="#0a0a00",outline="#ffff44",width=2)
            c.create_text(W//2,H-64,text=f"Press C  —  {self.nearby_npc['name']}",fill="#ffff44",font=self.fnt_small,anchor="center")
        c.create_rectangle(0,H-28,W,H,fill="#06060a",outline="")
        c.create_text(W//2,H-14,text="WASD move  |  C interact  |  ESC exit building",fill="#555566",font=self.fnt_small)
        round_rect(c,W-230,8,W-8,52,r=8,fill=DARK,outline=GOLD,width=2)
        c.create_text(W-20,30,text=f"$ {self.money:,}",fill=GOLD,font=self.fnt_body,anchor="e")
        if self.int_building=="arena":
            c.create_rectangle(0,58,220,78,fill="#1a0000",outline=RED_C,width=1)
            c.create_text(8,68,text=f"HP:{self.player_health}  Stage:{self.fight_stage+1}/5  Enemy:{ENEMY_NAMES[min(self.fight_stage,4)]}",
                          fill=RED_C,font=self.fnt_small,anchor="w")
        self._draw_raffle_hud()

    def _draw_npc(self,c,npc):
        nx,ny=npc["x"],npc["y"]; col=npc.get("col","#e8c07a")
        hat_col=npc.get("hat_col","#8B0000"); body_col=npc.get("body_col","#2255aa")
        is_near=self.nearby_npc and self.nearby_npc.get("id")==npc.get("id")
        if is_near: c.create_oval(nx-20,ny-32,nx+20,ny+28,outline="#ffff44",width=2)
        c.create_oval(nx-14,ny+18,nx+14,ny+28,fill="#0a0000",outline="")
        c.create_rectangle(nx-6,ny+6,nx-2,ny+20,fill="#1a1a2a",outline="")
        c.create_rectangle(nx+2,ny+6,nx+6,ny+20,fill="#1a1a2a",outline="")
        c.create_rectangle(nx-11,ny-8,nx+11,ny+8,fill=body_col,outline=DARK,width=1)
        c.create_rectangle(nx-16,ny-6,nx-11,ny+3,fill=body_col,outline=DARK,width=1)
        c.create_rectangle(nx+11,ny-6,nx+16,ny+3,fill=body_col,outline=DARK,width=1)
        c.create_oval(nx-9,ny-24,nx+9,ny-8,fill=col,outline=DARK,width=1)
        c.create_rectangle(nx-13,ny-26,nx+13,ny-22,fill=hat_col,outline=DARK)
        c.create_rectangle(nx-9,ny-36,nx+9,ny-26,fill=hat_col,outline=DARK)
        c.create_text(nx,ny+34,text=npc["name"],fill=GOLD,font=self.fnt_small,anchor="center")

    def _draw_furniture(self,c,furn):
        fx1,fy1,fx2,fy2=furn["bounds"]; ftype=furn.get("type","table")
        mx=(fx1+fx2)//2; my=(fy1+fy2)//2; fw=fx2-fx1; fh=fy2-fy1

        if ftype=="felt_table":
            round_rect(c,fx1,fy1,fx2,fy2,r=20,fill=FELT,outline="#0a3015",width=3)
            round_rect(c,fx1+8,fy1+8,fx2-8,fy2-8,r=16,fill=FELT_L,outline="")
            c.create_text(mx,my,text=furn.get("label",""),fill="#2a5a2a",font=self.fnt_body)

        elif ftype=="counter":
            # Thick wooden counter with bevelled top edge and a dark underside
            c.create_rectangle(fx1+4,fy1+12,fx2-4,fy2+6,fill="#5a3a08",outline="",)   # shadow
            c.create_rectangle(fx1,fy1,fx2,fy2,fill="#8B6020",outline="#5a3a08",width=2)
            c.create_rectangle(fx1,fy1,fx2,fy1+14,fill="#a87830",outline="")           # lighter top
            c.create_line(fx1+2,fy1+14,fx2-2,fy1+14,fill="#6a4010",width=1)           # edge line
            # Vertical panel grooves every ~120px
            for px2 in range(fx1+120,fx2,120):
                c.create_line(px2,fy1+16,px2,fy2-4,fill="#6a4010",width=1)
            # Small gold trim strip along top
            c.create_line(fx1+4,fy1+4,fx2-4,fy1+4,fill=GOLD,width=1)

        elif ftype=="stool":
            # Bar stool: padded round seat, cross-brace legs, circular footrest
            sx,sy=mx,fy1; r=fw//2
            # Seat shadow
            c.create_oval(sx-r+3,sy+3,sx+r+3,sy+r//2+3,fill="#111",outline="")
            # Seat cushion (two-tone)
            c.create_oval(sx-r,sy,sx+r,sy+r//2,fill="#3a2200",outline="#6a4010",width=2)
            c.create_oval(sx-r+4,sy+3,sx+r-4,sy+r//2-3,fill="#4a2e0a",outline="")
            # Highlight on cushion
            c.create_arc(sx-r+6,sy+4,sx+r//2,sy+r//4+4,start=30,extent=120,
                         fill="",outline="#7a5820",width=1)
            # Four legs fanning out downward
            base_y=fy2; leg_spread=r-4
            for ang2 in [45,135,225,315]:
                ra=math.radians(ang2)
                lx=sx+int(leg_spread*math.cos(ra)); c.create_line(sx,sy+r//4,lx,base_y,fill="#5a3a10",width=3)
            # Circular footrest
            fr_y=(sy+r//4+base_y)//2+4
            c.create_oval(sx-r+8,fr_y-4,sx+r-8,fr_y+4,fill="#4a2e0a",outline="#6a4010",width=2)

        elif ftype=="plant":
            # Terracotta pot with soil, main stem, layered leaf clusters
            pw=max(fw//2,14); ph=fh
            pot_top=my+ph//6; pot_bot=fy2
            pot_w_top=pw-4; pot_w_bot=pw-10
            # Pot shadow
            c.create_oval(mx-pot_w_bot+3,pot_bot-6,mx+pot_w_bot+3,pot_bot+6,fill="#111",outline="")
            # Pot body (trapezoid via polygon)
            c.create_polygon(mx-pot_w_top,pot_top, mx+pot_w_top,pot_top,
                             mx+pot_w_bot,pot_bot, mx-pot_w_bot,pot_bot,
                             fill="#8B3010",outline="#6a2008",width=2)
            # Rim ring at top of pot
            c.create_oval(mx-pot_w_top,pot_top-5,mx+pot_w_top,pot_top+5,fill="#a03a14",outline="#6a2008",width=1)
            # Dark soil inside rim
            c.create_oval(mx-pot_w_top+4,pot_top-3,mx+pot_w_top-4,pot_top+3,fill="#2a1800",outline="")
            # Main stem
            stem_bot=pot_top-2; stem_top=fy1+ph//4
            c.create_line(mx,stem_bot,mx,stem_top,fill="#2a4a10",width=3)
            # Three branching stems
            for bx2,by2,bend in [(-pw+8,stem_top+ph//5,-1),(pw-8,stem_top+ph//5,1),(0,stem_top,0)]:
                c.create_line(mx,stem_top+ph//6,mx+bx2,by2,fill="#2a4a10",width=2)
            # Leaf clusters at different heights and sizes
            for lx2,ly2,lr,lc in [
                (mx-pw+6, fy1+ph//3,   pw-4, "#1a5a0a"),
                (mx+pw-6, fy1+ph//3,   pw-4, "#1e6a0c"),
                (mx,      fy1+ph//8,   pw,   "#2a7a18"),
                (mx-pw//2,fy1+ph//5+4, pw-8, "#248015"),
                (mx+pw//2,fy1+ph//5+4, pw-8, "#1c6a10"),
            ]:
                c.create_oval(lx2-lr//2,ly2-lr//3,lx2+lr//2,ly2+lr//3,fill=lc,outline="#0d3a08",width=1)
            # Highlight veins on top cluster
            c.create_line(mx,fy1+ph//8-lr//4,mx,fy1+ph//8+lr//4,fill="#3a9a20",width=1)

        elif ftype=="lamp":
            # Floor lamp: heavy cast base, slim pole, conical shade with inner glow
            bw=fw//2; pole_w=3
            base_y=fy2; shade_y=fy1; pole_top=shade_y+14
            # Cast base (3-tier)
            c.create_oval(mx-bw,base_y-6,mx+bw,base_y+6,fill="#1a1a1a",outline="#333",width=1)  # shadow pad
            c.create_oval(mx-bw+4,base_y-10,mx+bw-4,base_y+2,fill="#4a3a18",outline="#2a2008",width=2)
            c.create_oval(mx-bw+10,base_y-16,mx+bw-10,base_y-4,fill="#5a4820",outline="#3a3010",width=1)
            c.create_oval(mx-bw+16,base_y-22,mx+bw-16,base_y-10,fill="#6a5828",outline="#3a3010",width=1)
            # Pole
            c.create_rectangle(mx-pole_w,pole_top,mx+pole_w,base_y-20,fill="#7a6030",outline="#5a4020",width=1)
            # Highlight stripe on pole
            c.create_line(mx+1,pole_top+4,mx+1,base_y-24,fill="#9a8040",width=1)
            # Pole finial (small ball at top)
            c.create_oval(mx-4,pole_top-4,mx+4,pole_top+4,fill="#8B6914",outline=GOLD,width=1)
            # Shade (conical polygon)
            sw=bw+4
            c.create_polygon(mx,shade_y, mx-sw,shade_y+fh//3, mx+sw,shade_y+fh//3,
                             fill="#c8a040",outline="#8B6010",width=2)
            # Inner shade (slightly smaller, lighter)
            c.create_polygon(mx,shade_y+4, mx-sw+6,shade_y+fh//3-2, mx+sw-6,shade_y+fh//3-2,
                             fill="#e0b84a",outline="")
            # Glow ellipse under shade
            c.create_oval(mx-sw+8,shade_y+fh//3-6,mx+sw-8,shade_y+fh//3+10,
                          fill="#ffee88",outline="#e0c050",width=1)
            # Shade rim detail line
            c.create_line(mx-sw,shade_y+fh//3,mx+sw,shade_y+fh//3,fill="#8B6010",width=2)

        elif ftype=="cabinet":
            # Wooden cabinet: frame, two door panels, hinges, handles, top trim
            # Drop shadow
            c.create_rectangle(fx1+5,fy1+5,fx2+5,fy2+5,fill="#111",outline="")
            # Main body
            c.create_rectangle(fx1,fy1,fx2,fy2,fill="#2e1c08",outline="#1a0e04",width=2)
            # Top trim rail
            c.create_rectangle(fx1,fy1,fx2,fy1+10,fill="#4a2e10",outline="#2a1a08",width=1)
            c.create_line(fx1+2,fy1+10,fx2-2,fy1+10,fill="#6a4820",width=1)
            # Bottom base rail
            c.create_rectangle(fx1,fy2-10,fx2,fy2,fill="#4a2e10",outline="#2a1a08",width=1)
            # Centre divider
            c.create_rectangle(mx-2,fy1+10,mx+2,fy2-10,fill="#1a0e04",outline="")
            # Left door panel
            lp_x1,lp_x2=fx1+6,mx-4
            c.create_rectangle(lp_x1,fy1+16,lp_x2,fy2-12,fill="#3a2210",outline="#5a3818",width=1)
            # Left panel inset bevel
            c.create_rectangle(lp_x1+4,fy1+20,lp_x2-4,fy2-16,fill="#2a1a0c",outline="#4a2e18",width=1)
            # Right door panel
            rp_x1,rp_x2=mx+4,fx2-6
            c.create_rectangle(rp_x1,fy1+16,rp_x2,fy2-12,fill="#3a2210",outline="#5a3818",width=1)
            c.create_rectangle(rp_x1+4,fy1+20,rp_x2-4,fy2-16,fill="#2a1a0c",outline="#4a2e18",width=1)
            # Hinges (left side of each door)
            for hinge_y in [fy1+22,fy2-26]:
                for hx2 in [lp_x1+1,rp_x1+1]:
                    c.create_rectangle(hx2,hinge_y,hx2+6,hinge_y+8,fill="#8B6914",outline=GOLD,width=1)
            # Handles (gold knobs on inside edge of each door)
            handle_y=my
            c.create_oval(lp_x2-10,handle_y-5,lp_x2-2,handle_y+5,fill=GOLD,outline="#8B6914",width=1)
            c.create_oval(rp_x1+2,handle_y-5,rp_x1+10,handle_y+5,fill=GOLD,outline="#8B6914",width=1)
            # Wood grain lines (subtle)
            for gy2 in range(fy1+26,fy2-14,18):
                c.create_line(lp_x1+6,gy2,lp_x2-6,gy2,fill="#2a1808",width=1)
                c.create_line(rp_x1+6,gy2,rp_x2-6,gy2,fill="#2a1808",width=1)

    def _check_npc_proximity(self):
        room=self.int_rooms.get(self.int_room,{}); self.nearby_npc=None
        for npc in room.get("npcs",[]):
            if math.hypot(self.int_px-npc["x"],self.int_py-npc["y"])<220:
                self.nearby_npc=npc; break

    def _check_door_proximity(self):
        if time.time()<self._int_door_cooldown: return
        room=self.int_rooms.get(self.int_room,{})
        pr=18
        for door in room.get("doors",[]):
            dx2,dy2,dw,dh=door["x"],door["y"],door["w"],door["h"]
            if dx2-pr<=self.int_px<=dx2+dw+pr and dy2-pr<=self.int_py<=dy2+dh+pr:
                if door["to"]=="exit":
                    self._exit_interior()
                else:
                    # Check if door requires room ownership
                    lock=door.get("locked")
                    if lock:
                        owned=getattr(self,"hotel_owned_rooms",{})
                        if lock not in owned:
                            self._msg("You need to buy this room first!",RED_C); return
                    self._int_door_cooldown=time.time()+0.8
                    self.int_room=door["to"]
                    # spawn in middle of destination room, well away from its walls/doors
                    self.int_px=W//2; self.int_py=430
                    self.nearby_npc=None; self.npc_dialogue=""
                return

    def _try_interact(self):
        if not self.nearby_npc: return
        npc=self.nearby_npc; self.npc_dialogue=npc.get("line",""); self.dial_timer=90
        game=npc.get("game")
        if not game: return
        # Hard-cancel the interior loop FIRST so its next draw never clobbers game widgets
        if self._interior_loop_id:
            try: self.after_cancel(self._interior_loop_id)
            except: pass
            self._interior_loop_id=None
        self.screen="game"
        game_map={
            "blackjack":self._blackjack_screen,"roulette":self._roulette_screen,
            "slots":self._slots_screen,"craps":self._craps_screen,
            "war":self._war_screen,"high_card":self._high_card_screen,
            "horse_race":self._horse_race_screen,"dice_roll":self._dice_roll_screen,
            "texas_holdem":self._texas_holdem_screen,"yahtzee":self._yahtzee_screen,
            "shady_deal":self._shady_screen,"vip_menu":self._vip_screen,
            "vip_double":self._vip_double_screen,"vip_bj":self._vip_high_stakes_bj,
            "vip_poker":lambda:self._texas_holdem_screen(vip=True),"vip_roulette":self._vip_golden_roulette,
            "shop_screen":self._shop_screen,
            "change_skin":self._change_skin_screen,
            "den_shop":self._den_shop_screen,
            "atm_screen":self._atm_screen,
            "bank_stats":self._bank_screen,"arena_fight":self._arena_fight_screen,
            "arena_bet":self._arena_bet_screen,"arena_restaurant":self._arena_restaurant_screen,
            "dojo_train":self._dojo_train_screen,"hotel_checkin":self._hotel_checkin_screen,"hotel_raffle":self._hotel_raffle_screen,
            "hotel_tv":self._hotel_tv_screen,
            "start_heist":self._heist_start,
            **{f"gumball_{r}":(lambda: (self._clear_overlay(), self._gumball_screen())[-1]) for r in ["common","uncommon","rare","epic","legendary","mythic"]},
            "gumball":lambda:(self._clear_overlay(), self._gumball_screen())[-1],
            "figurine_table_f2":lambda:self._figurine_table_screen(2),
            "figurine_table_f3":lambda:self._figurine_table_screen(3),
        }
        fn=game_map.get(game)
        if fn: self._clear_overlay(); fn()

    # ── ROOM DEFINITIONS ─────────────────────────────────
    def _make_casino_rooms(self):
        def lobby_decor(c):
            c.create_rectangle(W//2-80,60,W//2+80,H-30,fill="#5a0000",outline="")
            c.create_rectangle(W//2-68,60,W//2+68,H-30,fill="#8B0000",outline="")
            c.create_line(W//2-68,60,W//2-68,H-30,fill=GOLD,width=2)
            c.create_line(W//2+68,60,W//2+68,H-30,fill=GOLD,width=2)
        def bj_decor(c):
            # Rich wood-panelled walls
            for wx2 in range(0,W,80):
                c.create_rectangle(wx2,65,wx2+78,H-30,fill="#1a0c04" if (wx2//80)%2==0 else "#150a02",outline="#0a0600",width=1)
            # Gold chair rail along walls
            c.create_line(0,500,W,500,fill="#8B6914",width=3)
            c.create_line(0,503,W,503,fill="#5a4010",width=1)
            # Wainscoting panels (lower wall detail)
            for wx2 in range(8,W-8,90):
                c.create_rectangle(wx2,505,wx2+84,H-35,fill="#120800",outline="#3a2010",width=1)
                c.create_rectangle(wx2+6,511,wx2+78,H-41,fill="#0e0600",outline="#2a1808",width=1)
            # Ceiling coffers (decorative grid)
            for cx2 in range(0,W,120):
                c.create_rectangle(cx2,65,cx2+118,180,fill="#0d0600",outline="#3a2010",width=1)
                c.create_rectangle(cx2+8,73,cx2+110,172,fill="#120800",outline="#2a1808",width=1)
            # Central felt table — proper D-shape blackjack table
            tx1,ty1,tx2,ty2 = W//2-220,245,W//2+220,400
            # Table shadow
            c.create_oval(tx1+8,ty2-10,tx2+8,ty2+18,fill="#0a0600",outline="")
            # Outer rim (padded leather rail)
            round_rect(c,tx1-12,ty1-10,tx2+12,ty2+12,r=32,fill="#3a1a00",outline="#2a1000",width=3)
            # Felt surface
            round_rect(c,tx1,ty1,tx2,ty2,r=28,fill="#0d5c1e",outline="#0a3a14",width=3)
            round_rect(c,tx1+8,ty1+8,tx2-8,ty2-8,r=24,fill="#0f6622",outline="")
            # Betting circle arcs for 5 player positions
            for i in range(5):
                angle_frac=(i+0.5)/5; bx2=int(tx1+(tx2-tx1)*angle_frac); by2=ty2-18
                c.create_oval(bx2-18,by2-12,bx2+18,by2+12,fill="",outline="#1a8830",width=2)
                c.create_text(bx2,by2,text=str(i+1),fill="#1a8830",font=tkfont.Font(family="Courier New",size=8))
            # Insurance line
            c.create_line(tx1+30,ty1+45,tx2-30,ty1+45,fill="#1a8830",width=1,dash=(4,4))
            c.create_text(W//2,ty1+36,text="INSURANCE PAYS 2:1",fill="#1a8830",font=tkfont.Font(family="Courier New",size=9))
            c.create_text(W//2,ty1+60,text="BLACKJACK PAYS 3 : 2",fill="#1a8830",font=tkfont.Font(family="Courier New",size=11,weight="bold"))
            c.create_text(W//2,ty1+80,text="DEALER MUST DRAW TO 16 AND STAND ON ALL 17's",fill="#1a8830",font=tkfont.Font(family="Courier New",size=8))
            # Chip tray slot in front of dealer
            c.create_rectangle(W//2-50,ty1+6,W//2+50,ty1+22,fill="#0a0000",outline="#5a4010",width=1)
            for ci,cc in enumerate(["#cc2200","#2288cc","#22aa44","#aaaaaa","#1a1a1a"]):
                cx3=W//2-36+ci*18; c.create_oval(cx3-7,ty1+8,cx3+7,ty1+20,fill=cc,outline="#111",width=1)
            # Ornate wall sconces (left & right)
            for sx2 in [50,W-50]:
                # Backplate
                c.create_rectangle(sx2-14,82,sx2+14,160,fill="#3a2008",outline="#8B6914",width=2)
                c.create_rectangle(sx2-10,86,sx2+10,100,fill="#5a3010",outline="")
                # Arm
                c.create_line(sx2,160,sx2+(-20 if sx2<W//2 else 20),188,fill="#8B6914",width=4)
                # Glass globe
                arm_tip_x=sx2+(-20 if sx2<W//2 else 20)
                c.create_oval(arm_tip_x-14,178,arm_tip_x+14,210,fill="#ffeeaa",outline="#d4a820",width=2)
                c.create_oval(arm_tip_x-9,183,arm_tip_x+9,205,fill="#fff8cc",outline="")
                # Glow halo
                c.create_oval(arm_tip_x-22,172,arm_tip_x+22,216,fill="",outline="#8B6914",width=1)
            # Grand chandelier above table
            ch_x,ch_y=W//2,135
            c.create_line(ch_x,65,ch_x,ch_y-18,fill="#8B6914",width=4)
            # Chandelier arms radiating out
            for i in range(8):
                a=math.radians(i*45)
                ex=ch_x+int(44*math.cos(a)); ey=ch_y+int(18*math.sin(a))
                c.create_line(ch_x,ch_y,ex,ey,fill="#8B6914",width=3)
                c.create_oval(ex-7,ey-10,ex+7,ey+6,fill="#ffee88",outline="#d4a820",width=1)
                c.create_oval(ex-4,ey-7,ex+4,ey+3,fill="#fffacc",outline="")
            c.create_oval(ch_x-12,ch_y-12,ch_x+12,ch_y+12,fill="#d4a820",outline="#8B6914",width=2)
            # Framed card-suit paintings on rear wall
            for px3,suit,sc in [(180,u"♠","#f0e8d0"),(W-180,u"♥","#cc2200")]:
                c.create_rectangle(px3-34,80,px3+34,168,fill="#1a0e04",outline="#8B6914",width=3)
                c.create_rectangle(px3-28,86,px3+28,162,fill="#0e0800",outline="#5a3810",width=1)
                c.create_text(px3,124,text=suit,fill=sc,font=tkfont.Font(size=38))
            # Player stools along bottom of table
            for i in range(5):
                sx3=int(tx1+22+(tx2-tx1-44)*i/4); sy3=ty2+14
                # Stool cushion
                c.create_oval(sx3-16,sy3,sx3+16,sy3+10,fill="#3a1a00",outline="#7a4a10",width=2)
                c.create_oval(sx3-12,sy3+2,sx3+12,sy3+8,fill="#4a2a08",outline="")
                # Legs
                for lx3 in [sx3-10,sx3+10]:
                    c.create_line(lx3,sy3+10,lx3+(-3 if lx3<sx3 else 3),sy3+36,fill="#5a3a10",width=3)
                # Footrest
                c.create_line(sx3-14,sy3+26,sx3+14,sy3+26,fill="#3a2008",width=2)
            # Plush carpet strip in front of table
            c.create_rectangle(tx1-20,ty2+52,tx2+20,ty2+72,fill="#2a0010",outline="#5a0030",width=1)
            for px4 in range(tx1,tx2,18):
                c.create_oval(px4,ty2+54,px4+12,ty2+70,fill="#3a0018",outline="")
            # Corner plants (ornate pots)
            for px5,py5 in [(60,450),(W-60,450)]:
                c.create_polygon(px5-16,py5+30,px5+16,py5+30,px5+12,py5+58,px5-12,py5+58,fill="#6a3010",outline="#4a2008",width=2)
                c.create_oval(px5-16,py5+22,px5+16,py5+36,fill="#8B4010",outline="#5a2808",width=1)
                c.create_oval(px5-4,py5+26,px5+4,py5+32,fill="#5a2808",outline="")
                # Foliage
                for la,lr2,lc2 in [(-20,20,"#1a5a0a"),(0,22,"#1f6a0c"),(20,20,"#1a5a0a"),(-10,16,"#145208"),(10,16,"#145208")]:
                    c.create_oval(px5+la-lr2//2,py5-lr2//2,px5+la+lr2//2,py5+lr2//2,fill=lc2,outline="#0d3a08",width=1)
        def rou_decor(c):
            wx,wy,wr=240,300,110; RED_N={1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
            c.create_oval(wx-wr-12,wy-wr-12,wx+wr+12,wy+wr+12,fill="#5a3010",outline=GOLD,width=4)
            for i in range(37):
                ang=(i/37)*360; col="#006000" if i==0 else("#c0392b" if i in RED_N else "#1a1a1a")
                c.create_arc(wx-wr,wy-wr,wx+wr,wy+wr,start=ang,extent=360/37,fill=col,outline="white",width=1,style="pie")
            c.create_oval(wx-18,wy-18,wx+18,wy+18,fill=GOLD,outline=DARK,width=2)
            round_rect(c,430,180,W-30,430,r=12,fill=FELT,outline="#0a3015",width=3)
            # Betting chip trays on side wall
            for ty in [200,280,360]:
                c.create_rectangle(W-28,ty,W-4,ty+60,fill="#2a1000",outline=GOLD,width=1)
                for cy in range(ty+8,ty+56,16):
                    c.create_oval(W-24,cy,W-8,cy+12,fill=["#cc2200","#1a88cc","#22aa44"][ty//80%3],outline="#111",width=1)
            # Bar stools around betting table
            for sx2 in [450,540,630,720,810,900,990]:
                c.create_oval(sx2-10,435,sx2+10,455,fill="#2a1a00",outline="#6a4a10",width=1)
            # Chandelier
            c.create_line(W//2+200,60,W//2+200,115,fill="#8B6914",width=3)
            c.create_oval(W//2+170,108,W//2+230,138,fill="#ffdd44",outline=GOLD,width=2)
        def slots_decor(c):
            for i,sx2 in enumerate([200,W//2,W-200]):
                round_rect(c,sx2-60,155,sx2+60,410,r=16,fill="#1a0040",outline=PURPLE,width=4)
                round_rect(c,sx2-50,168,sx2+50,296,r=10,fill="#000033",outline=GOLD,width=2)
                c.create_text(sx2,232,text=["🍒","💎","7"][i],fill=GOLD,font=tkfont.Font(size=34))
            # Coin trays below machines
            for sx2 in [200,W//2,W-200]:
                c.create_rectangle(sx2-40,410,sx2+40,430,fill="#5a4010",outline=GOLD,width=1)
            # Bar stools
            for sx2 in [200,W//2,W-200]:
                c.create_oval(sx2-14,438,sx2+14,458,fill="#2a1a00",outline="#6a4a10",width=2)
                c.create_line(sx2-8,458,sx2-10,480,fill="#4a2a00",width=2)
                c.create_line(sx2+8,458,sx2+10,480,fill="#4a2a00",width=2)
            # Neon sign at top
            c.create_rectangle(W//2-140,68,W//2+140,100,fill="#0d0028",outline=PURPLE,width=2)
            c.create_text(W//2,84,text="✦  SLOTS  ✦",fill=PURPLE,font=tkfont.Font(family="Courier New",size=13,weight="bold"))
            # Carpet pattern
            for cx2 in range(80,W-60,200):
                c.create_oval(cx2-20,490,cx2+20,520,fill="#0d0028",outline=PURPLE,width=1)
        def craps_decor(c):
            # Dark brick walls with mortar lines
            for row in range(9):
                ry=65+row*64; off=(row%2)*44
                for cx4 in range(-off,W+88,88):
                    c.create_rectangle(cx4,ry,cx4+84,ry+60,fill="#1a0c08" if row%2==0 else "#160a06",outline="#0a0604",width=1)
                    c.create_rectangle(cx4+3,ry+3,cx4+81,ry+57,fill="#1e1008",outline="")
            # Neon "CRAPS" sign on back wall
            c.create_rectangle(W//2-130,72,W//2+130,112,fill="#050505",outline="#004488",width=3)
            c.create_rectangle(W//2-126,76,W//2+126,108,fill="#000a18",outline="#0066cc",width=1)
            c.create_text(W//2,90,text="C R A P S",fill="#00aaff",font=tkfont.Font(family="Courier New",size=18,weight="bold"))
            # Glow effect under sign
            c.create_rectangle(W//2-100,108,W//2+100,120,fill="#001a33",outline="")
            # Main craps table — proper elongated boat shape
            tx1,ty1,tx2,ty2=60,155,W-60,430
            tw=tx2-tx1
            # Table shadow
            c.create_rectangle(tx1+6,ty2,tx2+6,ty2+16,fill="#050302",outline="")
            # Padded outer rail (thick leather bumper)
            round_rect(c,tx1-10,ty1-10,tx2+10,ty2+10,r=22,fill="#2a1a00",outline="#1a0e00",width=4)
            round_rect(c,tx1-4,ty1-4,tx2+4,ty2+4,r=18,fill="#3a2400",outline="#5a3a00",width=2)
            # Felt surface
            round_rect(c,tx1,ty1,tx2,ty2,r=16,fill="#0a3050",outline="#063040",width=2)
            # Divider walls (centre pyramid box area)
            mid=W//2
            c.create_rectangle(mid-40,ty1+4,mid+40,ty2-4,fill="#083040",outline="#104060",width=1)
            c.create_text(mid,ty1+30,text="ANY\nSEVEN",fill="#cc4400",font=tkfont.Font(family="Courier New",size=9,weight="bold"),justify="center")
            c.create_text(mid,ty1+75,text="ANY\nCRAPS",fill="#cc4400",font=tkfont.Font(family="Courier New",size=9,weight="bold"),justify="center")
            c.create_text(mid,ty1+118,text="C&E",fill="#cc6600",font=tkfont.Font(family="Courier New",size=10,weight="bold"))
            c.create_text(mid,ty1+150,text="HARD\nWAYS",fill="#888",font=tkfont.Font(family="Courier New",size=9),justify="center")
            # Left side layout
            lx1,lx2=tx1+4,mid-46
            # Pass line (big box at bottom)
            c.create_rectangle(lx1+4,ty2-42,lx2-4,ty2-6,fill="#0e4a70",outline="#1a7aaa",width=2)
            c.create_text((lx1+lx2)//2,ty2-24,text="P A S S  L I N E",fill="#88ccee",font=tkfont.Font(family="Courier New",size=12,weight="bold"))
            # Don't Pass bar
            c.create_rectangle(lx1+4,ty2-68,lx2-4,ty2-46,fill="#083040",outline="#0a4060",width=1)
            c.create_text((lx1+lx2)//2,ty2-57,text="DON'T PASS BAR",fill="#4a88aa",font=tkfont.Font(family="Courier New",size=9))
            # Come / Don't Come
            c.create_rectangle(lx2-80,ty1+6,lx2-4,ty1+56,fill="#0e3a50",outline="#1a6080",width=1)
            c.create_text(lx2-42,ty1+31,text="COME",fill="#88ccee",font=tkfont.Font(family="Courier New",size=10,weight="bold"))
            # Field
            c.create_rectangle(lx1+4,ty1+60,lx2-84,ty1+108,fill="#083848",outline="#0a5068",width=1)
            c.create_text((lx1+4+lx2-84)//2,ty1+84,text="FIELD\n3 4 9 10 11",fill="#aaccdd",font=tkfont.Font(family="Courier New",size=8),justify="center")
            # Place numbers box (4,5,6,8,9,10)
            bw2=(lx2-4-(lx1+4))//6
            for ni,num in enumerate([4,5,6,8,9,10]):
                bx4=lx1+4+ni*bw2
                bc="#1a4060" if num in [6,8] else "#0e3040"
                c.create_rectangle(bx4,ty1+112,bx4+bw2-2,ty1+158,fill=bc,outline="#1a5070",width=1)
                c.create_text(bx4+bw2//2,ty1+135,text=str(num),fill="#88ccee",font=tkfont.Font(family="Courier New",size=11,weight="bold"))
            # Mirror layout on right side
            rx1,rx2=mid+46,tx2-4
            c.create_rectangle(rx1+4,ty2-42,rx2-4,ty2-6,fill="#0e4a70",outline="#1a7aaa",width=2)
            c.create_text((rx1+rx2)//2,ty2-24,text="P A S S  L I N E",fill="#88ccee",font=tkfont.Font(family="Courier New",size=12,weight="bold"))
            c.create_rectangle(rx1+4,ty2-68,rx2-4,ty2-46,fill="#083040",outline="#0a4060",width=1)
            c.create_text((rx1+rx2)//2,ty2-57,text="DON'T PASS BAR",fill="#4a88aa",font=tkfont.Font(family="Courier New",size=9))
            c.create_rectangle(rx1+4,ty1+6,rx1+80,ty1+56,fill="#0e3a50",outline="#1a6080",width=1)
            c.create_text(rx1+42,ty1+31,text="COME",fill="#88ccee",font=tkfont.Font(family="Courier New",size=10,weight="bold"))
            c.create_rectangle(rx1+84,ty1+60,rx2-4,ty1+108,fill="#083848",outline="#0a5068",width=1)
            c.create_text((rx1+84+rx2-4)//2,ty1+84,text="FIELD\n3 4 9 10 11",fill="#aaccdd",font=tkfont.Font(family="Courier New",size=8),justify="center")
            bw3=(rx2-4-(rx1+4))//6
            for ni,num in enumerate([4,5,6,8,9,10]):
                bx5=rx1+4+ni*bw3
                bc="#1a4060" if num in [6,8] else "#0e3040"
                c.create_rectangle(bx5,ty1+112,bx5+bw3-2,ty1+158,fill=bc,outline="#1a5070",width=1)
                c.create_text(bx5+bw3//2,ty1+135,text=str(num),fill="#88ccee",font=tkfont.Font(family="Courier New",size=11,weight="bold"))
            # Chip rail along top edge of table
            c.create_rectangle(tx1,ty1-4,tx2,ty1+4,fill="#1a0e00",outline="#3a2000",width=1)
            for rx3 in range(tx1+20,tx2-10,28):
                chip_col=["#cc2200","#2288cc","#22aa44","#aaa","#111","#aa8800"][rx3%6]
                c.create_oval(rx3-8,ty1-12,rx3+8,ty1+4,fill=chip_col,outline="#111",width=1)
                c.create_line(rx3-8,ty1-4,rx3+8,ty1-4,fill="#333",width=1)
            # Puck (on/off)
            c.create_oval(tx1+16,ty1+8,tx1+40,ty1+32,fill="#f0f0f0",outline="#aaa",width=2)
            c.create_text(tx1+28,ty1+20,text="OFF",fill="#cc0000",font=tkfont.Font(family="Courier New",size=8,weight="bold"))
            # Stickman box
            c.create_rectangle(mid-28,ty2-4,mid+28,ty2+18,fill="#0a2030",outline="#1a5070",width=1)
            c.create_text(mid,ty2+7,text="STICK",fill="#4a88aa",font=tkfont.Font(family="Courier New",size=8))
            # Decorative dice on side walls
            for ddx,ddy,v1,v2 in [(28,260,5,3),(28,330,2,6),(W-28,260,4,1),(W-28,330,6,2)]:
                c.create_rectangle(ddx-16,ddy-16,ddx+16,ddy+16,fill="#f5f5ee",outline="#888",width=2)
                c.create_rectangle(ddx-14,ddy-14,ddx+14,ddy+14,fill="#ffffff",outline="")
                pips={1:[(0,0)],2:[(-5,-5),(5,5)],3:[(-5,-5),(0,0),(5,5)],
                      4:[(-5,-5),(5,-5),(-5,5),(5,5)],5:[(-5,-5),(5,-5),(0,0),(-5,5),(5,5)],
                      6:[(-5,-6),(5,-6),(-5,0),(5,0),(-5,6),(5,6)]}
                for ppx,ppy in pips.get(v1,[]):
                    c.create_oval(ddx+ppx-3,ddy+ppy-3,ddx+ppx+3,ddy+ppy+3,fill="#1a1a1a",outline="")
            # Player stools along both long sides
            for sx4 in range(tx1+30,tx2-10,55):
                # Bottom side stools
                c.create_oval(sx4-13,ty2+12,sx4+13,ty2+24,fill="#2a1a00",outline="#7a4a10",width=2)
                c.create_oval(sx4-9,ty2+14,sx4+9,ty2+22,fill="#3a2a08",outline="")
                for lx4 in [sx4-9,sx4+9]:
                    c.create_line(lx4,ty2+24,lx4+(-2 if lx4<sx4 else 2),ty2+44,fill="#5a3a10",width=2)
                c.create_line(sx4-12,ty2+36,sx4+12,ty2+36,fill="#3a2008",width=2)
            # Wall-mounted chip trays
            for wx3 in [8,W-50]:
                c.create_rectangle(wx3,200,wx3+40,380,fill="#1a0e00",outline="#3a2000",width=2)
                c.create_rectangle(wx3+3,203,wx3+37,208,fill="#3a2000",outline="")
                for cy5 in range(212,376,24):
                    for ci2,cc2 in enumerate(["#cc2200","#2288cc","#22aa44"]):
                        c.create_oval(wx3+5+ci2*11,cy5,wx3+14+ci2*11,cy5+18,fill=cc2,outline="#111",width=1)
                        c.create_line(wx3+5+ci2*11,cy5+6,wx3+14+ci2*11,cy5+6,fill="#333",width=1)
        def poker_decor(c):
            round_rect(c,W//2-210,210,W//2+210,400,r=34,fill=FELT,outline="#0a3015",width=4)
            round_rect(c,W//2-200,218,W//2+200,392,r=30,fill=FELT_L,outline="")
            c.create_text(W//2,245,text="TEXAS  HOLD'EM  —  3 Players",fill="#2a5a2a",font=tkfont.Font(family="Courier New",size=11))
            # Player seats around table
            for ang2 in [0,60,120,180,240,300]:
                ra=math.radians(ang2); sx2=W//2+int(230*math.cos(ra)); sy2=305+int(110*math.sin(ra))
                c.create_oval(sx2-12,sy2-8,sx2+12,sy2+8,fill="#2a1a00",outline="#6a4a10",width=2)
            # Wall paintings
            for wx2 in [60,W-60]:
                c.create_rectangle(wx2-24,160,wx2+24,230,fill="#1a0a00",outline=GOLD,width=2)
                c.create_rectangle(wx2-20,164,wx2+20,226,fill="#2a1800",outline="")
                c.create_text(wx2,195,text="♠",fill=GOLD,font=tkfont.Font(size=26))
            # Side tables
            for stx in [80,W-80]:
                c.create_rectangle(stx-28,440,stx+28,480,fill="#4a3010",outline="#8B6914",width=2)
                c.create_oval(stx-20,430,stx+20,448,fill="#5a3a18",outline=GOLD,width=1)
        def yah_decor(c):
            round_rect(c,W//2-180,155,W//2+180,420,r=18,fill="#1a1a00",outline="#5a5a00",width=3)
            c.create_text(W//2,195,text="Y A H T Z E E",fill="#aaa800",font=tkfont.Font(family="Courier New",size=16,weight="bold"))
            # Dice cup display on side
            c.create_rectangle(120,220,176,290,fill="#3a3000",outline=GOLD,width=2)
            c.create_oval(126,226,170,284,fill="#2a2800",outline="#8B8000",width=1)
            c.create_text(148,258,text="🎲",font=tkfont.Font(size=22))
            # Score sheets on wall (shelves)
            for sy2 in [180,240,300]:
                c.create_rectangle(W-130,sy2,W-30,sy2+50,fill="#1a1a08",outline="#4a4a20",width=1)
                for row in range(4): c.create_line(W-128,sy2+8+row*10,W-32,sy2+8+row*10,fill="#333300",width=1)
            # Player chairs
            for cx2 in [W//2-220,W//2+220]:
                c.create_rectangle(cx2-22,330,cx2+22,380,fill="#2a2a00",outline="#5a5a00",width=2)
                c.create_rectangle(cx2-22,310,cx2+22,334,fill="#3a3a00",outline="#5a5a00",width=1)
            # Trophy shelf
            c.create_rectangle(60,440,200,480,fill="#2a2000",outline=GOLD,width=1)
            for tx2 in [90,130,170]:
                c.create_rectangle(tx2-8,420,tx2+8,444,fill="#8B6914",outline=GOLD,width=1)
                c.create_oval(tx2-10,412,tx2+10,424,fill="#aaa000",outline=GOLD,width=1)
        def dice_decor(c):
            round_rect(c,W//2-180,168,W//2+180,410,r=18,fill=FELT,outline="#0a3015",width=3)
            c.create_text(W//2,210,text="DICE  ROLL  — Roll vs. Dealer",fill="#2a5a2a",font=tkfont.Font(family="Courier New",size=11))
            # Giant decorative dice on walls
            for dx2,dy2 in [(100,240),(W-100,240)]:
                c.create_rectangle(dx2-30,dy2-30,dx2+30,dy2+30,fill="#f0f0f0",outline="#333",width=3)
                for dpx,dpy in [(-14,-14),(0,-14),(14,-14),(-14,0),(14,0),(-14,14),(0,14)]:
                    c.create_oval(dx2+dpx-4,dy2+dpy-4,dx2+dpx+4,dy2+dpy+4,fill="#1a1a1a")
            # Side shelves with dice sets
            for sy2 in [380,440,490]:
                c.create_rectangle(40,sy2,140,sy2+36,fill="#1a3010",outline="#2a5a20",width=1)
                for sdx in [60,90,120]:
                    c.create_rectangle(sdx-8,sy2+6,sdx+8,sy2+24,fill="#f0f0f0",outline="#555",width=1)
                    c.create_oval(sdx-3,sy2+12,sdx+3,sy2+18,fill="#111")
            # Player stools
            for sx2 in [W//2-120,W//2,W//2+120]:
                c.create_oval(sx2-13,418,sx2+13,436,fill="#2a1a00",outline="#6a4a10",width=2)
                c.create_line(sx2,436,sx2,460,fill="#4a2a00",width=3)

        # Door layout: top wall y=65 h=34 | bottom wall y=638 h=34
        #              left wall x=0 w=80 | right wall x=W-80 w=80
        lobby_doors=[
            {"to":"bj",   "x":100, "y":65,    "w":160,"h":34,"col":"#1a0000","label":"Blackjack"},
            {"to":"rou",  "x":840, "y":65,    "w":160,"h":34,"col":"#001a00","label":"Roulette"},
            {"to":"slots","x":0,   "y":200,   "w":80, "h":50,"col":"#0d0020","label":"Slots"},
            {"to":"craps","x":0,   "y":280,   "w":80, "h":50,"col":"#001020","label":"Craps"},
            {"to":"yah",  "x":0,   "y":360,   "w":80, "h":50,"col":"#1a1a00","label":"Yahtzee"},
            {"to":"dice", "x":0,   "y":440,   "w":80, "h":50,"col":"#001a0a","label":"Dice Roll"},
            {"to":"war",  "x":W-80,"y":200,   "w":80, "h":50,"col":"#1a0800","label":"War"},
            {"to":"hcard","x":W-80,"y":280,   "w":80, "h":50,"col":"#001a1a","label":"High Card"},
            {"to":"poker","x":W-80,"y":360,   "w":80, "h":50,"col":"#001a00","label":"Hold'em"},
            {"to":"exit", "x":460, "y":638,   "w":180,"h":34,"col":"#111",   "label":"Exit Casino"},
        ]
        # Back-to-lobby door is at the bottom wall; player spawns mid-lobby away from wall doors
        BACK={"to":"lobby","x":460,"y":638,"w":180,"h":34,"col":"#333","label":"Back to Lobby"}
        def war_furniture():
            return [
                {"type":"felt_table","bounds":(W//2-160,230,W//2+160,390),"label":"WAR"},
                {"type":"stool","bounds":(W//2-200,400,W//2-170,425),"label":""},
                {"type":"stool","bounds":(W//2+170,400,W//2+200,425),"label":""},
                {"type":"plant","bounds":(60,440,110,500),"label":""},
                {"type":"plant","bounds":(W-110,440,W-60,500),"label":""},
                {"type":"cabinet","bounds":(50,200,110,320),"label":""},
                {"type":"cabinet","bounds":(W-110,200,W-50,320),"label":""},
            ]
        def hcard_furniture():
            return [
                {"type":"felt_table","bounds":(W//2-150,240,W//2+150,390),"label":"HIGH CARD"},
                {"type":"stool","bounds":(W//2-190,400,W//2-160,425),"label":""},
                {"type":"stool","bounds":(W//2+160,400,W//2+190,425),"label":""},
                {"type":"lamp","bounds":(70,160,110,260),"label":""},
                {"type":"lamp","bounds":(W-110,160,W-70,260),"label":""},
                {"type":"plant","bounds":(60,430,110,490),"label":""},
                {"type":"plant","bounds":(W-110,430,W-60,490),"label":""},
            ]
        return {
            "lobby":{"title":"Royal Casino — Grand Lobby","floor":"#2a1200","wall":"#1a0800",
                     "decor_fn":lobby_decor,"furniture":[],"doors":lobby_doors,
                     "npcs":[{"id":"host","x":W//2,"y":340,"name":"Casino Host",
                               "col":"#e8c07a","hat_col":"#8B0000","body_col":"#1a3a6a",
                               "line":"Doors around the room\nlead to every game!","game":None}]},
            "bj":   {"title":"Blackjack Hall","floor":"#0d1a08","wall":"#060d04","decor_fn":bj_decor,
                     "furniture":[{"type":"felt_table","bounds":(W//2-200,230,W//2+200,390),"label":""}],
                     "doors":[BACK],
                     "npcs":[{"id":"dealer_bj","x":W//2,"y":248,"name":"Dealer Rosa","col":"#d0b080",
                               "hat_col":DARK,"body_col":"#1a1a2a","line":"Place chips then DEAL!","game":"blackjack"}]},
            "rou":  {"title":"Roulette Room","floor":"#060d00","wall":"#030800","decor_fn":rou_decor,
                     "furniture":[],"doors":[BACK],
                     "npcs":[{"id":"croupier","x":700,"y":290,"name":"Croupier Max","col":"#c8b090",
                               "hat_col":"#2a2a3a","body_col":"#1a3a00","line":"Pick colour & number,\nplace chips then DEAL!","game":"roulette"}]},
            "slots":{"title":"Slots Corner","floor":"#0d0028","wall":"#080018","decor_fn":slots_decor,
                     "furniture":[],"doors":[BACK],
                     "npcs":[{"id":"attendant","x":W//2,"y":460,"name":"Attendant Lily","col":"#e0b898",
                               "hat_col":PURPLE,"body_col":PURPLE,"line":"Place chips then DEAL to spin.","game":"slots"}]},
            "craps":{"title":"Craps Table","floor":"#000a1a","wall":"#00060e","decor_fn":craps_decor,
                     "furniture":[],"doors":[BACK],
                     "npcs":[{"id":"stickman","x":W//2,"y":265,"name":"Stickman Joe","col":"#d8c0a0",
                               "hat_col":"#00204a","body_col":"#00204a","line":"Bet pass line!\nPlace chips then DEAL.","game":"craps"}]},
            "war":  {"title":"War Room","floor":"#1a0800","wall":"#0d0400","decor_fn":None,
                     "furniture":war_furniture(),
                     "doors":[BACK],
                     "npcs":[{"id":"dealer_war","x":W//2,"y":248,"name":"Dealer Rex","col":"#c8a080",
                               "hat_col":"#3a2000","body_col":"#8B0000","line":"Highest card wins!\nPlace chips then DEAL.","game":"war"}]},
            "hcard":{"title":"High Card Lounge","floor":"#001818","wall":"#000e0e","decor_fn":None,
                     "furniture":hcard_furniture(),
                     "doors":[BACK],
                     "npcs":[{"id":"dealer_hc","x":W//2,"y":258,"name":"Dealer Mia","col":"#d8c0a8",
                               "hat_col":"#002a2a","body_col":"#004444","line":"Draw one card each.\nHighest wins!","game":"high_card"}]},
            "poker":{"title":"Texas Hold'em Room","floor":"#0a1a0a","wall":"#060e06","decor_fn":poker_decor,
                     "furniture":[{"type":"felt_table","bounds":(W//2-210,210,W//2+210,400),"label":""}],
                     "doors":[BACK],
                     "npcs":[{"id":"dealer_ph","x":W//2,"y":228,"name":"Dealer Phil","col":"#c8b060",
                               "hat_col":"#1a2a00","body_col":"#1a3a10","line":"Texas Hold'em!\nTalk to me to play.","game":"texas_holdem"}]},
            "yah":  {"title":"Yahtzee Lounge","floor":"#1a1a00","wall":"#0e0e00","decor_fn":yah_decor,
                     "furniture":[],"doors":[BACK],
                     "npcs":[{"id":"dealer_yah","x":W//2,"y":340,"name":"Dice Master Dan","col":"#e8d070",
                               "hat_col":"#3a3a00","body_col":"#2a2a00","line":"Roll up to 3 times.\nBest score wins cash!","game":"yahtzee"}]},
            "dice": {"title":"Dice Roll","floor":"#001a00","wall":"#000e00","decor_fn":dice_decor,
                     "furniture":[],"doors":[BACK],
                     "npcs":[{"id":"dealer_dice","x":W//2,"y":340,"name":"Lucky Lou","col":"#a0e890",
                               "hat_col":"#005000","body_col":"#004400","line":"One die each.\nHighest wins!","game":"dice_roll"}]},
        }

    def _make_stables_rooms(self):
        if not hasattr(self,'_horse_frame'): self._horse_frame=0
        f=self._horse_frame
        def decor(c):
            TT,TB,FX,SX=148,430,W-60,128; lh=(TB-TT)//5
            # Wood-plank floor lanes
            for lane in range(5):
                ly=TT+lane*lh
                fill="#8B7214" if lane%2==0 else "#9B8020"
                c.create_rectangle(SX,ly,FX,ly+lh,fill=fill,outline="#5a3800",width=1)
            c.create_rectangle(SX,TT,FX,TB,fill="",outline="#3a2000",width=3)
            # Finishing post
            for fy2 in range(TT,TB,16):
                c.create_rectangle(FX-12,fy2,FX,fy2+16,fill="white" if(fy2//16)%2==0 else"black",outline="")
            # Animated horses
            for lane,(name,hcol) in enumerate(zip(HORSE_NAMES,HORSE_COLS)):
                cy=TT+lane*lh+lh//2
                phase=f*0.18+lane*1.3
                bob=int(3*math.sin(phase*2))
                hx=SX+90; hy=cy+bob
                # Body
                c.create_oval(hx-34,hy-13,hx+34,hy+13,fill=hcol,outline="#1a0800",width=2)
                # Neck
                neck_ang=0.35+0.12*math.sin(phase)
                nex=hx+34+int(20*math.cos(neck_ang)); ney=hy-13-int(16*math.sin(neck_ang))
                c.create_line(hx+28,hy-8,nex,ney,fill=hcol,width=8)
                # Head
                c.create_oval(nex-9,ney-7,nex+9,ney+7,fill=hcol,outline="#1a0800",width=1)
                # Nostril + eye
                c.create_oval(nex+4,ney+1,nex+7,ney+4,fill="#1a0800",outline="")
                c.create_oval(nex+2,ney-3,nex+5,ney,fill="#111",outline="")
                # Mane
                for mi in range(4):
                    mx2=hx+28+int(mi*5*math.cos(neck_ang))
                    my2=hy-8-int(mi*5*math.sin(neck_ang))
                    c.create_oval(mx2-3,my2-5,mx2+3,my2+2,fill="#1a0800",outline="")
                # Tail
                for ti in range(3):
                    tw=int(5*math.sin(phase+ti*0.8))
                    c.create_line(hx-34,hy-3+ti*5,hx-46,hy+ti*4+tw,fill="#1a0800",width=2)
                # Legs gallop
                for lx2,lp in [(hx-20,0.0),(hx-6,1.57),(hx+6,3.14),(hx+20,4.71)]:
                    sw=math.sin(phase+lp)*16
                    kx=lx2+int(sw*0.4); ky=hy+13+7
                    fx2=lx2+int(sw);     fhy=hy+13+20
                    c.create_line(lx2,hy+13,kx,ky,fill=hcol,width=4)
                    c.create_line(kx,ky,fx2,fhy,fill=hcol,width=3)
                    c.create_oval(fx2-3,fhy-2,fx2+3,fhy+4,fill="#1a0800",outline="")
                # Lane label
                c.create_text(SX-5,cy,text=f"{lane+1}. {name}",fill=hcol,font=self.fnt_small,anchor="e")
            # Barn sign
            c.create_rectangle(W//2-110,68,W//2+110,100,fill="#5a3010",outline=GOLD,width=2)
            c.create_text(W//2,84,text="THE STABLES",fill=GOLD,font=tkfont.Font(family="Georgia",size=12,weight="bold"))
        self._horse_frame+=1
        return {"main":{"title":"The Stables","floor":"#2a1a08","wall":"#1a0e04","decor_fn":decor,"furniture":[],
                        "doors":[{"to":"exit","x":460,"y":638,"w":180,"h":34,"col":"#333","label":"Exit Stables"}],
                        "npcs":[{"id":"jockey","x":W//2,"y":468,"name":"Jockey Sam","col":"#e8b070",
                                  "hat_col":"#8B0000","body_col":"#8B0000","line":"Pick a horse 1-5 then\nplace chips and DEAL!","game":"horse_race"}]}}

    def _make_shady_rooms(self):
        def decor(c):
            c.create_rectangle(0,60,W,H-30,fill="#060606")
            for gx2,gy2,gt,gc in [(150,200,"RISK","#cc2244"),(820,280,"LUCK","#44aacc"),(420,340,"DEAL","#88cc22"),(950,200,"SHADY","#cc8822")]:
                c.create_text(gx2,gy2,text=gt,fill=gc,font=self.fnt_title,angle=random.randint(-20,20))
            c.create_oval(W//2-25,74,W//2+25,112,fill="#997700",outline=GOLD)
            c.create_oval(W//2-20,79,W//2+20,107,fill="#ffee88",outline="")
            # Broken crates
            for bx2,by2 in [(80,380),(W-160,420),(200,460)]:
                c.create_rectangle(bx2,by2,bx2+60,by2+40,fill="#3a2800",outline="#1a1200",width=2)
                c.create_line(bx2,by2,bx2+60,by2+40,fill="#1a1200",width=1)
                c.create_line(bx2+60,by2,bx2,by2+40,fill="#1a1200",width=1)
            # Trash barrels
            for tx2,ty2 in [(900,350),(960,400)]:
                c.create_rectangle(tx2-16,ty2,tx2+16,ty2+38,fill="#1a1a1a",outline="#333",width=2)
                c.create_line(tx2-16,ty2+10,tx2+16,ty2+10,fill="#333",width=1)
                c.create_line(tx2-16,ty2+22,tx2+16,ty2+22,fill="#333",width=1)
            # Wall graffiti tags
            for gfx,gfy,gft,gfc in [(60,150,"✗","#cc0000"),(W-80,200,"$","#00cc88"),(100,480,"!","#cc8800")]:
                c.create_text(gfx,gfy,text=gft,fill=gfc,font=tkfont.Font(size=28,weight="bold"))
            # Dim lamp
            c.create_line(W//2-200,60,W//2-200,110,fill="#4a3000",width=3)
            c.create_oval(W//2-214,105,W//2-186,125,fill="#aa8800",outline="#cc9900",width=1)
            # Chain
            for ci in range(8):
                c.create_oval(W-50,140+ci*14,W-30,152+ci*14,outline="#555",width=2,fill="")
        return {"main":{"title":"Shady Alley","floor":"#060606","wall":"#030303","decor_fn":decor,
                        "furniture":[],
                        "doors":[{"to":"exit","x":460,"y":638,"w":180,"h":34,"col":"#333","label":"Leave Alley"}],
                        "npcs":[{"id":"fixer","x":W//2,"y":314,"name":"The Fixer","col":"#a08060",
                                  "hat_col":"#111","body_col":"#222","line":"Need cash? I can help…\nfor a price.","game":"shady_deal"}]}}

    def _make_vip_rooms(self):
        # ── Lobby ─────────────────────────────────────────
        def lobby_decor(c):
            # Deep purple marble floor
            for row in range(14):
                for col in range(16):
                    x1=col*72; y1=65+row*40
                    shade=(row+col)%2
                    c.create_rectangle(x1,y1,x1+71,y1+39,
                                       fill="#0e0028" if shade else "#130032",outline="#1a0040",width=1)
            c.create_rectangle(20,65,W-20,H-30,fill="",outline=GOLD,width=2)
            c.create_rectangle(28,73,W-28,H-38,fill="",outline="#5a4010",width=1)
            # Chandeliers
            for chx in [200,W//2,W-200]:
                c.create_line(chx,65,chx,108,fill=GOLD,width=4)
                for i in range(8):
                    a=math.radians(i*45)
                    ex=chx+int(36*math.cos(a)); ey=116+int(14*math.sin(a))
                    c.create_line(chx,116,ex,ey,fill=GOLD,width=2)
                    c.create_oval(ex-6,ey-8,ex+6,ey+5,fill="#ffee88",outline=GOLD,width=1)
                c.create_oval(chx-10,108,chx+10,124,fill=GOLD,outline="#5a4010",width=2)
            # Drapes
            for dx in [0,W-60]:
                c.create_rectangle(dx,65,dx+58,H-30,fill="#1a0040",outline="")
                c.create_rectangle(dx+6,65,dx+52,H-30,fill="#220050",outline="")
                for fy in range(65,H-30,40):
                    c.create_line(dx+8,fy,dx+50,fy+20,fill="#2a0060",width=2)
            # Gold rope dividers
            for rx in [220,W-220]:
                c.create_oval(rx-8,300,rx+8,316,fill=GOLD,outline="#5a4010",width=1)
                c.create_line(rx,308,rx,480,fill=GOLD,width=3,dash=(6,4))
                c.create_oval(rx-8,478,rx+8,494,fill=GOLD,outline="#5a4010",width=1)
            # ── Reception desk ──────────────────────────────
            c.create_rectangle(W//2-120,195,W//2+120,265,fill="#1a0040",outline=GOLD,width=3)
            c.create_rectangle(W//2-114,201,W//2+114,259,fill="#220050",outline="#5a4010",width=1)
            c.create_text(W//2,230,text="CONCIERGE",fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=10,weight="bold"))
            # Desk items: flowers
            c.create_oval(W//2-80,188,W//2-68,200,fill="#cc2244",outline="",)
            c.create_oval(W//2-76,182,W//2-64,194,fill="#ee3355",outline="")
            c.create_line(W//2-72,200,W//2-72,220,fill="#1a6622",width=2)
            # Desk bell
            c.create_oval(W//2+60,200,W//2+80,216,fill="#c8a850",outline=GOLD,width=1)
            c.create_line(W//2+70,216,W//2+70,224,fill="#8B6914",width=3)
            # ── Armchairs (left & right) ─────────────────────
            for ax,flip in [(100,False),(W-100,True)]:
                d=1 if flip else -1
                c.create_rectangle(ax-32,360,ax+32,420,fill="#1a0050",outline=GOLD,width=2)
                c.create_rectangle(ax-28,354,ax+28,368,fill="#220060",outline=GOLD,width=1)
                c.create_rectangle(ax-36,360,ax-28,420,fill="#1a0050",outline=GOLD,width=1)
                c.create_rectangle(ax+28,360,ax+36,420,fill="#1a0050",outline=GOLD,width=1)
                c.create_rectangle(ax-28,416,ax+28,430,fill="#110030",outline="#3a1060",width=1)
            # ── Grandfather clock (right wall) ───────────────
            cx2=W-105
            c.create_rectangle(cx2-22,150,cx2+22,460,fill="#1a0c04",outline=GOLD,width=2)
            c.create_rectangle(cx2-18,154,cx2+18,220,fill="#0d0600",outline=GOLD,width=1)
            c.create_oval(cx2-14,158,cx2+14,214,fill="#0a0400",outline=GOLD,width=1)
            c.create_line(cx2,186,cx2,172,fill=GOLD,width=2)   # hour hand
            c.create_line(cx2,186,cx2+10,178,fill="#aaa",width=1) # min hand
            c.create_oval(cx2-3,183,cx2+3,189,fill=GOLD,outline="",)
            c.create_rectangle(cx2-10,224,cx2+10,430,fill="#0d0600",outline="#3a2010",width=1)
            c.create_oval(cx2-8,320,cx2+8,360,fill="#8B6914",outline=GOLD,width=1)
            # ── Potted palms (flanking exit) ─────────────────
            for px2 in [W//2-170,W//2+170]:
                c.create_rectangle(px2-14,580,px2+14,640,fill="#1a0050",outline=GOLD,width=2)
                c.create_line(px2,580,px2,520,fill="#1a6622",width=3)
                for a2 in range(0,360,60):
                    ea=math.radians(a2); lx=px2+int(36*math.cos(ea)); ly=520+int(16*math.sin(ea))
                    c.create_line(px2,520,lx,ly,fill="#2a8830",width=3)
                    c.create_oval(lx-8,ly-5,lx+8,ly+5,fill="#1a7020",outline="")
            # Welcome mat
            c.create_rectangle(W//2-80,H-68,W//2+80,H-36,fill="#0a0030",outline=GOLD,width=2)
            c.create_text(W//2,H-52,text="VIP",fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=11,weight="bold"))

        # ── Salon (Double or Nothing) ───────────────────
        def salon_decor(c):
            c.create_rectangle(0,65,W,H-30,fill="#05000f",outline="")
            for wx in range(0,W,100): c.create_line(wx,65,wx,H-30,fill="#0a0020",width=1)
            # Wheel base circle drawn here; actual segments drawn at runtime by draw_wheel()
            cx,cy=W//2,295; WR2=155
            c.create_oval(cx-WR2-18,cy-WR2-18,cx+WR2+18,cy+WR2+18,fill="#1a0800",outline=GOLD,width=5)
            # Pedestal stand
            c.create_rectangle(cx-18,cy+WR2+18,cx+18,cy+WR2+54,fill="#1a0c04",outline=GOLD,width=2)
            c.create_rectangle(cx-34,cy+WR2+50,cx+34,cy+WR2+64,fill="#1a0c04",outline=GOLD,width=2)
            # Velvet drapes
            for dx,flip in [(0,False),(W-70,True)]:
                fold=1 if flip else -1
                c.create_rectangle(dx,65,dx+68,H-30,fill="#1a0040",outline="")
                for fy in range(65,H,30): c.create_line(dx+4,fy,dx+64,fy+15*fold,fill="#220050",width=2)
            for tx2 in [68,W-68]:
                c.create_oval(tx2-6,280,tx2+6,292,fill=GOLD,outline="#5a4010")
                c.create_line(tx2,292,tx2,380,fill=GOLD,width=2)
                c.create_oval(tx2-8,378,tx2+8,390,fill=GOLD,outline="#5a4010")
            c.create_oval(W//2-18,66,W//2+18,90,fill="#ffee88",outline=GOLD,width=2)
            # Two velvet audience chairs
            for ax in [cx-220,cx+220]:
                c.create_rectangle(ax-28,390,ax+28,450,fill="#2a0050",outline=GOLD,width=2)
                c.create_rectangle(ax-24,380,ax+24,396,fill="#330060",outline=GOLD,width=1)
                c.create_rectangle(ax-32,390,ax-24,450,fill="#220040",outline="#440070",width=1)
                c.create_rectangle(ax+24,390,ax+32,450,fill="#220040",outline="#440070",width=1)
                c.create_rectangle(ax-24,446,ax+24,460,fill="#110030",outline="#2a0050",width=1)
            # Side table with champagne
            c.create_oval(cx-260,468,cx-200,484,fill="#1a0c04",outline=GOLD,width=1)
            c.create_line(cx-230,484,cx-230,516,fill="#1a0c04",width=8)
            c.create_rectangle(cx-252,514,cx-210,524,fill="#1a0c04",outline=GOLD,width=1)
            for bx2 in [cx-248,cx-234,cx-220]:
                c.create_rectangle(bx2,484,bx2+8,514,fill="#1a3a50",outline="#3a6a80",width=1)
                c.create_oval(bx2-1,480,bx2+9,488,fill="#2a5a70",outline="")
            # Floor lamp
            lx=cx+230
            c.create_rectangle(lx-4,440,lx+4,560,fill="#1a0c04",outline="")
            c.create_oval(lx-22,430,lx+22,450,fill="#ffee88",outline=GOLD,width=2)
            c.create_oval(lx-14,556,lx+14,566,fill="#0d0600",outline=GOLD,width=1)
            # Sign
            c.create_rectangle(W//2-88,72,W//2+88,108,fill="#0a0020",outline=GOLD,width=2)
            c.create_text(W//2,90,text="DOUBLE OR NOTHING",fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=9,weight="bold"))

        def bj_decor(c):
            for wx in range(0,W,90):
                c.create_rectangle(wx,65,wx+88,H-30,
                                   fill="#1a0c04" if (wx//90)%2==0 else "#150a02",outline="#0a0600",width=1)
            c.create_line(0,500,W,500,fill="#8B6914",width=3)
            for wx in range(8,W-8,90):
                c.create_rectangle(wx,505,wx+84,H-35,fill="#120800",outline="#3a2010",width=1)
                c.create_rectangle(wx+6,511,wx+78,H-41,fill="#0e0600",outline="#2a1808",width=1)
            for cx2 in range(0,W,120):
                c.create_rectangle(cx2,65,cx2+118,180,fill="#0d0600",outline="#3a2010",width=1)
                c.create_rectangle(cx2+8,73,cx2+110,172,fill="#120800",outline="#2a1808",width=1)
            # BJ table
            tx1,ty1,tx2,ty2=W//2-230,240,W//2+230,395
            round_rect(c,tx1-12,ty1-10,tx2+12,ty2+12,r=32,fill="#3a1a00",outline="#2a1000",width=3)
            round_rect(c,tx1,ty1,tx2,ty2,r=28,fill="#0d5c1e",outline="#0a3a14",width=3)
            round_rect(c,tx1+8,ty1+8,tx2-8,ty2-8,r=24,fill="#0f6622",outline="")
            c.create_text(W//2,ty1+50,text="BLACKJACK PAYS 3:2",fill="#1a8830",
                          font=tkfont.Font(family="Courier New",size=11,weight="bold"))
            c.create_text(W//2,ty1+75,text="MINIMUM BET  $500",fill="#1a8830",
                          font=tkfont.Font(family="Courier New",size=10))
            for i in range(5):
                bx=int(tx1+(tx2-tx1)*(i+0.5)/5); by=ty2-18
                c.create_oval(bx-18,by-12,bx+18,by+12,fill="",outline="#1a8830",width=2)
            # Player stools
            for i in range(5):
                sx=int(tx1+(tx2-tx1)*(i+0.5)/5); sy=ty2+30
                c.create_oval(sx-18,sy,sx+18,sy+14,fill="#2a1400",outline="#8B6914",width=2)
                c.create_line(sx-14,sy+14,sx-10,sy+48,fill="#1a0c04",width=4)
                c.create_line(sx+14,sy+14,sx+10,sy+48,fill="#1a0c04",width=4)
                c.create_line(sx-10,sy+46,sx+10,sy+46,fill="#1a0c04",width=3)
            # Card shoe on table
            c.create_rectangle(tx2-70,ty1+20,tx2-10,ty1+70,fill="#1a0c04",outline=GOLD,width=2)
            c.create_rectangle(tx2-66,ty1+16,tx2-14,ty1+26,fill="#2a1400",outline="#8B6914",width=1)
            c.create_text(tx2-40,ty1+44,text="SHOE",fill="#5a3010",
                          font=tkfont.Font(family="Courier New",size=7))
            # Chip rack on wall
            for ri,rcol in enumerate(["#cc2222","#1a1a88","#228822","#ccaa22"]):
                rx=80+ri*52
                c.create_rectangle(rx,482,rx+40,500,fill="#0d0600",outline="#5a3010",width=1)
                for ci in range(5):
                    c.create_oval(rx+3+ci*7,484,rx+9+ci*7,498,fill=rcol,outline="#888888",width=1)
            c.create_text(80+4*26,490,text="",fill=GOLD,font=tkfont.Font(size=8))
            # Chandelier
            c.create_line(W//2,65,W//2,115,fill=GOLD,width=4)
            c.create_oval(W//2-14,108,W//2+14,128,fill="#ffee88",outline=GOLD,width=2)
            # Sconces
            for sx in [50,W-50]:
                c.create_rectangle(sx-14,82,sx+14,160,fill="#3a2008",outline=GOLD,width=2)
                c.create_oval(sx-14,172,sx+14,206,fill="#ffeeaa",outline=GOLD,width=2)
            # Framed rules poster
            c.create_rectangle(W-90,180,W-10,290,fill="#0d0600",outline=GOLD,width=2)
            for li,ln in enumerate(["RULES","BJ=21","A=1/11","J,Q,K=10"]):
                c.create_text(W-50,198+li*22,text=ln,fill=GOLD,
                              font=tkfont.Font(family="Courier New",size=7,weight="bold"))
            # Tip jar
            c.create_oval(tx1+10,ty1+20,tx1+40,ty1+56,fill="#1a3a50",outline="#3a6a80",width=2)
            c.create_text(tx1+25,ty1+38,text="TIPS",fill="#3a6a80",
                          font=tkfont.Font(family="Courier New",size=6))

        def poker_decor(c):
            c.create_rectangle(0,65,W,H-30,fill="#031a08",outline="")
            for wx in range(0,W,80):
                c.create_rectangle(wx,65,wx+78,H-30,
                                   fill="#041e0a" if (wx//80)%2 else "#031508",outline="#061a0c",width=1)
            # Oval table
            tx,ty,trx,try_=W//2,310,260,110
            c.create_oval(tx-trx-10,ty-try_-10,tx+trx+10,ty+try_+10,fill="#2a1800",outline="#1a0e00",width=3)
            c.create_oval(tx-trx,ty-try_,tx+trx,ty+try_,fill="#1a5c2a",outline="#0a3a18",width=3)
            c.create_oval(tx-trx+10,ty-try_+10,tx+trx-10,ty+try_-10,fill="#1f6830",outline="")
            # Cup holders
            for i in range(8):
                a=math.radians(i*45); rx2=trx-20; ry2=try_-16
                px2=tx+int(rx2*math.cos(a)); py2=ty+int(ry2*math.sin(a))
                c.create_oval(px2-8,py2-8,px2+8,py2+8,fill="#0a3015",outline="#1a5030",width=1)
            # Player chairs around table
            for i in range(7):
                a=math.radians(i*(360/7)+20); rx3=trx+36; ry3=try_+28
                px3=tx+int(rx3*math.cos(a)); py3=ty+int(ry3*math.sin(a))
                c.create_oval(px3-16,py3-10,px3+16,py3+10,fill="#1a0a00",outline="#8B6914",width=2)
            # Chip tower on table centre
            for ci in range(5):
                cc=["#cc2222","#1a1a88","#228822","#ccaa22","#cc22cc"][ci]
                c.create_oval(tx-10,ty-40+ci*8,tx+10,ty-32+ci*8,fill=cc,outline="#fff",width=1)
            # Portraits
            for px4,nm in [(130,"R.G."),(W-130,"D.A.")]:
                c.create_rectangle(px4-44,76,px4+44,178,fill="#0a1a06",outline=GOLD,width=3)
                c.create_rectangle(px4-38,82,px4+38,172,fill="#0e2008",outline="#3a5020",width=1)
                c.create_oval(px4-16,98,px4+16,130,fill="#d0a060",outline="#8B6914",width=1)
                c.create_text(px4,155,text=nm,fill=GOLD,
                              font=tkfont.Font(family="Georgia",size=9,slant="italic"))
            # Pendant lights
            for lx2 in [W//2-80,W//2,W//2+80]:
                c.create_line(lx2,65,lx2,200,fill="#444",width=2)
                c.create_oval(lx2-12,192,lx2+12,218,fill="#ffdd88",outline="#8B6914",width=1)
            # Corner bar with bottles
            c.create_rectangle(W-90,400,W-10,H-35,fill="#1a0a04",outline=GOLD,width=2)
            c.create_text(W-50,412,text="BAR",fill=GOLD,
                          font=tkfont.Font(family="Courier New",size=7,weight="bold"))
            for bx3 in [W-75,W-55,W-35]:
                c.create_rectangle(bx3-7,378,bx3+7,404,fill="#2a3a50",outline="#4a6a80",width=1)
                c.create_oval(bx3-7,374,bx3+7,382,fill="#3a5060",outline="")
            # Dealer button marker on table
            c.create_oval(tx+60,ty+20,tx+80,ty+36,fill="#eeeeee",outline="#888",width=1)
            c.create_text(tx+70,ty+28,text="D",fill="#000",
                          font=tkfont.Font(family="Courier New",size=8,weight="bold"))
            # Clock on wall
            c.create_oval(W//2-22,72,W//2+22,114,fill="#031a08",outline=GOLD,width=2)
            c.create_line(W//2,93,W//2,78,fill=GOLD,width=2)
            c.create_line(W//2,93,W//2+12,98,fill="#aaa",width=1)

        def gold_decor(c):
            for row in range(14):
                for col in range(16):
                    x1=col*72; y1=65+row*40; shade=(row+col)%2
                    c.create_rectangle(x1,y1,x1+71,y1+39,
                                       fill="#1a1000" if shade else "#1e1400",outline="#2a1e00",width=1)
            c.create_rectangle(20,65,W-20,H-30,fill="",outline=GOLD,width=3)
            c.create_rectangle(30,75,W-30,H-40,fill="",outline="#5a4010",width=1)
            # Roulette wheel display
            wx2,wy2,wr2=W//2,290,130
            c.create_oval(wx2-wr2-12,wy2-wr2-12,wx2+wr2+12,wy2+wr2+12,fill="#3a2800",outline=GOLD,width=4)
            RED_N={1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
            for i in range(37):
                ang=(i/37)*360
                rc="#006000" if i==0 else("#aa2222" if i in RED_N else "#1a1a1a")
                c.create_arc(wx2-wr2,wy2-wr2,wx2+wr2,wy2+wr2,start=ang,extent=360/37,
                             fill=rc,outline=GOLD,width=1,style="pie")
            c.create_oval(wx2-20,wy2-20,wx2+20,wy2+20,fill=GOLD,outline="#3a2800",width=2)
            c.create_text(wx2,wy2,text="0",fill="#ffffff",
                          font=tkfont.Font(family="Courier New",size=8,weight="bold"))
            # Betting layout
            round_rect(c,60,420,W-60,H-40,r=10,fill="#1a5c2a",outline=GOLD,width=2)
            for i,num in enumerate(range(1,13)):
                bx4=70+i*96; by4=432
                rc2="#aa2222" if num in RED_N else "#111"
                c.create_rectangle(bx4,by4,bx4+90,by4+38,fill=rc2,outline=GOLD,width=1)
                c.create_text(bx4+45,by4+19,text=str(num),fill="white",
                              font=tkfont.Font(family="Courier New",size=10,weight="bold"))
            # Ornate pillars
            for pilx in [36,W-36]:
                c.create_rectangle(pilx-14,65,pilx+14,H-30,fill="#1a1000",outline=GOLD,width=2)
                for py5 in range(80,H-30,60):
                    c.create_rectangle(pilx-12,py5,pilx+12,py5+10,fill="#2a1e00",outline=GOLD,width=1)
                c.create_oval(pilx-14,65,pilx+14,88,fill="#2a1e00",outline=GOLD,width=2)
            # Sconces
            for sx2 in [50,W-50]:
                c.create_rectangle(sx2-12,80,sx2+12,148,fill="#3a2800",outline=GOLD,width=2)
                c.create_oval(sx2-12,148,sx2+12,180,fill="#ffee88",outline=GOLD,width=2)
                c.create_oval(sx2-8,152,sx2+8,176,fill="#fffacc",outline="")
            # Chip stations along wall
            for cs in [120,W//2,W-120]:
                c.create_rectangle(cs-30,482,cs+30,510,fill="#1a1000",outline=GOLD,width=1)
                for ci2,cc2 in enumerate(["#cc2222","#ccaa22","#228822"]):
                    c.create_oval(cs-20+ci2*14,486,cs-8+ci2*14,500,fill=cc2,outline="#fff",width=1)
            # Ball return tray
            c.create_oval(wx2+wr2+16,wy2-12,wx2+wr2+48,wy2+12,fill="#1a1000",outline=GOLD,width=2)
            c.create_text(wx2+wr2+32,wy2,text="●",fill="#eeeeee",
                          font=tkfont.Font(size=8))
            # Grand sign
            c.create_rectangle(W//2-160,68,W//2+160,104,fill="#0d0800",outline=GOLD,width=2)
            c.create_text(W//2,86,text="✦  THE GOLDEN HALL  ✦",fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=13,weight="bold"))


        def raffle_decor(c):
            # Deep midnight floor with diamond pattern
            for row in range(14):
                for col in range(16):
                    x1r=col*72; y1r=65+row*40; shade=(row+col)%2
                    c.create_rectangle(x1r,y1r,x1r+71,y1r+39,
                                       fill="#0d0820" if shade else "#110a28",outline="#1a0f38",width=1)
            # Gold diamond overlay
            for row in range(7):
                for col in range(8):
                    cx8=col*144+72; cy8=65+row*80+40
                    pts=[cx8,cy8-18, cx8+22,cy8, cx8,cy8+18, cx8-22,cy8]
                    c.create_polygon(pts,fill="",outline="#2a1e00",width=1)
            c.create_rectangle(20,65,W-20,H-30,fill="",outline=GOLD,width=3)
            c.create_rectangle(30,75,W-30,H-40,fill="",outline="#3a2800",width=1)
            # Grand crystal chandelier centre
            chx,chy=W//2,90
            c.create_line(chx,65,chx,chy+10,fill=GOLD,width=5)
            c.create_oval(chx-16,chy,chx+16,chy+28,fill=GOLD,outline="#8B6914",width=2)
            for i in range(12):
                a=math.radians(i*30); r1=28; r2=52
                x1c=chx+int(r1*math.cos(a)); y1c=chy+14+int(r1*0.4*math.sin(a))
                x2c=chx+int(r2*math.cos(a)); y2c=chy+14+int(r2*0.4*math.sin(a))
                c.create_line(x1c,y1c,x2c,y2c,fill=GOLD,width=1)
                c.create_oval(x2c-5,y2c-8,x2c+5,y2c+8,fill="#d0f0ff",outline="#a0d8f8",width=1)
            for i in range(8):
                a=math.radians(i*45); r3=60
                x3c=chx+int(r3*math.cos(a)); y3c=chy+14+int(r3*0.35*math.sin(a))
                c.create_line(chx,chy+14,x3c,y3c+12,fill="#c0a030",width=1)
                c.create_oval(x3c-3,y3c+9,x3c+3,y3c+17,fill="#ffee88",outline=GOLD,width=1)
            # Velvet drapes left & right
            for dxr,flip in [(0,False),(W-72,True)]:
                fold=1 if flip else -1
                c.create_rectangle(dxr,65,dxr+70,H-30,fill="#160030",outline="")
                c.create_rectangle(dxr+6,65,dxr+64,H-30,fill="#1e0040",outline="")
                for fy in range(65,H-30,36):
                    c.create_line(dxr+8,fy,dxr+62,fy+18*fold,fill="#280050",width=2)
            # Tassel tie-backs
            for txr in [70,W-70]:
                c.create_oval(txr-8,280,txr+8,296,fill=GOLD,outline="#5a4010")
                c.create_line(txr,296,txr,360,fill=GOLD,width=2,dash=(4,3))
                c.create_oval(txr-8,358,txr+8,374,fill=GOLD,outline="#5a4010")
            # Raffle drum — large ornate drum on table centre
            drum_x,drum_y=W//2,310; drum_r=52; drum_h=48
            # Table base
            c.create_oval(drum_x-70,drum_y+drum_h,drum_x+70,drum_y+drum_h+16,fill="#1a0c04",outline=GOLD,width=2)
            c.create_rectangle(drum_x-8,drum_y+drum_h+16,drum_x+8,drum_y+drum_h+60,fill="#2a1808",outline=GOLD,width=1)
            c.create_oval(drum_x-28,drum_y+drum_h+56,drum_x+28,drum_y+drum_h+70,fill="#1a0c04",outline=GOLD,width=2)
            # Drum barrel
            c.create_oval(drum_x-drum_r,drum_y-drum_h//2,drum_x+drum_r,drum_y+drum_h//2,fill="#2a0050",outline=GOLD,width=3)
            c.create_oval(drum_x-drum_r+8,drum_y-drum_h//2+4,drum_x+drum_r-8,drum_y+drum_h//2-4,fill="#340060",outline="#5a0090",width=1)
            for i in range(8):
                a=math.radians(i*45)
                rx=int(drum_r*0.75*math.cos(a)); ry=int((drum_h//2)*0.65*math.sin(a))
                c.create_oval(drum_x+rx-6,drum_y+ry-9,drum_x+rx+6,drum_y+ry+9,fill=GOLD,outline="#5a4010",width=1)
                c.create_text(drum_x+rx,drum_y+ry,text="★",fill="#fffacc",font=tkfont.Font(size=6))
            # Handle axle
            c.create_rectangle(drum_x-drum_r-14,drum_y-4,drum_x-drum_r,drum_y+4,fill="#8B6914",outline=GOLD,width=1)
            c.create_rectangle(drum_x+drum_r,drum_y-4,drum_x+drum_r+14,drum_y+4,fill="#8B6914",outline=GOLD,width=1)
            c.create_oval(drum_x-drum_r-18,drum_y-8,drum_x-drum_r-6,drum_y+8,fill=GOLD,outline="#5a4010",width=2)
            c.create_oval(drum_x+drum_r+6,drum_y-8,drum_x+drum_r+18,drum_y+8,fill=GOLD,outline="#5a4010",width=2)
            # Ticket stubs scattered on floor
            for txs,tys,ta in [(W//2-160,520,15),(W//2-80,545,-8),(W//2+60,530,22),(W//2+150,515,-12),(W//2-30,560,5)]:
                pts2=[]
                for i2 in range(4):
                    ax2=math.radians(ta+i2*90)
                    pts2+=[txs+int(16*math.cos(ax2)),tys+int(8*math.sin(ax2))]
                c.create_polygon(pts2,fill="#f0e8d0",outline="#c0b090",width=1)
                c.create_line(txs-4,tys,txs+4,tys,fill="#cc2200",width=1)
            # Reception desk (host behind it)
            c.create_rectangle(W//2-100,160,W//2+100,240,fill="#1a0040",outline=GOLD,width=3)
            c.create_rectangle(W//2-94,166,W//2+94,234,fill="#220050",outline="#5a0090",width=1)
            c.create_text(W//2,200,text="RAFFLE DESK",fill=GOLD,font=tkfont.Font(family="Georgia",size=9,weight="bold"))
            # Prize board on back wall
            c.create_rectangle(W//2-180,70,W//2+180,148,fill="#0a0020",outline=GOLD,width=2)
            c.create_text(W//2,82,text="✦  VIP RAFFLE  ✦",fill=GOLD,font=tkfont.Font(family="Georgia",size=11,weight="bold"))
            c.create_text(W//2,104,text="$200 per ticket  ·  Draw every 5 games",fill="#aaaacc",
                          font=tkfont.Font(family="Courier New",size=8))
            c.create_text(W//2,122,text="Prizes: $500 · $1,500 · $5,000 · JACKPOT $20,000",fill=GOLD,
                          font=tkfont.Font(family="Courier New",size=8))
            # Gold rope barrier
            for rxr in [W//2-220,W//2+220]:
                c.create_oval(rxr-8,300,rxr+8,316,fill=GOLD,outline="#5a4010")
                c.create_line(rxr,308,rxr,460,fill=GOLD,width=3,dash=(6,4))
                c.create_oval(rxr-8,458,rxr+8,474,fill=GOLD,outline="#5a4010")
            # Armchairs flanking drum table
            for axr,flip2 in [(W//2-200,False),(W//2+200,True)]:
                c.create_rectangle(axr-28,440,axr+28,500,fill="#1a0040",outline=GOLD,width=2)
                c.create_rectangle(axr-24,432,axr+24,448,fill="#220050",outline=GOLD,width=1)
                c.create_rectangle(axr-32,440,axr-24,500,fill="#160030",outline="#3a0060",width=1)
                c.create_rectangle(axr+24,440,axr+32,500,fill="#160030",outline="#3a0060",width=1)
                c.create_rectangle(axr-24,496,axr+24,510,fill="#0e0020",outline="#2a0050",width=1)
            # Welcome mat
            c.create_rectangle(W//2-80,H-68,W//2+80,H-36,fill="#0a0030",outline=GOLD,width=2)
            c.create_text(W//2,H-52,text="RAFFLE",fill=GOLD,font=tkfont.Font(family="Georgia",size=10,weight="bold"))

        LDOOR={"to":"lobby","x":W//2-90,"y":638,"w":180,"h":34,"col":"#2a1a00","label":"← Lobby"}
        return {
            "lobby":{
                "title":"VIP Lobby","floor":"#0e0028","wall":"#05000e","decor_fn":lobby_decor,
                "furniture":[],
                "doors":[
                    {"to":"exit",    "x":460,      "y":638,"w":180,"h":34,"col":"#1a0040","label":"Exit Building"},
                    {"to":"salon",   "x":160,      "y":340,"w":140,"h":34,"col":"#2a0060","label":"Private Salon →"},
                    {"to":"bj_room", "x":W-160,    "y":340,"w":160,"h":34,"col":"#2a0060","label":"← High Stakes BJ"},
                    {"to":"poker",   "x":160,      "y":420,"w":140,"h":34,"col":"#2a0060","label":"Poker Room →"},
                    {"to":"gold_hall","x":W-160,   "y":420,"w":160,"h":34,"col":"#2a0060","label":"← Golden Hall"},
                    {"to":"raffle_room","x":W//2-80,"y":520,"w":160,"h":34,"col":"#2a0060","label":"★ Raffle Room"},
                ],
                "npcs":[{"id":"vip_concierge","x":W//2,"y":220,"name":"Concierge","col":"#f0d0a0",
                          "hat_col":PURPLE,"body_col":PURPLE,"line":"Good evening.\nHow may I assist?","game":None}]
            },
            "salon":{
                "title":"Private Salon","floor":"#05000f","wall":"#05000f","decor_fn":salon_decor,
                "furniture":[{"type":"felt_table","bounds":(W//2-60,260,W//2+60,340),"label":""}],
                "doors":[LDOOR],
                "npcs":[{"id":"salon_host","x":W//2,"y":220,"name":"Host Vivienne","col":"#f0d0a0",
                          "hat_col":PURPLE,"body_col":PURPLE,"line":"Double or Nothing.\nAre you feeling lucky?","game":"vip_double"}]
            },
            "bj_room":{
                "title":"High Stakes BJ","floor":"#1a0c04","wall":"#1a0c04","decor_fn":bj_decor,
                "furniture":[{"type":"felt_table","bounds":(W//2-230,240,W//2+230,395),"label":""}],
                "doors":[LDOOR],
                "npcs":[{"id":"bj_dealer","x":W//2,"y":205,"name":"Dealer Maurice","col":"#f0d0a0",
                          "hat_col":"#1a0000","body_col":"#1a0000","line":"Minimum $500.\nReady to play?","game":"vip_bj"}]
            },
            "poker":{
                "title":"Poker Room","floor":"#031a08","wall":"#031a08","decor_fn":poker_decor,
                "furniture":[{"type":"felt_table","bounds":(W//2-260,200,W//2+260,420),"label":""}],
                "doors":[LDOOR],
                "npcs":[{"id":"poker_host","x":W//2,"y":175,"name":"Dealer Renard","col":"#f0d0a0",
                          "hat_col":"#031a08","body_col":"#031a08","line":"VIP Hold'em.\nTake a seat.","game":"vip_poker"}]
            },
            "gold_hall":{
                "title":"Golden Hall","floor":"#1a1000","wall":"#1a1000","decor_fn":gold_decor,
                "furniture":[],
                "doors":[LDOOR],
                "npcs":[{"id":"croupier","x":W//2,"y":185,"name":"Croupier Élise","col":"#f0d0a0",
                          "hat_col":"#3a2800","body_col":"#3a2800","line":"Golden Roulette.\nPlace your bets.","game":"vip_roulette"}]
            },
            "raffle_room":{
                "title":"VIP Raffle Room","floor":"#0d0820","wall":"#08051a","decor_fn":raffle_decor,
                "furniture":[],
                "doors":[LDOOR],
                "npcs":[{"id":"raffle_host","x":W//2,"y":200,"name":"Host Margaux","col":"#f0d0a0",
                          "hat_col":PURPLE,"body_col":PURPLE,
                          "line":"★ VIP Raffle! ★\n$100 per ticket, up to 10.","game":"hotel_raffle"}]
            },
        }

    def _make_shop_rooms(self):
        def main_decor(c):
            # ── Checkerboard tile floor ───────────────────────
            ts=48
            for row in range(H//ts+1):
                for col2 in range(W//ts+1):
                    shade=(row+col2)%2
                    c.create_rectangle(col2*ts,65+row*ts,col2*ts+ts-1,65+row*ts+ts-1,
                                       fill="#e8e0d4" if shade else "#d0c8bc",outline="#c0b8ac",width=1)
            # ── Teal skirting board ───────────────────────────
            c.create_rectangle(0,65,W,76,fill="#2a7a5a",outline="")
            # ── Track lighting bar along ceiling ─────────────
            c.create_rectangle(60,66,W-60,78,fill="#555",outline="#888",width=1)
            for lx in range(100,W-80,90):
                c.create_oval(lx-8,68,lx+8,80,fill="#ffee88",outline="#aaa",width=1)
                c.create_line(lx,80,lx,92,fill="#888",width=2)
            # ── Back wall display shelves ─────────────────────
            c.create_rectangle(0,76,W,200,fill="#f0e8d8",outline="")
            c.create_rectangle(0,192,W,200,fill="#2a7a5a",outline="")
            # Shelf with folded clothes
            for sx in range(20,W-20,90):
                c.create_rectangle(sx,100,sx+78,194,fill="#e8e0d0",outline="#c0b090",width=1)
                # Stacked folded items
                for fi,(fc) in enumerate(["#cc6688","#5588cc","#88cc55","#cc8833"]):
                    fy=110+fi*18
                    c.create_rectangle(sx+6,fy,sx+72,fy+14,fill=fc,outline="#333333",width=1)
                    c.create_line(sx+6,fy+7,sx+72,fy+7,fill="#444444",width=1)
            # ── Left clothes rack ─────────────────────────────
            rx1=30; ry=230; rlen=260
            c.create_line(rx1,ry-6,rx1,ry+6,fill="#888",width=4)           # left stand
            c.create_line(rx1+rlen,ry-6,rx1+rlen,ry+6,fill="#888",width=4) # right stand
            c.create_line(rx1,ry,rx1+rlen,ry,fill="#aaa",width=5)           # rail
            # Hanging clothes
            outfit_cols=["#cc6688","#5588cc","#88aa44","#cc8833","#aa55cc","#44aacc","#ee4444","#44cc88"]
            for hi,hcol in enumerate(outfit_cols[:8]):
                hx=rx1+16+hi*30; hy=ry
                # Hanger hook
                c.create_arc(hx-8,hy-12,hx+8,hy,start=0,extent=180,outline="#888",style="arc",width=2)
                c.create_line(hx,hy,hx,hy+4,fill="#aaa",width=2)
                # Hanger bar
                c.create_line(hx-12,hy+4,hx+12,hy+4,fill="#aaa",width=2)
                # Garment
                c.create_polygon(hx-12,hy+4,hx-16,hy+48,hx+16,hy+48,hx+12,hy+4,
                                 fill=hcol,outline="#222222",width=1)
                c.create_line(hx-12,hy+4,hx-16,hy+18,fill="#333333",width=2)
                c.create_line(hx+12,hy+4,hx+16,hy+18,fill="#333333",width=2)
            # ── Right clothes rack ────────────────────────────
            rx2=W-310; ry2=230; rlen2=260
            c.create_line(rx2,ry2-6,rx2,ry2+6,fill="#888",width=4)
            c.create_line(rx2+rlen2,ry2-6,rx2+rlen2,ry2+6,fill="#888",width=4)
            c.create_line(rx2,ry2,rx2+rlen2,ry2,fill="#aaa",width=5)
            for hi,hcol in enumerate(["#ffaa44","#cc44aa","#4466cc","#44cc66","#ee6633","#8844cc","#ccaa22","#44aaee"]):
                hx=rx2+16+hi*30; hy=ry2
                c.create_arc(hx-8,hy-12,hx+8,hy,start=0,extent=180,outline="#888",style="arc",width=2)
                c.create_line(hx,hy,hx,hy+4,fill="#aaa",width=2)
                c.create_line(hx-12,hy+4,hx+12,hy+4,fill="#aaa",width=2)
                c.create_polygon(hx-12,hy+4,hx-16,hy+44,hx+16,hy+44,hx+12,hy+4,
                                 fill=hcol,outline="#222222",width=1)
            # ── Centre display table ──────────────────────────
            ctx=W//2; cty=360
            c.create_rectangle(ctx-80,cty,ctx+80,cty+16,fill="#c0a870",outline="#8B6914",width=2)
            c.create_rectangle(ctx-76,cty+16,ctx+76,cty+22,fill="#8B6914",outline="")
            c.create_rectangle(ctx-72,cty+22,ctx-64,cty+68,fill="#a08040",outline="#8B6914",width=1)
            c.create_rectangle(ctx+64,cty+22,ctx+72,cty+68,fill="#a08040",outline="#8B6914",width=1)
            # Folded items on table
            for ti,tcol in enumerate(["#dd5577","#5577dd","#55bb44"]):
                tx=ctx-52+ti*36
                c.create_rectangle(tx,cty-22,tx+30,cty,fill=tcol,outline="#333333",width=1)
                c.create_line(tx,cty-11,tx+30,cty-11,fill="#444444",width=1)
            # ── Cash register counter ─────────────────────────
            ccx=W-120; ccy=480
            c.create_rectangle(ccx-60,ccy,ccx+60,ccy+16,fill="#c0a870",outline="#8B6914",width=2)
            c.create_rectangle(ccx-56,ccy+16,ccx+56,ccy+22,fill="#8B6914",outline="")
            c.create_rectangle(ccx-52,ccy+22,ccx-46,ccy+60,fill="#a08040",outline="#8B6914",width=1)
            c.create_rectangle(ccx+46,ccy+22,ccx+52,ccy+60,fill="#a08040",outline="#8B6914",width=1)
            # Register
            c.create_rectangle(ccx-30,ccy-40,ccx+30,ccy,fill="#333",outline="#555",width=2)
            c.create_rectangle(ccx-24,ccy-34,ccx+24,ccy-6,fill="#111",outline="#444",width=1)
            for ky in range(ccy-30,ccy-8,8):
                for kx in range(ccx-20,ccx+22,8):
                    c.create_rectangle(kx,ky,kx+5,ky+5,fill="#444",outline="#222",width=1)
            c.create_text(ccx,ccy-44,text="CASH",fill="#888",
                          font=tkfont.Font(family="Courier New",size=7,weight="bold"))
            # ── Display mannequin left ────────────────────────
            mx2=120; my2=440
            c.create_oval(mx2-14,my2-70,mx2+14,my2-44,fill="#e8c07a",outline="#c0a060",width=1)
            c.create_rectangle(mx2-18,my2-44,mx2+18,my2+14,fill="#cc5577",outline="#aa3355",width=1)
            c.create_line(mx2-18,my2-30,mx2-36,my2-10,fill="#cc5577",width=6)
            c.create_line(mx2+18,my2-30,mx2+36,my2-10,fill="#cc5577",width=6)
            c.create_rectangle(mx2-8,my2+14,mx2-2,my2+52,fill="#555",outline="#333",width=1)
            c.create_rectangle(mx2+2,my2+14,mx2+8,my2+52,fill="#555",outline="#333",width=1)
            c.create_oval(mx2-20,my2+48,mx2+20,my2+58,fill="#333",outline="")
            # ── Store sign on back wall ───────────────────────
            c.create_rectangle(W//2-110,78,W//2+110,116,fill="#1a4a2a",outline="#2a7a5a",width=3)
            c.create_text(W//2,97,text="✦  BOUTIQUE  ✦",fill="#f5e8c0",
                          font=tkfont.Font(family="Georgia",size=13,weight="bold"))
            # ── Full length mirror ────────────────────────────
            c.create_rectangle(W-72,200,W-8,500,fill="#0a0a18",outline="#2a7a5a",width=3)
            c.create_rectangle(W-68,204,W-12,496,fill="#0c0c22",outline="#333",width=1)
            c.create_text(W-40,498,text="↕",fill="#2a7a5a",font=tkfont.Font(size=10))

        def cr_decor(c):
            # ── Warm cream walls ──────────────────────────────
            c.create_rectangle(0,65,W,H-30,fill="#f0e8d8",outline="")
            # Subtle wallpaper stripe
            for wx2 in range(0,W,30):
                c.create_line(wx2,65,wx2,H-30,fill="#e8e0cc",width=1)
            # Teal skirting boards top and bottom
            c.create_rectangle(0,65,W,80,fill="#2a7a5a",outline="")
            c.create_rectangle(0,H-42,W,H-30,fill="#2a7a5a",outline="")
            # ── Curtain rail across full width ───────────────
            c.create_rectangle(40,80,W-40,94,fill="#888",outline="#aaa",width=1)
            for rx in range(60,W-40,28):
                c.create_oval(rx-5,78,rx+5,88,fill="#c0a060",outline=GOLD,width=1)
            # ── Left cubicle curtain (drawn open) ────────────
            for drape,ddir in [(80,1),(W-80,-1)]:
                for fold in range(6):
                    fx=drape+fold*14*ddir
                    c.create_rectangle(fx,94,fx+10*ddir,H-44,
                                       fill="#2a7a5a" if fold%2==0 else "#237060",outline="")
                c.create_line(drape,94,drape,H-44,fill="#1a5a3a",width=2)
            # ── Three-panel floor mirror centre ──────────────
            for pi,pang in [(-1,0),(0,0),(1,0)]:
                px3=W//2+pi*72; pw=62; ph=360; py3=90
                c.create_rectangle(px3-pw//2-4,py3-4,px3+pw//2+4,py3+ph+4,
                                   fill="#2a7a5a",outline="#1a5a3a",width=2)
                c.create_rectangle(px3-pw//2,py3,px3+pw//2,py3+ph,
                                   fill="#c8d8e8",outline="#9ab0c0",width=1)
                # Reflection: tiny player in centre panel only
                if pi==0:
                    sk=SKINS[self.equipped_skin]
                    mx2=px3; my3=py3+ph//2
                    c.create_oval(mx2-8,my3+16,mx2+8,my3+22,fill="#222",outline="")
                    c.create_rectangle(mx2-4,my3+4,mx2-1,my3+18,fill=sk["legs"],outline=DARK,width=1)
                    c.create_rectangle(mx2+1,my3+4,mx2+4,my3+18,fill=sk["legs"],outline=DARK,width=1)
                    c.create_rectangle(mx2-6,my3-4,mx2+6,my3+6,fill=sk["body"],outline=DARK,width=1)
                    c.create_rectangle(mx2-10,my3-3,mx2-6,my3+4,fill=sk["body"],outline=DARK,width=1)
                    c.create_rectangle(mx2+6,my3-3,mx2+10,my3+4,fill=sk["body"],outline=DARK,width=1)
                    c.create_oval(mx2-6,my3-16,mx2+6,my3-4,fill=sk["face"],outline=DARK,width=1)
                    c.create_rectangle(mx2-8,my3-19,mx2+8,my3-15,fill=sk["hat"],outline=DARK)
                    c.create_rectangle(mx2-5,my3-27,mx2+5,my3-19,fill=sk["hat"],outline=DARK)
                    c.create_line(mx2-5,my3-23,mx2+5,my3-23,fill=sk["stripe"],width=1)
            # ── Padded bench ─────────────────────────────────
            c.create_rectangle(W//2-90,H-110,W//2+90,H-68,fill="#d0a870",outline="#8B6914",width=2)
            c.create_rectangle(W//2-86,H-106,W//2+86,H-72,fill="#e0b880",outline="#c09840",width=1)
            for bx4 in range(W//2-70,W//2+72,36):
                c.create_line(bx4,H-106,bx4,H-72,fill="#c09840",width=1)
            c.create_rectangle(W//2-90,H-68,W//2+90,H-58,fill="#8B6914",outline="#5a3a00",width=1)
            for leg in [W//2-78,W//2+78]:
                c.create_rectangle(leg-6,H-58,leg+6,H-44,fill="#8B6914",outline="#5a3a00",width=1)
            # ── Hooks on side walls ───────────────────────────
            for hx2,items in [(30,["#cc6688","#5588cc"]),(W-30,["#88cc55","#cc8833"])]:
                for hi,hcol2 in enumerate(items):
                    hy2=200+hi*80
                    c.create_oval(hx2-5,hy2-5,hx2+5,hy2+5,fill="#8B6914",outline=GOLD,width=1)
                    c.create_arc(hx2-8,hy2,hx2+8,hy2+18,start=0,extent=180,outline=GOLD,style="arc",width=2)
                    # Hanging garment
                    c.create_polygon(hx2-10,hy2+18,hx2-14,hy2+52,hx2+14,hy2+52,hx2+10,hy2+18,
                                     fill=hcol2,outline="#555",width=1)
            # ── Sign ─────────────────────────────────────────
            c.create_rectangle(W//2-100,82,W//2+100,114,fill="#1a4a2a",outline="#2a7a5a",width=2)
            c.create_text(W//2,98,text="CHANGING ROOM",fill="#f5e8c0",
                          font=tkfont.Font(family="Georgia",size=11,weight="bold"))
            # ── Track lighting ────────────────────────────────
            c.create_rectangle(W//2-120,80,W//2+120,88,fill="#555",outline="#777",width=1)
            for lx2 in [W//2-80,W//2,W//2+80]:
                c.create_oval(lx2-7,83,lx2+7,91,fill="#ffee88",outline="#aaa",width=1)

        return {
            "main":{
                "title":"Boutique","floor":"#2a1a08","wall":"#1a0c04","decor_fn":main_decor,
                "furniture":[],
                "doors":[
                    {"to":"exit",          "x":W//2+60, "y":638,"w":170,"h":34,"col":"#1a0c04","label":"Exit Shop"},
                    {"to":"changing_room", "x":W//2-160,"y":638,"w":180,"h":34,"col":"#2a1a08","label":"Changing Room →"},
                ],
                "npcs":[{"id":"shopkeeper","x":W//2,"y":280,"name":"Shopkeeper","col":"#f0d0a0",
                         "hat_col":"#1a3a1a","body_col":"#1a3a1a",
                         "line":"Welcome! Browse our\nexclusive skins.","game":"shop_screen"}]
            },
            "changing_room":{
                "title":"Changing Room","floor":"#1e1208","wall":"#1a0a04","decor_fn":cr_decor,
                "furniture":[],
                "doors":[{"to":"main","x":W//2-90,"y":638,"w":180,"h":34,"col":"#1a0c04","label":"← Back to Shop"}],
                "npcs":[{"id":"mirror_npc","x":W//2,"y":480,"name":"Mirror","col":"#c8c8ff",
                         "hat_col":"#0c0c1e","body_col":"#0c0c1e",
                         "line":"Change your look.\nWhich skin?","game":"change_skin"}]
            },
        }

    # ── helper: draw a scaled player preview on canvas ────────────────────
    def _draw_skin_preview(self,c,sid,cx,cy,scale=1,tag="skin_prev"):
        sk=SKINS[sid]; s=scale
        c.create_oval(cx-int(22*s),cy+int(28*s),cx+int(22*s),cy+int(38*s),
                      fill="#111",outline="",tags=tag)
        c.create_rectangle(cx-int(10*s),cy+int(8*s),cx-int(2*s),cy+int(30*s),
                           fill=sk["legs"],outline=DARK,width=1,tags=tag)
        c.create_rectangle(cx+int(2*s),cy+int(8*s),cx+int(10*s),cy+int(30*s),
                           fill=sk["legs"],outline=DARK,width=1,tags=tag)
        c.create_rectangle(cx-int(16*s),cy-int(8*s),cx+int(16*s),cy+int(10*s),
                           fill=sk["body"],outline=DARK,width=1,tags=tag)
        c.create_rectangle(cx-int(24*s),cy-int(6*s),cx-int(16*s),cy+int(6*s),
                           fill=sk["body"],outline=DARK,width=1,tags=tag)
        c.create_rectangle(cx+int(16*s),cy-int(6*s),cx+int(24*s),cy+int(6*s),
                           fill=sk["body"],outline=DARK,width=1,tags=tag)
        c.create_oval(cx-int(14*s),cy-int(36*s),cx+int(14*s),cy-int(8*s),
                      fill=sk["face"],outline=DARK,width=1,tags=tag)
        c.create_rectangle(cx-int(20*s),cy-int(40*s),cx+int(20*s),cy-int(34*s),
                           fill=sk["hat"],outline=DARK,tags=tag)
        c.create_rectangle(cx-int(13*s),cy-int(56*s),cx+int(13*s),cy-int(40*s),
                           fill=sk["hat"],outline=DARK,tags=tag)
        c.create_line(cx-int(13*s),cy-int(46*s),cx+int(13*s),cy-int(46*s),
                      fill=sk["stripe"],width=max(1,int(2*s)),tags=tag)

    def _shop_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("BOUTIQUE","#0a0800","#1a1000")
        skin_ids=list(SKINS.keys()); selected=[self.equipped_skin]
        LW=W//2-10   # left panel right edge
        PX=LW+120    # preview centre x

        # ── static chrome ────────────────────────────────────────────
        c.create_text(LW//2,88,text="ALL SKINS",fill=GOLD,
                      font=tkfont.Font(family="Georgia",size=13,weight="bold"))
        c.create_text(PX,88,text="PREVIEW",fill=GOLD,
                      font=tkfont.Font(family="Georgia",size=13,weight="bold"))
        c.create_line(LW+4,75,LW+4,H-30,fill="#333",width=1)
        c.create_text(LW+10,H-50,text=f"Balance: ${self.money:,}",fill=GOLD,
                      font=self.fnt_small,anchor="w",tags="sh_bal")

        # ── list (unique tag per row — no binding accumulation) ───────
        def draw_list():
            c.delete("sh_list")
            for i,sid in enumerate(skin_ids):
                sk=SKINS[sid]; y=110+i*56
                owned=sid in self.owned_skins; eq=sid==self.equipped_skin
                bg="#182818" if eq else("#121a12" if owned else "#1a1008")
                ol=GREEN_C if eq else(GOLD if owned else "#444")
                rtag=f"sh_row_{i}"          # unique per row — safe to rebind
                c.delete(rtag)
                round_rect(c,18,y,LW-8,y+48,r=7,fill=bg,outline=ol,width=2,tags=("sh_list",rtag))
                # Colour swatch
                c.create_rectangle(28,y+6,46,y+42,fill=sk["body"],outline=DARK,width=1,tags=("sh_list",rtag))
                c.create_rectangle(28,y+6,46,y+24,fill=sk["hat"],outline="",tags=("sh_list",rtag))
                # Name + price
                c.create_text(54,y+16,text=sk["name"],fill=GOLD if eq else CREAM,
                              font=tkfont.Font(family="Courier New",size=10,weight="bold"),
                              anchor="w",tags=("sh_list",rtag))
                price_txt= "✓ Equipped" if eq else("Owned" if owned else f"${sk['price']:,}")
                pcol=GREEN_C if eq else(GOLD if owned else "#888")
                c.create_text(54,y+34,text=price_txt,fill=pcol,
                              font=tkfont.Font(family="Courier New",size=8),
                              anchor="w",tags=("sh_list",rtag))
                c.tag_bind(rtag,"<Button-1>",lambda e,s=sid:select(s))

        # ── preview panel ─────────────────────────────────────────────
        def draw_preview(sid):
            c.delete("sh_prev"); c.delete("sh_info"); c.delete("sh_act")
            sk=SKINS[sid]
            # Large player preview
            self._draw_skin_preview(c,sid,PX,320,scale=1.6,tag="sh_prev")
            # Info text
            owned=sid in self.owned_skins; eq=sid==self.equipped_skin
            c.create_text(PX,175,text=sk["name"],fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=17,weight="bold"),tags="sh_info")
            c.create_text(PX,206,text=sk["desc"],fill=CREAM,
                          font=tkfont.Font(family="Courier New",size=9),tags="sh_info")
            status="✓ Equipped" if eq else("Owned — go to Changing Room" if owned else f"${sk['price']:,}")
            scol=GREEN_C if eq else(GOLD if owned else RED_C)
            c.create_text(PX,232,text=status,fill=scol,
                          font=tkfont.Font(family="Courier New",size=10,weight="bold"),tags="sh_info")
            # Action button drawn on canvas — rebinding sh_act is always fresh
            if not eq and not owned:
                round_rect(c,PX-70,440,PX+70,476,r=8,fill="#3a0000",outline=RED_C,width=2,tags="sh_act")
                c.create_text(PX,458,text=f"BUY  ${sk['price']:,}",fill=CREAM,
                              font=tkfont.Font(family="Courier New",size=10,weight="bold"),tags="sh_act")
                c.tag_bind("sh_act","<Button-1>",lambda e,s=sid:buy(s))

        def select(sid): selected[0]=sid; draw_preview(sid); draw_list()

        def buy(sid):
            sk=SKINS[sid]
            if self.money<sk["price"]:
                c.delete("sh_msg")
                c.create_text(PX,500,text=f"Need ${sk['price']:,}!",fill=RED_C,
                              font=self.fnt_small,tags="sh_msg")
                self.after(1600,lambda:c.delete("sh_msg")); return
            self.money-=sk["price"]; self.owned_skins.add(sid)
            self._refresh_balance_text()
            c.delete("sh_bal")
            c.create_text(LW+10,H-50,text=f"Balance: ${self.money:,}",fill=GOLD,
                          font=self.fnt_small,anchor="w",tags="sh_bal")
            c.delete("sh_msg")
            c.create_text(PX,500,text="Purchased! Head to the Changing Room to equip.",
                          fill=GREEN_C,font=self.fnt_small,tags="sh_msg",width=200)
            self.after(2200,lambda:c.delete("sh_msg"))
            draw_list(); draw_preview(sid)

        draw_list(); draw_preview(selected[0])
        self._make_btn(W//2-60,H-52,"← Back",self._back_to_interior,col="#222",fg=CREAM,w=110)

    def _change_skin_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("CHANGING ROOM","#0a0800","#180e04")
        owned_ids=[sid for sid in SKINS if sid in self.owned_skins]
        selected=[self.equipped_skin]

        c.create_text(W//4,88,text="YOUR SKINS",fill=GOLD,
                      font=tkfont.Font(family="Georgia",size=13,weight="bold"))
        c.create_text(W*3//4,88,text="WEARING NOW",fill=GOLD,
                      font=tkfont.Font(family="Georgia",size=13,weight="bold"))
        c.create_line(W//2,75,W//2,H-30,fill="#333",width=1)

        def draw_list():
            c.delete("cr_list")
            for i,sid in enumerate(owned_ids):
                sk=SKINS[sid]; y=115+i*64
                eq=sid==self.equipped_skin
                rtag=f"cr_row_{i}"
                c.delete(rtag)
                round_rect(c,18,y,W//2-12,y+56,r=8,
                           fill="#182818" if eq else "#111a11",
                           outline=GREEN_C if eq else GOLD,width=2,tags=("cr_list",rtag))
                self._draw_skin_preview(c,sid,60,y+28,scale=0.7,tag=rtag)
                c.create_text(94,y+18,text=sk["name"],
                              fill=GREEN_C if eq else CREAM,
                              font=tkfont.Font(family="Courier New",size=11,weight="bold"),
                              anchor="w",tags=("cr_list",rtag))
                c.create_text(94,y+36,text="✓ Wearing" if eq else sk["desc"],
                              fill=GREEN_C if eq else "#888",
                              font=tkfont.Font(family="Courier New",size=8),
                              anchor="w",tags=("cr_list",rtag))
                c.tag_bind(rtag,"<Button-1>",lambda e,s=sid:select(s))

        def draw_preview(sid):
            c.delete("cr_prev"); c.delete("cr_info")
            self._draw_skin_preview(c,sid,W*3//4,310,scale=2.2,tag="cr_prev")
            sk=SKINS[sid]; eq=sid==self.equipped_skin
            c.create_text(W*3//4,175,text=sk["name"],fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=18,weight="bold"),tags="cr_info")
            c.create_text(W*3//4,210,text=sk["desc"],fill=CREAM,
                          font=tkfont.Font(family="Courier New",size=9),tags="cr_info")
            c.delete("cr_act")
            if eq:
                c.create_text(W*3//4,450,text="✓ Currently wearing",fill=GREEN_C,
                              font=tkfont.Font(family="Courier New",size=11,weight="bold"),tags="cr_act")
            else:
                round_rect(c,W*3//4-70,438,W*3//4+70,474,r=8,
                           fill="#0a2a0a",outline=GREEN_C,width=2,tags="cr_act")
                c.create_text(W*3//4,456,text="WEAR THIS",fill=GREEN_C,
                              font=tkfont.Font(family="Courier New",size=11,weight="bold"),tags="cr_act")
                c.tag_bind("cr_act","<Button-1>",lambda e,s=sid:equip(s))

        def select(sid): selected[0]=sid; draw_preview(sid); draw_list()

        def equip(sid):
            self.equipped_skin=sid; selected[0]=sid
            draw_preview(sid); draw_list()

        draw_list(); draw_preview(selected[0])
        self._make_btn(W//2-60,H-52,"← Back",self._back_to_interior,col="#222",fg=CREAM,w=110)

    def _make_den_rooms(self):
        def decor(c):
            # Dark green felt floor
            for row in range(H//36+1):
                for col2 in range(W//36+1):
                    shade=(row+col2)%2
                    c.create_rectangle(col2*36,65+row*36,col2*36+35,65+row*36+35,
                                       fill="#0a2a0e" if shade else "#0c3010",outline="#0e3612",width=1)
            # Dark wood panelling on walls top section
            c.create_rectangle(0,65,W,180,fill="#1a0c04",outline="")
            c.create_rectangle(0,172,W,180,fill="#8B6914",outline="")
            for wx6 in range(0,W,80):
                c.create_rectangle(wx6,65,wx6+78,178,fill="#1e0e06" if (wx6//80)%2==0 else "#180a02",outline="#0a0600",width=1)
                c.create_rectangle(wx6+6,72,wx6+72,172,fill="#160800",outline="#2a1400",width=1)
            # Card suit mural on back wall
            for si2,(sym2,scol2) in enumerate([("♠","#6622cc"),("♥","#cc0033"),("♦","#cc0033"),("♣","#6622cc")]):
                c.create_text(x1_d:=80+si2*((W-120)//4),128,text=sym2,fill=scol2,
                              font=tkfont.Font(family="Georgia",size=32,weight="bold"))
            # Left display case — card decks
            c.create_rectangle(20,200,220,480,fill="#0a1a0a",outline="#4a2a0a",width=3)
            c.create_rectangle(24,204,216,476,fill="#060e06",outline="#3a2208",width=1)
            c.create_text(120,218,text="CARD SKINS",fill=GOLD,
                          font=tkfont.Font(family="Courier New",size=8,weight="bold"))
            # Card deck previews in case
            for ci2,(cname,cbk) in enumerate([("Classic","#8B0000"),("Navy","#001a66"),("Emerald","#004400"),("Gilded","#5a3a00")]):
                cx6=60+ci2%2*80; cy6=250+ci2//2*100
                round_rect(c,cx6-18,cy6-26,cx6+18,cy6+26,r=4,fill="white",outline="#aaa",width=1)
                round_rect(c,cx6-14,cy6-22,cx6+14,cy6+22,r=3,fill=cbk,outline=GOLD,width=1)
                c.create_text(cx6,cy6,text="♠",fill=GOLD,font=tkfont.Font(size=10))
                c.create_text(cx6,cy6+36,text=cname,fill=CREAM,font=tkfont.Font(family="Courier New",size=6))
            # Right display case — dice
            c.create_rectangle(W-220,200,W-20,480,fill="#0a1a0a",outline="#4a2a0a",width=3)
            c.create_rectangle(W-216,204,W-24,476,fill="#060e06",outline="#3a2208",width=1)
            c.create_text(W-120,218,text="DICE SKINS",fill=GOLD,
                          font=tkfont.Font(family="Courier New",size=8,weight="bold"))
            # Dice previews in case
            for di2,(dcol2,ddot2) in enumerate([("#eeeeee","#111"),("#111111","#eee"),("#880000","#fff"),("#001a88","#fff")]):
                dx6=W-200+di2%2*80; dy6=246+di2//2*100
                round_rect(c,dx6-16,dy6-16,dx6+16,dy6+16,r=6,fill=dcol2,outline="#888",width=1)
                for pip in [(-.25,-.25),(.25,.25)]:
                    c.create_oval(dx6+pip[0]*24-4,dy6+pip[1]*24-4,
                                  dx6+pip[0]*24+4,dy6+pip[1]*24+4,fill=ddot2,outline="")
                c.create_text(dx6,dy6+30,text=["Classic","Obsidian","Ruby","Sapphire"][di2],
                              fill=CREAM,font=tkfont.Font(family="Courier New",size=6))
            # Centre demo table
            round_rect(c,W//2-160,300,W//2+160,460,r=20,fill="#1a5c2a",outline="#8B6914",width=3)
            round_rect(c,W//2-150,310,W//2+150,450,r=16,fill="#1f6830",outline="")
            c.create_text(W//2,380,text="TRY BEFORE YOU BUY",fill="#1a8830",
                          font=tkfont.Font(family="Courier New",size=9,weight="bold"))
            # Overhead pendant lights
            for lx3 in [W//4,W//2,W*3//4]:
                c.create_line(lx3,65,lx3,110,fill="#555",width=2)
                c.create_oval(lx3-14,102,lx3+14,128,fill="#ffdd88",outline="#8B6914",width=1)
            # Sign
            c.create_rectangle(W//2-110,68,W//2+110,106,fill="#08000f",outline="#aa44ff",width=2)
            c.create_text(W//2,87,text="♠ THE DEN ♠",fill="#cc88ff",
                          font=tkfont.Font(family="Georgia",size=13,weight="bold"))
            # Shelf of chips left wall
            c.create_rectangle(20,500,220,524,fill="#3a2008",outline="#8B6914",width=2)
            for ci3 in range(8):
                cc3=["#cc2222","#1a1a88","#228822","#ccaa22","#aa22aa","#22aacc","#cccccc","#111"][ci3]
                c.create_oval(38+ci3*22,500,56+ci3*22,524,fill=cc3,outline="#fff",width=1)

        return {"main":{
            "title":"The Den","floor":"#0a2a0e","wall":"#0a0a1a","decor_fn":decor,
            "furniture":[],
            "doors":[{"to":"exit","x":W//2-90,"y":638,"w":180,"h":34,"col":"#0a001a","label":"Exit The Den"}],
            "npcs":[{"id":"den_keeper","x":W//2,"y":270,"name":"The Keeper","col":"#d0d0f0",
                     "hat_col":"#220044","body_col":"#110022",
                     "line":"Cards. Dice. Quality\ngear for quality games.","game":"den_shop"}]
        }}

    def _den_shop_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("THE DEN","#04000a","#080018")
        tab=["cards"]
        DIVX=W//2+10; LIST_START=190; ROW_H=58

        c.create_text(W//2,76,text="♠  THE DEN  ♠",fill="#cc88ff",
                      font=tkfont.Font(family="Georgia",size=15,weight="bold"))
        c.create_text(W-20,76,text=f"${self.money:,}",fill=GOLD,
                      font=self.fnt_body,anchor="e",tags="den_bal")
        c.create_line(0,170,W,170,fill="#330055",width=1)
        c.create_line(DIVX,170,DIVX,H-30,fill="#330055",width=1)

        def draw_card_prev(sid,cx7,cy7,scale=1.0,tag="den_prev"):
            cs=CARD_SKINS[sid]; w2=int(52*scale); h2=int(76*scale)
            round_rect(c,cx7-w2//2,cy7-h2//2,cx7+w2//2,cy7+h2//2,r=int(5*scale),
                       fill=cs["face"],outline=cs["border"],width=max(1,int(2*scale)),tags=tag)
            round_rect(c,cx7-w2//2+int(3*scale),cy7-h2//2+int(3*scale),
                       cx7+w2//2-int(3*scale),cy7+h2//2-int(3*scale),
                       r=int(4*scale),fill=cs["back"],outline=cs["border"],
                       width=max(1,int(2*scale)),tags=tag)
            # Centered 3×4 grid of dots
            cols,rows=3,4
            gw=(cols-1)*int(10*scale); gh=(rows-1)*int(12*scale)
            for pi in range(cols):
                for pj in range(rows):
                    dx8=cx7-gw//2+pi*int(10*scale)
                    dy8=cy7-gh//2+pj*int(12*scale)
                    r8=max(2,int(3*scale))
                    c.create_oval(dx8-r8,dy8-r8,dx8+r8,dy8+r8,fill=cs["border"],outline="",tags=tag)

        def draw_die_prev(sid,cx7,cy7,size=52,tag="den_prev"):
            ds=DICE_SKINS[sid]
            round_rect(c,cx7-size//2,cy7-size//2,cx7+size//2,cy7+size//2,
                       r=8,fill=ds["col"],outline=ds["ol"],width=2,tags=tag)
            for px3,py3 in [(-.25,-.25),(.25,.25),(0,0)]:
                c.create_oval(cx7+int(px3*size)-4,cy7+int(py3*size)-4,
                              cx7+int(px3*size)+4,cy7+int(py3*size)+4,
                              fill=ds["dot"],outline="",tags=tag)

        selected={"cards":"classic","dice":"classic"}

        # ── Tabs — unique tag per button ──────────────────────
        def draw_tabs():
            c.delete("tab_cards","tab_dice")
            for tname,tx7,sym in [("cards",W//4,"♠ CARDS"),("dice",W*3//4,"⚄ DICE")]:
                active=tab[0]==tname; ttag=f"tab_{tname}"
                round_rect(c,tx7-80,110,tx7+80,162,r=8,
                           fill="#220044" if active else "#0a0018",
                           outline="#aa44ff" if active else "#440066",width=2,tags=ttag)
                c.create_text(tx7,136,text=sym,fill="#cc88ff" if active else "#664488",
                              font=tkfont.Font(family="Courier New",size=11,weight="bold"),tags=ttag)
                # Bind to unique tag — safe to rebind each draw
                c.tag_bind(ttag,"<Button-1>",lambda e,t=tname:switch_tab(t))

        def draw_list(tname):
            c.delete("den_list")
            items=CARD_SKINS if tname=="cards" else DICE_SKINS
            owned_set=self.owned_card_skins if tname=="cards" else self.owned_dice_skins
            eqd=self.equipped_card_skin if tname=="cards" else self.equipped_dice_skin
            for i,(sid,sk) in enumerate(items.items()):
                y7=LIST_START+i*ROW_H; owned=sid in owned_set; eq=sid==eqd
                rtag=f"den_row_{i}"
                c.delete(rtag)
                round_rect(c,12,y7,DIVX-10,y7+ROW_H-8,r=7,
                           fill="#18082a" if eq else("#120620" if owned else "#0e0418"),
                           outline="#aa44ff" if eq else(GOLD if owned else "#440066"),
                           width=2,tags=("den_list",rtag))
                if tname=="cards":
                    draw_card_prev(sid,42,y7+ROW_H//2-4,scale=0.48,tag=rtag)
                else:
                    draw_die_prev(sid,42,y7+ROW_H//2-4,size=30,tag=rtag)
                c.create_text(76,y7+14,text=sk["name"],
                              fill="#aa44ff" if eq else CREAM,
                              font=tkfont.Font(family="Courier New",size=10,weight="bold"),
                              anchor="w",tags=("den_list",rtag))
                ptxt="✓ Equipped" if eq else("Owned" if owned else f"${sk['price']:,}")
                pcol="#aa44ff" if eq else(GOLD if owned else "#888")
                c.create_text(76,y7+30,text=ptxt,fill=pcol,
                              font=tkfont.Font(family="Courier New",size=8),
                              anchor="w",tags=("den_list",rtag))
                c.tag_bind(rtag,"<Button-1>",lambda e,s=sid,t=tname:select(s,t))

        def draw_preview(sid,tname):
            c.delete("den_prev","den_info","den_act")
            sk=CARD_SKINS[sid] if tname=="cards" else DICE_SKINS[sid]
            owned_set=self.owned_card_skins if tname=="cards" else self.owned_dice_skins
            eqd=self.equipped_card_skin if tname=="cards" else self.equipped_dice_skin
            owned=sid in owned_set; eq=sid==eqd
            if tname=="cards":
                draw_card_prev(sid,W*3//4,330,scale=2.1,tag="den_prev")
            else:
                draw_die_prev(sid,W*3//4,330,size=120,tag="den_prev")
            c.create_text(W*3//4,196,text=sk["name"],fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=17,weight="bold"),tags="den_info")
            c.create_text(W*3//4,224,text=sk["desc"],fill=CREAM,
                          font=tkfont.Font(family="Courier New",size=9),tags="den_info")
            status="✓ Equipped" if eq else("Owned" if owned else f"${sk['price']:,}")
            scol="#aa44ff" if eq else(GOLD if owned else RED_C)
            c.create_text(W*3//4,250,text=status,fill=scol,
                          font=tkfont.Font(family="Courier New",size=10,weight="bold"),tags="den_info")
            if not eq and not owned:
                round_rect(c,W*3//4-70,468,W*3//4+70,500,r=8,
                           fill="#1a0033",outline="#aa44ff",width=2,tags="den_act")
                c.create_text(W*3//4,484,text=f"BUY  ${sk['price']:,}",fill=CREAM,
                              font=tkfont.Font(family="Courier New",size=10,weight="bold"),tags="den_act")
                c.tag_bind("den_act","<Button-1>",lambda e,s=sid,t=tname:buy(s,t))
            elif owned and not eq:
                round_rect(c,W*3//4-60,468,W*3//4+60,500,r=8,
                           fill="#0a1a2a",outline=GOLD,width=2,tags="den_act")
                c.create_text(W*3//4,484,text="EQUIP",fill=GOLD,
                              font=tkfont.Font(family="Courier New",size=10,weight="bold"),tags="den_act")
                c.tag_bind("den_act","<Button-1>",lambda e,s=sid,t=tname:equip(s,t))

        def switch_tab(tname):
            tab[0]=tname; draw_tabs(); draw_list(tname); draw_preview(selected[tname],tname)

        def select(sid,tname):
            selected[tname]=sid; draw_preview(sid,tname); draw_list(tname)

        def buy(sid,tname):
            sk=CARD_SKINS[sid] if tname=="cards" else DICE_SKINS[sid]
            if self.money<sk["price"]:
                c.delete("den_msg")
                c.create_text(W*3//4,520,text=f"Need ${sk['price']:,}!",fill=RED_C,
                              font=self.fnt_small,tags="den_msg")
                self.after(1600,lambda:c.delete("den_msg")); return
            self.money-=sk["price"]
            if tname=="cards": self.owned_card_skins.add(sid)
            else:              self.owned_dice_skins.add(sid)
            self._refresh_balance_text()
            c.delete("den_bal")
            c.create_text(W-20,76,text=f"${self.money:,}",fill=GOLD,
                          font=self.fnt_body,anchor="e",tags="den_bal")
            equip(sid,tname)

        def equip(sid,tname):
            if tname=="cards": self.equipped_card_skin=sid
            else:              self.equipped_dice_skin=sid
            selected[tname]=sid; draw_preview(sid,tname); draw_list(tname)

        draw_tabs(); draw_list(tab[0]); draw_preview(selected[tab[0]],tab[0])
        self._make_btn(W//2-60,H-50,"← Back",self._back_to_interior,col="#0a001a",fg="#cc88ff",w=110)

    def _make_bank_rooms(self):
        def decor(c):
            # Marble floor tiles
            for row in range(14):
                for col2 in range(16):
                    x1=col2*72; y1=65+row*40
                    shade=(row+col2)%2
                    col3="#e8f0f8" if shade else "#d8e4f0"
                    c.create_rectangle(x1,y1,x1+71,y1+39,fill=col3,outline="#b8c8d8",width=1)
            # Veining on tiles
            for row in range(14):
                for col2 in range(16):
                    if (row*17+col2*11)%7==0:
                        x1=col2*72+8; y1=65+row*40+6
                        c.create_line(x1,y1,x1+40,y1+20,fill="#c8d4e0",width=1)
            # Grand entrance arch / header band
            c.create_rectangle(0,65,W,130,fill="#1a3050",outline="")
            for px2 in range(0,W,140):
                c.create_rectangle(px2+6,70,px2+130,126,fill="",outline="#2a4a70",width=2)
                c.create_rectangle(px2+12,76,px2+124,120,fill="",outline="#1e3a5a",width=1)
            c.create_line(0,128,W,128,fill="#8B6914",width=3)
            c.create_line(0,131,W,131,fill="#5a4010",width=1)
            # Bank name sign
            round_rect(c,W//2-200,72,W//2+200,120,r=10,fill="#0d1e30",outline=GOLD,width=3)
            c.create_text(W//2,86,text="ROYAL BANK OF RG TOWN",fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=13,weight="bold"))
            c.create_text(W//2,108,text='"Est. since the first bad bet"',fill="#4a6888",
                          font=tkfont.Font(family="Georgia",size=8,slant="italic"))
            # Teller counter — long marble counter with three windows
            cx1,cy1,cx2,cy2=80,240,W-80,360
            # Counter shadow
            c.create_rectangle(cx1+6,cy2,cx2+6,cy2+18,fill="#aabbc8",outline="")
            # Counter body
            c.create_rectangle(cx1,cy1,cx2,cy2,fill="#d0dce8",outline="#8899aa",width=3)
            c.create_rectangle(cx1,cy1,cx2,cy1+16,fill="#e0ecf8",outline="")
            c.create_line(cx1+4,cy1+16,cx2-4,cy1+16,fill="#8899aa",width=1)
            # Three teller windows (glass panels above counter)
            for wi in range(3):
                wx3=cx1+80+wi*((cx2-cx1-160)//2)
                # Glass pane
                c.create_rectangle(wx3-50,160,wx3+50,cy1,fill="#d0e8f8",outline="#668899",width=2)
                c.create_rectangle(wx3-44,165,wx3+44,cy1-2,fill="#e0f0ff",outline="")
                # Window divider
                c.create_line(wx3,160,wx3,cy1,fill="#668899",width=2)
                c.create_line(wx3-50,192,wx3+50,192,fill="#668899",width=1)
                # Window number
                c.create_rectangle(wx3-20,162,wx3+20,182,fill="#1a3050",outline="#2a4a70",width=1)
                c.create_text(wx3,172,text=f"  {wi+1}  ",fill=GOLD,
                              font=tkfont.Font(family="Courier New",size=9,weight="bold"))
                # Slot in counter
                c.create_rectangle(wx3-28,cy1-2,wx3+28,cy1+4,fill="#445566",outline="#334455",width=1)
            # Vault door on left wall
            vx,vy=58,300
            c.create_rectangle(vx-44,vy-60,vx+44,vy+60,fill="#556677",outline="#334455",width=4)
            c.create_rectangle(vx-36,vy-52,vx+36,vy+52,fill="#445566",outline="#223344",width=2)
            c.create_oval(vx-20,vy-20,vx+20,vy+20,fill="#667788",outline="#445566",width=3)
            c.create_oval(vx-12,vy-12,vx+12,vy+12,fill="#778899",outline="#556677",width=2)
            c.create_line(vx,vy-20,vx,vy-8,fill="#334455",width=3)
            c.create_line(vx,vy+8,vx,vy+20,fill="#334455",width=3)
            c.create_line(vx-20,vy,vx-8,vy,fill="#334455",width=3)
            c.create_line(vx+8,vy,vx+20,vy,fill="#334455",width=3)
            c.create_text(vx,vy+80,text="VAULT",fill="#445566",
                          font=tkfont.Font(family="Courier New",size=8,weight="bold"))
            # Security camera on right wall
            camx=W-60; camy=155
            c.create_rectangle(camx-14,camy-8,camx+14,camy+8,fill="#1a1a2a",outline="#333",width=2)
            c.create_oval(camx-8,camy-5,camx+8,camy+5,fill="#222",outline="#444",width=1)
            c.create_oval(camx-4,camy-3,camx+4,camy+3,fill="#112233",outline="")
            c.create_line(camx+14,camy,camx+24,camy,fill="#333",width=2)
            c.create_rectangle(camx+20,camy-6,camx+28,camy+6,fill="#1a1a2a",outline="#333",width=1)
            # Waiting area chairs
            for chairx in [W//2-120,W//2,W//2+120]:
                c.create_rectangle(chairx-20,430,chairx+20,465,fill="#2a3a4a",outline="#1a2a3a",width=2)
                c.create_rectangle(chairx-20,415,chairx-14,432,fill="#2a3a4a",outline="#1a2a3a",width=1)
                c.create_rectangle(chairx+14,415,chairx+20,432,fill="#2a3a4a",outline="#1a2a3a",width=1)
                c.create_rectangle(chairx-20,408,chairx+20,420,fill="#3a4a5a",outline="#2a3a4a",width=1)
            # "TAKE A NUMBER" dispenser
            c.create_rectangle(cx2-50,380,cx2-10,420,fill="#aa2200",outline="#881800",width=2)
            c.create_text(cx2-30,400,text="TAKE\nNUM",fill="#ffddcc",
                          font=tkfont.Font(family="Courier New",size=7,weight="bold"),justify="center")
            # Floor mat
            c.create_rectangle(W//2-100,480,W//2+100,510,fill="#1a3050",outline="#2a4a70",width=2)
            c.create_text(W//2,495,text="WELCOME",fill="#4a6888",
                          font=tkfont.Font(family="Courier New",size=9))
        def acct_decor(c):
            # Clean tiled floor
            for row in range(14):
                for col2 in range(16):
                    x1=col2*72; y1=65+row*40; shade=(row+col2)%2
                    c.create_rectangle(x1,y1,x1+71,y1+39,
                                       fill="#e0eaf4" if shade else "#d0dce8",outline="#b8c8d8",width=1)
            # Blue header band
            c.create_rectangle(0,65,W,128,fill="#0d1e30",outline="")
            round_rect(c,W//2-180,72,W//2+180,118,r=8,fill="#071426",outline=GOLD,width=2)
            c.create_text(W//2,86,text="ACCOUNT SERVICES",fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=13,weight="bold"))
            c.create_text(W//2,108,text="Secure. Private. Always online.",fill="#4a6888",
                          font=tkfont.Font(family="Georgia",size=8,slant="italic"))
            c.create_line(0,128,W,128,fill="#8B6914",width=3)
            # Four ATM machines along the back wall
            atm_positions=[140,320,W-320,W-140]
            for ax in atm_positions:
                # Machine body
                c.create_rectangle(ax-44,138,ax+44,390,fill="#1a2a3a",outline="#2a4a6a",width=3)
                c.create_rectangle(ax-40,142,ax+40,386,fill="#0d1e2e",outline="#1e3a5a",width=1)
                # Screen
                c.create_rectangle(ax-30,155,ax+30,245,fill="#002a44",outline="#00aaff",width=2)
                c.create_text(ax,172,text="RG BANK ATM",fill="#00aaff",
                              font=tkfont.Font(family="Courier New",size=7,weight="bold"))
                c.create_text(ax,195,text="SAVE / LOAD",fill="#00dd88",
                              font=tkfont.Font(family="Courier New",size=8,weight="bold"))
                c.create_text(ax,215,text="GAME STATE",fill="#00dd88",
                              font=tkfont.Font(family="Courier New",size=8))
                c.create_rectangle(ax-28,232,ax+28,243,fill="#001a2a",outline="#005588",width=1)
                # Keypad
                c.create_rectangle(ax-26,258,ax+26,318,fill="#111",outline="#333",width=1)
                for row2 in range(3):
                    for col2 in range(3):
                        kx=ax-16+col2*16; ky=264+row2*18
                        c.create_rectangle(kx,ky,kx+12,ky+13,fill="#1a2a3a",outline="#334455",width=1)
                        c.create_text(kx+6,ky+7,text=str(row2*3+col2+1),fill="#4488aa",
                                      font=tkfont.Font(family="Courier New",size=6))
                # Card slot
                c.create_rectangle(ax-18,328,ax+18,338,fill="#000",outline="#335577",width=1)
                c.create_text(ax,346,text="INSERT CARD",fill="#335577",
                              font=tkfont.Font(family="Courier New",size=6))
                # Dispenser tray
                c.create_rectangle(ax-22,360,ax+22,376,fill="#0a1a2a",outline="#2a4a6a",width=2)
                # Indicator light
                c.create_oval(ax+26,150,ax+36,160,fill="#00ff44",outline="")
            # Waiting rope barriers
            for bx in [W//2-180,W//2+180]:
                c.create_rectangle(bx-4,300,bx+4,490,fill="#8B6914",outline=GOLD,width=1)
                c.create_oval(bx-12,290,bx+12,310,fill=GOLD,outline="#5a3a00",width=1)
                c.create_line(W//2-176,300,W//2+176,300,fill=GOLD,width=3,dash=(8,4))
            # Privacy screen between ATMs
            for px3 in [W//2-90,W//2+90]:
                c.create_rectangle(px3-4,138,px3+4,390,fill="#2a4a6a",outline="#1a3a5a",width=1)
            # Floor sign
            c.create_rectangle(W//2-90,480,W//2+90,508,fill="#0d1e30",outline="#2a4a70",width=2)
            c.create_text(W//2,494,text="SECURE ZONE",fill="#4a6888",
                          font=tkfont.Font(family="Courier New",size=9))

        return {
            "main":{
                "title":"The Royal Bank","floor":"#e8f0f8","wall":"#1a3050","decor_fn":decor,
                "furniture":[{"type":"counter","bounds":(80,240,W-80,360),"label":""}],
                "doors":[
                    {"to":"exit",   "x":W//2+90, "y":638,"w":160,"h":34,"col":"#334455","label":"Leave Bank"},
                    {"to":"account","x":W//2-100,"y":638,"w":170,"h":34,"col":"#0d1e30","label":"Account Room →"},
                ],
                "npcs":[{"id":"teller","x":W//2,"y":210,"name":"Teller Grace","col":"#e0c8a0",
                          "hat_col":"#001020","body_col":"#001a30",
                          "line":"Good day! Want to see\nyour account statement?","game":"bank_stats"}]
            },
            "account":{
                "title":"Account Services","floor":"#e0eaf4","wall":"#0d1e30","decor_fn":acct_decor,
                "furniture":[],
                "doors":[{"to":"main","x":W//2-90,"y":638,"w":180,"h":34,"col":"#0d1e30","label":"← Back to Bank"}],
                "npcs":[
                    {"id":"atm1","x":140,"y":410,"name":"ATM","col":"#00aaff",
                     "hat_col":"#0d1e30","body_col":"#0d1e30","line":"Save or load your\ngame state here.","game":"atm_screen"},
                    {"id":"atm2","x":320,"y":410,"name":"ATM","col":"#00aaff",
                     "hat_col":"#0d1e30","body_col":"#0d1e30","line":"Save or load your\ngame state here.","game":"atm_screen"},
                    {"id":"atm3","x":W-320,"y":410,"name":"ATM","col":"#00aaff",
                     "hat_col":"#0d1e30","body_col":"#0d1e30","line":"Save or load your\ngame state here.","game":"atm_screen"},
                    {"id":"atm4","x":W-140,"y":410,"name":"ATM","col":"#00aaff",
                     "hat_col":"#0d1e30","body_col":"#0d1e30","line":"Save or load your\ngame state here.","game":"atm_screen"},
                ]
            },
        }

    # ── Save / Load helpers ───────────────────────────────────────────────
    def _encode_save(self):
        state={
            "money":self.money,"debt":self.debt,
            "wins":self.wins,"losses":self.losses,"ties":self.ties,
            "games_played":self.games_played,"total_bet":self.total_bet,
            "total_won":self.total_won,"total_lost":self.total_lost,
            "boss_alert_level":self.boss_alert_level,
            "interest_games_since_borrow":self.interest_games_since_borrow,
            "vip_unlocked":getattr(self,"vip_unlocked",False),"hotel_owned_rooms":getattr(self,"hotel_owned_rooms",{}),
            "arena_unlocked":getattr(self,"arena_unlocked",False),
            "shady_borrowed":getattr(self,"shady_borrowed",False),
            "starting_money":getattr(self,"starting_money",1000),
            "owned_skins":list(self.owned_skins),"equipped_skin":self.equipped_skin,
            "owned_card_skins":list(self.owned_card_skins),"equipped_card_skin":self.equipped_card_skin,
            "owned_dice_skins":list(self.owned_dice_skins),"equipped_dice_skin":self.equipped_dice_skin,
            "figurine_collection":getattr(self,"figurine_collection",[]),
            "figurine_display_f2":getattr(self,"figurine_display_f2",[]),
            "figurine_display_f3":getattr(self,"figurine_display_f3",[]),
        }
        return base64.b64encode(json.dumps(state).encode()).decode()

    def _decode_save(self,code):
        try:
            state=json.loads(base64.b64decode(code.strip().encode()).decode())
            self.money=int(state.get("money",self.money))
            self.debt=int(state.get("debt",self.debt))
            self.wins=int(state.get("wins",self.wins))
            self.losses=int(state.get("losses",self.losses))
            self.ties=int(state.get("ties",self.ties))
            self.games_played=int(state.get("games_played",self.games_played))
            self.total_bet=int(state.get("total_bet",self.total_bet))
            self.total_won=int(state.get("total_won",self.total_won))
            self.total_lost=int(state.get("total_lost",self.total_lost))
            self.boss_alert_level=int(state.get("boss_alert_level",self.boss_alert_level))
            self.interest_games_since_borrow=int(state.get("interest_games_since_borrow",0))
            self.vip_unlocked=bool(state.get("vip_unlocked",getattr(self,"vip_unlocked",False)))
            self.hotel_owned_rooms=state.get("hotel_owned_rooms",getattr(self,"hotel_owned_rooms",{}))
            self.arena_unlocked=bool(state.get("arena_unlocked",getattr(self,"arena_unlocked",False)))
            self.shady_borrowed=bool(state.get("shady_borrowed",getattr(self,"shady_borrowed",False)))
            self.starting_money=int(state.get("starting_money",getattr(self,"starting_money",1000)))
            self.owned_skins=set(state.get("owned_skins",list(self.owned_skins)))
            self.equipped_skin=state.get("equipped_skin",self.equipped_skin)
            self.owned_card_skins=set(state.get("owned_card_skins",list(self.owned_card_skins)))
            self.equipped_card_skin=state.get("equipped_card_skin",self.equipped_card_skin)
            self.owned_dice_skins=set(state.get("owned_dice_skins",list(self.owned_dice_skins)))
            self.equipped_dice_skin=state.get("equipped_dice_skin",self.equipped_dice_skin)
            self.figurine_collection=list(state.get("figurine_collection",getattr(self,"figurine_collection",[])))
            self.figurine_display_f2=list(state.get("figurine_display_f2",getattr(self,"figurine_display_f2",[])))
            self.figurine_display_f3=list(state.get("figurine_display_f3",getattr(self,"figurine_display_f3",[])))
            return True
        except Exception:
            return False

    def _atm_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("ATM — ACCOUNT SERVICES","#000a14","#001020")
        code=self._encode_save()

        # Title
        c.create_text(W//2,76,text="⊡  RG BANK ATM  ⊡",fill="#00aaff",
                      font=tkfont.Font(family="Courier New",size=13,weight="bold"))
        c.create_line(0,104,W,104,fill="#002244",width=1)

        # ── SAVE SECTION ─────────────────────────────────────────
        c.create_rectangle(30,116,W//2-10,H-60,fill="#050e18",outline="#00aaff",width=2)
        c.create_text(W//4,132,text="SAVE GAME",fill="#00aaff",
                      font=tkfont.Font(family="Courier New",size=11,weight="bold"))
        c.create_text(W//4,154,text="Copy this code to save your progress:",
                      fill="#4488aa",font=tkfont.Font(family="Courier New",size=8))
        # Code display — wrapped in a text box
        code_disp=tk.Text(self,width=30,height=6,bg="#001428",fg="#00dd88",
                          font=tkfont.Font(family="Courier New",size=9),
                          relief="flat",bd=2,wrap="word",state="normal")
        code_disp.insert("1.0",code)
        code_disp.config(state="disabled")
        code_disp.place(x=44,y=172,width=W//2-68,height=110)
        self._overlay_widgets.append(code_disp)

        def copy_code():
            self.clipboard_clear(); self.clipboard_append(code)
            c.delete("atm_msg")
            c.create_text(W//4,300,text="✓ Copied to clipboard!",fill="#00ff88",
                          font=tkfont.Font(family="Courier New",size=9),tags="atm_msg")
            self.after(2000,lambda:c.delete("atm_msg"))

        self._make_btn(W//4,298,"COPY CODE",copy_code,col="#002244",fg="#00aaff",w=160)
        # Summary
        c.create_text(W//4,330,text=f"💰  ${self.money:,}",fill=GOLD,
                      font=tkfont.Font(family="Courier New",size=10),tags="atm_sum")
        c.create_text(W//4,356,text=f"🎲  {self.games_played} games played",fill=CREAM,
                      font=tkfont.Font(family="Courier New",size=9),tags="atm_sum")
        c.create_text(W//4,380,text=f"🏆  {self.wins}W / {self.losses}L",fill=GREEN_C,
                      font=tkfont.Font(family="Courier New",size=9),tags="atm_sum")
        if self.debt>0:
            c.create_text(W//4,406,text=f"⚠  Debt: ${self.debt:,}",fill=RED_C,
                          font=tkfont.Font(family="Courier New",size=9),tags="atm_sum")

        # ── LOAD SECTION ─────────────────────────────────────────
        c.create_rectangle(W//2+10,116,W-30,H-60,fill="#050e18",outline="#00dd88",width=2)
        c.create_text(W*3//4,132,text="LOAD GAME",fill="#00dd88",
                      font=tkfont.Font(family="Courier New",size=11,weight="bold"))
        c.create_text(W*3//4,154,text="Paste your save code below:",
                      fill="#448866",font=tkfont.Font(family="Courier New",size=8))
        load_entry=tk.Text(self,width=30,height=6,bg="#001428",fg="#00dd88",
                           font=tkfont.Font(family="Courier New",size=9),
                           relief="flat",bd=2,wrap="word")
        load_entry.place(x=W//2+24,y=172,width=W//2-68,height=110)
        self._overlay_widgets.append(load_entry)

        def do_load():
            entered=load_entry.get("1.0","end").strip()
            if not entered:
                c.delete("load_msg")
                c.create_text(W*3//4,300,text="Please paste a code first.",fill=RED_C,
                              font=tkfont.Font(family="Courier New",size=9),tags="load_msg")
                self.after(2000,lambda:c.delete("load_msg")); return
            if self._decode_save(entered):
                c.delete("load_msg")
                c.create_text(W*3//4,300,text="✓ Game loaded!",fill="#00ff88",
                              font=tkfont.Font(family="Courier New",size=10,weight="bold"),tags="load_msg")
                self._refresh_balance_text()
                self.after(1200,self._back_to_interior)
            else:
                c.delete("load_msg")
                c.create_text(W*3//4,300,text="✗ Invalid code.",fill=RED_C,
                              font=tkfont.Font(family="Courier New",size=9),tags="load_msg")
                self.after(2000,lambda:c.delete("load_msg"))

        self._make_btn(W*3//4,298,"LOAD CODE",do_load,col="#002214",fg="#00dd88",w=160)
        c.create_text(W*3//4,336,text="⚠ Loading will overwrite\nyour current game.",fill="#445544",
                      font=tkfont.Font(family="Courier New",size=8),justify="center")

        self._make_btn(W//2,H-38,"← Back",self._back_to_interior,col="#111",fg=CREAM,w=110)

    def _settings_screen(self):
        self._cancel_pending_afters()
        if self._interior_loop_id:
            try: self.after_cancel(self._interior_loop_id)
            except: pass
            self._interior_loop_id=None
        self._loops_paused=True
        self._clear_overlay()
        c=self.canvas
        c.create_rectangle(0,0,W,H,fill="#050505",tags="cfg")
        round_rect(c,W//2-260,H//2-240,W//2+260,H//2+220,r=16,fill="#0a0a14",outline="#3a3a5a",width=3,tags="cfg")
        c.create_text(W//2,H//2-210,text="⚙  SETTINGS",fill=CREAM,
                      font=tkfont.Font(family="Georgia",size=16,weight="bold"),tags="cfg")
        c.create_line(W//2-240,H//2-186,W//2+240,H//2-186,fill="#333",width=1,tags="cfg")
        rows=[
            ("Version","RG Casino Town v2"),
            ("Screen",f"{W}×{H}"),
            ("Balance",f"${self.money:,}"),
            ("Debt",f"${self.debt:,}" if self.debt>0 else "None"),
            ("Games Played",str(self.games_played)),
            ("Wins / Losses",f"{self.wins} / {self.losses}"),
            ("VIP Unlocked","✓ Yes" if getattr(self,"vip_unlocked",False) else "✗ No"),
            ("Arena Unlocked","✓ Yes" if getattr(self,"arena_unlocked",False) else "✗ No"),
            ("Skin",SKINS[self.equipped_skin]["name"]),
            ("Card Skin",CARD_SKINS[self.equipped_card_skin]["name"]),
            ("Dice Skin",DICE_SKINS[self.equipped_dice_skin]["name"]),
        ]
        for i,(lbl,val) in enumerate(rows):
            y8=H//2-168+i*38
            c.create_text(W//2-200,y8,text=lbl,fill="#888",
                          font=tkfont.Font(family="Courier New",size=10),anchor="w",tags="cfg")
            c.create_text(W//2+200,y8,text=val,fill=CREAM,
                          font=tkfont.Font(family="Courier New",size=10),anchor="e",tags="cfg")
            c.create_line(W//2-240,y8+20,W//2+240,y8+20,fill="#1a1a2a",width=1,tags="cfg")

        def close():
            c.delete("cfg")
            for w2 in list(self._overlay_widgets):
                try: w2.destroy()
                except: pass
            self._overlay_widgets.clear()
            self._loops_paused=False
            if self.screen=="town":       self._town_loop()
            elif self.screen=="interior": self._interior_loop()

        self._make_btn(W//2-80,H//2+270,"Close",close,col="#1a1a2a",fg=CREAM,w=130)
        self._make_btn(W//2+80,H//2+270,"♫ Music",
                       lambda:(close(),self._music_screen()),
                       col="#1a0a2a",fg="#cc88ff",w=130)

    def _build_music_audio(self):
        import wave,struct,math,io
        SAMPLE_RATE=44100; BPM=125; BEAT=60/BPM; AMP=7200
        def get_f(m): return 440*(2**((m-69)/12))
        score=[
            ([43,67],1.0),([71],1.0),([74],1.0),([43,71],3.0),
            ([38,62],1.0),([66],1.0),([69],1.0),([38,66],3.0),
            ([40,64],1.0),([67],1.0),([71],1.0),([40,67],3.0),
            ([36,60],1.0),([64],1.0),([67],1.0),([36,64],3.0),
            ([43,67,74],1.5),([76],0.5),([74],1.0),([43,71],3.0),
            ([38,62,71],1.5),([74],0.5),([71],1.0),([38,69],3.0),
            ([40,64,69],1.5),([71],0.5),([69],1.0),([40,67],3.0),
            ([36,64],1.0),([62],1.0),([60],1.0),
            ([38,62],1.0),([64],1.0),([66],1.0),
            ([43,55,67,71,74],3.0),
        ]
        mem=io.BytesIO()
        with wave.open(mem,"wb") as wf:
            wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(SAMPLE_RATE)
            all_f=[]
            for idx2,(notes,beats) in enumerate(score):
                ns=int(SAMPLE_RATE*(beats*BEAT)); buf=[0.0]*ns
                last=(idx2==len(score)-1)
                for ni,m in enumerate(notes):
                    freq=get_f(m); off=int(ni*0.018*SAMPLE_RATE)
                    for i in range(off,ns):
                        t=(i-off)/SAMPLE_RATE
                        dr=4.2 if last else 2.3
                        env=math.exp(-dr*(i-off)/(ns-off))
                        if t<0.025: env*=(t/0.025)
                        s=(math.sin(2*math.pi*freq*t)+0.20*math.sin(2*math.pi*3.0*freq*t))
                        buf[i]+=s*env
                for v in buf:
                    cl=max(-1.0,min(1.0,v/(len(notes)*1.15)))
                    all_f.append(struct.pack("<h",int(cl*AMP)))
            wf.writeframes(b"".join(all_f))
        return mem.getvalue()

    def _stop_music_now(self):
        """Immediately stop audio on any platform."""
        self._music_thread_run=False
        self._music_playing=False
        import sys
        try:
            if sys.platform=="win32":
                import winsound
                # SND_PURGE stops an async playback immediately
                winsound.PlaySound(None, winsound.SND_PURGE)
            else:
                # Terminate the stored subprocess handle directly
                proc=getattr(self,"_music_proc",None)
                if proc is not None:
                    try: proc.terminate()
                    except Exception: pass
                    self._music_proc=None
        except Exception: pass

    def _music_screen(self):
        import threading, sys, os, tempfile, subprocess
        self._cancel_pending_afters()
        if self._interior_loop_id:
            try: self.after_cancel(self._interior_loop_id)
            except: pass
            self._interior_loop_id=None
        self._loops_paused=True
        self._clear_overlay(); c=self.canvas
        c.delete("all")
        c.create_rectangle(0,0,W,H,fill="#080010",tags="mus")
        round_rect(c,W//2-280,H//2-230,W//2+280,H//2+230,r=18,fill="#0d0020",outline="#6633aa",width=3,tags="mus")
        c.create_text(W//2,H//2-195,text="♫  MUSIC PLAYER",fill="#cc88ff",
                      font=tkfont.Font(family="Georgia",size=18,weight="bold"),tags="mus")
        c.create_line(W//2-255,H//2-170,W//2+255,H//2-170,fill="#3a1a5a",width=1,tags="mus")
        c.create_text(W//2,H//2-140,text="Smooth Living Mice (Arcade Mix)",fill=CREAM,
                      font=tkfont.Font(family="Georgia",size=13,slant="italic"),tags="mus")
        c.create_text(W//2,H//2-108,text="★  Now Playing  ★",fill="#aa66ff",
                      font=tkfont.Font(family="Courier New",size=10),tags="mus")
        playing=getattr(self,"_music_playing",False)
        status_txt="● PLAYING" if playing else "■ STOPPED"
        status_col="#00ff88" if playing else "#ff4444"
        c.create_text(W//2,H//2-65,text=status_txt,fill=status_col,
                      font=tkfont.Font(family="Courier New",size=14,weight="bold"),tags="mus")

        def stop_music():
            self._stop_music_now()
            self.after(80,self._music_screen)

        def start_music():
            if getattr(self,"_music_playing",False): return
            self._music_playing=True
            self._music_thread_run=True
            def _loop():
                try:
                    audio_bytes=self._build_music_audio()
                    plat=sys.platform
                    # All platforms: write to temp file once, loop via subprocess/winsound
                    import time
                    tf=tempfile.NamedTemporaryFile(suffix=".wav",delete=False)
                    tf.write(audio_bytes); tf.flush(); tf.close()
                    if plat=="win32":
                        import winsound
                        while getattr(self,"_music_thread_run",False):
                            # SND_ASYNC+SND_FILENAME is reliable on all Windows versions
                            winsound.PlaySound(tf.name,
                                winsound.SND_FILENAME|winsound.SND_ASYNC|winsound.SND_NODEFAULT)
                            # Poll every 50ms; song is ~22s
                            song_secs=22.0; elapsed=0.0
                            while elapsed<song_secs and getattr(self,"_music_thread_run",False):
                                time.sleep(0.05); elapsed+=0.05
                            if not getattr(self,"_music_thread_run",False):
                                winsound.PlaySound(None,winsound.SND_PURGE)
                                break
                    else:
                        exe="afplay" if plat=="darwin" else "aplay"
                        while getattr(self,"_music_thread_run",False):
                            proc=subprocess.Popen([exe,tf.name],
                                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                            self._music_proc=proc
                            proc.wait()
                            self._music_proc=None
                    try: os.unlink(tf.name)
                    except: pass
                except Exception: pass
                self._music_playing=False
            threading.Thread(target=_loop,daemon=True).start()
            self.after(120,self._music_screen)

        if playing:
            self._make_btn(W//2-70,H//2+60,"■  Stop",stop_music,col="#3a0010",fg="#ff6688",w=120)
        else:
            self._make_btn(W//2-70,H//2+60,"▶  Play",start_music,col="#0a2010",fg="#44ff88",w=120)

        plat_note={"win32":"Windows: winsound","darwin":"macOS: afplay"}.get(sys.platform,"Linux: aplay")
        c.create_text(W//2,H//2+120,text=f"Audio engine: {plat_note}",fill="#443355",
                      font=tkfont.Font(family="Courier New",size=8),tags="mus")

        def back_from_music():
            c.delete("mus")
            for w2 in list(self._overlay_widgets):
                try: w2.destroy()
                except: pass
            self._overlay_widgets.clear()
            self._loops_paused=False
            if self.screen=="town": self._town_loop()
            elif self.screen=="interior": self._interior_loop()
            else: self._settings_screen()

        self._make_btn(W//2+70,H//2+60,"← Back",back_from_music,col="#1a1a2a",fg=CREAM,w=120)

    def _make_dojo_rooms(self):
        def decor(c):
            # Wooden floor planks
            for i in range(14):
                y1=65+i*38; col="#c8a050" if i%2==0 else "#b89040"
                c.create_rectangle(0,y1,W,y1+37,fill=col,outline="#9a7830",width=1)
                for lx2 in range(0,W,120): c.create_line(lx2,y1,lx2,y1+37,fill="#9a7030",width=1)
            # Wall (top band)
            c.create_rectangle(0,65,W,130,fill="#1a0e04",outline="")
            # Dojo banner hanging from ceiling
            for bx2 in [W//4,W//2,3*W//4]:
                c.create_line(bx2,65,bx2,90,fill="#5a3010",width=2)
                c.create_rectangle(bx2-36,90,bx2+36,140,fill="#8B0000",outline="#5a0000",width=2)
                c.create_text(bx2,115,text=["道","場","武"][bx2//300],fill=GOLD,font=tkfont.Font(size=22,weight="bold"))
            # Weapon racks on sides
            for side,sx2 in [(-1,40),(1,W-40)]:
                c.create_rectangle(sx2-22,140,sx2+22,500,fill="#3a2010",outline="#1a0e00",width=2)
                for wy in range(160,480,40):
                    c.create_line(sx2-22,wy,sx2+22,wy,fill="#5a3010",width=2)
                    # Weapons on rack
                    c.create_rectangle(sx2-18,wy+4,sx2+18,wy+20,fill="#5a3818",outline="#2a1800",width=1)
            # Punching bags
            for bx3,by3 in [(160,200),(W-160,200)]:
                c.create_line(bx3,65,bx3,by3-10,fill="#5a3010",width=3)
                c.create_oval(bx3-22,by3-10,bx3+22,by3+60,fill="#8B2000",outline="#5a1000",width=3)
                c.create_oval(bx3-16,by3-4,bx3+16,by3+54,fill="#9a2800",outline="")
                for band_y in [by3+12,by3+32]: c.create_line(bx3-22,band_y,bx3+22,band_y,fill="#5a1000",width=2)
            # Training dummies in corners
            for dx2,dy2 in [(W//2-180,300),(W//2+180,300)]:
                c.create_line(dx2,dy2,dx2,dy2+130,fill="#5a3010",width=6)
                c.create_oval(dx2-18,dy2-30,dx2+18,dy2+10,fill="#d4a060",outline="#8B6020",width=2)
                c.create_oval(dx2-28,dy2+10,dx2+28,dy2+70,fill="#c8a050",outline="#8B6020",width=2)
                c.create_line(dx2-28,dy2+30,dx2-50,dy2+20,fill="#8B6020",width=5)
                c.create_line(dx2+28,dy2+30,dx2+50,dy2+20,fill="#8B6020",width=5)
            # Centre mat
            c.create_rectangle(W//2-200,380,W//2+200,530,fill="#cc2200",outline="#8B0000",width=4)
            c.create_rectangle(W//2-190,390,W//2+190,520,fill="#dd2200",outline="")
            c.create_oval(W//2-80,430,W//2+80,480,fill="",outline="#8B0000",width=3)
        return {"main":{"title":"The Dojo","floor":"#c8a050","wall":"#1a0e04","decor_fn":decor,
                        "furniture":[],
                        "doors":[{"to":"exit","x":460,"y":638,"w":180,"h":34,"col":"#3a1a00","label":"Leave Dojo"}],
                        "npcs":[{"id":"sensei","x":W//2,"y":310,"name":"Sensei Riku","col":"#d4a060",
                                  "hat_col":"#1a0e00","body_col":"#1a0e00",
                                  "line":"I will teach you the\nways of combat.","game":"dojo_train"}]}}

    def _dojo_train_screen(self):
        self._clear_overlay(); c=self.canvas; c.delete("all")
        # Dojo BG
        for i in range(14):
            y1=i*38; col="#c8a050" if i%2==0 else "#b89040"
            c.create_rectangle(0,y1,W,y1+37,fill=col,outline="#9a7830",width=1)
        c.create_rectangle(0,0,W,70,fill="#1a0e04",outline="")
        round_rect(c,W//2-250,4,W//2+250,62,r=8,fill="#0a0600",outline=GOLD,width=2)
        c.create_text(W//2,22,text="⛩  THE DOJO  ⛩",fill=GOLD,
                      font=tkfont.Font(family="Georgia",size=15,weight="bold"))
        c.create_text(W//2,48,text=f"Balance: ${self.money:,}",fill=CREAM,font=self.fnt_small,tags="dojo_bal")
        def refresh_bal():
            c.delete("dojo_bal")
            c.create_text(W//2,48,text=f"Balance: ${self.money:,}",fill=CREAM,font=self.fnt_small,tags="dojo_bal")
        c.create_text(W//2,86,text="Sensei Riku: \"Master a skill, master your fate.\"",
                      fill="#8B6020",font=tkfont.Font(family="Georgia",size=11,slant="italic"))
        # Skills shop
        SKILLS=[
            ("kick",      "Kick",       350, "Longer range strike. More damage than punch.",      "🦵"),
            ("fire_blast","Fire Blast",  600, "Charged ranged projectile. Hold D, release to fire.","🔥"),
            ("block",     "Block",       250, "Hold F to deflect most incoming attacks.",           "🛡"),
            ("jump",      "Jump",        400, "Press W to leap. Dodge projectiles mid-air!",        "⬆"),
        ]
        card_w,card_h=220,190; cols=4
        start_x=W//2-(cols*card_w//2)-(cols-1)*10//2
        for idx,(key,name,cost,desc,icon) in enumerate(SKILLS):
            cx2=start_x+idx*(card_w+14)+card_w//2; cy2=310
            owned=self.fight_skills.get(key,False)
            border=GOLD if owned else ("#cc4400" if self.money>=cost else "#333")
            fill="#0a0600" if not owned else "#0a1a00"
            c.create_rectangle(cx2-card_w//2+4,cy2-card_h//2+4,cx2+card_w//2+4,cy2+card_h//2+4,fill="#060402",outline="")
            round_rect(c,cx2-card_w//2,cy2-card_h//2,cx2+card_w//2,cy2+card_h//2,r=12,fill=fill,outline=border,width=2)
            c.create_text(cx2,cy2-card_h//2+30,text=icon,font=tkfont.Font(size=28),anchor="center")
            c.create_text(cx2,cy2-card_h//2+68,text=name,fill=GOLD if owned else CREAM,
                          font=tkfont.Font(family="Georgia",size=13,weight="bold"),anchor="center")
            status="✓ OWNED" if owned else f"${cost:,}"
            sc=GREEN_C if owned else (GOLD if self.money>=cost else "#444")
            c.create_text(cx2,cy2-card_h//2+90,text=status,fill=sc,
                          font=tkfont.Font(family="Courier New",size=10,weight="bold"),anchor="center")
            c.create_text(cx2,cy2-card_h//2+125,text=desc,fill="#888" if not owned else "#aaa",
                          font=tkfont.Font(family="Courier New",size=8),anchor="center",width=card_w-20)
            if not owned:
                def mk_buy(k=key,nm=name,cc=cost):
                    def buy():
                        if self.money<cc: self._msg(f"Need ${cc:,} to learn {nm}.",RED_C,y=H-55); return
                        self.money-=cc; self.fight_skills[k]=True
                        self._msg(f"Learned {nm}! Go test it in the Arena.",GREEN_C,y=H-55)
                        self.after(150,self._dojo_train_screen)
                    return buy
                self._make_btn(cx2,cy2+card_h//2-22,f"Train  ${cost:,}",mk_buy(),
                               col="#cc4400" if self.money>=cost else "#222",
                               fg="white" if self.money>=cost else "#444",w=140)
        # Skills summary
        owned_list=[n for k,n,_,_,_ in SKILLS if self.fight_skills.get(k)]
        summary="Your skills: Punch" + ("" if not owned_list else " + "+" + ".join(owned_list))
        c.create_text(W//2,490,text=summary,fill="#cc8800",
                      font=tkfont.Font(family="Courier New",size=10,weight="bold"))
        c.create_text(W//2,516,text="In the fight:  ← → Move   A Punch   S Kick   Hold D→Release Fire Blast   F Block   W Jump",
                      fill="#555",font=tkfont.Font(family="Courier New",size=8))
        self._make_btn(W//2,570,"← Back to Arena Lobby",self._back_to_interior,col="#1a0e04",fg=GOLD,w=190)

    def _make_arena_rooms(self):
        def lobby_decor(c):
            for row in range(9):
                ry=65+row*64; off=(row%2)*50
                for cx2 in range(-off,W+60,100):
                    c.create_rectangle(cx2,ry,cx2+96,ry+60,fill="#2a1a0e" if row%2==0 else "#221408",outline="#0e0804",width=1)
                    c.create_rectangle(cx2+4,ry+4,cx2+92,ry+56,fill="#281608",outline="")
            for bx in range(60,W-40,200):
                pts=[bx,65, bx+80,65, bx+70,120, bx+40,132, bx+10,120]
                c.create_polygon(pts,fill="#6a0000",outline="#8B0000",width=2)
                c.create_text(bx+40,100,text=u"⚔",fill="#cc0000",font=tkfont.Font(size=18))
            round_rect(c,140,190,W-140,440,r=20,fill="#8B7355",outline="#4a3a1a",width=4)
            round_rect(c,148,198,W-148,432,r=16,fill="#9a8060",outline="")
            for _ in range(40):
                sx=random.randint(155,W-155); sy=random.randint(205,425)
                c.create_oval(sx,sy,sx+6,sy+3,fill="#7a6040",outline="")
            for skx,sky in [(148,195),(W-148,195),(148,432),(W-148,432)]:
                c.create_oval(skx-10,sky-10,skx+10,sky+10,fill="#e8e0d0",outline="#aaa",width=1)
                c.create_oval(skx-4,sky-3,skx-1,sky+1,fill="#222",outline="")
                c.create_oval(skx+1,sky-3,skx+4,sky+1,fill="#222",outline="")
                c.create_line(skx-4,sky+4,skx+4,sky+4,fill="#222",width=2)
            for tx,ty in [(38,140),(38,240),(38,340),(W-38,140),(W-38,240),(W-38,340)]:
                c.create_rectangle(tx-5,ty,tx+5,ty+28,fill="#5a3010",outline="#2a1800",width=1)
                c.create_polygon(tx-8,ty-2,tx+8,ty-2,tx+4,ty-22,tx,ty-28,tx-4,ty-22,fill="#ff8800",outline="#ffaa00",width=1)
                c.create_polygon(tx-4,ty-2,tx+4,ty-2,tx+2,ty-16,tx,ty-20,tx-2,ty-16,fill="#ffdd00",outline="")
            for wrx in [80,W-80]:
                c.create_rectangle(wrx-22,165,wrx+22,195,fill="#3a2000",outline="#5a3000",width=2)
                for wi in [-12,0,12]:
                    c.create_line(wrx+wi,195,wrx+wi,150,fill="#8a8888",width=3)
                    c.create_polygon(wrx+wi-4,150,wrx+wi+4,150,wrx+wi,138,fill="#aaaaaa",outline="#888",width=1)
            for hx2 in range(20,W-10,18):
                hh=random.randint(12,24)
                fc=random.choice(["#1a0000","#0a0a1a","#001a00","#1a1a00"])
                c.create_oval(hx2-5,65+hh-14,hx2+5,65+hh,fill=fc,outline="")
                c.create_rectangle(hx2-5,65+hh,hx2+5,65+hh+16,fill=fc,outline="")
            c.create_text(W//2,172,text="THE ARENA - Main Hall",fill=RED_C,font=tkfont.Font(family="Georgia",size=16,weight="bold"))
            c.create_text(W-10,165,anchor="ne",text=f"Stage {self.fight_stage+1}/5 | HP:{self.player_health}",fill=GOLD,font=self.fnt_small)
        def betting_decor(c):
            for row in range(9):
                ry=65+row*64
                c.create_rectangle(0,ry,W,ry+60,fill="#1a0000" if row%2==0 else "#150000",outline="#0e0000",width=1)
            c.create_line(0,490,W,490,fill="#8B6914",width=4)
            c.create_rectangle(W//2-260,76,W//2+260,186,fill="#0a0000",outline=GOLD,width=3)
            c.create_text(W//2,96,text="TONIGHT'S ODDS",fill=GOLD,font=tkfont.Font(family="Courier New",size=13,weight="bold"))
            for i,(nm,od) in enumerate([("Red Corner","2:1"),("Blue Corner","3:1"),("Draw","10:1")]):
                c.create_text(W//2-80,122+i*20,text=nm,fill="#cc4444",font=tkfont.Font(family="Courier New",size=10),anchor="e")
                c.create_text(W//2+30,122+i*20,text=od,fill=GOLD,font=tkfont.Font(family="Courier New",size=10),anchor="w")
            for cx3 in [200,W//2-120,W//2+120,W-200]:
                c.create_rectangle(cx3-22,380,cx3+22,430,fill="#4a0000",outline="#8B0000",width=2)
                c.create_rectangle(cx3-22,358,cx3+22,382,fill="#6a0000",outline="#8B0000",width=1)
                c.create_rectangle(cx3-26,380,cx3-20,416,fill="#4a0000",outline="#5a0000",width=1)
                c.create_rectangle(cx3+20,380,cx3+26,416,fill="#4a0000",outline="#5a0000",width=1)
            for tx3 in [W//2-250,W//2,W//2+250]:
                c.create_oval(tx3-24,430,tx3+24,446,fill="#3a1a00",outline=GOLD,width=1)
                c.create_line(tx3,446,tx3,475,fill="#5a3010",width=3)
                c.create_oval(tx3-6,471,tx3+6,479,fill="#3a1a00",outline=GOLD,width=1)
            for bx2 in [200,W//2,W-200]:
                c.create_line(bx2,65,bx2,95,fill="#444",width=2)
                c.create_oval(bx2-8,90,bx2+8,112,fill="#fffacc",outline="#cc9900",width=1)
                c.create_oval(bx2-5,94,bx2+5,108,fill="#ffff88",outline="")
        def restaurant_decor(c):
            # === FLOOR — herringbone parquet ===
            for row in range(18):
                for col2 in range(20):
                    x1=col2*58-10; y1=65+row*34
                    shade=(row+col2)%2
                    c.create_rectangle(x1,y1,x1+57,y1+33,fill="#c8a060" if shade else "#b89050",outline="#9a7038",width=1)
            # Plank lines (herringbone feel)
            for row in range(18):
                y1=65+row*34
                for col2 in range(20):
                    x1=col2*58-10
                    if (row+col2)%2==0:
                        c.create_line(x1+14,y1,x1+44,y1+33,fill="#9a7038",width=1)
                    else:
                        c.create_line(x1+44,y1,x1+14,y1+33,fill="#9a7038",width=1)
            # === WALLS — rich burgundy dado panels ===
            c.create_rectangle(0,65,W,185,fill="#4a0a10",outline="")
            # Wall panel mouldings
            for wx2 in range(0,W,130):
                c.create_rectangle(wx2+6,70,wx2+122,182,fill="",outline="#7a2030",width=2)
                c.create_rectangle(wx2+12,76,wx2+116,176,fill="",outline="#5a1020",width=1)
            # Chair rail
            c.create_rectangle(0,183,W,194,fill="#8B6020",outline="#5a3800",width=1)
            c.create_line(0,183,W,183,fill="#c8a040",width=2)
            c.create_line(0,194,W,194,fill="#6a4818",width=2)
            # === GRAND CHANDELIER (centre) ===
            chx,chy=W//2,118
            c.create_line(chx,65,chx,chy-20,fill="#8B6914",width=5)
            # Chandelier crown
            c.create_oval(chx-22,chy-26,chx+22,chy-6,fill="#d4a820",outline=GOLD,width=2)
            c.create_oval(chx-14,chy-22,chx+14,chy-10,fill="#ffee88",outline="")
            # Three tiers of arms
            for tier,n_arms,rad,arm_len in [(0,6,0,52),(1,8,8,44),(2,5,16,36)]:
                for i in range(n_arms):
                    a=math.radians(i*360/n_arms + tier*15)
                    ex=chx+int(arm_len*math.cos(a)); ey=chy-rad+int((arm_len//3)*math.sin(a))
                    c.create_line(chx,chy-rad,ex,ey,fill="#8B6914",width=3)
                    # Candle + flame
                    c.create_rectangle(ex-3,ey,ex+3,ey+10,fill="#f0ead0",outline="#ccc",width=1)
                    c.create_polygon(ex,ey-8,ex-3,ey+2,ex+3,ey+2,fill="#ff8800",outline="#ffcc00",width=1,smooth=True)
                    c.create_oval(ex-2,ey-6,ex+2,ey-2,fill="#ffeeaa",outline="")
            # Crystal drop strands
            for i in range(16):
                a=math.radians(i*22.5)
                dx=int(30*math.cos(a)); dy=int(12*math.sin(a))
                c.create_line(chx+dx,chy+6,chx+dx,chy+22,fill="#aaddff",width=1)
                c.create_oval(chx+dx-3,chy+20,chx+dx+3,chy+26,fill="#cceeff",outline="#aaccee",width=1)
            # === WALL SCONCES (left + right) ===
            for sx2 in [80,W-80]:
                # Backplate
                c.create_rectangle(sx2-16,70,sx2+16,150,fill="#3a1a00",outline="#8B6914",width=2)
                c.create_rectangle(sx2-10,76,sx2+10,104,fill="#5a2a08",outline="")
                # Ornate arm
                side=1 if sx2>W//2 else -1
                c.create_line(sx2,148,sx2+side*22,166,fill="#8B6914",width=4)
                c.create_line(sx2+side*22,166,sx2+side*30,158,fill="#8B6914",width=3)
                # Globe
                gx2=sx2+side*30; gy2=158
                c.create_oval(gx2-16,gy2-18,gx2+16,gy2+14,fill="#fff8cc",outline="#d4a820",width=2)
                c.create_oval(gx2-10,gy2-12,gx2+10,gy2+8,fill="#fffaee",outline="")
                c.create_oval(gx2-16,gy2-18,gx2+16,gy2+14,fill="",outline="#ffee88",width=1)
            # === DINING TABLES (5 tables, each with white tablecloth + settings) ===
            table_positions=[(220,300),(W//2,290),(W-220,300),(320,450),(W-320,450)]
            for tx4,ty4 in table_positions:
                # Table shadow
                c.create_oval(tx4-44,ty4+14,tx4+44,ty4+26,fill="#555040",outline="")
                # Table leg
                c.create_rectangle(tx4-4,ty4+10,tx4+4,ty4+28,fill="#7a5020",outline="#5a3808",width=1)
                # Table top (round)
                c.create_oval(tx4-52,ty4-28,tx4+52,ty4+14,fill="#8B6020",outline="#5a3808",width=3)
                # White tablecloth
                c.create_oval(tx4-46,ty4-24,tx4+46,ty4+10,fill="#fafaf5",outline="#e0d8c8",width=2)
                # Tablecloth fold shadow
                c.create_oval(tx4-38,ty4-18,tx4+38,ty4+4,fill="",outline="#d8d0b8",width=1)
                # Candle centrepiece
                c.create_rectangle(tx4-3,ty4-20,tx4+3,ty4-8,fill="#f0ead0",outline="#ccc",width=1)
                c.create_polygon(tx4,ty4-28,tx4-4,ty4-18,tx4+4,ty4-18,fill="#ff8800",outline="#ffcc00",width=1)
                c.create_oval(tx4-2,ty4-26,tx4+2,ty4-22,fill="#ffeeaa",outline="")
                # Plates (2 per table)
                for side2,angle2 in [(-1,200),(1,340)]:
                    plx=tx4+int(28*math.cos(math.radians(angle2)))
                    ply=ty4+int(14*math.sin(math.radians(angle2)))
                    c.create_oval(plx-10,ply-6,plx+10,ply+6,fill="#f5f0e8",outline="#d0c8b0",width=2)
                    c.create_oval(plx-7,ply-4,plx+7,ply+4,fill="#eee8de",outline="")
                # Wine glasses (2 per table)
                for angle3 in [160,20]:
                    glx=tx4+int(22*math.cos(math.radians(angle3)))
                    gly=ty4+int(11*math.sin(math.radians(angle3)))
                    # Stem
                    c.create_line(glx,gly-2,glx,gly+8,fill="#aaaaaa",width=1)
                    c.create_line(glx-4,gly+8,glx+4,gly+8,fill="#aaaaaa",width=1)
                    # Bowl
                    c.create_oval(glx-5,gly-8,glx+5,gly-1,fill="#cc3333" if angle3==160 else "#f0f8ff",outline="#888",width=1)
                # Cutlery
                for angle4 in [240,300]:
                    fx=tx4+int(32*math.cos(math.radians(angle4)))
                    fy=ty4+int(16*math.sin(math.radians(angle4)))
                    c.create_line(fx-1,fy-6,fx-1,fy+6,fill="#888",width=1)
                    c.create_line(fx+2,fy-6,fx+2,fy+6,fill="#888",width=1)
            # === WALL MENU BOARDS (both sides) ===
            for mx2 in [58,W-58]:
                # Board frame
                c.create_rectangle(mx2-46,200,mx2+46,370,fill="#1a0a04",outline="#8B6914",width=3)
                c.create_rectangle(mx2-40,206,mx2+40,364,fill="#0d0602",outline="#5a3810",width=1)
                c.create_text(mx2,218,text="MENU",fill="#d4a820",font=tkfont.Font(family="Georgia",size=10,weight="bold"))
                c.create_line(mx2-36,228,mx2+36,228,fill="#5a3810",width=1)
                for mi,(nm,pr) in enumerate([("Egg","$50"),("BLT","$150"),("Salad","$200"),("English","$400"),("Ravioli","$900")]):
                    c.create_text(mx2-2,244+mi*22,text=nm,fill="#c8a060",font=tkfont.Font(family="Courier New",size=8))
                    c.create_text(mx2+2,244+mi*22,text=pr,fill="#88cc88",font=tkfont.Font(family="Courier New",size=7),anchor="w")
            # === KITCHEN PASS-THROUGH WINDOW ===
            c.create_rectangle(W//2-100,68,W//2+100,132,fill="#2a1a08",outline="#8B6020",width=3)
            c.create_rectangle(W//2-94,72,W//2+94,128,fill="#1a0e04",outline="#6a4810",width=1)
            c.create_text(W//2,100,text="KITCHEN",fill="#8B6020",font=tkfont.Font(family="Courier New",size=9,weight="bold"))
            # Steam wisps above kitchen
            for si in range(3):
                sx3=W//2-30+si*30
                c.create_line(sx3,68,sx3-4,58,sx3+4,48,sx3,38,fill="#cccccc",width=1,smooth=True)
            # === CARPET RUNNER down centre aisle ===
            c.create_rectangle(W//2-28,194,W//2+28,630,fill="#8B0020",outline="#5a0010",width=2)
            for ry2 in range(200,630,40):
                c.create_oval(W//2-18,ry2,W//2+18,ry2+30,fill="#6a0018",outline="#5a0010",width=1)
            # === POTTED PALMS in corners ===
            for px6,py6 in [(130,490),(W-130,490),(130,380),(W-130,380)]:
                # Pot
                c.create_polygon(px6-18,py6+30,px6+18,py6+30,px6+14,py6+55,px6-14,py6+55,
                                 fill="#7a4010",outline="#5a2808",width=2)
                c.create_oval(px6-18,py6+22,px6+18,py6+36,fill="#9a5518",outline="#6a3808",width=1)
                c.create_oval(px6-5,py6+26,px6+5,py6+32,fill="#5a2808",outline="")
                # Trunk
                c.create_line(px6,py6+24,px6-3,py6+10,fill="#5a3010",width=4)
                c.create_line(px6,py6+24,px6+2,py6+8,fill="#4a2808",width=3)
                # Fronds (8 palm leaves)
                for la,lr3,lc3 in [(-40,26,"#1a6a10"),(-20,30,"#1e7a12"),(0,32,"#228814"),(20,30,"#1e7a12"),
                                    (40,26,"#1a6a10"),(-30,24,"#155a0c"),(10,28,"#1a7210"),(30,24,"#175c0e")]:
                    ex=px6+int(lr3*math.cos(math.radians(la-80)))
                    ey=py6+int(lr3*math.sin(math.radians(la-80)))-8
                    c.create_line(px6-1,py6+8,ex,ey,fill=lc3,width=3,smooth=True)
                    c.create_line(px6-1,py6+8,ex+4,ey+3,fill=lc3,width=2,smooth=True)
        ARENA_BACK={"to":"lobby","x":460,"y":638,"w":180,"h":34,"col":"#8B0000","label":"Back to Arena"}
        return {
            "lobby":{"title":"The Arena - Main Hall","floor":"#3a2a10","wall":"#1a1000","decor_fn":lobby_decor,
                     "furniture":[{"type":"cabinet","bounds":(50,450,110,550),"label":""},{"type":"cabinet","bounds":(W-110,450,W-50,550),"label":""}],
                     "doors":[{"to":"betting","x":0,"y":220,"w":80,"h":50,"col":"#3a0000","label":"Betting"},
                              {"to":"restaurant","x":0,"y":300,"w":80,"h":50,"col":"#3a1800","label":"Diner"},
                              {"to":"dojo","x":W-80,"y":220,"w":80,"h":50,"col":"#2a1800","label":"Dojo"},
                              {"to":"exit","x":460,"y":638,"w":180,"h":34,"col":"#333","label":"Exit Arena"}],
                     "npcs":[{"id":"fight_master","x":W//2,"y":360,"name":"Fight Master","col":"#e06040",
                              "hat_col":"#1a0000","body_col":"#2a0000","line":"Funky Feet Fights!\n5 enemies await you.","game":"arena_fight"}]},
            "betting":{"title":"The Betting Den","floor":"#1a0000","wall":"#0e0000","decor_fn":betting_decor,"furniture":[],
                       "doors":[ARENA_BACK],
                       "npcs":[{"id":"promoter","x":W//2,"y":370,"name":"Promoter Pete","col":"#c8a060",
                                "hat_col":"#2a0000","body_col":"#5a0000","line":"Bet on the brawl!\nPick a side and wager.","game":"arena_bet"}]},
            "restaurant":{"title":"Roughhouse Restaurant","floor":"#f5e8d0","wall":"#e0cca8","decor_fn":restaurant_decor,"furniture":[],
                          "doors":[ARENA_BACK],
                          "npcs":[{"id":"chef","x":W//2,"y":220,"name":"Chef Mario","col":"#e8c090",
                                   "hat_col":"#ffffff","body_col":"#ffffff","line":"What'll it be today?\nOur kitchen is open!","game":"arena_restaurant"}]},
            "dojo":{"title":"The Dojo","floor":"#c8a050","wall":"#1a0e04","decor_fn":self._make_dojo_rooms()["main"]["decor_fn"],
                    "furniture":[],
                    "doors":[ARENA_BACK],
                    "npcs":[{"id":"sensei","x":W//2,"y":310,"name":"Sensei Riku","col":"#d4a060",
                              "hat_col":"#1a0e00","body_col":"#1a0e00",
                              "line":"I will teach you the\nways of combat.","game":"dojo_train"}]},
        }

    # ── BLACKJACK ─────────────────────────────────────────
    def _blackjack_screen(self,min_bet=1,title="BLACKJACK",payout=1.5):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg(title,"#080410","#120820")
        round_rect(c,80,140,W-80,H-HOTBAR_H-20,r=40,fill=FELT,outline="#0a3015",width=4)
        round_rect(c,90,150,W-90,H-HOTBAR_H-30,r=36,fill=FELT_L,outline="")
        c.create_text(W//2,228,text="DEALER",fill="#2a5a2a",font=self.fnt_small)
        c.create_text(W//2,432,text="PLAYER",fill="#2a5a2a",font=self.fnt_small)
        deck_ranks=CARD_RANKS*4; random.shuffle(deck_ranks)
        state={"deck":deck_ranks,"player":[],"dealer":[],"bet":0,"phase":"bet"}
        def deal_card(hand): hand.append(state["deck"].pop() if state["deck"] else random.choice(CARD_RANKS))
        def hand_value(hand):
            total=sum(card_value(r) for r in hand); aces=hand.count("A")
            while total>21 and aces: total-=10; aces-=1
            return total
        def draw_card(x,y,rank=None):
            suit=random.choice(list(CARD_SUITS.keys()))
            cs=CARD_SKINS[self.equipped_card_skin]
            round_rect(c,x,y,x+62,y+92,r=6,fill=cs["face"],outline=cs["border"],width=2,tags="cards")
            if rank is None:
                round_rect(c,x+4,y+4,x+58,y+88,r=5,fill=cs["back"],outline=cs["border"],width=2,tags="cards")
                for pi in range(3):
                    for pj in range(5):
                        bx2=x+10+pi*16; by2=y+10+pj*14
                        c.create_rectangle(bx2,by2,bx2+8,by2+8,fill=cs["border"],outline="",tags="cards")
            else:
                sym_col=cs["sym_r"] if suit in("♥","♦") else cs["sym_b"]
                c.create_text(x+9,y+13,text=rank,fill=sym_col,font=self.fnt_card,anchor="w",tags="cards")
                c.create_text(x+31,y+52,text=suit,fill=sym_col,font=tkfont.Font(size=22),anchor="center",tags="cards")
                c.create_text(x+53,y+79,text=rank,fill=sym_col,font=tkfont.Font(size=11),anchor="e",tags="cards")
        def redraw_table():
            c.delete("cards","score_txt","msg_layer")
            ph=state["phase"]; ds=W//2-len(state["dealer"])*34
            for i,r in enumerate(state["dealer"]): draw_card(ds+i*68,162,None if(ph=="play"and i==0)else r)
            ps=W//2-len(state["player"])*34
            for i,r in enumerate(state["player"]): draw_card(ps+i*68,358,r)
            pv=hand_value(state["player"])
            c.create_text(W//2,456,text=f"Your total: {pv}",fill=GOLD,font=self.fnt_body,tags="score_txt")
            if ph!="play":
                dv=hand_value(state["dealer"])
                c.create_text(W//2,276,text=f"Dealer: {dv}",fill=GOLD,font=self.fnt_body,tags="score_txt")
        def on_deal(bet):
            if bet<min_bet: self._msg(f"Min bet: ${min_bet}",RED_C); self._show_hotbar(on_deal); return
            state["bet"]=bet; state["phase"]="play"
            deal_card(state["player"]); deal_card(state["dealer"])
            deal_card(state["player"]); deal_card(state["dealer"])
            redraw_table()
            if hand_value(state["player"])==21: finish("blackjack")
            else: show_play_btns()
        def show_play_btns():
            self._make_btn(W//2-130,H-HOTBAR_H-26,"HIT",do_hit,col="#8B0000",fg=CREAM)
            self._make_btn(W//2,H-HOTBAR_H-26,"STAND",do_stand,col="#1a4a00",fg=CREAM)
        def do_hit():
            deal_card(state["player"]); redraw_table()
            pv=hand_value(state["player"])
            if pv>21: finish("bust")
            elif pv==21: do_stand()
        def do_stand():
            while hand_value(state["dealer"])<17: deal_card(state["dealer"])
            state["phase"]="done"; redraw_table()
            pv=hand_value(state["player"]); dv=hand_value(state["dealer"])
            if dv>21 or pv>dv: finish("win")
            elif pv==dv: finish("tie")
            else: finish("lose")
        def finish(outcome):
            state["phase"]="done"
            for w in list(self._overlay_widgets):
                try: w.destroy()
                except: pass
            self._overlay_widgets.clear(); redraw_table(); b=state["bet"]
            if outcome=="blackjack":
                gain=int(b*payout); self.money+=gain; self._msg(f"BLACKJACK! +${gain}",GREEN_C); self._post_game(gain,"win")
            elif outcome=="bust":
                self.money-=b; self._msg(f"Bust! -${b}",RED_C); self._post_game(b,"loss")
            elif outcome=="win":
                self.money+=b; self._msg(f"You win ${b}!",GREEN_C); self._post_game(b,"win")
            elif outcome=="tie":
                self._msg("Push — no money lost",GOLD); self._post_game(b,"tie")
            else:
                self.money-=b; self._msg(f"Dealer wins. -${b}",RED_C); self._post_game(b,"loss")
            self._refresh_balance_text()
            self._make_btn(W//2-70,650,"PLAY AGAIN",lambda:self._blackjack_screen(min_bet,title,payout))
            self._make_btn(W//2+80,650,"BACK",self._back_to_interior,col="#333",fg=CREAM,w=80)
        self._show_hotbar(on_deal)

    # ── ROULETTE ──────────────────────────────────────────
    def _roulette_screen(self,golden=False):
        self._clear_overlay(); c=self.canvas
        title="GOLDEN ROULETTE" if golden else "ROULETTE"
        self._draw_room_bg(title,"#060d00","#0d1800")
        RED_NUMS={1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
        WX,WY,WR=220,300,155
        wheel_col=GOLD if golden else "#5a3010"
        c.create_oval(WX-WR-10,WY-WR-10,WX+WR+10,WY+WR+10,fill=wheel_col,outline=GOLD,width=4)
        for i in range(37):
            angle=(i/37)*360
            col="#007700" if i==0 else("#c0392b" if i in RED_NUMS else "#1a1a1a")
            if golden: col=("#00aa00" if i==0 else("#d4a020" if i in RED_NUMS else "#2a2a3a"))
            c.create_arc(WX-WR,WY-WR,WX+WR,WY+WR,start=angle,extent=360/37,fill=col,outline="white",width=1,style="pie")
            rad=math.radians(angle+360/37/2)
            c.create_text(WX+(WR*0.7)*math.cos(rad),WY-(WR*0.7)*math.sin(rad),
                          text=str(i),fill="white",font=tkfont.Font(size=7,weight="bold"))
        c.create_oval(WX-18,WY-18,WX+18,WY+18,fill=GOLD,outline=DARK,width=2)
        round_rect(c,420,100,W-30,H-HOTBAR_H-20,r=16,fill=FELT,outline="#0a3015",width=3)
        c.create_text(560,130,text="Pick Colour:",fill=CREAM,font=self.fnt_body)
        col_var=tk.StringVar(value="Red")
        colours=["Red","Black","Green"]
        for ci,col_name in enumerate(colours):
            bg={"Red":"#c0392b","Black":"#1a1a1a","Green":"#006000"}[col_name]
            rb=tk.Radiobutton(self,text=col_name,variable=col_var,value=col_name,
                              font=self.fnt_body,bg=bg,fg="white",selectcolor="#555",
                              activebackground=bg,indicatoron=False,relief="flat",width=8,cursor="hand2")
            self.canvas.create_window(530+ci*110,162,window=rb); self._overlay_widgets.append(rb)
        c.create_text(560,202,text="Pick Number (0-36):",fill=CREAM,font=self.fnt_body)
        num_entry=self._make_entry(668,230,width=5); num_entry.insert(0,"7")
        if golden:
            c.create_text(560,265,text="GOLDEN: Jackpot 20x | Number 10x | Colour 3x",fill=GOLD,font=self.fnt_small)
        spin_angle=[0.0]; ball_angle=[0.0]
        POINTER_ANGLE=90.0   # pointer always at top (90° in canvas arc coords)
        def draw_spin_overlay(highlight_num=None):
            c.delete("spin_layer")
            a=spin_angle[0]
            for i in range(37):
                seg_a=(i/37)*360
                if golden: col=("#00aa00" if i==0 else("#d4a020" if i in RED_NUMS else "#2a2a3a"))
                else: col="#006000" if i==0 else("#c0392b" if i in RED_NUMS else "#1a1a1a")
                # Highlight the winning number when done
                if highlight_num is not None and i==highlight_num:
                    col="#ffff00"
                c.create_arc(WX-WR,WY-WR,WX+WR,WY+WR,start=seg_a+a,extent=360/37,fill=col,outline="white",width=1,style="pie",tags="spin_layer")
                rad=math.radians(seg_a+a+360/37/2)
                c.create_text(WX+(WR*0.7)*math.cos(rad),WY-(WR*0.7)*math.sin(rad),text=str(i),fill="white",font=tkfont.Font(size=7,weight="bold"),tags="spin_layer")
            # Pointer arrow at top
            c.create_polygon(WX-8,WY-WR-18, WX+8,WY-WR-18, WX,WY-WR+2,
                             fill="#ffcc00",outline="#aa8800",width=2,tags="spin_layer")
            # Ball
            brad=math.radians(ball_angle[0])
            bx=WX+(WR-15)*math.cos(brad); by=WY-(WR-15)*math.sin(brad)
            c.create_oval(bx-7,by-7,bx+7,by+7,fill="white",outline="silver",width=2,tags="spin_layer")
            c.create_oval(WX-18,WY-18,WX+18,WY+18,fill=GOLD,outline=DARK,width=2,tags="spin_layer")
        def on_deal(bet):
            try: player_num=int(num_entry.get()); assert 0<=player_num<=36
            except: self._msg("Invalid number (0-36)",RED_C); self._show_hotbar(on_deal); return
            player_col=col_var.get(); result=random.randint(0,36)
            result_col="Green" if result==0 else("Red" if result in RED_NUMS else "Black")
            # Calculate where wheel must stop so result slot is under pointer (90°)
            # Slot centre angle = (result/37)*360 + spin offset; we want that at 90°
            slot_centre_in_wheel=(result/37)*360 + 360/(37*2)  # centre of result's slot
            # total spin: many full rotations + alignment
            full_spins=6*360
            target_wheel_angle=(POINTER_ANGLE - slot_centre_in_wheel) % 360
            target_total=full_spins + target_wheel_angle
            start_angle=spin_angle[0]
            TOTAL_FRAMES=55
            def animate(frame=0):
                progress=frame/TOTAL_FRAMES
                # ease-out cubic
                ease=1-(1-progress)**3
                spin_angle[0]=(start_angle + target_total*ease) % 360
                # ball slows and settles into result slot
                ball_ease=1-(1-min(1.0,progress*1.1))**3
                ball_target_angle=POINTER_ANGLE - (result/37)*360 - 360/(37*2)
                ball_angle[0]=(ball_target_angle*ball_ease + (start_angle*1.3)*(1-ball_ease)) % 360
                draw_spin_overlay()
                if frame < TOTAL_FRAMES:
                    delay=16 if frame<30 else 24 if frame<45 else 40
                    self.after(delay,lambda:animate(frame+1))
                else:
                    spin_angle[0]=target_wheel_angle; ball_angle[0]=POINTER_ANGLE
                    draw_spin_overlay(highlight_num=result)
                    # Show result banner
                    res_bg={"Red":"#8B0000","Black":"#111","Green":"#006000"}[result_col]
                    c.create_rectangle(WX-100,WY+WR+12,WX+100,WY+WR+44,fill=res_bg,outline="#ffcc00",width=2,tags="spin_layer")
                    c.create_text(WX,WY+WR+28,text=f"  {result}  {result_col.upper()}  ",fill="#ffff00",
                                  font=tkfont.Font(family="Courier New",size=13,weight="bold"),tags="spin_layer")
                    both=player_col==result_col and player_num==result
                    colour_match=player_col==result_col; num_match=player_num==result
                    jx=20 if golden else 36; cx2=3 if golden else 1; nx=10 if golden else 17
                    if both:
                        gain=bet*jx; self.money+=gain; self._msg(f"JACKPOT! {result} {result_col}! +${gain}",GREEN_C); self._post_game(gain,"win")
                    elif colour_match:
                        gain=bet*cx2; self.money+=gain; self._msg(f"Colour match! {result} {result_col}. +${gain}",GREEN_C); self._post_game(gain,"win")
                    elif num_match:
                        gain=bet*nx; self.money+=gain; self._msg(f"Number match! +${gain}",GREEN_C); self._post_game(gain,"win")
                    else:
                        self.money-=bet; self._msg(f"Result: {result} {result_col}. -${bet}",RED_C); self._post_game(bet,"loss")
                    self._refresh_balance_text()
                    again=self._vip_golden_roulette if golden else self._roulette_screen
                    self._make_btn(W//2-70,650,"SPIN AGAIN",again)
                    self._make_btn(W//2+80,650,"BACK",self._back_to_interior if not golden else self._vip_screen,col="#333",fg=CREAM,w=80)
            animate()
        self._show_hotbar(on_deal)

    # ── SLOTS ─────────────────────────────────────────────
    def _slots_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("SLOT MACHINE","#0d0030","#180050")
        SYMS=["🍒","🍋","🔔","💎","7","⭐"]
        SYM_COL={"🍒":"#e74c3c","🍋":"#f1c40f","🔔":"#f39c12","💎":"#3498db","7":"#e74c3c","⭐":"#f1c40f"}
        round_rect(c,W//2-220,80,W//2+220,H-HOTBAR_H-20,r=30,fill="#1a0040",outline=PURPLE,width=5)
        round_rect(c,W//2-200,100,W//2+200,H-HOTBAR_H-40,r=20,fill="#110028",outline="#6a3090",width=2)
        reel_x=[W//2-130,W//2,W//2+130]
        for rx in reel_x: round_rect(c,rx-45,130,rx+45,280,r=8,fill="#000033",outline=GOLD,width=3)
        cur_syms=[random.choice(SYMS) for _ in range(3)]; final_syms=[None,None,None]
        def draw_reels(syms):
            c.delete("reel_sym")
            for rx,sym in zip(reel_x,syms):
                c.create_text(rx,205,text=sym,fill=SYM_COL.get(sym,"white"),font=tkfont.Font(size=40),tags="reel_sym")
        draw_reels(cur_syms)
        c.create_line(W//2-190,205,W//2+190,205,fill=GOLD,width=2,dash=(6,4))
        c.create_text(W//2,305,text="3 Same = 5x  |  2 Same = 2x",fill="#aaa",font=self.fnt_small)
        def on_deal(bet):
            final_syms[0]=random.choice(SYMS); final_syms[1]=random.choice(SYMS); final_syms[2]=random.choice(SYMS)
            c.delete("msg_layer")
            def anim(step=0):
                if step<25: draw_reels([random.choice(SYMS) for _ in range(3)]); self.after(60,lambda:anim(step+1))
                elif step<30: draw_reels([final_syms[0],random.choice(SYMS),random.choice(SYMS)]); self.after(80,lambda:anim(step+1))
                elif step<34: draw_reels([final_syms[0],final_syms[1],random.choice(SYMS)]); self.after(100,lambda:anim(step+1))
                else: draw_reels(final_syms); resolve()
            def resolve():
                a,b2,b3=final_syms
                if a==b2==b3:
                    gain=bet*5; self.money+=gain; self._msg(f"JACKPOT! +${gain}",GREEN_C,y=430); self._post_game(gain,"win")
                elif a==b2 or b2==b3 or a==b3:
                    gain=bet*2; self.money+=gain; self._msg(f"Two match! +${gain}",GREEN_C,y=430); self._post_game(gain,"win")
                else:
                    self.money-=bet; self._msg(f"No match. -${bet}",RED_C,y=430); self._post_game(bet,"loss")
                self._refresh_balance_text()
                self._make_btn(W//2-70,650,"SPIN AGAIN",self._slots_screen)
                self._make_btn(W//2+80,650,"BACK",self._back_to_interior,col="#333",fg=CREAM,w=80)
            anim()
        self._show_hotbar(on_deal)

    # ── CRAPS ─────────────────────────────────────────────
    def _craps_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("CRAPS","#000a20","#00102e")
        round_rect(c,60,120,W-60,H-HOTBAR_H-30,r=30,fill="#0a3050",outline="#1a6090",width=4)
        c.create_text(W//2,162,text="PASS LINE",fill="#777",font=tkfont.Font(size=22,weight="bold"))
        def draw_die(x,y,val,size=70):
            ds=DICE_SKINS[self.equipped_dice_skin]
            round_rect(c,x,y,x+size,y+size,r=10,fill=ds["col"],outline=ds["ol"],width=2,tags="dice_img")
            pips={1:[(0.5,0.5)],2:[(0.25,0.25),(0.75,0.75)],3:[(0.25,0.25),(0.5,0.5),(0.75,0.75)],
                  4:[(0.25,0.25),(0.75,0.25),(0.25,0.75),(0.75,0.75)],
                  5:[(0.25,0.25),(0.75,0.25),(0.5,0.5),(0.25,0.75),(0.75,0.75)],
                  6:[(0.25,0.2),(0.75,0.2),(0.25,0.5),(0.75,0.5),(0.25,0.8),(0.75,0.8)]}
            pr=size*0.1
            for px2,py2 in pips.get(val,[]):
                cx2=x+px2*size; cy2=y+py2*size
                c.create_oval(cx2-pr,cy2-pr,cx2+pr,cy2+pr,fill=ds["dot"],outline="",tags="dice_img")
        state={"phase":"bet","point":0,"bet":0}
        def show_dice(d1,d2):
            c.delete("dice_img","dice_total")
            draw_die(W//2-100,270,d1); draw_die(W//2+30,270,d2)
            c.create_text(W//2,390,text=f"Roll: {d1+d2}",fill=GOLD,font=self.fnt_title,tags="dice_total")
        show_dice(1,1)
        c.create_text(W//2,226,text="Place chips below then DEAL",fill="#888",font=self.fnt_small)
        def animate_roll(cb,steps=8,delay=60):
            def _step(n=0):
                d1,d2=random.randint(1,6),random.randint(1,6); show_dice(d1,d2)
                if n<steps: self.after(delay,lambda:_step(n+1))
                else: cb(d1,d2)
            _step()
        def finish_craps(won,bet,msg,col):
            if won: self.money+=bet; self._post_game(bet,"win")
            else: self.money-=bet; self._post_game(bet,"loss")
            self._msg(msg,col); self._refresh_balance_text()
            for w in list(self._overlay_widgets): w.destroy()
            self._overlay_widgets.clear()
            self._make_btn(W//2-70,650,"AGAIN",self._craps_screen)
            self._make_btn(W//2+80,650,"BACK",self._back_to_interior,col="#333",fg=CREAM,w=80)
        def do_point_roll():
            c.delete("msg_layer")
            def after_pr(d1,d2):
                total=d1+d2; b=state["bet"]
                if total==state["point"]: finish_craps(True,b,f"Hit {total}! +${b}",GREEN_C)
                elif total==7: finish_craps(False,b,f"Seven out! -${b}",RED_C)
                else: self._msg(f"No decision — roll again",GOLD)
                self._refresh_balance_text()
            animate_roll(after_pr,steps=6)
        def on_deal(bet):
            state["bet"]=bet
            def after_come_out(d1,d2):
                total=d1+d2
                if total in(7,11): finish_craps(True,bet,f"Natural {total}! +${bet}",GREEN_C)
                elif total in(2,3,12): finish_craps(False,bet,f"Craps {total}! -${bet}",RED_C)
                else:
                    state["point"]=total; c.delete("msg_layer")
                    c.create_text(W//2,454,text=f"Point: {total} — roll {total} to win, 7 to lose",fill=GOLD,font=self.fnt_body,tags="point_lbl")
                    self._make_btn(W//2,508,"ROLL AGAIN",do_point_roll,col=BLUE_C,fg="white")
                self._refresh_balance_text()
            animate_roll(after_come_out)
        self._show_hotbar(on_deal)

    # ── WAR ───────────────────────────────────────────────
    def _war_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("WAR","#1a0a00","#2a1000")
        round_rect(c,80,120,W-80,H-HOTBAR_H-30,r=30,fill=FELT,outline="#0a3015",width=4)
        c.create_text(W//2,172,text="Highest card wins!",fill="#999",font=self.fnt_body)
        c.create_text(W//2,226,text="Dealer",fill=CREAM,font=self.fnt_body)
        c.create_text(W//2,396,text="You",fill=CREAM,font=self.fnt_body)
        rank_vals={r:i for i,r in enumerate(CARD_RANKS)}
        def on_deal(bet):
            deck=[(r,s) for r in CARD_RANKS for s in CARD_SUITS]; random.shuffle(deck)
            pr,ps=deck.pop(); dr,ds=deck.pop(); c.delete("war_cards","msg_layer")
            def show_cards():
                cs=CARD_SKINS[self.equipped_card_skin]
                for rx,ry,rk,rs in [(W//2,222,dr,ds),(W//2,390,pr,ps)]:
                    round_rect(c,rx-45,ry-70,rx+45,ry+70,r=10,fill=cs["face"],outline=cs["border"],width=2,tags="war_cards")
                    sym_col=cs["sym_r"] if rs in("♥","♦") else cs["sym_b"]
                    c.create_text(rx-28,ry-55,text=rk,fill=sym_col,font=tkfont.Font(size=22,weight="bold"),tags="war_cards")
                    c.create_text(rx,ry,text=rs,fill=sym_col,font=tkfont.Font(size=36),tags="war_cards")
                if rank_vals[pr]>rank_vals[dr]:
                    self.money+=bet; self._msg(f"{pr} beats {dr}! +${bet}",GREEN_C,y=548); self._post_game(bet,"win")
                elif rank_vals[pr]<rank_vals[dr]:
                    self.money-=bet; self._msg(f"{dr} beats {pr}. -${bet}",RED_C,y=548); self._post_game(bet,"loss")
                else:
                    self._msg("Tie! Bet returned.",GOLD,y=548); self._post_game(bet,"tie")
                self._refresh_balance_text()
                self._make_btn(W//2-70,640,"AGAIN",self._war_screen)
                self._make_btn(W//2+80,640,"BACK",self._back_to_interior,col="#333",fg=CREAM,w=80)
            self.after(300,show_cards)
        self._show_hotbar(on_deal)

    # ── HIGH CARD ─────────────────────────────────────────
    def _high_card_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("HIGH CARD","#001a1a","#002a2a")
        round_rect(c,80,120,W-80,H-HOTBAR_H-30,r=30,fill="#004444",outline="#006666",width=4)
        c.create_text(W//2,198,text="Draw one card each — highest wins!",fill=CREAM,font=self.fnt_body)
        rank_vals={r:i for i,r in enumerate(CARD_RANKS)}
        def on_deal(bet):
            deck=[(r,s) for r in CARD_RANKS for s in CARD_SUITS]; random.shuffle(deck)
            pr,ps=deck.pop(); dr,ds=deck.pop(); c.delete("hc_cards","msg_layer")
            def show():
                cs=CARD_SKINS[self.equipped_card_skin]
                for cx2,cy2,rk,rs,lbl in [(W//2-130,308,dr,ds,"DEALER"),(W//2+130,308,pr,ps,"YOU")]:
                    round_rect(c,cx2-50,cy2-75,cx2+50,cy2+75,r=10,fill=cs["face"],outline=cs["border"],width=2,tags="hc_cards")
                    sym_col=cs["sym_r"] if rs in("♥","♦") else cs["sym_b"]
                    c.create_text(cx2-32,cy2-58,text=rk,fill=sym_col,font=tkfont.Font(size=20,weight="bold"),tags="hc_cards")
                    c.create_text(cx2,cy2,text=rs,fill=sym_col,font=tkfont.Font(size=34),tags="hc_cards")
                    c.create_text(cx2,cy2+92,text=lbl,fill=GOLD,font=self.fnt_small,tags="hc_cards")
                if rank_vals[pr]>rank_vals[dr]:
                    self.money+=bet; self._msg(f"{pr} > {dr}! +${bet}",GREEN_C); self._post_game(bet,"win")
                elif rank_vals[pr]<rank_vals[dr]:
                    self.money-=bet; self._msg(f"{dr} > {pr}. -${bet}",RED_C); self._post_game(bet,"loss")
                else:
                    self._msg("Tie! No money lost.",GOLD); self._post_game(bet,"tie")
                self._refresh_balance_text()
                self._make_btn(W//2-70,650,"AGAIN",self._high_card_screen)
                self._make_btn(W//2+80,650,"BACK",self._back_to_interior,col="#333",fg=CREAM,w=80)
            self.after(250,show)
        self._show_hotbar(on_deal)

    # ── HORSE RACE ────────────────────────────────────────
    def _horse_race_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("HORSE RACING","#001000","#001800")
        TT=150; TB=490; FINISH_X=W-100; START_X=120; lane_h=(TB-TT)//5
        c.create_rectangle(START_X,TT,FINISH_X,TB,fill="#8B6914",outline=DARK,width=3)
        for i in range(5):
            ly=TT+i*lane_h; c.create_line(START_X,ly,FINISH_X,ly,fill="#6a4f10",width=2)
            for sx2 in range(START_X,FINISH_X,40):
                c.create_rectangle(sx2,ly,sx2+20,ly+lane_h,fill="#8B7214" if(sx2//40)%2==0 else"#9B8020",outline="")
        for fy in range(TT,TB,20):
            c.create_rectangle(FINISH_X-12,fy,FINISH_X,fy+20,fill="white" if(fy//20)%2==0 else"black",outline="")
        for i,(name,col) in enumerate(zip(HORSE_NAMES,HORSE_COLS)):
            c.create_text(START_X-5,TT+i*lane_h+lane_h//2,text=f"{i+1}. {name}",fill=col,font=self.fnt_small,anchor="e")
        c.create_text(W//2,TB+18,text="Pick horse (1-5):",fill=CREAM,font=self.fnt_body)
        pick_e=self._make_entry(W//2+150,TB+18,width=3)
        c.create_text(W//2,TB+46,text="Place chips below then DEAL to race!",fill="#888",font=self.fnt_small)
        positions=[START_X+20]*5; running=[False]
        def draw_horse(i,x):
            lane_y=TT+i*lane_h+lane_h//2; col=HORSE_COLS[i]
            c.create_oval(x-22,lane_y-10,x+22,lane_y+10,fill=col,outline=DARK,width=2,tags=f"horse_{i}")
            c.create_oval(x+14,lane_y-14,x+30,lane_y+2,fill=col,outline=DARK,width=2,tags=f"horse_{i}")
            c.create_text(x,lane_y,text=str(i+1),fill="white",font=tkfont.Font(size=9,weight="bold"),tags=f"horse_{i}")
        def on_deal(bet):
            try: pick=int(pick_e.get())-1; assert 0<=pick<=4
            except: self._msg("Pick a horse 1-5 first!",RED_C); self._show_hotbar(on_deal); return
            for w in list(self._overlay_widgets):
                try: w.destroy()
                except: pass
            self._overlay_widgets.clear()
            running[0]=True
            def race_tick():
                if not running[0]: return
                c.delete(*[f"horse_{i}" for i in range(5)],"race_msg")
                for i in range(5): positions[i]=min(positions[i]+random.randint(1,4),FINISH_X-10); draw_horse(i,positions[i])
                winners=[i for i,p in enumerate(positions) if p>=FINISH_X-12]
                if winners:
                    running[0]=False
                    c.create_text(W//2,TB+20,text=f"Winner: {HORSE_NAMES[winners[0]]}!",fill=GOLD,font=self.fnt_title,tags="race_msg")
                    if pick in winners and len(winners)==1:
                        self.money+=bet*3; self._msg(f"{HORSE_NAMES[pick]} wins! +${bet*3}",GREEN_C,y=TB+48); self._post_game(bet*3,"win")
                    elif pick in winners:
                        self._msg("Tie — bet returned.",GOLD,y=TB+48); self._post_game(bet,"tie")
                    else:
                        self.money-=bet; self._msg(f"{HORSE_NAMES[winners[0]]} wins. -${bet}",RED_C,y=TB+48); self._post_game(bet,"loss")
                    self._refresh_balance_text()
                    self._make_btn(W//2-70,650,"RACE AGAIN",self._horse_race_screen)
                    self._make_btn(W//2+90,650,"BACK",self._back_to_interior,col="#333",fg=CREAM,w=80)
                    return
                self.after(80,race_tick)
            race_tick()
        self._show_hotbar(on_deal)

    # ── DICE ROLL (NEW) ───────────────────────────────────
    def _dice_roll_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("DICE ROLL","#001a00","#002a00")
        round_rect(c,80,130,W-80,H-HOTBAR_H-20,r=20,fill=FELT,outline="#0a3015",width=3)
        c.create_text(W//2,200,text="You vs. Dealer — highest die wins!",fill=CREAM,font=self.fnt_body)
        c.create_text(W//2-200,290,text="YOU",fill=CREAM,font=self.fnt_title)
        c.create_text(W//2+200,290,text="DEALER",fill=CREAM,font=self.fnt_title)
        def draw_die(cx,cy,val,size=90,tag="die_img"):
            x,y=cx-size//2,cy-size//2
            ds=DICE_SKINS[self.equipped_dice_skin]
            round_rect(c,x,y,x+size,y+size,r=12,fill=ds["col"],outline=ds["ol"],width=3,tags=tag)
            pips={1:[(0.5,0.5)],2:[(0.25,0.25),(0.75,0.75)],3:[(0.25,0.25),(0.5,0.5),(0.75,0.75)],
                  4:[(0.25,0.25),(0.75,0.25),(0.25,0.75),(0.75,0.75)],
                  5:[(0.25,0.25),(0.75,0.25),(0.5,0.5),(0.25,0.75),(0.75,0.75)],
                  6:[(0.2,0.2),(0.8,0.2),(0.2,0.5),(0.8,0.5),(0.2,0.8),(0.8,0.8)]}
            pr=size*0.09
            for px2,py2 in pips.get(val,[]):
                c.create_oval(x+px2*size-pr,y+py2*size-pr,x+px2*size+pr,y+py2*size+pr,
                              fill=ds["dot"],outline="",tags=tag)
        draw_die(W//2-200,370,1); draw_die(W//2+200,370,1)
        def on_deal(bet):
            c.delete("die_img","die_total","msg_layer"); ticks=[0]
            def animate():
                d1=random.randint(1,6); d2=random.randint(1,6)
                draw_die(W//2-200,370,d1); draw_die(W//2+200,370,d2)
                ticks[0]+=1
                if ticks[0]<12: self.after(80,animate)
                else:
                    c.create_text(W//2-200,460,text=f"You: {d1}",fill=GOLD,font=self.fnt_body,tags="die_total")
                    c.create_text(W//2+200,460,text=f"Dealer: {d2}",fill=GOLD,font=self.fnt_body,tags="die_total")
                    if d1>d2:
                        self.money+=bet; self._msg(f"You rolled {d1}! +${bet}",GREEN_C); self._post_game(bet,"win")
                    elif d1<d2:
                        self.money-=bet; self._msg(f"Dealer rolled {d2}. -${bet}",RED_C); self._post_game(bet,"loss")
                    else:
                        self._msg(f"Both {d1}! Tie — bet returned.",GOLD); self._post_game(bet,"tie")
                    self._refresh_balance_text()
                    self._make_btn(W//2-70,620,"ROLL AGAIN",self._dice_roll_screen)
                    self._make_btn(W//2+80,620,"BACK",self._back_to_interior,col="#333",fg=CREAM,w=80)
            animate()
        self._show_hotbar(on_deal)
    # ── TEXAS HOLD'EM (NEW) ───────────────────────────────
    def _texas_holdem_screen(self,vip=False):
        self._clear_overlay(); c=self.canvas
        title="VIP TEXAS HOLD'EM" if vip else "TEXAS HOLD'EM"
        self._draw_room_bg(title,"#040f04","#081a08")
        round_rect(c,60,120,W-60,H-HOTBAR_H-10,r=40,fill=FELT,outline="#0a3015",width=4)
        round_rect(c,70,130,W-70,H-HOTBAR_H-20,r=36,fill=FELT_L,outline="")
        suits=list(CARD_SUITS.keys())
        deck=[(r,s) for r in CARD_RANKS for s in suits]; random.shuffle(deck)
        ANTE=100 if vip else 50
        state={"deck":deck,"phase":"bet","bet":0,"pot":0,
               "player":[],"ai1":[],"ai2":[],"community":[]}
        def draw_card_at(x,y,rank=None,suit=None,tag="pc"):
            cs=CARD_SKINS[self.equipped_card_skin]
            round_rect(c,x,y,x+56,y+82,r=6,fill=cs["face"],outline=cs["border"],width=2,tags=tag)
            if rank is None:
                round_rect(c,x+4,y+4,x+52,y+78,r=5,fill=cs["back"],outline=cs["border"],width=2,tags=tag)
                for pi in range(3):
                    for pj in range(4):
                        c.create_rectangle(x+8+pi*13,y+8+pj*16,x+15+pi*13,y+14+pj*16,
                                           fill=cs["border"],outline="",tags=tag)
            else:
                sym_col=cs["sym_r"] if suit in("♥","♦") else cs["sym_b"]
                c.create_text(x+8,y+12,text=rank,fill=sym_col,font=self.fnt_card,anchor="w",tags=tag)
                c.create_text(x+28,y+46,text=suit,fill=sym_col,font=tkfont.Font(size=18),anchor="center",tags=tag)
        def redraw_table():
            c.delete("pc","ai_cards","cc","score_lbl","pot_lbl")
            ph=state["phase"]
            for i,card in enumerate(state["player"]):
                draw_card_at(W//2-60+i*65,445,card[0],card[1],"pc")
            for i,card in enumerate(state["ai1"]):
                draw_card_at(200+i*65,165,card[0] if ph=="showdown" else None,
                             card[1] if ph=="showdown" else None,"ai_cards")
            for i,card in enumerate(state["ai2"]):
                draw_card_at(W-340+i*65,165,card[0] if ph=="showdown" else None,
                             card[1] if ph=="showdown" else None,"ai_cards")
            for i,card in enumerate(state["community"]):
                draw_card_at(W//2-145+i*68,305,card[0],card[1],"cc")
            c.create_text(W//2,435,text="YOUR HAND",fill="#2a5a2a",font=self.fnt_small,tags="score_lbl")
            c.create_text(185,155,text="AI Alice",fill=GOLD,font=self.fnt_small,tags="score_lbl")
            c.create_text(W-185,155,text="AI Bob",fill=GOLD,font=self.fnt_small,tags="score_lbl")
            if state["community"]: c.create_text(W//2,295,text="COMMUNITY",fill="#2a5a2a",font=self.fnt_small,tags="cc")
            c.create_text(W//2,535,text=f"Pot: ${state['pot']:,}",fill=GOLD,font=self.fnt_body,tags="pot_lbl")
        def deal_cards():
            for _ in range(2): state["player"].append(state["deck"].pop())
            for _ in range(2): state["ai1"].append(state["deck"].pop())
            for _ in range(2): state["ai2"].append(state["deck"].pop())
            redraw_table(); show_action_btns("preflop")
        def show_action_btns(stage):
            self._clear_overlay()
            lbl={"preflop":"Pre-Flop","flop":"The Flop","turn":"The Turn","river":"The River"}.get(stage,"")
            c.create_text(W//2,240,text=lbl,fill=GOLD,font=self.fnt_body,tags="pot_lbl")
            def do_check(): advance(stage)
            def do_raise():
                extra=max(50,state["bet"]//2)
                if self.money<extra: self._msg("Not enough!",RED_C); return
                state["pot"]+=extra; self.money-=extra; self._refresh_balance_text(); advance(stage)
            def do_fold():
                self._msg("You fold. Pot to AI.",RED_C,y=600)
                self.money-=0  # ante already deducted; pot lost
                self._post_game(state["bet"],"loss"); self._refresh_balance_text()
                back=self._vip_screen if vip else self._back_to_interior
                self._make_btn(W//2-70,645,"PLAY AGAIN",lambda:self._texas_holdem_screen(vip))
                self._make_btn(W//2+80,645,"BACK",back,col="#333",fg=CREAM,w=80)
            self._make_btn(W//2-200,580,"CHECK/CALL",do_check,col=BLUE_C,fg="white",w=140)
            self._make_btn(W//2,580,"RAISE",do_raise,col=ORANGE,fg=DARK,w=100)
            self._make_btn(W//2+180,580,"FOLD",do_fold,col=RED_C,fg="white",w=80)
        def advance(stage):
            self._clear_overlay()
            if stage=="preflop":
                state["deck"].pop()
                for _ in range(3): state["community"].append(state["deck"].pop())
                redraw_table(); show_action_btns("flop")
            elif stage=="flop":
                state["deck"].pop(); state["community"].append(state["deck"].pop())
                redraw_table(); show_action_btns("turn")
            elif stage=="turn":
                state["deck"].pop(); state["community"].append(state["deck"].pop())
                redraw_table(); show_action_btns("river")
            else: showdown()
        def showdown():
            state["phase"]="showdown"; redraw_table()
            all_hands={"YOU":best_poker_hand(state["player"]+state["community"]),
                       "Alice":best_poker_hand(state["ai1"]+state["community"]),
                       "Bob":best_poker_hand(state["ai2"]+state["community"])}
            winner=max(all_hands,key=lambda k:all_hands[k])
            c.delete("score_lbl")
            for i,(name,score) in enumerate(all_hands.items()):
                col=GREEN_C if name==winner else "#888"
                c.create_text(W//2-260+i*260,568,text=f"{name}: {HAND_NAMES.get(score[0],'?')}",
                              fill=col,font=self.fnt_small,tags="score_lbl")
            back=self._vip_screen if vip else self._back_to_interior
            if winner=="YOU":
                gain=state["pot"]+ANTE*2; self.money+=gain
                self._msg(f"YOU WIN with {HAND_NAMES.get(all_hands['YOU'][0],'?')}! +${gain}",GREEN_C,y=600)
                self._post_game(gain,"win")
            else:
                self._msg(f"{winner} wins with {HAND_NAMES.get(all_hands[winner][0],'?')}.",RED_C,y=600)
                self._post_game(state["bet"],"loss")
            self._refresh_balance_text()
            self._make_btn(W//2-70,645,"PLAY AGAIN",lambda:self._texas_holdem_screen(vip))
            self._make_btn(W//2+80,645,"BACK",back,col="#333",fg=CREAM,w=80)
        def on_deal(bet):
            state["bet"]=bet; state["pot"]=bet+ANTE*2
            if self.money<bet: self._msg("Not enough!",RED_C); self._show_hotbar(on_deal); return
            self.money-=bet; self._refresh_balance_text(); redraw_table()
            self.after(400,deal_cards)
        c.create_text(W//2,H-HOTBAR_H-55,text=f"Your ante goes in. AI both add ${ANTE} each. DEAL to start.",fill="#888",font=self.fnt_small)
        self._show_hotbar(on_deal)

    # ── YAHTZEE (NEW) ─────────────────────────────────────
    def _yahtzee_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("YAHTZEE","#1a1a00","#2a2a00")
        round_rect(c,60,100,W-60,H-10,r=20,fill="#111100",outline="#5a5a00",width=3)
        c.create_text(W//2,140,text="Roll up to 3 times · Hold dice · Pick a category",fill=CREAM,font=self.fnt_small)
        state={"dice":[1,1,1,1,1],"holds":[False]*5,"rolls":0,"bet":0,"scored":False}
        die_size=72; die_y=195; die_xs=[W//2-180+i*92 for i in range(5)]
        def draw_dice():
            c.delete("yah_dice")
            for i,v in enumerate(state["dice"]):
                x=die_xs[i]-die_size//2; y=die_y
                bg="#3a3a00" if state["holds"][i] else "#f5f5f0"
                fg="#f5f5f0" if state["holds"][i] else DARK
                border=GOLD if state["holds"][i] else "#aaa"
                round_rect(c,x,y,x+die_size,y+die_size,r=8,fill=bg,outline=border,width=3,tags="yah_dice")
                pips={1:[(0.5,0.5)],2:[(0.25,0.25),(0.75,0.75)],3:[(0.25,0.25),(0.5,0.5),(0.75,0.75)],
                      4:[(0.25,0.25),(0.75,0.25),(0.25,0.75),(0.75,0.75)],
                      5:[(0.25,0.25),(0.75,0.25),(0.5,0.5),(0.25,0.75),(0.75,0.75)],
                      6:[(0.2,0.2),(0.8,0.2),(0.2,0.5),(0.8,0.5),(0.2,0.8),(0.8,0.8)]}
                pr=die_size*0.09
                for px2,py2 in pips.get(v,[]):
                    c.create_oval(x+px2*die_size-pr,y+py2*die_size-pr,x+px2*die_size+pr,y+py2*die_size+pr,
                                  fill=fg,outline="",tags="yah_dice")
                if state["holds"][i]:
                    c.create_text(die_xs[i],die_y+die_size+14,text="HELD",fill=GOLD,font=self.fnt_small,tags="yah_dice")
        def do_roll():
            if state["rolls"]>=3: self._msg("3 rolls used! Pick a category.",RED_C,y=380); return
            for i in range(5):
                if not state["holds"][i]: state["dice"][i]=random.randint(1,6)
            state["rolls"]+=1; draw_dice()
            if state["rolls"]>=3: show_categories()
        def toggle_hold(i):
            if state["rolls"]==0: return
            state["holds"][i]=not state["holds"][i]; draw_dice()
        def show_roll_btns():
            rl=3-state["rolls"]
            self._make_btn(W//2,310+die_size,f"ROLL  ({rl} left)",do_roll,col="#5a5a00",fg=GOLD,w=150)
            for i in range(5):
                def mk(idx=i): return lambda:toggle_hold(idx)
                b=tk.Button(self,text=f"Hold {i+1}",command=mk(),font=self.fnt_small,
                            bg="#2a2a00",fg=GOLD,activebackground="#3a3a00",relief="flat",cursor="hand2",width=7)
                self.canvas.create_window(die_xs[i],die_y+die_size+38,window=b); self._overlay_widgets.append(b)
        def show_categories():
            self._clear_overlay()
            c.create_text(W//2,360,text="Pick a scoring category:",fill=GOLD,font=self.fnt_body)
            per_col=7
            for idx,(name,fn) in enumerate(YAHTZEE_CATS):
                sv=fn(state["dice"]); col_i=idx//per_col; row_i=idx%per_col
                bx=W//2-270+col_i*280; by=390+row_i*42
                def mk(n=name,sv2=sv):
                    def do():
                        if state["scored"]: return
                        state["scored"]=True; self._clear_overlay()
                        gain=int(sv2*(state["bet"]/50)) if state["bet"]>0 else sv2
                        if gain>0:
                            self.money+=gain; self._msg(f"{n}: {sv2}pts → +${gain}!",GREEN_C,y=500)
                            self._post_game(gain,"win")
                        else:
                            loss=max(1,state["bet"]//4); self.money-=loss
                            self._msg(f"{n}: 0pts. -${loss}",RED_C,y=500); self._post_game(loss,"loss")
                        self._refresh_balance_text()
                        self._make_btn(W//2-70,570,"PLAY AGAIN",self._yahtzee_screen)
                        self._make_btn(W//2+80,570,"BACK",self._back_to_interior,col="#333",fg=CREAM,w=80)
                    return do
                lbl=f"{name}: {fn(state['dice'])}"
                col_fg=GREEN_C if fn(state["dice"])>0 else "#555"
                b=tk.Button(self,text=lbl,command=mk(),font=self.fnt_small,
                            bg="#1a1a00",fg=col_fg,activebackground="#2a2a00",relief="flat",cursor="hand2",width=22)
                self.canvas.create_window(bx,by,window=b); self._overlay_widgets.append(b)
        def on_deal(bet):
            state["bet"]=bet; state["dice"]=[random.randint(1,6) for _ in range(5)]
            state["rolls"]=1; state["holds"]=[False]*5; state["scored"]=False
            draw_dice(); show_roll_btns()
        draw_dice()
        c.create_text(W//2,H-HOTBAR_H-55,text="Place a bet then DEAL to roll your first hand",fill="#888",font=self.fnt_small)
        self._show_hotbar(on_deal)
    # ── SHADY ALLEY ───────────────────────────────────────
    def _shady_screen(self):
        self._clear_overlay(); c=self.canvas
        c.create_rectangle(0,0,W,H,fill="#050505",outline="")
        for x in range(0,W,80): c.create_rectangle(x,0,x+40,H,fill="#080808",outline="")
        round_rect(c,W//2-320,60,W//2+320,H-40,r=18,fill="#0a0a0a",outline="#333",width=2)
        c.create_text(W//2,100,text="SHADY ALLEY",fill=RED_C,font=self.fnt_huge,anchor="center")
        c.create_line(W//2-280,130,W//2+280,130,fill="#333",width=1)
        c.create_text(W//2,162,text=f"Your balance: ${self.money:,}",fill=GOLD,font=self.fnt_body,anchor="center",tags="shady_bal")
        c.create_text(W//2,192,text=f"Your debt:    ${self.debt:,}",fill=RED_C if self.debt else "#555",font=self.fnt_body,anchor="center",tags="shady_debt")
        if self.debt>0:
            c.create_text(W//2,225,text=f"Note: Debt grows 10% every {INTEREST_INTERVAL} games you play.",fill="#888",font=self.fnt_small,anchor="center")
        def refresh_labels():
            c.delete("shady_bal","shady_debt")
            c.create_text(W//2,162,text=f"Your balance: ${self.money:,}",fill=GOLD,font=self.fnt_body,anchor="center",tags="shady_bal")
            c.create_text(W//2,192,text=f"Your debt:    ${self.debt:,}",fill=RED_C if self.debt else "#555",font=self.fnt_body,anchor="center",tags="shady_debt")
        # Borrow
        if not self.shady_borrowed or self.debt==0:
            amounts=[200,500,1000,2500]
            c.create_text(W//2,262,text="Borrow (10% interest every 3 games):",fill=CREAM,font=self.fnt_body,anchor="center")
            for i,amt in enumerate(amounts):
                def mk_borrow(a=amt):
                    def do():
                        self.money+=a; self.debt+=a
                        self.shady_borrowed=True; self.borrow_count+=1
                        self.interest_games_since_borrow=0
                        refresh_labels(); self._msg(f"Borrowed ${a:,}. Watch the interest…",RED_C,y=580)
                        self._refresh_balance_text()
                    return do
                self._make_btn(W//2-240+i*160,295,f"${amt:,}",mk_borrow(),col="#1a0000",fg=RED_C,w=90)
        # Repay
        if self.debt>0:
            c.create_text(W//2,355,text="Repay:",fill=CREAM,font=self.fnt_body,anchor="center")
            repay_e=self._make_entry(W//2,388,width=10)
            repay_e.insert(0,str(self.debt))
            def do_repay():
                try: amt=int(repay_e.get()); assert amt>0
                except: self._msg("Enter a valid amount.",RED_C,y=580); return
                amt=min(amt,self.debt,self.money)
                self.money-=amt; self.debt-=amt
                if self.debt<=0:
                    self.shady_borrowed=False; self.boss_alert_level=max(0,self.boss_alert_level-2)
                    self._msg(f"Debt cleared! Paid ${amt:,}.",GREEN_C,y=580)
                else:
                    self._msg(f"Paid ${amt:,}. Debt: ${self.debt:,}",GOLD,y=580)
                refresh_labels(); self._refresh_balance_text()
            self._make_btn(W//2+150,388,"REPAY",do_repay,col=GREEN_C,fg=DARK,w=90)
        # Work off debt
        if self.debt>0 and self.money<=0:
            c.create_text(W//2,440,text="Broke? Work it off.",fill="#888",font=self.fnt_small,anchor="center")
            self._make_btn(W//2,470,"WORK OFF DEBT",self._work_off_debt_screen,col="#333",fg=RED_C,w=160)
        self._make_btn(W//2,628,"Leave",self._leave_shady,col="#222",fg="#888",w=80)

    # ── VIP LOUNGE MENU ───────────────────────────────────
    def _vip_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("VIP LOUNGE","#0a0020","#140038")
        for i in range(12):
            a=(i/12)*2*math.pi
            c.create_oval(W//2+320*math.cos(a)-5,360+240*math.sin(a)-5,
                          W//2+320*math.cos(a)+5,360+240*math.sin(a)+5,fill=GOLD,outline="")
        c.create_text(W//2,110,text="Welcome, distinguished guest.",fill=GOLD,font=self.fnt_title)
        c.create_text(W//2,145,text=f"Balance: ${self.money:,}",fill=GOLD,font=self.fnt_body)
        c.create_line(W//2-260,168,W//2+260,168,fill="#4a2060",width=2)
        y0=205
        self._make_btn(W//2,y0,     "💎  Double or Nothing",     self._vip_double_screen,    col=PURPLE,   fg="white",w=260)
        self._make_btn(W//2,y0+70,  "🃏  High Stakes Blackjack",  self._vip_high_stakes_bj,   col="#5a0000", fg="white",w=260)
        self._make_btn(W//2,y0+140, "♠  VIP Texas Hold'em",      lambda:self._texas_holdem_screen(vip=True),col="#1a3a00",fg="white",w=260)
        self._make_btn(W//2,y0+210, "🎡  Golden Roulette",        self._vip_golden_roulette,  col="#4a3a00", fg="white",w=260)
        self._make_btn(W//2,y0+290, "Back",                       self._back_to_interior,    col="#333",    fg=CREAM,  w=100)

    def _vip_double_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("DOUBLE OR NOTHING","#05000f","#0a001a")
        N=10; WCX=W//2; WCY=295; WR=155
        WIN_SEGS={0,2,4,6}   # 4 of 10 = 40% visual; RNG uses 45%
        SEG_COLS={True:GOLD, False:"#6a0000"}
        wheel_rot=[0.0]; spinning=[False]

        def draw_wheel(rot=0.0):
            c.delete("whl")
            # Outer decorative ring
            c.create_oval(WCX-WR-18,WCY-WR-18,WCX+WR+18,WCY+WR+18,
                          fill="#1a0800",outline=GOLD,width=5,tags="whl")
            seg=360/N
            for i in range(N):
                win=i in WIN_SEGS
                start=rot+i*seg
                c.create_arc(WCX-WR,WCY-WR,WCX+WR,WCY+WR,
                             start=start,extent=seg-1,
                             fill=SEG_COLS[win],outline="#111",width=2,
                             style="pie",tags="whl")
                # Label inside segment
                mid=math.radians(start+seg/2)
                tx=WCX+(WR*0.66)*math.cos(mid)
                ty=WCY-(WR*0.66)*math.sin(mid)
                c.create_text(tx,ty,text="2×" if win else "✗",fill="white" if win else "#ff6666",
                              font=tkfont.Font(family="Courier New",size=9,weight="bold"),tags="whl")
            # Inner cap
            c.create_oval(WCX-22,WCY-22,WCX+22,WCY+22,fill="#1a0800",outline=GOLD,width=3,tags="whl")
            c.create_text(WCX,WCY,text="★",fill=GOLD,font=tkfont.Font(family="Georgia",size=14),tags="whl")
            # Fixed needle at top — drawn last so it's always on top
            c.create_polygon(WCX-9,WCY-WR-36,WCX+9,WCY-WR-36,
                             WCX,WCY-WR+8,
                             fill=RED_C,outline="#ff8800",width=2,tags="whl")
            c.create_oval(WCX-12,WCY-WR-44,WCX+12,WCY-WR-20,
                          fill="#1a0800",outline=GOLD,width=2,tags="whl")

        draw_wheel()

        # HUD
        c.create_text(W//2,490,text=f"Balance: ${self.money:,}",fill=GOLD,
                      font=self.fnt_body,anchor="center",tags="don_bal")
        c.create_text(W//2,520,text="Bet your entire balance — 45% chance to double",
                      fill="#665",font=self.fnt_small,anchor="center")

        def spin():
            if spinning[0]: return
            if self.money<=0: self._msg("No money to bet!",RED_C,y=570); return
            spinning[0]=True
            stake=self.money
            win=random.random()<0.45

            # Pick target segment
            win_list=list(WIN_SEGS); loss_list=[i for i in range(N) if i not in WIN_SEGS]
            target_seg=random.choice(win_list if win else loss_list)

            # Needle is at canvas 90° (top). A segment i starts at rot+i*seg_size.
            # We want needle (90°) to land inside target_seg, so:
            #   final_rot + target_seg*(360/N) + offset = 90  (mod 360)
            seg_size=360/N
            offset=random.uniform(4,seg_size-4)
            final_rot=(90-(target_seg*seg_size+offset))%360

            # How far to spin: several full laps + delta to reach final_rot
            cur=wheel_rot[0]
            delta=(final_rot-cur)%360
            total=4*360+delta
            end=cur+total

            speed=[26.0]; pos=[cur]

            def tick():
                pos[0]+=speed[0]
                speed[0]=max(0.35,speed[0]*0.983)
                draw_wheel(pos[0]%360)
                if pos[0]<end and speed[0]>0.36:
                    aid=self.after(16,tick); self._pending_after.append(aid)
                else:
                    wheel_rot[0]=final_rot
                    draw_wheel(final_rot)
                    spinning[0]=False
                    _settle(win,stake)

            aid=self.after(16,tick); self._pending_after.append(aid)

        def _settle(win,stake):
            c.delete("don_bal")
            if win:
                self.money+=stake
                self._post_game(stake,"win")
                self._msg(f"✦ DOUBLED! +${stake:,}",GREEN_C,y=570)
            else:
                self.money=0
                self._post_game(stake,"loss")
                self._msg("Lost it all.",RED_C,y=570)
            self._refresh_balance_text()
            c.create_text(W//2,490,text=f"Balance: ${self.money:,}",fill=GOLD,
                          font=self.fnt_body,anchor="center",tags="don_bal")

        self._make_btn(W//2-80,550,"SPIN",spin,col=PURPLE,fg="white",w=120)
        self._make_btn(W//2+80,550,"← Back",self._back_to_interior,col="#222",fg=CREAM,w=100)

    def _vip_high_stakes_bj(self):
        self._blackjack_screen(min_bet=500,title="HIGH STAKES BLACKJACK",payout=2.0)

    def _vip_golden_roulette(self):
        self._roulette_screen(golden=True)

    # ── BANK ─────────────────────────────────────────────
    def _bank_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("ACCOUNT STATEMENT","#001020","#001830")
        profit=self.money-self.starting_money
        profit_col=GREEN_C if profit>=0 else RED_C
        wr=round(self.wins/max(1,self.games_played)*100,1)
        rows=[
            ("Starting Balance",  f"${self.starting_money:,}"),
            ("Current Balance",   f"${self.money:,}"),
            ("Profit / Loss",     f"{'+'if profit>=0 else ''}{profit:,}"),
            ("Debt Outstanding",  f"${self.debt:,}"),
            ("",""),
            ("Games Played",      str(self.games_played)),
            ("Wins",              str(self.wins)),
            ("Losses",            str(self.losses)),
            ("Ties",              str(self.ties)),
            ("Win Rate",          f"{wr}%"),
            ("",""),
            ("Total Wagered",     f"${self.total_bet:,}"),
            ("Total Won",         f"${self.total_won:,}"),
            ("Total Lost",        f"${self.total_lost:,}"),
            ("",""),
            ("VIP Status",        "UNLOCKED ✓" if self.vip_unlocked else f"Need +${max(0,5000-profit):,} profit"),
            ("Arena Status",      "UNLOCKED ✓" if self.arena_unlocked else f"Need +${max(0,10000-profit):,} profit"),
        ]
        x1,x2=W//2-260,W//2+260; y=120
        round_rect(c,x1-20,y-10,x2+20,y+len(rows)*34+20,r=12,fill="#001428",outline=GOLD,width=2)
        for label,val in rows:
            if not label:
                c.create_line(x1,y+16,x2,y+16,fill="#1a2a3a",width=1)
            else:
                col=GOLD; 
                if label=="Profit / Loss": col=profit_col
                elif label in("Wins","Total Won"): col=GREEN_C
                elif label in("Losses","Total Lost","Debt Outstanding") and (self.losses>0 or self.debt>0): col=RED_C
                elif "UNLOCKED" in str(val): col=GREEN_C
                c.create_text(x1+10,y+16,text=label,fill=CREAM,font=self.fnt_small,anchor="w")
                c.create_text(x2-10,y+16,text=val,fill=col,font=self.fnt_small,anchor="e")
            y+=34
        self._make_btn(W//2,y+30,"Close",self._back_to_interior,col="#333",fg=CREAM,w=90)

    # ── ARENA FIGHT — Street Fighter style ───────────────
    def _arena_fight_screen(self):
        self._cancel_pending_afters(); self._clear_overlay()
        c=self.canvas

        if self.fight_stage>=5:
            c.delete("all")
            c.create_rectangle(0,0,W,H,fill="#0a0000")
            c.create_text(W//2,180,text="🏆  ARENA CHAMPION  🏆",fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=30,weight="bold"),anchor="center")
            c.create_text(W//2,260,text="You defeated all 5 fighters!",fill=CREAM,font=self.fnt_title,anchor="center")
            prize=5000; self.money+=prize; self._refresh_balance_text()
            c.create_text(W//2,330,text=f"Prize: +${prize:,}",fill=GOLD,font=self.fnt_title,anchor="center")
            self._post_game(prize,"win")
            self.fight_stage=0; self.enemy_hp=list(ENEMY_MAX_HP); self.player_health=100
            self._make_btn(W//2,430,"Fight Again",self._arena_fight_screen,col=RED_C,fg="white",w=180)
            self._make_btn(W//2,500,"Back to Arena",self._back_to_interior,col="#333",fg=CREAM,w=160)
            return

        if self.player_health<=0:
            c.delete("all")
            c.create_rectangle(0,0,W,H,fill="#0a0000")
            c.create_text(W//2,240,text="💀  K.O.  💀",fill=RED_C,font=self.fnt_huge,anchor="center")
            c.create_text(W//2,310,text="Visit the restaurant to restore HP.",fill=CREAM,font=self.fnt_body,anchor="center")
            self.player_health=30
            self._make_btn(W//2,400,"Back to Arena",self._back_to_interior,col="#333",fg=CREAM,w=140)
            return

        FIGHTERS=[
            dict(name="Brickwall Barry",col="#8B6020",pants="#1a3a6a",belt="#cc2200",
                 moves=["Jab","Cross","Gut Punch","Headbutt","Rushing Jab","Double Jab","Iron Jab"],
                 specials=[
                     ("IRON SHOULDER",(30,44),"charge"),   # charges across screen
                     ("HEADBUTT BLITZ",(22,34),"flurry"),  # rapid 3-hit
                 ],
                 p_dmg=(8,20),block=0.45,speed=2.0,aggression=0.65,dodge=0.20,combo_chance=0.45),
            dict(name="Slippery Sal",col="#a07850",pants="#4a004a",belt="#00aa88",
                 moves=["Flicker Jab","Jab Jab","Step-in Punch","Counter Hook","Bait Punch","Rush Jab","Shadow Strike"],
                 specials=[
                     ("SPIN FLURRY",      (20,32),"flurry"),
                     ("BACK DASH COUNTER",(18,28),"dodge"),
                     ("RUSH COMBO",       (22,34),"charge"),
                 ],
                 p_dmg=(5,16),block=0.55,speed=3.4,aggression=0.75,dodge=0.45,combo_chance=0.65),
            dict(name="The Mauler",col="#6a4818",pants="#0a0a0a",belt="#8B0000",
                 moves=["Overhand","Body Blow","Hook Punch","Slam Fist","Crushing Jab","Power Cross","Bone Breaker"],
                 specials=[
                     ("GROUND POUND",(36,52),"shockwave"), # shockwave along floor
                     ("BEAR HUG GRAB",(28,44),"grab"),     # grabs player can't block
                     ("CHARGE SMASH",(40,58),"charge"),    # charges full screen
                 ],
                 p_dmg=(12,26),block=0.35,speed=1.9,aggression=0.80,dodge=0.15,combo_chance=0.60),
            dict(name="Viper Vanessa",col="#c8a080",pants="#2a0040",belt="#cc8800",
                 moves=["Snake Jab","Flurry","Poison Jab","Double Cross","Counter Punch","Rapid Fire","Fang Strike"],
                 specials=[
                     ("SNAKE SHOT",  (22,34),"projectile"),  # fires snake projectile
                     ("TWIN FANGS",  (20,30),"twin_proj"),   # fires two snakes
                     ("VENOM CLOUD", (18,28),"cloud"),       # poison cloud zone
                     ("FANG RUSH",   (24,36),"flurry"),      # 5-hit fang combo
                 ],
                 p_dmg=(6,18),block=0.60,speed=3.0,aggression=0.85,dodge=0.50,combo_chance=0.75),
            dict(name="Fat Tony",col="#b08060",pants="#333",belt="#8B6914",
                 moves=["Sumo Punch","Belly Smash","Avalanche Fist","Seismic Jab","Wall Punch","Thunder Clap","Fat Jab"],
                 specials=[
                     ("CANNONBALL ROLL",(30,48),"roll"),   # rolls across screen bouncing
                     ("THE CRUSHER",(44,62),"grab"),       # unblockable grab
                     ("BELLY QUAKE",(26,40),"shockwave"),  # floor shockwave
                     ("SUMO STAMPEDE",(20,32),"charge"),   # fast charge
                 ],
                 p_dmg=(14,30),block=0.30,speed=1.6,aggression=0.90,dodge=0.10,combo_chance=0.70),
        ]
        ei=min(self.fight_stage,4); ef=FIGHTERS[ei]
        emax=ENEMY_MAX_HP[ei]; self.enemy_hp[ei]=emax

        FLOOR_Y=520; PUNCH_RANGE=125; KICK_RANGE=158
        GRAV=2.2; JUMP_VEL=-26
        # Player skill cooldowns (frames at 50ms each)
        COOLDOWNS={"punch":8,"kick":14,"fire_blast":60,"jump":0}

        fs={
            "php":self.player_health,"ehp":emax,
            "charge":0.0,
            "p_anim":"idle","e_anim":"idle",
            "p_anim_t":0,"e_anim_t":0,
            "flash_p":False,"flash_e":False,
            "msg":"","msg_col":CREAM,"msg_t":0,
            "p_x":160,"e_x":W-160,
            "p_y":0,"e_y":0,
            "p_vy":0,"e_vy":0,
            "e_attack_t":0,"e_combo_left":0,
            "combo":0,"frame":0,
            "ko_pending":False,"victory_pending":False,
            "blocking":False,
            "fireballs":[],
            "p_hit_t":0,"e_hit_t":0,
            # Player skill cooldown timers
            "cd_punch":0,"cd_kick":0,"cd_blast":0,
            # Enemy special state
            "e_roll_active":False,"e_roll_x":0,"e_roll_dx":0,"e_roll_bounces":0,
            "e_cloud_x":0,"e_cloud_y":0,"e_cloud_t":0,
            "e_special_type":"",
        }

        GAME_RUNNING=[True]; BOUND_IDS=[]
        def cleanup(): 
            for bid in BOUND_IDS:
                try: self.unbind("<KeyPress>",bid)
                except: pass
                try: self.unbind("<KeyRelease>",bid)
                except: pass
        def stop_game():
            GAME_RUNNING[0]=False; cleanup()
            for k in list(self.keys): self.keys.discard(k)

        def draw_player(x,floor_y,ground_offset,anim,flash,charge):
            y=floor_y-4-ground_offset
            skin="#e8b878"; gi="#cc2200"; pb="#1a3a6a"
            if flash: skin="#ffaaaa"; gi="#ff5555"
            if ground_offset>0:
                c.create_oval(x-20,floor_y-6,x+20,floor_y+2,fill="#222",outline="",tags="fg")
            else:
                c.create_oval(x-28,y+2,x+28,y+10,fill="#111",outline="",tags="fg")
            bob=int(3*math.sin(fs["frame"]*0.15)) if anim=="idle" and ground_offset==0 else 0
            y2=y+bob
            if anim=="kick":
                facing=1 if fs["e_x"]>=fs["p_x"] else -1
                c.create_line(x-8,y2-8,x-10,y2+22,fill=pb,width=10,tags="fg")
                c.create_line(x+8,y2-8,x+facing*38,y2-28,fill=pb,width=10,tags="fg")
                c.create_oval(x+facing*30,y2-40,x+facing*54,y2-18,fill="#8B6020",outline="",tags="fg")
            elif anim=="hurt":
                c.create_line(x-8,y2-8,x-24,y2+16,fill=pb,width=10,tags="fg")
                c.create_line(x+8,y2-8,x+24,y2+16,fill=pb,width=10,tags="fg")
            elif ground_offset>0:
                c.create_line(x-12,y2-6,x-10,y2+20,fill=pb,width=10,tags="fg")
                c.create_line(x+12,y2-6,x+10,y2+20,fill=pb,width=10,tags="fg")
            else:
                lsw=int(4*math.sin(fs["frame"]*0.15)) if anim=="idle" else 0
                c.create_line(x-8,y2-8,x-8+lsw,y2+24,fill=pb,width=10,tags="fg")
                c.create_line(x+8,y2-8,x+8-lsw,y2+24,fill=pb,width=10,tags="fg")
            c.create_oval(x-18,y2-44,x+18,y2-8,fill=gi,outline="#8B0000",width=2,tags="fg")
            c.create_rectangle(x-18,y2-16,x+18,y2-10,fill="#ffcc00",outline="#8B6914",width=1,tags="fg")
            if anim=="punch":
                facing=1 if fs["e_x"]>=fs["p_x"] else -1
                c.create_line(x-facing*16,y2-36,x-facing*26,y2-16,fill=gi,width=6,tags="fg")
                c.create_line(x+facing*16,y2-36,x+facing*58,y2-40,fill=gi,width=9,tags="fg")
                c.create_oval(x+facing*52,y2-48,x+facing*70,y2-30,fill=skin,outline="#8B5020",width=2,tags="fg")
            elif anim=="special":
                c.create_line(x-16,y2-34,x-46,y2-28,fill=gi,width=7,tags="fg")
                c.create_line(x+16,y2-34,x+46,y2-28,fill=gi,width=7,tags="fg")
            elif anim=="block":
                c.create_line(x-16,y2-38,x-10,y2-60,fill=gi,width=7,tags="fg")
                c.create_line(x+16,y2-38,x+10,y2-60,fill=gi,width=7,tags="fg")
                c.create_oval(x-20,y2-72,x+20,y2-48,fill="#334488",outline="#6688cc",width=2,tags="fg")
            elif anim not in("hurt",):
                asw=int(5*math.sin(fs["frame"]*0.15)) if anim=="idle" else 0
                c.create_line(x-16,y2-38,x-28,y2-14+asw,fill=gi,width=6,tags="fg")
                c.create_line(x+16,y2-38,x+28,y2-14-asw,fill=gi,width=6,tags="fg")
            c.create_oval(x-14,y2-68,x+14,y2-44,fill=skin,outline="#8B5020",width=2,tags="fg")
            c.create_rectangle(x-16,y2-70,x+16,y2-62,fill="#cc2200",outline="#8B0000",width=1,tags="fg")
            c.create_oval(x-7,y2-62,x-3,y2-58,fill="#1a1a1a",tags="fg")
            c.create_oval(x+3,y2-62,x+7,y2-58,fill="#1a1a1a",tags="fg")
            if anim=="block":
                c.create_text(x,y2-82,text="🛡 BLOCKING",fill="#6688cc",
                              font=tkfont.Font(family="Courier New",size=7,weight="bold"),tags="fg")
            bw=80
            c.create_rectangle(x-bw//2,y2-98,x+bw//2,y2-88,fill="#1a0000",outline="#333",width=1,tags="fg")
            if charge>0:
                cf="#ff8800" if charge<80 else "#ff2200"
                c.create_rectangle(x-bw//2,y2-98,x-bw//2+int(bw*charge/100),y2-88,fill=cf,outline="",tags="fg")
            c.create_text(x,y2-93,text=f"⚡{int(charge)}%",fill="#ffcc00",
                          font=tkfont.Font(family="Courier New",size=7,weight="bold"),tags="fg")
            dist=abs(fs["e_x"]-x)
            if dist<=KICK_RANGE and ground_offset==0:
                c.create_text(x,y2-110,text="IN RANGE",fill="#00ff88",
                              font=tkfont.Font(family="Courier New",size=7,weight="bold"),tags="fg")

        def draw_enemy(x,floor_y,ground_offset,ef2,anim,flash):
            y=floor_y-4-ground_offset
            skin=ef2["col"]; pants=ef2["pants"]; belt=ef2["belt"]
            if flash: skin="#ff8888"
            bob=int(4*math.sin(fs["frame"]*0.13+1)) if anim=="idle" and ground_offset==0 else 0
            y2=y+bob
            # face=+1 if player is to the right of enemy, -1 if to the left
            face=1 if fs["p_x"]>=x else -1
            if ground_offset>0:
                c.create_oval(x-22,floor_y-6,x+22,floor_y+2,fill="#222",outline="",tags="fg")
            else:
                c.create_oval(x-30,y2+2,x+30,y2+10,fill="#111",outline="",tags="fg")
            if anim in("attack","special"):
                c.create_line(x-8,y2-8,x-12,y2+26,fill=pants,width=11,tags="fg")
                c.create_line(x+8,y2-8,x+14,y2+26,fill=pants,width=11,tags="fg")
                # Punching arm extends toward player
                c.create_line(x+face*18,y2-34,x+face*62,y2-30,fill=skin,width=10,tags="fg")
                c.create_oval(x+face*68,y2-42,x+face*48,y2-22,fill=skin,outline="#1a0800",width=2,tags="fg")
                if anim=="special":
                    # Second arm also extends toward player (two-fisted)
                    c.create_line(x-face*18,y2-34,x-face*52,y2-28,fill=skin,width=9,tags="fg")
                    c.create_oval(x-face*46,y2-38,x-face*64,y2-20,fill=skin,outline="#1a0800",width=2,tags="fg")
            elif anim=="block":
                c.create_line(x-8,y2-8,x-12,y2+26,fill=pants,width=11,tags="fg")
                c.create_line(x+8,y2-8,x+14,y2+26,fill=pants,width=11,tags="fg")
                c.create_line(x-18,y2-38,x-12,y2-62,fill=skin,width=8,tags="fg")
                c.create_line(x+18,y2-38,x+12,y2-62,fill=skin,width=8,tags="fg")
                c.create_oval(x-22,y2-74,x+22,y2-50,fill="#663300",outline="#995500",width=2,tags="fg")
            elif anim=="hurt":
                c.create_line(x-8,y2-8,x-22,y2+22,fill=pants,width=11,tags="fg")
                c.create_line(x+8,y2-8,x+22,y2+22,fill=pants,width=11,tags="fg")
            elif ground_offset>0:
                c.create_line(x-12,y2-6,x-10,y2+22,fill=pants,width=11,tags="fg")
                c.create_line(x+12,y2-6,x+10,y2+22,fill=pants,width=11,tags="fg")
            else:
                lsw=int(4*math.sin(fs["frame"]*0.13)) if anim=="idle" else 0
                c.create_line(x-8,y2-8,x-8+lsw,y2+26,fill=pants,width=11,tags="fg")
                c.create_line(x+8,y2-8,x+8-lsw,y2+26,fill=pants,width=11,tags="fg")
            c.create_oval(x-20,y2-46,x+20,y2-6,fill=skin,outline="#1a0800",width=2,tags="fg")
            c.create_rectangle(x-20,y2-18,x+20,y2-10,fill=belt,outline="#5a3a00",width=1,tags="fg")
            if anim not in("attack","special","block","hurt"):
                asw=int(5*math.sin(fs["frame"]*0.13)) if anim=="idle" else 0
                # Front arm (toward player) swings forward, back arm swings back
                c.create_line(x+face*18,y2-40,x+face*30,y2-14+asw,fill=skin,width=7,tags="fg")
                c.create_line(x-face*18,y2-40,x-face*30,y2-14-asw,fill=skin,width=7,tags="fg")
            c.create_oval(x-16,y2-72,x+16,y2-44,fill=skin,outline="#1a0800",width=2,tags="fg")
            hgcol=[("#1a3a6a","#0a2040"),("#4a004a","#300030"),("#0a0a0a","#333"),(skin,"#553333"),("#8B6914",GOLD)]
            hc,hoc=hgcol[min(ei,4)]
            c.create_rectangle(x-18,y2-76,x+18,y2-68,fill=hc,outline=hoc,width=1,tags="fg")
            c.create_oval(x-8,y2-64,x-3,y2-58,fill="#cc0000",tags="fg")
            c.create_oval(x+3,y2-64,x+8,y2-58,fill="#cc0000",tags="fg")
            if anim=="block":
                c.create_text(x,y2-88,text="🛡 BLOCK",fill="#cc8833",
                              font=tkfont.Font(family="Courier New",size=7,weight="bold"),tags="fg")

        def draw_scene():
            c.delete("all")
            c.create_rectangle(0,0,W,H,fill="#0d0000")
            for cx3 in range(0,W,26):
                ch=random.Random(cx3+ei*777).randint(28,68)
                cc=random.Random(cx3*5+ei).choice(["#1a0000","#0d0010","#001a00","#1a1400"])
                c.create_oval(cx3-10,380-ch,cx3+10,380,fill=cc,outline="")
                c.create_oval(cx3-8,372-ch,cx3+8,372-ch+20,fill="#2a1100",outline="")
            c.create_rectangle(0,FLOOR_Y-8,W,H,fill="#1a0800")
            for lx3 in range(0,W,55): c.create_line(lx3,FLOOR_Y-8,lx3,H,fill="#2a1000",width=1)
            c.create_line(0,FLOOR_Y-8,W,FLOOR_Y-8,fill="#5a3010",width=3)
            round_rect(c,W//2-210,6,W//2+210,56,r=8,fill="#0a0000",outline=RED_C,width=2)
            c.create_text(W//2,20,text=f"STAGE {self.fight_stage+1}  ─  {ef['name'].upper()}",
                          fill=RED_C,font=tkfont.Font(family="Georgia",size=13,weight="bold"))
            c.create_text(W//2,42,text="★  FUNKY FEET FIGHTS  ★",fill="#8B0000",
                          font=tkfont.Font(family="Courier New",size=8))
            bw=370; bh=22; by=68
            c.create_rectangle(24,by,24+bw,by+bh,fill="#001a00",outline=GREEN_C,width=2)
            pw=int(bw*max(0,fs["php"])/100)
            hcol=GREEN_C if fs["php"]>40 else("#ffaa00" if fs["php"]>20 else RED_C)
            c.create_rectangle(24,by,24+pw,by+bh,fill=hcol,outline="")
            c.create_text(24+bw//2,by+11,text=f"YOU  {max(0,fs['php'])}/100",fill="white",font=self.fnt_small)
            exb=W-24-bw
            c.create_rectangle(exb,by,W-24,by+bh,fill="#1a0000",outline=RED_C,width=2)
            ew=int(bw*max(0,fs["ehp"])/emax)
            c.create_rectangle(W-24-ew,by,W-24,by+bh,fill=RED_C,outline="")
            c.create_text(exb+bw//2,by+11,text=f"{ef['name']}  {max(0,fs['ehp'])}/{emax}",fill="white",font=self.fnt_small)
            if fs["combo"]>1:
                c.create_text(W//2,108,text=f"✦ {fs['combo']}x COMBO! ✦",fill="#ffcc00",
                              font=tkfont.Font(family="Georgia",size=15,weight="bold"))
            for fb in fs["fireballs"]:
                if not fb["active"]: continue
                fx2=fb["x"]; fy2=FLOOR_Y-4-fb.get("ground_y",0)-42
                col2=fb.get("col","#ff4400")
                if col2.startswith("#0") or "green" in col2.lower() or col2=="#00cc44":
                    # Snake projectile
                    for si2 in range(5):
                        ox=si2*14*(-1 if fb["dx"]<0 else 1)
                        snake_y=fy2+int(6*math.sin(si2*0.8+fs["frame"]*0.3))
                        c.create_oval(fx2+ox-7,snake_y-5,fx2+ox+7,snake_y+5,fill="#00cc44",outline="#006622",width=1,tags="fg")
                    c.create_oval(fx2-10,fy2-8,fx2+10,fy2+8,fill="#00ee44",outline="#004400",width=2,tags="fg")
                    c.create_oval(fx2-4,fy2-3,fx2-1,fy2+3,fill="#ff2200",tags="fg")
                    c.create_oval(fx2+1,fy2-3,fx2+4,fy2+3,fill="#ff2200",tags="fg")
                else:
                    for fi2 in range(7):
                        ox=fi2*15*(-1 if fb["dx"]<0 else 1)
                        fc2=["#ff4400","#ff8800","#ffcc00","#ff2200","#ffee44","#ffffff","#ff6600"][fi2]
                        r2=max(3,13-fi2*2)
                        c.create_oval(fx2+ox-r2,fy2-r2,fx2+ox+r2,fy2+r2,fill=fc2,outline="",tags="fg")
                    c.create_oval(fx2-22,fy2-22,fx2+22,fy2+22,fill="",outline="#ff6600",width=3,tags="fg")
            # Venom cloud
            if fs["e_cloud_t"]>0:
                cx4=fs["e_cloud_x"]; cy4=FLOOR_Y-40
                alpha=fs["e_cloud_t"]/40
                for ci3 in range(8):
                    ang=ci3*45+fs["frame"]*3; r3=int(45+12*math.sin(ci3))
                    cxoff=int(r3*math.cos(math.radians(ang))); cyoff=int(r3*0.5*math.sin(math.radians(ang)))
                    c.create_oval(cx4+cxoff-18,cy4+cyoff-12,cx4+cxoff+18,cy4+cyoff+12,
                                  fill="#44ff44",outline="#00cc00",width=1,stipple="gray50",tags="fg")
                c.create_text(cx4,cy4-30,text="☠ VENOM CLOUD",fill="#88ff44",
                              font=tkfont.Font(family="Courier New",size=8,weight="bold"),tags="fg")
            # Fat Tony roll anim
            if fs["e_roll_active"]:
                rx=fs["e_x"]; ry=FLOOR_Y-30
                angle=fs["frame"]*15
                c.create_oval(rx-28,ry-28,rx+28,ry+28,fill="#b08060",outline="#8B6914",width=3,tags="fg")
                c.create_arc(rx-28,ry-28,rx+28,ry+28,start=angle,extent=180,fill="#9a7050",outline="",tags="fg")
                c.create_text(rx,ry,text="💥",font=tkfont.Font(size=16),tags="fg")
            draw_player(fs["p_x"],FLOOR_Y,int(fs["p_y"]),fs["p_anim"],fs["flash_p"],fs["charge"])
            draw_enemy(fs["e_x"],FLOOR_Y,int(fs["e_y"]),ef,fs["e_anim"],fs["flash_e"])
            if fs["msg"] and fs["msg_t"]>0:
                tw=max(220,len(fs["msg"])*9)
                round_rect(c,W//2-tw//2-10,548,W//2+tw//2+10,580,r=7,fill="#0a0000",outline=fs["msg_col"],width=2)
                c.create_text(W//2,564,text=fs["msg"],fill=fs["msg_col"],
                              font=tkfont.Font(family="Georgia",size=12,weight="bold"))
            sk=self.fight_skills
            hint="← → Move   A Punch"
            if sk["kick"]: hint+="   S Kick"
            if sk["fire_blast"]: hint+="   Hold D→Release Blast"
            if sk["block"]: hint+="   F Block"
            if sk["jump"]: hint+="   W Jump"
            hint+="   (Dojo: buy more skills)"
            c.create_text(W//2,H-20,text=hint,fill="#444",font=tkfont.Font(family="Courier New",size=8))
            if fs["ko_pending"]:
                c.create_rectangle(0,0,W,H,fill="#000000",stipple="gray50",outline="")
                c.create_text(W//2,H//2-20,text="K.O.!",fill=RED_C,
                              font=tkfont.Font(family="Georgia",size=56,weight="bold"),anchor="center")
            if fs["victory_pending"]:
                c.create_rectangle(0,0,W,H,fill="#000000",stipple="gray50",outline="")
                c.create_text(W//2,H//2-20,text="VICTORY!",fill="#ffcc00",
                              font=tkfont.Font(family="Georgia",size=48,weight="bold"),anchor="center")
            fs["frame"]+=1

        def _apply_grav():
            for who in ["p","e"]:
                y_key=who+"_y"; vy_key=who+"_vy"
                if fs[y_key]>0 or fs[vy_key]!=0:
                    fs[vy_key]+=GRAV
                    fs[y_key]=max(0,fs[y_key]-fs[vy_key])
                    if fs[y_key]<=0:
                        fs[y_key]=0; fs[vy_key]=0

        def game_loop():
            if not GAME_RUNNING[0]: return
            fs["p_anim_t"]=max(0,fs["p_anim_t"]-1)
            fs["e_anim_t"]=max(0,fs["e_anim_t"]-1)
            fs["msg_t"]=max(0,fs["msg_t"]-1)
            if fs["p_anim_t"]==0 and fs["p_anim"] not in("idle","block"): fs["p_anim"]="idle"
            if fs["e_anim_t"]==0 and fs["e_anim"] not in("idle","block"): fs["e_anim"]="idle"
            fs["flash_p"]=False; fs["flash_e"]=False
            if fs["p_hit_t"]>0: fs["p_hit_t"]-=1
            if fs["e_hit_t"]>0: fs["e_hit_t"]-=1
            # Tick player cooldowns
            for cd in ("cd_punch","cd_kick","cd_blast"):
                if fs[cd]>0: fs[cd]-=1
            # Tick cloud
            if fs["e_cloud_t"]>0:
                fs["e_cloud_t"]-=1
                if abs(fs["p_x"]-fs["e_cloud_x"])<80 and fs["p_y"]<30 and fs["p_hit_t"]==0:
                    _enemy_hit_player(4,"☠ Venom Cloud",False)

            # Player movement
            airborne=fs["p_y"]>20
            move_spd=6 if getattr(self,'creative_mode',False) else 4
            if "left" in self.keys:
                if airborne:
                    fs["p_x"]=max(40,fs["p_x"]-move_spd+1)   # slightly slower mid-air
                else:
                    # On ground: can't pass through enemy from the right side
                    fs["p_x"]=max(40, max(fs["e_x"]+55,fs["p_x"]-move_spd) if fs["p_x"]>fs["e_x"] else fs["p_x"]-move_spd)
            if "right" in self.keys:
                if airborne:
                    fs["p_x"]=min(W-40,fs["p_x"]+move_spd+1)
                else:
                    # On ground: can't pass through enemy from the left side
                    fs["p_x"]=min(W-40, min(fs["e_x"]-55,fs["p_x"]+move_spd) if fs["p_x"]<fs["e_x"] else fs["p_x"]+move_spd)
            if "d" in self.keys: fs["charge"]=min(100,fs["charge"]+2.6)
            if "f" in self.keys and self.fight_skills["block"]:
                if fs["p_anim"]=="idle": fs["p_anim"]="block"
            elif fs["p_anim"]=="block": fs["p_anim"]="idle"

            _apply_grav()

            # Fat Tony roll
            if fs["e_roll_active"]:
                fs["e_x"]+=fs["e_roll_dx"]
                if fs["e_x"]<=60:   fs["e_x"]=60;  fs["e_roll_dx"]=abs(fs["e_roll_dx"]); fs["e_roll_bounces"]+=1
                if fs["e_x"]>=W-60: fs["e_x"]=W-60; fs["e_roll_dx"]=-abs(fs["e_roll_dx"]); fs["e_roll_bounces"]+=1
                # Hit player
                if abs(fs["e_x"]-fs["p_x"])<50 and fs["p_hit_t"]==0:
                    _enemy_hit_player(random.randint(28,42),"🔵 CANNONBALL ROLL",True)
                if fs["e_roll_bounces"]>=4:
                    fs["e_roll_active"]=False; fs["e_anim"]="idle"

            # Fireballs
            for fb in fs["fireballs"]:
                if not fb["active"]: continue
                fb["x"]+=fb["dx"]
                fb["ground_y"]=fb.get("ground_y",0)
                if abs(fb["x"]-fs["e_x"])<46 and abs(fb["ground_y"]-fs["e_y"])<60 and fs["ehp"]>0:
                    fb["active"]=False; _deal_damage_to_enemy(fb["dmg"],"🔥 FIRE BLAST!","#ff8800",True)
                elif fb.get("owner")=="enemy" and abs(fb["x"]-fs["p_x"])<46 and abs(fb.get("ground_y",0)-fs["p_y"])<60:
                    fb["active"]=False; _enemy_hit_player(fb["dmg"],fb.get("label","Projectile"),True)
                elif fb["x"]>W+50 or fb["x"]<-50: fb["active"]=False
            fs["fireballs"]=[fb for fb in fs["fireballs"] if fb["active"]]

            # Enemy AI — freeze horizontal movement while player is in the air
            if fs["e_attack_t"]>0:
                fs["e_attack_t"]-=1
            elif not fs["e_roll_active"]:
                dist=abs(fs["e_x"]-fs["p_x"])
                player_airborne=fs["p_y"]>20
                if dist>PUNCH_RANGE+30 and not player_airborne:
                    fs["e_x"]+= -ef["speed"] if fs["e_x"]>fs["p_x"] else ef["speed"]
                # Viper: fires projectiles even from range
                if ei==3 and dist>PUNCH_RANGE+30 and random.random()<0.25 and fs["e_attack_t"]==0:
                    _enemy_do_special()
                elif dist<=PUNCH_RANGE+30:
                    r=random.random()
                    cool_base=max(5,20-self.fight_stage*2)
                    if fs["e_combo_left"]>0:
                        fs["e_combo_left"]-=1
                        _enemy_attack(random.choice(ef["moves"]),random.randint(*ef["p_dmg"]),"punch",cool_base)
                    # Fat Tony: high roll rate
                    elif ei==4 and r<0.35 and not fs["e_roll_active"]:
                        _enemy_do_special_forced("roll")
                    # Viper: high projectile rate — picks snake or twin
                    elif ei==3 and r<0.45:
                        _enemy_do_special_forced(random.choice(["projectile","twin_proj"]))
                    elif r<ef["aggression"]*0.28:
                        _enemy_do_special()
                    elif r<ef["aggression"]*0.65:
                        combo_n=random.randint(1,3) if random.random()<ef["combo_chance"] else 1
                        fs["e_combo_left"]=combo_n-1
                        _enemy_attack(random.choice(ef["moves"]),random.randint(*ef["p_dmg"]),"punch",cool_base)
                    elif r<ef["aggression"]*0.75 and fs["e_y"]==0:
                        fs["e_vy"]=JUMP_VEL; fs["e_attack_t"]=random.randint(10,22)
                    else:
                        fs["e_anim"]="block"; fs["e_anim_t"]=random.randint(5,14)
                        fs["e_attack_t"]=random.randint(8,20)

            draw_scene()
            if GAME_RUNNING[0]:
                aid=self.after(50,game_loop); self._pending_after.append(aid)

        def _enemy_attack(move,dmg,atype,cooldown):
            fs["e_anim"]="special" if atype not in("punch",) else"attack"; fs["e_anim_t"]=10
            fs["e_attack_t"]=cooldown
            if fs["p_hit_t"]>0: return
            _enemy_hit_player(dmg,move,atype not in("punch",))

        def _enemy_do_special():
            specials=ef.get("specials",[])
            if not specials: return
            name,dmg_range,stype=random.choice(specials)
            dmg=random.randint(*dmg_range)
            cool=random.randint(35,60)
            fs["e_anim"]="special"; fs["e_anim_t"]=14; fs["e_attack_t"]=cool
            fs["e_special_type"]=stype

            if stype=="roll" and not fs["e_roll_active"]:
                # Fat Tony cannonball roll
                fs["e_roll_active"]=True
                fs["e_roll_dx"]=-8 if fs["e_x"]>fs["p_x"] else 8
                fs["e_roll_bounces"]=0
                fs["msg"]=f"🔵 {name}! Tony is ROLLING!"; fs["msg_col"]="#ffaa00"; fs["msg_t"]=18
            elif stype=="projectile":
                # Viper snake shot
                direction=-1 if fs["e_x"]>fs["p_x"] else 1
                fs["fireballs"].append({"x":fs["e_x"]+direction*40,"y":FLOOR_Y-30,
                                        "dx":direction*15,"dmg":dmg,"ground_y":0,
                                        "active":True,"owner":"enemy","label":f"🐍 {name}",
                                        "col":"#00cc44"})
                fs["msg"]=f"🐍 {name}! Dodge it!"; fs["msg_col"]="#00cc44"; fs["msg_t"]=16
            elif stype=="cloud":
                # Viper venom cloud lingers
                fs["e_cloud_x"]=fs["p_x"]; fs["e_cloud_y"]=FLOOR_Y-40; fs["e_cloud_t"]=40
                fs["msg"]=f"☠ {name}! Toxic zone!"; fs["msg_col"]="#88ff44"; fs["msg_t"]=16
            elif stype=="grab":
                # Unblockable grab — ignore block
                old_block=fs["blocking"]; fs["blocking"]=False
                _enemy_hit_player(dmg,f"💪 {name} (UNBLOCKABLE)",True)
                fs["blocking"]=old_block
                fs["msg"]=f"💪 {name}! Can't block this!"; fs["msg_col"]=RED_C; fs["msg_t"]=18
            elif stype=="charge":
                # Quick dash — only hits if close enough (no infinite range)
                if abs(fs["e_x"]-fs["p_x"])<=300:
                    step=60 if fs["e_x"]>fs["p_x"] else -60
                    fs["e_x"]=max(80,min(W-80,fs["p_x"]-step))
                    _enemy_hit_player(dmg,f"💨 {name}",True)
                    fs["msg"]=f"💨 {name}! DASH PUNCH!"; fs["msg_col"]="#ff8800"; fs["msg_t"]=16
                else:
                    fs["msg"]=f"{name} charging..."; fs["msg_col"]="#888"; fs["msg_t"]=8
            elif stype=="shockwave":
                # Floor shockwave — only hits grounded player
                if fs["p_y"]<20:
                    _enemy_hit_player(dmg,f"🌊 {name} (floor shockwave)",True)
                    fs["msg"]=f"🌊 {name}! JUMP to dodge!"; fs["msg_col"]="#ff8800"; fs["msg_t"]=18
                else:
                    fs["msg"]=f"🌊 {name} — you jumped over it!"; fs["msg_col"]="#00ff88"; fs["msg_t"]=16
            elif stype=="flurry":
                # Schedule rapid multi-hits
                hits=random.randint(3,5)
                fs["e_combo_left"]=hits-1
                _enemy_hit_player(dmg//hits+random.randint(2,6),f"⚡ {name} hit 1",False)
                fs["msg"]=f"⚡ {name}! Brace yourself!"; fs["msg_col"]=RED_C; fs["msg_t"]=18
            elif stype=="twin_proj":
                # Viper fires two snake shots with slight vertical spread
                direction=-1 if fs["e_x"]>fs["p_x"] else 1
                for offset in [-20, 20]:
                    fs["fireballs"].append({"x":fs["e_x"]+direction*44,"y":FLOOR_Y-30+offset,
                                            "dx":direction*14,"dmg":dmg//2+random.randint(2,8),
                                            "ground_y":max(0,-offset),"active":True,
                                            "owner":"enemy","label":f"🐍 {name}","col":"#00cc44"})
                fs["msg"]=f"🐍🐍 {name}! TWO SNAKES!"; fs["msg_col"]="#00ee44"; fs["msg_t"]=16
            else:
                _enemy_hit_player(dmg,f"★ {name}",True)

        def _enemy_do_special_forced(stype):
            """Trigger a specific special type directly."""
            specials=ef.get("specials",[])
            matches=[s for s in specials if s[2]==stype]
            if not matches: _enemy_do_special(); return
            name,dmg_range,_stype=random.choice(matches)
            # Temporarily patch and call
            dmg=random.randint(*dmg_range)
            cool=random.randint(30,55)
            fs["e_anim"]="special"; fs["e_anim_t"]=14; fs["e_attack_t"]=cool
            fs["e_special_type"]=stype
            if stype=="roll" and not fs["e_roll_active"]:
                fs["e_roll_active"]=True
                fs["e_roll_dx"]=-9.0 if fs["e_x"]>fs["p_x"] else 9.0
                fs["e_roll_bounces"]=0
                fs["msg"]=f"🔵 {name}! Tony is ROLLING!"; fs["msg_col"]="#ffaa00"; fs["msg_t"]=18
            elif stype in("projectile","twin_proj"):
                direction=-1 if fs["e_x"]>fs["p_x"] else 1
                fs["fireballs"].append({"x":fs["e_x"]+direction*44,"y":FLOOR_Y-30,
                                        "dx":direction*16,"dmg":dmg,"ground_y":0,
                                        "active":True,"owner":"enemy","label":f"🐍 {name}","col":"#00cc44"})
                if stype=="twin_proj":
                    fs["fireballs"].append({"x":fs["e_x"]+direction*44,"y":FLOOR_Y-10,
                                            "dx":direction*13,"dmg":dmg//2,"ground_y":20,
                                            "active":True,"owner":"enemy","label":f"🐍 {name}","col":"#00cc44"})
                    fs["msg"]=f"🐍🐍 {name}! TWO SNAKES!"; fs["msg_col"]="#00ee44"; fs["msg_t"]=16
                else:
                    fs["msg"]=f"🐍 {name}! DODGE!"; fs["msg_col"]="#00cc44"; fs["msg_t"]=16

        def _enemy_hit_player(dmg,move,is_spec=False):
            # Creative mode: near-invincible
            if getattr(self,'creative_mode',False):
                dmg=1; self.money=max(self.money,999_999_999)
            # Enemy can't hit airborne player with melee
            if fs["p_y"]>30 and not is_spec: return
            is_blocked=fs["blocking"] and self.fight_skills["block"]
            # Dodge check
            if not is_spec and random.random()<ef["dodge"]*0.3:
                fs["msg"]=f"{ef['name']} MISSED!"; fs["msg_col"]="#888"; fs["msg_t"]=12; return
            if is_blocked:
                dmg=max(1,int(dmg*0.12))
                fs["msg"]=f"🛡 BLOCKED! Chip dmg: {dmg}"; fs["msg_col"]="#aaccff"; fs["msg_t"]=14
            else:
                fs["msg"]=f"{ef['name']}: {move}!  -{dmg} HP"; fs["msg_col"]=RED_C; fs["msg_t"]=16
            fs["p_anim"]="hurt" if not is_blocked else "block"; fs["p_anim_t"]=8
            fs["flash_p"]=True; fs["p_hit_t"]=14
            fs["php"]=max(0,fs["php"]-dmg); self.player_health=fs["php"]
            if fs["php"]<=0:
                fs["ko_pending"]=True; GAME_RUNNING[0]=False
                draw_scene(); stop_game()
                self.after(1800,self._arena_fight_screen)

        def _deal_damage_to_enemy(dmg,shout,col,is_special=False):
            if fs["ehp"]<=0: return
            # Enemy can't be hit by melee while airborne
            if fs["e_y"]>30 and not is_special:
                fs["msg"]="Missed — enemy is airborne!"; fs["msg_col"]="#888"; fs["msg_t"]=12; return
            if fs["e_hit_t"]>0: return
            # Enemy block
            block_r=ef["block"]
            if fs["e_anim"]=="block": block_r=min(0.95,block_r+0.40)
            if random.random()<block_r:
                dmg=max(1,int(dmg*(0.08 if fs["e_anim"]=="block" else 0.30)))
                fs["msg"]=f"{ef['name']} BLOCKED hard! {dmg} chip dmg"
                fs["msg_col"]="#aaccff"; fs["msg_t"]=14; fs["combo"]=0
            else:
                fs["combo"]+=1
                combo_str=f"  x{fs['combo']} COMBO!" if fs["combo"]>1 else ""
                fs["msg"]=f"{shout} {dmg} dmg!{combo_str}"; fs["msg_col"]=col; fs["msg_t"]=16
            fs["e_anim"]="hurt"; fs["e_anim_t"]=8; fs["flash_e"]=True; fs["e_hit_t"]=10
            fs["ehp"]=max(0,fs["ehp"]-dmg); self.enemy_hp[ei]=fs["ehp"]
            if fs["ehp"]<=0:
                fs["victory_pending"]=True; GAME_RUNNING[0]=False
                draw_scene(); stop_game()
                prize=100+self.fight_stage*75; self.money+=prize
                self.fight_stage+=1; self.enemy_hp[ei]=emax
                self._refresh_balance_text()
                self.after(1800,self._arena_fight_screen)

        def do_punch():
            if not GAME_RUNNING[0] or fs["ko_pending"] or fs["victory_pending"]: return
            if fs["cd_punch"]>0: return
            fs["p_anim"]="punch"; fs["p_anim_t"]=9; fs["cd_punch"]=COOLDOWNS["punch"]
            # Direction: face toward enemy
            if abs(fs["e_x"]-fs["p_x"])>PUNCH_RANGE:
                fs["msg"]="Whiff! (out of range)"; fs["msg_col"]="#888"; fs["msg_t"]=8
            else:
                _deal_damage_to_enemy(random.randint(10,22)+fs["combo"]*2,"CRACK!",RED_C)

        def do_kick():
            if not GAME_RUNNING[0] or fs["ko_pending"] or fs["victory_pending"]: return
            if not self.fight_skills["kick"]:
                fs["msg"]="Buy Kick at the Dojo!"; fs["msg_col"]="#888"; fs["msg_t"]=16; return
            if fs["cd_kick"]>0: return
            fs["p_anim"]="kick"; fs["p_anim_t"]=9; fs["cd_kick"]=COOLDOWNS["kick"]
            if abs(fs["e_x"]-fs["p_x"])>KICK_RANGE:
                fs["msg"]="Whiff! (out of range)"; fs["msg_col"]="#888"; fs["msg_t"]=8
            else:
                _deal_damage_to_enemy(random.randint(16,32)+fs["combo"]*2,"THWACK!",RED_C)

        def do_fire_release():
            if not GAME_RUNNING[0] or fs["ko_pending"] or fs["victory_pending"]: return
            if not self.fight_skills["fire_blast"]:
                fs["msg"]="Buy Fire Blast at the Dojo!"; fs["msg_col"]="#888"; fs["msg_t"]=16; return
            if fs["cd_blast"]>0:
                fs["msg"]="Fire Blast cooling down…"; fs["msg_col"]="#888"; fs["msg_t"]=8; return
            if fs["charge"]<30:
                fs["msg"]="Hold D longer to charge!"; fs["msg_col"]="#888"; fs["msg_t"]=14
                fs["charge"]=0; return
            dmg=int(fs["charge"]*0.78)+random.randint(10,22)
            fs["p_anim"]="special"; fs["p_anim_t"]=12; fs["cd_blast"]=COOLDOWNS["fire_blast"]
            direction=1 if fs["e_x"]>fs["p_x"] else -1
            fs["fireballs"].append({"x":fs["p_x"]+direction*52,"y":FLOOR_Y-42,
                                    "dx":direction*22,"dmg":dmg,"ground_y":fs["p_y"],
                                    "active":True,"owner":"player"})
            fs["charge"]=0

        def do_jump():
            if not GAME_RUNNING[0] or fs["ko_pending"] or fs["victory_pending"]: return
            if not self.fight_skills["jump"]:
                fs["msg"]="Buy Jump at the Dojo!"; fs["msg_col"]="#888"; fs["msg_t"]=16; return
            if fs["p_y"]==0:
                fs["p_vy"]=JUMP_VEL

        def on_key_press(e):
            k=e.keysym.lower()
            if k=="a": do_punch()
            elif k=="s": do_kick()
            elif k=="w": do_jump()
            elif k=="f":
                fs["blocking"]=True
                if self.fight_skills["block"] and fs["p_anim"]=="idle":
                    fs["p_anim"]="block"
        def on_key_release(e):
            k=e.keysym.lower()
            if k=="d": do_fire_release()
            elif k=="f":
                fs["blocking"]=False
                if fs["p_anim"]=="block": fs["p_anim"]="idle"

        bid_p=self.bind("<KeyPress>",on_key_press,"+")
        bid_r=self.bind("<KeyRelease>",on_key_release,"+")
        BOUND_IDS.extend([bid_p,bid_r])
        draw_scene(); game_loop()

    # ── ARENA BET (NEW) ───────────────────────────────────
    def _arena_bet_screen(self):
        self._cancel_pending_afters(); self._clear_overlay()
        c=self.canvas

        FIGHTER_COLS={
            "Brickwall Barry": ("#8B6020","#1a3a6a","#cc2200"),
            "Slippery Sal":    ("#a07850","#4a004a","#00aa88"),
            "The Mauler":      ("#6a4818","#0a0a0a","#8B0000"),
            "Viper Vanessa":   ("#c8a080","#2a0040","#cc8800"),
            "Fat Tony":        ("#b08060","#333333","#8B6914"),
        }
        all_names=list(FIGHTER_COLS.keys())
        f1_name,f2_name=random.sample(all_names,2)
        f1c=FIGHTER_COLS[f1_name]; f2c=FIGHTER_COLS[f2_name]
        # Randomised hidden strengths — determines winner probability
        f1_str=random.randint(40,100); f2_str=random.randint(40,100)

        # --- State ---
        state={"phase":"betting","bet_on":None,"bet_amount":0,
               "f1_hp":100,"f2_hp":100,
               "f1_x":200,"f2_x":W-200,
               "f1_anim":"idle","f2_anim":"idle",
               "f1_anim_t":0,"f2_anim_t":0,
               "f1_y":0,"f2_y":0,"f1_vy":0,"f2_vy":0,
               "frame":0,"msg":"","msg_t":0,"msg_col":CREAM,
               "tick_t":0,"winner":None,"fireballs":[]}
        FLOOR_Y=490; GRAV=2.4; JVEL=-20

        # Per-fighter sim weights [punch, jump_punch, special, dodge]
        FIGHTER_WEIGHTS={
            "Brickwall Barry": [65,15,10,10],
            "Slippery Sal":    [45,25,15,15],
            "The Mauler":      [55,10,20,15],
            "Viper Vanessa":   [25,15,50,10],
            "Fat Tony":        [40,5,45,10],
        }
        roll_state={"active":False,"x":0.0,"dx":0.0,"bounces":0,"owner":""}

        def draw_stick(c2,x,floor_y,gy,anim,skin,pants,belt,flip=False):
            y=floor_y-4-int(gy)
            bob=int(2*math.sin(state["frame"]*0.14)) if anim=="idle" else 0; y2=y+bob
            c2.create_oval(x-26,y2+2,x+26,y2+10,fill="#111",outline="")
            sk=skin; gi=belt; pb=pants
            if anim=="hurt": sk="#ff9999"
            if anim in("attack","special"):
                c2.create_line(x-8,y2-8,x-10,y2+22,fill=pb,width=9)
                c2.create_line(x+8,y2-8,x+14,y2+22,fill=pb,width=9)
                arm_x=x+(-54 if flip else 54)
                c2.create_line(x+(16 if flip else -16),y2-36,arm_x,y2-38,fill=gi,width=8)
                c2.create_oval(arm_x+(-8 if flip else -8),y2-46,arm_x+(8 if flip else 8),y2-30,fill=sk,outline="#333",width=2)
            elif anim=="hurt":
                lsw=12
                c2.create_line(x-8,y2-8,x-8-lsw,y2+20,fill=pb,width=9)
                c2.create_line(x+8,y2-8,x+8+lsw,y2+20,fill=pb,width=9)
            elif anim=="jump" or gy>0:
                c2.create_line(x-8,y2-8,x-14,y2+18,fill=pb,width=9)
                c2.create_line(x+8,y2-8,x+14,y2+18,fill=pb,width=9)
            else:
                lsw=int(4*math.sin(state["frame"]*0.14)) if anim=="idle" else 0
                c2.create_line(x-8,y2-8,x-8+lsw,y2+24,fill=pb,width=9)
                c2.create_line(x+8,y2-8,x+8-lsw,y2+24,fill=pb,width=9)
            c2.create_oval(x-18,y2-44,x+18,y2-8,fill=gi,outline="#333",width=2)
            c2.create_rectangle(x-18,y2-16,x+18,y2-10,fill="#ffcc00",outline="#8B6914",width=1)
            if anim not in("attack","special","hurt"):
                asw=int(5*math.sin(state["frame"]*0.14)) if anim=="idle" else 0
                c2.create_line(x+(16 if flip else -16),y2-38,x+(28 if flip else -28),y2-14+asw,fill=gi,width=6)
                c2.create_line(x+(-16 if flip else 16),y2-38,x+(-28 if flip else 28),y2-14-asw,fill=gi,width=6)
            c2.create_oval(x-14,y2-68,x+14,y2-44,fill=sk,outline="#333",width=2)
            c2.create_rectangle(x-16,y2-70,x+16,y2-62,fill=belt,outline="#333",width=1)
            c2.create_oval(x-7,y2-63,x-3,y2-58,fill="#cc0000")
            c2.create_oval(x+3,y2-63,x+7,y2-58,fill="#cc0000")

        def draw_bet_scene():
            c.delete("all")
            # Arena BG
            c.create_rectangle(0,0,W,H,fill="#0d0000")
            for cx3 in range(0,W,24):
                ch=random.Random(cx3*7).randint(25,65)
                cc=random.Random(cx3*11).choice(["#1a0000","#0d0010","#001a00"])
                c.create_oval(cx3-9,380-ch,cx3+9,380,fill=cc,outline="")
                c.create_oval(cx3-7,372-ch,cx3+7,372-ch+18,fill="#2a1100",outline="")
            c.create_rectangle(0,FLOOR_Y-8,W,H,fill="#1a0800")
            for lx in range(0,W,55): c.create_line(lx,FLOOR_Y-8,lx,H,fill="#2a1000",width=1)
            c.create_line(0,FLOOR_Y-8,W,FLOOR_Y-8,fill="#5a3010",width=3)
            # Banner
            round_rect(c,W//2-240,6,W//2+240,54,r=8,fill="#0a0000",outline=GOLD,width=2)
            c.create_text(W//2,20,text="⚔  BET ON THE BRAWL  ⚔",fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=14,weight="bold"))
            c.create_text(W//2,42,text=f"Balance: ${self.money:,}",fill=CREAM,font=self.fnt_small)
            # Health bars
            bw=280; bh=20; by=62
            c.create_rectangle(20,by,20+bw,by+bh,fill="#1a0000",outline=RED_C,width=2)
            c.create_rectangle(20,by,20+int(bw*max(0,state["f1_hp"])/100),by+bh,fill=RED_C,outline="")
            c.create_text(20+bw//2,by+10,text=f"{f1_name}  {max(0,state['f1_hp'])}/100",fill="white",font=self.fnt_small)
            c.create_rectangle(W-20-bw,by,W-20,by+bh,fill="#1a0000",outline="#4488ff",width=2)
            c.create_rectangle(W-20-int(bw*max(0,state["f2_hp"])/100),by,W-20,by+bh,fill="#4488ff",outline="")
            c.create_text(W-20-bw//2,by+10,text=f"{f2_name}  {max(0,state['f2_hp'])}/100",fill="white",font=self.fnt_small)
            # VS label while betting
            if state["phase"]=="betting":
                c.create_text(W//2,200,text="VS",fill=GOLD,font=tkfont.Font(family="Georgia",size=40,weight="bold"))
                c.create_text(state["f1_x"],230,text=f1_name,fill=RED_C,font=self.fnt_body)
                c.create_text(state["f2_x"],230,text=f2_name,fill="#4488ff",font=self.fnt_body)
            # Fireballs / snake shots
            for fb in state["fireballs"]:
                if not fb["active"]: continue
                fx=fb["x"]; fy=FLOOR_Y-4-int(fb.get("gy",0))-38
                is_snake=fb.get("owner")=="f2" and "Vanessa" in f2_name or fb.get("owner")=="f1" and "Vanessa" in f1_name
                if is_snake:
                    for si2 in range(5):
                        ox=si2*12*(1 if fb["dx"]>0 else -1)
                        sy2=fy+int(5*math.sin(si2*0.9+state["frame"]*0.3))
                        c.create_oval(fx+ox-6,sy2-4,fx+ox+6,sy2+4,fill="#00cc44",outline="#004400",width=1)
                    c.create_oval(fx-8,fy-6,fx+8,fy+6,fill="#00ee55",outline="#004400",width=2)
                else:
                    for fi in range(5):
                        ox=fi*12*(1 if fb["dx"]>0 else -1)
                        fc=["#ff4400","#ff8800","#ffcc00","#ff2200","#ffee44"][fi]
                        c.create_oval(fx+ox-8,fy-8,fx+ox+8,fy+8,fill=fc,outline="")
            # Fat Tony roll ball
            if roll_state["active"]:
                rx=int(roll_state["x"]); ry=FLOOR_Y-30
                ang=state["frame"]*18
                c.create_oval(rx-26,ry-26,rx+26,ry+26,fill="#b08060",outline="#8B6914",width=3)
                c.create_arc(rx-26,ry-26,rx+26,ry+26,start=ang,extent=180,fill="#9a7050",outline="")
                c.create_text(rx,ry,text="💥",font=tkfont.Font(size=14))
            # Fighters
            draw_stick(c,state["f1_x"],FLOOR_Y,state["f1_y"],state["f1_anim"],*f1c,flip=False)
            draw_stick(c,state["f2_x"],FLOOR_Y,state["f2_y"],state["f2_anim"],*f2c,flip=True)
            # Message
            if state["msg"] and state["msg_t"]>0:
                tw=max(200,len(state["msg"])*9)
                round_rect(c,W//2-tw//2-10,H-68,W//2+tw//2+10,H-36,r=7,fill="#0a0000",outline=state["msg_col"],width=2)
                c.create_text(W//2,H-52,text=state["msg"],fill=state["msg_col"],
                              font=tkfont.Font(family="Georgia",size=12,weight="bold"))
            # Bet indicator
            if state["bet_on"]:
                bet_col=RED_C if state["bet_on"]==f1_name else "#4488ff"
                c.create_text(W//2,H-20,text=f"Your bet: {state['bet_on']}  ${state['bet_amount']:,}",
                              fill=bet_col,font=tkfont.Font(family="Courier New",size=10,weight="bold"))
            state["frame"]+=1

        FIGHT_RUNNING=[False]

        def start_fight_sim(bet_amount):
            state["phase"]="fighting"; state["bet_amount"]=bet_amount
            FIGHT_RUNNING[0]=True
            # Properly destroy ALL overlay widgets (bet buttons etc.) without cancelling after-queue
            for w in list(self._overlay_widgets):
                try: w.destroy()
                except: pass
            self._overlay_widgets.clear()
            self._hide_hotbar()
            # First tick after stack unwinds
            aid=self.after(120,fight_tick); self._pending_after.append(aid)

        def fight_tick():
            if not FIGHT_RUNNING[0]: return
            state["msg_t"]=max(0,state["msg_t"]-1)
            state["f1_anim_t"]=max(0,state["f1_anim_t"]-1)
            state["f2_anim_t"]=max(0,state["f2_anim_t"]-1)
            if state["f1_anim_t"]==0 and state["f1_anim"]!="idle": state["f1_anim"]="idle"
            if state["f2_anim_t"]==0 and state["f2_anim"]!="idle": state["f2_anim"]="idle"
            # Gravity
            for yk,vk in [("f1_y","f1_vy"),("f2_y","f2_vy")]:
                if state[yk]>0 or state[vk]!=0:
                    state[vk]+=GRAV
                    state[yk]=max(0,state[yk]-state[vk])
                    if state[yk]<=0: state[yk]=0; state[vk]=0
            # Move fighters toward each other
            if abs(state["f2_x"]-state["f1_x"])>160:
                state["f1_x"]+=2; state["f2_x"]-=2
            # Fat Tony roll
            if roll_state["active"]:
                roll_state["x"]+=roll_state["dx"]
                if roll_state["x"]<=50: roll_state["x"]=50; roll_state["dx"]=abs(roll_state["dx"]); roll_state["bounces"]+=1
                if roll_state["x"]>=W-50: roll_state["x"]=W-50; roll_state["dx"]=-abs(roll_state["dx"]); roll_state["bounces"]+=1
                # Update the rolling fighter's position
                if roll_state["owner"]=="f1": state["f1_x"]=int(roll_state["x"])
                else: state["f2_x"]=int(roll_state["x"])
                # Hit other fighter
                target="f2_hp" if roll_state["owner"]=="f1" else "f1_hp"
                target_x="f2_x" if roll_state["owner"]=="f1" else "f1_x"
                target_name=f2_name if roll_state["owner"]=="f1" else f1_name
                roller_name=f1_name if roll_state["owner"]=="f1" else f2_name
                if abs(roll_state["x"]-state[target_x])<50:
                    dmg=random.randint(18,30)
                    state[target]=max(0,state[target]-dmg)
                    state["msg"]=f"🔵 {roller_name} CANNONBALL! -{dmg}"; state["msg_col"]="#4488ff"; state["msg_t"]=14
                if roll_state["bounces"]>=4:
                    roll_state["active"]=False
                    if roll_state["owner"]=="f1": state["f1_anim"]="idle"
                    else: state["f2_anim"]="idle"
            # Projectiles
            for fb in state["fireballs"]:
                if not fb["active"]: continue
                fb["x"]+=fb["dx"]
                if abs(fb["x"]-state["f2_x"])<44 and fb["owner"]=="f1":
                    fb["active"]=False
                    dmg=fb["dmg"]; state["f2_hp"]=max(0,state["f2_hp"]-dmg)
                    state["f2_anim"]="hurt"; state["f2_anim_t"]=7
                    state["msg"]=f"🔥 {f1_name} HIT! -{dmg}"; state["msg_col"]="#ff8800"; state["msg_t"]=14
                elif abs(fb["x"]-state["f1_x"])<44 and fb["owner"]=="f2":
                    fb["active"]=False
                    dmg=fb["dmg"]; state["f1_hp"]=max(0,state["f1_hp"]-dmg)
                    state["f1_anim"]="hurt"; state["f1_anim_t"]=7
                    state["msg"]=f"🔥 {f2_name} HIT! -{dmg}"; state["msg_col"]="#ff8800"; state["msg_t"]=14
                elif fb["x"]>W+50 or fb["x"]<-50: fb["active"]=False
            state["fireballs"]=[fb for fb in state["fireballs"] if fb["active"]]
            # AI combat tick
            state["tick_t"]+=1
            cooldown=max(5,16-state["frame"]//70)
            if state["tick_t"]>=cooldown and not roll_state["active"]:
                state["tick_t"]=0
                f1_wins_exchange=f1_str/(f1_str+f2_str)
                if random.random()<f1_wins_exchange:
                    attacker,defender="f1","f2"; an,dn=f1_name,f2_name; dhp="f2_hp"
                else:
                    attacker,defender="f2","f1"; an,dn=f2_name,f1_name; dhp="f1_hp"
                weights=FIGHTER_WEIGHTS.get(an,[50,20,15,15])
                action=random.choices(["punch","jump_punch","special","dodge"],weights=weights)[0]
                base_dmg=random.randint(8,22)
                if action=="punch":
                    state[attacker+"_anim"]="attack"; state[attacker+"_anim_t"]=8
                    if random.random()<0.22:
                        state[defender+"_vy"]=JVEL
                        state["msg"]=f"{dn} JUMPED over {an}!"; state["msg_col"]="#aaccff"; state["msg_t"]=12
                    elif random.random()<0.30:
                        base_dmg=max(1,base_dmg//4)
                        state[defender+"_anim"]="hurt"; state[defender+"_anim_t"]=5
                        state[dhp]=max(0,state[dhp]-base_dmg)
                        state["msg"]=f"🛡 {dn} BLOCKED! {base_dmg} chip"; state["msg_col"]="#aaccff"; state["msg_t"]=13
                    else:
                        state[defender+"_anim"]="hurt"; state[defender+"_anim_t"]=8
                        state[dhp]=max(0,state[dhp]-base_dmg)
                        hit=random.choice(["CRACK","THWACK","SMASH","BOOM","POW"])
                        state["msg"]=f"{an}: {hit}! -{base_dmg}"; state["msg_col"]=RED_C; state["msg_t"]=14
                elif action=="jump_punch":
                    state[attacker+"_vy"]=JVEL
                    state[attacker+"_anim"]="jump"; state[attacker+"_anim_t"]=10
                    state[defender+"_anim"]="hurt"; state[defender+"_anim_t"]=8
                    base_dmg+=8
                    state[dhp]=max(0,state[dhp]-base_dmg)
                    state["msg"]=f"✈ {an} FLYING PUNCH! -{base_dmg}"; state["msg_col"]="#ff8800"; state["msg_t"]=15
                elif action=="special":
                    state[attacker+"_anim"]="special"; state[attacker+"_anim_t"]=12
                    base_dmg=random.randint(16,34)
                    # Fat Tony: always roll
                    if an==f1_name and "Tony" in an or an==f2_name and "Tony" in an:
                        roll_state["active"]=True; roll_state["x"]=float(state[attacker+"_x"])
                        roll_state["dx"]=-9.0 if state[attacker+"_x"]>state[defender+"_x"] else 9.0
                        roll_state["bounces"]=0; roll_state["owner"]=attacker
                        state["msg"]=f"🔵 {an} CANNONBALL ROLL!"; state["msg_col"]="#4488ff"; state["msg_t"]=16
                    # Viper: always projectile
                    elif an==f1_name and "Viper" in an or an==f2_name and "Viper" in an or \
                         an==f1_name and "Vanessa" in an or an==f2_name and "Vanessa" in an:
                        direction=1 if state[attacker+"_x"]<state[defender+"_x"] else -1
                        state["fireballs"].append({"x":state[attacker+"_x"]+direction*44,
                                                   "dx":direction*18,"dmg":base_dmg,
                                                   "active":True,"owner":attacker})
                        state["msg"]=f"🐍 {an} SNAKE SHOT!"; state["msg_col"]="#00cc44"; state["msg_t"]=14
                    else:
                        # Other fighters: 60% projectile, 40% direct
                        if random.random()<0.60:
                            direction=1 if state[attacker+"_x"]<state[defender+"_x"] else -1
                            state["fireballs"].append({"x":state[attacker+"_x"]+direction*44,
                                                       "dx":direction*16,"dmg":base_dmg,
                                                       "active":True,"owner":attacker})
                            state["msg"]=f"🔥 {an} FIRE BLAST!"; state["msg_col"]="#ff8800"; state["msg_t"]=14
                        else:
                            state[defender+"_anim"]="hurt"; state[defender+"_anim_t"]=10
                            state[dhp]=max(0,state[dhp]-base_dmg)
                            state["msg"]=f"★ {an} SPECIAL -{base_dmg}!"; state["msg_col"]="#ffcc00"; state["msg_t"]=16
                elif action=="dodge":
                    state[attacker+"_vy"]=JVEL
                    state["msg"]=f"{an} jumps back!"; state["msg_col"]="#888"; state["msg_t"]=8

            # Check win
            if state["f1_hp"]<=0 or state["f2_hp"]<=0:
                FIGHT_RUNNING[0]=False
                winner=f2_name if state["f1_hp"]<=0 else f1_name
                draw_bet_scene()
                bet=state["bet_amount"]
                if state["bet_on"]==winner:
                    gain=bet*2; self.money+=gain; self._refresh_balance_text()
                    result_msg=f"✓ {winner} won!  You win ${gain:,}!"; result_col=GREEN_C
                    self._post_game(bet,"win")
                else:
                    self.money-=bet; self._refresh_balance_text()
                    result_msg=f"✗ {winner} won — you lost ${bet:,}."; result_col=RED_C
                    self._post_game(bet,"loss")
                round_rect(c,W//2-260,H//2-50,W//2+260,H//2+140,r=16,fill="#0a0000",outline=GOLD,width=3)
                c.create_text(W//2,H//2-15,text=f"🏆  {winner} WINS!",fill=GOLD,
                              font=tkfont.Font(family="Georgia",size=28,weight="bold"),anchor="center")
                c.create_text(W//2,H//2+35,text=result_msg,fill=result_col,
                              font=tkfont.Font(family="Georgia",size=14,weight="bold"),anchor="center")
                self._make_btn(W//2-80,H//2+100,"Bet Again",self._arena_bet_screen,col=GOLD,fg=DARK,w=130)
                self._make_btn(W//2+80,H//2+100,"Back",self._back_to_interior,col="#333",fg=CREAM,w=100)
                return
            draw_bet_scene()
            aid=self.after(55,fight_tick); self._pending_after.append(aid)

        # --- Betting UI ---
        draw_bet_scene()
        chosen=[None]
        def pick(name):
            chosen[0]=name
            # Only update the pick label — do NOT call draw_bet_scene() as that
            # deletes all canvas items including the hotbar chip button windows
            c.delete("pick_lbl")
            bc=RED_C if name==f1_name else "#4488ff"
            round_rect(c,W//2-120,H-HOTBAR_H-38,W//2+120,H-HOTBAR_H-10,r=8,
                       fill="#0a0000",outline=bc,width=2,tags="pick_lbl")
            c.create_text(W//2,H-HOTBAR_H-24,text=f"► Picked: {name}",fill=bc,
                          font=tkfont.Font(family="Courier New",size=11,weight="bold"),
                          anchor="center",tags="pick_lbl")
        self._make_btn(state["f1_x"],290,f"Bet on {f1_name}",lambda:pick(f1_name),col="#5a0000",fg="white",w=180)
        self._make_btn(state["f2_x"],290,f"Bet on {f2_name}",lambda:pick(f2_name),col="#00004a",fg="white",w=180)
        def on_deal(bet):
            if not chosen[0]:
                self._msg("Pick a fighter first!",RED_C); self._show_hotbar(on_deal); return
            state["bet_on"]=chosen[0]
            start_fight_sim(bet)
        self._show_hotbar(on_deal)

    # ── ARENA RESTAURANT (NEW) ────────────────────────────
    def _arena_restaurant_screen(self):
        self._clear_overlay(); c=self.canvas
        # Draw the restaurant room directly (not the grey game bg)
        c.delete("all")
        # Floor
        for row in range(18):
            for col2 in range(20):
                x1=col2*58-10; y1=65+row*34
                c.create_rectangle(x1,y1,x1+57,y1+33,
                                   fill="#c8a060" if (row+col2)%2==0 else "#b89050",outline="#9a7038",width=1)
        # Burgundy wall band
        c.create_rectangle(0,0,W,82,fill="#4a0a10",outline="")
        for wx2 in range(0,W,130):
            c.create_rectangle(wx2+6,4,wx2+122,78,fill="",outline="#7a2030",width=2)
        c.create_rectangle(0,80,W,92,fill="#8B6020",outline="#5a3800",width=1)
        c.create_line(0,80,W,80,fill="#c8a040",width=2)
        # Restaurant title sign
        round_rect(c,W//2-240,6,W//2+240,68,r=10,fill="#1a0a04",outline="#d4a820",width=3)
        c.create_text(W//2,22,text="✦  ROUGHHOUSE RESTAURANT  ✦",fill="#d4a820",
                      font=tkfont.Font(family="Georgia",size=14,weight="bold"))
        c.create_text(W//2,48,text=f"HP: {self.player_health}/100   Balance: ${self.money:,}",
                      fill=CREAM,font=self.fnt_small,tags="rest_lbl")
        def refresh():
            c.delete("rest_lbl")
            c.create_text(W//2,48,text=f"HP: {self.player_health}/100   Balance: ${self.money:,}",
                          fill=CREAM,font=self.fnt_small,tags="rest_lbl")
        # Dish data: name, cost, hp, desc, emoji, plate_col, food_col
        DISHES=[
            ("Boiled Egg",      50,  15,"Restores a little HP.",         "🥚","#fffaee","#f5e870"),
            ("BLT Sandwich",   150,  35,"Classic BLT — hearty & filling.","🥪","#f0d8a0","#8B4010"),
            ("Caesar Salad",   200,  45,"Fresh and crisp.",              "🥗","#e8f5e0","#3a8020"),
            ("Full English",   400,  70,"The full works. Massive HP.",   "🍳","#f5e8d0","#c04010"),
            ("Bluefin Ravioli",900, 100,"Chef's finest. Full HP!",       "🍝","#faecd0","#c82010"),
        ]
        # Draw 5 menu cards in two rows (3 top, 2 bottom)
        positions=[(180,200),(W//2,200),(W-180,200),(W//2-180,430),(W//2+180,430)]
        card_w,card_h=240,200
        for idx,(name,cost,hp_gain,desc,emoji,plate_c,food_c) in enumerate(DISHES):
            cx6,cy6=positions[idx]
            can_afford=self.money>=cost
            border_col=GOLD if can_afford else "#3a3a3a"
            fill_col="#1c0e04" if can_afford else "#111"
            # Card shadow
            c.create_rectangle(cx6-card_w//2+4,cy6-card_h//2+4,cx6+card_w//2+4,cy6+card_h//2+4,
                               fill="#080402",outline="")
            # Card body
            round_rect(c,cx6-card_w//2,cy6-card_h//2,cx6+card_w//2,cy6+card_h//2,
                       r=14,fill=fill_col,outline=border_col,width=2)
            # Plate illustration at top of card
            py6=cy6-card_h//2+46
            c.create_oval(cx6-36,py6-22,cx6+36,py6+22,fill="#f8f4ee",outline="#d0c8b0",width=3)
            c.create_oval(cx6-29,py6-17,cx6+29,py6+17,fill="#f0ece4",outline="#c8c0a8",width=1)
            c.create_oval(cx6-20,py6-11,cx6+20,py6+11,fill=plate_c,outline=food_c,width=2)
            # Emoji food icon
            c.create_text(cx6,py6,text=emoji,font=tkfont.Font(size=18),anchor="center")
            # Dish name
            c.create_text(cx6,cy6-card_h//2+80,text=name,fill=GOLD if can_afford else "#666",
                          font=tkfont.Font(family="Georgia",size=12,weight="bold"),anchor="center")
            # HP badge
            hp_col=GREEN_C if can_afford else "#335533"
            c.create_rectangle(cx6-30,cy6-card_h//2+92,cx6+30,cy6-card_h//2+110,
                               fill="#0a2008",outline=hp_col,width=1)
            c.create_text(cx6,cy6-card_h//2+101,text=f"+{hp_gain} HP",fill=hp_col,
                          font=tkfont.Font(family="Courier New",size=9,weight="bold"),anchor="center")
            # Description
            c.create_text(cx6,cy6-card_h//2+128,text=desc,fill="#888" if not can_afford else "#aaa",
                          font=tkfont.Font(family="Courier New",size=8),anchor="center",width=card_w-24)
            # Price + buy button
            btn_y=cy6+card_h//2-30
            btn_col=GOLD if can_afford else "#2a2a2a"
            btn_fg=DARK if can_afford else "#444"
            def mk(n=name,cc=cost,hg=hp_gain):
                def buy():
                    if self.money<cc: self._msg(f"Can't afford {n}.",RED_C,y=H-55); return
                    self.money-=cc; self.player_health=min(100,self.player_health+hg)
                    self._msg(f"Enjoyed {n}! +{hg} HP  ❤  HP: {self.player_health}/100",GREEN_C,y=H-55)
                    self._refresh_balance_text(); refresh()
                    # Redraw screen to update card affordability colours
                    self.after(200,self._arena_restaurant_screen)
                return buy
            self._make_btn(cx6,btn_y,f"${cost:,}",mk(),col=btn_col,fg=btn_fg,w=90)
        # Back button
        self._make_btn(W//2,H-30,"← Back to Arena",self._back_to_interior,col="#1a0a04",fg=GOLD,w=160)

    # ══════════════════════════════════════════════════════
    # FIGURINE SYSTEM
    # ══════════════════════════════════════════════════════
    FIGURINES=[
        # id, name, rarity, colour, description
        # ── COMMON (20) ──────────────────────────────────
        ("f_coin",      "Lucky Coin",        "common",   "#f5c518","A shiny gold coin on a tiny stand."),
        ("f_dice",      "Classic Dice",      "common",   "#eeeeee","A tiny ivory die, mid-roll."),
        ("f_card",      "Ace of Spades",     "common",   "#222222","A miniature playing card."),
        ("f_horseshoe", "Horseshoe",         "common",   "#888888","Good luck horseshoe."),
        ("f_mug",       "Beer Mug",          "common",   "#d4a030","Frothy mug, barely an inch tall."),
        ("f_cactus",    "Desert Cactus",     "common",   "#3a8a28","A stubby little cactus."),
        ("f_cat",       "Alley Cat",         "common",   "#886644","A sleepy cat curled up."),
        ("f_parrot",    "Casino Parrot",     "common",   "#22aa44","Squawks at jackpots."),
        ("f_boot",      "Old Boot",          "common",   "#7a5530","Crusty travelling boot."),
        ("f_star",      "Shooting Star",     "common",   "#ffffaa","A tiny glowing star."),
        ("f_mushroom",  "Red Mushroom",      "common",   "#cc3322","White-spotted cap."),
        ("f_snake_sm",  "Garden Snake",      "common",   "#448822","Coiled green snake."),
        ("f_frog",      "Lucky Frog",        "common",   "#44aa44","Sits on a coin."),
        ("f_candle",    "Wax Candle",        "common",   "#ffeeaa","Half-melted wax candle."),
        ("f_anchor",    "Sailor's Anchor",   "common",   "#445566","Old iron anchor."),
        ("f_lantern",   "Paper Lantern",     "common",   "#ff8844","Glowing red lantern."),
        ("f_clover",    "Four-Leaf Clover",  "common",   "#33aa33","Four perfect leaves."),
        ("f_barrel",    "Whisky Barrel",     "common",   "#8B4513","Tiny oak barrel."),
        ("f_spade",     "Tiny Spade",        "common",   "#555555","A miniature shovel."),
        ("f_gem_sm",    "Raw Gemstone",      "common",   "#66aaff","Uncut blue gem."),
        # ── UNCOMMON (15) ────────────────────────────────
        ("f_horse_tb",  "Thunderhoof",       "uncommon", "#cc4444","Red racing horse, mid-gallop."),
        ("f_horse_nm",  "Nightmare",         "uncommon", "#3377cc","Blue horse, eyes glowing."),
        ("f_horse_ls",  "Lucky Star",        "uncommon", "#e8a020","Golden mare."),
        ("f_horse_im",  "Ironmane",          "uncommon", "#33aa55","Green horse, iron shoes."),
        ("f_horse_sb",  "Shadowbolt",        "uncommon", "#9944bb","Purple horse, crackling mane."),
        ("f_casino_sm", "Mini Casino",       "uncommon", "#8B0000","Tiny casino building."),
        ("f_stable_sm", "Mini Stables",      "uncommon", "#7d5a3c","Tiny stables with hay bale."),
        ("f_bank_sm",   "Mini Bank",         "uncommon", "#1a3a5c","Tiny bank with vault door."),
        ("f_shop_sm",   "Mini Boutique",     "uncommon", "#e8e0d0","Tiny clothes shop."),
        ("f_snake_co",  "Cobra",             "uncommon", "#ccaa22","Rearing cobra with hood spread."),
        ("f_snake_py",  "Python",            "uncommon", "#448844","Long python coiled on a branch."),
        ("f_wolf",      "Lone Wolf",         "uncommon", "#aaaaaa","Howling silver wolf."),
        ("f_owl",       "Wise Owl",          "uncommon", "#aa8844","Perched owl with spectacles."),
        ("f_crystal",   "Crystal Ball",      "uncommon", "#aaccff","Swirling mist inside."),
        ("f_jester",    "Jester",            "uncommon", "#cc4488","Bells on cap, mid-somersault."),
        # ── RARE (10) ────────────────────────────────────
        ("f_ff_razr",   "Razor Ray",         "rare",     "#cc2222","Funky Feet fighter, fire stance."),
        ("f_ff_slck",   "Slick Sam",         "rare",     "#2255cc","Funky Feet fighter, ice pose."),
        ("f_ff_blze",   "Blaze Betty",       "rare",     "#cc6600","Funky Feet fighter, flame kick."),
        ("f_ff_iron",   "Iron Ivan",         "rare",     "#228833","Funky Feet fighter, rock fist."),
        ("f_arena_sm",  "Mini Arena",        "rare",     "#2a0000","Tiny arena with crowd."),
        ("f_hotel_sm",  "Mini Grand Hotel",  "rare",     "#c8b89a","Tiny hotel, 3 floors."),
        ("f_den_sm",    "Mini Den",          "rare",     "#0a0a1a","Tiny den, purple neon."),
        ("f_vip_sm",    "Mini VIP Lounge",   "rare",     "#4a2060","Tiny VIP lounge."),
        ("f_dragon",    "Cave Dragon",       "rare",     "#aa2200","Baby dragon with flame."),
        ("f_mermaid",   "Sea Mermaid",       "rare",     "#22aacc","Sitting on a rock."),
        # ── EPIC (5) ─────────────────────────────────────
        ("f_snake_ki",  "King Cobra",        "epic",     "#ddaa00","Golden king cobra, jewelled crown."),
        ("f_ff_champ",  "Champion Trophy",   "epic",     "#f5c518","Golden Funky Feet trophy."),
        ("f_phoenix",   "Phoenix",           "epic",     "#ff6600","Blazing phoenix mid-flight."),
        ("f_kraken",    "Kraken",            "epic",     "#224488","Tentacles reaching from water."),
        ("f_golem",     "Stone Golem",       "epic",     "#887766","Ancient golem, mossy."),
        # ── LEGENDARY (10) ───────────────────────────────
        ("f_horse_gold","Golden Horse",      "legendary","#f5c518","All-gold racing champion."),
        ("f_ff_legend", "Legendary Fighter", "legendary","#ff4400","Engulfed in fire and ice."),
        ("f_casino_big","Grand Casino",      "legendary","#cc0000","Full casino replica, lit up."),
        ("f_serpent",   "Sea Serpent",       "legendary","#006644","Enormous coiled sea serpent."),
        ("f_colossus",  "The Colossus",      "legendary","#888888","Giant iron warrior."),
        ("f_unicorn",   "Enchanted Unicorn", "legendary","#ff88ff","Horn glows rainbow."),
        ("f_sphinx",    "Desert Sphinx",     "legendary","#cc9944","Ancient sphinx, eyes glow."),
        ("f_leviathan", "Leviathan",         "legendary","#002244","Colossal ocean beast."),
        ("f_valkyrie",  "Valkyrie",          "legendary","#aaaaff","Winged warrior descending."),
        ("f_titan",     "Stone Titan",       "legendary","#666655","Mountain-sized titan, crouching."),
        # ── MYTHIC (5) ───────────────────────────────────
        ("f_myth_rg",   "RG Deity",          "mythic",   "#ffffff","The god of the casino. Glows."),
        ("f_myth_time", "Timekeeper",        "mythic",   "#ffffcc","Holds all time in one hand."),
        ("f_myth_void", "Void Serpent",      "mythic",   "#110022","Serpent eating its own tail."),
        ("f_myth_sun",  "Solar Dragon",      "mythic",   "#ffcc00","Dragon made of pure sunlight."),
        ("f_myth_chs",  "Chaos God",         "mythic",   "#ff00ff","All rarities swirl within."),
    ]
    FIGURINE_BY_ID={f[0]:f for f in FIGURINES}
    RARITY_COLS={"common":"#aaaaaa","uncommon":"#44cc44","rare":"#4488ff",
                 "epic":"#aa44ff","legendary":"#ffaa00","mythic":"#ff44ff"}
    RARITY_WEIGHTS={"common":55,"uncommon":25,"rare":12,"epic":5,"legendary":2,"mythic":1}
    # pool by rarity
    FIGURINE_POOL={}
    for _f in FIGURINES:
        FIGURINE_POOL.setdefault(_f[2],[]).append(_f[0])

    GUMBALL_COST=500  # flat cost per roll — any rarity possible

    def _roll_figurine(self,rarity=None):
        """Roll a random figurine, optionally forcing rarity."""
        if rarity is None:
            pool=list(self.RARITY_WEIGHTS.keys())
            weights=[self.RARITY_WEIGHTS[r] for r in pool]
            total=sum(weights); roll=random.randint(1,total); cum=0
            for r,w in zip(pool,weights):
                cum+=w
                if roll<=cum: rarity=r; break
        choices=self.FIGURINE_POOL.get(rarity,[])
        if not choices: return None
        return random.choice(choices)

    def _draw_figurine(self,c,fid,x,y,size=28):
        """Draw a small figurine sprite at (x,y) centre, scaled to size."""
        if fid not in self.FIGURINE_BY_ID: return
        _,name,rarity,col,_ = self.FIGURINE_BY_ID[fid]
        rc=self.RARITY_COLS[rarity]
        s=size//2
        # Base glow
        c.create_oval(x-s-2,y-s-2,x+s+2,y+s+2,fill="",outline=rc,width=2)
        # Body shape varies by rarity
        if "horse" in fid:
            # Horse body
            c.create_oval(x-s+4,y-s+6,x+s-2,y+4,fill=col,outline="#333",width=1)
            c.create_oval(x-s+2,y-s-2,x-s+12,y-s+10,fill=col,outline="#333",width=1)
            for li,lx in enumerate([x-s+6,x-s+10,x+s-12,x+s-8]):
                c.create_line(lx,y+4,lx+(1 if li%2 else -1),y+s,fill=col,width=3)
            c.create_line(x+s-4,y-s+8,x+s+4,y-s-2,fill=col,width=3)
        elif "snake" in fid or "serpent" in fid or "leviathan" in fid:
            # Coiled snake
            for ri in range(3):
                r2=s-ri*4
                c.create_oval(x-r2,y-r2//2,x+r2,y+r2//2,fill="",outline=col,width=3-ri)
            c.create_oval(x-4,y-s+2,x+4,y-s+10,fill=col,outline="#333",width=1)
        elif "dragon" in fid or "phoenix" in fid:
            # Winged creature
            c.create_polygon(x,y-s,x-s,y+s//2,x,y,x+s,y+s//2,fill=col,outline="#333",width=1)
            c.create_line(x,y-s,x-s-4,y-4,fill=col,width=3)
            c.create_line(x,y-s,x+s+4,y-4,fill=col,width=3)
        elif "sm" in fid or "big" in fid:
            # Mini building — small box with roof
            c.create_rectangle(x-s+4,y-2,x+s-4,y+s-2,fill=col,outline="#333",width=1)
            c.create_polygon(x-s+2,y-2,x,y-s+2,x+s-2,y-2,fill=col,outline="#333",width=1)
        elif "trophy" in fid or "coin" in fid or "crystal" in fid or "star" in fid:
            # Round/orb shape
            c.create_oval(x-s+2,y-s+2,x+s-2,y+s-2,fill=col,outline=rc,width=2)
            c.create_text(x,y,text="★" if "trophy" in fid else "◉",fill="#fff",font=tkfont.Font(size=s//2))
        else:
            # Generic humanoid / creature
            c.create_oval(x-s//2,y-s,x+s//2,y-s//3,fill=col,outline="#333",width=1)  # head
            c.create_rectangle(x-s//2+2,y-s//3,x+s//2-2,y+s//3,fill=col,outline="#333",width=1)  # body
            c.create_line(x-s//2+2,y-s//4,x-s,y+s//6,fill=col,width=3)  # arm L
            c.create_line(x+s//2-2,y-s//4,x+s,y+s//6,fill=col,width=3)  # arm R
            c.create_line(x-4,y+s//3,x-6,y+s,fill=col,width=3)  # leg L
            c.create_line(x+4,y+s//3,x+6,y+s,fill=col,width=3)  # leg R
        # Rarity dot bottom
        c.create_oval(x-4,y+s-2,x+4,y+s+6,fill=rc,outline="",)

    def _figurine_table_screen(self,floor):
        """Show table management screen for hotel floor 2 (10 slots) or 3 (30 slots)."""
        self._clear_overlay(); c=self.canvas
        max_slots=10 if floor==2 else 30
        display_attr="figurine_display_f2" if floor==2 else "figurine_display_f3"
        placed=getattr(self,display_attr,[])
        col1="#0a1a10" if floor==2 else "#06100e"
        col2="#0d2214" if floor==2 else "#082018"
        self._draw_room_bg(f"FIGURINE TABLE — {'2ND' if floor==2 else '3RD'} FLOOR",col1,col2)
        c.create_text(W//2,76,text=f"{'🟩' if floor==2 else '🟦'} Figurine Display Table — {max_slots} slots",
                      fill=GOLD,font=tkfont.Font(family="Georgia",size=14,weight="bold"))
        c.create_text(W//2,100,text=f"Slots used: {len(placed)}/{max_slots}",fill=CREAM,
                      font=tkfont.Font(family="Courier New",size=9))

        # Draw the placed figurines grid
        cols=5 if floor==2 else 6
        slot_w=90; slot_h=80
        start_x=W//2-(cols*slot_w)//2+slot_w//2
        c.create_text(W//2,122,text="— Placed figurines — (click to remove)",
                      fill="#888899",font=tkfont.Font(family="Courier New",size=8))
        for i in range(max_slots):
            gx=start_x+(i%cols)*slot_w; gy=148+(i//cols)*slot_h
            bg="#0d1a10" if floor==2 else "#0a1410"
            c.create_rectangle(gx-38,gy-34,gx+38,gy+34,fill=bg,outline="#2a4030",width=1)
            if i<len(placed):
                fid=placed[i]
                self._draw_figurine(c,fid,gx,gy-4,size=26)
                fn=self.FIGURINE_BY_ID[fid][1] if fid in self.FIGURINE_BY_ID else fid
                c.create_text(gx,gy+24,text=fn[:10],fill="#aaccaa",
                              font=tkfont.Font(family="Courier New",size=6))
                def make_remove(idx):
                    def do():
                        placed.pop(idx); setattr(self,display_attr,placed)
                        self._figurine_table_screen(floor)
                    return do
                self._make_btn(gx,gy+38,"✕",make_remove(i),col="#2a0010",fg="#ff6666",w=28)
            else:
                c.create_text(gx,gy,text="—",fill="#334433",font=tkfont.Font(size=14))

        # Divider
        table_bottom=148+(((max_slots-1)//cols)+1)*slot_h+48
        c.create_line(60,table_bottom,W-60,table_bottom,fill="#2a4030",width=1)
        c.create_text(W//2,table_bottom+14,text="— Your collection (click to place) —",
                      fill="#888899",font=tkfont.Font(family="Courier New",size=8))

        # Collection scroll — show in a sub-grid below
        coll=getattr(self,"figurine_collection",[])
        already_placed_ids=set(placed)
        avail=[fid for fid in coll if fid not in already_placed_ids]
        coll_y=table_bottom+30
        ccols=8; csz=22; cgap=72
        cstart=W//2-(min(len(avail),ccols)*cgap)//2+cgap//2
        shown=0
        for fid in avail:
            if shown>=16: break  # max show 2 rows
            cx2=cstart+(shown%ccols)*cgap; cy2=coll_y+(shown//ccols)*60
            self._draw_figurine(c,fid,cx2,cy2-4,size=csz)
            fn2=self.FIGURINE_BY_ID[fid][1] if fid in self.FIGURINE_BY_ID else fid
            rc2=self.RARITY_COLS.get(self.FIGURINE_BY_ID[fid][2],"#aaa") if fid in self.FIGURINE_BY_ID else "#aaa"
            c.create_text(cx2,cy2+18,text=fn2[:9],fill=rc2,font=tkfont.Font(family="Courier New",size=6))
            def make_place(fid2=fid):
                def do():
                    if len(placed)>=max_slots:
                        self._msg("Table full!",RED_C); return
                    placed.append(fid2); setattr(self,display_attr,placed)
                    self._figurine_table_screen(floor)
                return do
            self._make_btn(cx2,cy2+30,"Place",make_place(),col="#0a2010",fg="#44ff88",w=52)
            shown+=1
        if not avail:
            c.create_text(W//2,coll_y+20,text="No figurines to place — visit the Gumball Emporium!",
                          fill="#556655",font=tkfont.Font(family="Courier New",size=9))

        self._make_btn(W//2,H-32,"← Back",self._back_to_interior,col="#1a1828",fg=CREAM,w=120)

    def _gumball_screen(self,_=None):
        """Gumball machine — roll for a random figurine of any rarity."""
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("GUMBALL MACHINE","#0a0018","#110020")
        cost=self.GUMBALL_COST

        c.create_text(W//2,76,text="✦  GUMBALL MACHINE  ✦",fill="#cc66ff",
                      font=tkfont.Font(family="Georgia",size=16,weight="bold"))
        c.create_text(W//2,100,text=f"${cost:,} per roll  ·  Any rarity possible!",fill=CREAM,
                      font=tkfont.Font(family="Courier New",size=9))

        # ════════════════════════════════════════════════════
        # LEFT: Rarity spin strip
        # ════════════════════════════════════════════════════
        spin_x=140; spin_y=330
        c.create_rectangle(spin_x-106,spin_y-130,spin_x+106,spin_y+130,
                           fill="#0a0018",outline="#550077",width=2)
        c.create_text(spin_x,spin_y-144,text="— RARITY ROLL —",fill="#887799",
                      font=tkfont.Font(family="Courier New",size=8,weight="bold"))
        # Highlight bar centre
        c.create_rectangle(spin_x-104,spin_y-20,spin_x+104,spin_y+20,
                           fill="#1a0030",outline="#883399",width=2)
        spin_label_ids=[]
        for row_ in range(7):
            sid=c.create_text(spin_x,spin_y-108+row_*36,text="",fill="#443355",
                              font=tkfont.Font(family="Courier New",size=10,weight="bold"))
            spin_label_ids.append(sid)

        # ════════════════════════════════════════════════════
        # CENTRE: Gumball machine + chute animation
        # ════════════════════════════════════════════════════
        gx=W//2; gy=300

        # Globe outer (drawn first, ref kept for colour update)
        globe_col_id=c.create_oval(gx-62,gy-80,gx+62,gy+50,fill="#440066",outline="#111",width=4)
        globe_inner_id=c.create_oval(gx-50,gy-68,gx+50,gy+38,fill="#550077",outline="#333",width=2)
        # Shine arc on globe
        c.create_arc(gx-44,gy-62,gx+4,gy-22,start=50,extent=80,outline="#9966aa",style="arc",width=3)
        # Static balls inside globe
        ball_cols_=["#cc2244","#2266cc","#22aa44","#cc8800","#aa22cc","#cc4400","#2299aa"]
        for bi_ in range(7):
            ba_=math.radians(bi_*51)
            bx_=gx+int(26*math.cos(ba_)); by_=gy-16+int(18*math.sin(ba_))
            c.create_oval(bx_-6,by_-6,bx_+6,by_+6,fill=ball_cols_[bi_],outline="#111",width=1)
            c.create_oval(bx_-2,by_-4,bx_+1,by_-1,fill="#ddccee",outline="")  # highlight
        # Neck funnel
        c.create_polygon(gx-10,gy+46,gx-18,gy+60,gx+18,gy+60,gx+10,gy+46,
                         fill="#1a1a1a",outline="#444",width=1)

        # ── Chute / tube: the ball rolls down here ──────────
        # Chute is a vertical tube from neck down into the dispenser cup
        chute_x=gx; chute_top=gy+60; chute_bot=gy+200
        c.create_rectangle(chute_x-9,chute_top,chute_x+9,chute_bot,
                           fill="#0d0018",outline="#553366",width=2)
        # Chute glass highlight (left edge lighter)
        c.create_line(chute_x-7,chute_top+4,chute_x-7,chute_bot-4,fill="#331a44",width=2)
        # Dispenser cup at bottom of chute
        c.create_rectangle(chute_x-20,chute_bot,chute_x+20,chute_bot+18,
                           fill="#222",outline="#555",width=2)
        c.create_arc(chute_x-20,chute_bot+10,chute_x+20,chute_bot+30,
                     start=180,extent=180,fill="#1a1a1a",outline="#555")
        # Arrow label
        c.create_text(chute_x+24,chute_top+70,text="← chute",fill="#443355",
                      font=tkfont.Font(family="Courier New",size=7))

        # Cabinet body below chute
        cab_top=chute_bot+18
        c.create_rectangle(gx-28,cab_top,gx+28,cab_top+80,fill="#2a2a2a",outline="#555",width=2)
        c.create_rectangle(gx-34,cab_top+72,gx+34,cab_top+92,fill="#222",outline="#555",width=2)
        # Coin slot
        c.create_rectangle(gx-14,cab_top+12,gx+14,cab_top+22,fill="#1a1a1a",outline="#777",width=1)
        c.create_rectangle(gx-6,cab_top+14,gx+6,cab_top+20,fill="#111",outline="#999",width=1)
        # Turn handle
        c.create_oval(gx+14,cab_top+32,gx+28,cab_top+46,fill="#888",outline="#aaa",width=1)
        c.create_line(gx+21,cab_top+39,gx+36,cab_top+32,fill="#aaa",width=3)
        c.create_oval(gx+33,cab_top+28,gx+39,cab_top+36,fill="#cc8800",outline=GOLD,width=1)
        # Rarity plaque
        c.create_rectangle(gx-26,cab_top+50,gx+26,cab_top+64,fill="#111",outline="#883399",width=1)
        c.create_text(gx,cab_top+57,text="GUMBALL",fill="#cc66ff",
                      font=tkfont.Font(family="Courier New",size=6,weight="bold"))

        # Animated ball in chute (starts hidden at globe neck, falls to cup)
        anim_ball_id=c.create_oval(chute_x-7,chute_top-16,chute_x+7,chute_top,
                                   fill="#440066",outline="",state="hidden")

        # ════════════════════════════════════════════════════
        # RIGHT: Odds board + result
        # ════════════════════════════════════════════════════
        c.create_rectangle(W-210,118,W-14,318,fill="#0a0018",outline="#550077",width=2)
        c.create_text(W-112,132,text="ODDS",fill="#cc66ff",
                      font=tkfont.Font(family="Courier New",size=8,weight="bold"))
        odds_text=[("Common","55%"),("Uncommon","25%"),("Rare","12%"),
                   ("Epic","5%"),("Legendary","2%"),("Mythic","1%")]
        for oi,(rname,pct) in enumerate(odds_text):
            ry=148+oi*28; rc_=self.RARITY_COLS[rname.lower()]
            c.create_oval(W-202,ry+3,W-190,ry+15,fill=rc_,outline="")
            c.create_text(W-184,ry+9,text=rname,fill=rc_,anchor="w",
                          font=tkfont.Font(family="Courier New",size=7))
            c.create_text(W-22,ry+9,text=pct,fill=CREAM,anchor="e",
                          font=tkfont.Font(family="Courier New",size=7,weight="bold"))

        result_id=c.create_text(W//2,570,text="",fill=GOLD,
                                font=tkfont.Font(family="Georgia",size=13,weight="bold"))
        desc_id=c.create_text(W//2,594,text="",fill=CREAM,
                              font=tkfont.Font(family="Courier New",size=8))

        fig_drawn=[False]; rolling=[False]
        rarity_seq=list(self.RARITY_WEIGHTS.keys())

        def _ball_fall(ball_y,target_y,ball_col,on_done):
            """Animate ball falling down the chute."""
            if ball_y>=target_y:
                # Ball arrived — flash cup
                c.itemconfig(anim_ball_id,state="hidden")
                on_done()
                return
            speed=max(4,int((target_y-ball_y)*0.18))
            new_y=min(ball_y+speed,target_y)
            c.coords(anim_ball_id,chute_x-7,new_y-14,chute_x+7,new_y)
            c.itemconfig(anim_ball_id,fill=ball_col,state="normal")
            self.after(30,lambda:_ball_fall(new_y,target_y,ball_col,on_done))

        def _spin_frame(tick,total,final_rar,fid):
            if not rolling[0]: return
            if tick<total-8: interval=40
            elif tick<total-4: interval=100
            else: interval=200
            if tick<total-2:
                centre_idx=tick % len(rarity_seq)
            else:
                centre_idx=rarity_seq.index(final_rar)
            for row_,sid in enumerate(spin_label_ids):
                idx=(centre_idx-3+row_) % len(rarity_seq)
                rar_=rarity_seq[idx]
                rc__=self.RARITY_COLS[rar_]
                display_col=rc__ if row_==3 else "#443355"
                c.itemconfig(sid,text=rar_.upper(),fill=display_col)
            pulse_col=self.RARITY_COLS[rarity_seq[centre_idx % len(rarity_seq)]]
            c.itemconfig(globe_col_id,fill=pulse_col)
            if tick>=total:
                # Spin done — now animate ball falling down chute
                rc_f=self.RARITY_COLS[final_rar]
                c.itemconfig(globe_col_id,fill=rc_f)
                c.itemconfig(globe_inner_id,fill=rc_f)
                def reveal():
                    rolling[0]=False
                    _,name,_,_,desc=self.FIGURINE_BY_ID[fid]
                    c.itemconfig(result_id,text=f"✨  {name}  [{final_rar.upper()}]",fill=rc_f)
                    c.itemconfig(desc_id,text=desc)
                    if not fig_drawn[0]:
                        fig_drawn[0]=True
                        self._draw_figurine(c,fid,W-112,420,size=34)
                _ball_fall(chute_top,chute_bot-2,rc_f,reveal)
                return
            self.after(interval,lambda:_spin_frame(tick+1,total,final_rar,fid))

        def roll():
            if rolling[0]: return
            if self.money<cost:
                self._msg(f"Need ${cost:,}!",RED_C); return
            self.money-=cost; self._refresh_balance_text()
            fid=self._roll_figurine()
            if not fid: return
            if not hasattr(self,"figurine_collection"): self.figurine_collection=[]
            self.figurine_collection.append(fid)
            _,_,final_rar,_,_=self.FIGURINE_BY_ID[fid]
            rolling[0]=True; fig_drawn[0]=False
            c.itemconfig(result_id,text=""); c.itemconfig(desc_id,text="")
            c.itemconfig(anim_ball_id,state="hidden")
            _spin_frame(0,28,final_rar,fid)

        self._make_btn(gx,cab_top+110,"🪙 Insert Coin",roll,col="#2a0050",fg="#cc66ff",w=180)
        self._make_btn(W//2,H-32,"← Back",self._back_to_interior,col="#1a1828",fg=CREAM,w=120)

    def _make_figshop_rooms(self):
        def main_decor(c):
            # Dark tiled floor — deep purple/black checkerboard
            for row in range(H//44+1):
                for col in range(W//44+1):
                    shade=(row+col)%2
                    c.create_rectangle(col*44,65+row*44,col*44+43,65+row*44+43,
                                       fill="#0d0018" if shade else "#110020",outline="#1a0030",width=1)
            # Back wall — dark panelling
            c.create_rectangle(0,65,W,180,fill="#0a0016",outline="")
            for px5 in range(0,W,90):
                c.create_rectangle(px5+4,70,px5+86,178,fill="#0e001e",outline="#220033",width=1)
            # Ceiling — dark with pendant lights over each machine
            c.create_rectangle(0,65,W,80,fill="#08000f",outline="")
            # Main sign
            c.create_rectangle(W//2-240,68,W//2+240,112,fill="#0a0018",outline="#883399",width=3)
            c.create_text(W//2,90,text="✦  GUMBALL  EMPORIUM  ✦",fill="#cc66ff",
                          font=tkfont.Font(family="Georgia",size=14,weight="bold"))
            # 6 detailed gumball machines — 3 per row
            rars=["common","uncommon","rare","epic","legendary","mythic"]
            rows_xy=[(W//4,260),(W//2,260),(3*W//4,260),
                     (W//4,480),(W//2,480),(3*W//4,480)]
            for i,rar in enumerate(rars):
                mx5,my5=rows_xy[i]; rc5=self.RARITY_COLS[rar]
                # Pendant light above machine
                c.create_line(mx5,68,mx5,my5-80,fill="#441155",width=2)
                c.create_oval(mx5-10,my5-86,mx5+10,my5-66,fill="#ffeecc",outline=rc5,width=1)
                c.create_oval(mx5-6,my5-82,mx5+6,my5-70,fill="#fff8cc",outline="")
                # Machine base / cabinet
                c.create_rectangle(mx5-18,my5+36,mx5+18,my5+90,fill="#2a2a2a",outline="#444",width=2)
                # Coin slot
                c.create_rectangle(mx5-10,my5+44,mx5+10,my5+52,fill="#1a1a1a",outline="#666",width=1)
                c.create_rectangle(mx5-5,my5+46,mx5+5,my5+50,fill="#111",outline="#888",width=1)
                # Turn handle
                c.create_oval(mx5+8,my5+58,mx5+22,my5+72,fill="#888",outline="#aaa",width=1)
                c.create_line(mx5+15,my5+65,mx5+28,my5+58,fill="#aaa",width=3)
                c.create_oval(mx5+25,my5+54,mx5+31,my5+62,fill="#cc8800",outline=GOLD,width=1)
                # Base foot
                c.create_rectangle(mx5-24,my5+86,mx5+24,my5+100,fill="#222",outline="#555",width=2)
                # Dispensing cup at bottom
                c.create_rectangle(mx5-8,my5+78,mx5+8,my5+90,fill="#333",outline="#555",width=1)
                c.create_arc(mx5-8,my5+84,mx5+8,my5+96,start=180,extent=180,fill="#222",outline="#555")
                # Neck / funnel connecting globe to cabinet
                c.create_polygon(mx5-8,my5+32,mx5-14,my5+40,mx5+14,my5+40,mx5+8,my5+32,
                                 fill="#1a1a1a",outline="#444",width=1)
                # Globe outer ring (metal)
                c.create_oval(mx5-46,my5-54,mx5+46,my5+34,fill=rc5,outline="#111",width=4)
                # Globe glass highlight (lighter inner oval)
                glob_hi=self.RARITY_COLS.get(rar,"#888888")
                c.create_oval(mx5-38,my5-46,mx5+38,my5+26,fill=glob_hi,outline="#333",width=2)
                # Shine reflection on globe (top-left arc)
                c.create_arc(mx5-34,my5-42,mx5+4,my5-8,start=50,extent=80,
                             outline="#ccbbdd",style="arc",width=3)
                # Balls inside globe — 7 coloured balls
                ball_cols=["#cc2244","#2266cc","#22aa44","#cc8800","#aa22cc","#cc4400","#2299aa"]
                for bi5 in range(7):
                    ba5=math.radians(bi5*51+i*15)
                    bx5=mx5+int(22*math.cos(ba5)); by5=my5-10+int(14*math.sin(ba5))
                    bc5=ball_cols[bi5%len(ball_cols)]
                    c.create_oval(bx5-5,by5-5,bx5+5,by5+5,fill=bc5,outline="#111",width=1)
                    # Highlight dot on each ball
                    c.create_oval(bx5-2,by5-3,bx5+1,by5,fill="#dddddd",outline="")
                # Rarity label plaque on front of cabinet
                c.create_rectangle(mx5-30,my5+52,mx5+30,my5+66,fill="#111",outline="#883399",width=1)
                c.create_text(mx5,my5+59,text="GUMBALL",fill="#cc66ff",
                              font=tkfont.Font(family="Courier New",size=6,weight="bold"))
                # Price tag below
                c.create_text(mx5,my5+108,text=f"${self.GUMBALL_COST:,}",fill=CREAM,
                              font=tkfont.Font(family="Courier New",size=8,weight="bold"))
                c.create_text(mx5,my5+122,text="per roll",fill="#887799",
                              font=tkfont.Font(family="Courier New",size=7))

            # Collection board — left wall
            c.create_rectangle(16,130,186,340,fill="#0a0018",outline="#883399",width=2)
            c.create_text(100,148,text="COLLECTION",fill="#cc66ff",
                          font=tkfont.Font(family="Courier New",size=8,weight="bold"))
            c.create_line(22,160,180,160,fill="#330044",width=1)
            for ri5,rar5 in enumerate(["common","uncommon","rare","epic","legendary","mythic"]):
                ry5=172+ri5*26; rc9=self.RARITY_COLS[rar5]
                c.create_rectangle(22,ry5,180,ry5+22,fill="#0d0020",outline="#330044",width=1)
                c.create_oval(26,ry5+4,38,ry5+16,fill=rc9,outline="")
                c.create_text(100,ry5+11,text=rar5.capitalize(),fill=rc9,
                              font=tkfont.Font(family="Courier New",size=7))

            # Showcase cabinet — right wall
            c.create_rectangle(W-190,130,W-16,500,fill="#0a0018",outline="#883399",width=2)
            c.create_text(W-103,148,text="SHOWCASE",fill="#cc66ff",
                          font=tkfont.Font(family="Courier New",size=8,weight="bold"))
            for shelf5 in range(4):
                sy5=168+shelf5*80
                c.create_rectangle(W-184,sy5,W-22,sy5+4,fill="#220033",outline="")
                c.create_rectangle(W-184,sy5+4,W-22,sy5+76,fill="#0e001c",outline="")
            c.create_text(W-103,196,text="🏆",fill=GOLD,font=tkfont.Font(size=16))
            c.create_text(W-103,276,text="⬟",fill="#cc66ff",font=tkfont.Font(size=18))
            c.create_text(W-103,356,text="✦",fill=GOLD,font=tkfont.Font(size=16))
            c.create_text(W-103,435,text="◈",fill="#ff44ff",font=tkfont.Font(size=16))

        EXIT_DOOR={"to":"exit","x":W//2-70,"y":H-65,"w":140,"h":36,"col":"#0a0018","label":"Exit Emporium"}
        rows_npc=[(W//4,360),(W//2,360),(3*W//4,360),
                  (W//4,580),(W//2,580),(3*W//4,580)]
        machine_npcs=[]
        for i in range(6):
            nx,ny=rows_npc[i]
            machine_npcs.append({
                "id":f"gumball_{i}","x":nx,"y":ny,
                "name":"Gumball Machine","col":"#cc66ff",
                "hat_col":"#0a0018","body_col":"#150025",
                "line":f"Gumball Machine\n${self.GUMBALL_COST:,} per roll","game":"gumball"
            })
        return {
            "main":{
                "title":"Gumball Emporium","floor":"#180028","wall":"#110020",
                "decor_fn":main_decor,"furniture":[],
                "doors":[EXIT_DOOR],
                "npcs":machine_npcs,
            }
        }

    # ── HOTEL ROOMS ──────────────────────────────────────
    def _make_hotel_rooms(self):
        def lobby_decor(c):
            # Marble floor — warm ivory tiles
            for row in range(14):
                for col in range(16):
                    x1h=col*72; y1h=65+row*40; shade=(row+col)%2
                    c.create_rectangle(x1h,y1h,x1h+71,y1h+39,
                                       fill="#e8e0d0" if shade else "#ddd8c8",outline="#c8c0b0",width=1)
            c.create_rectangle(20,65,W-20,H-30,fill="",outline="#8B6914",width=3)
            # Columns flanking lobby
            for cx9 in [60,W-60]:
                c.create_rectangle(cx9-14,65,cx9+14,H-30,fill="#d8d0c0",outline="#b0a080",width=2)
                for py9 in range(80,H-30,60):
                    c.create_rectangle(cx9-12,py9,cx9+12,py9+8,fill="#c8c0b0",outline="#a09070",width=1)
                c.create_oval(cx9-16,65,cx9+16,88,fill="#d0c8b0",outline="#a09070",width=2)
            # Check-in counter
            c.create_rectangle(W//2-160,170,W//2+160,260,fill="#a08060",outline=GOLD,width=3)
            c.create_rectangle(W//2-154,176,W//2+154,254,fill="#b89070",outline="#8B6914",width=1)
            c.create_text(W//2,215,text="CHECK-IN",fill="#fff8e8",
                          font=tkfont.Font(family="Georgia",size=12,weight="bold"))
            # Bell on desk
            c.create_oval(W//2+80,198,W//2+104,218,fill="#d4b84a",outline=GOLD,width=2)
            c.create_line(W//2+92,218,W//2+92,228,fill="#8B6914",width=3)
            # Flowers on desk
            c.create_oval(W//2-90,162,W//2-70,178,fill="#ff6688",outline="")
            c.create_oval(W//2-86,156,W//2-66,172,fill="#ff88aa",outline="")
            c.create_line(W//2-78,178,W//2-78,200,fill="#2a6a22",width=2)
            # Chandelier
            chx2=W//2; chy2=82
            c.create_line(chx2,65,chx2,chy2+8,fill="#8B6914",width=4)
            c.create_oval(chx2-12,chy2,chx2+12,chy2+22,fill=GOLD,outline="#5a4010",width=2)
            for i in range(10):
                a=math.radians(i*36); r4=36
                x4c=chx2+int(r4*math.cos(a)); y4c=chy2+11+int(r4*0.38*math.sin(a))
                c.create_line(chx2,chy2+11,x4c,y4c+10,fill=GOLD,width=1)
                c.create_oval(x4c-5,y4c+7,x4c+5,y4c+17,fill="#fff8cc",outline=GOLD,width=1)
            # Elevator — right side, compact door panel
            ex=W-72; ey1=H-170; ey2=H-40
            c.create_rectangle(ex-26,ey1,ex+26,ey2,fill="#c0b8a8",outline="#808060",width=2)
            c.create_rectangle(ex-22,ey1+4,ex+1,ey2-4,fill="#b8a888",outline="#806848",width=1)
            c.create_rectangle(ex,ey1+4,ex+22,ey2-4,fill="#b8a888",outline="#806848",width=1)
            c.create_oval(ex-6,ey1+8,ex+6,ey1+20,fill="#e0d8c8",outline=GOLD,width=1)
            c.create_text(ex,ey1+14,text="▲",fill="#4a3810",font=tkfont.Font(size=7))
            c.create_text(ex,ey2-12,text="LIFT",fill="#6a5830",
                          font=tkfont.Font(family="Courier New",size=6,weight="bold"))
            # Armchairs in lobby waiting area
            for ax2 in [140,W-140]:
                c.create_rectangle(ax2-30,380,ax2+30,450,fill="#a07050",outline="#6a4a30",width=2)
                c.create_rectangle(ax2-26,370,ax2+26,386,fill="#b08060",outline=GOLD,width=1)
                c.create_rectangle(ax2-34,380,ax2-26,450,fill="#906040",outline="#5a3820",width=1)
                c.create_rectangle(ax2+26,380,ax2+34,450,fill="#906040",outline="#5a3820",width=1)
            # Coffee table
            c.create_oval(W//2-60,430,W//2+60,470,fill="#8B6914",outline="#5a4010",width=2)
            c.create_oval(W//2-6,438,W//2+6,462,fill="#7a5a10",outline=GOLD,width=1)
            # Potted palm (left wall)
            c.create_rectangle(120,530,150,590,fill="#8B4513",outline="#5a2a08",width=2)
            c.create_line(135,530,135,470,fill="#2a6a22",width=3)
            for a3 in range(0,360,60):
                ea=math.radians(a3); lx3=135+int(40*math.cos(ea)); ly3=470+int(16*math.sin(ea))
                c.create_line(135,470,lx3,ly3,fill="#3a8a28",width=3)
                c.create_oval(lx3-10,ly3-6,lx3+10,ly3+6,fill="#2a7020",outline="")
            # Hotel sign above counter
            c.create_rectangle(W//2-140,72,W//2+140,108,fill="#1a3a6a",outline=GOLD,width=2)
            c.create_text(W//2,90,text="✦  GRAND HOTEL  ✦",fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=12,weight="bold"))
            # Welcome mat
            c.create_rectangle(W//2-80,H-68,W//2+80,H-36,fill="#1a3a6a",outline=GOLD,width=2)
            c.create_text(W//2,H-52,text="WELCOME",fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=10,weight="bold"))

        def floor2_decor(c):
            # Carpeted hallway floor — rich burgundy
            for row in range(14):
                for col in range(16):
                    x1f=col*72; y1f=65+row*40; shade=(row+col)%2
                    c.create_rectangle(x1f,y1f,x1f+71,y1f+39,
                                       fill="#3a0810" if shade else "#440a14",outline="#2a0608",width=1)
            # Gold runner carpet strip down middle
            c.create_rectangle(W//2-30,65,W//2+30,H-30,fill="#2a1800",outline="")
            for ry2 in range(80,H-30,40):
                c.create_rectangle(W//2-24,ry2,W//2+24,ry2+30,fill="#3a2400",outline="#5a3a10",width=1)
                c.create_text(W//2,ry2+15,text="◆",fill=GOLD,font=tkfont.Font(size=7))
            c.create_rectangle(20,65,W-20,H-30,fill="",outline=GOLD,width=2)
            # Wall sconces
            for sx3 in [40,W-40]:
                c.create_rectangle(sx3-8,120,sx3+8,178,fill="#2a1800",outline=GOLD,width=2)
                c.create_oval(sx3-8,178,sx3+8,204,fill="#ffee88",outline=GOLD,width=1)
            # Compact lifts at bottom (left=down to lobby, right=up to floor3)
            for exr,lbl in [(80,"▼ LOBBY"),(W-80,"▲ FL.3")]:
                c.create_rectangle(exr-26,H-170,exr+26,H-50,fill="#c0b8a8",outline="#808060",width=2)
                c.create_rectangle(exr-22,H-166,exr+1,H-54,fill="#b8a888",outline="#806848",width=1)
                c.create_rectangle(exr,H-166,exr+22,H-54,fill="#b8a888",outline="#806848",width=1)
                c.create_oval(exr-6,H-162,exr+6,H-150,fill="#e0d8c8",outline=GOLD,width=1)
                c.create_text(exr,H-156,text="▲▼",fill="#4a3810",font=tkfont.Font(size=6))
                c.create_text(exr,H-60,text=lbl,fill="#6a5830",
                              font=tkfont.Font(family="Courier New",size=6,weight="bold"))
            c.create_text(W//2,88,text="─── 2nd Floor ───",fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=11,weight="bold"))
            # Figurine display table — centre of hallway
            tx=W//2; ty=330
            c.create_rectangle(tx-180,ty,tx+180,ty+18,fill="#6a4820",outline=GOLD,width=2)  # tabletop
            c.create_rectangle(tx-176,ty+18,tx+176,ty+24,fill="#4a3010",outline="")
            c.create_rectangle(tx-172,ty+24,tx-158,ty+65,fill="#5a3818",outline="#3a2008",width=1)
            c.create_rectangle(tx+158,ty+24,tx+172,ty+65,fill="#5a3818",outline="#3a2008",width=1)
            c.create_rectangle(tx-6,ty+24,tx+6,ty+65,fill="#5a3818",outline="#3a2008",width=1)
            # 10 slot markers on table
            for si in range(10):
                sx=tx-162+si*36; sy=ty-2
                c.create_oval(sx-8,sy-8,sx+8,sy+8,fill="#2a1808",outline=GOLD,width=1)
            c.create_text(tx,ty-18,text="✦  Figurine Display  ✦",fill=GOLD,
                          font=tkfont.Font(family="Courier New",size=8,weight="bold"))
            c.create_text(tx,ty+82,text="[Interact to manage]",fill="#6a5030",
                          font=tkfont.Font(family="Courier New",size=7))

        def floor3_decor(c):
            # Premium floor — dark teal carpet
            for row in range(14):
                for col in range(16):
                    x1g=col*72; y1g=65+row*40; shade=(row+col)%2
                    c.create_rectangle(x1g,y1g,x1g+71,y1g+39,
                                       fill="#061a18" if shade else "#082018",outline="#041410",width=1)
            c.create_rectangle(W//2-32,65,W//2+32,H-30,fill="#031810",outline="")
            for ry5 in range(80,H-30,40):
                c.create_rectangle(W//2-26,ry5,W//2+26,ry5+30,fill="#052018",outline="#0a4030",width=1)
                c.create_text(W//2,ry5+15,text="◆",fill="#00aaaa",font=tkfont.Font(size=7))
            c.create_rectangle(20,65,W-20,H-30,fill="",outline="#00aaaa",width=2)
            # Side sconces
            for sx4 in [40,W-40]:
                c.create_rectangle(sx4-8,120,sx4+8,178,fill="#052018",outline="#00aaaa",width=2)
                c.create_oval(sx4-8,178,sx4+8,204,fill="#88ffee",outline="#00aaaa",width=1)
            # Lift visual at bottom-left (decorative — use floor 2 door to actually travel)
            exr4=80
            c.create_rectangle(exr4-26,H-170,exr4+26,H-50,fill="#a0b8b0",outline="#608080",width=2)
            c.create_rectangle(exr4-22,H-166,exr4+1,H-54,fill="#90a8a0",outline="#507070",width=1)
            c.create_rectangle(exr4,H-166,exr4+22,H-54,fill="#90a8a0",outline="#507070",width=1)
            c.create_oval(exr4-6,H-162,exr4+6,H-150,fill="#d0e8e0",outline="#00aaaa",width=1)
            c.create_text(exr4,H-156,text="▲▼",fill="#00aaaa",font=tkfont.Font(size=6))
            c.create_text(exr4,H-60,text="LIFT",fill="#006655",
                          font=tkfont.Font(family="Courier New",size=6,weight="bold"))
            c.create_text(W//2,88,text="─── 3rd Floor ───",fill="#00aaaa",
                          font=tkfont.Font(family="Georgia",size=11,weight="bold"))
            # Grand figurine display table — wide, 30 slots across 3 rows
            tx3=W//2; ty3=300
            c.create_rectangle(tx3-360,ty3,tx3+360,ty3+22,fill="#063828",outline="#00aaaa",width=2)
            c.create_rectangle(tx3-356,ty3+22,tx3+356,ty3+28,fill="#042a1e",outline="")
            for leg3 in [tx3-350,tx3-120,tx3+120,tx3+350]:
                c.create_rectangle(leg3-7,ty3+28,leg3+7,ty3+72,fill="#052a20",outline="#0a4030",width=1)
            # 30 slot markers — 3 rows of 10
            for row3 in range(3):
                for col3 in range(10):
                    sx3=tx3-324+col3*72; sy3=ty3+(row3*8)-6
                    c.create_oval(sx3-6,sy3-6,sx3+6,sy3+6,fill="#031810",outline="#00aaaa",width=1)
            c.create_text(tx3,ty3-20,text="✦  Grand Figurine Exhibition  ✦",fill="#00aaaa",
                          font=tkfont.Font(family="Courier New",size=8,weight="bold"))
            c.create_text(tx3,ty3+88,text="[Interact to manage — 30 slots]",fill="#0a6655",
                          font=tkfont.Font(family="Courier New",size=7))

        def room_decor_f2(c):
            """Floor 2 guest room — comfortable, warm"""
            c.create_rectangle(0,65,W,H-30,fill="#2a1a0a",outline="")
            # Wooden floorboards
            for row in range(65,H-30,22):
                for col in range(0,W,60):
                    c.create_rectangle(col+1,row+1,col+59,row+21,fill="#3a2210",outline="#2a1608",width=1)
            # Bed (centre-left)
            bx,by=180,320
            c.create_rectangle(bx-80,by+60,bx+80,by+100,fill="#1a0c04",outline="#0d0600",width=2) # bedframe base
            c.create_rectangle(bx-80,by-40,bx+80,by+80,fill="#e8e0d0",outline="#c0b890",width=2) # mattress
            c.create_rectangle(bx-80,by-40,bx+80,by+10,fill="#cc2244",outline="#880022",width=2) # duvet red
            for stripe in range(bx-72,bx+72,24):
                c.create_rectangle(stripe,by-40,stripe+12,by+10,fill="#aa1a36",outline="") # stripe
            c.create_rectangle(bx-60,by-60,bx-10,by-36,fill="#e8e0d0",outline="#c0b890",width=1) # pillow L
            c.create_rectangle(bx+10,by-60,bx+60,by-36,fill="#e8e0d0",outline="#c0b890",width=1) # pillow R
            c.create_rectangle(bx-80,by-68,bx+80,by-40,fill="#4a2a10",outline=GOLD,width=2) # headboard
            c.create_rectangle(bx-80,by+80,bx+80,by+100,fill="#3a1a08",outline="#2a0e04",width=1) # foot board
            # Bedside table + lamp
            c.create_rectangle(bx+100,by-10,bx+150,by+80,fill="#3a2210",outline="#2a1608",width=2)
            c.create_rectangle(bx+100,by+30,bx+150,by+80,fill="#2a1808",outline="#1a1008",width=1)
            c.create_rectangle(bx+105,by-8,bx+145,by-2,fill="#5a3820",outline="#3a2010",width=1)
            c.create_oval(bx+108,by-28,bx+142,by-2,fill="#ffee88",outline=GOLD,width=2)
            c.create_rectangle(bx+120,by-2,bx+130,by+20,fill="#6a4820",outline="",)
            c.create_oval(bx+112,by+16,bx+138,by+28,fill="#3a2210",outline=GOLD,width=1)
            # TV on wall
            tvx,tvy=W-120,200
            c.create_rectangle(tvx-70,tvy-44,tvx+70,tvy+44,fill="#111",outline="#333",width=3)
            c.create_rectangle(tvx-64,tvy-38,tvx+64,tvy+38,fill="#1a2a3a",outline="")
            # TV screen shows a blue-grey glow
            c.create_rectangle(tvx-62,tvy-36,tvx+62,tvy+36,fill="#1e3a5a",outline="")
            c.create_text(tvx,tvy,text="📺",fill="#88aacc",font=tkfont.Font(size=18))
            c.create_rectangle(tvx-8,tvy+44,tvx+8,tvy+56,fill="#222",outline="#111",width=1)
            c.create_rectangle(tvx-22,tvy+54,tvx+22,tvy+60,fill="#111",outline="#333",width=1)
            c.create_text(tvx,tvy+72,text="[C] Watch TV",fill="#556677",
                          font=tkfont.Font(family="Courier New",size=7))
            txr2,tyr2=W-140,430
            c.create_oval(txr2-40,tyr2-16,txr2+40,tyr2+16,fill="#5a3a18",outline=GOLD,width=2)
            for a5 in [0,120,240]:
                ea5=math.radians(a5); cxr5=txr2+int(70*math.cos(ea5)); cyr5=tyr2+int(50*math.sin(ea5))
                c.create_rectangle(cxr5-16,cyr5-10,cxr5+16,cyr5+30,fill="#3a2210",outline=GOLD,width=1)
                c.create_rectangle(cxr5-14,cyr5-10,cxr5+14,cyr5-4,fill="#4a3018",outline="")
            # Minibar / cabinet — bottom left corner
            c.create_rectangle(20,H-130,100,H-40,fill="#2e1c08",outline="#1a0e04",width=2)
            c.create_rectangle(24,H-126,96,H-80,fill="#3a2210",outline="#5a3818",width=1)
            c.create_line(60,H-126,60,H-80,fill="#1a0e04",width=1)
            c.create_text(60,H-60,text="MINI BAR",fill="#8B6914",
                          font=tkfont.Font(family="Courier New",size=7,weight="bold"))
            # Window with curtains
            c.create_rectangle(W//2-50,75,W//2+50,160,fill="#a8d4f0",outline="#6a9ab8",width=2)
            c.create_line(W//2,75,W//2,160,fill="#6a9ab8",width=1)
            c.create_rectangle(W//2-50,75,W//2-30,160,fill="#2a0050",outline="")
            c.create_rectangle(W//2+30,75,W//2+50,160,fill="#2a0050",outline="")
            c.create_rectangle(W//2-60,72,W//2+60,84,fill="#1a0030",outline=GOLD,width=1)
            c.create_text(W//2,78,text="Std Room • Floor 2",fill=GOLD,font=tkfont.Font(size=7))

        def room_decor_f3(c):
            """Floor 3 suite — luxury teal/gold"""
            c.create_rectangle(0,65,W,H-30,fill="#061a14",outline="")
            # Stone tile floor with inlaid pattern
            for row2 in range(65,H-30,28):
                for col2 in range(0,W,56):
                    shade2=(row2//28+col2//56)%2
                    c.create_rectangle(col2+1,row2+1,col2+55,row2+27,
                                       fill="#082018" if shade2 else "#0a2820",outline="#051510",width=1)
            # Central gold medallion on floor
            c.create_oval(W//2-50,380,W//2+50,460,fill="",outline="#2a1800",width=2)
            c.create_oval(W//2-38,392,W//2+38,448,fill="",outline=GOLD,width=1)
            # Bed — kingsize, opulent
            bx3,by3=200,320
            c.create_rectangle(bx3-100,by3+60,bx3+100,by3+108,fill="#0d1a10",outline="#0a1208",width=2)
            c.create_rectangle(bx3-100,by3-48,bx3+100,by3+80,fill="#f0ece0",outline="#d0c8a8",width=2)
            c.create_rectangle(bx3-100,by3-48,bx3+100,by3+16,fill="#006666",outline="#004444",width=2)
            for st2 in range(bx3-92,bx3+90,28):
                c.create_rectangle(st2,by3-48,st2+14,by3+16,fill="#007a7a",outline="")
            c.create_rectangle(bx3-72,by3-72,bx3-12,by3-46,fill="#f0ece0",outline="#d0c8a8",width=1)
            c.create_rectangle(bx3+12,by3-72,bx3+72,by3-46,fill="#f0ece0",outline="#d0c8a8",width=1)
            c.create_rectangle(bx3-100,by3-82,bx3+100,by3-48,fill="#0d2a1e",outline="#00aaaa",width=3)
            # Bedside tables + lamps both sides
            for bsign in [-1,1]:
                bsx=bx3+bsign*130
                c.create_rectangle(bsx-24,by3-14,bsx+24,by3+76,fill="#0d1a10",outline="#0a2820",width=2)
                c.create_oval(bsx-18,by3-36,bsx+18,by3-8,fill="#88ffee",outline="#00aaaa",width=2)
                c.create_rectangle(bsx-4,by3-8,bsx+4,by3+14,fill="#0d2820",outline="")
            # Large TV wall-mounted
            tvx3=W-130; tvy3=200
            c.create_rectangle(tvx3-80,tvy3-52,tvx3+80,tvy3+52,fill="#0a0a0a",outline="#00aaaa",width=3)
            c.create_rectangle(tvx3-74,tvy3-46,tvx3+74,tvy3+46,fill="#0d1a24",outline="")
            c.create_rectangle(tvx3-72,tvy3-44,tvx3+72,tvy3+44,fill="#112a3a",outline="")
            c.create_text(tvx3,tvy3,text="📺",fill="#55ddcc",font=tkfont.Font(size=22))
            c.create_rectangle(tvx3-10,tvy3+52,tvx3+10,tvy3+66,fill="#0a0a0a",outline="#222",width=1)
            c.create_rectangle(tvx3-28,tvy3+64,tvx3+28,tvy3+72,fill="#0a0a0a",outline="#00aaaa",width=1)
            c.create_text(tvx3,tvy3+84,text="[C] Watch TV",fill="#006655",
                          font=tkfont.Font(family="Courier New",size=7))
            txr3,tyr3=W-150,450
            c.create_oval(txr3-50,tyr3-20,txr3+50,tyr3+20,fill="#0d2820",outline="#00aaaa",width=2)
            for a6 in [0,90,180,270]:
                ea6=math.radians(a6); cxr6=txr3+int(80*math.cos(ea6)); cyr6=tyr3+int(60*math.sin(ea6))
                c.create_rectangle(cxr6-18,cyr6-12,cxr6+18,cyr6+32,fill="#082018",outline="#00aaaa",width=1)
                c.create_rectangle(cxr6-16,cyr6-12,cxr6+16,cyr6-6,fill="#0a2820",outline="")
            # Mini fridge + espresso machine — bottom left corner
            c.create_rectangle(20,H-140,100,H-40,fill="#0a1a10",outline="#00aaaa",width=2)
            c.create_rectangle(24,H-136,96,H-92,fill="#0d2018",outline="#007070",width=1)
            c.create_text(60,H-114,text="FRIDGE",fill="#00aaaa",font=tkfont.Font(family="Courier New",size=7))
            c.create_rectangle(24,H-90,96,H-44,fill="#0a1810",outline="#007070",width=1)
            c.create_text(60,H-67,text="☕",fill="#00aaaa",font=tkfont.Font(size=10))
            # Jacuzzi tub (corner)
            c.create_oval(W-150,H-140,W-30,H-60,fill="#0a3040",outline="#00aaaa",width=3)
            c.create_oval(W-142,H-132,W-38,H-68,fill="#0d3848",outline="#008888",width=1)
            c.create_text(W-90,H-96,text="♨",fill="#88ffee",font=tkfont.Font(size=14))
            # Window (wide, panoramic)
            c.create_rectangle(W//2-90,75,W//2+90,170,fill="#a0c8e8",outline="#00aaaa",width=2)
            c.create_line(W//2,75,W//2,170,fill="#00aaaa",width=1)
            c.create_rectangle(W//2-90,75,W//2-62,170,fill="#062018",outline="")
            c.create_rectangle(W//2+62,75,W//2+90,170,fill="#062018",outline="")
            c.create_rectangle(W//2-100,72,W//2+100,86,fill="#062018",outline="#00aaaa",width=1)
            c.create_text(W//2,79,text="Suite • Floor 3",fill="#00aaaa",font=tkfont.Font(size=7))

        EDOOR_UP2   ={"to":"floor2",    "x":W-110,"y":H-100,"w":90,"h":40,"col":"#5a4830","label":"▲ Floor 2"}
        EDOOR_DOWN1 ={"to":"lobby",     "x":20,   "y":H-100,"w":90,"h":40,"col":"#5a4830","label":"▼ Lobby"}
        EDOOR_UP3   ={"to":"floor3",    "x":W-110,"y":H-100,"w":90,"h":40,"col":"#1a3828","label":"▲ Floor 3"}
        EDOOR_DOWN2 ={"to":"floor2",    "x":20,   "y":H-100,"w":90,"h":40,"col":"#1a3828","label":"▼ Floor 2"}
        EXIT_DOOR   ={"to":"exit",      "x":W//2-80,"y":H-72,"w":160,"h":36,"col":"#1a3a6a","label":"Exit Hotel"}
        F2_EXIT ={"to":"floor2","x":W//2-80,"y":H-72,"w":160,"h":36,"col":"#5a4830","label":"← Floor 2"}
        F3_EXIT ={"to":"floor3","x":W//2-80,"y":H-72,"w":160,"h":36,"col":"#062018","label":"← Floor 3"}

        # Floor 2: 4 rooms left (101-104), 4 rooms right (105-108)
        F2_DOORS=[
            {"to":"room_101","x":20,   "y":160,"w":110,"h":38,"col":"#3a2210","label":"Room 101","locked":"room_101"},
            {"to":"room_102","x":20,   "y":280,"w":110,"h":38,"col":"#3a2210","label":"Room 102","locked":"room_102"},
            {"to":"room_103","x":20,   "y":400,"w":110,"h":38,"col":"#3a2210","label":"Room 103","locked":"room_103"},
            {"to":"room_104","x":20,   "y":520,"w":110,"h":38,"col":"#3a2210","label":"Room 104","locked":"room_104"},
            {"to":"room_105","x":W-130,"y":160,"w":110,"h":38,"col":"#3a2210","label":"Room 105","locked":"room_105"},
            {"to":"room_106","x":W-130,"y":280,"w":110,"h":38,"col":"#3a2210","label":"Room 106","locked":"room_106"},
            {"to":"room_107","x":W-130,"y":400,"w":110,"h":38,"col":"#3a2210","label":"Room 107","locked":"room_107"},
            {"to":"room_108","x":W-130,"y":520,"w":110,"h":38,"col":"#3a2210","label":"Room 108","locked":"room_108"},
        ]
        # Floor 3: 4 suites left (201-204), 4 suites right (205-208)
        F3_DOORS=[
            {"to":"room_201","x":20,   "y":160,"w":110,"h":38,"col":"#062018","label":"Suite 201","locked":"room_201"},
            {"to":"room_202","x":20,   "y":280,"w":110,"h":38,"col":"#062018","label":"Suite 202","locked":"room_202"},
            {"to":"room_203","x":20,   "y":400,"w":110,"h":38,"col":"#062018","label":"Suite 203","locked":"room_203"},
            {"to":"room_204","x":20,   "y":520,"w":110,"h":38,"col":"#062018","label":"Suite 204","locked":"room_204"},
            {"to":"room_205","x":W-130,"y":160,"w":110,"h":38,"col":"#062018","label":"Suite 205","locked":"room_205"},
            {"to":"room_206","x":W-130,"y":280,"w":110,"h":38,"col":"#062018","label":"Suite 206","locked":"room_206"},
            {"to":"room_207","x":W-130,"y":400,"w":110,"h":38,"col":"#062018","label":"Suite 207","locked":"room_207"},
            {"to":"room_208","x":W-130,"y":520,"w":110,"h":38,"col":"#062018","label":"Suite 208","locked":"room_208"},
        ]

        rooms_dict={
            "lobby":{
                "title":"Grand Hotel — Lobby","floor":"#e8e0d0","wall":"#d8d0c0",
                "decor_fn":lobby_decor,"furniture":[
                    {"type":"plant","bounds":(100,480,152,580),"label":""},
                    {"type":"lamp","bounds":(200,380,240,520),"label":""},
                    {"type":"lamp","bounds":(W-240,380,W-200,520),"label":""},
                ],
                "doors":[EXIT_DOOR,EDOOR_UP2],
                "npcs":[{"id":"hotel_desk","x":W//2,"y":230,"name":"Receptionist Clara","col":"#f0d0a0",
                          "hat_col":"#1a3a6a","body_col":"#1a3a6a",
                          "line":"Welcome! Buy a room\nor check availability.","game":"hotel_checkin"}]
            },
            "floor2":{
                "title":"Grand Hotel — 2nd Floor","floor":"#3a0810","wall":"#2a0608",
                "decor_fn":floor2_decor,"furniture":[
                    {"type":"lamp","bounds":(160,240,200,380),"label":""},
                    {"type":"lamp","bounds":(W-200,240,W-160,380),"label":""},
                ],
                "doors":[EDOOR_DOWN1,EDOOR_UP3]+F2_DOORS,
                "npcs":[{"id":"fig_table_f2","x":W//2,"y":350,"name":"Display Table","col":GOLD,
                         "hat_col":"#2a1800","body_col":"#3a2800",
                         "line":"10-slot figurine table.\nClick to manage display.","game":"figurine_table_f2"}]
            },
            "floor3":{
                "title":"Grand Hotel — 3rd Floor","floor":"#061a14","wall":"#041010",
                "decor_fn":floor3_decor,"furniture":[
                    {"type":"lamp","bounds":(160,240,200,380),"label":""},
                    {"type":"lamp","bounds":(W-200,240,W-160,380),"label":""},
                ],
                "doors":[EDOOR_DOWN2]+F3_DOORS,
                "npcs":[{"id":"fig_table_f3","x":W//2,"y":350,"name":"Grand Display Table","col":"#00aaaa",
                         "hat_col":"#031810","body_col":"#052018",
                         "line":"30-slot figurine table.\nClick to manage display.","game":"figurine_table_f3"}]
            },
        }
        # Add all 16 room entries
        f2_names={f"room_{101+i}":f"Room {101+i}" for i in range(8)}
        f3_names={f"room_{201+i}":f"Suite {201+i}" for i in range(8)}
        for rkey,rname in f2_names.items():
            rooms_dict[rkey]={
                "title":f"Standard Room — {rname}","floor":"#2a1a0a","wall":"#1a0e04",
                "decor_fn":room_decor_f2,"furniture":[],"has_tv":True,
                "doors":[F2_EXIT],"npcs":[]
            }
        for rkey,rname in f3_names.items():
            rooms_dict[rkey]={
                "title":f"Luxury Suite — {rname}","floor":"#061a14","wall":"#041010",
                "decor_fn":room_decor_f3,"furniture":[],"has_tv":True,
                "doors":[F3_EXIT],"npcs":[]
            }
        return rooms_dict

    # ── HOTEL SCREENS ─────────────────────────────────────
    def _hotel_checkin_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("GRAND HOTEL — RECEPTION","#0a1828","#0d1e30")
        if not hasattr(self,"hotel_owned_rooms"): self.hotel_owned_rooms={}
        owned=self.hotel_owned_rooms
        c.create_text(W//2,82,text="✦  Room Availability  ✦",fill=GOLD,
                      font=tkfont.Font(family="Georgia",size=13,weight="bold"))
        rooms=(
            [{"id":f"room_{101+i}","name":f"Room {101+i}","floor":2,"cost":600+(i%2)*50,
              "desc":"Standard · TV · Bed · Minibar"} for i in range(8)]+
            [{"id":f"room_{201+i}","name":f"Suite {201+i}","floor":3,"cost":2000+(i%2)*200,
              "desc":"Luxury · TV · Jacuzzi · Espresso"} for i in range(8)]
        )
        col_w=295; row_h=58; start_x=W//2-305; start_y=106
        for idx,rm in enumerate(rooms):
            col=idx%2; row=idx//2
            x1=start_x+col*col_w; y1=start_y+row*row_h
            bought=rm["id"] in owned
            col_bg="#1a2a0a" if bought else "#0d1220"
            col_bd="#2a8a2a" if bought else (GOLD if rm["floor"]==2 else "#00aaaa")
            round_rect(c,x1,y1,x1+col_w-8,y1+row_h-4,r=6,fill=col_bg,outline=col_bd,width=2)
            c.create_text(x1+8,y1+12,text=rm["name"],fill=GOLD if rm["floor"]==2 else "#00ffcc",
                          font=tkfont.Font(family="Georgia",size=10,weight="bold"),anchor="w")
            c.create_text(x1+8,y1+28,text=rm["desc"],fill=CREAM,
                          font=tkfont.Font(family="Courier New",size=7),anchor="w")
            if bought:
                c.create_text(x1+col_w-16,y1+20,text="✓",fill="#44cc44",
                              font=tkfont.Font(family="Georgia",size=14,weight="bold"),anchor="e")
            else:
                def buy(r=rm):
                    if self.money<r["cost"]:
                        self._msg(f"Need ${r['cost']:,}.",RED_C); return
                    self.money-=r["cost"]; self._refresh_balance_text()
                    self.hotel_owned_rooms[r["id"]]=r["floor"]
                    self._msg(f"{r['name']} purchased!",GREEN_C)
                    self._hotel_checkin_screen()
                self._make_btn(x1+col_w-52,y1+20,f"${rm['cost']:,}",buy,col="#1a1830",fg=GOLD,w=86)
        self._make_btn(W//2,H-30,"← Back",self._back_to_interior,col="#1a1828",fg=CREAM,w=120)

    def _hotel_raffle_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("VIP RAFFLE","#0a0020","#0d0028")
        TICKET_COST=100; PRIZE=1000000; MAX_TICKETS=10; TOTAL=300
        if not hasattr(self,"_raffle_tickets"): self._raffle_tickets=[]   # list of chosen numbers
        if not hasattr(self,"_raffle_end_time"): self._raffle_end_time=None
        if not hasattr(self,"_raffle_after_id"): self._raffle_after_id=None
        # Legacy compat — if old int format, reset
        if isinstance(self._raffle_tickets, int): self._raffle_tickets=[]

        c.create_text(W//2,78,text="★  VIP RAFFLE  ★",fill=GOLD,
                      font=tkfont.Font(family="Georgia",size=18,weight="bold"))
        c.create_text(W//2,104,text=f"${TICKET_COST:,} per ticket  ·  Up to {MAX_TICKETS} tickets  ·  Win ${PRIZE:,}",
                      fill="#aaaaff",font=tkfont.Font(family="Courier New",size=9))

        timer_id=c.create_text(W//2,126,text="No active draw — buy a ticket to start!",fill=CREAM,
                               font=tkfont.Font(family="Courier New",size=10,weight="bold"))
        result_id=c.create_text(W//2,148,text="",fill=GOLD,
                                font=tkfont.Font(family="Georgia",size=13,weight="bold"))

        # ── Number picker for NEXT ticket ────────────────────
        c.create_text(W//2,178,text="Choose a number for your next ticket  (1 – 300):",
                      fill=CREAM,font=tkfont.Font(family="Courier New",size=9))
        pick_var=[1]
        pick_id=c.create_text(W//2,206,text="1",fill=GOLD,
                              font=tkfont.Font(family="Georgia",size=20,weight="bold"))

        def pick_change(d):
            pick_var[0]=max(1,min(TOTAL,pick_var[0]+d))
            c.itemconfig(pick_id,text=str(pick_var[0]))

        self._make_btn(W//2-88,206,"◀◀",lambda:pick_change(-10),col="#1a0040",fg=GOLD,w=46)
        self._make_btn(W//2-46,206,"◀", lambda:pick_change(-1), col="#1a0040",fg=GOLD,w=34)
        self._make_btn(W//2+46,206,"▶", lambda:pick_change(1),  col="#1a0040",fg=GOLD,w=34)
        self._make_btn(W//2+88,206,"▶▶",lambda:pick_change(10), col="#1a0040",fg=GOLD,w=46)

        buy_btn_id=[None]   # hold ref so we can show/hide

        # ── Tickets owned display ─────────────────────────────
        tix_header=c.create_text(W//2,242,
                                 text=f"Your tickets: {len(self._raffle_tickets)}/{MAX_TICKETS}",
                                 fill=CREAM,font=tkfont.Font(family="Courier New",size=10))

        # Grid of ticket slots (2 rows × 5 cols)
        SLOT_W=88; SLOT_H=28; COLS=5
        slot_ids=[]
        for ti in range(MAX_TICKETS):
            col_i=ti%COLS; row_i=ti//COLS
            sx=W//2-220+col_i*(SLOT_W+8); sy=268+row_i*(SLOT_H+6)
            round_rect(c,sx,sy,sx+SLOT_W,sy+SLOT_H,r=6,fill="#120028",outline="#443366",width=1)
            num_str=str(self._raffle_tickets[ti]) if ti<len(self._raffle_tickets) else "—"
            col_str=GOLD if ti<len(self._raffle_tickets) else "#333355"
            sid=c.create_text(sx+SLOT_W//2,sy+SLOT_H//2,text=f"#{num_str}",fill=col_str,
                              font=tkfont.Font(family="Courier New",size=9,weight="bold"))
            slot_ids.append((sid,sx,sy))

        def refresh_slots():
            c.itemconfig(tix_header,text=f"Your tickets: {len(self._raffle_tickets)}/{MAX_TICKETS}")
            for ti,(sid,_,_) in enumerate(slot_ids):
                if ti<len(self._raffle_tickets):
                    c.itemconfig(sid,text=f"#{self._raffle_tickets[ti]}",fill=GOLD)
                else:
                    c.itemconfig(sid,text="—",fill="#333355")

        def update_timer():
            if self._raffle_end_time is None: return
            try: c.winfo_exists()
            except: return
            if self.screen!="game": return
            remaining=int(self._raffle_end_time-time.time())
            if remaining<=0:
                draw=random.randint(1,TOTAL)
                wins=[n for n in self._raffle_tickets if n==draw]
                if wins:
                    prize=PRIZE*len(wins)
                    self.money+=prize; self._refresh_balance_text()
                    c.itemconfig(result_id,text=f"🎉 NUMBER {draw} WINS! +${prize:,}",fill=GOLD)
                    self._post_game(prize,"win")
                else:
                    c.itemconfig(result_id,text=f"Drawn: {draw}. No match. Better luck next time!",fill=RED_C)
                c.itemconfig(timer_id,text="Draw complete! Buy tickets for the next draw.")
                self._raffle_tickets=[]; self._raffle_end_time=None; self._raffle_after_id=None
                refresh_slots()
                return
            mins,secs=divmod(remaining,60)
            c.itemconfig(timer_id,text=f"⏱  Draw in  {mins}:{secs:02d}")
            self._raffle_after_id=self.after(1000,update_timer)

        def buy_one():
            if self._raffle_end_time and time.time()>self._raffle_end_time: return
            if len(self._raffle_tickets)>=MAX_TICKETS:
                self._msg("You already have 10 tickets!",RED_C); return
            if self.money<TICKET_COST:
                self._msg(f"Need ${TICKET_COST:,}!",RED_C); return
            self.money-=TICKET_COST; self._refresh_balance_text()
            self._raffle_tickets.append(pick_var[0])
            refresh_slots()
            if self._raffle_end_time is None:
                self._raffle_end_time=time.time()+120
                update_timer()

        self._make_btn(W//2,340,f"Buy Ticket #{len(self._raffle_tickets)+1} — ${TICKET_COST:,}",
                       buy_one,col="#2a0060",fg=GOLD,w=320)
        self._make_btn(W//2,530,"← Back",self._back_to_interior,col="#1a1828",fg=CREAM,w=120)

        if self._raffle_end_time:
            update_timer()


    def _hotel_tv_screen(self, show=None):
        self._clear_overlay(); c=self.canvas
        tv_after_ids=[]
        # State vars first — must be defined before any closures reference them
        tv_running=[True]
        current_show=[show]   # None = menu, or show name string
        frame_counter=[0]
        show_start=[time.time()]

        def cancel_all():
            for aid in tv_after_ids:
                try: self.after_cancel(aid)
                except: pass
            tv_after_ids.clear()

        def back():
            tv_running[0]=False; cancel_all(); self._back_to_interior()

        def stop_and_menu():
            tv_running[0]=False; cancel_all()
            current_show[0]=None; frame_counter[0]=0; show_start[0]=time.time()
            tv_running[0]=True; draw_menu()

        # ── Shared TV bezel (drawn once per show change) ─────────
        def draw_bezel():
            c.delete("all")
            c.create_rectangle(0,0,W,H,fill="#050505")
            c.create_rectangle(W//2-380,50,W//2+380,H-50,fill="#111",outline="#333",width=4)
            c.create_rectangle(W//2-370,60,W//2+370,H-60,fill="#000",outline="")
            for bx_off in [-20,0,20]:
                c.create_oval(W//2+340+bx_off-6,H-55,W//2+340+bx_off+6,H-45,fill="#222",outline="#444")

        # ── Show: DUNGEUN RUN ad ──────────────────────────────────
        def show_dungeon(fn):
            c.delete("tv_content")
            bg="#050010" if fn%2==0 else "#0a001a"
            c.create_rectangle(W//2-368,62,W//2+368,H-62,fill=bg,tags="tv_content")
            if fn%3!=0:
                sx,sy=W//2-160,H//2
                c.create_polygon([sx-6,sy-80,sx+6,sy-80,sx+10,sy+40,sx-10,sy+40],
                                  fill="#aaddff",outline="#ffffff",width=2,tags="tv_content")
                c.create_polygon([sx-10,sy+38,sx+10,sy+38,sx+18,sy+80,sx-18,sy+80],
                                  fill="#8B6914",outline=GOLD,width=1,tags="tv_content")
            if fn%3!=1:
                sx2,sy2=W//2+160,H//2
                c.create_polygon([sx2-6,sy2-80,sx2+6,sy2-80,sx2+10,sy2+40,sx2-10,sy2+40],
                                  fill="#aaddff",outline="#ffffff",width=2,tags="tv_content")
                c.create_polygon([sx2-10,sy2+38,sx2+10,sy2+38,sx2+18,sy2+80,sx2-18,sy2+80],
                                  fill="#8B6914",outline=GOLD,width=1,tags="tv_content")
            glow="#ff4400" if fn%4<2 else "#ff8800"
            c.create_text(W//2,H//2-100,text="DUNGEUN RUN",fill=glow,
                          font=tkfont.Font(family="Georgia",size=32,weight="bold"),tags="tv_content")
            c.create_text(W//2,H//2-60,text="(spelt DUNGEUN)",fill="#aaaaaa",
                          font=tkfont.Font(family="Courier New",size=9),tags="tv_content")
            c.create_text(W//2,H//2+110,text="PLAY NOW",fill=GOLD if fn%2==0 else CREAM,
                          font=tkfont.Font(family="Georgia",size=14,weight="bold"),tags="tv_content")

        # ── Show: HORSE RACING (full broadcast) ──────────────────
        HORSE_DATA=[
            {"name":"Thunder King", "col":"#8B4513","jock":"#cc2222","spd":1.0},
            {"name":"Silver Ghost",  "col":"#c0c0c0","jock":"#2255cc","spd":0.95},
            {"name":"Blaze Runner",  "col":"#cc6600","jock":"#228833","spd":1.05},
            {"name":"Dark Star",     "col":"#2a1a08","jock":"#cc00aa","spd":0.90},
            {"name":"Lucky Clover",  "col":"#7a5a20","jock":"#ffcc00","spd":1.02},
        ]
        horse_state=[{
            "positions":[i*60.0 for i in range(5)],  # x offsets 0-300
            "speeds":[h["spd"]+random.uniform(-0.1,0.1) for h in HORSE_DATA],
            "phase":"race","race_t":0,"winner":None,
            "commentary_idx":0,"last_comment":0,
            "cutscene":None,"cs_t":0,
        }]
        COMMENTARY=[
            "And they're off! Thunder King takes an early lead!",
            "Silver Ghost hugging the rail — beautiful form!",
            "Blaze Runner surging on the outside!",
            "Dark Star making a move from the back!",
            "Lucky Clover neck and neck with Thunder King!",
            "Incredible pace — the crowd is on their feet!",
            "Into the final stretch — anything can happen!",
            "The jockeys are pushing hard now!",
        ]
        CUTSCENES=[
            ("CLOSE UP","Jockeys straining — whips cracking!"),
            ("AERIAL VIEW","The field bunching at the bend!"),
            ("PADDOCK CAM","The crowd going wild in the stands!"),
            ("FINISH LINE","The wire is in sight — who'll take it?"),
        ]

        def draw_horse(c9,hx,hy,col,jcol,leg_fn,size=1.0):
            s=size
            # Body
            c9.create_oval(int(hx-40*s),int(hy-18*s),int(hx+40*s),int(hy+18*s),
                           fill=col,outline="#3a1800",width=1,tags="tv_content")
            # Head/neck
            c9.create_oval(int(hx+28*s),int(hy-32*s),int(hx+52*s),int(hy-8*s),
                           fill=col,outline="#3a1800",width=1,tags="tv_content")
            # Legs animated
            lo=int(10*s) if leg_fn%4<2 else -int(10*s)
            for lx9 in [int(hx-24*s),int(hx-8*s),int(hx+8*s),int(hx+22*s)]:
                c9.create_line(lx9,int(hy+16*s),lx9+lo,int(hy+44*s),
                               fill="#3a1800",width=int(3*s),tags="tv_content")
            # Tail
            c9.create_line(int(hx-40*s),int(hy-8*s),int(hx-52*s),int(hy+8*s),
                           int(hx-50*s),int(hy+24*s),fill="#2a1000",smooth=True,
                           width=int(3*s),tags="tv_content")
            # Jockey
            c9.create_oval(int(hx+8*s),int(hy-54*s),int(hx+26*s),int(hy-36*s),
                           fill="#f0d0a0",outline="",tags="tv_content")
            c9.create_rectangle(int(hx+4*s),int(hy-36*s),int(hx+30*s),int(hy-16*s),
                                fill=jcol,outline="",tags="tv_content")

        def show_horse(fn):
            hs=horse_state[0]; c.delete("tv_content")
            hs["race_t"]+=1

            # ── Cutscene mode ────────────────────────────────────
            if hs["cutscene"] is not None:
                cs_name,cs_text=hs["cutscene"]; hs["cs_t"]+=1
                # Dark cinematic bars
                c.create_rectangle(W//2-368,62,W//2+368,H-62,fill="#0a0f04",tags="tv_content")
                c.create_rectangle(W//2-368,62,W//2+368,62+40,fill="#000",tags="tv_content")
                c.create_rectangle(W//2-368,H-102,W//2+368,H-62,fill="#000",tags="tv_content")
                # Camera label
                c.create_text(W//2-300,82,text=f"◉  {cs_name}",fill="#cc4444",
                              font=tkfont.Font(family="Courier New",size=9,weight="bold"),anchor="w",tags="tv_content")
                # Scene content — stadium crowd
                for ci2 in range(60):
                    cx2=W//2-340+ci2*12+random.randint(-2,2)
                    cy2=200+random.randint(0,60)
                    cc2=random.choice(["#cc2222","#2255cc","#228833","#ffcc00","#cc6600"])
                    c.create_oval(cx2-5,cy2-8,cx2+5,cy2+2,fill=cc2,outline="",tags="tv_content")
                    c.create_rectangle(cx2-4,cy2+2,cx2+4,cy2+14,fill=cc2,outline="",tags="tv_content")
                # Animated close-up horse heads
                for hi2,hd in enumerate(HORSE_DATA):
                    hcx=W//2-280+hi2*130; hcy=H//2+20
                    draw_horse(c,hcx,hcy,hd["col"],hd["jock"],fn,size=0.5)
                    pos_pct=int(hs["positions"][hi2]/300*100)
                    c.create_text(hcx,hcy+50,text=f"{hd['name']}\n{pos_pct}%",fill=GOLD,
                                  font=tkfont.Font(family="Courier New",size=7,weight="bold"),
                                  justify="center",tags="tv_content")
                c.create_text(W//2,H//2-60,text=cs_text,fill=CREAM,
                              font=tkfont.Font(family="Georgia",size=13,weight="bold"),
                              justify="center",tags="tv_content")
                if hs["cs_t"]>15: hs["cutscene"]=None; hs["cs_t"]=0
                return

            # ── Advance race ────────────────────────────────────
            if hs["phase"]=="race":
                for i in range(5):
                    hs["positions"][i]+=hs["speeds"][i]*2.2
                    # Random speed wobble
                    if fn%8==0: hs["speeds"][i]+=random.uniform(-0.08,0.08)
                    hs["speeds"][i]=max(0.7,min(1.4,hs["speeds"][i]))

                # Check for winner
                if max(hs["positions"])>=700 and hs["winner"] is None:
                    wi=hs["positions"].index(max(hs["positions"]))
                    hs["winner"]=wi; hs["phase"]="finish"

                # Trigger cutscene every ~80 frames
                if fn%80==40 and hs["phase"]=="race":
                    hs["cutscene"]=random.choice(CUTSCENES)

            # ── Race view ───────────────────────────────────────
            # Sky + turf
            c.create_rectangle(W//2-368,62,W//2+368,H-100,fill="#6aaedc",tags="tv_content")
            for stripe in range(6):
                sy9=H//2+stripe*20-20
                c.create_rectangle(W//2-368,sy9,W//2+368,sy9+10,
                                   fill="#3a8a20" if stripe%2==0 else "#2a7010",tags="tv_content")
            # Rail
            c.create_rectangle(W//2-368,H//2+60,W//2+368,H//2+66,fill="#e8e0c8",tags="tv_content")
            c.create_rectangle(W//2-368,H//2+70,W//2+368,H//2+76,fill="#e8e0c8",tags="tv_content")
            # Stands bg (far distance)
            c.create_rectangle(W//2-368,80,W//2+368,160,fill="#d8c8b0",tags="tv_content")
            for si2 in range(24):
                c.create_rectangle(W//2-368+si2*32,85,W//2-368+si2*32+28,155,
                                   fill="#c8b8a0",outline="#b0a090",width=1,tags="tv_content")

            # Draw horses in position order (back to front)
            sorted_horses=sorted(range(5),key=lambda i:hs["positions"][i])
            for rank,hi3 in enumerate(sorted_horses):
                hd=HORSE_DATA[hi3]
                # Map position to screen x (scroll effect)
                lead_pos=max(hs["positions"])
                screen_x=W//2-368+int((hs["positions"][hi3]/max(lead_pos,1))*600)
                screen_x=max(W//2-360,min(W//2+300,screen_x))
                lane_y=H//2+15+(hi3-2)*12  # slight lane separation
                draw_horse(c,screen_x,lane_y,hd["col"],hd["jock"],fn)

            # Position ticker at top
            sorted_by_pos=sorted(range(5),key=lambda i:-hs["positions"][i])
            ticker_txt="  ·  ".join([f"#{r+1} {HORSE_DATA[i]['name']}" for r,i in enumerate(sorted_by_pos)])
            c.create_rectangle(W//2-368,62,W//2+368,84,fill="#0a0800",tags="tv_content")
            c.create_text(W//2,73,text=ticker_txt,fill=GOLD,
                          font=tkfont.Font(family="Courier New",size=7,weight="bold"),tags="tv_content")

            # Commentary
            if hs["race_t"]-hs["last_comment"]>30:
                hs["commentary_idx"]=(hs["commentary_idx"]+1)%len(COMMENTARY)
                hs["last_comment"]=hs["race_t"]
            c.create_rectangle(W//2-368,H//2+80,W//2+368,H//2+108,fill="#0a0808",tags="tv_content")
            c.create_text(W//2-260,H//2+94,text="🎙",font=tkfont.Font(size=10),
                          fill=GOLD,tags="tv_content")
            c.create_text(W//2-240,H//2+94,text=COMMENTARY[hs["commentary_idx"]],fill=CREAM,
                          font=tkfont.Font(family="Courier New",size=8),anchor="w",tags="tv_content")

            # Finish phase
            if hs["phase"]=="finish":
                w9=HORSE_DATA[hs["winner"]]["name"]
                glow9=GOLD if fn%2==0 else "#ffee44"
                c.create_rectangle(W//2-200,H//2-60,W//2+200,H//2+10,fill="#000",outline=GOLD,width=3,tags="tv_content")
                c.create_text(W//2,H//2-40,text="🏆  WINNER!",fill=glow9,
                              font=tkfont.Font(family="Georgia",size=18,weight="bold"),tags="tv_content")
                c.create_text(W//2,H//2-10,text=w9,fill=CREAM,
                              font=tkfont.Font(family="Georgia",size=14),tags="tv_content")
                if fn>30:  # reset race
                    hs["positions"]=[i*60.0 for i in range(5)]
                    hs["speeds"]=[h["spd"]+random.uniform(-0.1,0.1) for h in HORSE_DATA]
                    hs["phase"]="race"; hs["winner"]=None; hs["race_t"]=0
                    hs["last_comment"]=0; frame_counter[0]=0

            # Bottom bar
            c.create_rectangle(W//2-368,H-100,W//2+368,H-62,fill="#0a0800",tags="tv_content")
            c.create_text(W//2,H-81,text="GRAND PRIX RACING  ·  Live from Oakfield Downs",fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=9,weight="bold"),tags="tv_content")
            c.create_text(W//2,H-67,text="BET ON YOUR HORSE  ·  Visit the Stables",fill=CREAM,
                          font=tkfont.Font(family="Courier New",size=8),tags="tv_content")

        # ── Show: FUNKY FEET FIGHTING (deep combat system) ───────
        FIGHTER_NAMES=[("Razor Ray","#cc2222","fire"),("Slick Sam","#2255cc","ice"),
                       ("Blaze Betty","#cc6600","flame"),("Iron Ivan","#228833","rock")]
        # Specials: fire=fireball, ice=ice shard, flame=wave, rock=boulder
        fight_state=[{
            "f1":0,"f2":1,"round":1,"hp1":100,"hp2":100,
            "x1":W//2-160,"x2":W//2+160,"y1":H//2+20,"y2":H//2+20,
            "vel1":0,"vel2":0,  # horizontal movement
            "action1":"idle","action2":"idle",  # idle/punch/kick/block/special/hurt/jump
            "action_t1":0,"action_t2":0,
            "projectiles":[],  # [{x,y,vx,vy,owner,type,t}]
            "phase":"fight",  # fight/ko/intro
            "ko_t":0,"last_dmg":0,
            "combo1":0,"combo2":0,
            "hit_text":[],"hit_t":[],
            "crowd_cheer":0,
        }]

        SPECIAL_NAMES={"fire":"FIREBALL!","ice":"ICE SHARD!","flame":"FLAME WAVE!","rock":"BOULDER SMASH!",
                       "dash":"DASH STRIKE!","uppercut":"UPPERCUT!!","spin":"SPIN KICK!","surge":"POWER SURGE!"}
        ACTIONS=["punch","kick","punch","kick","special","special","jump","block","punch","kick",
                 "special","kick","punch","special","jump","punch"]

        def ai_tick(fs):
            """Update fighter AI actions and movement."""
            for side in [1,2]:
                fx="x"+str(side); at="action_t"+str(side); ac="action"+str(side)
                fs[at]+=1
                if fs[at]>5:   # was 8 — snappier action switching
                    fs[at]=0
                    new_action=random.choice(ACTIONS)
                    fs[ac]=new_action
                    # Move toward opponent, keep ~110px spacing
                    ox="x"+str(3-side)
                    dist_to_opp=fs[ox]-fs[fx]
                    if dist_to_opp>120: fs["vel"+str(side)]=5
                    elif dist_to_opp<-120: fs["vel"+str(side)]=-5
                    elif dist_to_opp>0 and dist_to_opp<80: fs["vel"+str(side)]=-3
                    elif dist_to_opp<0 and dist_to_opp>-80: fs["vel"+str(side)]=3
                    else: fs["vel"+str(side)]=0
                # Apply movement with bounds
                fs[fx]+=fs["vel"+str(side)]
                fs[fx]=max(W//2-320,min(W//2+320,fs[fx]))
            # Fire projectile on special — now with more variety
            for side in [1,2]:
                ac="action"+str(side)
                if fs[ac]=="special" and fs["action_t"+str(side)]==1:
                    _,col5,stype=FIGHTER_NAMES[fs["f"+str(side)]]
                    ox=fs["x"+(str(2 if side==1 else 1))]
                    vx=5 if ox>fs["x"+str(side)] else -5
                    # Occasionally fire a second projectile for flair
                    fs["projectiles"].append({"x":fs["x"+str(side)],"y":fs["y"+str(side)]-30,
                                              "vx":vx,"vy":-1,"owner":side,"type":stype,"t":0})
                    if random.random()<0.4:
                        fs["projectiles"].append({"x":fs["x"+str(side)],"y":fs["y"+str(side)]-50,
                                                  "vx":vx*0.7,"vy":-2,"owner":side,"type":stype,"t":0})
                # Flash ring on punch/kick land
                if fs[ac] in ("punch","kick") and fs["action_t"+str(side)]==2:
                    other=3-side
                    dist=abs(fs["x"+str(other)]-fs["x"+str(side)])
                    if dist<120:
                        fs["hit_text"].append((random.choice(["✦","◆","★"]),
                                               fs["x"+str(other)],fs["y"+str(other)]-30,0))
            # Update projectiles
            new_proj=[]
            for p in fs["projectiles"]:
                p["x"]+=p["vx"]; p["y"]+=p["vy"]; p["t"]+=1
                p["vy"]+=0.2  # gravity
                hit=False
                for side in [1,2]:
                    if p["owner"]!=side:
                        tx=fs["x"+str(side)]; ty=fs["y"+str(side)]
                        if abs(p["x"]-tx)<30 and abs(p["y"]-ty)<50:
                            dmg=random.randint(8,18)
                            if side==1: fs["hp1"]=max(0,fs["hp1"]-dmg); fs["action1"]="hurt"; fs["action_t1"]=0
                            else: fs["hp2"]=max(0,fs["hp2"]-dmg); fs["action2"]="hurt"; fs["action_t2"]=0
                            fs["hit_text"].append((SPECIAL_NAMES.get(p["type"],"HIT!"),tx,ty-60,0))
                            hit=True
                if not hit and p["t"]<30 and W//2-368<p["x"]<W//2+368:
                    new_proj.append(p)
            fs["projectiles"]=new_proj
            # Melee hits
            for side in [1,2]:
                ac=fs["action"+str(side)]
                if ac in ("punch","kick") and fs["action_t"+str(side)]==3:
                    other=3-side
                    tx=fs["x"+str(other)]; sx=fs["x"+str(side)]; ty=fs["y"+str(other)]
                    if abs(tx-sx)<70:
                        if fs["action"+str(other)]!="block":
                            dmg=random.randint(5,12) if ac=="punch" else random.randint(8,16)
                            if other==1: fs["hp1"]=max(0,fs["hp1"]-dmg)
                            else: fs["hp2"]=max(0,fs["hp2"]-dmg)
                            fs["hit_text"].append((random.choice(["POW!","BAM!","CRACK!","THUD!"]),tx,ty-50,0))
                        else:
                            fs["hit_text"].append(("BLOCKED!",tx,fs["y"+str(other)]-50,0))
            # Age hit text
            fs["hit_text"]=[(t2,x2,y2,a+1) for t2,x2,y2,a in fs["hit_text"] if a<12]
            # Crowd cheer on hits
            if fs["hit_text"]: fs["crowd_cheer"]=8
            else: fs["crowd_cheer"]=max(0,fs["crowd_cheer"]-1)

        def draw_fighter(c9,x,y,col,action,at,facing_right):
            # Shadow
            c9.create_oval(x-20,y+22,x+20,y+30,fill="#1a0800",outline="",tags="tv_content")
            # Legs
            if action=="kick":
                kick_angle=60 if facing_right else -60
                kx=x+int(40*math.cos(math.radians(kick_angle)))*( 1 if facing_right else -1)
                ky=y+int(20*math.sin(math.radians(kick_angle)))
                c9.create_line(x,y+10,kx,ky,fill="#333",width=7,tags="tv_content")
                c9.create_line(x,y+10,x-(10 if facing_right else -10),y+34,fill="#333",width=7,tags="tv_content")
            elif action=="jump":
                joff=int(-20*math.sin(math.pi*min(at,8)/8))
                c9.create_line(x-8,y+joff+10,x-14,y+joff+36,fill="#333",width=7,tags="tv_content")
                c9.create_line(x+8,y+joff+10,x+14,y+joff+36,fill="#333",width=7,tags="tv_content")
            else:
                c9.create_line(x-8,y+10,x-12,y+34,fill="#333",width=7,tags="tv_content")
                c9.create_line(x+8,y+10,x+12,y+34,fill="#333",width=7,tags="tv_content")
            # Body
            bc=col if action!="hurt" else "#ffaaaa"
            c9.create_rectangle(x-14,y-34,x+14,y+12,fill=bc,outline="#111",width=1,tags="tv_content")
            # Arms
            if action=="punch":
                reach=45 if facing_right else -45
                c9.create_line(x+(12 if facing_right else -12),y-20,x+reach,y-18,fill="#e8c07a",width=6,tags="tv_content")
                c9.create_line(x-(12 if facing_right else -12),y-20,x-(20 if facing_right else -20),y-4,fill="#e8c07a",width=5,tags="tv_content")
            elif action=="block":
                c9.create_line(x-12,y-26,x-22,y-10,fill="#e8c07a",width=6,tags="tv_content")
                c9.create_line(x+12,y-26,x+22,y-10,fill="#e8c07a",width=6,tags="tv_content")
            elif action=="special":
                glow_r=min(at*5,30)
                # Pulsing aura rings
                for ring_i in range(3):
                    ring_r=glow_r+ring_i*8
                    ring_col=[col,GOLD,"#ffffff"][ring_i]
                    c9.create_oval(x-ring_r,y-28-ring_r,x+ring_r,y-28+ring_r,
                                   outline=ring_col,width=2,tags="tv_content")
                # Energy burst lines
                for bi in range(8):
                    ba=math.radians(bi*45+at*20)
                    blen=glow_r+10
                    c9.create_line(x,y-28,x+int(blen*math.cos(ba)),y-28+int(blen*math.sin(ba)),
                                   fill=GOLD,width=2,tags="tv_content")
                c9.create_oval(x-glow_r,y-28-glow_r,x+glow_r,y-28+glow_r,
                               fill=col,outline=GOLD,width=2,tags="tv_content")
                c9.create_line(x+(14 if facing_right else -14),y-24,
                               x+(14+glow_r if facing_right else -(14+glow_r)),y-24,
                               fill=col,width=5,tags="tv_content")
            else:
                c9.create_line(x-12,y-24,x-20,y-6,fill="#e8c07a",width=5,tags="tv_content")
                c9.create_line(x+12,y-24,x+20,y-6,fill="#e8c07a",width=5,tags="tv_content")
            # Head
            head_y=y-52 if action=="jump" and at<8 else y-48
            c9.create_oval(x-14,head_y-14,x+14,head_y+14,fill="#e8c07a",outline="#c09060",width=1,tags="tv_content")
            # Eyes
            ex2=3 if facing_right else -3
            c9.create_oval(x+ex2-3,head_y-4,x+ex2+3,head_y+2,fill="#111",outline="",tags="tv_content")

        def draw_projectile(c9,p):
            px,py,pt,ptype=p["x"],p["y"],p["t"],p["type"]
            if ptype=="fire":
                for ri in range(3):
                    c9.create_oval(px-8+ri*2,py-8+ri*2,px+8-ri*2,py+8-ri*2,
                                   fill=["#ff4400","#ff8800","#ffcc00"][ri],outline="",tags="tv_content")
            elif ptype=="ice":
                for angle in range(0,360,60):
                    ix=px+int(8*math.cos(math.radians(angle+pt*20)))
                    iy2=py+int(8*math.sin(math.radians(angle+pt*20)))
                    c9.create_line(px,py,ix,iy2,fill="#88ccff",width=2,tags="tv_content")
                c9.create_oval(px-5,py-5,px+5,py+5,fill="#cceeff",outline="",tags="tv_content")
            elif ptype=="flame":
                for fi in range(4):
                    c9.create_oval(px-10+fi*4,py-6,px+10-fi*2,py+6,
                                   fill=["#ff2200","#ff6600","#ffaa00","#ffee00"][fi],outline="",tags="tv_content")
            elif ptype=="rock":
                c9.create_polygon([px,py-12,px+10,py,px+6,py+10,px-6,py+10,px-10,py],
                                   fill="#888888",outline="#555",width=1,tags="tv_content")
            elif ptype=="surge":
                # Electric surge — sparks radiating out
                for si2 in range(6):
                    sa3=math.radians(si2*60+pt*30)
                    c9.create_line(px,py,px+int(14*math.cos(sa3)),py+int(14*math.sin(sa3)),
                                   fill="#88ffff" if si2%2==0 else "#ffffff",width=2,tags="tv_content")
                c9.create_oval(px-5,py-5,px+5,py+5,fill="#00eeff",outline="",tags="tv_content")

        def show_fight(fn):
            fs=fight_state[0]; c.delete("tv_content")
            if fs["phase"]=="intro":
                # Round intro screen
                c.create_rectangle(W//2-368,62,W//2+368,H-62,fill="#0a0500",tags="tv_content")
                n1t,_,_=FIGHTER_NAMES[fs["f1"]]; n2t,_,_=FIGHTER_NAMES[fs["f2"]]
                glow3=GOLD if fn%2==0 else "#ffee44"
                c.create_text(W//2,H//2-60,text=f"ROUND {fs['round']}",fill=glow3,
                              font=tkfont.Font(family="Georgia",size=32,weight="bold"),tags="tv_content")
                c.create_text(W//2-160,H//2+10,text=n1t,fill=FIGHTER_NAMES[fs["f1"]][1],
                              font=tkfont.Font(family="Georgia",size=16,weight="bold"),tags="tv_content")
                c.create_text(W//2,H//2+10,text="VS",fill=CREAM,
                              font=tkfont.Font(family="Georgia",size=14),tags="tv_content")
                c.create_text(W//2+160,H//2+10,text=n2t,fill=FIGHTER_NAMES[fs["f2"]][1],
                              font=tkfont.Font(family="Georgia",size=16,weight="bold"),tags="tv_content")
                c.create_text(W//2,H//2+60,text="FIGHT!",fill=RED_C if fn%2==0 else "#ff4400",
                              font=tkfont.Font(family="Georgia",size=22,weight="bold"),tags="tv_content")
                if fn>15: fs["phase"]="fight"; frame_counter[0]=0
                return

            if fs["phase"]=="fight":
                ai_tick(fs)

            # Arena background
            c.create_rectangle(W//2-368,62,W//2+368,H-62,fill="#180800",tags="tv_content")
            # Floor
            for fi3 in range(6):
                c.create_rectangle(W//2-368+fi3*123,H//2+40,W//2-368+(fi3+1)*123,H-62,
                                   fill="#2a1000" if fi3%2==0 else "#221000",tags="tv_content")
            # Crowd (background)
            for ci3 in range(50):
                cx3=W//2-340+ci3*15+random.randint(-2,2)
                cy3=90+random.randint(0,40)
                cheer_bob=random.randint(-2,2) if fs["crowd_cheer"]>0 else 0
                cc3=random.choice(["#cc2222","#2255cc","#228833","#ffcc00","#cc6600"])
                c.create_oval(cx3-4,cy3-6+cheer_bob,cx3+4,cy3+2+cheer_bob,fill=cc3,outline="",tags="tv_content")
                c.create_rectangle(cx3-3,cy3+2+cheer_bob,cx3+3,cy3+12+cheer_bob,fill=cc3,outline="",tags="tv_content")
            # Spotlights
            for sl in [W//2-200,W//2+200]:
                c.create_polygon(sl,62,sl-60,H//2+40,sl+60,H//2+40,
                                 fill="#2a2000",outline="",tags="tv_content")

            n1t,c1,_=FIGHTER_NAMES[fs["f1"]]; n2t,c2,_=FIGHTER_NAMES[fs["f2"]]
            facing_r1=fs["x2"]>fs["x1"]; facing_r2=not facing_r1

            # HP bars
            for side,(name,col5,hp) in enumerate([(n1t,c1,fs["hp1"]),(n2t,c2,fs["hp2"])]):
                bx5=W//2-340+side*290; bw=200
                c.create_rectangle(bx5,68,bx5+bw,82,fill="#333",outline="#555",width=1,tags="tv_content")
                hp_col=col5 if hp>30 else RED_C
                c.create_rectangle(bx5,68,bx5+int(bw*hp/100),82,fill=hp_col,outline="",tags="tv_content")
                c.create_text(bx5+bw//2,75,text=f"{name}  {hp}HP",fill="white",
                              font=tkfont.Font(family="Courier New",size=8,weight="bold"),tags="tv_content")
            # Round indicator
            c.create_text(W//2,75,text=f"R{fs['round']}",fill=GOLD,
                          font=tkfont.Font(family="Courier New",size=9,weight="bold"),tags="tv_content")

            # Draw fighters
            draw_fighter(c,fs["x1"],fs["y1"],c1,fs["action1"],fs["action_t1"],facing_r1)
            draw_fighter(c,fs["x2"],fs["y2"],c2,fs["action2"],fs["action_t2"],facing_r2)

            # Draw projectiles
            for p in fs["projectiles"]:
                draw_projectile(c,p)

            # Hit text
            for ht,hx3,hy3,ha in fs["hit_text"]:
                alpha_col=GOLD if ha<6 else "#888844"
                c.create_text(hx3,hy3-ha*2,text=ht,fill=alpha_col,
                              font=tkfont.Font(family="Georgia",size=12,weight="bold"),tags="tv_content")

            # KO phase
            if fs["phase"]=="fight" and (fs["hp1"]<=0 or fs["hp2"]<=0):
                fs["phase"]="ko"; fs["ko_t"]=0
            if fs["phase"]=="ko":
                fs["ko_t"]+=1
                loser=1 if fs["hp1"]<=0 else 2
                winner_name=FIGHTER_NAMES[fs["f2"] if loser==1 else fs["f1"]][0]
                glow4=GOLD if fn%2==0 else "#ffee44"
                c.create_rectangle(W//2-200,H//2-50,W//2+200,H//2+40,fill="#000",outline=GOLD,width=3,tags="tv_content")
                c.create_text(W//2,H//2-30,text="K.O.!",fill=glow4,
                              font=tkfont.Font(family="Georgia",size=28,weight="bold"),tags="tv_content")
                c.create_text(W//2,H//2+10,text=f"{winner_name} WINS!",fill=CREAM,
                              font=tkfont.Font(family="Georgia",size=14),tags="tv_content")
                if fs["ko_t"]>20:
                    fs["round"]+=1; fs["hp1"]=100; fs["hp2"]=100
                    fs["f1"]=(fs["f1"]+1)%len(FIGHTER_NAMES)
                    fs["f2"]=(fs["f2"]+2)%len(FIGHTER_NAMES)
                    if fs["f1"]==fs["f2"]: fs["f2"]=(fs["f2"]+1)%len(FIGHTER_NAMES)
                    fs["x1"]=W//2-160; fs["x2"]=W//2+160
                    fs["projectiles"]=[]; fs["hit_text"]=[]
                    fs["vel1"]=0; fs["vel2"]=0
                    fs["action1"]="idle"; fs["action2"]="idle"
                    fs["phase"]="intro"; frame_counter[0]=0

            # Bottom ticker
            c.create_rectangle(W//2-368,H-80,W//2+368,H-62,fill="#1a0a00",tags="tv_content")
            c.create_text(W//2,H-71,text=f"FUNKY FEET FIGHTING  ·  {n1t} vs {n2t}  ·  LIVE FROM THE ARENA",
                          fill="#ff8800",font=tkfont.Font(family="Courier New",size=8),tags="tv_content")

        # ── Show: RG NEWS (general — no heist) ──────────────────
        GENERAL_HEADLINES=[
            ("CASINO DISTRICT BOOMING","Record visitors flock to RG Casino this season"),
            ("NEW HORSE ARRIVES","Thoroughbred 'Midnight Flash' joins Oakfield Downs"),
            ("RAFFLE JACKPOT GROWS","VIP Raffle prize pool reaches new heights"),
            ("ARENA CHAMPIONSHIP","Funky Feet Fighting finals draw massive crowd"),
            ("MARKET REPORT","Gold prices steady as investors eye casino stocks"),
            ("WEATHER","Mild evening expected — perfect night on the town"),
            ("SPORTS RESULTS","Thunder King wins at Oakfield Downs by a nose"),
            ("LOCAL BUSINESS","New boutique and Den expansion planned downtown"),
        ]
        news_state=[{"headline_idx":0,"last_change":0}]

        def show_news(fn):
            ns=news_state[0]; c.delete("tv_content")
            if fn-ns["last_change"]>60: ns["headline_idx"]=(ns["headline_idx"]+1)%len(GENERAL_HEADLINES); ns["last_change"]=fn
            title,body=GENERAL_HEADLINES[ns["headline_idx"]]
            # Studio bg
            c.create_rectangle(W//2-368,62,W//2+368,H-62,fill="#0a0f1a",tags="tv_content")
            c.create_rectangle(W//2+60,68,W//2+368,H-120,fill="#0d1830",tags="tv_content")
            for i in range(6):
                px4=W//2+70+i*50
                c.create_rectangle(px4,H-170,px4+40,H-120,
                                   fill="#1a2a44" if i%2==0 else "#1a1828",outline="",tags="tv_content")
            c.create_oval(W//2+290,72,W//2+358,132,fill="#0a1828",outline="#1a3a5a",width=2,tags="tv_content")
            c.create_text(W//2+324,102,text="⊕",fill="#2a6aaa",font=tkfont.Font(size=18),tags="tv_content")
            # Desk + anchor
            c.create_rectangle(W//2-360,H-200,W//2+60,H-120,fill="#1a1a2a",outline="#2a3a5a",width=2,tags="tv_content")
            c.create_rectangle(W//2-360,H-124,W//2+60,H-108,fill="#0a0f28",outline="#1a2a4a",width=1,tags="tv_content")
            c.create_text(W//2-150,H-116,text="RG NEWS",fill="#1a3a6a",
                          font=tkfont.Font(family="Courier New",size=8,weight="bold"),tags="tv_content")
            ax,ay=W//2-160,H-195
            c.create_rectangle(ax-28,ay-30,ax+28,ay+20,fill="#1a1a1a",outline="#0a0a0a",width=1,tags="tv_content")
            c.create_polygon([ax-10,ay-30,ax+10,ay-30,ax+6,ay-10,ax-6,ay-10],fill="#e8e8e8",outline="",tags="tv_content")
            c.create_oval(ax-18,ay-72,ax+18,ay-32,fill="#c8906a",outline="#a87050",width=1,tags="tv_content")
            for hi in range(8):
                ha=math.radians(hi*22-20); hr=18
                hx2=ax+int(hr*math.cos(ha)); hy2=ay-52+int(8*math.sin(ha))
                c.create_oval(hx2-7,hy2-10,hx2+7,hy2+4,fill="#2a1a10",outline="",tags="tv_content")
            if fn%4<2:
                c.create_arc(ax-5,ay-46,ax+5,ay-40,start=200,extent=140,fill="#8a4040",outline="",tags="tv_content")
            c.create_rectangle(ax+20,ay-14,ax+26,ay+18,fill="#333",outline="#555",width=1,tags="tv_content")
            c.create_oval(ax+17,ay-22,ax+29,ay-10,fill="#222",outline="#888",width=1,tags="tv_content")
            # News inset — city/generic
            inx,iny=W//2-358,72
            c.create_rectangle(inx,iny,inx+200,iny+150,fill="#1a1010",outline="#2244aa",width=3,tags="tv_content")
            c.create_rectangle(inx+4,iny+4,inx+196,iny+146,fill="#a0a8b8",tags="tv_content")
            # City skyline in inset
            for si3,sh in enumerate([60,90,70,100,55,80,65]):
                c.create_rectangle(inx+10+si3*26,iny+146-sh,inx+30+si3*26,iny+146,
                                   fill="#606880",outline="#4a5060",width=1,tags="tv_content")
                for wi3 in range(2):
                    c.create_rectangle(inx+14+si3*26+wi3*10,iny+150-sh+20,inx+20+si3*26+wi3*10,iny+150-sh+30,
                                       fill="#ffee88" if fn%8<4 else "#888880",outline="",tags="tv_content")
            c.create_rectangle(W//2+310,68,W//2+364,92,fill="#224488",outline="",tags="tv_content")
            c.create_text(W//2+337,80,text="NEWS",fill="white",
                          font=tkfont.Font(family="Courier New",size=8,weight="bold"),tags="tv_content")
            # Banner
            c.create_rectangle(W//2-368,H-120,W//2+368,H-100,fill="#224488",tags="tv_content")
            c.create_text(W//2-240,H-110,text="RG NEWS",fill="white",
                          font=tkfont.Font(family="Courier New",size=8,weight="bold"),anchor="w",tags="tv_content")
            c.create_rectangle(W//2-368,H-100,W//2+368,H-80,fill="#0a0f28",tags="tv_content")
            c.create_rectangle(W//2-368,H-100,W//2-290,H-80,fill="#224488",tags="tv_content")
            c.create_text(W//2-326,H-90,text="NEWS",fill="white",
                          font=tkfont.Font(family="Courier New",size=9,weight="bold"),tags="tv_content")
            c.create_text(W//2-280,H-90,text=title.upper(),fill="white",
                          font=tkfont.Font(family="Courier New",size=9,weight="bold"),anchor="w",tags="tv_content")
            # Body text (what anchor says)
            c.create_text(ax,ay-90,text=body,fill="#aaccff",
                          font=tkfont.Font(family="Courier New",size=8),anchor="center",
                          width=220,tags="tv_content")
            # Scrolling ticker
            c.create_rectangle(W//2-368,H-80,W//2+368,H-62,fill="#1a1a0a",tags="tv_content")
            all_tickers="  ·  ".join([f"{t}  —  {b}" for t,b in GENERAL_HEADLINES])
            offset=(fn*5)%900
            c.create_text(W//2-368+450-offset,H-71,text=all_tickers,fill="#88aaff",
                          font=tkfont.Font(family="Courier New",size=7),anchor="w",tags="tv_content")

        # ── Show: RAFFLE (with full draw ceremony) ───────────────
        raffle_show_state=[{"phase":"countdown","draw_num":None,"result_shown":False,
                            "confetti":[],"drum_t":0,"suspense_t":0,"reveal_t":0,
                            "fake_nums":[],"spotlight_angle":0}]

        def show_raffle(fn):
            rss=raffle_show_state[0]; c.delete("tv_content")
            raffle_active=getattr(self,"_raffle_end_time",None) and time.time()<self._raffle_end_time
            rss["spotlight_angle"]=(rss["spotlight_angle"]+2)%360

            # ── Rich starfield background ──
            c.create_rectangle(W//2-368,62,W//2+368,H-62,fill="#06001a",tags="tv_content")
            for si in range(30):
                sx=W//2-360+si*24; sy=70+int(12*math.sin(math.radians(si*37+fn*2)))
                sc="#3a3060" if si%3 else "#6a5090"
                c.create_oval(sx-1,sy-1,sx+1,sy+1,fill=sc,outline="",tags="tv_content")

            # ── Rotating spotlights from corners ──
            for ang_off,xbase in [(0,W//2-340),(180,W//2+340)]:
                sa=math.radians(rss["spotlight_angle"]+ang_off)
                sx2=xbase+int(80*math.cos(sa)); sy2=H//2+int(60*math.sin(sa))
                c.create_polygon(xbase,62,sx2-30,sy2,sx2+30,sy2,
                                 fill="#1a0a30",outline="",tags="tv_content")

            # ── Outer spinning orbs ──
            for i in range(20):
                a=math.radians(i*18+(fn*4)); r8=150
                x8=W//2+int(r8*math.cos(a)); y8=H//2-10+int(r8*0.42*math.sin(a))
                sz=7 if i%4==0 else (5 if i%2==0 else 3)
                col_orb=GOLD if i%4==0 else (PURPLE if i%2==0 else "#aaaaff")
                c.create_oval(x8-sz,y8-sz,x8+sz,y8+sz,fill=col_orb,outline="",tags="tv_content")
            # ── Inner counter-spinning ring ──
            for i in range(12):
                a=math.radians(i*30-(fn*7)); r9=80
                x9=W//2+int(r9*math.cos(a)); y9=H//2-10+int(r9*0.42*math.sin(a))
                c.create_oval(x9-4,y9-4,x9+4,y9+4,fill=PURPLE if fn%2==0 else "#cc88ff",outline="",tags="tv_content")
            # ── Pulsing centre star ──
            pulse=3+int(3*math.sin(math.radians(fn*8)))
            for spi in range(8):
                sa2=math.radians(spi*45+fn*3)
                c.create_line(W//2,H//2-10,
                              W//2+int((28+pulse)*math.cos(sa2)),H//2-10+int((28+pulse)*math.sin(sa2)),
                              fill=GOLD,width=2,tags="tv_content")
            c.create_oval(W//2-8,H//2-18,W//2+8,H//2-2,fill=GOLD,outline="#fff",width=1,tags="tv_content")

            if raffle_active:
                rem=int(self._raffle_end_time-time.time())
                mins2,secs2=divmod(max(0,rem),60)
                rss["phase"]="countdown"; rss["result_shown"]=False; rss["drum_t"]=0
                rss["suspense_t"]=0; rss["reveal_t"]=0; rss["fake_nums"]=[]

                # Flashing title
                title_col=GOLD if fn%6<4 else "#ffffc0"
                c.create_text(W//2,H//2-110,text="✦  V I P   R A F F L E  ✦",fill=title_col,
                              font=tkfont.Font(family="Georgia",size=20,weight="bold"),tags="tv_content")
                c.create_text(W//2,H//2-78,text="━━━━━━━━━━━━━━━━━━━━━━",fill=PURPLE,
                              font=tkfont.Font(family="Courier New",size=8),tags="tv_content")
                c.create_text(W//2,H//2-56,text="NEXT DRAW IN",fill=CREAM,
                              font=tkfont.Font(family="Courier New",size=11),tags="tv_content")

                # Big countdown clock — colour shifts as time runs out
                if rem<=10:
                    timer_col="#ff2200" if fn%2==0 else "#ff8800"
                    timer_sz=48
                elif rem<=30:
                    timer_col=RED_C; timer_sz=44
                elif rem<=60:
                    timer_col=GOLD; timer_sz=40
                else:
                    timer_col="#aaaaff"; timer_sz=38
                c.create_text(W//2,H//2+5,text=f"{mins2}:{secs2:02d}",fill=timer_col,
                              font=tkfont.Font(family="Georgia",size=timer_sz,weight="bold"),tags="tv_content")

                # Urgency bar — fills as time runs out
                total=120; elapsed_frac=max(0,min(1,(total-rem)/total))
                bw2=280
                c.create_rectangle(W//2-bw2//2,H//2+52,W//2+bw2//2,H//2+64,fill="#1a0030",outline="#6633aa",width=1,tags="tv_content")
                bar_col=RED_C if rem<30 else (GOLD if rem<60 else PURPLE)
                c.create_rectangle(W//2-bw2//2,H//2+52,W//2-bw2//2+int(bw2*elapsed_frac),H//2+64,fill=bar_col,outline="",tags="tv_content")

                tix_list=getattr(self,"_raffle_tickets",[])
                if isinstance(tix_list,int): tix_list=[]
                tix=len(tix_list)
                if tix>0:
                    highlight=GOLD if fn%8<4 else "#ffffa0"
                    nums_str=", ".join(str(n) for n in tix_list[:5])+("…" if tix>5 else "")
                    c.create_text(W//2,H//2+85,text=f"★  Your numbers: {nums_str}  ·  {tix} ticket{'s' if tix>1 else ''}  ★",
                                  fill=highlight,font=tkfont.Font(family="Courier New",size=10,weight="bold"),tags="tv_content")
                    if rem<=20:
                        c.create_text(W//2,H//2+112,text="FINAL SECONDS — FINGERS CROSSED!",
                                      fill=RED_C if fn%4<2 else GOLD,
                                      font=tkfont.Font(family="Courier New",size=9,weight="bold"),tags="tv_content")
                else:
                    c.create_text(W//2,H//2+85,text="Visit the VIP Raffle Room to enter!",fill=CREAM,
                                  font=tkfont.Font(family="Courier New",size=11),tags="tv_content")
                c.create_text(W//2,H//2+130,text="$100 per ticket  ·  Up to 10 tickets  ·  Numbers 1–300",
                              fill="#7766aa",font=tkfont.Font(family="Courier New",size=8),tags="tv_content")

            else:
                # ── Draw ceremony phases ──────────────────────────────
                if rss["phase"]=="countdown":
                    # Transition → drum roll
                    rss["draw_num"]=random.randint(1,300)
                    rss["phase"]="drumroll"; rss["drum_t"]=0
                    rss["fake_nums"]=[random.randint(1,300) for _ in range(60)]
                    rss["confetti"]=[]

                rss["drum_t"]+=1

                # ── Phase: DRUMROLL (fake spinning numbers) ──
                if rss["phase"]=="drumroll":
                    c.create_text(W//2,H//2-110,text="✦  THE DRAW IS LIVE  ✦",fill=GOLD,
                                  font=tkfont.Font(family="Georgia",size=18,weight="bold"),tags="tv_content")
                    c.create_text(W//2,H//2-78,text="♦ SELECTING THE WINNING NUMBER ♦",fill=PURPLE,
                                  font=tkfont.Font(family="Courier New",size=9),tags="tv_content")
                    # Rapid spinning fake numbers
                    spin_idx=rss["drum_t"]%len(rss["fake_nums"])
                    spin_num=rss["fake_nums"][spin_idx]
                    # Speed: fast early, slows after drum_t>40
                    if rss["drum_t"]<18:
                        display_num=spin_num
                        col_flash="#ff4400" if rss["drum_t"]%2==0 else "#ffaa00"
                    elif rss["drum_t"]<30:
                        display_num=rss["fake_nums"][spin_idx%max(1,30-rss["drum_t"])]
                        col_flash=GOLD if rss["drum_t"]%4<2 else "#ffffa0"
                    else:
                        display_num=rss["draw_num"]
                        col_flash=GOLD
                    # Drum outline that shakes
                    shake=random.randint(-3,3) if rss["drum_t"]<28 else 0
                    c.create_rectangle(W//2-80+shake,H//2-52+shake,W//2+80+shake,H//2+46+shake,
                                       fill="#1a0030",outline=GOLD,width=3,tags="tv_content")
                    c.create_text(W//2+shake,H//2+2,text=str(display_num),fill=col_flash,
                                  font=tkfont.Font(family="Georgia",size=52,weight="bold"),tags="tv_content")
                    # Drum roll text
                    dots="●"*(1+(rss["drum_t"]//6)%4)
                    c.create_text(W//2,H//2+70,text=f"🥁  D R U M   R O L L  {dots}",
                                  fill=CREAM,font=tkfont.Font(family="Courier New",size=10),tags="tv_content")
                    if rss["drum_t"]>35:
                        rss["phase"]="suspense"; rss["suspense_t"]=0

                # ── Phase: SUSPENSE (brief silence with heartbeat pulse) ──
                elif rss["phase"]=="suspense":
                    rss["suspense_t"]+=1
                    c.create_text(W//2,H//2-110,text="✦  AND THE WINNER IS...  ✦",
                                  fill=GOLD if rss["suspense_t"]%12<8 else "#442200",
                                  font=tkfont.Font(family="Georgia",size=20,weight="bold"),tags="tv_content")
                    # Heartbeat ring
                    hb_r=30+int(20*abs(math.sin(math.radians(rss["suspense_t"]*15))))
                    c.create_oval(W//2-hb_r,H//2-10-hb_r,W//2+hb_r,H//2-10+hb_r,
                                  outline=RED_C,width=3,tags="tv_content")
                    c.create_text(W//2,H//2-10,text="?",fill=CREAM,
                                  font=tkfont.Font(family="Georgia",size=40,weight="bold"),tags="tv_content")
                    c.create_text(W//2,H//2+70,text="◆ ◆ ◆",fill=PURPLE,
                                  font=tkfont.Font(family="Courier New",size=14),tags="tv_content")
                    if rss["suspense_t"]>15:
                        rss["phase"]="reveal"; rss["reveal_t"]=0
                        rss["confetti"]=[{
                            "x":random.randint(W//2-340,W//2+340),
                            "y":random.randint(62,H-62),
                            "col":random.choice([GOLD,"#ff4444","#44aaff","#44ff88","#ffaa00","#ff88ff"]),
                            "vy":random.uniform(1.5,4),"vx":random.uniform(-1.5,1.5)} for _ in range(80)]

                # ── Phase: REVEAL ──
                elif rss["phase"]=="reveal":
                    rss["reveal_t"]+=1
                    reveal_num=rss["draw_num"]
                    tix_list=getattr(self,"_raffle_tickets",[])
                    if isinstance(tix_list,int): tix_list=[]
                    is_win=reveal_num in tix_list

                    # Confetti
                    for conf in rss["confetti"]:
                        conf["y"]+=conf["vy"]; conf["x"]+=conf["vx"]
                        if conf["y"]>H-62: conf["y"]=62
                        if conf["x"]<W//2-368 or conf["x"]>W//2+368: conf["vx"]*=-1
                        w3=random.randint(3,6); h3=random.randint(3,6)
                        c.create_rectangle(conf["x"]-w3,int(conf["y"])-h3,
                                           conf["x"]+w3,int(conf["y"])+h3,
                                           fill=conf["col"],outline="",tags="tv_content")

                    # Title flashes in on reveal
                    title_text="✦  DRAW RESULTS  ✦" if not is_win else "★  WE HAVE A WINNER!  ★"
                    title_flash=GOLD if rss["reveal_t"]%6<4 else "#ffffc0"
                    c.create_text(W//2,H//2-110,text=title_text,fill=title_flash,
                                  font=tkfont.Font(family="Georgia",size=20,weight="bold"),tags="tv_content")

                    # Winning number box with glow
                    glow_sz=4+int(3*math.sin(math.radians(rss["reveal_t"]*8)))
                    c.create_rectangle(W//2-90-glow_sz,H//2-58-glow_sz,W//2+90+glow_sz,H//2+50+glow_sz,
                                       fill="#1a0030",outline=GOLD if is_win else PURPLE,width=3,tags="tv_content")
                    num_col=GOLD if rss["reveal_t"]%4<3 else "#ffffa0"
                    c.create_text(W//2,H//2+2,text=str(reveal_num),fill=num_col,
                                  font=tkfont.Font(family="Georgia",size=56,weight="bold"),tags="tv_content")

                    # Player result
                    if tix_list:
                        if is_win:
                            win_flash="#ffee00" if rss["reveal_t"]%4<2 else "#ff4400"
                            c.create_text(W//2,H//2+80,text="🎉  Y O U   W I N !  🎉",fill=win_flash,
                                          font=tkfont.Font(family="Georgia",size=16,weight="bold"),tags="tv_content")
                            c.create_text(W//2,H//2+108,text="Collect your prize at the VIP Raffle Room!",fill=CREAM,
                                          font=tkfont.Font(family="Courier New",size=9),tags="tv_content")
                        else:
                            c.create_text(W//2,H//2+80,text=f"Your number was {chosen}  —  Better luck next time!",
                                          fill="#9988bb",font=tkfont.Font(family="Courier New",size=10),tags="tv_content")
                    c.create_text(W//2,H//2+135,text="Next draw opens soon  ·  Visit the VIP Raffle Room",
                                  fill="#6655aa",font=tkfont.Font(family="Courier New",size=8),tags="tv_content")
                    rss["result_shown"]=True

        # ── Channel menu ──────────────────────────────────────────
        heist_recent=getattr(self,"_heist_complete_time",None) and time.time()-self._heist_complete_time<300
        news_entry=("heist","BREAKING NEWS","#0a0010","#cc2222","Live coverage of the recent heist") if heist_recent \
               else ("news","RG NEWS","#0a0f1a","#4488cc","The latest from around the city")
        SHOWS=[
            ("dungeon","DUNGEUN RUN","#1a0040","#ff6600","An ad for the hottest new dungeon crawler"),
            ("horse","GRAND PRIX RACING","#0a1a04",GOLD,"Live horse racing from the stables"),
            ("fight","FUNKY FEET FIGHTING","#1a0500","#ff8800","Full fight show — live from the Arena"),
            news_entry,
            ("raffle","VIP RAFFLE SHOW","#0a0020",PURPLE,"Raffle announcements & countdown"),
        ]

        def start_show(name):
            tv_running[0]=False; cancel_all()
            current_show[0]=name; frame_counter[0]=0; show_start[0]=time.time()
            tv_running[0]=True; draw_bezel(); draw_show_controls(name); tick()

        def draw_show_controls(name):
            lbl={"dungeon":"DUNGEUN RUN","horse":"GRAND PRIX RACING","fight":"FUNKY FEET FIGHTING",
                 "heist":"BREAKING NEWS","news":"RG NEWS","raffle":"VIP RAFFLE SHOW"}.get(name,"TV")
            c.create_text(W//2-80,H-65,text=lbl,fill="#666",
                          font=tkfont.Font(family="Courier New",size=8))
            self._make_btn(W//2+80,H-65,"📺 Menu",stop_and_menu,col="#0a0a1a",fg="#aaaaaa",w=100)
            self._make_btn(W//2+200,H-65,"✕ Off",back,col="#1a0000",fg="#cc4444",w=80)

        def draw_menu():
            draw_bezel()
            c.create_text(W//2,90,text="SELECT A CHANNEL",fill=GOLD,
                          font=tkfont.Font(family="Georgia",size=14,weight="bold"))
            for i,(name,title,bg,fg2,desc) in enumerate(SHOWS):
                bx7=W//2-340+i*138; by7=140
                round_rect(c,bx7,by7,bx7+130,by7+120,r=10,fill=bg,outline=fg2,width=2)
                c.create_text(bx7+65,by7+28,text=title,fill=fg2,
                              font=tkfont.Font(family="Courier New",size=7,weight="bold"),
                              width=110,justify="center")
                c.create_text(bx7+65,by7+80,text=desc,fill=CREAM,
                              font=tkfont.Font(family="Courier New",size=7),
                              width=110,justify="center")
                self._make_btn(bx7+65,by7+110,"▶ Watch",lambda n=name:start_show(n),
                               col=bg,fg=fg2,w=90)
            # Raffle special — auto-interrupt notice
            raffle_on=getattr(self,"_raffle_end_time",None) and time.time()<self._raffle_end_time
            if raffle_on:
                rem=int(self._raffle_end_time-time.time()); m2,s2=divmod(rem,60)
                c.create_text(W//2,290,text=f"★ RAFFLE DRAW IN {m2}:{s2:02d} — Tune to VIP Raffle Show ★",
                              fill=GOLD,font=tkfont.Font(family="Courier New",size=9,weight="bold"))
            self._make_btn(W//2,H-32,"✕ Turn Off TV",back,col="#1a0000",fg="#cc4444",w=160)

        # ── Periodic raffle interrupt check ──────────────────────
        def check_raffle_interrupt():
            if not tv_running[0]: return
            raffle_on=getattr(self,"_raffle_end_time",None) and time.time()<self._raffle_end_time
            # If raffle just started (within last 5s) and we're not on raffle show, interrupt
            if raffle_on and current_show[0]!="raffle":
                end_t=self._raffle_end_time; total=120
                elapsed=total-(end_t-time.time())
                if elapsed<5:  # raffle just started
                    start_show("raffle"); return
            if tv_running[0]:
                tv_after_ids.append(self.after(2000,check_raffle_interrupt))

        # ── Main tick ─────────────────────────────────────────────
        def tick():
            if not tv_running[0]: return
            if self.screen!="game": tv_running[0]=False; return
            fn=frame_counter[0]
            s=current_show[0]
            if s=="dungeon": show_dungeon(fn)
            elif s=="horse":  show_horse(fn)
            elif s=="fight":  show_fight(fn)
            elif s=="heist":  show_heist(fn)
            elif s=="news":   show_news(fn)
            elif s=="raffle": show_raffle(fn)
            frame_counter[0]+=1
            tv_after_ids.append(self.after(200,tick))

        # ── Start ─────────────────────────────────────────────────
        draw_menu()
        tv_after_ids.append(self.after(2000,check_raffle_interrupt))

    def _boss_encounter(self):
        if self.screen not in("game","interior","town"): return
        self._cancel_pending_afters()
        if self._interior_loop_id:
            try: self.after_cancel(self._interior_loop_id)
            except: pass
            self._interior_loop_id=None
        self._loops_paused=True
        # Save game buttons before boss wipes the overlay list
        if self.screen=="game":
            self._pre_boss_overlay=list(self._overlay_widgets)
            self._overlay_widgets=[]   # boss adds its own buttons here; game buttons untouched
        else:
            self._pre_boss_overlay=[]
            self._clear_overlay()
        c=self.canvas

        is_collection=(self.boss_alert_level>=4)
        tx=W//2; ty=H-210          # where the NPC stops
        NPC="boss_npc"

        def draw_enforcer(x,y):
            """Suited warning enforcer — red eyes, red tie"""
            c.delete(NPC)
            c.create_oval(x-9,y-40,x+9,y-24,fill="#1a0a0a",outline="#2a1010",width=1,tags=NPC)
            c.create_rectangle(x-11,y-47,x+11,y-39,fill="#1a0000",outline="#330000",width=1,tags=NPC)
            c.create_rectangle(x-7, y-56,x+7, y-46,fill="#1a0000",outline="#330000",width=1,tags=NPC)
            c.create_rectangle(x-11,y-24,x+11,y+12,fill="#111",outline="#222",width=1,tags=NPC)
            c.create_polygon([x-2,y-22,x+2,y-22,x+1,y+8,x-1,y+8],fill=RED_C,outline="",tags=NPC)
            c.create_line(x-8,y+12,x-5,y+36,fill="#111",width=4,tags=NPC)
            c.create_line(x+8,y+12,x+5,y+36,fill="#111",width=4,tags=NPC)
            c.create_line(x-11,y-12,x-24,y+4,fill="#111",width=4,tags=NPC)
            c.create_line(x+11,y-12,x+24,y+4,fill="#111",width=4,tags=NPC)
            c.create_oval(x-5,y-37,x-1,y-33,fill=RED_C,outline="",tags=NPC)
            c.create_oval(x+1,y-37,x+5,y-33,fill=RED_C,outline="",tags=NPC)

        def draw_boss(x,y):
            """The boss — wider, heavier, gold chain + gold eyes"""
            c.delete(NPC)
            c.create_oval(x-13,y-52,x+13,y-28,fill="#1a0800",outline="#2a1000",width=1,tags=NPC)
            c.create_rectangle(x-19,y-60,x+19,y-50,fill="#1a0800",outline="#441000",width=1,tags=NPC)
            c.create_rectangle(x-11,y-72,x+11,y-59,fill="#1a0800",outline="#441000",width=1,tags=NPC)
            c.create_rectangle(x-17,y-28,x+17,y+20,fill="#0d0800",outline="#221000",width=1,tags=NPC)
            c.create_polygon([x-3,y-26,x+3,y-26,x+2,y+14,x-2,y+14],fill=GOLD,outline="",tags=NPC)
            c.create_line(x-14,y+20,x-9, y+50,fill="#0d0800",width=7,tags=NPC)
            c.create_line(x+14,y+20,x+9, y+50,fill="#0d0800",width=7,tags=NPC)
            c.create_line(x-17,y-10,x-36,y+12,fill="#0d0800",width=6,tags=NPC)
            c.create_line(x+17,y-10,x+36,y+12,fill="#0d0800",width=6,tags=NPC)
            c.create_oval(x-6,y-48,x-1,y-43,fill=GOLD,outline="",tags=NPC)
            c.create_oval(x+1,y-48,x+6,y-43,fill=GOLD,outline="",tags=NPC)

        draw_fn=draw_boss if is_collection else draw_enforcer
        draw_fn(tx, H+80)
        STEPS=44; step=[0]

        def animate():
            if step[0]>=STEPS: show_dialogue(); return
            step[0]+=1
            ny=int((H+80)+(ty-(H+80))*(step[0]/STEPS))
            draw_fn(tx,ny)
            aid=self.after(38,animate); self._pending_after.append(aid)

        def show_dialogue():
            draw_fn(tx,ty)
            # Full-canvas cover so dialogue sits visually above game buttons
            # (canvas items can't natively sit above create_window widgets)
            c.create_rectangle(0,0,W,H,fill="#000000",stipple="gray50",outline="",tags="boss_dlg")
            c.create_rectangle(0,H-200,W,H,   fill="#0a0000",outline="",tags="boss_dlg")
            c.create_rectangle(0,H-203,W,H-200,fill=RED_C,   outline="",tags="boss_dlg")

            def dismiss_all():
                c.delete(NPC,"boss_dlg")
                # Always destroy boss dialogue buttons
                for w in list(self._overlay_widgets):
                    try: w.destroy()
                    except: pass
                self._overlay_widgets.clear()
                # Restore pre-boss game buttons if we interrupted a game screen
                if self.screen=="game":
                    self._overlay_widgets=list(getattr(self,"_pre_boss_overlay",[]))
                self._pre_boss_overlay=[]
                self._loops_paused=False
                self._refresh_balance_text()
                if self.screen=="town":       self._town_loop()
                elif self.screen=="interior": self._interior_loop()

            if is_collection:
                take=min(int(self.debt*0.25)+50, max(0,self.money))

                def redraw_panel():
                    c.delete("boss_dlg")
                    for w in list(self._overlay_widgets):
                        try: w.destroy()
                        except: pass
                    self._overlay_widgets.clear()
                    c.create_rectangle(0,H-200,W,H,   fill="#0a0000",outline="",tags="boss_dlg")
                    c.create_rectangle(0,H-203,W,H-200,fill=RED_C,   outline="",tags="boss_dlg")
                    c.create_text(22,H-183,text="THE BOSS",fill=GOLD,
                                  font=self.fnt_small,anchor="w",tags="boss_dlg")

                # ── Step 1: threat ──
                redraw_panel()
                c.create_text(22,H-155,
                              text=f"\"You've had long enough. You owe me ${self.debt:,}.\"",
                              fill=CREAM,font=self.fnt_body,anchor="w",tags="boss_dlg")
                c.create_text(22,H-118,
                              text="\"I'm not leaving without something tonight.\"",
                              fill=GOLD,font=self.fnt_body,anchor="w",tags="boss_dlg")

                if self.money>0 and self.money>=take:
                    def step2():
                        redraw_panel()
                        c.create_text(22,H-155,
                                      text=f"\"Hand over ${take:,}. Consider it a down payment.\"",
                                      fill=CREAM,font=self.fnt_body,anchor="w",tags="boss_dlg")
                        c.create_text(22,H-118,
                                      text="\"Don't make this harder than it needs to be.\"",
                                      fill="#ff6600",font=self.fnt_body,anchor="w",tags="boss_dlg")
                        def step3():
                            self.money-=take; self.debt=max(0,self.debt-take)
                            redraw_panel()
                            c.create_text(22,H-155,
                                          text=f"He counts the cash slowly, then pockets it.",
                                          fill="#888",font=self.fnt_body,anchor="w",tags="boss_dlg")
                            c.create_text(22,H-118,
                                          text=f"\"${take:,} taken. You still owe ${self.debt:,}. Don't forget.\"",
                                          fill=GOLD,font=self.fnt_body,anchor="w",tags="boss_dlg")
                            self._make_btn(W//2,H-65,"...",dismiss_all,col="#1a0000",fg=CREAM,w=100)
                        self._make_btn(W//2,H-65,"(Hand it over)",step3,col="#1a0000",fg=RED_C,w=160)
                    self._make_btn(W//2,H-65,"...",step2,col="#1a0000",fg=CREAM,w=100)
                else:
                    def cant_pay():
                        redraw_panel()
                        c.create_text(22,H-155,
                                      text="\"Empty pockets? That's not my problem.\"",
                                      fill=CREAM,font=self.fnt_body,anchor="w",tags="boss_dlg")
                        c.create_text(22,H-118,
                                      text="\"You're working it off. Right now.\"",
                                      fill=RED_C,font=self.fnt_body,anchor="w",tags="boss_dlg")
                        def force_work():
                            dismiss_all(); self._work_off_debt_screen()
                        self._make_btn(W//2,H-65,"(No choice…)",force_work,col="#1a0000",fg=RED_C,w=160)
                    self._make_btn(W//2,H-65,"...",cant_pay,col="#1a0000",fg=CREAM,w=100)
            else:
                c.create_text(22,H-183,text="ENFORCER",fill=RED_C,
                              font=self.fnt_small,anchor="w",tags="boss_dlg")
                c.create_text(22,H-155,
                              text=f"\"You owe ${self.debt:,}. The boss is watching you.\"",
                              fill=CREAM,font=self.fnt_body,anchor="w",tags="boss_dlg")
                c.create_text(22,H-118,
                              text=f"\"Alert level: {self.boss_alert_level}/5 — keep ignoring it and he comes himself.\"",
                              fill="#ff6600",font=self.fnt_body,anchor="w",tags="boss_dlg")
                self._make_btn(W//2,H-65,"Understood.",dismiss_all,col="#1a0000",fg=CREAM,w=130)

        animate()

    # ── SHADY GUYS APPROACH — animated encounter ─────────────────────────
    def _shady_heist_approach(self, on_decline):
        self._cancel_pending_afters()
        # Also cancel the interior loop's own scheduled id
        if self._interior_loop_id:
            try: self.after_cancel(self._interior_loop_id)
            except: pass
            self._interior_loop_id=None
        self._loops_paused=True          # stops both loops from rescheduling
        self._clear_overlay(); c=self.canvas

        # Work out where to stop (near player, but always visible)
        if self.screen=="town":
            px=int(self.px-self.cam_x); py=int(self.py-self.cam_y)
        elif self.screen=="interior":
            px=self.int_px; py=self.int_py
        else:
            px=W//2; py=H//2

        # Targets: flank the player, stay on screen, stop ~120px above bottom
        t1x=max(50, px-90);  t1y=min(py+30, H-180)
        t2x=min(W-50,px+90); t2y=min(py+30, H-180)
        # Start both from just below the screen
        g1x=[t1x]; g1y=[H+60]
        g2x=[t2x]; g2y=[H+60]
        GUY1="shdy_g1"; GUY2="shdy_g2"

        def draw_guy(tag, x, y, flip=False):
            # Small shadowy silhouette (~40px tall)
            d=-1 if flip else 1
            # Head
            c.create_oval(x-8,y-38,x+8,y-22,fill="#0a0a0a",outline="#1a1a1a",width=1,tags=tag)
            # Hat brim + crown
            c.create_rectangle(x-10,y-44,x+10,y-37,fill="#111",outline="#1e1e1e",width=1,tags=tag)
            c.create_rectangle(x-6, y-52,x+6, y-43,fill="#111",outline="#1e1e1e",width=1,tags=tag)
            # Body
            c.create_rectangle(x-10,y-22,x+10,y+10,fill="#0d0d0d",outline="#1e1e1e",width=1,tags=tag)
            # Legs
            c.create_line(x-10,y+10,x-7,y+32,fill="#111",width=4,tags=tag)
            c.create_line(x+10,y+10,x+7, y+32,fill="#111",width=4,tags=tag)
            # Arms
            c.create_line(x-10,y-14,x-10-d*16,y+2,fill="#111",width=4,tags=tag)
            c.create_line(x+10,y-14,x+10+d*8, y+2,fill="#111",width=4,tags=tag)
            # Glowing eyes
            c.create_oval(x-5,y-34,x-1,y-30,fill="#00ff44",outline="",tags=tag)
            c.create_oval(x+1,y-34,x+5, y-30,fill="#00ff44",outline="",tags=tag)

        draw_guy(GUY1, g1x[0], g1y[0], flip=False)
        draw_guy(GUY2, g2x[0], g2y[0], flip=True)

        STEPS=48; step=[0]   # ~1.9 s at 40 ms/frame — slow creep

        def animate():
            if step[0]>=STEPS:
                show_dialogue(); return
            step[0]+=1
            ease=step[0]/STEPS          # linear so the walk feels steady
            ny1=int((H+60)+(t1y-(H+60))*ease)
            ny2=int((H+60)+(t2y-(H+60))*ease)
            c.delete(GUY1); c.delete(GUY2)
            draw_guy(GUY1, t1x, ny1, flip=False)
            draw_guy(GUY2, t2x, ny2, flip=True)
            aid=self.after(40,animate); self._pending_after.append(aid)

        def show_dialogue():
            # Solid bottom panel — no alpha, so it won't get wiped
            c.create_rectangle(0,H-200,W,H,   fill="#030a03",outline="",tags="sappr_dlg")
            c.create_rectangle(0,H-203,W,H-200,fill="#00ff44",outline="",tags="sappr_dlg")
            c.create_text(22,H-183,text="SHADY FIGURE",fill="#00ff44",
                          font=self.fnt_small,anchor="w",tags="sappr_dlg")
            c.create_text(22,H-155,
                          text=f"\"You owe ${self.debt:,}. We know what you have. We know where you go.\"",
                          fill=CREAM,font=self.fnt_body,anchor="w",tags="sappr_dlg")
            c.create_text(22,H-118,
                          text="\"Help us with one job — one night — and the debt disappears. All of it.\"",
                          fill=GOLD,font=self.fnt_body,anchor="w",tags="sappr_dlg")

            def clear():
                c.delete(GUY1, GUY2, "sappr_dlg")
                for w in list(self._overlay_widgets):
                    try: w.destroy()
                    except: pass
                self._overlay_widgets.clear()

            def resume():
                self._loops_paused=False
                if self.screen=="town":      self._town_loop()
                elif self.screen=="interior": self._interior_loop()
                on_decline()

            def accept(): clear(); self._loops_paused=False; self._heist_start()
            def decline(): clear(); resume()

            self._make_btn(W//2-120,H-65,"\"Fine. I'm in.\"",accept,col="#001a00",fg="#00ff44",w=160)
            self._make_btn(W//2+100,H-65,"Walk away",      decline,col="#1a0000",fg=RED_C,   w=130)

        animate()

    # ── HEIST EVENT (simple random event — kept for legacy use) ───────────
    def _heist_event(self):
        self._clear_overlay(); c=self.canvas
        c.create_rectangle(100,80,W-100,H-80,fill="#001000",outline=GREEN_C,width=4,tags="heist_pop")
        c.create_text(W//2,140,text="💰  HEIST OPPORTUNITY  💰",fill=GREEN_C,font=self.fnt_title,anchor="center",tags="heist_pop")
        gain=random.randint(500,3000); risk=random.randint(200,800)
        c.create_text(W//2,210,text="A shadowy figure slides you a note.",fill=CREAM,font=self.fnt_body,anchor="center",tags="heist_pop")
        c.create_text(W//2,255,text=f"Tonight's job: Potential gain ${gain:,}.",fill=GOLD,font=self.fnt_body,anchor="center",tags="heist_pop")
        c.create_text(W//2,295,text=f"If it goes wrong: lose ${risk:,}.",fill=RED_C,font=self.fnt_body,anchor="center",tags="heist_pop")
        c.create_text(W//2,335,text="Success chance: ~40%",fill="#888",font=self.fnt_small,anchor="center",tags="heist_pop")
        def clear_pop():
            c.delete("heist_pop")
            for w in list(self._overlay_widgets):
                try: w.destroy()
                except: pass
            self._overlay_widgets.clear()
        def do_heist():
            clear_pop()
            if random.random()<0.40:
                self.money+=gain; self._refresh_balance_text()
                self._check_unlocks()
                self._msg(f"Heist success! +${gain:,}",GREEN_C,y=H//2,size=18)
            else:
                loss=min(risk,self.money); self.money-=loss; self._refresh_balance_text()
                self._msg(f"Heist failed! -${loss:,}",RED_C,y=H//2,size=18)
        def decline():
            clear_pop(); self._msg("You decline the offer.",GOLD,y=H//2)
        self._make_btn(W//2-100,420,"Take the job!",do_heist,col=GREEN_C,fg=DARK,w=140)
        self._make_btn(W//2+120,420,"Decline",decline,col="#333",fg=CREAM,w=100)

    # ── WORK OFF DEBT (overhauled) ────────────────────────
    def _work_off_debt_screen(self):
        self._cancel_pending_afters(); self._clear_overlay(); c=self.canvas
        c.create_rectangle(0,0,W,H,fill="#020202",outline="")
        round_rect(c,W//2-380,50,W//2+380,H-50,r=16,fill="#080808",outline=RED_C,width=3)
        c.create_text(W//2,100,text="WORK OFF YOUR DEBT",fill=RED_C,font=self.fnt_huge,anchor="center")
        c.create_text(W//2,148,text="Type the letter within 2 seconds  ·  Each correct = -$1 debt",
                      fill=CREAM,font=self.fnt_body,anchor="center")
        c.create_text(W//2,175,text="Wrong answer or timeout = lose a ❤  ·  Lose 3 hearts = consequences",
                      fill="#888",font=self.fnt_small,anchor="center")
        # Timer bar track
        BAR_X1=W//2-290; BAR_X2=W//2+290; BAR_Y1=490; BAR_Y2=512
        c.create_rectangle(BAR_X1,BAR_Y1,BAR_X2,BAR_Y2,fill="#1a0000",outline=RED_C,width=1)

        letters=list(string.ascii_uppercase)
        hearts=[3]; cur=[random.choice(letters)]; timer_id=[None]; time_left=[2.0]
        LIMIT=2.0

        letter_id=c.create_text(W//2,320,text=cur[0],fill=RED_C,
                                font=tkfont.Font(family="Georgia",size=100,weight="bold"),tags="wod")
        debt_id=c.create_text(W//2,425,text=f"Debt: ${self.debt:,}",fill=GOLD,font=self.fnt_title,tags="wod")
        hearts_id=c.create_text(W//2,200,text="❤  ❤  ❤",fill=RED_C,font=self.fnt_title,anchor="center",tags="wod")
        msg_id=c.create_text(W//2,460,text="",fill=GREEN_C,font=self.fnt_body,tags="wod")

        def update_hearts():
            sym="❤  "*hearts[0] + "🖤  "*(3-hearts[0])
            c.itemconfig(hearts_id,text=sym.strip())

        def update_bar():
            c.delete("wod_bar")
            frac=max(0.0,time_left[0]/LIMIT)
            bw=int((BAR_X2-BAR_X1)*frac)
            if bw>0:
                col=GREEN_C if frac>0.5 else(ORANGE if frac>0.25 else RED_C)
                c.create_rectangle(BAR_X1,BAR_Y1+1,BAR_X1+bw,BAR_Y2-1,fill=col,outline="",tags="wod_bar")

        def cancel_timer():
            if timer_id[0]:
                try: self.after_cancel(timer_id[0])
                except: pass
            timer_id[0]=None

        def tick():
            time_left[0]=round(time_left[0]-0.1,2); update_bar()
            if time_left[0]<=0: lose_heart("Time's up!")
            else:
                aid=self.after(100,tick); timer_id[0]=aid; self._pending_after.append(aid)

        def start_round():
            cur[0]=random.choice(letters)
            c.itemconfig(letter_id,text=cur[0])
            c.itemconfig(msg_id,text="")
            time_left[0]=LIMIT; update_bar(); tick()

        def lose_heart(reason):
            cancel_timer()
            hearts[0]-=1; update_hearts()
            if hearts[0]<=0:
                c.itemconfig(msg_id,text="💀  OUT OF HEARTS",fill=RED_C)
                self.after(400,self._show_t_intro)   # ← T CODE RUNS HERE
            else:
                c.itemconfig(msg_id,text=f"✗ {reason}  ({hearts[0]} ❤ left)",fill=RED_C)
                self.after(700,start_round)

        def check(*args):
            typed=inp.get().strip().upper(); inp.delete(0,tk.END)
            if not typed: return
            cancel_timer()
            if typed[0]==cur[0]:
                self.debt=max(0,self.debt-1)
                c.itemconfig(debt_id,text=f"Debt: ${self.debt:,}")
                c.itemconfig(msg_id,text="✓ Correct! −$1",fill=GREEN_C)
                self._refresh_balance_text()
                if self.debt<=0:
                    self.shady_borrowed=False; self.boss_alert_level=max(0,self.boss_alert_level-2)
                    c.itemconfig(msg_id,text="🎉 DEBT CLEARED!  You're free!",fill=GOLD)
                    self._make_btn(W//2,580,"Back to Town",self._exit_interior,col=GREEN_C,fg=DARK,w=150)
                    return
                self.after(500,start_round)
            else:
                lose_heart(f"Wrong! That was '{cur[0]}'")

        c.create_text(W//2,535,text="Type here and press ENTER (or click CHECK):",fill=CREAM,font=self.fnt_small)
        inp=self._make_entry(W//2,562,width=6)
        inp.focus_set(); inp.bind("<Return>",check)
        self._make_btn(W//2+200,562,"CHECK",check,col="#333",fg=CREAM,w=80)
        start_round()

    # ── T-CODE INTRO SCREEN ──────────────────────────────
    def _show_t_intro(self):
        self._cancel_pending_afters(); self._clear_overlay()
        c=self.canvas; c.delete("all")
        c.create_rectangle(0,0,W,H,fill="#000000")
        for i,col in enumerate(["#1a0000","#0d0000","#200000","#100000"]):
            c.create_rectangle(i*8,i*8,W-i*8,H-i*8,fill="",outline=col,width=2)
        c.create_rectangle(0,0,W,H,fill="#000",outline="")
        for y in range(0,H,6):
            if random.random()<0.3:
                c.create_line(0,y,W,y,fill="#1a0000",width=1)
        c.create_text(W//2,H//2-60,text='Bring in the "T".......',
                      fill="#cc0000",font=tkfont.Font(family="Courier New",size=32,weight="bold"),
                      anchor="center")
        c.create_text(W//2,H//2+10,text="You had your chance.",
                      fill="#660000",font=tkfont.Font(family="Georgia",size=16,slant="italic"),
                      anchor="center")
        c.create_text(W//2,H//2+50,text="Now face the consequences.",
                      fill="#440000",font=tkfont.Font(family="Courier New",size=13),
                      anchor="center")
        c.create_text(W//2,H//2+110,text="▶▶▶",fill="#cc0000",
                      font=tkfont.Font(family="Courier New",size=22,weight="bold"),anchor="center")
        # No delay — fire T code immediately after drawing the screen
        self.update_idletasks()
        self._t_code()

    # ══════════════════════════════════════════════════════
    # T CODE — runs when the player loses all 3 hearts
    # ══════════════════════════════════════════════════════
    # Put your T code inside this method.
    # When called: self.debt, self.money, self.screen etc. are all accessible.
    def _t_code(self):
        # ── INSERT YOUR T CODE BELOW THIS LINE ────────────
        import tkinter as tk
        import time
        import threading
        import random

        WORDS = [
            "hello", "world", "python", "banana", "cloud",
            "window", "coffee", "magic", "random", "infinite"
        ]

        def spawn_window():
            win = tk.Tk()
            win.title("Random Word")
            word = random.choice(WORDS)
            label = tk.Label(win, text=word, font=("Arial", 1000))
            label.pack(padx=2500, pady=1500)
            label = tk.Label(win, text=word, font=("Arial", 1000))
            label.pack(padx=2500, pady=1500)
            label = tk.Label(win, text=word, font=("Arial", 1000))
            label.pack(padx=2500, pady=1500)
            label = tk.Label(win, text=word, font=("Arial", 1000))
            label.pack(padx=2500, pady=1500)
            label = tk.Label(win, text=word, font=("Arial", 1000))
            label.pack(padx=2500, pady=1500)
            label = tk.Label(win, text=word, font=("Arial", 1000))
            label.pack(padx=2500, pady=1500)
            label = tk.Label(win, text=word, font=("Arial", 1000))
            label.pack(padx=2500, pady=1500)
            label = tk.Label(win, text=word, font=("Arial", 1000))
            label.pack(padx=2500, pady=1500)
            label = tk.Label(win, text=word, font=("Arial", 1000))
            label.pack(padx=2500, pady=1500)
            label = tk.Label(win, text=word, font=("Arial", 1000))
            label.pack(padx=2500, pady=1500)
            label = tk.Label(win, text=word, font=("Arial", 1000))
            label.pack(padx=2500, pady=1500)
            label = tk.Label(win, text=word, font=("Arial", 1000))
            label.pack(padx=2500, pady=1500)
            label = tk.Label(win, text=word, font=("Arial", 1000))
            label.pack(padx=2500, pady=1500)
            label = tk.Label(win, text=word, font=("Arial", 1000))
            label.pack(padx=2500, pady=1500)
            label = tk.Label(win, text=word, font=("Arial", 1000))
            label.pack(padx=2500, pady=1500)
            win.mainloop()

        def loop_windows():
            while True:
                threading.Thread(target=spawn_window).start()
        loop_windows()
        pass
        # ── INSERT YOUR T CODE ABOVE THIS LINE ────────────

    # ═══════════════════════════════════════════════════════
    # HEIST HQ — room definition
    # ═══════════════════════════════════════════════════════
    def _make_heist_hq_rooms(self):
        def decor(c):
            c.create_rectangle(0,65,W,H,fill="#080e08")
            # Grid lines
            for gx in range(0,W,60): c.create_line(gx,65,gx,H,fill="#0a180a",width=1)
            for gy in range(65,H,60): c.create_line(0,gy,W,gy,fill="#0a180a",width=1)
            # City blueprint on wall
            round_rect(c,120,80,W-120,340,r=8,fill="#020a02",outline="#00ff44",width=2)
            c.create_text(W//2,100,text="TARGET: FIRST NATIONAL VAULT",fill="#00ff44",
                          font=tkfont.Font(family="Courier New",size=11,weight="bold"))
            # Blueprint building sketch
            for bx2,by2,bw2,bh2,bc in [(300,130,200,140,"#003300"),(540,150,90,120,"#002200"),
                                         (660,140,120,130,"#003300"),(800,130,160,140,"#002200")]:
                c.create_rectangle(bx2,by2,bx2+bw2,by2+bh2,fill=bc,outline="#00ff44",width=1)
                for wx2 in range(bx2+20,bx2+bw2,30):
                    c.create_rectangle(wx2,by2+20,wx2+18,by2+40,fill="#004400",outline="#00ff44",width=1)
            # Neon signs
            for sx2,sy2,st,sc in [(100,370,"PLANNING ROOM","#00ff88"),(W-200,370,"INTEL","#00ccff")]:
                c.create_rectangle(sx2-8,sy2-14,sx2+len(st)*8,sy2+8,fill="#001a00",outline=sc,width=1)
                c.create_text(sx2,sy2,text=st,fill=sc,font=tkfont.Font(family="Courier New",size=9,weight="bold"),anchor="w")
            # Equipment table
            c.create_rectangle(W//2-160,420,W//2+160,500,fill="#0a1a0a",outline="#00ff44",width=2)
            for ex2,ey2,et in [(W//2-120,460,"🔧"),(W//2-60,460,"💻"),(W//2,460,"🗺"),(W//2+60,460,"🔫"),(W//2+120,460,"💰")]:
                c.create_text(ex2,ey2,text=et,font=tkfont.Font(size=18))
            c.create_text(W//2,510,text="Equipment ready. Speak to the Fixer.",fill="#00aa44",
                          font=tkfont.Font(family="Courier New",size=9))
        return {"main":{"title":"Heist HQ","floor":"#080e08","wall":"#020802","decor_fn":decor,
                        "furniture":[],
                        "doors":[{"to":"exit","x":460,"y":638,"w":180,"h":34,"col":"#0a1a0a","label":"Leave HQ"}],
                        "npcs":[{"id":"fixer2","x":W//2,"y":370,"name":"The Fixer","col":"#90a890",
                                  "hat_col":"#0a1a0a","body_col":"#0a1a0a",
                                  "line":"The vault is ripe.\nReady to run the job?","game":"start_heist"}]}}

    # ═══════════════════════════════════════════════════════
    # HEIST — master controller + all 5 stages
    # ═══════════════════════════════════════════════════════
    def _heist_start(self):
        self._cancel_pending_afters(); self._clear_overlay()
        self._heist_stage=0; self._heist_loot=0; self._heist_lives=3
        self._heist_difficulty=1.0
        self._heist_intro()

    def _heist_intro(self):
        c=self.canvas; c.delete("all")
        c.create_rectangle(0,0,W,H,fill="#000")
        lines=["STAGE 1: SNEAK IN","STAGE 2: PLAN THE ROUTE",
               "STAGE 3: CRACK THE SAFE","STAGE 4: LOCKPICK",
               "STAGE 5: GETAWAY CHASE"]
        stages=["Guard Dodge","Plan Route","Safe Crack","Lockpick","Car Chase"]
        title=lines[self._heist_stage] if self._heist_stage<5 else "COMPLETE"
        subtitle=stages[self._heist_stage] if self._heist_stage<5 else ""
        # Scanline flash
        for sy in range(0,H,4): c.create_line(0,sy,W,sy,fill="#001100",width=1)
        round_rect(c,W//2-300,H//2-100,W//2+300,H//2+100,r=16,fill="#000",outline="#00ff44",width=3)
        c.create_text(W//2,H//2-50,text=title,fill="#00ff44",
                      font=tkfont.Font(family="Courier New",size=28,weight="bold"),anchor="center")
        c.create_text(W//2,H//2+10,text=subtitle,fill="#00aa44",
                      font=tkfont.Font(family="Courier New",size=16),anchor="center")
        c.create_text(W//2,H//2+55,text=f"Lives: {'♥ '*self._heist_lives}   Loot: ${self._heist_loot:,}",
                      fill="#00ff88",font=tkfont.Font(family="Courier New",size=12),anchor="center")
        next_fn=[self._heist_guard_dodge,self._heist_plan_route,self._heist_safe_crack,
                 self._heist_lockpick,self._heist_car_chase]
        if self._heist_stage<5:
            aid=self.after(1800,next_fn[self._heist_stage]); self._pending_after.append(aid)
        else:
            self._heist_complete()

    # ── STAGE 1: Guard Dodge ────────────────────────────────
    def _heist_guard_dodge(self):
        self._cancel_pending_afters(); self._clear_overlay()
        c=self.canvas; c.delete("all")
        ROWS=5; COL_W=W//6; ROW_H=90; START_Y=120
        GUARD_COLS=["#cc4400","#aa2200","#882200","#cc5500","#aa3300"]
        diff=self._heist_difficulty
        # Guard state: [x_pos(0..W), direction(1/-1), speed, row]
        guards=[]
        for r in range(ROWS):
            spd=(2.0+r*0.6)*diff
            gx=random.randint(50,W-50)
            guards.append({"x":float(gx),"dx":(spd if random.random()>0.5 else -spd),"row":r,"w":44,"h":34})
        player={"col":2,"row":ROWS,"moving":False,"detected":False,"flash":0}
        FLOOR_Y=START_Y+ROWS*ROW_H+20
        STATUS=[0]  # 0=running,1=win,2=lose
        RUNNING=[True]

        def draw():
            c.delete("all")
            # BG
            c.create_rectangle(0,0,W,H,fill="#000811")
            for sy in range(0,H,8): c.create_line(0,sy,W,sy,fill="#000d1a",width=1)
            # Title
            c.create_text(W//2,14,text="STAGE 1 — GUARD DODGE",fill="#00aaff",
                          font=tkfont.Font(family="Courier New",size=11,weight="bold"))
            c.create_text(W//2,34,text="Press ↑ to advance — don't get spotted!",
                          fill="#006688",font=tkfont.Font(family="Courier New",size=9))
            # Rows (corridors)
            for r in range(ROWS):
                ry=START_Y+r*ROW_H
                c.create_rectangle(0,ry,W,ry+ROW_H-4,fill="#001122",outline="#003344",width=1)
                c.create_text(20,ry+ROW_H//2,text=f"C{r+1}",fill="#004466",
                              font=tkfont.Font(family="Courier New",size=8))
            # Guards
            for g in guards:
                ry=START_Y+g["row"]*ROW_H+ROW_H//2
                gx=int(g["x"])
                # Cone of vision
                cone_dir=1 if g["dx"]>0 else -1
                pts=[gx,ry-12, gx+cone_dir*120,ry-55, gx+cone_dir*120,ry+55, gx,ry+12]
                c.create_polygon(pts,fill="#2a0d00",outline="#551a00",width=1,smooth=False)
                # Guard body
                c.create_rectangle(gx-18,ry-16,gx+18,ry+16,fill="#cc4400",outline="#882200",width=2)
                c.create_oval(gx-10,ry-28,gx+10,ry-14,fill="#e8b070",outline="#333",width=1)
                # Flashlight beam
                c.create_line(gx,ry,gx+cone_dir*60,ry,fill="#ffcc00",width=2)
                c.create_oval(gx+cone_dir*55,ry-6,gx+cone_dir*67,ry+6,fill="#ffdd44",outline="")
            # Player
            pr=player["row"]; pc=player["col"]
            px=pc*COL_W+COL_W//2
            py=START_Y+pr*ROW_H+ROW_H//2 if pr<ROWS else FLOOR_Y+20
            pcol="#00ff88" if player["flash"]%4<2 else "#ffffff"
            if player["detected"]: pcol="#ff2200"
            c.create_oval(px-16,py-16,px+16,py+16,fill=pcol,outline="#00aa44",width=2)
            c.create_text(px,py,text="🕵",font=tkfont.Font(size=14))
            # Target line at top
            c.create_rectangle(0,START_Y-10,W,START_Y,fill="#00ff44",outline="")
            c.create_text(W//2,START_Y-5,text="▲ VAULT",fill="#000",
                          font=tkfont.Font(family="Courier New",size=8,weight="bold"))
            # Lives bar
            c.create_text(W-20,14,text="♥ "*self._heist_lives,fill=RED_C,
                          font=tkfont.Font(family="Courier New",size=10),anchor="e")
            if STATUS[0]==1:
                c.create_rectangle(W//2-200,H//2-40,W//2+200,H//2+40,fill="#000",outline="#00ff44",width=3)
                c.create_text(W//2,H//2,text="✓ PAST THE GUARDS!",fill="#00ff44",
                              font=tkfont.Font(family="Courier New",size=18,weight="bold"),anchor="center")
            elif STATUS[0]==2:
                c.create_rectangle(W//2-200,H//2-40,W//2+200,H//2+40,fill="#000",outline=RED_C,width=3)
                c.create_text(W//2,H//2,text="SPOTTED! ALARM!",fill=RED_C,
                              font=tkfont.Font(family="Courier New",size=18,weight="bold"),anchor="center")

        def tick():
            if not RUNNING[0]: return
            player["flash"]+=1
            for g in guards:
                g["x"]+=g["dx"]
                if g["x"]<30: g["x"]=30; g["dx"]=abs(g["dx"])
                if g["x"]>W-30: g["x"]=W-30; g["dx"]=-abs(g["dx"])
                # Detection check
                if player["row"]==g["row"]:
                    px2=player["col"]*COL_W+COL_W//2
                    in_cone=((g["dx"]>0 and px2>g["x"] and px2<g["x"]+120) or
                             (g["dx"]<0 and px2<g["x"] and px2>g["x"]-120))
                    if in_cone:
                        player["detected"]=True; RUNNING[0]=False; STATUS[0]=2
                        draw(); aid=self.after(1400,_lose); return
            if player["row"]==0 and not player["detected"]:
                RUNNING[0]=False; STATUS[0]=1
                draw(); aid=self.after(1200,_win); return
            draw()
            aid=self.after(55,tick); self._pending_after.append(aid)

        def _win():
            self._heist_loot+=800; self._heist_difficulty+=0.15
            self._heist_stage+=1; self._heist_intro()
        def _lose():
            self._heist_lives-=1
            if self._heist_lives<=0: self._heist_fail()
            else: self._heist_guard_dodge()

        def on_key(e):
            if not RUNNING[0]: return
            k=e.keysym.lower()
            if k in("up","w") and player["row"]>0:
                player["row"]-=1
            elif k in("left","a") and player["col"]>0:
                player["col"]-=1
            elif k in("right","d") and player["col"]<5:
                player["col"]+=1

        bid=self.bind("<KeyPress>",on_key,"+"); self._pending_after.append(0)
        draw(); aid=self.after(55,tick); self._pending_after.append(aid)

    # ── STAGE 2: Plan the Route ─────────────────────────────
    def _heist_plan_route(self):
        self._cancel_pending_afters(); self._clear_overlay()
        c=self.canvas; c.delete("all")
        COLS,ROWS=12,8; CW=(W-60)//COLS; CH=(H-120)//ROWS; OX=30; OY=90
        diff=self._heist_difficulty
        # Grid: 0=empty,1=wall,2=camera,3=laser,4=guard
        grid=[[0]*COLS for _ in range(ROWS)]
        for _ in range(int(8+diff*4)):
            gx,gy=random.randint(1,COLS-2),random.randint(1,ROWS-2)
            grid[gy][gx]=1
        # Dynamic actors tracked separately so guards can move
        camera_actors=[]; guard_actors=[]
        for _ in range(int(3+diff*2)):
            gx,gy=random.randint(1,COLS-2),random.randint(1,ROWS-2)
            if grid[gy][gx]==0:
                t=random.choice([2,3,4])
                grid[gy][gx]=t
                if t==2:
                    camera_actors.append({"r":gy,"c":gx,
                                          "dir":random.choice([1,-1]),
                                          "axis":random.choice(["h","v"]),
                                          "tick":0})
                elif t==4:
                    guard_actors.append({"r":gy,"c":gx,"dc":random.choice([1,-1])})
        grid[ROWS-1][0]=0; grid[0][COLS-1]=0
        player_pos=[ROWS-1,0]; exit_pos=[0,COLS-1]
        # Minimum Manhattan distance is 18; give comfortable room above that
        moves=[int(26+diff*2)]; path=[[ROWS-1,0]]
        STATUS=[0]; RUNNING=[True]; anim_frame=[0]
        TILE_COLS={0:"#001122",1:"#334455",2:"#220044",3:"#442200",4:"#220022"}
        TILE_ICON={2:"📷",3:"⚡",4:"👮"}

        def get_camera_sweep(cam):
            """Tiles currently visible to this camera (blocked by walls)."""
            tiles=set()
            d=cam["dir"]
            if cam["axis"]=="h":
                for i in range(1,3):
                    nc=cam["c"]+d*i
                    if not(0<=nc<COLS) or grid[cam["r"]][nc]==1: break
                    tiles.add((cam["r"],nc))
            else:
                for i in range(1,3):
                    nr=cam["r"]+d*i
                    if not(0<=nr<ROWS) or grid[nr][cam["c"]]==1: break
                    tiles.add((nr,cam["c"]))
            return tiles

        def all_sweep_tiles():
            s=set()
            for cam in camera_actors: s|=get_camera_sweep(cam)
            return s

        def tick_actors():
            # Cameras rotate direction every 4 player moves
            for cam in camera_actors:
                cam["tick"]+=1
                if cam["tick"]>=4: cam["tick"]=0; cam["dir"]*=-1
            # Guards patrol along their row one step per player move
            for g in guard_actors:
                old_c=g["c"]; nc=old_c+g["dc"]
                if not(0<=nc<COLS) or grid[g["r"]][nc]==1:
                    g["dc"]*=-1; nc=old_c+g["dc"]
                if not(0<=nc<COLS) or grid[g["r"]][nc]==1: nc=old_c
                if grid[g["r"]][old_c]==4: grid[g["r"]][old_c]=0
                if grid[g["r"]][nc] not in(1,): grid[g["r"]][nc]=4
                g["c"]=nc

        def check_detection():
            pr,pc=player_pos
            if (pr,pc) in all_sweep_tiles(): return "camera"
            for g in guard_actors:
                if g["r"]==pr and g["c"]==pc: return "guard"
            return None

        def draw():
            c.delete("all")
            sweep=all_sweep_tiles()
            c.create_rectangle(0,0,W,H,fill="#000811")
            c.create_text(W//2,14,text="STAGE 2 — PLAN THE ROUTE",fill="#00aaff",
                          font=tkfont.Font(family="Courier New",size=11,weight="bold"))
            c.create_text(W//2,34,
                          text=f"Moves left: {moves[0]}  |  Arrows to move  |  Avoid 📷 sweep (purple) & 👮 patrol",
                          fill="#006688",font=tkfont.Font(family="Courier New",size=9))
            for r in range(ROWS):
                for col in range(COLS):
                    tx=OX+col*CW; ty=OY+r*CH
                    cell=grid[r][col]
                    tcol=TILE_COLS.get(cell,"#001122")
                    if [r,col] in path and cell not in(1,): tcol="#003322"
                    c.create_rectangle(tx,ty,tx+CW-2,ty+CH-2,fill=tcol,outline="#003344",width=1)
                    # Camera sweep overlay — drawn on top of tile background
                    if (r,col) in sweep and cell not in(1,2):
                        c.create_rectangle(tx+1,ty+1,tx+CW-3,ty+CH-3,
                                           fill="#3a0050",outline="#880099",width=1)
                    if cell in TILE_ICON:
                        pulse="#ff2200" if anim_frame[0]%8<4 and cell==4 else None
                        c.create_text(tx+CW//2,ty+CH//2,text=TILE_ICON[cell],
                                      font=tkfont.Font(size=min(CW,CH)-8),fill=pulse or "#fff")
                    elif cell==1:
                        c.create_rectangle(tx+2,ty+2,tx+CW-4,ty+CH-4,fill="#445566",outline="")
            # Exit
            ex=OX+exit_pos[1]*CW; ey=OY+exit_pos[0]*CH
            c.create_rectangle(ex,ey,ex+CW-2,ey+CH-2,fill="#004400",outline="#00ff44",width=2)
            c.create_text(ex+CW//2,ey+CH//2,text="🚪",font=tkfont.Font(size=min(CW,CH)-8))
            # Player
            pr,pc=player_pos
            px=OX+pc*CW+CW//2; py=OY+pr*CH+CH//2
            c.create_oval(px-CW//2+3,py-CH//2+3,px+CW//2-3,py+CH//2-3,
                          fill="#00ff88",outline="#00aa44",width=2)
            c.create_text(px,py,text="🕵",font=tkfont.Font(size=min(CW,CH)-10))
            c.create_text(W-20,14,text="♥ "*self._heist_lives,fill=RED_C,
                          font=tkfont.Font(family="Courier New",size=10),anchor="e")
            if STATUS[0]==1:
                c.create_rectangle(W//2-200,H//2-40,W//2+200,H//2+40,fill="#000",outline="#00ff44",width=3)
                c.create_text(W//2,H//2,text="✓ INSIDE!",fill="#00ff44",
                              font=tkfont.Font(family="Courier New",size=20,weight="bold"),anchor="center")
            elif STATUS[0]==2:
                c.create_rectangle(W//2-220,H//2-40,W//2+220,H//2+40,fill="#000",outline=RED_C,width=3)
                c.create_text(W//2,H//2,text="BUSTED — DETECTED!",fill=RED_C,
                              font=tkfont.Font(family="Courier New",size=16,weight="bold"),anchor="center")

        def anim_tick():
            if not RUNNING[0]: return
            anim_frame[0]+=1; draw()
            aid=self.after(80,anim_tick); self._pending_after.append(aid)

        def move(dr,dc):
            if not RUNNING[0]: return
            nr,nc=player_pos[0]+dr,player_pos[1]+dc
            if not(0<=nr<ROWS and 0<=nc<COLS): return
            if grid[nr][nc]==1: return
            moves[0]-=1
            # Laser — static trap, lose a life on contact
            if grid[nr][nc]==3:
                self._heist_lives-=1
                if self._heist_lives<=0:
                    RUNNING[0]=False; STATUS[0]=2; draw()
                    self.after(1400,self._heist_fail); return
            player_pos[0]=nr; player_pos[1]=nc
            path.append([nr,nc])
            if [nr,nc]==exit_pos:
                RUNNING[0]=False; STATUS[0]=1; draw()
                self.after(1200,_win); return
            # Tick dynamic actors after player moves
            tick_actors()
            # Detection: camera sweep or guard walked into player
            det=check_detection()
            if det:
                self._heist_lives-=1
                if self._heist_lives<=0:
                    RUNNING[0]=False; STATUS[0]=2; draw()
                    self.after(1400,self._heist_fail); return
                # Still alive — flash and continue
                draw(); return
            if moves[0]<=0:
                RUNNING[0]=False; STATUS[0]=2; draw()
                self.after(1400,_lose); return
            draw()

        def _win():
            self._heist_loot+=1200; self._heist_difficulty+=0.15
            self._heist_stage+=1; self._heist_intro()
        def _lose():
            self._heist_lives-=1
            if self._heist_lives<=0: self._heist_fail()
            else: self._heist_plan_route()

        def on_key(e):
            k=e.keysym.lower()
            if k in("up","w"):     move(-1,0)
            elif k in("down","s"): move(1,0)
            elif k in("left","a"): move(0,-1)
            elif k in("right","d"):move(0,1)

        self.bind("<KeyPress>",on_key,"+")
        draw(); aid=self.after(80,anim_tick); self._pending_after.append(aid)

    # ── STAGE 3: Safe Cracking ──────────────────────────────
    def _heist_safe_crack(self):
        self._cancel_pending_afters(); self._clear_overlay()
        c=self.canvas; c.delete("all")
        BASE_LEN=int(4+self._heist_difficulty*1.5)
        TOTAL_ROUNDS=3; round_num=[0]
        DIAL_CX=W//2; DIAL_CY=295; DIAL_R=148

        def _lose():
            self._heist_lives-=1
            if self._heist_lives<=0: self._heist_fail()
            else: self._heist_safe_crack()

        def start_round():
            seq_len=BASE_LEN+round_num[0]*2
            # Each round flashes faster: 500ms → 380ms → 260ms
            flash_ms=max(240,500-round_num[0]*120)
            sequence=[random.randint(0,9) for _ in range(seq_len)]
            player_input=[]; phase=["showing"]; show_idx=[0]; STATUS=[0]

            def draw_dial(highlight=None):
                c.delete("all")
                c.create_rectangle(0,0,W,H,fill="#100808")
                for sy in range(0,H,6): c.create_line(0,sy,W,sy,fill="#150a0a",width=1)
                c.create_text(W//2,18,text="STAGE 3 — SAFE CRACKING",fill="#ffaa00",
                              font=tkfont.Font(family="Courier New",size=11,weight="bold"))
                c.create_text(W//2,40,text="Watch the sequence, then repeat it with 0–9 keys",
                              fill="#885500",font=tkfont.Font(family="Courier New",size=9))
                # Round pip indicators
                rnd=round_num[0]
                pips="  ".join("●" if i<=rnd else "○" for i in range(TOTAL_ROUNDS))
                c.create_text(W//2,60,
                              text=f"Lock {rnd+1} of {TOTAL_ROUNDS}   {pips}   ({seq_len} digits)",
                              fill="#cc7700",font=tkfont.Font(family="Courier New",size=9,weight="bold"))
                # Dial
                c.create_oval(DIAL_CX-DIAL_R-14,DIAL_CY-DIAL_R-14,
                              DIAL_CX+DIAL_R+14,DIAL_CY+DIAL_R+14,fill="#1a0800",outline="#5a3010",width=6)
                c.create_oval(DIAL_CX-DIAL_R,DIAL_CY-DIAL_R,DIAL_CX+DIAL_R,DIAL_CY+DIAL_R,
                              fill="#2a1200",outline="#8B6914",width=4)
                for i in range(10):
                    a=math.radians(i*36-90)
                    nx=DIAL_CX+int((DIAL_R-26)*math.cos(a))
                    ny=DIAL_CY+int((DIAL_R-26)*math.sin(a))
                    if highlight==i:
                        c.create_oval(nx-18,ny-18,nx+18,ny+18,fill="#ff8800",outline="#ffcc00",width=3)
                        c.create_text(nx,ny,text=str(i),fill="#000",
                                      font=tkfont.Font(family="Courier New",size=14,weight="bold"))
                    else:
                        c.create_oval(nx-14,ny-14,nx+14,ny+14,fill="#1a0800",outline="#5a3010",width=2)
                        c.create_text(nx,ny,text=str(i),fill="#8B6914",
                                      font=tkfont.Font(family="Courier New",size=12))
                c.create_oval(DIAL_CX-22,DIAL_CY-22,DIAL_CX+22,DIAL_CY+22,fill="#5a3010",outline=GOLD,width=3)
                prog_y=H-96
                if phase[0]=="showing":
                    c.create_text(W//2,prog_y,text="MEMORISE THIS!",fill="#ff4400",
                                  font=tkfont.Font(family="Courier New",size=14,weight="bold"))
                else:
                    c.create_text(W//2,prog_y,
                                  text="Input: "+" ".join(str(n) for n in player_input),
                                  fill="#ffcc00",font=tkfont.Font(family="Courier New",size=13,weight="bold"))
                bar=("█"*len(player_input))+("░"*(seq_len-len(player_input)))
                c.create_text(W//2,prog_y+28,text=bar,fill="#ff8800",
                              font=tkfont.Font(family="Courier New",size=15))
                if STATUS[0]==1:
                    c.create_rectangle(W//2-220,H//2-42,W//2+220,H//2+42,fill="#000",outline="#ffaa00",width=3)
                    c.create_text(W//2,H//2,text=f"✓ LOCK {rnd+1} CRACKED!",fill="#ffaa00",
                                  font=tkfont.Font(family="Courier New",size=20,weight="bold"),anchor="center")
                elif STATUS[0]==2:
                    c.create_rectangle(W//2-220,H//2-42,W//2+220,H//2+42,fill="#000",outline=RED_C,width=3)
                    c.create_text(W//2,H//2,text="WRONG CODE — ALARM!",fill=RED_C,
                                  font=tkfont.Font(family="Courier New",size=16,weight="bold"),anchor="center")
                c.create_text(W-20,18,text="♥ "*self._heist_lives,fill=RED_C,
                              font=tkfont.Font(family="Courier New",size=10),anchor="e")

            def show_sequence():
                if show_idx[0]>=len(sequence):
                    phase[0]="input"; draw_dial(); return
                n=sequence[show_idx[0]]; draw_dial(highlight=n); show_idx[0]+=1
                aid=self.after(flash_ms,lambda:(draw_dial(),self.after(120,show_sequence)))
                self._pending_after.append(aid)

            def on_key(e):
                if phase[0]!="input" or STATUS[0]!=0: return
                k=e.keysym
                if k.isdigit():
                    n=int(k); player_input.append(n); draw_dial(highlight=n)
                    if len(player_input)==seq_len:
                        if player_input==sequence:
                            STATUS[0]=1; draw_dial(); self.after(900,_round_win)
                        else:
                            STATUS[0]=2; draw_dial(); self.after(1400,_lose)

            self.bind("<KeyPress>",on_key,"+")
            draw_dial(); self.after(600,show_sequence)

        def _round_win():
            round_num[0]+=1
            if round_num[0]>=TOTAL_ROUNDS:
                self._heist_loot+=1500; self._heist_difficulty+=0.15
                self._heist_stage+=1; self._heist_intro()
            else:
                start_round()

        start_round()

    # ── STAGE 4: Lockpick ───────────────────────────────────
    def _heist_lockpick(self):
        self._cancel_pending_afters(); self._clear_overlay()
        c=self.canvas; c.delete("all")
        diff=self._heist_difficulty
        NUM_PINS=int(5+diff*1.5); PIN_W=54; PIN_GAP=16
        total_w=NUM_PINS*(PIN_W+PIN_GAP)-PIN_GAP
        start_x=(W-total_w)//2; PIN_Y=280; PIN_H=240
        # Each successive pin: narrower window, faster speed, and accelerates over time
        def make_pin(i):
            window=max(10,32-i*3-int(diff*4))          # shrinks each pin
            base_spd=(2.0+i*0.3+diff*0.6)              # faster each pin
            spd=base_spd*(1 if random.random()>0.5 else -1)
            return {"y":float(random.randint(PIN_Y+40,PIN_Y+PIN_H-60)),
                    "dy":spd,"base_spd":base_spd,
                    "set":False,"window":window,
                    "ticks":0,"fakout_cd":random.randint(18,40)}
        pins=[make_pin(i) for i in range(NUM_PINS)]
        current_pin=[0]; STATUS=[0]; RUNNING=[True]

        def draw():
            c.delete("all")
            c.create_rectangle(0,0,W,H,fill="#080010")
            for sy in range(0,H,6): c.create_line(0,sy,W,sy,fill="#0a0018",width=1)
            c.create_text(W//2,20,text="STAGE 4 — LOCKPICK",fill="#aa44ff",
                          font=tkfont.Font(family="Courier New",size=11,weight="bold"))
            c.create_text(W//2,44,text="Press SPACE in the sweet spot — pins get faster and narrower!",
                          fill="#6622aa",font=tkfont.Font(family="Courier New",size=9))
            round_rect(c,start_x-20,PIN_Y-20,start_x+total_w+20,PIN_Y+PIN_H+20,r=12,
                       fill="#100020",outline="#6622aa",width=3)
            for i,pin in enumerate(pins):
                px=start_x+i*(PIN_W+PIN_GAP)
                c.create_rectangle(px,PIN_Y,px+PIN_W,PIN_Y+PIN_H,fill="#0a0018",outline="#3311aa",width=1)
                if pin["set"]:
                    c.create_rectangle(px,PIN_Y,px+PIN_W,PIN_Y+PIN_H,fill="#1a0040",outline="#8844ff",width=2)
                    c.create_text(px+PIN_W//2,PIN_Y+PIN_H//2,text="✓",fill="#8844ff",
                                  font=tkfont.Font(size=22,weight="bold"))
                    continue
                sweet_y=PIN_Y+PIN_H//2-pin["window"]//2
                c.create_rectangle(px+4,sweet_y,px+PIN_W-4,sweet_y+pin["window"],
                                   fill="#331144",outline="#cc44ff",width=2)
                # Speed indicator bar under track
                spd_ratio=min(1.0,abs(pin["dy"])/12.0)
                bar_w=int((PIN_W-8)*spd_ratio)
                c.create_rectangle(px+4,PIN_Y+PIN_H+4,px+PIN_W-4,PIN_Y+PIN_H+10,fill="#1a0030",outline="")
                c.create_rectangle(px+4,PIN_Y+PIN_H+4,px+4+bar_w,PIN_Y+PIN_H+10,
                                   fill="#ff2200" if spd_ratio>0.7 else "#ff8800" if spd_ratio>0.4 else "#cc44ff",outline="")
                py2=int(pin["y"]); active=i==current_pin[0]
                in_spot=sweet_y<=py2<=sweet_y+pin["window"]
                pcol="#cc44ff" if not active else("#00ff88" if in_spot else "#ff4400")
                c.create_rectangle(px+8,py2-7,px+PIN_W-8,py2+7,fill=pcol,outline="#fff",width=2 if active else 1)
                if active:
                    c.create_rectangle(px-2,py2-9,px+PIN_W+2,py2+9,fill="",outline="#ffffff",width=1)
            prog="".join("█" if p["set"] else "░" for p in pins)
            c.create_text(W//2,H-68,text=prog,fill="#aa44ff",
                          font=tkfont.Font(family="Courier New",size=20))
            c.create_text(W//2,H-40,text=f"Pin {current_pin[0]+1} of {NUM_PINS}",fill="#6622aa",
                          font=tkfont.Font(family="Courier New",size=10))
            c.create_text(W-20,20,text="♥ "*self._heist_lives,fill=RED_C,
                          font=tkfont.Font(family="Courier New",size=10),anchor="e")
            if STATUS[0]==1:
                c.create_rectangle(W//2-220,H//2-44,W//2+220,H//2+44,fill="#000",outline="#aa44ff",width=3)
                c.create_text(W//2,H//2,text="✓ LOCK OPEN!",fill="#aa44ff",
                              font=tkfont.Font(family="Courier New",size=22,weight="bold"),anchor="center")
            elif STATUS[0]==2:
                c.create_rectangle(W//2-220,H//2-44,W//2+220,H//2+44,fill="#000",outline=RED_C,width=3)
                c.create_text(W//2,H//2,text="PIN SNAPPED!",fill=RED_C,
                              font=tkfont.Font(family="Courier New",size=20,weight="bold"),anchor="center")

        def tick():
            if not RUNNING[0]: return
            cp=current_pin[0]
            if cp<NUM_PINS and not pins[cp]["set"]:
                pin=pins[cp]; pin["ticks"]+=1
                # Gradual acceleration — speed grows 0.5% per tick
                accel=1.0+pin["ticks"]*0.005
                pin["dy"]=math.copysign(min(pin["base_spd"]*accel,14.0),pin["dy"])
                pin["y"]+=pin["dy"]
                if pin["y"]>=PIN_Y+PIN_H-14: pin["dy"]=-abs(pin["dy"])
                if pin["y"]<=PIN_Y+14:       pin["dy"]=abs(pin["dy"])
                # Random fake-out: sudden direction flip mid-track
                pin["fakout_cd"]-=1
                if pin["fakout_cd"]<=0:
                    pin["dy"]*=-1
                    pin["fakout_cd"]=random.randint(16,36)
            draw()
            aid=self.after(36,tick); self._pending_after.append(aid)

        def on_key(e):
            if not RUNNING[0] or STATUS[0]!=0: return
            if e.keysym=="space":
                cp=current_pin[0]; pin=pins[cp]
                sweet_y=PIN_Y+PIN_H//2-pin["window"]//2
                if sweet_y<=int(pin["y"])<=sweet_y+pin["window"]:
                    pin["set"]=True; current_pin[0]+=1
                    if current_pin[0]>=NUM_PINS:
                        RUNNING[0]=False; STATUS[0]=1; draw()
                        self.after(1400,_win)
                else:
                    RUNNING[0]=False; STATUS[0]=2; draw()
                    self.after(1400,_lose)

        def _win():
            self._heist_loot+=1000; self._heist_difficulty+=0.15
            self._heist_stage+=1; self._heist_intro()
        def _lose():
            self._heist_lives-=1
            if self._heist_lives<=0: self._heist_fail()
            else: self._heist_lockpick()

        self.bind("<KeyPress>",on_key,"+")
        draw(); aid=self.after(36,tick); self._pending_after.append(aid)

    # ── STAGE 5: Car Chase ──────────────────────────────────
    def _heist_car_chase(self):
        self._cancel_pending_afters(); self._clear_overlay()
        c=self.canvas; c.delete("all")
        LANE_W=120; LANES=7; ROAD_X=(W-LANES*LANE_W)//2; ROAD_W=LANES*LANE_W
        PLAYER_LANE=[3]; PLAYER_Y=[H-120]; DIST=[0]; GOAL=2000; STATUS=[0]; RUNNING=[True]
        PLAYER_Y_MIN=70; PLAYER_Y_MAX=H-50; PLAYER_Y_STEP=22
        diff=self._heist_difficulty
        scroll_speed=[5.0+diff*2.0]   # mutable so tick can ramp it
        MAX_SPEED=28.0; RAMP=0.008    # added to scroll_speed every tick
        alarm_flash=[0]
        obstacles=[]
        for _ in range(10):
            obstacles.append({"lane":random.randint(0,LANES-1),
                               "y":float(random.randint(-900,-100)),
                               "type":random.choice(["police","police","roadblock","truck"])})

        def spawn_extra():
            obstacles.append({"lane":random.randint(0,LANES-1),
                               "y":float(random.randint(-400,-80)),
                               "type":random.choice(["police","police","roadblock","truck"])})

        def draw():
            c.delete("all")
            alarm_flash[0]+=1; af=alarm_flash[0]
            spd=scroll_speed[0]
            # Sky pulses faster as speed increases
            pulse_rate=max(2,int(10-spd//3))
            sky_col="#1a0000" if af%pulse_rate<pulse_rate//2 else "#2a0000"
            c.create_rectangle(0,0,W,H,fill=sky_col)
            for sy in range(0,H,18): c.create_line(0,sy,W,sy,fill="#220000",width=1)
            c.create_rectangle(ROAD_X,0,ROAD_X+ROAD_W,H,fill="#111111")
            for l in range(LANES+1):
                lx=ROAD_X+l*LANE_W
                c.create_line(lx,0,lx,H,fill="#333",width=2)
            dash_off=(DIST[0]*spd)%80
            for l in range(LANES):
                lx=ROAD_X+l*LANE_W+LANE_W//2
                for dy in range(-80,H+80,80):
                    c.create_line(lx,dy+dash_off,lx,dy+40+dash_off,fill="#555",width=2)
            for ob in obstacles:
                ox=ROAD_X+ob["lane"]*LANE_W+LANE_W//2; oy=int(ob["y"])
                t=ob["type"]
                if t=="police":
                    c.create_rectangle(ox-26,oy-28,ox+26,oy+28,fill="#001a88",outline="#0022cc",width=2)
                    c.create_rectangle(ox-18,oy-18,ox+18,oy+18,fill="#001166",outline="")
                    lbar_col="#ff0000" if af%6<3 else "#0000ff"
                    c.create_rectangle(ox-22,oy-28,ox+22,oy-16,fill=lbar_col,outline="#fff",width=1)
                    c.create_text(ox,oy+8,text="POLICE",fill="#4488ff",
                                  font=tkfont.Font(family="Courier New",size=6,weight="bold"))
                elif t=="roadblock":
                    c.create_rectangle(ox-40,oy-12,ox+40,oy+12,fill="#cc8800",outline="#ffaa00",width=2)
                    for rx in range(ox-36,ox+36,12):
                        c.create_line(rx,oy-12,rx+8,oy+12,fill="#000",width=3)
                    c.create_text(ox,oy,text="STOP",fill="#ff2200",
                                  font=tkfont.Font(family="Courier New",size=8,weight="bold"))
                else:
                    c.create_rectangle(ox-28,oy-40,ox+28,oy+40,fill="#444",outline="#666",width=2)
                    c.create_rectangle(ox-24,oy-34,ox+24,oy+34,fill="#2a2a2a",outline="")
            pl=PLAYER_LANE[0]; px=ROAD_X+pl*LANE_W+LANE_W//2; py=PLAYER_Y[0]
            c.create_rectangle(px-26,py-34,px+26,py+34,fill="#cc2200",outline="#ff4400",width=2)
            c.create_rectangle(px-20,py-24,px+20,py+24,fill="#881100",outline="")
            c.create_oval(px-22,py+22,px-10,py+38,fill="#111",outline="#444",width=1)
            c.create_oval(px+10,py+22,px+22,py+38,fill="#111",outline="#444",width=1)
            c.create_oval(px-22,py-38,px-10,py-22,fill="#111",outline="#444",width=1)
            c.create_oval(px+10,py-38,px+22,py-22,fill="#111",outline="#444",width=1)
            # HUD
            prog=min(1.0,DIST[0]/GOAL)
            c.create_rectangle(20,14,W-20,34,fill="#000",outline="#00ff44",width=2)
            c.create_rectangle(20,14,20+int((W-40)*prog),34,fill="#00ff44",outline="")
            c.create_text(W//2,24,text=f"ESCAPE: {int(prog*100)}%",fill="#000",
                          font=tkfont.Font(family="Courier New",size=9,weight="bold"))
            # Speed indicator — colour shifts red as speed climbs
            spd_ratio=min(1.0,(spd-5)/MAX_SPEED)
            spd_col="#00ff44" if spd_ratio<0.4 else "#ffaa00" if spd_ratio<0.75 else "#ff2200"
            c.create_text(20,40,text=f"SPEED  {'▮'*int(spd_ratio*10)}{'▯'*(10-int(spd_ratio*10))}",
                          fill=spd_col,font=tkfont.Font(family="Courier New",size=8),anchor="w")
            c.create_text(W-20,40,text="♥ "*self._heist_lives,fill=RED_C,
                          font=tkfont.Font(family="Courier New",size=10),anchor="e")
            if spd_ratio>0.72:
                c.create_text(W//2,56,text="⚠ SPEED CRITICAL",fill="#ff2200",
                              font=tkfont.Font(family="Courier New",size=8,weight="bold"))
            if STATUS[0]==1:
                c.create_rectangle(W//2-240,H//2-50,W//2+240,H//2+50,fill="#000",outline="#00ff44",width=4)
                c.create_text(W//2,H//2,text="🏁 ESCAPED!",fill="#00ff44",
                              font=tkfont.Font(family="Georgia",size=26,weight="bold"),anchor="center")
            elif STATUS[0]==2:
                c.create_rectangle(W//2-240,H//2-50,W//2+240,H//2+50,fill="#000",outline=RED_C,width=4)
                c.create_text(W//2,H//2,text="CAUGHT!",fill=RED_C,
                              font=tkfont.Font(family="Georgia",size=26,weight="bold"),anchor="center")

        def tick():
            if not RUNNING[0]: return
            DIST[0]+=1
            # Ramp speed every tick
            scroll_speed[0]=min(MAX_SPEED,scroll_speed[0]+RAMP)
            spd=scroll_speed[0]
            # Spawn extra obstacles at higher speeds
            if DIST[0]%200==0 and len(obstacles)<22:
                spawn_extra()
            for ob in obstacles:
                ob["y"]+=spd
                if ob["y"]>H+60:
                    ob["y"]=float(random.randint(-600,-80))
                    ob["lane"]=random.randint(0,LANES-1)
                    ob["type"]=random.choice(["police","police","roadblock","truck"])
            # Always guarantee at least one free lane in the danger zone
            py=PLAYER_Y[0]
            danger_zone=[ob for ob in obstacles if py-90<=ob["y"]<=py+90]
            blocked_lanes=set(ob["lane"] for ob in danger_zone)
            if len(blocked_lanes)>=LANES:
                furthest=min(danger_zone,key=lambda o:abs(o["y"]-py))
                furthest["y"]=float(random.randint(-600,-200))
                furthest["lane"]=random.randint(0,LANES-1)
            pl=PLAYER_LANE[0]
            px=ROAD_X+pl*LANE_W+LANE_W//2
            for ob in obstacles:
                ox=ROAD_X+ob["lane"]*LANE_W+LANE_W//2; oy=int(ob["y"])
                if abs(px-ox)<50 and abs(py-oy)<60:
                    RUNNING[0]=False; STATUS[0]=2; draw()
                    self.after(1400,_lose); return
            if DIST[0]>=GOAL:
                RUNNING[0]=False; STATUS[0]=1; draw()
                self.after(1400,_win); return
            draw()
            # Tick interval also tightens as speed grows
            delay=max(18,50-int(spd*1.4))
            aid=self.after(delay,tick); self._pending_after.append(aid)

        def on_key(e):
            if not RUNNING[0]: return
            k=e.keysym.lower()
            if k in("left","a") and PLAYER_LANE[0]>0: PLAYER_LANE[0]-=1
            elif k in("right","d") and PLAYER_LANE[0]<LANES-1: PLAYER_LANE[0]+=1
            elif k in("up","w"):   PLAYER_Y[0]=max(PLAYER_Y_MIN,PLAYER_Y[0]-PLAYER_Y_STEP)
            elif k in("down","s"): PLAYER_Y[0]=min(PLAYER_Y_MAX,PLAYER_Y[0]+PLAYER_Y_STEP)

        def _win():
            self._heist_loot+=2000; self._heist_difficulty+=0.15
            self._heist_stage+=1; self._heist_intro()
        def _lose():
            self._heist_lives-=1
            if self._heist_lives<=0: self._heist_fail()
            else: self._heist_car_chase()

        self.bind("<KeyPress>",on_key,"+")
        draw(); aid=self.after(50,tick); self._pending_after.append(aid)

    def _heist_fail(self):
        self._cancel_pending_afters(); self._clear_overlay()
        c=self.canvas; c.delete("all")
        c.create_rectangle(0,0,W,H,fill="#100000")
        for sy in range(0,H,6): c.create_line(0,sy,W,sy,fill="#180000",width=1)
        c.create_text(W//2,180,text="HEIST FAILED",fill=RED_C,
                      font=tkfont.Font(family="Georgia",size=36,weight="bold"),anchor="center")
        c.create_text(W//2,260,text="You were caught. The law always wins…",fill="#882200",
                      font=tkfont.Font(family="Georgia",size=14,slant="italic"),anchor="center")
        c.create_text(W//2,320,text=f"Loot collected before bust: ${self._heist_loot:,}",fill="#555",
                      font=tkfont.Font(family="Courier New",size=11),anchor="center")
        self._make_btn(W//2-80,420,"Try Again",self._heist_start,col=RED_C,fg="white",w=130)
        self._make_btn(W//2+80,420,"Leave",self._back_to_interior,col="#333",fg=CREAM,w=100)

    def _heist_complete(self):
        self._cancel_pending_afters(); self._clear_overlay()
        c=self.canvas; c.delete("all")
        c.create_rectangle(0,0,W,H,fill="#000811")
        for i in range(20):
            a=math.radians(i*18)
            c.create_line(W//2,H//2,W//2+int(500*math.cos(a)),H//2+int(500*math.sin(a)),
                          fill=["#00ff44","#ffcc00","#00aaff","#ff4400"][i%4],width=2)
        round_rect(c,W//2-280,H//2-120,W//2+280,H//2+120,r=20,fill="#000",outline="#00ff44",width=4)
        c.create_text(W//2,H//2-70,text="🎉  HEIST COMPLETE!  🎉",fill="#00ff44",
                      font=tkfont.Font(family="Georgia",size=24,weight="bold"),anchor="center")
        self.money+=self._heist_loot
        self._heist_complete_time=time.time()
        c.create_text(W//2,H//2-10,text=f"Total Loot: ${self._heist_loot:,}",fill=GOLD,
                      font=tkfont.Font(family="Georgia",size=20,weight="bold"),anchor="center")
        c.create_text(W//2,H//2+40,text=f"New Balance: ${self.money:,}",fill=CREAM,
                      font=tkfont.Font(family="Courier New",size=13),anchor="center")
        self._refresh_balance_text()
        self._post_game(self._heist_loot,"win")
        self._make_btn(W//2,H//2+100,"Run Another Job",self._heist_start,col="#00aa44",fg="white",w=160)
        self._make_btn(W//2,H//2+150,"Back to HQ",self._back_to_interior,col="#333",fg=CREAM,w=140)

if __name__=="__main__":
    app=CasinoApp()
    app.mainloop()
