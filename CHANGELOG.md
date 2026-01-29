# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **X (Twitter) Integration**: Monitor tweets from 20+ AI thought leaders and companies
  - Sam Altman, Andrej Karpathy, Yann LeCun, Demis Hassabis, and more
  - OpenAI, Anthropic, Google AI, Meta AI official accounts
  - Uses Nitter instances (no API key required)
  - Automatic AI keyword filtering
  - Priority scoring based on account importance
  - See `docs/X_YOUTUBE_SETUP.md` for details

- **YouTube Integration**: Track videos from 12+ AI-focused channels
  - Two Minute Papers, Yannic Kilcher, AI Explained, and more
  - OpenAI and Google DeepMind official channels
  - Lex Fridman AI interviews, Stanford lectures
  - Uses YouTube Data API v3 (API key required)
  - Automatic AI keyword filtering
  - Priority scoring based on channel quality
  - See `docs/X_YOUTUBE_SETUP.md` for setup guide

- **Priority System**: Articles now have a priority field (0-10)
  - Official company sources: Priority 9-10
  - Top researchers and educators: Priority 8-9
  - Community sources: Priority 5-7
  - Affects sorting and filtering in final report

- **Configuration Options**:
  - `ENABLE_X=true/false` - Toggle X (Twitter) fetching
  - `ENABLE_YOUTUBE=true/false` - Toggle YouTube fetching
  - `YOUTUBE_API_KEY` - YouTube Data API v3 key

- **Documentation**:
  - `docs/X_YOUTUBE_SETUP.md` - Comprehensive setup guide
  - Troubleshooting tips for common issues
  - Quota management for YouTube API
  - Instructions for adding more accounts/channels

- **Testing**:
  - `test_new_sources.py` - Quick test script for new fetchers
  - `tests/test_new_fetchers.py` - Unit tests for X and YouTube fetchers
  - Syntax validation for all new code

### Changed
- **Article Model**: Added `priority` field with default value 5
- **README**: Updated feature list to include X and YouTube
- **Config**: Extended settings to support new data sources
- **Workflow**: Integrated X and YouTube fetchers into fetch node

### Technical Details
- X Fetcher uses multiple Nitter instances with automatic fallback
- YouTube Fetcher efficiently manages API quota (3-5 units per video)
- Both fetchers support concurrent execution with retry logic
- AI-related content filtering with 25+ keywords
- Respects existing time windows and filtering pipeline

### Migration Notes
- No breaking changes - new features are opt-in
- Existing `.env` files will work without modification
- To enable new sources, add to `.env`:
  ```bash
  ENABLE_X=true
  ENABLE_YOUTUBE=true
  YOUTUBE_API_KEY=your_key_here  # Only needed for YouTube
  ```

## [Previous Versions]

See git history for previous changes.
