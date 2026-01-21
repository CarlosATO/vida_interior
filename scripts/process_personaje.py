import pygame

pygame.init()
pygame.display.init()
pygame.display.set_mode((1,1))

ruta = 'sofia.png'
img = pygame.image.load(ruta).convert_alpha()

w,h = img.get_size()
print('size', w,h)

# contar opacos iniciales
initial_opaque = sum(1 for y in range(h) for x in range(w) if img.get_at((x,y))[3] != 0)
print('initial opaque pixels:', initial_opaque)

# calcular color de fondo a partir de esquinas
corners = [img.get_at((0,0))[:3], img.get_at((w-1,0))[:3], img.get_at((0,h-1))[:3], img.get_at((w-1,h-1))[:3]]
bg = (sum(c[0] for c in corners)//4, sum(c[1] for c in corners)//4, sum(c[2] for c in corners)//4)
print('bg', bg)

def color_dist(c1, c2):
    return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2) ** 0.5

# flood-fill desde esquinas
tol = 90.0
stack = [(0,0),(w-1,0),(0,h-1),(w-1,h-1)]
visited = set()
while stack:
    x,y = stack.pop()
    if (x,y) in visited:
        continue
    visited.add((x,y))
    r,g,b,a = img.get_at((x,y))
    if color_dist((r,g,b), bg) <= tol:
        img.set_at((x,y),(r,g,b,0))
        if x-1 >= 0:
            stack.append((x-1,y))
        if x+1 < w:
            stack.append((x+1,y))
        if y-1 >= 0:
            stack.append((x,y-1))
        if y+1 < h:
            stack.append((x,y+1))

# pase global
tol_global = 80.0
for yy in range(h):
    for xx in range(w):
        r,g,b,a = img.get_at((xx,yy))
        if color_dist((r,g,b), bg) <= tol_global:
            img.set_at((xx,yy),(r,g,b,0))

# contar opacos finales
final_opaque = sum(1 for y in range(h) for x in range(w) if img.get_at((x,y))[3] != 0)
print('final opaque pixels:', final_opaque)

out = 'assets/sofia_processed.png'
pygame.image.save(img, out)
print('Saved', out)
