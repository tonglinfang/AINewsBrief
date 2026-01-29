# X (Twitter) and YouTube Setup Guide

This guide explains how to configure and use the X (Twitter) and YouTube data sources in AINewsBrief.

---

## 🐦 X (Twitter) Integration

### Overview

The X fetcher monitors tweets from leading AI researchers, company leaders, and organizations to capture real-time discussions, announcements, and insights from the AI community.

### Tracked Accounts

#### AI Company Leaders
- **Sam Altman** (@sama) - OpenAI CEO
- **Greg Brockman** (@gdb) - OpenAI President
- **Andrej Karpathy** (@karpathy) - AI Researcher
- **Yann LeCun** (@ylecun) - Meta AI Chief Scientist
- **Demis Hassabis** (@demishassabis) - Google DeepMind CEO
- **Jeff Dean** (@JeffDean) - Google Senior Fellow
- **Jim Fan** (@DrJimFan) - NVIDIA Senior Research Scientist
- **Andrew Ng** (@AndrewYNg) - AI Pioneer

#### AI Companies
- **OpenAI** (@OpenAI)
- **Anthropic** (@AnthropicAI)
- **Google AI** (@GoogleAI)
- **Google DeepMind** (@GoogleDeepMind)
- **Meta AI** (@MetaAI)
- **Mistral AI** (@MistralAI)
- **Stability AI** (@StabilityAI)
- **Hugging Face** (@HuggingFace)

#### AI Researchers & Influencers
- **Ethan Mollick** (@emollick) - AI adoption researcher
- **François Chollet** (@fchollet) - Keras creator
- **Ian Goodfellow** (@goodfellow_ian) - GAN inventor
- **Sebastian Raschka** (@rasbt) - ML researcher

### How It Works

1. **Nitter Instances**: Uses Nitter (privacy-friendly Twitter frontend) to fetch RSS feeds without requiring Twitter API keys
2. **Multi-Instance Fallback**: Tries multiple Nitter instances if one is down
3. **AI Filtering**: Only includes tweets mentioning AI-related keywords (GPT, LLM, Claude, machine learning, etc.)
4. **Engagement Quality**: Focuses on recent posts (24-hour window)
5. **Priority Scoring**: Company accounts and top researchers get higher priority (8-10)

### Configuration

#### Enable/Disable X Fetching

In your `.env` file:

```bash
# Enable X (Twitter) fetching
ENABLE_X=true

# Disable if you don't want X content
# ENABLE_X=false
```

#### Adjust Time Window

```bash
# Default: 24 hours
ARTICLE_AGE_HOURS=24

# For more frequent updates, reduce to 6 hours
# ARTICLE_AGE_HOURS=6
```

### No API Key Required

The X fetcher uses Nitter, which doesn't require Twitter API credentials. This makes it:
- ✅ Free to use
- ✅ No rate limits
- ✅ Privacy-friendly
- ⚠️ Dependent on Nitter instance availability

### Limitations

- **Nitter Availability**: Nitter instances may occasionally be down or rate-limited
- **No Media**: Only captures tweet text, not images or videos
- **Rate Limiting**: Some Nitter instances may temporarily block high-frequency requests
- **Latency**: Slight delay compared to direct Twitter API access

### Adding More Accounts

Edit `src/tools/x_fetcher.py` to add accounts:

```python
ACCOUNTS = {
    "your_username": {"name": "Display Name", "priority": 8},
    # Add more accounts here
}
```

---

## 🎥 YouTube Integration

### Overview

The YouTube fetcher monitors AI-focused video channels to capture tutorials, research paper explanations, AI news, and company announcements.

### Tracked Channels

#### Technical Deep Dives
- **Two Minute Papers** - AI research paper reviews (Priority: 9)
- **Yannic Kilcher** - ML research paper explanations (Priority: 8)
- **3Blue1Brown** - Math/AI visual explanations (Priority: 8)

#### AI News & Analysis
- **AI Explained** - AI news and paper analysis (Priority: 8)
- **The AI Epiphany** - AI tutorials and news (Priority: 7)
- **Sentdex** - Python AI tutorials (Priority: 7)

#### AI Companies
- **OpenAI** - Official OpenAI channel (Priority: 10)
- **Google DeepMind** - Official DeepMind channel (Priority: 9)

#### AI Tools & Applications
- **Matt Wolfe** - AI tools and news (Priority: 7)
- **AI Advantage** - AI productivity tools (Priority: 6)

#### Academic/Educational
- **Lex Fridman** - AI researcher interviews (Priority: 8)
- **Stanford Online** - Stanford AI lectures (Priority: 8)

### How It Works

1. **YouTube Data API v3**: Official Google API for accessing video metadata
2. **Channel Monitoring**: Checks upload playlists for new videos
3. **AI Filtering**: Only includes videos with AI-related keywords in title/description
4. **Metadata Extraction**: Captures title, description, publish date, view count
5. **Priority Scoring**: Company channels and top educators get higher priority

### Configuration

#### Step 1: Get YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable **YouTube Data API v3**:
   - Navigate to "APIs & Services" → "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API key"
   - Copy the API key

#### Step 2: Add API Key to .env

```bash
# YouTube API Configuration
YOUTUBE_API_KEY=YOUR_API_KEY_HERE
```

#### Step 3: Enable YouTube Fetching

```bash
# Enable YouTube fetching
ENABLE_YOUTUBE=true

# Disable if you don't want YouTube content
# ENABLE_YOUTUBE=false
```

#### Step 4: Adjust Time Window

```bash
# YouTube uses 48-hour window by default (videos are less frequent)
ARTICLE_AGE_HOURS=24  # This affects other sources

# YouTube internally uses ARTICLE_AGE_HOURS * 2
```

### API Quota Management

YouTube Data API v3 has a daily quota limit:
- **Free Tier**: 10,000 quota units/day
- **Each video fetch**: ~3-5 units
- **Expected usage**: ~50-150 units per run (for 12 channels)
- **Recommended frequency**: Every 6-12 hours (2-4 runs/day)

#### Quota-Efficient Configuration

```bash
# Run less frequently to conserve quota
# Use GitHub Actions schedule: cron: '0 */12 * * *'  # Every 12 hours

# Reduce articles per channel (in src/tools/youtube_fetcher.py)
# self.max_per_channel = 2  # Instead of 3
```

#### Monitor Quota Usage

Check your quota at: [Google Cloud Console → APIs & Services → Dashboard](https://console.cloud.google.com/apis/dashboard)

### Limitations

- **API Quota**: Limited to 10,000 units/day (free tier)
- **No Transcripts**: Only uses title and description (not video content)
- **Rate Limits**: Google may throttle excessive requests
- **API Key Required**: Must set up Google Cloud project

### Adding More Channels

Edit `src/tools/youtube_fetcher.py` to add channels:

```python
CHANNELS = {
    "UC_channel_id": {
        "name": "Channel Name",
        "priority": 8,
        "description": "Brief description"
    },
    # Add more channels here
}
```

**How to find Channel ID:**
1. Go to channel page
2. View page source (Ctrl+U)
3. Search for "channelId"
4. Copy the ID (starts with "UC")

Or use: `https://www.youtube.com/@username` → Click "About" → "Share Channel" → Copy channel ID from URL

---

## 🎯 Best Practices

### Recommended Configuration

```bash
# .env recommended settings for X + YouTube

# Enable both sources
ENABLE_X=true
ENABLE_YOUTUBE=true

# Balance frequency vs. API quota
ARTICLE_AGE_HOURS=24          # 24-hour window for most sources
MAX_ARTICLES_PER_SOURCE=20    # Limit per source
MAX_TOTAL_ARTICLES=50         # Total limit across all sources

# Priority filtering
MIN_IMPORTANCE_SCORE=5        # Only include scored 5+ by LLM
```

### GitHub Actions Scheduling

For optimal balance:

```yaml
# .github/workflows/daily-brief.yml
on:
  schedule:
    # Run every 6 hours (4 times/day)
    - cron: '0 */6 * * *'

    # Or run twice daily
    # - cron: '0 8,20 * * *'  # 8am and 8pm
```

### Content Quality Tips

1. **Increase MIN_IMPORTANCE_SCORE** to reduce noise:
   ```bash
   MIN_IMPORTANCE_SCORE=6  # Stricter filtering
   ```

2. **Prioritize official sources**:
   - X posts from company accounts get priority 10
   - YouTube videos from company channels get priority 10

3. **Disable low-value sources** if feed is too crowded:
   ```bash
   ENABLE_RSS=false  # Disable general tech news RSS
   ```

---

## 🔧 Troubleshooting

### X (Twitter) Issues

**Problem**: No tweets fetched
- **Cause**: All Nitter instances are down
- **Solution**:
  1. Wait and retry (instances rotate availability)
  2. Add more Nitter instances in `src/tools/x_fetcher.py`
  3. Check Nitter status: https://github.com/zedeus/nitter/wiki/Instances

**Problem**: Only getting old tweets
- **Cause**: Nitter caching delay
- **Solution**: This is normal; Nitter may cache RSS feeds for 15-30 minutes

### YouTube Issues

**Problem**: No videos fetched
- **Cause**: Missing or invalid API key
- **Solution**:
  1. Verify `YOUTUBE_API_KEY` is set in `.env`
  2. Check API is enabled in Google Cloud Console
  3. Verify API key restrictions (if any)

**Problem**: "Quota exceeded" error
- **Cause**: Daily API quota limit reached
- **Solution**:
  1. Wait until quota resets (midnight Pacific Time)
  2. Reduce fetch frequency
  3. Request quota increase in Google Cloud Console

**Problem**: Videos not AI-related
- **Cause**: Channel posts non-AI content occasionally
- **Solution**:
  1. AI filtering removes most non-relevant videos
  2. LLM analyzer will score them low (they'll be filtered out)
  3. Remove channel if consistently off-topic

---

## 📊 Output Format

### X Posts in Report

```markdown
### 🔥 Breaking News

#### X - Sam Altman: Excited to announce GPT-5...
⭐⭐⭐⭐⭐ (10分)

**摘要**: OpenAI宣布GPT-5发布，性能大幅提升...

**关键洞察**: 标志着大型语言模型新时代的开始

**来源**: X (Twitter) | 发布时间: 2026-01-29 10:30 UTC

[查看推文](https://twitter.com/sama/status/123456789)
```

### YouTube Videos in Report

```markdown
### 🔬 Research

#### 🎥 Two Minute Papers: This AI Can Understand Videos Like Never Before!
⭐⭐⭐⭐ (8分)

**摘要**: 最新视频理解模型突破，能够理解复杂场景...

**关键洞察**: 视频理解能力达到新高度，接近人类水平

**来源**: YouTube - Two Minute Papers | 发布时间: 2026-01-28 14:00 UTC

[观看视频](https://www.youtube.com/watch?v=abc123)
```

---

## 🚀 Quick Start

1. **Clone and install**:
   ```bash
   git clone <repo>
   cd AINewsBrief
   pip install -r requirements.txt
   ```

2. **Configure .env**:
   ```bash
   cp .env.example .env
   # Edit .env and add:
   # - YOUTUBE_API_KEY (required for YouTube)
   # - ENABLE_X=true
   # - ENABLE_YOUTUBE=true
   ```

3. **Test locally**:
   ```bash
   python -m src.agent
   ```

4. **Check output**:
   ```bash
   cat reports/YYYY-MM-DD_HH-MM-SS.md
   ```

---

## 📚 Additional Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [Nitter Project](https://github.com/zedeus/nitter)
- [Nitter Public Instances](https://github.com/zedeus/nitter/wiki/Instances)
- [Google Cloud Console](https://console.cloud.google.com/)

---

## 🤝 Contributing

To add more accounts or channels:

1. Edit `src/tools/x_fetcher.py` or `src/tools/youtube_fetcher.py`
2. Add account/channel with appropriate priority
3. Test locally
4. Submit PR with description of why this source is valuable

---

## 📝 License

Same as parent project (AINewsBrief)
