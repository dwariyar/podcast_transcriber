import React, { useState } from 'react';
// Import Bootstrap components from react-bootstrap
import { Container, Card, Form, Button, Spinner, Alert } from 'react-bootstrap';

// Main App component
const App = () => {
    const [rssUrl, setRssUrl] = useState('');
    const [transcript, setTranscript] = useState('');
    const [status, setStatus] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    // Function to handle transcription by calling the Flask backend
    const handleTranscribe = async () => {
        setError('');
        setTranscript('');
        setStatus('');

        if (!rssUrl) {
            setError('Please enter a podcast RSS feed URL.');
            return;
        }

        setIsLoading(true);
        setStatus('Sending request to backend for transcription...');

        try {
            // Make a POST request to your Flask backend's /transcribe endpoint
            // Dynamically determine the backend URL based on environment
            // In production (GitHub Pages build), it will use REACT_APP_API_BASE_URL from .env.production

            const API_BASE_URL = (typeof process !== 'undefined' && process.env.REACT_APP_API_BASE_URL) 
                         ? process.env.REACT_APP_API_BASE_URL 
                         : 'https://podcast-transcriber-backend.onrender.com'; // Fallback
            const backendUrl = `${API_BASE_URL}/transcribe`;

            const response = await fetch(backendUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ rss_url: rssUrl }), // Send the RSS URL in a JSON payload
            });

            // Check if the response was successful (HTTP status 2xx)
            if (!response.ok) {
                // If the backend sent an error response (e.g., 400, 500), parse its JSON body
                const errorData = await response.json();
                throw new Error(errorData.error || `Backend error: ${response.status} ${response.statusText}`);
            }

            // Parse the JSON response from the backend
            const result = await response.json();

            if (result.status === 'success') {
                setTranscript(result.transcript || 'No transcript returned.');
                setStatus(result.message || 'Transcription complete!');
            } else {
                // Handle cases where backend returns status: 'error' but still 200 OK
                setError(result.message || 'An unknown error occurred on the backend.');
            }

        } catch (err) {
            console.error('Frontend caught transcription error:', err);
            // Display the error message from the caught exception
            setError(`Transcription failed: ${err.message}. Please check the URL and backend server.`);
            setStatus('Error');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        // Using Bootstrap's utility classes and components
        <Container className="d-flex flex-column align-items-center justify-content-center min-vh-100 py-4 bg-light">
            <Card className="shadow-lg p-4 p-md-5 w-100" style={{ maxWidth: '600px', borderRadius: '1rem' }}>
                <Card.Body>
                    <h1 className="text-center mb-4 text-dark fs-3 fw-bold">Podcast Transcriber</h1>
                    
                    <Form className="mb-4">
                        <Form.Group controlId="rss-url" className="mb-3">
                            <Form.Label className="fw-semibold text-secondary">Enter Podcast RSS Feed URL:</Form.Label>
                            <Form.Control
                                type="url"
                                placeholder="e.g., https://feeds.npr.org/510310/podcast.xml"
                                value={rssUrl}
                                onChange={(e) => setRssUrl(e.target.value)}
                                disabled={isLoading}
                                className="rounded-lg shadow-sm"
                            />
                        </Form.Group>

                        <Button
                            variant="primary"
                            className="w-100 py-2 rounded-lg fw-bold text-white shadow-sm"
                            onClick={handleTranscribe}
                            disabled={isLoading}
                            style={{ transition: 'all 0.2s ease-in-out', transform: isLoading ? 'scale(1)' : 'scale(1)' }}
                        >
                            {isLoading ? (
                                <>
                                    <Spinner animation="border" size="sm" className="me-2" />
                                    Transcribing...
                                </>
                            ) : (
                                'Transcribe Podcast'
                            )}
                        </Button>
                    </Form>

                    {status && !error && (
                        <Alert variant="info" className="mt-4 text-center">
                            {status}
                        </Alert>
                    )}

                    {error && (
                        <Alert variant="danger" className="mt-4 text-center">
                            {error}
                        </Alert>
                    )}

                    {transcript && (
                        <div className="mt-5">
                            <h2 className="text-center mb-3 text-dark fs-5 fw-semibold">Transcription Result:</h2>
                            <Card className="bg-light border-secondary p-3 shadow-inner" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                                <Card.Text className="text-muted text-justify">
                                    {transcript}
                                </Card.Text>
                            </Card>
                        </div>
                    )}
                </Card.Body>
            </Card>
        </Container>
    );
};

export default App;
