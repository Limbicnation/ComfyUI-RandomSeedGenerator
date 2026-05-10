"""Pytest suite for AdvancedSeedGenerator.

Covers the four modes (fixed, random, increment, decrement), wrap behavior at
both 64-bit boundaries, IS_CHANGED contract, and reset_state.
"""

import sys
import time
from pathlib import Path

import pytest

# Allow `import random_seed_generator` when pytest is run from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from random_seed_generator import (  # noqa: E402
    MAX_SEED,
    MIN_SEED,
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
    AdvancedSeedGenerator,
)


@pytest.fixture(autouse=True)
def _reset_class_state():
    """`_last_seed` is class-level shared state — reset before every test."""
    AdvancedSeedGenerator.reset_state()
    yield
    AdvancedSeedGenerator.reset_state()


@pytest.fixture
def gen():
    return AdvancedSeedGenerator()


def test_fixed_returns_input_seed(gen):
    assert gen.generate_seed("fixed", 42) == (42,)


def test_fixed_does_not_mutate_last_seed(gen):
    """Regression: fixed mode must not touch the shared increment/decrement counter.

    Before this guard, calling `fixed` clobbered `_last_seed`, which silently
    altered other AdvancedSeedGenerator nodes running increment/decrement in the
    same workflow.
    """
    AdvancedSeedGenerator._last_seed = 500
    assert gen.generate_seed("fixed", 12345) == (12345,)
    assert AdvancedSeedGenerator._last_seed == 500


def test_random_updates_last_seed(gen):
    AdvancedSeedGenerator._last_seed = 0
    (result,) = gen.generate_seed("random", 0)
    assert AdvancedSeedGenerator._last_seed == result


def test_increment_updates_last_seed(gen):
    AdvancedSeedGenerator._last_seed = 100
    gen.generate_seed("increment", 0)
    assert AdvancedSeedGenerator._last_seed == 101


def test_random_within_bounds(gen):
    (result,) = gen.generate_seed("random", 0)
    assert isinstance(result, int)
    assert MIN_SEED <= result <= MAX_SEED


def test_random_produces_different_values(gen):
    samples = {gen.generate_seed("random", 0)[0] for _ in range(20)}
    # 20 draws from a 2^64 space colliding 19 times would be a miracle.
    assert len(samples) > 1


def test_increment_advances_last_seed(gen):
    AdvancedSeedGenerator._last_seed = 100
    assert gen.generate_seed("increment", 0) == (101,)
    assert gen.generate_seed("increment", 0) == (102,)


def test_decrement_decreases_last_seed(gen):
    AdvancedSeedGenerator._last_seed = 100
    assert gen.generate_seed("decrement", 0) == (99,)
    assert gen.generate_seed("decrement", 0) == (98,)


def test_increment_wraps_at_max(gen):
    AdvancedSeedGenerator._last_seed = MAX_SEED
    assert gen.generate_seed("increment", 0) == (MIN_SEED,)


def test_decrement_wraps_at_min(gen):
    AdvancedSeedGenerator._last_seed = MIN_SEED
    assert gen.generate_seed("decrement", 0) == (MAX_SEED,)


def test_unknown_mode_raises_value_error(gen):
    with pytest.raises(ValueError, match="Unknown mode"):
        gen.generate_seed("teleport", 0)


def test_is_changed_dynamic_modes_return_timestamp():
    for mode in ("random", "increment", "decrement"):
        before = time.time()
        result = AdvancedSeedGenerator.IS_CHANGED(mode, 0)
        after = time.time()
        assert isinstance(result, float)
        assert before <= result <= after


def test_is_changed_fixed_returns_stable_key():
    assert AdvancedSeedGenerator.IS_CHANGED("fixed", 99) == "fixed_99"
    assert AdvancedSeedGenerator.IS_CHANGED("fixed", 99) == "fixed_99"


def test_reset_state_clears_last_seed(gen):
    AdvancedSeedGenerator._last_seed = 7777
    assert AdvancedSeedGenerator._last_seed == 7777
    AdvancedSeedGenerator.reset_state()
    assert AdvancedSeedGenerator._last_seed == 0


def test_node_registration_mappings():
    assert NODE_CLASS_MAPPINGS == {"AdvancedSeedGenerator": AdvancedSeedGenerator}
    assert "AdvancedSeedGenerator" in NODE_DISPLAY_NAME_MAPPINGS


def test_input_types_schema_shape():
    schema = AdvancedSeedGenerator.INPUT_TYPES()
    assert "required" in schema
    assert set(schema["required"].keys()) == {"mode", "seed"}
    mode_choices, *_ = schema["required"]["mode"]
    assert set(mode_choices) == {"fixed", "random", "increment", "decrement"}
    seed_type, seed_meta = schema["required"]["seed"]
    assert seed_type == "INT"
    assert seed_meta["min"] == MIN_SEED
    assert seed_meta["max"] == MAX_SEED


def test_comfyui_class_attributes():
    assert AdvancedSeedGenerator.RETURN_TYPES == ("INT",)
    assert AdvancedSeedGenerator.RETURN_NAMES == ("seed",)
    assert AdvancedSeedGenerator.FUNCTION == "generate_seed"
    assert AdvancedSeedGenerator.CATEGORY == "utils"
