import json, shutil, os, sys

manifest_path = r"c:\Users\Friends\Desktop\AV GUARDIAN\scratch\selected_100_manifest.json"
dest_folder = r"c:\Users\Friends\Desktop\AV GUARDIAN\benchmark_images"

os.makedirs(dest_folder, exist_ok=True)

with open(manifest_path) as f:
    manifest = json.load(f)

print(f"Copying {len(manifest)} images to {dest_folder}...")
missing = []
copied = 0

for item in manifest:
    src = item['path']
    img_id = item['id']
    source = item['source']
    filename = item['filename']
    # rename to id-prefixed for easy reference: 001_PixabayImages_originalname.jpg
    dest_name = f"{img_id:03d}_{source}_{filename}"
    dest_path = os.path.join(dest_folder, dest_name)
    
    if os.path.exists(src):
        shutil.copy2(src, dest_path)
        copied += 1
        print(f"  [{img_id:03d}] OK -> {dest_name[:60]}...")
    else:
        missing.append(src)
        print(f"  [{img_id:03d}] MISSING: {src}")

print(f"\nDone: {copied}/100 copied, {len(missing)} missing")
if missing:
    print("Missing files:")
    for m in missing:
        print(f"  {m}")

# Check total size
total_size = sum(os.path.getsize(os.path.join(dest_folder, f)) for f in os.listdir(dest_folder))
print(f"Total size: {total_size/1024/1024:.1f} MB")
