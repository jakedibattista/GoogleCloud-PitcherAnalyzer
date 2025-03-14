"""Main module for the Baseball Pitcher Analyzer application."""

import logging
from pitcher_analyzer.mechanics_analyzer import MechanicsAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PitcherAnalysis:
    """Main class for the Baseball Pitcher Analyzer."""
    
    def __init__(self):
        """Initialize the PitcherAnalysis class."""
        logger.info("Initializing PitcherAnalysis")
        self.mechanics_analyzer = MechanicsAnalyzer()
        logger.info("PitcherAnalysis initialized successfully")
        
    def analyze_video(self, video_path, pitcher_name, pitch_type, game_type):
        """
        Analyze a baseball pitcher's mechanics from a video.
        
        Args:
            video_path: Path to the video file
            pitcher_name: Name or level of the pitcher
            pitch_type: Type of pitch being thrown
            game_type: Context of the game
            
        Returns:
            Analysis results including mechanics score and recommendations
        """
        try:
            logger.info(f"Analyzing video: {video_path}")
            
            results = self.mechanics_analyzer.analyze_mechanics(
                video_path=video_path,
                pitcher_name=pitcher_name,
                pitch_type=pitch_type,
                game_type=game_type
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing video: {e}")
            return {
                'mechanics_score': 0,
                'deviations': [f"Analysis failed: {str(e)}"],
                'recommendations': ["Please try again or contact support"]
            } 