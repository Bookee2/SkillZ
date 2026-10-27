"""Import a local course GPX onto a catalogue edition, exactly as gpx_import.py does for a fetched one.

    cd <TrailGoat checkout> && .venv/bin/python "<queue>/import_local.py" <edition_id> <file.gpx> [--label "126K"] [--name "…"] [--want-km 126] [--commit]

For batch-3 flyovers whose official file isn't a URL shape the importer resolves (a file found by hand, a KML
turned into GPX, segments joined). build_course() from gpx_import.py, the same distance check (±25 %), the same
course name ("<event> <label> — <year>"), save_fuel_course() and the edition's course_id/status. Dry run without
--commit. Prints the new course id."""
import json, os, sys
sys.path.insert(0, os.getcwd())
from app.db import get_conn, init_db, list_fuel_courses, save_fuel_course
from gpx_import import build_course, parse_distance_km, M_PER_MI

args = [a for a in sys.argv[1:] if not a.startswith('--')]
opt = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
ed_id, path = int(args[0]), args[1]; commit = '--commit' in sys.argv
init_db()
with get_conn() as c:
    r = dict(c.execute("SELECT ed.id, ed.year, ed.race_date, ed.distance_label, ed.course_id, ed.status, e.name FROM race_editions ed "
                       "JOIN race_events e ON e.id = ed.event_id WHERE ed.id = ?", (ed_id,)).fetchone())
print('edition', r)
if r['course_id']: sys.exit(f"edition {ed_id} already has course {r['course_id']}")
label = opt('--label') or r['distance_label']
base = f"{r['name']} {label}" if label and label.lower() not in r['name'].lower() else r['name']
name = base + (f" — {r['year']}" if r['year'] else '')
if opt('--name'): name = opt('--name')                       # a clean name where the event's own reads oddly with a label
if name.lower() in {x['name'].lower() for x in list_fuel_courses(2000)}: sys.exit(f'already in library: {name}')
rec = build_course(name, open(path, encoding='utf-8').read(), r['race_date'])
got_km = rec['distance_m'] / 1000; want_km = float(opt('--want-km')) if opt('--want-km') else parse_distance_km(label, bare_miles=True)
print(f"{name}: {got_km:.1f} km ({got_km * 1000 / M_PER_MI:.1f} mi), gain {rec['gain_m']:.0f} m, {len(json.loads(rec['aid_stations'] or '[]'))} aids, {rec['country']}/{rec['region']}")
if want_km and not (want_km * 0.75 <= got_km <= want_km * 1.25): sys.exit(f'distance mismatch: file {got_km:.1f} km vs ~{want_km:.0f} km')
if not commit: print('dry run: not saved'); sys.exit()
cid = save_fuel_course(rec)
with get_conn() as c:
    c.execute("UPDATE race_editions SET course_id = ?, status = 'imported' WHERE id = ?", (cid, ed_id))
print('IMPORTED course', cid)
