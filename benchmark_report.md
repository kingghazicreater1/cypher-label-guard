# CypherLabelGuard benchmark report

- Items: 50   answered: 50   api errors: 0   unrecognised label: 6
- Wall time: 653.5s  (0.08 items/s)

## Accuracy
- **Consensus: 78.0%**  (39/50, 95% CI 64.8-87.2%)
- gemini (gemini-flash-lite-latest): 74.0%  (37/50, voted on 42)
- groq (openai/gpt-oss-120b): 16.0%  (8/50, voted on 11)
- openrouter (nvidia/nemotron-3.5-lightning:free): 12.0%  (6/50, voted on 7)
- Simple majority of the provider votes: 78.0%  (39/50)

## Matched-Subset Analysis (Zero Coverage Bias: 5 items where ALL 3 models voted)
- **Consensus: 80.0%** (4/5)
- gemini (gemini-flash-lite-latest): 80.0% (4/5)
- groq (openai/gpt-oss-120b): 80.0% (4/5)
- openrouter (nvidia/nemotron-3.5-lightning:free): 80.0% (4/5)
- Simple Majority: 80.0% (4/5)

## Quorum & Parliamentary Decisions
- **HUMAN_REVIEW_REQUIRED**: 42/50 (84.0%)
- **STALEMATE**: 7/50 (14.0%)
- **AWAITING_CONFIGURED_KEYS**: 1/50 (2.0%)

## Consensus vs best single model (gemini (gemini-flash-lite-latest))
- Difference: +4.0 points. Consensus sahi/single galat: 2, single sahi/consensus galat: 0, sign-test p=0.500

## Agreement vs correctness
| models agree | items | accuracy |
|---|---|---|
| 3/3 | 5 | 80.0% |
| 2/2 | 6 | 66.7% |
| 1/1 | 33 | 93.9% |
| 0/0 | 6 | 0.0% |

## Human-review saving (sirf non-unanimous items insan dekhe)
- Auto-accept (sab models agree): 5/50 = 10% items, in ki accuracy 80.0%
- Insan ko dikhane wale items: 45/50 = 90%
- Agar insan bilkul sahi ho to final accuracy: 98.0%

## Verdict
Farq statistically saaf nahi. Accuracy barabar hai, to value 'agreement score + kam review' hai, 'zyada accurate' ka claim mat karo.

Note: AG News public dataset hai aur models ne shayad dekha ho. Customer ko dikhane se pehle apne customer jaisa data (apni labels) par bhi chalao.
