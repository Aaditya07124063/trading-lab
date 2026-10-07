// Market intelligence pages: Overview, Markets, Watchlist, Stock detail, Market Regime.
// Real values come from api.js (the lab's data files). Demo values come from providers.js and are labelled.
import { h, hero, card, section, stat, kpis, kv, spec, note, table, state, load, fmt, delta, badge, tone, statusBadge, src, seg, calc, trendBadge, toast, ticks, gauge, level, diverge } from '../ui.js';
import { spark, lineChart, bars, COL } from '../charts.js';
import { art } from '../art.js';
import { api, findSymbol } from '../api.js';
import { news, market } from '../providers.js';
import { newsItem } from './news.js';

const INDEX_FILES = [['NIFTY 50', 'NIFTY50'], ['SENSEX', 'SENSEX']];
const stockLink = s => h('a', { class: 'tag', href: '#/stock/' + s, onclick: e => e.stopPropagation() }, s);
const lastBar = p => `Last bar ${fmt.date(p.dates.at(-1))} · not live`;
const FRAMES = { '1W': 5, '1M': 21, '6M': 126, '1Y': 252, '5Y': 1260 };

/** Real index entries for the files the lab has, demo entries for the rest. */
async function indexCards() {
    const rows = await api.watchlist();
    const real = await Promise.all(INDEX_FILES.map(async ([name, sym]) => {
        const r = rows.find(x => x.symbol === sym);
        if (!r) return { name, missing: true };
        const p = await api.prices(r.file, 60);
        return { name, sym, price: r.price, pct: r.pct, chg: r.chg, series: p.close, sub: lastBar(p), kind: 'real' };
    }));
    return [...real, ...(await market.indices()).map(d => ({ ...d, kind: 'demo', sub: 'Illustrative · not a quote' }))];
}
/** Large index figure: label, value, change, trend line, as-of line. */
const indexStat = (x, size = '') => x.missing
    ? h('div', { class: 'idx ' + size }, h('span', { class: 'lbl' }, x.name, src('na')), h('b', { class: 'muted' }, '–'), h('small', {}, 'No data file · add it from Watchlist'))
    : h(x.sym ? 'a' : 'div', { class: `idx ${size} ${x.kind}`, href: x.sym ? '#/stock/' + x.sym : null },
        h('span', { class: 'lbl' }, x.name, src(x.kind)), h('b', {}, fmt.num(x.price)),
        h('span', { class: 'chg' }, delta(x.pct), x.chg != null && delta(x.chg, 2, '')), spark(x.series, 34), h('small', {}, x.sub));

function breadthBand(b) {
    return h('div', { class: 'band' },
        h('div', {}, h('div', { class: 'lbl', style: 'color:var(--ink);margin-bottom:6px' }, 'Market breadth'), src('demo'), h('div', { class: 'muted small', style: 'margin-top:6px' }, b.universe)),
        ticks([[b.advancing, COL.green, '', 'advancing'], [b.unchanged, COL.muted, 'u', 'unchanged'], [b.declining, COL.red, 'd', 'declining']]),
        kpis([['Advancing', h('span', { class: 'up' }, b.advancing)], ['Declining', h('span', { class: 'down' }, b.declining)], ['Unchanged', b.unchanged], ['A/D ratio', (b.advancing / b.declining).toFixed(2)]]));
}

/** Display-only regime rule on a real daily series: close against its 200-day average, 20-day volatility against its own median. */
function regimeOf(p) {
    const c = p.close, n = c.length, sma = c.map((_, i) => i < 199 ? null : c.slice(i - 199, i + 1).reduce((s, v) => s + v, 0) / 200);
    const vol = c.map((_, i) => i < 20 ? null : calc.vol(c.slice(0, i + 1))), known = vol.filter(v => v != null).sort((x, y) => x - y), med = known[Math.floor(known.length / 2)];
    const label = i => sma[i] == null ? null : (c[i] >= sma[i] ? 'Uptrend' : 'Downtrend') + ' · ' + (vol[i] > med ? 'high vol' : 'low vol');
    const segs = [];
    for (let i = 199; i < n; i++) { const l = label(i), last = segs.at(-1); last && last.l === l ? last.n++ : segs.push({ l, n: 1, from: p.dates[i] }); }
    return { c, n, sma, vol, med, segs, cur: label(n - 1), since: segs.at(-1)?.from };
}
const REGIME_COL = { 'Uptrend · low vol': 'var(--green)', 'Uptrend · high vol': 'var(--amber)', 'Downtrend · low vol': 'var(--blue)', 'Downtrend · high vol': 'var(--red)' };

// ------------------------------------------------------------------ Overview
export async function overview(view, ctx) {
    const [cards, rows, r, b, items, act] = await Promise.all([indexCards(), api.watchlist(), api.research(), market.breadth(), news.list(), market.activity()]);
    const nifty = rows.find(x => x.symbol === 'NIFTY50'), p = nifty && await api.prices(nifty.file, 1500), rg = p && p.close.length > 220 ? regimeOf(p) : null;
    const top = [...items].sort((x, y) => y.impact_score - x.impact_score)[0];
    const stocks = rows.filter(x => !/NIFTY|SENSEX|XAU/.test(x.symbol)).sort((x, y) => y.pct - x.pct);
    const s2 = r.s2_mom, runs = s2 ? Object.values(s2.runs) : [], verified = s2 && runs.every(x => x.verified) && s2.documents.every(d => d.verified);
    const latest = [...r.experiments].sort((x, y) => String(y.executed_at).localeCompare(String(x.executed_at)))[0];
    const [main, ...others] = cards;

    view.replaceChildren(
        hero(['Market', 'Overview'], { kicker: ctx.kicker, class: 'tall', art: art('figure', 'overview'),
            meta: [['Feed', 'None · last bar in the lab\'s files'], ['Research cut-off', fmt.date(r.research_cutoff)], ['Tracked', `${rows.length} instruments`]],
            body: h('div', { class: 'indices' }, indexStat(main, 'xl'), others.slice(0, 2).map(x => indexStat(x))) }),
        breadthBand(b),
        h('div', { class: 'grid' },
            h('div', { class: 'c8 stack' },
                card('NIFTY 50 · one year', { source: p ? 'real' : 'na', sub: p && lastBar(p) },
                    p ? lineChart({ x: p.dates.slice(-252), height: 380, label: 'NIFTY 50 close, last 252 bars, with 200-day average',
                        series: [{ name: 'Close', values: p.close.slice(-252), color: COL.cyan }, rg && { name: '200-day average', values: rg.sma.slice(-252), color: COL.magenta, width: 1 }].filter(Boolean) })
                        : state.empty('No NIFTY 50 file', 'Add it from Watchlist')),
                card('Top movers', { source: 'real', sub: `${stocks.length} tracked stocks · last bar in each file` },
                    stocks.length ? h('div', { class: 'movers' }, stocks.map((x, i) => h('a', { href: '#/stock/' + x.symbol },
                        h('i', {}, String(i + 1).padStart(2, '0')), h('b', {}, x.symbol), h('span', { class: 'muted' }, fmt.num(x.price)), delta(x.pct))))
                        : state.empty('No stock files', 'Add instruments from Watchlist'))),
            h('div', { class: 'c4 stack' },
                card('Market regime', { source: 'derived', actions: h('a', { class: 'info small', href: '#/regime' }, 'Open →') },
                    rg ? [stat('Display rule on NIFTY 50 · not a research conclusion', rg.cur, `in this state since ${fmt.date(rg.since)}`, 'word')] : state.empty('Needs 200+ daily bars')),
                top && card('News signal', { source: 'demo', actions: h('a', { class: 'info small', href: '#/news' }, 'All →') }, newsItem(top, true)),
                card('Research status', { source: 'research', class: 'research', actions: h('a', { class: 'info small', href: '#/research' }, 'Lab →') },
                    spec([
                        ['S2-MOM-v1', s2 ? h('span', { class: 'row' }, badge('Frozen', 'violet'), badge(`${runs.filter(x => x.registered).length}/${runs.length} runs registered`), badge(verified ? 'Hashes match' : 'Hash mismatch', verified ? 'green' : 'red')) : 'not registered'],
                        ['ORB v1', h('span', { class: 'row' }, badge(r.orb.protocol_status, 'violet'), badge(r.orb.final_evaluation_registered ? 'Evaluated' : 'Holdout locked', 'amber'))],
                        ['Latest', latest ? h('span', { class: 'row' }, h('a', { class: 'tag', href: '#/experiments' }, latest.experiment_id), statusBadge(latest.status)) : '–'],
                        ['Registry', `${r.experiments.length} experiments · ${r.logged_trials} logged runs`, true],
                    ])),
                card('Unusual volume', { source: 'demo' },
                    h('table', {}, h('tbody', {}, act.map(a => h('tr', {}, h('td', {}, stockLink(a.symbol)), h('td', { class: 'r' }, a.volume_x.toFixed(1) + '× avg'), h('td', { class: 'r' }, delta(a.move_pct, 1)))))),
                    h('p', { class: 'muted small' }, 'Illustrative rows. A real screen needs daily volume for every index member.')))));
}

// ------------------------------------------------------------------ Markets
export async function markets(view, ctx) {
    const [cards, sectors, b, act, row] = await Promise.all([indexCards(), market.sectors(), market.breadth(), market.activity(), findSymbol('NIFTY50')]);
    const p = row && await api.prices(row.file, 1300), chartBox = h('div', {});
    const draw = f => {
        const n = Math.min(FRAMES[f], p.close.length), cut = a => a.slice(-n), c = cut(p.close), o = cut(p.open);
        chartBox.replaceChildren(
            lineChart({ x: cut(p.dates), height: 380, label: `NIFTY 50, ${f}`, series: [{ values: c, color: COL.cyan }], candles: { open: o, high: cut(p.high), low: cut(p.low), close: c } }),
            h('div', { class: 'lbl', style: 'margin:14px 0 6px' }, 'Volume'),
            bars(cut(p.volume), c.map((v, k) => v >= o[k] ? 'rgba(47,227,140,.55)' : 'rgba(255,85,103,.55)'), 60, 'NIFTY 50 volume'));
    };
    const i = p ? p.close.length - 1 : 0;
    view.replaceChildren(
        hero(['Market', 'Structure'], { kicker: ctx.kicker, art: art('field', 'markets'),
            meta: [['Indices', `${cards.filter(x => x.kind === 'real').length} real · ${cards.filter(x => x.kind === 'demo').length} demo`], ['Sectors', 'Demo · no sector files yet'], ['Feed', 'None · last bar']] }),
        ...(p ? [h('div', { class: 'row between end', style: 'gap:30px 60px;margin-bottom:44px' },
                indexStat(cards[0], 'xl'),
                h('div', { style: 'flex:1;min-width:280px;max-width:620px' }, kpis([['Open', fmt.num(p.open[i])], ['High', fmt.num(p.high[i])], ['Low', fmt.num(p.low[i])], ['Volume', fmt.compact(p.volume[i])]]))),
            card('NIFTY 50', { source: 'real', sub: lastBar(p), actions: seg(Object.keys(FRAMES), draw, '6M') }, chartBox)]
            : [state.empty('No NIFTY 50 file', 'Add it from Watchlist')]),
        section('Index wall'),
        table([
            { label: 'Index', render: x => x.sym ? h('a', { href: '#/stock/' + x.sym }, h('b', {}, x.name)) : h('b', {}, x.name), sort: x => x.name },
            { label: 'Price', r: true, render: x => fmt.num(x.price), sort: x => x.price },
            { label: 'Change', r: true, render: x => x.missing ? '–' : delta(x.price - x.price / (1 + x.pct / 100), 2, ''), sort: x => x.pct },
            { label: 'Change %', r: true, render: x => delta(x.pct), sort: x => x.pct },
            { label: 'Trend (60 bars)', render: x => x.series ? spark(x.series, 22) : '–', sort: false },
            { label: 'As of', render: x => h('span', { class: 'muted small' }, x.sub || '–'), sort: false },
            { label: 'Source', render: x => src(x.missing ? 'na' : x.kind), sort: false },
        ], cards, { scroll: false, class: 'big' }),
        section('Sector performance', src('demo'), h('span', { class: 'muted small' }, 'No sector index files exist in the lab yet')),
        table([
            { label: 'Sector', key: 'name', render: x => h('b', {}, x.name) },
            { label: '1 day', render: x => h('span', { class: 'row nowrap' }, diverge(x.d1, 3), delta(x.d1)), sort: x => x.d1 },
            { label: '1 month', r: true, render: x => delta(x.m1), sort: x => x.m1 },
            { label: 'Relative strength', render: x => h('span', { class: 'row nowrap' }, level(x.rs), h('span', { class: 'num muted' }, x.rs)), sort: x => x.rs },
            { label: 'News sentiment', render: x => tone(x.sentiment), sort: x => x.sentiment },
        ], sectors, { sort: 1, scroll: false }),
        section('Breadth and activity'),
        breadthBand(b),
        h('div', { class: 'grid' },
            card('Unusual activity', { source: 'demo', class: 'c12' }, table([
                { label: 'Stock', render: a => stockLink(a.symbol), sort: a => a.symbol },
                { label: 'Volume vs 20-day', r: true, render: a => a.volume_x.toFixed(1) + '×', sort: a => a.volume_x },
                { label: 'Move', r: true, render: a => delta(a.move_pct, 1), sort: a => a.move_pct },
                { label: 'Note', key: 'note', sort: false },
            ], act, { sort: 1, scroll: false }))));
    if (p) draw('6M');
}

// ------------------------------------------------------------------ Watchlist
const HIDE_KEY = 'tl.watchlist.hidden';
const hidden = () => new Set(JSON.parse(localStorage.getItem(HIDE_KEY) || '[]'));

export async function watchlist(view, ctx) {
    const body = h('div', {}), found = h('div', {});
    const filter = h('input', { class: 'inp', placeholder: 'Filter this list', style: 'width:200px', 'aria-label': 'Filter the watchlist' });
    const find = h('input', { class: 'inp', placeholder: 'Find any NSE/BSE symbol to add', style: 'width:280px', value: ctx.query.q || '', 'aria-label': 'Find an NSE or BSE symbol to add' });
    let kind = 'All', showHidden = false, rows = [];

    async function enrich(fresh) {
        const base = await api.watchlist(fresh), items = await news.list();
        rows = await Promise.all(base.map(async r => {
            const p = await api.prices(r.file, 260).catch(() => null), mine = items.filter(n => n.securities.includes(r.symbol));
            return { ...r, p, volume: p?.volume?.at(-1) ?? null, trend: p ? calc.trend(p.close) : 'n/a', date: p?.dates.at(-1),
                news: mine.length, sentiment: mine[0]?.sentiment, impact: mine[0]?.impact, isIndex: /NIFTY|SENSEX/.test(r.symbol) };
        }));
        draw();
    }
    function draw() {
        const hid = hidden(), t = filter.value.trim().toLowerCase();
        const list = rows.filter(r => (showHidden || !hid.has(r.symbol)) && r.symbol.toLowerCase().includes(t) && (kind === 'All' || (kind === 'Indices') === r.isIndex));
        body.replaceChildren(table([
            { label: 'Instrument', render: r => h('span', {}, h('b', {}, r.symbol), h('div', { class: 'muted small' }, market.reference(r.symbol).name || r.file)), sort: r => r.symbol },
            { label: 'Price', r: true, render: r => fmt.num(r.price), sort: r => r.price },
            { label: 'Change', r: true, render: r => delta(r.pct), sort: r => r.pct },
            { label: 'Volume', r: true, render: r => r.volume ? fmt.compact(r.volume) : h('span', { class: 'muted' }, 'n/a'), sort: r => r.volume },
            { label: 'Trend', render: r => h('div', { class: 'row nowrap' }, r.p && spark(r.p.close.slice(-60), 22), trendBadge(r.trend)), sort: r => r.trend },
            { label: 'As of', render: r => h('span', { class: 'muted small nowrap' }, fmt.date(r.date)), sort: r => r.date },
            { label: 'News', r: true, render: r => r.news || h('span', { class: 'muted' }, '0'), sort: r => r.news },
            { label: 'Sentiment', render: r => r.sentiment ? tone(r.sentiment) : h('span', { class: 'muted' }, '–'), sort: r => r.sentiment },
            { label: 'Impact', render: r => r.impact ? tone(r.impact) : h('span', { class: 'muted' }, '–'), sort: r => r.impact },
            { label: '', sort: false, render: r => h('button', { class: 'btn small', title: 'Hides the row in this browser only. The data file is kept.',
                onclick: e => { e.stopPropagation(); const s = hidden(); s.has(r.symbol) ? s.delete(r.symbol) : s.add(r.symbol); localStorage.setItem(HIDE_KEY, JSON.stringify([...s])); draw(); } }, hidden().has(r.symbol) ? 'Show' : 'Hide') },
        ], list, { class: 'big', onRow: r => { location.hash = '#/stock/' + r.symbol; }, empty: 'No instrument matches', emptyHint: 'Clear the filter or add a symbol above.' }));
    }
    async function search() {
        const q = find.value.trim();
        if (!q) return found.replaceChildren();
        await load(found, api.search(q), list => list.length ? card(`Results for “${q}”`, { class: 'box', sub: 'Yahoo Finance symbol search' }, table([
            { label: 'Symbol', render: x => h('b', {}, x.symbol), sort: x => x.symbol }, { label: 'Name', key: 'name' }, { label: 'Exchange', key: 'exchange' },
            { label: '', sort: false, render: x => h('button', { class: 'btn', onclick: async e => {
                e.target.disabled = true; e.target.textContent = 'Downloading…';
                try { const r = await api.add(x.symbol); if (!r.ok) throw new Error(r.error); toast(`Added ${r.file} (history up to the research cut-off)`); found.replaceChildren(); await enrich(true); }
                catch (err) { toast('Could not add: ' + err.message); e.target.disabled = false; e.target.textContent = 'Add'; }
            } }, 'Add') },
        ], list, { scroll: false })) : state.empty('No NSE/BSE match', 'The search needs an internet connection.'), 2);
    }
    filter.addEventListener('input', draw);
    find.addEventListener('keydown', e => e.key === 'Enter' && search());
    const count = h('span', {}, '…');
    view.replaceChildren(
        hero(['Watch', 'List'], { kicker: ctx.kicker, small: true, art: art('field', 'watchlist'),
            meta: [['Instruments', count], ['Price · change · volume · trend', src('real')], ['News · sentiment · impact', src('demo')]] }),
        h('div', { class: 'row between', style: 'margin-bottom:26px' },
            h('div', { class: 'row' }, filter, seg(['All', 'Stocks', 'Indices'], k => { kind = k; draw(); }, 'All'),
                h('label', { class: 'row muted small' }, h('input', { type: 'checkbox', onchange: e => { showHidden = e.target.checked; draw(); } }), 'show hidden')),
            h('div', { class: 'row' }, find, h('button', { class: 'btn', onclick: search }, 'Search'))),
        found, body);
    body.replaceChildren(state.loading(6));
    await enrich();
    count.textContent = `${rows.length} with a daily file`;
    if (ctx.query.q) search();
}

// ------------------------------------------------------------------ Stock detail: a research dossier
export async function stock(view, ctx) {
    const symbol = (ctx.args[0] || '').replace(/\.(NS|BO)$/i, '').toUpperCase();
    const row = symbol && await findSymbol(symbol);
    if (!row) {
        view.replaceChildren(hero([symbol || 'Stock'], { kicker: ctx.kicker, small: true }), state.empty(`The lab has no data file for ${symbol || 'this symbol'}`,
            h('span', {}, 'Add it from the ', h('a', { class: 'info', href: '#/watchlist?q=' + encodeURIComponent(symbol) }, 'Watchlist search'), ' to download its daily history.')));
        return;
    }
    const [p, items] = await Promise.all([api.prices(row.file, 1300), news.list({ symbol })]);
    const ref = market.reference(symbol), c = p.close, i = c.length - 1;
    const unit = /NIFTY|SENSEX/.test(symbol) ? '' : symbol === 'XAUUSD' ? '$' : '₹';
    ctx.setTitle('Dossier · ' + symbol);
    const chartBox = h('div', {}), hasVol = p.volume?.some(v => v > 0);
    const drawChart = f => {
        const n = Math.min(FRAMES[f], c.length), cut = a => a.slice(-n), v = cut(c), open = cut(p.open);
        chartBox.replaceChildren(...[
            lineChart({ x: cut(p.dates), height: 400, label: `${symbol} price, ${f}`, series: [{ values: v, color: COL.cyan }], candles: { open, high: cut(p.high), low: cut(p.low), close: v } }),
            hasVol && h('div', { class: 'lbl', style: 'margin:14px 0 6px' }, 'Volume'),
            hasVol && bars(cut(p.volume), v.map((cl, k) => cl >= open[k] ? 'rgba(47,227,140,.55)' : 'rgba(255,85,103,.55)'), 64, `${symbol} volume`),
        ].filter(Boolean));
    };
    const rsi = calc.rsi(c.slice(-250)), vol = calc.vol(c), mom = calc.ret(c, 126), trend = calc.trend(c);
    const lo52 = Math.min(...p.low.slice(-252)), hi52 = Math.max(...p.high.slice(-252)), avgVol = hasVol ? calc.sma(p.volume, 20) : null;
    view.replaceChildren(
        hero([symbol], { kicker: ctx.kicker, art: art('field', symbol), sub: ref.name || row.file, subId: true,
            meta: [['File', row.file], ['Last bar', fmt.date(p.dates[i])], ['Bars loaded', fmt.int(c.length)], ['Nothing after', fmt.date(p.cutoff)], ['History', `${row.years} years`], ['Status', 'Not a live quote']],
            body: h('div', { class: 'row between end' },
                h('div', { class: 'idx xl' }, h('span', { class: 'lbl' }, 'Last close', src('real')), h('b', {}, unit + fmt.num(row.price)), h('span', { class: 'chg' }, delta(row.pct), delta(row.chg, 2, ''))),
                h('a', { class: 'btn', href: '#/backtesting?file=' + encodeURIComponent(row.file) }, 'Backtest this instrument →')) }),
        card('Price', { source: 'real', actions: seg(['1D', ...Object.keys(FRAMES)], drawChart, '1Y', { '1D': 'Needs an intraday bars endpoint, which does not exist yet' }) }, chartBox),
        h('div', { class: 'grid' },
            card('Price', { class: 'c3', source: 'real' }, kpis([['Open', fmt.num(p.open[i])], ['High', fmt.num(p.high[i])], ['Low', fmt.num(p.low[i])]]),
                h('div', { style: 'margin-top:22px' }, gauge((row.price - lo52) / (hi52 - lo52 || 1), [fmt.num(lo52, 0), '52-week range', fmt.num(hi52, 0)]))),
            card('Volume', { class: 'c3', source: hasVol ? 'real' : 'na' }, hasVol
                ? kpis([['Last bar', fmt.compact(p.volume[i])], ['20-day average', fmt.compact(avgVol)], ['vs average', avgVol ? (p.volume[i] / avgVol).toFixed(2) + '×' : '–']])
                : h('p', { class: 'muted small' }, 'This file has no volume column.')),
            card('Momentum', { class: 'c3', source: 'derived' }, kpis([['6 months', delta(mom)], ['RSI (14)', rsi == null ? '–' : h('span', { class: rsi > 70 || rsi < 30 ? 'warn' : '' }, rsi.toFixed(1))], ['Trend', trendBadge(trend)]]),
                rsi != null && h('div', { style: 'margin-top:22px' }, gauge(rsi / 100, ['0', 'RSI', '100']))),
            card('Volatility', { class: 'c3', source: 'derived' }, kpis([['20-day, annualised', vol == null ? '–' : vol.toFixed(1) + '%'], ['50-day average', fmt.num(calc.sma(c, 50))], ['200-day average', fmt.num(calc.sma(c, 200))]]))),
        h('p', { class: 'muted small', style: 'margin-top:18px' }, 'Derived blocks are standard indicators computed in the browser from the real closes. They are display aids, not strategy signals and not research results.'),
        h('div', { class: 'grid' },
            card('News', { class: 'c8', source: 'demo' }, items.length ? items.map(n => newsItem(n))
                : state.empty('No demo items mention this symbol', 'When a timestamped news source is connected, company events will appear here.')),
            card('Market context', { class: 'c4' }, kv([
                ['Sector', h('span', {}, ref.sector || 'unknown', ' ', h('span', { class: 'muted small' }, '(static reference)'))],
                ['Index membership', h('span', { class: 'muted' }, 'not available (needs a point-in-time index list)')],
                ['Market cap', h('span', { class: 'muted' }, 'not available (no fundamentals source)')],
                ['Market regime', h('a', { class: 'info', href: '#/regime' }, 'See Market Regime')],
                ['Exchange', row.exchange === 'CSV' ? 'NSE (historical file)' : row.exchange],
            ]))));
    drawChart('1Y');
}

// ------------------------------------------------------------------ Market Regime
export async function regime(view, ctx) {
    const row = await findSymbol('NIFTY50');
    if (!row) { view.replaceChildren(hero(['Market', 'Regime'], { kicker: ctx.kicker }), state.empty('No NIFTY 50 file', 'The regime view needs data/india/NIFTY50d1.csv.')); return; }
    const [p, b] = await Promise.all([api.prices(row.file, 1500), market.breadth()]);
    const { c, n, sma, vol, med, segs, cur, since } = regimeOf(p);
    const total = n - 199, share = l => (segs.filter(s => s.l === l).reduce((s, x) => s + x.n, 0) / total * 100).toFixed(0) + '%';
    const x = p.dates.slice(199), dist = (c.at(-1) / sma.at(-1) - 1) * 100, vnow = vol.at(-1), vmax = Math.max(...vol.filter(v => v != null));
    view.replaceChildren(
        hero(['Market', 'Regime'], { kicker: ctx.kicker, art: art('field', 'regime'),
            meta: [['As of', fmt.date(p.dates.at(-1))], ['In this state since', fmt.date(since)], ['Sample', `${fmt.date(x[0])} → ${fmt.date(x.at(-1))}`], ['Input', 'NIFTY 50 daily file']],
            body: [h('div', { class: 'row', style: 'margin-bottom:14px' }, h('span', { class: 'stamp derived' }, 'Derived · display rule'), h('span', { class: 'muted small' }, 'not a registered research conclusion')),
                stat('Current regime', cur, null, 'word')] }),
        note('This view applies a simple display rule to the real NIFTY 50 file: price against its 200-day average, and 20-day volatility against its own median. '
            + 'It is not the regime definition of any registered study (ORB v1 §6 regime labels are reporting-only and are not shown or recomputed here).', 'info'),
        h('div', { class: 'grid', style: 'margin-top:44px' },
            card('Trend', { class: 'c4', source: 'derived' }, stat('Close vs 200-day average', delta(dist), `${fmt.num(c.at(-1))} against ${fmt.num(sma.at(-1))}`, 'l'),
                gauge((dist + 15) / 30, ['−15%', 'average', '+15%'])),
            card('Volatility', { class: 'c4', source: 'derived' }, stat('20-day realised, annualised', vnow.toFixed(1) + '%', `sample median ${med.toFixed(1)}% · ${vnow > med ? 'above' : 'below'} median`, 'l'),
                gauge(vnow / vmax, ['0', 'median ' + med.toFixed(0) + '%', vmax.toFixed(0) + '%'])),
            card('Breadth', { class: 'c4', source: 'demo' }, stat('Advance / decline ratio', (b.advancing / b.declining).toFixed(2), `${b.advancing} up · ${b.declining} down · ${b.unchanged} flat`, 'l'),
                h('div', { style: 'margin-top:12px' }, ticks([[b.advancing, COL.green, '', 'advancing'], [b.unchanged, COL.muted, 'u', 'unchanged'], [b.declining, COL.red, 'd', 'declining']])))),
        h('div', { class: 'grid' },
            card('Regime tape', { class: 'c12', source: 'derived', sub: `${fmt.date(x[0])} to ${fmt.date(x.at(-1))}` },
                h('div', { class: 'regimebar', role: 'img', 'aria-label': 'Regime by session over the sample' }, segs.map(s => h('i', { style: `flex:${s.n};background:${REGIME_COL[s.l]}`, title: `${s.l} from ${s.from} (${s.n} sessions)` }))),
                h('div', { class: 'row', style: 'margin-top:14px;gap:8px 26px' }, Object.entries(REGIME_COL).map(([l, col]) => h('span', { class: 'lbl' }, h('i', { class: 'swatch', style: `background:${col}` }), `${l} ${share(l)}`)))),
            card('NIFTY 50 trend', { class: 'c12', source: 'real' }, lineChart({ x, height: 320, series: [{ name: 'Close', values: c.slice(199), color: COL.cyan }, { name: '200-day average', values: sma.slice(199), color: COL.magenta, width: 1 }] })),
            card('Volatility', { class: 'c12', source: 'derived', sub: '20-day realised, annualised' },
                lineChart({ x, height: 200, fmt: v => v.toFixed(1) + '%', series: [{ name: 'Volatility', values: vol.slice(199), color: COL.amber }, { name: 'Median', values: x.map(() => med), color: COL.ink, width: 1, dash: [3, 4] }] }))));
}
