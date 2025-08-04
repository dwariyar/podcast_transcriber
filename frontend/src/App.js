import React, { useState } from 'react';
// Import Bootstrap components from react-bootstrap
import { Container, Card, Form, Button, Spinner, Alert, ListGroup } from 'react-bootstrap';

// Main App component
const App = () => {
    const [rssUrl, setRssUrl] = useState('');
    const [numEpisodes, setNumEpisodes] = useState(1);
    const [sampleDuration, setSampleDuration] = useState(60);
    const [transcribedEpisodes, setTranscribedEpisodes] = useState([]);
    const [status, setStatus] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [statusUpdates, setStatusUpdates] = useState([]);
    const [algoliaLink, setAlgoliaLink] = useState('');

    // New states for user-provided API keys
    const [openaiApiKey, setOpenaiApiKey] = useState('');
    const [algoliaAppId, setAlgoliaAppId] = useState('');
    const [algoliaWriteApiKey, setAlgoliaWriteApiKey] = useState('');

    // Dynamically determine the backend URL based on environment
    const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5001';
    const backendUrl = `${API_BASE_URL}/transcribe`;

    // Function to handle transcription by calling the Flask backend
    const handleTranscribe = async () => {
        setError('');
        setTranscribedEpisodes([]);
        setStatus('');
        setStatusUpdates([]);
        setAlgoliaLink('');

        if (!rssUrl) {
            setError('Please enter a podcast RSS feed URL.');
            return;
        }

        // Validate API keys
        if (!openaiApiKey || !algoliaAppId || !algoliaWriteApiKey) {
            setError('Please provide all required API keys (OpenAI, Algolia App ID, Algolia Write API Key).');
            return;
        }

        setIsLoading(true);
        setStatus('Initiating transcription process...');
        setStatusUpdates(['Initiating transcription process...']);

        try {
            const response = await fetch(backendUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    rss_url: rssUrl,
                    numEpisodes: numEpisodes,
                    sampleDuration: sampleDuration,
                    openaiApiKey: openaiApiKey,         // Send OpenAI API Key
                    algoliaAppId: algoliaAppId,         // Send Algolia App ID
                    algoliaWriteApiKey: algoliaWriteApiKey // Send Algolia Write API Key
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                if (errorData.status_updates) {
                    setStatusUpdates(prev => [...prev, ...errorData.status_updates]);
                }
                throw new Error(errorData.error || `Backend error: ${response.status} ${response.statusText}`);
            }

            const result = await response.json();

            if (result.status_updates) {
                setStatusUpdates(result.status_updates);
            }

            if (result.message) {
                setStatus(result.message);
                if (result.transcribed_episodes && result.transcribed_episodes.length > 0) {
                    setTranscribedEpisodes(result.transcribed_episodes);
                } else {
                    setStatus(result.message || 'Transcription complete, but no episodes found or transcribed.');
                }

                // Construct Algolia dashboard link using user-provided App ID and fixed index name
                if (algoliaAppId) { // Use the user-provided algoliaAppId
                    const algoliaDashboardLink = `https://dashboard.algolia.com/apps/${algoliaAppId}/explorer/browse/podcast_episodes?searchMode=search`;
                    setAlgoliaLink(algoliaDashboardLink);
                }

            } else {
                setError(result.error || 'An unknown error occurred on the backend.');
            }

        } catch (err) {
            console.error('Frontend caught transcription error:', err);
            setError(`Transcription failed: ${err.message}. Please check the URL and backend server.`);
            setStatus('Error');
            setStatusUpdates(prev => [...prev, `Error: ${err.message}`]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Container className="d-flex flex-column align-items-center justify-content-center min-vh-100 py-4 bg-light">
            <Card className="shadow-lg p-4 p-md-5 w-100" style={{ maxWidth: '600px', borderRadius: '1rem' }}>
                <Card.Body>
                    <h1 className="text-center mb-4 text-dark fs-3 fw-bold">Podcast Transcriber</h1>
                    
                    <Form className="mb-4">
                        {/* API Key Inputs */}
                        <Form.Group controlId="openai-api-key" className="mb-3">
                            <Form.Label className="fw-semibold text-secondary">OpenAI API Key:</Form.Label>
                            <Form.Control
                                type="password" // Use password type for sensitive input
                                placeholder="sk-..."
                                value={openaiApiKey}
                                onChange={(e) => setOpenaiApiKey(e.target.value)}
                                disabled={isLoading}
                                className="rounded-lg shadow-sm"
                            />
                        </Form.Group>

                        <Form.Group controlId="algolia-app-id" className="mb-3">
                            <Form.Label className="fw-semibold text-secondary">Algolia Application ID:</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="Your Algolia App ID"
                                value={algoliaAppId}
                                onChange={(e) => setAlgoliaAppId(e.target.value)}
                                disabled={isLoading}
                                className="rounded-lg shadow-sm"
                            />
                        </Form.Group>

                        <Form.Group controlId="algolia-write-api-key" className="mb-4">
                            <Form.Label className="fw-semibold text-secondary">Algolia Write API Key:</Form.Label>
                            <Form.Control
                                type="password" // Use password type for sensitive input
                                placeholder="Your Algolia Write API Key"
                                value={algoliaWriteApiKey}
                                onChange={(e) => setAlgoliaWriteApiKey(e.target.value)}
                                disabled={isLoading}
                                className="rounded-lg shadow-sm"
                            />
                        </Form.Group>

                        <hr className="mb-4"/> {/* Separator */}

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

                        <Form.Group controlId="num-episodes" className="mb-3">
                            <Form.Label className="fw-semibold text-secondary">Number of Episodes to Transcribe:</Form.Label>
                            <Form.Control
                                type="number"
                                value={numEpisodes}
                                onChange={(e) => setNumEpisodes(Math.max(1, parseInt(e.target.value) || 1))}
                                min="1"
                                disabled={isLoading}
                                className="rounded-lg shadow-sm"
                            />
                        </Form.Group>

                        <Form.Group controlId="sample-duration" className="mb-4">
                            <Form.Label className="fw-semibold text-secondary">Audio Sample Duration (seconds):</Form.Label>
                            <Form.Control
                                type="number"
                                value={sampleDuration}
                                onChange={(e) => setSampleDuration(Math.max(10, parseInt(e.target.value) || 60))}
                                min="10"
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

                    {/* Granular Process Tracking */}
                    {statusUpdates.length > 0 && (
                        <div className="mt-4">
                            <h3 className="text-center mb-2 text-dark fs-6 fw-semibold">Process Log:</h3>
                            <ListGroup className="shadow-sm" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                                {statusUpdates.map((msg, index) => (
                                    <ListGroup.Item key={index} variant="light" className="py-1 px-2 text-muted small">
                                        {msg}
                                    </ListGroup.Item>
                                ))}
                            </ListGroup>
                        </div>
                    )}

                    {/* General Status/Error Alerts */}
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

                    {/* Algolia Link */}
                    {algoliaLink && (
                        <div className="mt-4 text-center">
                            <h3 className="text-center mb-2 text-dark fs-6 fw-semibold">View Algolia Dashboard:</h3>
                            <Button 
                                variant="outline-info" 
                                href={algoliaLink} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="rounded-lg shadow-sm"
                            >
                                Go to Algolia Index
                            </Button>
                        </div>
                    )}

                    {/* Transcription Results */}
                    {transcribedEpisodes.length > 0 && (
                        <div className="mt-5">
                            <h2 className="text-center mb-3 text-dark fs-5 fw-semibold">Transcription Result(s):</h2>
                            {transcribedEpisodes.map((episode, index) => (
                                <Card key={index} className="bg-light border-secondary p-3 shadow-inner mb-3">
                                    <Card.Title className="text-dark fs-6 fw-semibold">{episode.title}</Card.Title>
                                    <Card.Text className="text-muted text-justify" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                                        {episode.full_transcription}
                                    </Card.Text>
                                </Card>
                            ))}
                        </div>
                    )}
                </Card.Body>
            </Card>
        </Container>
    );
};

export default App;
