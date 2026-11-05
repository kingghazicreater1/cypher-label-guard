# CypherLabelGuard benchmark report

- Items: 25   answered: 25   api errors: 0   unrecognised label: 0
- Wall time: 251.0s  (0.10 items/s)

## Accuracy
- **Consensus: 88.0%**  (22/25, 95% CI 70.0-95.8%)
- groq_oss120b (openai/gpt-oss-120b): 32.0%  (8/25, voted on 9)
- groq_qwen27b (qwen/qwen3.8-27b): 80.0%  (20/25, voted on 23)
- Simple majority of the provider votes: 88.0%  (22/25)

## Consensus vs best single model (groq_qwen27b (qwen/qwen3.8-27b))
- Difference: +8.0 points. Consensus sahi/single galat: 2, single sahi/consensus galat: 0, sign-test p=0.500

## Agreement vs correctness
| models agree | items | accuracy |
|---|---|---|
| 2/2 | 7 | 85.7% |
| 1/1 | 18 | 88.9% |

## Verdict
Farq statistically saaf nahi. Accuracy barabar hai, to value 'agreement score + kam review' hai, 'zyada accurate' ka claim mat karo.

Note: AG News public dataset hai aur models ne shayad dekha ho. Customer ko dikhane se pehle apne customer jaisa data (apni labels) par bhi chalao.
