"""
facial_analysis.py
Shared facial-expression analysis helper, mirroring the working
analyze_facial_expression() logic from app.py, so both the single-user
Video Practice page and the Group Practice Call page can use identical,
already-proven analysis logic.
"""

import base64
import json
import os
import streamlit as st
from anthropic import Anthropic

FACIAL_PROMPT = """You are an expert communication coach analyzing a student during a sponsor meeting practice session.
Evaluate their body language and presentation:
1. EYE CONTACT (0-25): Looking at camera directly?
2. CONFIDENCE (0-25): Posture, facial expression?
3. ENGAGEMENT (0-25): Look interested and present?
4. PROFESSIONALISM (0-25): Appearance and setting appropriate?
Return ONLY this JSON:
{"eye_contact":0,"confidence":0,"engagement":0,"professionalism":0,"total":0,"observations":["o1","o2","o3"],"improvements":["i1","i2"],"quick_wins":["q1","q2"],"summary":"2-3 sentence assessment"}"""


def get_client():
    try:
        key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        key = os.environ.get("ANTHROPIC_API_KEY", "")
    return Anthropic(api_key=key)


def analyze_facial_expression(image_bytes):
    try:
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        r = get_client().messages.create(
            model="claude-sonnet-4-6", max_tokens=800,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                {"type": "text", "text": FACIAL_PROMPT}
            ]}])
        raw = r.content[0].text.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        st.error(f"Analysis error: {e}")
        return None
