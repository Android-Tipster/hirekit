from http.server import BaseHTTPRequestHandler
import json
import anthropic
from json_repair import repair_json


PROMPT_TEMPLATE = """You are a senior hiring consultant and organizational psychologist. Create a rigorous, specific interview kit.

Job Title: {job_title}
Role Level: {role_level}
Industry: {industry}
Company Context: {company_context}

Job Description:
{job_description}

Generate a complete interview kit as JSON. Be highly specific — every question must only make sense for THIS role.

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{{
  "role_summary": "2-3 sentences on what success looks like in the first 90 days",
  "key_competencies": [
    {{
      "name": "Competency Name",
      "description": "Why this matters for this specific role",
      "scoring_guide": {{
        "1": "Observable behavior that earns a 1 — specific to this role",
        "3": "Observable behavior that earns a 3",
        "5": "Observable behavior that earns a 5 — what exceptional looks like"
      }}
    }}
  ],
  "behavioral_questions": [
    {{
      "question": "Tell me about a time when... (role-specific, open-ended)",
      "competency_tested": "Name of competency",
      "what_to_listen_for": "2-3 specific signals of a strong answer",
      "red_flags": "1-2 warning signs"
    }}
  ],
  "technical_questions": [
    {{
      "question": "Technical or skills-based question specific to this role",
      "what_strong_answer_includes": "Key elements an expert answer would include"
    }}
  ],
  "dealbreaker_signals": [
    "Specific red flag that should end the process"
  ],
  "onboarding_milestones": [
    "Day 1: specific goal",
    "Week 1: specific goal",
    "Month 1: measurable outcome",
    "Month 3: measurable outcome"
  ],
  "candidate_comparison_criteria": [
    "Specific dimension to score candidates on"
  ]
}}

Generate exactly {num_behavioral} behavioral questions and {num_technical} technical questions.
Include 6-8 dealbreaker signals and 5-6 comparison criteria."""


class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))

            api_key = body.get("api_key", "").strip()
            if not api_key:
                self._error(400, "api_key is required")
                return

            job_title = body.get("job_title", "").strip()
            if not job_title:
                self._error(400, "job_title is required")
                return

            prompt = PROMPT_TEMPLATE.format(
                job_title=job_title,
                job_description=body.get("job_description", "(not provided)"),
                role_level=body.get("role_level", "Mid-Level"),
                industry=body.get("industry", "Tech / SaaS"),
                company_context=body.get("company_context", "not specified"),
                num_behavioral=int(body.get("num_behavioral", 12)),
                num_technical=int(body.get("num_technical", 5)),
            )

            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}],
            )

            raw = message.content[0].text.strip()
            if raw.startswith("```"):
                parts = raw.split("```")
                raw = parts[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            try:
                kit = json.loads(raw)
            except json.JSONDecodeError:
                # LLMs occasionally produce slightly malformed JSON; repair it
                kit = json.loads(repair_json(raw))
            self._json(200, kit)

        except anthropic.AuthenticationError:
            self._error(401, "Invalid Anthropic API key.")
        except anthropic.RateLimitError:
            self._error(429, "Rate limit hit. Wait a moment and try again.")
        except json.JSONDecodeError as e:
            self._error(500, f"Claude returned invalid JSON: {e}")
        except Exception as e:
            self._error(500, str(e))

    def _json(self, status, data):
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def _error(self, status, message):
        self._json(status, {"error": message})
