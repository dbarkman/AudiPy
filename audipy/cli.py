"""AudiPy command-line interface."""

from __future__ import annotations

import dataclasses

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from audipy import audible_client
from audipy import recommend as recommend_module
from audipy import sync as sync_module
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
def sync() -> None:
    """Fetch your Audible library into the local database."""
    config = Config.load()
    if not config.auth_file.exists():
        console.print("[yellow]Not logged in.[/] Run [bold]audipy login[/] first.")
        raise typer.Exit(code=1)
    console.print("[blue]📥 Syncing your Audible library…[/]")
    try:
        with console.status("Fetching from Audible…"):
            count = sync_module.sync_library(config)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]❌ Sync failed:[/] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(f"[bold green]✅ Synced {count} books[/] → {config.db_file}")


@app.command()
def recommend(
    authors: int = typer.Option(None, help="Number of top authors to use (default from config)."),
    narrators: int = typer.Option(None, help="Number of top narrators to use."),
    series: int = typer.Option(None, help="Number of top series to use."),
) -> None:
    """Generate recommendations from your synced library."""
    config = Config.load()
    if not config.db_file.exists():
        console.print("[yellow]No library synced yet.[/] Run [bold]audipy sync[/] first.")
        raise typer.Exit(code=1)
    overrides = {}
    if authors is not None:
        overrides["top_authors"] = authors
    if narrators is not None:
        overrides["top_narrators"] = narrators
    if series is not None:
        overrides["top_series"] = series
    if overrides:
        config = dataclasses.replace(config, **overrides)

    console.print(
        f"[blue]🔎 Finding books via your top {config.top_series} series, "
        f"{config.top_authors} authors, {config.top_narrators} narrators…[/]"
    )
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        tasks: dict[str, int] = {}
        labels = {"series": "series", "author": "authors", "narrator": "narrators"}

        def on_progress(rec_type: str, idx: int, total: int) -> None:
            if rec_type not in tasks:
                tasks[rec_type] = progress.add_task(f"Searching {labels[rec_type]}", total=total)
            progress.update(tasks[rec_type], completed=idx)

        try:
            counts = recommend_module.generate(config, progress=on_progress)
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]❌ Recommendation run failed:[/] {exc}")
            raise typer.Exit(code=1) from exc

    console.print(
        f"[bold green]✅ Found[/] {counts['series']} series, "
        f"{counts['author']} author, {counts['narrator']} narrator recommendations."
    )
    console.print("[dim]Run [bold]audipy report[/] to see them.[/]")


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
