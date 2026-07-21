"""
Enterprise POS Dataset Generator — v6 (Definitive Edition)
==========================================================
Covers all modules of the Timsoft Intelligent POS PFE:

  Module 1 — Recommendation          (FP-Growth, SVD, ALS, FM)
  Module 2 — Demand Forecasting      (Prophet/SARIMA/XGBoost/LightGBM/LSTM/TFT)
  Module 3 — Anomaly Detection       (Isolation Forest / Autoencoder / supervised)
  Module 4 — Customer Segmentation   (K-Means / DBSCAN / hierarchical)
  Module 5 — NLP Assistant           (LLM + RAG, no data changes required)

CHANGES FROM v5
---------------
* Time range extended: 18 months (Jan 2023 → Jun 2024) → 36 months (Jan 2023 → Dec 2025).
* Customer base scaled from 5k → 10k to match higher order volume.
* Holidays + Ramadan periods extended into 2025 with astronomically correct dates.
* Anomaly counts scale automatically with order volume (proportions unchanged).
* Affinity rules, seasonality, and weekday/month patterns unchanged
  → enables clean attribution of model improvements to "more data" alone.
* Print-summary line for non-anomaly voids fixed (was double-counting line items
  vs. orders).

DESIGN PRINCIPLES
-----------------
1. DATA ONCE, TRAIN MANY TIMES. Every module trains on the same dataset.
2. GROUND TRUTH SEPARATED. Hidden labels (archetypes, anomaly flags) live in
   separate files so models train unsupervised but evaluation is rigorous.
3. BACKWARD COMPATIBLE. Same pipe-separated schema as v5 for existing columns.
4. REPRODUCIBLE. Fixed seeds, deterministic output.

OUTPUTS
-------
  enterprise_pos_dataset.csv      — main POS transactions (pipe-separated)
  customers.csv                   — customer profiles (with archetype labels)
  anomalies_ground_truth.csv      — anomaly labels for Module 3 evaluation
  cashiers.csv                    — staff roster
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta, date as date_cls, time as time_cls
from collections import Counter, defaultdict

# ============================================================================
# 0. GLOBAL SEEDS AND CONSTANTS
# ============================================================================

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
RNG = np.random.default_rng(SEED)
PY_RNG = random.Random(SEED)

DATE_START = date_cls(2023, 1, 1)
DATE_END   = date_cls(2025, 12, 31)
TOTAL_DAYS = (DATE_END - DATE_START).days

OUTPUT_MAIN      = 'enterprise_pos_dataset.csv'
OUTPUT_CUSTOMERS = 'customers.csv'
OUTPUT_ANOMALIES = 'anomalies_ground_truth.csv'
OUTPUT_CASHIERS  = 'cashiers.csv'

# ============================================================================
# 1. MENU (unchanged from v5 — Module 1 affinity depends on this)
# ============================================================================

menus = {
    'Cafe': {
        'Espresso': (3.00, 'Beverage'), 'Cappuccino': (4.50, 'Beverage'), 'Iced Latte': (4.75, 'Beverage'),
        'Caramel Macchiato': (5.25, 'Beverage'), 'Matcha Green Tea Latte': (5.50, 'Beverage'),
        'Cold Brew Coffee': (4.50, 'Beverage'), 'Black Tea': (2.50, 'Beverage'),
        'Orange Juice': (4.00, 'Beverage'), 'Fruit Smoothie': (6.50, 'Beverage'),
        'Butter Croissant': (3.50, 'Bakery'), 'Almond Croissant': (4.25, 'Bakery'),
        'Blueberry Muffin': (3.75, 'Bakery'), 'Chocolate Chip Cookie': (2.50, 'Bakery'),
        'Everything Bagel with Cream Cheese': (4.50, 'Bakery'),
        'Avocado Toast': (8.00, 'Food'), 'Breakfast Sandwich (Egg & Cheese)': (6.50, 'Food'),
        'Oatmeal with Berries': (5.50, 'Food')
    },
    'American': {
        'Classic Cheeseburger': (9.50, 'Main'), 'Bacon Double Burger': (12.00, 'Main'),
        'Crispy Chicken Sandwich': (10.50, 'Main'), 'Spicy BBQ Bacon Burger': (11.50, 'Main'),
        'Philly Cheesesteak': (13.00, 'Main'), 'Chicken Tenders (4pc)': (9.00, 'Main'),
        'Hot Dog with Mustard': (6.00, 'Main'), 'Buffalo Wings (10pc)': (12.50, 'Appetizer'),
        'Loaded Nachos': (9.00, 'Appetizer'),
        'French Fries': (3.50, 'Side'), 'Sweet Potato Fries': (4.50, 'Side'),
        'Onion Rings': (4.50, 'Side'), 'Mac & Cheese': (5.00, 'Side'),
        'Coca-Cola': (2.50, 'Beverage'), 'Diet Coke': (2.50, 'Beverage'),
        'Sprite': (2.50, 'Beverage'), 'Dr Pepper': (2.50, 'Beverage'),
        'Iced Tea': (3.00, 'Beverage'),
        'Vanilla Milkshake': (5.00, 'Dessert'), 'Chocolate Brownie': (4.50, 'Dessert'),
        'Apple Pie': (5.00, 'Dessert')
    },
    'Italian': {
        'Margherita Pizza': (14.00, 'Main'), 'Pepperoni Pizza': (16.00, 'Main'),
        'Truffle Mushroom Pizza': (18.00, 'Main'), 'Meatball Calzone': (15.00, 'Main'),
        'Prosciutto & Arugula Pizza': (17.50, 'Main'),
        'Spaghetti Carbonara': (16.50, 'Main'), 'Beef Lasagna': (17.00, 'Main'),
        'Fettuccine Alfredo': (15.50, 'Main'), 'Lobster Ravioli': (22.00, 'Main'),
        'Potato Gnocchi with Pesto': (16.00, 'Main'),
        'Garlic Bread': (5.00, 'Side'), 'Caprese Salad': (9.00, 'Side'),
        'Bruschetta': (8.00, 'Appetizer'), 'Fried Calamari': (12.00, 'Appetizer'),
        'Red Wine (Chianti)': (9.00, 'Alcohol'), 'Red Wine (Cabernet)': (10.00, 'Alcohol'),
        'White Wine (Pinot Grigio)': (9.00, 'Alcohol'), 'Prosecco': (8.50, 'Alcohol'),
        'Peroni Beer': (6.00, 'Alcohol'),
        'Tiramisu': (7.50, 'Dessert'), 'Lemon Gelato': (5.50, 'Dessert'), 'Cannoli': (6.00, 'Dessert')
    },
    'Mexican': {
        'Beef Tacos (3pc)': (11.00, 'Main'), 'Chicken Burrito': (10.50, 'Main'),
        'Steak Fajitas': (16.00, 'Main'), 'Pork Carnitas Bowl': (12.50, 'Main'),
        'Cheese Quesadilla': (8.50, 'Main'), 'Chicken Enchiladas': (13.00, 'Main'),
        'Tortilla Chips': (3.00, 'Side'), 'Guacamole': (4.50, 'Side'),
        'Spicy Salsa': (2.00, 'Side'), 'Queso Dip': (5.00, 'Side'), 'Rice & Beans': (4.00, 'Side'),
        'Classic Margarita': (10.00, 'Alcohol'), 'Spicy Jalapeno Margarita': (11.00, 'Alcohol'),
        'Corona Extra': (5.50, 'Alcohol'), 'Modelo Especial': (6.00, 'Alcohol'),
        'Horchata': (4.00, 'Beverage'), 'Mexican Coke (Glass Bottle)': (3.50, 'Beverage'),
        'Churros with Chocolate': (6.00, 'Dessert'), 'Caramel Flan': (5.50, 'Dessert')
    },
    'Japanese': {
        'Spicy Tuna Roll': (8.50, 'Main'), 'California Roll': (7.00, 'Main'),
        'Dragon Roll': (13.00, 'Main'), 'Salmon Nigiri (2pc)': (6.00, 'Main'),
        'Tuna Sashimi (5pc)': (12.00, 'Main'), 'Chicken Teriyaki Bento': (15.00, 'Main'),
        'Pork Ramen': (14.00, 'Main'), 'Vegetable Udon': (12.00, 'Main'),
        'Edamame': (5.00, 'Appetizer'), 'Miso Soup': (3.50, 'Side'),
        'Pork Gyoza (6pc)': (7.00, 'Appetizer'), 'Seaweed Salad': (5.50, 'Side'),
        'Hot Sake (Small)': (7.00, 'Alcohol'), 'Sapporo Draft': (6.00, 'Alcohol'),
        'Green Tea': (2.50, 'Beverage'),
        'Green Tea Mochi Ice Cream': (4.50, 'Dessert')
    },
    'Healthy_Vegan': {
        'Quinoa Power Bowl': (12.00, 'Main'), 'Kale & Sweet Potato Salad': (11.00, 'Main'),
        'Vegan Buddha Bowl': (13.50, 'Main'), 'Grilled Tofu Wrap': (10.00, 'Main'),
        'Acai Berry Bowl': (9.50, 'Food'),
        'Roasted Chickpeas': (4.00, 'Side'), 'Side Salad with Vinaigrette': (5.00, 'Side'),
        'Hummus & Pita': (6.50, 'Side'),
        'Kombucha (Ginger)': (5.00, 'Beverage'), 'Cold Pressed Green Juice': (7.00, 'Beverage'),
        'Coconut Water': (4.00, 'Beverage'),
        'Vegan Peanut Butter Protein Ball': (3.00, 'Dessert')
    },
    'Steakhouse': {
        '8oz Filet Mignon': (35.00, 'Main'), '14oz Ribeye': (32.00, 'Main'),
        'Grilled Atlantic Salmon': (26.00, 'Main'), 'Herb-Crusted Rack of Lamb': (38.00, 'Main'),
        'Garlic Mashed Potatoes': (7.00, 'Side'), 'Creamed Spinach': (8.00, 'Side'),
        'Grilled Asparagus': (9.00, 'Side'), 'Truffle Mac & Cheese': (12.00, 'Side'),
        'Oysters on the Half Shell (6pc)': (18.00, 'Appetizer'),
        'Jumbo Shrimp Cocktail': (16.00, 'Appetizer'),
        'Premium Cabernet Sauvignon (Glass)': (15.00, 'Alcohol'),
        'Chardonnay (Glass)': (12.00, 'Alcohol'), 'Old Fashioned Cocktail': (14.00, 'Alcohol'),
        'New York Cheesecake': (9.00, 'Dessert'), 'Crème Brûlée': (10.00, 'Dessert')
    }
}

SECTIONS = list(menus.keys())

# ============================================================================
# 2. AFFINITY SYSTEM (unchanged — Module 1 depends on these patterns)
# ============================================================================

AFFINITIES = {
    'Cafe': [
        ('Espresso', 'Butter Croissant', 2.5),
        ('Cappuccino', 'Almond Croissant', 2.8),
        ('Iced Latte', 'Blueberry Muffin', 2.0),
        ('Cold Brew Coffee', 'Chocolate Chip Cookie', 2.2),
        ('Avocado Toast', 'Orange Juice', 2.5),
        ('Avocado Toast', 'Iced Latte', 1.8),
        ('Breakfast Sandwich (Egg & Cheese)', 'Cappuccino', 2.0),
        ('Oatmeal with Berries', 'Fruit Smoothie', 2.3),
        ('Oatmeal with Berries', 'Black Tea', 1.6),
        ('Matcha Green Tea Latte', 'Oatmeal with Berries', 2.0),
        ('Matcha Green Tea Latte', 'Avocado Toast', 1.7),
        ('Butter Croissant', 'Almond Croissant', 1.4),
        ('Everything Bagel with Cream Cheese', 'Cold Brew Coffee', 2.1),
    ],
    'American': [
        ('Classic Cheeseburger', 'French Fries', 3.0),
        ('Bacon Double Burger', 'French Fries', 3.2),
        ('Spicy BBQ Bacon Burger', 'Onion Rings', 2.5),
        ('Crispy Chicken Sandwich', 'Sweet Potato Fries', 2.2),
        ('Crispy Chicken Sandwich', 'French Fries', 2.0),
        ('Classic Cheeseburger', 'Coca-Cola', 2.5),
        ('Bacon Double Burger', 'Dr Pepper', 2.0),
        ('Chicken Tenders (4pc)', 'Sprite', 1.8),
        ('Buffalo Wings (10pc)', 'Iced Tea', 2.2),
        ('Loaded Nachos', 'Coca-Cola', 1.9),
        ('French Fries', 'Vanilla Milkshake', 1.8),
        ('Classic Cheeseburger', 'Chocolate Brownie', 1.4),
        ('Philly Cheesesteak', 'Mac & Cheese', 2.3),
        ('Hot Dog with Mustard', 'French Fries', 2.8),
    ],
    'Italian': [
        ('Spaghetti Carbonara', 'Garlic Bread', 3.0),
        ('Fettuccine Alfredo', 'Garlic Bread', 2.8),
        ('Beef Lasagna', 'Garlic Bread', 2.5),
        ('Potato Gnocchi with Pesto', 'Caprese Salad', 2.0),
        ('Margherita Pizza', 'Bruschetta', 1.6),
        ('Pepperoni Pizza', 'Fried Calamari', 1.5),
        ('Spaghetti Carbonara', 'Red Wine (Chianti)', 2.2),
        ('Beef Lasagna', 'Red Wine (Cabernet)', 2.0),
        ('Lobster Ravioli', 'White Wine (Pinot Grigio)', 2.5),
        ('Margherita Pizza', 'Peroni Beer', 2.0),
        ('Truffle Mushroom Pizza', 'Prosecco', 1.8),
        ('Spaghetti Carbonara', 'Tiramisu', 1.6),
        ('Lobster Ravioli', 'Lemon Gelato', 1.5),
        ('Margherita Pizza', 'Cannoli', 1.3),
        ('Bruschetta', 'Fried Calamari', 1.7),
    ],
    'Mexican': [
        ('Tortilla Chips', 'Guacamole', 3.5),
        ('Tortilla Chips', 'Spicy Salsa', 2.8),
        ('Tortilla Chips', 'Queso Dip', 2.5),
        ('Guacamole', 'Spicy Salsa', 1.8),
        ('Beef Tacos (3pc)', 'Rice & Beans', 2.2),
        ('Chicken Burrito', 'Tortilla Chips', 2.0),
        ('Steak Fajitas', 'Guacamole', 2.3),
        ('Steak Fajitas', 'Rice & Beans', 1.9),
        ('Cheese Quesadilla', 'Spicy Salsa', 2.0),
        ('Pork Carnitas Bowl', 'Tortilla Chips', 1.7),
        ('Steak Fajitas', 'Classic Margarita', 2.5),
        ('Beef Tacos (3pc)', 'Corona Extra', 2.0),
        ('Chicken Enchiladas', 'Modelo Especial', 1.8),
        ('Cheese Quesadilla', 'Horchata', 2.0),
        ('Chicken Burrito', 'Mexican Coke (Glass Bottle)', 1.9),
        ('Steak Fajitas', 'Spicy Jalapeno Margarita', 2.0),
        ('Beef Tacos (3pc)', 'Churros with Chocolate', 1.4),
        ('Chicken Enchiladas', 'Caramel Flan', 1.3),
    ],
    'Japanese': [
        ('Spicy Tuna Roll', 'California Roll', 2.5),
        ('Dragon Roll', 'Salmon Nigiri (2pc)', 2.2),
        ('Spicy Tuna Roll', 'Tuna Sashimi (5pc)', 1.8),
        ('Spicy Tuna Roll', 'Edamame', 2.3),
        ('California Roll', 'Miso Soup', 2.5),
        ('Dragon Roll', 'Seaweed Salad', 2.0),
        ('Salmon Nigiri (2pc)', 'Miso Soup', 2.2),
        ('Pork Ramen', 'Pork Gyoza (6pc)', 2.8),
        ('Vegetable Udon', 'Edamame', 2.0),
        ('Tuna Sashimi (5pc)', 'Hot Sake (Small)', 2.5),
        ('Dragon Roll', 'Sapporo Draft', 2.2),
        ('Pork Ramen', 'Green Tea', 1.8),
        ('Chicken Teriyaki Bento', 'Green Tea', 2.0),
        ('Pork Ramen', 'Green Tea Mochi Ice Cream', 1.4),
    ],
    'Healthy_Vegan': [
        ('Quinoa Power Bowl', 'Kombucha (Ginger)', 2.5),
        ('Vegan Buddha Bowl', 'Cold Pressed Green Juice', 2.3),
        ('Grilled Tofu Wrap', 'Side Salad with Vinaigrette', 2.2),
        ('Kale & Sweet Potato Salad', 'Hummus & Pita', 2.0),
        ('Acai Berry Bowl', 'Coconut Water', 2.8),
        ('Quinoa Power Bowl', 'Roasted Chickpeas', 1.8),
        ('Vegan Buddha Bowl', 'Hummus & Pita', 1.9),
        ('Grilled Tofu Wrap', 'Kombucha (Ginger)', 1.7),
        ('Kale & Sweet Potato Salad', 'Cold Pressed Green Juice', 2.0),
        ('Acai Berry Bowl', 'Vegan Peanut Butter Protein Ball', 1.6),
        ('Quinoa Power Bowl', 'Vegan Peanut Butter Protein Ball', 1.3),
    ],
    'Steakhouse': [
        ('8oz Filet Mignon', 'Garlic Mashed Potatoes', 2.8),
        ('8oz Filet Mignon', 'Grilled Asparagus', 2.3),
        ('14oz Ribeye', 'Garlic Mashed Potatoes', 2.5),
        ('14oz Ribeye', 'Creamed Spinach', 2.3),
        ('Grilled Atlantic Salmon', 'Grilled Asparagus', 2.8),
        ('Herb-Crusted Rack of Lamb', 'Truffle Mac & Cheese', 2.0),
        ('8oz Filet Mignon', 'Jumbo Shrimp Cocktail', 2.0),
        ('14oz Ribeye', 'Oysters on the Half Shell (6pc)', 1.7),
        ('8oz Filet Mignon', 'Premium Cabernet Sauvignon (Glass)', 2.8),
        ('14oz Ribeye', 'Premium Cabernet Sauvignon (Glass)', 2.5),
        ('Grilled Atlantic Salmon', 'Chardonnay (Glass)', 2.8),
        ('Herb-Crusted Rack of Lamb', 'Old Fashioned Cocktail', 2.0),
        ('8oz Filet Mignon', 'Crème Brûlée', 1.6),
        ('14oz Ribeye', 'New York Cheesecake', 1.5),
        ('Garlic Mashed Potatoes', 'Creamed Spinach', 1.8),
    ]
}

# ============================================================================
# 3. TEMPORAL STRUCTURE
# ============================================================================

BASE_DAILY = {
    'Cafe':          9,
    'American':      11,
    'Italian':       8,
    'Mexican':       7,
    'Japanese':      6,
    'Healthy_Vegan': 4,
    'Steakhouse':    4,
}

WEEKDAY_MULT = {
    'Cafe':          [0.90, 0.95, 1.00, 1.05, 1.10, 1.30, 1.25],
    'American':      [0.85, 0.90, 0.95, 1.05, 1.25, 1.40, 1.15],
    'Italian':       [0.80, 0.85, 0.95, 1.05, 1.30, 1.45, 1.20],
    'Mexican':       [0.85, 0.90, 0.95, 1.00, 1.25, 1.40, 1.15],
    'Japanese':      [0.90, 0.95, 1.00, 1.05, 1.20, 1.35, 1.10],
    'Healthy_Vegan': [1.15, 1.20, 1.15, 1.10, 1.00, 0.80, 0.70],
    'Steakhouse':    [0.70, 0.75, 0.85, 1.00, 1.35, 1.55, 1.15],
}

MONTH_MULT = [0.90, 0.93, 0.98, 1.03, 1.08, 1.12, 1.15, 1.13, 1.05, 1.00, 0.95, 1.08]
TREND_TOTAL_GROWTH = 0.15  # 15% growth across the full 36-month window (~5%/year)

HOLIDAY_EFFECTS = {
    'nye':       1.70,
    'major':     1.35,
    'minor':     1.18,
    'eid_fitr':  1.50,
    'eid_adha':  1.10,
}

HOLIDAYS = {
    # 2023
    date_cls(2023, 1,  1): 'nye',
    date_cls(2023, 1, 14): 'major',
    date_cls(2023, 3, 20): 'major',
    date_cls(2023, 4,  9): 'minor',
    date_cls(2023, 4, 21): 'eid_fitr',
    date_cls(2023, 4, 22): 'eid_fitr',
    date_cls(2023, 4, 23): 'eid_fitr',
    date_cls(2023, 5,  1): 'minor',
    date_cls(2023, 6, 28): 'eid_adha',
    date_cls(2023, 6, 29): 'eid_adha',
    date_cls(2023, 7, 19): 'minor',
    date_cls(2023, 7, 25): 'major',
    date_cls(2023, 8, 13): 'minor',
    date_cls(2023, 9, 27): 'minor',
    date_cls(2023, 10, 15): 'minor',
    date_cls(2023, 12, 17): 'minor',
    date_cls(2023, 12, 31): 'nye',
    # 2024
    date_cls(2024, 1,  1): 'nye',
    date_cls(2024, 1, 14): 'major',
    date_cls(2024, 3, 20): 'major',
    date_cls(2024, 4,  9): 'minor',
    date_cls(2024, 4, 10): 'eid_fitr',
    date_cls(2024, 4, 11): 'eid_fitr',
    date_cls(2024, 4, 12): 'eid_fitr',
    date_cls(2024, 5,  1): 'minor',
    date_cls(2024, 6, 16): 'eid_adha',
    date_cls(2024, 6, 17): 'eid_adha',
    date_cls(2024, 7, 19): 'minor',
    date_cls(2024, 7, 25): 'major',
    date_cls(2024, 8, 13): 'minor',
    date_cls(2024, 9, 27): 'minor',
    date_cls(2024, 10, 15): 'minor',
    date_cls(2024, 12, 17): 'minor',
    date_cls(2024, 12, 31): 'nye',
    # 2025
    date_cls(2025, 1,  1): 'nye',
    date_cls(2025, 1, 14): 'major',
    date_cls(2025, 3, 20): 'major',
    date_cls(2025, 3, 30): 'eid_fitr',
    date_cls(2025, 3, 31): 'eid_fitr',
    date_cls(2025, 4,  1): 'eid_fitr',
    date_cls(2025, 4,  9): 'minor',
    date_cls(2025, 5,  1): 'minor',
    date_cls(2025, 6,  6): 'eid_adha',
    date_cls(2025, 6,  7): 'eid_adha',
    date_cls(2025, 7, 19): 'minor',
    date_cls(2025, 7, 25): 'major',
    date_cls(2025, 8, 13): 'minor',
    date_cls(2025, 9, 27): 'minor',
    date_cls(2025, 10, 15): 'minor',
    date_cls(2025, 12, 17): 'minor',
    date_cls(2025, 12, 31): 'nye',
}

RAMADAN_PERIODS = [
    (date_cls(2023, 3, 22), date_cls(2023, 4, 20)),
    (date_cls(2024, 3, 11), date_cls(2024, 4, 9)),
    (date_cls(2025, 2, 28), date_cls(2025, 3, 29)),
]

def _expand_ramadan():
    days = set()
    for start, end in RAMADAN_PERIODS:
        d = start
        while d <= end:
            days.add(d)
            d += timedelta(days=1)
    return days

RAMADAN_DAYS = _expand_ramadan()

RAMADAN_MULT = {
    'Cafe':          0.30,
    'Healthy_Vegan': 0.35,
    'American':      0.70,
    'Italian':       0.75,
    'Mexican':       0.75,
    'Japanese':      0.75,
    'Steakhouse':    0.80,
}

TIME_DISTRIBUTIONS = {
    'Cafe': {
        'slots':   ['07:00 AM', '07:30 AM', '08:00 AM', '08:30 AM', '09:00 AM', '10:00 AM', '11:00 AM'],
        'weights': [0.08, 0.12, 0.22, 0.22, 0.18, 0.10, 0.08],
        'period':  'morning',
    },
    'American': {
        'slots':   ['11:30 AM', '12:00 PM', '12:30 PM', '01:00 PM', '06:00 PM', '07:00 PM', '08:00 PM'],
        'weights': [0.08, 0.17, 0.18, 0.10, 0.13, 0.20, 0.14],
        'period':  'mixed',
    },
    'Italian': {
        'slots':   ['06:30 PM', '07:00 PM', '07:30 PM', '08:00 PM', '08:30 PM', '09:00 PM'],
        'weights': [0.08, 0.15, 0.22, 0.25, 0.18, 0.12],
        'period':  'dinner',
    },
    'Mexican': {
        'slots':   ['06:00 PM', '07:00 PM', '07:30 PM', '08:00 PM', '08:30 PM', '09:00 PM'],
        'weights': [0.10, 0.18, 0.20, 0.22, 0.17, 0.13],
        'period':  'dinner',
    },
    'Japanese': {
        'slots':   ['06:00 PM', '06:30 PM', '07:00 PM', '07:30 PM', '08:00 PM', '08:30 PM'],
        'weights': [0.12, 0.15, 0.20, 0.22, 0.18, 0.13],
        'period':  'dinner',
    },
    'Healthy_Vegan': {
        'slots':   ['11:00 AM', '11:30 AM', '12:00 PM', '12:30 PM', '01:00 PM'],
        'weights': [0.10, 0.18, 0.28, 0.25, 0.19],
        'period':  'lunch',
    },
    'Steakhouse': {
        'slots':   ['07:00 PM', '07:30 PM', '08:00 PM', '08:30 PM', '09:00 PM'],
        'weights': [0.12, 0.20, 0.25, 0.23, 0.20],
        'period':  'dinner',
    },
}

def slot_to_period(slot_str):
    """Map a time slot string to morning/lunch/dinner."""
    hh = int(slot_str[:2])
    am_pm = slot_str[-2:]
    if am_pm == 'AM':
        return 'morning' if hh < 11 else 'lunch'
    else:  # PM
        if hh == 12:
            return 'lunch'
        if hh <= 3:
            return 'lunch'
        return 'dinner'

ITEM_SEASONALITY = {
    'Iced Latte': 'summer', 'Cold Brew Coffee': 'summer', 'Iced Tea': 'summer',
    'Fruit Smoothie': 'summer', 'Orange Juice': 'summer', 'Coconut Water': 'summer',
    'Cold Pressed Green Juice': 'summer', 'Kombucha (Ginger)': 'summer',
    'Acai Berry Bowl': 'summer', 'Kale & Sweet Potato Salad': 'summer',
    'Vegan Buddha Bowl': 'summer', 'Caprese Salad': 'summer',
    'Lemon Gelato': 'summer', 'Green Tea Mochi Ice Cream': 'summer',
    'Vanilla Milkshake': 'summer',
    'Classic Margarita': 'summer', 'Spicy Jalapeno Margarita': 'summer',
    'Corona Extra': 'summer', 'Modelo Especial': 'summer', 'Peroni Beer': 'summer',
    'Sapporo Draft': 'summer',
    'White Wine (Pinot Grigio)': 'summer', 'Prosecco': 'summer', 'Chardonnay (Glass)': 'summer',
    'Horchata': 'summer', 'Mexican Coke (Glass Bottle)': 'summer',
    'Grilled Atlantic Salmon': 'summer', 'Grilled Asparagus': 'summer',
    'Espresso': 'winter', 'Cappuccino': 'winter', 'Caramel Macchiato': 'winter',
    'Matcha Green Tea Latte': 'winter', 'Black Tea': 'winter',
    'Hot Sake (Small)': 'winter', 'Green Tea': 'winter',
    'Oatmeal with Berries': 'winter',
    'Pork Ramen': 'winter', 'Vegetable Udon': 'winter',
    'Beef Lasagna': 'winter', 'Fettuccine Alfredo': 'winter', 'Spaghetti Carbonara': 'winter',
    'Creamed Spinach': 'winter', 'Garlic Mashed Potatoes': 'winter', 'Truffle Mac & Cheese': 'winter',
    'Mac & Cheese': 'winter',
    'Red Wine (Chianti)': 'winter', 'Red Wine (Cabernet)': 'winter',
    'Premium Cabernet Sauvignon (Glass)': 'winter', 'Old Fashioned Cocktail': 'winter',
    'Apple Pie': 'winter', 'Chocolate Brownie': 'winter', 'Tiramisu': 'winter',
    'Crème Brûlée': 'winter', 'New York Cheesecake': 'winter',
    '14oz Ribeye': 'winter', 'Herb-Crusted Rack of Lamb': 'winter',
    '8oz Filet Mignon': 'winter',
}

SEASONAL_AMPLITUDE = 0.35

def season_multiplier(item_name, month):
    season = ITEM_SEASONALITY.get(item_name, 'neutral')
    if season == 'summer':
        return 1.0 + SEASONAL_AMPLITUDE * np.cos((month - 7) * np.pi / 6)
    if season == 'winter':
        return 1.0 + SEASONAL_AMPLITUDE * np.cos((month - 1) * np.pi / 6)
    return 1.0

def compute_daily_multiplier(d, section):
    mult = 1.0
    mult *= WEEKDAY_MULT[section][d.weekday()]
    mult *= MONTH_MULT[d.month - 1]
    days_elapsed = (d - DATE_START).days
    mult *= 1.0 + TREND_TOTAL_GROWTH * (days_elapsed / TOTAL_DAYS)
    if d in HOLIDAYS:
        mult *= HOLIDAY_EFFECTS[HOLIDAYS[d]]
    if d in RAMADAN_DAYS:
        mult *= RAMADAN_MULT[section]
    if RNG.random() < 0.04:
        mult *= RNG.choice([0.65, 0.75, 1.25, 1.35])
    mult *= max(0.1, RNG.normal(1.0, 0.08))
    return max(mult, 0.05)

# ============================================================================
# 4. CUSTOMER SYSTEM — rich behavioral profiles for Module 4 segmentation
# ============================================================================

ARCHETYPE_DIST = {
    'regular':    {'fraction': 0.15, 'visits': (15, 28)},
    'occasional': {'fraction': 0.30, 'visits': (5, 12)},
    'infrequent': {'fraction': 0.35, 'visits': (2, 4)},
    'one_timer':  {'fraction': 0.20, 'visits': (1, 1)},
}

PRICE_TIERS = ['budget', 'mid', 'premium']
PRICE_TIER_DIST = [0.35, 0.45, 0.20]

TIME_PREFS = ['morning', 'lunch', 'dinner', 'flexible']
TIME_PREF_DIST = [0.18, 0.18, 0.50, 0.14]

DAY_PREFS = ['weekday', 'weekend', 'any']
DAY_PREF_DIST = [0.35, 0.20, 0.45]

BASKET_BIAS = ['small', 'medium', 'large']
BASKET_BIAS_DIST = [0.30, 0.50, 0.20]

SECTIONS_BY_PERIOD = {
    'morning':  ['Cafe'],
    'lunch':    ['Healthy_Vegan', 'American'],
    'dinner':   ['Italian', 'Mexican', 'Japanese', 'Steakhouse', 'American'],
    'flexible': SECTIONS,
}

N_CUSTOMERS = 10000

def generate_customers():
    """Create customer profiles with frequency + behavioral dimensions."""
    customers = []
    cid = 1

    for archetype, params in ARCHETYPE_DIST.items():
        n = int(N_CUSTOMERS * params['fraction'])
        v_min, v_max = params['visits']
        for _ in range(n):
            visits = PY_RNG.randint(v_min, v_max)
            price_tier = PY_RNG.choices(PRICE_TIERS, PRICE_TIER_DIST)[0]
            time_pref = PY_RNG.choices(TIME_PREFS, TIME_PREF_DIST)[0]
            day_pref = PY_RNG.choices(DAY_PREFS, DAY_PREF_DIST)[0]
            basket_bias = PY_RNG.choices(BASKET_BIAS, BASKET_BIAS_DIST)[0]

            pool = SECTIONS_BY_PERIOD[time_pref]
            n_preferred = min(len(pool), PY_RNG.choice([1, 1, 2]))
            preferred_sections = PY_RNG.sample(pool, n_preferred)

            all_cats = ['Beverage', 'Food', 'Main', 'Side', 'Appetizer',
                        'Dessert', 'Alcohol', 'Bakery']
            n_cats = PY_RNG.choice([2, 2, 3])
            preferred_categories = PY_RNG.sample(all_cats, n_cats)

            customers.append({
                'customer_id':          cid,
                'archetype':            archetype,
                'price_tier':           price_tier,
                'time_preference':      time_pref,
                'day_preference':       day_pref,
                'basket_size_bias':     basket_bias,
                'preferred_sections':   preferred_sections,
                'preferred_categories': preferred_categories,
                'expected_visits':      visits,
                'visit_budget':         visits,
            })
            cid += 1

    PY_RNG.shuffle(customers)
    return customers

# ============================================================================
# 5. STAFF SYSTEM — cashiers with shifts
# ============================================================================

CASHIER_SHIFTS = {
    'morning':   ['C01', 'C02', 'C03', 'C04'],  # 07-14
    'afternoon': ['C05', 'C06', 'C07', 'C08'],  # 12-20
    'evening':   ['C09', 'C10', 'C11', 'C12'],  # 17-22
}
ALL_CASHIERS = sorted({c for cs in CASHIER_SHIFTS.values() for c in cs})

def cashier_for_slot(slot_str):
    """Pick a plausible cashier for a given time slot."""
    hh = int(slot_str[:2])
    am_pm = slot_str[-2:]
    h24 = hh if am_pm == 'AM' else (hh if hh == 12 else hh + 12)
    if h24 < 12:
        return PY_RNG.choice(CASHIER_SHIFTS['morning'])
    if h24 < 17:
        return PY_RNG.choice(CASHIER_SHIFTS['morning'] + CASHIER_SHIFTS['afternoon'])
    if h24 < 20:
        return PY_RNG.choice(CASHIER_SHIFTS['afternoon'] + CASHIER_SHIFTS['evening'])
    return PY_RNG.choice(CASHIER_SHIFTS['evening'])

SUSPICIOUS_CASHIER = 'C07'

# ============================================================================
# 6. BASKET GENERATION
# ============================================================================

BASKET_SIZES_BY_BIAS = {
    'small':  ([1, 2, 3, 4, 5], [0.25, 0.40, 0.25, 0.08, 0.02]),
    'medium': ([1, 2, 3, 4, 5], [0.08, 0.30, 0.35, 0.20, 0.07]),
    'large':  ([1, 2, 3, 4, 5], [0.02, 0.15, 0.30, 0.35, 0.18]),
}

def build_base_popularity(menu_items):
    """Stable per-section item popularity (drawn once per run)."""
    w = {}
    for item, (price, cat) in menu_items.items():
        if cat in ('Main', 'Food'):
            w[item] = RNG.uniform(0.8, 1.5)
        elif cat in ('Beverage', 'Alcohol'):
            w[item] = RNG.uniform(0.3, 0.8)
        elif cat in ('Side', 'Appetizer'):
            w[item] = RNG.uniform(0.3, 0.7)
        elif cat == 'Bakery':
            w[item] = RNG.uniform(0.4, 0.9)
        else:
            w[item] = RNG.uniform(0.15, 0.4)
    return w

def build_affinity_map(affinities):
    amap = {}
    for a, b, boost in affinities:
        amap.setdefault(a, {})[b] = boost
        amap.setdefault(b, {})[a] = boost
    return amap

def apply_customer_weights(base_weights, menu_items, customer, month):
    """Apply customer preferences to item weights for this specific order."""
    adj = {}
    for item, w in base_weights.items():
        price, cat = menu_items[item]
        new_w = w * season_multiplier(item, month)
        if customer is not None:
            pt = customer['price_tier']
            if pt == 'budget':
                if price < 8:
                    new_w *= 1.8
                elif price >= 15:
                    new_w *= 0.25
            elif pt == 'premium':
                if price >= 15:
                    new_w *= 1.9
                elif price < 6:
                    new_w *= 0.5
            if cat in customer['preferred_categories']:
                new_w *= 1.8
        adj[item] = new_w
    return adj

def generate_basket(menu_items, base_pop, affinity_map, customer, month):
    items = list(menu_items.keys())
    bias = customer['basket_size_bias'] if customer is not None else 'medium'
    sizes, probs = BASKET_SIZES_BY_BIAS[bias]
    basket_size = RNG.choice(sizes, p=probs)

    weights_today = apply_customer_weights(base_pop, menu_items, customer, month)

    anchor_probs = np.array([weights_today[it] for it in items], dtype=float)
    anchor_probs /= anchor_probs.sum()
    anchor = RNG.choice(items, p=anchor_probs)
    basket = [anchor]

    for _ in range(basket_size - 1):
        remaining = [it for it in items if it not in basket]
        if not remaining:
            break
        adj = []
        for cand in remaining:
            p = weights_today[cand]
            for in_basket in basket:
                if in_basket in affinity_map and cand in affinity_map[in_basket]:
                    p *= affinity_map[in_basket][cand]
            p *= RNG.uniform(0.5, 1.5)
            adj.append(p)
        adj = np.array(adj, dtype=float)
        adj /= adj.sum()
        basket.append(RNG.choice(remaining, p=adj))

    return basket

# ============================================================================
# 7. CUSTOMER SELECTION per order
# ============================================================================

def customer_compatibility(customer, section, weekday, period):
    """Return a score for how well this customer fits the given slot."""
    if customer['visit_budget'] <= 0:
        return 0.0
    score = 1.0
    if section in customer['preferred_sections']:
        score *= 3.5
    else:
        score *= 0.6
    is_weekend = weekday >= 5
    if customer['day_preference'] == 'weekday' and not is_weekend:
        score *= 1.5
    elif customer['day_preference'] == 'weekend' and is_weekend:
        score *= 1.5
    elif customer['day_preference'] == 'any':
        pass
    else:
        score *= 0.55
    if customer['time_preference'] == period:
        score *= 2.0
    elif customer['time_preference'] == 'flexible':
        score *= 1.1
    else:
        score *= 0.35
    score *= np.sqrt(customer['visit_budget'])
    return score

def sample_customer(active_pool, section, weekday, period):
    """Pick a customer for this order, or None (for walk-in anonymous)."""
    if not active_pool:
        return None
    scores = np.array(
        [customer_compatibility(c, section, weekday, period) for c in active_pool],
        dtype=float
    )
    total = scores.sum()
    if total <= 0:
        return None
    scores /= total
    idx = RNG.choice(len(active_pool), p=scores)
    chosen = active_pool[idx]
    chosen['visit_budget'] -= 1
    return chosen

# ============================================================================
# 8. PAYMENT & TABLE
# ============================================================================

def pick_payment_method(order_total):
    """Payment method depends loosely on order size."""
    if order_total < 10:
        return PY_RNG.choices(['cash', 'card', 'mobile'], [0.55, 0.30, 0.15])[0]
    if order_total < 30:
        return PY_RNG.choices(['cash', 'card', 'mobile'], [0.30, 0.50, 0.20])[0]
    return PY_RNG.choices(['cash', 'card', 'mobile'], [0.15, 0.65, 0.20])[0]

def pick_table(section):
    """30% takeaway, 70% dine-in."""
    if RNG.random() < 0.30:
        return None
    return int(RNG.integers(1, 26))

def pick_discount(is_holiday):
    """Legit discount: 0% most of the time, 5-20% sometimes, higher on holidays."""
    r = RNG.random()
    if is_holiday:
        if r < 0.80:
            return 0.0
        if r < 0.95:
            return float(RNG.choice([10, 15, 20]))
        return float(RNG.choice([25, 30]))
    else:
        if r < 0.90:
            return 0.0
        if r < 0.98:
            return float(RNG.choice([5, 10, 15]))
        return float(RNG.choice([20, 25]))

# ============================================================================
# 9. MAIN GENERATION LOOP
# ============================================================================

def generate_main():
    print("=" * 70)
    print("ENTERPRISE POS DATASET GENERATOR V6 — Definitive Edition")
    print(f"Period: {DATE_START} → {DATE_END} ({TOTAL_DAYS} days)")
    print("=" * 70)

    print("\n[1/4] Generating customer profiles...")
    customers = generate_customers()
    print(f"      → {len(customers)} customers")
    by_arch = Counter(c['archetype'] for c in customers)
    for a, n in by_arch.items():
        print(f"          {a:>12}: {n}")

    print("\n[2/4] Building base popularities and affinity maps...")
    base_pops = {s: build_base_popularity(menus[s]) for s in SECTIONS}
    aff_maps = {s: build_affinity_map(AFFINITIES[s]) for s in SECTIONS}

    print("\n[3/4] Generating transactions...")
    rows = []
    order_id = 100000
    detail_id = 500000
    section_counts = {s: 0 for s in SECTIONS}

    current = DATE_START
    while current <= DATE_END:
        is_holiday = current in HOLIDAYS
        for section in SECTIONS:
            mult = compute_daily_multiplier(current, section)
            expected = BASE_DAILY[section] * mult
            n_orders_today = RNG.poisson(expected)

            slots = TIME_DISTRIBUTIONS[section]['slots']
            slot_weights = TIME_DISTRIBUTIONS[section]['weights']

            for _ in range(n_orders_today):
                slot = RNG.choice(slots, p=slot_weights)
                period = slot_to_period(slot)

                if len(customers) > 400:
                    pool_sample = PY_RNG.sample(customers, 400)
                else:
                    pool_sample = customers
                cust = sample_customer(pool_sample, section, current.weekday(), period)

                basket = generate_basket(
                    menus[section], base_pops[section], aff_maps[section],
                    cust, current.month
                )

                total_pre = sum(menus[section][it][0] for it in basket)
                discount_pct = pick_discount(is_holiday)
                payment = pick_payment_method(total_pre * (1 - discount_pct / 100))
                cashier = cashier_for_slot(slot)
                table = pick_table(section)

                for item_name in basket:
                    price, category = menus[section][item_name]
                    line_total = round(price * (1 - discount_pct / 100), 2)
                    rows.append({
                        'order_details_id': detail_id,
                        'order_id':         order_id,
                        'order_date':       current.strftime('%Y-%m-%d'),
                        'order_time':       slot,
                        'item_name':        item_name,
                        'category':         category,
                        'price':            price,
                        'restaurant_type':  section,
                        'customer_id':      cust['customer_id'] if cust else 0,
                        'cashier_id':       cashier,
                        'payment_method':   payment,
                        'table_number':     table if table is not None else '',
                        'is_voided':        False,
                        'void_reason':      '',
                        'discount_pct':     discount_pct,
                        'line_total':       line_total,
                    })
                    detail_id += 1
                order_id += 1
                section_counts[section] += 1

        current += timedelta(days=1)
        if (current - DATE_START).days % 60 == 0:
            total_so_far = sum(section_counts.values())
            print(f"      day {(current - DATE_START).days}/{TOTAL_DAYS}  |  "
                  f"{total_so_far:,} orders")

    print(f"      done: {sum(section_counts.values()):,} orders generated")
    return rows, customers, section_counts

# ============================================================================
# 10. ANOMALY INJECTION — 6 labeled types
# ============================================================================

def inject_anomalies(rows):
    """
    Post-process rows to inject 6 types of labeled anomalies.
    Returns a list of (order_id, anomaly_type, description) tuples.
    """
    df = pd.DataFrame(rows)
    anomaly_log = []

    order_groups = df.groupby('order_id').indices
    order_ids = list(order_groups.keys())
    n_orders = len(order_ids)

    # ---- 1. void_after_payment (~0.15%)
    n_type1 = int(n_orders * 0.0015)
    chosen = PY_RNG.sample(order_ids, n_type1)
    for oid in chosen:
        idxs = order_groups[oid]
        df.loc[idxs, 'is_voided'] = True
        df.loc[idxs, 'void_reason'] = 'customer_complaint'
        if RNG.random() < 0.6:
            df.loc[idxs, 'cashier_id'] = SUSPICIOUS_CASHIER
        anomaly_log.append((oid, 'void_after_payment',
                            'Paid order voided with weak reason'))

    # ---- 2. suspicious_discount (~0.20%)
    n_type2 = int(n_orders * 0.0020)
    remaining = [o for o in order_ids if o not in chosen]
    chosen2 = PY_RNG.sample(remaining, n_type2)
    for oid in chosen2:
        idxs = order_groups[oid]
        pct = float(PY_RNG.choice([75, 80, 85, 90, 95]))
        df.loc[idxs, 'discount_pct'] = pct
        df.loc[idxs, 'line_total'] = (
            df.loc[idxs, 'price'] * (1 - pct / 100)
        ).round(2)
        if RNG.random() < 0.5:
            df.loc[idxs, 'cashier_id'] = SUSPICIOUS_CASHIER
        anomaly_log.append((oid, 'suspicious_discount',
                            f'Discount {pct}% (>70% threshold)'))

    # ---- 3. price_tampering (~0.10%)
    n_type3 = int(n_orders * 0.0010)
    remaining = [o for o in order_ids if o not in chosen and o not in chosen2]
    chosen3 = PY_RNG.sample(remaining, n_type3)
    for oid in chosen3:
        idxs = order_groups[oid]
        target_idx = PY_RNG.choice(list(idxs))
        orig = df.at[target_idx, 'price']
        tampered = round(orig * PY_RNG.uniform(0.30, 0.50), 2)
        df.at[target_idx, 'price'] = tampered
        df.at[target_idx, 'line_total'] = round(
            tampered * (1 - df.at[target_idx, 'discount_pct'] / 100), 2
        )
        anomaly_log.append((oid, 'price_tampering',
                            f'Line item price {orig} → {tampered}'))

    # ---- 4. odd_hour (~0.10%)
    n_type4 = int(n_orders * 0.0010)
    used = set(chosen) | set(chosen2) | set(chosen3)
    remaining = [o for o in order_ids if o not in used]
    chosen4 = PY_RNG.sample(remaining, n_type4)
    odd_hours = ['03:00 AM', '03:30 AM', '04:00 AM', '11:30 PM', '12:30 AM']
    for oid in chosen4:
        idxs = order_groups[oid]
        df.loc[idxs, 'order_time'] = PY_RNG.choice(odd_hours)
        anomaly_log.append((oid, 'odd_hour',
                            'Transaction logged outside operating hours'))

    # ---- 5. basket_size_outlier (~0.15%)
    n_type5 = int(n_orders * 0.0015)
    new_rows = []
    max_od = df['order_details_id'].max() + 1
    max_oid = df['order_id'].max() + 1
    for _ in range(n_type5):
        section = PY_RNG.choice(SECTIONS)
        items_in_section = list(menus[section].keys())
        big_size = PY_RNG.randint(15, 22)
        chosen_items = PY_RNG.choices(items_in_section, k=big_size)
        template = df.iloc[PY_RNG.randrange(len(df))]
        for it in chosen_items:
            price, cat = menus[section][it]
            new_rows.append({
                'order_details_id': max_od,
                'order_id':         max_oid,
                'order_date':       template['order_date'],
                'order_time':       template['order_time'],
                'item_name':        it,
                'category':         cat,
                'price':            price,
                'restaurant_type':  section,
                'customer_id':      0,
                'cashier_id':       cashier_for_slot(template['order_time']),
                'payment_method':   'cash',
                'table_number':     int(RNG.integers(1, 26)),
                'is_voided':        False,
                'void_reason':      '',
                'discount_pct':     0.0,
                'line_total':       price,
            })
            max_od += 1
        anomaly_log.append((max_oid, 'basket_size_outlier',
                            f'Basket of {big_size} items'))
        max_oid += 1

    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

    # ---- 6. shift_end_void_cluster (~8 clusters of 3-5 voids each)
    n_clusters = 8
    late_orders = df[df['order_time'].isin(
        ['01:00 PM', '08:00 PM', '08:30 PM', '09:00 PM']
    )].copy()
    late_order_ids = late_orders['order_id'].unique().tolist()

    for _ in range(n_clusters):
        if len(late_order_ids) < 5:
            break
        cluster_size = PY_RNG.randint(3, 5)
        cluster = PY_RNG.sample(late_order_ids, cluster_size)
        for oid in cluster:
            idxs = df.index[df['order_id'] == oid]
            df.loc[idxs, 'is_voided'] = True
            df.loc[idxs, 'void_reason'] = 'item_unavailable'
            df.loc[idxs, 'cashier_id'] = SUSPICIOUS_CASHIER
            anomaly_log.append((int(oid), 'shift_end_void_cluster',
                                'Part of cluster of end-of-shift voids'))
            late_order_ids.remove(oid)

    # Inject normal (non-anomalous) voids at ~1.5% rate
    anomalous_ids = {a[0] for a in anomaly_log}
    non_anomalous = [o for o in order_ids if o not in anomalous_ids]
    n_normal_voids = int(len(non_anomalous) * 0.015)
    normal_void_ids = PY_RNG.sample(non_anomalous, n_normal_voids)
    for oid in normal_void_ids:
        idxs = df.index[df['order_id'] == oid]
        df.loc[idxs, 'is_voided'] = True
        df.loc[idxs, 'void_reason'] = PY_RNG.choice(
            ['customer_changed_mind', 'wrong_order', 'item_unavailable']
        )

    # Track normal-void count for the summary print (clean separation)
    n_normal_voids_logged = len(normal_void_ids)

    return df, anomaly_log, n_normal_voids_logged

# ============================================================================
# 11. MAIN — assemble and save everything
# ============================================================================

def main():
    rows, customers, section_counts = generate_main()

    print("\n[4/4] Injecting anomalies...")
    df, anomaly_log, n_normal_voids = inject_anomalies(rows)

    # Add item_id
    item_ids = {name: i + 1 for i, name in enumerate(sorted(df['item_name'].unique()))}
    df['item_id'] = df['item_name'].map(item_ids)

    # Reorder columns
    col_order = [
        'order_details_id', 'order_id', 'order_date', 'order_time',
        'item_name', 'category', 'price', 'restaurant_type', 'item_id',
        'customer_id', 'cashier_id', 'payment_method', 'table_number',
        'is_voided', 'void_reason', 'discount_pct', 'line_total',
    ]
    df = df[col_order].sort_values(['order_date', 'order_id']).reset_index(drop=True)

    df.to_csv(OUTPUT_MAIN, sep='|', index=False)

    # Save customers
    cust_rows = []
    for c in customers:
        cust_rows.append({
            'customer_id':          c['customer_id'],
            'archetype':            c['archetype'],
            'price_tier':           c['price_tier'],
            'time_preference':      c['time_preference'],
            'day_preference':       c['day_preference'],
            'basket_size_bias':     c['basket_size_bias'],
            'preferred_sections':   ','.join(c['preferred_sections']),
            'preferred_categories': ','.join(c['preferred_categories']),
            'expected_visits':      c['expected_visits'],
            'actual_visits':        c['expected_visits'] - c['visit_budget'],
        })
    pd.DataFrame(cust_rows).to_csv(OUTPUT_CUSTOMERS, index=False)

    # Save anomalies
    pd.DataFrame(anomaly_log, columns=['order_id', 'anomaly_type', 'description'])\
        .to_csv(OUTPUT_ANOMALIES, index=False)

    # Save cashiers
    cashier_rows = []
    for shift, cs in CASHIER_SHIFTS.items():
        for c in cs:
            cashier_rows.append({
                'cashier_id': c,
                'shift':      shift,
                'flagged':    c == SUSPICIOUS_CASHIER,
            })
    pd.DataFrame(cashier_rows).to_csv(OUTPUT_CASHIERS, index=False)

    # ---- Summary
    total_orders = df['order_id'].nunique()
    # Count voided ORDERS (not line items) for accurate reporting
    voided_orders = df[df['is_voided']]['order_id'].nunique()
    anom_void_types = {'void_after_payment', 'shift_end_void_cluster'}
    anomaly_voided_orders = len({a[0] for a in anomaly_log if a[1] in anom_void_types})
    non_anomaly_voids = voided_orders - anomaly_voided_orders

    print(f"\n{'=' * 70}")
    print("DATASET SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Total line items:    {len(df):,}")
    print(f"  Total orders:        {total_orders:,}")
    print(f"  Unique items:        {df['item_name'].nunique()}")
    print(f"  Avg basket size:     {len(df) / total_orders:.2f}")
    print(f"  Orders/day average:  {total_orders / TOTAL_DAYS:.1f}")
    print(f"  Customers:           {len(customers)}")
    print(f"  Cashiers:            {len(ALL_CASHIERS)}")
    print(f"  Labeled anomalies:   {len(anomaly_log)}")
    print(f"  Voided orders total: {voided_orders} "
          f"(of which {anomaly_voided_orders} are labeled anomalies, "
          f"{non_anomaly_voids} are normal voids)")
    print(f"\n  Per-section orders:")
    for s, n in section_counts.items():
        print(f"    {s:>15}: {n:>6,}")
    print(f"\n  Anomaly breakdown:")
    anom_counts = Counter(a[1] for a in anomaly_log)
    for typ, n in anom_counts.items():
        print(f"    {typ:>25}: {n:>4}")
    print(f"\n  Output files:")
    for f in [OUTPUT_MAIN, OUTPUT_CUSTOMERS, OUTPUT_ANOMALIES, OUTPUT_CASHIERS]:
        print(f"    {f}")
    print(f"{'=' * 70}")

    return df, customers, anomaly_log

if __name__ == '__main__':
    main()
