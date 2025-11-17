#!/usr/bin/env python3
"""
Verify API Keys Configuration
This script checks if all required API keys are properly configured.
"""

import sys
from pathlib import Path
import yaml
from loguru import logger

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_api_keys():
    """Load API keys from config file."""
    config_path = Path(__file__).parent.parent / "config" / "api_keys.yaml"

    if not config_path.exists():
        logger.error(f"❌ API keys file not found: {config_path}")
        logger.info("💡 Please copy config/api_keys.yaml.example to config/api_keys.yaml")
        return None

    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"❌ Error loading API keys: {e}")
        return None

def verify_alpha_vantage(api_key):
    """Verify Alpha Vantage API key."""
    if not api_key or api_key == "YOUR_ALPHA_VANTAGE_KEY_HERE":
        logger.warning("⚠️  Alpha Vantage API key not configured")
        logger.info("   Get free key at: https://www.alphavantage.co/support/#api-key")
        return False

    try:
        import requests
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey={api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if "Error Message" in data:
            logger.error(f"❌ Alpha Vantage API key invalid: {data['Error Message']}")
            return False
        elif "Note" in data:
            logger.warning(f"⚠️  Alpha Vantage rate limit: {data['Note']}")
            logger.info("✅ Alpha Vantage API key is valid (but rate limited)")
            return True
        elif "Time Series (5min)" in data or "Meta Data" in data:
            logger.success("✅ Alpha Vantage API key is valid and working")
            return True
        else:
            logger.warning("⚠️  Alpha Vantage responded but format unexpected")
            logger.debug(f"Response: {data}")
            return True  # Probably valid

    except Exception as e:
        logger.error(f"❌ Error verifying Alpha Vantage: {e}")
        return False

def verify_openai(api_key, model):
    """Verify OpenAI API key."""
    if not api_key or api_key == "YOUR_OPENAI_KEY_HERE":
        logger.warning("⚠️  OpenAI API key not configured")
        logger.info("   Get key at: https://platform.openai.com/api-keys")
        return False

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # Try a minimal completion to verify the key
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )

        logger.success(f"✅ OpenAI API key is valid (model: {model})")
        return True

    except Exception as e:
        error_msg = str(e)
        if "invalid" in error_msg.lower() or "unauthorized" in error_msg.lower():
            logger.error(f"❌ OpenAI API key invalid: {e}")
        else:
            logger.error(f"❌ Error verifying OpenAI: {e}")
        return False

def verify_newsapi(api_key, enabled):
    """Verify NewsAPI key."""
    if not enabled:
        logger.info("ℹ️  NewsAPI is disabled (optional)")
        return True

    if not api_key or api_key == "YOUR_NEWSAPI_KEY_HERE":
        logger.warning("⚠️  NewsAPI enabled but key not configured")
        logger.info("   Get key at: https://newsapi.org/register")
        return False

    try:
        from newsapi import NewsApiClient
        newsapi = NewsApiClient(api_key=api_key)

        # Try a simple query
        response = newsapi.get_top_headlines(q='stock', page_size=1)

        if response.get('status') == 'ok':
            logger.success("✅ NewsAPI key is valid and working")
            return True
        else:
            logger.error(f"❌ NewsAPI error: {response}")
            return False

    except Exception as e:
        logger.error(f"❌ Error verifying NewsAPI: {e}")
        return False

def main():
    """Main verification function."""
    logger.info("=" * 60)
    logger.info("🔑 API Keys Verification")
    logger.info("=" * 60)

    # Load API keys
    config = load_api_keys()
    if not config:
        sys.exit(1)

    results = {}

    # Verify Alpha Vantage
    logger.info("\n📊 Checking Alpha Vantage API...")
    alpha_vantage_key = config.get('alpha_vantage', {}).get('api_key')
    results['alpha_vantage'] = verify_alpha_vantage(alpha_vantage_key)

    # Verify OpenAI
    logger.info("\n🤖 Checking OpenAI API...")
    openai_key = config.get('openai', {}).get('api_key')
    openai_model = config.get('openai', {}).get('model', 'gpt-4o-mini')
    results['openai'] = verify_openai(openai_key, openai_model)

    # Verify NewsAPI (optional)
    logger.info("\n📰 Checking NewsAPI...")
    newsapi_key = config.get('newsapi', {}).get('api_key')
    newsapi_enabled = config.get('newsapi', {}).get('enabled', False)
    results['newsapi'] = verify_newsapi(newsapi_key, newsapi_enabled)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📋 Summary")
    logger.info("=" * 60)

    required_keys = ['alpha_vantage', 'openai']
    all_required_valid = all(results.get(key, False) for key in required_keys)

    if all_required_valid:
        logger.success("✅ All required API keys are configured and valid!")
        logger.info("\n🎯 You're ready to proceed to Step 4!")
    else:
        logger.error("❌ Some required API keys are missing or invalid")
        logger.info("\n⚠️  Please configure the missing keys in config/api_keys.yaml")
        sys.exit(1)

if __name__ == "__main__":
    main()
