const puppeteer = require('puppeteer-core');
const chromium = require('@sparticuz/chromium');

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    const { url } = req.body;

    if (!url || !url.trim()) {
      return res.status(400).json({
        error: 'Please provide a valid URL'
      });
    }

    // Launch browser with Puppeteer
    const browser = await puppeteer.launch({
      args: chromium.args,
      defaultViewport: chromium.defaultViewport,
      executablePath: await chromium.executablePath(),
      headless: chromium.headless,
    });

    const page = await browser.newPage();

    // Navigate to the Key Extractor site
    await page.goto('https://preview--route-key-finder.lovable.app/', {
      waitUntil: 'networkidle0',
      timeout: 30000
    });

    // Wait for the input field to be visible
    await page.waitForSelector('input[type="text"]', { timeout: 10000 });

    // Enter the URL in the input field
    await page.type('input[type="text"]', url);

    // Click the Extract button
    await page.click('button:has-text("Extract")');

    // Wait for the key to be extracted (wait for success message)
    await page.waitForSelector('text=/Key Extracted Successfully/i', {
      timeout: 60000  // Wait up to 60 seconds for extraction
    });

    // Extract the key from the page
    const extractedKey = await page.evaluate(() => {
      // Look for the key in the success message area
      const keyElement = document.querySelector('[class*="key"], [id*="key"]');
      if (keyElement) {
        return keyElement.textContent.trim();
      }
      // Fallback: look for text matching key pattern
      const bodyText = document.body.innerText;
      const keyMatch = bodyText.match(/verify_[A-Z0-9]+/);
      return keyMatch ? keyMatch[0] : null;
    });

    await browser.close();

    if (!extractedKey) {
      return res.status(500).json({
        error: 'Failed to extract key from the service'
      });
    }

    return res.status(200).json({
      key: extractedKey
    });

  } catch (error) {
    console.error('Error extracting key:', error);
    return res.status(500).json({
      error: 'Failed to extract key: ' + error.message
    });
  }
}
