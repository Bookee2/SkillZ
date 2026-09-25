/* =================== v2: shared colour, data and theme helpers =================== */
const D2 = __DATA2__;
const hexRGB = h => {
    h = String(h || '').trim().replace('#', '');
    if (h.length === 3) h = h.split('').map(c => c + c).join('');
    const n = parseInt(h || '888888', 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
};
const tokRGB = name => hexRGB(getComputedStyle(root).getPropertyValue(name));
const mixRGB = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
const rgbCss = (c, a = 1) => `rgba(${Math.round(c[0] * 255)},${Math.round(c[1] * 255)},${Math.round(c[2] * 255)},${a})`;
const luma = c => 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
const isDark = () => luma(tokRGB('--bg-0')) < 0.4;
const themeFns = [];
const onTheme = fn => themeFns.push(fn);
{
    const fire = () => requestAnimationFrame(() => themeFns.forEach(fn => { try { fn(); } catch (e) { console.error(e); } }));
    new MutationObserver(fire).observe(root, { attributes: true, attributeFilter: ['data-theme'] });
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', fire);
}
const fontsReady = (document.fonts && document.fonts.load)
    ? Promise.all(['900 100px "Red Hat Display"', '700 40px "Red Hat Display"', '300 40px "Red Hat Display"']
        .map(f => document.fonts.load(f))).then(() => document.fonts.ready).catch(() => {})
    : Promise.resolve();
const sampleArr = (a, f) => { const n = a.length, t = clamp(f) * (n - 1), i = Math.min(n - 2, Math.floor(t)); return a[i] + (a[i + 1] - a[i]) * (t - i); };
const dotBudget = (big, mid, small) => innerWidth >= 1000 ? big : innerWidth >= 640 ? mid : small;
const hav = (a, b) => {
    const R = 6371000, r = Math.PI / 180, dLat = (b[0] - a[0]) * r, dLon = (b[1] - a[1]) * r;
    const s = Math.sin(dLat / 2) ** 2 + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(s));
};
function routeTable(route) {
    const cum = [0];
    for (let i = 1; i < route.length; i++) cum.push(cum[i - 1] + hav(route[i - 1], route[i]));
    const tot = cum[cum.length - 1] || 1;
    return {
        at(f) {
            const t = clamp(f) * tot; let lo = 0, hi = cum.length - 1;
            while (hi - lo > 1) { const m = (lo + hi) >> 1; if (cum[m] <= t) lo = m; else hi = m; }
            const k = (t - cum[lo]) / ((cum[hi] - cum[lo]) || 1);
            return [route[lo][0] + (route[hi][0] - route[lo][0]) * k, route[lo][1] + (route[hi][1] - route[lo][1]) * k];
        },
    };
}
function projector(route, box) {          // lat/lon into a box, north up, aspect kept
    const lat0 = route.reduce((s, p) => s + p[0], 0) / route.length, k = Math.cos(lat0 * Math.PI / 180);
    const xs = route.map(p => p[1] * k), ys = route.map(p => -p[0]);
    const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    const s = Math.min(box.w / ((x1 - x0) || 1), box.h / ((y1 - y0) || 1));
    const ox = box.x + (box.w - (x1 - x0) * s) / 2, oy = box.y + (box.h - (y1 - y0) * s) / 2;
    return p => [ox + (p[1] * k - x0) * s, oy + (-p[0] - y0) * s];
}

/* =================== v2: DotField, a WebGL point engine =================== */
/* Every dot carries two positions, two colours and two sizes. The vertex shader
   blends them with a per-dot staggered ease and a sideways swing, so a morph is
   one uniform changing from 0 to 1 (the Three.js Journey morphing technique,
   without the library). The pointer is a lens in the same shader. */
const DF_VS = `
attribute vec2 aFrom; attribute vec2 aTo; attribute vec3 aCFrom; attribute vec3 aCTo; attribute vec2 aSeed; attribute vec2 aSize;
uniform float uT; uniform float uSpread; uniform float uSwirl; uniform float uTime; uniform float uJitter;
uniform float uSizePx; uniform float uDpr; uniform float uLens; uniform vec2 uRes; uniform vec3 uMouse; uniform vec4 uBurst;
varying vec3 vC; varying float vS;
void main() {
    float p = clamp(uT * (1.0 + uSpread) - aSeed.x * uSpread, 0.0, 1.0);
    float e = p < 0.5 ? 4.0 * p * p * p : 1.0 - pow(-2.0 * p + 2.0, 3.0) / 2.0;
    vec2 d = aTo - aFrom; float L = length(d);
    vec2 perp = L > 0.001 ? vec2(-d.y, d.x) / L : vec2(0.0);
    vec2 pos = aFrom + d * e + perp * sin(3.14159265 * e) * (aSeed.y - 0.5) * 2.0 * uSwirl * min(1.0, L / 160.0);
    pos += vec2(sin(uTime * 1.3 + aSeed.y * 61.0), cos(uTime * 1.07 + aSeed.x * 47.0)) * uJitter;
    float lens = 0.0;
    if (uMouse.z > 0.5) {
        vec2 m = pos - uMouse.xy; float dm = length(m);
        lens = 1.0 - smoothstep(0.0, uLens, dm);
        if (dm > 0.001) pos += m / dm * lens * lens * uLens * 0.6;
    }
    if (uBurst.w > 0.0) {
        vec2 b = pos - uBurst.xy; float db = length(b);
        float k = exp(-uBurst.z * 2.6) * (1.0 - smoothstep(0.0, 360.0, db));
        if (db > 0.001) pos += b / db * k * uBurst.w * (0.6 + aSeed.y);
    }
    vec2 clip = pos / uRes * 2.0 - 1.0;
    gl_Position = vec4(clip.x, -clip.y, 0.0, 1.0);
    float s = mix(aSize.x, aSize.y, e);
    vS = s;
    gl_PointSize = s * uSizePx * uDpr * (0.8 + 0.45 * aSeed.y) * (1.0 + lens * 0.9);
    vC = mix(aCFrom, aCTo, e);
}`;
const DF_FS = `
precision mediump float;
varying vec3 vC; varying float vS; uniform float uAlpha;
void main() {
    if (vS < 0.02) discard;
    vec2 c = gl_PointCoord - 0.5; float r = dot(c, c) * 4.0;
    float a = 1.0 - smoothstep(0.45, 1.0, r);
    if (a <= 0.0) discard;
    gl_FragColor = vec4(vC, a * uAlpha);
}`;
function DotField(canvas, N, opts = {}) {
    let gl = null;
    try { gl = canvas.getContext('webgl', { alpha: true, antialias: false, premultipliedAlpha: false }); } catch (e) { gl = null; }
    if (!gl) return null;
    const compile = (type, src) => {
        const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
        if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
        return s;
    };
    const prog = gl.createProgram();
    gl.attachShader(prog, compile(gl.VERTEX_SHADER, DF_VS)); gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, DF_FS));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
    gl.useProgram(prog);
    const dims = { aFrom: 2, aTo: 2, aCFrom: 3, aCTo: 3, aSeed: 2, aSize: 2 };
    const arr = {}, buf = {}, A = {};
    for (const k in dims) {
        arr[k] = new Float32Array(N * dims[k]);
        A[k] = gl.getAttribLocation(prog, k);
        buf[k] = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf[k]);
        gl.bufferData(gl.ARRAY_BUFFER, arr[k], gl.DYNAMIC_DRAW);
        if (A[k] >= 0) { gl.enableVertexAttribArray(A[k]); gl.vertexAttribPointer(A[k], dims[k], gl.FLOAT, false, 0, 0); }
    }
    for (let i = 0; i < N * 2; i++) arr.aSeed[i] = Math.random();
    for (let i = 0; i < N * 2; i++) arr.aSize[i] = 1;
    const U = {};
    ['uT', 'uSpread', 'uSwirl', 'uTime', 'uJitter', 'uSizePx', 'uDpr', 'uLens', 'uRes', 'uMouse', 'uBurst', 'uAlpha'].forEach(n => U[n] = gl.getUniformLocation(prog, n));
    const upload = (...keys) => keys.forEach(k => { gl.bindBuffer(gl.ARRAY_BUFFER, buf[k]); gl.bufferSubData(gl.ARRAY_BUFFER, 0, arr[k]); });
    upload('aSeed', 'aSize');
    const api = {
        N, canvas, w: 1, h: 1, dpr: 1, T: 1, spread: 0.55, swirl: 60, auto: null,
        sizePx: opts.size || 2.1, jitter: opts.jitter ?? 0.3, lens: opts.lens || 90, alpha: opts.alpha || 0.92,
        mouse: [0, 0, 0], burst: [0, 0, 0, 0], burstT0: 0, onResize: null,
    };
    api.resize = () => {
        const r = canvas.getBoundingClientRect();
        api.dpr = Math.min(2, devicePixelRatio || 1);
        api.w = Math.max(1, r.width); api.h = Math.max(1, r.height);
        canvas.width = Math.round(api.w * api.dpr); canvas.height = Math.round(api.h * api.dpr);
    };
    api.resize();
    let lastW = api.w, lastH = api.h;
    new ResizeObserver(() => {
        const r = canvas.getBoundingClientRect();
        if (Math.abs(r.width - lastW) < 1 && Math.abs(r.height - lastH) < 1) return;
        lastW = r.width; lastH = r.height; api.resize();
        if (api.onResize) api.onResize();
    }).observe(canvas);
    const ease = p => p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
    const cur = new Float32Array(2);
    function curPos(i) {            // the shader's own maths, on the CPU, minus the pointer
        const sx = arr.aSeed[i * 2], sy = arr.aSeed[i * 2 + 1];
        const e = ease(clamp(api.T * (1 + api.spread) - sx * api.spread));
        const fx = arr.aFrom[i * 2], fy = arr.aFrom[i * 2 + 1], dx = arr.aTo[i * 2] - fx, dy = arr.aTo[i * 2 + 1] - fy, L = Math.hypot(dx, dy);
        let x = fx + dx * e, y = fy + dy * e;
        if (L > 0.001) { const k = Math.sin(Math.PI * e) * (sy - 0.5) * 2 * api.swirl * Math.min(1, L / 160); x += -dy / L * k; y += dx / L * k; }
        cur[0] = x; cur[1] = y; return e;
    }
    api.set = t => {
        arr.aFrom.set(t.pos); arr.aTo.set(t.pos); arr.aCFrom.set(t.col); arr.aCTo.set(t.col);
        for (let i = 0; i < N; i++) { arr.aSize[i * 2] = arr.aSize[i * 2 + 1] = t.size[i]; }
        upload('aFrom', 'aTo', 'aCFrom', 'aCTo', 'aSize'); api.T = 1; api.auto = null;
    };
    api.morph = (t, o = {}) => {
        for (let i = 0; i < N; i++) {
            const e = curPos(i);
            arr.aFrom[i * 2] = cur[0]; arr.aFrom[i * 2 + 1] = cur[1];
            for (let c = 0; c < 3; c++) arr.aCFrom[i * 3 + c] += (arr.aCTo[i * 3 + c] - arr.aCFrom[i * 3 + c]) * e;
            arr.aSize[i * 2] += (arr.aSize[i * 2 + 1] - arr.aSize[i * 2]) * e;
            arr.aSize[i * 2 + 1] = t.size[i];
        }
        arr.aTo.set(t.pos); arr.aCTo.set(t.col);
        upload('aFrom', 'aTo', 'aCFrom', 'aCTo', 'aSize');
        api.T = 0; api.spread = o.spread ?? 0.55; api.swirl = o.swirl ?? 60;
        api.auto = { t0: o.now ?? performance.now(), dur: o.dur ?? 1800 };
    };
    api.pair = (a, b, o = {}) => {
        arr.aFrom.set(a.pos); arr.aTo.set(b.pos); arr.aCFrom.set(a.col); arr.aCTo.set(b.col);
        for (let i = 0; i < N; i++) { arr.aSize[i * 2] = a.size[i]; arr.aSize[i * 2 + 1] = b.size[i]; }
        upload('aFrom', 'aTo', 'aCFrom', 'aCTo', 'aSize');
        api.spread = o.spread ?? 0.35; api.swirl = o.swirl ?? 26; api.auto = null;
    };
    api.play = (dur, now) => { api.T = 0; api.auto = { t0: now ?? performance.now(), dur }; };
    api.render = now => {
        gl.viewport(0, 0, canvas.width, canvas.height);
        gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
        gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        gl.uniform1f(U.uT, api.T); gl.uniform1f(U.uSpread, api.spread); gl.uniform1f(U.uSwirl, api.swirl);
        gl.uniform1f(U.uTime, now / 1000); gl.uniform1f(U.uJitter, calm ? 0 : api.jitter);
        gl.uniform1f(U.uSizePx, api.sizePx); gl.uniform1f(U.uDpr, api.dpr); gl.uniform1f(U.uLens, api.lens);
        gl.uniform2f(U.uRes, api.w, api.h); gl.uniform3f(U.uMouse, api.mouse[0], api.mouse[1], calm ? 0 : api.mouse[2]);
        const age = (now - api.burstT0) / 1000;
        gl.uniform4f(U.uBurst, api.burst[0], api.burst[1], age, age < 2.5 && !calm ? api.burst[3] : 0);
        gl.uniform1f(U.uAlpha, api.alpha);
        gl.drawArrays(gl.POINTS, 0, N);
    };
    api.frame = now => {
        if (api.auto) { api.T = clamp((now - api.auto.t0) / api.auto.dur); if (api.T >= 1) api.auto = null; }
        api.render(now);
    };
    (window.__tgFields = window.__tgFields || []).push(api);
    canvas.addEventListener('pointermove', e => { const r = canvas.getBoundingClientRect(); api.mouse = [e.clientX - r.left, e.clientY - r.top, 1]; });
    canvas.addEventListener('pointerleave', () => { api.mouse[2] = 0; });
    canvas.addEventListener('pointerdown', e => {
        if (!opts.burst && opts.burst !== undefined) return;
        const r = canvas.getBoundingClientRect();
        api.burst = [e.clientX - r.left, e.clientY - r.top, 0, opts.burst ?? 150]; api.burstT0 = performance.now();
    });
    return api;
}

/* ---- shape candidates: text, the mascot, profiles, routes ---- */
function pickN(cands, N) {
    const out = { pos: new Float32Array(N * 2), col: new Float32Array(N * 3), size: new Float32Array(N) };
    const M = cands.length; if (!M) return out;
    let idx;
    if (M >= N) {
        idx = Array.from({ length: M }, (_, i) => i);
        for (let i = 0; i < N; i++) { const j = i + Math.floor(Math.random() * (M - i)); const t = idx[i]; idx[i] = idx[j]; idx[j] = t; }
        idx.length = N;
    } else {
        idx = Array.from({ length: N }, (_, i) => i < M ? i : Math.floor(Math.random() * M));
        for (let i = N - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); const t = idx[i]; idx[i] = idx[j]; idx[j] = t; }
    }
    const seen = new Uint8Array(M);
    idx.forEach((ci, i) => {
        const c = cands[ci], dup = seen[ci]; seen[ci] = 1;
        out.pos[i * 2] = c.x + (dup ? (Math.random() - 0.5) * 1.8 : 0);
        out.pos[i * 2 + 1] = c.y + (dup ? (Math.random() - 0.5) * 1.8 : 0);
        out.col[i * 3] = c.c[0]; out.col[i * 3 + 1] = c.c[1]; out.col[i * 3 + 2] = c.c[2];
        out.size[i] = c.s ?? 1;
    });
    return out;
}
function textCands(lines, box, { weight = 900, color }) {
    const w = Math.max(2, Math.round(box.w)), h = Math.max(2, Math.round(box.h));
    const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
    const x = cv.getContext('2d', { willReadFrequently: true });
    const fam = '"Red Hat Display", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    x.font = `${weight} 100px ${fam}`;
    const widest = Math.max(...lines.map(l => x.measureText(l).width)) || 1;
    const size = Math.min(w * 0.94 / widest * 100, h * 0.9 / lines.length);
    x.font = `${weight} ${size}px ${fam}`; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillStyle = '#fff';
    lines.forEach((l, i) => x.fillText(l, w / 2, h / 2 + (i - (lines.length - 1) / 2) * size * 0.98));
    const data = x.getImageData(0, 0, w, h).data, out = [];
    for (let yy = 0; yy < h; yy++) for (let xx = 0; xx < w; xx++) {
        if (data[(yy * w + xx) * 4 + 3] > 140) out.push({ x: box.x + xx + Math.random() * 0.6, y: box.y + yy + Math.random() * 0.6, c: color(xx / w, yy / h), s: 1 });
    }
    return out;
}
function imageCands(img, box) {
    const ar = (img.naturalWidth || 184) / (img.naturalHeight || 240);
    let h = box.h, w = h * ar; if (w > box.w) { w = box.w; h = w / ar; }
    w = Math.max(2, Math.round(w)); h = Math.max(2, Math.round(h));
    const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
    const x = cv.getContext('2d', { willReadFrequently: true }); x.drawImage(img, 0, 0, w, h);
    const data = x.getImageData(0, 0, w, h).data, out = [];
    const dark = isDark(), bg = tokRGB('--bg-1'), ink = tokRGB('--ink');
    const ox = box.x + (box.w - w) / 2, oy = box.y + (box.h - h) / 2;
    for (let yy = 0; yy < h; yy++) for (let xx = 0; xx < w; xx++) {
        const k = (yy * w + xx) * 4; if (data[k + 3] < 110) continue;
        let c = [data[k] / 255, data[k + 1] / 255, data[k + 2] / 255];
        const sat = Math.max(...c) - Math.min(...c), outline = luma(c) < 0.2;
        if (dark && outline) c = mixRGB(bg, ink, 0.5);                  // the ink outline would vanish on the night ground
        const copies = outline ? 3 : sat > 0.22 ? 3 : 1;                // outline and coloured gear carry the likeness
        for (let r = 0; r < copies; r++) out.push({ x: ox + xx + Math.random() * 0.9, y: oy + yy + Math.random() * 0.9, c, s: outline ? 0.9 : 1 });
    }
    return out;
}
function gradeColour() {
    const up = tokRGB('--fuel'), down = tokRGB('--aid'), ink = tokRGB('--ink'), bg = tokRGB('--bg-1');
    const flat = mixRGB(bg, ink, 0.72);
    return (g, strength = 1) => {
        const hue = g > 0.03 ? mixRGB(flat, up, clamp((g - 0.01) / 0.07)) : g < -0.03 ? mixRGB(flat, down, clamp((-g - 0.01) / 0.07)) : flat;
        return mixRGB(bg, hue, 0.22 + 0.78 * strength);
    };
}
function profileCands(ele, distM, box, N) {
    const n = ele.length, lo = Math.min(...ele), hi = Math.max(...ele), span = (hi - lo) || 1;
    const col = gradeColour(), step = distM / (n - 1), out = [];
    const at = f => sampleArr(ele, f);
    const yOf = v => box.y + box.h - (v - lo) / span * box.h;
    const gAt = f => (at(f + 1.5 / n) - at(f - 1.5 / n)) / (step * 3);
    const nLine = Math.round(N * 0.46);
    for (let k = 0; k < N; k++) {
        const f = Math.random(), v = at(f), top = yOf(v), g = gAt(f);
        if (k < nLine) out.push({ x: box.x + f * box.w, y: top + (Math.random() - 0.5) * 1.8, c: col(g, 1), s: 1.08 });
        else { const u = Math.pow(Math.random(), 1.9); out.push({ x: box.x + f * box.w, y: top + u * (box.y + box.h - top), c: col(g, 1 - u * 0.9), s: 0.9 }); }
    }
    return out;
}
function routeCands(route, box, N) {
    const rt = routeTable(route), proj = projector(route, box), a = tokRGB('--course'), b = tokRGB('--accent'), bg = tokRGB('--bg-1'), out = [];
    for (let k = 0; k < N; k++) {
        const f = (k + Math.random()) / N, p = proj(rt.at(f)), q = proj(rt.at(Math.min(1, f + 0.002)));
        const dx = q[0] - p[0], dy = q[1] - p[1], L = Math.hypot(dx, dy) || 1, halo = k % 10 < 3;
        const j = halo ? (Math.random() < 0.5 ? -1 : 1) * (3 + Math.random() * 9) : (Math.random() - 0.5) * 2.8;
        out.push({ x: p[0] - dy / L * j, y: p[1] + dx / L * j, c: halo ? mixRGB(bg, mixRGB(a, b, f), 0.5) : mixRGB(a, b, f), s: halo ? 0.75 : 1.15 });
    }
    return out;
}
function dustCands(box, N) {
    const c = mixRGB(tokRGB('--bg-1'), tokRGB('--muted'), 0.5), out = [];
    for (let k = 0; k < N; k++) out.push({ x: box.x + Math.random() * box.w, y: box.y + Math.random() * box.h, c, s: 0.7 });
    return out;
}

/* =================== P1. One field, many shapes =================== */
(function fieldDemo() {
    const stage = $('#demo-field'); if (!stage) return;
    const cv = $('#field-canvas'), lab = $('#field-label'), chips = $('#field-chips'), playBtn = $('#field-play');
    const N = dotBudget(9000, 6000, 3200);
    let F = null;
    try { F = DotField(cv, N, { size: innerWidth < 640 ? 1.8 : 2.0, lens: innerWidth < 640 ? 70 : 100, jitter: 0.3 }); } catch (e) { console.error(e); }
    if (!F) { $('.no-webgl', stage).hidden = false; return; }
    const box = (fx, fy, fw, fh) => ({ x: F.w * fx, y: F.h * fy, w: F.w * fw, h: F.h * fh });
    const grad = () => { const a = tokRGB('--course'), b = tokRGB('--accent'); return u => mixRGB(a, b, u); };
    const SHAPES = [
        { key: 'word', name: 'TrailGoat', sub: 'The wordmark, in the launch-kit gradient',
          build: () => { const g = grad(); return pickN(textCands(['TRAILGOAT'], box(0.04, 0.16, 0.92, 0.52), { color: u => g(u) }), N); } },
        { key: 'goat', name: 'The mascot', sub: 'Sampled from the Tokyo Night goat, in its own colours',
          build: () => pickN(imageCands(goatImg, box(0.2, 0.05, 0.6, 0.8)), N) },
        { key: 'wser', name: 'Western States 100', sub: `${(W.distM / MI).toFixed(1)} mi · ${fmt(W.gainM * FT)} ft of climbing`,
          build: () => pickN(profileCands(W.ele, W.distM, box(0.05, 0.2, 0.9, 0.5), N), N) },
        { key: 'map', name: 'Western States, from above', sub: 'Olympic Valley to Auburn, north up',
          build: () => pickN(routeCands(W.route, box(0.2, 0.05, 0.6, 0.78), N), N) },
        { key: 'count', name: `${fmt(D.catalogCount)} race courses`, sub: 'Every one of them has a shape',
          build: () => { const g = grad(); return pickN(textCands([String(D.catalogCount)], box(0.22, 0.08, 0.56, 0.68), { color: u => g(u) }), N); } },
        { key: 'hard', name: 'Hardrock 100', sub: `${(D2.hard.distM / MI).toFixed(1)} mi · ${fmt(D2.hard.gainM * FT)} ft of climbing`,
          build: () => pickN(profileCands(D2.hard.ele, D2.hard.distM, box(0.05, 0.18, 0.9, 0.54), N), N) },
        { key: 'lead', name: 'Leadville 100', sub: `${(D2.lead.distM / MI).toFixed(1)} mi · over Hope Pass and back`,
          build: () => pickN(profileCands(D2.lead.ele, D2.lead.distM, box(0.05, 0.2, 0.9, 0.5), N), N) },
    ];
    SHAPES.forEach((s, i) => {
        const b = document.createElement('button');
        b.type = 'button'; b.className = 'chip-btn'; b.textContent = s.key === 'count' ? String(D.catalogCount) : s.name.replace(', from above', ' map');
        b.setAttribute('aria-pressed', 'false');
        b.addEventListener('click', () => { auto = false; paintPlay(); go(i, performance.now(), calm || !d.running); });
        chips.insertBefore(b, chips.querySelector('.spacer'));
    });
    let cache = {}, curI = -1, auto = true, nextAt = 0;
    const MORPH = 1900, HOLD = 2900;
    const target = i => cache[SHAPES[i].key] || (cache[SHAPES[i].key] = SHAPES[i].build());
    function label(i) {
        lab.innerHTML = `<b>${SHAPES[i].name}</b><span>${SHAPES[i].sub}</span>`;
        $$('button', chips).forEach((b, j) => { if (b !== playBtn) b.setAttribute('aria-pressed', String(j === i)); });
    }
    function go(i, now, instant) {
        curI = i; label(i);
        if (instant) { F.set(target(i)); F.render(now); }
        else F.morph(target(i), { dur: MORPH, spread: 0.55, swirl: 70, now });
        nextAt = now + MORPH + HOLD;
    }
    function paintPlay() {
        playBtn.setAttribute('aria-pressed', String(auto));
        playBtn.querySelector('span').textContent = auto ? 'Pause' : 'Play';
        playBtn.querySelector('svg').innerHTML = auto ? '<path d="M8 5v14M16 5v14"/>' : '<path d="M7 5v14l12-7z"/>';
    }
    playBtn.addEventListener('click', () => { auto = !auto; paintPlay(); if (auto) nextAt = performance.now() + 300; });
    const loop = rafLoop((ms, now) => { if (auto && now >= nextAt) go((curI + 1) % SHAPES.length, now, false); F.frame(now); });
    let ready = false, d = { running: false };
    fontsReady.then(() => {
        ready = true;
        F.set(pickN(dustCands(box(0, 0, 1, 1), N), N)); curI = SHAPES.length - 1;
        nextAt = performance.now() + 500;
        if (calm || !d.running) go(0, performance.now(), true);
    });
    d = register(stage, {
        start() { if (ready) { if (curI < 0) curI = SHAPES.length - 1; nextAt = Math.min(nextAt, performance.now() + 400); } loop.start(); },
        stop() { loop.stop(); },
        rest() { if (ready) go(Math.max(0, curI), performance.now(), true); },
    });
    const rebuild = () => { cache = {}; if (curI >= 0 && ready) { F.set(target(curI)); F.render(performance.now()); } };
    F.onResize = rebuild; onTheme(rebuild);
})();

/* =================== P2. The plan builds itself, on Leadville =================== */
function LeadStory(cv, labs, N, onBeat) {
    const L = D2.lead;
    let F = null;
    try { F = DotField(cv, N, { size: innerWidth < 640 ? 2.3 : 2.7, lens: 55, jitter: 0.15, burst: 0 }); } catch (e) { console.error(e); }
    if (!F) return null;
    // ---- the course, the pace and the sun ----
    const nL = L.ele.length, DXL = L.distM / (nL - 1), lo = Math.min(...L.ele), hi = Math.max(...L.ele);
    const eleL = m => sampleArr(L.ele, m / L.distM);
    const gradeL = m => (eleL(m + 450) - eleL(m - 450)) / 900;
    const cumT = new Float64Array(nL);
    for (let i = 1; i < nL; i++) {
        const g = (L.ele[i] - L.ele[i - 1]) / DXL;
        const f = g >= 0 ? 1 + g * 4.5 : (g > -0.12 ? 1 + g * 1.5 : 0.82 + (-g - 0.12) * 2);
        cumT[i] = cumT[i - 1] + f * (1 + 0.8 * i / (nL - 1)) * DXL;
    }
    const PLAN_H = 25, TOT = PLAN_H * 3600, sc = TOT / cumT[nL - 1];
    for (let i = 0; i < nL; i++) cumT[i] *= sc;
    const tL = m => { const x = clamp(m / DXL, 0, nL - 1), i = Math.min(nL - 2, Math.floor(x)); return cumT[i] + (cumT[i + 1] - cumT[i]) * (x - i); };
    const [dPart, tPart] = L.start.split('T'), [Y, Mo, Da] = dPart.split('-').map(Number), [hh, mn] = tPart.split(':').map(Number);
    const UTC_OFF = 6;                                          // Colorado is on MDT (UTC-6) in August
    const START = Date.UTC(Y, Mo - 1, Da, hh + UTC_OFF, mn);
    const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    function clockL(t) {
        const d = new Date(START + t * 1000 - UTC_OFF * 3600000);
        let h = d.getUTCHours(); const m = d.getUTCMinutes(), ap = h >= 12 ? 'PM' : 'AM';
        const h12 = h % 12 || 12;
        return { day: DAYS[d.getUTCDay()], text: `${h12}:${String(m).padStart(2, '0')} ${ap}`, short: `${h12} ${ap}`, h };
    }
    function sunAlt(ms) {                                       // low-precision solar position, good to a fraction of a degree
        const r = Math.PI / 180, dd = (ms - Date.UTC(2000, 0, 1, 12)) / 86400000;
        const g = (357.529 + 0.98560028 * dd) * r, q = 280.459 + 0.98564736 * dd;
        const lam = (q + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * r, eps = (23.439 - 0.00000036 * dd) * r;
        const ra = Math.atan2(Math.cos(eps) * Math.sin(lam), Math.cos(lam)), dec = Math.asin(Math.sin(eps) * Math.sin(lam));
        const gmst = ((18.697374558 + 24.06570982441908 * dd) % 24 + 24) % 24;
        const ha = (gmst * 15 + L.lon) * r - ra;
        return Math.asin(Math.sin(L.lat * r) * Math.sin(dec) + Math.cos(L.lat * r) * Math.cos(dec) * Math.cos(ha)) / r;
    }
    const stops = [0, ...L.aids.map(a => a.m), L.distM];
    const stopName = k => k >= stops.length - 1 ? 'Finish' : L.aids[k - 1].n;
    const dS = new Float32Array(N), tS = new Float32Array(N), eS = new Float32Array(N), gS = new Float32Array(N), aS = new Float32Array(N), legS = new Int16Array(N);
    for (let i = 0; i < N; i++) {
        const m = (i + 0.5) / N * L.distM; dS[i] = m; tS[i] = tL(m); eS[i] = eleL(m); gS[i] = gradeL(m); aS[i] = sunAlt(START + tS[i] * 1000);
        let k = 0; while (k < stops.length - 2 && stops[k + 1] <= m) k++; legS[i] = k;
    }
    // ---- numbers the captions quote ----
    const half = Math.floor(nL / 2);
    const iPk1 = L.ele.indexOf(Math.max(...L.ele.slice(0, half))), iPk2 = half + L.ele.slice(half).indexOf(Math.max(...L.ele.slice(half)));
    const mPk1 = iPk1 * DXL, mPk2 = iPk2 * DXL;
    const aid = n => L.aids.find(a => a.n === n);
    const twinOut = aid('Twin Lakes Village').m, winfield = aid('Winfield').m;
    const dur = s => { const h = Math.floor(s / 3600), m = Math.round((s % 3600) / 60); return h ? `${h} h ${String(m).padStart(2, '0')} min` : `${m} min`; };
    const upT = tL(mPk1) - tL(twinOut), downT = tL(winfield) - tL(mPk1);
    const legT = stops.slice(1).map((b, k) => tL(b) - tL(stops[k])), legG = legT.map(s => s / 3600 * 75), totG = legG.reduce((s, g) => s + g, 0);
    const kMax = legG.indexOf(Math.max(...legG));
    const unit = Math.max(1, Math.ceil(totG / (N * 0.92)));
    const need = legG.map(g => Math.round(g / unit));
    const climbShare = Math.round(Array.from(gS).filter(g => g > 0.03).length / N * 100);
    const DARK = -6;                                            // civil twilight: below this the trail needs a light
    let iDawn = 0; while (iDawn < N && aS[iDawn] < DARK) iDawn++;
    let iDusk = N - 1; while (iDusk > 0 && aS[iDusk] < DARK) iDusk--;
    const sliceM = Math.round(L.distM / N);
    // ---- the six beats: every dot keeps its slice of trail ----
    const BEATS = [
        { chip: 'Course', stat: () => `${(L.distM / MI).toFixed(1)} mi · ${fmt(N)} dots · ${sliceM} m each`,
          text: () => `<b>Get a course.</b> Leadville loads from the catalog: out to Winfield and back over Hope Pass. Each dot is a ${sliceM} m slice of trail. The way out runs cyan on one side of the line, the way back blue on the other.` },
        { chip: 'Profile', stat: () => `Hope Pass ${fmt(hi * FT)} ft · low ${fmt(lo * FT)} ft`,
          text: () => `<b>The profile.</b> The same dots leave the map for distance and elevation. Hope Pass, ${fmt(hi * FT)} ft, is the peak you climb twice.` },
        { chip: 'Grade', stat: () => `${climbShare}% of the course climbs more than 3%`,
          text: () => `<b>Grade.</b> Climbs turn orange and descents blue, the way the Run Planner shades them.` },
        { chip: 'Time', stat: () => `Finish ${clockL(TOT).day} ${clockL(TOT).text} on a ${PLAN_H}-hour plan`,
          text: () => `<b>Pacing.</b> Distance becomes time on a ${PLAN_H}-hour plan. Climbs stretch and descents shrink: the climb from Twin Lakes to Hope Pass takes ${dur(upT)}, the descent to Winfield ${dur(downT)}.` },
        { chip: 'Fuel', stat: () => `${fmt(totG)} g of carbs · one dot = ${unit} g`,
          text: () => `<b>Fuel.</b> Carbs for every leg at 75 g an hour, ${unit === 1 ? 'one dot per gram' : `one dot per ${unit} g`}. ` + (kMax === need.length - 1
              ? `The last leg, ${((stops[stops.length - 1] - stops[stops.length - 2]) / MI).toFixed(1)} miles from ${L.aids[L.aids.length - 1].n} to the finish, needs the most: ${fmt(legG[kMax])} g, because it's long and it comes when the plan is slowest.`
              : `The leg into ${stopName(kMax + 1)} needs the most: ${fmt(legG[kMax])} g.`) },
        { chip: 'Night', stat: () => `Dark before ${clockL(tS[iDawn]).text} and after ${clockL(tS[iDusk]).text}`,
          text: () => `<b>Night.</b> Back on the map, lit by the clock and the sun's real position over Leadville on ${dPart.split('-').reverse().slice(0, 2).map(Number).join(' ').replace(/^(\d+) (\d+)$/, (m, a, b) => `${a} ${['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][+b]}`)}. Miles 0 to ${(dS[iDawn] / MI).toFixed(0)} and ${(dS[iDusk] / MI).toFixed(0)} to the finish run in the dark. That's where the headlamp goes.` },
    ];
    let G = null, targets = [];
    function geom() {
        return {
            P: { x: F.w * 0.07, y: F.h * 0.16, w: F.w * 0.86, h: F.h * 0.6 },
            M: { x: F.w * 0.1, y: F.h * 0.07, w: F.w * 0.8, h: F.h * 0.84 },
        };
    }
    function buildAll() {
        G = geom();
        const P = G.P, rt = routeTable(L.route), proj = projector(L.route, G.M);
        const course = tokRGB('--course'), accent = tokRGB('--accent'), ink = tokRGB('--ink'), inkB = tokRGB('--ink-bright'), bg = tokRGB('--bg-1');
        const fuel = tokRGB('--fuel'), gold = tokRGB('--gold'), gear = tokRGB('--gear'), gcol = gradeColour();
        const mk = () => ({ pos: new Float32Array(N * 2), col: new Float32Array(N * 3), size: new Float32Array(N).fill(1) });
        const setC = (t, i, c) => { t.col[i * 3] = c[0]; t.col[i * 3 + 1] = c[1]; t.col[i * 3 + 2] = c[2]; };
        const yOf = e => P.y + P.h - (e - lo) / (hi - lo) * P.h;
        const jit = () => (Math.random() - 0.5) * 1.6;
        const map = mk(), prof = mk(), grade = mk(), time = mk(), fuelT = mk(), night = mk();
        G.mapXY = new Float32Array(N * 2);
        for (let i = 0; i < N; i++) {
            const f = dS[i] / L.distM, p = proj(rt.at(f)), a = proj(rt.at(Math.max(0, f - 0.003))), b = proj(rt.at(Math.min(1, f + 0.003)));
            const dx = b[0] - a[0], dy = b[1] - a[1], len = Math.hypot(dx, dy) || 1, off = 3.4;   // keep to your side of the trail
            const x = p[0] - dy / len * off + jit() * 0.5, y = p[1] + dx / len * off + jit() * 0.5;
            G.mapXY[i * 2] = x; G.mapXY[i * 2 + 1] = y;
            map.pos[i * 2] = x; map.pos[i * 2 + 1] = y; setC(map, i, dS[i] < L.distM / 2 ? course : accent);
            const px = P.x + f * P.w, py = yOf(eS[i]) + jit();
            prof.pos[i * 2] = px; prof.pos[i * 2 + 1] = py; setC(prof, i, mixRGB(course, inkB, (eS[i] - lo) / (hi - lo)));
            grade.pos[i * 2] = px; grade.pos[i * 2 + 1] = py; setC(grade, i, gcol(gS[i]));
            time.pos[i * 2] = P.x + tS[i] / TOT * P.w; time.pos[i * 2 + 1] = py; setC(time, i, gcol(gS[i]));
            night.pos[i * 2] = x; night.pos[i * 2 + 1] = y;
            const al = aS[i];
            if (al < DARK) { setC(night, i, gold); night.size[i] = 1.45; }
            else if (al < -0.833) { setC(night, i, gear); night.size[i] = 1.15; }
            else { setC(night, i, mixRGB(bg, ink, 0.34)); night.size[i] = 0.75; }
        }
        // fuel: one column per leg, one dot per `unit` grams, filled in course order
        const legs = need.length, colW = P.w / legs, cpc = 5, rowsMax = Math.ceil(Math.max(...need) / cpc);
        const sp = Math.min(colW * 0.74 / cpc, (P.h + F.h * 0.08) / rowsMax), base = P.y + P.h + F.h * 0.06;
        G.fuel = { colW, sp, base, rowsMax, cpc };
        let idx = 0;
        for (let k = 0; k < legs; k++) {
            const x0 = P.x + k * colW + (colW - cpc * sp) / 2, tint = k % 2 ? mixRGB(fuel, inkB, 0.2) : fuel;
            for (let j = 0; j < need[k] && idx < N; j++, idx++) {
                fuelT.pos[idx * 2] = x0 + (j % cpc + 0.5) * sp; fuelT.pos[idx * 2 + 1] = base - (Math.floor(j / cpc) + 0.5) * sp;
                setC(fuelT, idx, tint);
            }
        }
        for (; idx < N; idx++) {                                     // the dots this plan doesn't need rest out of sight
            fuelT.pos[idx * 2] = time.pos[idx * 2]; fuelT.pos[idx * 2 + 1] = base; setC(fuelT, idx, fuel); fuelT.size[idx] = 0;
        }
        targets = [map, prof, grade, time, fuelT, night];
    }
    // ---- labels that belong to each beat ----
    function labelsFor(k) {
        const P = G.P, out = [], f2x = m => P.x + m / L.distM * P.w, t2x = s => P.x + s / TOT * P.w, yOf = e => P.y + P.h - (e - lo) / (hi - lo) * P.h;
        const narrow = F.w < 560;                                   // phone widths: fewer, shorter labels so none collide
        const mapAt = m => { const i = clamp(Math.round(m / L.distM * N - 0.5), 0, N - 1); return [G.mapXY[i * 2], G.mapXY[i * 2 + 1]]; };
        if (k === 0 || k === 5) {
            const s = mapAt(0), t = mapAt(twinOut), p = mapAt(mPk1), w = mapAt(winfield);
            out.push({ t: narrow ? 'Leadville' : 'Leadville · start and finish', x: s[0] + 12, y: s[1], c: 'left' });
            out.push({ t: 'Twin Lakes', x: t[0] + 12, y: t[1], c: 'left' });
            out.push({ t: `Hope Pass · ${fmt(hi * FT)} ft`, x: p[0] + 12, y: p[1], c: 'left peak' });
            out.push({ t: narrow ? 'Winfield' : 'Winfield · turn around', x: w[0] - 12, y: w[1], c: 'right' });
            if (k === 5) out.push({ t: '<i class="sw gold"></i>Headlamp on <i class="sw gear"></i>Twilight <i class="sw day"></i>Daylight', x: F.w - 16, y: 26, c: 'right legend' });
        }
        if (k === 1 || k === 2) {
            [0, 25, 50, 75, L.distM / MI].forEach((mi, j) => out.push({ t: j === 4 ? `${mi.toFixed(1)} mi` : `${mi} mi`, x: f2x(Math.min(L.distM, mi * MI)), y: P.y + P.h + 10, c: 'axis' }));
            if (f2x(mPk2) - f2x(mPk1) < 150) out.push({ t: 'Hope Pass, out and back', x: (f2x(mPk1) + f2x(mPk2)) / 2, y: Math.min(yOf(L.ele[iPk1]), yOf(L.ele[iPk2])) - 10, c: 'peak' });
            else {
                out.push({ t: 'Hope Pass, out', x: f2x(mPk1), y: yOf(L.ele[iPk1]) - 10, c: 'peak' });
                out.push({ t: 'Hope Pass, back', x: f2x(mPk2), y: yOf(L.ele[iPk2]) - 10, c: 'peak' });
            }
            out.push({ t: 'Winfield', x: f2x(winfield), y: yOf(eleL(winfield)) + 22, c: 'axis' });
        }
        if (k === 3) {
            for (let s = 0; s <= TOT + 1; s += (narrow ? 8 : 4) * 3600) out.push({ t: s === 0 ? (narrow ? '4 AM' : 'Start 4 AM') : clockL(s).short, x: t2x(s), y: P.y + P.h + 10, c: 'axis' });
            out.push({ t: narrow ? `Up ${dur(upT)}` : `Up from Twin Lakes: ${dur(upT)}`, x: t2x(tL(mPk1)) - 10, y: yOf(L.ele[iPk1]) + 4, c: 'right up' });
            out.push({ t: narrow ? `Down ${dur(downT)}` : `Down to Winfield: ${dur(downT)}`, x: t2x(tL(winfield)) + 10, y: yOf(eleL(winfield)) - 4, c: 'left down' });
        }
        if (k === 4) {
            const fu = G.fuel, wide = F.w >= 760, placed = [];
            const order = need.map((_, j) => j).sort((a, b) => legG[b] - legG[a]);     // biggest legs claim a label first
            order.forEach(j => { const x = P.x + (j + 0.5) * fu.colW; if (placed.every(px => Math.abs(px - x) >= 40)) placed.push(x); });
            need.forEach((n, j) => {
                const x = P.x + (j + 0.5) * fu.colW, top = fu.base - Math.ceil(n / fu.cpc) * fu.sp;
                if (placed.includes(x)) out.push({ t: `${fmt(legG[j])} g`, x, y: top - 4, c: 'g' });
                if (wide) out.push({ t: stopName(j + 1).replace(' Village', '').replace('Turquoise Lake Dam', 'Dam').replace('Carter Summit Mini Aid', 'Carter').replace('Outward Bound', 'Outward Bd'), x, y: fu.base + 6, c: 'col' });
            });
        }
        const est = t => t.replace(/<[^>]+>/g, '').length * 7 + 4;     // mono label width, near enough to keep labels on the canvas
        out.forEach(l => {
            if (/\blegend\b/.test(l.c)) return;
            if (/\bleft\b/.test(l.c) && l.x + est(l.t) > F.w - 6) { l.c = l.c.replace('left', 'right'); l.x -= 24; }
            else if (/\bright\b/.test(l.c) && l.x - est(l.t) < 6) { l.c = l.c.replace('right', 'left'); l.x += 24; }
        });
        return out;
    }
    let shownLabels = -1;
    function paintLabels(k) {
        if (k === shownLabels) return; shownLabels = k;
        labs.style.opacity = '0';
        setTimeout(() => {
            labs.innerHTML = labelsFor(k).map(l => `<span class="lab ${l.c}" style="left:${l.x.toFixed(1)}px;top:${l.y.toFixed(1)}px">${l.t}</span>`).join('');
            labs.style.opacity = '1';
        }, calm ? 0 : 160);
    }
    let pairK = -1;
    const api = { F, BEATS, N, pos: 0 };
    api.showAt = (v, now) => {                      // v in [0, 5], scrubbed by a slider or by scroll
        v = clamp(v, 0, 5); api.pos = v;
        const k = Math.min(4, Math.floor(v)), f = v - k;
        if (k !== pairK) { F.pair(targets[k], targets[k + 1], { spread: 0.4, swirl: k === 2 ? 10 : 28 }); pairK = k; }
        F.T = f; F.auto = null;
        const b = Math.round(v); paintLabels(b); if (onBeat) onBeat(b);
        F.render(now ?? performance.now());
    };
    api.move = (from, to, dur, now) => {            // a timed morph between any two beats
        F.pair(targets[from], targets[to], { spread: 0.4, swirl: from === 2 ? 10 : 28 }); pairK = -1;
        F.play(dur, now); api.pos = to; paintLabels(to); if (onBeat) onBeat(to);
    };
    api.rebuild = () => { buildAll(); pairK = -1; shownLabels = -1; api.showAt(Math.round(api.pos)); };
    buildAll();
    F.onResize = api.rebuild; onTheme(api.rebuild);
    return api;
}

/* ---- the slider-and-autoplay version ---- */
(function leadDemo() {
    const stage = $('#demo-lead'); if (!stage) return;
    const desc = $('#lead-desc'), chipsWrap = $('#lead-chips'), scrub = $('#lead-scrub'), playBtn = $('#lead-play'), stat = $('#lead-stat');
    const chipEls = [];
    let S = null;
    const onBeat = k => {
        chipEls.forEach((c, j) => c.classList.toggle('on', j === k));
        if (S) { setHTML(desc, S.BEATS[k].text()); setText(stat, S.BEATS[k].stat()); }
    };
    S = LeadStory($('#lead-canvas'), $('#lead-labels'), dotBudget(2400, 2000, 1400), onBeat);
    if (!S) { $('.no-webgl', stage).hidden = false; return; }
    S.BEATS.forEach((b, k) => {
        const el = document.createElement('button'); el.type = 'button'; el.className = 'beat'; el.textContent = b.chip;
        el.addEventListener('click', () => { autoOn = false; paintPlay(); jumpTo(k); });
        chipsWrap.appendChild(el); chipEls.push(el);
    });
    let autoOn = true, phase = null, d = { running: false };
    const MOVE = 2300, HOLD = 2700;
    function jumpTo(k) {
        const from = Math.round(S.pos);
        if (calm || !d.running || k === from) { S.showAt(k); scrub.value = String(k * 100); return; }
        S.move(from, k, MOVE, performance.now()); phase = { from, to: k, t0: performance.now(), hold: false }; scrub.value = String(k * 100);
    }
    function paintPlay() {
        playBtn.setAttribute('aria-pressed', String(autoOn));
        playBtn.querySelector('span').textContent = autoOn ? 'Pause' : 'Play';
        playBtn.querySelector('svg').innerHTML = autoOn ? '<path d="M8 5v14M16 5v14"/>' : '<path d="M7 5v14l12-7z"/>';
    }
    playBtn.addEventListener('click', () => { autoOn = !autoOn; paintPlay(); if (autoOn) phase = { from: Math.round(S.pos), to: Math.round(S.pos), t0: performance.now() - MOVE, hold: true }; });
    scrub.addEventListener('input', () => { autoOn = false; paintPlay(); phase = null; S.showAt(scrub.value / 100); });
    const loop = rafLoop((ms, now) => {
        if (autoOn) {
            if (!phase) phase = { from: Math.round(S.pos), to: Math.round(S.pos), t0: now - MOVE, hold: true };
            if (phase.hold && now - phase.t0 >= MOVE + (phase.to === 5 ? HOLD + 1200 : HOLD)) {
                const from = phase.to, to = (from + 1) % 6;
                S.move(from, to, MOVE, now); phase = { from, to, t0: now, hold: false }; scrub.value = String(to * 100);
            } else if (!phase.hold && now - phase.t0 >= MOVE) phase.hold = true;
        } else if (phase && !phase.hold && now - phase.t0 >= MOVE) phase.hold = true;
        S.F.frame(now);
    });
    S.showAt(0);
    d = register(stage, { start() { loop.start(); }, stop() { loop.stop(); }, rest() { S.showAt(5); scrub.value = '500'; } });
})();

/* =================== P3. Living topo: a flow field made of real terrain =================== */
(function topo() {
    const stage = $('#demo-topo'); if (!stage) return;
    const T = D2.dem, cv = $('#topo-canvas'), ov = $('#topo-over'), labsEl = $('#topo-labels');
    const GW = T.w, GH = T.h, bin = atob(T.b64), H = new Float32Array(GW * GH);
    for (let i = 0; i < GW * GH; i++) H[i] = (bin.charCodeAt(2 * i) | (bin.charCodeAt(2 * i + 1) << 8)) / 65535;
    const TX = new Float32Array(GW * GH), TY = new Float32Array(GW * GH), MAG = new Float32Array(GW * GH);
    for (let y = 0; y < GH; y++) for (let x = 0; x < GW; x++) {
        const k = y * GW + x;
        const gx = (H[y * GW + Math.min(GW - 1, x + 1)] - H[y * GW + Math.max(0, x - 1)]) / 2;
        const gy = (H[Math.min(GH - 1, y + 1) * GW + x] - H[Math.max(0, y - 1) * GW + x]) / 2;
        const m = Math.hypot(gx, gy); MAG[k] = m;
        if (m > 1e-9) { TX[k] = -gy / m; TY[k] = gx / m; }       // along the contour, never across it
    }
    const FLAT = 0.0009;                                        // under about 2 % grade there is no contour to follow
    const ctx = cv.getContext('2d'), octx = ov.getContext('2d');
    let Wc = 1, Hc = 1, dpr = 1, s = 1, ox = 0, oy = 0, P = 0, px, py, age, life;
    let bands = [], fade = '', lampHue = [1, 0.85, 0.6], courseC = [0, 0.7, 0.8], dark = true, lightOn = false, lx = 0, ly = 0;
    const route = T.route.filter(p => p[1] >= 0 && p[1] <= GW && p[2] >= 0 && p[2] <= GH);
    const g2c = (gx, gy) => [ox + gx * s, oy + gy * s];
    function colours() {
        dark = isDark();
        const lo_ = tokRGB('--course'), mid = tokRGB('--accent'), top = tokRGB('--ink-bright'), bg = tokRGB('--bg-1');
        bands = Array.from({ length: 7 }, (_, b) => { const u = b / 6; const c = u < 0.5 ? mixRGB(lo_, mid, u * 2) : mixRGB(mid, top, (u - 0.5) * 2); return rgbCss(c, dark ? 0.55 : 0.7); });
        fade = rgbCss(bg, dark ? 0.075 : 0.09);
        lampHue = dark ? [1, 0.86, 0.6] : tokRGB('--fuel'); courseC = tokRGB('--course');
        ctx.fillStyle = rgbCss(bg, 1); ctx.fillRect(0, 0, Wc, Hc);
    }
    function resize() {
        const r = stage.getBoundingClientRect(); dpr = Math.min(2, devicePixelRatio || 1);
        Wc = Math.max(1, r.width); Hc = Math.max(1, cv.getBoundingClientRect().height || r.height);
        [cv, ov].forEach(c => { c.width = Math.round(Wc * dpr); c.height = Math.round(Hc * dpr); });
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0); octx.setTransform(dpr, 0, 0, dpr, 0, 0);
        s = Math.max(Wc / GW, Hc / GH); ox = (Wc - GW * s) / 2; oy = (Hc - GH * s) / 2;
        P = Math.round(clamp(Wc * Hc / 190, 700, 2600));
        px = new Float32Array(P); py = new Float32Array(P); age = new Uint16Array(P); life = new Uint16Array(P);
        for (let i = 0; i < P; i++) spawn(i, true);
        colours(); placeLabels(); drawOverlay(performance.now());
    }
    function spawn(i, anyAge) {
        for (let k = 0; k < 8; k++) {
            const x = 1 + Math.random() * (GW - 2), y = 1 + Math.random() * (GH - 2);
            if (MAG[(y | 0) * GW + (x | 0)] > FLAT) { px[i] = x; py[i] = y; life[i] = 50 + (Math.random() * 190 | 0); age[i] = anyAge ? (Math.random() * life[i]) | 0 : 0; return; }
        }
        px[i] = Math.random() * GW; py[i] = Math.random() * GH; life[i] = 20; age[i] = 0;
    }
    const SPEED = 0.42;
    function step() {
        ctx.fillStyle = fade; ctx.fillRect(0, 0, Wc, Hc);
        const paths = bands.map(() => new Path2D());
        for (let i = 0; i < P; i++) {
            const x = px[i], y = py[i], k = (y | 0) * GW + (x | 0);
            if (x < 1 || y < 1 || x >= GW - 1 || y >= GH - 1 || MAG[k] < FLAT || ++age[i] > life[i]) { spawn(i, false); continue; }
            const nx = x + TX[k] * SPEED + (Math.random() - 0.5) * 0.06, ny = y + TY[k] * SPEED + (Math.random() - 0.5) * 0.06;
            const b = Math.min(6, (H[k] * 7) | 0), a = g2c(x, y), c = g2c(nx, ny);
            paths[b].moveTo(a[0], a[1]); paths[b].lineTo(c[0], c[1]);
            px[i] = nx; py[i] = ny;
        }
        ctx.lineWidth = 1; ctx.lineCap = 'round';
        paths.forEach((p, b) => { ctx.strokeStyle = bands[b]; ctx.stroke(p); });
    }
    const LAMP_MS = 16000;
    function lampAt(now) {                                       // the headlamp runs the in-view stretch, out and back
        const u = (now % LAMP_MS) / LAMP_MS, n = route.length - 1, t = u * n, i = Math.min(n - 1, Math.floor(t)), f = t - i;
        return g2c(route[i][1] + (route[i + 1][1] - route[i][1]) * f, route[i][2] + (route[i + 1][2] - route[i][2]) * f);
    }
    function drawOverlay(now) {
        octx.clearRect(0, 0, Wc, Hc);
        if (route.length > 1) {
            octx.beginPath();
            route.forEach((p, i) => { const c = g2c(p[1], p[2]); if (i) octx.lineTo(c[0], c[1]); else octx.moveTo(c[0], c[1]); });
            octx.strokeStyle = rgbCss(courseC, dark ? 0.85 : 0.9); octx.lineWidth = 2; octx.lineJoin = 'round'; octx.stroke();
            const [x, y] = lampAt(now);
            const g = octx.createRadialGradient(x, y, 0, x, y, 30);
            g.addColorStop(0, rgbCss(lampHue, 0.95)); g.addColorStop(0.25, rgbCss(lampHue, 0.45)); g.addColorStop(1, rgbCss(lampHue, 0));
            octx.fillStyle = g; octx.beginPath(); octx.arc(x, y, 30, 0, Math.PI * 2); octx.fill();
            octx.fillStyle = dark ? '#fff8e6' : rgbCss(lampHue, 1); octx.beginPath(); octx.arc(x, y, 3.2, 0, Math.PI * 2); octx.fill();
        }
        if (lightOn && dark) {
            const g = octx.createRadialGradient(lx, ly, 0, lx, ly, 150);
            g.addColorStop(0, 'rgba(255,248,230,0.16)'); g.addColorStop(1, 'rgba(255,248,230,0)');
            octx.globalCompositeOperation = 'lighter'; octx.fillStyle = g; octx.fillRect(lx - 150, ly - 150, 300, 300); octx.globalCompositeOperation = 'source-over';
        }
    }
    function placeLabels() {
        labsEl.innerHTML = T.labels.map(l => { const [x, y] = g2c(l.x, l.y); return `<span class="topo-lab" style="left:${x.toFixed(1)}px;top:${y.toFixed(1)}px">${l.n}${l.n === 'Hope Pass' ? ` · ${fmt(l.ele * FT)} ft` : ''}</span>`; }).join('');
    }
    stage.addEventListener('pointermove', e => { const r = stage.getBoundingClientRect(); lx = e.clientX - r.left; ly = e.clientY - r.top; lightOn = true; });
    stage.addEventListener('pointerleave', () => { lightOn = false; });
    const loop = rafLoop((ms, now) => { step(); drawOverlay(now); });
    new ResizeObserver(() => resize()).observe(stage);
    onTheme(() => { colours(); for (let i = 0; i < 90; i++) step(); drawOverlay(performance.now()); });
    resize(); for (let i = 0; i < 140; i++) step(); drawOverlay(performance.now());
    register(stage, {
        start() { loop.start(); }, stop() { loop.stop(); },
        rest() { colours(); for (let i = 0; i < 200; i++) step(); drawOverlay(LAMP_MS * 0.3); },
    });
})();

/* =================== P4. Course signatures, five ways =================== */
(function signatures() {
    const stage = $('#demo-sigs'); if (!stage) return;
    const grid = $('#sig5-grid'), panel = $('#sig5-ridge'), tabs = $$('#sig5-tabs button'), replayBtn = $('#sig5-replay'), note = $('#sig5-note');
    const byId = Object.fromEntries(D2.ridge.map(c => [c.id, c]));
    const cards = [233, 228, 473, 125, 438, 66, 142, 158, 495, 319].map(id => byId[id]).filter(Boolean);
    const classOf = mi => mi < 31 ? ['Under 50K', '--course'] : mi < 50 ? ['50K–50M', '--aid'] : mi < 62.2 ? ['50M–100K', '--gear'] : mi < 99 ? ['100K–100M', '--gold'] : mi < 150 ? ['100M', '--climb'] : ['200M+', '--weather'];
    const nameOf = c => shortName(c.name).replace(' Endurance Run 100 Miler', '').replace(' 100 Miler Solo', ' 100').replace(' Trail 100 Run', ' 100');
    const NOTES = {
        line: 'Line: the quietest. The profile draws itself as the card scrolls in, and hovering traces it.',
        dots: 'Dot matrix: the profile on a grid of lamps, lit column by column like a stadium board.',
        sand: 'Sand: grains fall and settle into the course. The most playful, and the most work per frame.',
        seal: 'Seal: the profile wrapped into a race badge. Shareable, and it would print on the pace band.',
        ridge: 'Ridgeline: all 39 courses stacked like the Unknown Pleasures cover, flattest at the back. Hover a line to name it.',
    };
    let style = 'line', sandJob = 0;
    const norm = c => { const e = c.ele120, lo = Math.min(...e), hi = Math.max(...e); return e.map(v => (v - lo) / ((hi - lo) || 1)); };
    function plotLine(plot, c, i) {
        const v = norm(c), pts = v.map((y, j) => [(j / (v.length - 1) * 200).toFixed(1), (58 - y * 50).toFixed(1)]);
        const d = pts.map((p, j) => (j ? 'L' : 'M') + p[0] + ' ' + p[1]).join('');
        plot.innerHTML = `<svg viewBox="0 -4 200 66" aria-hidden="true"><path class="sig-area" d="${d}L200 62L0 62Z"/><path class="sig-line" pathLength="1" d="${d}"/></svg><span class="sig-dot"></span><span class="sig-read"></span>`;
        const dot = $('.sig-dot', plot), read = $('.sig-read', plot), mi = c.distM / MI;
        plot.addEventListener('pointermove', e => {
            const r = plot.getBoundingClientRect(), f = clamp((e.clientX - r.left) / r.width), j = Math.round(f * (v.length - 1)), yv = (58 - v[j] * 50 + 4) / 66;
            dot.style.left = (f * 100) + '%'; dot.style.top = (yv * 100) + '%';
            read.style.left = clamp(f * 100, 18, 82) + '%'; read.style.top = (yv * 100) + '%';
            read.textContent = `mi ${(f * mi).toFixed(1)} · ${fmt(c.ele120[j] * FT)} ft`; plot.parentElement.classList.add('tracing');
        });
        plot.addEventListener('pointerleave', () => plot.parentElement.classList.remove('tracing'));
    }
    function plotDots(plot, c, i) {
        const v = norm(c), cols = 30, rows = 9, cw = 200 / cols, rh = 64 / rows, r = Math.min(cw, rh) * 0.36;
        let h = '<svg viewBox="0 0 200 64" aria-hidden="true">';
        for (let x = 0; x < cols; x++) {
            const lit = Math.max(1, Math.round(sampleArr(v, x / (cols - 1)) * rows));
            for (let y = 0; y < rows; y++) h += `<circle class="dm${y < lit ? ' on' : ''}" cx="${((x + 0.5) * cw).toFixed(2)}" cy="${(64 - (y + 0.5) * rh).toFixed(2)}" r="${r.toFixed(2)}" style="--d:${x * 26 + y * 8 + i * 40}ms"/>`;
        }
        plot.innerHTML = h + '</svg>';
    }
    function plotSeal(plot, c, i) {
        const v = norm(c), n = v.length, R0 = 52, A = 26, id = 'sl' + c.id, mi = (c.distM / MI).toFixed(1);
        const pts = v.map((y, j) => { const a = -Math.PI / 2 + j / n * Math.PI * 2, r = R0 + y * A; return [(100 + Math.cos(a) * r).toFixed(1), (100 + Math.sin(a) * r).toFixed(1)]; });
        const d = pts.map((p, j) => (j ? 'L' : 'M') + p[0] + ' ' + p[1]).join('') + 'Z';
        const ring = `${nameOf(c).toUpperCase()} · ${mi} MI · ${fmt(c.gainM * FT)} FT ·`;
        plot.innerHTML = `<svg viewBox="0 0 200 200" aria-hidden="true"><defs><path id="${id}" d="M100,100 m-88,0 a88,88 0 1,1 176,0 a88,88 0 1,1 -176,0"/></defs>
            <circle cx="100" cy="100" r="${R0 - 2}" class="seal-in"/><path class="seal-fill" d="${d}"/><path class="seal-line" pathLength="1" d="${d}"/>
            <text class="seal-ring"><textPath href="#${id}" textLength="545" lengthAdjust="spacing">${ring}</textPath></text>
            <text class="seal-num" x="100" y="104" text-anchor="middle">${mi}</text><text class="seal-unit" x="100" y="122" text-anchor="middle">MILES</text></svg>`;
    }
    function plotSand(plot, c, i) {
        plot.innerHTML = '<canvas class="sand" aria-hidden="true"></canvas>';
        const cvs = $('canvas', plot), rr = plot.getBoundingClientRect(), dp = Math.min(2, devicePixelRatio || 1);
        const w = Math.max(40, rr.width), h = w * 64 / 200; cvs.width = Math.round(w * dp); cvs.height = Math.round(h * dp); cvs.style.height = h + 'px';
        const v = norm(c), acc = tokRGB(getComputedStyle(plot.parentElement).getPropertyValue('--acc').replace(/var\((--[a-z-]+)\)/, '$1').trim() || '--course');
        const shades = [rgbCss(acc, 0.95), rgbCss(mixRGB(acc, tokRGB('--ink-bright'), 0.3), 0.9), rgbCss(mixRGB(acc, tokRGB('--bg-1'), 0.35), 0.9)];
        const G = []; const top = x => h - 4 - sampleArr(v, x / w) * (h - 10);
        for (let k = 0; k < 560; k++) {
            const x = Math.random() * w, t = top(x), ty = t + Math.pow(Math.random(), 2.2) * (h - t);
            G.push({ x, ty, y0: -4 - Math.random() * h * 0.7, delay: x / w * 650 + Math.random() * 260 + i * 55, dur: 650 + Math.random() * 350, s: k % 3 });
        }
        return { cvs, ctx: cvs.getContext('2d'), G, shades, w, h, dp };
    }
    function runSand(jobs) {
        const id = ++sandJob, t0 = performance.now();
        const frame = now => {
            if (id !== sandJob) return;
            let busy = false;
            jobs.forEach(j => {
                j.ctx.setTransform(j.dp, 0, 0, j.dp, 0, 0); j.ctx.clearRect(0, 0, j.w, j.h);
                j.G.forEach(g => {
                    const u = clamp((now - t0 - g.delay) / g.dur); if (u < 1) busy = true;
                    j.ctx.fillStyle = j.shades[g.s]; j.ctx.fillRect(g.x, g.y0 + (g.ty - g.y0) * (calm ? 1 : bounce(u)), 1.9, 1.9);
                });
            });
            if (busy && !calm) requestAnimationFrame(frame);
        };
        requestAnimationFrame(frame);
    }
    function ridgeline() {
        const rows = [...D2.ridge].sort((a, b) => a.gainM / a.distM - b.gainM / b.distM);
        const n = rows.length, VW = 1000, gap = 13, topPad = 78, X0 = 60, X1 = 940, VH = topPad + n * gap + 18;
        const dens = rows.map(r => r.gainM / r.distM), dmax = Math.max(...dens);
        let h = `<svg viewBox="0 0 ${VW} ${VH}" role="img" aria-label="Ridgeline plot of 39 course profiles, flattest at the back">`;
        rows.forEach((r, k) => {
            const base = topPad + k * gap, amp = 8 + 46 * Math.pow(dens[k] / dmax, 0.8), e = r.ele, lo = Math.min(...e), hi = Math.max(...e);
            const pts = e.map((v, j) => [(X0 + j / (e.length - 1) * (X1 - X0)).toFixed(1), (base - (v - lo) / ((hi - lo) || 1) * amp).toFixed(1)]);
            const d = pts.map((p, j) => (j ? 'L' : 'M') + p[0] + ' ' + p[1]).join('');
            h += `<g class="rl" data-k="${k}" style="--d:${k * 32}ms"><path class="f" d="${d}L${X1} ${base}L${X0} ${base}Z"/><path class="l" pathLength="1" d="${d}"/></g>`;
        });
        h += '</svg><div class="rl-tip" hidden></div>';
        panel.innerHTML = h;
        const svg = $('svg', panel), tip = $('.rl-tip', panel), gs = $$('.rl', panel);
        svg.addEventListener('pointermove', e => {
            const r = svg.getBoundingClientRect(), y = (e.clientY - r.top) / r.height * VH;
            const k = clamp(Math.round((y - topPad + 18) / gap), 0, n - 1), row = rows[k];
            gs.forEach((g, j) => g.classList.toggle('on', j === k));
            tip.hidden = false; tip.style.left = clamp((e.clientX - r.left) / r.width * 100, 12, 88) + '%'; tip.style.top = ((topPad + k * gap - 70) / VH * 100) + '%';
            tip.innerHTML = `<b>${nameOf(row)}</b><span>${(row.distM / MI).toFixed(1)} mi · ${fmt(row.gainM * FT)} ft · ${fmt(row.gainM * FT / (row.distM / MI))} ft/mi</span>`;
        });
        svg.addEventListener('pointerleave', () => { tip.hidden = true; gs.forEach(g => g.classList.remove('on')); });
    }
    function render() {
        tabs.forEach(t => t.setAttribute('aria-selected', String(t.dataset.style === style)));
        setText(note, NOTES[style]);
        sandJob++;
        if (style === 'ridge') { grid.hidden = true; panel.hidden = false; ridgeline(); animate(); return; }
        grid.hidden = false; panel.hidden = true;
        grid.className = 'sigs sig5-' + style;
        grid.innerHTML = '';
        const jobs = [];
        cards.forEach((c, i) => {
            const mi = c.distM / MI, [cls, tok] = classOf(mi);
            const a = document.createElement('a');
            a.className = 'sig'; a.href = 'https://trailgoat.run/course/' + (c.id === 233 ? 'western-states-100-2026' : '') ; a.target = '_blank'; a.rel = 'noopener';
            if (c.id !== 233) a.removeAttribute('href');
            a.style.setProperty('--acc', `var(${tok})`); a.style.setProperty('--i', i);
            a.innerHTML = `<div class="sig-plot"></div><p class="sig-name">${nameOf(c)}</p><p class="sig-meta"><span class="chip">${cls}</span>${mi.toFixed(1)} mi · ${fmt(c.gainM * FT)} ft</p>`;
            grid.appendChild(a);
            const plot = $('.sig-plot', a);
            if (style === 'line') plotLine(plot, c, i);
            else if (style === 'dots') plotDots(plot, c, i);
            else if (style === 'seal') plotSeal(plot, c, i);
            else if (style === 'sand') jobs.push(plotSand(plot, c, i));
        });
        if (jobs.length) runSand(jobs); else animate();
    }
    function animate() {
        const host = style === 'ridge' ? panel : grid;
        host.classList.add('primed'); void host.offsetWidth;
        if (!calm) host.classList.remove('primed'); else host.classList.remove('primed');
    }
    tabs.forEach(t => t.addEventListener('click', () => { style = t.dataset.style; render(); }));
    replayBtn.addEventListener('click', render);
    let played = false;
    register(stage, { start() { if (!played) { played = true; render(); } }, stop() {}, rest() {} });
    render();
    onTheme(() => { if (style === 'sand') render(); });
})();

/* =================== P5. Type that climbs =================== */
(function typeClimb() {
    const stage = $('#demo-type'); if (!stage) return;
    const svg = $('#type-svg'), btns = $$('#type-presets button'), cap = $('#type-cap');
    const VBW = 1200, VBH = 320, BASE = 272, TOP = 122, FS = 34;
    const PRE = {
        tag: { ele: D2.hard.ele, text: 'PLAN THE CLIMB · NAIL THE FUEL · SEND THE TRAIL · ', cap: `Ridge: Hardrock 100, ${fmt(D2.hard.gainM * FT)} ft of climbing` },
        lead: { ele: D2.lead.ele, text: `LEADVILLE 100 · HOPE PASS OUT · HOPE PASS BACK · ${fmt(D2.lead.gainM * FT)} FT UP · ${fmt(D2.lead.gainM * FT)} FT DOWN · `, cap: 'Ridge: Leadville 100, its own profile' },
    };
    let preset = 'tag', R = null, letters = [], s0 = 0, inkC = [1, 1, 1], fuelC = [1, 0.6, 0.3];
    const meas = document.createElement('canvas').getContext('2d');
    function ridge(ele) {
        const n = ele.length, w = 14, sm = ele.map((_, i) => { let s = 0, c = 0; for (let k = -w; k <= w; k++) { const j = i + k; if (j >= 0 && j < n) { s += ele[j]; c++; } } return s / c; });
        const lo = Math.min(...sm), hi = Math.max(...sm);
        const pts = sm.map((v, i) => [i / (n - 1) * VBW, BASE - (v - lo) / ((hi - lo) || 1) * (BASE - TOP)]);
        const cum = [0]; for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
        return { pts, cum, len: cum[cum.length - 1] };
    }
    function at(s) {
        const c = R.cum; let lo = 0, hi = c.length - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (c[m] <= s) lo = m; else hi = m; }
        const a = R.pts[lo], b = R.pts[hi], f = (s - c[lo]) / ((c[hi] - c[lo]) || 1);
        return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, Math.atan2(b[1] - a[1], b[0] - a[0]) * 180 / Math.PI];
    }
    function build() {
        const P = PRE[preset]; R = ridge(P.ele); cap.textContent = P.cap;
        inkC = tokRGB('--ink-bright'); fuelC = tokRGB('--fuel');
        const d = R.pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join('');
        meas.font = `900 ${FS}px "Red Hat Display", sans-serif`;          // widest weight, so heavy letters never collide
        const one = P.text.split('').map(ch => meas.measureText(ch).width + 2);
        const unitLen = one.reduce((s, v) => s + v, 0), reps = Math.ceil(R.len / unitLen) + 1;
        const chars = [], adv = [];
        for (let r = 0; r < reps; r++) P.text.split('').forEach((ch, i) => { chars.push(ch); adv.push(one[i]); });
        const cum = [0]; adv.forEach((a, i) => cum.push(cum[i] + a));
        svg.innerHTML = `<defs><linearGradient id="tyg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="var(--accent)" stop-opacity="0.22"/><stop offset="1" stop-color="var(--accent)" stop-opacity="0"/></linearGradient></defs>
            <path d="${d}L${VBW} ${VBH}L0 ${VBH}Z" fill="url(#tyg)"/><path d="${d}" fill="none" stroke="var(--edge)" stroke-width="1.5"/><g id="ty-letters"></g>`;
        const g = $('#ty-letters', svg);
        letters = chars.map((ch, i) => {
            const t = svgEl('text', { 'font-size': FS, 'text-anchor': 'middle' }, g); t.textContent = ch; return { el: t, off: cum[i] + adv[i] / 2, ch };
        });
        R.total = cum[cum.length - 1];
        place();
    }
    function place() {
        letters.forEach(L_ => {
            const s = ((L_.off - s0) % R.total + R.total) % R.total;
            if (s > R.len - 4 || L_.ch === ' ') { L_.el.style.display = 'none'; return; }
            const [x, y, a0] = at(s), ang = clamp(a0, -34, 34), climb = clamp((-ang - 2) / 30);
            L_.el.style.display = '';
            L_.el.setAttribute('transform', `translate(${x.toFixed(1)} ${(y - 6).toFixed(1)}) rotate(${ang.toFixed(1)})`);
            L_.el.style.fontWeight = String(Math.round(300 + 600 * climb));
            L_.el.style.fill = rgbCss(mixRGB(inkC, fuelC, clamp((-ang - 12) / 22)), 1);
        });
    }
    btns.forEach(b => b.addEventListener('click', () => { preset = b.dataset.p; btns.forEach(x => x.setAttribute('aria-pressed', String(x === b))); build(); }));
    let last = 0;
    const loop = rafLoop((ms, now) => { const dt = last ? Math.min(0.05, (now - last) / 1000) : 0; last = now; s0 -= 70 * dt; place(); });
    fontsReady.then(build);
    register(stage, { start() { last = 0; loop.start(); }, stop() { loop.stop(); }, rest() { if (R) { s0 = 0; place(); } } });
    onTheme(() => { if (R) { inkC = tokRGB('--ink-bright'); fuelC = tokRGB('--fuel'); place(); } });
})();
