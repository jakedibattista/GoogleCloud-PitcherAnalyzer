"""Module for analyzing baseball pitcher mechanics."""

import os
import logging
import tempfile
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from google.cloud import storage
import time
import cv2
import numpy as np
import base64
import re
import io
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
logger.info("Loading environment variables...")
load_dotenv(verbose=False)

# Initialize API key
api_key = os.getenv('GEMINI_API_KEY')

class MechanicsAnalyzer:
    """Analyzer for baseball pitcher mechanics."""
    
    def __init__(self):
        """Initialize the mechanics analyzer."""
        logger.info("Initializing MechanicsAnalyzer")
        
        # Initialize Google Cloud Storage
        self.gcs_available = False
        try:
            self.project_id = os.getenv('GCP_PROJECT_ID') or os.getenv('GOOGLE_CLOUD_PROJECT')
            self.bucket_name = os.getenv('GCP_BUCKET_NAME')
            
            if self.project_id and self.bucket_name:
                self.storage_client = storage.Client(project=self.project_id)
                self._ensure_bucket_exists()
                self.gcs_available = True
                logger.info(f"✅ Google Cloud Storage initialized with bucket: {self.bucket_name}")
            else:
                logger.warning("Google Cloud Storage configuration not found, using local storage")
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Storage: {e}")
        
        # Initialize Gemini API from environment variable
        self.gemini_available = False
        try:
            # Get API key from environment variable with detailed logging
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("No API key found in environment variable GEMINI_API_KEY")
                return
                
            logger.info("Found API key in environment variable")
            logger.info(f"API key format validation: starts with 'AIza'? {api_key.startswith('AIza')}")
            
            # Configure Gemini with detailed error handling
            try:
                genai.configure(api_key=api_key)
                logger.info("Successfully configured Gemini with API key")
            except Exception as config_error:
                logger.error(f"Failed to configure Gemini: {config_error}")
                return
            
            # Initialize model with more error details
            try:
                logger.info("Initializing Gemini model: models/gemini-2.0-flash")
                genai.configure(api_key=api_key)
                
                # Set default generation config
                generation_config = {
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                }
                
                # Initialize model with specific configuration
                self.model = genai.GenerativeModel(
                    model_name='models/gemini-2.0-flash',
                    generation_config=generation_config
                )
                logger.info("Model initialized successfully")
                
                # Test with a simple image prompt
                try:
                    # Create a small test image
                    test_image = Image.new('RGB', (100, 100), color='red')
                    test_response = self.model.generate_content(["Describe this image", test_image])
                    test_response.resolve()
                    logger.info(f"Vision test response received: {test_response.text[:30]}...")
                    self.gemini_available = True
                    logger.info("✅ Gemini Vision API initialized successfully")
                except Exception as vision_test_error:
                    logger.error(f"Vision API test failed: {vision_test_error}")
                    raise
            except Exception as model_error:
                logger.error(f"Failed to initialize model: {model_error}")
                return
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _ensure_bucket_exists(self):
        """Check if the GCS bucket exists."""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            # Just check if bucket exists, don't try to modify permissions
            exists = bucket.exists()
            if exists:
                logger.info(f"Using existing bucket: {self.bucket_name}")
                return True
            else:
                logger.warning(f"Bucket {self.bucket_name} does not exist")
                return False
        except Exception as e:
            logger.error(f"Error checking bucket: {e}")
            return False
    
    def _upload_to_gcs(self, file_path, destination_blob_name=None):
        """Upload a file to Google Cloud Storage."""
        if not self.gcs_available:
            logger.warning("Google Cloud Storage not available, skipping upload")
            return None
            
        try:
            if destination_blob_name is None:
                destination_blob_name = f"videos/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(file_path)}"
                
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(destination_blob_name)
            
            # Upload with retry logic
            max_retries = int(os.getenv('MAX_RETRIES', '3'))
            for attempt in range(max_retries):
                try:
                    # Upload the file
                    blob.upload_from_filename(file_path)
                    
                    # Get the public URL - we assume the bucket is already configured for public access
                    public_url = f"https://storage.googleapis.com/{self.bucket_name}/{destination_blob_name}"
                    
                    logger.info(f"File {file_path} uploaded to {public_url}")
                    return public_url
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Upload attempt {attempt + 1} failed: {e}. Retrying...")
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise
            
        except Exception as e:
            logger.error(f"Error uploading to GCS: {e}")
            return None

    def analyze_mechanics(self, video_path, pitcher_name, pitch_type, game_type):
        """
        Analyze pitcher mechanics from a video.
        
        Args:
            video_path: Path to the video file
            pitcher_name: Name or level of the pitcher
            pitch_type: Type of pitch being thrown
            game_type: Context of the game
            
        Returns:
            Dictionary with mechanics score and analysis
        """
        try:
            logger.info(f"Starting analysis for {pitcher_name}, {pitch_type}, {game_type}")
            logger.info(f"Video path: {video_path}")
            
            # First, try to use Google Cloud Storage
            if self.gcs_available:
                try:
                    # Check if this is a GCS URL already (from existing video)
                    if video_path.startswith('https://storage.googleapis.com/'):
                        logger.info("Using existing GCS video URL")
                        existing_video = video_path
                    else:
                        # For new uploads, check if video already exists
                        video_filename = os.path.basename(video_path)
                        bucket = self.storage_client.bucket(self.bucket_name)
                        
                        # Look for the video in the videos/ directory
                        existing_video = None
                        for blob in bucket.list_blobs(prefix='videos/'):
                            if video_filename in blob.name:
                                existing_video = blob.public_url
                                logger.info(f"Found existing video in GCS: {existing_video}")
                                break
                        
                        # If video doesn't exist and this is a new upload, upload it
                        if not existing_video and not video_path.startswith('https://'):
                            gcs_path = self._upload_to_gcs(video_path)
                            if gcs_path:
                                logger.info(f"Video uploaded to GCS: {gcs_path}")
                                existing_video = gcs_path
                    
                    # Use Gemini with GCS URL
                    if self.gemini_available and existing_video:
                        result = self._analyze_with_gemini(video_path, pitcher_name, pitch_type, game_type, gcs_url=existing_video)
                        return result
                except Exception as e:
                    logger.error(f"GCS upload failed: {e}")
            
            # If GCS is not available or upload failed, warn about reduced accuracy
            logger.warning("Google Cloud Storage is not available. Analysis accuracy may be reduced.")
            
            # Fall back to rule-based analysis
            logger.info("Using rule-based analysis as fallback")
            return self._generate_analysis(pitcher_name, pitch_type, game_type)
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                'mechanics_score': 0,
                'deviations': [f"Analysis failed: {str(e)}"],
                'recommendations': ["Please try again or contact support"]
            }
    
    def _compress_video(self, input_path, max_size_mb=10):
        """Compress video to a smaller size while maintaining quality."""
        logger.info(f"Compressing video from {input_path}")
        
        try:
            # Create a temporary file for the compressed video
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                output_path = temp_file.name
            
            # Read the video
            cap = cv2.VideoCapture(input_path)
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Calculate new dimensions while maintaining aspect ratio
            if width > 640 or height > 480:
                if width > height:
                    new_width = 640
                    new_height = int(height * (640/width))
                else:
                    new_height = 480
                    new_width = int(width * (480/height))
            else:
                new_width = width
                new_height = height
            
            # Create video writer with H.264 codec
            fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
            out = cv2.VideoWriter(output_path, fourcc, fps, (new_width, new_height))
            
            frame_count = 0
            max_frames = min(int(fps * 5), 150)  # Limit to 5 seconds or 150 frames
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret or frame_count >= max_frames:
                    break
                    
                # Resize frame
                if width != new_width or height != new_height:
                    frame = cv2.resize(frame, (new_width, new_height))
                
                out.write(frame)
                frame_count += 1
            
            cap.release()
            out.release()
            
            # Verify the output file exists and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Video compressed successfully to {output_path} ({frame_count} frames)")
                return output_path
            else:
                logger.error("Compression failed: Output file is empty or missing")
                return input_path
            
        except Exception as e:
            logger.error(f"Error compressing video: {e}")
            return input_path

    def _analyze_with_gemini(self, video_path, pitcher_name, pitch_type, game_type, gcs_url=None):
        """Analyze video using Gemini's multimodal capabilities."""
        try:
            # Create the prompt
            prompt = self._create_analysis_prompt(pitcher_name, pitch_type, game_type)
            logger.info("Generated analysis prompt")
            
            # Use the GCS URL if provided, otherwise use the local video path
            video_url = gcs_url if gcs_url else video_path
            
            # Get response from Gemini
            logger.info("Sending request to Gemini...")
            try:
                # Create content list with prompt and video URL
                content = [{
                    "text": prompt + "\n\nAnalyze this video showing the complete pitching motion."
                }, {
                    "text": f"Video URL: {video_url}"
                }]
                
                # Generate content
                logger.info(f"Sending request with video URL")
                response = self.model.generate_content(content)
                response.resolve()
                
                # Log the raw response for debugging
                logger.info("Raw Gemini response received")
                logger.info(f"Response text:\n{response.text}")
                
                analysis_text = response.text.strip()
                
                # Verify the response contains expected sections
                if "INJURY/FATIGUE INDICATORS:" not in analysis_text or "KEY METRICS:" not in analysis_text:
                    logger.warning("Response missing expected sections. Retrying with modified prompt...")
                    
                    # Modify prompt to be more explicit
                    modified_prompt = prompt + "\n\nIMPORTANT: Please analyze the provided video and structure your response exactly as shown above, including all sections (INJURY/FATIGUE INDICATORS and KEY METRICS)."
                    
                    # Retry with modified prompt
                    content[0]["text"] = modified_prompt
                    response = self.model.generate_content(content)
                    response.resolve()
                    
                    analysis_text = response.text.strip()
                
                # Return the raw analysis
                return {
                    'raw_analysis': analysis_text
                }
            
            except Exception as e:
                logger.error(f"Error in video analysis: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
            
        except Exception as e:
            logger.error(f"Error in video analysis: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _create_analysis_prompt(self, pitcher_name, pitch_type, game_type, frame_names=None):
        """Create a detailed prompt for Gemini analysis."""
        
        # Define specific analysis criteria based on pitcher level and pitch type
        pitcher_level_context = ""
        pitch_specific_focus = ""
        
        # Adjust context based on pitcher level
        if "kershaw" in pitcher_name.lower():
            pitcher_level_context = """
            As an elite MLB pitcher analysis, focus on:
            - Advanced mechanics refinement
            - Elite-level consistency markers
            - Professional performance optimization
            - High-velocity impact on mechanics
            """
        else:  # Amateur
            pitcher_level_context = """
            As an amateur pitcher analysis, focus on:
            - Fundamental mechanics development
            - Basic form correction
            - Injury prevention for developing players
            - Building consistent mechanics
            """
        
        # Adjust focus based on pitch type
        if pitch_type.lower() == "curveball":
            pitch_specific_focus = """
            For curveball analysis, evaluate:
            - Arm slot consistency for spin axis
            - Wrist/finger position impact
            - Hip-shoulder separation timing
            - Release point precision
            """
        else:  # Fastball
            pitch_specific_focus = """
            For fastball analysis, evaluate:
            - Power generation through legs
            - Direct line to plate
            - Arm speed and timing
            - Follow-through completion
            """
        
        base_prompt = f"""
        You are a professional baseball pitching coach analyzing this pitcher's mechanics from the provided video. Be extremely precise in your measurements using these specific guidelines:

        Pitcher: {pitcher_name}
        Pitch Type: {pitch_type}
        Game Context: {game_type}

        {pitcher_level_context}
        
        {pitch_specific_focus}
        
        Use these specific measurement criteria:

        1. Arm: Grade both arm action and release point
        - Arm Action (A-F grade):
          * A: Efficient path, clean circle, no deviation
          * B: Minor path deviation, good timing
          * C: Moderate path issues, some timing variance
          * D: Significant path issues, poor timing
          * F: Severe mechanical issues, injury risk
        - Release Point:
          * Over the top: Above ear level
          * High three-quarters: Between ear and top of shoulder
          * Three-quarters: At shoulder level
          * Low three-quarters: Between shoulder and elbow
          * Sidearm: At or below elbow

        2. Balance: Measure head position relative to back hip during leg lift
        - Grade (A-F):
          * A: Head stays within 2 inches of vertical line from back hip
          * B: Head moves 2-4 inches from vertical line
          * C: Head moves 4-6 inches from vertical line
          * D: Head moves 6-8 inches from vertical line
          * F: Head moves more than 8 inches from vertical line

        3. Stride & Drive: Grade both leg drive power and stride mechanics
        - Leg Drive (A-F grade):
          * A: Explosive drive, maintains direction
          * B: Good drive, slight directional loss
          * C: Moderate drive, some leakage
          * D: Weak drive, significant leakage
          * F: Poor drive, severe mechanical issues
        - Stride Length & Direction:
          * Optimal: 85-100% of height, direct to plate
          * Good: 80-85% of height, slight closed/open
          * Fair: 75-80% of height, moderately closed/open
          * Poor: <75% or >100%, severely closed/open

        Provide a single, concise analysis focusing only on these specific aspects. Format your response EXACTLY as follows, with NO additional commentary:

        KEY METRICS:

        Arm: [Grade (A-F) for arm action] - [one line describing key arm path observation] | Release Point: [exact position using criteria above]

        Balance: [Grade (A-F) based on head movement criteria above] - [one line noting exact head movement distance from vertical line]

        Stride & Drive: [Grade (A-F) for leg drive] - [one line on drive quality] | Stride: [length as % of height and direction to plate]

        Overall: [2-4 sentences evaluating the pitcher's mechanics like an MLB scout/coach would. Include: 1) Overall mechanical efficiency and potential, 2) Most critical adjustment needed, 3) Long-term projection if improvements are made. Be specific about velocity, movement, and command potential.]

        INJURY/FATIGUE INDICATORS:
        Risk Level: [Low/High] - [2-3 sentences explaining specific mechanical patterns that contribute to injury risk. Include both immediate concerns and long-term durability factors.]
        - Low Risk: Default classification unless clear signs of injury or fatigue are present.
        - High Risk: Reserved for extremely concerning signs of injury or fatigue that need immediate intervention.
        """
        return base_prompt
    
    def _parse_gemini_response(self, response_text):
        """Parse Gemini's response into structured format."""
        try:
            # Initialize default values
            score = 70
            issues = []
            recommendations = []
            
            # Parse score
            if "SCORE:" in response_text:
                score_text = response_text.split("SCORE:")[1].split("\n")[0]
                try:
                    score = int(''.join(filter(str.isdigit, score_text)))
                except ValueError:
                    score = 70

            # Parse issues
            if "ISSUES:" in response_text:
                issues_section = response_text.split("ISSUES:")[1].split("RECOMMENDATIONS:")[0]
                issues = [issue.strip() for issue in issues_section.split("•") if issue.strip()]
                issues = issues[:3]  # Ensure exactly 3 issues

            # Parse recommendations
            if "RECOMMENDATIONS:" in response_text:
                recommendations_section = response_text.split("RECOMMENDATIONS:")[1]
                recommendations = [rec.strip() for rec in recommendations_section.split("•") if rec.strip()]
                recommendations = recommendations[:3]  # Ensure exactly 3 recommendations

            # Ensure we have exactly 3 items for each category
            while len(issues) < 3:
                issues.append("Additional analysis needed")
            while len(recommendations) < 3:
                recommendations.append("Additional recommendations pending")

            return {
                'mechanics_score': score,
                'deviations': issues,
                'recommendations': recommendations
            }

        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return self._generate_analysis("generic", "fastball", "practice")
    
    def _generate_analysis(self, pitcher_name, pitch_type, game_type):
        """Generate customized analysis based on inputs."""
        logger.info(f"Generating rule-based analysis for {pitcher_name}, {pitch_type}, {game_type}")
        
        # Calculate score based on inputs
        score = self._calculate_score(pitcher_name, pitch_type, game_type)
        
        # Generate fallback analysis
        if "kershaw" in pitcher_name.lower():
            injury_indicators = [
                "No significant injury risk factors observed",
                "Normal fatigue patterns for professional level",
                "Consistent mechanics throughout delivery"
            ]
            metrics = {
                "Arm Slot": {"score": 9, "analysis": "Elite high arm slot, consistent with Kershaw's form"},
                "Balance": {"score": 9, "analysis": "Excellent balance and posture throughout delivery"},
                "Leg Drive": {"score": 9, "analysis": "Strong, consistent leg drive with good hip-shoulder separation"}
            }
        else:
            injury_indicators = [
                "Some inconsistency in arm slot may increase injury risk",
                "Moderate stress on shoulder during late phase",
                "Normal fatigue patterns for development level"
            ]
            metrics = {
                "Arm Slot": {"score": 7, "analysis": "Generally good, some inconsistency in late phases"},
                "Balance": {"score": 6, "analysis": "Room for improvement in maintaining center of gravity"},
                "Leg Drive": {"score": 7, "analysis": "Good power generation, needs better front leg block"}
            }
        
        return {
            'mechanics_score': score,
            'injury_indicators': injury_indicators,
            'key_metrics': metrics
        }
    
    def _calculate_score(self, pitcher_name, pitch_type, game_type):
        """Calculate a mechanics score based on inputs."""
        # Base score
        score = 75
        
        # Only allow Kershaw or Amateur
        pitcher_lower = pitcher_name.lower()
        if "kershaw" in pitcher_lower:
            score = 90  # Kershaw gets a high base score
        elif "amateur" in pitcher_lower:
            score = 70  # Amateur gets a moderate base score
        else:
            score = 75  # Default case, though we should prevent this
        
        # Simple pitch type adjustments
        pitch_lower = pitch_type.lower()
        if pitch_lower == "fastball":
            score += 2
        elif pitch_lower == "curveball":
            score -= 2
            
        # Ensure score is within bounds
        return max(0, min(100, score))
    
    def _generate_issues(self, pitcher_name, pitch_type, game_type):
        """Generate customized issues based on inputs."""
        pitcher_lower = pitcher_name.lower()
        
        if "kershaw" in pitcher_lower:
            issues = [
                "Minor timing variation in leg lift phase",
                "Slight early trunk rotation before front foot plants",
                "Occasional glove-side drift during delivery"
            ]
        else:  # Amateur
            issues = [
                "Inconsistent leg drive during push-off phase",
                "Arm slot drops during delivery, creating strain on shoulder",
                "Head movement disrupts balance throughout pitching motion"
            ]
            
        return issues
    
    def _generate_recommendations(self, pitcher_name, pitch_type, game_type):
        """Generate customized recommendations based on inputs."""
        pitcher_lower = pitcher_name.lower()
        
        if "kershaw" in pitcher_lower:
            recommendations = [
                "Fine-tune leg lift timing for optimal rhythm",
                "Delay trunk rotation until front foot is firmly planted",
                "Maintain consistent glove position through release"
            ]
        else:  # Amateur
            recommendations = [
                "Focus on maintaining consistent leg drive throughout delivery",
                "Practice keeping arm slot high to reduce shoulder strain",
                "Keep head still and aligned with target throughout motion"
            ]
            
        return recommendations
    
    def check_connectivity(self):
        """Check if we can connect to Gemini API and Google Cloud."""
        return {
            'gemini': self.gemini_available,
            'google_cloud': self.gcs_available
        } 