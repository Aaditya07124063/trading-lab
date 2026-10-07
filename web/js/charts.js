// Canvas charts: sparkline, line/candle chart with crosshair, bars. No library.
// Styled as instruments: thin lines, dotted grid, mono labels, one accent per series.
import { h } from './ui.js';

const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const COL = { get green() { return css('--green'); }, get red() { return css('--red'); }, get blue() { return css('--blue'); },
    get cyan() { return css('--cyan'); }, get magenta() { return css('--magenta'); }, get ink() { return css('--ink-2'); },
    get muted() { return css('--muted'); }, get line() { return css('--line'); }, get amber() { return css('--amber'); } };
export { COL };
const still = () => matchMedia('(prefers-reduced-motion: reduce)').matches || document.documentElement.classList.contains('calm');
const R = 66;                                               // right gutter for the value axis, shared so stacked charts align

function setup(canvas, height) {
    const dpr = window.devicePixelRatio || 1, w = canvas.clientWidth || canvas.parentElement.clientWidth || 300;
    canvas.width = w * dpr; canvas.height = height * dpr; canvas.style.height = height + 'px';
    const g = canvas.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    return [g, w];
}
/** Redraw when the element first gets a size and whenever its width changes. */
function onSize(el, draw) {
    let last = 0;
    new ResizeObserver(() => { const w = el.clientWidth; if (w && w !== last) { last = w; draw(); } }).observe(el);
}
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
/** Short axis label for a YYYY-MM-DD string: day and month, or month and year on long spans. */
function shortDate(s, long) {
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s || '');
    return !m ? s ?? '' : long ? `${MON[m[2] - 1]} ’${m[1].slice(2)}` : `${m[3]} ${MON[m[2] - 1]}`;
}

/** Small trend line. Colour follows first-to-last direction unless given. */
export function spark(values, height = 38, color) {
    const c = h('canvas', { 'aria-hidden': 'true' });
    onSize(c, () => {
        if (!values?.length) return;
        const [g, w] = setup(c, height), lo = Math.min(...values), hi = Math.max(...values), span = hi - lo || 1;
        g.strokeStyle = color || (values.at(-1) >= values[0] ? COL.green : COL.red);
        g.lineWidth = 1.1; g.beginPath();
        values.forEach((v, i) => g[i ? 'lineTo' : 'moveTo'](i / (values.length - 1) * w, height - 2 - (v - lo) / span * (height - 4)));
        g.stroke();
    });
    return c;
}

/** Line chart. opts: {x: labels[], series: [{name, values, color, width, fill, dash}], height, fmt, zero, label,
 *  candles: {open, high, low, close} (drawn instead of the first series when there are few enough bars)} */
export function lineChart(opts) {
    const height = opts.height || 260, fmt = opts.fmt || (v => v.toLocaleString('en-IN', { maximumFractionDigits: 2 }));
    const canvas = h('canvas', { role: 'img', 'aria-label': opts.label || 'Chart: ' + (opts.series.map(s => s.name).filter(Boolean).join(', ') || 'series') }), tip = h('div', { class: 'tip' });
    const legend = h('div', { class: 'legend' }, opts.series.filter(s => s.name).map(s => h('span', {}, h('i', { style: `background:${s.color}` }), s.name)));
    const box = h('div', { class: 'chart' }, opts.series.some(s => s.name) && legend, canvas, tip);
    const cd = opts.candles, n = opts.x.length, candles = cd && n <= 140;
    const all = [...opts.series.flatMap(s => s.values), ...(candles ? [...cd.high, ...cd.low] : [])].filter(v => v != null && !Number.isNaN(v));
    if (!all.length) return h('div', { class: 'state' }, h('b', {}, 'No data to chart'));
    let lo = Math.min(...all), hi = Math.max(...all);
    if (opts.zero) { lo = Math.min(lo, 0); hi = Math.max(hi, 0); }
    const pad = (hi - lo) * 0.07 || 1; lo -= pad; hi += pad;
    const L = 1, T = 10, B = 24, long = n > 1 && (new Date(opts.x[n - 1]) - new Date(opts.x[0])) / 864e5 > 500;
    let W = 0, shown = still() ? 1 : 0;
    const X = i => L + (n > 1 ? i / (n - 1) : 0) * (W - L - R), Y = v => T + (1 - (v - lo) / (hi - lo)) * (height - T - B);
    function draw(hover) {
        const [g, w] = setup(canvas, height); W = w;
        const mono = css('--mono'), muted = COL.muted;
        g.font = '10px ' + mono; g.textBaseline = 'middle'; g.lineWidth = 1;
        g.strokeStyle = 'rgba(255,255,255,.16)'; g.setLineDash([1, 5]);
        for (let k = 0; k <= 4; k++) {                      // dotted grid and value labels
            const v = lo + (hi - lo) * k / 4, y = Math.round(Y(v)) + .5;
            g.beginPath(); g.moveTo(L, y); g.lineTo(W - R, y); g.stroke();
            g.fillStyle = muted; g.fillText(fmt(v), W - R + 10, y);
        }
        g.setLineDash([]); g.textBaseline = 'alphabetic';
        const ticks = Math.max(1, Math.min(6, Math.floor((W - L - R) / 120)));
        for (let k = 0; k <= ticks; k++) {                  // time labels: as many as fit without touching
            const i = Math.round(k * (n - 1) / ticks);
            g.textAlign = k === 0 ? 'left' : k === ticks ? 'right' : 'center';
            g.fillStyle = muted; g.fillText(shortDate(opts.x[i], long).toUpperCase(), X(i), height - 5);
            g.fillStyle = 'rgba(255,255,255,.3)'; g.fillRect(Math.round(X(i)), height - B + 2, 1, 4);
        }
        g.textAlign = 'left';
        g.save(); g.beginPath(); g.rect(0, 0, L + (W - L - R) * shown + 2, height); g.clip();      // draw-in reveal
        opts.series.forEach((s, k) => {
            if (candles && k === 0) {
                const bw = Math.max(1, Math.min(9, (W - L - R) / n * .62));
                for (let i = 0; i < n; i++) {
                    g.fillStyle = g.strokeStyle = cd.close[i] >= cd.open[i] ? COL.green : COL.red;
                    const x = Math.round(X(i)) + .5, y0 = Y(Math.max(cd.open[i], cd.close[i])), y1 = Y(Math.min(cd.open[i], cd.close[i]));
                    g.beginPath(); g.moveTo(x, Y(cd.high[i])); g.lineTo(x, Y(cd.low[i])); g.stroke();
                    g.fillRect(x - bw / 2, y0, bw, Math.max(1, y1 - y0));
                }
                return;
            }
            g.strokeStyle = s.color; g.lineWidth = s.width || 1.25; g.setLineDash(s.dash || []); g.beginPath();
            let first = null, last = null;
            s.values.forEach((v, i) => { if (v == null) return; g[first == null ? 'moveTo' : 'lineTo'](X(i), Y(v)); first ??= i; last = i; });
            if (k === 0) { g.shadowColor = s.color; g.shadowBlur = 7; }
            g.stroke(); g.shadowBlur = 0; g.setLineDash([]);
            if (first != null && (s.fill || (k === 0 && opts.area !== false))) {            // soft area under the primary series
                const base = Y(opts.zero ? 0 : lo);
                g.lineTo(X(last), base); g.lineTo(X(first), base); g.closePath();
                const grad = g.createLinearGradient(0, T, 0, height - B);
                grad.addColorStop(opts.zero ? 1 : 0, s.color); grad.addColorStop(opts.zero ? 0 : 1, 'transparent');
                g.globalAlpha = s.fill ? .22 : .1; g.fillStyle = grad; g.fill(); g.globalAlpha = 1;
            }
        });
        g.restore();
        const s0 = opts.series[0], end = s0.values.findLastIndex(v => v != null);
        if (end >= 0 && shown >= 1) {                       // last-value marker on the axis
            const y = Y(s0.values[end]), text = fmt(s0.values[end]);
            g.fillStyle = s0.color; g.fillRect(X(end) - 2, y - 2, 4, 4);
            g.fillStyle = '#000'; g.fillRect(W - R + 5, y - 8, R - 5, 16);
            g.strokeStyle = s0.color; g.lineWidth = 1; g.strokeRect(W - R + 5.5, y - 7.5, R - 6, 15);
            g.fillStyle = s0.color; g.textBaseline = 'middle'; g.fillText(text, W - R + 10, y + .5);
        }
        if (hover != null) {                                // crosshair
            g.strokeStyle = 'rgba(255,255,255,.5)'; g.lineWidth = 1; g.setLineDash([2, 3]);
            const x = Math.round(X(hover)) + .5, v = (candles ? cd.close : s0.values)[hover];
            g.beginPath(); g.moveTo(x, T); g.lineTo(x, height - B); g.stroke();
            if (v != null) { const y = Math.round(Y(v)) + .5; g.beginPath(); g.moveTo(L, y); g.lineTo(W - R, y); g.stroke(); }
            g.setLineDash([]);
        }
    }
    canvas.addEventListener('mousemove', e => {
        const r = canvas.getBoundingClientRect(), i = Math.max(0, Math.min(n - 1, Math.round((e.clientX - r.left - L) / (W - L - R) * (n - 1))));
        draw(i);
        tip.style.display = 'block';
        tip.textContent = opts.x[i] + '   ' + (candles ? `O ${fmt(cd.open[i])}  H ${fmt(cd.high[i])}  L ${fmt(cd.low[i])}  C ${fmt(cd.close[i])}   ` : '')
            + opts.series.slice(candles ? 1 : 0).map(s => (s.name ? s.name + ' ' : '') + (s.values[i] == null ? '–' : fmt(s.values[i]))).join('   ');
        tip.style.left = Math.max(0, Math.min(X(i) + 12, W - tip.offsetWidth - 4)) + 'px'; tip.style.top = (canvas.offsetTop + 4) + 'px';
    });
    canvas.addEventListener('mouseleave', () => { tip.style.display = 'none'; draw(); });
    onSize(box, () => {
        if (shown >= 1) return draw();
        const t0 = performance.now(), step = t => { shown = Math.min(1, (t - t0) / 520); if (canvas.isConnected) { draw(); if (shown < 1) requestAnimationFrame(step); } };
        requestAnimationFrame(step);
    });
    return box;
}

/** Vertical bars, e.g. volume. colors: one colour or one per bar. The right gutter matches lineChart so the bars sit under the price bars. */
export function bars(values, colors, height = 70, label = 'Volume bars') {
    const c = h('canvas', { role: 'img', 'aria-label': label }), box = h('div', { class: 'chart' }, c);
    onSize(box, () => {
        if (!values?.length) return;
        const [g, w] = setup(c, height), hi = Math.max(...values) || 1, n = values.length, plot = w - 1 - R, bw = Math.max(1, Math.min(9, plot / n * .62));
        values.forEach((v, i) => {
            g.fillStyle = Array.isArray(colors) ? colors[i] : colors || COL.muted;
            const x = 1 + (n > 1 ? i / (n - 1) : 0) * plot, bh = Math.max(v ? 1 : 0, v / hi * (height - 2));
            g.fillRect(Math.round(x - bw / 2), height - bh, bw, bh);
        });
        g.fillStyle = COL.muted; g.font = '10px ' + css('--mono'); g.textBaseline = 'top';
        g.fillText(Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(hi), w - R + 10, 0);
    });
    return box;
}
