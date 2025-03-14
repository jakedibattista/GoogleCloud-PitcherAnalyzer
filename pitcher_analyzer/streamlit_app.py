"""Streamlit application for the Baseball Pitcher Analyzer."""

import os
import tempfile
import logging
import streamlit as st
import time
from pitcher_analyzer.main import PitcherAnalysis
from pitcher_analyzer.video_manager import VideoManager
from dotenv import load_dotenv
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
logger.info("Initializing application...")
load_dotenv(verbose=False)

# Initialize session state variables
if "pitcher_level" not in st.session_state:
    st.session_state.pitcher_level = "Amateur"
if "pitch_type" not in st.session_state:
    st.session_state.pitch_type = "Fastball"
if "game_context" not in st.session_state:
    st.session_state.game_context = "Bullpen/Practice Session"
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "analyzer" not in st.session_state:
    st.session_state.analyzer = PitcherAnalysis()
if "video_manager" not in st.session_state:
    st.session_state.video_manager = VideoManager()
if "selected_video" not in st.session_state:
    st.session_state.selected_video = None
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# Set page configuration
st.set_page_config(
    page_title="Pitcher Scorecard",
    page_icon="⚾",
    layout="wide"
)

# Theme toggle function
def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

# Add custom CSS with theme support
st.markdown("""
<style>
    /* Theme variables */
    :root {
        --bg-primary: """ + (st.session_state.dark_mode and '#0F172A' or '#FFFFFF') + """;
        --bg-secondary: """ + (st.session_state.dark_mode and '#1E293B' or '#F8FAFC') + """;
        --text-primary: """ + (st.session_state.dark_mode and '#F1F5F9' or '#0F172A') + """;
        --text-secondary: """ + (st.session_state.dark_mode and '#CBD5E1' or '#475569') + """;
        --border-color: """ + (st.session_state.dark_mode and '#334155' or '#E2E8F0') + """;
        --card-shadow: """ + (st.session_state.dark_mode and '0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -2px rgba(0, 0, 0, 0.1)' or '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.02)') + """;
        --success-bg: """ + (st.session_state.dark_mode and '#064E3B' or '#ECFDF5') + """;
        --success-text: """ + (st.session_state.dark_mode and '#6EE7B7' or '#065F46') + """;
        --info-bg: """ + (st.session_state.dark_mode and '#1E40AF' or '#EFF6FF') + """;
        --info-text: """ + (st.session_state.dark_mode and '#93C5FD' or '#1E40AF') + """;
        --accent-color: """ + (st.session_state.dark_mode and '#2563EB' or '#1F2937') + """;
        --accent-color-hover: """ + (st.session_state.dark_mode and '#1D4ED8' or '#111827') + """;
        --tooltip-bg: """ + (st.session_state.dark_mode and '#1E293B' or '#FFFFFF') + """;
        --tooltip-text: """ + (st.session_state.dark_mode and '#F1F5F9' or '#0F172A') + """;
        --separator-color: """ + (st.session_state.dark_mode and '#334155' or '#E2E8F0') + """;
    }

    /* Global font settings */
    * {
        font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        letter-spacing: -0.01em;
    }

    /* Header styles */
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--text-primary);
        text-align: center;
        margin: 2rem 0;
        letter-spacing: -0.03em;
        line-height: 1.2;
        text-shadow: none;
    }

    /* Section headers */
    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0 0 1.5rem 0;
        padding: 0;
        color: var(--text-primary);
        letter-spacing: -0.02em;
    }

    /* Button styles */
    .stButton > button {
        background-color: #60A5FA !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        border-radius: 0.75rem !important;
        transition: all 0.2s ease !important;
        font-size: 0.95rem !important;
        letter-spacing: -0.01em !important;
        width: 100% !important;
        height: 2.4rem !important;
        line-height: 1.2 !important;
    }

    .stButton > button:hover {
        background-color: #3B82F6 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 6px -1px rgba(30, 64, 175, 0.1), 0 2px 4px -2px rgba(30, 64, 175, 0.1) !important;
        color: #FFFFFF !important;
    }

    /* Dark mode toggle specific styling */
    .dark-mode-toggle button {
        background-color: #60A5FA !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        padding: 0.5rem 1rem !important;
        height: 2.4rem !important;
        line-height: 1.2 !important;
        border-radius: 0.75rem !important;
        transition: all 0.2s ease !important;
    }

    /* Secondary button styles (for Delete and Rename) */
    .stButton > button[kind="secondary"] {
        background-color: #60A5FA !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        border-radius: 0.75rem !important;
        transition: all 0.2s ease !important;
        font-size: 0.95rem !important;
        letter-spacing: -0.01em !important;
        width: 100% !important;
        height: 2.4rem !important;
        line-height: 1.2 !important;
    }

    /* Primary button styles (Delete All Videos) */
    .stButton > button[kind="primary"] {
        background-color: #60A5FA !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        border-radius: 0.75rem !important;
        transition: all 0.2s ease !important;
        font-size: 0.95rem !important;
        letter-spacing: -0.01em !important;
        width: 100% !important;
        height: 2.4rem !important;
        line-height: 1.2 !important;
    }

    /* Card styles */
    .metric-card {
        background-color: var(--bg-secondary);
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        border: 1px solid var(--border-color);
        box-shadow: var(--card-shadow);
        transition: all 0.2s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px -1px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
    }

    /* Checkbox and Radio styles */
    .stCheckbox > div > label {
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        color: var(--text-primary) !important;
    }

    .stRadio > div {
        font-weight: 500 !important;
        font-size: 0.95rem !important;
    }

    /* Select box styling */
    .stSelectbox > div > div {
        border-radius: 0.75rem !important;
        border: 1px solid var(--border-color) !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        color: var(--text-primary) !important;
        background-color: var(--bg-secondary) !important;
    }

    .stSelectbox > div > div:hover {
        border-color: var(--accent-color) !important;
        box-shadow: 0 0 0 1px var(--accent-color) !important;
    }

    /* File uploader styling */
    .stFileUploader {
        border: 2px dashed var(--accent-color) !important;
        padding: 2rem !important;
        border-radius: 1rem !important;
        background-color: """ + (st.session_state.dark_mode and 'rgba(37, 99, 235, 0.1)' or 'rgba(31, 41, 55, 0.05)') + """ !important;
        transition: all 0.2s ease !important;
    }

    .stFileUploader:hover {
        border-color: var(--accent-color) !important;
        background-color: """ + (st.session_state.dark_mode and 'rgba(37, 99, 235, 0.15)' or 'rgba(31, 41, 55, 0.1)') + """ !important;
    }

    /* File uploader text and icon colors */
    .stFileUploader > div > div {
        color: var(--text-primary) !important;
    }

    .stFileUploader svg {
        fill: var(--accent-color) !important;
        opacity: """ + (st.session_state.dark_mode and '0.9' or '0.7') + """ !important;
    }

    /* File upload area text */
    .uploadedFileName {
        color: var(--text-primary) !important;
    }

    .stFileUploader small {
        color: var(--text-secondary) !important;
    }

    /* File upload progress bar */
    .stProgress > div > div > div > div {
        background-color: var(--accent-color) !important;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab"] {
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: -0.01em !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--accent-color) !important;
        border-bottom: 2px solid var(--accent-color) !important;
        background-color: transparent !important;
    }

    /* Add a subtle hover effect for tabs */
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--accent-color) !important;
        opacity: 0.9;
        background-color: transparent !important;
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background: var(--accent-color) !important;
        border-radius: 1rem !important;
    }

    /* Help text and tooltips */
    .stTooltipIcon {
        color: var(--text-secondary) !important;
    }

    .stTooltipContent {
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        letter-spacing: -0.01em !important;
        line-height: 1.5 !important;
        padding: 0.75rem 1rem !important;
        border-radius: 0.75rem !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1) !important;
    }

    /* Sidebar styling */
    .stSidebar {
        background-color: var(--bg-primary);
        border-right: 1px solid var(--border-color);
    }

    .stSidebar .block-container {
        padding-top: 2rem !important;
    }

    /* Markdown text */
    .stMarkdown {
        color: var(--text-secondary) !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
    }

    .stMarkdown h3 {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 1rem !important;
        color: var(--text-primary) !important;
    }

    /* Video container styles */
    .stVideo {
        margin: 0 !important;
        padding: 0 !important;
        margin-top: 1.5rem !important;  /* Add margin to align with Arm container */
    }
    
    /* Remove padding from video elements */
    .element-container:has(> stVideo) {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Remove padding from video wrapper */
    .stVideo > div {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Streamlit block container adjustments */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
        background-color: var(--bg-primary);
    }
    
    /* Remove extra spacing after video */
    div.stVideo + div {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Metric styles */
    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
        margin-top: 0.5rem;
        background-color: var(--bg-secondary);
        padding: 0.5rem;
        border-radius: 0.5rem;
        box-shadow: var(--card-shadow);
    }
    
    .metric-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .metric-score {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .metric-description {
        font-size: 1rem;
        color: var(--text-secondary);
        line-height: 1.5;
        margin-bottom: 0.5rem;
        background-color: """ + (st.session_state.dark_mode and 'rgba(255,255,255,0.05)' or 'rgba(0,0,0,0.02)') + """;
        padding: 0.75rem;
        border-radius: 0.5rem;
    }
    
    .metric-additional {
        font-size: 0.95rem;
        color: var(--text-secondary);
        line-height: 1.4;
        padding-left: 1rem;
        border-left: 3px solid var(--accent-color);
        margin-top: 0.5rem;
        background-color: """ + (st.session_state.dark_mode and 'rgba(255,255,255,0.03)' or 'rgba(0,0,0,0.01)') + """;
        padding: 0.5rem 1rem;
        border-radius: 0 0.5rem 0.5rem 0;
    }
    
    /* Risk indicators */
    .risk-text {
        display: inline;
        font-weight: 600;
        margin-right: 8px;
    }
    
    .risk-low {
        color: """ + (st.session_state.dark_mode and '#6EE7B7' or '#059669') + """;
    }
    
    .risk-medium {
        color: """ + (st.session_state.dark_mode and '#FCD34D' or '#D97706') + """;
    }
    
    .risk-high {
        color: """ + (st.session_state.dark_mode and '#FCA5A5' or '#DC2626') + """;
    }
    
    /* Info text */
    .info-text {
        font-size: 16px;
        margin: 10px 0;
        line-height: 1.5;
        color: var(--text-secondary);
    }
    
    /* Pitcher info */
    .pitcher-info {
        background-color: var(--bg-secondary);
        padding: 1rem;
        border-radius: 0.5rem;
        font-size: 1rem;
        line-height: 1.5;
        color: var(--text-secondary);
    }
    
    .pitcher-info strong {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    .grade-container {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
        gap: 20px;
        justify-content: center;
        background-color: """ + (st.session_state.dark_mode and 'rgba(255,255,255,0.05)' or 'rgba(0,0,0,0.02)') + """;
        padding: 1rem;
        border-radius: 0.75rem;
    }

    /* Metric header styles for better contrast */
    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
        margin-top: 0.5rem;
        background-color: var(--bg-secondary);
        padding: 0.5rem;
        border-radius: 0.5rem;
        box-shadow: var(--card-shadow);
    }

    /* Grade colors for better contrast in light mode */
    .grade-a-plus { background-color: #059669; color: #FFFFFF; }
    .grade-a { background-color: #10B981; color: #FFFFFF; }
    .grade-a-minus { background-color: #34D399; color: #FFFFFF; }
    .grade-b-plus { background-color: #3B82F6; color: #FFFFFF; }
    .grade-b { background-color: #60A5FA; color: #FFFFFF; }
    .grade-b-minus { background-color: #93C5FD; color: #FFFFFF; }
    .grade-c-plus { background-color: #F59E0B; color: #FFFFFF; }
    .grade-c { background-color: #FBBF24; color: #FFFFFF; }
    .grade-c-minus { background-color: #FCD34D; color: #FFFFFF; }
    .grade-d-plus { background-color: #EF4444; color: #FFFFFF; }
    .grade-d { background-color: #F87171; color: #FFFFFF; }
    .grade-d-minus { background-color: #FCA5A5; color: #FFFFFF; }
    .grade-f { background-color: #DC2626; color: #FFFFFF; }

    /* Help icon and tooltip styles */
    .stMarkdown div[data-testid="stMarkdownContainer"] > p {
        color: var(--text-primary) !important;
    }

    /* Style for help icons */
    button[kind="help"] {
        filter: brightness(2) !important;
        opacity: 0.9 !important;
    }

    button[kind="help"]:hover {
        filter: brightness(2.5) !important;
        opacity: 1 !important;
    }

    /* Tooltip container style */
    .stTooltipIcon {
        color: var(--text-primary) !important;
    }

    /* Tooltip content style */
    .stTooltipContent {
        background-color: var(--tooltip-bg) !important;
        color: var(--tooltip-text) !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }

    /* Separator styles */
    hr {
        border-color: var(--separator-color) !important;
        border-width: 2px !important;
        margin: 1.5rem 0 !important;
        opacity: """ + (st.session_state.dark_mode and '0.7' or '0.3') + """ !important;
    }

    /* Help text color */
    .stMarkdown div[data-testid="stMarkdownContainer"] > p {
        color: var(--text-secondary) !important;
    }

    /* Instructions text styling */
    .stMarkdown {
        color: var(--text-primary) !important;
    }

    .stMarkdown h3 {
        color: var(--text-primary) !important;
        font-size: 1.5rem !important;
        margin-bottom: 1rem !important;
    }

    .stMarkdown ul {
        color: var(--text-primary) !important;
        margin-left: 1.5rem !important;
    }

    .stMarkdown li {
        color: var(--text-primary) !important;
        margin-bottom: 0.5rem !important;
    }

    /* Override any default Streamlit text colors */
    div[data-testid="stMarkdownContainer"] {
        color: var(--text-primary) !important;
    }

    div[data-testid="stMarkdownContainer"] > * {
        color: var(--text-primary) !important;
    }

    /* Ensure nested elements inherit text color */
    div[data-testid="stMarkdownContainer"] ul li {
        color: var(--text-primary) !important;
    }

    /* Style bullet points */
    .stMarkdown ul li::marker {
        color: var(--text-primary) !important;
    }

    /* Style nested text */
    .stMarkdown ul li ul li {
        color: var(--text-primary) !important;
    }

    /* Dropdown menu background */
    [data-baseweb="popover"] {
        background-color: var(--bg-secondary) !important;
    }

    /* Dropdown option hover state */
    [data-baseweb="select"] div[role="option"]:hover {
        background-color: var(--accent-color) !important;
        color: #FFFFFF !important;
    }

    /* Dropdown menu styling */
    [data-baseweb="popover"] [data-baseweb="menu"] {
        background-color: var(--bg-secondary) !important;
    }

    /* Dropdown options */
    [data-baseweb="select"] [role="option"] {
        color: var(--text-primary) !important;
        background-color: var(--bg-secondary) !important;
    }

    /* Selected option in dropdown */
    [data-baseweb="select"] [aria-selected="true"] {
        color: #FFFFFF !important;
        background-color: var(--accent-color) !important;
    }

    /* Hover state for dropdown options */
    [data-baseweb="select"] [role="option"]:hover {
        background-color: var(--accent-color) !important;
        color: #FFFFFF !important;
    }

    /* Value container */
    [data-baseweb="select"] [data-testid="stMarkdownContainer"] div {
        color: var(--text-primary) !important;
    }

    /* Select box input */
    [data-baseweb="input"] input {
        color: var(--text-primary) !important;
        background-color: var(--bg-secondary) !important;
    }

    /* Dropdown list container */
    [role="listbox"] {
        background-color: var(--bg-secondary) !important;
        border-color: var(--border-color) !important;
    }

    /* Ensure text in select boxes is visible */
    [data-baseweb="select"] div {
        color: var(--text-primary) !important;
        background-color: var(--bg-secondary) !important;
    }

    /* Selected value in select box */
    [data-baseweb="select"] [data-testid="stMarkdownContainer"] {
        color: var(--text-primary) !important;
    }

    /* Help icon and tooltip complete overhaul */
    button[kind="help"] {
        filter: brightness(2) !important;
        opacity: 0.9 !important;
    }

    button[kind="help"]:hover {
        filter: brightness(2.5) !important;
        opacity: 1 !important;
    }

    /* White text in dropdowns */
    [data-baseweb="select"] div[aria-selected="true"] {
        color: #FFFFFF !important;
        background-color: var(--accent-color) !important;
    }

    /* Video list styling */
    .video-item {
        margin-bottom: 1rem !important;
    }

    /* Override the default h3 style specifically for video items */
    .video-item .stMarkdown h3 {
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        margin: 0.5rem 0 !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.01em !important;
        line-height: 1.2 !important;
    }

    /* Compact spacing for video management section */
    [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {
        margin-bottom: 0.5rem !important;
    }

    /* Header area fix */
    header[data-testid="stHeader"] {
        background-color: var(--bg-primary) !important;
        border-bottom: 1px solid var(--border-color) !important;
    }

    /* Ensure top toolbar is themed */
    .stToolbar {
        background-color: var(--bg-primary) !important;
    }

    /* Fix for any default white backgrounds */
    .stApp {
        background-color: var(--bg-primary) !important;
    }

    /* Ensure deploy button area is themed */
    [data-testid="stToolbar"] {
        background-color: var(--bg-primary) !important;
    }

    /* Fix for top right menu */
    [data-testid="stDecoration"] {
        background-color: var(--bg-primary) !important;
    }

    /* Ensure consistent background for all containers */
    [data-testid="stAppViewContainer"] {
        background-color: var(--bg-primary) !important;
    }

    /* Fix for any remaining white space in header */
    [data-testid="stHeader"] > div {
        background-color: var(--bg-primary) !important;
    }

    /* Ensure top bar buttons maintain theme */
    button[kind="toolbar"] {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown("<div class='main-header'>Pitcher Scorecard</div>", unsafe_allow_html=True)

# Check connectivity
connectivity = st.session_state.analyzer.mechanics_analyzer.check_connectivity()

# Sidebar for inputs
with st.sidebar:
    # Add tabs for analysis and management
    tab1, tab2 = st.tabs(["Analysis", "Video Management"])
    
    with tab1:
        # Add toggle for new/existing video without label
        use_existing = st.radio("", ["Upload New Video", "Use Existing Video"], label_visibility="collapsed")
        
        if use_existing == "Upload New Video":
            # File uploader with custom label
            uploaded_file = st.file_uploader("Upload Pitching Video", type=["mp4", "mov", "avi", "mpeg4"], label_visibility="collapsed")
            video_path = None
            if uploaded_file is not None:
                # Create a temporary file to store the uploaded video
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    video_path = tmp_file.name
                st.session_state.selected_video = video_path
        else:
            # Get list of existing videos
            cloud_videos = st.session_state.video_manager.list_cloud_videos()
            if cloud_videos:
                # Extract video names from GCS URIs
                video_names = [uri.split('/')[-1] for uri in cloud_videos]
                selected_video = st.selectbox("Select Existing Video", video_names)
                if selected_video:
                    # Find the full GCS URI for the selected video
                    selected_uri = next((uri for uri in cloud_videos if selected_video in uri), None)
                    if selected_uri:
                        # Only update video_path and rerun if a different video is selected
                        if st.session_state.selected_video != selected_uri:
                            video_path = selected_uri
                            st.session_state.selected_video = video_path
                            # Clear previous analysis results
                            st.session_state.analysis_results = None
                            st.rerun()
                        else:
                            video_path = selected_uri
            else:
                st.info("No existing videos found. Please upload a new video.")
                video_path = None
                st.session_state.selected_video = None
        
        # Add video speed control
        st.markdown("### Video Processing")
        use_slow_motion = st.checkbox("Use Slow Motion Analysis (Recommended)", value=True, 
            help="When enabled, this will automatically slow down the video to 10% speed for better analysis of pitching mechanics.")
        if use_slow_motion:
            speed_factor = 0.1  # Fixed speed factor at 10%
        else:
            speed_factor = 1.0
        
        # Rest of the analysis settings
        st.markdown("### Analysis Settings")
        pitcher_options = [
            "Amateur",
            "Clayton Kershaw"
        ]
        pitcher_level = st.selectbox("Pitcher Level/Name", pitcher_options, key="pitcher_level_select")
        
        pitch_options = ["Fastball", "Curveball"]
        pitch_type = st.selectbox("Pitch Type", pitch_options, key="pitch_type_select")
        
        game_options = [
            "Bullpen/Practice Session",
            "Regular Season Game"
        ]
        game_context = st.selectbox("Game Context", game_options, key="game_context_select")
        
        # Analysis button
        analyze_button = st.button("Analyze Pitching Mechanics", key="analyze_button")
        
        st.markdown("---")
        
        # Dark mode toggle
        st.markdown('<div class="dark-mode-toggle">', unsafe_allow_html=True)
        st.button("Dark/Light Mode", on_click=toggle_theme, key="theme_toggle")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Manage Videos")
        
        # Get list of videos
        cloud_videos = st.session_state.video_manager.list_cloud_videos()
        if cloud_videos:
            video_names = [uri.split('/')[-1] for uri in cloud_videos]
            
            # Add Delete All button at the top
            if st.button("🗑️ Delete All Videos", type="primary", use_container_width=True):
                if st.session_state.video_manager.delete_all_videos():
                    st.success("Successfully deleted all videos")
                    st.rerun()
                else:
                    st.error("Failed to delete all videos")
            
            st.markdown("---")
            
            # Display each video with management options
            for video_name in video_names:
                with st.container():
                    st.markdown(f"<div class='video-item'>", unsafe_allow_html=True)
                    
                    # Initialize rename state for this video if not exists
                    rename_key = f"rename_state_{video_name}"
                    if rename_key not in st.session_state:
                        st.session_state[rename_key] = False
                    
                    # Display video name
                    st.markdown(f"### {video_name}")
                    
                    # Buttons in a row
                    col1, col2 = st.columns(2)
                    with col1:
                        # Toggle rename state when button is clicked
                        if st.button("✏️ Rename", key=f"rename_btn_{video_name}", use_container_width=True, type="secondary"):
                            st.session_state[rename_key] = not st.session_state[rename_key]
                    
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_{video_name}", type="secondary", use_container_width=True):
                            if st.session_state.video_manager.delete_video(video_name):
                                st.success(f"Deleted {video_name}")
                                st.rerun()
                            else:
                                st.error("Failed to delete video")
                    
                    # Show rename input field if in rename state
                    if st.session_state[rename_key]:
                        new_name = st.text_input(
                            "Enter new name",
                            key=f"new_name_{video_name}",
                            value=video_name
                        )
                        if st.button("Save", key=f"save_{video_name}", use_container_width=True):
                            if new_name and new_name != video_name:
                                if st.session_state.video_manager.rename_video(video_name, new_name):
                                    st.success(f"Renamed {video_name} to {new_name}")
                                    st.session_state[rename_key] = False
                                    st.rerun()
                                else:
                                    st.error("Failed to rename video")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No videos found in storage.")

# Main content area
if st.session_state.selected_video:
    # Create two columns for layout
    video_col, metrics_col = st.columns([1, 1])
    
    # Video column
    with video_col:
        # Display the video
        if st.session_state.selected_video.startswith('gs://'):
            try:
                # Download from GCS to temporary file
                temp_video_path = st.session_state.video_manager.download_video(st.session_state.selected_video)
                st.video(open(temp_video_path, 'rb').read())
                # Clean up temp file after displaying
                try:
                    os.unlink(temp_video_path)
                except:
                    pass
            except Exception as e:
                st.error(f"Error loading video: {str(e)}")
        elif st.session_state.selected_video.startswith('https://'):
            st.video(st.session_state.selected_video)
        else:
            st.video(open(st.session_state.selected_video, 'rb').read())

        # Display Injury Risk Assessment under the video
        if st.session_state.analysis_results and 'raw_analysis' in st.session_state.analysis_results:
            analysis = st.session_state.analysis_results['raw_analysis']
            sections = analysis.split('\n\n')
            metrics = {}
            
            # Process sections to extract metrics
            for section in sections:
                section = section.strip()
                if section.startswith('Overall:'):
                    metrics['Overall'] = section.replace('Overall:', '').strip()
                elif 'INJURY/FATIGUE INDICATORS:' in section:
                    injury_risk = section.replace('INJURY/FATIGUE INDICATORS:', '').strip()

            # Display Injury Risk Assessment
            if 'injury_risk' in locals():
                risk_match = re.search(r'Risk Level:\s*(\w+)\s*[-:]\s*(.*)', injury_risk)
                if risk_match:
                    risk_level = risk_match.group(1)
                    explanation = risk_match.group(2).strip()
                    risk_class = {
                        'Low': 'risk-low',
                        'High': 'risk-high'
                    }.get(risk_level, 'risk-low')
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class="metric-header">
                            <span class="metric-title">Risk Assessment: <span class='{risk_class}'>{risk_level} Risk</span></span>
                        </div>
                        <div class='metric-description'>
                            {explanation}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Key Metrics column
    with metrics_col:
        # Display metrics (excluding injury risk and overall)
        if st.session_state.analysis_results and 'raw_analysis' in st.session_state.analysis_results:
            analysis = st.session_state.analysis_results['raw_analysis']
            sections = analysis.split('\n\n')
            metrics = {}
            
            # Process each section
            for section in sections:
                section = section.strip()
                
                # Extract metrics
                if section.startswith('Arm:'):
                    metrics['Arm'] = section.replace('Arm:', '').strip()
                elif section.startswith('Balance:'):
                    metrics['Balance'] = section.replace('Balance:', '').strip()
                elif section.startswith('Stride & Drive:'):
                    metrics['Stride & Drive'] = section.replace('Stride & Drive:', '').strip()
            
            # Define color coding for grades
            grade_colors = {
                'A': st.session_state.dark_mode and '#6EE7B7' or '#059669',
                'B': st.session_state.dark_mode and '#6EE7B7' or '#059669',
                'C': 'red',
                'D': 'red',
                'F': 'red'
            }

            # Display metrics with grades
            for metric_name in ['Arm', 'Balance', 'Stride & Drive']:
                if metric_name in metrics:
                    content = metrics[metric_name]
                    # Extract grade if present and format with colon
                    grade_match = re.search(r'([A-F])\s*[-:]', content)
                    if grade_match:
                        grade = grade_match.group(1)
                        # Get color for the grade
                        color = grade_colors.get(grade, 'black')
                        # Display header with grade and color in a container without background color for the grade
                        st.markdown(f"<div class='metric-header'><span class='metric-title'>{metric_name} <span style='color:{color};'>({grade})</span></span></div>", unsafe_allow_html=True)
                        # Remove grade from content
                        content = re.sub(r'([A-F])\s*[-:]', '', content).strip()
                    else:
                        # Display header without grade
                        st.markdown(f"**{metric_name}**")
                    # Split content into main and additional parts
                    parts = content.split('|', 1)
                    main_content = parts[0].strip()
                    additional_info = parts[1].strip() if len(parts) > 1 else None
                    st.markdown(f"<div class='metric-description'>{main_content}</div>", unsafe_allow_html=True)
                    if additional_info:
                        st.markdown(f"<div class='metric-additional'>{additional_info}</div>", unsafe_allow_html=True)

    # Display Overall Assessment in full width after both columns
    if st.session_state.analysis_results and 'raw_analysis' in st.session_state.analysis_results:
        analysis = st.session_state.analysis_results['raw_analysis']
        sections = analysis.split('\n\n')
        
        # Find Overall Assessment
        overall_text = None
        for section in sections:
            if section.startswith('Overall:'):
                overall_text = section.replace('Overall:', '').strip()
                break
        
        if overall_text:
            st.markdown(f"""
            <div class='metric-card'>
                <div class="metric-header">
                    <span class="metric-title">Overall Assessment</span>
                </div>
                <div class='metric-description'>
                    {overall_text}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Analyze the video when the button is clicked
    if analyze_button:
        with st.spinner("Analyzing pitching mechanics..."):
            try:
                # Add a progress bar for visual feedback
                progress_bar = st.progress(0)
                
                # Process video if slow motion is enabled
                if use_slow_motion and st.session_state.selected_video:
                    video_path = st.session_state.video_manager.slow_down_video(st.session_state.selected_video, speed_factor)
                else:
                    video_path = st.session_state.selected_video
                
                for i in range(100):
                    # Update progress bar
                    progress_bar.progress(i + 1)
                    time.sleep(0.01)
                
                # Call the analyze_video method
                results = st.session_state.analyzer.analyze_video(
                    video_path=video_path,
                    pitcher_name=pitcher_level,
                    pitch_type=pitch_type,
                    game_type=game_context
                )
                
                # Store results in session state
                st.session_state.analysis_results = results
                
                # Force a rerun to refresh the display
                st.rerun()
            
            except Exception as e:
                st.error(f"Error analyzing video: {str(e)}")
                logger.error(f"Error in analysis: {e}")
    
    # Clean up the temporary file if it was a new upload
    if use_existing == "Upload New Video":
        try:
            os.unlink(video_path)
        except:
            pass
else:
    # Display instructions when no file is selected
    st.info("Please upload a video or select an existing video to analyze pitcher mechanics.")
    st.markdown("""
    ### How to use this tool:
    1. **Choose your video source:**
       - Upload a new video (MP4, MOV, or AVI format)
       - Or select from existing analyzed videos
       
    2. **For new uploads:**
       - Videos must be under 200MB
       - For best results, use a 3-5 second clip focusing on the pitching motion

    3. **Provide pitch details:**
       - Select the pitcher's level or name
       - Choose the type of pitch being thrown
       - Specify the game context

    4. **Analysis:**
       - Click "Analyze Pitching Mechanics"
       - The analysis will provide:
         - Overall mechanics score
         - Key issues identified
         - Specific recommendations for improvement
    """)

# Footer with connectivity status and powered by message
st.markdown("---")
footer_cols = st.columns([1, 1])
with footer_cols[0]:
    if connectivity.get('gemini', False):
        st.success("✅ Connected to Gemini API")
    else:
        st.info("ℹ️ Gemini API: Offline Mode")

with footer_cols[1]:
    if connectivity.get('google_cloud', False):
        st.success("✅ Connected to Google Cloud")
    else:
        st.info("ℹ️ Google Cloud: Local Storage")

st.markdown("Powered by AI - Helping pitchers improve their mechanics and prevent injuries.") 