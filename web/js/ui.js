// Reusable UI pieces. Every page builds from these so heroes, panels, tables, labels and states look the same.

export function h(tag, attrs, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
        if (v == null || v === false) continue;
        if (k === 'class') el.className = v;
        else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
        else if (k === 'html') el.innerHTML = v;
        else el.setAttribute(k, v === true ? '' : v);
    }
    for (const kid of kids.flat(Infinity)) if (kid != null && kid !== false) el.append(kid.nodeType ? kid : document.createTextNode(kid));
    return el;
}

// ---- data-source labels: never mix real, demo and research values without saying which is which
export const SRC = {
    real: ['REAL', 'From the lab\'s own data files, nothing after the research cut-off'],
    derived: ['DERIVED', 'Computed in the browser from real data files; a display aid, not a research result'],
    research: ['RESEARCH', 'Read from the registered experiment files; not recomputed'],
    demo: ['DEMO DATA', 'Illustrative sample data. No real feed is connected for this module'],
    na: ['NOT AVAILABLE', 'No data source exists for this yet'],
};
export const src = kind => h('span', { class: 'src ' + kind, title: SRC[kind][1] }, SRC[kind][0]);
export const badge = (text, color = '') => h('span', { class: 'badge ' + color }, text);

const TONE = { positive: 'green', negative: 'red', neutral: '', high: 'red', medium: 'amber', low: '' };
export const tone = v => badge(v, TONE[String(v).toLowerCase()] ?? '');
const STATUS = { FROZEN: 'blue', REPRODUCED: 'green', FINAL: 'green', DIAGNOSTIC: 'amber', EXPLORATORY: 'violet', PLANNED: '', SUPERSEDED: '', INVALID: 'red' };
export const statusBadge = s => badge(s, STATUS[s] ?? (String(s).startsWith('REQUIRES') ? 'red' : ''));

// ---- formatting
export const fmt = {
    num: (v, d = 2) => v == null || Number.isNaN(v) ? '–' : Number(v).toLocaleString('en-IN', { minimumFractionDigits: d, maximumFractionDigits: d }),
    int: v => v == null ? '–' : Number(v).toLocaleString('en-IN'),
    pct: (v, d = 2) => v == null || Number.isNaN(v) ? '–' : (v > 0 ? '+' : '') + Number(v).toFixed(d) + '%',
    compact: v => v == null ? '–' : Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(v),
    date: s => s ? new Date(s).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '–',
    time: s => s ? new Date(s).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '–',
    hash: s => s ? s.slice(0, 12) + '…' + s.slice(-6) : '–',
    ist: s => s ? new Date(s).toLocaleString('en-GB', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }).toUpperCase() + ' IST' : '–',
};
/** Full SHA-256 in groups of eight, first group highlighted. */
export const hash = s => s ? h('span', { class: 'hash' }, h('i', {}, s.slice(0, 8)), ' ' + s.slice(8).match(/.{1,8}/g).join(' ')) : h('span', { class: 'muted' }, '–');
export const delta = (v, d = 2, suffix = '%') => h('span', { class: 'num ' + (v > 0 ? 'up' : v < 0 ? 'down' : 'muted') },
    v == null || Number.isNaN(v) ? '–' : (v > 0 ? '+' : '') + Number(v).toFixed(d) + suffix);

// ---- containers
/** Page head: oversized title lines, tiny metadata, optional artwork canvas. opts: {kicker, sub, meta: [[k, v]], art, class, small, body} */
export function hero(lines, o = {}) {
    return h('section', { class: 'hero ' + (o.class || '') }, o.art,
        h('div', { class: 'kicker' }, o.kicker),
        h('h1', { class: 'mega' + (o.small ? ' sm' : ''), 'aria-label': lines.join(' ') }, lines.map(t => h('span', { 'data-t': t, 'aria-hidden': 'true' }, t))),
        o.sub && h('p', { class: 'lede' + (o.subId ? ' id' : '') }, o.sub),
        o.meta && h('dl', { class: 'meta' }, o.meta.filter(Boolean).map(([k, v]) => h('div', {}, h('dt', {}, k), h('dd', {}, v ?? '–')))),
        o.body && h('div', { class: 'body' }, o.body));
}
/** Open panel: a hairline, a label row and the content. opts: {sub, actions, source, class, flush} */
export function card(title, opts = {}, ...body) {
    const head = title && h('header', {}, h('h3', {}, title), opts.sub && h('span', { class: 'muted small' }, opts.sub),
        h('span', { class: 'sp' }), opts.actions, opts.source && src(opts.source));
    return h('section', { class: 'card ' + (opts.class || '') }, head, h('div', { class: 'body' }, body));
}
export const section = (title, ...right) => h('div', { class: 'section' }, h('h2', { class: /\d/.test(title) ? 'id' : '' }, title), right);
/** Large value over a small technical label. size: '', 'l', 'xl', 'word' */
export const stat = (label, value, sub, size = '') => h('div', { class: 'stat ' + size }, h('b', {}, value ?? '–'), h('span', {}, label), sub && h('small', {}, sub));
export const kpis = (items, size) => h('div', { class: 'kpis' }, items.filter(Boolean).map(([label, value, sub]) => stat(label, value, sub, size)));
export const kv = pairs => h('dl', { class: 'kv' }, pairs.filter(p => p).map(([k, v]) => [h('dt', {}, k), h('dd', {}, v ?? '–')]));
/** Specification rows: small label left, value right. */
export const spec = rows => h('div', { class: 'spec' }, rows.filter(Boolean).map(([k, v, mono]) => h('div', {}, h('span', { class: 'lbl' }, k), h('span', { class: 'val' + (mono ? ' mono' : '') }, v ?? '–'))));
/** Three-part status line, e.g. PROTOCOL / FROZEN. items: [label, value, tone] with tone ok | bad | hold | frz */
export const tri = items => h('div', { class: 'tri' }, items.filter(Boolean).map(([k, v, t, title]) => h('div', { class: t || '', title: title || null }, h('span', {}, k), h('b', {}, v))));
export const note = (text, kind = '') => h('div', { class: 'note ' + kind }, text);

// ---- small instruments (DOM only)
/** Row of ticks, one per counted item. parts: [[count, colour, class]] */
export const ticks = parts => h('div', { class: 'ticks', role: 'img', 'aria-label': parts.map(p => `${p[0]} ${p[3] || ''}`).join(', ') },
    parts.flatMap(([n, color, cls]) => Array.from({ length: n }, () => h('i', { class: cls || '', style: `background:${color}` }))));
/** Marker on a ruled line. pos is 0..1. */
export const gauge = (pos, labels) => [h('div', { class: 'gauge' }, h('i', { style: `left:${Math.max(0, Math.min(1, pos)) * 100}%` })),
    labels && h('div', { class: 'gauge-l' }, labels.map(l => h('span', {}, l)))];
export const level = pct => h('span', { class: 'level' }, h('i', { style: `width:${Math.max(0, Math.min(100, pct))}%` }));
/** Bar growing left or right from a centre line. */
export const diverge = (v, max) => { const w = Math.min(1, Math.abs(v) / max) * 50;
    return h('span', { class: 'div' }, h('i', { style: `width:${w}%;${v < 0 ? 'right' : 'left'}:50%;background:var(--${v < 0 ? 'red' : 'green'})` })); };

// ---- states
export const state = {
    loading: (rows = 4) => h('div', {}, Array.from({ length: rows }, (_, i) => h('div', { class: 'skel', style: `width:${88 - i * 13}%` }))),
    empty: (title, hint) => h('div', { class: 'state' }, h('b', {}, title), hint),
    error: e => h('div', { class: 'state err', role: 'alert' }, h('b', {}, 'Could not load this'), String(e?.message || e)),
    /** A known, explained "cannot do this right now" state (not an error dump). */
    hold: (title, ...body) => h('div', { class: 'state hold', role: 'status' }, h('b', {}, title), body),
};
/** Show a loading state in `el`, then the rendered result or an error state. */
export async function load(el, promise, render, rows) {
    el.replaceChildren(state.loading(rows));
    try { el.replaceChildren(...[await render(await promise)].flat().filter(Boolean)); }
    catch (e) { console.warn(e); el.replaceChildren(state.error(e)); }
    return el;
}

// ---- table: cols = [{key, label, r (right align), render(row), sort (value fn or false)}]
export function table(cols, rows, opts = {}) {
    let sortCol = opts.sort ?? null, dir = opts.dir ?? -1;
    const wrap = h('div', { class: opts.scroll === false ? 'tw' : 'scroll' });
    const val = (c, r) => (typeof c.sort === 'function' ? c.sort(r) : r[c.key]);
    const pick = i => { dir = sortCol === i ? -dir : -1; sortCol = i; draw(); };
    const draw = () => {
        const data = sortCol == null ? rows : [...rows].sort((a, b) => {
            const c = cols[sortCol], x = val(c, a), y = val(c, b);
            return (x == null) - (y == null) || (typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y))) * dir;
        });
        wrap.replaceChildren(rows.length ? h('table', { class: opts.class || '' },
            h('thead', {}, h('tr', {}, cols.map((c, i) => h('th', {
                class: (c.r ? 'r ' : '') + (c.sort === false ? '' : 'sort'), scope: 'col', tabindex: c.sort === false ? null : 0,
                'aria-sort': sortCol === i ? (dir > 0 ? 'ascending' : 'descending') : null,
                onclick: c.sort === false ? null : () => pick(i), onkeydown: c.sort === false ? null : e => e.key === 'Enter' && pick(i),
            }, c.label, sortCol === i ? (dir > 0 ? ' ▲' : ' ▼') : '')))),
            h('tbody', {}, data.map(r => h('tr', { class: opts.onRow ? 'click' : '', onclick: opts.onRow ? () => opts.onRow(r) : null, tabindex: opts.onRow ? 0 : null,
                onkeydown: opts.onRow ? e => e.key === 'Enter' && opts.onRow(r) : null },
                cols.map(c => h('td', { class: c.r ? 'r' : '' }, c.render ? c.render(r) : r[c.key] ?? '–')))))
        ) : state.empty(opts.empty || 'Nothing to show', opts.emptyHint));
    };
    draw();
    return wrap;
}

export function tabs(items, onPick, active = items[0]) {
    const bar = h('div', { class: 'tabs', role: 'tablist' });
    const draw = cur => bar.replaceChildren(...items.map(t => h('button', { class: t === cur ? 'on' : '', role: 'tab', 'aria-selected': String(t === cur), onclick: () => { draw(t); onPick(t); } }, t)));
    draw(active);
    return bar;
}
export function seg(items, onPick, active, disabled = {}) {
    const bar = h('div', { class: 'seg' });
    const draw = cur => bar.replaceChildren(...items.map(t => h('button', { class: t === cur ? 'on' : '', 'aria-pressed': String(t === cur), disabled: t in disabled, title: disabled[t] || null,
        onclick: () => { draw(t); onPick(t); } }, t)));
    draw(active);
    return bar;
}
export const field = (label, control) => h('label', { class: 'field' }, label, control);
export const select = (options, value, attrs = {}) => h('select', attrs, options.map(o => {
    const [v, text] = Array.isArray(o) ? o : [o, o];
    return h('option', { value: v, selected: String(v) === String(value) }, text);
}));

// ---- detail drawer and toast
let opener = null;
export function drawer(title, body, source, kicker) {
    const d = document.getElementById('drawer');
    if (!d.classList.contains('open')) opener = document.activeElement;
    d.setAttribute('aria-label', title);
    d.replaceChildren(h('header', {}, h('div', {}, h('div', { class: 'row' }, kicker && h('span', { class: 'lbl' }, kicker), source && src(source)), h('h3', {}, title)),
        h('button', { class: 'btn', onclick: closeDrawer, 'aria-label': 'Close details' }, 'Esc')),
        h('div', { class: 'body stack' }, body));
    d.classList.add('open'); d.focus();
}
export function closeDrawer() {
    const d = document.getElementById('drawer');
    if (!d.classList.contains('open')) return;
    d.classList.remove('open');
    if (opener?.isConnected) opener.focus();
    opener = null;
}
export function toast(text) {
    const t = h('div', { class: 'toast', role: 'status' }, text);
    document.body.append(t);
    setTimeout(() => t.remove(), 2600);
}

// ---- small maths on real price series (display aids, not research results)
export const calc = {
    sma: (a, n) => a.length < n ? null : a.slice(-n).reduce((s, v) => s + v, 0) / n,
    ret: (a, n) => a.length <= n ? null : (a.at(-1) / a.at(-1 - n) - 1) * 100,
    vol: (a, n = 20) => {                                   // annualised realised volatility of daily log returns, %
        if (a.length <= n) return null;
        const r = a.slice(-n - 1).map((v, i, s) => i ? Math.log(v / s[i - 1]) : 0).slice(1), m = r.reduce((s, v) => s + v, 0) / n;
        return Math.sqrt(r.reduce((s, v) => s + (v - m) ** 2, 0) / (n - 1) * 252) * 100;
    },
    rsi: (a, n = 14) => {                                   // Wilder's RSI
        if (a.length <= n) return null;
        let up = 0, dn = 0;
        for (let i = 1; i <= n; i++) { const d = a[i] - a[i - 1]; d > 0 ? up += d : dn -= d; }
        up /= n; dn /= n;
        for (let i = n + 1; i < a.length; i++) { const d = a[i] - a[i - 1]; up = (up * (n - 1) + Math.max(d, 0)) / n; dn = (dn * (n - 1) + Math.max(-d, 0)) / n; }
        return dn === 0 ? 100 : 100 - 100 / (1 + up / dn);
    },
    trend: a => {                                           // price against its 50- and 200-day averages
        const s50 = calc.sma(a, 50), s200 = calc.sma(a, 200), last = a.at(-1);
        if (s50 == null) return 'n/a';
        if (s200 == null) return last > s50 ? 'Above 50D' : 'Below 50D';
        return last > s50 && s50 > s200 ? 'Uptrend' : last < s50 && s50 < s200 ? 'Downtrend' : 'Mixed';
    },
};
export const trendBadge = t => badge(t, t === 'Uptrend' || t === 'Above 50D' ? 'green' : t === 'Downtrend' || t === 'Below 50D' ? 'red' : '');
