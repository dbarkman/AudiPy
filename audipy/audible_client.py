"""Audible authentication and API access for a single local user.

Uses the community ``audible`` library. Tokens are cached to a local JSON file
under the AudiPy home directory (``auth.json``, chmod 0600) — the library
handles automatic access-token refresh from the long-lived refresh token, so
you only complete the interactive login (including OTP) once.
"""

from __future__ import annotations

import getpass
from collections.abc import Iterator

from audible import Authenticator, Client
from rich.console import Console

from audipy.config import Config

console = Console()

# Max items the Audible library endpoint returns per page.
PAGE_SIZE = 1000


class NotAuthenticatedError(RuntimeError):
    """Raised when an operation needs auth but no token cache exists."""


# --- Interactive login callbacks -------------------------------------------------
# The `audible` library invokes these only when Amazon demands the corresponding
# challenge during login. Each returns the value the library needs.


def _otp_callback() -> str:
    console.print("[yellow]📱 Two-factor authentication required.[/]")
    return input("Enter the OTP code from your authenticator/SMS: ").strip()


def _cvf_callback() -> str:
    console.print("[yellow]📧 Amazon sent a verification code (check email/SMS).[/]")
    return input("Enter the CVF verification code: ").strip()


def _captcha_callback(captcha_url: str) -> str:
    console.print("[yellow]🤖 Amazon is asking for a captcha.[/]")
    console.print(f"Open this URL and read the captcha:\n[cyan]{captcha_url}[/]")
    return input("Enter the captcha answer: ").strip()


def _approval_callback() -> None:
    console.print(
        "[yellow]✅ Amazon sent an approval request.[/] "
        "Approve the sign-in in your Amazon app or email, then press Enter."
    )
    input()


def login(config: Config, username: str, password: str, marketplace: str) -> None:
    """Interactively authenticate with Audible and cache tokens locally.

    Blocks on stdin for any OTP/CVF/captcha/approval challenge Amazon raises.
    On success, writes the token cache to ``config.auth_file`` (chmod 0600).
    """
    auth = Authenticator.from_login(
        username=username,
        password=password,
        locale=marketplace,
        captcha_callback=_captcha_callback,
        otp_callback=_otp_callback,
        cvf_callback=_cvf_callback,
        approval_callback=_approval_callback,
    )
    # Store unencrypted (single-user local file); lock down permissions instead.
    auth.to_file(config.auth_file, encryption=False)
    config.auth_file.chmod(0o600)


def load_authenticator(config: Config) -> Authenticator:
    """Load cached tokens, refreshing the access token if it has expired."""
    if not config.auth_file.exists():
        raise NotAuthenticatedError(
            "No Audible token cache found. Run `audipy login` first."
        )
    auth = Authenticator.from_file(config.auth_file, encryption=False)
    if auth.access_token_expired:
        auth.refresh_access_token()
        auth.to_file(config.auth_file, encryption=False)
        config.auth_file.chmod(0o600)
    return auth


def get_client(config: Config) -> Client:
    """Return an authenticated Audible API client."""
    return Client(auth=load_authenticator(config))


def prompt_credentials(default_marketplace: str) -> tuple[str, str, str]:
    """Prompt the terminal for username, password, and marketplace."""
    console.print("\n[bold blue]🔐 Audible login[/]")
    console.print("[dim]Your password is used once to authenticate and is never stored.[/]")
    username = input("Audible email/username: ").strip()
    password = getpass.getpass("Password (hidden, not saved): ").strip()
    marketplace = (
        input(f"Marketplace (us/uk/de/…) [{default_marketplace}]: ").strip()
        or default_marketplace
    ).lower()
    return username, password, marketplace


def iter_library_items(config: Config, response_groups: str) -> Iterator[dict]:
    """Yield every book in the library, paging through the API.

    The library endpoint no longer returns a ``total_size``, so counting and
    syncing both work by paging until a short page signals the end.
    """
    client = get_client(config)
    page = 1
    while True:
        resp = client.get(
            "1.0/library",
            num_results=PAGE_SIZE,
            page=page,
            response_groups=response_groups,
        )
        items = resp.get("items", []) if isinstance(resp, dict) else []
        yield from items
        if len(items) < PAGE_SIZE:
            return
        page += 1


def count_library(config: Config) -> int:
    """Return the number of books in the library (auth/API smoke test)."""
    return sum(1 for _ in iter_library_items(config, response_groups="product_desc"))
