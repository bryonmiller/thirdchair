# Hosting guide

The public site lives in the `site` directory. It is plain HTML, CSS, and JavaScript with no account login, database, model key, or dependency on the project workspace host.

## Recommended public address

Use either:

1. `https://bryonmiller.github.io/third-chair/`
2. `https://research.bryonmiller.com/third-chair/`

The first address needs only a public GitHub repository and GitHub Pages. The second requires a DNS change for a domain Bryon controls.

## GitHub Pages

1. Create a public repository named `third-chair`.
2. Push the release to the `main` branch.
3. In repository settings, open Pages and choose GitHub Actions as the source.
4. The included workflow publishes the `site` directory.
5. Open the resulting address in a private browser window.

## Other static hosts

Cloudflare Pages, Netlify, and Vercel can publish the `site` directory with no build command. An ordinary web server can use the same directory as its document root.

## Custom domain

If a subdomain is used, add the exact hostname as a `CNAME` file inside `site` before release and follow the host's DNS instructions. Keep the GitHub Pages address working until the custom certificate is active.

## Before the contest link is shared

- Confirm the title and author name in page metadata.
- Test desktop and mobile layouts.
- Use keyboard navigation through every interactive control.
- Check every PDF and ZIP download.
- Confirm there is no ChatGPT, workspace, localhost, or temporary URL in the HTML.
- Confirm the results section distinguishes real runs from fixtures.
- Check that the repository and site work for a signed-out visitor.

The owner-only project checkpoint may be used for quality review, but it is not the contest address.

