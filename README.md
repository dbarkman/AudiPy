# AudiPy

A local, single-user command-line tool that analyzes your Audible library and
helps you find your next great read. It looks at what you already own and
surfaces:

- 📚 **Missing books in your series** — the next entries in series you've started
- ✍️ **More by your authors** — other books by authors you already read
- 🎧 **Discovery via your narrators** — books read by narrators you trust

Each suggestion is tagged 💰 **cash** or 🎫 **credit** using the rule that you
should never pay more than a credit's worth of cash: below your max price, pay
cash and save the credit; at or above it, spend a credit instead.

Everything runs on your machine. Your Audible tokens and the synced library are
stored under `~/.audipy/` and never leave your computer.

## Requirements

- Python 3.12+ (managed automatically by `uv`)
- [uv](https://docs.astral.sh/uv/)
- An Audible account

## Install

```bash
uv sync
```

## Usage

```bash
# 1. Log in to Audible (one time; handles OTP/2FA). Tokens are cached locally
#    and auto-refresh, so you won't need to do this again.
uv run audipy login

# 2. Pull your library into the local database.
uv run audipy sync

# 3. Generate recommendations.
uv run audipy recommend

# 4. Read them.
uv run audipy report                 # all three lists
uv run audipy report series          # just series continuations
uv run audipy report author --cash   # only cash deals under your max price
uv run audipy report --save          # also write text files to ./reports/
```

Other commands: `audipy status` (verify auth + library size) and
`audipy logout` (delete the local token cache).

### Tuning a run

`recommend` uses your top authors/narrators/series by number of books owned.
Override how many it considers:

```bash
uv run audipy recommend --series 100 --authors 25 --narrators 25
```

## Configuration

Defaults work out of the box. To customize, create `~/.audipy/config.toml`:

```toml
marketplace = "us"     # us, uk, de, fr, ca, au, in, it, es, jp, br
max_price = 12.66      # cash-vs-credit threshold (one credit's cost)
language = "english"   # filter recommendations to this language
top_authors = 25
top_narrators = 25
top_series = 100
```

Environment variables `AUDIPY_MARKETPLACE`, `AUDIPY_MAX_PRICE`, and
`AUDIPY_LANGUAGE` override the file. `AUDIPY_HOME` changes the data directory
(default `~/.audipy`).

## Where your data lives

| Path | Contents |
|---|---|
| `~/.audipy/auth.json` | Audible token cache (chmod 600) |
| `~/.audipy/audipy.db` | SQLite: your library + recommendations |
| `~/.audipy/config.toml` | Optional settings |
| `./reports/` | Text reports from `report --save` (git-ignored) |

None of these are committed to git.

## Development

```bash
uv run pytest        # tests
uv run ruff check    # lint
```

Built with the community [`audible`](https://pypi.org/project/audible/)
library, [Typer](https://typer.tiangolo.com/), and
[Rich](https://rich.readthedocs.io/).
