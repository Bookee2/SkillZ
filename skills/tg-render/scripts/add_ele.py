"""Write terrain elevation into a track that has none, from the same Terrarium DEM tiles render.py uses (z13, bilinear),
cached in the flythrough .tiles folder under render.py's names (dem_<z>_<x>_<y>.png).
    .venv/bin/python add_ele.py <in.gpx> <out.gpx>"""
import math, os, re, sys, urllib.request, ssl, certifi, io
from PIL import Image
TILES = '/Users/kb/Desktop/Projects/TrailGoat/scripts/flythrough/.tiles'; Z = 13
CTX = ssl.create_default_context(cafile=certifi.where()); cache = {}
def tile(x, y):
    if (x, y) in cache: return cache[(x, y)]
    fn = os.path.join(TILES, f'dem_{Z}_{x}_{y}.png')
    if not os.path.exists(fn):
        u = f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{Z}/{x}/{y}.png'
        data = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'TrailGoat-flythrough'}), timeout=40, context=CTX).read()
        open(fn + '.tmp', 'wb').write(data); os.replace(fn + '.tmp', fn)
    im = Image.open(fn).convert('RGB'); cache[(x, y)] = im.load(); return cache[(x, y)]
def ele(lat, lon):
    n = 2 ** Z; fx = (lon + 180) / 360 * n * 256; fy = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n * 256
    def h(px, py):
        t = tile(int(px // 256), int(py // 256)); r, g, b = t[int(px % 256), int(py % 256)]; return r * 256 + g + b / 256 - 32768
    x0, y0 = math.floor(fx - 0.5), math.floor(fy - 0.5); ax, ay = fx - 0.5 - x0, fy - 0.5 - y0
    return (h(x0, y0) * (1 - ax) * (1 - ay) + h(x0 + 1, y0) * ax * (1 - ay) + h(x0, y0 + 1) * (1 - ax) * ay + h(x0 + 1, y0 + 1) * ax * ay)
g = open(sys.argv[1], encoding='utf-8').read()
def sub(m):
    la, lo = float(m.group(1)), float(m.group(2)); return f'<trkpt lat="{m.group(1)}" lon="{m.group(2)}"><ele>{ele(la, lo):.1f}</ele></trkpt>'
g2, n = re.subn(r'<trkpt lat="([-\d.]+)" lon="([-\d.]+)"\s*/>', sub, g)
if not n: g2, n = re.subn(r'<trkpt lat="([-\d.]+)" lon="([-\d.]+)">\s*</trkpt>', sub, g)
open(sys.argv[2], 'w', encoding='utf-8').write(g2); print(n, 'points given elevation;', len(cache), 'tiles')
