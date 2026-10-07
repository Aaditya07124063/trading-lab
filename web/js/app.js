// Application shell: numbered sidebar, status header, hash router. Pages live in js/pages/.
import { h, state, closeDrawer, fmt } from './ui.js';
import { api, findSymbol } from './api.js';
import { overview, markets, stock, watchlist, regime } from './pages/market.js';
import { newsPage } from './pages/news.js';
import { research, experiments, orb } from './pages/research.js';
import { backtesting } from './pages/backtesting.js';
import { settings } from './pages/settings.js';

if (localStorage.getItem('tl.calm') === '1') document.documentElement.classList.add('calm');

// [route, sidebar label, group heading, page, crumb, tag shown in the sidebar, layer]
const PAGES = [
    ['overview', 'Overview', 'Market intelligence', overview, 'Market overview', '', 'market'],
    ['markets', 'Markets', '', markets, 'Market structure', '', 'market'],
    ['watchlist', 'Watchlist', '', watchlist, 'Watchlist', '', 'market'],
    ['news', 'Intelligence', '', newsPage, 'News & intelligence', 'DEMO', 'market'],
    ['regime', 'Regime', '', regime, 'Market regime', '', 'market'],
    ['research', 'Research', 'Quant research', research, 'Research lab', '', 'research'],
    ['experiments', 'Experiments', '', experiments, 'Experiment archive', '', 'research'],
    ['backtesting', 'Backtest', '', backtesting, 'Backtest engine', '', 'research'],
    ['orb', 'ORB', '', orb, 'ORB v1 protocol', '', 'research'],
    ['settings', 'Settings', 'System', settings, 'Settings', '', 'system'],
];
const LAYER = { market: 'Layer: market intelligence', research: 'Layer: quantitative research · historical files, not live', system: 'Layer: system' };
const no = i => String(i + 1).padStart(2, '0');
const $ = id => document.getElementById(id);

function drawNav(active) {
    $('nav').replaceChildren(...PAGES.flatMap(([route, label, group, , , tag], i) => [
        group && h('div', { class: 'grp' }, group),
        h('a', { class: route === active ? 'on' : '', href: '#/' + route, 'aria-current': route === active ? 'page' : null }, h('i', {}, no(i)), h('span', {}, label), tag && h('em', {}, tag)),
    ]));
}

let first = true;
async function route() {
    closeDrawer();
    const [path, query = ''] = location.hash.replace(/^#\/?/, '').split('?');
    const [name = 'overview', ...rest] = path.split('/').filter(Boolean).map(decodeURIComponent);
    const key = name === 'stock' ? 'watchlist' : name || 'overview', i = PAGES.findIndex(p => p[0] === key), page = PAGES[i];
    const fn = name === 'stock' ? stock : page?.[3], view = $('view');
    drawNav(key);
    document.body.classList.toggle('research', page?.[6] === 'research');
    if (!fn) { view.replaceChildren(state.empty('Page not found', 'Use the sidebar to pick a page.')); return; }
    const crumb = name === 'stock' ? 'Research dossier' : page[4];
    const setTitle = t => { $('crumb').textContent = t; document.title = t + ' — Trading Lab'; };
    setTitle(crumb);
    view.replaceChildren(state.loading(6)); window.scrollTo(0, 0);
    if (!first) view.focus({ preventScroll: true });        // keyboard and screen-reader users land on the new page
    first = false;
    const kicker = [h('b', {}, `${no(i)} / ${name === 'stock' ? 'dossier' : page[1]}`), h('span', {}, LAYER[page[6]])];
    try { await fn(view, { args: rest, query: Object.fromEntries(new URLSearchParams(query)), kicker, setTitle }); }
    catch (e) { console.error(e); view.replaceChildren(state.error(e)); }
}

// ---- top bar
function setupSearch() {
    const q = $('q'), pop = $('qpop');
    let items = [], on = 0;
    const go = it => { if (it) { location.hash = it.href; q.value = ''; pop.hidden = true; q.blur(); } };
    const draw = () => { pop.hidden = !items.length; pop.replaceChildren(...items.map((it, i) => h('div', { class: i === on ? 'on' : '', onmousedown: () => go(it) }, h('b', {}, it.text), h('span', { class: 'muted small' }, it.hint)))); };
    q.addEventListener('input', async () => {
        const t = q.value.trim().toLowerCase();
        if (!t) { items = []; return draw(); }
        const rows = await api.watchlist().catch(() => []);
        items = [...rows.filter(r => r.symbol.toLowerCase().includes(t)).map(r => ({ text: r.symbol, hint: 'instrument', href: '#/stock/' + r.symbol })),
            ...PAGES.filter(p => (p[1] + ' ' + p[4]).toLowerCase().includes(t)).map(p => ({ text: p[1], hint: 'page', href: '#/' + p[0] })),
            { text: `Find “${q.value.trim()}” on NSE/BSE`, hint: 'opens Watchlist search', href: '#/watchlist?q=' + encodeURIComponent(q.value.trim()) }].slice(0, 9);
        on = 0; draw();
    });
    q.addEventListener('keydown', e => {
        if (e.key === 'ArrowDown') { on = Math.min(on + 1, items.length - 1); draw(); e.preventDefault(); }
        else if (e.key === 'ArrowUp') { on = Math.max(on - 1, 0); draw(); e.preventDefault(); }
        else if (e.key === 'Enter') go(items[on]);
        else if (e.key === 'Escape') { q.value = ''; items = []; draw(); q.blur(); }
    });
    q.addEventListener('blur', () => setTimeout(() => { pop.hidden = true; }, 120));
    document.addEventListener('keydown', e => {
        if (e.key === '/' && !/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) { e.preventDefault(); q.focus(); }
        if (e.key === 'Escape') closeDrawer();
    });
}
/** Header status. DATA never says LIVE: there is no feed. It says how old the newest bar in the lab's files is. */
function setupStatus() {
    const set = (id, cls, text, small) => { const el = $(id); el.className = cls; el.children[1].textContent = text; if (small != null) el.children[2].textContent = small; };
    const ist = o => new Date().toLocaleString('en-GB', { timeZone: 'Asia/Kolkata', ...o });
    const tick = () => {
        $('clock').textContent = ist({ hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' IST';
        $('date').textContent = ist({ weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase();
        const day = ist({ weekday: 'short' }), mins = Number(ist({ hour: '2-digit', hour12: false })) % 24 * 60 + Number(ist({ minute: '2-digit' }));
        const open = !/Sat|Sun/.test(day) && mins >= 555 && mins < 930;                // 09:15 to 15:30 IST, by the clock only
        set('st-mkt', open ? 'ok' : 'off', open ? 'NSE HOURS · OPEN' : 'NSE HOURS · CLOSED');
    };
    tick(); setInterval(tick, 1000);
    api.research().then(async r => {
        set('st-sys', 'ok', 'ONLINE', `${r.experiments.length} EXPERIMENTS REGISTERED`);
        const row = await findSymbol('NIFTY50').catch(() => null), last = row && (await api.prices(row.file, 5)).dates.at(-1);
        const days = last ? Math.floor((Date.now() - new Date(last)) / 864e5) : null;
        set('st-data', 'stale', 'NO LIVE FEED', last ? `${days > 4 ? 'STALE · ' : ''}LAST BAR ${fmt.date(last).toUpperCase()}` : `HISTORICAL · CUT-OFF ${fmt.date(r.research_cutoff).toUpperCase()}`);
    }).catch(() => { set('st-sys', 'err', 'OFFLINE', 'BACKEND NOT REACHABLE'); set('st-data', 'err', 'UNAVAILABLE', ''); });
}

setupSearch(); setupStatus();
window.addEventListener('hashchange', route);
route();
