#!/usr/bin/env python3
"""Test script to verify Daneel's fixes to Psychohistory.

This script:
1. Tests that the Alpaca client has the new methods
2. Tests that constraints are PRD-compliant
3. Tests that gradient thresholds allow trading
4. Attempts a small test trade ($25) on crypto

Run with: python test_fixes.py
"""

import os
import sys
from decimal import Decimal
from datetime import date

# Ensure psychohistory is importable
sys.path.insert(0, '/Users/jamienucho/psychohistory')

def test_constraints():
    """Test that constraints match PRD spec."""
    print("\n=== TEST: Constraints ===")

    from psychohistory.daemon.constraints import (
        MAX_SINGLE_POSITION,
        MIN_CASH,
        MIN_CONFLUENCE_SCORE,
        MIN_AGREEING_LAYERS,
    )

    tests = [
        ("MAX_SINGLE_POSITION", MAX_SINGLE_POSITION, Decimal("0.15"), "15%"),
        ("MIN_CASH", MIN_CASH, Decimal("0.20"), "20%"),
        ("MIN_CONFLUENCE_SCORE", MIN_CONFLUENCE_SCORE, Decimal("0.70"), "70%"),
        ("MIN_AGREEING_LAYERS", MIN_AGREEING_LAYERS, 3, "3"),
    ]

    all_passed = True
    for name, actual, expected, display in tests:
        passed = actual == expected
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name} = {actual} (expected {display})")
        if not passed:
            all_passed = False

    return all_passed


def test_alpaca_client():
    """Test that Alpaca client has required methods."""
    print("\n=== TEST: Alpaca Client Methods ===")

    from psychohistory.trading.alpaca_client import AlpacaClient, AccountInfo

    # Check AccountInfo has non_marginable_buying_power
    has_field = hasattr(AccountInfo, '__dataclass_fields__') and 'non_marginable_buying_power' in AccountInfo.__dataclass_fields__
    print(f"  {'PASS' if has_field else 'FAIL'}: AccountInfo.non_marginable_buying_power field exists")

    # Check AlpacaClient has new methods
    has_get_open_orders = hasattr(AlpacaClient, 'get_open_orders')
    has_cancel_all = hasattr(AlpacaClient, 'cancel_all_orders')

    print(f"  {'PASS' if has_get_open_orders else 'FAIL'}: AlpacaClient.get_open_orders() exists")
    print(f"  {'PASS' if has_cancel_all else 'FAIL'}: AlpacaClient.cancel_all_orders() exists")

    return has_field and has_get_open_orders and has_cancel_all


def test_gradient_thresholds():
    """Test that gradient thresholds are lowered for initial trading."""
    print("\n=== TEST: Gradient Thresholds ===")

    from psychohistory.gradient.field import GradientFieldEngine
    from psychohistory.gradient.types import FieldState

    engine = GradientFieldEngine()

    mag_ok = engine.magnitude_threshold <= 0.25
    dim_ok = engine.min_active_dimensions <= 2

    print(f"  {'PASS' if mag_ok else 'FAIL'}: magnitude_threshold = {engine.magnitude_threshold} (<= 0.25)")
    print(f"  {'PASS' if dim_ok else 'FAIL'}: min_active_dimensions = {engine.min_active_dimensions} (<= 2)")

    return mag_ok and dim_ok


def test_alpaca_connection():
    """Test actual connection to Alpaca paper trading."""
    print("\n=== TEST: Alpaca Connection ===")

    # Check for credentials
    api_key = os.environ.get("ALPACA_API_KEY")
    secret_key = os.environ.get("ALPACA_SECRET_KEY")

    if not api_key or not secret_key:
        print("  SKIP: ALPACA_API_KEY or ALPACA_SECRET_KEY not set")
        print("  Set these environment variables to test live connection")
        return None

    try:
        from psychohistory.trading import get_trading_client
        client = get_trading_client()

        # Get account info
        account = client.get_account()
        print(f"  PASS: Connected to Alpaca")
        print(f"        Equity: ${float(account.equity):,.2f}")
        print(f"        Cash: ${float(account.cash):,.2f}")
        print(f"        Buying Power: ${float(account.buying_power):,.2f}")
        print(f"        Crypto BP: ${float(account.non_marginable_buying_power):,.2f}")

        # Get positions
        positions = client.get_positions()
        print(f"        Open Positions: {len(positions)}")

        # Get open orders
        orders = client.get_open_orders()
        print(f"        Pending Orders: {len(orders)}")

        return True

    except Exception as e:
        print(f"  FAIL: Could not connect to Alpaca: {e}")
        return False


def test_small_trade():
    """Attempt a small test trade ($25 of SOL)."""
    print("\n=== TEST: Small Trade ($25 SOL) ===")

    api_key = os.environ.get("ALPACA_API_KEY")
    if not api_key:
        print("  SKIP: No Alpaca credentials")
        return None

    try:
        from psychohistory.trading import get_trading_client
        client = get_trading_client()

        # Check if we have enough cash
        account = client.get_account()
        if account.cash < Decimal("30"):
            print(f"  SKIP: Insufficient cash (${float(account.cash):.2f} < $30)")
            return None

        # Cancel any pending orders first
        pending = client.get_open_orders()
        if pending:
            print(f"  Cancelling {len(pending)} pending orders...")
            client.cancel_all_orders()
            import time
            time.sleep(2)

        # Submit small buy order
        print("  Submitting: BUY $25 SOL/USD...")
        result = client.submit_order(
            symbol="SOL",
            side="buy",
            notional=Decimal("25"),
        )

        if result.success:
            print(f"  PASS: Order submitted successfully!")
            print(f"        Order ID: {result.order_id}")
            print(f"        Status: {result.status}")
            return True
        else:
            print(f"  FAIL: Order rejected - {result.error}")
            return False

    except Exception as e:
        print(f"  FAIL: Error during trade: {e}")
        return False


def main():
    print("=" * 60)
    print("PSYCHOHISTORY FIX VERIFICATION")
    print("=" * 60)
    print("\nDaneel is testing the repairs...")

    results = {
        "constraints": test_constraints(),
        "alpaca_client": test_alpaca_client(),
        "gradient_thresholds": test_gradient_thresholds(),
        "alpaca_connection": test_alpaca_connection(),
    }

    # Only attempt trade if connection works
    if results["alpaca_connection"]:
        response = input("\nAttempt small test trade? ($25 SOL) [y/N]: ")
        if response.lower() == 'y':
            results["small_trade"] = test_small_trade()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for test_name, result in results.items():
        if result is None:
            status = "SKIPPED"
        elif result:
            status = "PASSED"
        else:
            status = "FAILED"
        print(f"  {test_name}: {status}")

    # Return success if core tests passed
    core_passed = all(r for r in [results["constraints"], results["alpaca_client"], results["gradient_thresholds"]] if r is not None)
    return 0 if core_passed else 1


if __name__ == "__main__":
    sys.exit(main())
