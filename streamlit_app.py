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

# Load data
shots = load_shot_data()
annotations = load_annotations()
shot_ids = [shot["Shot ID"] for shot in shots]
shot_index = {shot["Shot ID"]: shot for shot in shots}
annotation_index = {a["shot_id"]: a for a in annotations}

# Clear All Data Button
with st.expander("⚠️ Danger Zone: Clear All Data"):
    if st.button("Delete ALL shots and annotations", type="primary"):
        for file in glob.glob(os.path.join(DATA_DIR, "*.json")):
            os.remove(file)
        for file in glob.glob(os.path.join(VIDEOS_DIR, "*.mp4")):
            os.remove(file)
        st.success("All shots, annotations, and videos have been deleted.")
        st.rerun()

# Upload Form Section
with st.expander("➕ Upload New Shot"):
    team = st.text_input("Team Shooting", key="team")
    opponent = st.text_input("Opponent", key="opponent")
    game_date = st.date_input("Date of Game", key="date")
    match_minute = st.number_input("Match Minute", min_value=0, max_value=120, step=1, key="minute")
    shot_location = st.text_input("Shot Location (e.g. Penalty Box)", key="location")
    needs_review = st.checkbox("Needs Review?", value=False, key="review")
    video_file = st.file_uploader("Upload Shot Video (.mp4)", type=["mp4"], key="video")

    submit_clicked = st.button("Save Shot")

    if submit_clicked:
        missing_fields = []
        if not team:
            missing_fields.append("Team Shooting")
        if not opponent:
            missing_fields.append("Opponent")
        if not video_file:
            missing_fields.append("Video File")

        if missing_fields:
            st.error(f"{', '.join(missing_fields)} was not filled in")
        else:
            duplicate = any(
                s["Team Shooting"] == team and s["Opponent"] == opponent and s["Date of Game"] == str(game_date)
                for s in shots
            )
            if duplicate and "confirm_repeat" not in st.session_state:
                st.session_state["confirm_repeat"] = st.radio(
                    "This shot seems to be a repeat. Are you sure you want to submit?",
                    ["No", "Yes"], key="confirm_repeat_radio"
                )
                st.stop()

            if duplicate and st.session_state.get("confirm_repeat") == "No":
                st.warning("Submission canceled.")
                st.session_state.pop("confirm_repeat")
                st.stop()

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
                "Shot Location": shot_location,
                "AI Certainty %": "TBD",
                "Annotated?": False,
                "Needs Review?": needs_review
            }

            save_shot_metadata(metadata, shot_id)
            st.success(f"Shot {shot_id} uploaded and saved.")
            for key in ["team", "opponent", "date", "minute", "location", "review", "video", "confirm_repeat"]:
                st.session_state.pop(key, None)
            st.rerun()

# Display Unannotated Shots Table
unannotated_shots = [s for s in shots if not s.get("Annotated?")]
if unannotated_shots:
    st.markdown("### 📋 Shots Awaiting Annotation")
    unannotated_df = pd.DataFrame(unannotated_shots).sort_values(by="Date of Game", ascending=False)
    st.dataframe(unannotated_df)
    selected_shot = st.selectbox("Select Shot ID to Annotate", [s["Shot ID"] for s in unannotated_shots])
    if selected_shot and st.button("Annotate Selected Shot"):
        st.session_state["shot_id"] = selected_shot
        st.rerun()
else:
    st.info("✅ All shots have been annotated.")

# Summary Table of Completed Annotations with clickable Shot ID
if annotations:
    st.markdown("### ✅ Completed Annotations Summary")
    annotation_df = pd.DataFrame(annotations).sort_values(by="shot_id", ascending=False)

    def make_clickable(shot_id):
        return f'<a href="?shot_id={shot_id}">{shot_id}</a>'

    annotation_df.insert(0, "Shot ID", annotation_df["shot_id"].apply(make_clickable))
    annotation_df = annotation_df.drop(columns=["shot_id"], errors="ignore")
    st.write("Click a Shot ID to edit its annotation.", unsafe_allow_html=True)
    st.write(annotation_df.to_html(escape=False, index=False), unsafe_allow_html=True)

# Handle query param shot_id
query_params = st.query_params
if "shot_id" in query_params:
    st.session_state["shot_id"] = query_params["shot_id"][0]

# Annotation Section
if "shot_id" in st.session_state:
    shot_id = st.session_state["shot_id"]
    shot = shot_index.get(shot_id)
    prior_annotation = annotation_index.get(shot_id, {})
    if shot:
        st.title(f"📝 Annotating {shot_id}")
        st.subheader(f"{shot['Team Shooting']} vs {shot['Opponent']}")

        video_path = os.path.join(VIDEOS_DIR, f"{shot_id}.mp4")
        if os.path.exists(video_path):
            st.video(video_path)
        else:
            st.warning("Video not available.")

        st.markdown("### Extracted Metadata")
        st.write({k: v for k, v in shot.items() if k not in ["Shot ID"]})
        looks_good = st.checkbox("Data looks correct?", value=prior_annotation.get("looks_good", True))

        st.markdown("### Annotate Metrics")
        body_part = st.selectbox("Body Part Used", ["Left Foot", "Right Foot", "Header", "Other"], index=["Left Foot", "Right Foot", "Header", "Other"].index(prior_annotation.get("body_part", "Left Foot")))
        execution_type = st.selectbox("Shot Execution Type", ["First-Time", "Controlled - Static", "Controlled - on Run", "Volley", "Half-Volley"], index=["First-Time", "Controlled - Static", "Controlled - on Run", "Volley", "Half-Volley"].index(prior_annotation.get("execution_type", "First-Time")))
        gk_position = st.multiselect("Goalkeeper Position", ["Out of Position", "On Line", "Rushing", "Screened"], default=prior_annotation.get("goalkeeper_position", []))
        assist_type = st.selectbox("Assist Type", ["Through Ball", "Cut-Back", "Cross", "Rebound", "Shot from Set Piece"], index=["Through Ball", "Cut-Back", "Cross", "Rebound", "Shot from Set Piece"].index(prior_annotation.get("assist_type", "Through Ball")))
        trajectory = st.selectbox("Pass Trajectory", ["Ground Pass", "Lofted", "Bouncing", "Driven Cross"], index=["Ground Pass", "Lofted", "Bouncing", "Driven Cross"].index(prior_annotation.get("pass_trajectory", "Ground Pass")))
        touches = st.number_input("Number of Touches Before Shot", min_value=0, max_value=10, step=1, value=prior_annotation.get("touches", 0))
        set_piece = st.selectbox("Last Set Piece Type", ["Live Ball", "Corner", "Direct FK", "Indirect FK", "Penalty", "Throw"], index=["Live Ball", "Corner", "Direct FK", "Indirect FK", "Penalty", "Throw"].index(prior_annotation.get("last_set_piece", "Live Ball")))
        notes = st.text_area("General Notes / Flags", value=prior_annotation.get("notes", ""))

        if st.button("Submit Annotation"):
            annotation = {
                "shot_id": shot_id,
                "looks_good": looks_good,
                "body_part": body_part,
                "execution_type": execution_type,
                "goalkeeper_position": gk_position,
                "assist_type": assist_type,
                "pass_trajectory": trajectory,
                "touches": touches,
                "last_set_piece": set_piece,
                "notes": notes
            }
            save_annotation(annotation, shot_id)
            shot["Annotated?"] = True
            save_shot_metadata(shot, shot_id)
            st.success("Annotation saved!")
            st.session_state.pop("shot_id")
            st.rerun()
