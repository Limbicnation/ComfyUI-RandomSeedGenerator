"""ComfyUI node for reproducible seed generation with fixed, random, increment, and decrement modes."""

import random
import time
import logging

logger = logging.getLogger(__name__)

# Seed bounds (64-bit unsigned integer range)
MIN_SEED = 0
MAX_SEED = 0xFFFFFFFFFFFFFFFF  # 2^64 - 1


class AdvancedSeedGenerator:
    """Generates seed values for reproducible or exploratory image generation.

    Modes:
        fixed: Returns the exact seed value provided.
        random: Generates a new random seed (0 to 2^64-1) each execution.
        increment: Increments the last seed by 1 (wraps at MAX to 0).
        decrement: Decrements the last seed by 1 (wraps at 0 to MAX).

    Note:
        _last_seed is class-level state shared across all node instances.
        ComfyUI does not expose per-node identity to IS_CHANGED or generate_seed,
        so per-instance isolation is not possible without upstream API changes.
    """

    _last_seed: int = 0

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (["fixed", "increment", "decrement", "random"],),
                "seed": ("INT", {
                    "default": 0,
                    "min": MIN_SEED,
                    "max": MAX_SEED,
                    "step": 1,
                    "display": "number",
                }),
            }
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("seed",)
    FUNCTION = "generate_seed"
    CATEGORY = "utils"

    def generate_seed(self, mode: str, seed: int) -> tuple[int]:
        """Generate a seed value based on the selected mode.

        Args:
            mode: One of "fixed", "increment", "decrement", "random".
            seed: The user-provided seed value (used directly in fixed mode).

        Returns:
            A single-element tuple containing the generated seed.

        Raises:
            ValueError: If mode is not recognized.
        """
        if mode == "fixed":
            result = seed
        elif mode == "random":
            result = random.randint(MIN_SEED, MAX_SEED)
        elif mode == "increment":
            result = self.__class__._last_seed + 1
            if result > MAX_SEED:
                result = MIN_SEED
        elif mode == "decrement":
            result = self.__class__._last_seed - 1
            if result < MIN_SEED:
                result = MAX_SEED
        else:
            raise ValueError(f"Unknown mode: {mode!r}")

        self.__class__._last_seed = result
        logger.debug("Generated seed %d (mode=%s)", result, mode)
        return (result,)

    @classmethod
    def IS_CHANGED(cls, mode: str, seed: int):
        """Force re-execution for dynamic modes; cache for fixed mode."""
        if mode in ("random", "increment", "decrement"):
            return time.time()
        return f"fixed_{seed}"

    @classmethod
    def reset_state(cls) -> None:
        """Reset class-level state. Useful for testing."""
        cls._last_seed = 0


# ComfyUI Registration
NODE_CLASS_MAPPINGS = {
    "AdvancedSeedGenerator": AdvancedSeedGenerator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AdvancedSeedGenerator": "🎲 Advanced Seed Generator",
}

__all__ = ["AdvancedSeedGenerator", "NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]