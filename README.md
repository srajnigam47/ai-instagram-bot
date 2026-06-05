# 🤖 AI Instagram Bot — Full Automation (100% Free)

Posts AI-generated photos + captions to Instagram automatically, 3x per day.
No server needed. No laptop needed. Runs free on GitHub Actions.

---

## 📦 What's Inside

```
src/
  bot.py              ← Main orchestrator
  image_generator.py  ← Hugging Face AI image generation
  caption_generator.py← Groq LLM caption writing
  instagram_poster.py ← Instagram Graph API posting
.github/workflows/
  post.yml            ← GitHub Actions scheduler (3x/day)
```

---

## 🔑 Step 1: Get Your Free API Keys

### 1. Hugging Face (Image Generation) — FREE
1. Go to https://huggingface.co/ → Sign up
2. Go to Settings → Access Tokens → New Token
3. Copy the token → this is your `HF_API_KEY`

### 2. Groq (Caption AI) — FREE
1. Go to https://console.groq.com/ → Sign up
2. Click "API Keys" → Create API Key
3. Copy → this is your `GROQ_API_KEY`

### 3. ImgBB (Free Image Hosting) — FREE
Instagram needs a public image URL. ImgBB hosts images for free.
1. Go to https://api.imgbb.com/ → Sign up
2. Get your API key → this is your `IMGBB_API_KEY`

### 4. Instagram Graph API — FREE
This is the only slightly complex step:

**a) Make your Instagram account Professional:**
   - Instagram app → Settings → Account → Switch to Professional Account → Creator

**b) Create a Facebook Developer App:**
   1. Go to https://developers.facebook.com/
   2. My Apps → Create App → "Other" → "Business"
   3. Add Product: "Instagram Graph API"

**c) Get your Access Token:**
   1. In your app → Instagram Graph API → Generate Token
   2. Connect your Instagram account
   3. Copy the token → `INSTAGRAM_ACCESS_TOKEN`

**d) Get your Account ID:**
   Run this in your browser (replace YOUR_TOKEN):
   ```
   https://graph.facebook.com/v19.0/me/accounts?access_token=YOUR_TOKEN
   ```
   The `id` in the response → `INSTAGRAM_ACCOUNT_ID`

> ⚠️ Default tokens expire in 60 days. To get a long-lived token, see:
> https://developers.facebook.com/docs/instagram-basic-display-api/guides/long-lived-access-tokens

---

## 🚀 Step 2: Set Up GitHub Repository

1. Go to https://github.com → New Repository → Name it `ai-instagram-bot`
2. Upload all these files to the repo
3. Go to Settings → Secrets and variables → Actions → New repository secret

Add these secrets:
```
INSTAGRAM_ACCESS_TOKEN  → your Instagram token
INSTAGRAM_ACCOUNT_ID    → your Instagram account ID  
GROQ_API_KEY            → your Groq key
HF_API_KEY              → your Hugging Face key
IMGBB_API_KEY           → your ImgBB key
```

---

## ⏰ Step 3: Set Your Posting Times

Open `.github/workflows/post.yml` and edit the cron schedule.
Times are in UTC. IST = UTC + 5:30.

```yaml
- cron: '30 2 * * *'   # Change to your preferred times
```

Cron format: `minute hour day month weekday`

Use https://crontab.guru/ to build your schedule easily.

---

## ▶️ Step 4: Test It

1. Go to your GitHub repo → Actions tab
2. Click "AI Instagram Bot" → "Run workflow" → Run
3. Watch the logs — it should generate and post!

---

## 🎨 Step 5: Customize Your AI Girl

Edit `src/bot.py` → `THEMES` list to change:
- Styles (fashion, fitness, glamour, etc.)
- Settings (locations, environments)
- Vibes (personality, mood)

Edit `src/image_generator.py` → `build_prompt()` to change:
- Hair color, eye color, look of your AI character
- Photography style
- Clothing style

---

## 📊 Posting Schedule (Default)

| Time (IST) | Post |
|------------|------|
| 8:00 AM    | Morning lifestyle shot |
| 1:00 PM    | Fashion/aesthetic photo |
| 7:00 PM    | Evening glamour shot |

Change anytime in `post.yml`.

---

## 🔄 Keeping Token Fresh

Instagram tokens expire. Set a reminder every 50 days to refresh:
1. Go to Facebook Developer console
2. Regenerate token
3. Update GitHub Secret `INSTAGRAM_ACCESS_TOKEN`

Or use the long-lived token approach (valid 60 days, auto-refreshable).

---

## ❓ Troubleshooting

| Error | Fix |
|-------|-----|
| `HF model 503` | Model loading, retry in 20s — code handles this |
| `Instagram 400` | Check token is valid and account is Professional |
| `ImgBB upload failed` | Check ImgBB API key |
| `Groq 401` | Check Groq API key in secrets |
| GitHub Action not running | Check Actions is enabled in repo settings |

---

## 💡 Pro Tips

- **Reels**: Add video generation with Kling AI (free tier) for 10x reach
- **Stories**: Duplicate the workflow, post same image as Story
- **Consistency**: Don't change the character description mid-way — same face = brand
- **Disclosure**: Add "AI" to your bio — protects account, adds mystique

---

Built with: Hugging Face + Groq + ImgBB + Instagram Graph API + GitHub Actions
Cost: $0/month 🎉
