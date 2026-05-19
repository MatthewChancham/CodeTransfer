"""
╔══════════════════════════════════════════════════════╗
║       RG CASINO TOWN  — Full Edition                 ║
║  Texas Hold'em • Yahtzee • Dice Roll • The Arena     ║
║  Boss Encounters • Heist • Debt Interest • VIP+      ║
╚══════════════════════════════════════════════════════╝
"""
import tkinter as tk
from tkinter import font as tkfont
import random, math, time, datetime, string
from collections import Counter
from itertools import combinations

W,H=1100,700; TOWN_W=1600; TOWN_H=1100
PLAYER_SPEED=4; PLAYER_R=12; HOTBAR_H=70
GOLD="#f5c518"; CREAM="#f5f0e8"; DARK="#1a1208"; RED_C="#c0392b"
GREEN_C="#27ae60"; BLUE_C="#2980b9"; PURPLE="#8e44ad"
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
        self.interest_games_since_borrow=0; self.boss_alert_level=0
        self.vip_unlocked=False; self.arena_unlocked=False
        self.player_health=100; self.fight_stage=0
        self.enemy_hp=list(ENEMY_MAX_HP)
        self.screen="title"; self._exit_cooldown=0
        self._fountain_frame=0; self._town_msg=""; self._town_msg_timer=0
        self._pending_after=[]
        self._interior_loop_id=None   # tracks scheduled interior loop so it can be hard-cancelled
        self.px=800; self.py=600; self.keys=set(); self.cam_x=0; self.cam_y=0
        self.int_building=None; self.int_room=None; self.int_rooms={}
        self.int_px=W//2; self.int_py=420
        self.nearby_npc=None; self.npc_dialogue=""; self.dial_timer=0
        self.canvas=tk.Canvas(self,width=W,height=H,bg=DARK,highlightthickness=0); self.canvas.pack()
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
            dict(name="shady",  x=180, y=550,w=140,h=120,col="#2c2c2c",roof="#111111",label="SHADY ALLEY",desc="Borrow / Repay"),
            dict(name="vip",    x=1200,y=450,w=170,h=150,col="#4a2060",roof="#2d0d4a",label="VIP LOUNGE", desc="Exclusive games"),
            dict(name="bank",   x=700, y=820,w=150,h=120,col="#1a3a5c",roof="#0f2340",label="BANK",       desc="Stats & balance"),
            dict(name="arena",  x=1000,y=680,w=190,h=155,col="#2a0000",roof="#1a0000",label="THE ARENA",  desc="Fight & Dine"),
        ]
        self.bind("<KeyPress>",self._key_down); self.bind("<KeyRelease>",self._key_up)
        self.focus_set(); self._show_title()

    # ── TITLE / AGE GATE ────────────────────────────────
    def _show_title(self):
        self.screen="title"; c=self.canvas; c.delete("all"); self._clear_overlay()
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
        if year==1534:  # Bishop easter egg
            self._clear_overlay(); c=self.canvas; c.delete("all")
            c.create_rectangle(0,0,W,H,fill="#000")
            c.create_text(W//2,H//2,text="Welcome............. Bishop",fill=RED_C,font=self.fnt_huge,anchor="center")
            self.after(2500,self._start_town); return
        if year<1900 or year>today.year: self._title_error("Please enter a valid birth year.")
        elif age<18: self._underage_shutdown()
        else: self._start_town()

    def _start_town(self):
        self._clear_overlay(); self.screen="town"; self._town_loop()

    def _title_error(self,msg):
        if self._title_err_id: self.canvas.delete(self._title_err_id)
        self._title_err_id=self.canvas.create_text(W//2,484,text=msg,fill=RED_C,font=self.fnt_small,anchor="center")

    def _underage_shutdown(self):
        self._clear_overlay(); c=self.canvas; c.delete("all")
        c.create_rectangle(0,0,W,H,fill="#1a0000")
        c.create_text(W//2,H//2-60,text="ACCESS DENIED",fill="#ff4444",font=self.fnt_huge,anchor="center")
        c.create_text(W//2,H//2,text="You must be 18 or older.",fill=CREAM,font=self.fnt_title,anchor="center")
        c.create_text(W//2,H//2+50,text="Closing in 3 seconds.",fill="#888",font=self.fnt_body,anchor="center")
        self.after(3000,self.destroy)

    # ── INPUT ────────────────────────────────────────────
    def _key_down(self,e):
        self.keys.add(e.keysym.lower())
        if e.keysym=="Escape":
            if self.screen=="interior": self._exit_interior()
            elif self.screen=="game": self._back_to_interior()
        elif e.keysym.lower()=="c" and self.screen=="interior": self._try_interact()

    def _key_up(self,e): self.keys.discard(e.keysym.lower())

    # ── POST-GAME STATS & EVENTS ─────────────────────────
    def _post_game(self,bet,result):
        self.games_played+=1; self.total_bet+=bet
        if result=="win":   self.wins+=1;   self.total_won+=bet
        elif result=="loss":self.losses+=1;  self.total_lost+=bet
        else:               self.ties+=1
        self._check_unlocks(); self._apply_interest_if_due()

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
                self.after(700,self._boss_encounter)

    def _show_town_msg(self,text,ms=2500): self._town_msg=text; self._town_msg_timer=ms
    # ── TOWN LOOP ─────────────────────────────────────────
    def _town_loop(self):
        if self.screen!="town": return
        self._fountain_frame+=1
        if self._town_msg_timer>0:
            self._town_msg_timer-=33
            if self._town_msg_timer<=0: self._town_msg=""
        self._move_player(); self._draw_town(); self._check_building_entry()
        self.after(33,self._town_loop)

    def _move_player(self):
        dx=dy=0
        if "w" in self.keys or "up"    in self.keys: dy-=PLAYER_SPEED
        if "s" in self.keys or "down"  in self.keys: dy+=PLAYER_SPEED
        if "a" in self.keys or "left"  in self.keys: dx-=PLAYER_SPEED
        if "d" in self.keys or "right" in self.keys: dx+=PLAYER_SPEED
        self.px=max(PLAYER_R,min(TOWN_W-PLAYER_R,self.px+dx))
        self.py=max(PLAYER_R,min(TOWN_H-PLAYER_R,self.py+dy))
        self.cam_x=max(0,min(TOWN_W-W,self.px-W//2))
        self.cam_y=max(0,min(TOWN_H-H,self.py-H//2))

    def _tw(self,x): return x-self.cam_x
    def _th(self,y): return y-self.cam_y

    def _check_building_entry(self):
        if time.time()<self._exit_cooldown: return
        for b in self.buildings:
            bx=b["x"]+b["w"]//2; by=b["y"]+b["h"]
            if math.hypot(self.px-bx,self.py-by)<55:
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
        for tx,ty in [(280,320),(1120,280),(830,680),(180,730),(1320,680),(480,780),(940,860),(1400,230),(80,380),(650,750),(360,600),(1060,550)]:
            self._draw_tree(tx,ty)
        for lx,ly in [(618,478),(722,478),(618,562),(722,562),(478,493),(858,493),(498,276),(898,300),(398,620),(1002,616)]:
            self._draw_lamp(lx,ly)
        for b in self.buildings: self._draw_building(b)
        px,py=self._tw(self.px),self._th(self.py)
        c.create_oval(px-PLAYER_R+3,py+PLAYER_R-1,px+PLAYER_R-3,py+PLAYER_R+5,fill="#111111",outline="")
        c.create_rectangle(px-5,py+4,px-1,py+PLAYER_R+4,fill="#2255aa",outline=DARK,width=1)
        c.create_rectangle(px+1,py+4,px+5,py+PLAYER_R+4,fill="#2255aa",outline=DARK,width=1)
        c.create_rectangle(px-8,py-4,px+8,py+5,fill="#cc3333",outline=DARK,width=1)
        c.create_rectangle(px-12,py-3,px-8,py+3,fill="#cc3333",outline=DARK,width=1)
        c.create_rectangle(px+8,py-3,px+12,py+3,fill="#cc3333",outline=DARK,width=1)
        c.create_oval(px-7,py-PLAYER_R-2,px+7,py-4,fill="#e8c07a",outline=DARK,width=1)
        c.create_rectangle(px-10,py-PLAYER_R,px+10,py-PLAYER_R+3,fill="#8B0000",outline=DARK)
        c.create_rectangle(px-6,py-PLAYER_R-9,px+6,py-PLAYER_R,fill="#8B0000",outline=DARK)
        c.create_line(px-6,py-PLAYER_R-2,px+6,py-PLAYER_R-2,fill=GOLD,width=2)
        self._draw_hud()
        if self._town_msg:
            c.create_rectangle(W//2-330,H//2-36,W//2+330,H//2+36,fill="#0a0000",outline=RED_C,width=2)
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
        else:
            round_rect(c,x1,y1,x2,y2,r=8,fill=b["col"],outline=DARK,width=2)
            c.create_polygon(x1-5,y1,mx,y1-40,x2+5,y1,fill=b["roof"],outline=DARK,width=2)
            c.create_rectangle(mx-55,y1-70,mx+55,y1-48,fill=DARK,outline=GOLD,width=2)
            c.create_text(mx,y1-59,text=b["label"],fill=GOLD,font=self.fnt_small,anchor="center")
        dist=math.hypot(self.px-(b["x"]+b["w"]//2),self.py-(b["y"]+b["h"]//2))
        if dist<120:
            c.create_rectangle(mx-70,y2+6,mx+70,y2+26,fill="#06060a",outline="#ffff44",width=1)
            c.create_text(mx,y2+16,text=f"► {b['desc']}",fill="#ffff55",font=self.fnt_small)

    def _draw_hud(self):
        c=self.canvas
        round_rect(c,10,10,312,84,r=12,fill="#120800",outline=GOLD,width=2)
        c.create_text(52,34,text=f"Balance:  ${self.money:,}",fill=GOLD,font=self.fnt_body,anchor="w")
        debt_col=RED_C if self.debt>0 else "#555566"
        c.create_text(52,55,text=f"Debt: ${self.debt:,}",fill=debt_col,font=self.fnt_small,anchor="w")
        c.create_text(52,70,text=f"Played: {self.games_played}   W:{self.wins} L:{self.losses}",fill="#888899",font=self.fnt_small,anchor="w")
        if self.debt>0:
            c.create_rectangle(W-160,6,W-6,32,fill="#330000",outline=RED_C,width=2)
            c.create_text(W-83,19,text="REPAY DEBT",fill=RED_C,font=self.fnt_small,anchor="center")
        if not self.vip_unlocked:
            need=max(0,5000-(self.money-self.starting_money))
            c.create_text(W-10,H-48,text=f"VIP: +${need:,} profit needed",fill="#555544",font=self.fnt_small,anchor="e")
        if not self.arena_unlocked:
            need=max(0,10000-(self.money-self.starting_money))
            c.create_text(W-10,H-32,text=f"Arena: +${need:,} profit needed",fill="#554444",font=self.fnt_small,anchor="e")

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

    def _back_to_interior(self):
        self._cancel_pending_afters(); self._hide_hotbar(); self._clear_overlay()
        self.screen="interior"; self._interior_loop()

    def _exit_interior(self):
        self._cancel_pending_afters(); self._hide_hotbar(); self._clear_overlay()
        self.screen="town"; self._exit_cooldown=time.time()+2.0
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
        spawn={"casino":(W//2,500),"stables":(W//2,500),"shady":(W//2,480),
               "vip":(W//2,480),"bank":(W//2,490),"arena":(W//2,490)}
        self.int_px,self.int_py=spawn.get(building_name,(W//2,480))
        self.nearby_npc=None; self.npc_dialogue=""; self.dial_timer=0
        self._setup_interior(building_name); self._clear_overlay(); self._interior_loop()

    def _setup_interior(self,name):
        builders={"casino":self._make_casino_rooms,"stables":self._make_stables_rooms,
                  "shady":self._make_shady_rooms,"vip":self._make_vip_rooms,
                  "bank":self._make_bank_rooms,"arena":self._make_arena_rooms}
        self.int_rooms=builders[name](); self.int_room=list(self.int_rooms.keys())[0]

    def _interior_loop(self):
        if self.screen!="interior": return
        self._move_int_player(); self._draw_interior()
        self._check_npc_proximity(); self._check_door_proximity()
        if self.dial_timer>0: self.dial_timer-=1
        self._interior_loop_id=self.after(33,self._interior_loop)

    def _move_int_player(self):
        dx=dy=0; speed=4
        if "w" in self.keys or "up"    in self.keys: dy-=speed
        if "s" in self.keys or "down"  in self.keys: dy+=speed
        if "a" in self.keys or "left"  in self.keys: dx-=speed
        if "d" in self.keys or "right" in self.keys: dx+=speed
        nx=max(18,min(W-18,self.int_px+dx)); ny=max(70,min(H-80,self.int_py+dy))
        room=self.int_rooms.get(self.int_room,{})
        for furn in room.get("furniture",[]):
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
            if math.hypot(self.int_px-(dx2+dw//2),self.int_py-(dy2+dh//2))<70:
                c.create_rectangle(dx2-2,dy2-2,dx2+dw+2,dy2+dh+2,outline="#ffff44",width=2)
        for npc in room.get("npcs",[]): self._draw_npc(c,npc)
        px,py=self.int_px,self.int_py
        c.create_oval(px-10,py+14,px+10,py+20,fill="#0a0000",outline="")
        c.create_rectangle(px-5,py+4,px-1,py+16,fill="#2255aa",outline=DARK,width=1)
        c.create_rectangle(px+1,py+4,px+5,py+16,fill="#2255aa",outline=DARK,width=1)
        c.create_rectangle(px-9,py-6,px+9,py+6,fill="#cc3333",outline=DARK,width=1)
        c.create_rectangle(px-13,py-4,px-9,py+4,fill="#cc3333",outline=DARK,width=1)
        c.create_rectangle(px+9,py-4,px+13,py+4,fill="#cc3333",outline=DARK,width=1)
        c.create_oval(px-7,py-18,px+7,py-6,fill="#e8c07a",outline=DARK,width=1)
        c.create_rectangle(px-10,py-20,px+10,py-17,fill="#8B0000",outline=DARK)
        c.create_rectangle(px-7,py-28,px+7,py-20,fill="#8B0000",outline=DARK)
        c.create_line(px-7,py-23,px+7,py-23,fill=GOLD,width=1)
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
        if ftype=="felt_table":
            round_rect(c,fx1,fy1,fx2,fy2,r=20,fill=FELT,outline="#0a3015",width=3)
            round_rect(c,fx1+8,fy1+8,fx2-8,fy2-8,r=16,fill=FELT_L,outline="")
            c.create_text((fx1+fx2)//2,(fy1+fy2)//2,text=furn.get("label",""),fill="#2a5a2a",font=self.fnt_body)
        elif ftype=="counter":
            c.create_rectangle(fx1,fy1,fx2,fy2,fill="#8B6914",outline=GOLD,width=2)
            c.create_rectangle(fx1,fy1,fx2,fy1+10,fill="#a07830",outline="")

    def _check_npc_proximity(self):
        room=self.int_rooms.get(self.int_room,{}); self.nearby_npc=None
        for npc in room.get("npcs",[]):
            if math.hypot(self.int_px-npc["x"],self.int_py-npc["y"])<72:
                self.nearby_npc=npc; break

    def _check_door_proximity(self):
        room=self.int_rooms.get(self.int_room,{})
        for door in room.get("doors",[]):
            dx2=door["x"]+door["w"]//2; dy2=door["y"]+door["h"]//2
            if math.hypot(self.int_px-dx2,self.int_py-dy2)<30:
                if door["to"]=="exit": self._exit_interior()
                else:
                    self.int_room=door["to"]; self.int_px=W//2; self.int_py=490
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
            "bank_stats":self._bank_screen,"arena_fight":self._arena_fight_screen,
            "arena_bet":self._arena_bet_screen,"arena_restaurant":self._arena_restaurant_screen,
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
            round_rect(c,W//2-340,200,W//2+340,420,r=40,fill=FELT,outline="#0a3015",width=4)
            round_rect(c,W//2-328,210,W//2+328,410,r=36,fill=FELT_L,outline="")
            c.create_text(W//2,240,text="BLACKJACK PAYS 3:2",fill="#2a5a2a",font=tkfont.Font(family="Courier New",size=11))
        def rou_decor(c):
            wx,wy,wr=240,300,130; RED_N={1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
            c.create_oval(wx-wr-12,wy-wr-12,wx+wr+12,wy+wr+12,fill="#5a3010",outline=GOLD,width=4)
            for i in range(37):
                ang=(i/37)*360; col="#006000" if i==0 else("#c0392b" if i in RED_N else "#1a1a1a")
                c.create_arc(wx-wr,wy-wr,wx+wr,wy+wr,start=ang,extent=360/37,fill=col,outline="white",width=1,style="pie")
            c.create_oval(wx-18,wy-18,wx+18,wy+18,fill=GOLD,outline=DARK,width=2)
            round_rect(c,430,160,W-30,460,r=12,fill=FELT,outline="#0a3015",width=3)
        def slots_decor(c):
            for i,sx2 in enumerate([200,W//2,W-200]):
                round_rect(c,sx2-70,148,sx2+70,430,r=20,fill="#1a0040",outline=PURPLE,width=4)
                round_rect(c,sx2-58,163,sx2+58,306,r=12,fill="#000033",outline=GOLD,width=2)
                c.create_text(sx2,234,text=["🍒","💎","7"][i],fill=GOLD,font=tkfont.Font(size=36))
        def craps_decor(c):
            round_rect(c,60,148,W-60,430,r=28,fill="#0a3050",outline="#1a6090",width=4)
            c.create_text(W//2,198,text="PASS  LINE",fill="#777",font=tkfont.Font(family="Georgia",size=22,weight="bold"))
        def poker_decor(c):
            round_rect(c,80,150,W-80,430,r=40,fill=FELT,outline="#0a3015",width=4)
            round_rect(c,90,160,W-90,420,r=36,fill=FELT_L,outline="")
            c.create_text(W//2,200,text="TEXAS  HOLD'EM  —  3 Players",fill="#2a5a2a",font=tkfont.Font(family="Courier New",size=12))
        def yah_decor(c):
            round_rect(c,80,140,W-80,440,r=20,fill="#1a1a00",outline="#5a5a00",width=3)
            c.create_text(W//2,185,text="Y A H T Z E E",fill="#aaa800",font=tkfont.Font(family="Courier New",size=18,weight="bold"))
        def dice_decor(c):
            round_rect(c,80,150,W-80,430,r=20,fill=FELT,outline="#0a3015",width=3)
            c.create_text(W//2,200,text="DICE  ROLL  — Roll vs. Dealer",fill="#2a5a2a",font=tkfont.Font(family="Courier New",size=12))

        lobby_doors=[
            {"to":"bj",   "x":155,"y":62, "w":155,"h":34,"col":"#1a0000","label":"Blackjack"},
            {"to":"rou",  "x":790,"y":62, "w":155,"h":34,"col":"#001a00","label":"Roulette"},
            {"to":"slots","x":0,  "y":195,"w":115,"h":34,"col":"#0d0020","label":"Slots"},
            {"to":"craps","x":0,  "y":265,"w":115,"h":34,"col":"#001020","label":"Craps"},
            {"to":"yah",  "x":0,  "y":335,"w":115,"h":34,"col":"#1a1a00","label":"Yahtzee"},
            {"to":"dice", "x":0,  "y":405,"w":115,"h":34,"col":"#001a0a","label":"Dice Roll"},
            {"to":"war",  "x":985,"y":195,"w":115,"h":34,"col":"#1a0800","label":"War"},
            {"to":"hcard","x":985,"y":265,"w":115,"h":34,"col":"#001a1a","label":"High Card"},
            {"to":"poker","x":985,"y":335,"w":115,"h":34,"col":"#001a00","label":"Hold'em"},
            {"to":"exit", "x":460,"y":590,"w":180,"h":34,"col":"#111",   "label":"Exit Casino"},
        ]
        return {
            "lobby":{"title":"Royal Casino — Grand Lobby","floor":"#2a1200","wall":"#1a0800",
                     "decor_fn":lobby_decor,"furniture":[],"doors":lobby_doors,
                     "npcs":[{"id":"host","x":W//2,"y":340,"name":"Casino Host",
                               "col":"#e8c07a","hat_col":"#8B0000","body_col":"#1a3a6a",
                               "line":"Doors around the room\nlead to every game!","game":None}]},
            "bj":   {"title":"Blackjack Hall","floor":"#0d1a08","wall":"#060d04","decor_fn":bj_decor,
                     "furniture":[{"type":"felt_table","bounds":(W//2-340,200,W//2+340,420),"label":""}],
                     "doors":[{"to":"lobby","x":460,"y":508,"w":180,"h":30,"col":"#333","label":"Back to Lobby"}],
                     "npcs":[{"id":"dealer_bj","x":W//2,"y":220,"name":"Dealer Rosa","col":"#d0b080",
                               "hat_col":DARK,"body_col":"#1a1a2a","line":"Place chips then DEAL!","game":"blackjack"}]},
            "rou":  {"title":"Roulette Room","floor":"#060d00","wall":"#030800","decor_fn":rou_decor,
                     "furniture":[],"doors":[{"to":"lobby","x":460,"y":508,"w":180,"h":30,"col":"#333","label":"Back to Lobby"}],
                     "npcs":[{"id":"croupier","x":700,"y":290,"name":"Croupier Max","col":"#c8b090",
                               "hat_col":"#2a2a3a","body_col":"#1a3a00","line":"Pick colour & number,\nplace chips then DEAL!","game":"roulette"}]},
            "slots":{"title":"Slots Corner","floor":"#0d0028","wall":"#080018","decor_fn":slots_decor,
                     "furniture":[],"doors":[{"to":"lobby","x":460,"y":508,"w":180,"h":30,"col":"#333","label":"Back to Lobby"}],
                     "npcs":[{"id":"attendant","x":W//2,"y":460,"name":"Attendant Lily","col":"#e0b898",
                               "hat_col":PURPLE,"body_col":PURPLE,"line":"Place chips then DEAL to spin.","game":"slots"}]},
            "craps":{"title":"Craps Table","floor":"#000a1a","wall":"#00060e","decor_fn":craps_decor,
                     "furniture":[],"doors":[{"to":"lobby","x":460,"y":508,"w":180,"h":30,"col":"#333","label":"Back to Lobby"}],
                     "npcs":[{"id":"stickman","x":W//2,"y":250,"name":"Stickman Joe","col":"#d8c0a0",
                               "hat_col":"#00204a","body_col":"#00204a","line":"Bet pass line!\nPlace chips then DEAL.","game":"craps"}]},
            "war":  {"title":"War Room","floor":"#1a0800","wall":"#0d0400","decor_fn":None,
                     "furniture":[{"type":"felt_table","bounds":(W//2-280,210,W//2+280,430),"label":"WAR"}],
                     "doors":[{"to":"lobby","x":460,"y":508,"w":180,"h":30,"col":"#333","label":"Back to Lobby"}],
                     "npcs":[{"id":"dealer_war","x":W//2,"y":228,"name":"Dealer Rex","col":"#c8a080",
                               "hat_col":"#3a2000","body_col":"#8B0000","line":"Highest card wins!\nPlace chips then DEAL.","game":"war"}]},
            "hcard":{"title":"High Card Lounge","floor":"#001818","wall":"#000e0e","decor_fn":None,
                     "furniture":[{"type":"felt_table","bounds":(W//2-250,220,W//2+250,420),"label":"HIGH CARD"}],
                     "doors":[{"to":"lobby","x":460,"y":508,"w":180,"h":30,"col":"#333","label":"Back to Lobby"}],
                     "npcs":[{"id":"dealer_hc","x":W//2,"y":238,"name":"Dealer Mia","col":"#d8c0a8",
                               "hat_col":"#002a2a","body_col":"#004444","line":"Draw one card each.\nHighest wins!","game":"high_card"}]},
            "poker":{"title":"Texas Hold'em Room","floor":"#0a1a0a","wall":"#060e06","decor_fn":poker_decor,
                     "furniture":[{"type":"felt_table","bounds":(W//2-340,190,W//2+340,430),"label":""}],
                     "doors":[{"to":"lobby","x":460,"y":508,"w":180,"h":30,"col":"#333","label":"Back to Lobby"}],
                     "npcs":[{"id":"dealer_ph","x":W//2,"y":210,"name":"Dealer Phil","col":"#c8b060",
                               "hat_col":"#1a2a00","body_col":"#1a3a10","line":"Texas Hold'em!\nTalk to me to play.","game":"texas_holdem"}]},
            "yah":  {"title":"Yahtzee Lounge","floor":"#1a1a00","wall":"#0e0e00","decor_fn":yah_decor,
                     "furniture":[],"doors":[{"to":"lobby","x":460,"y":508,"w":180,"h":30,"col":"#333","label":"Back to Lobby"}],
                     "npcs":[{"id":"dealer_yah","x":W//2,"y":340,"name":"Dice Master Dan","col":"#e8d070",
                               "hat_col":"#3a3a00","body_col":"#2a2a00","line":"Roll up to 3 times.\nBest score wins cash!","game":"yahtzee"}]},
            "dice": {"title":"Dice Roll","floor":"#001a00","wall":"#000e00","decor_fn":dice_decor,
                     "furniture":[],"doors":[{"to":"lobby","x":460,"y":508,"w":180,"h":30,"col":"#333","label":"Back to Lobby"}],
                     "npcs":[{"id":"dealer_dice","x":W//2,"y":340,"name":"Lucky Lou","col":"#a0e890",
                               "hat_col":"#005000","body_col":"#004400","line":"One die each.\nHighest wins!","game":"dice_roll"}]},
        }

    def _make_stables_rooms(self):
        def decor(c):
            TT,TB,FX,SX=150,460,W-100,120; lh=(TB-TT)//5
            c.create_rectangle(SX,TT,FX,TB,fill="#8B6914",outline=DARK,width=3)
            for i in range(5):
                ly=TT+i*lh; c.create_line(SX,ly,FX,ly,fill="#6a4f10",width=2)
                for sx2 in range(SX,FX,40):
                    c.create_rectangle(sx2,ly,sx2+20,ly+lh,fill="#8B7214" if(sx2//40)%2==0 else"#9B8020",outline="")
            for fy in range(TT,TB,20):
                c.create_rectangle(FX-12,fy,FX,fy+20,fill="white" if(fy//20)%2==0 else"black",outline="")
            for i,(name,col) in enumerate(zip(HORSE_NAMES,HORSE_COLS)):
                c.create_text(SX-5,TT+i*lh+lh//2,text=f"{i+1}. {name}",fill=col,font=self.fnt_small,anchor="e")
        return {"main":{"title":"The Stables","floor":"#2a1a08","wall":"#1a0e04","decor_fn":decor,"furniture":[],
                        "doors":[{"to":"exit","x":460,"y":508,"w":180,"h":30,"col":"#333","label":"Exit Stables"}],
                        "npcs":[{"id":"jockey","x":W//2,"y":468,"name":"Jockey Sam","col":"#e8b070",
                                  "hat_col":"#8B0000","body_col":"#8B0000","line":"Pick a horse 1–5 then\nplace chips and DEAL!","game":"horse_race"}]}}

    def _make_shady_rooms(self):
        def decor(c):
            c.create_rectangle(0,60,W,H-30,fill="#060606")
            for gx2,gy2,gt,gc in [(150,200,"RISK","#cc2244"),(820,280,"LUCK","#44aacc"),(420,340,"DEAL","#88cc22"),(950,200,"SHADY","#cc8822")]:
                c.create_text(gx2,gy2,text=gt,fill=gc,font=self.fnt_title,angle=random.randint(-20,20))
            c.create_oval(W//2-25,74,W//2+25,112,fill="#997700",outline=GOLD)
            c.create_oval(W//2-20,79,W//2+20,107,fill="#ffee88",outline="")
        return {"main":{"title":"Shady Alley","floor":"#060606","wall":"#030303","decor_fn":decor,
                        "furniture":[{"type":"counter","bounds":(300,330,W-300,420)}],
                        "doors":[{"to":"exit","x":460,"y":508,"w":180,"h":30,"col":"#333","label":"Leave Alley"}],
                        "npcs":[{"id":"fixer","x":W//2,"y":314,"name":"The Fixer","col":"#a08060",
                                  "hat_col":"#111","body_col":"#222","line":"Need cash? I can help…\nfor a price.","game":"shady_deal"}]}}

    def _make_vip_rooms(self):
        def decor(c):
            for i in range(12):
                a=(i/12)*2*math.pi
                c.create_oval(W//2+300*math.cos(a)-5,300+200*math.sin(a)-5,
                              W//2+300*math.cos(a)+5,300+200*math.sin(a)+5,fill=GOLD,outline="")
            for chx in [200,W//2,W-200]:
                c.create_oval(chx-30,62,chx+30,120,fill="#ffcc22",outline=GOLD,width=2)
                c.create_text(chx,91,text="✦",fill="white",font=tkfont.Font(size=20))
            c.create_line(100,480,W-100,480,fill="#8B0000",width=5)
        return {"main":{"title":"VIP Lounge","floor":"#0a0020","wall":"#05000e","decor_fn":decor,"furniture":[],
                        "doors":[{"to":"exit","x":460,"y":508,"w":180,"h":30,"col":"#333","label":"Exit VIP"}],
                        "npcs":[{"id":"vip_host","x":W//2,"y":318,"name":"Host Vivienne","col":"#f0d0a0",
                                  "hat_col":PURPLE,"body_col":PURPLE,"line":"Welcome! Choose your\nexclusive game.","game":"vip_menu"}]}}

    def _make_bank_rooms(self):
        def decor(c):
            for cx2 in [200,380,W-380,W-200]:
                c.create_rectangle(cx2-18,130,cx2+18,480,fill="#cccccc",outline="#aaa",width=2)
                c.create_oval(cx2-22,120,cx2+22,148,fill="#bbbbbb",outline="#999")
            round_rect(c,150,330,W-150,460,r=12,fill="#8B6914",outline=GOLD,width=3)
        return {"main":{"title":"The Bank","floor":"#001020","wall":"#000810","decor_fn":decor,
                        "furniture":[{"type":"counter","bounds":(150,330,W-150,460)}],
                        "doors":[{"to":"exit","x":460,"y":508,"w":180,"h":30,"col":"#333","label":"Leave Bank"}],
                        "npcs":[{"id":"teller","x":W//2,"y":314,"name":"Teller Grace","col":"#e0c8a0",
                                  "hat_col":"#001020","body_col":"#001a30","line":"Good day! Want to see\nyour account statement?","game":"bank_stats"}]}}

    def _make_arena_rooms(self):
        def decor(c):
            c.create_rectangle(80,155,W-80,455,fill="#8B7355",outline="#4a3a1a",width=3)
            for _ in range(20):
                sx=random.randint(90,W-90); sy=random.randint(165,445)
                c.create_oval(sx,sy,sx+4,sy+2,fill="#9a8060",outline="")
            c.create_rectangle(0,60,W,160,fill="#2a0a00",outline="")
            for cx2 in range(30,W-20,22):
                h=random.randint(20,50); gy=155-h
                col=random.choice(["#3a1a00","#4a2a10","#2a1000","#3a0800"])
                c.create_oval(cx2-8,gy-12,cx2+8,gy+2,fill=col,outline="")
                c.create_rectangle(cx2-6,gy+2,cx2+6,gy+h,fill=col,outline="")
            c.create_text(W//2,120,text="THE ARENA — Funky Feet Fights",fill=RED_C,
                          font=tkfont.Font(family="Georgia",size=18,weight="bold"))
            c.create_text(W-10,165,anchor="ne",
                          text=f"Stage {self.fight_stage+1}/5 — {ENEMY_NAMES[min(self.fight_stage,4)]} | HP:{self.player_health}",
                          fill=GOLD,font=self.fnt_small)
        return {"main":{"title":"The Arena","floor":"#3a2a10","wall":"#1a1000","decor_fn":decor,"furniture":[],
                        "doors":[{"to":"exit","x":460,"y":540,"w":180,"h":30,"col":"#333","label":"Exit Arena"}],
                        "npcs":[
                            {"id":"promoter","x":200,"y":390,"name":"Promoter Pete","col":"#c8a060",
                             "hat_col":"#2a0000","body_col":"#5a0000","line":"Bet on the brawl!\nPick a side and wager.","game":"arena_bet"},
                            {"id":"fight_master","x":W//2,"y":360,"name":"Fight Master","col":"#e06040",
                             "hat_col":"#1a0000","body_col":"#2a0000","line":"Funky Feet Fights!\n5 enemies await you.","game":"arena_fight"},
                            {"id":"chef","x":W-200,"y":390,"name":"Chef Mario","col":"#e8c090",
                             "hat_col":"#ffffff","body_col":"#ffffff","line":"Roughhouse Restaurant\nis open!","game":"arena_restaurant"},
                        ]}}
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
            round_rect(c,x,y,x+62,y+92,r=6,fill="white",outline="#ccc",width=1,tags="cards")
            if rank is None:
                round_rect(c,x+4,y+4,x+58,y+88,r=5,fill="#8B0000",outline="",tags="cards")
            else:
                col=CARD_SUITS[suit]
                c.create_text(x+9,y+13,text=rank,fill=col,font=self.fnt_card,anchor="w",tags="cards")
                c.create_text(x+31,y+52,text=suit,fill=col,font=tkfont.Font(size=22),anchor="center",tags="cards")
                c.create_text(x+53,y+79,text=rank,fill=col,font=tkfont.Font(size=11),anchor="e",tags="cards")
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
        def draw_spin_overlay():
            c.delete("spin_layer")
            a=spin_angle[0]
            for i in range(37):
                seg_a=(i/37)*360
                if golden: col=("#00aa00" if i==0 else("#d4a020" if i in RED_NUMS else "#2a2a3a"))
                else: col="#006000" if i==0 else("#c0392b" if i in RED_NUMS else "#1a1a1a")
                c.create_arc(WX-WR,WY-WR,WX+WR,WY+WR,start=seg_a+a,extent=360/37,fill=col,outline="white",width=1,style="pie",tags="spin_layer")
                rad=math.radians(seg_a+a+360/37/2)
                c.create_text(WX+(WR*0.7)*math.cos(rad),WY-(WR*0.7)*math.sin(rad),text=str(i),fill="white",font=tkfont.Font(size=7,weight="bold"),tags="spin_layer")
            brad=math.radians(ball_angle[0])
            bx=WX+(WR-15)*math.cos(brad); by=WY-(WR-15)*math.sin(brad)
            c.create_oval(bx-7,by-7,bx+7,by+7,fill="white",outline="silver",width=2,tags="spin_layer")
            c.create_oval(WX-18,WY-18,WX+18,WY+18,fill=GOLD,outline=DARK,width=2,tags="spin_layer")
        def on_deal(bet):
            try: player_num=int(num_entry.get()); assert 0<=player_num<=36
            except: self._msg("Invalid number (0-36)",RED_C); self._show_hotbar(on_deal); return
            player_col=col_var.get(); result=random.randint(0,36)
            result_col="Green" if result==0 else("Red" if result in RED_NUMS else "Black")
            ticks=[0]
            def animate():
                t=ticks[0]; speed=12 if t<20 else max(2,12-(t-20)*0.5)
                spin_angle[0]=(spin_angle[0]+speed)%360; ball_angle[0]=(ball_angle[0]+speed*1.3)%360
                draw_spin_overlay(); ticks[0]+=1
                if t<40: self.after(30,animate)
                else:
                    both=player_col==result_col and player_num==result
                    colour_match=player_col==result_col
                    num_match=player_num==result
                    jx=20 if golden else 36; cx2=3 if golden else 1; nx=10 if golden else 17
                    if both:
                        gain=bet*jx; self.money+=gain; self._msg(f"JACKPOT! {result} {result_col}! +${gain}",GREEN_C); self._post_game(gain,"win")
                    elif colour_match:
                        gain=bet*cx2; self.money+=gain; self._msg(f"Colour! {result} {result_col}. +${gain}",GREEN_C); self._post_game(gain,"win")
                    elif num_match:
                        gain=bet*nx; self.money+=gain; self._msg(f"Number match! +${gain}",GREEN_C); self._post_game(gain,"win")
                    else:
                        self.money-=bet; self._msg(f"{result} {result_col}. -${bet}",RED_C); self._post_game(bet,"loss")
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
            round_rect(c,x,y,x+size,y+size,r=10,fill="white",outline="#ccc",width=2,tags="dice_img")
            pips={1:[(0.5,0.5)],2:[(0.25,0.25),(0.75,0.75)],3:[(0.25,0.25),(0.5,0.5),(0.75,0.75)],
                  4:[(0.25,0.25),(0.75,0.25),(0.25,0.75),(0.75,0.75)],
                  5:[(0.25,0.25),(0.75,0.25),(0.5,0.5),(0.25,0.75),(0.75,0.75)],
                  6:[(0.25,0.2),(0.75,0.2),(0.25,0.5),(0.75,0.5),(0.25,0.8),(0.75,0.8)]}
            pr=size*0.1
            for px2,py2 in pips.get(val,[]):
                cx2=x+px2*size; cy2=y+py2*size
                c.create_oval(cx2-pr,cy2-pr,cx2+pr,cy2+pr,fill=DARK,outline="",tags="dice_img")
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
                for rx,ry,rk,rs in [(W//2,222,dr,ds),(W//2,390,pr,ps)]:
                    round_rect(c,rx-45,ry-70,rx+45,ry+70,r=10,fill="white",outline="#ccc",width=2,tags="war_cards")
                    col=CARD_SUITS[rs]
                    c.create_text(rx-28,ry-55,text=rk,fill=col,font=tkfont.Font(size=22,weight="bold"),tags="war_cards")
                    c.create_text(rx,ry,text=rs,fill=col,font=tkfont.Font(size=36),tags="war_cards")
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
                for cx2,cy2,rk,rs,lbl in [(W//2-130,308,dr,ds,"DEALER"),(W//2+130,308,pr,ps,"YOU")]:
                    round_rect(c,cx2-50,cy2-75,cx2+50,cy2+75,r=10,fill="white",outline="#ccc",width=2,tags="hc_cards")
                    col=CARD_SUITS[rs]
                    c.create_text(cx2-32,cy2-58,text=rk,fill=col,font=tkfont.Font(size=20,weight="bold"),tags="hc_cards")
                    c.create_text(cx2,cy2,text=rs,fill=col,font=tkfont.Font(size=34),tags="hc_cards")
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
            round_rect(c,x,y,x+size,y+size,r=12,fill="white",outline="#ccc",width=3,tags=tag)
            pips={1:[(0.5,0.5)],2:[(0.25,0.25),(0.75,0.75)],3:[(0.25,0.25),(0.5,0.5),(0.75,0.75)],
                  4:[(0.25,0.25),(0.75,0.25),(0.25,0.75),(0.75,0.75)],
                  5:[(0.25,0.25),(0.75,0.25),(0.5,0.5),(0.25,0.75),(0.75,0.75)],
                  6:[(0.2,0.2),(0.8,0.2),(0.2,0.5),(0.8,0.5),(0.2,0.8),(0.8,0.8)]}
            pr=size*0.09
            for px2,py2 in pips.get(val,[]):
                c.create_oval(x+px2*size-pr,y+py2*size-pr,x+px2*size+pr,y+py2*size+pr,fill=DARK,outline="",tags=tag)
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
            round_rect(c,x,y,x+56,y+82,r=6,fill="white",outline="#ccc",width=1,tags=tag)
            if rank is None:
                round_rect(c,x+4,y+4,x+52,y+78,r=5,fill="#8B0000",outline="",tags=tag)
            else:
                col=CARD_SUITS.get(suit,"black")
                c.create_text(x+8,y+12,text=rank,fill=col,font=self.fnt_card,anchor="w",tags=tag)
                c.create_text(x+28,y+46,text=suit,fill=col,font=tkfont.Font(size=18),anchor="center",tags=tag)
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
        # Heist
        if self.debt>0 and random.randint(1,5)==1:
            c.create_line(W//2-280,500,W//2+280,500,fill="#333",width=1)
            c.create_text(W//2,520,text="A stranger approaches with an offer…",fill="#666",font=self.fnt_small,anchor="center")
            self._make_btn(W//2,550,"HEAR THE OFFER",self._heist_event,col="#0a0a00",fg=GOLD,w=160)
        self._make_btn(W//2,628,"Leave",self._back_to_interior,col="#222",fg="#888",w=80)

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
        self._draw_room_bg("DOUBLE OR NOTHING","#0a0020","#140038")
        c.create_text(W//2,120,text="Risk everything — double or lose it all.",fill=CREAM,font=self.fnt_body)
        c.create_text(W//2,160,text=f"Your balance: ${self.money:,}",fill=GOLD,font=self.fnt_body,tags="vip_bal")
        c.create_text(W//2,200,text="Win chance: 45%",fill="#888",font=self.fnt_small)
        def do_double():
            if self.money<=0: self._msg("You need money to risk!",RED_C); return
            gain=self.money
            if random.random()>0.45:
                self.money*=2
                self._post_game(gain,"win"); self._msg(f"DOUBLED! +${gain:,}. Balance: ${self.money:,}",GREEN_C)
            else:
                self._post_game(self.money,"loss"); self.money=0
                self._msg("Lost it all!",RED_C)
            self._refresh_balance_text()
            c.delete("vip_bal")
            c.create_text(W//2,160,text=f"Your balance: ${self.money:,}",fill=GOLD,font=self.fnt_body,tags="vip_bal")
        self._make_btn(W//2,300,"DOUBLE OR NOTHING",do_double,col=PURPLE,fg="white",w=220)
        self._make_btn(W//2,375,"Back to VIP Menu",self._vip_screen,col="#333",fg=CREAM,w=170)

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

    # ── ARENA FIGHT (NEW) ─────────────────────────────────
    def _arena_fight_screen(self):
        self._cancel_pending_afters()
        self._clear_overlay(); c=self.canvas
        if self.fight_stage>=5:
            self._draw_room_bg("ARENA CHAMPION","#1a0000","#2a0000")
            c.create_text(W//2,200,text="🏆  CHAMPION! 🏆",fill=GOLD,font=self.fnt_huge,anchor="center")
            c.create_text(W//2,280,text="You defeated all 5 enemies!",fill=CREAM,font=self.fnt_body,anchor="center")
            c.create_text(W//2,320,text="Fat Tony lies defeated. The crowd goes wild.",fill=CREAM,font=self.fnt_body,anchor="center")
            prize=5000; self.money+=prize
            c.create_text(W//2,380,text=f"Prize Money: +${prize:,}",fill=GOLD,font=self.fnt_title,anchor="center")
            self._refresh_balance_text(); self._post_game(prize,"win")
            self.fight_stage=0; self.enemy_hp=list(ENEMY_MAX_HP); self.player_health=100
            self._make_btn(W//2,460,"Fight again from Stage 1",self._arena_fight_screen,col=RED_C,fg="white",w=210)
            self._make_btn(W//2,525,"Back to Arena",self._back_to_interior,col="#333",fg=CREAM,w=140)
            return
        if self.player_health<=0:
            self._draw_room_bg("KNOCKED OUT","#1a0000","#2a0000")
            c.create_text(W//2,250,text="💀  YOU WERE KNOCKED OUT  💀",fill=RED_C,font=self.fnt_title,anchor="center")
            c.create_text(W//2,310,text="Visit the restaurant to restore HP.",fill=CREAM,font=self.fnt_body,anchor="center")
            self.player_health=30  # restore a little
            self._make_btn(W//2,400,"Back to Arena",self._back_to_interior,col="#333",fg=CREAM,w=140)
            return
        self._draw_room_bg("FUNKY FEET FIGHTS","#0a0000","#1a0000")
        enemy_idx=min(self.fight_stage,4)
        enemy_name=ENEMY_NAMES[enemy_idx]; enemy_max=ENEMY_MAX_HP[enemy_idx]
        e_hp=self.enemy_hp[enemy_idx]
        # Health bars
        def draw_bars():
            c.delete("bars")
            bw=420; bh=28
            ex,ey=W//2+100,140
            c.create_rectangle(ex,ey,ex+bw,ey+bh,fill="#1a0000",outline=RED_C,width=2,tags="bars")
            c.create_rectangle(ex,ey,ex+int(bw*e_hp/enemy_max),ey+bh,fill=RED_C,outline="",tags="bars")
            c.create_text(ex+bw//2,ey+bh//2,text=f"{enemy_name}  {e_hp}/{enemy_max}",fill="white",font=self.fnt_small,tags="bars")
            px2,py2=W//2-540,140
            c.create_rectangle(px2,py2,px2+bw,py2+bh,fill="#001a00",outline=GREEN_C,width=2,tags="bars")
            c.create_rectangle(px2,py2,px2+int(bw*self.player_health/100),py2+bh,fill=GREEN_C,outline="",tags="bars")
            c.create_text(px2+bw//2,py2+bh//2,text=f"YOU  {self.player_health}/100",fill="white",font=self.fnt_small,tags="bars")
        draw_bars()
        c.create_text(W//2,100,text=f"STAGE {self.fight_stage+1} — {enemy_name.upper()}",fill=RED_C,
                      font=tkfont.Font(family="Georgia",size=22,weight="bold"))
        c.create_text(W//2,200,text="A button will flash — CLICK IT FAST!",fill=CREAM,font=self.fnt_body)
        c.create_text(W//2,230,text="If you're too slow, the enemy strikes back.",fill="#888",font=self.fnt_small)
        # Attack round mini-game
        attack_active=[False]; miss_after_id=[None]; btn_ref=[None]
        status_id=c.create_text(W//2,320,text="Get ready…",fill=GOLD,font=self.fnt_title)
        rounds=[0]; max_rounds=5
        def schedule_next_round():
            if rounds[0]>=max_rounds: end_fight(); return
            c.itemconfig(status_id,text=f"Round {rounds[0]+1}/{max_rounds}  —  WAIT…",fill=GOLD)
            delay=random.randint(1800,4200)
            aid=self.after(delay,show_attack_btn); self._pending_after.append(aid)
        def show_attack_btn():
            if self.screen!="game": return
            attack_active[0]=True
            bx=random.randint(180,W-180); by=random.randint(350,540)
            b=tk.Button(self,text="⚡ ATTACK!",command=do_hit,
                        font=tkfont.Font(family="Georgia",size=16,weight="bold"),
                        bg=RED_C,fg="white",activebackground="#8B0000",
                        relief="flat",cursor="hand2",width=14)
            self.canvas.create_window(bx,by,window=b)
            self._overlay_widgets.append(b); btn_ref[0]=b
            c.itemconfig(status_id,text=f"Round {rounds[0]+1}/{max_rounds}  —  ATTACK NOW!",fill=RED_C)
            mid2=self.after(1000,lambda:do_miss())
            miss_after_id[0]=mid2; self._pending_after.append(mid2)
        def do_hit():
            if not attack_active[0]: return
            attack_active[0]=False
            if miss_after_id[0]:
                try: self.after_cancel(miss_after_id[0])
                except: pass
            if btn_ref[0]:
                try: btn_ref[0].destroy()
                except: pass
                self._overlay_widgets.discard(btn_ref[0]) if hasattr(self._overlay_widgets,'discard') else None
                try: self._overlay_widgets.remove(btn_ref[0])
                except: pass
            dmg=random.randint(8,25)
            self.enemy_hp[enemy_idx]=max(0,self.enemy_hp[enemy_idx]-dmg)
            e_hp=self.enemy_hp[enemy_idx]
            c.itemconfig(status_id,text=f"You hit for {dmg}! Enemy HP: {e_hp}",fill=GREEN_C)
            draw_bars()
            rounds[0]+=1
            if self.enemy_hp[enemy_idx]<=0:
                self.after(700,enemy_defeated)
            else:
                self.after(900,schedule_next_round)
        def do_miss():
            if not attack_active[0]: return
            attack_active[0]=False
            if btn_ref[0]:
                try: btn_ref[0].destroy()
                except: pass
                try: self._overlay_widgets.remove(btn_ref[0])
                except: pass
            dmg=random.randint(5,18)
            self.player_health=max(0,self.player_health-dmg)
            c.itemconfig(status_id,text=f"Too slow! Took {dmg} damage. Your HP: {self.player_health}",fill=RED_C)
            draw_bars()
            rounds[0]+=1
            if self.player_health<=0:
                self.after(700,lambda:self._arena_fight_screen())
            elif self.enemy_hp[enemy_idx]<=0:
                self.after(700,enemy_defeated)
            else:
                self.after(900,schedule_next_round)
        def end_fight():
            # Out of rounds, compare remaining HP
            e_remain=self.enemy_hp[enemy_idx]/enemy_max
            p_remain=self.player_health/100
            if p_remain>e_remain:
                c.itemconfig(status_id,text="Time's up — you had more HP! You win the round.",fill=GREEN_C)
                self.after(1200,enemy_defeated)
            else:
                c.itemconfig(status_id,text="Time's up — enemy wins the round!",fill=RED_C)
                self.after(1200,lambda:self._arena_fight_screen())
        def enemy_defeated():
            self._cancel_pending_afters(); self._clear_overlay()
            prize=100+self.fight_stage*75; self.money+=prize
            self.fight_stage+=1; self.enemy_hp[enemy_idx]=enemy_max  # reset that enemy
            msg=f"{enemy_name} DEFEATED! +${prize}" if self.fight_stage<5 else "FAT TONY DEFEATED! CHAMPION!"
            c.itemconfig(status_id,text=msg,fill=GOLD)
            self._refresh_balance_text()
            if self.fight_stage<5:
                self._make_btn(W//2,600,f"Fight Stage {self.fight_stage+1}: {ENEMY_NAMES[self.fight_stage]}",
                               self._arena_fight_screen,col=RED_C,fg="white",w=280)
                self._make_btn(W//2,650,"Take a break (Arena lobby)",self._back_to_interior,col="#333",fg=CREAM,w=220)
            else:
                self.after(600,self._arena_fight_screen)
        schedule_next_round()

    # ── ARENA BET (NEW) ───────────────────────────────────
    def _arena_bet_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("BET ON THE BRAWL","#0a0000","#1a0000")
        f1,f2=random.sample(ENEMY_NAMES,2)
        c.create_text(W//2,130,text="Two fighters will brawl. Pick the winner!",fill=CREAM,font=self.fnt_body)
        c.create_text(W//2-220,220,text=f1,fill=RED_C,font=self.fnt_title)
        c.create_text(W//2+220,220,text=f2,fill=BLUE_C,font=self.fnt_title)
        c.create_text(W//2,220,text="VS",fill=GOLD,font=self.fnt_huge)
        chosen=[None]
        def pick(fighter): chosen[0]=fighter; c.delete("pick_lbl"); c.create_text(W//2,290,text=f"Picked: {fighter}",fill=GOLD,font=self.fnt_body,tags="pick_lbl")
        self._make_btn(W//2-220,270,f"Pick {f1}",lambda:pick(f1),col="#5a0000",fg="white",w=150)
        self._make_btn(W//2+220,270,f"Pick {f2}",lambda:pick(f2),col="#00004a",fg="white",w=150)
        def on_deal(bet):
            if not chosen[0]: self._msg("Pick a fighter first!",RED_C); self._show_hotbar(on_deal); return
            winner=random.choice([f1,f2])
            c.create_text(W//2,400,text=f"Winner: {winner}!",fill=GOLD,font=self.fnt_title)
            if chosen[0]==winner:
                self.money+=bet; self._msg(f"Correct! +${bet}",GREEN_C); self._post_game(bet,"win")
            else:
                self.money-=bet; self._msg(f"Wrong pick. -${bet}",RED_C); self._post_game(bet,"loss")
            self._refresh_balance_text()
            self._make_btn(W//2-70,500,"BET AGAIN",self._arena_bet_screen)
            self._make_btn(W//2+80,500,"BACK",self._back_to_interior,col="#333",fg=CREAM,w=80)
        self._show_hotbar(on_deal)

    # ── ARENA RESTAURANT (NEW) ────────────────────────────
    def _arena_restaurant_screen(self):
        self._clear_overlay(); c=self.canvas
        self._draw_room_bg("ROUGHHOUSE RESTAURANT","#0a0500","#150a00")
        c.create_text(W//2,110,text="Restore your Health Points before the next fight!",fill=CREAM,font=self.fnt_body)
        c.create_text(W//2,140,text=f"Your HP: {self.player_health}/100  |  Your Balance: ${self.money:,}",
                      fill=GOLD,font=self.fnt_small,tags="rest_lbl")
        def refresh():
            c.delete("rest_lbl")
            c.create_text(W//2,140,text=f"Your HP: {self.player_health}/100  |  Your Balance: ${self.money:,}",
                          fill=GOLD,font=self.fnt_small,tags="rest_lbl")
        y=185
        for name,cost,hp_gain,desc in RESTAURANT_MENU:
            can_afford=self.money>=cost
            col=GREEN_C if can_afford else "#333"
            c.create_text(W//2-320,y+10,text=f"{name}  —  ${cost:,}  (+{hp_gain}HP)",
                          fill=CREAM,font=self.fnt_body,anchor="w")
            c.create_text(W//2-320,y+30,text=desc,fill="#888",font=self.fnt_small,anchor="w")
            def mk(n=name,cc=cost,hg=hp_gain):
                def buy():
                    if self.money<cc: self._msg(f"Can't afford {n}.",RED_C,y=580); return
                    self.money-=cc; self.player_health=min(100,self.player_health+hg)
                    self._msg(f"Ate {n}! +{hg}HP. HP now: {self.player_health}",GREEN_C,y=580)
                    self._refresh_balance_text(); refresh()
                return buy
            self._make_btn(W//2+270,y+18,f"Buy ${cost:,}",mk(),col=col,fg=DARK if can_afford else "#555",w=120)
            y+=65
        self._make_btn(W//2,y+20,"Back to Arena",self._back_to_interior,col="#333",fg=CREAM,w=140)
    # ── BOSS ENCOUNTER (NEW) ──────────────────────────────
    def _boss_encounter(self):
        if self.screen not in("game","interior","town"): return
        c=self.canvas
        c.create_rectangle(80,60,W-80,H-60,fill="#020000",outline=RED_C,width=4,tags="boss_pop")
        c.create_text(W//2,120,text="⚠   THE BOSS   ⚠",fill=RED_C,font=self.fnt_huge,anchor="center",tags="boss_pop")
        c.create_line(100,158,W-100,158,fill=RED_C,width=2,tags="boss_pop")
        if self.boss_alert_level>=4:
            take=min(int(self.debt*0.25)+50,max(0,self.money))
            self.money-=take; self.debt=max(0,self.debt-take)
            lines=[f"You've ignored your debt for too long.",
                   f"I'm collecting ${take:,} as a down payment.",
                   f"Remaining debt: ${self.debt:,}"]
        else:
            lines=[f"A black SUV idles outside your building...",
                   f"A suited man leans through the window.",
                   f"'You owe me ${self.debt:,}. Don't make me wait.'",
                   f"'Alert level: {self.boss_alert_level}/5'"]
        for i,ln in enumerate(lines):
            c.create_text(W//2,195+i*55,text=ln,fill=CREAM,font=self.fnt_body,anchor="center",tags="boss_pop")
        def dismiss():
            c.delete("boss_pop")
            for w in list(self._overlay_widgets):
                try: w.destroy()
                except: pass
            self._overlay_widgets.clear()
            self._refresh_balance_text()
        self._make_btn(W//2,H-100,"Understood.",dismiss,col="#333",fg=CREAM,w=130)

    # ── HEIST EVENT (NEW) ─────────────────────────────────
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
                self.after(400,self._t_code)   # ← T CODE RUNS HERE
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

if __name__=="__main__":
    app=CasinoApp()
    app.mainloop()
