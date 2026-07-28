# Segmentation Stability Interpretation

## Headline

The final k=5 K-Means segmentation is reproducible across random seeds. Across 30 seed refits, pairwise ARI has mean **0.997** and minimum **0.992**. Mean ARI against the canonical `random_state=42` solution is **0.998**.

This means the low silhouette score should be read as weak geometric separation, not as random or unstable customer assignment. Customer behavior is continuous, so there are few natural gaps, but the imposed k=5 partition is operationally reproducible.

## Bootstrap Perturbation

Bootstrap refits show mean ARI versus the reference partition of **0.944** on customers appearing in each resample. In the consensus sample, customer pairs from the same reference segment have mean co-assignment **0.957**, while pairs from different reference segments have mean co-assignment **0.012**.

The consensus result is the practical robustness check: customers tend to remain with the same neighboring customers under resampling, rather than drifting randomly between groups.

## Segment Meaning

After matching clusters by nearest centroid, centroid profile variability is modest: median coefficient of variation across defining profile features is **0.001** and the maximum observed coefficient of variation is **0.007**.

This supports the app's regenerate-segments workflow: label numbers may permute internally, but the business profiles represented by the segments remain consistent when clusters are matched by centroid.

## k=5 Override Versus k=2

Silhouette still prefers k=2. In this run:

- k=2 silhouette: **0.164**, pairwise seed ARI mean: **1.000**
- k=5 silhouette: **0.100**, pairwise seed ARI mean: **0.997**

The k=5 choice supports the business override: it gives more actionable differentiation than k=2, while retaining strong reproducibility. k=2 is cleaner geometrically but collapses the customer base toward a broad engaged/not-engaged split, which is less useful for targeted actions.

## Honest Framing

Clusters are not well-separated because restaurant customer behavior is continuous. The defense is not that k=5 discovers five naturally isolated islands; it is that the five operational segments are stable, reproducible, and interpretable enough to support consistent business actions.

## Generated Files

- `C:\Users\slimc\Desktop\POS1\backend\Ai models\data\final\Module 4\stability\segmentation_seed_stability.csv`
- `C:\Users\slimc\Desktop\POS1\backend\Ai models\data\final\Module 4\stability\segmentation_bootstrap_consensus.csv`
- `C:\Users\slimc\Desktop\POS1\backend\Ai models\data\final\Module 4\stability\segmentation_profile_stability.csv`
- `C:\Users\slimc\Desktop\POS1\backend\Ai models\data\final\Module 4\stability\segmentation_k2_vs_k5_comparison.csv`
- `C:\Users\slimc\Desktop\POS1\backend\Ai models\data\final\Module 4\stability\figures\segmentation_seed_ari_distribution.png`
- `C:\Users\slimc\Desktop\POS1\backend\Ai models\data\final\Module 4\stability\figures\segmentation_bootstrap_consensus_distribution.png`
- `C:\Users\slimc\Desktop\POS1\backend\Ai models\data\final\Module 4\stability\figures\segmentation_k2_vs_k5_stability_comparison.png`
