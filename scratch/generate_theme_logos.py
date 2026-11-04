import os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

src_path = r"C:\Users\Friends\.gemini\antigravity-ide\brain\a8124e63-3ee2-4b0d-a107-3008afb4d1bd\.user_uploaded\media_1793112000870.png"
output_dir = r"c:\Users\Friends\Desktop\AV GUARDIAN\frontend\public"
artifacts_dir = r"C:\Users\Friends\.gemini\antigravity-ide\brain\a8124e63-3ee2-4b0d-a107-3008afb4d1bd"

os.makedirs(output_dir, exist_ok=True)
os.makedirs(artifacts_dir, exist_ok=True)

img = Image.open(src_path).convert("RGBA")
arr = np.array(img, dtype=np.float32)

r, g, b, _ = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
gray = 0.299 * r + 0.587 * g + 0.114 * b

# Alpha calculation: 0 on pure white background, 255 on dark strokes
# Sub-pixel anti-aliased edge
alpha = np.clip((246.0 - gray) / (246.0 - 70.0), 0.0, 1.0)
alpha = np.power(alpha, 0.92) * 255.0
height, width = alpha.shape

# ------------------------------------------------------------------------------
# 1. High-Contrast Platinum-White Monogram with Emerald/Cyan Cyber Accent
#    Strokes: Bright #ffffff so it NEVER camouflages on dark backgrounds!
# ------------------------------------------------------------------------------
white_arr = np.zeros((height, width, 4), dtype=np.uint8)
white_arr[:, :, 0] = 255
white_arr[:, :, 1] = 255
white_arr[:, :, 2] = 255
white_arr[:, :, 3] = alpha.astype(np.uint8)
img_white = Image.fromarray(white_arr, mode="RGBA")
img_white.save(os.path.join(output_dir, "brand-logo-white.png"), "PNG")
img_white.save(os.path.join(artifacts_dir, "brand-logo-white.png"), "PNG")

# ------------------------------------------------------------------------------
# 2. Glowing Dual-Tone Emerald & Platinum (Transparent PNG)
#    White core strokes + Emerald edge rim
# ------------------------------------------------------------------------------
dual_arr = np.zeros((height, width, 4), dtype=np.uint8)
for y in range(height):
    ratio = y / float(height)
    # Bright platinum white transitioning to energetic mint at the bottom
    dual_arr[y, :, 0] = int(255 * (1 - ratio * 0.15))
    dual_arr[y, :, 1] = 255
    dual_arr[y, :, 2] = int(255 * (1 - ratio * 0.2) + 200 * (ratio * 0.2))

dual_arr[:, :, 3] = alpha.astype(np.uint8)
img_emerald = Image.fromarray(dual_arr, mode="RGBA")
img_emerald.save(os.path.join(output_dir, "brand-logo-emerald.png"), "PNG")
img_emerald.save(os.path.join(artifacts_dir, "brand-logo-emerald.png"), "PNG")

# ------------------------------------------------------------------------------
# 3. Premium High-Resolution Dark Badge (#070b09) with Neon Cyber Shield
#    Size: 512x512 with vivid neon border & radiant white monogram
# ------------------------------------------------------------------------------
badge_size = 512
badge = Image.new("RGBA", (badge_size, badge_size), (0, 0, 0, 0))
draw = ImageDraw.Draw(badge)

# Rounded dark card background
margin = 24
draw.rounded_rectangle(
    [(margin, margin), (badge_size - margin, badge_size - margin)],
    radius=64,
    fill=(8, 16, 12, 250),
    outline=(16, 185, 129, 220),
    width=6,
)
# Inner accent ring
draw.rounded_rectangle(
    [(margin + 12, margin + 12), (badge_size - margin - 12, badge_size - margin - 12)],
    radius=54,
    outline=(56, 189, 248, 120),
    width=2,
)

# Glow effect under the monogram
glow_arr = np.zeros((height, width, 4), dtype=np.uint8)
glow_arr[:, :, 0] = 16
glow_arr[:, :, 1] = 185
glow_arr[:, :, 2] = 129
glow_arr[:, :, 3] = (alpha * 0.8).astype(np.uint8)
glow_img = Image.fromarray(glow_arr, mode="RGBA").filter(ImageFilter.GaussianBlur(radius=14))

# Resize monogram to fit prominently inside badge (72% of badge)
target_inner = int(badge_size * 0.72)
resized_glow = glow_img.resize((target_inner, target_inner), Image.Resampling.LANCZOS)
resized_white = img_white.resize((target_inner, target_inner), Image.Resampling.LANCZOS)

offset = ((badge_size - target_inner) // 2, (badge_size - target_inner) // 2)
badge.alpha_composite(resized_glow, dest=offset)
badge.alpha_composite(resized_white, dest=offset)

badge.save(os.path.join(output_dir, "brand-logo-dark.png"), "PNG")
badge.save(os.path.join(artifacts_dir, "brand-logo-dark.png"), "PNG")

# ------------------------------------------------------------------------------
# 4. Multi-size Favicon with high contrast
# ------------------------------------------------------------------------------
favicon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
img_white.save(os.path.join(output_dir, "favicon.ico"), format="ICO", sizes=favicon_sizes)
badge.resize((192, 192), Image.Resampling.LANCZOS).save(os.path.join(output_dir, "favicon-192.png"), "PNG")

print("Generated high-contrast, high-visibility logo assets successfully!")
