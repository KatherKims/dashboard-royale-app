# Retro dashboard assets

This presentation layer was added on top of teammate upload `b972f68`.

- `retro.css`: pixel-style panels, navigation, controls, responsive layout and reduced-motion support.
- `pixel-casino.svg`: original code-drawn decorative casino scene in the existing palette. It does not depict measured floor coordinates or data.
- `fonts/Silkscreen-Regular.ttf`: Silkscreen by Jason Kottke and The Silkscreen Project Authors, distributed under the included SIL Open Font License (`fonts/OFL.txt`). Source: https://github.com/google/fonts/tree/main/ofl/silkscreen
- `dashboard/retro_style.py` embeds the local font and artwork, so visitors need no third-party font connection.

Headings use Silkscreen; body text and charts use readable monospace fonts. The existing animated Evidence Claw uses stepped movement and honors reduced-motion preferences.

Validation: all five pages rendered with Streamlit AppTest; the claw revealed a machine in the browser; desktop and 390px layouts were inspected with no page-wide horizontal overflow on the narrow layout. An AST comparison confirmed that analytical functions were unchanged; only the shared chart renderer's font settings changed. Existing analytical limitations are outside this visual update.
