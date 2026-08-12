# experiments/p5_8_bug/username.py

def normalize_username(value: str) -> str:
    return value.strip().replace(" ", "_")
