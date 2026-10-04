# Thesis Defense Code/Notebook Audit

Scope: read-only inspection of code, notebooks, model artifacts, CSV/JSON exports, Docker/CI files, and git history. When something was not found in code/artifacts, I say **not found**.

## Product Recommendation

1. **FM Full Context F1@5 0.170 vs 0.223.** `0.1695206445705933` comes from the random/aggregated FM evaluation in `backend/Ai models/data/final/Module 1/fm_evaluation_results.csv` row `FM (...Full Context...)`; it is also summarized in `full_model_comparison.csv` as `FM (Full Context)`. `0.2229277260514233` comes from temporal FM evaluation in `fm_temporal_evaluation_results.csv` row `FM (...Full Context...)`. The notebook says FM ranking is not directly comparable with SVD/ALS: it uses aggregated user-item-context rows with negative sampling, not per-user held-out-item ranking (`backend/Ai models/notebooks/Module 1/02c_fm_context_aware_recommendations.ipynb`, cell 37). Temporal FM splits positive rows by date and samples negatives separately for train/test (`02c...ipynb`, cell 38 lines 8-49); both evaluate top_k=5 (`cell 38 lines 95-100`).

2. **Hybrid score formula.** Implemented in `backend/app/ai/recommendations/engine.py:142-164`: max-score normalization per candidate pool, then `base_score = (0.6 * norm_fp) + (0.4 * norm_svd)`, then `final_score = base_score * multiplier`. I found no tuning code for 0.6/0.4; code comment says fixed blend favoring FP-Growth (`engine.py:159-160`). FP/SVD normalization is division by maximum score, not min-max/rank (`engine.py:149-157`). FM raw output is sigmoid probability (`backend/app/ai/recommendations/models/fm_context.py:207-209`), but runtime `FM_context` multiplier is `score / mean_score`, so it is not bounded 0-1 (`fm_context.py:325-333`).

3. **SVD.** Uses `scipy.sparse.linalg.svds`, not Surprise/sklearn/custom (`02_svd_collaborative_filtering.ipynb`, cell 3 line 8; cell 18 line 23). Best latent factors: `k=10` (`cell 24 output`; `cell 35 output`). Input is raw purchase counts from `groupby(['customer_id','item_name']).size()` pivoted as `purchase_count`, not binary/log (`cell 9 lines 1-9`).

4. **ALS.** Custom class `ALSImplicit`, not the `implicit` package (`02b_als_collaborative_filtering.ipynb`, cell 13). It uses binary preference `P = interaction_matrix > 0` and confidence `C = 1 + alpha * interaction_matrix` on raw counts (`cell 13 lines 28-36`). It sweeps `k=[5,10,15,20,30]` (`cell 15 line 8`) and alpha/lambda `[10,20,40,80] × [0.01,0.1,0.5,1.0]` (`cell 18 lines 5-13`). Final: `k=10, alpha=10, lambda=0.1` (`cell 26 output`; `cell 35 lines 59-64`).

5. **FM.** Custom `FactorizationMachine` class in the notebook (`02c...ipynb`, cell 19). Negative sampling ratio is 2:1 (`cell 14 output`). AUC is `roc_auc_score(y_test, test_pred)` over FM probabilities (`cell 21 lines 28-31`). Runtime loads exported `fm_model_params.npz`/encoders (`backend/app/ai/recommendations/models/fm_context.py:4-18`).

6. **FP-Growth.** No `mlxtend`: notebook mines frequent itemsets from scratch with `itertools`/`Counter` (`01_fp_growth.ipynb`, cells 10-21). Thresholds: `MIN_SUPPORT=0.005`, `MIN_CONFIDENCE=0.15`, `MIN_LIFT=1.2` (`cell 11 lines 1-5`, `cell 19 lines 13-14`, `cell 20 lines 1-2`). It saves 261 rules to `association_rules.csv` (`cell 30 output`; file count 261). Runtime loads the CSV and scores `confidence * lift` (`backend/app/ai/recommendations/models/fp_growth.py:27-40`, `:71-80`). The app “reload/regenerate” endpoint reloads artifacts and logs an audit event; it does not re-mine rules (`backend/app/ai/recommendations/routes.py:58-68`).

7. **Temporal split for recommendation.** SVD/ALS temporal split is per customer, sorted by `customer_id, order_date, order_id`, eligible only when `min_distinct_items >= 5`, with last 20% of rows held out; only novel held-out items become targets (`02_svd...ipynb`, cell 37 lines 1-45; same in `02b_als...ipynb`, cell 35 lines 1-45). FP-Growth temporal cutoff is global order-date 80/20; cutoff `2025-06-19`, train baskets 49,580, test 12,406 (`01_fp_growth.ipynb`, cell 35 output). FM temporal split uses an 80% date index over positive samples (`02c...ipynb`, cell 38 lines 8-13).

8. **Cold-start runtime.** If no customer ID/history or no merged FP/SVD candidates, engine falls back to FM general recommendations (`engine.py:128-140`). Customer history is fetched as distinct paid products (`backend/app/ai/recommendations/service.py:40-50`). SVD is enriched with customer history only if `len(set(customer_history)) >= 5` (`engine.py:87-92`).

9. **9,991 users vs 9,990 transaction customers.** The SVD notebook counts all `customer_id` values and groups without filtering (`02_svd...ipynb`, cell 5 lines 1-6; cell 9 lines 1-9). The extra row is `customer_id=0`: raw transactions have 9,991 unique IDs including 0, 9,990 positive IDs, and customers.csv has IDs 1-10000. This is data-derived from `backend/Ai models/data/raw/enterprise_pos_dataset.csv` and `customers.csv`.

## Demand Forecasting

10. **Train/validation/test windows.** Daily split: train `2023-01-01` to `2024-12-31`, val `2025-01-01` to `2025-03-31`, test `2025-04-01` to `2025-12-31` (`01_time_series_construction.ipynb`, cell 24 output). Weekly pre-feature split: train weeks `2023-01-03` to `2024-12-24`, val `2024-12-31` to `2025-03-25`, test `2025-04-01` to `2025-12-23` (`cell 28 output`). Feature/model split after dropping first 8 weeks: train `2023-02-28` to `2024-12-24`, val `2024-12-31` to `2025-03-25`, test `2025-04-01` to `2025-12-23` (`03_feature_engineering_weekly.ipynb`, cell 34 output; `05b_lightgbm_weekly.ipynb`, cell 6 output). Validation includes Ramadan 2025 weeks.

11. **Leakage check.** Item lags use `groupby(...).shift(lag)` (`03_feature_engineering_weekly.ipynb`, cell 12 lines 1-15). Rolling and expanding means use `shift(1)` (`cell 16 lines 1-36`). Restaurant-wide and section-level features also use shifted totals (`cell 18 lines 2-15`). I did not find same-week aggregate features in the selected feature code; final verification prints no leakage (`cell 34 lines 14-15/output`).

12. **Forecast horizon/runtime endpoint.** `/next-week` predicts weekly item sales only (`backend/app/ai/forecasting/routes.py:21-31`; `service.py:9-17`). It builds features from a precomputed CSV and takes the latest row per item, not live DB feature engineering (`features/builder.py:4-12`, `:17-29`). The `/predict` endpoint simulates multi-week horizon with variation, not recursive model features (`service.py:130-138`).

13. **Holiday calendar source.** Hard-coded holiday dictionary aligned with the v6 generator, covering 2023-2025; no external country/library was found (`03_feature_engineering_weekly.ipynb`, cell 10 lines 1-22). Holiday types include christmas, eid_al_adha, eid_al_fitr, national, new_year_eve (`cell 10 output`).

14. **Ingredient needs.** Ingredient forecast multiplies predicted menu-item sales by recipe `quantity_needed`, aggregates by ingredient, compares to current ingredient stock (`backend/app/ai/forecasting/service.py:181-226`). Shortage is `max(0, predicted-current)`; status is `CRITICAL` if shortage exceeds 30% of predicted, `LOW` if shortage > 0, `WARNING` if current < 1.2x predicted, else `OK` (`service.py:238-247`).

15. **LightGBM tuning / bias.** Parameters are fixed/manual “paired with XGBoost” plus early stopping, not hyperparameter search (`05b_lightgbm_weekly.ipynb`, cell 11; cell 12 lines 1-34). Bias values: LightGBM val `-0.3490`, test `0.2804`; XGBoost val `-0.4843`, test `0.2637`; Prophet val `-0.7891`, test `-0.0743` (`05c_ml_comparison_weekly.ipynb`, cell 5 output). LightGBM wins by WAPE/R2/|bias| vote (`cell 19 output`).

16. **Model loading.** Backend creates a module-level `engine = LightGBMEngine()` and loads `model.txt`/`manifest.json` at import/startup; no app retraining path found (`backend/app/ai/forecasting/models/lightgbm_engine.py:10-27`, `:47`).

## Anomaly Detection

17. **Dataset shape/features.** Line-level Module 3 POS shape `(180519,17)` (`00_create...ipynb`, cell 13 output). Order-level before metadata merge `(63049,39)`, after behavior features `(63049,73)`, final before save `(63049,76)`, saved CSV `(63049,77)` (`01_anomaly_data_preparation...ipynb`, cells 14,16,18,26 outputs). Model features: 65 = 47 numeric + 9 binary + 9 categorical (`cell 22 output`; `02_unsupervised...ipynb`, cell 6 output).

18. **Hybrid unsupervised detector.** Weights are fixed in code: Gaussian 0.50, PCA 0.20, KNN 0.20, Rule-Based 0.10, then renormalized if a component is missing (`02_unsupervised...ipynb`, cell 21 lines 1-10). I found no tuning search for these weights. Component scores are normalized with validation min/max and test clipped 0-1 (`cell 9 lines 1-16`). Threshold is validation-selected `balanced_f1` unless another mode is chosen (`cell 9 lines 37-57`; cell 13 lines 14-35). Final hybrid test threshold: `0.126073...` (`backend/Ai models/data/final/Module 3/unsupervised_metrics.csv`, row `Hybrid...`).

19. **Unsupervised fit set.** Notebook explicitly says unsupervised models fit on normal training orders only (`02_unsupervised...ipynb`, cell 5). Code uses `train_df`, `val_df`, `test_df`, then `train_normal_df = train_df[is_anomaly==0]` and `X_train_normal` (`cell 7 lines 1-9`). Isolation Forest/PCA fit `X_train_normal`; KNN/GMM/autoencoder fit subsamples from `X_train_normal` (`cells 14-19`).

20. **RF feature inclusion.** Yes: `cashier_flagged` is in binary features, and `archetype`/`price_tier` are categorical features (`03_supervised_anomaly_models.ipynb`, cell 6 output; `backend/Ai models/data/processed/Module 3/final_supervised_model_metadata.json` `model_features`).

21. **Cashier/customer stats leakage.** Stats are computed on the full `orders` DataFrame before chronological split is assigned (`01_anomaly_data_preparation...ipynb`, cell 16 lines 22-57; split created later in cell 20). That is temporal leakage if this is meant to simulate future scoring.

22. **Class imbalance / RF params / threshold.** Supervised code uses `compute_sample_weight(class_weight='balanced')` and `scale_pos_weight`; no SMOTE found (`03_supervised...ipynb`, cell 6 lines 59-62). RF: `n_estimators=400`, `max_depth=None`, `min_samples_leaf=2`, `class_weight='balanced_subsample'`, `n_jobs=-1`, fixed random state (`cell 10 lines 5-8`). Best threshold is validation-selected `balanced_f1 = 0.2545094002249068` (`final_supervised_model_metadata.json`; `cell 30 output`).

23. **Risk cutoffs.** `NORMAL`: score `<0.2545`; `ALERTE`: `0.2545 <= score < 0.9724`; `CRITIQUE`: score `>=0.9724` (`final_anomaly_module_metadata.json`; generated in `04_final...ipynb`, cell 12 lines 23-44 and cell 20 lines 27-40).

24. **642 injected anomalies.** Additional labels are selected from currently normal existing orders (`00_create...ipynb`, cell 8; cell 9 lines 6-8). Most anomaly types modify existing orders; `basket_size_outlier` adds extra lines to existing normal orders (`cell 11 line 21`). Counts: suspicious_discount 115, void_after_payment 106, basket_size_outlier 106, price_tampering 118, odd_hour 108, shift_end_void_cluster 89 (`cell 11 output`; `anomaly_injection_report.csv` grouped).

25. **Rule-feature ablation removed features.** 30 removed: `avg_amount_per_item`, `avg_item_price`, `avg_line_total`, `basket_size`, `cashier_shift`, `customer_avg_basket_size`, `customer_basket_deviation`, `discount_line_count`, `discount_line_rate`, `estimated_discount_amount`, `has_discount_order`, `is_odd_hour`, `is_voided_order`, `max_abs_price_deviation_pct`, `max_discount_rate`, `max_item_price`, `max_line_total`, `mean_abs_price_deviation_pct`, `mean_discount_rate`, `mean_price_deviation_pct`, `min_item_price`, `min_line_total`, `n_unique_categories`, `n_unique_items`, `order_hour`, `total_amount`, `unique_item_ratio`, `void_line_count`, `void_line_rate`, `void_reason_exists` (`backend/Ai models/notebooks/Supervised/metrics/rule_explicit_feature_ablation_selection.json`; generated in `03_supervised...ipynb`, cell 34).

26. **Live app scoring / reason codes.** App loads precomputed `final_anomaly_alerts_dashboard.csv`, `final_anomaly_alerts_full.csv`, and metadata; it does not run RF scoring for new orders on request (`backend/app/ai/anomalies/service.py:39-65`). `/alerts` queries `AnomalyAlert` rows from DB (`routes.py:62-75`). Reason/explanation is generated in the final notebook by rule checks for high discount, price deviation, void, odd hour, basket, amount, C07, etc. (`04_final...ipynb`, cell 12 lines 47-104), then served as `alert_explanation`/`reason_codes` (`service.py:89-97`).

## Customer Segmentation

27. **K-Means profile attributes.** Yes. Candidate clustering excludes RFM value columns but includes categorical profile attributes: `archetype`, `price_tier`, `time_preference`, `day_preference`, `basket_size_bias`, etc. (`Segmentation_Modeling.ipynb`, cell 15 output).

28. **Why 551 columns.** The behavior matrix is `(10001,551)` after `StandardScaler` for numeric and `OneHotEncoder` for categorical (`cell 17 output). It is 52 numeric features + 499 one-hot categorical levels. Largest drivers are `preferred_categories` (393 levels) and `preferred_sections` (50), then smaller profile/preference columns (`customer_features.csv` cardinality; categorical list in cell 15 output).

29. **K values tested and metrics.** KMeans tested `k=2..10` (`cell 19 line 1). Metrics from cell 19 output: k2 silhouette 0.164194 / DB 2.061692 / CH 1297.500186; k3 0.089857 / 2.531848 / 1099.284669; k4 0.100905 / 2.511724 / 988.131607; k5 0.100014 / 2.628738 / 874.248081; k6 0.086506 / 2.553080 / 775.076762; k7 0.088705 / 2.622643 / 696.511869; k8 0.087907 / 2.628188 / 634.593224; k9 0.066293 / 2.626367 / 588.249555; k10 0.071618 / 2.608086 / 550.989967. Best silhouette was K=2, but final K=5 was manual business override (`cell 38 line 1`; `cell 64 lines 54-60`).

30. **RFM and hybrid rules.** R/F/M are quintile scores; recency reversed (`Data_Preparation_Feature_Engineering.ipynb`, cell 13 lines 20-32). RFM segment rules are explicit in `Segmentation_Modeling.ipynb`, cell 9 lines 8-31. Value tiers: High `score >= 12`, Mid `>=8`, Low `>0`, else No-History (`cell 54 lines 1-9`). Hybrid segment is `rfm_value_tier + " | " + kmeans_segment_name` (`cell 54 lines 11-17`), producing 15 segments (`cell 54 output`).

31. **Recency reference/scaling.** Reference date is `valid_tx["order_datetime"].max() + 1 day` (`Data_Preparation...ipynb`, cell 13 lines 1-16). Scaling uses `StandardScaler` for numeric clustering features (`Segmentation_Modeling.ipynb`, cell 17 lines 3-20). I found no log transform for monetary in the modeling code.

32. **Regenerate segmentation.** Endpoint runs `run_pipeline` in background (`backend/app/ai/segmentation/routes.py:94-103`). Pipeline reads live DB `customers`, `orders`, `order_items`, `products`, recomputes RFM + KMeans(k=5) + hybrid segments, and writes CSV outputs (`backend/app/ai/segmentation/pipeline.py:90-119`, `:159-188`, `:274-316`, `:365-410`).

## Web, Security, Performance

33. **Token storage/lifetimes.** Access token and user are stored in frontend `localStorage` (`frontend/src/AuthContext.tsx:23-35`, `:50-55`; `frontend/src/api.ts:9-13`). Refresh token is an `httpOnly` cookie named `pos_refresh_token`, path `/api/auth` (`backend/app/auth/routes.py:51-60`). Access lifetime default 15 minutes, refresh lifetime 7 days (`backend/app/core/config.py:29-30`).

34. **Refresh rotation/reuse.** Refresh tokens are hashed server-side (`backend/app/auth/service.py:44-47`; `backend/app/core/security.py:42-47`). Rotation creates a new token, revokes old, stores replacement ID (`auth/service.py:56-83`). Reuse of revoked/expired/missing token returns invalid (`auth/service.py:68-73`; `auth/routes.py:127-136`), but I found no token-family reuse detection/revocation cascade.

35. **Rate limit/bcrypt.** Login rate limiting is custom in-memory dict by IP+username, default 5 failed attempts per 300 seconds (`backend/app/auth/routes.py:22-44`, `:80-83`; `backend/app/core/config.py:34-35`). No rate-limit library found. Password hashing uses Passlib bcrypt default context; cost factor not explicitly set in code (`backend/app/core/security.py:7-19`).

36. **Load test/performance setup.** Tool/script is stdlib `urllib` + `ThreadPoolExecutor`, 10 concurrent users, 5 requests/user (`backend/load_test.py:1-11`, `:75-78`; `backend/load_test_exact.py:1-11`, `:56-68`). It logs in once to get a token, not per iteration (`load_test.py:57-60`; `load_test_exact.py:80-83`). Uvicorn is launched without `--workers`, so default single worker (`docker-compose.yml:40`; `backend/Dockerfile:22`). DB is sync SQLAlchemy `create_engine`/`SessionLocal`, not async (`backend/app/core/database.py:10-15`). Explanation for ~2s everywhere: not found as a comment/report; likely candidates from code are single worker + sync DB + concurrent requests, but that is an inference.

37. **AI endpoints live/precomputed.** Recommendation models load at startup (`backend/app/main.py:57-58`); forecasting LightGBM loads once (`lightgbm_engine.py:10-27`, `:47`) but features are precomputed CSV (`features/builder.py:6-29`); anomaly reads precomputed CSV alerts (`anomalies/service.py:39-65`); segmentation overview reads CSV lazily, while regenerate recomputes from DB (`segmentation/service.py:45-76`; `segmentation/routes.py:94-103`).

38. **Stock deduction/refund/void.** Stock/product ingredient deduction occurs on payment processing (`backend/app/payments/routes.py:55-81`) and also when order status is changed to `paid` (`backend/app/orders/routes.py:329-347`). Both commit in the same DB transaction/session and roll back on exception (`payments/routes.py:98-102`; `orders/routes.py:360-364`). Refund restores product and ingredient stock (`payments/routes.py:137-153`). Cancelled/voided order status frees table but does not restore stock unless refund endpoint is used (`orders/routes.py:319-327`).

39. **Receipt taxes.** Frontend applies 10% tax: `tax = subtotal * 0.1` (`frontend/src/pages/POSPage.tsx:110-112`). Backend tax rate not found.

40. **Counts.** I counted 18 SQLAlchemy tables from `__tablename__` definitions; 78 API route decorators; 22 frontend routes including `/login`, `/unauthorized`, `/pos/payment`, wildcard, etc. Sources: router includes in `backend/app/main.py:116-129`, route decorators in `backend/app/**/routes.py`, table declarations in `backend/app/**/models.py`, frontend routes in `frontend/src/App.tsx`.

41. **Tests.** Six pytest tests in `backend/tests/test_security_requests.py`: cashier cannot call manager route (`:86`), `alg=none` JWT rejected (`:94`), cashier cannot access another cashier order (`:102`), purchase-order receive increments stock/audits (`:113`), cashier cannot manage purchase orders (`:174`), cashier cannot read audit logs (`:185`). Frontend tests: not found; `frontend/package.json` has dev/build/lint/preview only. Coverage: not found; no coverage dependency/config found.

42. **CI/CD.** GitHub Actions workflow stages: `secrets-scan` with Gitleaks (`.github/workflows/ci.yml:15-28`), backend with Postgres service, install, Ruff, Bandit, pytest (`:30-96`), frontend npm ci/audit/lint/build (`:98-126`), Docker image build (`:128-167`), GHCR publish on main push (`:169-220`).

43. **Docker.** Compose defines 3 containers/services: `db`, `backend`, `frontend` (`docker-compose.yml`). Backend image copies the whole backend directory, so the AI model files under `backend/Ai models` are inside the backend container and loaded there (`backend/Dockerfile`; forecasting path in `lightgbm_engine.py:8`).

44. **Split bill/refund completeness.** Split bill is not fully implemented: frontend divides remaining amount and posts `/api/payments`, but backend marks the order `paid` on first payment and rejects later payments for already paid orders (`frontend/src/pages/PaymentPage.tsx:33-49`; `backend/app/payments/routes.py:52-65`). Refund backend exists and restores stock (`payments/routes.py:121-168`), but frontend “Refund” method posts a normal payment with method `"refund"` rather than calling `/api/payments/{id}/refund` (`PaymentPage.tsx:58-61`, `:33-41`). So refund is backend-implemented, frontend flow incomplete.

## Project

45. **Commit-history dates.** Git history starts `2026-07-01` (`01aa20f Initial commit`) and latest commit is `2026-08-07` (`8ac5cce updates`). Module commit traces: recommendations Module 1/app `2026-07-21`, `2026-07-22`, `2026-07-28`; forecasting Module 2/app `2026-07-21`, `2026-07-22`; anomaly Module 3/app `2026-07-21`, `2026-07-28`; segmentation Module 4/app `2026-07-21`, `2026-07-28`, `2026-08-07`; web/POS/auth/order/payment/stock/frontend `2026-07-21` through `2026-08-07`; CI/Docker `2026-07-21`/`2026-07-22`. There are many uncommitted modified files dated later in the working tree, but commit history only proves July 1 to August 7, 2026.
