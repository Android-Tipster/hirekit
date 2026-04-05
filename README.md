# HireKit

**Paste a job description. Get a complete interviewer kit in 30 seconds.**

Live at **[hirekit-kohl.vercel.app](https://hirekit-kohl.vercel.app)**

---

## What it generates

From a single job description, HireKit produces:

- **Role Overview** — what success looks like in the first 90 days (specific to this role)
- **Competency Framework** — 5-6 role-specific competencies, each with a 1/3/5 behavioral scoring rubric
- **Behavioral Questions** — 12 open-ended questions mapped to specific competencies, with "listen for" guidance and red flag warnings for each
- **Technical Questions** — 5 role-specific skills questions with model answer guidance
- **Dealbreaker Signals** — 6-8 specific warning signs that should end the process early
- **Candidate Comparison Matrix** — a printable scoring table for comparing multiple finalists
- **Onboarding Milestones** — Day 1 / Week 1 / Month 1 / Month 3 goals if the candidate is hired
- **PDF download** — formatted, print-ready document for the interview room

Every output is specific to the job description you provide. Not a generic question bank.

---

## Who it's for

Startup founders, hiring managers at 10-200 person companies, and freelance recruiters who:
- Need a rigorous interview structure for a specific role in under a minute
- Don't want to pay $600/month for an enterprise ATS just to get decent interview questions
- Are tired of Googling "behavioral interview questions for software engineers" and getting the same 10 generic answers

---

## How to use

1. Go to [hirekit-kohl.vercel.app](https://hirekit-kohl.vercel.app)
2. Enter the job title and paste the job description
3. Select the role level and industry
4. Enter your [Anthropic API key](https://console.anthropic.com) (BYOK — never stored)
5. Click Generate
6. Download the PDF or print directly

No account required. No signup.

---

## Privacy

Your API key and job descriptions are sent directly to the Anthropic API. They are never logged, stored, or processed by any intermediary server beyond what Anthropic's API requires. The Vercel function is stateless.

---

## Run locally (Streamlit version)

```bash
git clone https://github.com/Android-Tipster/hirekit
cd hirekit
pip install streamlit anthropic reportlab pandas
streamlit run app.py
```

---

## Architecture

- `index.html` — Vanilla JS frontend with jsPDF for client-side PDF generation
- `api/generate.py` — Vercel Python serverless function (Claude Haiku via Anthropic API)
- `app.py` — Streamlit version for local use
- `vercel.json` — Zero-config routing

The frontend makes a POST to `/api/generate`, receives structured JSON, renders the kit in-page, and uses jsPDF + jspdf-autotable for the PDF download. No framework dependencies on the frontend.

---

## Revenue path

| Tier | Price | What's included |
|------|-------|-----------------|
| Free | $0 | BYOK (bring your own Anthropic API key) |
| Pro (coming) | $15/month | No API key needed, 50 kits/month, custom branding on PDF |
| Team (coming) | $29/month | Shared workspace, kit history, ATS export |

---

Built with [Claude Haiku](https://anthropic.com) · Deployed on [Vercel](https://vercel.com) · April 2026
