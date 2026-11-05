import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
import json
import urllib.request

# ==============================================================================
# CONFIGURATION & PAGE SETUP
# ==============================================================================
st.set_page_config(
    page_title="Music and Media Habits Survey",
    page_icon="🎵",
    layout="centered"
)

# Custom CSS for clean UI styling
st.markdown("""
<style>
    .main { max-width: 750px; margin: 0 auto; }
    .stButton>button { width: 100%; border-radius: 6px; height: 3em; font-weight: bold; }
    .stAlert { border-radius: 6px; }
    .css-1v0mb0e { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# File to store participant responses locally
DATA_FILE = "survey_responses.csv"

# Optional: Paste your Google Apps Script Web App URL here to stream responses directly to Google Sheets!
# (Example: "https://script.google.com/macros/s/.../exec")
GOOGLE_SHEET_WEBHOOK_URL = st.secrets.get("GOOGLE_SHEET_WEBHOOK_URL", "")

# Directories to search for audio files
SEARCH_AUDIO_DIRS = [
    "./01_Prescreening_Survey_Audio",
    "./audio",
    "./Pre screeing audio",
    ".",
    r"C:\Users\akshi\OneDrive\Desktop\Pre screeing audio"
]

def find_audio_file(clip_id, file_num):
    extensions = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac']
    names_to_try = [
        f"clip{file_num}",
        f"clip{file_num:02d}",
        f"{clip_id}",
        f"song_real_{file_num:02d}"
    ]
    for audio_dir in SEARCH_AUDIO_DIRS:
        if not os.path.exists(audio_dir):
            continue
        for name in names_to_try:
            for ext in extensions:
                candidate = os.path.join(audio_dir, f"{name}{ext}")
                if os.path.exists(candidate):
                    return candidate
        all_files = sorted([
            f for f in os.listdir(audio_dir)
            if os.path.splitext(f)[1].lower() in extensions
        ])
        if 1 <= file_num <= len(all_files):
            return os.path.join(audio_dir, all_files[file_num - 1])
    return None

def send_to_google_sheet(data_dict):
    """Sends submission directly to Google Sheet Webhook if configured."""
    webhook_url = GOOGLE_SHEET_WEBHOOK_URL or st.session_state.get("webhook_url", "")
    if not webhook_url:
        return False
    try:
        # Convert nested dicts (like recognition_ratings) to JSON strings for tabular clarity
        payload = {}
        for k, v in data_dict.items():
            if isinstance(v, dict):
                payload[k] = json.dumps(v)
            else:
                payload[k] = str(v)
        
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            return response.status in (200, 201)
    except Exception as e:
        print(f"Google Sheet sync warning: {e}")
        return False

# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================
if "page" not in st.session_state:
    st.session_state.page = "welcome"
if "responses" not in st.session_state:
    st.session_state.responses = {}

def navigate_to(page_name):
    st.session_state.page = page_name
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# ==============================================================================
# PAGE 1: WELCOME & CONSENT
# ==============================================================================
if st.session_state.page == "welcome":
    st.title("🎵 Music and Media Habits Survey")
    st.caption("Estimated Time: ~6 minutes")

    st.info("""
    **Welcome!** We are interested in understanding the music and films people listen to and watch. 
    In this short survey, you will answer questions about your media habits and rate whether you recognize a few short audio clips.
    """)

    st.markdown("""
    ### Confidentiality & Consent
    - Your participation is voluntary, and you may stop at any time.
    - All data is strictly confidential and linked to an anonymous Participant Code.
    - Some participants who complete this survey may be invited to take part in a follow-up study.
    """)

    participant_id = st.text_input("Enter your assigned Participant ID (e.g., P001):", value=st.session_state.responses.get("participant_id", ""))
    consent = st.checkbox("I agree to participate in this survey.")

    if st.button("Begin Survey ➡️"):
        if not participant_id.strip():
            st.error("Please enter a valid Participant ID to proceed.")
        elif not consent:
            st.warning("Please check the consent box to proceed.")
        else:
            st.session_state.responses["participant_id"] = participant_id.strip()
            st.session_state.responses["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            navigate_to("section_a")

# ==============================================================================
# PAGE 2: SECTION A - ELIGIBILITY CHECKS
# ==============================================================================
elif st.session_state.page == "section_a":
    st.title("Section A: Basic Background")
    st.progress(0.2)

    st.subheader("Please answer the following basic questions:")

    age = st.number_input("A1. How old are you?", min_value=10, max_value=100, value=st.session_state.responses.get("age", 22))
    childhood = st.selectbox("A2. Where did you spend most of your childhood (up to age 15)?", ["India", "Another country"], index=0)
    hindi_comprehension = st.select_slider(
        "A3. How well do you understand the lyrics of Hindi songs?",
        options=[1, 2, 3, 4, 5],
        value=st.session_state.responses.get("hindi_comprehension", 4),
        format_func=lambda x: {1: "1 - Not at all", 2: "2 - Poorly", 3: "3 - Moderately", 4: "4 - Well", 5: "5 - Completely"}[x]
    )
    hearing_diff = st.radio("A4. Do you have any difficulty hearing through headphones?", ["No", "Yes"])
    vision = st.radio("A5. Is your vision normal, or normal when corrected with glasses/lenses?", ["Yes", "No"])
    musician = st.radio("A6. Are you a professional musician or studying music professionally?", ["No", "Yes"])
    headphones_avail = st.radio("A7. Do you have stereo headphones available to use for this study?", ["Yes", "No"])

    if st.button("Next: Section B ➡️"):
        st.session_state.responses.update({
            "age": age,
            "childhood": childhood,
            "hindi_comprehension": hindi_comprehension,
            "hearing_diff": hearing_diff,
            "vision": vision,
            "musician": musician,
            "headphones_avail": headphones_avail
        })
        navigate_to("section_b")

# ==============================================================================
# PAGE 3: SECTION B - DEMOGRAPHICS
# ==============================================================================
elif st.session_state.page == "section_b":
    st.title("Section B: Demographics & Device")
    st.progress(0.4)

    gender = st.selectbox("B1. Gender", ["Woman", "Man", "Another description", "Prefer not to say"])
    languages = st.text_input("B2. Which languages do you speak? (List in order of frequency)", value=st.session_state.responses.get("languages", "English, Hindi"))
    education = st.selectbox("B3. Highest level of education completed or in progress", ["High School", "Bachelor's Degree", "Master's Degree", "Doctorate / Professional", "Other"])
    region = st.text_input("B4. Which state or region did you grow up in?", value=st.session_state.responses.get("region", "Delhi"))
    device = st.selectbox("B5. Which device are you using for this study?", ["Laptop", "Desktop", "Tablet / Mobile"])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            navigate_to("section_a")
    with col2:
        if st.button("Next: Section C ➡️"):
            st.session_state.responses.update({
                "gender": gender,
                "languages": languages,
                "education": education,
                "region": region,
                "device": device
            })
            navigate_to("section_c")

# ==============================================================================
# PAGE 4: SECTION C - MUSIC AND MEDIA HABITS
# ==============================================================================
elif st.session_state.page == "section_c":
    st.title("Section C: Listening & Media Habits")
    st.progress(0.6)

    st.markdown("### Weekly Listening")
    c1_total_hours = st.selectbox("C1. In a typical week, how many hours do you listen to music in total?", ["None", "Under 1 hour", "1 to 3 hours", "4 to 7 hours", "8 to 14 hours", "15 or more hours"], index=3)

    st.markdown("### Weekly Music Hours by Genre")
    hours_bands = ["None", "Under 1 hour", "1 to 3 hours", "4 to 7 hours", "8 to 14 hours", "15 or more hours"]
    c2_bollywood_hrs = st.selectbox("Hindi film songs (Bollywood)", hours_bands, index=3)
    c2_western_hrs = st.selectbox("Western pop", hours_bands, index=2)
    c2_edm_hrs = st.selectbox("Electronic or dance music (EDM)", hours_bands, index=1)
    c2_classical_hrs = st.selectbox("Indian classical music", hours_bands, index=1)
    c2_calm_hrs = st.selectbox("Calm instrumental, piano, or lo-fi", hours_bands, index=2)

    st.markdown("### Media Exposure")
    c3_hindi_films_hrs = st.selectbox("C3. Weekly hours watching Hindi films or series:", hours_bands, index=2)
    c4_start_age = st.number_input("C4. At what age did you start regularly listening to Hindi film songs?", min_value=0, max_value=40, value=7)
    c5_home_exp = st.slider("C5. Growing up, how often was Hindi film music played at home or family gatherings?", 1, 5, 4)
    c6_event_exp = st.slider("C6. How often do you attend events where Hindi film songs are played (weddings, festivals, parties)?", 1, 5, 4)

    st.markdown("### Subjective Familiarity (1 = Not at all, 7 = Extremely)")
    c7_bollywood_fam = st.slider("Familiarity with Hindi film music", 1, 7, 6)
    c7_western_fam = st.slider("Familiarity with Western pop", 1, 7, 5)
    c7_edm_fam = st.slider("Familiarity with EDM", 1, 7, 4)
    c7_classical_fam = st.slider("Familiarity with Indian classical", 1, 7, 3)

    st.markdown("### Attention Check")
    c10_attention_1 = st.selectbox("C10. To show you are reading carefully, please choose 'Sometimes':", ["Never", "Rarely", "Sometimes", "Often", "Always"], index=0)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            navigate_to("section_b")
    with col2:
        if st.button("Next: Section D (Audio Recognition) ➡️"):
            st.session_state.responses.update({
                "c1_total_hours": c1_total_hours,
                "c2_bollywood_hrs": c2_bollywood_hrs,
                "c2_western_hrs": c2_western_hrs,
                "c2_edm_hrs": c2_edm_hrs,
                "c2_classical_hrs": c2_classical_hrs,
                "c2_calm_hrs": c2_calm_hrs,
                "c3_hindi_films_hrs": c3_hindi_films_hrs,
                "c4_start_age": c4_start_age,
                "c5_home_exp": c5_home_exp,
                "c6_event_exp": c6_event_exp,
                "c7_bollywood_fam": c7_bollywood_fam,
                "c7_western_fam": c7_western_fam,
                "c7_edm_fam": c7_edm_fam,
                "c7_classical_fam": c7_classical_fam,
                "c10_attention_1": c10_attention_1
            })
            navigate_to("section_d")

# ==============================================================================
# PAGE 5: SECTION D - SONG RECOGNITION TEST (11 CLIPS)
# ==============================================================================
elif st.session_state.page == "section_d":
    st.title("Section D: Short Audio Recognition Test")
    st.progress(0.8)

    st.info("""
    **Instructions:** Listen to each short audio clip using your headphones, then answer the recognition question below it.
    """)

    song_clips = [
        {"num": 1, "id": "song_real_01", "name": "Audio Clip 1", "type": "real"},
        {"num": 2, "id": "song_real_02", "name": "Audio Clip 2", "type": "real"},
        {"num": 3, "id": "song_real_03", "name": "Audio Clip 3", "type": "real"},
        {"num": 4, "id": "song_real_04", "name": "Audio Clip 4", "type": "real"},
        {"num": 5, "id": "song_foil_01", "name": "Audio Clip 5", "type": "foil"},
        {"num": 6, "id": "song_foil_01", "name": "Audio Clip 6", "type": "foil"},
        {"num": 7, "id": "attention_check_press_1", "name": "Audio Clip 7 (Attention Check)", "type": "attention"},
        {"num": 8, "id": "song_real_05", "name": "Audio Clip 8", "type": "real"},
        {"num": 9, "id": "song_foil_02", "name": "Audio Clip 9", "type": "foil"},
        {"num": 10, "id": "song_real_06", "name": "Audio Clip 10", "type": "real"},
        {"num": 11, "id": "song_real_07", "name": "Audio Clip 11", "type": "real"},
        {"num": 12, "id": "song_real_08", "name": "Audio Clip 12", "type": "real"},
    ]

    rec_ratings = {}
    for clip in song_clips:
        st.markdown(f"#### 🎧 {clip['name']}")
        
        audio_file_path = find_audio_file(clip["id"], clip["num"])
        
        if audio_file_path and os.path.exists(audio_file_path):
            ext = os.path.splitext(audio_file_path)[1].lower().replace('.', '')
            mime_type = "audio/wav" if ext == "wav" else "audio/mp3"
            with open(audio_file_path, "rb") as f:
                st.audio(f.read(), format=mime_type)
        else:
            st.warning(f"⚠️ Audio clip not found for clip #{clip['num']} ({clip['id']})")
            t = np.linspace(0, 2, 44100 * 2)
            st.audio(np.sin(2 * np.pi * 440 * t), sample_rate=44100)

        if clip["type"] == "attention":
            ans = st.radio("Select the option specified in the audio clip instructions above:", [1, 2, 3, 4, 5], key=clip["id"])
            rec_ratings[clip["id"]] = ans
        else:
            r_da = st.slider(f"Do you recognize {clip['name']}? (1 = Definitely Not, 5 = Definitely Yes)", 1, 5, 3, key=f"{clip['id']}_da")
            rec_ratings[clip["id"]] = r_da

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            navigate_to("section_c")
    with col2:
        if st.button("Submit Survey 🏁"):
            st.session_state.responses["recognition_ratings"] = rec_ratings
            
            # AUTOMATED ELIGIBILITY & BFS CALCULATIONS
            resp = st.session_state.responses
            
            # 1. Eligibility Rule Check
            age_ok = 18 <= resp["age"] <= 40
            upbringing_ok = resp["childhood"] == "India"
            hindi_ok = resp["hindi_comprehension"] >= 4
            hearing_ok = resp["hearing_diff"] == "No"
            vision_ok = resp["vision"] == "Yes"
            musician_ok = resp["musician"] == "No"
            headphones_ok = resp["headphones_avail"] == "Yes"
            att1_ok = resp["c10_attention_1"] == "Sometimes"
            att2_ok = resp["recognition_ratings"].get("attention_check_press_1") == 1
            bolly_exp_ok = resp["c2_bollywood_hrs"] not in ["None"] and resp["c7_bollywood_fam"] >= 3

            is_eligible = (
                age_ok and upbringing_ok and hindi_ok and hearing_ok and
                vision_ok and musician_ok and headphones_ok and att1_ok and
                att2_ok and bolly_exp_ok
            )

            # 2. Recognition Score Calculation (Real Songs Mean - Foils Mean)
            real_scores = [resp["recognition_ratings"].get(f"song_real_0{i}", 3) for i in range(1, 6)]
            foil_scores = [resp["recognition_ratings"].get("song_foil_01", 1), resp["recognition_ratings"].get("song_foil_02", 1)]
            rec_score = float(np.mean(real_scores) - np.mean(foil_scores))

            # 3. Aggregate Composite BFS
            years_exp = max(0, resp["age"] - resp["c4_start_age"])
            bfs_composite = np.mean([
                resp["c5_home_exp"],
                resp["c6_event_exp"],
                resp["c7_bollywood_fam"],
                rec_score,
                years_exp / 5.0
            ])

            resp["eligible"] = "Eligible" if is_eligible else "Ineligible"
            resp["recognition_score"] = round(rec_score, 2)
            resp["bfs_composite_score"] = round(bfs_composite, 2)

            # 1. SAVE TO LOCAL CSV
            df_new = pd.DataFrame([resp])
            if os.path.exists(DATA_FILE):
                df_existing = pd.read_csv(DATA_FILE)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                df_combined.to_csv(DATA_FILE, index=False)
            else:
                df_new.to_csv(DATA_FILE, index=False)

            # 2. STREAM TO GOOGLE SHEET (If Webhook Configured)
            send_to_google_sheet(resp)

            navigate_to("thank_you")

# ==============================================================================
# PAGE 6: THANK YOU / COMPLETION
# ==============================================================================
elif st.session_state.page == "thank_you":
    st.title("🎉 Thank You!")
    st.balloons()
    st.success("Your responses have been recorded successfully.")
    
    st.markdown("""
    Thank you for taking the time to complete the **Music and Media Habits Survey**. 
    If you are selected for the follow-up research session, our lab team will contact you via your assigned Participant Code.
    
    *You may now close this browser window.*
    """)

# ==============================================================================
# ADMIN / RESEARCHER DASHBOARD FOOTER (EXPANDER)
# ==============================================================================
st.markdown("---")
with st.expander("🔒 Researcher Admin Data Portal"):
    admin_pass = st.text_input("Enter Researcher Admin Password:", type="password")
    if admin_pass == "admin123":
        st.success("Admin authenticated!")
        if os.path.exists(DATA_FILE):
            df_data = pd.read_csv(DATA_FILE)
            st.write(f"Total Submissions Recorded Locally: **{len(df_data)}**")
            st.dataframe(df_data)
            
            csv_bytes = df_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download All Responses CSV",
                data=csv_bytes,
                file_name=f"survey_responses_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No responses recorded on this server yet.")
            
        st.markdown("---")
        st.markdown("#### Connect to Live Google Sheets")
        webhook_in = st.text_input("Google Apps Script Webhook URL:", value=st.session_state.get("webhook_url", ""))
        if st.button("Save Webhook URL"):
            st.session_state["webhook_url"] = webhook_in.strip()
            st.success("Webhook URL saved for this session!")


import json
import requests


def send_to_google_sheet(data_dict):
  """Sends submission directly to Google Sheet Webhook via requests."""
  webhook_url = GOOGLE_SHEET_WEBHOOK_URL or st.session_state.get(
      "webhook_url", ""
  )
  if not webhook_url:
    return False
  try:
    payload = {}
    for k, v in data_dict.items():
      if isinstance(v, dict):
        payload[k] = json.dumps(v)
      else:
        payload[k] = str(v)

    # Use requests to properly handle HTTP 302 redirects from Google
    response = requests.post(webhook_url, json=payload, timeout=10)
    return response.status_code in (200, 201)
  except Exception as e:
    print(f"Google Sheet sync warning: {e}")
    return False


            
