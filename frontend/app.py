import os
import dash
from dash import dcc, html, Input, Output, State, callback_context, clientside_callback, ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import psycopg2
from psycopg2 import pool
import pandas as pd
from urllib.parse import urlparse, parse_qs, quote
import sqlalchemy as sa
from flask import send_from_directory
from backend.InferenceQuery import inference_query

# Initialize the Dash app with a modern theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], serve_locally=True, suppress_callback_exceptions=True)
app.title = "Es2al Sayed - إسأل سيد"

# PostgreSQL connection pool
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "localhost"),
    'port': int(os.getenv("DB_PORT", "5433")),
    'database': os.getenv("DB_NAME", "SpeechDatabaseInfo"),
    'user': os.getenv("DB_USER", "postgres"),
    'password': os.getenv("DB_PASSWORD"),
}
MAIN_MEDIA_PATH = os.getenv("MAIN_MEDIA_PATH", "/mnt/d/Personal/PromptSpeech")
MEDIA_ROUTE = "/media"

DATABASE_URL = sa.engine.URL.create(
    "postgresql", username=DB_CONFIG['user'], password=DB_CONFIG['password'],
    host=DB_CONFIG['host'], port=DB_CONFIG['port'], database=DB_CONFIG['database'],
)
engine = sa.create_engine(DATABASE_URL, echo=False, future=True)

# Create connection pool
try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(1, 20, **DB_CONFIG)
    print("Database connection successful!")
except Exception as e:
    print(f"Database connection error: {e}")
    connection_pool = None

# ========== CRITICAL FIX: Add Flask route to serve media files ==========
@app.server.route(f'{MEDIA_ROUTE}/<path:path>')
def serve_media(path):
    """Serve media files from the MAIN_MEDIA_PATH directory"""
    # send_from_directory safe-joins `path` onto the fixed root and 404s on
    # traversal attempts; never build the directory argument from client input.
    return send_from_directory(MAIN_MEDIA_PATH, path)

# Helper function to convert database paths to served URLs
def convert_to_media_url(db_path):
    """Convert database file path to web-servable URL"""
    if not db_path or db_path == 'Not Available' or pd.isna(db_path):
        return None
    
    # Remove MAIN_MEDIA_PATH prefix if it exists
    if db_path.startswith(MAIN_MEDIA_PATH):
        relative_path = db_path[len(MAIN_MEDIA_PATH):].lstrip('/')
    else:
        relative_path = db_path.lstrip('/')
    
    # Convert to URL with proper encoding
    url = f"{MEDIA_ROUTE}/{relative_path}"
    return url

# --- Your index_string (kept as in original) ---
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .main-container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 30px;
                margin: 20px;
            }
            .video-card {
                transition: transform 0.3s, box-shadow 0.3s;
                cursor: pointer;
                border-radius: 15px;
                overflow: hidden;
                margin-bottom: 20px;
            }
            .video-card:hover {
                transform: translateY(-10px);
                box-shadow: 0 15px 30px rgba(0,0,0,0.2);
            }
            .video-cover {
                width: 100%;
                height: 200px;
                object-fit: cover;
            }
            .no-cover {
                width: 100%;
                height: 200px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
            .app-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .btn-custom {
                border-radius: 25px;
                padding: 10px 25px;
                font-weight: bold;
                transition: all 0.3s;
            }
            .btn-custom:hover {
                transform: scale(1.05);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .chat-container {
                background: #f8f9fa;
                border-radius: 15px;
                padding: 20px;
                margin-top: 20px;
            }
            .info-box {
                background: #fff3cd;
                border-left: 5px solid #ffc107;
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .contact-box {
                background: #d1ecf1;
                border-left: 5px solid #17a2b8;
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .rtl {
                direction: rtl;
                text-align: right;
            }
            .timestamp-button {
                display: block;
                width: 100%;
                text-align: left;
                margin-bottom: 8px;
                padding: 10px 15px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.3s;
                font-size: 14px;
            }
            .timestamp-button:hover {
                transform: translateX(5px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Database connection functions
def get_db_connection():
    if connection_pool is None:
        raise Exception("Database connection pool not initialized")
    return connection_pool.getconn()

def return_db_connection(conn):
    if connection_pool is not None:
        connection_pool.putconn(conn)

# Function to get videos from database
def get_videos(subject_filter=None, year_filter=None):
    try:
        conn = get_db_connection()
        query = 'SELECT * FROM "Video" WHERE 1=1'
        params = []
        if subject_filter and subject_filter != 'All':
            query += ' AND subject = %s'
            params.append(subject_filter)
        if year_filter and year_filter != 'All':
            query += ' AND year = %s'
            params.append(year_filter)
        df = pd.read_sql_query(query, conn, params=params)
        return_db_connection(conn)
        return df
    except Exception as e:
        print(f"Error getting videos: {e}")
        return pd.DataFrame()

# Function to get books from database
def get_books():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query('SELECT * FROM "Book"', conn)
        return_db_connection(conn)
        return df
    except Exception as e:
        print(f"Error getting books: {e}")
        return pd.DataFrame()

# Function to get unique subjects and years
def get_filter_options():
    try:
        conn = get_db_connection()
        subjects_df = pd.read_sql_query('SELECT DISTINCT subject FROM "Video" WHERE subject IS NOT NULL', conn)
        subjects = subjects_df['subject'].dropna().tolist()
        
        years_df = pd.read_sql_query('SELECT DISTINCT year FROM "Video" WHERE year IS NOT NULL ORDER BY year DESC', conn)
        years = years_df['year'].dropna().tolist()
        
        return_db_connection(conn)
        
        return subjects, years
    except Exception as e:
        print(f"Error getting filter options: {e}")
        return [], []

# Function for video Q&A
def get_answer_timestamp(video_name, query):
    output = inference_query(query, video_name)
    return {
        "start": output["startTimeStamp"],
        "end": output["endTimeStamp"],
        "answer": output.get("answer", f"Answer for: {query}")
    }

def format_time(seconds):
    """Convert seconds to MM:SS format"""
    try:
        seconds = int(float(seconds))
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"
    except:
        return "00:00"

# ---------- Layout ----------

# Initialize app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='subject-filter-store', data='All'),
    dcc.Store(id='year-filter-store', data='All'),
    html.Div([
        html.Div([
            html.H1("إسأل سيد - Es2al Sayed", style={'margin': 0, 'fontSize': '48px'}),
            html.P("Your Interactive Learning Platform", style={'margin': '10px 0 0 0', 'fontSize': '18px'}),
        ], className='app-header'),
        html.Div([
            html.Div([
                html.P("⚠️ The transcription may contain errors because it is generated by AI. Please contact us if you have any feedback.", 
                       style={'margin': 0, 'fontWeight': 'bold'}),
                html.P("⚠️ قد يحتوي النص المكتوب على أخطاء لأنه تم إنشاؤه بواسطة الذكاء الاصطناعي. يرجى الاتصال بنا إذا كان لديك أي ملاحظات.", 
                       className='rtl', style={'margin': '10px 0 0 0', 'fontWeight': 'bold'}),
            ], className='info-box'),
            html.Div([
                html.P("📧 For volunteer and help in the improvement of project, contact us:", 
                       style={'margin': 0, 'fontWeight': 'bold'}),
                html.P("Email: contact@es2alsayed.com | Phone: +20 123 456 7890", 
                       style={'margin': '5px 0 0 0'}),
            ], className='contact-box'),
        ], id='info-messages'),
        html.Div(id='main-content'),
    ], className='main-container'),
])

# ---------- Views ----------

def create_video_list_view():
    subjects, years = get_filter_options()
    
    valid_subjects = [s for s in subjects if s is not None and pd.notna(s) and str(s).strip()]
    valid_years = [y for y in years if y is not None and pd.notna(y)]
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                dcc.Link(dbc.Button("📚 Books", color='info', className='btn-custom', style={'marginRight': '10px'}), href='/books'),
                dcc.Link(dbc.Button("🎥 Videos", color='primary', className='btn-custom'), href='/'),
            ], width=12, className='mb-3'),
        ]),
        dbc.Row([
            dbc.Col([dcc.Dropdown(
                id='subject-filter',
                options=[{'label': 'All Subjects', 'value': 'All'}] + [{'label': str(s), 'value': str(s)} for s in valid_subjects],
                value='All',
                placeholder="Filter by Subject",
                style={'borderRadius': '25px'}
            )], md=6),
            dbc.Col([dcc.Dropdown(
                id='year-filter',
                options=[{'label': 'All Years', 'value': 'All'}] + [{'label': str(y), 'value': str(y)} for y in valid_years],
                value='All',
                placeholder="Filter by Year",
                style={'borderRadius': '25px'}
            )], md=6),
        ], className='mb-4'),
        html.Div(id='video-grid', children=[html.Div("Loading videos...", className='text-center')]),
    ])

def create_books_list_view():
    return html.Div([
        dbc.Row([
            dbc.Col([
                dcc.Link(dbc.Button("📚 Books", color='info', className='btn-custom', style={'marginRight': '10px'}), href='/books'),
                dcc.Link(dbc.Button("🎥 Videos", color='primary', className='btn-custom'), href='/'),
            ], width=12, className='mb-3'),
        ]),
        html.H2("📚 Books Library", className='mb-4'),
        html.Div(id='books-grid'),
    ])

def create_video_player_view(video_id):
    try:
        conn = get_db_connection()
        video = pd.read_sql_query('SELECT * FROM "Video" WHERE id = %s', conn, params=[int(video_id)]).iloc[0]
        return_db_connection(conn)
    except Exception as e:
        print(f"Error loading video: {e}")
        return html.Div("Error loading video")
    
    # Convert paths to URLs
    video_url = convert_to_media_url(video.get('linkToMP4'))
    has_video = video_url is not None
    
    return html.Div([
        dcc.Link(dbc.Button("← Back to Videos", color='secondary', className='btn-custom mb-3'), href='/'),
        html.H2(video['name'], className='mb-3'),
        html.P(f"Subject: {video['subject']} | Year: {video['year']}", className='text-muted mb-4'),
        dbc.Row([
            dbc.Col([
                html.Video(
                    id='video-player',
                    src=video_url if has_video else '',
                    controls=True,
                    style={'width': '100%', 'borderRadius': '15px', 'boxShadow': '0 10px 30px rgba(0,0,0,0.2)'}
                ) if has_video else html.Div("Video not available", className='no-cover'),
            ], md=8),
            dbc.Col([
                html.Div([
                    dbc.Button("📄 Transcription", id='btn-transcription', color='primary', className='btn-custom w-100 mb-2',
                              disabled=video['linkToPdf'] == 'Not Available' or pd.isna(video.get('linkToPdf'))),
                    dbc.Button("📝 Summary", id='btn-summary', color='success', className='btn-custom w-100 mb-2',
                              disabled=video['linkToSummaryPdf'] == 'Not Available' or pd.isna(video.get('linkToSummaryPdf'))),
                    dbc.Button("🌐 Translation", id='btn-translation', color='info', className='btn-custom w-100 mb-2',
                              disabled=video.get('linkToTranslation', 'Not Available') == 'Not Available' or pd.isna(video.get('linkToTranslation'))),
                ]),
                html.Div([
                    html.H5("💬 Ask a Question", className='mt-4 mb-3'),
                    dcc.Textarea(id='chat-input', placeholder='Type your question about this video...', 
                                style={'width': '100%', 'height': '100px', 'borderRadius': '15px', 'padding': '10px', 'border': '2px solid #667eea'}),
                    dbc.Button("Send", id='btn-send-chat', color='primary', className='btn-custom w-100 mt-2'),
                    html.Div(id='chat-response', className='chat-container mt-3'),
                ]),
            ], md=4),
        ]),
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id='pdf-modal-title')),
            dbc.ModalBody(html.Iframe(id='pdf-viewer', style={'width': '100%', 'height': '600px'})),
            dbc.ModalFooter(dbc.Button("Close", id='close-pdf-modal', className='btn-custom')),
        ], id='pdf-modal', size='xl', is_open=False),
        dcc.Store(id='current-video-id', data=video_id),
        dcc.Store(id='video-seek-trigger', data=None),  # Store to trigger video seek
    ])

def create_book_viewer(book_id):
    try:
        conn = get_db_connection()
        book = pd.read_sql_query('SELECT * FROM "Book" WHERE id = %s', conn, params=[int(book_id)]).iloc[0]
        return_db_connection(conn)
    except Exception as e:
        print(f"Error loading book: {e}")
        return html.Div("Error loading book")
    
    # Convert path to URL
    book_url = convert_to_media_url(book.get('linkToPdf'))
    has_book = book_url is not None
    
    return html.Div([
        dcc.Link(dbc.Button("← Back to Books", color='secondary', className='btn-custom mb-3'), href='/books'),
        html.H2(book['Title'], className='mb-4'),
        html.Iframe(src=book_url if has_book else '', 
                   style={'width': '100%', 'height': '800px', 'border': 'none', 'borderRadius': '15px', 'boxShadow': '0 10px 30px rgba(0,0,0,0.2)'}) 
                   if has_book else html.Div("Book PDF not available", className='no-cover', style={'height': '400px'}),
    ])

# ---------- URL Routing Callback ----------

@app.callback(
    Output('main-content', 'children'),
    [Input('url', 'pathname'),
     Input('url', 'search')]
)
def display_page(pathname, search):
    params = parse_qs(search[1:]) if search else {}
    
    if pathname == '/books':
        if 'id' in params:
            book_id = int(params['id'][0])
            return create_book_viewer(book_id)
        return create_books_list_view()
    elif pathname == '/video' and 'id' in params:
        video_id = int(params['id'][0])
        return create_video_player_view(video_id)
    else:
        return create_video_list_view()

# ---------- Video Grid Callback ----------

@app.callback(
    Output('video-grid', 'children'),
    [Input('subject-filter', 'value'), 
     Input('year-filter', 'value')]
)
def update_video_grid(subject, year):
    try:
        videos = get_videos(subject, year)
        
        if videos.empty:
            return html.Div("No videos found", className='text-center text-muted')
        
        cards = []
        for idx, video in videos.iterrows():
            video_id = int(video['id']) if pd.notna(video['id']) else 0
            video_name = str(video['name']) if pd.notna(video['name']) else 'Unknown'
            video_subject = str(video['subject']) if pd.notna(video['subject']) else 'Unknown'
            video_year = str(video['year']) if pd.notna(video['year']) else 'Unknown'
            
            # Convert cover path to URL
            cover_url = convert_to_media_url(video.get('linkToCover'))
            
            card = dbc.Card([
                dbc.CardImg(src=cover_url, top=True, className='video-cover') if cover_url else html.Div("🎥", className='no-cover'),
                dbc.CardBody([
                    html.H5(video_name, className='card-title'),
                    html.P(f"{video_subject} - {video_year}", className='card-text text-muted'),
                    dcc.Link(dbc.Button("Watch", color='primary', className='btn-custom'), href=f'/video?id={video_id}'),
                ]),
            ], className='video-card')
            cards.append(dbc.Col(card, md=4, className='mb-4'))
        
        return dbc.Row(cards)
        
    except Exception as e:
        print(f"Error in update_video_grid: {e}")
        import traceback
        traceback.print_exc()
        return html.Div("Error loading videos.", className='text-center text-danger')

# ---------- Books Grid Callback ----------

@app.callback(
    Output('books-grid', 'children'),
    [Input('url', 'pathname')]
)
def update_books_grid(pathname):
    if pathname != '/books':
        raise PreventUpdate
    
    books = get_books()
    if books.empty:
        return html.Div("No books found", className='text-center text-muted')
    
    cards = []
    for idx, book in books.iterrows():
        book_id = int(book['id']) if pd.notna(book['id']) else 0
        
        # Convert cover path to URL
        cover_url = convert_to_media_url(book.get('linkToCover'))
        
        card = dbc.Card([
            dbc.CardImg(src=cover_url, top=True, className='video-cover') if cover_url else html.Div("📚", className='no-cover'),
            dbc.CardBody([
                html.H5(str(book['Title']), className='card-title'),
                dcc.Link(dbc.Button("Open Book", color='success', className='btn-custom'), href=f'/books?id={book_id}'),
            ]),
        ], className='video-card')
        cards.append(dbc.Col(card, md=4, className='mb-4'))
    
    return dbc.Row(cards)

# ---------- PDF Modal Callback ----------

@app.callback(
    [Output('pdf-modal', 'is_open'), 
     Output('pdf-viewer', 'src'), 
     Output('pdf-modal-title', 'children')],
    [Input('btn-transcription', 'n_clicks'), 
     Input('btn-summary', 'n_clicks'), 
     Input('btn-translation', 'n_clicks'), 
     Input('close-pdf-modal', 'n_clicks')],
    [State('current-video-id', 'data'), 
     State('pdf-modal', 'is_open')],
    prevent_initial_call=True
)
def toggle_pdf_modal(trans_clicks, summ_clicks, transl_clicks, close_clicks, video_id, is_open):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'close-pdf-modal':
        return False, '', ''
    
    if video_id is None:
        raise PreventUpdate
    
    try:
        conn = get_db_connection()
        video = pd.read_sql_query('SELECT * FROM "Video" WHERE id = %s', conn, params=[int(video_id)]).iloc[0]
        return_db_connection(conn)
        
        if trigger_id == 'btn-transcription':
            pdf_url = convert_to_media_url(video.get('linkToPdf'))
            if pdf_url:
                return True, pdf_url, 'Transcription'
        elif trigger_id == 'btn-summary':
            pdf_url = convert_to_media_url(video.get('linkToSummaryPdf'))
            if pdf_url:
                return True, pdf_url, 'Summary'
        elif trigger_id == 'btn-translation':
            pdf_url = convert_to_media_url(video.get('linkToTranslation'))
            if pdf_url:
                return True, pdf_url, 'Translation'
    except Exception as e:
        print(f"Error in PDF modal: {e}")
    
    raise PreventUpdate

# ---------- Chat Callback ----------

@app.callback(
    [Output('chat-response', 'children'), 
     Output('chat-input', 'value'),
     Output('video-seek-trigger', 'data')],
    [Input('btn-send-chat', 'n_clicks')],
    [State('chat-input', 'value'), 
     State('current-video-id', 'data')],
    prevent_initial_call=True
)
def handle_chat(n_clicks, query, video_id):
    if not n_clicks or not query or video_id is None:
        raise PreventUpdate
    
    try:
        conn = get_db_connection()
        video = pd.read_sql_query('SELECT * FROM "Video" WHERE id = %s', conn, params=[int(video_id)]).iloc[0]
        return_db_connection(conn)
        
        result = get_answer_timestamp(video['name'], query)

        # Raw timestamps (in seconds)
        start_sec = float(result['start'])
        end_sec = float(result['end'])

        # Formatted timestamps MM:SS
        start_fmt = format_time(start_sec)
        end_fmt = format_time(end_sec)
        
        response_div = html.Div([
            html.H6('Answer:', className='mb-2'),
            html.P(result['answer']),
            html.Hr(),
            html.P(f"⏱️ Timestamp: {start_fmt} → {end_fmt}", 
                   className='text-muted', style={'fontSize': '14px'}),
            html.P("🎯 Video will jump to the answer automatically!", 
                   className='text-success', style={'fontSize': '13px', 'fontWeight': 'bold'}),
        ])
        
        # Clear input and return timestamp to trigger video seek
        return response_div, '', start_sec

    except Exception as e:
        print(f"Error in chat: {e}")
        import traceback
        traceback.print_exc()
        return html.Div("حدث خطأ أثناء معالجة سؤالك. حاول مرة أخرى.", style={'color': 'red'}), query, None

# ---------- Clientside Callback for Video Seeking ----------

clientside_callback(
    """
    function(timestamp) {
        if (timestamp !== null && timestamp !== undefined && timestamp > 0) {
            setTimeout(function() {
                var video = document.getElementById('video-player');
                if (video) {
                    console.log('Seeking video to:', timestamp);
                    video.currentTime = timestamp;
                    video.play();
                } else {
                    console.log('Video element not found');
                }
            }, 100);
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('video-player', 'className'),
    Input('video-seek-trigger', 'data'),
    prevent_initial_call=True
)

# ---------- Run App ----------

if __name__ == '__main__':
    try:
        print("Starting Dash server...")
        print(f"Media files will be served from: {MAIN_MEDIA_PATH}")
        print(f"Media route: {MEDIA_ROUTE}")
        app.run(debug=True, host='localhost', port=8050)
    finally:
        if connection_pool is not None:
            print("Closing database connections...")
            connection_pool.closeall()