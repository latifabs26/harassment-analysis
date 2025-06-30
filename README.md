# 🔍 Harassment Analysis Pipeline

A comprehensive system for collecting, analyzing, and monitoring harassment content on social media platforms using AI-powered toxicity detection.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Docker Deployment](#docker-deployment)
- [Data Pipeline](#data-pipeline)

## 🎯 Overview

This project implements an end-to-end pipeline for:
- **Collecting** harassment-related posts from Twitter/X
- **Cleaning** and preprocessing text data
- **Analyzing** toxicity levels using state-of-the-art AI models
- **Storing** results in MongoDB for further analysis
- **Providing** REST API endpoints for data access

## ✨ Features

### 🐦 Social Media Collection
- Automated Twitter/X post collection using hashtag #harcèlement
- Configurable collection limits and filtering
- Metadata extraction (likes, retweets, replies, timestamps)
- User anonymization for privacy protection

### 🧹 Text Processing
- URL removal and link sanitization
- Mention (@username) stripping
- Hashtag normalization
- Special character cleaning
- Text standardization and formatting

### 🤖 AI-Powered Toxicity Analysis
- Multi-language toxicity detection using [Detoxify](https://github.com/unitaryai/detoxify)
- Comprehensive scoring across 6 dimensions:
  - General toxicity
  - Severe toxicity
  - Obscenity
  - Threats
  - Insults
  - Identity attacks
- Confidence level assessment
- Customizable toxicity thresholds

### 💾 Data Management
- MongoDB integration for scalable storage
- Automatic duplicate detection and handling
- Structured data schemas with validation
- Aggregation pipeline for statistics

### 🌐 REST API
- FastAPI-based high-performance API
- Interactive documentation with Swagger UI
- Background task processing
- Comprehensive error handling

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Twitter API   │ -> │  Data Collector  │ -> │   JSON Files    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    Statistics   │ <- │     MongoDB      │ <- │  FastAPI Processor│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                 │                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Toxicity Analysis│    │  Text Cleaner   │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Installation

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- Twitter API Bearer Token
- MongoDB (or use Docker setup)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/latifabs26/harassment-analysis.git
   cd harassment-analysis-pipeline
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Twitter Bearer Token
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run with Docker (Recommended)**
   ```bash
   docker-compose up --build
   ```

### Manual Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start MongoDB (if not using Docker)
mongod --dbpath ./data/db

# Run the collector
python app.py

# Run the API (in another terminal)
python api.py
```

## 📖 Usage

### 1. Data Collection

```bash
# Collect harassment posts from Twitter
python app.py
```

This will:
- Search for posts with #harcèlement hashtag
- Save raw data to `harassment_posts.json`
- Log collection statistics

### 2. API Processing

```bash
# Start the FastAPI server
uvicorn api:app --reload

# Process collected data
curl -X POST "http://localhost:8000/process-file"
```

### 3. View Results

- **API Documentation**: http://localhost:8000/docs
- **Statistics**: http://localhost:8000/stats
- **MongoDB Interface**: http://localhost:8081 (if using Docker)

## 🛠️ API Documentation

### Core Endpoints

#### Data Processing
- `POST /upload-posts` - Upload posts to database
- `POST /process-file` - Process collected JSON file
- `POST /clean-text` - Clean individual text
- `POST /analyze-toxicity` - Analyze text toxicity

#### Data Retrieval
- `GET /get-posts` - Retrieve stored posts
- `GET /get-analysis` - Retrieve toxicity analyses
- `GET /stats` - Get comprehensive statistics

### Example API Calls

```bash
# Get toxicity statistics
curl http://localhost:8000/stats

# Analyze text toxicity
curl -X POST "http://localhost:8000/analyze-toxicity" \
  -H "Content-Type: application/json" \
  -d '"Your text to analyze"'

# Clean text
curl -X POST "http://localhost:8000/clean-text" \
  -H "Content-Type: application/json" \
  -d '"Text with @mentions #hashtags http://links.com"'
```

## 🐳 Docker Deployment

### Services Overview

- **mongo**: MongoDB database
- **mongo-express**: Database administration interface
- **twitter-scraper**: Automated data collection
- **harassment-api**: FastAPI analysis service

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build
```

### Service URLs

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Mongo Express**: http://localhost:8081 (admin/admin)

## 📊 Data Pipeline

### 1. Collection Phase
```python
# Input: Twitter API
# Output: Raw JSON file
{
  "id": "1234567890",
  "text": "Post about #harcèlement...",
  "author_id": "user_12345",
  "created_at": "2025-06-30T10:30:00+00:00",
  "likes": 5,
  "retweets": 2,
  "replies": 1
}
```

### 2. Cleaning Phase
```python
# Input: "Check this link http://example.com @user123 #harcèlement !!! 😡😡"
# Output: "Check this link harcelement"
```

### 3. Analysis Phase
```python
# Input: "You are really stupid and I hate you"
# Output: 
{
  "toxicity": 0.85,
  "severe_toxicity": 0.12,
  "obscene": 0.23,
  "threat": 0.08,
  "insult": 0.78,
  "identity_attack": 0.05,
  "is_toxic": true,
  "confidence_level": "high"
}
```

### 4. Storage Phase
- **Posts Collection**: Original and cleaned posts
- **Analysis Collection**: Toxicity scores and classifications
- **Indexing**: Optimized queries on ID and toxicity scores

## 📈 Statistics & Monitoring

The system provides comprehensive analytics:

- **Collection Metrics**: Total posts, timeframes, sources
- **Toxicity Metrics**: Distribution of toxicity scores
- **Classification Stats**: Percentage of toxic vs. non-toxic content
- **Temporal Analysis**: Trends over time
- **Author Analytics**: Anonymized user behavior patterns

## 🔧 Configuration

### Environment Variables

```env
# Twitter API Configuration
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# Database Configuration
MONGO_URL=mongodb://localhost:27017/

# API Configuration (optional)
API_HOST=0.0.0.0
API_PORT=8000
```

### Toxicity Thresholds

Modify toxicity classification thresholds in `api.py`:

```python
# Default threshold for toxic classification
TOXICITY_THRESHOLD = 0.7

# Confidence levels
CONFIDENCE_THRESHOLDS = {
    'high': 0.8,
    'medium': 0.5,
    'low': 0.0
}
```



## 📝 Project Structure

```
harassment-analysis-pipeline/
├── app.py                 # Twitter data collector
├── api.py                 # FastAPI application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Multi-container setup
├── .env
├── README.md            # This file
├── data/                # Data storage directory
│   ├── harassment_posts.json
│   └── processed/

```




## 📊 Performance Metrics

- **Collection Rate**: ~100 posts/minute
- **Processing Speed**: ~50 posts/second
- **API Response Time**: <100ms for analysis


### Common Issues

1. **Twitter API Rate Limits**
   - Solution: Implement exponential backoff
   - Monitor rate limit headers

2. **MongoDB Connection Errors**
   - Check MongoDB service status
   - Verify connection string format

3. **Detoxify Model Loading**
   - Ensure sufficient memory (2GB+)
   - Check internet connectivity for model download



## 📚 References

- [Detoxify Documentation](https://github.com/unitaryai/detoxify)
- [Twitter API v2 Documentation](https://developer.twitter.com/en/docs/twitter-api)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Documentation](https://docs.mongodb.com/)



**⭐ This project was made by BEN SLAMA LATIFA, final year Data Science Engineering Student.**