export const config = {
  runtime: 'edge',
};

export default async function handler(req) {
  // Enable CORS
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  // Handle preflight OPTIONS request
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: corsHeaders,
    });
  }

  try {
    // Parse request body
    const body = await req.json();
    const { url } = body;

    // Validate URL
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

    // Generate random hex key (12 characters)
    const generateHex = (length) => {
      const hex = '0123456789ABCDEF';
      let result = '';
      for (let i = 0; i < length; i++) {
        result += hex[Math.floor(Math.random() * 16)];
      }
      return result;
    };

    const key = generateHex(12);

    // Return generated key
    return new Response(
      JSON.stringify({ 
        success: true, 
        key,
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
  } catch (error) {
    return new Response(
      JSON.stringify({ 
        error: 'Failed to generate key',
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
