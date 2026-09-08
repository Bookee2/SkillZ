/* TrailGoat — the icon system. ONE source of truth for every pictogram.
 *
 * Brand rule: no standard emoji anywhere in the product. Icons are simple line
 * art — 24×24 viewBox, stroked in currentColor, so they inherit the colour and
 * size of whatever they sit in. The goat mascot image is the one exception.
 *
 * Usage:
 *   TG_ICON('rain')                  -> '<svg …>…</svg>'  (class "ico")
 *   TG_ICON('rain', 'wx-ico')        -> custom class
 *   TrailGoatIcons.weather(code, isDay) -> icon name for an Open-Meteo WMO code
 *   TrailGoatIcons.draw(ctx, name, x, y, size, color) -> same art on a canvas
 *
 * Keep every path stroke-only (no fills) so one CSS colour drives the whole set.
 */
(function () {
    'use strict';

    var P = {
        /* --- navigation --- */
        // Dashboard: a gauge — fewer strokes than the old 4-box grid, and it
        // reads as "your numbers at a glance" at 14px.
        gauge: '<path d="M3.5 17.5a8.5 8.5 0 1 1 17 0"/><path d="M12 17.5l4.4-5.6"/>',
        flag: '<path d="M4 21V4h13l-2.5 4L17 12H4"/>',
        pen: '<path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>',
        // Training: an activity pulse (single stroke, like flag/pen).
        pulse: '<path d="M2.5 12.5h4.2l2.6-6.4 4.2 12.2 2.7-5.8h5.3"/>',
        calendar: '<rect x="3" y="5" width="18" height="16" rx="2.5"/><path d="M7.5 3v3.4M16.5 3v3.4"/>',
        search: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
        sliders: '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M2 14h4M10 8h4M18 16h4"/>',

        /* --- weather (Open-Meteo WMO codes) --- */
        sun: '<circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.2 4.2l1.6 1.6M18.2 18.2l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.2 19.8l1.6-1.6M18.2 5.8l1.6-1.6"/>',
        moon: '<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a7.5 7.5 0 1 0 10.5 10.5z"/>',
        partly: '<path d="M8 5.2V3.4M3.6 8h1.8M4.9 4.9l1.3 1.3M11.1 4.9 9.8 6.2"/><circle cx="8" cy="9.4" r="2.6"/><path d="M7.5 19.5h9.8a3.4 3.4 0 0 0 .3-6.8 4.8 4.8 0 0 0-9.2-.7 3.7 3.7 0 0 0-.9 7.5z"/>',
        cloud: '<path d="M7.2 19h10a3.6 3.6 0 0 0 .3-7.2 5.1 5.1 0 0 0-9.8-.8A3.9 3.9 0 0 0 7.2 19z"/>',
        fog: '<path d="M7.6 13.5h9.2a3.2 3.2 0 0 0 .3-6.4 4.6 4.6 0 0 0-8.8-.7 3.5 3.5 0 0 0-.7 7z"/><path d="M4 17h16M6.5 20.5h11"/>',
        drizzle: '<path d="M7.4 15.5h9.6a3.4 3.4 0 0 0 .3-6.8 4.9 4.9 0 0 0-9.4-.8 3.7 3.7 0 0 0-.5 7.6z"/><path d="M9.5 18.6v1.8M14.5 18.6v1.8"/>',
        rain: '<path d="M7.4 14.5h9.6a3.4 3.4 0 0 0 .3-6.8 4.9 4.9 0 0 0-9.4-.8 3.7 3.7 0 0 0-.5 7.6z"/><path d="M9 17.6l-1 3M13 17.6l-1 3M17 17.6l-1 3"/>',
        snow: '<path d="M7.4 14h9.6a3.4 3.4 0 0 0 .3-6.8 4.9 4.9 0 0 0-9.4-.8A3.7 3.7 0 0 0 7.4 14z"/><path d="M9 18.2h.01M12 20.2h.01M15 18.2h.01M12 17.2h.01"/>',
        storm: '<path d="M7.4 14h9.6a3.4 3.4 0 0 0 .3-6.8 4.9 4.9 0 0 0-9.4-.8A3.7 3.7 0 0 0 7.4 14z"/><path d="M13 16.5l-2.6 3.4h3.2L11.4 23"/>',
        // Sunrise/sunset differ by the ARROW, not just the sun — at 13px the rays
        // alone were indistinguishable.
        sunrise: '<path d="M3 17h3.4M17.6 17H21M8.6 17a3.4 3.4 0 0 1 6.8 0M2.5 20.6h19"/><path d="M12 3v5.6M9.4 5.4 12 2.8l2.6 2.6"/>',
        sunset: '<path d="M3 17h3.4M17.6 17H21M8.6 17a3.4 3.4 0 0 1 6.8 0M2.5 20.6h19"/><path d="M12 2.8v5.6M9.4 5.8 12 8.4l2.6-2.6"/>',
        thermometer: '<path d="M14 14.8V5a2 2 0 1 0-4 0v9.8a4.2 4.2 0 1 0 4 0z"/><path d="M12 8.5v6.8"/>',
        droplet: '<path d="M12 3.2s5.4 5.6 5.4 9.2a5.4 5.4 0 0 1-10.8 0C6.6 8.8 12 3.2 12 3.2z"/>',
        wind: '<path d="M3 9h9.5a2.8 2.8 0 1 0-2.8-2.8M3 14h13a3 3 0 1 1-3 3"/><path d="M3 11.5h6"/>',
        clock: '<circle cx="12" cy="12" r="8.6"/><path d="M12 7.2V12l3.2 2"/>',

        /* --- activity kinds & misc UI --- */
        runner: '<circle cx="15.5" cy="4.6" r="1.9"/><path d="M6 21l3.4-5.6 3-2.2-1.4-4.4-3.6 2.3-1.2 2.7"/><path d="M13.4 8.8l3 2.6 3.1.4M9.4 15.4l2.8 2.2.9 3.4"/>',
        mountain: '<path d="M2.5 19.5h19L14 6.5l-3.3 5.6-2-2.6z"/><path d="M10.7 12.1l2 3.3"/>',
        home: '<path d="M3.5 10.4 12 3.6l8.5 6.8V20a1 1 0 0 1-1 1h-5v-6h-5v6h-5a1 1 0 0 1-1-1z"/>',
        pencilSm: '<path d="M4 20h4L20 8a2.1 2.1 0 0 0-3-3L5 17z"/>',
        check: '<path d="M4 12.5 9.5 18 20 6.5"/>',
        map: '<path d="M9 4.2 3 6.6v13.2l6-2.4 6 2.4 6-2.4V4.2l-6 2.4z"/><path d="M9 4.2v13.2M15 6.6v13.2"/>',
        mail: '<rect x="2.5" y="5" width="19" height="14" rx="2.5"/><path d="m3.5 7 8.5 6 8.5-6"/>',
        pin: '<path d="M12 21.5S5.5 15.6 5.5 10.8A6.5 6.5 0 0 1 12 4.3a6.5 6.5 0 0 1 6.5 6.5c0 4.8-6.5 10.7-6.5 10.7z"/><circle cx="12" cy="10.7" r="2.3"/>',

        /* --- typed course waypoints (TG-234) --- */
        parking: '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M9.6 16.6V7.4h3a2.7 2.7 0 0 1 0 5.4h-3"/>',
        signpost: '<path d="M12 21v-9.6M12 6.2V3"/><path d="M5.2 6.2h11.4l2.6 2.6-2.6 2.6H5.2z"/>',
        crew: '<circle cx="9" cy="7.8" r="3.1"/><path d="M3.4 20a5.6 5.6 0 0 1 11.2 0"/><path d="M15.6 5.2a3.1 3.1 0 0 1 0 5.9M16.4 14.6a5.6 5.6 0 0 1 4.2 5.4"/>',
        restroom: '<rect x="5.5" y="3.5" width="13" height="17" rx="1.6"/><path d="M15.3 11.2v1.6"/>',
        hazard: '<path d="M12 3.8 2.6 19.6h18.8z"/><path d="M12 9.8v4.2M12 16.9h.01"/>',
        chart: '<path d="M3 20.5h18"/><path d="M6 20.5v-6M11 20.5V8M16 20.5v-9M21 20.5V4.5"/>',
        download: '<path d="M12 3.5v11.5"/><path d="m7.6 10.6 4.4 4.4 4.4-4.4"/><path d="M4 17.5v1.5a1.5 1.5 0 0 0 1.5 1.5h13a1.5 1.5 0 0 0 1.5-1.5v-1.5"/>',
    };

    var ALIAS = { partlycloudy: 'partly', showers: 'rain', thunder: 'storm' };

    function ico(name, cls) {
        var inner = P[ALIAS[name] || name];
        if (!inner) return '';
        return '<svg class="' + (cls || 'ico') + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
            'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + inner + '</svg>';
    }

    /* Open-Meteo WMO weather code -> icon name (same thresholds the weather
       pages already used for their emoji). */
    function weather(code, isDay) {
        if (code == null) return isDay === false ? 'moon' : 'sun';
        if (code === 0) return isDay === false ? 'moon' : 'sun';
        if (code <= 2) return isDay === false ? 'moon' : 'partly';
        if (code === 3) return 'cloud';
        if (code <= 49) return 'fog';
        if (code <= 59) return 'drizzle';
        if (code <= 69) return 'rain';
        if (code <= 79) return 'snow';
        if (code <= 84) return 'rain';
        if (code <= 94) return 'snow';
        return 'storm';
    }

    var WX_LABEL = {
        sun: 'Clear', moon: 'Clear', partly: 'Partly cloudy', cloud: 'Overcast', fog: 'Fog',
        drizzle: 'Drizzle', rain: 'Rain', snow: 'Snow', storm: 'Thunderstorm',
    };
    function weatherLabel(code, isDay) { return WX_LABEL[weather(code, isDay)] || ''; }

    /* Canvas rendering (Chart.js overlays draw icons with the 2D context, where
       an <svg> string is useless). Parses the same paths into Path2D and scales
       the 24×24 art to `size`, centred on (x, y). */
    var _cache = {};
    function paths(name) {
        var key = ALIAS[name] || name;
        if (_cache[key]) return _cache[key];
        var inner = P[key];
        if (!inner || typeof Path2D === 'undefined') return null;
        var out = [];
        // <path d="…">
        inner.replace(/<path d="([^"]+)"/g, function (_, d) { out.push(new Path2D(d)); return ''; });
        // <circle cx cy r> — Path2D has no circle(), so build an arc
        inner.replace(/<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"/g, function (_, cx, cy, r) {
            var p = new Path2D();
            p.arc(+cx, +cy, +r, 0, Math.PI * 2);
            out.push(p);
            return '';
        });
        // <rect x y width height rx>
        inner.replace(/<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"(?: rx="([\d.]+)")?/g,
            function (_, x, y, w, h, r) {
                var p = new Path2D();
                if (p.roundRect) p.roundRect(+x, +y, +w, +h, +(r || 0));
                else p.rect(+x, +y, +w, +h);
                out.push(p);
                return '';
            });
        _cache[key] = out;
        return out;
    }

    function draw(ctx, name, x, y, size, color) {
        var ps = paths(name);
        if (!ps || !ps.length) return false;
        var s = (size || 16) / 24;
        ctx.save();
        ctx.translate(x - size / 2, y - size / 2);
        ctx.scale(s, s);
        ctx.strokeStyle = color || '#fff';
        ctx.lineWidth = 1.6 / s;   // the context is scaled by s, so this renders ~1.6 device px
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ps.forEach(function (p) { ctx.stroke(p); });
        ctx.restore();
        return true;
    }

    /* Typed course waypoints (TG-234): one place maps a pin type to its icon,
       so the creator, planner and any future surface agree. */
    var WAYPOINT_ICON = {
        parking: 'parking', trailhead: 'signpost', water: 'droplet', crew: 'crew',
        restroom: 'restroom', hazard: 'hazard', other: 'pin',
    };
    function waypoint(type) { return WAYPOINT_ICON[type] || 'pin'; }

    window.TrailGoatIcons = { ico: ico, weather: weather, weatherLabel: weatherLabel, draw: draw, paths: P, waypoint: waypoint };
    window.TG_ICON = ico;
})();
