import pathlib, json, base64, sys
here = pathlib.Path(__file__).parent; sp = here.parent
s = (here / "src2.html").read_text()
a = s.index("<script>"); b = s.index("</script>", a)      # the inline script, after the CDN tags
s = s[:a] + "".join(c if ord(c) < 128 else "\\u%04x" % ord(c) for c in s[a:b]) + s[b:]
data = json.load(open(sp / "tg-data.json")); data["catalogCount"] = 506
data2 = json.load(open(sp / "tg-data2.json"))
goat = "data:image/webp;base64," + base64.b64encode((here / "goat-right.webp").read_bytes()).decode()
poster = "data:image/webp;base64," + base64.b64encode((here / "poster.webp").read_bytes()).decode()
for k, v in (("__DATA2__", json.dumps(data2, separators=(",", ":"), ensure_ascii=True)), ("__DATA__", json.dumps(data, separators=(",", ":"), ensure_ascii=True)), ("__GOAT__", goat), ("__POSTER__", poster)):
    assert k in s, k; s = s.replace(k, v)
if not s.lstrip().lower().startswith("<meta charset"):   # the published wrapper adds these too; local and offline copies need them
    s = '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n' + s
(here / "trailgoat-in-motion.html").write_text(s)
ia = s.index("<script>"); js = s[ia + 8:s.index("</script>", ia)]
assert len(js) > 100_000, len(js)
(here / "check.js").write_text(js)
print("page KB", len(s) // 1024)
