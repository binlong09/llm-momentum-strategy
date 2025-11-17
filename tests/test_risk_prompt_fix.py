"""Quick test to verify risk prompt storage fix."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.llm.risk_scorer import LLMRiskScorer
from src.llm.prompt_store import PromptStore

def test_fix():
    print("=" * 80)
    print("TESTING RISK PROMPT STORAGE FIX")
    print("=" * 80)

    # Initialize
    risk_scorer = LLMRiskScorer(model='gpt-4o-mini')
    prompt_store = PromptStore()
    prompt_store.clear_session()

    # Test data - minimal news
    test_news = {
        'AAPL': ["Apple reports strong earnings."],
        'NVDA': [],  # Test no-news case
    }

    import pandas as pd
    test_portfolio = pd.DataFrame({
        'symbol': ['AAPL', 'NVDA'],
        'weight': [0.5, 0.5]
    })

    print("\n1. Testing WITH prompt storage enabled...")
    print("   This should now store prompts for BOTH stocks (even NVDA with no news)")

    # Score with prompt storage
    result_portfolio = risk_scorer.score_portfolio_risks(
        test_portfolio.copy(),
        test_news,
        show_progress=True,
        store_prompts=True,
        prompt_store=prompt_store
    )

    # Check results
    summary = prompt_store.get_session_summary()
    print(f"\n2. Prompt Store Summary:")
    print(f"   Stocks stored: {summary['stock_count']}")
    print(f"   Prompt types: {summary['prompt_types']}")

    # Check individual stocks
    print("\n3. Individual Stock Prompts:")
    for symbol in ['AAPL', 'NVDA']:
        prompt = prompt_store.get_prompt(symbol, 'risk_scoring')
        if prompt:
            print(f"   ✅ {symbol}: Prompt stored ({len(prompt)} chars)")
            print(f"      Preview: {prompt[:100]}...")
        else:
            print(f"   ❌ {symbol}: NO PROMPT STORED")

    # Summary
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)

    if summary['stock_count'] == 2:
        print("✅ Both stocks have prompts stored")
    else:
        print(f"❌ Expected 2 stocks, got {summary['stock_count']}")

    if 'risk_scoring' in summary['prompt_types']:
        print("✅ Risk scoring prompt type present")
    else:
        print("❌ Risk scoring prompt type missing")

    # Check NVDA specifically (no-news case)
    nvda_prompt = prompt_store.get_prompt('NVDA', 'risk_scoring')
    if nvda_prompt:
        print("✅ NVDA (no news) has prompt stored - FIX WORKING!")
        if "No recent news available" in nvda_prompt:
            print("   ✅ Prompt correctly indicates no news")
    else:
        print("❌ NVDA (no news) missing prompt - FIX NOT WORKING")

    print("\n🎉 Test complete!")

if __name__ == "__main__":
    test_fix()
