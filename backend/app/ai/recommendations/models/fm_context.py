"""
Factorization Machine Context-Aware Engine
───────────────────────────────────────────
Loads the trained FM model (w0, w, V) and label encoders from the notebook
to score items based on contextual features: time of day, day of week,
meal period, and restaurant type.

This is the "context layer" that re-ranks recommendations so the cashier
doesn't see dinner items at 8:00 AM.

Model Artifacts:
  - fm_model_params.npz   (w0, w, V — trained FM parameters)
  - fm_encoders.pkl        (LabelEncoders for user, item, meal, restaurant, category)

Source Notebook: 02c_fm_context_aware_recommendations.ipynb

Architecture (from notebook):
  Feature matrix = [user_oh | item_oh | meal_oh | day_oh | is_weekend | hour | restaurant_oh | category_oh]
  Dimensions:       9991      122       4         7        1            1      7                8  = 10141
"""
import numpy as np
# Trusted local model artifacts are loaded from the app bundle.
import pickle  # nosec B403
from datetime import datetime
from pathlib import Path
from typing import Optional
from scipy.sparse import csr_matrix, hstack
import logging

logger = logging.getLogger(__name__)

# ── Category mapping: item_name → category (from the dataset) ──
# This maps each menu item to its food category for the FM feature vector
ITEM_CATEGORY_MAP = {
    # Mains
    "8oz Filet Mignon": "Main", "14oz Ribeye": "Main", "Grilled Atlantic Salmon": "Main",
    "Herb-Crusted Rack of Lamb": "Main", "Lobster Ravioli": "Main",
    "Spaghetti Carbonara": "Main", "Fettuccine Alfredo": "Main", "Beef Lasagna": "Main",
    "Potato Gnocchi with Pesto": "Main", "Margherita Pizza": "Main",
    "Pepperoni Pizza": "Main", "Truffle Mushroom Pizza": "Main",
    "Prosciutto & Arugula Pizza": "Main", "Meatball Calzone": "Main",
    "Classic Cheeseburger": "Main", "Bacon Double Burger": "Main",
    "Spicy BBQ Bacon Burger": "Main", "Crispy Chicken Sandwich": "Main",
    "Hot Dog with Mustard": "Main", "Philly Cheesesteak": "Main",
    "Chicken Tenders (4pc)": "Main", "Steak Fajitas": "Main",
    "Chicken Burrito": "Main", "Chicken Enchiladas": "Main",
    "Beef Tacos (3pc)": "Main", "Pork Carnitas Bowl": "Main",
    "California Roll": "Main", "Spicy Tuna Roll": "Main", "Dragon Roll": "Main",
    "Salmon Nigiri (2pc)": "Main", "Tuna Sashimi (5pc)": "Main",
    "Chicken Teriyaki Bento": "Main", "Pork Ramen": "Main", "Vegetable Udon": "Main",
    "Acai Berry Bowl": "Main", "Quinoa Power Bowl": "Main",
    "Vegan Buddha Bowl": "Main", "Grilled Tofu Wrap": "Main",
    "Avocado Toast": "Main", "Breakfast Sandwich (Egg & Cheese)": "Main",
    "Everything Bagel with Cream Cheese": "Main", "Oatmeal with Berries": "Main",
    # Sides
    "French Fries": "Side", "Sweet Potato Fries": "Side", "Onion Rings": "Side",
    "Mac & Cheese": "Side", "Garlic Bread": "Side", "Side Salad with Vinaigrette": "Side",
    "Garlic Mashed Potatoes": "Side", "Creamed Spinach": "Side",
    "Grilled Asparagus": "Side", "Truffle Mac & Cheese": "Side",
    "Rice & Beans": "Side", "Kale & Sweet Potato Salad": "Side",
    "Roasted Chickpeas": "Side",
    # Appetizers
    "Bruschetta": "Appetizer", "Fried Calamari": "Appetizer",
    "Caprese Salad": "Appetizer", "Buffalo Wings (10pc)": "Appetizer",
    "Loaded Nachos": "Appetizer", "Guacamole": "Appetizer",
    "Tortilla Chips": "Appetizer", "Queso Dip": "Appetizer",
    "Cheese Quesadilla": "Appetizer", "Miso Soup": "Appetizer",
    "Edamame": "Appetizer", "Pork Gyoza (6pc)": "Appetizer",
    "Seaweed Salad": "Appetizer", "Hummus & Pita": "Appetizer",
    "Jumbo Shrimp Cocktail": "Appetizer", "Oysters on the Half Shell (6pc)": "Appetizer",
    "Spicy Salsa": "Appetizer",
    # Desserts
    "Tiramisu": "Dessert", "Cannoli": "Dessert", "Lemon Gelato": "Dessert",
    "New York Cheesecake": "Dessert", "Crème Brûlée": "Dessert",
    "Chocolate Brownie": "Dessert", "Apple Pie": "Dessert",
    "Chocolate Chip Cookie": "Dessert", "Churros with Chocolate": "Dessert",
    "Caramel Flan": "Dessert", "Green Tea Mochi Ice Cream": "Dessert",
    "Vegan Peanut Butter Protein Ball": "Dessert",
    # Bakery
    "Almond Croissant": "Bakery", "Butter Croissant": "Bakery",
    "Blueberry Muffin": "Bakery",
    # Beverages
    "Espresso": "Beverage", "Cappuccino": "Beverage", "Iced Latte": "Beverage",
    "Cold Brew Coffee": "Beverage", "Caramel Macchiato": "Beverage",
    "Matcha Green Tea Latte": "Beverage", "Black Tea": "Beverage",
    "Green Tea": "Beverage", "Orange Juice": "Beverage", "Fruit Smoothie": "Beverage",
    "Coca-Cola": "Beverage", "Diet Coke": "Beverage", "Sprite": "Beverage",
    "Dr Pepper": "Beverage", "Iced Tea": "Beverage", "Vanilla Milkshake": "Beverage",
    "Coconut Water": "Beverage", "Cold Pressed Green Juice": "Beverage",
    "Kombucha (Ginger)": "Beverage", "Horchata": "Beverage",
    "Mexican Coke (Glass Bottle)": "Beverage", "Hot Sake (Small)": "Beverage",
    "Sapporo Draft": "Beverage",
    # Alcohol
    "Chardonnay (Glass)": "Alcohol", "Premium Cabernet Sauvignon (Glass)": "Alcohol",
    "Red Wine (Chianti)": "Alcohol", "Red Wine (Cabernet)": "Alcohol",
    "White Wine (Pinot Grigio)": "Alcohol", "Prosecco": "Alcohol",
    "Peroni Beer": "Alcohol", "Classic Margarita": "Alcohol",
    "Spicy Jalapeno Margarita": "Alcohol", "Corona Extra": "Alcohol",
    "Modelo Especial": "Alcohol", "Old Fashioned Cocktail": "Alcohol",
}


def _get_meal_period(hour: int) -> str:
    """Determine meal period from hour of day."""
    if 5 <= hour < 11:
        return "breakfast"
    elif 11 <= hour < 16:
        return "lunch"
    elif 16 <= hour < 22:
        return "dinner"
    else:
        return "late_night"


class FMEngine:
    """Factorization Machine for context-aware item scoring."""

    def __init__(self):
        self._w0: float = 0.0
        self._w: Optional[np.ndarray] = None
        self._V: Optional[np.ndarray] = None
        self._encoders: dict = {}
        self._n_users: int = 0
        self._n_items: int = 0
        self._n_meals: int = 0
        self._n_days: int = 7
        self._n_restaurants: int = 0
        self._n_categories: int = 0
        self._item_names: list[str] = []
        self._item_name_lower_map: dict[str, int] = {}
        self._category_name_to_idx: dict[str, int] = {}
        self._loaded = False

    def load(self, base_dir: Path) -> None:
        """Load FM model parameters and encoders."""
        params_path = base_dir / "models" / "Module 1" / "fm_model_params.npz"
        encoders_path = base_dir / "models" / "Module 1" / "fm_encoders.pkl"

        if not params_path.exists() or not encoders_path.exists():
            logger.warning(f"FM model files not found at {base_dir / 'models' / 'Module 1'}")
            return

        # Load model parameters
        params = np.load(str(params_path))
        self._w0 = float(params["w0"])
        self._w = params["w"]
        self._V = params["V"]

        # Load trusted encoders packaged with the trained model.
        with open(str(encoders_path), "rb") as f:
            self._encoders = pickle.load(f)  # nosec B301

        # Extract dimensions from encoders
        self._n_users = len(self._encoders["user"].classes_)
        self._n_items = len(self._encoders["item"].classes_)
        self._n_meals = len(self._encoders["meal"].classes_)
        self._n_restaurants = len(self._encoders["restaurant"].classes_)
        self._n_categories = len(self._encoders["category"].classes_)

        # Build item name lookup
        self._item_names = list(self._encoders["item"].classes_)
        self._item_name_lower_map = {
            name.lower().strip(): idx
            for idx, name in enumerate(self._item_names)
        }

        # Build category lookup
        self._category_name_to_idx = {
            name: idx for idx, name in enumerate(self._encoders["category"].classes_)
        }

        expected_features = (
            self._n_users + self._n_items + self._n_meals +
            self._n_days + 1 + 1 + self._n_restaurants + self._n_categories
        )  # = 10141

        logger.info(
            f"[FM] Loaded model: w0={self._w0:.3f}, "
            f"w={self._w.shape}, V={self._V.shape}, "
            f"expected features={expected_features}, "
            f"items={self._n_items}, meals={self._n_meals}, "
            f"restaurants={self._n_restaurants}"
        )
        self._loaded = True

    @property
    def is_loaded(self) -> bool:
        return self._loaded and self._w is not None

    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Numerically stable sigmoid."""
        return np.where(
            x >= 0,
            1 / (1 + np.exp(-x)),
            np.exp(x) / (1 + np.exp(x))
        )

    def _predict_raw(self, X) -> np.ndarray:
        """FM prediction: linear + pairwise interaction terms."""
        linear = X.dot(self._w) + self._w0
        XV = X.dot(self._V)
        XV_sq = np.array(XV ** 2)
        X_sq_V_sq = np.array(X.power(2).dot(self._V ** 2))
        interaction = 0.5 * np.sum(XV_sq - X_sq_V_sq, axis=1)
        return np.asarray(linear).flatten() + np.asarray(interaction).flatten()

    def _predict_proba(self, X) -> np.ndarray:
        """Predict probability via sigmoid of raw FM score."""
        return self._sigmoid(self._predict_raw(X))

    def _build_feature_matrix(self, data: dict, n: int):
        """
        Build the sparse feature matrix exactly as the training notebook does.
        Feature order: [user_oh | item_oh | meal_oh | day_oh | is_weekend | hour | restaurant_oh | category_oh]
        """
        user_oh = csr_matrix(
            (np.ones(n), (np.arange(n), data["user_idx"])),
            shape=(n, self._n_users)
        )
        item_oh = csr_matrix(
            (np.ones(n), (np.arange(n), data["item_idx"])),
            shape=(n, self._n_items)
        )
        meal_oh = csr_matrix(
            (np.ones(n), (np.arange(n), data["meal_idx"])),
            shape=(n, self._n_meals)
        )
        day_oh = csr_matrix(
            (np.ones(n), (np.arange(n), data["day_of_week"])),
            shape=(n, self._n_days)
        )
        is_weekend = csr_matrix(
            np.array(data["is_weekend"]).reshape(-1, 1).astype(float)
        )
        hour_norm = csr_matrix(
            (np.array(data["hour"]) / 23.0).reshape(-1, 1)
        )
        rest_oh = csr_matrix(
            (np.ones(n), (np.arange(n), data["restaurant_idx"])),
            shape=(n, self._n_restaurants)
        )
        cat_oh = csr_matrix(
            (np.ones(n), (np.arange(n), data["category_idx"])),
            shape=(n, self._n_categories)
        )

        return hstack(
            [user_oh, item_oh, meal_oh, day_oh, is_weekend, hour_norm, rest_oh, cat_oh],
            format="csr"
        )

    def _get_item_category_idx(self, item_name: str) -> int:
        """Get category index for an item."""
        cat_name = ITEM_CATEGORY_MAP.get(item_name, "Food")
        return self._category_name_to_idx.get(cat_name, 0)

    def score_items(
        self,
        hour: Optional[int] = None,
        restaurant_type: str = "Cafe",
    ) -> list[dict]:
        """
        Score all items for a generic user in the current context.
        Returns a list of {item_name, score} sorted by score descending.
        """
        if not self.is_loaded:
            return []

        now = datetime.now()
        if hour is None:
            hour = now.hour
        day_of_week = now.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        meal_period = _get_meal_period(hour)

        # Encode meal
        meal_classes = list(self._encoders["meal"].classes_)
        meal_idx = meal_classes.index(meal_period) if meal_period in meal_classes else 0

        # Encode restaurant
        rest_classes = list(self._encoders["restaurant"].classes_)
        rest_idx = rest_classes.index(restaurant_type) if restaurant_type in rest_classes else 0

        # Use a "default" user (user_idx=0) for anonymous recommendations
        n = self._n_items
        data = {
            "user_idx": np.zeros(n, dtype=int),
            "item_idx": np.arange(n, dtype=int),
            "hour": np.full(n, hour, dtype=int),
            "day_of_week": np.full(n, day_of_week, dtype=int),
            "is_weekend": np.full(n, is_weekend, dtype=int),
            "meal_idx": np.full(n, meal_idx, dtype=int),
            "restaurant_idx": np.full(n, rest_idx, dtype=int),
            "category_idx": np.array(
                [self._get_item_category_idx(name) for name in self._item_names],
                dtype=int
            ),
        }

        X = self._build_feature_matrix(data, n)
        scores = self._predict_proba(X)

        results = []
        for i, (name, score) in enumerate(zip(self._item_names, scores)):
            results.append({"item_name": name, "score": float(score)})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def get_context_multipliers(
        self, item_names: list[str], hour: Optional[int] = None
    ) -> dict[str, float]:
        """
        Get context-aware multipliers for a set of items.
        Returns {item_name_lower: multiplier} where multiplier > 1 means
        the item is contextually appropriate, < 1 means it's not.
        """
        if not self.is_loaded:
            return {}

        all_scores = self.score_items(hour=hour)
        if not all_scores:
            return {}

        # Normalize scores to multipliers (mean = 1.0)
        scores_arr = np.array([s["score"] for s in all_scores])
        mean_score = scores_arr.mean() if scores_arr.mean() > 0 else 1.0

        multipliers = {}
        for entry in all_scores:
            key = entry["item_name"].lower().strip()
            multipliers[key] = entry["score"] / mean_score

        return multipliers

    def get_summary(self) -> dict:
        """Return summary stats."""
        if not self.is_loaded:
            return {"status": "not_loaded"}

        return {
            "n_users": self._n_users,
            "n_items": self._n_items,
            "n_features": self._w.shape[0] if self._w is not None else 0,
            "n_factors": self._V.shape[1] if self._V is not None else 0,
            "meal_classes": list(self._encoders["meal"].classes_),
            "restaurant_classes": list(self._encoders["restaurant"].classes_),
            "status": "loaded",
        }
