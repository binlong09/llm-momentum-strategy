#!/usr/bin/env python3
"""
Configuration Validator
Validates that config.yaml has all required parameters with valid values.
"""

import sys
from pathlib import Path
import yaml
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_config():
    """Load configuration file."""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"

    if not config_path.exists():
        logger.error(f"❌ Configuration file not found: {config_path}")
        return None

    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"❌ Error loading config: {e}")
        return None

def validate_strategy_params(config):
    """Validate strategy parameters."""
    errors = []
    warnings = []

    strategy = config.get('strategy', {})

    # Check required fields
    if not strategy.get('universe'):
        errors.append("Missing strategy.universe")

    # Momentum parameters
    lookback = strategy.get('momentum_lookback_months')
    if lookback is None:
        errors.append("Missing strategy.momentum_lookback_months")
    elif not isinstance(lookback, int) or lookback < 1 or lookback > 60:
        warnings.append(f"momentum_lookback_months={lookback} is unusual (typical: 6-12 months)")

    # Portfolio construction
    top_pct = strategy.get('top_percentile')
    if top_pct is None:
        errors.append("Missing strategy.top_percentile")
    elif not (0 < top_pct <= 1):
        errors.append(f"top_percentile must be between 0 and 1, got {top_pct}")

    portfolio_size = strategy.get('final_portfolio_size')
    if portfolio_size is None:
        errors.append("Missing strategy.final_portfolio_size")
    elif portfolio_size < 1:
        errors.append(f"final_portfolio_size must be positive, got {portfolio_size}")

    # Weighting parameters
    max_weight = strategy.get('max_position_weight')
    if max_weight is None:
        errors.append("Missing strategy.max_position_weight")
    elif not (0 < max_weight <= 1):
        errors.append(f"max_position_weight must be between 0 and 1, got {max_weight}")

    tilt_factor = strategy.get('weight_tilt_factor')
    if tilt_factor is None:
        warnings.append("Missing strategy.weight_tilt_factor (using default)")
    elif tilt_factor < 0:
        errors.append(f"weight_tilt_factor must be non-negative, got {tilt_factor}")

    # LLM parameters
    llm = strategy.get('llm', {})
    if not llm.get('news_lookback_days'):
        errors.append("Missing strategy.llm.news_lookback_days")
    if not llm.get('forecast_horizon_days'):
        errors.append("Missing strategy.llm.forecast_horizon_days")

    return errors, warnings

def validate_backtesting_params(config):
    """Validate backtesting parameters."""
    errors = []
    warnings = []

    backtesting = config.get('backtesting', {})

    # Check date format
    required_dates = ['validation_start', 'validation_end', 'test_start', 'test_end']
    for date_field in required_dates:
        date_val = backtesting.get(date_field)
        if not date_val:
            errors.append(f"Missing backtesting.{date_field}")
        else:
            # Try to parse date
            try:
                from datetime import datetime
                datetime.strptime(date_val, '%Y-%m-%d')
            except ValueError:
                errors.append(f"Invalid date format for backtesting.{date_field}: {date_val} (use YYYY-MM-DD)")

    # Check metrics
    if not backtesting.get('metrics'):
        warnings.append("No backtesting.metrics specified")

    return errors, warnings

def validate_data_sources(config):
    """Validate data source configuration."""
    errors = []
    warnings = []

    data_sources = config.get('data_sources', {})

    # Price data source
    price_source = data_sources.get('price_data')
    if not price_source:
        errors.append("Missing data_sources.price_data")
    elif price_source not in ['alpha_vantage', 'yfinance']:
        warnings.append(f"Unknown price_data source: {price_source}")

    # News sources
    news_sources = data_sources.get('news_sources', {})
    if not any(news_sources.values()):
        warnings.append("No news sources enabled")

    return errors, warnings

def validate_cache_config(config):
    """Validate caching configuration."""
    errors = []
    warnings = []

    cache = config.get('cache', {})

    if cache.get('enabled'):
        if not cache.get('cache_dir'):
            errors.append("cache.enabled=true but cache_dir not specified")

        # Check refresh intervals
        price_cache = cache.get('price_cache_days')
        if price_cache and price_cache > 7:
            warnings.append(f"price_cache_days={price_cache} is quite long")

    return errors, warnings

def validate_logging_config(config):
    """Validate logging configuration."""
    errors = []
    warnings = []

    logging = config.get('logging', {})

    level = logging.get('level', 'INFO')
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if level not in valid_levels:
        errors.append(f"Invalid logging.level: {level} (must be one of {valid_levels})")

    return errors, warnings

def main():
    """Main validation function."""
    logger.info("=" * 60)
    logger.info("⚙️  Configuration Validation")
    logger.info("=" * 60)

    # Load config
    config = load_config()
    if not config:
        sys.exit(1)

    logger.success("✅ Config file loaded successfully")

    # Run all validations
    all_errors = []
    all_warnings = []

    validators = [
        ("Strategy Parameters", validate_strategy_params),
        ("Backtesting Parameters", validate_backtesting_params),
        ("Data Sources", validate_data_sources),
        ("Cache Configuration", validate_cache_config),
        ("Logging Configuration", validate_logging_config),
    ]

    for section_name, validator_func in validators:
        logger.info(f"\n📋 Validating {section_name}...")
        errors, warnings = validator_func(config)

        if errors:
            for error in errors:
                logger.error(f"  ❌ {error}")
            all_errors.extend(errors)

        if warnings:
            for warning in warnings:
                logger.warning(f"  ⚠️  {warning}")
            all_warnings.extend(warnings)

        if not errors and not warnings:
            logger.success(f"  ✅ {section_name} valid")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Validation Summary")
    logger.info("=" * 60)

    if all_errors:
        logger.error(f"❌ Found {len(all_errors)} error(s)")
        for i, error in enumerate(all_errors, 1):
            logger.error(f"  {i}. {error}")

    if all_warnings:
        logger.warning(f"⚠️  Found {len(all_warnings)} warning(s)")
        for i, warning in enumerate(all_warnings, 1):
            logger.warning(f"  {i}. {warning}")

    if not all_errors and not all_warnings:
        logger.success("✅ Configuration is valid with no issues!")
        logger.info("\n🎯 Ready to proceed to data collection!")
    elif not all_errors:
        logger.success("✅ Configuration is valid (with warnings)")
        logger.info("\n🎯 Ready to proceed to data collection!")
    else:
        logger.error("\n❌ Please fix the errors in config/config.yaml")
        sys.exit(1)

if __name__ == "__main__":
    main()
