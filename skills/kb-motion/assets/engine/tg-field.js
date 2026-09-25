/* TGField: a field of dots that can become any shape.
 *
 * One WebGL draw call. Every dot carries two positions, two colours and two
 * sizes, and the vertex shader blends them with a staggered, curved ease, so a
 * morph is one number going from 0 to 1. Shapes come from sampling canvas text,
 * the mascot's pixels, elevation profiles and GPS routes.
 *
 * Used by the home page's plan story (home-motion.js), the 404 page and the
 * course page's map loader. Everything reads the active theme's tokens, rests
 * on a finished frame under reduced motion, and stops drawing when it scrolls
 * out of view or the tab is hidden.
 */
(function () {
    'use strict';
    var root = document.documentElement;
    var clamp = function (v, a, b) { a = a === undefined ? 0 : a; b = b === undefined ? 1 : b; return Math.min(b, Math.max(a, v)); };
    var rmq = matchMedia('(prefers-reduced-motion: reduce)');
    var calm = function () { return rmq.matches; };

    // ---- colour from the theme's tokens ----
    var probe = document.createElement('canvas').getContext('2d');
    function colour(v) {
        probe.fillStyle = '#888888';
        try { probe.fillStyle = String(v || '').trim() || '#888888'; } catch (e) { /* keep grey */ }
        var s = probe.fillStyle;
        if (s[0] === '#') { var n = parseInt(s.slice(1), 16); return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255]; }
        var m = s.match(/[\d.]+/g) || [136, 136, 136];
        return [m[0] / 255, m[1] / 255, m[2] / 255];
    }
    var TOKENS = { fuel: '--c-fuel', aid: '--c-aid', course: '--c-course', gear: '--c-gear', accent: '--accent',
        gold: '--gold', ink: '--ink', inkBright: '--ink-bright', bg: '--bg-1', bg0: '--bg-0', muted: '--muted' };
    function tok(key) {
        var cs = getComputedStyle(root);
        var v = cs.getPropertyValue(TOKENS[key] || key);
        if (!String(v).trim() && key === 'inkBright') v = cs.getPropertyValue('--ink');
        return colour(v);
    }
    var mix = function (a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; };
    var css = function (c, a) { return 'rgba(' + Math.round(c[0] * 255) + ',' + Math.round(c[1] * 255) + ',' + Math.round(c[2] * 255) + ',' + (a === undefined ? 1 : a) + ')'; };
    var luma = function (c) { return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; };
    var isDark = function () { return luma(tok('bg0')) < 0.4; };

    // Theme switches: tg-store.js fires tg:theme once the theme's CSS is in.
    var themeFns = [];
    function onTheme(fn) { themeFns.push(fn); }
    var fireTheme = function () { requestAnimationFrame(function () { themeFns.forEach(function (fn) { try { fn(); } catch (e) { console.error(e); } }); }); };
    document.addEventListener('tg:theme', fireTheme);
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', fireTheme);

    var fontsReady = (document.fonts && document.fonts.load)
        ? Promise.all(['800 100px "Red Hat Display"', '700 40px "Red Hat Display"'].map(function (f) { return document.fonts.load(f); }))
            .then(function () { return document.fonts.ready; }).catch(function () {})
        : Promise.resolve();

    function sampleArr(a, f) { var n = a.length, t = clamp(f) * (n - 1), i = Math.min(n - 2, Math.floor(t)); return a[i] + (a[i + 1] - a[i]) * (t - i); }
    function budget(big, mid, small) { return innerWidth >= 1000 ? big : innerWidth >= 640 ? mid : small; }
    function hav(a, b) {
        var R = 6371000, r = Math.PI / 180, dLat = (b[0] - a[0]) * r, dLon = (b[1] - a[1]) * r;
        var s = Math.pow(Math.sin(dLat / 2), 2) + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.pow(Math.sin(dLon / 2), 2);
        return 2 * R * Math.asin(Math.sqrt(s));
    }
    function routeTable(route) {
        var cum = [0];
        for (var i = 1; i < route.length; i++) cum.push(cum[i - 1] + hav(route[i - 1], route[i]));
        var tot = cum[cum.length - 1] || 1;
        return { at: function (f) {
            var t = clamp(f) * tot, lo = 0, hi = cum.length - 1;
            while (hi - lo > 1) { var m = (lo + hi) >> 1; if (cum[m] <= t) lo = m; else hi = m; }
            var k = (t - cum[lo]) / ((cum[hi] - cum[lo]) || 1);
            return [route[lo][0] + (route[hi][0] - route[lo][0]) * k, route[lo][1] + (route[hi][1] - route[lo][1]) * k];
        } };
    }
    function projector(route, box) {          // lat/lon into a box, north up, aspect kept
        var lat0 = route.reduce(function (s, p) { return s + p[0]; }, 0) / route.length, k = Math.cos(lat0 * Math.PI / 180);
        var xs = route.map(function (p) { return p[1] * k; }), ys = route.map(function (p) { return -p[0]; });
        var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs), y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
        var s = Math.min(box.w / ((x1 - x0) || 1), box.h / ((y1 - y0) || 1));
        var ox = box.x + (box.w - (x1 - x0) * s) / 2, oy = box.y + (box.h - (y1 - y0) * s) / 2;
        return function (p) { return [ox + (p[1] * k - x0) * s, oy + (-p[0] - y0) * s]; };
    }

    // ---- the engine ----
    var VS = [
        'attribute vec2 aFrom; attribute vec2 aTo; attribute vec3 aCFrom; attribute vec3 aCTo; attribute vec2 aSeed; attribute vec2 aSize;',
        'uniform float uT; uniform float uSpread; uniform float uSwirl; uniform float uTime; uniform float uJitter;',
        'uniform float uSizePx; uniform float uDpr; uniform float uLens; uniform vec2 uRes; uniform vec3 uMouse; uniform vec4 uBurst;',
        'varying vec3 vC; varying float vS;',
        'void main() {',
        '    float p = clamp(uT * (1.0 + uSpread) - aSeed.x * uSpread, 0.0, 1.0);',
        '    float e = p < 0.5 ? 4.0 * p * p * p : 1.0 - pow(-2.0 * p + 2.0, 3.0) / 2.0;',
        '    vec2 d = aTo - aFrom; float L = length(d);',
        '    vec2 perp = L > 0.001 ? vec2(-d.y, d.x) / L : vec2(0.0);',
        '    vec2 pos = aFrom + d * e + perp * sin(3.14159265 * e) * (aSeed.y - 0.5) * 2.0 * uSwirl * min(1.0, L / 160.0);',
        '    pos += vec2(sin(uTime * 1.3 + aSeed.y * 61.0), cos(uTime * 1.07 + aSeed.x * 47.0)) * uJitter;',
        '    float lens = 0.0;',
        '    if (uMouse.z > 0.5) {',
        '        vec2 m = pos - uMouse.xy; float dm = length(m);',
        '        lens = 1.0 - smoothstep(0.0, uLens, dm);',
        '        if (dm > 0.001) pos += m / dm * lens * lens * uLens * 0.6;',
        '    }',
        '    if (uBurst.w > 0.0) {',
        '        vec2 b = pos - uBurst.xy; float db = length(b);',
        '        float k = exp(-uBurst.z * 2.6) * (1.0 - smoothstep(0.0, 360.0, db));',
        '        if (db > 0.001) pos += b / db * k * uBurst.w * (0.6 + aSeed.y);',
        '    }',
        '    vec2 clip = pos / uRes * 2.0 - 1.0;',
        '    gl_Position = vec4(clip.x, -clip.y, 0.0, 1.0);',
        '    float s = mix(aSize.x, aSize.y, e);',
        '    vS = s;',
        '    gl_PointSize = s * uSizePx * uDpr * (0.8 + 0.45 * aSeed.y) * (1.0 + lens * 0.9);',
        '    vC = mix(aCFrom, aCTo, e);',
        '}'].join('\n');
    var FS = [
        'precision mediump float;',
        'varying vec3 vC; varying float vS; uniform float uAlpha;',
        'void main() {',
        '    if (vS < 0.02) discard;',
        '    vec2 c = gl_PointCoord - 0.5; float r = dot(c, c) * 4.0;',
        '    float a = 1.0 - smoothstep(0.45, 1.0, r);',
        '    if (a <= 0.0) discard;',
        '    gl_FragColor = vec4(vC, a * uAlpha);',
        '}'].join('\n');

    function DotField(canvas, N, opts) {
        opts = opts || {};
        var gl = null;
        try { gl = canvas.getContext('webgl', { alpha: true, antialias: false, premultipliedAlpha: false }); } catch (e) { gl = null; }
        if (!gl) return null;
        var compile = function (type, src) {
            var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
            if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
            return s;
        };
        var prog = gl.createProgram();
        gl.attachShader(prog, compile(gl.VERTEX_SHADER, VS)); gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FS));
        gl.linkProgram(prog);
        if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
        gl.useProgram(prog);
        var dims = { aFrom: 2, aTo: 2, aCFrom: 3, aCTo: 3, aSeed: 2, aSize: 2 };
        var arr = {}, buf = {}, A = {}, k;
        for (k in dims) {
            arr[k] = new Float32Array(N * dims[k]);
            A[k] = gl.getAttribLocation(prog, k);
            buf[k] = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf[k]);
            gl.bufferData(gl.ARRAY_BUFFER, arr[k], gl.DYNAMIC_DRAW);
            if (A[k] >= 0) { gl.enableVertexAttribArray(A[k]); gl.vertexAttribPointer(A[k], dims[k], gl.FLOAT, false, 0, 0); }
        }
        var i;
        for (i = 0; i < N * 2; i++) arr.aSeed[i] = Math.random();
        for (i = 0; i < N * 2; i++) arr.aSize[i] = 1;
        var U = {};
        ['uT', 'uSpread', 'uSwirl', 'uTime', 'uJitter', 'uSizePx', 'uDpr', 'uLens', 'uRes', 'uMouse', 'uBurst', 'uAlpha'].forEach(function (n) { U[n] = gl.getUniformLocation(prog, n); });
        var upload = function () { for (var j = 0; j < arguments.length; j++) { var key = arguments[j]; gl.bindBuffer(gl.ARRAY_BUFFER, buf[key]); gl.bufferSubData(gl.ARRAY_BUFFER, 0, arr[key]); } };
        upload('aSeed', 'aSize');
        var api = {
            N: N, canvas: canvas, w: 1, h: 1, dpr: 1, T: 1, spread: 0.55, swirl: 60, auto: null,
            sizePx: opts.size || 2.1, jitter: opts.jitter === undefined ? 0.3 : opts.jitter, lens: opts.lens || 90, alpha: opts.alpha || 0.92,
            mouse: [0, 0, 0], burst: [0, 0, 0, 0], burstT0: 0, onResize: null,
        };
        api.resize = function () {
            var r = canvas.getBoundingClientRect();
            api.dpr = Math.min(2, devicePixelRatio || 1);
            api.w = Math.max(1, r.width); api.h = Math.max(1, r.height);
            canvas.width = Math.round(api.w * api.dpr); canvas.height = Math.round(api.h * api.dpr);
        };
        api.resize();
        var lastW = api.w, lastH = api.h;
        if ('ResizeObserver' in window) new ResizeObserver(function () {
            var r = canvas.getBoundingClientRect();
            if (Math.abs(r.width - lastW) < 1 && Math.abs(r.height - lastH) < 1) return;
            lastW = r.width; lastH = r.height; api.resize();
            if (api.onResize) api.onResize();
        }).observe(canvas);
        var ease = function (p) { return p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; };
        var cur = new Float32Array(2);
        function curPos(j) {            // the shader's own maths on the CPU, minus the pointer
            var sx = arr.aSeed[j * 2], sy = arr.aSeed[j * 2 + 1];
            var e = ease(clamp(api.T * (1 + api.spread) - sx * api.spread));
            var fx = arr.aFrom[j * 2], fy = arr.aFrom[j * 2 + 1], dx = arr.aTo[j * 2] - fx, dy = arr.aTo[j * 2 + 1] - fy, L = Math.hypot(dx, dy);
            var x = fx + dx * e, y = fy + dy * e;
            if (L > 0.001) { var q = Math.sin(Math.PI * e) * (sy - 0.5) * 2 * api.swirl * Math.min(1, L / 160); x += -dy / L * q; y += dx / L * q; }
            cur[0] = x; cur[1] = y; return e;
        }
        api.set = function (t) {
            arr.aFrom.set(t.pos); arr.aTo.set(t.pos); arr.aCFrom.set(t.col); arr.aCTo.set(t.col);
            for (var j = 0; j < N; j++) { arr.aSize[j * 2] = arr.aSize[j * 2 + 1] = t.size[j]; }
            upload('aFrom', 'aTo', 'aCFrom', 'aCTo', 'aSize'); api.T = 1; api.auto = null;
        };
        api.morph = function (t, o) {
            o = o || {};
            for (var j = 0; j < N; j++) {
                var e = curPos(j);
                arr.aFrom[j * 2] = cur[0]; arr.aFrom[j * 2 + 1] = cur[1];
                for (var c = 0; c < 3; c++) arr.aCFrom[j * 3 + c] += (arr.aCTo[j * 3 + c] - arr.aCFrom[j * 3 + c]) * e;
                arr.aSize[j * 2] += (arr.aSize[j * 2 + 1] - arr.aSize[j * 2]) * e;
                arr.aSize[j * 2 + 1] = t.size[j];
            }
            arr.aTo.set(t.pos); arr.aCTo.set(t.col);
            upload('aFrom', 'aTo', 'aCFrom', 'aCTo', 'aSize');
            api.T = 0; api.spread = o.spread === undefined ? 0.55 : o.spread; api.swirl = o.swirl === undefined ? 60 : o.swirl;
            api.auto = { t0: o.now === undefined ? performance.now() : o.now, dur: o.dur || 1800 };
        };
        api.pair = function (a, b, o) {
            o = o || {};
            arr.aFrom.set(a.pos); arr.aTo.set(b.pos); arr.aCFrom.set(a.col); arr.aCTo.set(b.col);
            for (var j = 0; j < N; j++) { arr.aSize[j * 2] = a.size[j]; arr.aSize[j * 2 + 1] = b.size[j]; }
            upload('aFrom', 'aTo', 'aCFrom', 'aCTo', 'aSize');
            api.spread = o.spread === undefined ? 0.35 : o.spread; api.swirl = o.swirl === undefined ? 26 : o.swirl; api.auto = null;
        };
        api.play = function (dur, now) { api.T = 0; api.auto = { t0: now === undefined ? performance.now() : now, dur: dur }; };
        api.render = function (now) {
            gl.viewport(0, 0, canvas.width, canvas.height);
            gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
            gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
            var still = calm();
            gl.uniform1f(U.uT, api.T); gl.uniform1f(U.uSpread, api.spread); gl.uniform1f(U.uSwirl, api.swirl);
            gl.uniform1f(U.uTime, now / 1000); gl.uniform1f(U.uJitter, still ? 0 : api.jitter);
            gl.uniform1f(U.uSizePx, api.sizePx); gl.uniform1f(U.uDpr, api.dpr); gl.uniform1f(U.uLens, api.lens);
            gl.uniform2f(U.uRes, api.w, api.h); gl.uniform3f(U.uMouse, api.mouse[0], api.mouse[1], still ? 0 : api.mouse[2]);
            var age = (now - api.burstT0) / 1000;
            gl.uniform4f(U.uBurst, api.burst[0], api.burst[1], age, age < 2.5 && !still ? api.burst[3] : 0);
            gl.uniform1f(U.uAlpha, api.alpha);
            gl.drawArrays(gl.POINTS, 0, N);
        };
        api.frame = function (now) {
            if (api.auto) { api.T = clamp((now - api.auto.t0) / api.auto.dur); if (api.T >= 1) api.auto = null; }
            api.render(now);
        };
        if (opts.interactive !== false) {
            canvas.addEventListener('pointermove', function (e) { var r = canvas.getBoundingClientRect(); api.mouse = [e.clientX - r.left, e.clientY - r.top, 1]; });
            canvas.addEventListener('pointerleave', function () { api.mouse[2] = 0; });
            if (opts.burst) canvas.addEventListener('pointerdown', function (e) {
                var r = canvas.getBoundingClientRect();
                api.burst = [e.clientX - r.left, e.clientY - r.top, 0, opts.burst]; api.burstT0 = performance.now();
            });
        }
        return api;
    }

    // ---- shapes ----
    function pickN(cands, N) {
        var out = { pos: new Float32Array(N * 2), col: new Float32Array(N * 3), size: new Float32Array(N) };
        var M = cands.length, idx, i, j, t; if (!M) return out;
        if (M >= N) {
            idx = []; for (i = 0; i < M; i++) idx.push(i);
            for (i = 0; i < N; i++) { j = i + Math.floor(Math.random() * (M - i)); t = idx[i]; idx[i] = idx[j]; idx[j] = t; }
            idx.length = N;
        } else {
            idx = []; for (i = 0; i < N; i++) idx.push(i < M ? i : Math.floor(Math.random() * M));
            for (i = N - 1; i > 0; i--) { j = Math.floor(Math.random() * (i + 1)); t = idx[i]; idx[i] = idx[j]; idx[j] = t; }
        }
        var seen = new Uint8Array(M);
        idx.forEach(function (ci, n) {
            var c = cands[ci], dup = seen[ci]; seen[ci] = 1;
            out.pos[n * 2] = c.x + (dup ? (Math.random() - 0.5) * 1.8 : 0);
            out.pos[n * 2 + 1] = c.y + (dup ? (Math.random() - 0.5) * 1.8 : 0);
            out.col[n * 3] = c.c[0]; out.col[n * 3 + 1] = c.c[1]; out.col[n * 3 + 2] = c.c[2];
            out.size[n] = c.s === undefined ? 1 : c.s;
        });
        return out;
    }
    function textCands(lines, box, colourAt, weight) {
        var w = Math.max(2, Math.round(box.w)), h = Math.max(2, Math.round(box.h));
        var cv = document.createElement('canvas'); cv.width = w; cv.height = h;
        var x = cv.getContext('2d', { willReadFrequently: true });
        var fam = '"Red Hat Display", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
        weight = weight || 800;
        x.font = weight + ' 100px ' + fam;
        var widest = Math.max.apply(null, lines.map(function (l) { return x.measureText(l).width; })) || 1;
        var size = Math.min(w * 0.94 / widest * 100, h * 0.9 / lines.length);
        x.font = weight + ' ' + size + 'px ' + fam; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillStyle = '#fff';
        lines.forEach(function (l, n) { x.fillText(l, w / 2, h / 2 + (n - (lines.length - 1) / 2) * size * 0.98); });
        var data = x.getImageData(0, 0, w, h).data, out = [];
        for (var yy = 0; yy < h; yy++) for (var xx = 0; xx < w; xx++) {
            if (data[(yy * w + xx) * 4 + 3] > 140) out.push({ x: box.x + xx + Math.random() * 0.6, y: box.y + yy + Math.random() * 0.6, c: colourAt(xx / w, yy / h), s: 1 });
        }
        return out;
    }
    function imageCands(img, box) {
        var ar = (img.naturalWidth || 184) / (img.naturalHeight || 240);
        var h = box.h, w = h * ar; if (w > box.w) { w = box.w; h = w / ar; }
        w = Math.max(2, Math.round(w)); h = Math.max(2, Math.round(h));
        var cv = document.createElement('canvas'); cv.width = w; cv.height = h;
        var x = cv.getContext('2d', { willReadFrequently: true }); x.drawImage(img, 0, 0, w, h);
        var data = x.getImageData(0, 0, w, h).data, out = [];
        var dark = isDark(), bg = tok('bg'), ink = tok('ink');
        var ox = box.x + (box.w - w) / 2, oy = box.y + (box.h - h) / 2;
        for (var yy = 0; yy < h; yy++) for (var xx = 0; xx < w; xx++) {
            var q = (yy * w + xx) * 4; if (data[q + 3] < 110) continue;
            var c = [data[q] / 255, data[q + 1] / 255, data[q + 2] / 255];
            var sat = Math.max(c[0], c[1], c[2]) - Math.min(c[0], c[1], c[2]), outline = luma(c) < 0.2;
            if (dark && outline) c = mix(bg, ink, 0.5);                 // the ink outline would vanish on a dark ground
            var copies = outline ? 3 : sat > 0.22 ? 3 : 1;              // outline and coloured gear carry the likeness
            for (var r = 0; r < copies; r++) out.push({ x: ox + xx + Math.random() * 0.9, y: oy + yy + Math.random() * 0.9, c: c, s: outline ? 0.9 : 1 });
        }
        return out;
    }
    function gradeColour() {
        var up = tok('fuel'), down = tok('aid'), ink = tok('ink'), bg = tok('bg');
        var flat = mix(bg, ink, 0.72);
        return function (g, strength) {
            strength = strength === undefined ? 1 : strength;
            var hue = g > 0.03 ? mix(flat, up, clamp((g - 0.01) / 0.07)) : g < -0.03 ? mix(flat, down, clamp((-g - 0.01) / 0.07)) : flat;
            return mix(bg, hue, 0.22 + 0.78 * strength);
        };
    }
    function profileCands(ele, distM, box, N) {
        var n = ele.length, lo = Math.min.apply(null, ele), hi = Math.max.apply(null, ele), span = (hi - lo) || 1;
        var col = gradeColour(), step = distM / (n - 1), out = [];
        var at = function (f) { return sampleArr(ele, f); };
        var yOf = function (v) { return box.y + box.h - (v - lo) / span * box.h; };
        var gAt = function (f) { return (at(f + 1.5 / n) - at(f - 1.5 / n)) / (step * 3); };
        var nLine = Math.round(N * 0.46);
        for (var q = 0; q < N; q++) {
            var f = Math.random(), v = at(f), top = yOf(v), g = gAt(f);
            if (q < nLine) out.push({ x: box.x + f * box.w, y: top + (Math.random() - 0.5) * 1.8, c: col(g, 1), s: 1.08 });
            else { var u = Math.pow(Math.random(), 1.9); out.push({ x: box.x + f * box.w, y: top + u * (box.y + box.h - top), c: col(g, 1 - u * 0.9), s: 0.9 }); }
        }
        return out;
    }
    function routeCands(route, box, N) {
        var rt = routeTable(route), proj = projector(route, box), a = tok('course'), b = tok('accent'), bg = tok('bg'), out = [];
        for (var q = 0; q < N; q++) {
            var f = (q + Math.random()) / N, p = proj(rt.at(f)), r = proj(rt.at(Math.min(1, f + 0.002)));
            var dx = r[0] - p[0], dy = r[1] - p[1], L = Math.hypot(dx, dy) || 1, halo = q % 10 < 3;
            var j = halo ? (Math.random() < 0.5 ? -1 : 1) * (3 + Math.random() * 9) : (Math.random() - 0.5) * 2.8;
            out.push({ x: p[0] - dy / L * j, y: p[1] + dx / L * j, c: halo ? mix(bg, mix(a, b, f), 0.5) : mix(a, b, f), s: halo ? 0.75 : 1.15 });
        }
        return out;
    }
    function dustCands(box, N) {
        var c = mix(tok('bg'), tok('muted'), 0.5), out = [];
        for (var q = 0; q < N; q++) out.push({ x: box.x + Math.random() * box.w, y: box.y + Math.random() * box.h, c: c, s: 0.7 });
        return out;
    }

    // ---- motion governor: draw only while on screen, the tab is visible and motion is allowed ----
    function rafLoop(fn) {
        var id = 0, on = false;
        var tick = function (now) { if (!on) return; fn(now); id = requestAnimationFrame(tick); };
        return { start: function () { if (on) return; on = true; id = requestAnimationFrame(tick); },
                 stop: function () { on = false; cancelAnimationFrame(id); }, get running() { return on; } };
    }
    function govern(el, api) {
        var visible = false, running = false;
        var sync = function () {
            var go = visible && !document.hidden && !calm();
            if (go && !running) { running = true; api.start(); }
            else if (!go && running) { running = false; api.stop(); }
            if (!go && calm() && api.rest) api.rest();
        };
        if ('IntersectionObserver' in window) {
            new IntersectionObserver(function (es) { visible = es[0].isIntersecting; sync(); }, { threshold: 0.1 }).observe(el);
        } else { visible = true; }
        document.addEventListener('visibilitychange', sync);
        rmq.addEventListener('change', sync);
        sync();
        return { get running() { return running; }, sync: sync };
    }

    // ---- ready-made pieces ----
    var goatImg = null;
    function goat() {
        if (goatImg) return goatImg;
        goatImg = new Image(); goatImg.decoding = 'async'; goatImg.src = '/img/goat-field.webp?v=1';
        goatImg.ready = new Promise(function (res) {
            if (goatImg.complete && goatImg.naturalWidth) res(); else { goatImg.onload = res; goatImg.onerror = res; }
        });
        return goatImg;
    }
    var gradient = function () { var a = tok('course'), b = tok('accent'); return function (u) { return mix(a, b, u); }; };

    /* A field that cycles through shapes. Each shape is { build(box, N) → target, label? }.
       Returns null without WebGL, so the caller keeps its fallback. */
    function cycle(canvas, shapes, opts) {
        opts = opts || {};
        var N = opts.dots || budget(7000, 5000, 3000);
        var F = null;
        try { F = DotField(canvas, N, { size: opts.size || (innerWidth < 640 ? 1.8 : 2.0), lens: opts.lens || 90, jitter: 0.3, burst: opts.burst === undefined ? 140 : opts.burst }); }
        catch (e) { console.error(e); }
        if (!F) return null;
        var box = function (fx, fy, fw, fh) { return { x: F.w * fx, y: F.h * fy, w: F.w * fw, h: F.h * fh }; };
        var cache = {}, curI = -1, nextAt = 0, ready = false;
        var MORPH = opts.morph || 1900, HOLD = opts.hold || 2900;
        var target = function (i) { return cache[i] || (cache[i] = shapes[i].build(box, N)); };
        function go(i, now, instant) {
            curI = i;
            if (opts.onShape) opts.onShape(shapes[i], i);
            if (instant) { F.set(target(i)); F.render(now); }
            else F.morph(target(i), { dur: MORPH, spread: 0.55, swirl: 70, now: now });
            nextAt = now + MORPH + HOLD;
        }
        var loop = rafLoop(function (now) {
            if (ready && shapes.length > 1 && now >= nextAt) go((curI + 1) % shapes.length, now, false);
            F.frame(now);
        });
        var gov = null;
        Promise.all([fontsReady, goat().ready]).then(function () {
            ready = true;
            F.set(pickN(dustCands(box(0, 0, 1, 1), N), N));
            if (gov && gov.running) { curI = -1; nextAt = performance.now() + 250; }
            else go(opts.restIndex || 0, performance.now(), true);
        });
        gov = govern(canvas, {
            start: function () { if (ready && curI < 0) nextAt = performance.now() + 250; loop.start(); },
            stop: function () { loop.stop(); },
            rest: function () { if (ready) go(opts.restIndex || 0, performance.now(), true); },
        });
        var rebuild = function () { cache = {}; if (curI >= 0 && ready) { F.set(target(curI)); F.render(performance.now()); } };
        F.onResize = rebuild; onTheme(rebuild);
        return { F: F, go: function (i) { go(i, performance.now(), !gov.running); } };
    }

    /* Dots with momentum: the loader's GPU version. Every particle's position and
       velocity live in a float texture that a shader steps each frame: a spring
       toward the course's profile, a curl-noise swirl that dies away, and damping,
       so the swarm overshoots and settles instead of easing. WebGL2 with float
       render targets only; null otherwise, and loader() falls back to the eased field. */
    function swarm(host, cv, target, N, SIDE) {
        var gl = null;
        try { gl = cv.getContext('webgl2', { alpha: true, antialias: false, premultipliedAlpha: false }); } catch (e) { gl = null; }
        if (!gl) return null;
        var fmt = gl.getExtension('EXT_color_buffer_float') ? gl.RGBA32F : gl.getExtension('EXT_color_buffer_half_float') ? gl.RGBA16F : null;
        if (!fmt) return null;
        var comp = function (t, src) { var sh = gl.createShader(t); gl.shaderSource(sh, src); gl.compileShader(sh); if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(sh)); return sh; };
        var prog = function (a, b) { var pr = gl.createProgram(); gl.attachShader(pr, comp(gl.VERTEX_SHADER, a)); gl.attachShader(pr, comp(gl.FRAGMENT_SHADER, b)); gl.linkProgram(pr); if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(pr)); return pr; };
        var sim, draw;
        try {
            sim = prog('#version 300 es\nin vec2 aP;void main(){gl_Position=vec4(aP,0.,1.);}',
                '#version 300 es\nprecision highp float;precision highp sampler2D;uniform sampler2D uS;uniform sampler2D uT;uniform float uTime,uDt,uK,uNoise;out vec4 o;' +
                'vec2 curl(vec2 p,float t){vec2 a=vec2(.0061,.0043),b=vec2(-.0037,.0079),c=vec2(.0113,-.0052);' +
                'vec2 r=vec2(a.y,-a.x)*cos(dot(a,p)+t*.7);r+=vec2(b.y,-b.x)*cos(dot(b,p)-t*.5)*1.3;r+=vec2(c.y,-c.x)*cos(dot(c,p)+t*.9)*.7;return r*120.;}' +
                'void main(){ivec2 ij=ivec2(gl_FragCoord.xy);vec4 s=texelFetch(uS,ij,0);vec2 p=s.xy,v=s.zw,t=texelFetch(uT,ij,0).xy;' +
                'vec2 acc=(t-p)*uK+curl(p,uTime)*uNoise;v=(v+acc*uDt)*pow(.92,uDt*60.);o=vec4(p+v*uDt,v);}');
            draw = prog('#version 300 es\nprecision highp float;precision highp sampler2D;uniform sampler2D uS;uniform sampler2D uC;uniform int uSide;uniform vec2 uRes;uniform float uSize;out vec3 vC;' +
                'void main(){ivec2 ij=ivec2(gl_VertexID%uSide,gl_VertexID/uSide);vec4 s=texelFetch(uS,ij,0);float sp=clamp(length(s.zw)/600.,0.,1.);' +
                'vC=texelFetch(uC,ij,0).rgb;vec2 c=s.xy/uRes*2.-1.;gl_Position=vec4(c.x,-c.y,0.,1.);gl_PointSize=uSize*(1.+sp*.6);}',
                '#version 300 es\nprecision mediump float;in vec3 vC;uniform float uA;out vec4 o;void main(){vec2 c=gl_PointCoord-.5;float a=1.-smoothstep(.1,.25,dot(c,c));if(a<=0.)discard;o=vec4(vC,a*uA);}');
        } catch (e) { return null; }
        var vao = gl.createVertexArray(); gl.bindVertexArray(vao);
        var tb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, tb); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
        var aP = gl.getAttribLocation(sim, 'aP'); gl.enableVertexAttribArray(aP); gl.vertexAttribPointer(aP, 2, gl.FLOAT, false, 0, 0);
        gl.bindVertexArray(null); var empty = gl.createVertexArray();
        var tex = function (f, format, type, data) {
            var t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
            [gl.TEXTURE_MIN_FILTER, gl.TEXTURE_MAG_FILTER].forEach(function (k) { gl.texParameteri(gl.TEXTURE_2D, k, gl.NEAREST); });
            gl.texImage2D(gl.TEXTURE_2D, 0, f, SIDE, SIDE, 0, format, type, data); return t;
        };
        var r = cv.getBoundingClientRect(), dpr = Math.min(2, devicePixelRatio || 1), W = Math.max(1, r.width), H = Math.max(1, r.height);
        cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
        var init = new Float32Array(SIDE * SIDE * 4), tg = new Float32Array(SIDE * SIDE * 4), col = new Uint8Array(SIDE * SIDE * 4);
        for (var i = 0; i < SIDE * SIDE; i++) {
            var k = i % N;
            init[i * 4] = Math.random() * W; init[i * 4 + 1] = Math.random() * H;
            tg[i * 4] = target.pos[k * 2]; tg[i * 4 + 1] = target.pos[k * 2 + 1];
            col[i * 4] = target.col[k * 3] * 255; col[i * 4 + 1] = target.col[k * 3 + 1] * 255; col[i * 4 + 2] = target.col[k * 3 + 2] * 255; col[i * 4 + 3] = 255;
        }
        var A = tex(fmt, gl.RGBA, gl.FLOAT, init), B = tex(fmt, gl.RGBA, gl.FLOAT, init), T = tex(gl.RGBA32F, gl.RGBA, gl.FLOAT, tg), Cc = tex(gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, col);
        var fb = function (t) { var f = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, f); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0); var ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE; gl.bindFramebuffer(gl.FRAMEBUFFER, null); return ok ? f : null; };
        var fA = fb(A), fB = fb(B);
        if (!fA || !fB) return null;
        var U = function (pr, n) { return gl.getUniformLocation(pr, n); };
        var cur = 0, last = 0, t0 = performance.now(), dark = isDark();
        function frame(now) {
            var dt = last ? Math.min(0.033, (now - last) / 1000) : 1 / 60; last = now;
            var since = (now - t0) / 1000;
            gl.useProgram(sim); gl.bindVertexArray(vao); gl.disable(gl.BLEND);
            gl.bindFramebuffer(gl.FRAMEBUFFER, cur ? fA : fB); gl.viewport(0, 0, SIDE, SIDE);
            gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, cur ? B : A); gl.uniform1i(U(sim, 'uS'), 0);
            gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, T); gl.uniform1i(U(sim, 'uT'), 1);
            gl.uniform1f(U(sim, 'uTime'), now / 1000); gl.uniform1f(U(sim, 'uDt'), dt);
            gl.uniform1f(U(sim, 'uK'), 2 + 20 * (1 - Math.exp(-since / 0.7)));
            gl.uniform1f(U(sim, 'uNoise'), 40 + 1500 * Math.exp(-since / 0.5));
            gl.drawArrays(gl.TRIANGLES, 0, 3); cur = 1 - cur;
            gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.viewport(0, 0, cv.width, cv.height);
            gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
            gl.useProgram(draw); gl.bindVertexArray(empty); gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, dark ? gl.ONE : gl.ONE_MINUS_SRC_ALPHA);
            gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, cur ? B : A); gl.uniform1i(U(draw, 'uS'), 0);
            gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, Cc); gl.uniform1i(U(draw, 'uC'), 1);
            gl.uniform1i(U(draw, 'uSide'), SIDE); gl.uniform2f(U(draw, 'uRes'), W, H); gl.uniform1f(U(draw, 'uSize'), 2.0 * dpr);
            gl.uniform1f(U(draw, 'uA'), dark ? 0.55 : 0.85);
            gl.drawArrays(gl.POINTS, 0, SIDE * SIDE);
        }
        var loop = rafLoop(frame);
        loop.start();
        return { stop: function () { loop.stop(); } };
    }

    /* The course loader: dust gathers into the course's own profile while the map
       draws, then the whole thing fades as the map arrives. `ele` is optional; with
       none the dots form the goat. Returns { done() }. */
    function loader(host, ele, distM) {
        if (!host) return { done: function () {} };
        var cv = document.createElement('canvas');
        cv.className = 'tg-field-loader'; cv.setAttribute('aria-hidden', 'true');
        host.insertBefore(cv, host.firstChild);
        var N = budget(2600, 2000, 1400), F = null;
        // Dots with momentum first: a GPU swarm that swirls into the course's profile.
        if (!calm() && ele && ele.length > 3) {
            var SIDE = innerWidth >= 1000 ? 96 : 72, sw = null;
            try {
                var r0 = cv.getBoundingClientRect(), bx = { x: r0.width * 0.08, y: r0.height * 0.22, w: r0.width * 0.84, h: r0.height * 0.46 };
                sw = swarm(host, cv, pickN(profileCands(ele, distM || 1, bx, SIDE * SIDE), SIDE * SIDE), SIDE * SIDE, SIDE);
            } catch (e) { sw = null; }
            if (sw) {
                host.classList.add('has-field');
                var over = false;
                return { swarm: true, done: function () {
                    if (over) return; over = true; cv.classList.add('out');
                    setTimeout(function () { sw.stop(); cv.remove(); host.classList.remove('has-field'); }, 450);
                } };
            }
            // no WebGL2: this canvas may hold a failed context, so start fresh
            var fresh = document.createElement('canvas'); fresh.className = cv.className; fresh.setAttribute('aria-hidden', 'true');
            cv.replaceWith(fresh); cv = fresh;
        }
        try { F = DotField(cv, N, { size: 2.2, jitter: 0.35, interactive: false }); } catch (e) { F = null; }
        if (!F) { cv.remove(); return { done: function () {} }; }
        host.classList.add('has-field');
        var box = function (fx, fy, fw, fh) { return { x: F.w * fx, y: F.h * fy, w: F.w * fw, h: F.h * fh }; };
        var shape = function () {
            return ele && ele.length > 3 ? pickN(profileCands(ele, distM || 1, box(0.08, 0.22, 0.84, 0.46), N), N)
                : pickN(imageCands(goat(), box(0.3, 0.1, 0.4, 0.62)), N);
        };
        var loop = rafLoop(function (now) { F.frame(now); });
        var finished = false;
        var begin = function () {
            if (finished) return;
            if (calm()) { F.set(shape()); F.render(performance.now()); return; }
            F.set(pickN(dustCands(box(0, 0, 1, 1), N), N));
            F.morph(shape(), { dur: 1500, spread: 0.6, swirl: 50 });
            loop.start();
        };
        F.onResize = function () { if (!finished) { F.set(shape()); F.render(performance.now()); } };   // settle at the new size
        if (ele && ele.length > 3) begin(); else goat().ready.then(begin);
        return { done: function () {
            if (finished) return; finished = true;
            cv.classList.add('out');
            setTimeout(function () { loop.stop(); cv.remove(); host.classList.remove('has-field'); }, calm() ? 0 : 450);
        } };
    }

    window.TGField = {
        DotField: DotField, pickN: pickN, textCands: textCands, imageCands: imageCands, profileCands: profileCands,
        routeCands: routeCands, dustCands: dustCands, gradeColour: gradeColour, routeTable: routeTable, projector: projector,
        sampleArr: sampleArr, budget: budget, tok: tok, colour: colour, mix: mix, css: css, isDark: isDark, clamp: clamp, calm: calm,
        onTheme: onTheme, fontsReady: fontsReady, rafLoop: rafLoop, govern: govern, goat: goat, gradient: gradient,
        cycle: cycle, loader: loader,
    };
})();
