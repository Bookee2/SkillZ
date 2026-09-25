/* Home page motion: the hero's race readout and the plan story.
 *
 * 1. A living hero. The Western States flythrough behind the hero is a real
 *    render (scripts/flythrough/render.py): the headlamp runner is keyed at
 *    route.at(TOTAL * min(1, (frame - 1) / 1065)) over 1,440 frames at 24 fps,
 *    so every moment of playback is a known mile. The readout reads the playing
 *    frame (requestVideoFrameCallback where available) and looks the rest up in
 *    the course data: elevation, grade, carbs, next aid and the race clock. All
 *    three encodes (webm, mp4, phone mp4) share that timing. If the video
 *    isn't playing (reduced motion, Save-Data, First Light) the readout shows the
 *    poster's frame.
 * 2. A plan comes together, round two. Leadville drawn in dots: each dot is a
 *    slice of trail, and the same dots travel through map, profile, grade,
 *    time, fuel and night. Needs tg-field.js.
 *
 * Course data is embedded (downsampled from the catalog: Western States 100 and
 * Leadville Trail 100 Run) so the page makes no extra request for it.
 */
(function () {
    'use strict';
    var DATA = {"wser":{"distM":161051,"ele":[1900,1973,2057,2145,2262,2354,2445,2495,2612,2607,2556,2508,2508,2428,2375,2296,2288,2305,2308,2280,2238,2195,2168,2127,2107,2122,2145,2176,2231,2195,2227,2229,2220,2154,2120,2165,2210,2245,2235,2190,2198,2173,2123,2114,2128,2122,2108,2078,2069,2118,2103,2083,2089,2066,2028,1981,1941,1906,1834,1758,1763,1800,1792,1754,1705,1684,1755,1777,1826,1852,1939,1988,2009,2046,2076,2113,2047,1994,1949,1914,1911,1932,1915,1876,1818,1837,1824,1813,1794,1764,1705,1642,1571,1532,1520,1480,1442,1441,1438,1434,1433,1431,1431,1424,1382,1366,1331,1270,1147,1025,921,885,1041,1153,1268,1316,1327,1305,1251,1189,1103,1005,932,877,846,758,641,553,681,784,876,922,994,1076,1063,1042,1031,1095,1133,1089,1047,944,826,880,927,985,1031,1014,993,972,903,838,764,686,596,576,575,581,637,617,592,597,610,631,657,670,654,551,523,436,375,314,299,296,351,306,331,283,261,247,248,262,283,275,253,237,257,322,361,416,430,374,392,378,353,390,381,403,449,463,464,466,469,427,404,396,413,409,427,424,422,408,385,368,359,301,224,209,202,232,278,359,403,408,477,470,426,378,319,258,219,184,197,213,230,308,380,421,413,394],"aids":[{"n":"Lyon Ridge","m":17417},{"n":"Red Star Ridge","m":26423},{"n":"Duncan Canyon","m":39812},{"n":"Robinson Flat","m":49383},{"n":"Miller's Defeat","m":56117},{"n":"Dusty Corners","m":62046},{"n":"Last Chance","m":69947},{"n":"Devil's Thumb","m":77130},{"n":"El Dorado Creek","m":85507},{"n":"Michigan Bluff","m":89969},{"n":"Foresthill","m":99594},{"n":"Dardanelles (Cal-1)","m":105348},{"n":"Peachstone (Cal-2)","m":113222},{"n":"Ford's Bar (Cal-3)","m":117639},{"n":"Rucky Chucky","m":124919},{"n":"Green Gate","m":127805},{"n":"Auburn Lake Trails","m":136386},{"n":"Quarry Rd","m":145460},{"n":"Pointed Rocks","m":151345},{"n":"Robie Point","m":158848}]},"lead":{"distM":160229,"ele":[3092,3079,3079,3080,3069,3050,3044,3037,3029,3022,3018,3013,3014,3014,3005,2998,2986,2981,2977,2974,2977,2981,2987,2991,3001,2998,3000,3000,3000,3008,3004,3005,3003,3009,3011,3011,3011,3010,3020,3037,3052,3071,3103,3136,3174,3191,3213,3224,3234,3238,3245,3254,3228,3239,3237,3236,3245,3243,3244,3255,3265,3288,3287,3268,3258,3255,3240,3227,3236,3224,3210,3197,3169,3158,3141,3131,3114,3094,3088,3070,3056,3046,3032,3022,3019,3019,3015,3015,3037,3019,3013,3015,3015,3016,3019,3020,3018,3017,3030,3024,3015,3018,3020,3033,3028,3019,3018,3016,3017,3021,3016,3014,3013,3014,3013,3014,3013,3013,3016,3013,3014,3014,3013,3014,3011,2966,2958,2956,2955,2955,2951,2948,2945,2942,2937,2933,2931,2933,2931,2928,2926,2926,2927,2926,2922,2940,2947,2946,2945,2938,2929,2922,2915,2909,2904,2904,2906,2905,2902,2900,2899,2898,2896,2893,2892,2889,2887,2893,2898,2902,2906,2911,2917,2922,2927,2933,2934,2938,2939,2941,2943,2944,2945,2945,2940,2934,2940,2950,2960,2977,2987,2988,2984,2990,3000,3007,3005,3003,2999,3007,3019,3035,3047,3057,3057,3059,3058,3062,3072,3089,3099,3125,3144,3158,3169,3168,3164,3145,3159,3190,3211,3228,3213,3187,3192,3203,3230,3212,3198,3169,3138,3113,3077,3043,3010,3002,2995,2986,2951,2924,2886,2848,2823,2815,2811,2812,2813,2806,2808,2807,2807,2805,2807,2812,2827,2850,2899,2952,2989,3029,3080,3125,3172,3235,3289,3323,3348,3378,3411,3446,3483,3531,3578,3616,3656,3701,3751,3814,3792,3753,3709,3654,3595,3557,3513,3472,3433,3361,3296,3233,3146,3084,3081,3082,3082,3082,3089,3094,3094,3098,3129,3159,3182,3195,3194,3199,3213,3208,3189,3172,3162,3144,3129,3118,3119,3126,3138,3159,3168,3182,3203,3215,3205,3194,3197,3186,3167,3137,3101,3095,3098,3093,3083,3080,3080,3085,3078,3123,3210,3270,3341,3418,3448,3499,3540,3584,3647,3691,3739,3783,3819,3771,3719,3669,3626,3591,3547,3498,3459,3422,3388,3357,3330,3307,3255,3194,3138,3095,3046,3000,2966,2919,2863,2834,2815,2807,2806,2806,2806,2807,2807,2814,2808,2815,2811,2822,2839,2873,2911,2939,2979,3017,3022,3022,3034,3061,3106,3137,3164,3188,3208,3227,3200,3195,3189,3201,3227,3217,3198,3169,3149,3153,3168,3168,3160,3148,3129,3108,3094,3076,3063,3057,3059,3059,3058,3049,3039,3024,3010,3003,2999,3004,3007,3004,2993,2985,2986,2989,2981,2965,2952,2943,2936,2938,2944,2945,2944,2942,2942,2939,2939,2935,2932,2929,2923,2918,2913,2907,2903,2899,2895,2890,2888,2889,2892,2895,2898,2899,2900,2901,2904,2907,2905,2904,2907,2913,2920,2926,2936,2943,2945,2946,2942,2932,2922,2927,2926,2926,2927,2930,2932,2932,2933,2936,2941,2944,2947,2949,2954,2955,2956,2957,2963,2981,3015,3023,3027,3021,3019,3024,3016,3009,3000,2994,3001,3013,3018,3027,3034,3038,3030,3033,3038,3046,3039,3034,3041,3054,3068,3086,3113,3125,3138,3157,3173,3195,3228,3259,3239,3240,3230,3223,3209,3185,3163,3126,3097,3068,3049,3032,3018,3011,3011,3011,3010,3008,3003,3004,3004,3007,3000,3000,3000,2998,2999,2989,2986,2978,2977,2972,2977,2969,2965,2960,2958,2950,2949,2945,2943,2941,2962,2971,2976,2977,2976,2977,2987,2996,3000,3004,3012,3020,3030,3041,3050,3069,3081,3077,3079,3092],"aids":[{"n":"Carter Summit Mini Aid","m":17059},{"n":"Turquoise Lake Dam","m":32992},{"n":"Outward Bound","m":41843},{"n":"Half Pipe","m":51177},{"n":"Twin Lakes Village","m":64857},{"n":"Hope Pass","m":73064},{"n":"Winfield","m":84008},{"n":"Hope Pass","m":94951},{"n":"Twin Lakes Village","m":102998},{"n":"Half Pipe","m":116838},{"n":"Outward Bound","m":126012},{"n":"Turquoise Lake Dam","m":135507}],"route":[[39.24862,-106.29229],[39.24841,-106.31009],[39.25428,-106.32794],[39.25913,-106.34019],[39.26692,-106.34106],[39.27752,-106.34293],[39.28471,-106.35445],[39.28598,-106.36531],[39.29186,-106.37195],[39.2944,-106.38252],[39.28983,-106.38022],[39.28509,-106.38213],[39.28709,-106.38963],[39.28639,-106.39773],[39.2862,-106.4051],[39.28387,-106.4133],[39.28518,-106.42535],[39.28129,-106.43001],[39.28412,-106.44473],[39.27982,-106.43669],[39.27814,-106.42878],[39.27815,-106.42419],[39.27678,-106.41953],[39.27717,-106.41192],[39.27625,-106.40381],[39.27546,-106.39564],[39.27464,-106.38943],[39.27545,-106.38171],[39.27593,-106.37457],[39.27649,-106.36529],[39.27465,-106.35739],[39.26897,-106.35316],[39.26405,-106.35537],[39.26016,-106.35802],[39.25595,-106.36327],[39.25227,-106.36707],[39.24966,-106.36879],[39.24727,-106.36546],[39.24848,-106.35223],[39.24372,-106.35577],[39.23667,-106.37266],[39.23348,-106.38867],[39.22546,-106.39018],[39.21876,-106.37329],[39.20625,-106.36206],[39.19357,-106.3641],[39.19271,-106.37625],[39.18362,-106.3698],[39.17379,-106.36355],[39.16687,-106.36779],[39.15826,-106.36778],[39.14934,-106.37415],[39.14489,-106.38058],[39.14521,-106.39356],[39.1385,-106.39804],[39.13454,-106.39621],[39.12433,-106.3912],[39.11608,-106.38939],[39.10863,-106.39439],[39.10197,-106.39335],[39.08913,-106.38976],[39.08363,-106.39055],[39.08254,-106.38632],[39.08136,-106.38339],[39.07895,-106.39055],[39.07365,-106.39155],[39.06995,-106.38683],[39.05991,-106.38765],[39.04756,-106.38992],[39.04265,-106.39115],[39.03386,-106.39809],[39.02631,-106.4023],[39.02345,-106.40436],[39.02175,-106.40493],[39.01882,-106.40528],[39.01627,-106.40356],[39.01503,-106.40417],[39.01286,-106.40347],[39.01153,-106.40397],[39.00982,-106.40377],[39.0039,-106.40274],[38.99802,-106.40528],[38.99087,-106.4178],[38.99061,-106.43033],[38.98844,-106.44036],[38.98639,-106.45019],[38.98329,-106.44114],[38.98636,-106.44651],[38.98869,-106.44498],[38.98978,-106.43412],[38.99067,-106.42027],[38.99594,-106.41042],[39.00152,-106.40278],[39.00729,-106.40448],[39.01037,-106.40294],[39.01235,-106.4032],[39.01421,-106.40412],[39.01583,-106.40415],[39.01756,-106.40428],[39.02017,-106.40501],[39.02235,-106.40504],[39.02453,-106.40352],[39.02789,-106.40125],[39.03613,-106.39689],[39.04451,-106.39054],[39.04959,-106.3903],[39.06107,-106.38745],[39.07216,-106.3884],[39.07587,-106.39288],[39.08016,-106.38684],[39.08289,-106.38205],[39.08208,-106.38917],[39.08456,-106.3907],[39.09183,-106.39038],[39.10243,-106.39369],[39.10877,-106.39436],[39.11608,-106.38939],[39.12426,-106.39116],[39.13407,-106.3959],[39.13847,-106.39801],[39.14539,-106.39442],[39.14472,-106.38201],[39.14916,-106.37412],[39.1574,-106.36764],[39.16639,-106.36786],[39.1737,-106.36389],[39.18318,-106.36945],[39.19295,-106.37696],[39.1936,-106.36849],[39.20292,-106.3622],[39.21348,-106.36382],[39.22261,-106.38414],[39.22873,-106.39174],[39.23529,-106.38376],[39.23771,-106.3571],[39.24788,-106.3586],[39.24931,-106.36898],[39.25115,-106.36716],[39.25296,-106.35933],[39.2554,-106.35263],[39.26225,-106.3472],[39.26753,-106.34654],[39.27203,-106.34783],[39.27652,-106.3523],[39.27737,-106.36109],[39.27887,-106.36915],[39.27864,-106.3832],[39.28465,-106.38275],[39.28945,-106.37903],[39.29461,-106.3845],[39.29324,-106.37436],[39.28898,-106.3658],[39.28554,-106.35749],[39.27987,-106.34492],[39.26825,-106.34152],[39.26032,-106.34105],[39.24883,-106.34499],[39.23836,-106.34896],[39.24204,-106.3274],[39.24332,-106.30754],[39.24862,-106.29229]],"start":"2026-08-22T04:00","lat":39.24862,"lon":-106.29229}};
    var MI = 1609.344, FT = 3.28084;
    var clamp = function (v, a, b) { a = a === undefined ? 0 : a; b = b === undefined ? 1 : b; return Math.min(b, Math.max(a, v)); };
    var fmt = function (n) { return Math.round(n).toLocaleString('en-US'); };
    var setText = function (el, s) { if (el && el.textContent !== s) el.textContent = s; };
    var setHTML = function (el, s) { if (el && el.__h !== s) { el.__h = s; el.innerHTML = s; } };
    var calm = function () { return matchMedia('(prefers-reduced-motion: reduce)').matches; };
    var is24 = function () { return !!(window.TrailGoatTime && TrailGoatTime.uses24h()); };   // Settings → Clock

    /* =================== 1. The hero readout =================== */
    (function hero() {
        var readout = document.getElementById('hero-read');
        var vid = document.querySelector('.hero-video');
        if (!readout) return;
        var W = DATA.wser, N = W.ele.length, DX = W.distM / (N - 1);
        // The Planner-style grade-adjusted pace with late-race fatigue, scaled to a 27-hour finish.
        var cumT = new Float64Array(N), i;
        for (i = 1; i < N; i++) {
            var g0 = (W.ele[i] - W.ele[i - 1]) / DX;
            var f0 = g0 >= 0 ? 1 + g0 * 4.5 : (g0 > -0.12 ? 1 + g0 * 1.5 : 0.82 + (-g0 - 0.12) * 2);
            cumT[i] = cumT[i - 1] + f0 * (1 + 0.8 * i / (N - 1)) * DX;
        }
        var sc = 27 * 3600 / cumT[N - 1];
        for (i = 0; i < N; i++) cumT[i] *= sc;
        var TOTAL = cumT[N - 1];
        var at = function (arr, m) { var x = clamp(m / DX, 0, N - 1), j = Math.min(N - 2, Math.floor(x)); return arr[j] + (arr[j + 1] - arr[j]) * (x - j); };
        var eleAt = function (m) { return at(W.ele, m); };
        var tAt = function (m) { return at(cumT, m); };
        var gradeAt = function (m) { return (eleAt(m + 500) - eleAt(m - 500)) / 1000; };
        function clock(t) {                                     // Western States starts at 5 AM Saturday
            var abs = 5 * 3600 + t, day = abs >= 86400 ? 'Sun' : 'Sat';
            var s = Math.round(abs % 86400 / 60), h = Math.floor(s / 60) % 24, mm = s % 60, ap = h >= 12 ? 'PM' : 'AM';
            if (is24()) return day + ' ' + String(h).padStart(2, '0') + ':' + String(mm).padStart(2, '0');
            return day + ' ' + (h % 12 || 12) + ':' + String(mm).padStart(2, '0') + ' ' + ap;
        }
        var FPS = 24, OUT_FR = Math.floor(FPS * 60 * 0.74);      // frame 1,065 of 1,440: the headlamp reaches Auburn
        var POSTER_T = (FPS * 16 - 1) / FPS;                     // the poster is frame 384
        var mileAt = function (t) { return W.distM * Math.min(1, Math.max(0, t) * FPS / OUT_FR); };
        var el = {};
        ['mile', 'ele', 'grade', 'carbs', 'next', 'clock'].forEach(function (k) { el[k] = document.getElementById('hr-' + k); });
        var nextCell = el.next && el.next.parentElement, lastNext = null;
        function show(t) {
            var m = mileAt(t), done = t * FPS >= OUT_FR, raceT = done ? TOTAL : tAt(m);
            setText(el.mile, (m / MI).toFixed(1));
            setHTML(el.ele, fmt(eleAt(m) * FT) + '<small>ft</small>');
            var g = done ? 0 : Math.round(gradeAt(m) * 100);
            setText(el.grade, (g > 0 ? '+' : '') + g + '%');
            el.grade.className = g >= 3 ? 'up' : (g <= -3 ? 'down' : '');
            setHTML(el.carbs, fmt(raceT / 3600 * 75) + '<small>g</small>');
            var ni = -1;
            if (!done) for (var a = 0; a < W.aids.length; a++) if (W.aids[a].m > m + 1) { ni = a; break; }
            var key = done ? 'fin' : (ni < 0 ? 'last' : W.aids[ni].n);
            setHTML(el.next, done ? '<span class="fin">Finished · Auburn</span>'
                : ni < 0 ? 'Finish · Auburn <small>in ' + ((W.distM - m) / MI).toFixed(1) + ' mi</small>'
                : W.aids[ni].n + ' <small>in ' + ((W.aids[ni].m - m) / MI).toFixed(1) + ' mi</small>');
            if (lastNext !== null && key !== lastNext && !calm() && nextCell) {
                nextCell.classList.remove('flash'); void nextCell.offsetWidth; nextCell.classList.add('flash');
            }
            lastNext = key;
            setText(el.clock, clock(raceT));
        }
        show(POSTER_T);
        document.addEventListener('tg:clock', function () { lastNext = null; show(vid && !vid.paused ? vid.currentTime : POSTER_T); });
        if (!vid) return;
        // Frame-accurate where the browser offers it; a rAF read of currentTime otherwise.
        if ('requestVideoFrameCallback' in HTMLVideoElement.prototype) {
            // Only a playing film moves the readout: a paused first frame (autoplay refused)
            // would read mile 0, while the poster on screen is frame 384.
            var pump = function (now, meta) { if (!vid.paused) show(meta.mediaTime); vid.requestVideoFrameCallback(pump); };
            vid.requestVideoFrameCallback(pump);
        } else {
            var poll = function () { if (!vid.paused) show(vid.currentTime); requestAnimationFrame(poll); };
            requestAnimationFrame(poll);
        }
        vid.addEventListener('seeked', function () { if (!vid.paused) show(vid.currentTime); });
        vid.addEventListener('pause', function () { if (!vid.currentTime) show(POSTER_T); });
    })();

    /* =================== 2. A plan comes together, round two =================== */
    (function planStory() {
        var stage = document.getElementById('plan-story');
        var TF = window.TGField;
        if (!stage || !TF) return;
        var cv = document.getElementById('ps-canvas'), labs = document.getElementById('ps-labels');
        var steps = Array.prototype.slice.call(stage.querySelectorAll('.ps-step'));
        var L = DATA.lead, tok = TF.tok, mix = TF.mix, sampleArr = TF.sampleArr;
        var N = TF.budget(2400, 2000, 1400), F = null;
        try { F = TF.DotField(cv, N, { size: innerWidth < 640 ? 2.3 : 2.7, lens: 55, jitter: 0.15, burst: 0 }); } catch (e) { console.error(e); }
        if (!F) { stage.classList.add('ps-nogl'); return; }

        // ---- the course, the pace and the sun ----
        var nL = L.ele.length, DXL = L.distM / (nL - 1);
        var lo = Math.min.apply(null, L.ele), hi = Math.max.apply(null, L.ele);
        var eleL = function (m) { return sampleArr(L.ele, m / L.distM); };
        var gradeL = function (m) { return (eleL(m + 450) - eleL(m - 450)) / 900; };
        var cumT = new Float64Array(nL), i;
        for (i = 1; i < nL; i++) {
            var gg = (L.ele[i] - L.ele[i - 1]) / DXL;
            var ff = gg >= 0 ? 1 + gg * 4.5 : (gg > -0.12 ? 1 + gg * 1.5 : 0.82 + (-gg - 0.12) * 2);
            cumT[i] = cumT[i - 1] + ff * (1 + 0.8 * i / (nL - 1)) * DXL;
        }
        var PLAN_H = 25, TOT = PLAN_H * 3600, scl = TOT / cumT[nL - 1];
        for (i = 0; i < nL; i++) cumT[i] *= scl;
        var tL = function (m) { var x = clamp(m / DXL, 0, nL - 1), j = Math.min(nL - 2, Math.floor(x)); return cumT[j] + (cumT[j + 1] - cumT[j]) * (x - j); };
        var parts = L.start.split('T'), ymd = parts[0].split('-').map(Number), hm = parts[1].split(':').map(Number);
        var UTC_OFF = 6;                                          // Colorado is on MDT (UTC-6) in August
        var START = Date.UTC(ymd[0], ymd[1] - 1, ymd[2], hm[0] + UTC_OFF, hm[1]);
        var DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        function clockL(t) {
            var d = new Date(START + t * 1000 - UTC_OFF * 3600000);
            var h = d.getUTCHours(), m = d.getUTCMinutes(), h12 = h % 12 || 12, ap = h >= 12 ? 'PM' : 'AM';
            var mm = String(m).padStart(2, '0');
            if (is24()) return { day: DAYS[d.getUTCDay()], text: String(h).padStart(2, '0') + ':' + mm, short: String(h).padStart(2, '0') + ':00' };
            return { day: DAYS[d.getUTCDay()], text: h12 + ':' + mm + ' ' + ap, short: h12 + ' ' + ap };
        }
        function sunAlt(ms) {                                     // low-precision solar position, good to a fraction of a degree
            var r = Math.PI / 180, dd = (ms - Date.UTC(2000, 0, 1, 12)) / 86400000;
            var g = (357.529 + 0.98560028 * dd) * r, q = 280.459 + 0.98564736 * dd;
            var lam = (q + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * r, eps = (23.439 - 0.00000036 * dd) * r;
            var ra = Math.atan2(Math.cos(eps) * Math.sin(lam), Math.cos(lam)), dec = Math.asin(Math.sin(eps) * Math.sin(lam));
            var gmst = ((18.697374558 + 24.06570982441908 * dd) % 24 + 24) % 24;
            var ha = (gmst * 15 + L.lon) * r - ra;
            return Math.asin(Math.sin(L.lat * r) * Math.sin(dec) + Math.cos(L.lat * r) * Math.cos(dec) * Math.cos(ha)) / r;
        }
        var stops = [0].concat(L.aids.map(function (a) { return a.m; }), [L.distM]);
        var stopName = function (k) { return k >= stops.length - 1 ? 'Finish' : L.aids[k - 1].n; };
        var dS = new Float32Array(N), tS = new Float32Array(N), eS = new Float32Array(N), gS = new Float32Array(N), aS = new Float32Array(N);
        for (i = 0; i < N; i++) {
            var mm0 = (i + 0.5) / N * L.distM; dS[i] = mm0; tS[i] = tL(mm0); eS[i] = eleL(mm0); gS[i] = gradeL(mm0); aS[i] = sunAlt(START + tS[i] * 1000);
        }
        // ---- numbers the captions quote ----
        var half = Math.floor(nL / 2);
        var maxIdx = function (a, from, to) { var b = from; for (var j = from; j < to; j++) if (a[j] > a[b]) b = j; return b; };
        var iPk1 = maxIdx(L.ele, 0, half), iPk2 = maxIdx(L.ele, half, nL);
        var mPk1 = iPk1 * DXL, mPk2 = iPk2 * DXL;
        var aid = function (n) { for (var j = 0; j < L.aids.length; j++) if (L.aids[j].n === n) return L.aids[j]; return null; };
        var twinOut = aid('Twin Lakes Village').m, winfield = aid('Winfield').m;
        var dur = function (s) { var h = Math.floor(s / 3600), m = Math.round((s % 3600) / 60); return h ? h + ' h ' + String(m).padStart(2, '0') + ' min' : m + ' min'; };
        var upT = tL(mPk1) - tL(twinOut), downT = tL(winfield) - tL(mPk1);
        var legT = stops.slice(1).map(function (b, k) { return tL(b) - tL(stops[k]); });
        var legG = legT.map(function (s) { return s / 3600 * 75; }), totG = legG.reduce(function (s, g) { return s + g; }, 0);
        var kMax = legG.indexOf(Math.max.apply(null, legG));
        var unit = Math.max(1, Math.ceil(totG / (N * 0.92)));
        var need = legG.map(function (g) { return Math.round(g / unit); });
        var climbShare = Math.round(Array.prototype.filter.call(gS, function (g) { return g > 0.03; }).length / N * 100);
        var DARK = -6;                                            // civil twilight: below this the trail needs a light
        var iDawn = 0; while (iDawn < N && aS[iDawn] < DARK) iDawn++;
        var iDusk = N - 1; while (iDusk > 0 && aS[iDusk] < DARK) iDusk--;
        var sliceM = Math.round(L.distM / N);
        var raceDay = ymd[2] + ' ' + MONTHS[ymd[1] - 1];
        // ---- the six beats: every dot keeps its slice of trail ----
        var BEATS = [
            { chip: 'Course', stat: function () { return (L.distM / MI).toFixed(1) + ' mi · ' + fmt(N) + ' dots · ' + sliceM + ' m each'; },
              text: function () { return '<b>Get a course.</b> Leadville comes from the catalog: out to Winfield and back over Hope Pass. Each dot is a ' + sliceM + ' m slice of trail. The way out runs on one side of the line, the way back on the other.'; } },
            { chip: 'Profile', stat: function () { return 'Hope Pass ' + fmt(hi * FT) + ' ft · low ' + fmt(lo * FT) + ' ft'; },
              text: function () { return '<b>The profile.</b> The same dots leave the map for distance and elevation. Hope Pass, ' + fmt(hi * FT) + ' ft, is the peak you climb twice.'; } },
            { chip: 'Grade', stat: function () { return climbShare + '% of the course climbs more than 3%'; },
              text: function () { return '<b>Grade.</b> Climbs turn orange and descents blue, the way the Run Planner shades them.'; } },
            { chip: 'Time', stat: function () { var c = clockL(TOT); return 'Finish ' + c.day + ' ' + c.text + ' on a ' + PLAN_H + '-hour plan'; },
              text: function () { return '<b>Pacing.</b> Distance becomes time on a ' + PLAN_H + '-hour plan. Climbs stretch and descents shrink: the climb from Twin Lakes to Hope Pass takes ' + dur(upT) + ', the descent to Winfield ' + dur(downT) + '.'; } },
            { chip: 'Fuel', stat: function () { return fmt(totG) + ' g of carbs · one dot = ' + unit + ' g'; },
              text: function () { return '<b>Fuel.</b> Carbs for every leg at 75 g an hour, ' + (unit === 1 ? 'one dot per gram' : 'one dot per ' + unit + ' g') + '. ' + (kMax === need.length - 1
                  ? 'The last leg, ' + ((stops[stops.length - 1] - stops[stops.length - 2]) / MI).toFixed(1) + ' miles from ' + L.aids[L.aids.length - 1].n + ' to the finish, needs the most: ' + fmt(legG[kMax]) + ' g, because it’s long and it comes when the plan is slowest.'
                  : 'The leg into ' + stopName(kMax + 1) + ' needs the most: ' + fmt(legG[kMax]) + ' g.'); } },
            { chip: 'Night', stat: function () { return 'Dark before ' + clockL(tS[iDawn]).text + ' and after ' + clockL(tS[iDusk]).text; },
              text: function () { return '<b>Night.</b> Back on the map, lit by the clock and the sun’s real position over Leadville on ' + raceDay + '. Miles 0 to ' + (dS[iDawn] / MI).toFixed(0) + ' and ' + (dS[iDusk] / MI).toFixed(0) + ' to the finish run in the dark. That’s where the headlamp goes.'; } },
        ];
        var G = null, targets = [];
        function buildAll() {
            G = { P: { x: F.w * 0.07, y: F.h * 0.16, w: F.w * 0.86, h: F.h * 0.6 }, M: { x: F.w * 0.1, y: F.h * 0.07, w: F.w * 0.8, h: F.h * 0.84 } };
            var P = G.P, rt = TF.routeTable(L.route), proj = TF.projector(L.route, G.M);
            var course = tok('course'), accent = tok('accent'), ink = tok('ink'), inkB = tok('inkBright'), bg = tok('bg');
            var fuel = tok('fuel'), gold = tok('gold'), gear = tok('gear'), gcol = TF.gradeColour();
            var mk = function () { return { pos: new Float32Array(N * 2), col: new Float32Array(N * 3), size: new Float32Array(N).fill(1) }; };
            var setC = function (t, j, c) { t.col[j * 3] = c[0]; t.col[j * 3 + 1] = c[1]; t.col[j * 3 + 2] = c[2]; };
            var yOf = function (e) { return P.y + P.h - (e - lo) / (hi - lo) * P.h; };
            var jit = function () { return (Math.random() - 0.5) * 1.6; };
            var map = mk(), prof = mk(), grade = mk(), time = mk(), fuelT = mk(), night = mk();
            G.mapXY = new Float32Array(N * 2);
            for (var j = 0; j < N; j++) {
                var f = dS[j] / L.distM, p = proj(rt.at(f)), a = proj(rt.at(Math.max(0, f - 0.003))), b = proj(rt.at(Math.min(1, f + 0.003)));
                var dx = b[0] - a[0], dy = b[1] - a[1], len = Math.hypot(dx, dy) || 1, off = 3.4;   // keep to your side of the trail
                var x = p[0] - dy / len * off + jit() * 0.5, y = p[1] + dx / len * off + jit() * 0.5;
                G.mapXY[j * 2] = x; G.mapXY[j * 2 + 1] = y;
                map.pos[j * 2] = x; map.pos[j * 2 + 1] = y; setC(map, j, dS[j] < L.distM / 2 ? course : accent);
                var px = P.x + f * P.w, py = yOf(eS[j]) + jit();
                prof.pos[j * 2] = px; prof.pos[j * 2 + 1] = py; setC(prof, j, mix(course, inkB, (eS[j] - lo) / (hi - lo)));
                grade.pos[j * 2] = px; grade.pos[j * 2 + 1] = py; setC(grade, j, gcol(gS[j]));
                time.pos[j * 2] = P.x + tS[j] / TOT * P.w; time.pos[j * 2 + 1] = py; setC(time, j, gcol(gS[j]));
                night.pos[j * 2] = x; night.pos[j * 2 + 1] = y;
                var al = aS[j];
                if (al < DARK) { setC(night, j, gold); night.size[j] = 1.45; }
                else if (al < -0.833) { setC(night, j, gear); night.size[j] = 1.15; }
                else { setC(night, j, mix(bg, ink, 0.34)); night.size[j] = 0.75; }
            }
            // fuel: one column per leg, one dot per `unit` grams, filled in course order
            var legs = need.length, colW = P.w / legs, cpc = 5, rowsMax = Math.ceil(Math.max.apply(null, need) / cpc);
            var sp = Math.min(colW * 0.74 / cpc, (P.h + F.h * 0.08) / rowsMax), base = P.y + P.h + F.h * 0.06;
            G.fuel = { colW: colW, sp: sp, base: base, cpc: cpc };
            var idx = 0;
            for (var k = 0; k < legs; k++) {
                var x0 = P.x + k * colW + (colW - cpc * sp) / 2, tint = k % 2 ? mix(fuel, inkB, 0.2) : fuel;
                for (var q = 0; q < need[k] && idx < N; q++, idx++) {
                    fuelT.pos[idx * 2] = x0 + (q % cpc + 0.5) * sp; fuelT.pos[idx * 2 + 1] = base - (Math.floor(q / cpc) + 0.5) * sp;
                    setC(fuelT, idx, tint);
                }
            }
            for (; idx < N; idx++) {                                 // the dots this plan doesn't need rest out of sight
                fuelT.pos[idx * 2] = time.pos[idx * 2]; fuelT.pos[idx * 2 + 1] = base; setC(fuelT, idx, fuel); fuelT.size[idx] = 0;
            }
            targets = [map, prof, grade, time, fuelT, night];
        }
        // ---- labels that belong to each beat ----
        function labelsFor(k) {
            var P = G.P, out = [], f2x = function (m) { return P.x + m / L.distM * P.w; }, t2x = function (s) { return P.x + s / TOT * P.w; };
            var yOf = function (e) { return P.y + P.h - (e - lo) / (hi - lo) * P.h; };
            var narrow = F.w < 560;                                  // phone widths: fewer, shorter labels so none collide
            var mapAt = function (m) { var j = clamp(Math.round(m / L.distM * N - 0.5), 0, N - 1); return [G.mapXY[j * 2], G.mapXY[j * 2 + 1]]; };
            if (k === 0 || k === 5) {
                var s = mapAt(0), t = mapAt(twinOut), p = mapAt(mPk1), w = mapAt(winfield);
                out.push({ t: narrow ? 'Leadville' : 'Leadville · start and finish', x: s[0] + 12, y: s[1], c: 'left' });
                out.push({ t: 'Twin Lakes', x: t[0] + 12, y: t[1], c: 'left' });
                out.push({ t: 'Hope Pass · ' + fmt(hi * FT) + ' ft', x: p[0] + 12, y: p[1], c: 'left peak' });
                out.push({ t: narrow ? 'Winfield' : 'Winfield · turn around', x: w[0] - 12, y: w[1], c: 'right' });
                if (k === 5) out.push({ t: '<i class="sw gold"></i>Headlamp on <i class="sw gear"></i>Twilight <i class="sw day"></i>Daylight', x: F.w - 16, y: 26, c: 'right legend' });
            }
            if (k === 1 || k === 2) {
                [0, 25, 50, 75, L.distM / MI].forEach(function (mi, j) { out.push({ t: j === 4 ? mi.toFixed(1) + ' mi' : mi + ' mi', x: f2x(Math.min(L.distM, mi * MI)), y: P.y + P.h + 10, c: 'axis' }); });
                if (f2x(mPk2) - f2x(mPk1) < 150) out.push({ t: 'Hope Pass, out and back', x: (f2x(mPk1) + f2x(mPk2)) / 2, y: Math.min(yOf(L.ele[iPk1]), yOf(L.ele[iPk2])) - 10, c: 'peak' });
                else {
                    out.push({ t: 'Hope Pass, out', x: f2x(mPk1), y: yOf(L.ele[iPk1]) - 10, c: 'peak' });
                    out.push({ t: 'Hope Pass, back', x: f2x(mPk2), y: yOf(L.ele[iPk2]) - 10, c: 'peak' });
                }
                out.push({ t: 'Winfield', x: f2x(winfield), y: yOf(eleL(winfield)) + 22, c: 'axis' });
            }
            if (k === 3) {
                for (var sec = 0; sec <= TOT + 1; sec += (narrow ? 8 : 4) * 3600) out.push({ t: sec === 0 ? (narrow ? clockL(0).short : 'Start ' + clockL(0).short) : clockL(sec).short, x: t2x(sec), y: P.y + P.h + 10, c: 'axis' });
                out.push({ t: narrow ? 'Up ' + dur(upT) : 'Up from Twin Lakes: ' + dur(upT), x: t2x(tL(mPk1)) - 10, y: yOf(L.ele[iPk1]) + 4, c: 'right up' });
                out.push({ t: narrow ? 'Down ' + dur(downT) : 'Down to Winfield: ' + dur(downT), x: t2x(tL(winfield)) + 10, y: yOf(eleL(winfield)) - 4, c: 'left down' });
            }
            if (k === 4) {
                var fu = G.fuel, wide = F.w >= 760, placed = [];
                var order = need.map(function (_, j) { return j; }).sort(function (a, b) { return legG[b] - legG[a]; });   // biggest legs claim a label first
                order.forEach(function (j) { var x = P.x + (j + 0.5) * fu.colW; if (placed.every(function (px) { return Math.abs(px - x) >= 40; })) placed.push(x); });
                need.forEach(function (n, j) {
                    var x = P.x + (j + 0.5) * fu.colW, top = fu.base - Math.ceil(n / fu.cpc) * fu.sp;
                    if (placed.indexOf(x) >= 0) out.push({ t: fmt(legG[j]) + ' g', x: x, y: top - 4, c: 'g' });
                    if (wide) out.push({ t: stopName(j + 1).replace(' Village', '').replace('Turquoise Lake Dam', 'Dam').replace('Carter Summit Mini Aid', 'Carter').replace('Outward Bound', 'Outward Bd'), x: x, y: fu.base + 6, c: 'col' });
                });
            }
            var est = function (t) { return t.replace(/<[^>]+>/g, '').length * 7 + 4; };   // mono label width, near enough
            out.forEach(function (l) {
                if (/\blegend\b/.test(l.c)) return;
                if (/\bleft\b/.test(l.c) && l.x + est(l.t) > F.w - 6) { l.c = l.c.replace('left', 'right'); l.x -= 24; }
                else if (/\bright\b/.test(l.c) && l.x - est(l.t) < 6) { l.c = l.c.replace('right', 'left'); l.x += 24; }
            });
            return out;
        }
        var shownLabels = -1;
        function paintLabels(k) {
            if (k === shownLabels) return; shownLabels = k;
            labs.style.opacity = '0';
            setTimeout(function () {
                labs.innerHTML = labelsFor(k).map(function (l) { return '<span class="ps-lab ' + l.c + '" style="left:' + l.x.toFixed(1) + 'px;top:' + l.y.toFixed(1) + 'px">' + l.t + '</span>'; }).join('');
                labs.style.opacity = '1';
            }, calm() ? 0 : 160);
        }
        function onBeat(k) { steps.forEach(function (st, j) { st.classList.toggle('on', j === k); }); }
        var pairK = -1, pos = 0;
        function showAt(v) {
            v = clamp(v, 0, 5); pos = v;
            var k = Math.min(4, Math.floor(v));
            if (k !== pairK) { F.pair(targets[k], targets[k + 1], { spread: 0.4, swirl: k === 2 ? 10 : 28 }); pairK = k; }
            F.T = v - k; F.auto = null;
            var b = Math.round(v); paintLabels(b); onBeat(b);
            F.render(performance.now());
        }
        function fillSteps() {
            steps.forEach(function (st, k) {
                if (!BEATS[k]) return;
                setHTML(st.querySelector('p'), BEATS[k].text()); setText(st.querySelector('.ps-stat'), BEATS[k].stat());
            });
        }
        buildAll(); fillSteps();
        F.onResize = function () { buildAll(); pairK = -1; shownLabels = -1; showAt(pos); };
        TF.onTheme(F.onResize);
        document.addEventListener('tg:clock', function () { shownLabels = -1; fillSteps(); showAt(pos); });

        // ---- the page's scroll is the timeline ----
        // Where the middle of the screen sits between two steps' centres, eased
        // through the middle 40% so each beat holds while its step is read.
        function progress() {
            var mid = innerHeight * 0.55, cs = steps.map(function (st) { var r = st.getBoundingClientRect(); return r.top + r.height / 2; });
            if (mid <= cs[0]) return 0;
            if (mid >= cs[cs.length - 1]) return cs.length - 1;
            for (var k = 0; k < cs.length - 1; k++) {
                if (mid < cs[k + 1]) {
                    var f = clamp(((mid - cs[k]) / (cs[k + 1] - cs[k]) - 0.3) / 0.4);
                    return k + (f < 0.5 ? 4 * f * f * f : 1 - Math.pow(-2 * f + 2, 3) / 2);
                }
            }
            return 0;
        }
        var inView = false, cur = 0, target = 0, raf = 0;
        var tick = function () {
            raf = 0; target = progress();
            cur = calm() ? target : cur + (target - cur) * 0.2;      // ease toward the scroll so wheel steps don't jerk
            if (Math.abs(target - cur) < 0.002) cur = target;
            showAt(cur);
            if (cur !== target && inView) raf = requestAnimationFrame(tick);
        };
        var kick = function () { if (inView && !raf) raf = requestAnimationFrame(tick); };
        addEventListener('scroll', kick, { passive: true });
        addEventListener('resize', kick);
        if ('IntersectionObserver' in window) {
            new IntersectionObserver(function (es) { inView = es[0].isIntersecting; if (inView) { cur = target = progress(); showAt(cur); } }).observe(stage);
        }
        showAt(0);
    })();

    /* =================== 3. Signal drop: the phone keeps working with no bars =================== */
    (function signalDrop() {
        var phone = document.getElementById('hm-phone'), TF = window.TGField;
        if (!phone) return;
        var W = DATA.wser, N = W.ele.length, DX = W.distM / (N - 1), i;
        var cumT = new Float64Array(N);
        for (i = 1; i < N; i++) {
            var g0 = (W.ele[i] - W.ele[i - 1]) / DX;
            cumT[i] = cumT[i - 1] + (g0 >= 0 ? 1 + g0 * 4.5 : (g0 > -0.12 ? 1 + g0 * 1.5 : 0.82 + (-g0 - 0.12) * 2)) * (1 + 0.8 * i / (N - 1)) * DX;
        }
        var sc = 27 * 3600 / cumT[N - 1];
        var at = function (arr, m) { var x = clamp(m / DX, 0, N - 1), j = Math.min(N - 2, Math.floor(x)); return arr[j] + (arr[j + 1] - arr[j]) * (x - j); };
        var aid = function (n) { for (var j = 0; j < W.aids.length; j++) if (W.aids[j].n === n) return W.aids[j]; return null; };
        var from = aid('Foresthill'), to = aid('Rucky Chucky');
        if (!from || !to) return;
        function clock(t) {
            var abs = 5 * 3600 + t, s = Math.round(abs % 86400 / 60), h = Math.floor(s / 60) % 24, mm = s % 60;
            if (is24()) return String(h).padStart(2, '0') + ':' + String(mm).padStart(2, '0');
            return (h % 12 || 12) + ':' + String(mm).padStart(2, '0') + ' ' + (h >= 12 ? 'PM' : 'AM');
        }
        var $ = function (id) { return document.getElementById(id); };
        var paintMeta = function () { $('ph-meta').textContent = 'mile ' + (to.m / MI).toFixed(1) + ' · ETA ' + clock(at(cumT, to.m) * sc); };
        paintMeta(); document.addEventListener('tg:clock', paintMeta);
        // The profile from mile 55 to 85, the stretch the runner is on.
        var lo = W.distM * 0.55, hi = W.distM * 0.85, sub = [];
        for (var m = lo; m <= hi + 1; m += (hi - lo) / 60) sub.push([m, at(W.ele, m)]);
        var eLo = Math.min.apply(null, sub.map(function (s2) { return s2[1]; })), eHi = Math.max.apply(null, sub.map(function (s2) { return s2[1]; }));
        var X = function (mm) { return (mm - lo) / (hi - lo) * 160; }, Y = function (e) { return 54 - (e - eLo) / (eHi - eLo) * 44; };
        var d = sub.map(function (s2, j) { return (j ? 'L' : 'M') + X(s2[0]).toFixed(1) + ' ' + Y(s2[1]).toFixed(1); }).join('');
        $('ph-line').setAttribute('d', d); $('ph-area').setAttribute('d', d + 'L160 60L0 60Z');
        var dot = $('ph-dot'), bars = phone.querySelectorAll('.ph-bars i'), net = $('ph-net'), toast = $('ph-toast'), time = $('ph-time');
        function setDot(f) { var mm = from.m + (to.m - from.m) * f; dot.setAttribute('cx', X(mm).toFixed(1)); dot.setAttribute('cy', Y(at(W.ele, mm)).toFixed(1)); time.textContent = clock(at(cumT, mm) * sc).replace(/ [AP]M$/, ''); }
        function setBars(n, label) { for (var j = 0; j < bars.length; j++) bars[j].classList.toggle('off', j >= n); setText(net, label); }
        function rest() { setBars(0, 'No service'); toast.classList.add('show'); setDot(0.5); }
        rest();
        if (!TF) return;
        var CYCLE = 9500, t0 = 0;
        var loop = TF.rafLoop(function (now) {
            if (!t0) t0 = now;
            var ms = now - t0, s2 = (ms % CYCLE) / 1000;
            setDot(clamp((ms % 19000) / 19000));
            if (s2 < 1.5) setBars(4, '5G'); else if (s2 < 2) setBars(3, '5G'); else if (s2 < 2.5) setBars(2, 'LTE'); else if (s2 < 3) setBars(1, '3G');
            else if (s2 < 7.6) setBars(0, 'No service'); else setBars(4, '5G');
            toast.classList.toggle('show', s2 >= 3.5 && s2 < 7.2);
        });
        TF.govern(phone, { start: function () { t0 = 0; loop.start(); }, stop: function () { loop.stop(); }, rest: rest });
    })();

    /* =================== 4. Sand signatures on the featured courses =================== */
    (function sand() {
        var TF = window.TGField, cvs = document.querySelectorAll('canvas.hm-sand');
        if (!TF || !cvs.length) return;
        var bounce = function (t) { var n = 7.5625, d = 2.75; if (t < 1 / d) return n * t * t; if (t < 2 / d) return n * (t -= 1.5 / d) * t + 0.75; if (t < 2.5 / d) return n * (t -= 2.25 / d) * t + 0.9375; return n * (t -= 2.625 / d) * t + 0.984375; };
        function job(cv, i) {
            var ele = []; try { ele = JSON.parse(cv.getAttribute('data-ele')) || []; } catch (e) { ele = []; }
            if (ele.length < 3) return null;
            var lo = Math.min.apply(null, ele), hi = Math.max.apply(null, ele), v = ele.map(function (x) { return (x - lo) / ((hi - lo) || 1); });
            var r = cv.getBoundingClientRect(), dp = Math.min(2, devicePixelRatio || 1), w = Math.max(40, r.width), h = Math.max(20, r.height);
            cv.width = Math.round(w * dp); cv.height = Math.round(h * dp);
            var acc = TF.colour(getComputedStyle(cv.parentNode.parentNode).getPropertyValue('--acc')), ink = TF.tok('inkBright'), bg = TF.tok('bg');
            var shades = [TF.css(acc, 0.95), TF.css(TF.mix(acc, ink, 0.3), 0.9), TF.css(TF.mix(acc, bg, 0.35), 0.9)];
            var top = function (x) { return h - 3 - TF.sampleArr(v, x / w) * (h - 8); }, G = [], n = Math.round(w * 2.6);
            for (var k = 0; k < n; k++) {
                var x = Math.random() * w, t = top(x);
                G.push({ x: x, ty: t + Math.pow(Math.random(), 2.2) * (h - t), y0: -4 - Math.random() * h * 0.7,
                    delay: x / w * 650 + Math.random() * 260 + i * 70, dur: 650 + Math.random() * 350, s: k % 3 });
            }
            return { ctx: cv.getContext('2d'), G: G, shades: shades, w: w, h: h, dp: dp };
        }
        function draw(jobs, t) {
            var busy = false;
            jobs.forEach(function (j) {
                if (!j) return;
                j.ctx.setTransform(j.dp, 0, 0, j.dp, 0, 0); j.ctx.clearRect(0, 0, j.w, j.h);
                j.G.forEach(function (g) {
                    var u = t === null ? 1 : clamp((t - g.delay) / g.dur); if (u < 1) busy = true;
                    j.ctx.fillStyle = j.shades[g.s]; j.ctx.fillRect(g.x, g.y0 + (g.ty - g.y0) * bounce(u), 1.7, 1.7);
                });
            });
            return busy;
        }
        var list = document.querySelector('.hm-course-list'), played = false, run = 0;
        function play() {
            var jobs = Array.prototype.map.call(cvs, job), id = ++run;
            if (calm()) { draw(jobs, null); return; }
            var t0 = performance.now();
            var frame = function (now) { if (id !== run) return; if (draw(jobs, now - t0)) requestAnimationFrame(frame); };
            requestAnimationFrame(frame);
        }
        if ('IntersectionObserver' in window && list) {
            new IntersectionObserver(function (es, o) { if (es[0].isIntersecting && !played) { played = true; o.disconnect(); play(); } }, { threshold: 0.2 }).observe(list);
        } else play();
        TF.onTheme(function () { if (played) { var id = ++run; draw(Array.prototype.map.call(cvs, job), null); } });
    })();

    /* =================== 5. Ridgeline: the catalog stacked, flattest at the back =================== */
    (function ridgeline() {
        var fig = document.getElementById('hm-ridge'), host = document.getElementById('hm-ridge-plot'), data = document.getElementById('hm-ridge-data');
        if (!fig || !host || !data) return;
        var rows = [];
        try { rows = JSON.parse(data.textContent).rows || []; } catch (e) { rows = []; }
        if (rows.length < 8) return;
        var n = rows.length, VW = 1000, gap = 13, topPad = 70, X0 = 30, X1 = 970, VH = topPad + n * gap + 14;
        var dens = rows.map(function (r) { return r.gainM / r.distM; }), dmax = Math.max.apply(null, dens);
        var esc = function (t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
        var h = '<svg viewBox="0 0 ' + VW + ' ' + VH + '" role="img" aria-label="Ridgeline of ' + n + ' race profiles from the catalog, flattest at the back">';
        rows.forEach(function (r, k) {
            var base = topPad + k * gap, amp = 8 + 46 * Math.pow(dens[k] / dmax, 0.8), e = r.ele;
            var lo = Math.min.apply(null, e), hi = Math.max.apply(null, e);
            var d = e.map(function (v, j) { return (j ? 'L' : 'M') + (X0 + j / (e.length - 1) * (X1 - X0)).toFixed(1) + ' ' + (base - (v - lo) / ((hi - lo) || 1) * amp).toFixed(1); }).join('');
            h += '<a href="/course/' + esc(r.slug) + '" class="rl" style="--d:' + (k * 28) + 'ms"><title>' + esc(r.name) + '</title>'
                + '<path class="f" d="' + d + 'L' + X1 + ' ' + base + 'L' + X0 + ' ' + base + 'Z"/><path class="l" pathLength="1" d="' + d + '"/></a>';
        });
        host.innerHTML = h + '</svg><div class="hm-ridge-tip" hidden></div>';
        fig.hidden = false;
        var svg = host.querySelector('svg'), tip = host.querySelector('.hm-ridge-tip'), gs = host.querySelectorAll('.rl');
        function pick(e) {
            var r = svg.getBoundingClientRect(), y = (e.clientY - r.top) / r.height * VH;
            var k = clamp(Math.round((y - topPad + 18) / gap), 0, n - 1), row = rows[k];
            for (var j = 0; j < gs.length; j++) gs[j].classList.toggle('on', j === k);
            tip.hidden = false;
            tip.style.left = clamp((e.clientX - r.left) / r.width * 100, 14, 86) + '%';
            tip.style.top = ((topPad + k * gap - 58) / VH * 100) + '%';
            tip.innerHTML = '<b>' + esc(row.name) + '</b><span>' + (row.distM / MI).toFixed(1) + ' mi · ' + fmt(row.gainM * FT) + ' ft · ' + fmt(row.gainM * FT / (row.distM / MI)) + ' ft/mi</span>';
        }
        svg.addEventListener('pointermove', pick);
        svg.addEventListener('pointerleave', function () { tip.hidden = true; for (var j = 0; j < gs.length; j++) gs[j].classList.remove('on'); });
        // Lines draw in, back to front, the first time the plot scrolls into view.
        if (!calm() && 'IntersectionObserver' in window) {
            host.classList.add('primed');
            new IntersectionObserver(function (es, o) { if (es[0].isIntersecting) { o.disconnect(); void host.offsetWidth; host.classList.remove('primed'); } }, { threshold: 0.15 }).observe(host);
        }
    })();
})();
