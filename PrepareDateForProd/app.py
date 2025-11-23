"""
Dash video viewer + chatbot + segment seeking app.

Requirements:
    pip install dash psycopg2-binary sqlalchemy

How to run:
    1) Edit DB_* variables below to point to your PostgreSQL instance.
    2) Set MAIN_MEDIA_PATH to the folder that contains subfolders for each video (folder names match `name` column).
       Each video folder should contain the mp4, transcription pdf and summary pdf (if they exist).
    3) If you already have `find_segments(video_name, query)` implemented, import it or replace the stub at the bottom.
    4) Run: python app.py
"""

import os
import json
import pathlib
from urllib.parse import quote

import dash
from dash import html, dcc, Input, Output, State, MATCH, ALL
import dash_bootstrap_components as dbc  # optional (we'll fallback if not installed)
import sqlalchemy as sa
import pandas as pd
from flask import send_from_directory
from PrepareDateForProd.InferenceQuery import inference_query
from Database.searchinDatabase import get_table_from_db
from Database.DataBaseFunctions import connectTodatabase
# -----------------------
# ========== CONFIG =====
# -----------------------
# Edit these to match your environment / secrets
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "root")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "SpeechDatabaseInfo")
TABLE_NAME = os.getenv("TABLE_NAME", "Video")

configuration_db = {"db_name": "SpeechDatabaseInfo",
                     "password": "root",
                     "host": "localhost",
                      "port": 5433 }
# MAIN_MEDIA_PATH should be the directory that contains one folder per video,
# each folder name exactly matches the "name" column from the DB. Each folder contains:
#   - the .mp4 file (use whatever filename you like; linkToMP4 from DB points to it or we'll try to find a .mp4)
#   - the transcription PDF (if present)
#   - the summary PDF (if present)
MAIN_MEDIA_PATH = os.getenv("MAIN_MEDIA_PATH", "/mnt/d/Personal/PromptSpeech/EvaluationData")  # <--- change this

# Flask static serving prefix for media (will be routed to files under MAIN_MEDIA_PATH)
MEDIA_ROUTE = "/media"

# Video table columns (you stated these)
list_columns = ["id", "name", "year", "linkToCover", "linkToMP4", "linkToPdf", "linToSummaryPdf"]
quoted_columns = [f'"{col}"' for col in list_columns]

# -----------------------
# ========== DB =========
# -----------------------
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = sa.create_engine(DATABASE_URL, echo=False, future=True)

def load_videos_from_db():
    """
    Loads rows from the videos table and returns a pandas DataFrame containing at least the columns in list_columns.
    """
    connction, cursor = connectTodatabase(configuration_db)
    df = get_table_from_db(cursor, "Video", list_columns, filter_conditions=None)
    # Ensure columns exist
    for c in list_columns:
        if c not in df.columns:
            df[c] = None
    return df

# -----------------------
# ========== APP ========
# -----------------------
EXTERNAL_STYLESHEETS = [
    # small bootstrap for nicer layout (optional). If not installed, Dash will still work.
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
]

app = dash.Dash(__name__, external_stylesheets=EXTERNAL_STYLESHEETS,suppress_callback_exceptions=True,serve_locally=True)
server = app.server  # flask server

# -----------------------
# ========== HELPERS =====
# -----------------------
def safe_media_url(video_name: str, filename: str):
    """
    Produces a URL under MEDIA_ROUTE for the given file inside the video_name folder.
    We'll URL-quote the filename to be safe.
    """
    # encode path parts
    return f"{MEDIA_ROUTE}/{quote(video_name)}/{quote(filename)}"

def find_local_media_file(video_folder: str, ext=".mp4"):
    """
    Try to find the first file inside video_folder that ends with ext.
    Returns filename or None.
    """
    p = pathlib.Path(video_folder)
    if not p.exists() or not p.is_dir():
        return None
    for f in p.iterdir():
        if f.is_file() and f.name.lower().endswith(ext.lower()):
            return f.name
    return None

# -----------------------
# ========== Flask routes to serve media files under MAIN_MEDIA_PATH =====
# -----------------------
@app.server.route(f"{MEDIA_ROUTE}/<path:subpath>")
def serve_media(subpath):
    """
    Serve files from MAIN_MEDIA_PATH/<subpath>.
    subpath is expected to be like "<video_name>/<filename>".
    """
    # Protect against path traversal by resolving paths
    root = pathlib.Path(MAIN_MEDIA_PATH).resolve()
    requested = (root / subpath).resolve()
    try:
        # Ensure requested is inside the media root
        if not str(requested).startswith(str(root)):
            return "Forbidden", 403
        directory = str(requested.parent)
        filename = requested.name
        return send_from_directory(directory, filename)
    except Exception as e:
        return f"Error: {e}", 404

# -----------------------
# ========== Layout ======
# -----------------------
app.layout = html.Div(
    [
        dcc.Store(id="video-list-store"),  # holds loaded list
        dcc.Store(id="selected-video-store"),  # holds selected video row as json
        html.H2("Es2al Sayed", style={"margin": "10px 0 20px 0"}),
        html.Div(
            [
                html.Div(
                    [
                        html.H5("Videos"),
                        html.Div(id="video-cards", style={"overflowY": "auto", "maxHeight": "75vh", "paddingRight": "8px"}),
                    ],
                    style={"width": "40%", "display": "inline-block", "verticalAlign": "top", "padding": "8px", "borderRight": "1px solid #ddd"},
                ),
                html.Div(
                    [
                        html.Div(id="video-player-area", children=[
                            html.P("Select a video from the left to play it.")
                        ]),
                    ],
                    style={"width": "68%", "display": "inline-block", "padding": "8px", "verticalAlign": "top"},
                ),
            ],
            style={"display": "flex"}
        ),
        # Hidden div to allow clientside seeking callback to return something
        html.Div(id="seek-output", style={"display":"none"}),
        html.Div(style={"height": "20px"})
    ],
    style={"fontFamily": "system-ui, Arial, sans-serif", "padding": "10px 20px"}
)

# -----------------------
# ========== Callbacks ===
# -----------------------

@app.callback(Output("video-list-store", "data"), Input("video-list-store", "data"))
def load_video_list_if_needed(data):
    """
    Loads the video list from DB once (on app load). We use a callback triggered by initial None data.
    """
    if data is not None:
        return data
    try:
        df = load_videos_from_db()
    except Exception as e:
        # Return an error payload
        return {"error": str(e)}
    # Convert DataFrame to list of dicts
    records = df.to_dict(orient="records")
    return {"records": records}


@app.callback(Output("video-cards", "children"),
              Input("video-list-store", "data"))
def render_video_cards(store_data):
    """
    Render the list of videos as clickable cards.
    Each card has a button that sets selected-video-store.
    """
    if not store_data:
        return "Loading..."
    if "error" in store_data:
        return html.Div(["Error loading videos: ", html.Pre(store_data["error"])])
    records = store_data.get("records", [])
    cards = []
    for rec in records:
        name = rec.get("name") or "Untitled"
        cover = rec.get("linkToCover") or ""
        print(cover)
        # If cover is empty but a file exists in folder, try to use it
        cover_url = f"{MEDIA_ROUTE}/{cover}"
        print(cover_url)
        
        
        cover_component = html.Img(src=cover_url, style={"width":"320px","height":"100px","objectFit":"cover","borderRadius":"6px"})
        # build the card
        card = html.Div(
            [
                html.Div(cover_component, style={"marginBottom":"6px"}),
                html.Div(name, style={"fontWeight":"600", "fontSize":"14px", "marginBottom":"4px"}),
                html.Button("Select", id={"type":"select-video-btn","index": rec.get("id")}, n_clicks=0, className="btn btn-sm btn-primary")
            ],
            style={"padding":"8px", "borderBottom":"1px solid #f0f0f0"}
        )
        cards.append(card)
    return cards


@app.callback(Output("selected-video-store", "data"),
              Input({"type":"select-video-btn","index": ALL}, "n_clicks"),
              State("video-list-store", "data"))
def on_select_video(n_clicks_list, store_data):
    """
    When a "Select" button is pressed, find which one and return the video record into the store.
    """
    if not store_data:
        return dash.no_update
    records = store_data.get("records", [])
    if not n_clicks_list or all([n is None or n==0 for n in n_clicks_list]):
        # nothing clicked
        return dash.no_update
    # find index of largest n_clicks (latest click)
    max_clicks = -1
    idx = None
    for i, v in enumerate(n_clicks_list):
        v0 = v or 0
        if v0 > max_clicks:
            max_clicks = v0
            idx = i
    if idx is None:
        return dash.no_update
    # Map idx -> record id: the order of buttons matches order of records in render; we rely on that
    # For safety, match by id if possible:
    try:
        # get button id mapping by reading the generated pattern ids (they align with records order)
        selected_rec = records[idx]
    except Exception:
        selected_rec = records[idx] if idx < len(records) else None
    if not selected_rec:
        return dash.no_update
    return selected_rec


@app.callback(Output("video-player-area", "children"),
              Input("selected-video-store", "data"))
def render_player_area(selected):
    """
    Renders the video player, PDF buttons and chatbot for the selected video.
    """
    if not selected:
        return html.P("Select a video from the left to play it.")
    # selected is a dict containing at least the columns from DB
    name = selected.get("name")
    linkToMP4 = selected.get("linkToMP4") or ""
    linkToPdf = selected.get("linkToPdf") or ""
    linkToSummary = selected.get("linToSummaryPdf") or ""  # note the column name specified: 'linToSummaryPdf'
    cover = selected.get("linkToCover") or ""
        
        # If cover is empty but a file exists in folder, try to use it
    cover_url = f"{MEDIA_ROUTE}/{cover}"
    # Decide mp4 file URL:
    mp4_url = None
    
    
    mp4_url = f"{MEDIA_ROUTE}/{linkToMP4}"
    # else:
    #     # try to find any mp4 inside the folder MAIN_MEDIA_PATH/name
    #     folder = pathlib.Path(MAIN_MEDIA_PATH) / name
    #     file_found = find_local_media_file(folder, ext=".mp4")
    #     if file_found:
    #         mp4_url = safe_media_url(name, file_found)

    # PDF URLs: prefer db link if present, otherwise local file in folder
    def resolve_pdf(field_value, folder, expect_name_contains=None):
        if field_value:
            return field_value
        # try to find a pdf in the folder
        # if folder.exists():
        #     # optionally try to prefer using names
        #     for f in folder.iterdir():
        #         if f.is_file() and f.suffix.lower()==".pdf":
        #             # if we have a hint 'transcript' or 'summary' in filename prefer that
        #             if expect_name_contains and expect_name_contains.lower() in f.name.lower():
        #                 return safe_media_url(name, f.name)
        #     # fallback: first pdf
        #     for f in folder.iterdir():
        #         if f.is_file() and f.suffix.lower()==".pdf":
        #             return safe_media_url(name, f.name)
        # return None

    folder = pathlib.Path(MAIN_MEDIA_PATH) / name
    pdf_transcript_url = resolve_pdf(linkToPdf, folder, expect_name_contains="transcript")
    pdf_summary_url = resolve_pdf(linkToSummary, folder, expect_name_contains="summary")

    # Build UI
    video_player = html.Video(id="video-player",
                              controls=True,
                               poster=cover_url, 
                              children=[],
                              style={"width":"100%", "maxHeight":"80vh", "background":"#000"}
                              )
    if mp4_url:
        
        video_player = html.Video(id="video-player", controls=True,  poster=cover_url,src=mp4_url,
                                 style={"width":"100%", "maxHeight":"800vh", "background":"#000"})

    pdf_buttons = []
    if pdf_transcript_url:
        pdf_buttons.append(html.A(html.Button("Transcript (PDF)", className="btn btn-outline-secondary"),
                                  href=pdf_transcript_url, target="_blank", style={"marginRight":"8px"}))
    else:
        pdf_buttons.append(html.Button("Transcript (PDF) — not available", className="btn btn-outline-secondary", disabled=True, style={"marginRight":"8px"}))
    if pdf_summary_url:
        pdf_buttons.append(html.A(html.Button("Summary (PDF)", className="btn btn-outline-secondary"),
                                  href=pdf_summary_url, target="_blank"))
    else:
        pdf_buttons.append(html.Button("Summary (PDF) — not available", className="btn btn-outline-secondary", disabled=True))

    # Chatbot panel: simple input + submit -> server callback finds segments
    chatbot_panel = html.Div(
        [
            html.H5("Ask about this video"),
            dcc.Textarea(id="chat-query", placeholder="Type a question about the video...", style={"width":"100%","height":"70px"}),
            html.Div(style={"height":"6px"}),
            html.Button("Ask", id="chat-ask-btn", className="btn btn-primary"),
            html.Div(id="chat-results", style={"marginTop":"12px"})
        ],
        style={"marginTop":"12px", "border":"1px solid #eee", "padding":"10px", "borderRadius":"8px"}
    )

    # Compose right-side layout: video on top, buttons, chatbot aside
    right_col = html.Div(
        [
            html.Div([html.H4(name), video_player]),
            html.Div(pdf_buttons, style={"marginTop":"8px"}),
            html.Div(style={"height":"10px"}),
            chatbot_panel
        ]
    )
    return right_col


@app.callback(Output("chat-results", "children"),
              Input("chat-ask-btn", "n_clicks"),
              State("chat-query", "value"),
              State("selected-video-store", "data"))
def on_chat_ask(n_clicks, query, selected):
    """
    Called when user presses Ask. Calls the provided `find_segments(video_name, query)` function (user implemented).
    Expects that function to return a list of segments or a single dict with 'start' and 'end'.
    We'll render the segments as clickable buttons (pattern-matching ids) with data-start attribute for clientside seeking.
    """
    if not n_clicks:
        return ""
    if not query or not selected:
        return html.Div("Please select a video and type a question first.", style={"color":"#666"})
    video_name = selected.get("name")
    # Call the user-implemented function that returns segment(s)
    try:
        segments = find_segments(video_name, query)
    except Exception as e:
        return html.Div([html.B("Error while searching segments:"), html.Pre(str(e))])

    # Normalize segments into a list of dicts {'start':..., 'end':..., 'text':... (optional)}
    normalized = []
    if segments is None:
        return html.Div("No segments found.")
    if isinstance(segments, dict):
        # may be single segment
        if "start" in segments and "end" in segments:
            normalized = [segments]
        else:
            # maybe dict of multiple segments keyed by something
            for k,v in segments.items():
                if isinstance(v, dict) and "start" in v and "end" in v:
                    normalized.append(v)
    elif isinstance(segments, list):
        for s in segments:
            if isinstance(s, dict) and "start" in s and "end" in s:
                normalized.append(s)

    if not normalized:
        return html.Div("No segments found (returned structure wasn't recognized).")

    # Build clickable buttons for each segment. We use pattern-matching ids so a clientside callback can get all their n_clicks.
    buttons = []
    for i, seg in enumerate(normalized):
        start = float(seg.get("start", 0))
        end = float(seg.get("end", start))
        text = seg.get("text") or f"{start:.1f}s — {end:.1f}s"
        # render readable label mm:ss
        def fmt(t):
            t = int(round(t))
            m = t // 60
            s = t % 60
            return f"{m:02d}:{s:02d}"
        label = f"{fmt(start)} → {fmt(end)}"
        # Button has an id pattern so clientside callback can capture clicks
        btn = html.Button(
            f"{label} — {text if isinstance(text,str) else ''}",
            id={"type":"segment-button","index": i},
            n_clicks=0,
            **{"data-start": start},
            style={"display":"block", "width":"100%", "textAlign":"left", "marginBottom":"6px"}
        )
        buttons.append(btn)
    return html.Div(buttons)

# -----------------------
# ========== Clientside JS to seek video when a segment button is clicked =====
# -----------------------
app.clientside_callback(
    """
    function(n_clicks_list, starts){
        // n_clicks_list: array of n_clicks for each segment-button (order preserved)
        // starts: array of data-start for each button (order preserved)
        if(!n_clicks_list || !starts) return '';
        // find the index with maximum n_clicks (most recently clicked one)
        let max = -1;
        let idx = -1;
        for(let i=0;i<n_clicks_list.length;i++){
            let v = n_clicks_list[i] || 0;
            if(v > max){
                max = v;
                idx = i;
            }
        }
        if(idx === -1) return '';
        let start = starts[idx];
        if(start === null || start === undefined) return '';
        // seek the video element:
        let vid = document.getElementById('video-player');
        if(vid){
            try{
                vid.currentTime = parseFloat(start);
                vid.play();
            }catch(e){
                console.log('Error seeking video', e);
            }
        }
        return '';
    }
    """,
    Output("seek-output", "children"),
    Input({"type":"segment-button","index": ALL}, "n_clicks"),
    State({"type":"segment-button","index": ALL}, "data-start"),
)

# -----------------------
# ========== PLACEHOLDER: find_segments function ==========================
# Replace or import your real implementation. The app expects a callable:
#   find_segments(video_name: str, query: str) -> list[dict] OR dict
# Where each dict contains at least 'start' and 'end' in seconds (ints or floats).
# Optionally include 'text' to show a short excerpt/answer.
# Example return value:
#   [{"start": 12.2, "end": 18.4, "text": "They explain the algorithm's base case."}, ...]
# ------------------------------------------------------------------------
def find_segments(video_name: str, query: str):
    """
    STUB: replace this with your implemented function.
    For now it returns a fake list for demonstration.
    """
    # Example - return two fake segments (REMOVE this and import your real function)
    # raise NotImplementedError("Please replace the find_segments stub with your implementation.")
    # Demo output:
    output = inference_query(query,video_name)
    return [
        {"start": output["startTimeStamp"], "end": output["endTimeStamp"], "text": "None"}
    ]

# -----------------------
# ========== Run server ==
# -----------------------
if __name__ == "__main__":
    # Quick sanity checks on configuration:
    if not os.path.isdir(MAIN_MEDIA_PATH):
        print(f"Warning: MAIN_MEDIA_PATH {MAIN_MEDIA_PATH} does not exist or is not a directory. Media serving will fail until this is fixed.")
    print("Starting Dash app...")
    app.run(debug=True, port=8050)
