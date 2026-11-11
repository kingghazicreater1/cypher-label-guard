# Grand Beta Benchmark Images — 100 Test Images

This folder contains the **exact 100 images** used in the AV GUARDIAN Grand 100-Image Beta Benchmark.

## Naming Convention

```
{id:03d}_{source}_{original_filename}.jpg
```

| Part | Meaning |
|---|---|
| `001` ... `100` | Benchmark ID (matches `grand_beta_100_detailed_results.json`) |
| `PixabayImages` | From the PixabayImages folder (IDs 001–050) |
| `Pixabay1000` | From the Pixabay1000 folder (IDs 051–100) |

## Cross-Reference

Each image ID maps directly to a row in:
- `../scratch/grand_beta_100_detailed_results.json` — full AI output per image
- `../scratch/grand_beta_100_summary.csv` — CSV summary
- `../scratch/selected_100_manifest.json` — original file paths

## Benchmark Summary

| Metric | Result |
|---|---|
| Total images | 100 |
| Subject detection accuracy | 98/100 (98.0%) |
| Bounding box pinpoint rate | 92/100 (92.0%) |
| Zero-box cases | 6/100 (6.0%) |
| Avg confidence | 94.5% |
| Avg latency | 17.09s |

## Important Caveats

> **Ground truth was NOT independently verified.**
> The 98% accuracy figure is self-validated (model output vs filename inspection).
> This benchmark tests the Vision Chamber (Gemini Vision single-model) only.
> The 4-model Parliament consensus has NOT been benchmarked on real keys yet.

## Image Sources

All images are from [Pixabay](https://pixabay.com) — free for commercial use under the Pixabay License.
