// Supabase Edge Function for Key Extraction
// Handles domain-based routing for nanolinks, arolinks, and lksfy

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

// Constants
const DEFAULT_TARGET = 'https://zoo0.pages.dev';
const DEFAULT_USER_AGENT = 'Dart/3.8 (dart:io)';
const XOR_KEY = 'k6kW8r#Tz3f;';
const HEADER_NAMES = ['x-request-id', 'x-payload', 'authorization', 'x-data'];

// Types
interface ExtractionResult {
  success: boolean;
  key?: string;
  error?: string;
  domain?: string;
  timestamp: string;
}

// Utility Functions
function xorDecrypt(base64Data: string, key: string): string {
  const raw = atob(base64Data);
  const keyBytes = new TextEncoder().encode(key);
  const result: number[] = [];
  
  for (let i = 0; i < raw.length; i++) {
    result.push(raw.charCodeAt(i) ^ keyBytes[i % keyBytes.length]);
  }
  
  return new TextDecoder().decode(new Uint8Array(result));
}

async function getInitialHeaders(): Promise<{ baseUrl: string }> {
  const response = await fetch(DEFAULT_TARGET, {
    headers: { 'User-Agent': DEFAULT_USER_AGENT }
  });
  
  let combined = '';
  for (const headerName of HEADER_NAMES) {
    combined += response.headers.get(headerName) || '';
  }
  
  const decoded = xorDecrypt(combined, XOR_KEY);
  const jsonMatch = decoded.match(/\{[^}]+\}/);
  if (!jsonMatch) throw new Error('Failed to extract JSON');
  
  const data = JSON.parse(jsonMatch[0]);
  return { baseUrl: data.baseUrl };
}

async function fetchKeyUrl(baseUrl: string): Promise<string> {
  const url = `${baseUrl}/api/v1/auth/generate?server=1`;
  const response = await fetch(url);
  const data = await response.json();
  return data.data.keyUrl;
}

// Domain Handlers
async function handleNanoLinks(keyUrl: string): Promise<string> {
  const id = keyUrl.split('/').pop()!;
  
  // First request
  const url1 = `https://nano.tackledsoul.com/includes/open.php?id=${id}`;
  const response1 = await fetch(url1, {
    redirect: 'manual',
    headers: { Cookie: `tp=${id}; open=${id}` }
  });
  
  const redirect1 = response1.headers.get('location');
  if (!redirect1) throw new Error('No redirect from nanolinks');
  
  const newId = redirect1.split('/').pop()!;
  
  // Second request
  const url2 = `https://vi-music.app/includes/open.php?id=${newId}`;
  const response2 = await fetch(url2, {
    redirect: 'manual',
    headers: { Cookie: `tp=${newId}; open=${newId}` }
  });
  
  const redirect2 = response2.headers.get('location');
  if (!redirect2) throw new Error('No final redirect');
  
  const keyMatch = redirect2.match(/key=([^&]+)/);
  if (!keyMatch) throw new Error('Key not found');
  
  return keyMatch[1];
}

async function handleAroLinks(keyUrl: string): Promise<string> {
  const id = keyUrl.split('/').pop()!;
  
  // First request
  const response1 = await fetch(keyUrl);
  const html1 = await response1.text();
  
  const redirectMatch = html1.match(/window\.location\.href = "([^"]+)"/) ||
                        html1.match(/<a href="([^"]+)"/);
  if (!redirectMatch) throw new Error('Redirect URL not found');
  
  const redirectUrl = redirectMatch[1];
  
  // Second request with cookies
  const response2 = await fetch(keyUrl, {
    headers: {
      Cookie: `gt_uc_=${id}`,
      Referer: redirectUrl
    }
  });
  
  const html2 = await response2.text();
  
  // Try to find key
  let keyMatch = html2.match(/href="(https?:\/\/[^"]+key=([^"&]+)[^"]*)"/);
  if (keyMatch) return keyMatch[2];
  
  // Try code parameter
  keyMatch = html2.match(/href="(https?:\/\/[^"]+code=([^"&]+)[^"]*)"/);
  if (keyMatch) return keyMatch[2];
  
  throw new Error('Key not found in arolinks');
}

async function aesDecrypt(ciphertext: string, alias: string): Promise<string> {
  // Double base64 decode
  const decoded1 = atob(ciphertext);
  const decoded2 = atob(decoded1);
  
  // Generate key and IV
  const keySource = `sDye71jNq5${alias}`;
  const ivSource = `7M9u8DG4X${alias}`;
  
  const keyHash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(keySource));
  const ivHash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(ivSource));
  
  const key = new Uint8Array(keyHash).slice(0, 32);
  const iv = new Uint8Array(ivHash).slice(0, 16);
  
  // Import key
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    key,
    { name: 'AES-CBC' },
    false,
    ['decrypt']
  );
  
  // Decrypt
  const cipherBytes = new Uint8Array(decoded2.split('').map(c => c.charCodeAt(0)));
  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-CBC', iv },
    cryptoKey,
    cipherBytes
  );
  
  return new TextDecoder().decode(decrypted);
}

async function handleLksfy(keyUrl: string): Promise<string> {
  const alias = keyUrl.split('/').pop()!;
  
  // First request to get redirect
  const response1 = await fetch(keyUrl, {
    redirect: 'manual',
    headers: { Referer: keyUrl }
  });
  
  const redirectUrl = response1.headers.get('location');
  if (!redirectUrl) throw new Error('No redirect from lksfy');
  
  // Second request with referer
  const response2 = await fetch(keyUrl, {
    headers: { Referer: redirectUrl }
  });
  
  const html = await response2.text();
  
  // Extract base64 value
  const base64Match = html.match(/var base64 = \'([^\']+)\'/);
  if (!base64Match) throw new Error('Base64 value not found');
  
  // Decrypt to get form data
  const decryptedHtml = await aesDecrypt(base64Match[1], alias);
  
  // Extract form fields
  const csrfMatch = decryptedHtml.match(/name="_csrfToken"[^>]*value="([^"]+)"/);
  const adFormMatch = decryptedHtml.match(/name="ad_form_data"[^>]*value="([^"]+)"/);
  const tokenFieldsMatch = decryptedHtml.match(/name="_Token\[fields\]"[^>]*value="([^"]+)"/);
  const tokenUnlockedMatch = decryptedHtml.match(/name="_Token\[unlocked\]"[^>]*value="([^"]+)"/);
  const actionMatch = decryptedHtml.match(/action="([^"]+)"/);
  
  if (!csrfMatch || !actionMatch) throw new Error('Form data extraction failed');
  
  // Wait 5 seconds to prevent rate limiting
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  // POST request
  const postUrl = `https://lksfy.com${actionMatch[1]}`;
  const body = new URLSearchParams({
    '_method': 'POST',
    '_csrfToken': csrfMatch[1],
    'ad_form_data': adFormMatch?.[1] || '',
    '_Token[fields]': tokenFieldsMatch?.[1] || '',
    '_Token[unlocked]': tokenUnlockedMatch?.[1] || ''
  });
  
  const postResponse = await fetch(postUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'Referer': 'https://lksfy.com/',
      'Cookie': `csrfToken=${csrfMatch[1]}`,
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: body.toString()
  });
  
  const jsonResponse = await postResponse.json();
  
  if (jsonResponse.status !== 'success') {
    throw new Error(jsonResponse.message || 'POST request failed');
  }
  
  // Decrypt the URL
  const decryptedUrl = await aesDecrypt(jsonResponse.url, alias);
  
  // Extract key
  const keyMatch = decryptedUrl.match(/key=([^&]+)/);
  if (!keyMatch) throw new Error('Key not found in URL');
  
  return keyMatch[1];
}

// Main Handler
serve(async (req) => {
  // CORS headers
  if (req.method === 'OPTIONS') {
    return new Response('ok', {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
      },
    });
  }

  try {
    const { url } = await req.json();
    
    if (!url) {
      return new Response(
        JSON.stringify({ success: false, error: 'URL is required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Get baseUrl and keyUrl
    const { baseUrl } = await getInitialHeaders();
    const keyUrl = await fetchKeyUrl(baseUrl);
    
    // Detect domain and route to appropriate handler
    let key: string;
    let domain: string;
    
    if (keyUrl.includes('nanolinks')) {
      domain = 'nanolinks';
      key = await handleNanoLinks(keyUrl);
    } else if (keyUrl.includes('arolinks')) {
      domain = 'arolinks';
      key = await handleAroLinks(keyUrl);
    } else if (keyUrl.includes('lksfy')) {
      domain = 'lksfy';
      key = await handleLksfy(keyUrl);
    } else {
      // Default to nanolinks
      domain = 'nanolinks';
      key = await handleNanoLinks(keyUrl);
    }

    const result: ExtractionResult = {
      success: true,
      key,
      domain,
      timestamp: new Date().toISOString()
    };

    return new Response(
      JSON.stringify(result),
      { 
        headers: { 
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        } 
      }
    );
    
  } catch (error) {
    const result: ExtractionResult = {
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    };

    return new Response(
      JSON.stringify(result),
      { 
        status: 500,
        headers: { 
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        } 
      }
    );
  }
});
