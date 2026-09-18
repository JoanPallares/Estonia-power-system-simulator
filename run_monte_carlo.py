"""
run_monte_carlo.py
====================
Phase 54: canonical entry point — "python run_monte_carlo.py" -> reliability.

Thin wrapper: the real logic lives in run_monte_carlo_reliability.py
(kept for its more detailed docstring); this is the clean, short name
Phase 54 asks for.
"""

from run_monte_carlo_reliability import main

if __name__ == "__main__":
    main()
