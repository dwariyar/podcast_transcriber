# Setting Up

This project implements a web application for transcribing podcast episodes, leveraging OpenAI's Whisper model for speech-to-text conversion and Algolia for efficient search indexing. The architecture comprises a Python Flask backend for core logic and data management, and a React frontend for user interaction.

---

## Features

- **Podcast RSS Feed Ingestion**: Parses provided RSS feed URLs to extract podcast episode metadata.
- **Audio Sample Extraction**: Downloads and processes audio, extracting configurable random samples to optimize transcription time and resource consumption.
- **Speech-to-Text Transcription**: Utilizes OpenAI's Whisper model for high-accuracy audio transcription.
- **Local Data Persistence**: Stores episode titles and transcripts in a SQLite database.
- **Algolia Integration**: Indexes transcribed content with Algolia for powerful, faceted search capabilities.
- **Interactive Frontend**: A React application facilitating RSS URL submission and displaying transcription results.

---

## Repository Structure

The project adheres to a standard two-tier directory structure:

### `backend/`: Houses the Flask application and associated Python modules

- `app.py`: Flask application entry point and API routes  
- `podcast_workflow.py`: Orchestration logic for the transcription pipeline  
- `fetch_rss.py`: RSS feed parsing utility  
- `download_audio.py`: Audio downloading and sampling logic  
- `transcribe.py`: Whisper model integration  
- `database.py`: SQLite database abstraction  
- `upload_algolia.py`: Algolia API integration for indexing  
- `requirements.txt`: Python package dependencies  

### `frontend/`: Contains the React application

- `public/`: Static assets  
- `src/`: React source code (e.g., `App.js`, `index.js`)  
- `package.json`: Node.js dependencies and project scripts  

---

## Prerequisites

Make sure the following tools are installed:

- **Git** — Version control  
- **Python 3.8+** — Backend runtime (`pip` will be available)  
- **Node.js 14+ & npm 6+** — Frontend runtime and package manager  

---

## Setup Instructions

### 1. Repository Initialization

Clone the project:

```bash
git clone https://github.com/dwariyar/podcast_transcriber.git
cd podcast_transcriber
```

### 2. Backend Environment Configuration

Navigate to the 'backend' directory:

```bash
cd backend
```

### a. Virtual Environment and Dependencies

Create and activate a Python virtual environment, then install required packages:

```bash
python3 -m venv venv           # Create venv (use `py -m venv venv` on Windows)
source venv/bin/activate       # Activate venv (use `.\venv\Scripts\activate.bat` or `.\venv\Scripts\Activate.ps1` on Windows)
pip install -r requirements.txt
```

### b. Environment Variables

Populate your Algolia API credentials by creating a .env file from the example.
Edit .env to include your actual Algolia Application ID and Write API Key:

```bash
APP_ID="YOUR_ACTUAL_ALGOLIA_APPLICATION_ID"
ALGOLIA_WRITE_API_KEY="YOUR_ACTUAL_ALGOLIA_WRITE_API_KEY"
```

Acquire these from your Algolia Dashboard. Ensure the Write API Key possesses addObject, deleteObject, listIndexes, and settings permissions.

### 3. Frontend Environment Configuration

Navigate to the 'frontend' directory:

```bash
cd ../frontend
```

### a. Node.js Dependencies

Install the necessary Node.js packages:

```bash
npm install
```

### b. Bootstrap Integration

Bootstrap is utilized for frontend styling. Ensure its CSS is imported in your React application. The recommended approach is via 'src/index.js'.

Verify 'frontend/src/index.js' includes:

```bash
import 'bootstrap/dist/css/bootstrap.min.css';
```

## Running the Application

### 1. Start the Backend (Flask API)

From the 'backend/' directory, ensure your Python virtual environment is active:

```bash
cd my_podcast_project/backend
source venv/bin/activate # Or Windows equivalent
python app.py
```

### 2. Start the Frontend (React App)

From the 'frontend/' directory:

```bash
cd my_podcast_project/frontend
npm start
```

The React development server will usually launch your browser to http://localhost:3000.

With both services running, you can now interact with the Podcast Transcriber application via your browser.
