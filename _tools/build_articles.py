import re, html, os
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
SRC = REPO.parent / 'Content' / 'meat_texts_nl_fr_en.md'
ASSETS = REPO.parent / 'Content' / 'website_assets'
OUT = REPO / 'articles'
LANGS = ['nl', 'fr', 'en']
ICON_LABEL = {'pig': {'nl': 'varken', 'fr': 'porc', 'en': 'pig'}, 'cow': {'nl': 'rund', 'fr': 'bœuf', 'en': 'cow'}}
INDEX = {
    'nl': ('Weetjes', 'Artikels over ons voedselsysteem: achtergrond bij de cijfers in ClimateCart en concrete kennis om je klimaatimpact te verkleinen.'),
    'fr': ('Infos', "Des articles sur notre système alimentaire : le contexte derrière les chiffres de ClimateCart et des connaissances concrètes pour réduire votre impact climatique."),
    'en': ('Interesting facts', 'Articles about our food system: the background to the numbers in ClimateCart and practical knowledge to reduce your climate impact.'),
}

text = open(SRC, encoding='utf-8').read()
sections = {m.group(1): m.group(2) for m in re.finditer(r'^## (\d)\. .*?\n(.*?)(?=^## \d\. |\Z)', text, re.S | re.M)}

def meta_row(sec, label):
    row = re.search(rf'^\| {label} \|(.*)\|\s*$', sections[sec], re.M).group(1)
    return dict(zip(LANGS, [c.strip() for c in row.split('|')]))

SUBTITLE = {'meat-cuts': meta_row('2', 'Subtitle'), 'meat-origin': meta_row('1', 'Subtitle')}

def per_lang(sec):
    return {m.group(1).lower(): m.group(2).strip() for m in re.finditer(r'^### (NL|FR|EN)\n(.*?)(?=^### |\Z)', sections[sec], re.S | re.M)}

def icon(name, lang):
    svg = open(f'{ASSETS}/animal_{name}.svg', encoding='utf-8').read()
    svg = re.sub(r'\s(width|height)="\d+"', '', svg, count=2)
    return svg.replace('<svg', f'<svg class="icon" role="img" aria-label="{ICON_LABEL[name][lang]}"', 1).strip()

def inline(s, lang):
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*(?!\*)(.+?)\*', r'<em>\1</em>', s)
    if lang == 'fr':
        s = re.sub(r' ([?:;!])', '\u00a0\\1', s)
    for n in ('pig', 'cow'):
        s = s.replace(f'[{n} icon]', icon(n, lang))
    return s

def chart(spec):
    unit, data = spec.split(':', 1)
    unit = unit.replace('Bar chart,', '').strip()
    rows = [(c.rsplit(' ', 1)[0].strip(), c.rsplit(' ', 1)[1]) for c in (x.strip() for x in data.split('·'))]
    vmax = max(float(v.replace(',', '.')) for _, v in rows)
    bars = []
    for i, (name, v) in enumerate(rows):
        y = 12 + i * 44
        w = 190 * float(v.replace(',', '.')) / vmax
        fill = '#636f4b' if i == 0 else '#b7c09c'
        bars.append(f'<text x="0" y="{y + 20}" font-size="15" fill="#1a1a1a">{html.escape(name)}</text>'
                    f'<rect x="105" y="{y}" width="{w:.0f}" height="28" rx="4" fill="{fill}"/>'
                    f'<text x="{112 + w:.0f}" y="{y + 20}" font-size="15" fill="#1a1a1a">{v}</text>')
    desc = '; '.join(f'{n}: {v}' for n, v in rows)
    return (f'<svg class="chart" viewBox="0 0 340 {24 + 44 * len(rows)}" role="img" aria-labelledby="chart-title chart-desc">'
            f'<title id="chart-title">{html.escape(unit)}</title><desc id="chart-desc">{html.escape(desc)}</desc>'
            f'<g font-family="-apple-system, Segoe UI, Roboto, Arial, sans-serif">{"".join(bars)}</g></svg>'
            f'<p class="note">{html.escape(unit)}</p>')

def body(md, lang):
    out, lines, i = [], md.split('\n'), 0
    title = inline(lines[0][2:], lang)
    lines = lines[1:]
    while i < len(lines):
        ln = lines[i].strip()
        if not ln:
            i += 1; continue
        if ln.startswith('## '):
            out.append(f'<h2>{inline(ln[3:], lang)}</h2>')
        elif ln.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not set(''.join(cells)) <= set('-: '):
                    rows.append(cells)
                i += 1
            num = [bool(re.search(r'\d', rows[1][k])) and k == len(rows[0]) - 1 for k in range(len(rows[0]))]
            cls = lambda k: ' class="num"' if num[k] else ''
            head = ''.join(f'<th{cls(k)}>{inline(c, lang)}</th>' for k, c in enumerate(rows[0]))
            trs = ''.join('<tr>' + ''.join(f'<td{cls(k)}>{inline(c, lang)}</td>' for k, c in enumerate(r)) + '</tr>' for r in rows[1:])
            out.append(f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{trs}</tbody></table></div>')
            continue
        elif ln.startswith('[Bar chart'):
            out.append(chart(ln[1:-1]))
        elif ln.startswith('- '):
            items = []
            while i < len(lines) and lines[i].strip().startswith('- '):
                items.append(f'<li>{inline(lines[i].strip()[2:], lang)}</li>'); i += 1
            out.append('<ul>' + ''.join(items) + '</ul>')
            continue
        elif re.match(r'\*\*(Bron|Bronnen|Source|Sources)', ln):
            out.append(f'<p class="sources">{inline(ln, lang)}</p>')
        else:
            out.append(f'<p>{inline(ln, lang)}</p>')
        i += 1
    return title, '\n'.join(out)

def page(slug, lang, title, desc, content, depth):
    root = '../' * depth
    path = f'articles/{slug}/' if slug else 'articles/'
    alts = '\n'.join(f'<link rel="alternate" hreflang="{l}" href="https://climatecart.app/{path}{l}/">' for l in LANGS)
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — ClimateCart</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="https://climatecart.app/{path}{lang}/">
{alts}
<link rel="stylesheet" href="{root}style.css">
</head>
<body data-page="{slug or 'articles'}" data-lang="{lang}">
<main>

{content}

</main>
</body>
</html>
'''

def redirect(path, title):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — ClimateCart</title>
<meta http-equiv="refresh" content="0; url=en/">
<link rel="canonical" href="en/">
</head>
<body>
<p>Redirecting to the <a href="en/">English version</a>. Other languages: <a href="nl/">Nederlands</a> · <a href="fr/">Français</a>.</p>
</body>
</html>
'''

def write(rel, s):
    p = f'{OUT}/{rel}'
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(s)

titles = {}
PUBLISHED = ()  # e.g. (('meat-cuts', '3'), ('meat-origin', '4')) once articles go live
for slug, sec in PUBLISHED:
    for lang, md in per_lang(sec).items():
        title, content = body(md, lang)
        titles[(slug, lang)] = title
        sub = SUBTITLE[slug][lang]
        write(f'{slug}/{lang}/index.html', page(slug, lang, re.sub('<[^>]+>', '', title), sub,
              f'<h1>{title}</h1>\n<p class="subtitle">{html.escape(sub)}</p>\n\n{content}', 3))
    write(f'{slug}/index.html', redirect(f'articles/{slug}/', re.sub('<[^>]+>', '', titles[(slug, "en")])))

import build_nav
build_nav.main()
