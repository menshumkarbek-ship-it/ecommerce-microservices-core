"""Flat product illustrations for the seed catalog.

Each category gets a device silhouette in dark slate with a screen or
grille tinted in the category's accent. Everything is drawn on white so `process_no_bg_image` lifts
it onto a transparent card like any uploaded photo. Light fills stay at
or below #ebebeb — anything brighter than 240 would be knocked out too.
"""
from io import BytesIO

from PIL import Image, ImageChops, ImageDraw

SIZE = 700
BODY = '#1c2230'
BODY_EDGE = '#2b3344'
INK = '#11151f'
LIGHT = '#e6e8ee'
MARGIN = 60


def _tint(accent, factor):
    """Mix accent towards white by `factor` (0 = accent, 1 = white)."""
    rgb = tuple(int(accent[i:i + 2], 16) for i in (1, 3, 5))
    return tuple(int(c + (235 - c) * factor) for c in rgb)


def _paste_screen(img, draw, box, accent, radius=18):
    """Accent-filled screen with a lighter diagonal band, so every screen
    reads as glass rather than a flat swatch."""
    draw.rounded_rectangle(box, radius=radius, fill=accent)
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    band = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(band).polygon(
        [(x0 + int(w * 0.55), y0), (x1, y0), (x1, y0 + int(h * 0.45)),
         (x0 + int(w * 0.15), y1), (x0, y1), (x0, y0 + int(h * 0.85))],
        fill=(*_tint(accent, 0.25), 255))
    clip = Image.new('L', img.size, 0)
    ImageDraw.Draw(clip).rounded_rectangle(box, radius=radius, fill=255)
    img.paste(band, (0, 0), ImageChops.multiply(band.split()[3], clip))


def _phone(img, draw, accent):
    draw.rounded_rectangle((215, 70, 485, 570), radius=44, fill=BODY, outline=BODY_EDGE, width=4)
    _paste_screen(img, draw, (232, 88, 468, 552), accent, radius=32)
    draw.rounded_rectangle((305, 100, 395, 118), radius=9, fill=BODY)  # dynamic island


def _tablet(img, draw, accent):
    draw.rounded_rectangle((140, 80, 560, 560), radius=36, fill=BODY, outline=BODY_EDGE, width=4)
    _paste_screen(img, draw, (160, 100, 540, 540), accent, radius=22)
    draw.ellipse((342, 86, 358, 102), fill=BODY_EDGE)


def _laptop(img, draw, accent):
    draw.rounded_rectangle((110, 120, 590, 430), radius=22, fill=BODY, outline=BODY_EDGE, width=4)
    _paste_screen(img, draw, (130, 140, 570, 410), accent, radius=12)
    draw.polygon([(70, 432), (630, 432), (650, 468), (50, 468)], fill=BODY_EDGE)
    draw.rounded_rectangle((300, 440, 400, 452), radius=6, fill=BODY)


def _monitor(img, draw, accent):
    draw.rounded_rectangle((90, 100, 610, 420), radius=18, fill=BODY, outline=BODY_EDGE, width=4)
    _paste_screen(img, draw, (106, 116, 594, 404), accent, radius=8)
    draw.rectangle((330, 420, 370, 500), fill=BODY_EDGE)
    draw.rounded_rectangle((230, 500, 470, 530), radius=14, fill=BODY)


def _headphones(img, draw, accent):
    draw.arc((150, 90, 550, 500), start=180, end=360, fill=BODY, width=34)
    for x in (150, 550):
        draw.rounded_rectangle((x - 62, 300, x + 62, 470), radius=40, fill=BODY, outline=BODY_EDGE, width=4)
        draw.rounded_rectangle((x - 40, 322, x + 40, 448), radius=28, fill=accent)
        draw.rounded_rectangle((x - 18, 344, x + 18, 426), radius=14, fill=_tint(accent, 0.25))


def _watch(img, draw, accent):
    draw.rounded_rectangle((285, 60, 415, 170), radius=26, fill=BODY_EDGE)
    draw.rounded_rectangle((285, 470, 415, 590), radius=26, fill=BODY_EDGE)
    draw.rounded_rectangle((215, 150, 485, 490), radius=70, fill=BODY, outline=BODY_EDGE, width=4)
    _paste_screen(img, draw, (240, 176, 460, 464), accent, radius=52)
    draw.rounded_rectangle((484, 260, 500, 320), radius=6, fill=BODY_EDGE)  # crown


def _speaker(img, draw, accent):
    draw.rounded_rectangle((200, 90, 500, 560), radius=70, fill=BODY, outline=BODY_EDGE, width=4)
    draw.rounded_rectangle((240, 150, 460, 500), radius=40, fill=accent)
    for y in range(180, 480, 32):
        for x in range(265, 445, 32):
            draw.ellipse((x, y, x + 12, y + 12), fill=_tint(accent, 0.3))
    draw.rounded_rectangle((300, 112, 400, 130), radius=9, fill=BODY_EDGE)


def _powerbank(img, draw, accent):
    draw.rounded_rectangle((170, 170, 530, 470), radius=50, fill=BODY, outline=BODY_EDGE, width=4)
    draw.rounded_rectangle((200, 200, 500, 440), radius=36, fill=accent)
    bolt = [(370, 235), (300, 335), (345, 335), (330, 405), (400, 300), (355, 300)]
    draw.polygon(bolt, fill=LIGHT)


def _charger(img, draw, accent):
    draw.rounded_rectangle((220, 200, 480, 460), radius=48, fill=BODY, outline=BODY_EDGE, width=4)
    draw.rounded_rectangle((250, 230, 450, 430), radius=32, fill=accent)
    for x in (300, 380):  # wall prongs
        draw.rounded_rectangle((x, 130, x + 22, 200), radius=6, fill=BODY_EDGE)
    draw.rounded_rectangle((320, 400, 380, 414), radius=7, fill=LIGHT)  # USB-C port


def _puck(img, draw, accent):
    draw.line((350, 380, 350, 600), fill=BODY_EDGE, width=16)
    draw.ellipse((200, 150, 500, 450), fill=BODY, outline=BODY_EDGE, width=4)
    draw.ellipse((232, 182, 468, 418), fill=accent)
    draw.ellipse((300, 250, 400, 350), fill=BODY, outline=_tint(accent, 0.3), width=6)


def _mouse(img, draw, accent):
    draw.rounded_rectangle((235, 120, 465, 560), radius=115, fill=BODY, outline=BODY_EDGE, width=4)
    draw.pieslice((235, 120, 465, 350), start=180, end=360, fill=accent)
    draw.line((350, 120, 350, 300), fill=BODY_EDGE, width=6)
    draw.rounded_rectangle((338, 200, 362, 260), radius=12, fill=LIGHT)  # wheel


def _keyboard(img, draw, accent):
    draw.rounded_rectangle((70, 230, 630, 470), radius=30, fill=BODY, outline=BODY_EDGE, width=4)
    key = _tint(accent, 0.1)
    for row, y in enumerate((262, 314, 366)):
        offset = row * 14
        for x in range(100 + offset, 600 - offset, 46):
            draw.rounded_rectangle((x, y, x + 36, y + 36), radius=6, fill=key)
    draw.rounded_rectangle((180, 418, 520, 452), radius=8, fill=key)  # space bar


def _drive(img, draw, accent):
    draw.rounded_rectangle((200, 110, 500, 590), radius=44, fill=BODY, outline=BODY_EDGE, width=4)
    draw.rounded_rectangle((230, 140, 470, 400), radius=28, fill=accent)
    draw.rounded_rectangle((260, 440, 440, 520), radius=14, fill=LIGHT)  # label
    draw.rounded_rectangle((325, 536, 375, 550), radius=7, fill=BODY_EDGE)  # port


def _hub(img, draw, accent):
    draw.line((90, 340, 30, 340), fill=BODY_EDGE, width=18)
    draw.rounded_rectangle((90, 270, 610, 410), radius=28, fill=BODY, outline=BODY_EDGE, width=4)
    draw.rounded_rectangle((110, 288, 590, 392), radius=18, fill=accent)
    for x in range(150, 560, 82):  # ports along the front edge
        draw.rounded_rectangle((x, 392, x + 50, 412), radius=4, fill=LIGHT)


SHAPES = {
    'phone': _phone, 'tablet': _tablet, 'laptop': _laptop, 'monitor': _monitor,
    'headphones': _headphones, 'watch': _watch, 'speaker': _speaker,
    'powerbank': _powerbank, 'charger': _charger, 'puck': _puck, 'mouse': _mouse,
    'keyboard': _keyboard, 'drive': _drive, 'hub': _hub,
}


def render_product_image(shape, brand, name, accent):
    """Return PNG bytes of a 700x700 illustration for one product.

    The catalog card already prints brand and name under the photo, so the
    image is just the device, scaled to fill the frame the way a cut-out
    product shot would.
    """
    img = Image.new('RGBA', (SIZE, SIZE), (255, 255, 255, 255))
    SHAPES[shape](img, ImageDraw.Draw(img), accent)

    # Crop to the drawing, then fit it into the frame with an even margin.
    bbox = ImageChops.difference(img.convert('RGB'), Image.new('RGB', img.size, 'white')).getbbox()
    device = img.crop(bbox)
    scale = (SIZE - 2 * MARGIN) / max(device.size)
    device = device.resize((round(device.width * scale), round(device.height * scale)), Image.Resampling.LANCZOS)
    framed = Image.new('RGBA', (SIZE, SIZE), (255, 255, 255, 255))
    framed.paste(device, ((SIZE - device.width) // 2, (SIZE - device.height) // 2), device)

    buffer = BytesIO()
    framed.save(buffer, format='PNG')
    return buffer.getvalue()
