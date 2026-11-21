# AI Trade Intelligence V43 – Responsive Website Edition

This is the supplied V43 codebase with a responsive desktop/mobile Streamlit shell and an optional server-side account login gate. All V43/V42 and earlier application modules are retained.

## Run locally

```bash
python -m pip install -r requirements.txt
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and set unique credentials and your own Upstox token:

```toml
APP_LOGIN_USERNAME = "your_login_id"
APP_LOGIN_PASSWORD = "use_a_long_unique_password"
UPSTOX_ACCESS_TOKEN = "your_upstox_access_token"
```

Then run:

```bash
python -m streamlit run app.py
```

Open the local address shown by Streamlit. On a phone connected to the same network, use the computer's LAN IP and Streamlit port (default 8501), subject to firewall/network settings.

## Publish as a website

1. Create a **private** GitHub repository and upload this project. Do not upload `.streamlit/secrets.toml`, API tokens, or runtime databases containing personal trading records unless you intentionally want to transfer them.
2. Deploy the repository with Streamlit Community Cloud (or another Streamlit-compatible host), selecting `app.py` as the entry point.
3. In the hosting dashboard, open the app's Secrets settings and add `APP_LOGIN_USERNAME`, `APP_LOGIN_PASSWORD`, and `UPSTOX_ACCESS_TOKEN` in TOML format.
4. Deploy and open the generated HTTPS address on desktop and mobile browsers.
5. Keep a separate encrypted backup of local SQLite databases and any user data you need to migrate. The supplied V43 archive includes its V43 monitor database; runtime databases may be created or updated while the app runs.

## Login behavior

- If both `APP_LOGIN_USERNAME` and `APP_LOGIN_PASSWORD` are configured, the login screen is enforced before application data loading.
- If they are not configured, the app runs without a login gate and shows a sidebar warning. Configure credentials before exposing the app publicly.
- This is a basic single-account application gate, not a multi-user identity provider. For public production use, put the app behind a managed identity/access layer, HTTPS, host-level rate limiting and appropriate backups.
- Streamlit session authentication is not a substitute for broker API authorization. Keep Upstox tokens server-side in secrets.

## Desktop and mobile behavior

- Uses Streamlit's wide layout with responsive CSS breakpoints for phone/tablet widths.
- Sidebar navigation remains available through Streamlit's native mobile sidebar control.
- Metrics, charts, tabs, tables and buttons receive narrower-screen spacing and sizing adjustments.
- Plotly charts remain interactive; on narrow screens they may require horizontal/zoom interaction depending on chart complexity.

## Existing V43 limitations remain

- Live market streaming requires a valid Upstox token, SDK and valid instrument keys. It runs within the Streamlit process and is not a guaranteed 24/7 service.
- Historical opportunity scans use the selected historical data source; they are not an exchange-wide live scanner.
- Alerts are evaluated from available feed snapshots and are not guaranteed push notifications.
- No real-money broker order placement is enabled by V42/V43.
