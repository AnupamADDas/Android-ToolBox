"""Generate the original Android Toolbox app mark and Windows icon sizes."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ASSETS = Path(__file__).resolve().parents[1] / "assets"
ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def create_android_toolbox_icon():
    ASSETS.mkdir(exist_ok=True)
    # Draw large, then downsample for antialiased edges at every shell size.
    image = Image.new("RGBA", (1024, 1024))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((32, 32, 992, 992), radius=216, fill="#101c2c",
                           outline="#32485d", width=8)
    glow = Image.new("RGBA", image.size)
    ImageDraw.Draw(glow).ellipse((180, 150, 830, 850), fill=(36, 174, 171, 48))
    glow = glow.filter(ImageFilter.GaussianBlur(72))
    # Keep lighting within the opaque squircle.
    glow.putalpha(Image.composite(glow.getchannel("A"), Image.new("L", image.size), image.getchannel("A")))
    image = Image.alpha_composite(image, glow)
    draw = ImageDraw.Draw(image)
    # Phone + a small toolbox. An original utility mark, not an Android logo.
    draw.rounded_rectangle((260, 170, 696, 828), radius=76, fill="#152b3b",
                           outline="#53d9cf", width=40)
    draw.rounded_rectangle((401, 213, 555, 237), radius=12, fill="#53d9cf")
    draw.line(((365, 370), (435, 435), (365, 500)), fill="#e7f8fb", width=32,
              joint="curve")
    draw.rounded_rectangle((467, 482, 573, 510), radius=12, fill="#e7f8fb")
    draw.rounded_rectangle((420, 754, 536, 776), radius=11, fill="#53d9cf")
    draw.rounded_rectangle((600, 566, 738, 648), radius=24, fill="#101c2c",
                           outline="#f6c177", width=24)
    draw.rounded_rectangle((516, 626, 834, 842), radius=42, fill="#f6c177",
                           outline="#101c2c", width=14)
    draw.line((536, 712, 814, 712), fill="#101c2c", width=14)
    draw.rounded_rectangle((652, 686, 698, 746), radius=10, fill="#101c2c")
    image = image.resize((512, 512), Image.Resampling.LANCZOS)
    image.save(ASSETS / "icon.png")
    image.save(ASSETS / "icon.ico", sizes=[(size, size) for size in ICON_SIZES])

    # Installer header artwork; the actual app mark stays the same.
    header = Image.new("RGB", (128, 128), "#101c2c")
    mark = image.resize((112, 112), Image.Resampling.LANCZOS)
    header.paste(mark, (8, 8), mark)
    header.save(ASSETS / "installer-header.bmp")
    print(f"Generated {ASSETS / 'icon.ico'} ({len(ICON_SIZES)} resolutions)")


if __name__ == "__main__":
    create_android_toolbox_icon()
