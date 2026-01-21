from PIL import Image

ruta = 'assets/sofia.png'
out = 'assets/sofia_processed.png'

img = Image.open(ruta).convert('RGBA')
w, h = img.size
print('size', w, h)
px = img.load()

# contar opacos iniciales
initial_opaque = 0
for y in range(h):
    for x in range(w):
        if px[x, y][3] != 0:
            initial_opaque += 1
print('initial opaque pixels:', initial_opaque)

# calcular color de fondo a partir de esquinas
corners = [px[0,0][:3], px[w-1,0][:3], px[0,h-1][:3], px[w-1,h-1][:3]]
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
    if x < 0 or x >= w or y < 0 or y >= h:
        continue
    visited.add((x,y))
    r,g,b,a = px[x,y]
    if color_dist((r,g,b), bg) <= tol:
        px[x,y] = (r,g,b,0)
        stack.append((x-1,y))
        stack.append((x+1,y))
        stack.append((x,y-1))
        stack.append((x,y+1))

# pase global
tol_global = 80.0
for yy in range(h):
    for xx in range(w):
        r,g,b,a = px[xx,yy]
        if color_dist((r,g,b), bg) <= tol_global:
            px[xx,yy] = (r,g,b,0)

# contar opacos finales
final_opaque = 0
for y in range(h):
    for x in range(w):
        if px[x, y][3] != 0:
            final_opaque += 1
print('final opaque pixels:', final_opaque)

img.save(out)
print('Saved', out)
