// News & Intelligence. The whole page runs on the demo provider until a timestamped news source is connected.
import { h, hero, card, note, tabs, tone, src, kv, fmt, drawer, state, delta, load, badge, level, diverge } from '../ui.js';
import { art } from '../art.js';
import { news } from '../providers.js';

const tagLink = (text, href) => h('a', { class: 'tag', href, onclick: e => e.stopPropagation() }, text);
const SENT = { Positive: 'up', Negative: 'down' };
const cell = (label, ...body) => h('div', {}, h('span', { class: 'lbl' }, label), body);
/** Demo price and volume reaction as two small bars. */
const reaction = n => h('div', { class: 'react', title: `Demo values · ${n.reaction.window}` },
    h('span', {}, 'PX'), diverge(n.reaction.price_pct, 3), delta(n.reaction.price_pct, 1),
    h('span', {}, 'VOL'), level(n.reaction.volume_x / 4 * 100), h('span', { class: 'num' }, n.reaction.volume_x.toFixed(1) + '×'));

/** One intelligence item. compact = headline, impact and affected names only (used on Overview). */
export function newsItem(n, compact) {
    return h('article', { class: 'intel ' + n.impact.toLowerCase(), tabindex: 0, role: 'button', 'aria-label': `Demo item, ${n.impact} impact: ${n.headline}`,
        onclick: () => openNews(n), onkeydown: e => e.key === 'Enter' && openNews(n) },
        h('div', { class: 'head' }, h('span', { class: 'imp' }, `[ ${n.impact} impact ]`), src('demo'), h('span', {}, fmt.ist(n.published)), h('span', {}, `${n.source} / ${n.category}`)),
        h('h4', {}, n.headline),
        h('div', { class: 'cols' },
            cell('Impact', h('b', { class: SENT[n.sentiment] || '' }, n.sentiment)),
            cell('Confidence', h('b', {}, (n.confidence * 100).toFixed(0) + '% ', level(n.confidence * 100))),
            cell('Affected', h('div', {}, n.securities.length ? n.securities.map(s => tagLink(s, '#/stock/' + s)) : h('span', { class: 'muted small' }, 'market-wide'))),
            !compact && cell('Sector', h('div', {}, n.sectors.map(s => h('span', { class: 'tag' }, s)))),
            !compact && cell('Reaction · demo', reaction(n))),
        !compact && h('p', {}, h('b', { class: 'lbl' }, 'Why it matters  '), n.why));
}

/** Detail panel: the news → entity → sector → impact → price → volume chain for one item. */
export function openNews(n) {
    const step = (label, ...body) => h('div', { class: 'step' }, h('span', {}, label), body);
    const arrow = () => h('div', { class: 'arrow', 'aria-hidden': 'true' }, '↓');
    drawer(n.headline, [
        note('Demo item. It is invented to design this view: not a real article, and no number below is a real measurement.'),
        kv([['Source', n.source], ['Published', fmt.ist(n.published)], ['Category', n.category],
            ['Sentiment', tone(n.sentiment)], ['Impact', h('span', {}, tone(n.impact), h('span', { class: 'num muted' }, `  score ${n.impact_score.toFixed(2)}`))],
            ['Confidence', h('span', { class: 'num' }, (n.confidence * 100).toFixed(0) + '%')]]),
        h('div', { class: 'chain' },
            step('News', n.headline), arrow(),
            step('Entity', n.securities.length ? n.securities.map(s => tagLink(s, '#/stock/' + s)) : h('span', { class: 'muted' }, 'No single company (market-wide event)')), arrow(),
            step('Sector', n.sectors.map(s => h('span', { class: 'tag' }, s))), arrow(),
            step('Impact', tone(n.sentiment), ' ', tone(n.impact), h('span', { class: 'muted small' }, `  score ${n.impact_score.toFixed(2)}, confidence ${(n.confidence * 100).toFixed(0)}%`)), arrow(),
            step('Price', delta(n.reaction.price_pct, 1), h('span', { class: 'muted small' }, `  ${n.reaction.window}`)), arrow(),
            step('Volume', h('span', { class: 'num' }, n.reaction.volume_x.toFixed(1) + '× average'), h('span', { class: 'muted small' }, `  ${n.reaction.window}`)), arrow(),
            step('Market regime', n.regime)),
        h('div', {}, h('div', { class: 'lbl', style: 'margin-bottom:6px' }, 'Explanation'), h('p', { style: 'color:var(--ink-2)' }, n.explanation)),
    ], 'demo', `${n.impact} impact · ${n.category}`);
}

// The chain the module is designed around, and what exists of each stage today.
const PIPE = [['News', 'Timestamped source', 'not connected'], ['Entity', 'Company tagging', 'not built'], ['Sector', 'Sector mapping', 'not built'],
    ['Impact', 'Sentiment · event study', 'not built'], ['Price', 'Price reaction', 'not built'], ['Volume', 'Volume reaction', 'not built']];

export async function newsPage(view, ctx) {
    const list = h('div', {}), all = await news.list();
    const show = cat => load(list, news.list({ category: cat }), items => items.length ? items.map(n => newsItem(n))
        : state.empty('No items in this category', 'The demo feed has nothing here.'));
    view.replaceChildren(
        hero(['Market', 'Intelligence'], { kicker: ctx.kicker, art: art('figure', 'intelligence'),
            meta: [['Provider', news.label], ['Items', `${all.length} sample items`], ['Macro calendar', 'Not connected']],
            body: [h('span', { class: 'stamp' }, 'Demo data · no news provider connected'),
                h('p', { class: 'lede' }, 'Everything on this page is illustrative. No article, sentiment, impact or reaction value here is real, and nothing here is live.')] }),
        h('div', { class: 'pipe', role: 'list', 'aria-label': 'Intelligence pipeline and the status of each stage' },
            PIPE.map(([name, what, status]) => h('div', { role: 'listitem' }, h('b', {}, name), h('span', {}, what), h('em', {}, status)))),
        h('div', { class: 'grid', style: 'margin-top:54px' },
            h('div', { class: 'c8' }, tabs(news.categories(), show), list),
            h('div', { class: 'c4 stack' },
                card('Feed status', { source: 'demo' }, kv([['Provider', news.label], ['Mode', badge('Demo', 'amber')], ['Live', 'No']])),
                card('How to read an item', {}, h('p', { class: 'muted small' },
                    'Each item is read left to right: the event, who it touches, the sector, the expected impact and its confidence, then the price and volume reaction. Open one to follow the full chain.')),
                card('Connecting a real source', {}, h('p', { class: 'muted small' },
                    'The interface reads news through one provider object (js/providers.js). A real provider with the same two methods replaces the demo feed without changing any page.')))));
    show('All');
}
