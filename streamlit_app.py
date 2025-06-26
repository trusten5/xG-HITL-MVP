import streamlit as st
import json
import os
import glob
import uuid
import pandas as pd
import warnings

# Config and UI Setup
warnings.filterwarnings("ignore", category=DeprecationWarning)
st.set_page_config(page_title="xG Annotation MVP", layout="wide")
st.markdown("""
<style>
    html, body, [class*="css"]  {
        font-family: 'Segoe UI', sans-serif;
    }
    [data-testid="stNotification"] {display: none;}
    .main { background-color: #f9f9fb; }
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

st.title("xG Annotation Dashboard")
st.caption("Internal MVP for Human-in-the-Loop xG Annotation. Built to demonstrate video annotation, metric tagging, and review.")

# Directories
DATA_DIR = "data"
VIDEOS_DIR = "videos"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

# Load all shot metadata files
def load_shot_data():
    shot_files = glob.glob(os.path.join(DATA_DIR, "shot_*.json"))
    shots = []
    for file in shot_files:
        with open(file, "r") as f:
            try:
                shots.append(json.load(f))
            except:
                st.warning(f"Could not load: {file}")
    return shots

def load_annotations():
    annotation_files = glob.glob(os.path.join(DATA_DIR, "annotation_*.json"))
    annotations = []
    for file in annotation_files:
        with open(file, "r") as f:
            try:
                annotations.append(json.load(f))
            except:
                st.warning(f"Could not load annotation: {file}")
    return annotations

def save_shot_metadata(shot_data, shot_id):
    path = os.path.join(DATA_DIR, f"{shot_id}.json")
    with open(path, "w") as f:
        json.dump(shot_data, f, indent=2)

def save_annotation(annotation, shot_id):
    path = os.path.join(DATA_DIR, f"annotation_{shot_id}.json")
    with open(path, "w") as f:
        json.dump(annotation, f, indent=2)

# Initialize session state for upload inputs if not present
for key in ["team", "opponent", "game_date", "match_minute", "shot_coordinates", "needs_review"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key not in ["match_minute", "needs_review"] else (0 if key == "match_minute" else False)

# Load data
shots = load_shot_data()
annotations = load_annotations()
shot_ids = [shot["Shot ID"] for shot in shots]
shot_index = {shot["Shot ID"]: shot for shot in shots}
annotation_index = {a["shot_id"]: a for a in annotations}

# Upload Form Section
with st.expander("➕ Upload New Shot"):
    team = st.text_input("Team Shooting", value=st.session_state.team)
    opponent = st.text_input("Opponent", value=st.session_state.opponent)
    game_date = st.date_input("Date of Game")
    match_minute = st.number_input("Match Minute", min_value=0, max_value=120, step=1, value=st.session_state.match_minute)
    shot_coordinates = st.text_input("Shot Coordinates (e.g. 105, 40)", value=st.session_state.shot_coordinates)
    needs_review = st.checkbox("Needs Review?", value=st.session_state.needs_review)
    video_file = st.file_uploader("Upload Shot Video (.mp4)", type=["mp4"])

    if st.button("Save Shot") and team and opponent and video_file:
        shot_id = f"shot_{uuid.uuid4().hex[:6]}"
        video_path = os.path.join(VIDEOS_DIR, f"{shot_id}.mp4")
        with open(video_path, "wb") as f:
            f.write(video_file.read())

        metadata = {
            "Shot ID": shot_id,
            "Team Shooting": team,
            "Opponent": opponent,
            "Date of Game": str(game_date),
            "Match Minute": match_minute,
            "Shot Coordinates": shot_coordinates,
            "AI Certainty %": "TBD",
            "Annotated?": False,
            "Needs Review?": needs_review
        }

        save_shot_metadata(metadata, shot_id)

        # Reset fields
        st.session_state.team = ""
        st.session_state.opponent = ""
        st.session_state.match_minute = 0
        st.session_state.shot_coordinates = ""
        st.session_state.needs_review = False

        st.success(f"Shot {shot_id} uploaded and saved.")
        st.rerun()
