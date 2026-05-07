import math

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
