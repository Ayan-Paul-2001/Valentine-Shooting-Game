import pygame, random, math, sys, json, os, time
import numpy as np

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

W, H = 1000, 700
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Valentine Shooter")
clock = pygame.time.Clock()

# ══ SOUND GENERATION ══
def generate_gunshot():
    """Generate gunshot sound effect"""
    sample_rate = 22050
    duration = 0.15
    samples = int(sample_rate * duration)
    # White noise with envelope
    noise = np.random.uniform(-1, 1, samples)
    # Exponential decay envelope
    envelope = np.exp(-np.linspace(0, 8, samples))
    sound_array = (noise * envelope * 32767 * 0.3).astype(np.int16)
    # Stereo
    stereo = np.column_stack((sound_array, sound_array))
    return pygame.sndarray.make_sound(stereo)

def generate_hit():
    """Generate hit impact sound effect"""
    sample_rate = 22050
    duration = 0.2
    samples = int(sample_rate * duration)
    # Mix of frequencies for impact
    t = np.linspace(0, duration, samples)
    freq1 = 800 * np.exp(-t * 15)  # Descending pitch
    freq2 = 400 * np.exp(-t * 10)
    wave = np.sin(2 * np.pi * freq1 * t) * 0.5 + np.sin(2 * np.pi * freq2 * t) * 0.3
    # Add some noise
    noise = np.random.uniform(-0.2, 0.2, samples)
    combined = wave + noise
    # Envelope
    envelope = np.exp(-t * 8)
    sound_array = (combined * envelope * 32767 * 0.4).astype(np.int16)
    stereo = np.column_stack((sound_array, sound_array))
    return pygame.sndarray.make_sound(stereo)

def generate_applause():
    """Generate applause/clapping sound effect"""
    sample_rate = 22050
    duration = 2.5
    samples = int(sample_rate * duration)
    # Create multiple clap bursts
    sound = np.zeros(samples)
    # Random claps throughout
    for _ in range(150):  # Number of individual claps
        clap_pos = np.random.randint(0, samples - 500)
        clap_duration = np.random.randint(50, 150)
        # Each clap is a short burst of noise
        clap = np.random.uniform(-1, 1, clap_duration)
        # Envelope for each clap
        clap_env = np.exp(-np.linspace(0, 5, clap_duration))
        clap *= clap_env
        # Add to sound
        end_pos = min(clap_pos + clap_duration, samples)
        sound[clap_pos:end_pos] += clap[:end_pos - clap_pos] * 0.15
    # Overall envelope (fade in and out)
    overall_env = np.ones(samples)
    fade_in = int(sample_rate * 0.3)
    fade_out = int(sample_rate * 0.5)
    overall_env[:fade_in] = np.linspace(0, 1, fade_in)
    overall_env[-fade_out:] = np.linspace(1, 0, fade_out)
    sound *= overall_env
    # Clip and convert
    sound = np.clip(sound, -1, 1)
    sound_array = (sound * 32767 * 0.5).astype(np.int16)
    stereo = np.column_stack((sound_array, sound_array))
    return pygame.sndarray.make_sound(stereo)

# Generate sounds
try:
    sound_shoot = generate_gunshot()
    sound_hit = generate_hit()
    sound_applause = generate_applause()
except:
    # Fallback if numpy/sndarray not available
    sound_shoot = None
    sound_hit = None
    sound_applause = None

# Colors
WHITE=(255,255,255); BLACK=(0,0,0); RED=(220,50,60); DARK_RED=(140,20,30)
PINK=(255,105,140); DEEP_PINK=(255,20,100); LIGHT_PINK=(255,182,193)
GOLD=(255,215,0); GREEN=(50,205,50); GRAY=(150,150,150); DARK_GRAY=(60,60,60)
ORANGE=(255,165,0); PURPLE=(180,100,255); CYAN=(0,255,255)
SKIN=(255,219,172); SKIN_SH=(220,185,145); SKIN_HI=(255,235,200)
HAIR_BRN=(45,25,10); HAIR_HI=(80,50,25)
DRESS_R=(180,30,55); DRESS_D=(130,18,40); DRESS_L=(210,60,85)
WOOD_L=(160,110,60); WOOD_D=(110,70,35); WOOD_DD=(80,50,25)
SKY_T=(8,6,25); SKY_B=(25,12,40); GND_T=(35,60,25); GND_B=(20,40,15)

# Fonts
f_title=pygame.font.SysFont("impact",64)
f_xl=pygame.font.SysFont("segoe ui",48,True)
f_lg=pygame.font.SysFont("segoe ui",32,True)
f_md=pygame.font.SysFont("segoe ui",24,True)
f_sm=pygame.font.SysFont("segoe ui",18)
f_xs=pygame.font.SysFont("segoe ui",14)

SCORE_FILE=os.path.join(os.path.dirname(os.path.abspath(__file__)),"scores.json")
LEVEL_COLORS={"Easy":GREEN,"Medium":ORANGE,"Hard":RED}

def load_scores():
    try:
        with open(SCORE_FILE,"r") as f: return json.load(f)
    except: return []

def save_score(sc,lv):
    ss=load_scores()
    ss.append({"score":sc,"level":lv,"time":time.strftime("%Y-%m-%d %H:%M")})
    ss.sort(key=lambda x:x["score"],reverse=True)
    with open(SCORE_FILE,"w") as f: json.dump(ss[:10],f)

# ── Drawing Helpers ──
def lerp_c(c1,c2,t): return tuple(int(a+(b-a)*t) for a,b in zip(c1,c2))

def draw_grad(sf,rect,ct,cb):
    x,y,w,h=rect
    for r in range(h):
        t=r/max(1,h-1)
        pygame.draw.line(sf,lerp_c(ct,cb,t),(x,y+r),(x+w,y+r))

def draw_heart(sf,cx,cy,sz,col):
    s=sz/10; pts=[]
    for i in range(80):
        t=i/80*2*math.pi
        px=16*math.sin(t)**3
        py=-(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))
        pts.append((cx+px*s,cy+py*s))
    if len(pts)>2: pygame.draw.polygon(sf,col,pts)

def draw_sky(sf,fr):
    draw_grad(sf,(0,0,W,H),SKY_T,SKY_B)
    pygame.draw.circle(sf,(240,235,200),(W-120,80),40)
    pygame.draw.circle(sf,(220,215,180),(W-115,75),38)
    pygame.draw.circle(sf,SKY_T,(W-100,70),35)
    rng=random.Random(42)
    for i in range(70):
        sx,sy=rng.randint(0,W),rng.randint(0,H-180)
        fl=0.5+0.5*math.sin(fr*0.04+i*1.3)
        b=int(120+135*fl); r=1 if i%4 else 2
        pygame.draw.circle(sf,(b,b,min(255,b+30)),(sx,sy),r)

def draw_ground(sf):
    gy=H-90
    draw_grad(sf,(0,gy,W,90),GND_T,GND_B)
    rng=random.Random(99)
    for i in range(0,W,7):
        gh=rng.randint(4,18); gl=rng.randint(-3,3); gs=rng.randint(0,25)
        pygame.draw.line(sf,(30+gs,75+gs,18),(i,gy),(i+gl,gy-gh),2)
    for x in range(50,W,130):
        pygame.draw.rect(sf,WOOD_D,(x-5,gy-50,10,55))
        pygame.draw.rect(sf,WOOD_L,(x-4,gy-48,3,52))
        pygame.draw.circle(sf,WOOD_DD,(x,gy-50),6)
        pygame.draw.circle(sf,WOOD_L,(x,gy-50),4)
    pygame.draw.line(sf,WOOD_D,(0,gy-28),(W,gy-28),4)
    pygame.draw.line(sf,WOOD_L,(0,gy-27),(W,gy-27),2)
    pygame.draw.line(sf,WOOD_D,(0,gy-42),(W,gy-42),4)
    pygame.draw.line(sf,WOOD_L,(0,gy-41),(W,gy-41),2)

# ── REALISTIC DOLL ──
def draw_doll(sf,cx,cy,scale=1.0,hit=False):
    s=scale
    if hit:
        SK=GRAY;SS=DARK_GRAY;SH=(120,120,120)
        HR=DARK_GRAY;HH=(80,80,80);DR=(100,100,100);DD=(80,80,80);DL=(120,120,120)
        BW=DARK_GRAY
    else:
        SK=SKIN;SS=SKIN_SH;SH=SKIN_HI
        HR=HAIR_BRN;HH=HAIR_HI;DR=DRESS_R;DD=DRESS_D;DL=DRESS_L
        BW=DEEP_PINK

    # Shadow on ground
    sh_sf=pygame.Surface((int(60*s),int(10*s)),pygame.SRCALPHA)
    pygame.draw.ellipse(sh_sf,(0,0,0,40),(0,0,int(60*s),int(10*s)))
    sf.blit(sh_sf,(cx-int(30*s),cy+int(72*s)))

    # Stand
    pt=cy+int(38*s); pb=cy+int(75*s)
    pygame.draw.rect(sf,WOOD_DD,(cx-int(4*s),int(pt),int(8*s),int(pb-pt)))
    pygame.draw.rect(sf,WOOD_D,(cx-int(3*s),int(pt),int(6*s),int(pb-pt)))
    pygame.draw.rect(sf,WOOD_L,(cx-int(1*s),int(pt),int(2*s),int(pb-pt)))
    pygame.draw.ellipse(sf,WOOD_DD,(cx-int(20*s),int(pb)-3,int(40*s),12))
    pygame.draw.ellipse(sf,WOOD_D,(cx-int(18*s),int(pb)-2,int(36*s),9))
    pygame.draw.ellipse(sf,WOOD_L,(cx-int(10*s),int(pb)-1,int(20*s),5))

    # Back hair (behind body)
    pygame.draw.ellipse(sf,HR,(cx-int(18*s),cy-int(32*s),int(36*s),int(50*s)))

    # Legs
    pygame.draw.line(sf,SS,(cx-int(6*s),cy+int(32*s)),(cx-int(8*s),cy+int(40*s)),max(1,int(3*s)))
    pygame.draw.line(sf,SS,(cx+int(6*s),cy+int(32*s)),(cx+int(8*s),cy+int(40*s)),max(1,int(3*s)))
    # Shoes
    sc2=(50,25,15) if not hit else DARK_GRAY
    pygame.draw.ellipse(sf,sc2,(cx-int(13*s),cy+int(38*s),int(10*s),int(5*s)))
    pygame.draw.ellipse(sf,sc2,(cx+int(3*s),cy+int(38*s),int(10*s),int(5*s)))

    # Dress skirt
    sk_pts=[(cx-int(14*s),cy+int(10*s))]
    for i in range(15):
        t=i/14; ang=math.pi*t
        sx2=cx+int((-22+44*t)*s); sy2=cy+int((34+3*math.sin(ang*4))*s)
        sk_pts.append((sx2,sy2))
    sk_pts.append((cx+int(14*s),cy+int(10*s)))
    pygame.draw.polygon(sf,DR,sk_pts)
    # Skirt shading
    sh_pts=[(cx-int(14*s),cy+int(10*s)),(cx-int(22*s),cy+int(34*s)),
            (cx-int(3*s),cy+int(34*s)),(cx-int(3*s),cy+int(10*s))]
    pygame.draw.polygon(sf,DD,sh_pts)
    hi_pts=[(cx+int(4*s),cy+int(14*s)),(cx+int(8*s),cy+int(32*s)),
            (cx+int(16*s),cy+int(32*s)),(cx+int(12*s),cy+int(14*s))]
    pygame.draw.polygon(sf,DL,hi_pts)
    # Skirt hem
    for i in range(6):
        rx=cx+int((-18+i*7)*s)
        pygame.draw.arc(sf,DD,(rx,cy+int(32*s),int(8*s),int(5*s)),math.pi,2*math.pi,max(1,int(1*s)))

    # Upper body / bodice
    bd=[(cx-int(11*s),cy-int(4*s)),(cx-int(14*s),cy+int(12*s)),
        (cx+int(14*s),cy+int(12*s)),(cx+int(11*s),cy-int(4*s))]
    pygame.draw.polygon(sf,DR,bd)
    pygame.draw.polygon(sf,DD,[(cx-int(11*s),cy-int(4*s)),(cx-int(14*s),cy+int(12*s)),
        (cx-int(4*s),cy+int(12*s)),(cx-int(4*s),cy-int(4*s))])

    # Collar detail
    pygame.draw.line(sf,DD,(cx-int(6*s),cy-int(4*s)),(cx,cy+int(4*s)),max(1,int(1*s)))
    pygame.draw.line(sf,DD,(cx+int(6*s),cy-int(4*s)),(cx,cy+int(4*s)),max(1,int(1*s)))

    # Belt + bow
    pygame.draw.rect(sf,BW,(cx-int(14*s),cy+int(10*s),int(28*s),int(4*s)))
    pygame.draw.ellipse(sf,BW,(cx-int(10*s),cy+int(8*s),int(9*s),int(7*s)))
    pygame.draw.ellipse(sf,BW,(cx+int(1*s),cy+int(8*s),int(9*s),int(7*s)))
    pygame.draw.circle(sf,WHITE if not hit else GRAY,(cx,cy+int(12*s)),int(2*s))

    # Arms (natural proportions)
    # Left
    pygame.draw.line(sf,SK,(cx-int(11*s),cy),(cx-int(18*s),cy+int(14*s)),max(1,int(4*s)))
    pygame.draw.line(sf,SS,(cx-int(18*s),cy+int(14*s)),(cx-int(22*s),cy+int(24*s)),max(1,int(3*s)))
    pygame.draw.circle(sf,SK,(cx-int(22*s),cy+int(24*s)),int(3*s))
    # Right
    pygame.draw.line(sf,SS,(cx+int(11*s),cy),(cx+int(18*s),cy+int(12*s)),max(1,int(4*s)))
    pygame.draw.line(sf,SK,(cx+int(18*s),cy+int(12*s)),(cx+int(22*s),cy+int(22*s)),max(1,int(3*s)))
    pygame.draw.circle(sf,SS,(cx+int(22*s),cy+int(22*s)),int(3*s))

    # Neck
    pygame.draw.rect(sf,SS,(cx-int(4*s),cy-int(8*s),int(8*s),int(8*s)))
    pygame.draw.rect(sf,SK,(cx-int(3*s),cy-int(8*s),int(6*s),int(7*s)))
    # Necklace
    if not hit:
        pygame.draw.arc(sf,GOLD,(cx-int(6*s),cy-int(5*s),int(12*s),int(8*s)),math.pi,2*math.pi,1)
        pygame.draw.circle(sf,GOLD,(cx,cy+int(1*s)),max(1,int(1.5*s)))

    # Head
    hr=int(16*s)
    pygame.draw.circle(sf,SS,(cx+int(1*s),cy-int(18*s)),hr)
    pygame.draw.circle(sf,SK,(cx,cy-int(19*s)),hr)
    pygame.draw.circle(sf,SH,(cx-int(4*s),cy-int(25*s)),int(6*s))

    # Blush
    bl=pygame.Surface((int(8*s),int(5*s)),pygame.SRCALPHA)
    pygame.draw.ellipse(bl,(255,160,160,50) if not hit else (*GRAY,30),(0,0,int(8*s),int(5*s)))
    sf.blit(bl,(cx-int(14*s),cy-int(14*s)))
    sf.blit(bl,(cx+int(6*s),cy-int(14*s)))

    # Hair top + sides
    pygame.draw.ellipse(sf,HR,(cx-int(19*s),cy-int(38*s),int(38*s),int(24*s)))
    pygame.draw.ellipse(sf,HH,(cx-int(10*s),cy-int(36*s),int(16*s),int(10*s)))
    pygame.draw.ellipse(sf,HR,(cx-int(20*s),cy-int(28*s),int(10*s),int(26*s)))
    pygame.draw.ellipse(sf,HR,(cx+int(10*s),cy-int(28*s),int(10*s),int(26*s)))
    pygame.draw.ellipse(sf,HH,(cx-int(18*s),cy-int(22*s),int(5*s),int(14*s)))
    # Bangs
    for i in range(-3,4):
        bx=cx+int(i*4.5*s); bw=int(6*s); bh=int(12*s)+abs(i)*int(1.5*s)
        pygame.draw.ellipse(sf,HR,(bx-bw//2,cy-int(28*s),bw,bh))
    draw_heart(sf,cx+int(13*s),cy-int(32*s),int(7*s),BW)

    # Eyebrows
    pygame.draw.arc(sf,HR,(cx-int(10*s),cy-int(26*s),int(8*s),int(5*s)),0.3,math.pi-0.3,max(1,int(2*s)))
    pygame.draw.arc(sf,HR,(cx+int(2*s),cy-int(26*s),int(8*s),int(5*s)),0.3,math.pi-0.3,max(1,int(2*s)))

    # Eyes
    ew,eh=int(7*s),int(8*s)
    for side in [-1,1]:
        ex=cx+int(side*5.5*s)-ew//2; ey=cy-int(22*s)
        pygame.draw.ellipse(sf,WHITE if not hit else GRAY,(ex,ey,ew,eh))
        # Iris
        ic=(80,50,30) if not hit else DARK_GRAY
        ix=cx+int(side*5.5*s)-int(2.5*s); iy=cy-int(21*s)
        pygame.draw.ellipse(sf,ic,(ix,iy,int(5*s),int(6*s)))
        # Pupil
        px=cx+int(side*5.5*s)-int(1.2*s); py=cy-int(20*s)
        pygame.draw.ellipse(sf,BLACK if not hit else GRAY,(px,py,int(2.5*s),int(4*s)))
        # Catchlight
        pygame.draw.circle(sf,WHITE if not hit else GRAY,(cx+int(side*5*s),cy-int(21*s)),max(1,int(1.2*s)))
        # Lid
        pygame.draw.arc(sf,SS,(ex,ey,ew,eh),-0.2,math.pi+0.2,max(1,int(1*s)))

    # Eyelashes
    for dx in [-9,-7,-5]:
        la=1.3+(dx+7)*0.12
        pygame.draw.line(sf,HR,(cx+int(dx*s),cy-int(22*s)),
                         (cx+int(dx*s)+int(math.cos(la)*3*s),cy-int(22*s)-int(math.sin(la)*3*s)),1)
    for dx in [5,7,9]:
        la=1.8-(dx-7)*0.12
        pygame.draw.line(sf,HR,(cx+int(dx*s),cy-int(22*s)),
                         (cx+int(dx*s)+int(math.cos(la)*3*s),cy-int(22*s)-int(math.sin(la)*3*s)),1)

    # Nose
    pygame.draw.line(sf,SS,(cx,cy-int(15*s)),(cx-int(1.5*s),cy-int(11*s)),1)
    pygame.draw.line(sf,SS,(cx-int(1.5*s),cy-int(11*s)),(cx+int(1*s),cy-int(10*s)),1)

    # Mouth
    mc=(190,60,65) if not hit else GRAY
    lc=(220,90,100) if not hit else GRAY
    pygame.draw.arc(sf,mc,(cx-int(4*s),cy-int(8*s),int(4*s),int(4*s)),0,math.pi,max(1,int(1.5*s)))
    pygame.draw.arc(sf,mc,(cx,cy-int(8*s),int(4*s),int(4*s)),0,math.pi,max(1,int(1.5*s)))
    pygame.draw.arc(sf,lc,(cx-int(3.5*s),cy-int(7*s),int(7*s),int(5*s)),math.pi,2*math.pi,max(1,int(1.5*s)))

    # Target rings
    if not hit:
        for r,a in [(int(45*s),30),(int(35*s),20)]:
            rs=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
            pygame.draw.circle(rs,(255,50,50,a),(r,r),r,2)
            sf.blit(rs,(cx-r,cy+int(5*s)-r))

# ── Crosshair ──
def draw_cross(sf,mx,my):
    pygame.draw.circle(sf,(200,0,0),(mx,my),22,2)
    pygame.draw.circle(sf,(255,50,50),(mx,my),20,1)
    pygame.draw.circle(sf,(255,80,80),(mx,my),6,1)
    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        pygame.draw.line(sf,(200,0,0),(mx+dx*8,my+dy*8),(mx+dx*28,my+dy*28),2)
        mid=(mx+dx*18,my+dy*18)
        if dx!=0: pygame.draw.line(sf,(255,80,80),(mid[0],mid[1]-3),(mid[0],mid[1]+3),1)
        else: pygame.draw.line(sf,(255,80,80),(mid[0]-3,mid[1]),(mid[0]+3,mid[1]),1)
    pygame.draw.circle(sf,(255,0,0),(mx,my),2)

# ── Particles ──
class Particle:
    def __init__(s,x,y,col=None,spd=1.0,grav=0.15,sr=(2,6)):
        s.x,s.y=float(x),float(y)
        s.vx=random.uniform(-4,4)*spd; s.vy=random.uniform(-7,-1)*spd
        s.life=random.randint(20,55); s.ml=s.life
        s.sz=random.randint(*sr); s.grav=grav
        s.col=col or random.choice([RED,PINK,DEEP_PINK,GOLD,LIGHT_PINK,ORANGE])
    def update(s):
        s.x+=s.vx; s.y+=s.vy; s.vy+=s.grav; s.life-=1
    def draw(s,sf):
        if s.life<=0: return
        a=s.life/s.ml; r=max(1,int(s.sz*a))
        pygame.draw.circle(sf,s.col,(int(s.x),int(s.y)),r)
        if r>2:
            gs=pygame.Surface((r*4,r*4),pygame.SRCALPHA)
            pygame.draw.circle(gs,(*s.col,int(40*a)),(r*2,r*2),r*2)
            sf.blit(gs,(int(s.x)-r*2,int(s.y)-r*2))

class MuzzleFlash:
    def __init__(s,x,y): s.x,s.y,s.life,s.ml=x,y,6,6
    def update(s): s.life-=1
    def draw(s,sf):
        if s.life<=0: return
        t=s.life/s.ml; r=int(15*t)
        fs=pygame.Surface((r*4,r*4),pygame.SRCALPHA)
        pygame.draw.circle(fs,(255,255,200,int(180*t)),(r*2,r*2),r*2)
        pygame.draw.circle(fs,(255,255,100,int(255*t)),(r*2,r*2),r)
        sf.blit(fs,(s.x-r*2,s.y-r*2))

class BulletTrail:
    def __init__(s,sx,sy,ex,ey): s.sx,s.sy,s.ex,s.ey=sx,sy,ex,ey; s.life=8; s.ml=8
    def update(s): s.life-=1
    def draw(s,sf):
        if s.life<=0: return
        t=s.life/s.ml
        ts=pygame.Surface((W,H),pygame.SRCALPHA)
        pygame.draw.line(ts,(255,255,150,int(120*t)),(int(s.sx),int(s.sy)),(int(s.ex),int(s.ey)),max(1,int(2*t)))
        sf.blit(ts,(0,0))

class HeartP:
    def __init__(s):
        s.x=random.randint(0,W); s.y=random.randint(H,H+300)
        s.sp=random.uniform(1,3.5); s.sz=random.randint(8,20)
        s.col=random.choice([RED,PINK,DEEP_PINK,LIGHT_PINK,GOLD,PURPLE])
        s.wb=random.uniform(0,6.28); s.ws=random.uniform(0.02,0.06)
    def update(s):
        s.y-=s.sp; s.wb+=s.ws; s.x+=math.sin(s.wb)*2
        if s.y<-30: s.y=H+30; s.x=random.randint(0,W)
    def draw(s,sf): draw_heart(sf,s.x,s.y,s.sz,s.col)

# ── UI ──
def draw_panel(sf,r,al=180):
    p=pygame.Surface((r.w,r.h),pygame.SRCALPHA)
    pygame.draw.rect(p,(12,6,18,al),(0,0,r.w,r.h),border_radius=14)
    pygame.draw.rect(p,(255,100,140,50),(0,0,r.w,r.h),2,border_radius=14)
    sf.blit(p,r.topleft)

def draw_btn(sf,r,txt,fn,hv,gc=PINK):
    sh=pygame.Surface((r.w+4,r.h+4),pygame.SRCALPHA)
    pygame.draw.rect(sh,(0,0,0,60),(0,0,r.w+4,r.h+4),border_radius=12)
    sf.blit(sh,(r.x-2,r.y+2))
    if hv:
        g=pygame.Surface((r.w+16,r.h+16),pygame.SRCALPHA)
        pygame.draw.rect(g,(*gc,35),(0,0,r.w+16,r.h+16),border_radius=18)
        sf.blit(g,(r.x-8,r.y-8))
    bg=(55,28,45) if hv else (32,16,28)
    b=pygame.Surface((r.w,r.h),pygame.SRCALPHA)
    pygame.draw.rect(b,(*bg,230),(0,0,r.w,r.h),border_radius=12)
    pygame.draw.rect(b,(255,255,255,15),(2,2,r.w-4,r.h//3),border_radius=10)
    bc=gc if hv else (90,45,65)
    pygame.draw.rect(b,(*bc,180),(0,0,r.w,r.h),2,border_radius=12)
    sf.blit(b,r.topleft)
    t=fn.render(txt,True,WHITE if hv else (200,200,200))
    sf.blit(t,(r.centerx-t.get_width()//2,r.centery-t.get_height()//2))

# ══ CELEBRATION ══
def celebration_screen():
    # Play applause sound
    if sound_applause: sound_applause.play()
    hts=[HeartP() for _ in range(50)]; pts=[]; fr=0
    cols=[RED,PINK,DEEP_PINK,GOLD,PURPLE,CYAN,LIGHT_PINK,ORANGE,GREEN]
    while True:
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: return  # ESC returns to menu
                else: return  # Any other key also returns
            if e.type==pygame.MOUSEBUTTONDOWN: return
        fr+=1; draw_sky(screen,fr)
        for h in hts: h.update(); h.draw(screen)
        if fr%12==0:
            fx,fy=random.randint(100,W-100),random.randint(40,H//2-50)
            fc=random.choice(cols)
            for _ in range(40):
                p=Particle(fx,fy,fc,spd=1.5,sr=(2,5))
                a=random.uniform(0,6.28); sp=random.uniform(2,7)
                p.vx,p.vy=math.cos(a)*sp,math.sin(a)*sp
                p.life=random.randint(30,70); p.ml=p.life; pts.append(p)
        for p in pts[:]:
            p.update(); p.draw(screen)
            if p.life<=0: pts.remove(p)
        gv=int(20+15*math.sin(fr*0.05))
        tc=(255,min(255,100+gv*5),min(255,150+gv*3))
        for o in [4,2]:
            sh=f_xl.render("Happy Valentine's Day!",True,(80+o*5,10,30))
            screen.blit(sh,(W//2-sh.get_width()//2+o,H//2-90+o))
        t=f_xl.render("Happy Valentine's Day!",True,tc)
        screen.blit(t,(W//2-t.get_width()//2,H//2-90))
        msg="You're an amazing shooter!"
        tw=len(msg)*16; sx=W//2-tw//2
        for i,ch in enumerate(msg):
            oy=int(8*math.sin(fr*0.08+i*0.3))
            cs=f_md.render(ch,True,cols[i%len(cols)])
            screen.blit(cs,(sx+i*16,H//2+10+oy))
        pu=1+0.12*math.sin(fr*0.06)
        draw_heart(screen,W//2,H//2+100,int(45*pu),DEEP_PINK)
        draw_heart(screen,W//2,H//2+100,int(32*pu),RED)
        draw_heart(screen,W//2,H//2+100,int(18*pu),PINK)
        ht=f_xs.render("Click or press any key to continue...",True,GRAY)
        screen.blit(ht,(W//2-ht.get_width()//2,H-35))
        pygame.display.flip(); clock.tick(60)

# ══ SCORES ══
def scores_screen():
    scs=load_scores(); fr=0
    while True:
        mx,my=pygame.mouse.get_pos(); fr+=1
        br=pygame.Rect(W//2-90,H-75,180,48)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: return
            if e.type==pygame.MOUSEBUTTONDOWN and br.collidepoint(mx,my): return
        draw_sky(screen,fr)
        draw_panel(screen,pygame.Rect(W//2-320,60,640,520),200)
        t=f_lg.render("HIGH SCORES",True,GOLD)
        screen.blit(t,(W//2-t.get_width()//2,80))
        pygame.draw.line(screen,GOLD,(W//2-150,122),(W//2+150,122),1)
        hy=140; hdr=["RANK","SCORE","LEVEL","DATE"]
        hx=[W//2-260,W//2-110,W//2+30,W//2+150]
        for i,h in enumerate(hdr):
            t=f_xs.render(h,True,PINK); screen.blit(t,(hx[i],hy))
        pygame.draw.line(screen,(100,50,70),(W//2-280,hy+18),(W//2+280,hy+18),1)
        if not scs:
            t=f_md.render("No scores yet! Play a game.",True,GRAY)
            screen.blit(t,(W//2-t.get_width()//2,220))
        else:
            for i,sc in enumerate(scs[:10]):
                y=165+i*36
                if i%2==0:
                    rb=pygame.Surface((560,32),pygame.SRCALPHA)
                    pygame.draw.rect(rb,(255,255,255,8),(0,0,560,32),border_radius=4)
                    screen.blit(rb,(W//2-280,y))
                md={0:"1st",1:"2nd",2:"3rd"}
                rk=md.get(i,f"{i+1}th")
                rc=GOLD if i==0 else (200,200,200) if i==1 else (180,120,60) if i==2 else WHITE
                vs=[rk,str(sc["score"]),sc.get("level","?"),sc.get("time","?")]
                cs=[rc,WHITE,LEVEL_COLORS.get(sc.get("level",""),WHITE),GRAY]
                for j,v in enumerate(vs):
                    t=f_sm.render(v,True,cs[j]); screen.blit(t,(hx[j],y+6))
        draw_btn(screen,br,"BACK",f_md,br.collidepoint(mx,my))
        pygame.display.flip(); clock.tick(60)

# ══ LEVEL SELECT ══
def level_screen(cur):
    sel=cur; fr=0
    lvl_data={
        "Easy":   {"desc":"Slow targets • Big doll • Relaxed pace","stars":1,"interval":"2.8s","size":"Large"},
        "Medium": {"desc":"Moving targets • Normal doll • Drifting","stars":2,"interval":"1.4s","size":"Normal"},
        "Hard":   {"desc":"Teleporting • Tiny doll • Dodges cursor!","stars":3,"interval":"0.5s","size":"Small"},
    }
    while True:
        mx,my=pygame.mouse.get_pos(); fr+=1
        # 3 horizontal cards
        cw,ch2=260,320; gap=20; total=cw*3+gap*2
        sx=W//2-total//2
        cards={}
        for i,lv in enumerate(["Easy","Medium","Hard"]):
            cards[lv]=pygame.Rect(sx+i*(cw+gap),160,cw,ch2)
        br=pygame.Rect(W//2-90,H-65,180,45)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: return sel
            if e.type==pygame.MOUSEBUTTONDOWN:
                for lv,r in cards.items():
                    if r.collidepoint(mx,my): sel=lv
                if br.collidepoint(mx,my): return sel
        draw_sky(screen,fr)
        # Title
        t=f_lg.render("SELECT DIFFICULTY",True,PINK)
        screen.blit(t,(W//2-t.get_width()//2,60))
        pygame.draw.line(screen,PINK,(W//2-140,105),(W//2+140,105),1)
        # Cards
        for lv,r in cards.items():
            hv=r.collidepoint(mx,my); is_sel=lv==sel
            gc=LEVEL_COLORS[lv]
            # Card bg
            cd=pygame.Surface((r.w,r.h),pygame.SRCALPHA)
            bg_a=220 if is_sel else 180
            pygame.draw.rect(cd,(20,10,25,bg_a),(0,0,r.w,r.h),border_radius=16)
            # Top color bar
            pygame.draw.rect(cd,(*gc,180 if is_sel else 80),(0,0,r.w,6),border_radius=16)
            # Border
            bc=gc if is_sel or hv else (70,40,55)
            bw=3 if is_sel else (2 if hv else 1)
            pygame.draw.rect(cd,(*bc,200),(0,0,r.w,r.h),bw,border_radius=16)
            # Glow if selected
            if is_sel:
                gls=pygame.Surface((r.w+20,r.h+20),pygame.SRCALPHA)
                pygame.draw.rect(gls,(*gc,25),(0,0,r.w+20,r.h+20),border_radius=20)
                screen.blit(gls,(r.x-10,r.y-10))
            screen.blit(cd,r.topleft)
            # Content
            # Level name
            nm=f_lg.render(lv.upper(),True,gc if is_sel else lerp_c(gc,(150,150,150),0.3))
            screen.blit(nm,(r.centerx-nm.get_width()//2,r.y+20))
            # Stars
            star_y=r.y+65
            d=lvl_data[lv]
            for si in range(3):
                sc2=GOLD if si<d["stars"] else (50,40,35)
                sx2=r.centerx-30+si*25
                pygame.draw.polygon(screen,sc2,star_points(sx2,star_y,8))
            # Divider
            pygame.draw.line(screen,(80,50,65),(r.x+20,r.y+90),(r.x+r.w-20,r.y+90),1)
            # Stats
            stats=[("Speed",d["interval"]),("Target",d["size"])]
            for si2,(label,val) in enumerate(stats):
                sy2=r.y+105+si2*30
                lt=f_xs.render(label,True,GRAY); screen.blit(lt,(r.x+20,sy2))
                vt=f_sm.render(val,True,WHITE); screen.blit(vt,(r.x+r.w-20-vt.get_width(),sy2))
            # Description
            desc_lines=d["desc"].split("•")
            for di,dl in enumerate(desc_lines):
                dt=f_xs.render(dl.strip(),True,(180,150,160))
                screen.blit(dt,(r.centerx-dt.get_width()//2,r.y+180+di*20))
            # Mini doll preview
            doll_s={"Easy":0.55,"Medium":0.45,"Hard":0.30}
            draw_doll(screen,r.centerx,r.y+280,doll_s[lv])
            # Selected badge
            if is_sel:
                bdg=f_xs.render("SELECTED",True,gc)
                bw2=bdg.get_width()+16
                bs=pygame.Surface((bw2,22),pygame.SRCALPHA)
                pygame.draw.rect(bs,(*gc,40),(0,0,bw2,22),border_radius=11)
                pygame.draw.rect(bs,(*gc,120),(0,0,bw2,22),1,border_radius=11)
                screen.blit(bs,(r.centerx-bw2//2,r.bottom-30))
                screen.blit(bdg,(r.centerx-bdg.get_width()//2,r.bottom-28))
        draw_btn(screen,br,"BACK",f_md,br.collidepoint(mx,my))
        pygame.display.flip(); clock.tick(60)

def star_points(cx,cy,r):
    pts=[]
    for i in range(10):
        a=math.pi/2+i*math.pi/5
        d=r if i%2==0 else r*0.4
        pts.append((cx+math.cos(a)*d,cy-math.sin(a)*d))
    return pts

# ══ MAIN MENU ══
def main_menu():
    cur="Medium"; fr=0
    while True:
        mx,my=pygame.mouse.get_pos(); fr+=1
        bw2,bh2=280,52; bx=W//2-bw2//2
        bs_=pygame.Rect(bx,370,bw2,bh2)
        bl=pygame.Rect(bx,435,bw2,bh2)
        bsc=pygame.Rect(bx,500,bw2,bh2)
        bq=pygame.Rect(bx,565,bw2,bh2)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
            if e.type==pygame.MOUSEBUTTONDOWN:
                if bs_.collidepoint(mx,my): game_loop(cur)
                elif bl.collidepoint(mx,my): cur=level_screen(cur)
                elif bsc.collidepoint(mx,my): scores_screen()
                elif bq.collidepoint(mx,my): pygame.quit(); sys.exit()
        draw_sky(screen,fr); draw_ground(screen)
        b1=int(4*math.sin(fr*0.03)); b2=int(4*math.sin(fr*0.03+2))
        draw_doll(screen,120,H-210+b1,0.85)
        draw_doll(screen,W-120,H-210+b2,0.85)
        draw_panel(screen,pygame.Rect(W//2-210,95,420,550),190)
        gv=int(12*math.sin(fr*0.04))
        tc=(255,130+gv,160+gv)
        sh=f_title.render("VALENTINE",True,(80,15,30))
        screen.blit(sh,(W//2-sh.get_width()//2+3,113))
        t=f_title.render("VALENTINE",True,tc)
        screen.blit(t,(W//2-t.get_width()//2,110))
        s2=f_lg.render("S H O O T E R",True,(80,15,30))
        screen.blit(s2,(W//2-s2.get_width()//2+2,178))
        s3=f_lg.render("S H O O T E R",True,GOLD)
        screen.blit(s3,(W//2-s3.get_width()//2,176))
        pygame.draw.line(screen,PINK,(W//2-120,225),(W//2+120,225),1)
        draw_heart(screen,W//2,225,8,DEEP_PINK)
        # Level badge
        bw3=150; br2=pygame.Rect(W//2-bw3//2,245,bw3,26)
        lbs=pygame.Surface((bw3,26),pygame.SRCALPHA)
        pygame.draw.rect(lbs,(*LEVEL_COLORS[cur],35),(0,0,bw3,26),border_radius=13)
        pygame.draw.rect(lbs,(*LEVEL_COLORS[cur],100),(0,0,bw3,26),1,border_radius=13)
        screen.blit(lbs,br2.topleft)
        lt=f_xs.render(f"Level: {cur}",True,LEVEL_COLORS[cur])
        screen.blit(lt,(W//2-lt.get_width()//2,250))
        draw_cross(screen,W//2,320)
        draw_btn(screen,bs_,"START GAME",f_md,bs_.collidepoint(mx,my),GREEN)
        draw_btn(screen,bl,"DIFFICULTY",f_md,bl.collidepoint(mx,my),ORANGE)
        draw_btn(screen,bsc,"HIGH SCORES",f_md,bsc.collidepoint(mx,my),GOLD)
        draw_btn(screen,bq,"QUIT",f_md,bq.collidepoint(mx,my),RED)
        ft=f_xs.render("Shoot 7 dolls in a row for a surprise!",True,(180,120,140))
        screen.blit(ft,(W//2-ft.get_width()//2,H-28))
        pygame.display.flip(); clock.tick(60)

# ══ GAME LOOP ══
LCFG={
    "Easy":   {"sc":1.2,"hr":55,"show":1000,"hide":300},
    "Medium": {"sc":0.95,"hr":45,"show":400,"hide":200},
    "Hard":   {"sc":0.65,"hr":28,"show":100,"hide":100},
}
def game_loop(level):
    pygame.mouse.set_visible(False)
    cfg=LCFG[level]
    sc=0; ms=0; mx_ms=4; con=0
    ds=cfg["sc"]; mx2=90; myt=110; myb=200
    dx=float(random.randint(mx2,W-mx2)); dy=float(random.randint(myt,H-myb))
    dh=False; ht=0
    # Pop-up target mechanics
    doll_visible=True; show_start=pygame.time.get_ticks()
    show_time=cfg["show"]; hide_time=cfg["hide"]
    pts=[]; fls=[]; trs=[]; pops=[]; shk=0; fr=0
    # Generate position zones to ensure variety
    zones=[]
    zw,zh=(W-2*mx2)//3,(H-myt-myb)//2
    for zi in range(3):
        for zj in range(2):
            zones.append((mx2+zi*zw,myt+zj*zh,mx2+(zi+1)*zw,myt+(zj+1)*zh))
    last_zone=-1
    def rand_pos():
        nonlocal last_zone
        avail=[i for i in range(len(zones)) if i!=last_zone]
        zi=random.choice(avail); last_zone=zi
        z=zones[zi]
        return float(random.randint(z[0]+20,z[2]-20)),float(random.randint(z[1]+20,z[3]-20))

    while True:
        dt=clock.tick(60); fr+=1
        mmx,mmy=pygame.mouse.get_pos(); now=pygame.time.get_ticks()
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.mouse.set_visible(True); pygame.quit(); sys.exit()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: pygame.mouse.set_visible(True); return
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                # Play gunshot sound
                if sound_shoot: sound_shoot.play()
                fls.append(MuzzleFlash(mmx,mmy))
                trs.append(BulletTrail(W//2,H+20,mmx,mmy))
                for _ in range(6): pts.append(Particle(mmx,mmy,GOLD,spd=0.5,sr=(1,3)))
                shk=4
                if not dh and doll_visible:
                    dist=math.hypot(mmx-dx,mmy-(dy+5))
                    if dist<cfg["hr"]*ds:
                        # Play hit sound
                        if sound_hit: sound_hit.play()
                        p2=10+(5 if level=="Medium" else 15 if level=="Hard" else 0)
                        sc+=p2; con+=1; dh=True; ht=25
                        for _ in range(35): pts.append(Particle(dx,dy,spd=1.2))
                        pops.append({"t":f"+{p2}","x":dx,"y":dy-30,"l":50,"ml":50,"c":GOLD})
                        if con>=7:
                            pygame.mouse.set_visible(True); save_score(sc,level)
                            celebration_screen()
                            return  # Return to main menu after celebration
                    else:
                        ms+=1; con=0
                        pops.append({"t":"MISS!","x":mmx,"y":mmy-20,"l":35,"ml":35,"c":RED})
                        for _ in range(8): pts.append(Particle(mmx,mmy,(150,130,100),spd=0.4,sr=(1,4)))
                        if ms>=mx_ms:
                            pygame.mouse.set_visible(True); save_score(sc,level)
                            game_over_screen(sc,level); return
        
        # Pop-up visibility logic (doll is completely static - no movement)
        elapsed=now-show_start
        if doll_visible:
            if elapsed>show_time:
                doll_visible=False; show_start=now
        else:
            if elapsed>hide_time:
                doll_visible=True; show_start=now
                dx,dy=rand_pos()  # New random position when appearing
        
        # Hit animation
        if dh:
            ht-=1
            if ht<=0:
                dh=False; doll_visible=True; show_start=now
                dx,dy=rand_pos()
        
        # Shake
        sox=random.randint(-shk,shk) if shk>0 else 0
        soy=random.randint(-shk,shk) if shk>0 else 0
        if shk>0: shk-=1
        
        # Draw
        ren=pygame.Surface((W,H)); draw_sky(ren,fr); draw_ground(ren)
        # Only draw doll when visible (completely static - no bob animation)
        if doll_visible:
            draw_doll(ren,int(dx),int(dy),ds,hit=dh)
        for t2 in trs[:]:
            t2.update(); t2.draw(ren)
            if t2.life<=0: trs.remove(t2)
        for p2 in pts[:]:
            p2.update(); p2.draw(ren)
            if p2.life<=0: pts.remove(p2)
        for f2 in fls[:]:
            f2.update(); f2.draw(ren)
            if f2.life<=0: fls.remove(f2)
        for po in pops[:]:
            po["y"]-=1.2; po["l"]-=1
            al=max(0,po["l"]/po["ml"])
            t2=f_lg.render(po["t"],True,po["c"])
            ren.blit(t2,(po["x"]-t2.get_width()//2,int(po["y"])))
            if po["l"]<=0: pops.remove(po)
        # HUD
        hud=pygame.Surface((W,55),pygame.SRCALPHA)
        pygame.draw.rect(hud,(10,5,15,200),(0,0,W,55))
        pygame.draw.line(hud,(255,100,140,80),(0,54),(W,54),1)
        ren.blit(hud,(0,0))
        sl=f_xs.render("SCORE",True,GRAY); ren.blit(sl,(20,5))
        sv=f_md.render(str(sc),True,GOLD); ren.blit(sv,(20,22))
        ll=f_xs.render("LEVEL",True,GRAY); ren.blit(ll,(W//2-25,5))
        lv2=f_sm.render(level.upper(),True,LEVEL_COLORS[level]); ren.blit(lv2,(W//2-25,22))
        ll2=f_xs.render("LIVES",True,GRAY); ren.blit(ll2,(W-170,5))
        rem=mx_ms-ms
        for i in range(mx_ms):
            hx=W-160+i*32; c=RED if i<rem else (50,30,30)
            draw_heart(ren,hx,35,9,c)
        if con>0:
            bx2,by2=20,60; bw4=180
            st=f_xs.render(f"STREAK  {con}/7",True,GOLD if con>=5 else ORANGE if con>=3 else WHITE)
            ren.blit(st,(bx2,by2))
            pygame.draw.rect(ren,(30,15,25),(bx2,by2+18,bw4,7),border_radius=4)
            fl2=int(bw4*con/7)
            bc2=GOLD if con>=5 else ORANGE if con>=3 else PINK
            pygame.draw.rect(ren,bc2,(bx2,by2+18,fl2,7),border_radius=4)
        draw_cross(ren,mmx,mmy)
        screen.fill(BLACK); screen.blit(ren,(sox,soy))
        pygame.display.flip()

def game_over_screen(sc,lv):
    fr=0
    while True:
        mx,my=pygame.mouse.get_pos(); fr+=1
        br=pygame.Rect(W//2-230,H//2+120,210,52)
        bm=pygame.Rect(W//2+20,H//2+120,210,52)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
            if e.type==pygame.MOUSEBUTTONDOWN:
                if br.collidepoint(mx,my): game_loop(lv); return
                if bm.collidepoint(mx,my): return
        draw_sky(screen,fr)
        ov=pygame.Surface((W,H),pygame.SRCALPHA)
        pygame.draw.rect(ov,(0,0,0,100),(0,0,W,H)); screen.blit(ov,(0,0))
        draw_panel(screen,pygame.Rect(W//2-250,H//2-160,500,350),220)
        pu=1+0.04*math.sin(fr*0.08)
        draw_heart(screen,W//2,H//2-110,int(40*pu),(80,25,35))
        cp=[(W//2-2,H//2-135),(W//2+5,H//2-120),(W//2-3,H//2-110),(W//2+6,H//2-100),(W//2,H//2-90)]
        pygame.draw.lines(screen,BLACK,False,cp,2)
        t=f_xl.render("GAME OVER",True,RED)
        screen.blit(t,(W//2-t.get_width()//2,H//2-55))
        st=f_lg.render(f"Score: {sc}",True,GOLD)
        screen.blit(st,(W//2-st.get_width()//2,H//2+10))
        lt2=f_sm.render(f"Level: {lv}",True,LEVEL_COLORS[lv])
        screen.blit(lt2,(W//2-lt2.get_width()//2,H//2+60))
        tp=f_xs.render("Hit 7 in a row for a Valentine's surprise!",True,LIGHT_PINK)
        screen.blit(tp,(W//2-tp.get_width()//2,H//2+90))
        draw_btn(screen,br,"RETRY",f_md,br.collidepoint(mx,my),GREEN)
        draw_btn(screen,bm,"MENU",f_md,bm.collidepoint(mx,my),PINK)
        pygame.display.flip(); clock.tick(60)

if __name__=="__main__": main_menu()
