# ATS CV Builder — Deployment Guide

## Repository structure

```
ats-cv-builder/
├── app.py
├── requirements.txt
├── packages.txt
├── .gitignore
├── .streamlit/
│   └── secrets.toml        ← local only, never commit
└── utils/
    ├── __init__.py          ← empty file
    ├── cv_parser.py
    ├── researcher.py
    ├── gemini_client.py
    └── latex_builder.py
```

---

## Step 1 — Get API keys

| Service | Free tier | URL |
|---------|-----------|-----|
| **Google Gemini** | Yes (generous) | https://aistudio.google.com/app/apikey |

---

## Step 2 — Fill in secrets.toml

1. Edit `.streamlit/secrets.toml` with your real API keys.
2. Replace the sample profile with **your own** name, education, experience, skills, and projects.
3. Add `.streamlit/secrets.toml` to `.gitignore` — **never push it to GitHub**.

```gitignore
# .gitignore
.streamlit/secrets.toml
__pycache__/
*.pyc
.env
```

---

## Step 3 — Test locally

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install LaTeX (macOS example)
brew install --cask mactex        # macOS
# sudo apt install texlive-latex-extra texlive-fonts-recommended  # Ubuntu

# Run the app
streamlit run app.py
```

---

## Step 4 — Deploy to Streamlit Community Cloud

1. Push your repo to **GitHub** (public or private).
   - Confirm `.streamlit/secrets.toml` is **NOT** committed.

2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.

3. Select your repo, branch (`main`), and set **Main file path** to `app.py`.

4. Click **Advanced settings → Secrets** and paste the **entire contents**
   of your `secrets.toml` file into the text box.

5. Click **Deploy**.

> **Cold-start warning**: The first boot after a period of inactivity takes
> **3–5 minutes** because Streamlit Community Cloud runs `apt-get install`
> for the packages in `packages.txt` (the LaTeX distribution).
> Subsequent cold starts are cached and much faster.

---

## Step 5 — Updating your profile permanently

Streamlit Secrets are **read-only at runtime** — the app cannot write back.
When you upload a new PDF CV, the parsed profile is active for that browser
session only.

To make it permanent:

1. Upload your PDF → expand the **"Extracted JSON — copy to secrets.toml"**
   panel in the sidebar.
2. Convert the JSON to TOML format (or copy the structure from the template).
3. In Streamlit Community Cloud → **App Settings → Secrets**, update the
   `[profile]` section.
4. Click **Save** — the app reboots automatically with your new profile.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `pdflatex: command not found` | Verify `packages.txt` is in repo root and redeploy |
| `LaTeX compilation failed` | Check the LaTeX source in the **CV Preview** tab for escaping issues |
| `Gemini JSON parse error` | Retry — sometimes the model includes extra commentary; the parser retries |
| Slow cold starts (5+ min) | Expected — LaTeX package install. Warms up after first request |
| PDF has no text extracted | Upload a text-based PDF (not a scanned image) |
