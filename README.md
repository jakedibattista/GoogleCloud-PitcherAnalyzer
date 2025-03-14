# Pitcher Analysis Tool ⚾

A machine learning-powered tool for analyzing baseball pitcher mechanics using video analysis and Gemini API.

## Features

- **Video Analysis**: Upload and analyze pitch videos with advanced computer vision
- **Detailed Mechanical Analysis**: Get comprehensive breakdown of pitching mechanics
- **Injury Risk Assessment**: Identify potential injury risks in pitching motion
- **Performance Optimization**: Receive actionable recommendations to improve mechanics
- **Visual Feedback**: Clear visualizations of mechanical issues and improvements

## Secure Deployment

This application is configured for secure deployment on Google Cloud Run with:
- Secure credential management
- Environment variable configuration
- Cloud Storage integration
- Automated CI/CD pipeline

### Prerequisites

1. **Google Cloud Platform Account**
2. **Gemini API Access**
3. **Docker**
4. **Python 3.9+**

## Local Development

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/GoogleCloud-PitcherAnalyzer.git
cd GoogleCloud-PitcherAnalyzer
```

2. **Set up environment**:
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. **Configure environment variables**:
- Copy `.env.example` to `.env`
- Fill in your configuration values

4. **Run locally**:
```bash
streamlit run app.py
```

## Deployment

The application automatically deploys to Google Cloud Run when changes are pushed to the main branch.

Required GitHub Secrets:
- `GCP_PROJECT_ID`: Google Cloud project ID
- `GCP_BUCKET_NAME`: Cloud Storage bucket name
- `GCP_SA_KEY`: Service account key JSON
- `GEMINI_API_KEY`: Gemini API key

## Security

- All sensitive credentials are managed through GitHub Secrets
- No credentials are stored in version control
- Secure cloud deployment configuration
- Environment-based configuration management

## Troubleshooting

If you encounter issues:

1. **Check credentials**: Ensure your Google Cloud credentials are properly set up
2. **Verify dependencies**: Make sure all required packages are installed
3. **Check logs**: Review application logs for error messages
4. **Video format**: Ensure your video meets the recommended specifications

## Requirements

- Python 3.8+
- Google Cloud account with Gemini API enabled
- Gemini API key
- OpenCV and related dependencies

## License

This project is licensed under the MIT License - see the LICENSE file for details.

