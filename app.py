import streamlit as st
import anthropic
import json
import io
from datetime import date
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

st.set_page_config(
    page_title="HireKit - AI Interview Kit Generator",
    page_icon="",
    layout="wide"
)

# ── Styles ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main-header { font-size: 2.4rem; font-weight: 800; color: #1a1a2e; }
.sub-header  { font-size: 1.1rem; color: #555; margin-bottom: 1.5rem; }
.section-box {
    background: #f8f9fa; border-left: 4px solid #4f46e5;
    padding: 1rem 1.25rem; border-radius: 0 8px 8px 0; margin: 1rem 0;
}
.question-card {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 8px; padding: 1rem; margin: 0.5rem 0;
}
.competency-tag {
    background: #ede9fe; color: #4f46e5;
    padding: 2px 8px; border-radius: 99px; font-size: 0.78rem; font-weight: 600;
}
.red-flag { color: #dc2626; font-size: 0.9rem; }
.good-sign { color: #16a34a; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">HireKit</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Paste a job description. Get a complete interviewer kit in 30 seconds.</div>', unsafe_allow_html=True)
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-api03-...",
        help="Your key is never stored. Get one at console.anthropic.com"
    )
    st.caption("Bring your own key. Zero data stored.")
    st.divider()
    role_level = st.selectbox(
        "Role Level",
        ["Junior (0-2 yrs)", "Mid-Level (2-5 yrs)", "Senior (5-10 yrs)", "Principal / Staff", "Director / VP", "Executive / C-Suite"]
    )
    industry = st.selectbox(
        "Industry",
        ["SaaS / Tech", "E-commerce / Retail", "Healthcare", "Finance / Fintech", "Agency / Services",
         "Manufacturing / Operations", "Education", "Non-profit", "Media / Entertainment", "Other"]
    )
    num_behavioral = st.slider("Behavioral Questions", 8, 20, 12)
    num_technical = st.slider("Technical Questions", 3, 8, 5)
    st.divider()
    st.caption("Built with Claude 3.5 Haiku · Powered by Anthropic")

# ── Main Input ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 2])
with col1:
    job_title = st.text_input("Job Title", placeholder="e.g. Senior Product Manager")
with col2:
    company_context = st.text_input(
        "Company Context (optional)",
        placeholder="e.g. 30-person B2B SaaS startup, Series A, remote-first"
    )

job_description = st.text_area(
    "Job Description",
    height=200,
    placeholder="Paste the full job description here. The more detail you provide, the more specific the kit will be.\n\nNo JD? Just describe the role in a few sentences."
)

generate_btn = st.button("Generate Interview Kit", type="primary", use_container_width=True)

# ── Prompt ─────────────────────────────────────────────────────────────────────
def build_prompt(job_title, job_description, role_level, industry, company_context, num_behavioral, num_technical):
    return f"""You are a senior hiring consultant and organizational psychologist with 15+ years placing candidates at high-growth companies. Create a rigorous, specific interview kit for this role.

Job Title: {job_title}
Role Level: {role_level}
Industry: {industry}
Company Context: {company_context or "Not specified"}

Job Description:
{job_description or "(No description provided - infer from job title and level)"}

Generate a complete interview kit as a JSON object with EXACTLY this structure. Be highly specific to this role - no generic questions. Every question should only make sense for THIS job.

{{
  "role_summary": "2-3 sentences describing what success looks like in the first 90 days",
  "key_competencies": [
    {{
      "name": "Competency name (5-6 total)",
      "description": "Why this competency matters specifically for this role",
      "scoring_guide": {{
        "1": "Specific observable behavior that earns a 1 (poor fit)",
        "3": "Specific observable behavior that earns a 3 (acceptable)",
        "5": "Specific observable behavior that earns a 5 (exceptional)"
      }}
    }}
  ],
  "behavioral_questions": [
    {{
      "question": "Tell me about a time when... (specific, role-relevant, open-ended)",
      "competency_tested": "Name of the competency this tests",
      "what_to_listen_for": "2-3 specific signals that indicate a strong answer",
      "red_flags": "1-2 specific warning signs in their answer"
    }}
  ],
  "technical_questions": [
    {{
      "question": "Role-specific technical or skills-based question",
      "what_strong_answer_includes": "Key elements an expert would include"
    }}
  ],
  "dealbreaker_signals": [
    "Specific red flag behavior or response that should immediately disqualify"
  ],
  "onboarding_milestones": [
    "Day 1: Specific milestone",
    "Week 1: Specific milestone",
    "Month 1: Specific milestone",
    "Month 3: Measurable outcome"
  ],
  "candidate_comparison_criteria": [
    "Specific dimension to compare candidates on (e.g. 'Depth of experience with X')"
  ]
}}

Rules:
- Generate exactly {num_behavioral} behavioral questions and {num_technical} technical questions
- Every question must be specific to the role, not generic
- Dealbreaker signals: 6-8 items
- Candidate comparison criteria: 5-6 items
- Return ONLY valid JSON, no markdown fences, no explanation"""


# ── PDF Generator ──────────────────────────────────────────────────────────────
def generate_pdf(kit: dict, job_title: str, role_level: str, industry: str) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch
    )

    styles = getSampleStyleSheet()
    PURPLE = colors.HexColor("#4f46e5")
    LIGHT_PURPLE = colors.HexColor("#ede9fe")
    DARK = colors.HexColor("#1a1a2e")
    MUTED = colors.HexColor("#6b7280")
    RED = colors.HexColor("#dc2626")
    GREEN = colors.HexColor("#16a34a")

    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=22, textColor=DARK, spaceAfter=4, fontName="Helvetica-Bold")
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, textColor=PURPLE, spaceBefore=16, spaceAfter=6, fontName="Helvetica-Bold")
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=15, textColor=DARK)
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=9, leading=13, textColor=MUTED)
    label = ParagraphStyle("Label", parent=styles["Normal"], fontSize=9, fontName="Helvetica-Bold", textColor=PURPLE)
    red_p = ParagraphStyle("Red", parent=styles["Normal"], fontSize=9, leading=13, textColor=RED)
    green_p = ParagraphStyle("Green", parent=styles["Normal"], fontSize=9, leading=13, textColor=GREEN)

    story = []

    # Cover
    story.append(Paragraph("INTERVIEW KIT", ParagraphStyle("Cover", parent=h1, fontSize=11, textColor=PURPLE, fontName="Helvetica-Bold")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(job_title, h1))
    story.append(Paragraph(f"{role_level} · {industry} · Generated {date.today().strftime('%B %d, %Y')}", small))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=PURPLE))
    story.append(Spacer(1, 12))

    # Role Summary
    story.append(Paragraph("ROLE OVERVIEW", h2))
    story.append(Paragraph(kit.get("role_summary", ""), body))
    story.append(Spacer(1, 12))

    # Competencies
    story.append(Paragraph("COMPETENCY FRAMEWORK", h2))
    for comp in kit.get("key_competencies", []):
        story.append(Paragraph(comp["name"].upper(), label))
        story.append(Paragraph(comp["description"], body))
        sg = comp.get("scoring_guide", {})
        rubric_data = [
            [Paragraph("Score", label), Paragraph("Observable Behavior", label)],
            [Paragraph("1 - Poor", red_p), Paragraph(sg.get("1", ""), small)],
            [Paragraph("3 - OK", body), Paragraph(sg.get("3", ""), small)],
            [Paragraph("5 - Strong", green_p), Paragraph(sg.get("5", ""), small)],
        ]
        rubric_table = Table(rubric_data, colWidths=[1.1*inch, 5.6*inch])
        rubric_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), LIGHT_PURPLE),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(rubric_table)
        story.append(Spacer(1, 10))

    story.append(PageBreak())

    # Behavioral Questions
    story.append(Paragraph(f"BEHAVIORAL QUESTIONS ({len(kit.get('behavioral_questions',[]))})", h2))
    for i, q in enumerate(kit.get("behavioral_questions", []), 1):
        story.append(Paragraph(f"Q{i}: {q['question']}", ParagraphStyle("QBody", parent=body, fontName="Helvetica-Bold")))
        story.append(Paragraph(f"Competency: {q.get('competency_tested','')}", label))
        story.append(Paragraph(f"Listen for: {q.get('what_to_listen_for','')}", green_p))
        story.append(Paragraph(f"Red flag: {q.get('red_flags','')}", red_p))
        story.append(Spacer(1, 10))

    story.append(PageBreak())

    # Technical Questions
    story.append(Paragraph(f"TECHNICAL / SKILLS QUESTIONS ({len(kit.get('technical_questions',[]))})", h2))
    for i, q in enumerate(kit.get("technical_questions", []), 1):
        story.append(Paragraph(f"Q{i}: {q['question']}", ParagraphStyle("QBody", parent=body, fontName="Helvetica-Bold")))
        story.append(Paragraph(f"Strong answer includes: {q.get('what_strong_answer_includes','')}", small))
        story.append(Spacer(1, 10))

    # Dealbreakers
    story.append(Paragraph("DEALBREAKER SIGNALS", h2))
    story.append(Paragraph("If you observe any of the following, do not proceed to offer:", small))
    story.append(Spacer(1, 6))
    for signal in kit.get("dealbreaker_signals", []):
        story.append(Paragraph(f"  {signal}", red_p))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 12))

    # Comparison Matrix
    story.append(Paragraph("CANDIDATE COMPARISON MATRIX", h2))
    criteria = kit.get("candidate_comparison_criteria", [])
    matrix_header = [Paragraph("Criterion", label), Paragraph("Candidate A", label),
                     Paragraph("Candidate B", label), Paragraph("Candidate C", label)]
    matrix_data = [matrix_header]
    for c in criteria:
        matrix_data.append([Paragraph(c, small), Paragraph("", small), Paragraph("", small), Paragraph("", small)])
    matrix_data.append([Paragraph("TOTAL / DECISION", label), Paragraph("", label), Paragraph("", label), Paragraph("", label)])
    matrix_table = Table(matrix_data, colWidths=[3.0*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    matrix_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), LIGHT_PURPLE),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#f1f5f9")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(matrix_table)

    story.append(PageBreak())

    # Onboarding
    story.append(Paragraph("ONBOARDING MILESTONES (if hired)", h2))
    for milestone in kit.get("onboarding_milestones", []):
        story.append(Paragraph(f"  {milestone}", body))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Generated by HireKit · hirekit.streamlit.app · Powered by Anthropic Claude", small))

    doc.build(story)
    return buf.getvalue()


# ── Generation ─────────────────────────────────────────────────────────────────
if generate_btn:
    if not api_key:
        st.error("Add your Anthropic API key in the sidebar to continue.")
        st.stop()
    if not job_title:
        st.error("Enter a job title.")
        st.stop()

    with st.spinner("Generating your interview kit... (~15 seconds)"):
        try:
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": build_prompt(
                        job_title, job_description, role_level,
                        industry, company_context, num_behavioral, num_technical
                    )
                }]
            )
            raw = message.content[0].text.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            kit = json.loads(raw)
        except json.JSONDecodeError as e:
            st.error(f"JSON parse error: {e}. Raw response logged below.")
            st.code(raw[:2000])
            st.stop()
        except Exception as e:
            st.error(f"Generation failed: {e}")
            st.stop()

    st.success("Interview kit ready.")
    st.divider()

    # ── Display Results ──────────────────────────────────────────────────────
    st.subheader(f"Interview Kit: {job_title}")
    st.caption(f"{role_level} · {industry} · {date.today().strftime('%B %d, %Y')}")

    # Role Summary
    with st.expander("Role Overview", expanded=True):
        st.markdown(f'<div class="section-box">{kit.get("role_summary","")}</div>', unsafe_allow_html=True)

    # Competencies
    with st.expander("Competency Framework", expanded=True):
        for comp in kit.get("key_competencies", []):
            st.markdown(f"**{comp['name']}**")
            st.caption(comp["description"])
            sg = comp.get("scoring_guide", {})
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**1 - Poor**")
                st.caption(sg.get("1", ""))
            with col2:
                st.markdown(f"**3 - Acceptable**")
                st.caption(sg.get("3", ""))
            with col3:
                st.markdown(f"**5 - Strong**")
                st.caption(sg.get("5", ""))
            st.divider()

    # Behavioral Questions
    with st.expander(f"Behavioral Questions ({len(kit.get('behavioral_questions',[]))})", expanded=False):
        for i, q in enumerate(kit.get("behavioral_questions", []), 1):
            st.markdown(f'<div class="question-card">'
                f'<b>Q{i}:</b> {q["question"]}<br/>'
                f'<span class="competency-tag">{q.get("competency_tested","")}</span><br/><br/>'
                f'<span class="good-sign">Listen for: {q.get("what_to_listen_for","")}</span><br/>'
                f'<span class="red-flag">Red flag: {q.get("red_flags","")}</span>'
                '</div>', unsafe_allow_html=True)

    # Technical Questions
    with st.expander(f"Technical Questions ({len(kit.get('technical_questions',[]))})", expanded=False):
        for i, q in enumerate(kit.get("technical_questions", []), 1):
            st.markdown(f"**Q{i}:** {q['question']}")
            st.caption(f"Strong answer includes: {q.get('what_strong_answer_includes','')}")
            st.divider()

    # Dealbreakers
    with st.expander("Dealbreaker Signals", expanded=False):
        for signal in kit.get("dealbreaker_signals", []):
            st.markdown(f'<span class="red-flag"> {signal}</span>', unsafe_allow_html=True)

    # Comparison Matrix
    with st.expander("Candidate Comparison Matrix", expanded=False):
        criteria = kit.get("candidate_comparison_criteria", [])
        import pandas as pd
        df = pd.DataFrame({
            "Criterion": criteria,
            "Candidate A": [""] * len(criteria),
            "Candidate B": [""] * len(criteria),
            "Candidate C": [""] * len(criteria),
        })
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Onboarding
    with st.expander("Onboarding Milestones (if hired)", expanded=False):
        for milestone in kit.get("onboarding_milestones", []):
            st.markdown(f"- {milestone}")

    st.divider()

    # PDF Download
    try:
        pdf_bytes = generate_pdf(kit, job_title, role_level, industry)
        safe_title = job_title.lower().replace(" ", "-").replace("/", "-")
        st.download_button(
            label="Download Interview Kit as PDF",
            data=pdf_bytes,
            file_name=f"hirekit-{safe_title}-{date.today().isoformat()}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
    except Exception as e:
        st.warning(f"PDF generation failed ({e}). Use the on-screen kit instead.")

    # Store in session state
    st.session_state["last_kit"] = kit
    st.session_state["last_title"] = job_title

# ── Footer / Empty State ───────────────────────────────────────────────────────
if not generate_btn and "last_kit" not in st.session_state:
    st.markdown("""
    ### What you get
    - **Competency framework** with 5-6 role-specific dimensions and 1-5 scoring rubrics
    - **Behavioral questions** mapped to each competency with what to listen for and red flags
    - **Technical questions** with model answer guidance
    - **Dealbreaker signals** to stop an interview early
    - **Candidate comparison matrix** to score multiple finalists
    - **Onboarding milestones** if the candidate is hired
    - **PDF download** ready to print and bring to the interview

    ### Who it's for
    Startup founders, hiring managers, and freelance recruiters who need a rigorous interview structure
    for a specific role in under a minute. Not a generic question bank.

    ### Privacy
    Your API key and job descriptions are never stored. Everything runs in your browser session.
    """)
