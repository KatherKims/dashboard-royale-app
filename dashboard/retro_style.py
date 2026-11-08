"""Self-contained arcade styling; no network requests or analytics changes."""
from pathlib import Path
import base64

ASSETS = Path(__file__).resolve().parents[1] / "assets"


def stylesheet():
    font = base64.b64encode((ASSETS / "fonts/Silkscreen-Regular.ttf").read_bytes()).decode("ascii")
    css = (ASSETS / "retro.css").read_text(encoding="utf-8")
    return "<style>@font-face{font-family:Silkscreen;src:url(data:font/ttf;base64," + font + ") format('truetype');font-weight:400;font-display:swap;}" + css + "</style>"


def masthead():
    scene = base64.b64encode((ASSETS / "pixel-casino.svg").read_bytes()).decode("ascii")
    return f'''<div class="arcade-masthead">
<div><div class="arcade-kicker">The Gilded Ace / Decision Intelligence</div>
<div class="arcade-brand">ACEIQ</div>
<div class="arcade-tagline">Read the floor. Question the odds.</div>
<div class="arcade-meta"><span>Synthetic casino data</span><span>July planning: 30 days</span></div></div>
<img class="arcade-scene" src="data:image/svg+xml;base64,{scene}" alt="" aria-hidden="true"></div>'''
