/* =================== Toolbox: shared =================== */
const WSER_ROUTE = W.route;          // the page-level W is Western States; demos below reuse W as a canvas width
const paintCalmClass = () => document.documentElement.classList.toggle('is-calm', calm);
calmBtn.addEventListener('click', paintCalmClass); rmq.addEventListener('change', paintCalmClass); paintCalmClass();
calmBtn.addEventListener('click', () => { if (calm) demos.forEach(d => { if (!d.running && d.rest) d.rest(); }); });   // demos that never played rest too

/* =================== Toolbox T1. GPU particle simulation (WebGL2, ping-pong float textures) =================== */
/* Every particle's position and velocity live in a float texture. Each frame a
   fragment shader reads last frame's texture and writes the next: spring force
   toward the current shape, a curl-noise swirl, damping and the pointer. So the
   dots have momentum. They overshoot, swirl and settle instead of easing. */
(function gpuSim() {
    const stage = $('#demo-gpgpu'); if (!stage) return;
    const cv = $('#gp-canvas'), note = $('.no-webgl', stage), lab = $('#gp-label'), chips = $('#gp-chips'), scatterBtn = $('#gp-scatter');
    const fail = m => { note.textContent = m; note.hidden = false; };
    let gl = null;
    try { gl = cv.getContext('webgl2', { alpha: true, antialias: false, premultipliedAlpha: false }); } catch (e) { gl = null; }
    if (!gl) { fail('This browser has no WebGL2, which the GPU simulation needs.'); return; }
    let internal = null;
    if (gl.getExtension('EXT_color_buffer_float')) internal = gl.RGBA32F;
    else if (gl.getExtension('EXT_color_buffer_half_float')) internal = gl.RGBA16F;
    if (!internal) { fail("This GPU can't render to float textures, which the simulation needs."); return; }
    const SIDE = innerWidth >= 1000 ? 256 : innerWidth >= 640 ? 192 : 128, N = SIDE * SIDE;
    const compile = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
    const program = (vs, fs) => { const p = gl.createProgram(); gl.attachShader(p, compile(gl.VERTEX_SHADER, vs)); gl.attachShader(p, compile(gl.FRAGMENT_SHADER, fs)); gl.linkProgram(p); if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p)); return p; };
    const FULL_VS = `#version 300 es
in vec2 aP;
void main() { gl_Position = vec4(aP, 0.0, 1.0); }`;
    const SIM_FS = `#version 300 es
precision highp float; precision highp sampler2D;
uniform sampler2D uState; uniform sampler2D uTarget;
uniform float uTime; uniform float uDt; uniform float uSpring; uniform float uNoise; uniform float uDamp; uniform vec3 uMouse;
out vec4 outState;
vec2 curl(vec2 p, float t) {          // divergence-free: rotated gradients of three sine potentials
    vec2 k1 = vec2(0.0061, 0.0043), k2 = vec2(-0.0037, 0.0079), k3 = vec2(0.0113, -0.0052);
    vec2 c = vec2(k1.y, -k1.x) * cos(dot(k1, p) + t * 0.7);
    c += vec2(k2.y, -k2.x) * cos(dot(k2, p) - t * 0.5) * 1.3;
    c += vec2(k3.y, -k3.x) * cos(dot(k3, p) + t * 0.9) * 0.7;
    return c * 120.0;
}
void main() {
    ivec2 ij = ivec2(gl_FragCoord.xy);
    vec4 s = texelFetch(uState, ij, 0);
    vec2 p = s.xy, v = s.zw, t = texelFetch(uTarget, ij, 0).xy;
    vec2 acc = (t - p) * uSpring + curl(p, uTime) * uNoise;
    if (uMouse.z > 0.0) { vec2 d = p - uMouse.xy; float r = length(d) + 0.001; acc += d / r * uMouse.z * exp(-r / 80.0); }
    v = (v + acc * uDt) * pow(uDamp, uDt * 60.0);
    outState = vec4(p + v * uDt, v);
}`;
    const DRAW_VS = `#version 300 es
precision highp float; precision highp sampler2D;
uniform sampler2D uState; uniform sampler2D uColor; uniform int uSide; uniform vec2 uRes; uniform float uSize; uniform float uDpr; uniform vec3 uHot;
out vec3 vC;
void main() {
    ivec2 ij = ivec2(gl_VertexID % uSide, gl_VertexID / uSide);
    vec4 s = texelFetch(uState, ij, 0);
    float sp = clamp(length(s.zw) / 700.0, 0.0, 1.0);
    vC = mix(texelFetch(uColor, ij, 0).rgb, uHot, sp * 0.85);
    vec2 clip = s.xy / uRes * 2.0 - 1.0;
    gl_Position = vec4(clip.x, -clip.y, 0.0, 1.0);
    gl_PointSize = uSize * uDpr * (1.0 + sp * 0.7);
}`;
    const DRAW_FS = `#version 300 es
precision mediump float;
in vec3 vC; uniform float uAlpha; out vec4 o;
void main() { vec2 c = gl_PointCoord - 0.5; float a = 1.0 - smoothstep(0.1, 0.25, dot(c, c)); if (a <= 0.0) discard; o = vec4(vC, a * uAlpha); }`;
    let sim, draw;
    try { sim = program(FULL_VS, SIM_FS); draw = program(DRAW_VS, DRAW_FS); } catch (e) { console.error(e); fail("The GPU simulation's shaders didn't compile on this device."); return; }
    const vao = gl.createVertexArray(); gl.bindVertexArray(vao);
    const tri = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, tri); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const aP = gl.getAttribLocation(sim, 'aP'); gl.enableVertexAttribArray(aP); gl.vertexAttribPointer(aP, 2, gl.FLOAT, false, 0, 0);
    gl.bindVertexArray(null);
    const emptyVao = gl.createVertexArray();
    function tex(fmt, format, type, data) {
        const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
        [gl.TEXTURE_MIN_FILTER, gl.TEXTURE_MAG_FILTER].forEach(k => gl.texParameteri(gl.TEXTURE_2D, k, gl.NEAREST));
        [gl.TEXTURE_WRAP_S, gl.TEXTURE_WRAP_T].forEach(k => gl.texParameteri(gl.TEXTURE_2D, k, gl.CLAMP_TO_EDGE));
        gl.texImage2D(gl.TEXTURE_2D, 0, fmt, SIDE, SIDE, 0, format, type, data); return t;
    }
    function fbo(t) {
        const f = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, f);
        gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0);
        const ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE; gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        if (!ok) throw new Error('framebuffer'); return f;
    }
    let W = 1, H = 1, dpr = 1;
    function size() { const r = cv.getBoundingClientRect(); dpr = Math.min(2, devicePixelRatio || 1); W = Math.max(1, r.width); H = Math.max(1, r.height); cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    size();
    const init = new Float32Array(N * 4);
    for (let i = 0; i < N; i++) { init[i * 4] = Math.random() * W; init[i * 4 + 1] = Math.random() * H; }
    const stA = tex(internal, gl.RGBA, gl.FLOAT, init), stB = tex(internal, gl.RGBA, gl.FLOAT, init);
    const tgt = tex(gl.RGBA32F, gl.RGBA, gl.FLOAT, new Float32Array(N * 4));
    const colT = tex(gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(N * 4));
    let fbA, fbB;
    try { fbA = fbo(stA); fbB = fbo(stB); } catch (e) { fail("This GPU can't render to float textures, which the simulation needs."); return; }
    const su = {}, du = {};
    ['uState', 'uTarget', 'uTime', 'uDt', 'uSpring', 'uNoise', 'uDamp', 'uMouse'].forEach(n => su[n] = gl.getUniformLocation(sim, n));
    ['uState', 'uColor', 'uSide', 'uRes', 'uSize', 'uDpr', 'uHot', 'uAlpha'].forEach(n => du[n] = gl.getUniformLocation(draw, n));
    const box = (fx, fy, fw, fh) => ({ x: W * fx, y: H * fy, w: W * fw, h: H * fh });
    const SHAPES = [
        { name: 'Leadville 100', sub: 'profile', build: () => pickN(profileCands(D2.lead.ele, D2.lead.distM, box(0.05, 0.2, 0.9, 0.55), N), N) },
        { name: 'Western States, from above', sub: 'route', build: () => pickN(routeCands(WSER_ROUTE, box(0.18, 0.06, 0.64, 0.8), N), N) },
        { name: 'TrailGoat', sub: 'wordmark', build: () => { const a = tokRGB('--course'), b = tokRGB('--accent'); return pickN(textCands(['TRAILGOAT'], box(0.04, 0.2, 0.92, 0.5), { color: u => mixRGB(a, b, u) }), N); } },
        { name: 'The mascot', sub: 'mascot', build: () => pickN(imageCands(goatImg, box(0.22, 0.05, 0.56, 0.84)), N) },
        { name: 'Hardrock 100', sub: 'profile', build: () => pickN(profileCands(D2.hard.ele, D2.hard.distM, box(0.05, 0.18, 0.9, 0.58), N), N) },
    ];
    let cur = 0, shapeI = -1, boostT = -1e9, last = 0, nextAt = 0, auto = true, mouse = [0, 0, 0], dark = isDark(), hot = tokRGB('--gold');
    SHAPES.forEach((s, i) => {
        const b = document.createElement('button'); b.type = 'button'; b.className = 'chip-btn'; b.textContent = s.name.replace(', from above', ' map');
        b.addEventListener('click', () => { auto = false; setShape(i, performance.now()); if (!d.running) settle(); });
        chips.insertBefore(b, chips.querySelector('.spacer'));
    });
    function setShape(i, now) {
        shapeI = i; const t = SHAPES[i].build();
        const td = new Float32Array(N * 4), cd = new Uint8Array(N * 4);
        for (let k = 0; k < N; k++) {
            td[k * 4] = t.pos[k * 2]; td[k * 4 + 1] = t.pos[k * 2 + 1];
            cd[k * 4] = t.col[k * 3] * 255; cd[k * 4 + 1] = t.col[k * 3 + 1] * 255; cd[k * 4 + 2] = t.col[k * 3 + 2] * 255; cd[k * 4 + 3] = 255;
        }
        gl.bindTexture(gl.TEXTURE_2D, tgt); gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, SIDE, SIDE, gl.RGBA, gl.FLOAT, td);
        gl.bindTexture(gl.TEXTURE_2D, colT); gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, SIDE, SIDE, gl.RGBA, gl.UNSIGNED_BYTE, cd);
        boostT = now; nextAt = now + 6400;
        lab.innerHTML = `<b>${SHAPES[i].name}</b><span>${fmt(N)} particles with momentum, simulated on the GPU</span>`;
        $$('.chip-btn', chips).forEach((b, j) => b.setAttribute('aria-pressed', String(j === i)));
    }
    function settle() {                  // run the simulation to rest without animating it, for calm mode and hidden updates
        boostT = -1e9; last = 0; const t = performance.now();
        for (let k = 0; k < 150; k++) frame(t + k * 16);
        last = 0;
    }
    function frame(now) {
        const dt = last ? Math.min(0.033, (now - last) / 1000) : 1 / 60; last = now;
        const since = (now - boostT) / 1000;
        gl.useProgram(sim); gl.bindVertexArray(vao);
        gl.bindFramebuffer(gl.FRAMEBUFFER, cur ? fbA : fbB); gl.viewport(0, 0, SIDE, SIDE); gl.disable(gl.BLEND);
        gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, cur ? stB : stA); gl.uniform1i(su.uState, 0);
        gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, tgt); gl.uniform1i(su.uTarget, 1);
        gl.uniform1f(su.uTime, now / 1000); gl.uniform1f(su.uDt, dt);
        gl.uniform1f(su.uSpring, 2 + 20 * (1 - Math.exp(-since / 0.7)));
        gl.uniform1f(su.uNoise, calm ? 0 : 50 + 1700 * Math.exp(-since / 0.45));
        gl.uniform1f(su.uDamp, 0.92); gl.uniform3f(su.uMouse, mouse[0], mouse[1], mouse[2] && !calm ? 2600 : 0);
        gl.drawArrays(gl.TRIANGLES, 0, 3);
        cur = 1 - cur;
        gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.viewport(0, 0, cv.width, cv.height);
        gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
        gl.useProgram(draw); gl.bindVertexArray(emptyVao);
        gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, dark ? gl.ONE : gl.ONE_MINUS_SRC_ALPHA);
        gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, cur ? stB : stA); gl.uniform1i(du.uState, 0);
        gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, colT); gl.uniform1i(du.uColor, 1);
        gl.uniform1i(du.uSide, SIDE); gl.uniform2f(du.uRes, W, H); gl.uniform1f(du.uSize, innerWidth < 640 ? 1.6 : 1.7); gl.uniform1f(du.uDpr, dpr);
        gl.uniform3f(du.uHot, hot[0], hot[1], hot[2]); gl.uniform1f(du.uAlpha, dark ? 0.34 : 0.85);
        gl.drawArrays(gl.POINTS, 0, N);
    }
    cv.addEventListener('pointermove', e => { const r = cv.getBoundingClientRect(); mouse = [e.clientX - r.left, e.clientY - r.top, 1]; });
    cv.addEventListener('pointerleave', () => { mouse[2] = 0; });
    cv.addEventListener('pointerdown', () => { boostT = performance.now(); });
    scatterBtn.addEventListener('click', () => { boostT = performance.now(); });
    const loop = rafLoop((ms, now) => { if (auto && now >= nextAt) setShape((shapeI + 1) % SHAPES.length, now); frame(now); });
    let d = { running: false };
    fontsReady.then(() => { if (shapeI < 0) { setShape(0, performance.now()); if (!d.running) settle(); } });
    d = register(stage, {
        start() { last = 0; loop.start(); }, stop() { loop.stop(); },
        rest() { if (shapeI >= 0) settle(); },
    });
    new ResizeObserver(() => { const w0 = W, h0 = H; size(); if ((Math.abs(W - w0) > 1 || Math.abs(H - h0) > 1) && shapeI >= 0) { setShape(shapeI, performance.now()); if (!d.running) settle(); } }).observe(cv);
    onTheme(() => { dark = isDark(); hot = tokRGB('--gold'); if (shapeI >= 0) { setShape(shapeI, performance.now() - 5000); if (!d.running) settle(); } });
})();

/* =================== Toolbox T2. WebGPU compute: a quarter of a million particles on Hope Pass =================== */
(async function webgpuDemo() {
    const stage = $('#demo-webgpu'); if (!stage) return;
    const cv = $('#wg-canvas'), note = $('#wg-note'), stat = $('#wg-stat'), ov = $('#wg-over');
    const fail = m => { note.hidden = false; note.textContent = m; };
    if (!navigator.gpu) { fail("This browser doesn't expose WebGPU, so the compute demo can't run here. Current Chrome, Edge and Safari 26 have it."); return; }
    let device = null;
    try { const adapter = await navigator.gpu.requestAdapter(); if (!adapter) throw new Error('no adapter'); device = await adapter.requestDevice(); }
    catch (e) { fail('WebGPU is present, but no GPU adapter was available to this page.'); return; }
    device.addEventListener('uncapturederror', e => console.error('WebGPU:', e.error && e.error.message));
    const ctx = cv.getContext('webgpu'), format = navigator.gpu.getPreferredCanvasFormat(), ACC = 'rgba16float';
    ctx.configure({ device, format, alphaMode: 'opaque' });
    const T = D2.dem, GW = T.w, GH = T.h, bin = atob(T.b64), heights = new Float32Array(GW * GH);
    for (let i = 0; i < GW * GH; i++) heights[i] = (bin.charCodeAt(2 * i) | (bin.charCodeAt(2 * i + 1) << 8)) / 65535;
    const COUNT = innerWidth >= 1000 ? 262144 : 65536;
    const parts = new Float32Array(COUNT * 4);
    for (let i = 0; i < COUNT; i++) { const life = 40 + Math.random() * 220; parts[i * 4] = 1 + Math.random() * (GW - 3); parts[i * 4 + 1] = 1 + Math.random() * (GH - 3); parts[i * 4 + 2] = Math.random() * life; parts[i * 4 + 3] = life; }
    const buf = (data, usage) => { const b = device.createBuffer({ size: data.byteLength, usage: usage | GPUBufferUsage.COPY_DST }); device.queue.writeBuffer(b, 0, data); return b; };
    const partBuf = buf(parts, GPUBufferUsage.STORAGE), hBuf = buf(heights, GPUBufferUsage.STORAGE);
    const simU = device.createBuffer({ size: 32, usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST });
    const drawU = device.createBuffer({ size: 96, usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST });
    const simCode = `
struct U { gw: f32, gh: f32, time: f32, speed: f32, seed: f32, flatness: f32, p0: f32, p1: f32 };
@group(0) @binding(0) var<storage, read_write> parts: array<vec4f>;
@group(0) @binding(1) var<storage, read> height: array<f32>;
@group(0) @binding(2) var<uniform> u: U;
fn hash(n: u32) -> f32 {
    var x = n;
    x = x ^ (x >> 16u); x = x * 0x7feb352du; x = x ^ (x >> 15u); x = x * 0x846ca68bu; x = x ^ (x >> 16u);
    return f32(x) / 4294967295.0;
}
fn hAt(ix: i32, iy: i32) -> f32 {
    let x = clamp(ix, 0, i32(u.gw) - 1); let y = clamp(iy, 0, i32(u.gh) - 1);
    return height[u32(y) * u32(u.gw) + u32(x)];
}
@compute @workgroup_size(256)
fn main(@builtin(global_invocation_id) gid: vec3u) {
    let i = gid.x;
    if (i >= arrayLength(&parts)) { return; }
    var p = parts[i];
    let ix = i32(p.x); let iy = i32(p.y);
    let gx = (hAt(ix + 1, iy) - hAt(ix - 1, iy)) * 0.5;
    let gy = (hAt(ix, iy + 1) - hAt(ix, iy - 1)) * 0.5;
    let m = sqrt(gx * gx + gy * gy);
    p.z = p.z + 1.0;
    let s = i * 747796405u + u32(u.seed);
    if (m < u.flatness || p.z > p.w || p.x < 1.0 || p.y < 1.0 || p.x > u.gw - 2.0 || p.y > u.gh - 2.0) {
        p = vec4f(1.0 + hash(s) * (u.gw - 3.0), 1.0 + hash(s ^ 0x9e3779b9u) * (u.gh - 3.0), 0.0, 40.0 + hash(s + 3u) * 220.0);
    } else {
        let t = vec2f(-gy, gx) / m;
        p = vec4f(p.x + t.x * u.speed, p.y + t.y * u.speed, p.z, p.w);
    }
    parts[i] = p;
}`;
    const drawCode = `
struct R { canvas: vec2f, offset: vec2f, scale: f32, gw: f32, gh: f32, alpha: f32, cLow: vec4f, cMid: vec4f, cHigh: vec4f, fade: vec4f };
@group(0) @binding(0) var<storage, read> parts: array<vec4f>;
@group(0) @binding(1) var<storage, read> height: array<f32>;
@group(0) @binding(2) var<uniform> r: R;
struct VO { @builtin(position) pos: vec4f, @location(0) col: vec4f };
@vertex fn vsPoint(@builtin(vertex_index) vi: u32) -> VO {
    let p = parts[vi];
    let px = r.offset + p.xy * r.scale;
    var o: VO;
    o.pos = vec4f(px.x / r.canvas.x * 2.0 - 1.0, 1.0 - px.y / r.canvas.y * 2.0, 0.0, 1.0);
    let ix = u32(clamp(p.x, 0.0, r.gw - 1.0)); let iy = u32(clamp(p.y, 0.0, r.gh - 1.0));
    let hh = height[iy * u32(r.gw) + ix];
    var c = mix(r.cLow, r.cMid, clamp(hh * 2.0, 0.0, 1.0));
    c = mix(c, r.cHigh, clamp(hh * 2.0 - 1.0, 0.0, 1.0));
    let fadeInOut = clamp(p.z / 12.0, 0.0, 1.0) * clamp((p.w - p.z) / 12.0, 0.0, 1.0);
    o.col = vec4f(c.rgb, r.alpha * fadeInOut);
    return o;
}
@fragment fn fsPoint(i: VO) -> @location(0) vec4f { return i.col; }
@vertex fn vsFull(@builtin(vertex_index) vi: u32) -> VO {
    var q = array<vec2f, 3>(vec2f(-1.0, -1.0), vec2f(3.0, -1.0), vec2f(-1.0, 3.0));
    var o: VO; o.pos = vec4f(q[vi], 0.0, 1.0); o.col = r.fade; return o;
}
@fragment fn fsFade(i: VO) -> @location(0) vec4f { return i.col; }`;
    const blitCode = `
@group(0) @binding(0) var tex: texture_2d<f32>;
@group(0) @binding(1) var smp: sampler;
struct BO { @builtin(position) pos: vec4f, @location(0) uv: vec2f };
@vertex fn vs(@builtin(vertex_index) vi: u32) -> BO {
    var q = array<vec2f, 3>(vec2f(-1.0, -1.0), vec2f(3.0, -1.0), vec2f(-1.0, 3.0));
    var o: BO; o.pos = vec4f(q[vi], 0.0, 1.0); o.uv = vec2f((q[vi].x + 1.0) * 0.5, 1.0 - (q[vi].y + 1.0) * 0.5); return o;
}
@fragment fn fs(i: BO) -> @location(0) vec4f { return textureSample(tex, smp, i.uv); }`;
    let simPipe, simBG, fadePipe, pointsAdd, pointsAlpha, drawBG, blitPipe;
    try {
        const simMod = device.createShaderModule({ code: simCode }), drawMod = device.createShaderModule({ code: drawCode }), blitMod = device.createShaderModule({ code: blitCode });
        simPipe = device.createComputePipeline({ layout: 'auto', compute: { module: simMod, entryPoint: 'main' } });
        simBG = device.createBindGroup({ layout: simPipe.getBindGroupLayout(0), entries: [{ binding: 0, resource: { buffer: partBuf } }, { binding: 1, resource: { buffer: hBuf } }, { binding: 2, resource: { buffer: simU } }] });
        const layout = device.createBindGroupLayout({ entries: [
            { binding: 0, visibility: GPUShaderStage.VERTEX, buffer: { type: 'read-only-storage' } },
            { binding: 1, visibility: GPUShaderStage.VERTEX, buffer: { type: 'read-only-storage' } },
            { binding: 2, visibility: GPUShaderStage.VERTEX | GPUShaderStage.FRAGMENT, buffer: { type: 'uniform' } }] });
        const pl = device.createPipelineLayout({ bindGroupLayouts: [layout] });
        const blend = add => add
            ? { color: { srcFactor: 'src-alpha', dstFactor: 'one', operation: 'add' }, alpha: { srcFactor: 'one', dstFactor: 'one', operation: 'add' } }
            : { color: { srcFactor: 'src-alpha', dstFactor: 'one-minus-src-alpha', operation: 'add' }, alpha: { srcFactor: 'one', dstFactor: 'one-minus-src-alpha', operation: 'add' } };
        const points = add => device.createRenderPipeline({ layout: pl, vertex: { module: drawMod, entryPoint: 'vsPoint' },
            fragment: { module: drawMod, entryPoint: 'fsPoint', targets: [{ format: ACC, blend: blend(add) }] }, primitive: { topology: 'point-list' } });
        pointsAdd = points(true); pointsAlpha = points(false);
        fadePipe = device.createRenderPipeline({ layout: pl, vertex: { module: drawMod, entryPoint: 'vsFull' },
            fragment: { module: drawMod, entryPoint: 'fsFade', targets: [{ format: ACC, blend: blend(false) }] }, primitive: { topology: 'triangle-list' } });
        drawBG = device.createBindGroup({ layout, entries: [{ binding: 0, resource: { buffer: partBuf } }, { binding: 1, resource: { buffer: hBuf } }, { binding: 2, resource: { buffer: drawU } }] });
        blitPipe = device.createRenderPipeline({ layout: 'auto', vertex: { module: blitMod, entryPoint: 'vs' }, fragment: { module: blitMod, entryPoint: 'fs', targets: [{ format }] }, primitive: { topology: 'triangle-list' } });
    } catch (e) { console.error(e); fail("WebGPU is present, but this demo's pipeline couldn't be built on this GPU."); return; }
    const sampler = device.createSampler({ magFilter: 'linear', minFilter: 'linear' });
    let W = 1, H = 1, s = 1, ox = 0, oy = 0, acc = null, accView = null, blitBG = null, fresh = true, dark = isDark(), bg = { r: 0, g: 0, b: 0, a: 1 };
    const ALPHA_D = COUNT > 100000 ? 0.045 : 0.09, ALPHA_L = COUNT > 100000 ? 0.07 : 0.12, FADE_D = 0.06, FADE_L = 0.07;   // tuned so steep ground glows without washing out
    const octx = ov.getContext('2d');
    function uniforms() {
        dark = isDark();
        const b1 = tokRGB('--bg-1'); bg = { r: b1[0], g: b1[1], b: b1[2], a: 1 };
        const lo = tokRGB('--course'), mid = tokRGB('--accent'), top = tokRGB(dark ? '--ink-bright' : '--ink');
        device.queue.writeBuffer(drawU, 0, new Float32Array([W, H, ox, oy, s, GW, GH, dark ? ALPHA_D : ALPHA_L, ...lo, 1, ...mid, 1, ...top, 1, ...b1, dark ? FADE_D : FADE_L]));
        fresh = true;
    }
    function resize() {
        const r = cv.getBoundingClientRect(); W = Math.max(1, Math.round(r.width)); H = Math.max(1, Math.round(r.height));
        cv.width = W; cv.height = H;                       // one device pixel per CSS pixel keeps the 1 px points visible
        const dp = Math.min(2, devicePixelRatio || 1); ov.width = Math.round(W * dp); ov.height = Math.round(H * dp); octx.setTransform(dp, 0, 0, dp, 0, 0);
        if (acc) acc.destroy();
        acc = device.createTexture({ size: [W, H], format: ACC, usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.TEXTURE_BINDING }); accView = acc.createView();
        blitBG = device.createBindGroup({ layout: blitPipe.getBindGroupLayout(0), entries: [{ binding: 0, resource: accView }, { binding: 1, resource: sampler }] });
        s = Math.max(W / GW, H / GH); ox = (W - GW * s) / 2; oy = (H - GH * s) / 2;
        uniforms(); overlay();
    }
    function overlay() {
        octx.clearRect(0, 0, W, H);
        const b1 = tokRGB('--bg-1'), route = T.route.filter(p => p[1] >= 0 && p[1] <= GW && p[2] >= 0 && p[2] <= GH);
        octx.beginPath(); route.forEach((p, i) => { const x = ox + p[1] * s, y = oy + p[2] * s; if (i) octx.lineTo(x, y); else octx.moveTo(x, y); });
        octx.lineJoin = 'round'; octx.lineCap = 'round';
        octx.strokeStyle = rgbCss(b1, 0.85); octx.lineWidth = 5; octx.stroke();              // a dark casing keeps the route readable over the trails
        octx.strokeStyle = rgbCss(tokRGB('--gold'), 1); octx.lineWidth = 2.2; octx.stroke();
        octx.font = '600 11px "Red Hat Mono", ui-monospace, monospace'; octx.textBaseline = 'middle';
        T.labels.forEach(l => {
            const x = ox + l.x * s, y = oy + l.y * s, t = l.n === 'Hope Pass' ? `${l.n} \u00b7 ${fmt(l.ele * FT)} ft` : l.n, w = octx.measureText(t).width;
            octx.fillStyle = rgbCss(tokRGB('--gold'), 1); octx.beginPath(); octx.arc(x, y, 3.2, 0, Math.PI * 2); octx.fill();
            octx.fillStyle = rgbCss(b1, 0.86); octx.beginPath(); octx.roundRect(x + 8, y - 20, w + 12, 18, 4); octx.fill();
            octx.fillStyle = rgbCss(tokRGB('--ink-bright'), 1); octx.fillText(t, x + 14, y - 11);
        });
    }
    function frame(now) {
        device.queue.writeBuffer(simU, 0, new Float32Array([GW, GH, now / 1000, 0.33, Math.random() * 1e6, 0.0009, 0, 0]));
        const enc = device.createCommandEncoder();
        const cp = enc.beginComputePass(); cp.setPipeline(simPipe); cp.setBindGroup(0, simBG); cp.dispatchWorkgroups(Math.ceil(COUNT / 256)); cp.end();
        const rp = enc.beginRenderPass({ colorAttachments: [{ view: accView, loadOp: fresh ? 'clear' : 'load', clearValue: bg, storeOp: 'store' }] });
        fresh = false;
        rp.setBindGroup(0, drawBG); rp.setPipeline(fadePipe); rp.draw(3);
        rp.setPipeline(dark ? pointsAdd : pointsAlpha); rp.draw(COUNT); rp.end();
        const bp = enc.beginRenderPass({ colorAttachments: [{ view: ctx.getCurrentTexture().createView(), loadOp: 'clear', clearValue: bg, storeOp: 'store' }] });
        bp.setPipeline(blitPipe); bp.setBindGroup(0, blitBG); bp.draw(3); bp.end();
        device.queue.submit([enc.finish()]);
    }
    resize();
    window.__tgGPU = { frame: n => { for (let i = 0; i < (n || 1); i++) frame(performance.now()); }, cv };   // lets a test render and read back
    setText(stat, `${fmt(COUNT)} particles · one compute dispatch per frame · ${GW} × ${GH} height grid`);
    new ResizeObserver(() => resize()).observe(cv);
    onTheme(() => { uniforms(); overlay(); });
    const loop = rafLoop((ms, now) => frame(now));
    for (let i = 0; i < 40; i++) frame(performance.now());
    register(stage, { start() { loop.start(); }, stop() { loop.stop(); }, rest() { for (let i = 0; i < 80; i++) frame(performance.now()); } });
})();

/* =================== Toolbox T3. Contours by marching squares =================== */
(function contours() {
    const stage = $('#demo-contours'); if (!stage) return;
    const cv = $('#ct-canvas'), read = $('#ct-read'), replay = $('#ct-replay');
    const T = D2.dem, GW = T.w, GH = T.h, bin = atob(T.b64), Hm = new Float32Array(GW * GH);
    for (let i = 0; i < GW * GH; i++) Hm[i] = T.lo + (bin.charCodeAt(2 * i) | (bin.charCodeAt(2 * i + 1) << 8)) / 65535 * (T.hi - T.lo);
    const STEP = 100, levels = [];
    for (let v = Math.ceil(T.lo / STEP) * STEP; v < T.hi; v += STEP) levels.push(v);
    const segs = levels.map(t => {                     // marching squares: one pass per contour level
        const out = [];
        for (let y = 0; y < GH - 1; y++) for (let x = 0; x < GW - 1; x++) {
            const a = Hm[y * GW + x], b = Hm[y * GW + x + 1], c = Hm[(y + 1) * GW + x + 1], d = Hm[(y + 1) * GW + x];
            const up = (a > t) + (b > t) + (c > t) + (d > t); if (up === 0 || up === 4) continue;
            const pts = [];
            if ((a > t) !== (b > t)) pts.push(x + (t - a) / (b - a), y);
            if ((b > t) !== (c > t)) pts.push(x + 1, y + (t - b) / (c - b));
            if ((d > t) !== (c > t)) pts.push(x + (t - d) / (c - d), y + 1);
            if ((a > t) !== (d > t)) pts.push(x, y + (t - a) / (d - a));
            for (let k = 0; k + 3 < pts.length; k += 4) out.push(pts[k], pts[k + 1], pts[k + 2], pts[k + 3]);
        }
        return new Float32Array(out);
    });
    const ctx = cv.getContext('2d');
    let W = 1, H = 1, s = 1, ox = 0, oy = 0, paths = [], cols = [], hi = -1, prog = 1;
    const cellM = T.km[0] * 1000 / GW, shade = new Float32Array(GW * GH);          // hillshade, lit from the north-west
    for (let y = 0; y < GH; y++) for (let x = 0; x < GW; x++) {
        const dx = (Hm[y * GW + Math.min(GW - 1, x + 1)] - Hm[y * GW + Math.max(0, x - 1)]) / (2 * cellM);
        const dy = (Hm[Math.min(GH - 1, y + 1) * GW + x] - Hm[Math.max(0, y - 1) * GW + x]) / (2 * cellM);
        const nz = 1 / Math.hypot(dx, dy, 1);
        shade[y * GW + x] = Math.max(0, (dx * 0.5 + dy * 0.5 + 0.7071) * nz);
    }
    const shadeCv = document.createElement('canvas'); shadeCv.width = GW; shadeCv.height = GH;
    function paintShade() {
        const dark = isDark(), sh = tokRGB(dark ? '--well' : '--ink'), img = shadeCv.getContext('2d').createImageData(GW, GH);
        for (let i = 0; i < GW * GH; i++) {
            const a = clamp(1 - shade[i]) ** 1.4 * (dark ? 0.95 : 0.42);
            img.data[i * 4] = sh[0] * 255; img.data[i * 4 + 1] = sh[1] * 255; img.data[i * 4 + 2] = sh[2] * 255; img.data[i * 4 + 3] = a * 255;
        }
        shadeCv.getContext('2d').putImageData(img, 0, 0);
    }
    const route = T.route.filter(p => p[1] >= 0 && p[1] <= GW && p[2] >= 0 && p[2] <= GH);
    function build() {
        const r = cv.getBoundingClientRect(), dp = Math.min(2, devicePixelRatio || 1);
        W = Math.max(1, r.width); H = Math.max(1, r.height); cv.width = Math.round(W * dp); cv.height = Math.round(H * dp); ctx.setTransform(dp, 0, 0, dp, 0, 0);
        s = Math.max(W / GW, H / GH); ox = (W - GW * s) / 2; oy = (H - GH * s) / 2;
        paths = segs.map(sg => { const p = new Path2D(); for (let k = 0; k < sg.length; k += 4) { p.moveTo(ox + sg[k] * s, oy + sg[k + 1] * s); p.lineTo(ox + sg[k + 2] * s, oy + sg[k + 3] * s); } return p; });
        const lo = tokRGB('--course'), mid = tokRGB('--accent'), top = tokRGB('--ink-bright');
        cols = levels.map((_, k) => { const u = k / (levels.length - 1); return u < 0.5 ? mixRGB(lo, mid, u * 2) : mixRGB(mid, top, (u - 0.5) * 2); });
        paintShade(); draw();
    }
    function draw() {
        ctx.fillStyle = rgbCss(tokRGB('--bg-1'), 1); ctx.fillRect(0, 0, W, H);
        ctx.globalAlpha = 0.35 + 0.65 * clamp(prog * 3); ctx.imageSmoothingEnabled = true; ctx.drawImage(shadeCv, ox, oy, GW * s, GH * s); ctx.globalAlpha = 1;
        const n = levels.length;
        levels.forEach((v, k) => {
            const a = clamp((prog * (n + 5) - k) / 5); if (a <= 0) return;
            const index = v % 500 === 0, on = k === hi;
            ctx.strokeStyle = on ? rgbCss(tokRGB('--gold'), 1) : rgbCss(cols[k], a * (index ? 0.95 : 0.5));
            ctx.lineWidth = on ? 2.4 : index ? 1.5 : 0.8; ctx.stroke(paths[k]);
        });
        if (route.length > 1) {
            ctx.beginPath(); route.forEach((p, i) => { const x = ox + p[1] * s, y = oy + p[2] * s; if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y); });
            ctx.setLineDash([5, 4]); ctx.strokeStyle = rgbCss(tokRGB('--fuel'), clamp(prog * 2 - 1)); ctx.lineWidth = 1.8; ctx.stroke(); ctx.setLineDash([]);
        }
        const la = clamp(prog * 4 - 3); if (la <= 0) return;                       // place names arrive with the summit
        ctx.font = '600 11px "Red Hat Mono", ui-monospace, monospace'; ctx.textBaseline = 'middle';
        const b1 = tokRGB('--bg-1');
        T.labels.forEach(l => {
            const x = ox + l.x * s, y = oy + l.y * s, t = l.n === 'Hope Pass' ? `${l.n} \u00b7 ${fmt(l.ele * FT)} ft` : l.n, w = ctx.measureText(t).width;
            ctx.fillStyle = rgbCss(tokRGB('--fuel'), la); ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = rgbCss(b1, 0.88 * la); ctx.beginPath(); ctx.roundRect(x + 8, y - 20, w + 12, 18, 4); ctx.fill();
            ctx.fillStyle = rgbCss(tokRGB('--ink-bright'), la); ctx.fillText(t, x + 14, y - 11);
        });
    }
    function eleAtPx(px, py) {
        const gx = clamp((px - ox) / s, 0, GW - 1.001), gy = clamp((py - oy) / s, 0, GH - 1.001), x = gx | 0, y = gy | 0, fx = gx - x, fy = gy - y;
        const a = Hm[y * GW + x], b = Hm[y * GW + x + 1], c = Hm[(y + 1) * GW + x + 1], d = Hm[(y + 1) * GW + x];
        return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * fx * fy + d * (1 - fx) * fy;
    }
    cv.addEventListener('pointermove', e => {
        const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top, m = eleAtPx(x, y);
        hi = clamp(Math.round((m - levels[0]) / STEP), 0, levels.length - 1);
        read.hidden = false; read.style.left = x + 'px'; read.style.top = y + 'px';
        read.textContent = `${fmt(m)} m · ${fmt(m * FT)} ft · contour ${fmt(levels[hi])} m`;
        draw();
    });
    cv.addEventListener('pointerleave', () => { hi = -1; read.hidden = true; draw(); });
    const loop = rafLoop((ms) => { prog = clamp(ms / 4800); draw(); if (prog >= 1) loop.stop(); });
    function play() { if (calm) { prog = 1; draw(); return; } prog = 0; loop.stop(); loop.start(); }
    replay.addEventListener('click', play);
    new ResizeObserver(() => build()).observe(cv);
    onTheme(build);
    build();
    let played = false;
    register(stage, { start() { if (!played) { played = true; play(); } }, stop() { loop.stop(); prog = 1; draw(); }, rest() { prog = 1; draw(); } });
})();

/* =================== Toolbox T4. Real scrollytelling: the Leadville story, driven by the page's own scroll =================== */
(function scrolly() {
    const wrap = $('#scrolly'); if (!wrap) return;
    const steps = $$('.sc-step', wrap);
    const S = LeadStory($('#sc-canvas'), $('#sc-labels'), dotBudget(2200, 1800, 1300), k => steps.forEach((st, j) => st.classList.toggle('on', j === k)));
    if (!S) { $('.no-webgl', wrap).hidden = false; return; }
    steps.forEach((st, k) => { st.querySelector('p').innerHTML = S.BEATS[k].text(); st.querySelector('.sc-stat').textContent = S.BEATS[k].stat(); });
    window.__tgScrolly = { S, progress: () => progress() };            // lets a test drive it without animation frames
    function progress() {
        const mid = innerHeight * 0.55, cs = steps.map(st => { const r = st.getBoundingClientRect(); return r.top + r.height / 2; });
        if (mid <= cs[0]) return 0;
        if (mid >= cs[cs.length - 1]) return cs.length - 1;
        for (let k = 0; k < cs.length - 1; k++) if (mid < cs[k + 1]) return k + easeInOut(clamp(((mid - cs[k]) / (cs[k + 1] - cs[k]) - 0.3) / 0.4));
        return 0;
    }
    let inView = false, cur = 0, target = 0, raf = 0;
    const tick = () => {
        raf = 0; target = progress();
        cur = calm ? target : cur + (target - cur) * 0.2;
        if (Math.abs(target - cur) < 0.002) cur = target;
        S.showAt(cur);
        if (cur !== target && inView) raf = requestAnimationFrame(tick);
    };
    const kick = () => { if (inView && !raf) raf = requestAnimationFrame(tick); };
    addEventListener('scroll', kick, { passive: true });
    addEventListener('resize', kick);
    new IntersectionObserver(es => { inView = es[0].isIntersecting; if (inView) { cur = target = progress(); S.showAt(cur); } }, { threshold: 0 }).observe(wrap);
    S.showAt(0);
})();

/* =================== Toolbox T5. Scroll-driven CSS: the script only draws the shapes =================== */
(function cssScroll() {
    const stage = $('#demo-cssd'); if (!stage) return;
    const L = D2.lead, e = L.ele, lo = Math.min(...e), hi = Math.max(...e);
    const pts = e.map((v, i) => [(i / (e.length - 1) * 400).toFixed(1), (132 - (v - lo) / (hi - lo) * 116).toFixed(1)]);
    const d = pts.map((p, i) => (i ? 'L' : 'M') + p[0] + ' ' + p[1]).join('');
    $('#sd-line').setAttribute('d', d); $('#sd-area').setAttribute('d', d + 'L400 140L0 140Z');
    const stops = [0, ...L.aids.map(a => a.m), L.distM], DX = L.distM / (e.length - 1);
    const gains = stops.slice(1).map((b, k) => { let g = 0; for (let i = Math.floor(stops[k] / DX) + 1; i <= Math.min(e.length - 1, Math.floor(b / DX)); i++) g += Math.max(0, e[i] - e[i - 1]); return g; });
    const gmax = Math.max(...gains);
    $('#sd-bars').innerHTML = gains.map((g, i) => `<i class="sd-bar" style="--i:${i};height:${(8 + g / gmax * 92).toFixed(1)}%" title="${fmt(g * FT)} ft"></i>`).join('');
    $('#sd-count').style.setProperty('--target', String(D.catalogCount));
    const ok = window.CSS && CSS.supports && CSS.supports('animation-timeline: view()');
    $('#sd-note').hidden = !!ok;
})();

/* =================== Toolbox T6. View transitions: a course card grows into its page header =================== */
(function viewTrans() {
    const stage = $('#demo-vt'); if (!stage) return;
    const grid = $('#vt-grid'), detail = $('#vt-detail'), note = $('#vt-note');
    const byId = Object.fromEntries(D2.ridge.map(c => [c.id, c]));
    const list = [228, 473, 233, 66].map(id => byId[id]).filter(Boolean), REGION = { 473: 'Colorado' };
    const area = (c, w, h) => { const v = c.ele120, lo = Math.min(...v), hi = Math.max(...v); const p = v.map((y, i) => `${(i / (v.length - 1) * w).toFixed(1)} ${(h - 4 - (y - lo) / ((hi - lo) || 1) * (h - 12)).toFixed(1)}`); return { line: 'M' + p.join('L'), fill: 'M' + p.join('L') + `L${w} ${h}L0 ${h}Z` }; };
    const nameOf = c => shortName(c.name).replace(' Endurance Run 100 Miler', '').replace(' Trail 100 Run', ' 100');
    grid.innerHTML = list.map((c, i) => { const a = area(c, 200, 70); return `<button type="button" class="vt-card" data-i="${i}"><svg viewBox="0 0 200 70" aria-hidden="true"><path class="vt-fill" d="${a.fill}"/><path class="vt-line" d="${a.line}"/></svg><span class="vt-name">${nameOf(c)}</span><span class="vt-meta">${(c.distM / MI).toFixed(1)} mi · ${fmt(c.gainM * FT)} ft</span></button>`; }).join('');
    const supported = typeof document.startViewTransition === 'function';
    note.hidden = supported;
    const setNames = (svg, nm) => { if (svg) svg.style.viewTransitionName = 'vt-prof'; if (nm) nm.style.viewTransitionName = 'vt-name'; };
    const clearNames = () => $$('[style*="view-transition-name"]', stage).forEach(el => { el.style.viewTransitionName = ''; });
    function show(i) {
        const c = list[i], a = area(c, 1000, 260);
        detail.innerHTML = `<button type="button" class="btn vt-back">← All courses</button><div class="vt-head"><h3 class="vt-name">${nameOf(c)}</h3><p class="vt-meta">${[(c.distM / MI).toFixed(1) + ' mi', fmt(c.gainM * FT) + ' ft of climbing', c.region || REGION[c.id]].filter(Boolean).join(' · ')}</p></div>
            <svg class="vt-big" viewBox="0 0 1000 260" aria-hidden="true"><path class="vt-fill" d="${a.fill}"/><path class="vt-line" d="${a.line}"/></svg>`;
        $('.vt-back', detail).addEventListener('click', () => back(i));
    }
    function run(update) {
        if (!supported || calm) { update(); clearNames(); return; }
        const t = document.startViewTransition(update);
        t.finished.finally(clearNames);
    }
    function open(i) {
        const card = $(`.vt-card[data-i="${i}"]`, grid);
        setNames($('svg', card), $('.vt-name', card));
        run(() => { clearNames(); show(i); grid.hidden = true; detail.hidden = false; setNames($('.vt-big', detail), $('.vt-name', detail)); });
    }
    function back(i) {
        setNames($('.vt-big', detail), $('.vt-name', detail));
        run(() => { clearNames(); detail.hidden = true; grid.hidden = false; const card = $(`.vt-card[data-i="${i}"]`, grid); setNames($('svg', card), $('.vt-name', card)); });
    }
    grid.addEventListener('click', e => { const b = e.target.closest('.vt-card'); if (b) open(+b.dataset.i); });
})();

/* =================== Toolbox T7. GSAP: SplitText, DrawSVG and MorphSVG on one timeline =================== */
(function gsapDemo() {
    const stage = $('#demo-gsap'); if (!stage) return;
    const note = $('#gs-note'), lab = $('#gs-label'), playBtn = $('#gs-play');
    if (!window.gsap || !window.MorphSVGPlugin || !window.SplitText || !window.DrawSVGPlugin) { note.hidden = false; return; }
    gsap.registerPlugin(MorphSVGPlugin, SplitText, DrawSVGPlugin);
    (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(setup);   // SplitText measures letters, so fonts go first
    function setup() {
    const byId = Object.fromEntries(D2.ridge.map(c => [c.id, c]));
    const area = ele => { const lo = Math.min(...ele), hi = Math.max(...ele); return 'M40 400 ' + ele.map((v, i) => `L${(40 + i / (ele.length - 1) * 920).toFixed(1)} ${(400 - (v - lo) / ((hi - lo) || 1) * 330).toFixed(1)}`).join(' ') + ' L960 400 Z'; };
    const SH = [
        { id: 'wser', d: area(byId[233] ? byId[233].ele120 : W.ele), t: 'Western States 100 · downhill overall' },
        { id: 'lead', d: area(D2.lead.ele.filter((_, i) => i % 5 === 0)), t: 'Leadville 100 · Hope Pass twice' },
        { id: 'hard', d: area(D2.hard.ele.filter((_, i) => i % 3 === 0)), t: 'Hardrock 100 · 13 big climbs' },
        { id: 'goat', d: D2.goatPath, t: 'The mascot, traced from the launch-kit art' },
    ];
    const svg = $('#gs-svg');
    svg.insertAdjacentHTML('beforeend', SH.map(s => `<path id="gs-src-${s.id}" d="${s.d}" style="display:none"/>`).join(''));
    const shape = $('#gs-shape'); shape.setAttribute('d', SH[0].d);
    const split = new SplitText('#gs-head', { type: 'chars,words' });
    const say = i => () => { lab.textContent = SH[i].t; };
    const tl = gsap.timeline({ repeat: -1, repeatDelay: 0.4, paused: true, defaults: { ease: 'power3.inOut' } });
    tl.call(say(0))
      .from(split.chars, { yPercent: 120, opacity: 0, rotate: 7, duration: 0.8, ease: 'power3.out', stagger: 0.02 })
      .from(shape, { drawSVG: '0%', duration: 1.4, ease: 'power2.inOut' }, '<0.1')
      .from(shape, { fillOpacity: 0, duration: 0.8 }, '<0.8')
      .call(say(1), null, '+=1.1').to(shape, { morphSVG: '#gs-src-lead', duration: 1.3 }, '<')
      .call(say(2), null, '+=1.4').to(shape, { morphSVG: '#gs-src-hard', duration: 1.3 }, '<')
      .call(say(3), null, '+=1.4').to(shape, { morphSVG: { shape: '#gs-src-goat', type: 'rotational' }, duration: 1.5 }, '<')
      .call(say(0), null, '+=1.8').to(shape, { morphSVG: '#gs-src-wser', duration: 1.4 }, '<')
      .to(split.chars, { yPercent: -110, opacity: 0, duration: 0.45, ease: 'power2.in', stagger: 0.012 }, '+=1.2');
    let paused = false;
    playBtn.addEventListener('click', () => {
        paused = !paused; playBtn.querySelector('span').textContent = paused ? 'Play' : 'Pause';
        playBtn.querySelector('svg').innerHTML = paused ? '<path d="M7 5v14l12-7z"/>' : '<path d="M8 5v14M16 5v14"/>';
        if (paused) tl.pause(); else if (!calm) tl.play();
    });
    const restFrame = () => { tl.pause(); tl.seek(2.6); lab.textContent = SH[0].t; };
    let fresh = true; restFrame();
    register(stage, { start() { if (paused) return; if (fresh) { fresh = false; tl.restart(); } else tl.play(); }, stop() { tl.pause(); }, rest: restFrame });
    }
})();

/* =================== Toolbox T8. A state-machine goat (the Rive idea, built in CSS) =================== */
(function stateGoat() {
    const stage = $('#demo-sm'); if (!stage) return;
    const cv = $('#sm-canvas'), goat = $('#sm-goat'), tag = $('#sm-tag'), chips = $$('#sm-states span'), gIn = $('#sm-grade'), aIn = $('#sm-aid'), fIn = $('#sm-fin');
    const L = D2.lead, D = L.distM, n0 = L.ele.length;
    const sm = L.ele.map((_, i) => { let a = 0, c = 0; for (let k = -5; k <= 5; k++) { const j = i + k; if (j >= 0 && j < n0) { a += L.ele[j]; c++; } } return a / c; });
    const lo = Math.min(...sm), hi = Math.max(...sm);
    const eleAt = m => sampleArr(sm, m / D), gradeAt = m => (eleAt(m + 900) - eleAt(m - 900)) / 1800;
    goat.src = GOAT_SRC;
    const ctx = cv.getContext('2d');
    let W = 1, H = 1, dp = 1;
    const X = m => 48 + m / D * (W - 96), Y = v => H - 34 - (v - lo) / (hi - lo) * (H * 0.55);   // room for the goat at both ends
    function size() { const r = cv.getBoundingClientRect(); dp = Math.min(2, devicePixelRatio || 1); W = Math.max(1, r.width); H = Math.max(1, r.height); cv.width = Math.round(W * dp); cv.height = Math.round(H * dp); ctx.setTransform(dp, 0, 0, dp, 0, 0); }
    let state = 'idle', stT = 0, dist = 0, lastAid = -1, phase = 0, confetti = [];
    const COL = () => ['--fuel', '--course', '--gear', '--gold', '--crew', '--climb'].map(tokRGB);
    function set(s, now) {
        if (s === state) return; state = s; stT = now;
        chips.forEach(c => c.classList.toggle('on', c.dataset.s === s));
        if (s === 'aid') { tag.textContent = L.aids[lastAid].n; tag.hidden = false; }
        else if (s === 'celebrate') { tag.textContent = 'Finish!'; tag.hidden = false; burst(); }
        else tag.hidden = true;
    }
    function burst() {
        const cs = COL(), x = X(D), y = Y(eleAt(D)) - 40;
        confetti = Array.from({ length: 80 }, () => ({ x, y, vx: (Math.random() - 0.5) * 320, vy: -120 - Math.random() * 260, c: rgbCss(cs[(Math.random() * cs.length) | 0], 1), r: Math.random() * 6, spin: (Math.random() - 0.5) * 10 }));
    }
    const moving = g => g >= 0.04 ? 'climb' : g <= -0.04 ? 'descend' : 'run';
    function update(now, dt) {
        const since = now - stT;
        if (state === 'idle') { if (since > 1200) set('run', now); }
        else if (state === 'aid') { if (since > 900) set(moving(gradeAt(dist)), now); }
        else if (state === 'celebrate') { if (since > 2800) { dist = 0; lastAid = -1; set('idle', now); } }
        else {
            const g = gradeAt(dist), base = D / 24;
            const next = Math.min(D, dist + base * (g >= 0.04 ? 0.45 : g <= -0.04 ? 1.45 : 1) * dt);
            const ai = L.aids.findIndex((a, i) => i > lastAid && a.m > dist && a.m <= next);
            dist = next;
            if (ai >= 0) { lastAid = ai; set('aid', now); }
            else if (dist >= D) set('celebrate', now);
            else set(moving(g), now);
        }
        confetti.forEach(p => { p.vy += 520 * dt; p.x += p.vx * dt; p.y += p.vy * dt; p.r += p.spin * dt; });
    }
    function draw(now) {
        const bg = tokRGB('--bg-1'), acc = tokRGB('--accent');
        ctx.clearRect(0, 0, W, H);
        const g = ctx.createLinearGradient(0, H * 0.3, 0, H);
        g.addColorStop(0, rgbCss(acc, 0.22)); g.addColorStop(1, rgbCss(acc, 0));
        ctx.beginPath(); ctx.moveTo(X(0), H);
        for (let i = 0; i <= 200; i++) { const m = i / 200 * D; ctx.lineTo(X(m), Y(eleAt(m))); }
        ctx.lineTo(X(D), H); ctx.closePath(); ctx.fillStyle = g; ctx.fill();
        ctx.beginPath(); for (let i = 0; i <= 200; i++) { const m = i / 200 * D; if (i) ctx.lineTo(X(m), Y(eleAt(m))); else ctx.moveTo(X(m), Y(eleAt(m))); }
        ctx.strokeStyle = rgbCss(acc, 0.9); ctx.lineWidth = 2; ctx.stroke();
        ctx.fillStyle = rgbCss(tokRGB('--aid'), 0.9);
        L.aids.forEach((a, i) => { ctx.beginPath(); ctx.arc(X(a.m), Y(eleAt(a.m)), i <= lastAid ? 3.5 : 2.5, 0, Math.PI * 2); ctx.fill(); });
        confetti.forEach(p => { ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r); ctx.fillStyle = p.c; ctx.fillRect(-3, -1.5, 6, 3); ctx.restore(); });
        // the goat's pose comes from the state, the way a Rive state machine blends animations
        const x = X(dist), y = Y(eleAt(dist)), t = (now - stT) / 1000;
        const rate = { idle: 2.2, run: 11, climb: 6.5, descend: 15, aid: 18, celebrate: 6 }[state], amp = { idle: 1.5, run: 4, climb: 3, descend: 5, aid: 1.5, celebrate: 0 }[state];
        phase += rate / 60;
        const lean = { idle: 0, run: -2, climb: -11, descend: 8, aid: Math.sin(t * 22) * 5, celebrate: Math.sin(t * 6) * 8 }[state];
        const bob = state === 'celebrate' ? -Math.abs(Math.sin(t * 5.5)) * 44 : -Math.abs(Math.sin(phase)) * amp;
        const sc = state === 'idle' ? 1 + Math.sin(t * 2.4) * 0.015 : 1;
        goat.style.transform = `translate(${x.toFixed(1)}px, ${(y + bob).toFixed(1)}px) translate(-50%, -94%) rotate(${lean.toFixed(1)}deg) scale(${sc.toFixed(3)})`;
        tag.style.left = x + 'px'; tag.style.top = (y - 88) + 'px';
        const gr = Math.round(gradeAt(dist) * 100);
        setText(gIn, `${gr > 0 ? '+' : ''}${gr}%`); setText(aIn, String(state === 'aid')); setText(fIn, String(state === 'celebrate'));
    }
    let last = 0;
    const loop = rafLoop((ms, now) => { const dt = last ? Math.min(0.05, (now - last) / 1000) : 0; last = now; update(now, dt); draw(now); });
    size(); new ResizeObserver(() => { size(); draw(performance.now()); }).observe(cv);
    set('run', 0); set('idle', performance.now()); draw(performance.now());
    register(stage, { start() { last = 0; loop.start(); }, stop() { loop.stop(); }, rest() { dist = D * 0.43; set('climb', performance.now()); draw(performance.now()); } });
    onTheme(() => draw(performance.now()));
})();
