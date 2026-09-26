"""Writes the shared header and footer (from site-nav.json) into every page and versions style.css."""
import hashlib, json, re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKIP = {'.git', '_poster-draft', '_tools'}


def header(nav, page, lang):
    url = lambda p, l: nav['pages'][p].get(l) or (nav['pages'].get(nav['sectionOf'].get(p)) or nav['pages']['home'])[l]
    cur = lambda on: ' aria-current="page"' if on else ''
    pills = ''.join(f'<a href="{nav["pages"][s].get(lang) or nav["pages"][s]["en"]}"{cur(s == nav["sectionOf"].get(page))}>{nav["labels"][lang][s]}</a>'
                    for s in nav['sections'])
    langs = ''.join(f'<a href="{url(page, l)}" hreflang="{l}"{cur(l == lang)}>{l.upper()}</a>' for l in ('en', 'nl', 'fr'))
    return (f'<!-- nav:start -->\n<header class="topbar"><a class="brand" href="{url("home", lang)}">ClimateCart</a>'
            f'<nav class="lang">{langs}</nav></header>\n<nav class="pages">{pills}</nav>\n<!-- nav:end -->')


def main():
    nav = json.loads((REPO / 'site-nav.json').read_text(encoding='utf-8'))
    version = hashlib.md5((REPO / 'style.css').read_bytes()).hexdigest()[:8]
    for f in REPO.rglob('index.html'):
        if SKIP & set(f.relative_to(REPO).parts):
            continue
        s = f.read_text(encoding='utf-8')
        m = re.search(r'<body data-page="([^"]+)" data-lang="([^"]+)">', s)
        if not m:
            continue
        page, lang = m.groups()
        s = re.sub(r'<script src="/site\.js" defer></script>\n', '', s)
        s = re.sub(r'\n?<!-- nav:start -->.*?<!-- nav:end -->', '', s, flags=re.S)
        s = re.sub(r'\n?<!-- footer:start -->.*?<!-- footer:end -->', '', s, flags=re.S)
        s = re.sub(r'(<main[^>]*>)', lambda x: x.group(1) + '\n' + header(nav, page, lang), s, count=1)
        s = s.replace('</main>', f'<!-- footer:start -->\n<footer>{nav["footer"][lang]}</footer>\n<!-- footer:end -->\n</main>', 1)
        s = re.sub(r'href="((?:\.\./)*)style\.css(\?v=\w+)?"', lambda x: f'href="{x.group(1)}style.css?v={version}"', s)
        f.write_text(s, encoding='utf-8')
        print('updated', f.relative_to(REPO))


if __name__ == '__main__':
    main()
