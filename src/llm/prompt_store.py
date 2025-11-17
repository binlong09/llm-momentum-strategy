"""
LLM Prompt Storage and Retrieval

Stores prompts used for LLM scoring so users can review what was analyzed.
"""

from typing import Dict, Optional
from datetime import datetime
import json
from pathlib import Path
from loguru import logger


class PromptStore:
    """Store and retrieve LLM prompts for transparency."""

    def __init__(self, cache_dir: str = "data/llm_prompts"):
        """
        Initialize prompt store.

        Args:
            cache_dir: Directory to store prompts
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.current_session_prompts: Dict[str, Dict] = {}

    def store_prompt(
        self,
        symbol: str,
        prompt: str,
        prompt_type: str = "llm_scoring",
        metadata: Optional[Dict] = None
    ):
        """
        Store a prompt for a symbol.

        Args:
            symbol: Stock ticker
            prompt: The full prompt sent to LLM
            prompt_type: Type of prompt (llm_scoring, risk_scoring, etc.)
            metadata: Optional metadata (model, timestamp, etc.)
        """
        if symbol not in self.current_session_prompts:
            self.current_session_prompts[symbol] = {}

        self.current_session_prompts[symbol][prompt_type] = {
            'prompt': prompt,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }

    def get_prompt(self, symbol: str, prompt_type: str = "llm_scoring") -> Optional[str]:
        """
        Get stored prompt for a symbol.

        Args:
            symbol: Stock ticker
            prompt_type: Type of prompt to retrieve

        Returns:
            Prompt string or None if not found
        """
        if symbol in self.current_session_prompts:
            if prompt_type in self.current_session_prompts[symbol]:
                return self.current_session_prompts[symbol][prompt_type]['prompt']
        return None

    def get_all_prompts(self, symbol: str) -> Dict[str, str]:
        """
        Get all prompts for a symbol.

        Args:
            symbol: Stock ticker

        Returns:
            Dictionary mapping prompt_type to prompt string
        """
        if symbol not in self.current_session_prompts:
            return {}

        return {
            prompt_type: data['prompt']
            for prompt_type, data in self.current_session_prompts[symbol].items()
        }

    def save_session(self, session_name: Optional[str] = None):
        """
        Save current session prompts to disk.

        Args:
            session_name: Optional name for session (default: timestamp)
        """
        if not self.current_session_prompts:
            logger.warning("No prompts to save")
            return

        if session_name is None:
            session_name = datetime.now().strftime("%Y%m%d_%H%M%S")

        output_file = self.cache_dir / f"{session_name}.json"

        with open(output_file, 'w') as f:
            json.dump(self.current_session_prompts, f, indent=2)

        logger.info(f"Saved {len(self.current_session_prompts)} stock prompts to {output_file}")

    def load_session(self, session_name: str) -> bool:
        """
        Load prompts from a saved session.

        Args:
            session_name: Session name or filename

        Returns:
            True if loaded successfully
        """
        if not session_name.endswith('.json'):
            session_name += '.json'

        input_file = self.cache_dir / session_name

        if not input_file.exists():
            logger.error(f"Session file not found: {input_file}")
            return False

        try:
            with open(input_file, 'r') as f:
                self.current_session_prompts = json.load(f)

            logger.info(f"Loaded {len(self.current_session_prompts)} stock prompts from {input_file}")
            return True

        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return False

    def clear_session(self):
        """Clear current session prompts."""
        self.current_session_prompts = {}
        logger.info("Cleared current session prompts")

    def get_session_summary(self) -> Dict:
        """
        Get summary of current session.

        Returns:
            Summary dict with stats
        """
        if not self.current_session_prompts:
            return {'stock_count': 0, 'prompt_types': []}

        prompt_types = set()
        for symbol_data in self.current_session_prompts.values():
            prompt_types.update(symbol_data.keys())

        return {
            'stock_count': len(self.current_session_prompts),
            'prompt_types': sorted(list(prompt_types)),
            'symbols': sorted(list(self.current_session_prompts.keys()))
        }


# Global instance for easy access
_global_store = None


def get_prompt_store(cache_dir: str = "data/llm_prompts") -> PromptStore:
    """Get or create global prompt store instance."""
    global _global_store
    if _global_store is None:
        _global_store = PromptStore(cache_dir)
    return _global_store
