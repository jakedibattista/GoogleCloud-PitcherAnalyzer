"""Module for managing video uploads and processing."""

import os
import logging
import tempfile
import cv2
import numpy as np
from datetime import datetime
from google.cloud import storage
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Placeholder for Vision API
class VisionPlaceholder:
    """Placeholder for the Vision API."""
    
    def __init__(self):
        """Initialize the Vision API placeholder."""
        logger.warning("Vision API not available, using placeholder")
    
    def text_detection(self, image):
        """Placeholder for text detection."""
        logger.warning("Vision API text_detection called but not available")
        return []

# Create a placeholder for the Vision API
vision = VisionPlaceholder()

class VideoManager:
    """Manager for video uploads and processing."""
    
    def __init__(self):
        """Initialize the video manager."""
        logger.info("Initializing VideoManager")
        
        # Initialize Google Cloud Storage client if credentials are available
        self.storage_client = None
        try:
            self.project_id = os.getenv('GCP_PROJECT_ID') or os.getenv('GOOGLE_CLOUD_PROJECT')
            self.bucket_name = os.getenv('GCP_BUCKET_NAME')
            
            if self.project_id and self.bucket_name:
                self.storage_client = storage.Client(project=self.project_id)
                logger.info(f"Google Cloud Storage initialized with bucket: {self.bucket_name}")
            else:
                logger.warning("Google Cloud Storage configuration not found, using local storage")
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Storage: {e}")
    
    def process_video(self, video_path):
        """
        Process a video file to extract frames.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary with video metadata
        """
        try:
            logger.info(f"Processing video: {video_path}")
            
            # Get video metadata
            metadata = self._get_video_metadata(video_path)
            logger.info(f"Video metadata: {metadata}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return {
                'error': str(e),
                'frames': 0,
                'duration': 0,
                'fps': 0,
                'width': 0,
                'height': 0
            }
    
    def _get_video_metadata(self, video_path):
        """
        Get metadata from a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary with video metadata
        """
        try:
            # Open the video file
            cap = cv2.VideoCapture(video_path)
            
            # Check if video opened successfully
            if not cap.isOpened():
                logger.error(f"Error opening video file: {video_path}")
                return {
                    'error': 'Could not open video file',
                    'frames': 0,
                    'duration': 0,
                    'fps': 0,
                    'width': 0,
                    'height': 0
                }
            
            # Get video properties
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Calculate duration
            duration = frame_count / fps if fps > 0 else 0
            
            # Release the video capture object
            cap.release()
            
            return {
                'frames': frame_count,
                'duration': duration,
                'fps': fps,
                'width': width,
                'height': height
            }
            
        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            return {
                'error': str(e),
                'frames': 0,
                'duration': 0,
                'fps': 0,
                'width': 0,
                'height': 0
            }
    
    def get_gcs_uri(self, video_path: str) -> str:
        """
        Get the GCS URI for a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            GCS URI for the video file
        """
        if not self.storage_client:
            logger.warning("Google Cloud Storage not initialized, cannot get GCS URI")
            return ""
            
        try:
            # Get the filename from the path
            filename = os.path.basename(video_path)
            
            # Create the GCS URI
            gcs_uri = f"gs://{self.bucket_name}/videos/{filename}"
            
            return gcs_uri
        except Exception as e:
            logger.error(f"Error getting GCS URI: {e}")
            return ""
    
    def download_from_gcs(self, gcs_path):
        """
        Download a file from Google Cloud Storage.
        
        Args:
            gcs_path: GCS path to the file
            
        Returns:
            Local path to the downloaded file
        """
        if not self.storage_client:
            logger.warning("Google Cloud Storage not initialized, cannot download from GCS")
            return None
            
        try:
            # Parse the GCS path
            if gcs_path.startswith("gs://"):
                gcs_path = gcs_path[5:]
            
            bucket_name, blob_path = gcs_path.split("/", 1)
            
            # Get the bucket and blob
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                local_path = tmp_file.name
            
            # Download the file
            blob.download_to_filename(local_path)
            
            return local_path
        except Exception as e:
            logger.error(f"Error downloading from GCS: {e}")
            return None
    
    def trim_video(self, video_path: str, duration: int = 5) -> str:
        """
        Trim a video to the specified duration.
        
        Args:
            video_path: Path to the video file
            duration: Duration in seconds
            
        Returns:
            Path to the trimmed video
        """
        try:
            # Check if ffmpeg is available
            if not self._check_ffmpeg():
                logger.error("ffmpeg not found, cannot trim video")
                return video_path
                
            # Get video metadata
            metadata = self._get_video_metadata(video_path)
            
            # If the video is shorter than the requested duration, return the original
            if metadata['duration'] <= duration:
                return video_path
                
            # Create a temporary file for the trimmed video
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                trimmed_path = tmp_file.name
            
            # Trim the video using ffmpeg
            import subprocess
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-t', str(duration),
                '-c:v', 'copy',
                '-c:a', 'copy',
                trimmed_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            return trimmed_path
        except Exception as e:
            logger.error(f"Error trimming video: {e}")
            return video_path
    
    def find_video(self, video_name):
        """
        Find a video by name.
        
        Args:
            video_name: Name of the video
            
        Returns:
            Path to the video
        """
        try:
            # Check local videos first
            local_videos = self.list_local_videos()
            for video in local_videos:
                if video_name in video:
                    return video
                    
            # Check cloud videos if available
            if self.storage_client:
                cloud_videos = self.list_cloud_videos()
                for video in cloud_videos:
                    if video_name in video:
                        return self.download_from_gcs(video)
                        
            return None
        except Exception as e:
            logger.error(f"Error finding video: {e}")
            return None
    
    def _check_ffmpeg(self):
        """
        Check if ffmpeg is available.
        
        Returns:
            True if ffmpeg is available, False otherwise
        """
        try:
            import subprocess
            subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True)
            return True
        except Exception:
            return False
    
    def list_local_videos(self):
        """
        List local videos.
        
        Returns:
            List of local video paths
        """
        try:
            videos = []
            
            # Check common directories
            for directory in ['videos', 'uploads', 'data']:
                if os.path.exists(directory):
                    for filename in os.listdir(directory):
                        if filename.endswith(('.mp4', '.mov', '.avi')):
                            videos.append(os.path.join(directory, filename))
                            
            return videos
        except Exception as e:
            logger.error(f"Error listing local videos: {e}")
            return []
    
    def list_cloud_videos(self):
        """
        List videos in Google Cloud Storage.
        
        Returns:
            List of GCS URIs
        """
        if not self.storage_client:
            logger.warning("Google Cloud Storage not initialized, cannot list cloud videos")
            return []
            
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blobs = bucket.list_blobs(prefix='videos/')
            
            return [f"gs://{self.bucket_name}/{blob.name}" for blob in blobs if blob.name.endswith(('.mp4', '.mov', '.avi'))]
        except Exception as e:
            logger.error(f"Error listing cloud videos: {e}")
            return []
    
    def detect_velocity(self, video_path):
        """
        Detect the velocity of a pitch in a video.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Estimated velocity in mph
        """
        try:
            # This is a placeholder for actual velocity detection
            # In a real implementation, this would use computer vision to detect the velocity
            
            # For now, return a random velocity between 70 and 95 mph
            import random
            return random.randint(70, 95)
        except Exception as e:
            logger.error(f"Error detecting velocity: {e}")
            return 0
    
    def _ocr_text(self, image):
        """
        Extract text from an image using OCR.
        
        Args:
            image: Image to extract text from
            
        Returns:
            Extracted text
        """
        try:
            # Use the Vision API placeholder
            results = vision.text_detection(image)
            
            # In a real implementation, this would extract text from the results
            # For now, return an empty string
            return ""
        except Exception as e:
            logger.error(f"Error performing OCR: {e}")
            return ""
    
    def get_video(self, video_name):
        """
        Get a video by name.
        
        Args:
            video_name: Name of the video
            
        Returns:
            Path to the video
        """
        try:
            # Find the video
            video_path = self.find_video(video_name)
            
            if not video_path:
                logger.error(f"Video not found: {video_name}")
                return None
                
            return video_path
        except Exception as e:
            logger.error(f"Error getting video: {e}")
            return None
    
    def rename_video(self, old_name: str, new_name: str) -> bool:
        """
        Rename a video in Google Cloud Storage.
        
        Args:
            old_name: Current name of the video
            new_name: New name for the video
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.storage_client:
            logger.warning("Google Cloud Storage not initialized, cannot rename video")
            return False
            
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            
            # Get the old blob
            old_blob = bucket.blob(f"videos/{old_name}")
            if not old_blob.exists():
                logger.error(f"Video {old_name} not found")
                return False
            
            # Preserve the file extension
            old_ext = os.path.splitext(old_name)[1]  # Get extension from old name
            new_name_with_ext = new_name if new_name.endswith(old_ext) else f"{new_name}{old_ext}"
            
            # Create new blob
            new_blob = bucket.blob(f"videos/{new_name_with_ext}")
            
            # Copy old blob to new blob
            bucket.copy_blob(old_blob, bucket, new_blob.name)
            
            # Delete old blob
            old_blob.delete()
            
            logger.info(f"Successfully renamed video from {old_name} to {new_name_with_ext}")
            return True
            
        except Exception as e:
            logger.error(f"Error renaming video: {e}")
            return False
    
    def delete_video(self, video_name: str) -> bool:
        """
        Delete a video from Google Cloud Storage.
        
        Args:
            video_name: Name of the video to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.storage_client:
            logger.warning("Google Cloud Storage not initialized, cannot delete video")
            return False
            
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(f"videos/{video_name}")
            
            if not blob.exists():
                logger.error(f"Video {video_name} not found")
                return False
            
            # Delete the blob
            blob.delete()
            
            logger.info(f"Successfully deleted video: {video_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting video: {e}")
            return False
    
    def delete_all_videos(self) -> bool:
        """
        Delete all videos from Google Cloud Storage.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.storage_client:
            logger.warning("Google Cloud Storage not initialized, cannot delete videos")
            return False
            
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blobs = bucket.list_blobs(prefix='videos/')
            
            for blob in blobs:
                blob.delete()
                logger.info(f"Deleted video: {blob.name}")
            
            logger.info("Successfully deleted all videos")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting all videos: {e}")
            return False
    
    def get_video_info(self, video_name: str) -> dict:
        """
        Get information about a video in Google Cloud Storage.
        
        Args:
            video_name: Name of the video
            
        Returns:
            dict: Video information including size, upload time, etc.
        """
        if not self.storage_client:
            logger.warning("Google Cloud Storage not initialized, cannot get video info")
            return {
                'name': video_name,
                'size': 'Unknown',
                'uploaded': 'Unknown',
                'url': None,
                'error': 'Google Cloud Storage not initialized'
            }
            
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(f"videos/{video_name}")
            
            if not blob.exists():
                logger.error(f"Video {video_name} not found")
                return {
                    'name': video_name,
                    'size': 'Unknown',
                    'uploaded': 'Unknown',
                    'url': None,
                    'error': 'Video not found'
                }
            
            # Get blob metadata
            blob.reload()
            
            # Handle case where size might be None
            size_str = 'Unknown'
            if blob.size is not None:
                size_str = f"{blob.size / (1024 * 1024):.2f} MB"
            
            # Handle case where time_created might be None
            uploaded_str = 'Unknown'
            if blob.time_created is not None:
                uploaded_str = blob.time_created.strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                'name': video_name,
                'size': size_str,
                'uploaded': uploaded_str,
                'url': blob.public_url if blob.public_url else None
            }
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return {
                'name': video_name,
                'size': 'Unknown',
                'uploaded': 'Unknown',
                'url': None,
                'error': str(e)
            }
    
    def slow_down_video(self, video_path, speed_factor=0.5):
        """Create a slow-motion version of the video."""
        logger.info(f"Creating slow motion version of video with speed factor {speed_factor}")
        
        try:
            # Create a temporary file for the output
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                output_path = temp_file.name
            
            # Use ffmpeg directly for more reliable encoding
            import subprocess
            
            # Calculate the output frame rate (slow motion)
            probe_cmd = [
                'ffmpeg',
                '-i', video_path,
                '-hide_banner'
            ]
            
            # Get video info
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            fps_match = re.search(r'(\d+(?:\.\d+)?) fps', probe_result.stderr)
            input_fps = float(fps_match.group(1)) if fps_match else 30.0
            output_fps = input_fps * speed_factor
            
            # Construct ffmpeg command for slow motion
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f'setpts={1/speed_factor}*PTS',  # Slow down video
                '-r', str(output_fps),  # Set output frame rate
                '-c:v', 'libx264',  # Use software H.264 encoder
                '-preset', 'medium',  # Balance between speed and quality
                '-crf', '23',  # Quality setting (lower is better, 23 is default)
                '-movflags', '+faststart',  # Enable streaming
                '-y',  # Overwrite output file if it exists
                output_path
            ]
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                return video_path
            
            # Verify the output file exists and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Slow motion video created successfully: {output_path}")
                return output_path
            else:
                logger.error("Slow motion processing failed: Output file is empty or missing")
                return video_path
            
        except Exception as e:
            logger.error(f"Slow motion processing failed: {e}")
            return video_path
    
    def download_video(self, gcs_uri: str) -> str:
        """
        Download a video from Google Cloud Storage.
        
        Args:
            gcs_uri: GCS URI of the video (e.g., 'gs://bucket-name/path/to/video.mp4')
            
        Returns:
            str: Path to the downloaded video file
        """
        try:
            if not self.storage_client:
                logger.warning("Google Cloud Storage not initialized")
                raise ValueError("Storage client not initialized")

            # Validate GCS URI format
            if not gcs_uri.startswith('gs://'):
                logger.error(f"Invalid GCS URI format: {gcs_uri}")
                raise ValueError("Invalid GCS URI format")

            # Parse bucket name and blob path
            bucket_name = gcs_uri.split('/')[2]
            blob_path = '/'.join(gcs_uri.split('/')[3:])

            # Get bucket
            bucket = self.storage_client.bucket(bucket_name)

            # Create a temporary file to store the downloaded video
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                temp_path = tmp_file.name

            # Download the blob
            blob = bucket.blob(blob_path)
            blob.download_to_filename(temp_path)
            
            logger.info(f"Successfully downloaded video to {temp_path}")
            return temp_path

        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            raise ValueError(f"Error downloading video: {str(e)}") 