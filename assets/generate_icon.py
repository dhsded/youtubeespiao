"""
Icon and Logo Generator for YouTube Espião & Hunter Browser.
Generates multi-resolution .ICO and .PNG files.
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_app_icon(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Outer Circular Glow / Background
    padding = 24
    # Gradient-like layered circles
    for r in range(size // 2 - padding, 0, -4):
        alpha = int(255 * (r / (size // 2)))
        # Indigo (#6366F1) to Deep Purple (#4338CA)
        color = (
            int(99 + (67 - 99) * (1 - r / (size // 2))),
            int(102 + (56 - 102) * (1 - r / (size // 2))),
            int(241 + (202 - 241) * (1 - r / (size // 2))),
            255
        )
        draw.ellipse([size // 2 - r, size // 2 - r, size // 2 + r, size // 2 + r], fill=color)

    # 2. Cyan / Neon Radar Rings
    ring_color = (6, 182, 212, 180) # Cyan #06B6D4
    draw.ellipse([70, 70, size - 70, size - 70], outline=ring_color, width=6)
    draw.ellipse([120, 120, size - 120, size - 120], outline=(56, 189, 248, 140), width=4)

    # Radar Crosshair lines
    draw.line([(size // 2, 70), (size // 2, 120)], fill=ring_color, width=4)
    draw.line([(size // 2, size - 120), (size // 2, size - 70)], fill=ring_color, width=4)
    draw.line([(70, size // 2), (120, size // 2)], fill=ring_color, width=4)
    draw.line([(size - 120, size // 2), (size - 70, size // 2)], fill=ring_color, width=4)

    # 3. Center YouTube Play Card (Rounded Rectangle in Crimson/Red Gradient)
    card_w, card_h = 240, 160
    card_x0 = (size - card_w) // 2
    card_y0 = (size - card_h) // 2 - 10
    card_x1 = card_x0 + card_w
    card_y1 = card_y0 + card_h
    
    # Shadow
    draw.rounded_rectangle([card_x0 + 6, card_y0 + 10, card_x1 + 6, card_y1 + 10], radius=40, fill=(15, 23, 42, 160))
    # Red badge
    draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=40, fill=(239, 68, 68, 255))
    # Inner border
    draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=40, outline=(254, 202, 202, 200), width=4)

    # 4. Play Triangle (White)
    tri_x0 = size // 2 - 22
    tri_y0 = card_y0 + 40
    tri_x1 = size // 2 + 35
    tri_y1 = card_y0 + card_h // 2
    tri_y2 = card_y0 + card_h - 40
    draw.polygon([(tri_x0, tri_y0), (tri_x1, tri_y1), (tri_x0, tri_y2)], fill=(255, 255, 255, 255))

    # 5. Spy / Magnifying Glass / Target in Bottom-Right
    mag_cx = size - 135
    mag_cy = size - 135
    mag_r = 45
    # Glass outer ring (Emerald Green #10B981)
    draw.ellipse([mag_cx - mag_r, mag_cy - mag_r, mag_cx + mag_r, mag_cy + mag_r], fill=(16, 185, 129, 240), outline=(255, 255, 255, 255), width=6)
    # Target reticle
    draw.ellipse([mag_cx - 20, mag_cy - 20, mag_cx + 20, mag_cy + 20], outline=(255, 255, 255, 220), width=4)
    draw.ellipse([mag_cx - 6, mag_cy - 6, mag_cx + 6, mag_cy + 6], fill=(255, 255, 255, 255))
    # Handle
    draw.line([(mag_cx + 32, mag_cy + 32), (mag_cx + 65, mag_cy + 65)], fill=(255, 255, 255, 255), width=12)

    # Save PNG
    png_path = os.path.join(output_dir, "icon.png")
    img.save(png_path, format="PNG")

    # Save Multi-resolution ICO (256, 128, 64, 48, 32, 16)
    ico_path = os.path.join(output_dir, "icon.ico")
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=icon_sizes)

    print(f"Icon generated: {png_path} and {ico_path}")

if __name__ == "__main__":
    create_app_icon("assets")
