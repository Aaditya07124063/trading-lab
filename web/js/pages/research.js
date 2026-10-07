// Quantitative research pages: Research lab, Experiment archive, ORB v1 protocol.
// Inspection only. Every number is read from the registered files through /api/research; nothing is run or recomputed.
import { h, hero, card, section, stat, kpis, kv, spec, tri, note, table, fmt, badge, statusBadge, src, seg, drawer, state, hash } from '../ui.js';
import { art } from '../art.js';
import { api } from '../api.js';

const n = (v, d = 3) => v == null ? '–' : Number(v).toFixed(d);
const sg = (v, d = 4) => v == null ? '–' : (v > 0 ? '+' : '') + Number(v).toFixed(d);      // sign shown, value as saved
const ok = v => v ? badge('verified', 'green') : badge('mismatch', 'red');
const INTEGRITY = 'Figures are read from the registered result files and shown as saved. No interpretation is added here, and a backtest result is never a forecast of future returns.';
const HASH_NOTE = 'A SHA-256 check of the registered files, re-hashed on this page load. It says the files are unchanged; it is not a scientific judgement.';
const allVerified = s => Object.values(s.runs).every(x => x.verified) && s.documents.every(d => d.verified);

function runsTable(runs) {
    const names = { blinded: 'Blinded precision step', primary: 'Primary run (steps A–D)', sensitivity: 'Sensitivity run', confirmation: 'Confirmation run (out-of-sample)', step_e: 'Step E (costs)' };
    return table([
        { label: 'Run', render: ([k]) => names[k] || k, sort: false },
        { label: 'Registered', render: ([, r]) => r.registered ? badge('yes', 'green') : badge('no'), sort: false },
        { label: 'Files', r: true, render: ([, r]) => r.files, sort: false },
        { label: 'SHA-256 check', render: ([, r]) => r.registered ? ok(r.verified) : '–', sort: false },
    ], Object.entries(runs), { scroll: false });
}
/** H1 as saved: the mean large, the test statistics as small technical lines. */
const h1Stat = (label, x) => x && stat(label, sg(x.mean), h('span', {}, `% per month · t ${n(x.t, 2)} · p ${n(x.p_two_sided, 4)} · n ${x.n} · lag ${x.lag}  `, x.decision && badge(x.decision)), 'l');
function ladderTable(ladder) {
    const cell = v => v ? h('span', { class: 'num' }, `${n(v.mean_pct, 3)}  `, h('span', { class: 'muted' }, `t ${n(v.t_nw, 2)}`)) : '–';
    return table([{ label: 'Step', render: ([s]) => h('b', {}, s), sort: false },
        ...['W', 'L', 'WML', 'BM'].map(p => ({ label: p === 'BM' ? 'Benchmark' : p, r: true, render: ([, row]) => cell(row[p]), sort: false }))],
        Object.entries(ladder || {}), { scroll: false, empty: 'No ladder saved' });
}
function stepETable(sample) {
    const pct = v => v == null ? '–' : (v * 100).toFixed(4);
    return table([{ label: 'Scenario', render: ([s, v]) => h('span', { class: 'nowrap' }, h('b', {}, s), h('span', { class: 'muted small' }, `  ${v.slippage_bps['1-200']} / ${v.slippage_bps['201-500']} bps`)), sort: false },
        ...[['net_W', 'Net W'], ['net_BM', 'Net benchmark'], ['hypothetical_net_L', 'Net L (hypothetical)'], ['hypothetical_net_WML', 'Net WML (hypothetical)'], ['net_excess_W_over_BM', 'Net W − benchmark']]
            .map(([k, label]) => ({ label, r: true, render: ([, v]) => pct(v[k]), sort: false }))],
        Object.entries(sample.scenarios), { scroll: false });
}
const test = t => !t ? '–' : t.status ? h('span', { class: 'muted' }, t.status)
    : h('span', { class: 'num' }, `mean ${n(t.mean_pct, 4)} % · t ${n(t.t, 3)} · one-sided p ${n(t.p_one_sided, 4)} · lag ${t.lag}  `, badge(t.supported ? 'supported' : 'not supported', t.supported ? 'green' : ''));
const s2Tri = s => tri([['Protocol', 'Frozen', 'frz'], ['Result files', allVerified(s) ? 'Verified' : 'Mismatch', allVerified(s) ? 'ok' : 'bad', HASH_NOTE],
    ['Reproducibility', allVerified(s) ? 'Pass' : 'Fail', allVerified(s) ? 'ok' : 'bad', HASH_NOTE]]);
const orbTri = o => tri([['Protocol', o.protocol_status, 'frz'], ['Holdout', 'Locked', 'hold'], ['Final evaluation', o.final_evaluation_registered ? 'Registered' : 'Not run', o.final_evaluation_registered ? 'ok' : 'hold']]);

// ------------------------------------------------------------------ Research lab
export async function research(view, ctx) {
    const r = await api.research(), s = r.s2_mom, o = r.orb;
    const dev = o.dev_sample, inf = dev.primary_inference_bps || {}, wml = Object.entries(s?.primary?.ladder || {});
    view.replaceChildren(...[
        hero(['Research', 'Lab'], { kicker: ctx.kicker, art: art('field', 'research'),
            meta: [['Registry', `${r.experiments.length} experiments`], ['Logged runs', r.logged_trials], ['Research cut-off', fmt.date(r.research_cutoff)], ['Holdout', `locked from ${fmt.date(r.holdout_start)}`]],
            body: [h('span', { class: 'stamp frozen' }, 'Registered research · not live intelligence'), h('p', { class: 'lede' }, INTEGRITY)] }),
        section('S2-MOM-v1', src('research')),
        !s ? state.empty('S2-MOM-v1 is not in the registry') : [
            s2Tri(s),
            h('div', { class: 'grid', style: 'margin-top:40px' },
                card('Hypothesis', { class: 'c7' }, h('p', { style: 'font-size:17px;line-height:1.45;margin-bottom:18px;max-width:60ch' }, s.research_question), spec([
                    ['Estimand', s.primary_estimand, true], ['Hypothesis', s.hypothesis, true],
                    ['Protocol', `${s.protocol_version}, frozen ${fmt.date(s.frozen_on)} (commit ${String(s.freeze_commit).slice(0, 7)})`, true],
                    ['Universe', s.universe],
                    ['Registry field', h('span', {}, statusBadge(s.registry_status), h('span', { class: 'muted small' }, '  as written in the registry record; the runs were registered as amendments'))],
                ])),
                card('Sample', { class: 'c5' }, h('div', { class: 'kpis' },
                    stat('Months · primary', s.primary_sample.months, s.primary_sample.holding_months.join(' → '), 'xl'),
                    stat('Months · confirmation', s.oos_sample.months, s.oos_sample.holding_months.join(' → '), 'xl')),
                    h('p', { class: 'muted small' }, s.oos_sample.nature)),
                card('Result · H1: mean of δ = WML_A − WML_D', { class: 'c12', sub: 'decision labels are the ones the frozen rules wrote into the result files' }, h('div', { class: 'kpis' },
                    h1Stat('H1 · primary sample', s.primary?.H1), h1Stat('H1 · confirmation sample', s.confirmation?.H1),
                    s.sensitivity_reliability && stat('Reliability · frozen §25', s.sensitivity_reliability.not_reliable ? 'Not reliable' : 'Reliable',
                        `sensitivity treatments that change H1 or H3: ${(s.sensitivity_reliability.sensitivity_treatments_that_change_H1_or_H3 || []).join(', ') || 'none'}`, 'word'))),
                card('Bias ladder · primary sample', { class: 'c7', sub: 'mean % per month and Newey–West t' },
                    kpis(wml.map(([step, row]) => row.WML && [`WML · step ${step} · gross monthly`, sg(row.WML.mean_pct) + '%', `t ${n(row.WML.t_nw, 2)}`])),
                    h('div', { style: 'margin-top:26px' }, ladderTable(s.primary?.ladder))),
                card('Reproducibility', { class: 'c5', sub: 'files re-hashed on this page load' }, runsTable(s.runs),
                    h('div', { style: 'margin-top:18px' }, kv([
                        ['Protocol and addenda', h('span', {}, ok(s.documents.every(d => d.verified)), `  ${s.documents.length} documents`)],
                        ['Experiment code', hash(s.code_sha256)], ['Step E code', hash(s.step_e_code_sha256)]]))),
                s.step_e && card('Step E · costs · primary sample', { class: 'c12', sub: 'mean % per month · pre-specified scenarios S0–S4 (one-way slippage, rank 1–200 / 201–500)' },
                    stepETable(s.step_e.samples.primary),
                    h('div', { style: 'margin-top:20px' }, kv([['H3 (gross WML > 0)', test(s.step_e.samples.primary.H3)], ['H4 (net W − benchmark > 0, S0)', test(s.step_e.samples.primary.H4)],
                        ['Break-even one-way cost', s.step_e.samples.primary.break_even.break_even_one_way_cost_bps != null ? h('span', { class: 'num' }, n(s.step_e.samples.primary.break_even.break_even_one_way_cost_bps, 1) + ' bps') : s.step_e.samples.primary.break_even.status],
                        ['Confirmation: H3', test(s.step_e.samples.confirmation.H3)], ['Confirmation: H4', test(s.step_e.samples.confirmation.H4)]])),
                    h('p', { class: 'muted small' }, s.step_e.statement)))],
        section('ORB-v1', src('research')),
        orbTri(o),
        h('div', { class: 'grid', style: 'margin-top:40px' },
            card('Study', { class: 'c6', actions: h('a', { class: 'info small', href: '#/orb' }, 'Protocol →') }, spec([
                ['Strategy', o.records[0]?.strategy], ['Universe', o.records[0]?.universe, true],
                ['Hypothesis', o.records.at(-1)?.hypothesis], ['Holdout', `prospective, from ${fmt.date(o.holdout_start)}; locked until an authorisation artifact is committed`],
                ['Primary result', o.final_evaluation_registered ? 'see registry' : h('span', { class: 'muted' }, 'none yet: the final evaluation has not been run')],
                ['Protocol hash', hash(o.protocol_sha256)]])),
            card('Development sample · diagnostic, not evidence', { class: 'c6' }, kpis([
                ['Sessions', dev.sessions], ['Stocks', dev.universe_n], ['Trades', fmt.int(dev.trades?.n)],
                ['Mean net, bps/day', n(inf.mean, 2)], ['Label on dev sample', dev.reporting_label_on_dev_sample]]),
                h('p', { class: 'muted small' }, dev.purpose)))].flat());
}

// ------------------------------------------------------------------ Experiment archive
export async function experiments(view, ctx) {
    const r = await api.research(), box = h('div', {}), s = r.s2_mom, o = r.orb;
    const groups = ['All', ...new Set(r.experiments.map(e => e.status.startsWith('REQUIRES') ? 'REQUIRES ACTION' : e.status))];
    const byDate = [...r.experiments].sort((a, b) => String(a.executed_at).localeCompare(String(b.executed_at)));
    const ord = e => 'EXP-' + String(byDate.indexOf(e) + 1).padStart(3, '0');                  // archive position by execution time, display only
    const open = e => drawer(e.experiment_id, [
        kv([['Status', statusBadge(e.status)], ['Strategy', e.strategy], ['Research question', e.research_question], ['Hypothesis', e.hypothesis],
            ['Universe', e.universe], ['Instrument', e.instrument], ['Timeframe', e.timeframe], ['Period', `${e.start} → ${e.end}`], ['Dataset', e.dataset_id],
            ['Dataset stage', e.dataset_stage], ['Cost model', e.cost_model], ['Benchmark', e.benchmark], ['Test period', e.test_period],
            ['Out-of-sample status', e.oos_status], ['Viewed before finalisation', e.viewed_before_finalization], ['Result (headline)', e.headline || '–'],
            ['Limitations', e.limitations], ['Protocol', e.protocol_file && `${e.protocol_file} (${e.protocol_version || ''})`], ['Executed', fmt.time(e.executed_at)],
            ['Amendments', e.amendments]]),
        s && e.experiment_id === 'S2-MOM-v1' && h('div', {}, h('div', { class: 'lbl', style: 'margin-bottom:8px' }, 'Registered documents · SHA-256'),
            kv(s.documents.map(d => [h('span', {}, d.id, '  ', ok(d.verified)), hash(d.sha256)]))),
        e.experiment_id.startsWith('ORBV1') && h('div', {}, h('div', { class: 'lbl', style: 'margin-bottom:8px' }, 'Protocol · SHA-256'), hash(o.protocol_sha256)),
        note(INTEGRITY, 'info')], 'research', ord(e));
    const draw = g => box.replaceChildren(table([
        { label: '#', render: e => h('span', { class: 'num muted small nowrap' }, ord(e)), sort: e => byDate.indexOf(e) },
        { label: 'Experiment', render: e => h('b', { class: 'mono nowrap' }, e.experiment_id), sort: e => e.experiment_id },
        { label: 'Status', render: e => e.status.startsWith('REQUIRES') ? h('span', { title: e.status }, badge('Requires action', 'red')) : statusBadge(e.status), sort: e => e.status },
        { label: 'Strategy and result as registered', render: e => h('div', { style: 'min-width:240px;max-width:520px' }, e.strategy, h('div', { class: 'muted small' }, (e.headline || '–').slice(0, 110))), sort: e => e.strategy },
        { label: 'Period', render: e => h('span', { class: 'num small nowrap' }, `${String(e.start).slice(0, 7)} → ${String(e.end).slice(0, 7)}`), sort: e => e.start },
        { label: 'Executed', render: e => h('span', { class: 'num small nowrap' }, fmt.date(e.executed_at)), sort: e => e.executed_at },
    ], r.experiments.filter(e => g === 'All' || e.status === g || (g === 'REQUIRES ACTION' && e.status.startsWith('REQUIRES'))), { onRow: open, sort: 5 }));
    const find = id => r.experiments.find(e => e.experiment_id === id);
    const feature = (id, body, e) => h('section', { class: 'card box research c6' }, body,
        e && h('button', { class: 'btn', style: 'margin-top:22px', onclick: () => open(e) }, `Open ${id} →`));
    view.replaceChildren(
        hero(['Experiment', 'Archive'], { kicker: ctx.kicker, small: true, art: art('field', 'experiments'),
            meta: [['Experiments', r.experiments.length], ['Logged runs', `${r.logged_trials} · every run is counted for multiple-testing accounting`], ['Source', src('research')]] }),
        h('div', { class: 'grid' },
            s && feature('S2-MOM-v1', [
                h('div', { class: 'row between' }, h('span', { class: 'lbl' }, find('S2-MOM-v1') ? ord(find('S2-MOM-v1')) : 'S2'), src('research')),
                h('h3', { class: 'mono', style: 'font:500 34px/1.1 var(--mono);letter-spacing:-.05em;margin:10px 0 18px' }, 'S2-MOM-v1'),
                tri([['Protocol', 'Frozen', 'frz'], ['Hashes', allVerified(s) ? 'Verified' : 'Mismatch', allVerified(s) ? 'ok' : 'bad', HASH_NOTE]]),
                h('div', { class: 'kpis', style: 'margin-top:26px' }, stat('Months · primary', s.primary_sample.months, null, 'l'), stat('Months · confirmation', s.oos_sample.months, null, 'l')),
                h('div', { style: 'margin-top:18px' }, hash(s.documents[0]?.sha256))], find('S2-MOM-v1')),
            feature('ORB-v1', [
                h('div', { class: 'row between' }, h('span', { class: 'lbl' }, o.records[0] ? ord(find(o.records[0].experiment_id) || o.records[0]) : 'ORB'), src('research')),
                h('h3', { class: 'mono', style: 'font:500 34px/1.1 var(--mono);letter-spacing:-.05em;margin:10px 0 18px' }, 'ORB-v1'),
                tri([['Protocol', o.protocol_status, 'frz'], ['Holdout', o.final_evaluation_registered ? 'Evaluated' : 'Locked', 'hold']]),
                h('div', { class: 'kpis', style: 'margin-top:26px' }, stat('Stocks · frozen universe', o.dev_sample.universe_n, null, 'l'), stat('Holdout starts', o.holdout_start, null, 'l')),
                h('div', { style: 'margin-top:18px' }, hash(o.protocol_sha256))], o.records[0] && find(o.records[0].experiment_id))),
        section('Registry', src('research')),
        h('div', { style: 'margin-bottom:22px' }, seg(groups, draw, 'All')),
        box);
    draw('All');
}

// ------------------------------------------------------------------ ORB v1 (inspection only)
export async function orb(view, ctx) {
    const r = await api.research(), o = r.orb, a = o.records[0] || {}, last = o.records.at(-1) || {}, dev = o.dev_sample, inf = dev.primary_inference_bps || {};
    view.replaceChildren(
        hero(['ORB', 'v1'], { kicker: ctx.kicker, art: art('field', 'orb'),
            meta: [['Universe', a.universe], ['Bars', a.timeframe], ['Holdout starts', fmt.date(o.holdout_start)], ['Research cut-off', fmt.date(r.research_cutoff)], ['File', o.protocol_file]],
            body: [h('div', { class: 'row', style: 'margin-bottom:16px' }, h('span', { class: 'stamp frozen' }, `${o.protocol_status} protocol`), h('span', { class: 'muted small' }, 'read-only · nothing on this page can change it')),
                orbTri(o)] }),
        note('Inspection only. This page does not run, rerun or change ORB v1. The prospective holdout is locked in code and is not read here.', 'info'),
        h('div', { class: 'grid', style: 'margin-top:44px' },
            card('Protocol', { class: 'c7', source: 'research' }, spec([
                ['Universe', a.universe, true], ['Entry · exit', a.strategy], ['Benchmark', a.benchmark], ['Cost model', a.cost_model], ['Hypothesis', last.hypothesis],
                ['SHA-256', hash(o.protocol_sha256)]])),
            card('Holdout', { class: 'c5 box' }, stat('Access', h('span', { class: 'warn' }, 'Locked'), 'A committed authorisation artifact naming this protocol hash is required (protocol §7).', 'word'),
                h('div', { style: 'margin-top:20px' }, kv([['Design', 'Prospective holdout'], ['Holdout starts', fmt.date(o.holdout_start)],
                    ['Final evaluation', o.final_evaluation_registered ? badge('registered', 'green') : badge('not run', '')]])),
                h('p', { class: 'muted small' }, 'Collection progress is an operational report: python3 scripts/holdout_status.py. It is not shown here.'))),
        section('Development sample', h('span', { class: 'muted small' }, `${dev.window?.join(' to ')} · descriptive, not evidence, not used for tuning`)),
        kpis([['Sessions', dev.sessions], ['Stocks', dev.universe_n], ['Trades', fmt.int(dev.trades?.n)], ['Long / short', `${fmt.int(dev.trades?.long)} / ${fmt.int(dev.trades?.short)}`],
            ['Primary cost scenario', dev.primary_scenario], ['Mean net, bps/day', n(inf.mean, 2)], ['Gross mean, bps/day', n(dev.gross_mean_bps, 2)],
            ['Benchmark A net, bps/day', n(dev.benchmark_A_mean_net_bps, 2)], ['Dev-sample label', dev.reporting_label_on_dev_sample]]),
        h('p', { class: 'muted small', style: 'margin-top:18px' }, dev.purpose),
        section('Registered records'),
        table([
            { label: 'Experiment', render: e => h('b', { class: 'mono nowrap' }, e.experiment_id), sort: false }, { label: 'Status', render: e => statusBadge(e.status), sort: false },
            { label: 'Period', render: e => h('span', { class: 'num small nowrap' }, `${e.start} → ${e.end}`), sort: false }, { label: 'OOS status', key: 'oos_status', sort: false },
            { label: 'Result (as registered)', key: 'headline', sort: false }], o.records, { scroll: false }),
        section('Protocol document', h('span', { class: 'muted small' }, 'read-only text of the frozen file')),
        h('pre', { class: 'doc', tabindex: 0 }, o.protocol_text || 'Protocol file not found'));
}
