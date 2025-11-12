# 🔑 Sigma Study Key Generator

> Secure key extraction solution using React, TypeScript, Tailwind CSS, and Supabase

## 📋 Overview

This is a modern web application that extracts keys from various short link services with domain-based routing. It replaces the original Python script with a secure, scalable solution using:

- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: Supabase Edge Functions
- **Deployment**: GitHub Actions + Vercel/Netlify
- **Database**: Supabase PostgreSQL

## ✨ Features

- 🎯 **Domain-Based Routing**: Automatically detects and routes to appropriate handlers
  - `nanolinks.in` support
  - `arolinks.com` support
  - `lksfy.com` support with AES decryption
- 🔒 **Secure**: All sensitive operations run server-side
- 🚀 **Fast**: Modern React with optimized performance
- 📱 **Responsive**: Beautiful UI that works on all devices
- 🎨 **Beautiful**: Clean design with Tailwind CSS
- 📊 **History**: Track extraction history in Supabase

## 📁 Project Structure

```
sigma-study-key-generator/
├── frontend/                 # React + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API services
│   │   ├── types/          # TypeScript types
│   │   └── App.tsx         # Main app
│   ├── public/
│   ├── package.json
│   └── tailwind.config.js
├── supabase/
│   └── functions/          # Edge Functions
│       └── extract-key/    # Key extraction logic
│           └── index.ts
├── .github/
│   └── workflows/          # CI/CD pipelines
│       └── deploy.yml
├── .env.example            # Environment variables template
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn
- Supabase account ([supabase.com](https://supabase.com))
- GitHub account

### 1. Clone the Repository

```bash
git clone https://github.com/desichillbeats/sigma-study-key-generator.git
cd sigma-study-key-generator
```

### 2. Set Up Supabase

1. Create a new project at [supabase.com](https://supabase.com)
2. Get your project URL and API keys from Settings > API
3. Install Supabase CLI:

```bash
npm install -g supabase
```

4. Login to Supabase:

```bash
supabase login
```

5. Link your project:

```bash
supabase link --project-ref your-project-ref
```

### 3. Deploy Edge Functions

```bash
cd supabase/functions/extract-key
supabase functions deploy extract-key
```

### 4. Set Up Frontend

```bash
cd frontend
npm install
```

Create `.env.local` file:

```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

Start development server:

```bash
npm run dev
```

### 5. Build for Production

```bash
npm run build
```

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file in the `frontend` directory:

```env
# Supabase Configuration
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key

# Optional: Target URL (defaults to zoo0.pages.dev)
VITE_TARGET_URL=https://zoo0.pages.dev
```

### Supabase Edge Function Secrets

Set secrets for your Edge Function:

```bash
supabase secrets set TARGET_URL=https://zoo0.pages.dev
supabase secrets set XOR_KEY=k6kW8r#Tz3f;
```

## 📚 Usage

### Web Interface

1. Open the web application
2. Paste your link (e.g., `https://lksfy.com/dLoCri3RjP`)
3. Click "Extract Key"
4. Wait for the process to complete
5. Copy the extracted key

### API Endpoint

You can also call the API directly:

```bash
curl -X POST \
  https://your-project.supabase.co/functions/v1/extract-key \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://lksfy.com/dLoCri3RjP"}'
```

Response:

```json
{
  "success": true,
  "key": "extracted-key-here",
  "domain": "lksfy",
  "timestamp": "2025-11-12T12:00:00Z"
}
```

## 🏗️ Architecture

### Flow Diagram

```
User Input (URL)
    ↓
React Frontend
    ↓
Supabase Edge Function
    ↓
Domain Detection
    ↓
┌───────────┬────────────┬──────────┐
│  Nanolinks│  Arolinks  │  Lksfy   │
│  Handler  │  Handler   │  Handler │
└───────────┴────────────┴──────────┘
    ↓
HTTP Requests + Decryption
    ↓
Extracted Key
    ↓
Supabase Database (History)
    ↓
Return to Frontend
```

### Security

- ✅ All key extraction runs server-side
- ✅ No sensitive logic exposed to client
- ✅ Rate limiting via Supabase
- ✅ CORS protection
- ✅ Environment variables for secrets
- ✅ No API keys in frontend code

## 🛠️ Development

### Run Frontend Locally

```bash
cd frontend
npm run dev
```

### Run Edge Function Locally

```bash
supabase functions serve extract-key
```

### Run Tests

```bash
npm test
```

### Lint and Format

```bash
npm run lint
npm run format
```

## 🚢 Deployment

### Automated Deployment with GitHub Actions

The repository includes a GitHub Actions workflow that automatically:

1. Builds the frontend
2. Deploys Edge Functions to Supabase
3. Deploys frontend to Vercel/Netlify

### Manual Deployment

#### Deploy to Vercel

```bash
cd frontend
npm install -g vercel
vercel
```

#### Deploy to Netlify

```bash
cd frontend
npm install -g netlify-cli
netlify deploy
```

## 📊 Database Schema

```sql
-- Extraction History Table
CREATE TABLE extraction_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  url TEXT NOT NULL,
  domain TEXT NOT NULL,
  key TEXT,
  success BOOLEAN NOT NULL,
  error TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX idx_extraction_history_created_at 
ON extraction_history(created_at DESC);
```

## 🔍 Supported Domains

| Domain | Status | Handler |
|--------|--------|----------|
| nanolinks.in | ✅ Working | `handle_nano_links` |
| arolinks.com | ✅ Working | `handle_aro_links` |
| lksfy.com | ✅ Working | `handle_lksfy` |

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Original Python script by desichillbeats
- Built with React, TypeScript, and Tailwind CSS
- Backend powered by Supabase

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Contact: [your-email@example.com]

---

**Made with ❤️ by desichillbeats**
