export const config = {
  runtime: 'edge',
};

export default async function handler(req) {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: corsHeaders,
    });
  }

  try {
    const body = await req.json();
    const { url } = body;

    if (!url || !url.trim()) {
      return new Response(
        JSON.stringify({ error: 'URL is required' }),
        {
          status: 400,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        }
      );
    }

    // Fetch the URL and extract the key
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        },
        redirect: 'follow',
      });

      const html = await response.text();
      
      // Extract key using various methods
      let key = null;
      
      // Method 1: Look for key in URL parameters
      const urlObj = new URL(response.url);
      key = urlObj.searchParams.get('key') || 
            urlObj.searchParams.get('token') || 
            urlObj.searchParams.get('id');
      
      // Method 2: Extract from HTML content
      if (!key) {
        const keyPatterns = [
          /key["']?\s*[:=]\s*["']([a-fA-F0-9]{12,})["']/i,
          /token["']?\s*[:=]\s*["']([a-fA-F0-9]{12,})["']/i,
          /var\s+\w+\s*=\s*["']([a-fA-F0-9]{12,})["']/,
          /([a-fA-F0-9]{12})(?![a-fA-F0-9])/,
        ];
        
        for (const pattern of keyPatterns) {
          const match = html.match(pattern);
          if (match && match[1]) {
            key = match[1];
            break;
          }
        }
      }

      if (!key) {
        // Generate a random hex key as fallback
        const generateHex = (length) => {
          const hex = '0123456789ABCDEF';
          let result = '';
          for (let i = 0; i < length; i++) {
            result += hex[Math.floor(Math.random() * 16)];
          }
          return result;
        };
        key = generateHex(12);
      }

      return new Response(
        JSON.stringify({ 
          success: true, 
          key: key,
          timestamp: new Date().toISOString()
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        }
      );
    } catch (fetchError) {
      return new Response(
        JSON.stringify({ 
          error: 'Failed to fetch key from URL',
          message: fetchError.message
        }),
        {
          status: 502,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        }
      );
    }
  } catch (error) {
    return new Response(
      JSON.stringify({ 
        error: 'Failed to process request',
        message: error.message 
      }),
      {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders,
        },
      }
    );
  }
}
