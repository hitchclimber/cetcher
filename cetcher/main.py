from mutagen.flac import FLAC, Picture
from pathlib import Path
from typing import Optional, Tuple
from rich.console import Console
from rich.logging import RichHandler
import requests
import logging
import argparse

FILETYPES = {".mp3", ".flac", ".m4a"}
HEADERS = {"User-Agent": "AlbumArtFetcher/0.1"}

console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
log = logging.getLogger("rich")


def is_valid_leaf(directory: Path) -> bool:
    return all(
        file.is_file() and file.suffix.lower() in FILETYPES
        for file in directory.iterdir()
    )


def find_all_valid_leaves(directory: Path):
    for subdir in sorted(directory.iterdir()):
        if subdir.is_dir():
            if is_valid_leaf(subdir):
                yield subdir
            else:
                yield from find_all_valid_leaves(subdir)


def get_mbid(dir: Path) -> Optional[Tuple[Optional[str], Optional[str]]]:
    artist, album = dir.parts[-2:]
    query = f'release:"{album}" AND artist:"{artist}"'
    url = f"https://musicbrainz.org/ws/2/release/?query={query}&fmt=json"
    response = requests.get(url, headers=HEADERS)
    log.info(f"🔍 Searching MBID for: {artist} - {album}")
    if response.status_code == 200:
        data = response.json()
        releases = data.get("releases", [])
        if len(releases):
            item = releases[0]
            release_group = item.get("release-group")
            rel_gr_id = release_group.get("id") if release_group else None
            rel_id = item.get("id", None)
            log.info(f"Identified IDs for query: {rel_id} and {rel_gr_id}")
            return (rel_gr_id, rel_id)
        return None
    else:
        log.error(f"Failed to fetch MBID ({response.status_code})")
    return None


def get_cover_art(mbid, path) -> Tuple[bytes, str | None] | None:
    base_url = f"https://coverartarchive.org/{path}/{mbid}"

    response = requests.get(f"{base_url}/front", headers=HEADERS)
    if response.ok:
        return (response.content, response.headers.get("Content-Type"))
    else:
        log.error(f"Error while obtaining cover art: {response.reason}")


def main():
    parser = argparse.ArgumentParser(
        prog="Album Art Fetcher",
        description="Fetches and embeds album cover art from coverartarchive.org. It expects a directory structure like <artist>/<release>/<audio files> and can be called from either <artist> or <release>",
    )
    parser.add_argument(
        "-r", "--replace", action="store_true", help="Replace existing image"
    )
    parser.add_argument(
        "-p",
        "--prompt",
        action="store_true",
        help="Interactively decide for each file if existing image should be replaced",
    )
    args = parser.parse_args()

    console.print("[bold cyan]🚀 Starting album cover fetcher...[/bold cyan]")
    cwd = Path.cwd()
    dirs = find_all_valid_leaves(cwd.parent if is_valid_leaf(cwd) else cwd)
    success = True
    for d in dirs:
        mbid = get_mbid(d)
        if mbid:
            group_id, release_id = mbid
            result = (
                get_cover_art(group_id, "release-group")
                if group_id
                else get_cover_art(release_id, "release")
            )
            if result:
                cover_art, mime_type = result
                image = Picture()
                image.mime = (
                    mime_type if mime_type else "image/jpeg"
                )  # Fallback value, need to improve this later
                image.desc = "front cover"
                image.data = cover_art
                for file in d.glob("*.flac"):
                    audio = FLAC(file)

                    if audio.pictures and not args.replace:
                        log.warning("⚠️ File already contains images, skipping...")
                        continue

                    audio.add_picture(image)
                    audio.save()
                    console.print(
                        f"[bold yellow]💾 Embedded cover on {audio.filename}![/bold yellow]"
                    )
            else:
                log.error("⛔ Errors encountered, not doing anything...")
                success = False
                break

        else:
            log.error(f"⛔ Could not find MBID for {d.name}")
            success = False
            break
    if success:
        console.print("[bold green]✅ Done![/bold green]")
    else:
        console.print("[bold red]❌Errors were encountered, check logs [/bold red]")


if __name__ == "__main__":
    main()
