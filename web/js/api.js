// REAL DATA and RESEARCH RESULTS: the only module that talks to the Trading Lab backend.
// Demo data lives in providers.js and never passes through here.

const cache = new Map();

let busy = 0;
const mark = d => document.documentElement.classList.toggle('busy', (busy += d) > 0);   // drives the top-bar activity blink

async function request(path, opts) {
    mark(1);
    try {
        const r = await fetch(path, opts);
        if (!r.ok) {
            let detail = r.statusText;
            try { detail = (await r.json()).detail || detail; } catch { /* not JSON */ }
            throw Object.assign(new Error(detail), { status: r.status });
        }
        return await r.json();
    } finally { mark(-1); }
}
/** GET with an in-memory cache for the life of the page (data is cut at a fixed date, so it does not change). */
function get(path, fresh = false) {
    if (fresh || !cache.has(path)) cache.set(path, request(path).catch(e => { cache.delete(path); throw e; }));
    return cache.get(path);
}
const qs = o => new URLSearchParams(o).toString();

export const api = {
    watchlist: fresh => get('/api/watchlist', fresh),                          // real: last close and change per daily file
    prices: (file, n = 400) => get('/api/prices?' + qs({ file, n })),           // real: daily OHLCV, cut at the research cut-off
    research: () => get('/api/research'),                                      // research: registry, saved results, hash checks
    leaderboard: () => request('/api/leaderboard'),
    search: q => request('/api/search?' + qs({ q })),                          // Yahoo symbol search (needs internet)
    add: symbol => request('/api/add?' + qs({ symbol })),                      // downloads daily history into data/india
    backtest: p => request('/api/backtest?' + qs(p)),                          // runs a daily backtest; the backend logs it as a trial
    saveBacktest: p => request('/api/leaderboard/save?' + qs(p), { method: 'POST' }),
    intradayFiles: () => get('/api/intraday/files'),
    intradayRun: p => request('/api/intraday/run?' + qs(p)),
};

/** Watchlist row for a symbol such as RELIANCE or RELIANCE.NS; null when the lab has no file for it. */
export async function findSymbol(symbol) {
    const s = symbol.replace(/\.(NS|BO)$/i, '').toUpperCase();
    return (await api.watchlist()).find(r => r.symbol.toUpperCase() === s) || null;
}
