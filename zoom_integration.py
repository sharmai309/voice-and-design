"""
zoom_integration.py
Server-to-Server OAuth integration with Zoom's REST API.

Creates a real Zoom meeting for each Group Practice Call room so students
join an actual Zoom meeting instead of a home-grown video call.

Setup (one-time, on the Zoom Marketplace):
1. Go to https://marketplace.zoom.us/ -> Develop -> Build App -> "Server-to-Server OAuth".
2. Copy the Account ID, Client ID, and Client Secret it gives you.
3. Under Scopes, add: meeting:write:meeting, meeting:write:meeting:admin
   (or the newer granular equivalents Zoom's UI suggests for "create meetings").
4. Add the three values to .streamlit/secrets.toml:
       ZOOM_ACCOUNT_ID = "..."
       ZOOM_CLIENT_ID = "..."
       ZOOM_CLIENT_SECRET = "..."
5. Activate the app (Server-to-Server apps activate instantly, no review needed).
"""

import os
import requests
import streamlit as st

TOKEN_URL = "https://zoom.us/oauth/token"
API_BASE = "https://api.zoom.us/v2"


def _get_secret(key):
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, "")


def zoom_configured() -> bool:
    return bool(_get_secret("ZOOM_ACCOUNT_ID") and _get_secret("ZOOM_CLIENT_ID") and _get_secret("ZOOM_CLIENT_SECRET"))


@st.cache_data(ttl=3000, show_spinner=False)
def get_zoom_access_token():
    """Server-to-Server OAuth: exchange account credentials for a short-lived access token.
    Cached for 50 minutes (tokens last ~1 hour) so we don't re-auth on every call."""
    account_id = _get_secret("ZOOM_ACCOUNT_ID")
    client_id = _get_secret("ZOOM_CLIENT_ID")
    client_secret = _get_secret("ZOOM_CLIENT_SECRET")
    if not (account_id and client_id and client_secret):
        raise RuntimeError(
            "Missing Zoom credentials. Add ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, and "
            "ZOOM_CLIENT_SECRET to .streamlit/secrets.toml — see zoom_integration.py header."
        )
    resp = requests.post(
        TOKEN_URL,
        params={"grant_type": "account_credentials", "account_id": account_id},
        auth=(client_id, client_secret),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def create_zoom_meeting(topic: str, duration_minutes: int = 60):
    """Creates an instant Zoom meeting and returns join/start info.
    Returns a dict {meeting_id, join_url, start_url, passcode} or None on failure."""
    try:
        token = get_zoom_access_token()
    except Exception as e:
        st.error(f"Zoom auth failed: {e}")
        return None

    payload = {
        "topic": topic[:200],
        "type": 1,  # instant meeting
        "duration": duration_minutes,
        "settings": {
            "join_before_host": True,
            "waiting_room": False,
            "host_video": True,
            "participant_video": True,
            "mute_upon_entry": False,
            "approval_type": 2,  # no registration required
        },
    }
    try:
        resp = requests.post(
            f"{API_BASE}/users/me/meetings",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "meeting_id": data.get("id"),
            "join_url": data.get("join_url"),
            "start_url": data.get("start_url"),
            "passcode": data.get("password", ""),
        }
    except requests.exceptions.HTTPError as e:
        detail = e.response.text if e.response is not None else str(e)
        st.error(f"Could not create Zoom meeting: {detail}")
        return None
    except Exception as e:
        st.error(f"Could not create Zoom meeting: {e}")
        return None


def end_zoom_meeting(meeting_id):
    """Best-effort: ends a Zoom meeting early when a Group Practice Call room finishes."""
    try:
        token = get_zoom_access_token()
        requests.put(
            f"{API_BASE}/meetings/{meeting_id}/status",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"action": "end"},
            timeout=15,
        )
    except Exception:
        pass
