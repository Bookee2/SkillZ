"""Pull the preview thumbnail Epic saves inside each .uasset (JPEG or PNG in the
package's thumbnail table) out to image files: a visual catalogue of a pack
without opening or rendering anything (65 of 67 Niagara Examples systems had one).

    python3 extract_uasset_thumbs.py <content folder> <out folder> [prefix, default NS_]
"""
import os
import sys

root, out = sys.argv[1], sys.argv[2]
prefix = sys.argv[3] if len(sys.argv) > 3 else 'NS_'
os.makedirs(out, exist_ok=True)
n, missing = 0, []
for dp, _, files in os.walk(root):
    for f in files:
        if not (f.startswith(prefix) and f.endswith('.uasset')):
            continue
        b = open(os.path.join(dp, f), 'rb').read()
        i, kind = b.find(b'\x89PNG\r\n\x1a\n'), 'png'
        if i < 0:
            i, kind = b.find(b'\xff\xd8\xff'), 'jpg'
        if i < 0:
            missing.append(f)
            continue
        j = b.find(b'IEND', i) + 8 if kind == 'png' else b.find(b'\xff\xd9', i) + 2
        open(os.path.join(out, f[:-7] + '.' + kind), 'wb').write(b[i:j])
        n += 1
print('extracted', n, 'without a preview', missing)
