import os
from PIL import Image, ImageDraw

def create_android_toolbox_icon():
    os.makedirs("assets", exist_ok=True)
    size = (512, 512)
    # RGBA image with transparency
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Background rounded squircle
    bg_color = (24, 24, 27, 255)  # Dark zinc background
    border_color = (63, 63, 70, 255) # Border zinc
    corner_radius = 110

    # Draw rounded background
    draw.rounded_rectangle([20, 20, 492, 492], radius=corner_radius, fill=bg_color, outline=border_color, width=6)

    # 2. Subtle inner gradient or glowing accent circle behind Android
    glow_color = (16, 185, 129, 35) # Soft emerald glow
    draw.ellipse([80, 80, 432, 432], fill=glow_color)

    # 3. Android Green Color Palette
    android_green = (61, 220, 132, 255)  # Official modern Android green #3DDC84
    white = (255, 255, 255, 255)
    dark_eye = (24, 24, 27, 255)

    # Android Head Semi-circle
    # Bounding box for full circle: [126, 140, 386, 400]
    head_left = 136
    head_top = 180
    head_right = 376
    head_bottom = 420

    # Draw the dome
    draw.pieslice([head_left, head_top, head_right, head_bottom], start=180, end=360, fill=android_green)

    # Eyes
    eye_radius = 11
    # Left eye: center ~(200, 245)
    draw.ellipse([200 - eye_radius, 245 - eye_radius, 200 + eye_radius, 245 + eye_radius], fill=dark_eye)
    # Right eye: center ~(312, 245)
    draw.ellipse([312 - eye_radius, 312 - eye_radius, 312 + eye_radius, 312 + eye_radius], fill=dark_eye)

    # Antennas
    antenna_width = 12
    # Left antenna: (185, 195) to (155, 145)
    draw.line([(185, 195), (155, 140)], fill=android_green, width=antenna_width)
    draw.ellipse([155 - 6, 140 - 6, 155 + 6, 140 + 6], fill=android_green)

    # Right antenna: (327, 195) to (357, 145)
    draw.line([(327, 195), (357, 140)], fill=android_green, width=antenna_width)
    draw.ellipse([357 - 6, 140 - 6, 357 + 6, 140 + 6], fill=android_green)

    # 4. Minimalist Toolbox badge in bottom area
    # Modern floating card badge for "Toolbox"
    box_left = 150
    box_top = 320
    box_right = 362
    box_bottom = 440
    badge_bg = (37, 99, 235, 255)      # Modern Indigo/Blue #2563EB
    badge_border = (96, 165, 250, 255)  # Light blue border

    draw.rounded_rectangle([box_left, box_top, box_right, box_bottom], radius=24, fill=badge_bg, outline=badge_border, width=4)

    # Tool Handle on top of badge
    handle_color = (255, 255, 255, 230)
    draw.rounded_rectangle([216, 298, 296, 324], radius=8, outline=handle_color, width=6)

    # Tool icon (minimalist crossed wrench / lightning inside badge)
    # Wrench / bolt / lightning bolt in white
    # Draw sleek lightning bolt
    lightning_points = [
        (264, 335),
        (240, 380),
        (254, 380),
        (248, 425),
        (274, 375),
        (260, 375)
    ]
    draw.polygon(lightning_points, fill=white)

    # Save PNG
    png_path = os.path.join("assets", "icon.png")
    img.save(png_path, "PNG")

    # Save multi-resolution ICO
    ico_path = os.path.join("assets", "icon.ico")
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=icon_sizes)

    print(f"Icon generated successfully at {ico_path} and {png_path}!")

if __name__ == "__main__":
    create_android_toolbox_icon()
