import argparse
import logging
from pathlib import Path
from re import compile
from typing import Optional, Tuple
from unicodedata import normalize

import requests
from mutagen import File as MutagenFile
from mutagen.flac import Picture
from mutagen.id3 import APIC
from mutagen.mp4 import MP4Cover
from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Confirm

FILETYPES = {".mp3", ".flac", ".m4a"}
HEADERS = {"User-Agent": "AlbumArtFetcher/0.1"}

console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
log = logging.getLogger("rich")

SIMPLE_CLEANUP_PATTERN = compile(r"[-_\s]+")


def embed_flac(audio, cover_data: bytes, mime_type: str):
    pic = Picture()
    pic.mime = mime_type or "image/jpeg"
    pic.desc = "front cover"
    pic.type = 3  # Cover (front)
    pic.data = cover_data
    audio.add_picture(pic)


def embed_mp3(audio, cover_data: bytes, mime_type: str):
    if audio.tags is None:
        audio.add_tags()
    audio.tags.add(
        APIC(
            encoding=3,  # UTF-8
            mime=mime_type or "image/jpeg",
            type=3,  # Cover (front)
            desc="front cover",
            data=cover_data,
        )
    )


def embed_m4a(audio, cover_data: bytes, mime_type: str):
    fmt = (
        MP4Cover.FORMAT_PNG
        if mime_type and "png" in mime_type
        else MP4Cover.FORMAT_JPEG
    )
    audio["covr"] = [MP4Cover(cover_data, imageformat=fmt)]


EMBED_HANDLERS = {".flac": embed_flac, ".mp3": embed_mp3, ".m4a": embed_m4a}

HAS_COVER = {
    ".flac": lambda a: bool(a.pictures),
    ".mp3": lambda a: bool(a.tags and a.tags.getall("APIC")),
    ".m4a": lambda a: bool(a.get("covr")),
}


# check if directory contains files with valid filetype
def _is_valid_leaf(directory: Path) -> bool:
    return any(
        file.is_file() and file.suffix.lower() in FILETYPES
        for file in directory.iterdir()
    )


def find_all_valid_leaves(directory: Path):
    for subdir in sorted(directory.iterdir()):
        if subdir.is_dir():
            if _is_valid_leaf(subdir):
                yield subdir
            else:
                yield from find_all_valid_leaves(subdir)


def get_mbid(dir: Path) -> Optional[Tuple[Optional[str], Optional[str]]]:
    log.debug(f"Trying directory {dir}")
    # might not be strictly necessary, musicbrainz has a pretty good fuzzy matcher
    artist, album = [
        SIMPLE_CLEANUP_PATTERN.sub(" ", normalize("NFKD", d).strip())
        for d in dir.parts[-2:]
    ]

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


def get_cover_art(mbid, path) -> Optional[Tuple[bytes, Optional[str]]]:
    base_url = f"https://coverartarchive.org/{path}/{mbid}"

    response = requests.get(f"{base_url}/front", headers=HEADERS)
    if response.ok:
        return (response.content, response.headers.get("Content-Type"))
    else:
        log.error(f"Error while obtaining cover art: {response.reason}")


def main():
    parser = argparse.ArgumentParser(
        prog="Album Art Fetcher",
        description="Fetches and embeds album cover art from coverartarchive.org. It expects a directory structure like <artist>/<release>/<audio files> and can be called from either the <artist> or <release> folders, respectively",
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
    dirs = find_all_valid_leaves(cwd.parent if _is_valid_leaf(cwd) else cwd)
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
                for file in d.iterdir():
                    ext = file.suffix.lower()
                    if ext not in FILETYPES:
                        continue

                    audio = MutagenFile(file)

                    if HAS_COVER[ext](audio) and not args.replace:
                        if args.prompt:
                            if not Confirm.ask(
                                f"Replace cover in {file.name}?", default=True
                            ):
                                continue
                        else:
                            log.warning("⚠️ File already contains images, skipping...")
                            continue

                    EMBED_HANDLERS[ext](audio, cover_art, mime_type or "image/jpeg")
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
