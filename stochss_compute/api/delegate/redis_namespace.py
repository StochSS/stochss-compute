def vault_prefix(key: str) -> str:
    return f"vault-{key}"

def cache_prefix(key: str) -> str:
    return f"cache-{key}"

def state_prefix(key: str) -> str:
    return f"state-{key}"
