"""
ui_theme.py
Shared design system for Capstone Coach.

Every page (Home / Practice / Video / Progress / About / Group Practice Call)
imports inject_theme() so the app has ONE visual language instead of each
page re-inventing its own colors, spacing, and typography. This also fixes
the previous gap where the Group Practice Call page had no styling at all.
"""

import base64
import os
import streamlit as st

THEME_CSS = """
<style>
[data-testid="stAppViewContainer"] { background: #ffffff; }
[data-testid="stSidebar"] { background: #0f0f1a; }
[data-testid="stSidebar"] * { color: #ffffff !important; }
[data-testid="stSidebar"] .stRadio label { color: #ffffff !important; }
/* Hide Streamlit's auto-generated multipage nav — we render our own below,
   so both the Home sidebar and the Group Practice Call page share one nav. */
[data-testid="stSidebarNav"] { display: none; }
#MainMenu, footer { visibility: hidden; }
header { visibility: hidden; }
/* The sidebar expand arrow (stExpandSidebarButton) lives inside <header>,
   which we hide above for a cleaner look. That was suppressing the only
   control that lets a collapsed sidebar be reopened — force just this
   button back to visible/clickable, styled as a small dark tab. */
header [data-testid="stExpandSidebarButton"] {
  visibility: visible !important;
  display: flex !important;
  position: fixed !important;
  top: 10px !important;
  left: 10px !important;
  z-index: 999999 !important;
  background: #0f0f1a !important;
  border-radius: 8px !important;
  padding: 6px !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.25);
}
header [data-testid="stExpandSidebarButton"] svg { fill: #ffffff !important; color: #ffffff !important; }
.block-container { padding-top: 2rem; max-width: 1200px; }

/* ---------- Typography ---------- */
.hero-title { font-size: 3.5rem; font-weight: 800; background: linear-gradient(135deg, #7A1F2E, #B3273A); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; line-height: 1.2; margin-bottom: 1rem; }
.hero-sub { font-size: 1.2rem; color: #6B7280; margin-bottom: 2rem; line-height: 1.6; }
.hero-label { font-size: 0.85rem; font-weight: 600; color: #6B7280; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.5rem; }
.section-header { font-size: 1.8rem; font-weight: 700; color: #111827; margin-bottom: 8px; }
.section-sub { font-size: 1rem; color: #6B7280; margin-bottom: 24px; }

/* ---------- Cards ---------- */
.persona-card { background: #ffffff; border: 1px solid #E5E7EB; border-radius: 16px; padding: 24px; transition: all 0.2s; height: 100%; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
.persona-card:hover { border-color: #9F2B3F; box-shadow: 0 8px 25px rgba(159,43,63,0.12); transform: translateY(-2px); }
.persona-icon { font-size: 2.5rem; margin-bottom: 12px; }
.persona-name { font-size: 1.1rem; font-weight: 700; color: #111827; margin-bottom: 4px; }
.persona-company { font-size: 0.8rem; color: #9CA3AF; margin-bottom: 8px; }
.persona-desc { font-size: 0.9rem; color: #6B7280; line-height: 1.5; margin-bottom: 12px; }
.step-card { background: #F9FAFB; border-radius: 16px; padding: 24px; text-align: center; height: 100%; transition: transform .2s ease, box-shadow .2s ease; }
.step-card:hover { transform: translateY(-4px); box-shadow: 0 10px 24px rgba(0,0,0,0.06); }

/* ---------- Badges & hints ---------- */
.difficulty-badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.diff-1 { background: #D1FAE5; color: #065F46; }
.diff-2 { background: #E5E7EB; color: #374151; }
.diff-3 { background: #FEF3C7; color: #92400E; }
.diff-4 { background: #FEE2E2; color: #991B1B; }
.diff-5 { background: #EDE9FE; color: #5B21B6; }
.hint-bubble { background: #FBEAEC; border-left: 3px solid #9F2B3F; padding: 8px 12px; border-radius: 0 8px 8px 0; font-size: 0.85rem; color: #7A1F2E; margin: 4px 0 12px 48px; }

/* ---------- Group Practice Call components ---------- */
.room-banner { background: linear-gradient(135deg,#FBEAEC,#F7DEE1); border-radius: 16px; padding: 18px 22px; margin-bottom: 18px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; }
.room-code-pill { background:#ffffff; border-radius:10px; padding:8px 16px; font-weight:800; font-size:1.15rem; letter-spacing:0.12em; color:#9F2B3F; box-shadow:0 2px 8px rgba(0,0,0,0.06); }
.student-chip { display:flex; align-items:center; gap:8px; background:#F9FAFB; border:1px solid #E5E7EB; border-radius:12px; padding:10px 14px; font-weight:600; font-size:0.9rem; color:#111827; margin-bottom:8px; transition: all .2s ease; }
.student-chip.speaking { background:#FBEAEC; border-color:#9F2B3F; }
.student-chip.done { background:#ECFDF5; border-color:#10B981; color:#065F46; }
.live-dot { width:9px; height:9px; border-radius:50%; background:#EF4444; display:inline-block; animation: pulse 1.4s infinite; }
@keyframes pulse {
  0%   { box-shadow: 0 0 0 0 rgba(239,68,68,.55); }
  70%  { box-shadow: 0 0 0 8px rgba(239,68,68,0); }
  100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
}

/* ---------- Buttons ---------- */
.stButton button { border-radius: 10px !important; font-weight: 600 !important; transition: all 0.2s !important; }
.stButton button[kind="primary"] { background: linear-gradient(135deg, #7A1F2E, #B3273A) !important; border: none !important; }
.stButton button:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(159,43,63,0.18); }

/* ---------- CTA banner (homepage "Ready to practice?") ----------
   The text block and the button below it are meant to read as ONE
   pill-shaped card, not two stacked rectangles with a visible seam. */
.st-key-cta_banner .cta-card {
  background: linear-gradient(135deg, #7A1F2E, #B3273A);
  border-radius: 20px 20px 0 0;
  padding: 36px 40px 18px;
  text-align: center;
  color: #ffffff;
}
.st-key-cta_banner div[data-testid="stVerticalBlock"] { gap: 0 !important; }
.st-key-cta_banner .stButton { margin-top: 0 !important; }
.st-key-cta_banner .stButton button[kind="primary"] {
  background: #6E1B29 !important;
  border-radius: 0 0 20px 20px !important;
  border-top: 1px solid rgba(255,255,255,0.15) !important;
  padding-top: 16px !important;
  padding-bottom: 16px !important;
  font-size: 1rem !important;
}
.st-key-cta_banner .stButton button[kind="primary"]:hover {
  background: #7f2030 !important;
  transform: none;
}

/* ---------- Entrance animation (Animation Framework: fade + stagger) ---------- */
@keyframes fadeInUp { from { opacity:0; transform: translateY(18px); } to { opacity:1; transform: translateY(0); } }
.fade-in { animation: fadeInUp .55s ease both; }
.fade-in.d1 { animation-delay: .05s; }
.fade-in.d2 { animation-delay: .12s; }
.fade-in.d3 { animation-delay: .19s; }
.fade-in.d4 { animation-delay: .26s; }
.fade-in.d5 { animation-delay: .33s; }
.fade-in.d6 { animation-delay: .40s; }
</style>
"""


def inject_theme():
    """Call once near the top of every page script."""
    st.markdown(THEME_CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _load_logo_b64():
    path = os.path.join(os.path.dirname(__file__), "assets", "uchicago_logo.png")
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""


def sidebar_brand():
    """Shared sidebar logo block, identical on every page."""
    logo_b64 = _load_logo_b64()
    logo_html = (
        f'<div style="background:#ffffff;border-radius:12px;padding:14px 16px;margin-bottom:14px;">'
        f'<img src="data:image/png;base64,{logo_b64}" style="width:100%;display:block;">'
        f'</div>'
    ) if logo_b64 else ""
    st.sidebar.markdown(f"""
<div style="padding:16px 0 8px;">
  {logo_html}
  <div style="font-size:1.3rem;font-weight:800;color:white;margin-bottom:4px;">🎓 Capstone Coach</div>
  <div style="font-size:0.75rem;color:#9CA3AF;">Sponsor Meeting Simulator</div>
</div>
""", unsafe_allow_html=True)
