// Procedural artwork for page heads. Canvas only, no image assets.
// 'figure': a bust built from market glyphs that breaks into bands and scatters to the right, the "intelligence" inside the lab.
// 'field':  broken horizontal bands of the same glyphs.
// The glyphs are notation and symbols, never prices: this is decoration and carries no data. It is hidden from assistive tech.
import { h } from './ui.js';

const TOKENS = ['NIFTY50', 'SENSEX', 'RELIANCE', 'HDFCBANK', 'INFY', 'TCS', 'NSE', 'BSE', 'O', 'H', 'L', 'C', 'VOL', 'OHLC', 'Σw=1', 'σ²', 'μ', 'Δ', 'β', '∂P/∂t', 'ln(Pₜ/Pₜ₋₁)',
    'E[r]', 'H0', 'H1', 'δ=A−D', 'WML', 't(NW)', 'p<α', 'UNIV-1', 'ORB', '15m', 'T+1', 'SHA256', '0x', '∫', '√', '≠', '→', '//', '::', '01', '10', '0110', 'ff', '9c', 'a6', '7d', 'e1'];
const still = () => matchMedia('(prefers-reduced-motion: reduce)').matches || document.documentElement.classList.contains('calm');

function rng(seed) {
    let s = [...String(seed)].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7) || 1;
    return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
}
/** Is the point inside the bust? u, v in 0..1, v downwards. */
const bust = (u, v) => ((u - .46) / .19) ** 2 + ((v - .27) / .21) ** 2 < 1                    // head
    || (Math.abs(u - .47) < .085 && v > .44 && v < .62)                                      // neck
    || (v > .55 && ((u - .47) / .5) ** 2 + ((v - 1.04) / .48) ** 2 < 1);                     // shoulders

function paint(g, W, H, kind, seed) {
    const r = rng(seed), CW = 6.6, CH = 11, cols = Math.ceil(W / CW), rows = Math.ceil(H / CH);
    const cyan = '#27e0ff', magenta = '#ff3ba7', white = '#eef2f8', warm = '#ffb238';
    g.clearRect(0, 0, W, H); g.font = '9px "JetBrains Mono","SF Mono",ui-monospace,Menlo,monospace'; g.textBaseline = 'top';
    for (let row = 0, left = 0, band = null; row < rows; row++) {
        if (left-- <= 0) {                                  // a new band: a few rows that share one displacement and tint
            const k = r();
            left = Math.floor(r() * 5);
            band = { dx: k < .22 ? (r() - .5) * 70 : 0, tint: k < .1 ? cyan : k < .18 ? magenta : null, drop: k > .95,
                x0: .3 + r() * .45, x1: 0, on: r() < .62 };
            band.x1 = band.x0 + .15 + r() * .6;
        }
        if (band.drop) continue;
        let text = '';
        while (text.length < cols + 12) text += TOKENS[Math.floor(r() * TOKENS.length)] + (r() < .75 ? '' : ' ');
        const v = row / rows, front = .5 + .09 * Math.sin(v * 11 + 1);       // where the figure starts to come apart
        for (let c = 0; c < cols; c++) {
            const ch = text[c], u = c / cols, k = r(), k2 = r();
            if (ch === ' ') continue;
            let a = 0, x = c * CW + band.dx;
            if (kind === 'figure') {
                if (bust(u, v)) {
                    const d = u - front;
                    if (d > 0 && k > Math.exp(-d * 7)) continue;                         // thins out to the right
                    if (d > 0) x += d * k2 * W * .55;                                    // and drifts away
                    a = .34 + .66 * Math.max(0, 1 - ((u - .36) ** 2 * 7 + (v - .24) ** 2 * 1.1)) * (.6 + .4 * k2);
                } else if (k < .016) a = .2;                                             // dust
            } else if (band.on && u > band.x0 && u < band.x1) a = (.3 + .7 * k2) * Math.min(1, (u - band.x0) * 6, (band.x1 - u) * 8) * (.35 + .65 * u);
            else if (k < .01) a = .16;
            if (a <= 0) continue;
            const y = row * CH;
            if (band.tint) {                                // channel split on displaced bands
                g.globalAlpha = a * .7; g.fillStyle = cyan; g.fillText(ch, x - 2, y); g.fillStyle = magenta; g.fillText(ch, x + 2, y);
            }
            g.globalAlpha = a; g.fillStyle = k2 > .985 ? warm : band.tint && k2 > .5 ? band.tint : white;
            g.fillText(ch, x, y);
        }
    }
    g.globalAlpha = 1;
    for (let i = 0; i < (kind === 'figure' ? 9 : 5); i++) {          // broken horizontal bands
        const y = Math.round(r() * H), w = (.08 + r() * .45) * W, x = r() * (W - w * .6);
        g.globalAlpha = .25 + r() * .5; g.fillStyle = [cyan, magenta, white, white][Math.floor(r() * 4)];
        g.fillRect(x, y, w, r() < .25 ? 3 : 1);
    }
    for (let i = 0; i < 4; i++) {                                    // small solid data blocks
        g.globalAlpha = .85; g.fillStyle = i % 2 ? magenta : cyan;
        g.fillRect(Math.round(r() * W * .9), Math.round(r() * H), 6 + r() * 34, 5);
    }
    if (kind === 'figure') {
        g.globalAlpha = .9; g.strokeStyle = cyan; g.lineWidth = 1; g.beginPath();      // one signal line through the noise
        for (let i = 0, y = H * .6; i <= 60; i++) { y += (r() - .52) * 16; g[i ? 'lineTo' : 'moveTo'](i / 60 * W, y); }
        g.stroke();
        g.globalAlpha = .5; g.fillStyle = white;                                       // ruler and crosshair
        for (let y = 0; y < H; y += 22) g.fillRect(W - 9, y, y % 110 ? 4 : 9, 1);
        const cx = Math.round(W * .46) + .5, cy = Math.round(H * .27) + .5;
        g.strokeStyle = 'rgba(255,255,255,.5)'; g.beginPath(); g.moveTo(cx - 16, cy); g.lineTo(cx + 16, cy); g.moveTo(cx, cy - 16); g.lineTo(cx, cy + 16); g.stroke();
    }
    g.globalAlpha = 1;
}

/** Artwork canvas. Sizes itself from CSS, draws once, then glitches a few bands briefly every few seconds. */
export function art(kind = 'figure', seed = 'tl') {
    const c = h('canvas', { class: 'art', 'aria-hidden': 'true' });
    let base = null, W = 0, H = 0, timer = 0;
    const g = c.getContext('2d'), dpr = Math.min(2, window.devicePixelRatio || 1);
    const blit = clip => { g.clearRect(0, 0, c.width, c.height); g.drawImage(base, 0, 0, c.width, c.height * clip, 0, 0, c.width, c.height * clip); };
    function glitch() {
        if (!c.isConnected) return;                         // page changed: stop
        if (!document.hidden && !still()) {
            for (let i = 0; i < 3; i++) {
                const y = Math.random() * c.height, hh = (4 + Math.random() * 26) * dpr, dx = (Math.random() - .5) * 60 * dpr;
                g.clearRect(0, y, c.width, hh); g.drawImage(base, 0, y, c.width, hh, dx, y, c.width, hh);
            }
            setTimeout(() => c.isConnected && blit(1), 120);
        }
        timer = setTimeout(glitch, 3500 + Math.random() * 4500);
    }
    new ResizeObserver(() => {
        const w = c.clientWidth, hh = c.clientHeight;
        if (!w || !hh || (w === W && hh === H)) return;
        const first = !base; W = w; H = hh;
        c.width = w * dpr; c.height = hh * dpr;
        base = Object.assign(document.createElement('canvas'), { width: c.width, height: c.height });
        const bg = base.getContext('2d'); bg.setTransform(dpr, 0, 0, dpr, 0, 0);
        paint(bg, w, hh, kind, seed);
        if (!first || still()) return blit(1);
        const t0 = performance.now(), step = t => { const p = Math.min(1, (t - t0) / 700); blit(p); if (p < 1 && c.isConnected) requestAnimationFrame(step); };
        requestAnimationFrame(step);                        // top-to-bottom reveal, once
        clearTimeout(timer); timer = setTimeout(glitch, 2500);
    }).observe(c);
    return c;
}
