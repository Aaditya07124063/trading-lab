// Settings: what each data label means, safety state, registered datasets, and the previous interface.
import { h, hero, card, section, kv, table, badge, src, SRC, fmt, note } from '../ui.js';
import { art } from '../art.js';
import { api } from '../api.js';
import { news } from '../providers.js';

export async function settings(view, ctx) {
    const r = await api.research(), root = document.documentElement;
    const calm = h('input', { type: 'checkbox', checked: root.classList.contains('calm'),
        onchange: e => { root.classList.toggle('calm', e.target.checked); localStorage.setItem('tl.calm', e.target.checked ? '1' : '0'); } });
    view.replaceChildren(
        hero(['System', 'Settings'], { kicker: ctx.kicker, small: true, art: art('field', 'settings'),
            meta: [['Live trading', 'Disabled'], ['Broker', 'None'], ['Sign-in', 'None · local single-user lab'], ['Research cut-off', fmt.date(r.research_cutoff)]] }),
        h('div', { class: 'grid' },
            card('Interface', { class: 'c6 box' },
                h('p', {}, 'The earlier single-page interface is kept unchanged as a fallback.'),
                h('p', {}, h('a', { class: 'btn primary', href: 'classic.html' }, 'Open the classic UI')),
                h('label', { class: 'row', style: 'margin-top:22px' }, calm, h('span', {}, 'Calm mode: turn off grain, scanlines, artwork and glitch motion')),
                h('p', { class: 'muted small' }, 'Motion is also switched off automatically when the system asks for reduced motion. Keyboard: press / to search, Esc to close a panel, Enter on a table row to open it.')),
            card('Safety', { class: 'c6' }, kv([
                ['Live trading', badge('disabled', 'amber')], ['Broker connection', badge('none', '')], ['Order execution', badge('not implemented', '')],
                ['Research cut-off', fmt.date(r.research_cutoff)], ['Holdout', `locked from ${fmt.date(r.holdout_start)}`],
                ['Sign-in', 'none: local single-user lab']]),
                h('div', { style: 'margin-top:16px' }, note('Trading Lab is a research and market-intelligence tool. It places no orders, and a backtest is never a forecast.', 'info'))),
            card('Data labels', { class: 'c6' }, kv(Object.entries(SRC).map(([k, [, text]]) => [src(k), text])),
                h('p', { class: 'muted small' }, 'Real data, demo data and research results are loaded by separate modules (js/api.js, js/providers.js) and are never mixed without a label. Nothing in this lab is LIVE: the header shows how old the newest bar is.')),
            card('Connections', { class: 'c6' }, kv([
                ['Price data', h('span', {}, badge('files', 'blue'), '  CSV and parquet files in data/, cut at the research cut-off')],
                ['Symbol search and download', h('span', {}, badge('Yahoo Finance', 'blue'), '  used only when you search or add a symbol')],
                ['News', h('span', {}, badge('demo', 'amber'), '  ' + news.label)], ['Macro calendar', badge('not connected')], ['Fundamentals', badge('not connected')]]))),
        section('Registered datasets', h('span', { class: 'muted small' }, `${r.datasets.length} entries in registry/datasets.json`), src('real')),
        table([
            { label: 'File', render: d => h('span', { class: 'mono small' }, d.file), sort: d => d.file }, { label: 'Instrument', key: 'instrument' }, { label: 'Frequency', key: 'frequency' },
            { label: 'Rows', r: true, render: d => fmt.int(d.rows), sort: d => d.rows }, { label: 'From', render: d => String(d.start || '').slice(0, 10), sort: d => d.start },
            { label: 'To', render: d => String(d.end || '').slice(0, 10), sort: d => d.end }, { label: 'Validation', render: d => h('span', { title: d.validation_status }, badge(String(d.validation_status || '–').split(' - ')[0].slice(0, 22), d.validation_status === 'PASS' ? 'green' : d.validation_status === 'WARN' ? 'amber' : '')), sort: d => d.validation_status },
        ], r.datasets, { sort: 0, dir: 1 }));
}
