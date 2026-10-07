// DEMO DATA providers. Nothing here is real and nothing here is a research result.
//
// Each provider is a small class with async methods. To connect a real source later, write a class
// with the same methods (for example RealNewsProvider with list() and get()) and change the one
// line at the bottom that creates the instance. No page needs to change.
//
// Every value a page takes from this file must be shown with the DEMO DATA label (ui.js: src('demo')).

/** Repeatable pseudo-random numbers, so demo charts look the same on every load. */
function rng(seed) {
    let s = [...String(seed)].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7) || 1;
    return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;
}
function walk(seed, n, start, vol = 0.008, drift = 0.0004) {
    const r = rng(seed), out = [start];
    for (let i = 1; i < n; i++) out.push(out[i - 1] * (1 + drift + (r() - 0.5) * 2 * vol));
    return out.map(v => Math.round(v * 100) / 100);
}

export class MockNewsProvider {
    isDemo = true;
    label = 'Demo feed (no news source connected)';
    #items;
    async #load() { return this.#items ??= (await (await fetch('mock/news.json')).json()).items; }
    /** filter: {category, symbol, sector}. Newest first. */
    async list(filter = {}) {
        return (await this.#load()).filter(n =>
            (!filter.category || filter.category === 'All' || n.category === filter.category) &&
            (!filter.symbol || n.securities.includes(filter.symbol)) &&
            (!filter.sector || n.sectors.includes(filter.sector))
        ).sort((a, b) => b.published.localeCompare(a.published));
    }
    async get(id) { return (await this.#load()).find(n => n.id === id) || null; }
    categories() { return ['All', 'India', 'Markets', 'Stocks', 'Economy', 'Policy', 'Global']; }
}

const DEMO_INDICES = [['BANK NIFTY', 'banknifty', 52000], ['NIFTY IT', 'niftyit', 38000], ['NIFTY AUTO', 'niftyauto', 24000]];
const SECTORS = ['Banks', 'IT', 'Energy', 'Auto', 'FMCG', 'Pharma', 'Metals', 'Realty', 'Infrastructure', 'Financial Services'];
const SECTOR_OF = { RELIANCE: 'Energy', TCS: 'IT', INFY: 'IT', HDFCBANK: 'Banks', NIFTY50: 'Index', SENSEX: 'Index', NIFTY_10Y: 'Index', XAUUSD: 'Commodity' };
const NAME_OF = { RELIANCE: 'Reliance Industries', TCS: 'Tata Consultancy Services', INFY: 'Infosys', HDFCBANK: 'HDFC Bank',
    NIFTY50: 'NIFTY 50 index', SENSEX: 'S&P BSE SENSEX index', NIFTY_10Y: 'NIFTY 50 index (10-year file)', XAUUSD: 'Gold spot (USD)' };

export class MockMarketProvider {
    isDemo = true;
    /** Demo index cards for indices the lab has no data file for. */
    async indices() {
        return DEMO_INDICES.map(([name, seed, start]) => {
            const series = walk(seed, 60, start);
            return { name, price: series.at(-1), pct: (series.at(-1) / series.at(-2) - 1) * 100, series };
        });
    }
    async sectors() {
        return SECTORS.map(name => {
            const r = rng(name);
            return { name, d1: (r() - 0.45) * 3, m1: (r() - 0.4) * 12, rs: Math.round(30 + r() * 65), sentiment: ['Positive', 'Neutral', 'Negative'][Math.floor(r() * 3)] };
        });
    }
    async breadth() { return { advancing: 31, declining: 16, unchanged: 3, universe: 'NIFTY 50 (demo counts)' }; }
    async sentiment() { return { score: 0.28, label: 'Positive', basis: 'Demo value. A real score needs a timestamped news source.' }; }
    async activity() {
        return ['RELIANCE', 'INFY', 'HDFCBANK', 'TCS'].map(symbol => {
            const r = rng('act' + symbol);
            return { symbol, volume_x: 1.4 + r() * 2.2, move_pct: (r() - 0.5) * 6, note: ['Volume above 20-day average', 'Large block trade', 'Gap at open'][Math.floor(r() * 3)] };
        });
    }
    /** Static reference labels (sector, company name). Factual, but hand-typed for the handful of symbols the lab tracks. */
    reference(symbol) { return { sector: SECTOR_OF[symbol] || null, name: NAME_OF[symbol] || null }; }
}

export const news = new MockNewsProvider();          // swap for a RealNewsProvider with list() and get()
export const market = new MockMarketProvider();      // swap for a RealMarketProvider with the same methods
