### Ablation conclusion

Random Forest, the report-selected supervised model, dropped from F1=0.951 with full features to F1=0.470 after removing rule-explicit variables (Delta F1=-0.481). This is the headline estimate of how much the reported supervised performance depends on features that mirror the synthetic labelling rules.

The largest per-type recall losses are visible in the Random Forest recall comparison table above. Types with substantial drops are: odd_hour, price_tampering, shift_end_void_cluster, suspicious_discount, void_after_payment. Types that held up comparatively well are: none under the -0.10 threshold. Collapses on suspicious discount, odd-hour, price-tampering, basket-size outlier, or shift-end void cases indicate rule memorisation rather than evidence that those detections would generalise directly to real POS data.

The full-feature winner is Random Forest (F1=0.951); the reduced-feature winner is LightGBM (F1=0.600). If these differ, the original Random Forest deployment choice remains valid only for the full synthetic-feature setting and should not be treated as proof that Random Forest is the best model under more realistic feature constraints.

The reduced-feature result should be interpreted as an honest lower bound: it removes direct rule encodings and asks what signal remains in contextual and behavioural variables. Lower performance is therefore informative, not a failed experiment.

This strengthens the deployment recommendation in the report. The supervised detector should not be promoted to production solely on synthetic-label performance; it still needs validation on real POS anomaly labels or expert-reviewed alerts before operational use. The ablation quantifies why that validation step is necessary.
