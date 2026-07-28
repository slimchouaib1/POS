# Temporal Split Interpretation

The temporal split is the stricter evaluation because every training interaction occurs before the test period. This removes the main future-information path created by random row-level hold-outs.

## Degradation Pattern

The largest F1@5 drop is ALS (0.256 -> 0.177, delta -0.080). SVD and ALS are the main degradations under the shared future-item ranking interpretation.

The expected largest FM degradation did not appear in this exact run. FM full context changes from 0.170 to 0.223, and its classification AUC changes from 0.970 to 0.987. This should not be read as evidence that FM is strictly better than SVD/ALS; it is a warning that the FM ranking protocol and period-local negative-sampling task are not directly comparable to the SVD/ALS held-out-item task.

## Model Ranking

Random-split winner by F1@5: SVD (0.264). Temporal-split winner by F1@5: FM (full context) (0.223).

The SVD-over-ALS ordering held: SVD is 0.187 and ALS is 0.177. The margin remains thin, so the conclusion should be stated as SVD slightly ahead, not decisively superior.

SVD also remains above the popularity baseline: 0.187 vs 0.063. The advantage narrowed under temporal evaluation but is still about 3.0x.

## FP-Growth Stability

FP-Growth retained 223 train-mined/test-evaluated rules versus 261 full-data rules. The surviving rules are stronger: confidence moves from 23.7% to 24.8%, and lift moves from 7.37 to 7.55. This supports the interpretation that the remaining association rules capture temporally stable basket structure.

## Hybrid Recommendation Implications

The hybrid should keep FP-Growth as basket-level support, especially for item-to-item add-ons and cold-start contexts. SVD/ALS remain the cleaner evidence for personalization under the temporal task. FM remains useful for context-sensitive re-ranking, but temporal metrics should be used when describing expected deployment performance.

## FM/SVD Comparability Caveat

The FM ranking task is not identical to the SVD/ALS hold-out task. SVD and ALS rank future held-out items per user; the FM evaluation ranks items inside user/context groups built from positive rows plus period-local negative samples. FM comparisons are therefore directional and leakage-focused, not a strict apples-to-apples replacement benchmark.

## FM Temporal Classification Metrics

- FM (user+item): temporal AUC=0.640, temporal classification F1=0.458.
- FM (full context): temporal AUC=0.987, temporal classification F1=0.948.
