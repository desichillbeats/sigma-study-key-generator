# 🤖 Telegram Bot Solution for Key Extraction

## 💡 Problem Statement

The key extraction flow has **changed**:

**OLD FLOW** (Direct):
```
User enters URL → Domain Handler → Extract Key → Return Key
```

**NEW FLOW** (Telegram Bot Redirect):
```
User enters URL → Domain Handler → Redirects to Telegram Bot @sigma_keygen_bot → User clicks START → Bot gives Key
```

## ⚠️ The Challenge

We cannot automatically interact with Telegram bots from a web application because:
1. Telegram bots require user interaction (clicking START button)
2. No public API to automate Telegram bot conversations
3. Bot responses are user-specific and session-based

## ✅ SOLUTION: Hybrid Approach

Since we can't automate the Telegram bot interaction, we'll:
1. **Detect** when the flow redirects to Telegram
2. **Extract** the bot username and verification code
3. **Guide** the user with step-by-step instructions
4. **(Optional)** Deep link to open Telegram automatically

---

## 🛠️ Implementation

### Step 1: Update Edge Function to Detect Telegram

Modify `supabase/functions/extract-key/index.ts`:

```typescript
// Add this interface at the top
interface TelegramRedirectResult {
  success: boolean;
  requiresTelegram: true;
  botUsername: string;
  verificationCode?: string;
  telegramDeepLink: string;
  instructions: string[];
  timestamp: string;
}

// Add telegram detection function
async function detectTelegramRedirect(finalUrl: string): Promise<TelegramRedirectResult | null> {
  // Check if URL is a Telegram bot link
  const telegramMatch = finalUrl.match(/t\.me\/([a-zA-Z0-9_]+)(\?start=([a-zA-Z0-9_-]+))?/);
  
  if (telegramMatch) {
    const botUsername = telegramMatch[1];
    const verificationCode = telegramMatch[3];
    
    return {
      success: false,
      requiresTelegram: true,
      botUsername: botUsername,
      verificationCode: verificationCode,
      telegramDeepLink: finalUrl,
      instructions: [
        "1. Click the Telegram link below or copy it",
        "2. Open Telegram app (it will redirect automatically)",
        "3. Click START button in the chat with @" + botUsername,
        verificationCode ? "4. The bot will send your key (verification: " + verificationCode + ")" : "4. The bot will send your key",
        "5. Copy the key from Telegram and paste it back here"
      ],
      timestamp: new Date().toISOString()
    };
  }
  
  return null;
}
```

### Step 2: Update Domain Handlers

For each handler (nanolinks, arolinks, lksfy), check if the final URL is a Telegram link:

```typescript
async function handleNanoLinks(keyUrl: string): Promise<string | TelegramRedirectResult> {
  const id = keyUrl.split('/').pop()!;
  
  // ... existing code ...
  
  const redirect2 = response2.headers.get('location');
  if (!redirect2) throw new Error('No final redirect');
  
  // CHECK FOR TELEGRAM
  const telegramResult = await detectTelegramRedirect(redirect2);
  if (telegramResult) return telegramResult;
  
  // If not Telegram, extract key normally
  const keyMatch = redirect2.match(/key=([^&]+)/);
  if (!keyMatch) throw new Error('Key not found');
  
  return keyMatch[1];
}
```

### Step 3: Update Main Handler

Modify the main serve function to handle Telegram redirects:

```typescript
serve(async (req) => {
  // ... CORS headers ...
  
  try {
    const { url } = await req.json();
    
    // ... get baseUrl and keyUrl ...
    
    let result: string | TelegramRedirectResult;
    
    if (keyUrl.includes('nanolinks')) {
      result = await handleNanoLinks(keyUrl);
    } else if (keyUrl.includes('arolinks')) {
      result = await handleAroLinks(keyUrl);
    } else if (keyUrl.includes('lksfy')) {
      result = await handleLksfy(keyUrl);
    }
    
    // Check if result is Telegram redirect
    if (typeof result === 'object' && result.requiresTelegram) {
      return new Response(
        JSON.stringify(result),
        { 
          headers: { 
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          } 
        }
      );
    }
    
    // Normal key result
    return new Response(
      JSON.stringify({
        success: true,
        key: result,
        timestamp: new Date().toISOString()
      }),
      { headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' } }
    );
    
  } catch (error) {
    // ... error handling ...
  }
});
```

---

## 📱 Frontend Integration

Update your existing frontend to handle Telegram redirects:

```typescript
// Example: React component
interface ExtractionResponse {
  success: boolean;
  key?: string;
  requiresTelegram?: boolean;
  botUsername?: string;
  verificationCode?: string;
  telegramDeepLink?: string;
  instructions?: string[];
  error?: string;
}

async function extractKey(url: string): Promise<ExtractionResponse> {
  const response = await fetch('YOUR_SUPABASE_FUNCTION_URL/extract-key', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer YOUR_ANON_KEY'
    },
    body: JSON.stringify({ url })
  });
  
  return await response.json();
}

// In your component
const handleExtract = async () => {
  const result = await extractKey(userUrl);
  
  if (result.requiresTelegram) {
    // Show Telegram instructions
    setShowTelegramInstructions(true);
    setTelegramData(result);
  } else if (result.success) {
    // Show the key
    setExtractedKey(result.key);
  } else {
    // Show error
    setError(result.error);
  }
};
```

### UI Component for Telegram Instructions

```jsx
{showTelegramInstructions && (
  <div className="telegram-instructions">
    <h3>🤖 Telegram Verification Required</h3>
    <p>This key requires Telegram bot verification.</p>
    
    <div className="instructions-list">
      {telegramData.instructions.map((instruction, index) => (
        <div key={index} className="instruction-step">
          {instruction}
        </div>
      ))}
    </div>
    
    <div className="actions">
      <a 
        href={telegramData.telegramDeepLink} 
        target="_blank"
        className="btn-telegram"
      >
        📱 Open in Telegram
      </a>
      
      <button 
        onClick={() => {
          navigator.clipboard.writeText(telegramData.telegramDeepLink);
          alert('Telegram link copied!');
        }}
        className="btn-copy"
      >
        📋 Copy Link
      </button>
    </div>
    
    <div className="manual-key-input">
      <p>After getting the key from Telegram:</p>
      <input 
        type="text" 
        placeholder="Paste your key here"
        value={manualKey}
        onChange={(e) => setManualKey(e.target.value)}
      />
      <button onClick={submitManualKey}>✅ Submit Key</button>
    </div>
  </div>
)}
```

---

## 🚀 Deployment Steps

### 1. Deploy Updated Edge Function

```bash
cd supabase/functions/extract-key
supabase functions deploy extract-key
```

### 2. Update Frontend

Update your existing frontend code to handle the new Telegram redirect response.

### 3. Test the Flow

1. Enter a URL that triggers Telegram redirect
2. Verify that instructions appear
3. Click "Open in Telegram"
4. Click START in the bot
5. Copy key from bot
6. Paste back in your app

---

## 💡 Alternative Solutions

### Option A: User Waits for Bot Response (Current Approach)
- Pros: Simple, works for all users
- Cons: Requires manual steps

### Option B: Telegram Bot API (Advanced)
If you control the bot:
1. Set up Telegram Bot API webhook
2. Store user session in Supabase
3. Bot sends key back to your webhook
4. Frontend polls for key

```typescript
// In Edge Function
async function createTelegramSession(userId: string, verificationCode: string) {
  await supabase
    .from('telegram_sessions')
    .insert({
      user_id: userId,
      verification_code: verificationCode,
      status: 'pending',
      created_at: new Date()
    });
}

// Frontend polls for completion
const pollForKey = async (sessionId: string) => {
  const interval = setInterval(async () => {
    const { data } = await supabase
      .from('telegram_sessions')
      .select('key, status')
      .eq('id', sessionId)
      .single();
    
    if (data.status === 'completed') {
      clearInterval(interval);
      setExtractedKey(data.key);
    }
  }, 2000); // Poll every 2 seconds
};
```

### Option C: Browser Extension
Create a browser extension that:
1. Intercepts Telegram web redirects
2. Automatically opens Telegram
3. Captures bot response
4. Sends key back to your app

---

## 📊 Summary

**What We Built:**
1. ✅ Python logic converted to TypeScript Edge Function
2. ✅ Domain-based routing (nanolinks, arolinks, lksfy)
3. ✅ Telegram bot redirect detection
4. ✅ User-friendly instructions
5. ✅ Deep linking to Telegram

**User Experience:**
1. User pastes URL
2. App detects Telegram requirement
3. Shows clear instructions
4. Opens Telegram with one click
5. User gets key from bot
6. User pastes key back (or app polls if you implement webhook)

**Files Created:**
- `README.md` - Project documentation
- `supabase/functions/extract-key/index.ts` - Main extraction logic
- `TELEGRAM_BOT_SOLUTION.md` - This guide

---

## 🎯 Next Steps

1. Update the Edge Function with Telegram detection code
2. Update your frontend to handle `requiresTelegram` response
3. Add UI for Telegram instructions
4. Deploy and test
5. (Optional) Implement webhook approach if you control the bot

---

**Need Help?** Open an issue or contact the maintainer.

**Made with ❤️ by desichillbeats**
