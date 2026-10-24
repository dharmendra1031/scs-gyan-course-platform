# SCS Gyan — Staging Deployment Instructions

The GitHub **Staging Release Package** workflow builds a verified release ZIP
and runs a local startup smoke test. This is **not** a live deployment.

## Download

Open Actions → Staging Release Package → latest successful `development`
run → Artifacts → `scs-gyan-staging-release`. Extract the GitHub artifact,
then extract `scs-gyan-staging-<commit>.zip` to a new staging application
folder. The ZIP contains `RELEASE-MANIFEST.json` with the source commit
and SHA-256 hashes. Use the commit number when recording client acceptance.

No .env, SQLite file, student uploads or private course PDFs belong in
the release. Keep older packages for rollback.

## Windows Server + IIS + SQL Server

1. Install supported Windows Server updates, Python 3.12, Microsoft ODBC
   Driver 18, IIS, URL Rewrite, ARR, and a trusted TLS certificate.
2. Create a **separate staging SQL Server database**, a least-privilege
   runtime login, and a schema-migration login. Test SQL TLS trust.
3. Put the extracted project **outside the IIS website root**.
   IIS must expose only staticfiles and explicitly approved public media,
   never private_media, project source code or .env.
4. Copy `.env.staging.example` to `.env` next to `manage.py`.
   Replace all values marked replace-with and the example hostname.
   Set `TRUST_REVERSE_PROXY_HTTPS=True` only if the trusted IIS proxy
   strips client-supplied X-Forwarded-Proto before setting its own header.
5. Configure HTTPS-only IIS reverse proxy to
   `http://127.0.0.1:8008` and preserve the external Host. Restrict
   client/demo access by IP allowlist or IIS authentication.
6. Create a virtual environment and install dependencies from
   `requirements.txt`; it includes Waitress.
7. Back up staging SQL Server before deploying schema migrations.
8. Run the commands below. Configure a low-privilege managed Windows
   service for the Waitress process rather than leaving a PowerShell window
   open. Serve compiled static assets directly from IIS.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\staging_preflight.py
.\.venv\Scripts\python.exe manage.py check --deploy
.\.venv\Scripts\python.exe manage.py migrate --noinput
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
powershell -ExecutionPolicy Bypass -File scripts\start_staging.ps1
```

In the actual staging environment, separately verify all routes and access
control: `https://staging.example.org/health/`, `/courses/`,
`/articles/`, `/account/login/`, `/static/css/site.css`,
and an unauthenticated redirect from `/account/dashboard/`.
Replace `staging.example.org` with the real domain.

## Operations & safety

- Do not use `manage.py runserver` on a public network.
- Keep Razorpay keys unset until the real sandbox acceptance run.
- Never publicly map `PRIVATE_MEDIA_ROOT`; back it up securely.
- Verify DNS, HTTP→HTTPS redirect, Django host/CSRF settings and
  the IIS forwarded-protocol trust boundary. Do not enable HSTS preload
  before confirming HTTPS for all subdomains.
- Test a SQL backup/restore to a separate test database.
- Confirm another student's PDF/video/certificate access is denied.
- Collect approved course descriptions, privacy/terms/refund text,
  and client design sign-off before external release.

The package is for staging readiness only. A real URL still requires
server/domain/SQL Server access and client authorization.
