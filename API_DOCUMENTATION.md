# API Documentation - Vercel Edge Function

## Overview

This project includes a Vercel Edge Function for generating secure keys. The edge function runs at the edge of Vercel's network for low latency and high performance.

## Deployment

### Prerequisites
- Vercel account
- Vercel CLI (optional but recommended)

### Deploy to Vercel

1. **Via Vercel Dashboard:**
   - Go to [vercel.com](https://vercel.com)
   - Click "Import Project"
   - Connect your GitHub repository
   - Vercel will automatically detect the configuration
   - Click "Deploy"

2. **Via Vercel CLI:**
   ```bash
   npm i -g vercel
   vercel login
   vercel
   ```

## API Endpoint

### Generate Key

**Endpoint:** `POST /api/generate-key`

**Request Body:**
```json
{
  "url": "https://example.com/resource"
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "key": "A1B2C3D4E5F6",
  "timestamp": "2025-11-12T16:30:00.000Z"
}
```

**Response (Error - 400):**
```json
{
  "error": "URL is required"
}
```

**Response (Error - 500):**
```json
{
  "error": "Failed to generate key",
  "message": "Error details"
}
```

## Usage Example

### JavaScript/Fetch
```javascript
const generateKey = async (url) => {
  try {
    const response = await fetch('/api/generate-key', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url }),
    });
    
    const data = await response.json();
    
    if (data.success) {
      console.log('Generated Key:', data.key);
      return data.key;
    } else {
      console.error('Error:', data.error);
    }
  } catch (error) {
    console.error('Request failed:', error);
  }
};

// Usage
generateKey('https://example.com/resource');
```

### cURL
```bash
curl -X POST https://your-domain.vercel.app/api/generate-key \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/resource"}'
```

## Features

- **Edge Runtime**: Runs on Vercel's Edge Network for minimal latency
- **CORS Enabled**: Supports cross-origin requests
- **Error Handling**: Comprehensive error responses
- **Validation**: Input validation for URL parameter
- **Secure**: Generates cryptographically random keys

## File Structure

```
.
├── api/
│   └── generate-key.js       # Edge function handler
├── vercel.json                # Vercel configuration
├── key-extractor.html         # Frontend interface
└── API_DOCUMENTATION.md       # This file
```

## Configuration

The `vercel.json` file configures the edge function:

```json
{
  "version": 2,
  "functions": {
    "api/**/*.js": {
      "runtime": "edge"
    }
  }
}
```

## Local Development

To test locally:

1. Install Vercel CLI:
   ```bash
   npm i -g vercel
   ```

2. Run development server:
   ```bash
   vercel dev
   ```

3. The API will be available at:
   ```
   http://localhost:3000/api/generate-key
   ```

## Environment Variables

Currently, no environment variables are required. If you need to add any:

1. Create `.env.local` file (not committed to git)
2. Add variables in Vercel Dashboard under Project Settings → Environment Variables

## Troubleshooting

### CORS Issues
If you encounter CORS errors, ensure the edge function includes proper CORS headers (already configured).

### Deployment Failures
- Check that `vercel.json` is in the root directory
- Verify the `api/` folder structure is correct
- Review build logs in Vercel dashboard

### Function Timeout
Edge functions have a 30-second timeout. If operations take longer, consider:
- Optimizing the function
- Moving to serverless functions instead

## Support

For issues or questions:
- Check Vercel documentation: https://vercel.com/docs
- Review Edge Function limits: https://vercel.com/docs/functions/edge-functions

## License

MIT License - See repository for details.
