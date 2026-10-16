"""Zimbra MCP server configuration."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

_TRUE_VALUES = ("true", "1", "yes")


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").lower() in _TRUE_VALUES


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} must be an integer, got {raw!r}")
    if value <= 0:
        raise ValueError(f"{name} must be > 0, got {value}")
    return value


def _default_download_dir() -> Path:
    return Path.home() / "Downloads"


@dataclass
class ZimbraConfig:
    """Configuration for Zimbra connection."""

    url: str
    user: str
    password: str = field(repr=False)
    timeout: int = 30
    enable_send: bool = False
    enable_hard_delete: bool = False
    download_dir: Path = field(default_factory=_default_download_dir)
    max_attachment_bytes: int = 50 * 1024 * 1024
    allow_insecure_http: bool = False

    def __post_init__(self) -> None:
        parsed = urlparse(self.url)
        if parsed.scheme not in ("https", "http") or not parsed.netloc:
            raise ValueError(f"ZIMBRA_URL must be an http(s) URL, got {self.url!r}")
        if parsed.scheme == "http" and not self.allow_insecure_http:
            raise ValueError(
                "ZIMBRA_URL uses plain HTTP: credentials and auth token would be sent "
                "unencrypted. Use https:// or set ZIMBRA_ALLOW_INSECURE_HTTP=true."
            )
        self.download_dir = Path(self.download_dir).expanduser().resolve()

    @property
    def base_url(self) -> str:
        """Server root URL (scheme://host[:port]), without the SOAP path."""
        parsed = urlparse(self.url)
        return f"{parsed.scheme}://{parsed.netloc}"

    @classmethod
    def from_env(cls) -> "ZimbraConfig":
        """Load configuration from environment variables."""
        load_dotenv()

        url = os.getenv("ZIMBRA_URL")
        user = os.getenv("ZIMBRA_USER")
        password = os.getenv("ZIMBRA_PASSWORD")

        if not url:
            raise ValueError("ZIMBRA_URL not defined")
        if not user:
            raise ValueError("ZIMBRA_USER not defined")
        if not password:
            raise ValueError("ZIMBRA_PASSWORD not defined")

        download_dir = os.getenv("ZIMBRA_DOWNLOAD_DIR")

        return cls(
            url=url,
            user=user,
            password=password,
            timeout=_env_int("ZIMBRA_TIMEOUT", 30),
            enable_send=_env_flag("ZIMBRA_ENABLE_SEND"),
            enable_hard_delete=_env_flag("ZIMBRA_ENABLE_HARD_DELETE"),
            download_dir=Path(download_dir) if download_dir else _default_download_dir(),
            max_attachment_bytes=_env_int("ZIMBRA_MAX_ATTACHMENT_MB", 50) * 1024 * 1024,
            allow_insecure_http=_env_flag("ZIMBRA_ALLOW_INSECURE_HTTP"),
        )
