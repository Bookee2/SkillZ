/* Contours that rise: the course page's backdrop until the course has a flythrough.
 *
 * seo._topo_backdrop_html puts a canvas in the hero with the course's ~160-point
 * route line. This reads open terrain tiles (AWS Terrain Tiles, Terrarium
 * encoding: metres = R*256 + G + B/256 - 32768) around the route, samples them
 * into a height grid, traces contour lines with marching squares, and draws
 * them rising from the valley floor to the summit, with the route dashed on top.
 * Faint by design: the title and buttons sit on it. Reduced motion draws the
 * finished map; a failed tile load leaves the plain header.
 */
(function () {
    'use strict';
    var cv = document.querySelector('canvas.cp-topo');
    if (!cv) return;
    var hero = cv.closest('.cp-hero'), cap = hero && hero.querySelector('.cp-topo-cap');
    var route = [];
    try { route = JSON.parse(cv.getAttribute('data-route')) || []; } catch (e) { route = []; }
    if (route.length < 2) return;
    var metric = cv.getAttribute('data-units') === 'metric';
    var calm = function () { return matchMedia('(prefers-reduced-motion: reduce)').matches; };
    var clamp = function (v, a, b) { return Math.min(b, Math.max(a, v)); };

    // ---- web mercator, in tile units at zoom z ----
    var tx = function (lon, z) { return (lon + 180) / 360 * Math.pow(2, z); };
    var ty = function (lat, z) { var r = lat * Math.PI / 180; return (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * Math.pow(2, z); };

    // ---- colour from the theme's tokens ----
    var probe = document.createElement('canvas').getContext('2d');
    function tok(name) {
        probe.fillStyle = '#888';
        try { probe.fillStyle = getComputedStyle(document.documentElement).getPropertyValue(name).trim() || '#888'; } catch (e) { /* grey */ }
        var s = probe.fillStyle;
        if (s[0] === '#') { var n = parseInt(s.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
        var m = s.match(/[\d.]+/g) || [136, 136, 136]; return [+m[0], +m[1], +m[2]];
    }
    var mix = function (a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; };
    var rgba = function (c, a) { return 'rgba(' + Math.round(c[0]) + ',' + Math.round(c[1]) + ',' + Math.round(c[2]) + ',' + a + ')'; };

    // ---- the area: the route's box, padded, stretched to the hero's shape ----
    var lats = route.map(function (p) { return p[0]; }), lons = route.map(function (p) { return p[1]; });
    var box = { n: Math.max.apply(null, lats), s: Math.min.apply(null, lats), e: Math.max.apply(null, lons), w: Math.min.apply(null, lons) };
    var GRID_W = 320;

    function heroAspect() { var r = hero.getBoundingClientRect(); return Math.max(1.4, r.width / Math.max(1, r.height)); }

    function plan() {
        // Work at zoom 0, stretch the padded box to the hero's shape, then pick the
        // zoom where that box is about 1,400 px of tiles wide (a handful of tiles).
        var x0 = tx(box.w, 0), x1 = tx(box.e, 0), y0 = ty(box.n, 0), y1 = ty(box.s, 0);
        var cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, w = Math.max((x1 - x0) * 1.4, 1e-5), h = Math.max((y1 - y0) * 1.4, 1e-5);
        var asp = heroAspect();
        if (w / h < asp) w = h * asp; else h = w / asp;
        var z = Math.max(3, Math.min(13, Math.floor(Math.log(1400 / (w * 256)) / Math.LN2)));
        var k = Math.pow(2, z);
        return { z: z, x0: (cx - w / 2) * k, x1: (cx + w / 2) * k, y0: (cy - h / 2) * k, y1: (cy + h / 2) * k };
    }

    function loadTile(z, x, y) {
        return new Promise(function (res) {
            var n = Math.pow(2, z); x = ((x % n) + n) % n;
            if (y < 0 || y >= n) { res(null); return; }
            var img = new Image(); img.crossOrigin = 'anonymous';
            img.onload = function () { res(img); }; img.onerror = function () { res(null); };
            img.src = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/' + z + '/' + x + '/' + y + '.png';
        });
    }

    function heights(P) {
        var X0 = Math.floor(P.x0), X1 = Math.floor(P.x1), Y0 = Math.floor(P.y0), Y1 = Math.floor(P.y1);
        if ((X1 - X0 + 1) * (Y1 - Y0 + 1) > 30) return Promise.resolve(null);
        var jobs = [];
        for (var y = Y0; y <= Y1; y++) for (var x = X0; x <= X1; x++) jobs.push({ x: x, y: y, p: loadTile(P.z, x, y) });
        return Promise.all(jobs.map(function (j) { return j.p; })).then(function (imgs) {
            if (imgs.some(function (i) { return !i; })) return null;
            var mw = (X1 - X0 + 1) * 256, mh = (Y1 - Y0 + 1) * 256;
            var mc = document.createElement('canvas'); mc.width = mw; mc.height = mh;
            var mx = mc.getContext('2d', { willReadFrequently: true });
            jobs.forEach(function (j, k) { mx.drawImage(imgs[k], (j.x - X0) * 256, (j.y - Y0) * 256); });
            var px;
            try { px = mx.getImageData(0, 0, mw, mh).data; } catch (e) { return null; }
            var GW = GRID_W, GH = Math.max(8, Math.round(GW * (P.y1 - P.y0) / (P.x1 - P.x0)));
            var H = new Float32Array(GW * GH);
            var at = function (u, v) { var i = (Math.min(mh - 1, Math.max(0, v)) * mw + Math.min(mw - 1, Math.max(0, u))) * 4; return px[i] * 256 + px[i + 1] + px[i + 2] / 256 - 32768; };
            for (var gy = 0; gy < GH; gy++) for (var gx = 0; gx < GW; gx++) {
                var u = (P.x0 + (gx + 0.5) / GW * (P.x1 - P.x0) - X0) * 256, v = (P.y0 + (gy + 0.5) / GH * (P.y1 - P.y0) - Y0) * 256;
                var iu = Math.floor(u), iv = Math.floor(v), fu = u - iu, fv = v - iv;
                H[gy * GW + gx] = at(iu, iv) * (1 - fu) * (1 - fv) + at(iu + 1, iv) * fu * (1 - fv) + at(iu, iv + 1) * (1 - fu) * fv + at(iu + 1, iv + 1) * fu * fv;
            }
            return { H: H, GW: GW, GH: GH, P: P };
        });
    }

    // ---- marching squares: one set of segments per level ----
    function contours(G) {
        var H = G.H, GW = G.GW, GH = G.GH, lo = Infinity, hi = -Infinity, i;
        for (i = 0; i < H.length; i++) { if (H[i] < lo) lo = H[i]; if (H[i] > hi) hi = H[i]; }
        var unit = metric ? 1 : 0.3048, span = (hi - lo) / unit;
        var nice = metric ? [5, 10, 20, 25, 50, 100, 200, 250, 500] : [10, 20, 40, 50, 100, 200, 250, 500, 1000, 2000];
        var step = nice[nice.length - 1];
        for (i = 0; i < nice.length; i++) if (span / nice[i] <= 26) { step = nice[i]; break; }
        var levels = [];
        for (var v = Math.ceil(lo / unit / step) * step; v * unit < hi; v += step) levels.push(v);
        var segs = levels.map(function (lv) {
            var t = lv * unit, out = [];
            for (var y = 0; y < GH - 1; y++) for (var x = 0; x < GW - 1; x++) {
                var a = H[y * GW + x], b = H[y * GW + x + 1], c = H[(y + 1) * GW + x + 1], d = H[(y + 1) * GW + x];
                var up = (a > t) + (b > t) + (c > t) + (d > t); if (up === 0 || up === 4) continue;
                var p = [];
                if ((a > t) !== (b > t)) p.push(x + (t - a) / (b - a), y);
                if ((b > t) !== (c > t)) p.push(x + 1, y + (t - b) / (c - b));
                if ((d > t) !== (c > t)) p.push(x + (t - d) / (c - d), y + 1);
                if ((a > t) !== (d > t)) p.push(x, y + (t - a) / (d - a));
                for (var k = 0; k + 3 < p.length; k += 4) out.push(p[k], p[k + 1], p[k + 2], p[k + 3]);
            }
            return out;
        });
        return { levels: levels, segs: segs, step: step, index: step * 5 };
    }

    var G = null, C = null, prog = 1, raf = 0;
    var ctx = cv.getContext('2d');
    function draw() {
        var r = cv.getBoundingClientRect(), dp = Math.min(2, devicePixelRatio || 1), W = Math.max(1, r.width), Hh = Math.max(1, r.height);
        if (cv.width !== Math.round(W * dp) || cv.height !== Math.round(Hh * dp)) { cv.width = Math.round(W * dp); cv.height = Math.round(Hh * dp); }
        ctx.setTransform(dp, 0, 0, dp, 0, 0); ctx.clearRect(0, 0, W, Hh);
        if (!G || !C) return;
        var sx = W / (G.GW - 1), sy = Hh / (G.GH - 1), s = Math.max(sx, sy), ox = (W - (G.GW - 1) * s) / 2, oy = (Hh - (G.GH - 1) * s) / 2;
        var lo = tok('--c-course'), mid = tok('--accent'), top = tok('--ink'), n = C.levels.length;
        ctx.lineJoin = 'round';
        C.levels.forEach(function (lv, k) {
            var a = clamp((prog * (n + 6) - k) / 6, 0, 1); if (a <= 0) return;
            var u = n > 1 ? k / (n - 1) : 0, c = u < 0.5 ? mix(lo, mid, u * 2) : mix(mid, top, (u - 0.5) * 2);
            var idx = lv % C.index === 0, sg = C.segs[k];
            ctx.strokeStyle = rgba(c, a * (idx ? 0.62 : 0.32)); ctx.lineWidth = idx ? 1.4 : 0.8;
            ctx.beginPath();
            for (var j = 0; j < sg.length; j += 4) { ctx.moveTo(ox + sg[j] * s, oy + sg[j + 1] * s); ctx.lineTo(ox + sg[j + 2] * s, oy + sg[j + 3] * s); }
            ctx.stroke();
        });
        var ra = clamp(prog * 2 - 1, 0, 1);
        if (ra > 0) {
            var P = G.P, z = P.z;
            ctx.beginPath();
            route.forEach(function (p, j) {
                var gx = (tx(p[1], z) - P.x0) / (P.x1 - P.x0) * G.GW - 0.5, gy = (ty(p[0], z) - P.y0) / (P.y1 - P.y0) * G.GH - 0.5;
                var x = ox + gx * s, y = oy + gy * s; if (j) ctx.lineTo(x, y); else ctx.moveTo(x, y);
            });
            ctx.setLineDash([6, 5]); ctx.strokeStyle = rgba(tok('--c-fuel'), 0.75 * ra); ctx.lineWidth = 2; ctx.stroke(); ctx.setLineDash([]);
        }
    }
    function rise() {
        if (calm()) { prog = 1; draw(); return; }
        var t0 = performance.now();
        cancelAnimationFrame(raf);
        var tick = function (now) { prog = clamp((now - t0) / 3600, 0, 1); draw(); if (prog < 1) raf = requestAnimationFrame(tick); };
        raf = requestAnimationFrame(tick);
    }

    var started = false;
    function start() {
        if (started) return; started = true;
        heights(plan()).then(function (g) {
            if (!g) return;
            G = g; C = contours(g);
            hero.classList.add('topo-ready');
            if (cap) { cap.hidden = false; cap.textContent = 'Contours every ' + C.step + (metric ? ' m' : ' ft') + ' · terrain AWS/Mapzen'; }
            prog = 0; rise();
        }).catch(function () { /* the plain header stays */ });
    }
    // The hero is the top of the page: start at once when it's already on screen.
    if (hero.getBoundingClientRect().top < innerHeight || !('IntersectionObserver' in window)) start();
    else {
        new IntersectionObserver(function (es, o) { if (es[0].isIntersecting) { o.disconnect(); start(); } }).observe(hero);
    }
    if ('ResizeObserver' in window) new ResizeObserver(function () { if (G) draw(); }).observe(cv);
    document.addEventListener('tg:theme', function () { requestAnimationFrame(draw); });
})();
