"""Tests for stress_core.py -- the canonical stress-tier scale."""
from stress_core import STRESS_TIERS, score_to_tier


class TestStressTiers:
    def test_four_tiers_defined(self):
        assert set(STRESS_TIERS.keys()) == {"LOW", "ELEVATED", "HIGH", "CRITICAL"}

    def test_tiers_are_contiguous(self):
        assert STRESS_TIERS["LOW"] == (0.0, 25.0)
        assert STRESS_TIERS["ELEVATED"] == (25.0, 50.0)
        assert STRESS_TIERS["HIGH"] == (50.0, 75.0)
        assert STRESS_TIERS["CRITICAL"] == (75.0, 100.1)


class TestScoreToTier:
    def test_zero_is_low(self):
        assert score_to_tier(0.0) == "LOW"

    def test_24_point_9_is_low(self):
        assert score_to_tier(24.9) == "LOW"

    def test_25_is_elevated(self):
        assert score_to_tier(25.0) == "ELEVATED"

    def test_49_point_9_is_elevated(self):
        assert score_to_tier(49.9) == "ELEVATED"

    def test_50_is_high(self):
        assert score_to_tier(50.0) == "HIGH"

    def test_74_point_9_is_high(self):
        assert score_to_tier(74.9) == "HIGH"

    def test_75_is_critical(self):
        assert score_to_tier(75.0) == "CRITICAL"

    def test_100_is_critical(self):
        assert score_to_tier(100.0) == "CRITICAL"

    def test_above_100_falls_back_to_critical(self):
        # Defensive: a caller passing an out-of-range score (shouldn't
        # happen if compute_stress()'s own clamping is correct, but this
        # function makes no assumption about that) still resolves sanely.
        assert score_to_tier(150.0) == "CRITICAL"
