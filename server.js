const express = require('express');
const app = express();
app.use(express.json());

// Your verification token (we'll set this in Render's environment variables)
const VERIFICATION_TOKEN = process.env.VERIFICATION_TOKEN;

// Endpoint for eBay marketplace account deletion
app.post('/ebay-deletion', (req, res) => {
    console.log('Received deletion notification:', req.body);
    res.status(200).json({ message: 'Notification received' });
});

// Verification endpoint
app.get('/ebay-deletion', (req, res) => {
    const challenge = req.query.challenge_code;
    if (!challenge) {
        return res.status(400).json({ error: 'No challenge code provided' });
    }
    res.status(200).json({ challengeResponse: challenge });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
