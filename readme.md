# Quran Content Generator

A terminal app (built with [Textual](https://textual.textualize.io/)) that generates short Quran recitation videos: it composes a surah title page over a background image, fetches the recitation audio for a chosen reciter and surah, and combines them into a video file.

## Features

- Generate a styled background image with the surah name overlaid (via SVGs)
- Fetch recitation audio for any surah from [mp3quran.net](https://www.mp3quran.net/)
- Combine image + audio into a finished `.mp4`
- **Browse available reciters** — press `F1` at any time to pop up a scrollable, alphabetized list of every reciter available from the API, so you don't have to guess the exact spelling to type into the reciter field

## Requirements

- Python 3.10+
- [Textual](https://pypi.org/project/textual/)
- [Requests](https://pypi.org/project/requests/)
- [Pillow](https://pypi.org/project/Pillow/)
- [CairoSVG](https://pypi.org/project/CairoSVG/)
- [MoviePy](https://pypi.org/project/moviepy/)

Install dependencies:

```bash
pip install textual requests pillow cairosvg moviepy
```

## Project structure

``` PlainText
project-root/
├── assets/            # Background images and SVG overlays (000.svg, 001.svg, ...)
│   └── svgs/
├── scripts/
│   ├── app.py                  # Main Textual app
│   ├── compose_surah_page.py   # Image composition logic
│   └── styles.tcss             # Textual CSS
├── temp/               # Scratch files during generation (cleared automatically)
└── outputs/             # Finished .mp4 files land here
```

## Usage

Run the app:

```bash
python scripts/app.py
```

1. Fill in the reciter name, surah number, and (optionally) a background image name.
   - Not sure of a reciter's exact name? Press **F1** to open a popup listing every available reciter, alphabetically sorted. Press **Esc** to close it.
2. Click **Generate!**
3. Watch the status label for progress — image generation, audio fetch, then video encoding.
4. The finished video is saved to `outputs/<surah_number>.mp4`.

## Notes

- Reciter and audio data comes from the mp3quran.net public API; availability depends on their service.
- Surah numbers must be between 1 and 114.
- Temporary files in `temp/` are cleared automatically after each run (success or failure).
