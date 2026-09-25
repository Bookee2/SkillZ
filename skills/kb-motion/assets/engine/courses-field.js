/* /courses motion.
 *
 * 1. The header field: dots form the catalog count, then each featured race's
 *    own elevation profile (server-picked, see seo._field_races). The caption
 *    names the race on screen and links to it; the dots below jump to one.
 * 2. A card that becomes the page: a cross-document view transition. Clicking
 *    a course card names that card and its title, and the course page names its
 *    header and h1 the same (course.css), so the browser morphs one into the
 *    other. Browsers without cross-document view transitions just navigate.
 */
(function () {
    'use strict';
    var MI = 1609.344, FT = 3.28084;
    var fmt = function (n) { return Math.round(n).toLocaleString('en-US'); };

    /* ---- 1. The header field ---- */
    (function field() {
        var host = document.getElementById('cx-field'), TF = window.TGField;
        var data = document.getElementById('cx-data');
        if (!host || !TF || !data) return;
        var races = [];
        try { races = JSON.parse(data.textContent).races || []; } catch (e) { races = []; }
        var cap = document.getElementById('cx-cap'), nm = document.getElementById('cx-name'),
            meta = document.getElementById('cx-meta'), dots = document.getElementById('cx-dots'), k = cap.querySelector('.cx-k');
        var countText = nm.textContent;
        var count = (countText.match(/\d[\d,]*/) || [''])[0];
        var shapes = [{ kind: 'The catalog', name: countText, meta: 'Every one of them has a shape', href: '/courses',
            build: function (box, N) { return TF.pickN(TF.textCands([count], box(0.2, 0.08, 0.6, 0.62), TF.gradient()), N); } }];
        races.forEach(function (c) {
            shapes.push({ kind: 'Featured race', name: c.name,
                meta: [(c.distM / MI).toFixed(1) + ' mi', c.gainM ? fmt(c.gainM * FT) + ' ft' : '', c.region].filter(Boolean).join(' · '),
                href: '/course/' + (c.slug || c.id),
                build: function (box, N) { return TF.pickN(TF.profileCands(c.ele, c.distM || 1, box(0.04, 0.1, 0.92, 0.56), N), N); } });
        });
        host.hidden = false;
        var btns = shapes.map(function (s, i) {
            var b = document.createElement('button'); b.type = 'button'; b.setAttribute('aria-label', 'Show ' + s.name);
            b.addEventListener('click', function () { if (ctl) ctl.go(i); });
            dots.appendChild(b); return b;
        });
        var ctl = TF.cycle(document.getElementById('cx-canvas'), shapes, {
            dots: TF.budget(6000, 4500, 3000), hold: 3200, burst: 0, restIndex: shapes.length > 1 ? 1 : 0,
            onShape: function (s, i) {
                k.textContent = s.kind; nm.textContent = s.name; meta.textContent = s.meta; cap.href = s.href;
                btns.forEach(function (b, j) { b.setAttribute('aria-current', String(j === i)); });
            },
        });
        if (!ctl) host.hidden = true;
    })();

    /* ---- 2. A card that becomes the page ---- */
    var name = function (el, n) { if (el) el.style.viewTransitionName = n; };
    function mark(card) {
        document.querySelectorAll('[data-vt]').forEach(function (el) { el.style.viewTransitionName = ''; el.removeAttribute('data-vt'); });
        if (!card) return;
        var a = card.querySelector('a'), t = card.querySelector('.cp-card-name');
        name(a, 'tg-card'); name(t, 'tg-title');
        if (a) a.setAttribute('data-vt', ''); if (t) t.setAttribute('data-vt', '');
    }
    document.addEventListener('click', function (e) {
        var a = e.target.closest && e.target.closest('li[data-id] > a[href^="/course/"]');
        if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        mark(a.parentElement);
    });
    // Back from a course page: the card it came from shrinks back into place.
    window.addEventListener('pagereveal', function (e) {
        if (!e.viewTransition) return;
        var from = null;
        try { from = navigation.activation && navigation.activation.from && new URL(navigation.activation.from.url).pathname; } catch (err) { from = null; }
        if (!from || from.indexOf('/course/') !== 0) { mark(null); return; }
        var a = document.querySelector('li[data-id] > a[href="' + from + '"]');
        if (!a) { e.viewTransition.skipTransition(); return; }
        mark(a.parentElement);
        e.viewTransition.finished.finally(function () { mark(null); });
    });
})();
