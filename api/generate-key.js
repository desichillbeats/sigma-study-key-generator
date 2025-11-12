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

    // Make request to the key finder service
    const keyFinderUrl = 'https://preview--route-key-finder.lovable.app';
    
    try {
      // Send POST request to key finder with the user's URL
      const response = await fetch(keyFinderUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url }),
      });

      if (!response.ok) {
        throw new Error(`Key finder service returned ${response.status}`);
      }

      const data = await response.json();
      
      // Extract the key from the response
      // Adjust this based on the actual response structure
      const key = data.key || data.generatedKey || data.result;
      
      if (!key) {
        throw new Error('No key found in response');
      }

      // Return the extracted key
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
      // If the key finder service fails, return an error
      return new Response(
        JSON.stringify({ 
          error: 'Failed to fetch key from service',
          message: fetchError.message,
          details: 'Please check if the key finder service is available'
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
