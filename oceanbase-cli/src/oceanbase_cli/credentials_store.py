"""Encrypted DSN storage — plaintext never read from environment variables.

The Fernet key lives alongside the config dir (file mode 0600). The encrypted
payload is written to ``dsn.enc``. Agents/models should not be given the config
directory contents or CLI flags containing raw DSNs in production workflows.
"""

from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from oceanbase_cli.paths import config_dir, encrypted_dsn_path

# Pytest: set via set_test_encryption_key() so tests do not touch real ~/.config.
_test_fernet: Fernet | None = None


def set_test_encryption_key(key: bytes | None) -> None:
    """Use a fixed Fernet key for tests; pass None to use production key resolution."""
    global _test_fernet
    if key is None:
        _test_fernet = None
    else:
        _test_fernet = Fernet(key)


def _fernet() -> Fernet:
    if _test_fernet is not None:
        return _test_fernet
    d = config_dir()
    d.mkdir(parents=True, exist_ok=True)
    key_path = d / ".obcli-key"
    if not key_path.is_file():
        raw = Fernet.generate_key()
        key_path.write_bytes(raw)
        try:
            key_path.chmod(0o600)
        except OSError:
            pass
    else:
        raw = key_path.read_bytes()
    return Fernet(raw)


def store_encrypted_dsn(plaintext: str) -> None:
    """Encrypt and write DSN (e.g. oceanbase://... or embedded:...)."""
    text = plaintext.strip()
    if not text:
        raise ValueError("DSN must be non-empty")
    token = _fernet().encrypt(text.encode("utf-8"))
    p = encrypted_dsn_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(token)
    try:
        p.chmod(0o600)
    except OSError:
        pass


def load_encrypted_dsn() -> str | None:
    p = encrypted_dsn_path()
    if not p.is_file():
        return None
    try:
        return _fernet().decrypt(p.read_bytes()).decode("utf-8")
    except InvalidToken:
        return None


def clear_encrypted_dsn() -> None:
    p = encrypted_dsn_path()
    if p.is_file():
        p.unlink()
