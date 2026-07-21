import os
import json
import lightgbm as lgb
import pandas as pd
import numpy as np

# Path to the actual model file in the backend folder
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "Ai models", "models", "Module 2", "lightgbm")

class LightGBMEngine:
    def __init__(self):
        self.model_path = os.path.join(MODEL_DIR, "model.txt")
        self.manifest_path = os.path.join(MODEL_DIR, "manifest.json")
        self.model = None
        self.manifest = None
        self._load()

    def _load(self):
        if not os.path.exists(self.model_path) or not os.path.exists(self.manifest_path):
            print(f"[Warning] LightGBM model or manifest not found at {MODEL_DIR}")
            return
        
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            self.manifest = json.load(f)
            
        self.model = lgb.Booster(model_file=self.model_path)
        print(f"[LightGBM] Model loaded successfully. Ready to predict {self.manifest['n_items']} items.")

    def predict(self, features_df: pd.DataFrame) -> np.ndarray:
        """
        Takes a pandas DataFrame containing the exact 84 features in order
        and returns the predictions.
        """
        if self.model is None:
            raise ValueError("Model is not loaded.")
        
        # Ensure correct columns and order
        required_features = self.manifest['feature_names']
        missing = set(required_features) - set(features_df.columns)
        if missing:
            raise ValueError(f"Missing features for prediction: {missing}")
            
        X = features_df[required_features]
        predictions = self.model.predict(X)
        return predictions

engine = LightGBMEngine()
