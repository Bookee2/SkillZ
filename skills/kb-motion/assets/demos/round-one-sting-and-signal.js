/* =================== E. Signal drop =================== */
(function offline() {
    const stage = $('#demo-offline'), bars = $$('#e-bars i'), net = $('#e-net'), toast = $('#e-toast'), dot = $('#e-dot');
    const iR = W.aids.findIndex(a => a.n === 'Rucky Chucky'), iF = W.aids.findIndex(a => a.n === 'Foresthill');
    const a0 = W.aids[iF].m, a1 = W.aids[iR].m;
    $('#e-next-meta').textContent = `mile ${(a1 / MI).toFixed(1)} \u00b7 ETA ${clockParts(aidT[iR]).text}`;
    const lo = W.distM * 0.55, hi = W.distM * 0.85, sub = [];
    for (let m = lo; m <= hi; m += (hi - lo) / 60) sub.push([m, eleAt(m)]);
    const eLo = Math.min(...sub.map(s => s[1])), eHi = Math.max(...sub.map(s => s[1]));
    const X = m => (m - lo) / (hi - lo) * 240, Y = e => 64 - (e - eLo) / (eHi - eLo) * 54;
    const dLine = sub.map((s, i) => (i ? 'L' : 'M') + X(s[0]).toFixed(1) + ' ' + Y(s[1]).toFixed(1)).join('');
    $('#e-line').setAttribute('d', dLine); $('#e-area').setAttribute('d', dLine + 'L240 70L0 70Z');
    const setDot = f => { const m = a0 + (a1 - a0) * f; dot.setAttribute('cx', X(m).toFixed(1)); dot.setAttribute('cy', Y(eleAt(m)).toFixed(1)); };
    function setBars(n, label) { bars.forEach((b, i) => b.classList.toggle('off', i >= n)); setText(net, label); }
    const CYCLE = 9500;
    const loop = rafLoop(ms => {
        const k = ms % CYCLE; setDot(clamp((ms % 19000) / 19000));
        const s = k / 1000;
        if (s < 1.5) setBars(4, '5G'); else if (s < 2) setBars(3, '5G'); else if (s < 2.5) setBars(2, 'LTE'); else if (s < 3) setBars(1, '3G');
        else if (s < 7.6) setBars(0, 'No service'); else setBars(4, '5G');
        toast.classList.toggle('show', s >= 3.5 && s < 7.2);
    });
    register(stage, {
        start() { loop.start(); }, stop() { loop.stop(); },
        rest() { setBars(0, 'No service'); toast.classList.add('show'); setDot(0.5); },
    });
    setBars(0, 'No service'); toast.classList.add('show'); setDot(0.5);
})();

/* =================== G. Goat on the ridge =================== */
/* =================== F + H. Summit sting =================== */
const STING_COURSES = D.courses.map(c => ({ ...c, pos: c.ele.indexOf(Math.max(...c.ele)) / (c.ele.length - 1) }))
    .filter(c => c.pos > 0.2 && c.pos < 0.8).sort((a, b) => Math.abs(a.pos - 0.5) - Math.abs(b.pos - 0.5));
const LAYOUT = {
    wide:   { vw: 1600, vh: 900,  base: 0.9,  amp: 0.26, wordTop: 0.12, fs: '11cqw',   ts: '1.55cqw', us: '1.6cqw', tagTop: 0.355, urlTop: 0.41, goatH: 0.13,  cs: '1.05cqw', stack: false },
    square: { vw: 1080, vh: 1080, base: 0.9,  amp: 0.24, wordTop: 0.16, fs: '13.5cqw', ts: '2.6cqw',  us: '2.7cqw', tagTop: 0.33,  urlTop: 0.38, goatH: 0.1,   cs: '1.9cqw',  stack: false },
    tall:   { vw: 1080, vh: 1920, base: 0.86, amp: 0.18, wordTop: 0.14, fs: '25cqw',   ts: '4.2cqw',  us: '4.6cqw', tagTop: 0.44,  urlTop: 0.475, goatH: 0.065, cs: '3.2cqw',  stack: true },
};
function makeSting(host, kind) {
    const L = LAYOUT[kind];
    const uid = 's' + Math.random().toString(36).slice(2, 8);
    host.innerHTML = `<svg viewBox="0 0 ${L.vw} ${L.vh}" aria-hidden="true"><defs>
        <linearGradient id="${uid}g" x1="0" x2="1"><stop offset="0" stop-color="#0db9d7"/><stop offset="1" stop-color="#7aa2f7"/></linearGradient>
        <linearGradient id="${uid}a" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#7aa2f7" stop-opacity="0.28"/><stop offset="1" stop-color="#7aa2f7" stop-opacity="0"/></linearGradient></defs>
        <path class="st-area" fill="url(#${uid}a)"/><path class="st-line" stroke="url(#${uid}g)" pathLength="1" stroke-dasharray="1"/>
        <image class="st-goat" href="${GOAT_SRC}" preserveAspectRatio="xMidYMax meet"/></svg>
        <div class="st-word" role="img" aria-label="TrailGoat"></div><div class="st-tag">Greatness on all trails</div><div class="st-url">trailgoat.run</div><div class="st-course"></div>`;
    const word = $('.st-word', host), tag = $('.st-tag', host), url = $('.st-url', host), course = $('.st-course', host);
    const area = $('.st-area', host), line = $('.st-line', host), goat = $('.st-goat', host);
    word.style.top = (L.wordTop * 100) + '%'; word.style.setProperty('--fs', L.fs);
    tag.style.top = (L.tagTop * 100) + '%'; tag.style.setProperty('--ts', L.ts);
    url.style.top = (L.urlTop * 100) + '%'; url.style.setProperty('--us', L.us);
    course.style.setProperty('--cs', L.cs);
    const letters = [];
    'TRAILGOAT'.split('').forEach((ch, i) => {
        if (L.stack && i === 5) { const br = document.createElement('span'); br.className = 'br'; word.appendChild(br); }
        const s = document.createElement('span'); s.textContent = ch; s.setAttribute('aria-hidden', 'true');
        // One gradient across the whole word, like the lockup: each letter shows its slice.
        const n = L.stack ? (i < 5 ? 5 : 4) : 9, k = L.stack ? (i < 5 ? i : i - 5) : i;
        s.style.setProperty('--bw', (n * 100) + '%'); s.style.setProperty('--bx', (n > 1 ? k / (n - 1) * 100 : 0) + '%');
        word.appendChild(s); letters.push(s);
    });
    line.setAttribute('stroke-width', (L.vw * 0.004).toFixed(1));
    const gh = L.vh * L.goatH, gw = gh * GOAT_AR;
    goat.setAttribute('width', gw.toFixed(1)); goat.setAttribute('height', gh.toFixed(1));
    let summit = [0, 0];
    function useCourse(c) {
        const e = c.ele, n = e.length, lo = Math.min(...e), hi = Math.max(...e);
        const sm = e.map((v, i) => (e[Math.max(0, i - 1)] + v + e[Math.min(n - 1, i + 1)]) / 3);
        const pts = sm.map((v, i) => [i / (n - 1) * L.vw, L.vh * L.base - (v - lo) / (hi - lo) * L.vh * L.amp]);
        const d = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join('');
        line.setAttribute('d', d); area.setAttribute('d', d + `L${L.vw} ${L.vh}L0 ${L.vh}Z`);
        let bi = 0; pts.forEach((p, i) => { if (p[1] < pts[bi][1]) bi = i; }); summit = pts[bi];
        course.textContent = 'Ridge: ' + shortName(c.name);
    }
    function set(t) {
        line.setAttribute('stroke-dashoffset', (1 - easeInOut(clamp(t / 1200))).toFixed(4));
        area.style.opacity = clamp((t - 500) / 1000).toFixed(3);
        letters.forEach((s, i) => {
            const u = easeOut(clamp((t - (950 + i * 55)) / 560));
            s.style.transform = `translateY(${((1 - u) * 60).toFixed(1)}%)`; s.style.opacity = u.toFixed(3);
        });
        const gu = clamp((t - 1900) / 650), drop = (1 - bounce(gu)) * L.vh * 0.28;
        goat.setAttribute('x', (summit[0] - gw * 0.5).toFixed(1));
        goat.setAttribute('y', (summit[1] - gh * 0.97 - drop).toFixed(1));
        goat.style.opacity = t < 1900 ? 0 : 1;
        const tu = clamp((t - 2450) / 450); tag.style.opacity = tu; url.style.opacity = clamp((t - 2650) / 450);
        course.style.opacity = clamp((t - 300) / 600) * 0.9;
    }
    return { useCourse, set, END: 3300 };
}
let courseIx = 0, soundOn = false, actx = null;
function chime() {
    if (!soundOn || !actx) return;
    const t = actx.currentTime, master = actx.createGain(); master.gain.value = 0.12; master.connect(actx.destination);
    [[0.95, 440], [1.3, 659.25], [2.45, 880]].forEach(([at, f]) => {
        const o = actx.createOscillator(), g = actx.createGain(); o.type = 'triangle'; o.frequency.value = f;
        g.gain.setValueAtTime(0, t + at); g.gain.linearRampToValueAtTime(1, t + at + 0.01); g.gain.exponentialRampToValueAtTime(0.001, t + at + 0.9);
        o.connect(g); g.connect(master); o.start(t + at); o.stop(t + at + 1);
    });
}
function stingGroup(hosts, kinds, { withSound } = {}) {
    const st = hosts.map((h, i) => makeSting(h, kinds[i]));
    const HOLD = 2200; let lastCycle = -1;
    const use = () => st.forEach(s => s.useCourse(STING_COURSES[courseIx % STING_COURSES.length]));
    use(); st.forEach(s => s.set(s.END));
    const loop = rafLoop(ms => {
        const P = st[0].END + HOLD, cyc = Math.floor(ms / P), k = ms % P;
        if (cyc !== lastCycle) {
            if (lastCycle >= 0 && withSound) courseIx++;   // the main sting walks the catalog
            use(); lastCycle = cyc;
            if (withSound) chime();
        }
        st.forEach(s => s.set(k));
    });
    return {
        st, use,
        start() { lastCycle = -1; loop.start(); }, stop() { loop.stop(); },
        rest() { use(); st.forEach(s => s.set(s.END)); },
        restart() { loop.stop(); lastCycle = -1; loop.start(); },
    };
}
const mainGroup = stingGroup([$('#sting-main')], ['wide'], { withSound: true });
const mainDemo = register($('#sting-main'), mainGroup);
const sizeGroup = stingGroup([$('#sting-w'), $('#sting-s'), $('#sting-t')], ['wide', 'square', 'tall']);
register($('#sizes'), sizeGroup);
$('#sting-replay').addEventListener('click', () => {
    courseIx++;
    if (mainDemo.running) mainGroup.restart(); else mainGroup.rest();
});
$('#sting-sound').addEventListener('click', e => {
    soundOn = !soundOn;
    const b = e.currentTarget; b.setAttribute('aria-pressed', String(soundOn)); b.querySelector('span').textContent = soundOn ? 'Sound on' : 'Sound off';
    if (soundOn) { try { actx = actx || new (window.AudioContext || window.webkitAudioContext)(); actx.resume(); } catch (err) { soundOn = false; } }
    if (soundOn && mainDemo.running) mainGroup.restart();
});

/* =================== Page map =================== */
