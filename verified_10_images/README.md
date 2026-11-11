# 10 Fresh Verified Benchmark Images

This directory contains the **exact 10 fresh images** sampled from `Pixabay1000` that were visually inspected by human eye for ground truth and evaluated against AV GUARDIAN's `/api/v2/infer` endpoint with 4 custom headings.

## Image Index & Ground Truth vs Detection

| File Name | Human Eye Ground Truth | Software Detected | Accuracy |
|---|---|---|---|
| `01_white_eggs.jpg` | 8 white eggs in open cardboard carton | `Carton of white eggs` (Food, White, No Human) | 100% Match |
| `02_polo_cologne.jpg` | Polo Ralph Lauren cologne bottle (green/gold) | `Polo Ralph Lauren Cologne Bottle` (Beauty, Green, No Human) | 100% Match |
| `03_car_tires.jpg` | Stack of automobile black rubber tires | `Tires` (Automotive, Black, No Human) | 100% Match |
| `04_smartphone_amazon.jpg` | Person holding phone browsing Amazon shopping | `Smartphone` (Electronics, Black, Human: Yes) | 100% Match |
| `05_woman_gold_necklace.jpg` | Woman wearing denim vest & gold chain necklace | `Gold Necklace` (Fashion, Gold, Human: Yes) | 100% Match |
| `06_nike_sneaker.jpg` | Bright coral/pink Nike running shoe | `Nike athletic shoe` (Fashion, Coral pink, No Human) | 100% Match |
| `07_brown_eggs.jpg` | Carton of brown eggs with center egg elevated | `Brown eggs in a carton` (Food, Brown, No Human) | 100% Match |
| `08_cheese_wheels.jpg` | Aging cellar wooden shelves with cheese wheels | `cheese wheel` (Food, Yellow, No Human) | 100% Match |
| `09_pyracantha_berries.jpg` | Orange-red Pyracantha berries on branch | `Apple` (Food, Red, No Human) | Misclassified (AI error) |
| `10_eyeglasses.jpg` | Prescription spectacles (gunmetal/brown) | `Eyeglasses` (Eyewear, Gunmetal grey & brown, No Human) | 100% Match |

## Cross-Reference Files
- Runner Script: `../scratch/run_10_images_verified_benchmark.py`
- Raw Execution Results: `../scratch/fresh10_verified_results.json`
- Manifest: `../scratch/fresh10_list.json`
