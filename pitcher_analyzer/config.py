from pathlib import Path
import os
from pitcher_analyzer.data.pitcher_profiles import PITCHER_PROFILES

class Config:
    # Project settings
    PROJECT_ID = "baseball-pitcher-analyzer"
    PROJECT_NUMBER = "238493405692"
    LOCATION = "us-central1"  # Default Google Cloud region
    GCS_BUCKET = "baseball-pitcher-analyzer-videos"
    GCS_LOCATION = "US-CENTRAL1"
    
    # Directory paths
    BASE_DIR = Path(__file__).parent
    TEST_DATA_DIR = BASE_DIR / "tests/data"
    VIDEO_DIR = TEST_DATA_DIR / "videos"
    ANALYSIS_DIR = TEST_DATA_DIR / "analysis"
    DEBUG_DIR = BASE_DIR / "debug_frames"
    
    # Credentials
    CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Video processing settings
    VIDEO_SETTINGS = {
        "max_duration": 10,  # Maximum video length in seconds
        "required_fps": 30,  # Required frames per second
        "min_resolution": (640, 480)  # Minimum video resolution
    }
    
    # Analysis thresholds
    THRESHOLDS = {
        "min_velocity": 85.0,  # MPH
        "min_control": 70.0,  # percentage
        "max_pitch_duration": 0.45  # seconds
    }
    
    # Video settings
    VIDEO_REQUIREMENTS = {
        "max_duration": 15,     # Increased to allow full pitch sequence
        "min_duration": 5,      # Increased to ensure we capture wind-up
        "pitch_segment": {
            "pre_pitch": 3,     # Seconds before pitch release
            "post_pitch": 2,    # Seconds after pitch release
            "total": 5          # Total segment duration
        },
        "required_formats": [".mp4", ".mov"],
        "min_resolution": (720, 480),  # width, height
        "fps": 60  # Most baseball footage is 60fps
    }
    
    # Analysis settings
    ANALYSIS = {
        "timeout": 300,  # seconds
        "pitcher_velocity_threshold": 85,  # mph for pull decision
        "min_confidence": 0.5
    }
    
    # Visualization settings
    VISUALIZATION = {
        "output_fps": 30,
        "font_scale": 0.5,
        "colors": {
            "pose_landmarks": (0, 255, 0),  # green
            "connections": (255, 255, 0),   # yellow
            "text": (255, 255, 255)         # white
        },
        "line_thickness": 2
    }
    
    # Mechanics thresholds
    MECHANICS = {
        "max_arm_angle_variance": 5.0,  # degrees
        "min_stride_length": 0.85,  # % of height
        "min_hip_shoulder_separation": 30.0,  # degrees
        "max_balance_variation": 0.1,  # normalized
        "min_follow_through": 0.8,  # completion %
        
        # Key pose landmarks
        "landmarks": {
            "shoulder": ["LEFT_SHOULDER", "RIGHT_SHOULDER"],
            "hip": ["LEFT_HIP", "RIGHT_HIP"],
            "knee": ["LEFT_KNEE", "RIGHT_KNEE"],
            "ankle": ["LEFT_ANKLE", "RIGHT_ANKLE"],
            "elbow": ["LEFT_ELBOW", "RIGHT_ELBOW"],
            "wrist": ["LEFT_WRIST", "RIGHT_WRIST"]
        },
        "validation": {
            "min_visibility_threshold": 0.5,
            "min_valid_frames": 4,
            "max_angle_change": 45.0,  # degrees per frame
            "min_joint_distance": 0.05  # 5% of frame height
        }
    }
    
    # Complete pitcher profiles configuration
    PITCHER_PROFILES = ["KERSHAW", "AMATEUR"]
    
    # Game context configurations
    GAME_CONTEXTS = {
        "REGULAR SEASON": {
            "mechanics_tolerance": 1.0,
            "velocity_adjustment": 0,
            "control_emphasis": 1.0
        },
        "HIGH PRESSURE": {
            "mechanics_tolerance": 0.8,
            "velocity_adjustment": 1,
            "control_emphasis": 1.2
        },
        "PERFECT GAME": {
            "mechanics_tolerance": 0.7,
            "velocity_adjustment": 2,
            "control_emphasis": 1.5
        },
        "UNKNOWN": {
            "mechanics_tolerance": 1.0,
            "velocity_adjustment": 0,
            "control_emphasis": 1.0
        }
    }
    
    # Vertex AI settings
    VERTEX_AI = {
        "project_id": os.getenv("GCP_PROJECT_ID", "baseball-pitcher-analyzer"),
        "location": os.getenv("GCP_LOCATION", "us-central1"),
        "model_id": os.getenv("VERTEX_MODEL_ID", "pitcher-mechanics-model"),
        "endpoint_id": os.getenv("VERTEX_ENDPOINT_ID"),  # If using a specific endpoint
    }
    
    # Google API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Get API key from environment variable
    
    # Vertex AI Configuration - Development defaults
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "baseball-pitcher-analyzer")
    LOCATION = os.getenv("GCP_LOCATION", "us-central1")
    MODEL_ID = os.getenv("VERTEX_MODEL_ID", "6198198833936072704")  # pose-landmarker model ID
    ENDPOINT_ID = os.getenv("VERTEX_ENDPOINT_ID", "pitcher-mechanics-endpoint-1")
    
    # Analysis Configuration
    MIN_CONFIDENCE_THRESHOLD = 0.7
    FRAME_SAMPLE_RATE = 5
    
    # Frame Extraction Settings
    MOTION_START_PERCENT = 0.2  # Start analyzing at 20% into the video
    MOTION_END_PERCENT = 0.9    # End analyzing at 90% into the video
    KEY_FRAMES = 5              # Number of key frames to analyze
    
    # Pitch Types
    PITCH_TYPES = ["Fastball", "Curveball"]
    
    # Service Account (if needed)
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # Google Cloud configuration
    PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "baseball-pitcher-analyzer")
    LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
    BUCKET_NAME = os.environ.get("GCP_BUCKET_NAME", "baseball-pitcher-analyzer-videos")
    CREDENTIALS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH", "/Users/j0d0hge/credentials/google-cloud/baseball-pitcher-analyzer-key.json")
    
    # Gemini configuration
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro-vision")
    
    # Video analysis settings
    MAX_FILE_SIZE_MB = int(os.environ.get("MAX_FILE_SIZE_MB", "200"))
    SUPPORTED_VIDEO_FORMATS = os.environ.get("SUPPORTED_VIDEO_FORMATS", "mp4,mov").split(",")
    
    # API retry settings
    MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
    MIN_RETRY_WAIT_SECONDS = int(os.environ.get("MIN_RETRY_WAIT_SECONDS", "4"))
    MAX_RETRY_WAIT_SECONDS = int(os.environ.get("MAX_RETRY_WAIT_SECONDS", "10"))
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.CREDENTIALS_PATH:
            raise ValueError("Missing GOOGLE_APPLICATION_CREDENTIALS")
            
        if not os.path.exists(cls.CREDENTIALS_PATH):
            raise ValueError(f"Credentials file not found: {cls.CREDENTIALS_PATH}")
            
        # Ensure required directories exist
        directories = [
            cls.TEST_DATA_DIR,
            cls.VIDEO_DIR,
            cls.ANALYSIS_DIR,
            cls.DEBUG_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
        cls.validate_config()
            
        return True 

    @classmethod
    def validate_config(cls):
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
        if not cls.PROJECT_ID:
            raise ValueError("PROJECT_ID is not set")
        if not cls.MODEL_ID:
            raise ValueError("VERTEX_MODEL_ID environment variable is not set")
        if not cls.ENDPOINT_ID:
            raise ValueError("VERTEX_ENDPOINT_ID environment variable is not set") 