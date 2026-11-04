import os
import sys
import time
import hashlib
from PIL import Image

sys.path.insert(0, os.path.abspath("."))
from features.cat_f_multimodal.feat_35_vision_connector.feature import analyze_raster_buffer, detect_visual_entities
from features.cat_f_multimodal.feat_35_vision_connector.specimen_normalizer import SpecimenNormalizer

folder = r"c:\Users\Friends\Desktop\Pixabay1000"
files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))][:10]

t0 = time.time()
for idx, f in enumerate(files):
    fpath = os.path.join(folder, f)
    with open(fpath, "rb") as fp:
        raw_bytes = fp.read()
    
    # 1. Raster analysis
    raster = analyze_raster_buffer(raw_bytes)
    # 2. Entity detection
    entities = detect_visual_entities(raw_bytes, context_hints=f)
    # 3. Lineage hash
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    
    # 4. Ontology classification
    norm_living = SpecimenNormalizer.normalize_is_living(entities[0] if entities else "General Scene", entities)
    norm_human, _ = SpecimenNormalizer.normalize_human_presence(entities[0] if entities else "Scene", entities)
    norm_edible = any(e.lower() in SpecimenNormalizer.EDIBLE_ITEMS for e in entities)
    
    print(f"[{idx+1}] {f[:20]}... | Color: {raster.get('detected_color')} | Entities: {entities} | Living: {norm_living} | Human: {norm_human} | Edible: {norm_edible} | SHA: {sha256[:10]}...")

elapsed = time.time() - t0
print(f"\n10 images processed in {elapsed:.3f}s ({elapsed/10*1000:.1f}ms per image)")
