/* TrailGoat shell behaviours for a standalone page (kb-tokyo).
 * The site's own idiom: one IIFE, window.TrailGoat* globals, no framework.
 *   TrailGoatTheme  { get, set, list, DEFAULT }  — html.theme-* + localStorage 'tg_theme'
 *   TrailGoatToast(msg, { accent, duration })     — bottom-right toast stack
 *   Burger: <button class="nav-burger"> toggles .menu-open on .topbar and .nav-open on body
 *   Menus:  [data-menu="#id"] toggles the hidden attribute on a .menu; outside click / Esc close
 *   Reveal: html.reveal-armed + .reveal.in via IntersectionObserver (progressive)
 */
(function () {
    'use strict';
    var THEMES = [
        { key: 'tokyonight', label: 'Tokyo Night', swatch: ['#1a1b26', '#7aa2f7', '#bb9af7'] },
        { key: 'default',    label: 'Forest',      swatch: ['#07120f', '#ff7a1a', '#9ae600'] },
        { key: 'firstlight', label: 'First Light', swatch: ['#f5f7f6', '#1f7a3a', '#d9580d'] },
    ];
    var DEFAULT = 'tokyonight', KEY = 'tg_theme';
    function read() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
    function write(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
    function apply(key) {
        var html = document.documentElement;
        html.className = html.className.split(/\s+/).filter(function (c) { return c.indexOf('theme-') !== 0; }).join(' ');
        if (key !== DEFAULT) html.classList.add('theme-' + key);
        var m = document.querySelector('meta[name="theme-color"][data-tg-theme]');
        if (m) m.setAttribute('content', getComputedStyle(html).getPropertyValue('--bg-0').trim() || '#1a1b26');
        document.dispatchEvent(new CustomEvent('tg:theme', { detail: { theme: key } }));
    }
    function valid(k) { return THEMES.some(function (t) { return t.key === k; }); }
    var q = new URLSearchParams(location.search).get('theme');
    var current = valid(q) ? q : (valid(read()) ? read() : DEFAULT);
    apply(current);
    window.TrailGoatTheme = {
        get: function () { return current; },
        set: function (k) { if (!valid(k)) return false; current = k; write(k); apply(k); return true; },
        list: function () { return THEMES.map(function (t) { return { key: t.key, label: t.label, swatch: t.swatch.slice() }; }); },
        DEFAULT: DEFAULT,
    };

    var stack;
    window.TrailGoatToast = function (msg, opts) {
        opts = opts || {};
        if (!stack) { stack = document.createElement('div'); stack.className = 'tg-toast-stack'; stack.setAttribute('aria-live', 'polite'); document.body.appendChild(stack); }
        var t = document.createElement('div'); t.className = 'tg-toast'; t.textContent = msg;
        if (opts.accent) t.style.setProperty('--tg-toast-acc', opts.accent);
        stack.appendChild(t);
        requestAnimationFrame(function () { t.classList.add('show'); });
        setTimeout(function () { t.classList.remove('show'); setTimeout(function () { t.remove(); }, 260); }, opts.duration || 3600);
    };

    document.addEventListener('DOMContentLoaded', function () {
        // Theme grid(s): <div class="theme-grid" data-theme-grid>
        document.querySelectorAll('[data-theme-grid]').forEach(function (grid) {
            function paint() {
                grid.innerHTML = window.TrailGoatTheme.list().map(function (t) {
                    var on = t.key === window.TrailGoatTheme.get();
                    return '<button type="button" data-theme="' + t.key + '" class="' + (on ? 'active' : '') + '" aria-pressed="' + on + '">' +
                        '<span class="theme-swatch" aria-hidden="true" style="background:' + t.swatch[0] + '"><i style="background:' + t.swatch[1] + '"></i><i style="background:' + t.swatch[2] + '"></i></span>' + t.label + '</button>';
                }).join('');
            }
            paint();
            grid.addEventListener('click', function (e) { var b = e.target.closest('[data-theme]'); if (b) window.TrailGoatTheme.set(b.dataset.theme); });
            document.addEventListener('tg:theme', paint);
        });
        // Burger
        var topbar = document.querySelector('.topbar'), burger = document.querySelector('.nav-burger');
        function setOpen(on) { if (!topbar) return; topbar.classList.toggle('menu-open', on); document.body.classList.toggle('nav-open', on); if (burger) burger.setAttribute('aria-expanded', String(on)); }
        if (burger) {
            burger.addEventListener('click', function () { setOpen(!topbar.classList.contains('menu-open')); });
            document.addEventListener('click', function (e) { if (topbar.classList.contains('menu-open') && !topbar.contains(e.target)) setOpen(false); });
            document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setOpen(false); });
        }
        // Segmented / unit toggles: aria-pressed groups
        document.querySelectorAll('.unit-toggle, .segmented').forEach(function (g) {
            g.addEventListener('click', function (e) {
                var b = e.target.closest('button'); if (!b) return;
                g.querySelectorAll('button').forEach(function (x) { x.classList.toggle('active', x === b); x.setAttribute('aria-pressed', String(x === b)); });
            });
        });
        // Menus
        document.querySelectorAll('[data-menu]').forEach(function (btn) {
            var menu = document.querySelector(btn.dataset.menu); if (!menu) return;
            btn.addEventListener('click', function (e) { e.stopPropagation(); menu.hidden = !menu.hidden; btn.setAttribute('aria-expanded', String(!menu.hidden)); });
            document.addEventListener('click', function (e) { if (!menu.hidden && !menu.contains(e.target)) { menu.hidden = true; btn.setAttribute('aria-expanded', 'false'); } });
            document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { menu.hidden = true; btn.setAttribute('aria-expanded', 'false'); } });
        });
        // Modal: [data-modal="#id"] opens; [data-close] inside closes; scrim click closes
        document.querySelectorAll('[data-modal]').forEach(function (btn) {
            var scrim = document.querySelector(btn.dataset.modal); if (!scrim) return;
            btn.addEventListener('click', function () { scrim.hidden = false; var f = scrim.querySelector('button, [href], input'); if (f) f.focus(); });
            scrim.addEventListener('click', function (e) { if (e.target === scrim || e.target.closest('[data-close]')) scrim.hidden = true; });
            document.addEventListener('keydown', function (e) { if (e.key === 'Escape') scrim.hidden = true; });
        });
        // Toast demo: [data-toast="message"]
        document.querySelectorAll('[data-toast]').forEach(function (b) { b.addEventListener('click', function () { window.TrailGoatToast(b.dataset.toast, { accent: b.dataset.toastAccent }); }); });
        // Reveal
        if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches && document.querySelector('.reveal')) {
            document.documentElement.classList.add('reveal-armed');
            var io = new IntersectionObserver(function (es) { es.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } }); }, { threshold: 0.05, rootMargin: '0px 0px 160px 0px' });
            document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });
        }
        // Icons: <i data-ico="flag"></i> → inline SVG
        if (window.TG_ICON) document.querySelectorAll('[data-ico]').forEach(function (el) { el.outerHTML = window.TG_ICON(el.dataset.ico, el.dataset.cls || 'ico'); });
    });
})();
