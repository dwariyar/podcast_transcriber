# Setting Up

This project implements a web application for transcribing podcast episodes, leveraging OpenAI's Whisper model for speech-to-text conversion and Algolia for efficient search indexing. The architecture comprises a Python Quart backend for core logic and data management, and a React frontend for user interaction.

---

## Features

- **Podcast RSS Feed Ingestion**: Parses provided RSS feed URLs to extract podcast episode metadata.
- **Audio Sample Extraction**: Downloads and processes audio, extracting user-defined random samples (in minutes) to optimize transcription time and resource consumption.
- **Speech-to-Text Transcription**: Utilizes OpenAI's Whisper model for high-accuracy audio transcription, using a user-provided OpenAI API key.
- **Local Data Persistence**: Stores episode titles and transcripts in a SQLite database.
- **Algolia Integration**: Indexes transcribed content with Algolia for powerful search capabilities, using user-provided Algolia Application ID and Write API Key.
- **Interactive Frontend**: A React application facilitating RSS URL submission, configurable number of episodes for transcription, displaying transcription results, and real-time granular process tracking.
- **Algolia Dashboard Link**: Provides a direct link to the Algolia dashboard's index explorer, allowing users to view their indexed transcripts (requires Algolia login).

---

## Repository Structure

The project adheres to a standard two-tier directory structure:

### `backend/`: Houses the Quart application and associated Python modules

- `app.py`: Quart application entry point, API routes, and a health check  
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

Navigate to the `backend/` directory:

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

### b. API Key Management

Note: OpenAI and Algolia API keys (Application ID, Write API Key) are now provided directly via the frontend UI when you run the application. You do not need to configure them in backend environment variables (like a `.env` file) for the backend to function. Ensure your Algolia Write API Key possesses addObject, deleteObject, listIndexes, and settings permissions for full functionality.

### c. Character Encoding (Important for Transcription)

If you encounter a `UnicodeEncodeError` or `'ascii' codec can't encode character` error during transcription (especially with podcast titles or content containing special characters like curly quotes “ ”), it's likely due to your terminal's default character encoding.

To ensure your Python environment correctly handles all Unicode characters, set your locale environment variables to UTF-8 before running your Quart backend:

```bash
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

### 3. Frontend Environment Configuration

Navigate to the `frontend/` directory:

```bash
cd ../frontend
```

### a. Node.js Dependencies

Install the necessary Node.js packages:

```bash
npm install
```

### b. Bootstrap Integration

Bootstrap is utilized for frontend styling. Ensure its CSS is imported in your React application. The recommended approach is via `src/index.js`.

Verify `frontend/src/index.js` includes:

```bash
import 'bootstrap/dist/css/bootstrap.min.css';
```

## Running the Application Locally

### 1. Start the Backend (Quart API)

From the `backend/` directory, ensure your Python virtual environment is active and you've set the locale environment variables (see 2.c above):

```bash
cd my_podcast_project/backend
source venv/bin/activate # Or Windows equivalent
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export PYTHONPATH=$PYTHONPATH:/path/to/backend
export QUART_APP=app.py
quart run --host 0.0.0.0 --port 5001
```

### 2. Start the Frontend (React App)

From the `frontend/` directory:

```bash
cd my_podcast_project/frontend
npm start
```

The React development server will usually launch your browser to `http://localhost:3000`.

With both services running, you can now interact with the Podcast Transcriber application via your browser.

You will now need to input your OpenAI API Key, Algolia Application ID, and Algolia Write API Key directly into the provided fields in the frontend UI before initiating a transcription.
