def apply_discount(price: float, pct: float) -> float:
    """Apply a percentage discount, never below zero."""
    return price - price * pct
