# Clipdrop Live — landing page

Static site. Three pages: `index.html`, `privacy.html`, `terms.html`.
Shared CSS in `styles.css`, minimal JS in `script.js`.

No build step. Just upload the folder.

## Deploy on TransIP — clipdroplive.com

TransIP sells domains AND web hosting. You bought the domain there; the hosting
("StackHosting" or "Webhosting") is a separate product. There are two paths.

### Path A — TransIP Webhosting (you also have hosting at TransIP)

1. Go to https://www.transip.nl/cp/ → log in.
2. In the left menu, click **Webhosting**.
3. Click your hosting package → tab **Bestanden / Files**.
4. Click **FTP & SSH** → note the FTP server, username, and your set password
   (TransIP shows it once — set it if not yet done).
5. Open an FTP client. **macOS**: download Cyberduck (free) from
   https://cyberduck.io.
6. In Cyberduck → File → Open Connection:
   - Server: the FTP host shown by TransIP (something like `ftp.clipdroplive.com`)
   - Username and password from step 4
7. After connecting, you'll see a folder usually called `www/` or `public_html/`.
   Open it.
8. Drag these four files INTO that folder, replacing anything already there:
   - `index.html`
   - `privacy.html`
   - `terms.html`
   - `styles.css`
   - `script.js`
9. Visit https://clipdroplive.com — site is live.

If you get a "site not secure" warning, go back to TransIP control panel →
Webhosting → tab **SSL**, click **Activate Let's Encrypt**. Free, takes ~2 min.

### Path B — Domain only at TransIP, hosting elsewhere

If you don't have TransIP Webhosting, the cleanest free option is **Cloudflare
Pages** with direct upload (no GitHub).

1. Sign up at https://dash.cloudflare.com (free).
2. In the dashboard → Workers & Pages → Create → Pages → **Upload assets**.
3. Project name: `clipdroplive`.
4. Drag this whole `landing/` folder into the upload box. Click **Deploy**.
5. After deploy, click **Custom domains** → **Set up a custom domain** →
   enter `clipdroplive.com`.
6. Cloudflare will show two NS records (nameservers) — copy them.
7. Go to TransIP control panel → Domeinnaam → click `clipdroplive.com` →
   tab **DNS / Naamservers** → choose **eigen naamservers** (custom
   nameservers) → paste the two Cloudflare NS records → save.
8. Wait 10–30 min for DNS to propagate. Site is live at https://clipdroplive.com.

Cloudflare also gives you free SSL automatically.

## To re-deploy after edits

- Path A (TransIP Webhosting): re-upload the changed files via Cyberduck.
- Path B (Cloudflare Pages): in the dashboard, open the project → Deployments →
  Create new deployment → upload again.

## Local preview

Just open `index.html` in your browser, or run a tiny local server:

  cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/landing"
  python3 -m http.server 8000

Then open http://localhost:8000 in your browser.
