(async () => {
  const { page, lang } = document.body.dataset;
  const nav = await (await fetch('/site-nav.json')).json();
  const url = (p, l) => nav.pages[p][l] || (nav.pages[nav.sectionOf[p]] || nav.pages.home)[l];
  const current = (on) => (on ? ' aria-current="page"' : '');
  const pills = nav.sections
    .map((s) => `<a href="${nav.pages[s][lang] || nav.pages[s].en}"${current(s === nav.sectionOf[page])}>${nav.labels[lang][s]}</a>`)
    .join('');
  const langs = ['en', 'nl', 'fr']
    .map((l) => `<a href="${url(page, l)}" hreflang="${l}"${current(l === lang)}>${l.toUpperCase()}</a>`)
    .join('');
  const main = document.querySelector('main');
  main.insertAdjacentHTML('afterbegin',
    `<header class="topbar"><a class="brand" href="${url('home', lang)}">ClimateCart</a><nav class="lang">${langs}</nav></header><nav class="pages">${pills}</nav>`);
  main.insertAdjacentHTML('beforeend', `<footer>${nav.footer[lang]}</footer>`);
})();
