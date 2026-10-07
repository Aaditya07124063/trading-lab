// Backtest engine: the existing daily crossover backtester, the leaderboard and the intraday ORB explorer, as a research console.
// It calls the existing endpoints unchanged. These runs are EXPLORATORY and are logged by the backend as trials.
import { h, hero, card, section, stat, kpis, note, table, state, load, fmt, delta, badge, src, tabs, select, toast } from '../ui.js';
import { lineChart, COL } from '../charts.js';
import { art } from '../art.js';
import { api } from '../api.js';

const rs = v => v == null ? '–' : '₹' + Math.round(v).toLocaleString('en-IN');
const drawdown = eq => { let peak = -Infinity; return eq.map(v => { peak = Math.max(peak, v); return (v / peak - 1) * 100; }); };
/** One console line: small label, control. */
const line = (label, control) => h('label', {}, h('span', { class: 'lbl' }, label), control);
/** Console layout: parameters on the left, output on the right. */
const consoleGrid = (title, sub, lines, actions, hint, out) => h('div', { class: 'grid' },
    card(title, { class: 'c4 box research', sub }, h('div', { class: 'spec' }, lines), h('div', { class: 'row', style: 'margin-top:22px' }, actions), hint && h('p', { class: 'muted small' }, hint)),
    h('div', { class: 'c8' }, out));
const WARNING = 'Exploratory backtest on historical data. It is not a registered study, not out-of-sample evidence and not a forecast of future returns. Every run is logged in the trials registry.';

// ------------------------------------------------------------------ daily strategies
async function daily(box, query) {
    const files = await api.watchlist();
    if (!files.length) { box.replaceChildren(state.empty('No daily data files', 'Add an instrument from Watchlist first.')); return; }
    const file = select(files.map(f => [f.file, `${f.symbol}  (${f.years}y)`]), query.file || 'NIFTY_10Y.csv');
    const kind = select([['ema', 'EMA crossover'], ['sma', 'SMA crossover']], 'ema');
    const num = (v, min, max) => h('input', { type: 'number', value: v, min, max });
    const fast = num(20, 2), slow = num(50, 3), trail = num(0, 0, 50);
    const out = h('div', { class: 'stack' }), board = h('div', {});
    const run = h('button', { class: 'btn primary' }, 'Run experiment'), save = h('button', { class: 'btn', disabled: true, title: 'Re-runs this experiment and saves it to the leaderboard file' }, 'Save to leaderboard');
    let last = null;
    const params = () => ({ file: file.value, kind: kind.value, fast: fast.value, slow: slow.value, trailing: trail.value });
    const loadBoard = () => load(board, api.leaderboard(), rows => table([
        { label: 'Experiment', render: r => h('b', {}, r.name), sort: r => r.name }, { label: 'Return', r: true, render: r => delta(r.return_pct, 1), sort: r => r.return_pct },
        { label: 'Buy & hold', r: true, render: r => delta(r.bh_pct, 1), sort: r => r.bh_pct }, { label: 'Margin', r: true, render: r => delta(r.margin, 1, ' pts'), sort: r => r.margin },
        { label: 'CAGR', r: true, render: r => fmt.num(r.cagr) + '%', sort: r => r.cagr }, { label: 'Sharpe', r: true, key: 'sharpe' },
        { label: 'Max DD', r: true, render: r => fmt.num(r.max_dd, 1) + '%', sort: r => r.max_dd }, { label: 'Trades', r: true, key: 'trades' },
        { label: 'Verdict', render: r => h('span', { class: 'small' }, r.verdict), sort: false }, { label: 'Registry status', render: r => r.status ? badge(r.status, 'amber') : h('span', { class: 'muted' }, '–'), sort: false },
    ], rows, { sort: 3, empty: 'Leaderboard is empty', emptyHint: 'Run a backtest and save it.' }), 3);

    run.onclick = async () => {
        run.disabled = true; save.disabled = true;
        await load(out, api.backtest(params()), d => {
            last = params(); save.disabled = false;
            const m = d.metrics, dd = drawdown(d.equity);
            return [
                h('div', { class: 'kpis' },
                    stat('Return', delta(m.return_pct, 1), `buy & hold ${fmt.pct(m.bh_pct, 1)}`, 'l'), stat('Sharpe', m.sharpe, `buy & hold ${m.bh_sharpe}`, 'l'),
                    stat('Drawdown', fmt.num(m.max_dd, 1) + '%', `buy & hold ${fmt.num(m.bh_dd, 1)}%`, 'l')),
                kpis([['CAGR', fmt.num(m.cagr) + '%', `B&H ${fmt.num(m.bh_cagr)}%`], ['Trades', m.trades, `win rate ${m.win_rate}%`], ['Exposure', m.exposure_pct + '%', 'time in market'],
                    ['Turnover', h('span', { class: 'muted' }, 'n/a'), 'not returned by the API'], ['Volatility', h('span', { class: 'muted' }, 'n/a'), 'not returned by the API']]),
                note(`${m.verdict}. ${WARNING}`),
                h('div', { class: 'grid' },
                    card('Equity curve', { class: 'c12', source: 'real', sub: `${m.name} · ${d.start} to ${d.end} · ${fmt.int(d.candles)} bars` },
                        lineChart({ x: d.dates, height: 300, fmt: v => '₹' + Math.round(v / 1000) + 'k', series: [{ name: 'Strategy', values: d.equity, color: COL.cyan }, { name: 'Buy & hold', values: d.bh, color: COL.magenta, width: 1 }] })),
                    card('Drawdown', { class: 'c12', source: 'real', sub: 'strategy, from sampled equity' },
                        lineChart({ x: d.dates, height: 170, zero: true, fmt: v => v.toFixed(0) + '%', series: [{ values: dd, color: COL.red, fill: true }] })),
                    card('Trades', { class: 'c12', sub: `last ${d.trades.length} of ${m.trades}` }, table([
                        { label: 'Entry', key: 'entry_date' }, { label: 'Entry price', r: true, render: t => fmt.num(t.entry, 1), sort: t => t.entry }, { label: 'Exit', key: 'exit_date' },
                        { label: 'P&L', r: true, render: t => delta(t.pnl_pct, 1), sort: t => t.pnl_pct }, { label: 'Exit reason', key: 'reason' }], [...d.trades].reverse(), { scroll: false })))];
        }, 5);
        run.disabled = false;
    };
    save.onclick = async () => {
        save.disabled = true;
        try { const r = await api.saveBacktest(last); toast('Saved: ' + r.name); loadBoard(); } catch (e) { toast('Could not save: ' + e.message); save.disabled = false; }
    };
    box.replaceChildren(
        consoleGrid('Parameters', 'uses /api/backtest unchanged', [
            line('Universe', file), line('Strategy', kind), line('Fast period', fast), line('Slow period', slow), line('Trailing stop %', trail),
            line('Period', h('input', { disabled: true, value: 'full history (fixed)' })), line('Cost model', h('input', { disabled: true, value: '0.1% per side (fixed)' }))],
            [run, save], 'Fills at the next day\'s open · no look-ahead · dividends excluded · data cut at the research cut-off. Period and costs are fixed by the engine and cannot be changed here.', out),
        section('Leaderboard', h('span', { class: 'muted small' }, 'saved exploratory runs (results/leaderboard.csv)'), src('real')),
        board);
    out.replaceChildren(state.empty('Awaiting run', 'Set the parameters and press Run experiment. Each run is logged as a trial.'));
    loadBoard();
}

// ------------------------------------------------------------------ intraday ORB explorer (not ORB v1)
async function intraday(box) {
    const out = h('div', { class: 'stack' }), all = await api.intradayFiles(), files = all.filter(f => f.ok);
    if (!files.length) { box.replaceChildren(state.empty('No usable intraday files')); return; }
    const file = select(files.map(f => [f.file, `${f.symbol} ${f.timeframe_min}m · ${f.sessions} sessions`]), 'RELIANCEm15.csv');
    const range = select([[15, '15 min'], [30, '30 min'], [45, '45 min'], [60, '60 min']], 30), cutoff = h('input', { value: '14:30' });
    const short = select([['true', 'allowed'], ['false', 'long only']], 'true'), gross = select([['false', 'configured schedule'], ['true', 'GROSS (zero cost)']], 'false');
    const run = h('button', { class: 'btn primary' }, 'Run experiment');
    /** 409 from the backend means no intraday cost schedule is configured. Say so plainly and offer the labelled zero-cost pass. */
    const noCosts = () => state.hold('Cost configuration unavailable',
        h('p', {}, 'The intraday explorer reads its cost schedule from config/intraday_costs.json, and that file is not set up on this machine, so a net-of-cost run cannot start.'),
        h('p', {}, 'Nothing is wrong with the data, and the registered research cost schedules are separate: they are not used or changed here.'),
        h('p', {}, 'To enable net runs, copy config/intraday_costs.example.json to config/intraday_costs.json and review the rates.'),
        h('button', { class: 'btn', onclick: () => { gross.value = 'true'; run.click(); } }, 'Run a GROSS (zero-cost) pass instead'));
    run.onclick = async () => {
        run.disabled = true;
        const job = api.intradayRun({ file: file.value, range_minutes: range.value, cutoff: cutoff.value, short: short.value, gross: gross.value });
        if (await job.then(() => false, e => e.status === 409)) { out.replaceChildren(noCosts()); run.disabled = false; return; }
        await load(out, job, d => {
            const s = d.summary, b = d.benchmark, v = d.vs, c = d.costs;
            return [
                note(h('div', {}, h('b', {}, 'Limitations — read before trusting any number'), h('ul', { style: 'margin:6px 0 0;padding-left:18px' },
                    d.limitations.map(l => h('li', {}, l)), c.name.includes('GROSS') && h('li', {}, h('b', {}, 'GROSS run: zero costs. Not a realistic result.'))))),
                h('div', { class: 'kpis' },
                    stat(c.name.includes('GROSS') ? 'Gross return' : 'Net return', delta(s.return_pct), `benchmark ${fmt.pct(b.return_pct)}`, 'l'), stat('Sharpe', s.sharpe, `benchmark ${b.sharpe}`, 'l'),
                    stat('Drawdown', s.max_dd + '%', `${s.sessions} sessions`, 'l')),
                kpis([['vs open-to-close', delta(v.strategy_minus_benchmark, 2, ' pts')], ['CAGR', fmt.pct(s.cagr)], ['Exposure', s.exposure_pct + '%'],
                    ['Trades', s.trades, `${s.long_trades} long / ${s.short_trades} short`], ['Win rate', s.win_rate + '%', `profit factor ${s.profit_factor ?? '–'}`]]),
                h('div', { class: 'grid' },
                    card('Equity', { class: 'c12', source: 'real', sub: `${d.strategy} · ${s.start.slice(0, 10)} to ${s.end.slice(0, 10)} · costs ${c.name}` },
                        lineChart({ x: d.curve.dates, height: 280, fmt: x => '₹' + Math.round(x / 1000) + 'k', series: [{ name: 'Strategy', values: d.curve.equity, color: COL.cyan }, { name: 'Open-to-close', values: d.curve.bench, color: COL.magenta, width: 1 }] })),
                    card('Drawdown', { class: 'c12', source: 'real' }, lineChart({ x: d.curve.dates, height: 170, zero: true, fmt: x => x.toFixed(1) + '%', series: [{ values: d.curve.drawdown, color: COL.red, fill: true }] })),
                    card('Chronological split', { class: 'c12', sub: 'parameters were fixed before any period was seen' }, table([
                        { label: 'Period', render: ([k]) => k.replace('_', ' '), sort: false }, { label: 'Dates', render: ([, p]) => `${(p.start || '').slice(0, 10)} → ${(p.end || '').slice(0, 10)}`, sort: false },
                        { label: 'Sessions', r: true, render: ([, p]) => p.sessions, sort: false }, { label: 'Strategy', r: true, render: ([, p]) => delta(p.strategy.return_pct), sort: false },
                        { label: 'Benchmark', r: true, render: ([, p]) => delta(p.benchmark.return_pct), sort: false }, { label: 'Difference', r: true, render: ([, p]) => delta(p.vs.strategy_minus_benchmark, 2, ' pts'), sort: false },
                        { label: 'Max DD', r: true, render: ([, p]) => p.strategy.max_dd + '%', sort: false }], Object.entries(d.periods), { scroll: false })),
                    card(`P&L and costs — ${c.name}`, { class: 'c12' }, table(
                        [['Gross P&L', 'gross_pnl'], ['Brokerage', 'brokerage'], ['STT', 'stt'], ['Exchange', 'exchange'], ['SEBI', 'sebi'], ['Stamp', 'stamp'], ['GST', 'gst'], ['Slippage', 'total_slippage'], ['Total costs', 'total_costs'], ['Net P&L', 'net_pnl']]
                            .map(([label, k]) => ({ label, r: true, render: x => rs(x[k]), sort: false })), [s], { scroll: false })),
                    card('Trades', { class: 'c12', sub: `last ${d.trade_list.length} of ${s.trades}` }, table([
                        { label: 'Entry', render: t => t.entry_time.slice(0, 16), sort: t => t.entry_time }, { label: 'Side', key: 'side' }, { label: 'Qty', r: true, key: 'qty' },
                        { label: 'Entry px', r: true, render: t => fmt.num(t.entry_price), sort: t => t.entry_price }, { label: 'Exit', render: t => t.exit_time.slice(11, 16), sort: false },
                        { label: 'Exit px', r: true, render: t => fmt.num(t.exit_price), sort: t => t.exit_price }, { label: 'Gross', r: true, render: t => rs(t.gross_pnl), sort: t => t.gross_pnl },
                        { label: 'Costs', r: true, render: t => rs(t.total_charges + t.slippage), sort: false }, { label: 'Net', r: true, render: t => h('span', { class: t.net_pnl >= 0 ? 'up' : 'down' }, rs(t.net_pnl)), sort: t => t.net_pnl },
                        { label: 'Reason', key: 'reason' }], [...d.trade_list].reverse())))];
        }, 5);
        run.disabled = false;
    };
    box.replaceChildren(
        note('This explorer is the older single-stock opening-range tool. It is NOT ORB v1: it does not use the frozen protocol, the frozen universe or the holdout, and its output is exploratory. '
            + 'The registered ORB v1 study is on the ORB Research page.', 'info'),
        h('div', { style: 'height:30px' }),
        consoleGrid('Parameters', 'uses /api/intraday/run unchanged · bars before the holdout only', [
            line('Dataset', file), line('Opening range', range), line('Entry cut-off', cutoff), line('Shorts', short), line('Cost model', gross)], [run], null, out),
        section('Intraday datasets', h('span', { class: 'muted small' }, `${files.length} usable of ${all.length}`), src('real')),
        table([
            { label: 'File', render: f => h('b', { class: 'mono' }, f.file), sort: f => f.file }, { label: 'Bar', r: true, render: f => f.ok ? f.timeframe_min + 'm' : '–', sort: f => f.timeframe_min },
            { label: 'Sessions', r: true, key: 'sessions' }, { label: 'From', render: f => (f.start || '').slice(0, 10), sort: f => f.start }, { label: 'To', render: f => (f.end || '').slice(0, 10), sort: f => f.end },
            { label: 'Quality', render: f => !f.ok ? badge('unusable', 'red') : f.warnings.length ? badge(f.warnings.length + ' warnings', 'amber') : badge('clean', 'green'), sort: f => f.warnings.length },
            { label: 'Notes', render: f => h('span', { class: 'small muted' }, (f.warnings[0] || '').slice(0, 110)), sort: false }], all));
    out.replaceChildren(state.empty('Awaiting run', 'Set the parameters and press Run experiment. Each run is logged as a trial.'));
}

export async function backtesting(view, ctx) {
    const box = h('div', { class: 'stack' });
    const show = t => { box.replaceChildren(state.loading(5)); (t === 'Daily strategies' ? daily(box, ctx.query) : intraday(box)).catch(e => box.replaceChildren(state.error(e))); };
    view.replaceChildren(
        hero(['Backtest', 'Engine'], { kicker: ctx.kicker, art: art('field', 'backtest'),
            meta: [['Mode', 'Exploratory'], ['Evidence status', 'Not a registered study'], ['Trials', 'Every run is logged']],
            body: h('span', { class: 'stamp' }, 'Exploratory · not out-of-sample evidence') }),
        note(WARNING), h('div', { style: 'height:26px' }), tabs(['Daily strategies', 'Intraday explorer'], show), box);
    show('Daily strategies');
}
