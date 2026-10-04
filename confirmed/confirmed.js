// Landing page for the signup confirmation mail. Supabase appends the result to the URL:
// session tokens on success, an error on an expired or used link.
const hash = location.hash.slice(1);
const params = new URLSearchParams(hash);
const failed = params.has('error') || new URLSearchParams(location.search).has('error');

if (params.get('access_token') && params.get('refresh_token')) {
  document.getElementById('open-app').href = 'climatecart://email-confirmed#' + hash;
  document.getElementById('confirmed').hidden = false;
  history.replaceState(null, '', location.pathname);
} else if (failed) {
  document.getElementById('expired').hidden = false;
  history.replaceState(null, '', location.pathname);
} else {
  location.replace(document.body.dataset.home);
}
