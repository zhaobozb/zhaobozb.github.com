# www.zhaobo.me

Personal homepage of Bo Zhao. A single static page (plain HTML + CSS, no build step),
deployed to GitHub Pages by GitHub Actions.

## Layout

```
site/                     Everything published to the website (and nothing else)
  index.html              The homepage
  assets/css/             Stylesheet
  assets/icons/           Favicon, Apple touch icon
  assets/images/          Profile photos; publications/ holds paper thumbnails
  papers/  bibs/          Paper PDFs and BibTeX files (public URLs: /papers/…, /bibs/…)
  CV-ZB-20260206.pdf      CV (public URL: /CV-ZB-20260206.pdf)
  CNAME  sitemap.xml  robots.txt
tools/
  check_links.py          Fails if the site links to a local file that doesn't exist
  linkedin-banner/        Generator for the LinkedIn banner (not published)
.github/workflows/
  deploy.yml              CI/CD: link check → stamp footer date → deploy site/
```

## Preview locally

```sh
python3 -m http.server 8000 --directory site   # then open http://localhost:8000
python3 tools/check_links.py                   # same link check CI runs
```

## Deploy

Push to `master`. The workflow checks links, writes the latest commit date into the
footer ("Last updated …"), and publishes `site/` as-is. It can also be run manually
from the Actions tab. GitHub Pages must be set to **Source: GitHub Actions**.

## Common edits

- **New CV:** add the PDF to `site/` and update every link to the old file name in
  `index.html` (search for `CV-ZB-`). Keep or remove the old file depending on whether
  existing links to it should keep working.
- **New paper:** add the thumbnail to `site/assets/images/publications/`, the PDF to
  `site/papers/`, the BibTeX to `site/bibs/`, and a `<li class="pub">` entry in
  `index.html`. Add `is-selected` to show it in the default "Selected" view.
- **Citation count:** update the line under the Publications heading; the HTML
  comment next to it records the last checked values.
- **Stylesheet changes:** bump the `?v=` query on the stylesheet link in
  `index.html` so browsers fetch the new version.
- **LinkedIn banner:** `python3 tools/linkedin-banner/make_banner.py`
  (needs Google Chrome); upload `banner-final@2x.png`.
