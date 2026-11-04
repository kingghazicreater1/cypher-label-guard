v1 = "persistent cough [CONFIRMED]; pneumonia [RULED_OUT]; fever [NEGATED]; chills [NEGATED]; shortness of breath [NEGATED]"
# Suppose voter 2 had only 2 of the 5 items, or the tokens didn't match!
# 2 items matched (ratio 2/2 = 1.0), 3 items only had 1 voter (ratio 1/2 = 0.5)
support_ratios = [1.0, 1.0, 0.5, 0.5, 0.5]
concordance_ratio = round(sum(support_ratios) / len(support_ratios), 2)
effective_affirmative = int(round(concordance_ratio * 2))
computed_conf = round(100.0 * concordance_ratio, 1)
agree_str = f"{effective_affirmative} of 2 APIs concordant"
print("concordance_ratio:", concordance_ratio)
print("effective_affirmative:", effective_affirmative)
print("computed_conf:", computed_conf)
print("agree_str:", agree_str)
