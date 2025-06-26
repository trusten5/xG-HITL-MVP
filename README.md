# xG Annotation Dashboard

A web-based dashboard for uploading, managing, and annotating football (soccer) shot data and videos, designed to streamline the human-in-the-loop (HITL) annotation process for expected goals (xG) modeling.

## Features
- Upload shot videos and metadata
- Annotate shots with detailed metrics (body part, execution type, assist type, etc.)
- Track annotation status and review needs
- View summary tables of unannotated and annotated shots
- Simple, modern UI powered by Streamlit

## Getting Started

### Prerequisites
- Python 3.8+

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/trusten5/xG-HITL-mvp.git
   cd xG-HITL-mvp
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App
```bash
streamlit run app/app.py
```

The app will open in your browser. By default, it uses the `data/` and `videos/` directories for storing metadata and video files.

## Project Structure
```
xG-HITL-mvp/
  app/
    app.py              # Main Streamlit app
  data/                 # JSON files for shot metadata and annotations
  videos/               # Uploaded shot videos
  requirements.txt      # Python dependencies
  README.md             # Project documentation
```

## Example Data

### Shot Metadata (`data/shot_<id>.json`)
```json
{
  "Shot ID": "shot_9e195f",
  "Team Shooting": "Real Madrid",
  "Opponent": "Barcelona",
  "Date of Game": "2014-04-15",
  "Match Minute": 92,
  "Shot Location": "Penalty Box",
  "AI Certainty %": "N/A",
  "Annotated?": true,
  "Needs Review?": true
}
```

### Annotation (`data/annotation_<shot_id>.json`)
```json
{
  "shot_id": "shot_9e195f",
  "looks_good": true,
  "body_part": "Right Foot",
  "execution_type": "Controlled - on Run",
  "goalkeeper_position": ["Rushing"],
  "assist_type": "Through Ball",
  "pass_trajectory": "Ground Pass",
  "touches": 10,
  "last_set_piece": "Live Ball",
  "notes": ""
}
```

## Support & Contact
For questions or access requests, please contact the trusten@priorisports.com 
