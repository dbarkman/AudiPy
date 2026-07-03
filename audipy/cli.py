"""AudiPy command-line interface."""

from __future__ import annotations

import typer
from rich.console import Console

from audipy import audible_client
from audipy.config import Config

app = typer.Typer(
    add_completion=False,
    help="Analyze your Audible library and find your next great read.",
)
console = Console()


@app.command()
def login() -> None:
    """Authenticate with Audible and cache your tokens locally."""
    config = Config.load()
    username, password, marketplace = audible_client.prompt_credentials(config.marketplace)
    console.print(f"\n[bold blue]🔑 Authenticating with Audible ({marketplace})…[/]")
    try:
        audible_client.login(config, username, password, marketplace)
    except Exception as exc:  # noqa: BLE001 — surface any auth failure to the user
        console.print(f"[red]❌ Authentication failed:[/] {exc}")
        raise typer.Exit(code=1) from exc

    console.print("[bold green]✅ Authentication successful![/]")
    console.print(f"[dim]Tokens cached at {config.auth_file}[/]")
    console.print("Verifying API access…")
    _report_library_size(config)


@app.command()
def status() -> None:
    """Check that cached tokens work and report your library size."""
    config = Config.load()
    if not config.auth_file.exists():
        console.print("[yellow]Not logged in.[/] Run [bold]audipy login[/] to authenticate.")
        raise typer.Exit(code=1)
    console.print(f"[dim]Token cache: {config.auth_file}[/]")
    _report_library_size(config)


@app.command()
def logout() -> None:
    """Delete the local Audible token cache."""
    config = Config.load()
    if config.auth_file.exists():
        config.auth_file.unlink()
        console.print("[green]✅ Logged out — token cache removed.[/]")
    else:
        console.print("[dim]Already logged out (no token cache found).[/]")


def _report_library_size(config: Config) -> None:
    """Fetch the library size as a smoke test and print the result."""
    try:
        size = audible_client.count_library(config)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]❌ API access failed:[/] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(f"[bold green]📚 API access confirmed — {size} books in your library.[/]")


if __name__ == "__main__":
    app()
