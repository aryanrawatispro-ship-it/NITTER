# How to Get Twitter Cookies (Easiest Method!)

## Why Use Cookies?

✅ **More Secure** - No password in .env file
✅ **No 2FA Issues** - Bypasses two-factor authentication
✅ **Faster** - No login delay
✅ **More Reliable** - Less likely to be flagged

---

## Method 1: Chrome/Edge (Easiest)

### Step 1: Install Cookie Extension

1. Go to Chrome Web Store
2. Search for "**Get cookies.txt LOCALLY**" (by Ninh Pham)
3. Click "Add to Chrome"
4. Or use this link: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

### Step 2: Login to Twitter

1. Go to https://twitter.com
2. Login with your account
3. Make sure you're logged in (see your timeline)

### Step 3: Export Cookies

1. Click the extension icon (puzzle piece in top right)
2. Click "Get cookies.txt LOCALLY"
3. It will download `twitter.com_cookies.txt`

### Step 4: Convert to JSON

Save this Python script as `convert_cookies.py`:

```python
#!/usr/bin/env python3
import json

# Read cookies.txt file
with open('twitter.com_cookies.txt', 'r') as f:
    lines = f.readlines()

cookies = []
for line in lines:
    line = line.strip()

    # Skip comments and empty lines
    if not line or line.startswith('#'):
        continue

    # Parse cookie line
    parts = line.split('\t')
    if len(parts) >= 7:
        cookie = {
            'name': parts[5],
            'value': parts[6],
            'domain': parts[0],
            'path': parts[2],
            'secure': parts[3] == 'TRUE',
            'httpOnly': parts[1] == 'TRUE',
            'sameSite': 'None'
        }
        cookies.append(cookie)

# Save as JSON
with open('twitter_cookies.json', 'w') as f:
    json.dump(cookies, f, indent=2)

print(f"✅ Converted {len(cookies)} cookies to twitter_cookies.json")
```

Run it:
```bash
python3 convert_cookies.py
```

### Step 5: Use the Cookies

```bash
# Copy to your project
cp twitter_cookies.json ~/NITTER/

# Edit .env
cd ~/NITTER
nano .env

# Add this line:
TWITTER_COOKIES_FILE=twitter_cookies.json
```

---

## Method 2: Firefox (Alternative)

### Step 1: Install Extension

1. Go to Firefox Add-ons
2. Search for "**Cookie Quick Manager**"
3. Install it

### Step 2: Login and Export

1. Login to Twitter
2. Open Cookie Quick Manager (Ctrl+Shift+K)
3. Find cookies for `twitter.com`
4. Click "Export" → "JSON"
5. Save as `twitter_cookies.json`

---

## Method 3: Chrome DevTools (Manual)

### Step 1: Login to Twitter

1. Go to https://twitter.com
2. Login to your account

### Step 2: Open DevTools

1. Press F12 (or Right-click → Inspect)
2. Go to "Application" tab (or "Storage" in Firefox)
3. Expand "Cookies" in left sidebar
4. Click on "https://twitter.com"

### Step 3: Copy Cookies

Run this in the Console tab (Ctrl+Shift+J):

```javascript
// Get all Twitter cookies
const cookies = document.cookie.split(';').map(c => {
    const [name, value] = c.trim().split('=');
    return {
        name: name,
        value: value,
        domain: '.twitter.com',
        path: '/',
        secure: true,
        httpOnly: false,
        sameSite: 'None'
    };
});

// Copy to clipboard
copy(JSON.stringify(cookies, null, 2));
console.log('✅ Cookies copied to clipboard!');
```

### Step 4: Save to File

1. Cookies are now in your clipboard
2. Create file: `nano ~/NITTER/twitter_cookies.json`
3. Paste (Ctrl+V)
4. Save (Ctrl+X, Y, Enter)

---

## Method 4: Use Provided Script (Automated)

I'll create an automated script for you:

```bash
cd ~/NITTER
nano get_twitter_cookies.py
```

Paste this:

```python
#!/usr/bin/env python3
"""
Interactive script to help extract Twitter cookies.
"""

import json

print("="*50)
print("  Twitter Cookie Extractor")
print("="*50)
print()
print("Steps:")
print("1. Open Chrome/Firefox")
print("2. Login to Twitter.com")
print("3. Press F12 → Console tab")
print("4. Copy and run this JavaScript:")
print()
print("-"*50)
print("""
// Copy this into browser console:
copy(JSON.stringify(
    document.cookie.split(';').map(c => {
        const [name, value] = c.trim().split('=');
        return {
            name: name,
            value: value,
            domain: '.twitter.com',
            path: '/',
            secure: true,
            httpOnly: false,
            sameSite: 'None'
        };
    }), null, 2
));
console.log('✅ Cookies copied!');
""")
print("-"*50)
print()
print("5. Paste the JSON here and press Enter")
print("6. Then press Ctrl+D (EOF) when done")
print()

# Read JSON from stdin
import sys
json_data = sys.stdin.read()

try:
    cookies = json.loads(json_data)

    # Save to file
    with open('twitter_cookies.json', 'w') as f:
        json.dump(cookies, f, indent=2)

    print()
    print(f"✅ SUCCESS! Saved {len(cookies)} cookies to twitter_cookies.json")
    print()
    print("Now add this to your .env file:")
    print("TWITTER_COOKIES_FILE=twitter_cookies.json")
    print()

except json.JSONDecodeError as e:
    print(f"❌ ERROR: Invalid JSON: {e}")
    print("Please make sure you copied the correct output from the console.")
```

Run it:
```bash
chmod +x get_twitter_cookies.py
python3 get_twitter_cookies.py
```

---

## Important Notes

### Cookie Lifespan
- Twitter cookies typically last **30 days**
- When they expire, just re-export new cookies
- No need to login with password again

### Security
- **NEVER commit cookies to Git!**
- Cookies = same as password
- Add to .gitignore: `twitter_cookies.json`

### Which Cookies Are Important?
Essential Twitter cookies:
- `auth_token` - Main authentication
- `ct0` - CSRF token
- `guest_id` - Guest ID
- `twid` - User ID

You need ALL cookies, not just these.

---

## Testing Your Cookies

```bash
cd ~/NITTER

# Test if cookies work
docker compose exec api python3 << 'PYTHON'
import asyncio
import json
from src.scrapers.twitter_direct_scraper import TwitterDirectScraper
from src.nitter_manager import NitterInstanceManager

async def test():
    # Load cookies
    with open('twitter_cookies.json', 'r') as f:
        cookies = json.load(f)

    manager = NitterInstanceManager()
    async with TwitterDirectScraper(manager, cookies=cookies) as scraper:
        success = await scraper.login()
        if success:
            print("✅ Cookies work!")

            # Try scraping a profile
            profile = await scraper.scrape_profile("twitter")
            if profile:
                print(f"✅ Successfully scraped @{profile['username']}")
                print(f"   Followers: {profile['followers_count']}")
            else:
                print("❌ Cookie auth worked but scraping failed")
        else:
            print("❌ Cookie auth failed")

asyncio.run(test())
PYTHON
```

---

## Troubleshooting

### "Cookies expired"
- Re-export cookies from browser
- Twitter cookies last ~30 days

### "Authentication failed"
- Make sure you're logged in when exporting
- Export ALL cookies, not just some
- Check domain is `.twitter.com` or `twitter.com`

### "Invalid JSON"
- Validate JSON at https://jsonlint.com
- Make sure it's a JSON array: `[{...}, {...}]`
- No extra characters before/after

### "File not found"
```bash
# Check if file exists
ls -la ~/NITTER/twitter_cookies.json

# Check path in .env
cat ~/NITTER/.env | grep COOKIES

# Should be:
# TWITTER_COOKIES_FILE=twitter_cookies.json
```

---

## Cookie Format Example

Your `twitter_cookies.json` should look like this:

```json
[
  {
    "name": "auth_token",
    "value": "abc123...",
    "domain": ".twitter.com",
    "path": "/",
    "secure": true,
    "httpOnly": true,
    "sameSite": "None"
  },
  {
    "name": "ct0",
    "value": "xyz789...",
    "domain": ".twitter.com",
    "path": "/",
    "secure": true,
    "httpOnly": false,
    "sameSite": "Lax"
  }
]
```

Required fields for each cookie:
- `name` - Cookie name
- `value` - Cookie value
- `domain` - Should be `.twitter.com` or `twitter.com`

Optional but recommended:
- `path` - Usually `/`
- `secure` - Usually `true`
- `httpOnly` - Varies
- `sameSite` - Usually `None` or `Lax`

---

## Quick Summary

**Easiest Method:**
1. Install "Get cookies.txt LOCALLY" extension
2. Login to Twitter
3. Export cookies
4. Convert to JSON with script
5. Add to `.env`: `TWITTER_COOKIES_FILE=twitter_cookies.json`
6. Rebuild containers
7. Done!

**Total Time:** 5 minutes
**Security:** High (no password stored)
**Maintenance:** Re-export every 30 days

---

## After Getting Cookies

```bash
# 1. Place cookies file
cp twitter_cookies.json ~/NITTER/

# 2. Edit .env
echo "TWITTER_COOKIES_FILE=twitter_cookies.json" >> ~/NITTER/.env

# 3. Rebuild
cd ~/NITTER
docker compose down
docker compose build --no-cache
docker compose up -d

# 4. Test
sleep 20
curl -X POST http://localhost:8000/api/users/elonmusk/scrape
sleep 30
curl http://localhost:8000/api/jobs/recent?limit=1

# Should see: "items_scraped": 100
```

---

## Benefits Over Username/Password

| Method | Security | 2FA Support | Speed | Reliability |
|--------|----------|-------------|-------|-------------|
| **Cookies** | ✅ High | ✅ Yes | ✅ Fast | ✅ Best |
| Password | ⚠️ Medium | ❌ No | 🐌 Slow | ⚠️ OK |

**Use cookies!** It's the best method. 🚀
