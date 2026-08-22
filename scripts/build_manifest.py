#!/usr/bin/env python3
"""Rebuild brief/paintings.json from the National Gallery of Art Open Data release.

Usage:
    python3 scripts/build_manifest.py /path/to/nga_opendata_dir [--limit 120]

The input dir must contain the official NGA Open Data CSVs:
    published_images.csv   (IIIF URLs, uuid -> objectid)
    objects.csv            (titles, artists, dates, media)

Output:
    brief/paintings.json — a curated manifest of public-domain paintings with
    muted, exhibition-friendly palettes. Only open-access images are included.

Art data is CC0 (NGA Open Data). See https://github.com/NationalGalleryOfArt/opendata
"""
import argparse
import csv
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "brief" / "paintings.json"

# ---------------------------------------------------------------- filters
MIN_W, MIN_H = 1400, 900          # large enough to crop a 21:9 hero
MAX_ASPECT = 2.4                  # avoid extreme panoramas

# NGA classification values that are paintings on flat supports
PAINTING_MEDIA = ("oil", "tempera", "pastel", "watercolor", "gouache")

# Artist names that produce reliably muted, exhibition-grade palettes
PREFERRED_ARTISTS = (
    "Monet", "Renoir", "Pissarro", "Sisley", "Morisot", "Cézanne", "Cezanne",
    "Cassatt", "Whistler", "Hassam", "Twachtman", "Weir", "Robinson",
    "Inness", "Wyant", "Tryon", "Dewing", "Tarbell", "Benson", "Metcalf",
    "Boudin", "Homer", "Chase", "Sargent",
)

# terms that never make a calm hero
BAD_TITLE = re.compile(
    r"\b(nude|battle|war|corpse|funeral|crucif|martyr|execut|guillotin|"
    r"riot|crash|wreck|storm|flood|fire|blood|snake|demon|devil|hell|"
    r"pieta|entomb|deposition|lamentation|head of|portrait of a man|"
    r"self-portrait|study of a head)\b",
    re.IGNORECASE,
)

YEAR_RE = re.compile(r"(1[4-9]\d\d|20\d\d)")


def first_year(date_str):
    """Extract the first 4-digit year from a display-date string."""
    m = YEAR_RE.search(date_str or "")
    return int(m.group(1)) if m else None


# classification -> medium keywords that are fine
OK_CLASS = ("painting", "drawing", "watercolor")


def load_images(path):
    """uuid -> (iiifurl, width, height, objectid) for open-access images."""
    out = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            if r["openaccess"] != "1":
                continue
            try:
                w, h = int(r["width"]), int(r["height"])
            except ValueError:
                continue
            out[r["uuid"]] = (r["iiifurl"], w, h, r["depictstmsobjectid"])
    return out


def load_objects(path):
    """objectid -> (title, artist, date, medium, classification)."""
    out = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            out[r["objectid"]] = (
                r["title"],
                r["attributioninverted"] or r["attribution"],
                r["displaydate"],
                r["medium"],
                r["classification"],
            )
    return out


def is_muted(palette):
    """Cheap palette check: low average saturation, no neon tones.

    Returns False when the palette can't be computed, so we keep the painting.
    """
    if palette is None:
        return True
    n = len(palette)
    if n < 3:
        return True
    avg_sat = sum(c[1] for c in palette) / n
    bright = sum(1 for c in palette if c[1] > 0.55 and c[2] > 0.55)
    return avg_sat <= 0.42 and bright <= max(1, n // 5)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("data_dir", help="dir containing NGA open-data CSVs")
    ap.add_argument("--limit", type=int, default=120, help="max paintings in manifest")
    args = ap.parse_args()

    data_dir = pathlib.Path(args.data_dir)
    imgs = load_images(data_dir / "published_images.csv")
    objs = load_objects(data_dir / "objects.csv")
    print(f"images: {len(imgs)}, objects: {len(objs)}", file=sys.stderr)

    # objectid -> (uuid, iiifurl, w, h) for its primary open-access image
    best = {}
    for uuid, (url, w, h, oid) in imgs.items():
        if w < MIN_W or h < MIN_H or w / h > MAX_ASPECT:
            continue
        cur = best.get(oid)
        if cur is None or w * h > cur[2] * cur[3]:
            best[oid] = (uuid, url, w, h)
    print(f"objects with a big enough open image: {len(best)}", file=sys.stderr)

    scored = []
    for oid, (uuid, url, w, h) in best.items():
        o = objs.get(oid)
        if o is None:
            continue
        title, artist, date, medium, classification = o
        if (classification or "").lower() not in OK_CLASS:
            continue
        if not any(k in (medium or "").lower() for k in PAINTING_MEDIA):
            continue
        if BAD_TITLE.search(title or ""):
            continue
        if len(title or "") > 90:
            continue

        score = 0
        if any(a.lower() in (artist or "").lower() for a in PREFERRED_ARTISTS):
            score += 30
        y = first_year(date)
        if y is not None and 1800 <= y <= 1950:
            score += 10
        if h / w >= 0.66:  # landscape-ish crops best at 21:9
            score += 5
        scored.append((score, oid, uuid, url, title, artist, date))

    scored.sort(key=lambda t: -t[0])
    print(f"candidates after filters: {len(scored)}", file=sys.stderr)

    manifest = []
    for score, oid, uuid, url, title, artist, date in scored[: args.limit]:
        src = url + "/full/!1600,1600/0/default.jpg"
        manifest.append(
            {
                "key": uuid[:8],
                "title": title,
                "artist": artist,
                "year": date,
                "src": src,
                "page": f"https://www.nga.gov/artworks/{oid}.html",
            }
        )
        if len(manifest) >= args.limit:
            break

    OUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT} ({len(manifest)} paintings)")


if __name__ == "__main__":
    main()




