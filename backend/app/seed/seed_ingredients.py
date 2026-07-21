"""
Ingredient Seed Data
~45 base ingredients with realistic recipes for all 122 menu items.
Quantities are per 1 serving, in the ingredient's unit (g, ml, pcs).
"""
from app.products.models import Ingredient, ProductIngredient, Product


# ─── INGREDIENTS ────────────────────────────────────────────────────────────────
# (name, unit, initial_stock, low_threshold, cost_per_unit_DT, supplier, category)
INGREDIENTS = [
    # ── Proteins ──
    ("Beef Ribeye (Raw)",       "g",   8000,  3000, 0.065, "Quality Meats Ltd.",        "Protein"),
    ("Beef Filet Mignon (Raw)", "g",   5000,  2000, 0.085, "Quality Meats Ltd.",        "Protein"),
    ("Ground Beef",             "g",  12000,  4000, 0.028, "Quality Meats Ltd.",        "Protein"),
    ("Chicken Breast",          "g",  15000,  5000, 0.018, "Fresh Farm Suppliers",      "Protein"),
    ("Chicken Wings",           "g",   8000,  3000, 0.015, "Fresh Farm Suppliers",      "Protein"),
    ("Pork Shoulder",           "g",   6000,  2500, 0.022, "Quality Meats Ltd.",        "Protein"),
    ("Ground Pork",             "g",   4000,  1500, 0.020, "Quality Meats Ltd.",        "Protein"),
    ("Bacon",                   "g",   5000,  2000, 0.035, "Quality Meats Ltd.",        "Protein"),
    ("Lamb Rack (Raw)",         "g",   4000,  1500, 0.090, "Mediterranean Imports Co.", "Protein"),
    ("Salmon Fillet",           "g",   6000,  2500, 0.055, "Ocean Fresh Seafood",       "Protein"),
    ("Sashimi-Grade Tuna",      "g",   3000,  1200, 0.075, "Ocean Fresh Seafood",       "Protein"),
    ("Shrimp (Peeled)",         "g",   4000,  1500, 0.060, "Ocean Fresh Seafood",       "Protein"),
    ("Lobster Meat",            "g",   2000,   800, 0.120, "Ocean Fresh Seafood",       "Protein"),
    ("Calamari (Rings)",        "g",   3000,  1200, 0.040, "Ocean Fresh Seafood",       "Protein"),
    ("Fresh Oysters",           "pcs",  120,    40, 1.200, "Ocean Fresh Seafood",       "Protein"),
    ("Pepperoni",               "g",   3000,  1000, 0.030, "Italian Cheese Imports",    "Protein"),
    ("Prosciutto",              "g",   2000,   800, 0.065, "Italian Cheese Imports",    "Protein"),
    ("Hot Dog Sausage",         "pcs",   60,    20, 0.800, "Quality Meats Ltd.",        "Protein"),
    ("Firm Tofu",               "g",   5000,  2000, 0.008, "Fresh Farm Suppliers",      "Protein"),
    ("Eggs",                    "pcs",  200,    60, 0.350, "Fresh Farm Suppliers",      "Protein"),

    # ── Dairy ──
    ("Mozzarella Cheese",       "g",   8000,  3000, 0.022, "Italian Cheese Imports",    "Dairy"),
    ("Cheddar Cheese",          "g",   5000,  2000, 0.020, "Dairy Direct Co.",          "Dairy"),
    ("Parmesan Cheese",         "g",   3000,  1000, 0.045, "Italian Cheese Imports",    "Dairy"),
    ("Cream Cheese",            "g",   3000,  1000, 0.015, "Dairy Direct Co.",          "Dairy"),
    ("Heavy Cream",             "ml",  8000,  3000, 0.008, "Dairy Direct Co.",          "Dairy"),
    ("Butter",                  "g",   5000,  2000, 0.012, "Dairy Direct Co.",          "Dairy"),
    ("Whole Milk",              "ml", 25000, 10000, 0.003, "Dairy Direct Co.",          "Dairy"),
    ("Ricotta Cheese",          "g",   2000,   800, 0.018, "Italian Cheese Imports",    "Dairy"),

    # ── Grains & Carbs ──
    ("Pizza Dough",             "g",  15000,  5000, 0.005, "Artisan Bakery Supply",     "Grain"),
    ("Pasta (Dry)",             "g",  12000,  4000, 0.006, "Italian Cheese Imports",    "Grain"),
    ("Sushi Rice",              "g",  10000,  4000, 0.004, "Japanese Food Imports",     "Grain"),
    ("White Rice",              "g",   8000,  3000, 0.003, "Global Spices Inc.",        "Grain"),
    ("Burger Buns",             "pcs",  100,    30, 0.400, "Artisan Bakery Supply",     "Grain"),
    ("Flour Tortillas",         "pcs",  150,    50, 0.250, "Mexican Food Supply",       "Grain"),
    ("Udon Noodles",            "g",   5000,  2000, 0.008, "Japanese Food Imports",     "Grain"),
    ("All-Purpose Flour",       "g",  20000,  6000, 0.002, "Artisan Bakery Supply",     "Grain"),
    ("Tortilla Chips",          "g",   8000,  3000, 0.006, "Mexican Food Supply",       "Grain"),
    ("Bread Slices",            "pcs",  120,    40, 0.200, "Artisan Bakery Supply",     "Grain"),
    ("Croissant Dough",         "g",   6000,  2000, 0.012, "Artisan Bakery Supply",     "Grain"),
    ("Bagels",                  "pcs",   60,    20, 0.550, "Artisan Bakery Supply",     "Grain"),
    ("Hot Dog Buns",            "pcs",   60,    20, 0.350, "Artisan Bakery Supply",     "Grain"),
    ("Pita Bread",              "pcs",   80,    30, 0.300, "Mediterranean Imports Co.", "Grain"),
    ("Gnocchi (Fresh)",         "g",   3000,  1000, 0.014, "Italian Cheese Imports",    "Grain"),
    ("Oats",                    "g",   5000,  2000, 0.004, "Fresh Farm Suppliers",      "Grain"),
    ("Quinoa",                  "g",   3000,  1200, 0.012, "Fresh Farm Suppliers",      "Grain"),

    # ── Vegetables & Fruits ──
    ("Tomatoes",                "g",  15000,  5000, 0.005, "Fresh Farm Suppliers",      "Vegetable"),
    ("Lettuce (Mixed Greens)",  "g",   8000,  3000, 0.008, "Fresh Farm Suppliers",      "Vegetable"),
    ("Onions",                  "g",   8000,  3000, 0.003, "Fresh Farm Suppliers",      "Vegetable"),
    ("Garlic",                  "g",   2000,   600, 0.010, "Fresh Farm Suppliers",      "Vegetable"),
    ("Avocado",                 "pcs",   80,    25, 1.500, "Mexican Food Supply",       "Vegetable"),
    ("Jalapeño Peppers",        "g",   2000,   800, 0.008, "Mexican Food Supply",       "Vegetable"),
    ("Bell Peppers",            "g",   5000,  2000, 0.007, "Fresh Farm Suppliers",      "Vegetable"),
    ("Fresh Spinach",           "g",   5000,  2000, 0.010, "Fresh Farm Suppliers",      "Vegetable"),
    ("Kale",                    "g",   3000,  1200, 0.012, "Fresh Farm Suppliers",      "Vegetable"),
    ("Sweet Potatoes",          "g",   6000,  2500, 0.004, "Fresh Farm Suppliers",      "Vegetable"),
    ("Potatoes",                "g",  15000,  5000, 0.003, "Fresh Farm Suppliers",      "Vegetable"),
    ("Mushrooms",               "g",   4000,  1500, 0.015, "Fresh Farm Suppliers",      "Vegetable"),
    ("Asparagus",               "g",   3000,  1200, 0.020, "Fresh Farm Suppliers",      "Vegetable"),
    ("Fresh Basil",             "g",   1500,   500, 0.025, "Fresh Farm Suppliers",      "Vegetable"),
    ("Edamame (Shelled)",       "g",   3000,  1200, 0.010, "Japanese Food Imports",     "Vegetable"),
    ("Nori Seaweed Sheets",     "pcs",  200,    60, 0.300, "Japanese Food Imports",     "Vegetable"),
    ("Lemons",                  "pcs",  100,    30, 0.400, "Fresh Farm Suppliers",      "Fruit"),
    ("Mixed Berries",           "g",   4000,  1500, 0.020, "Fresh Farm Suppliers",      "Fruit"),
    ("Bananas",                 "pcs",   80,    25, 0.300, "Fresh Farm Suppliers",      "Fruit"),
    ("Apples",                  "pcs",   60,    20, 0.500, "Fresh Farm Suppliers",      "Fruit"),
    ("Oranges",                 "pcs",  100,    30, 0.450, "Fresh Farm Suppliers",      "Fruit"),
    ("Acai Puree (Frozen)",     "g",   2000,   800, 0.040, "Fresh Farm Suppliers",      "Fruit"),
    ("Chickpeas (Cooked)",      "g",   5000,  2000, 0.005, "Mediterranean Imports Co.", "Vegetable"),
    ("Arugula",                 "g",   2000,   800, 0.015, "Fresh Farm Suppliers",      "Vegetable"),

    # ── Sauces & Condiments ──
    ("Tomato Sauce",            "ml", 10000,  4000, 0.004, "Italian Cheese Imports",    "Sauce"),
    ("Soy Sauce",               "ml",  5000,  2000, 0.005, "Japanese Food Imports",     "Sauce"),
    ("Teriyaki Sauce",          "ml",  3000,  1200, 0.008, "Japanese Food Imports",     "Sauce"),
    ("BBQ Sauce",               "ml",  4000,  1500, 0.006, "Global Spices Inc.",        "Sauce"),
    ("Salsa (House-Made)",      "ml",  5000,  2000, 0.005, "Mexican Food Supply",       "Sauce"),
    ("Basil Pesto",             "g",   2000,   800, 0.025, "Italian Cheese Imports",    "Sauce"),
    ("Olive Oil (Extra Virgin)","ml", 10000,  4000, 0.010, "Mediterranean Imports Co.", "Sauce"),
    ("Sesame Oil",              "ml",  2000,   800, 0.012, "Japanese Food Imports",     "Sauce"),
    ("Yellow Mustard",          "ml",  3000,  1000, 0.004, "Global Spices Inc.",        "Sauce"),
    ("Mayonnaise",              "ml",  4000,  1500, 0.005, "Global Spices Inc.",        "Sauce"),
    ("Alfredo Sauce",           "ml",  4000,  1500, 0.010, "Italian Cheese Imports",    "Sauce"),
    ("Miso Paste",              "g",   2000,   800, 0.015, "Japanese Food Imports",     "Sauce"),
    ("Hummus",                  "g",   3000,  1200, 0.010, "Mediterranean Imports Co.", "Sauce"),
    ("Guacamole (House-Made)",  "g",   3000,  1200, 0.018, "Mexican Food Supply",       "Sauce"),
    ("Enchilada Sauce",         "ml",  3000,  1200, 0.006, "Mexican Food Supply",       "Sauce"),
    ("Queso Cheese Sauce",      "ml",  3000,  1200, 0.008, "Mexican Food Supply",       "Sauce"),
    ("Cocktail Sauce",          "ml",  2000,   800, 0.008, "Global Spices Inc.",        "Sauce"),
    ("Vinaigrette Dressing",    "ml",  3000,  1200, 0.007, "Mediterranean Imports Co.", "Sauce"),

    # ── Beverages Base ──
    ("Coffee Beans (Arabica)",  "g",   8000,  3000, 0.030, "Global Spices Inc.",        "Beverage"),
    ("Black Tea Leaves",        "g",   2000,   800, 0.025, "Global Spices Inc.",        "Beverage"),
    ("Green Tea Leaves",        "g",   2000,   800, 0.028, "Japanese Food Imports",     "Beverage"),
    ("Matcha Powder",           "g",   1000,   400, 0.080, "Japanese Food Imports",     "Beverage"),
    ("Coca-Cola (Cans)",        "pcs",  120,    40, 0.600, "Beverage Distributors",     "Beverage"),
    ("Diet Coke (Cans)",        "pcs",   80,    25, 0.600, "Beverage Distributors",     "Beverage"),
    ("Sprite (Cans)",           "pcs",   80,    25, 0.600, "Beverage Distributors",     "Beverage"),
    ("Dr Pepper (Cans)",        "pcs",   60,    20, 0.600, "Beverage Distributors",     "Beverage"),
    ("Corona Extra (Bottles)",  "pcs",   72,    24, 1.800, "Beverage Distributors",     "Beverage"),
    ("Modelo Especial (Btl)",   "pcs",   60,    20, 1.800, "Beverage Distributors",     "Beverage"),
    ("Sapporo Draft (Cans)",    "pcs",   48,    16, 2.000, "Japanese Food Imports",     "Beverage"),
    ("Peroni Beer (Bottles)",   "pcs",   48,    16, 1.900, "Italian Cheese Imports",    "Beverage"),
    ("Chardonnay (Bottle)",     "ml",  9000,  3000, 0.020, "Wine & Spirits Co.",        "Beverage"),
    ("Cabernet Sauvignon (Btl)","ml", 12000,  4000, 0.025, "Wine & Spirits Co.",        "Beverage"),
    ("Chianti (Bottle)",        "ml",  7500,  3000, 0.022, "Italian Cheese Imports",    "Beverage"),
    ("Pinot Grigio (Bottle)",   "ml",  7500,  3000, 0.018, "Italian Cheese Imports",    "Beverage"),
    ("Prosecco (Bottle)",       "ml",  6000,  2000, 0.022, "Italian Cheese Imports",    "Beverage"),
    ("Tequila (Blanco)",        "ml",  5000,  2000, 0.040, "Wine & Spirits Co.",        "Beverage"),
    ("Bourbon Whiskey",         "ml",  4000,  1500, 0.050, "Wine & Spirits Co.",        "Beverage"),
    ("Sake",                    "ml",  4000,  1500, 0.025, "Japanese Food Imports",     "Beverage"),
    ("Orange Juice (Fresh)",    "ml", 10000,  4000, 0.006, "Fresh Farm Suppliers",      "Beverage"),
    ("Coconut Water",           "pcs",   60,    20, 1.200, "Fresh Farm Suppliers",      "Beverage"),
    ("Kombucha (Ginger)",       "pcs",   48,    16, 2.200, "Fresh Farm Suppliers",      "Beverage"),
    ("Horchata Mix",            "g",   2000,   800, 0.010, "Mexican Food Supply",       "Beverage"),

    # ── Baking & Sweets ──
    ("Granulated Sugar",        "g",  10000,  3000, 0.002, "Global Spices Inc.",        "Baking"),
    ("Dark Chocolate",          "g",   3000,  1200, 0.025, "Artisan Bakery Supply",     "Baking"),
    ("Vanilla Extract",         "ml",  1000,   300, 0.060, "Global Spices Inc.",        "Baking"),
    ("Peanut Butter",           "g",   2000,   800, 0.012, "Fresh Farm Suppliers",      "Baking"),
    ("Cocoa Powder",            "g",   2000,   800, 0.020, "Artisan Bakery Supply",     "Baking"),
    ("Powdered Sugar",          "g",   3000,  1000, 0.003, "Artisan Bakery Supply",     "Baking"),
    ("Mascarpone",              "g",   2000,   800, 0.028, "Italian Cheese Imports",    "Dairy"),
    ("Ladyfinger Biscuits",     "pcs",  200,    60, 0.150, "Artisan Bakery Supply",     "Baking"),
    ("Caramel Sauce",           "ml",  2000,   800, 0.012, "Artisan Bakery Supply",     "Baking"),
    ("Gelato Base Mix",         "g",   3000,  1200, 0.015, "Italian Cheese Imports",    "Baking"),
    ("Whipped Cream",           "ml",  5000,  2000, 0.008, "Dairy Direct Co.",          "Dairy"),
    ("Mochi Dough (Premade)",   "g",   1500,   600, 0.020, "Japanese Food Imports",     "Baking"),
    ("Cannoli Shells",          "pcs",   80,    25, 0.600, "Italian Cheese Imports",    "Baking"),
    ("Blueberries",             "g",   2000,   800, 0.025, "Fresh Farm Suppliers",      "Fruit"),
    ("Ice Cream (Vanilla)",     "ml",  6000,  2000, 0.010, "Dairy Direct Co.",          "Dairy"),
    ("Triple Sec (Liqueur)",    "ml",  3000,  1000, 0.030, "Wine & Spirits Co.",        "Beverage"),
    ("Lime Juice (Fresh)",      "ml",  4000,  1500, 0.008, "Fresh Farm Suppliers",      "Beverage"),

    # ── Oils & Spices (bulk) ──
    ("Vegetable Oil",           "ml", 15000,  5000, 0.003, "Global Spices Inc.",        "Oil"),
    ("Salt",                    "g",  10000,  3000, 0.001, "Global Spices Inc.",        "Spice"),
    ("Black Pepper",            "g",   2000,   600, 0.015, "Global Spices Inc.",        "Spice"),
    ("Cumin",                   "g",   1000,   400, 0.020, "Global Spices Inc.",        "Spice"),
    ("Truffle Oil",             "ml",   500,   200, 0.150, "Mediterranean Imports Co.", "Oil"),
    ("Panko Breadcrumbs",       "g",   3000,  1000, 0.006, "Japanese Food Imports",     "Grain"),
    ("Ramen Broth (Pork)",      "ml",  8000,  3000, 0.008, "Japanese Food Imports",     "Sauce"),
    ("Black Beans (Cooked)",    "g",   5000,  2000, 0.004, "Mexican Food Supply",       "Vegetable"),
    ("Cold Pressed Green Juice","pcs",   48,    16, 2.500, "Fresh Farm Suppliers",      "Beverage"),
    ("Fruit Smoothie Mix",      "g",   3000,  1200, 0.015, "Fresh Farm Suppliers",      "Beverage"),
]

# ─── RECIPES ────────────────────────────────────────────────────────────────────
# { "Menu Item Name": [ ("Ingredient Name", qty_per_serving), ... ] }
RECIPES = {
    # ══════════ STEAKHOUSE ══════════
    "14oz Ribeye": [
        ("Beef Ribeye (Raw)", 400), ("Butter", 25), ("Garlic", 8),
        ("Salt", 5), ("Black Pepper", 3), ("Olive Oil (Extra Virgin)", 15),
    ],
    "8oz Filet Mignon": [
        ("Beef Filet Mignon (Raw)", 225), ("Butter", 30), ("Garlic", 8),
        ("Salt", 5), ("Black Pepper", 3), ("Olive Oil (Extra Virgin)", 15),
    ],
    "Jumbo Shrimp Cocktail": [
        ("Shrimp (Peeled)", 180), ("Cocktail Sauce", 60), ("Lemons", 1),
    ],
    "Oysters on the Half Shell (6pc)": [
        ("Fresh Oysters", 6), ("Lemons", 1), ("Cocktail Sauce", 30),
    ],
    "Herb-Crusted Rack of Lamb": [
        ("Lamb Rack (Raw)", 350), ("Fresh Basil", 10), ("Garlic", 10),
        ("Panko Breadcrumbs", 30), ("Olive Oil (Extra Virgin)", 20),
        ("Salt", 5), ("Black Pepper", 3),
    ],
    "Grilled Atlantic Salmon": [
        ("Salmon Fillet", 200), ("Olive Oil (Extra Virgin)", 15),
        ("Lemons", 1), ("Salt", 4), ("Black Pepper", 2), ("Asparagus", 100),
    ],
    "Creamed Spinach": [
        ("Fresh Spinach", 200), ("Heavy Cream", 80), ("Butter", 20),
        ("Garlic", 8), ("Parmesan Cheese", 20), ("Salt", 3),
    ],
    "Garlic Mashed Potatoes": [
        ("Potatoes", 250), ("Butter", 35), ("Heavy Cream", 50),
        ("Garlic", 12), ("Salt", 4),
    ],
    "Grilled Asparagus": [
        ("Asparagus", 180), ("Olive Oil (Extra Virgin)", 15),
        ("Salt", 3), ("Black Pepper", 2), ("Lemons", 0.5),
    ],
    "Truffle Mac & Cheese": [
        ("Pasta (Dry)", 120), ("Cheddar Cheese", 80), ("Heavy Cream", 100),
        ("Truffle Oil", 8), ("Butter", 20), ("Parmesan Cheese", 15),
    ],
    "Old Fashioned Cocktail": [
        ("Bourbon Whiskey", 60), ("Granulated Sugar", 5), ("Oranges", 0.25),
    ],
    "Premium Cabernet Sauvignon (Glass)": [
        ("Cabernet Sauvignon (Btl)", 180),
    ],
    "Red Wine (Cabernet)": [
        ("Cabernet Sauvignon (Btl)", 180),
    ],
    "Side Salad with Vinaigrette": [
        ("Lettuce (Mixed Greens)", 80), ("Tomatoes", 40), ("Onions", 20),
        ("Vinaigrette Dressing", 30),
    ],

    # ══════════ AMERICAN ══════════
    "Classic Cheeseburger": [
        ("Ground Beef", 150), ("Burger Buns", 1), ("Cheddar Cheese", 40),
        ("Lettuce (Mixed Greens)", 30), ("Tomatoes", 40), ("Onions", 25),
        ("Mayonnaise", 15),
    ],
    "Bacon Double Burger": [
        ("Ground Beef", 300), ("Burger Buns", 1), ("Cheddar Cheese", 60),
        ("Bacon", 50), ("Lettuce (Mixed Greens)", 30), ("Tomatoes", 40),
        ("Onions", 25), ("Mayonnaise", 15),
    ],
    "Spicy BBQ Bacon Burger": [
        ("Ground Beef", 200), ("Burger Buns", 1), ("Cheddar Cheese", 40),
        ("Bacon", 40), ("BBQ Sauce", 30), ("Jalapeño Peppers", 15),
        ("Lettuce (Mixed Greens)", 25), ("Onions", 20),
    ],
    "Crispy Chicken Sandwich": [
        ("Chicken Breast", 180), ("Burger Buns", 1), ("All-Purpose Flour", 40),
        ("Lettuce (Mixed Greens)", 30), ("Mayonnaise", 20), ("Vegetable Oil", 200),
    ],
    "Philly Cheesesteak": [
        ("Beef Ribeye (Raw)", 200), ("Bread Slices", 2), ("Mozzarella Cheese", 60),
        ("Bell Peppers", 50), ("Onions", 50), ("Olive Oil (Extra Virgin)", 15),
    ],
    "Hot Dog with Mustard": [
        ("Hot Dog Sausage", 1), ("Hot Dog Buns", 1), ("Yellow Mustard", 20),
        ("Onions", 15),
    ],
    "Chicken Tenders (4pc)": [
        ("Chicken Breast", 200), ("All-Purpose Flour", 50), ("Eggs", 1),
        ("Panko Breadcrumbs", 60), ("Vegetable Oil", 250), ("Salt", 3),
    ],
    "Buffalo Wings (10pc)": [
        ("Chicken Wings", 450), ("BBQ Sauce", 60), ("Butter", 25),
        ("Vegetable Oil", 300), ("Salt", 4),
    ],
    "French Fries": [
        ("Potatoes", 250), ("Vegetable Oil", 300), ("Salt", 5),
    ],
    "Sweet Potato Fries": [
        ("Sweet Potatoes", 250), ("Vegetable Oil", 300), ("Salt", 5),
    ],
    "Onion Rings": [
        ("Onions", 200), ("All-Purpose Flour", 60), ("Eggs", 1),
        ("Vegetable Oil", 300), ("Salt", 3),
    ],
    "Mac & Cheese": [
        ("Pasta (Dry)", 120), ("Cheddar Cheese", 80), ("Whole Milk", 100),
        ("Butter", 20), ("All-Purpose Flour", 15),
    ],
    "Vanilla Milkshake": [
        ("Ice Cream (Vanilla)", 200), ("Whole Milk", 150),
        ("Vanilla Extract", 5), ("Whipped Cream", 30),
    ],
    "Coca-Cola": [("Coca-Cola (Cans)", 1)],
    "Diet Coke": [("Diet Coke (Cans)", 1)],
    "Sprite": [("Sprite (Cans)", 1)],
    "Dr Pepper": [("Dr Pepper (Cans)", 1)],
    "Iced Tea": [
        ("Black Tea Leaves", 5), ("Granulated Sugar", 20), ("Lemons", 0.5),
    ],

    # ══════════ ITALIAN ══════════
    "Margherita Pizza": [
        ("Pizza Dough", 250), ("Tomato Sauce", 80), ("Mozzarella Cheese", 150),
        ("Fresh Basil", 5), ("Olive Oil (Extra Virgin)", 10),
    ],
    "Pepperoni Pizza": [
        ("Pizza Dough", 250), ("Tomato Sauce", 80), ("Mozzarella Cheese", 130),
        ("Pepperoni", 60),
    ],
    "Prosciutto & Arugula Pizza": [
        ("Pizza Dough", 250), ("Tomato Sauce", 60), ("Mozzarella Cheese", 120),
        ("Prosciutto", 50), ("Arugula", 30), ("Parmesan Cheese", 15),
    ],
    "Truffle Mushroom Pizza": [
        ("Pizza Dough", 250), ("Mozzarella Cheese", 130), ("Mushrooms", 100),
        ("Truffle Oil", 10), ("Garlic", 8), ("Olive Oil (Extra Virgin)", 10),
    ],
    "Spaghetti Carbonara": [
        ("Pasta (Dry)", 140), ("Bacon", 60), ("Parmesan Cheese", 40),
        ("Eggs", 2), ("Black Pepper", 3), ("Olive Oil (Extra Virgin)", 10),
    ],
    "Fettuccine Alfredo": [
        ("Pasta (Dry)", 140), ("Alfredo Sauce", 120), ("Parmesan Cheese", 30),
        ("Butter", 20), ("Garlic", 8),
    ],
    "Beef Lasagna": [
        ("Pasta (Dry)", 120), ("Ground Beef", 150), ("Tomato Sauce", 100),
        ("Mozzarella Cheese", 80), ("Ricotta Cheese", 60), ("Parmesan Cheese", 20),
        ("Onions", 30), ("Garlic", 8),
    ],
    "Lobster Ravioli": [
        ("Pasta (Dry)", 140), ("Lobster Meat", 100), ("Ricotta Cheese", 40),
        ("Heavy Cream", 80), ("Butter", 20), ("Garlic", 8),
        ("Parmesan Cheese", 15),
    ],
    "Potato Gnocchi with Pesto": [
        ("Gnocchi (Fresh)", 250), ("Basil Pesto", 50), ("Parmesan Cheese", 20),
        ("Olive Oil (Extra Virgin)", 10),
    ],
    "Meatball Calzone": [
        ("Pizza Dough", 280), ("Ground Beef", 150), ("Mozzarella Cheese", 100),
        ("Tomato Sauce", 60), ("Parmesan Cheese", 15), ("Eggs", 1),
        ("Onions", 25), ("Garlic", 8),
    ],
    "Bruschetta": [
        ("Bread Slices", 3), ("Tomatoes", 120), ("Fresh Basil", 8),
        ("Garlic", 6), ("Olive Oil (Extra Virgin)", 15),
    ],
    "Fried Calamari": [
        ("Calamari (Rings)", 200), ("All-Purpose Flour", 50),
        ("Vegetable Oil", 300), ("Lemons", 1), ("Salt", 3),
    ],
    "Caprese Salad": [
        ("Mozzarella Cheese", 120), ("Tomatoes", 150), ("Fresh Basil", 10),
        ("Olive Oil (Extra Virgin)", 20), ("Salt", 2),
    ],
    "Garlic Bread": [
        ("Bread Slices", 3), ("Butter", 30), ("Garlic", 10),
        ("Parmesan Cheese", 10),
    ],
    "Tiramisu": [
        ("Mascarpone", 100), ("Ladyfinger Biscuits", 6), ("Coffee Beans (Arabica)", 10),
        ("Eggs", 2), ("Granulated Sugar", 30), ("Cocoa Powder", 10),
    ],
    "Cannoli": [
        ("Cannoli Shells", 2), ("Ricotta Cheese", 100), ("Powdered Sugar", 20),
        ("Dark Chocolate", 15), ("Vanilla Extract", 3),
    ],
    "Lemon Gelato": [
        ("Gelato Base Mix", 150), ("Lemons", 2), ("Granulated Sugar", 30),
    ],
    "Crème Brûlée": [
        ("Heavy Cream", 150), ("Eggs", 3), ("Granulated Sugar", 40),
        ("Vanilla Extract", 5),
    ],
    "New York Cheesecake": [
        ("Cream Cheese", 150), ("Eggs", 2), ("Granulated Sugar", 40),
        ("Heavy Cream", 50), ("Vanilla Extract", 5), ("Butter", 20),
    ],
    "Peroni Beer": [("Peroni Beer (Bottles)", 1)],
    "Red Wine (Chianti)": [("Chianti (Bottle)", 180)],
    "White Wine (Pinot Grigio)": [("Pinot Grigio (Bottle)", 180)],
    "Prosecco": [("Prosecco (Bottle)", 150)],
    "Chardonnay (Glass)": [("Chardonnay (Bottle)", 180)],

    # ══════════ MEXICAN ══════════
    "Beef Tacos (3pc)": [
        ("Ground Beef", 180), ("Flour Tortillas", 3), ("Cheddar Cheese", 40),
        ("Lettuce (Mixed Greens)", 30), ("Tomatoes", 40), ("Salsa (House-Made)", 40),
        ("Onions", 20),
    ],
    "Chicken Burrito": [
        ("Chicken Breast", 180), ("Flour Tortillas", 1), ("White Rice", 100),
        ("Black Beans (Cooked)", 80), ("Cheddar Cheese", 50),
        ("Salsa (House-Made)", 40), ("Lettuce (Mixed Greens)", 25),
    ],
    "Chicken Enchiladas": [
        ("Chicken Breast", 160), ("Flour Tortillas", 3), ("Enchilada Sauce", 100),
        ("Cheddar Cheese", 60), ("Onions", 30), ("Garlic", 6),
    ],
    "Steak Fajitas": [
        ("Beef Ribeye (Raw)", 200), ("Bell Peppers", 100), ("Onions", 80),
        ("Flour Tortillas", 3), ("Olive Oil (Extra Virgin)", 15),
        ("Cheddar Cheese", 40), ("Salsa (House-Made)", 40),
    ],
    "Cheese Quesadilla": [
        ("Flour Tortillas", 2), ("Cheddar Cheese", 80), ("Mozzarella Cheese", 40),
        ("Bell Peppers", 30), ("Onions", 20),
    ],
    "Pork Carnitas Bowl": [
        ("Pork Shoulder", 200), ("White Rice", 150), ("Black Beans (Cooked)", 80),
        ("Salsa (House-Made)", 40), ("Onions", 20), ("Lettuce (Mixed Greens)", 25),
    ],
    "Loaded Nachos": [
        ("Tortilla Chips", 180), ("Cheddar Cheese", 80), ("Ground Beef", 100),
        ("Jalapeño Peppers", 20), ("Salsa (House-Made)", 50),
        ("Guacamole (House-Made)", 40),
    ],
    "Guacamole": [
        ("Avocado", 2), ("Tomatoes", 40), ("Onions", 20),
        ("Jalapeño Peppers", 10), ("Lemons", 0.5), ("Salt", 3),
    ],
    "Queso Dip": [
        ("Queso Cheese Sauce", 120), ("Jalapeño Peppers", 15),
        ("Tortilla Chips", 60),
    ],
    "Spicy Salsa": [
        ("Tomatoes", 150), ("Jalapeño Peppers", 30), ("Onions", 30),
        ("Garlic", 5), ("Salt", 3),
    ],
    "Rice & Beans": [
        ("White Rice", 150), ("Black Beans (Cooked)", 120),
        ("Onions", 20), ("Garlic", 5), ("Cumin", 3),
    ],
    "Churros with Chocolate": [
        ("All-Purpose Flour", 100), ("Eggs", 2), ("Granulated Sugar", 30),
        ("Butter", 20), ("Vegetable Oil", 200), ("Dark Chocolate", 50),
    ],
    "Caramel Flan": [
        ("Eggs", 3), ("Whole Milk", 200), ("Granulated Sugar", 60),
        ("Vanilla Extract", 5), ("Caramel Sauce", 30),
    ],
    "Tortilla Chips": [
        ("Tortilla Chips", 200), ("Salt", 3),
    ],
    "Classic Margarita": [
        ("Tequila (Blanco)", 60), ("Triple Sec (Liqueur)", 30),
        ("Lime Juice (Fresh)", 30), ("Salt", 2),
    ],
    "Spicy Jalapeno Margarita": [
        ("Tequila (Blanco)", 60), ("Triple Sec (Liqueur)", 30),
        ("Lime Juice (Fresh)", 30), ("Jalapeño Peppers", 10), ("Salt", 2),
    ],
    "Horchata": [
        ("Horchata Mix", 40), ("Whole Milk", 200), ("Granulated Sugar", 15),
    ],
    "Corona Extra": [("Corona Extra (Bottles)", 1)],
    "Modelo Especial": [("Modelo Especial (Btl)", 1)],
    "Mexican Coke (Glass Bottle)": [("Coca-Cola (Cans)", 1)],

    # ══════════ JAPANESE ══════════
    "California Roll": [
        ("Sushi Rice", 180), ("Nori Seaweed Sheets", 2), ("Shrimp (Peeled)", 60),
        ("Avocado", 0.5), ("Sesame Oil", 5), ("Soy Sauce", 15),
    ],
    "Spicy Tuna Roll": [
        ("Sushi Rice", 180), ("Nori Seaweed Sheets", 2),
        ("Sashimi-Grade Tuna", 100), ("Mayonnaise", 15), ("Sesame Oil", 5),
        ("Soy Sauce", 15),
    ],
    "Dragon Roll": [
        ("Sushi Rice", 200), ("Nori Seaweed Sheets", 2), ("Shrimp (Peeled)", 80),
        ("Avocado", 1), ("Sesame Oil", 5), ("Soy Sauce", 15),
    ],
    "Salmon Nigiri (2pc)": [
        ("Sushi Rice", 80), ("Salmon Fillet", 60), ("Soy Sauce", 10),
    ],
    "Tuna Sashimi (5pc)": [
        ("Sashimi-Grade Tuna", 125), ("Soy Sauce", 15), ("Garlic", 3),
    ],
    "Chicken Teriyaki Bento": [
        ("Chicken Breast", 200), ("White Rice", 180), ("Teriyaki Sauce", 50),
        ("Edamame (Shelled)", 50), ("Sesame Oil", 8),
    ],
    "Pork Ramen": [
        ("Ground Pork", 100), ("Udon Noodles", 200), ("Ramen Broth (Pork)", 400),
        ("Eggs", 1), ("Nori Seaweed Sheets", 1), ("Garlic", 6),
        ("Soy Sauce", 15), ("Sesame Oil", 5),
    ],
    "Vegetable Udon": [
        ("Udon Noodles", 250), ("Mushrooms", 60), ("Bell Peppers", 50),
        ("Fresh Spinach", 40), ("Soy Sauce", 20), ("Sesame Oil", 8),
        ("Garlic", 5),
    ],
    "Pork Gyoza (6pc)": [
        ("Ground Pork", 90), ("All-Purpose Flour", 50), ("Garlic", 5),
        ("Soy Sauce", 10), ("Sesame Oil", 5), ("Onions", 15),
        ("Vegetable Oil", 30),
    ],
    "Miso Soup": [
        ("Miso Paste", 30), ("Firm Tofu", 50), ("Nori Seaweed Sheets", 0.5),
        ("Garlic", 3), ("Green Tea Leaves", 2),
    ],
    "Edamame": [
        ("Edamame (Shelled)", 180), ("Salt", 4), ("Sesame Oil", 5),
    ],
    "Seaweed Salad": [
        ("Nori Seaweed Sheets", 3), ("Sesame Oil", 10), ("Soy Sauce", 10),
        ("Garlic", 3), ("Granulated Sugar", 5),
    ],
    "Green Tea Mochi Ice Cream": [
        ("Mochi Dough (Premade)", 80), ("Matcha Powder", 5),
        ("Ice Cream (Vanilla)", 80), ("Granulated Sugar", 10),
    ],
    "Hot Sake (Small)": [("Sake", 180)],
    "Sapporo Draft": [("Sapporo Draft (Cans)", 1)],
    "Green Tea": [("Green Tea Leaves", 5)],

    # ══════════ CAFE ══════════
    "Espresso": [("Coffee Beans (Arabica)", 18)],
    "Cappuccino": [("Coffee Beans (Arabica)", 18), ("Whole Milk", 180)],
    "Iced Latte": [("Coffee Beans (Arabica)", 18), ("Whole Milk", 200)],
    "Caramel Macchiato": [
        ("Coffee Beans (Arabica)", 18), ("Whole Milk", 200),
        ("Caramel Sauce", 20), ("Vanilla Extract", 3),
    ],
    "Cold Brew Coffee": [("Coffee Beans (Arabica)", 25)],
    "Matcha Green Tea Latte": [
        ("Matcha Powder", 5), ("Whole Milk", 240), ("Granulated Sugar", 10),
    ],
    "Black Tea": [("Black Tea Leaves", 5), ("Granulated Sugar", 10)],
    "Butter Croissant": [("Croissant Dough", 100), ("Butter", 30)],
    "Almond Croissant": [
        ("Croissant Dough", 100), ("Butter", 25), ("All-Purpose Flour", 20),
        ("Granulated Sugar", 15),
    ],
    "Blueberry Muffin": [
        ("All-Purpose Flour", 80), ("Blueberries", 40), ("Eggs", 1),
        ("Butter", 30), ("Granulated Sugar", 35), ("Whole Milk", 50),
    ],
    "Chocolate Chip Cookie": [
        ("All-Purpose Flour", 50), ("Butter", 30), ("Dark Chocolate", 25),
        ("Eggs", 0.5), ("Granulated Sugar", 30), ("Vanilla Extract", 3),
    ],
    "Chocolate Brownie": [
        ("Dark Chocolate", 60), ("Butter", 50), ("Eggs", 2),
        ("All-Purpose Flour", 40), ("Granulated Sugar", 50), ("Cocoa Powder", 15),
    ],
    "Breakfast Sandwich (Egg & Cheese)": [
        ("Eggs", 2), ("Cheddar Cheese", 40), ("Bread Slices", 2),
        ("Butter", 10),
    ],
    "Everything Bagel with Cream Cheese": [
        ("Bagels", 1), ("Cream Cheese", 50),
    ],
    "Avocado Toast": [
        ("Bread Slices", 2), ("Avocado", 1), ("Lemons", 0.25),
        ("Salt", 2), ("Black Pepper", 1), ("Olive Oil (Extra Virgin)", 10),
    ],
    "Oatmeal with Berries": [
        ("Oats", 80), ("Whole Milk", 150), ("Mixed Berries", 50),
        ("Granulated Sugar", 10),
    ],
    "Apple Pie": [
        ("Apples", 2), ("All-Purpose Flour", 100), ("Butter", 50),
        ("Granulated Sugar", 40), ("Vanilla Extract", 3),
    ],
    "Orange Juice": [("Oranges", 3)],
    "Fruit Smoothie": [
        ("Fruit Smoothie Mix", 60), ("Bananas", 1), ("Mixed Berries", 60),
        ("Whole Milk", 150),
    ],
    "Coconut Water": [("Coconut Water", 1)],
    "Kombucha (Ginger)": [("Kombucha (Ginger)", 1)],
    "Cold Pressed Green Juice": [("Cold Pressed Green Juice", 1)],

    # ══════════ HEALTHY / VEGAN ══════════
    "Acai Berry Bowl": [
        ("Acai Puree (Frozen)", 100), ("Bananas", 1), ("Mixed Berries", 40),
        ("Oats", 20), ("Granulated Sugar", 5),
    ],
    "Quinoa Power Bowl": [
        ("Quinoa", 120), ("Avocado", 0.5), ("Tomatoes", 60),
        ("Fresh Spinach", 40), ("Chickpeas (Cooked)", 60),
        ("Olive Oil (Extra Virgin)", 15), ("Lemons", 0.5),
    ],
    "Vegan Buddha Bowl": [
        ("Quinoa", 100), ("Sweet Potatoes", 100), ("Kale", 50),
        ("Chickpeas (Cooked)", 80), ("Avocado", 0.5),
        ("Olive Oil (Extra Virgin)", 15), ("Lemons", 0.5),
    ],
    "Kale & Sweet Potato Salad": [
        ("Kale", 100), ("Sweet Potatoes", 120), ("Chickpeas (Cooked)", 50),
        ("Vinaigrette Dressing", 30), ("Lemons", 0.5),
    ],
    "Grilled Tofu Wrap": [
        ("Firm Tofu", 180), ("Flour Tortillas", 1), ("Lettuce (Mixed Greens)", 40),
        ("Tomatoes", 40), ("Avocado", 0.5), ("Olive Oil (Extra Virgin)", 10),
    ],
    "Hummus & Pita": [
        ("Hummus", 120), ("Pita Bread", 2), ("Olive Oil (Extra Virgin)", 10),
    ],
    "Roasted Chickpeas": [
        ("Chickpeas (Cooked)", 200), ("Olive Oil (Extra Virgin)", 15),
        ("Cumin", 3), ("Salt", 3),
    ],
    "Vegan Peanut Butter Protein Ball": [
        ("Peanut Butter", 40), ("Oats", 30), ("Dark Chocolate", 15),
        ("Granulated Sugar", 10),
    ],
}


def seed_ingredients(db):
    """Create all ingredients and recipe mappings."""
    from app.products.models import Ingredient, ProductIngredient, Product

    if db.query(Ingredient).count() > 0:
        print("  [SEED] Ingredients already populated, skipping.")
        return

    # 1. Create ingredients
    ingredient_map = {}  # name -> Ingredient object
    for name, unit, stock, threshold, cost, supplier, cat in INGREDIENTS:
        ing = Ingredient(
            name=name,
            unit=unit,
            current_stock=stock,
            low_stock_threshold=threshold,
            cost_per_unit=cost,
            supplier=supplier,
            category=cat,
        )
        db.add(ing)
        db.flush()
        ingredient_map[name] = ing

    # 2. Create recipe mappings
    products = db.query(Product).all()
    product_map = {p.name: p for p in products}

    recipe_count = 0
    missing_items = []
    for item_name, recipe in RECIPES.items():
        product = product_map.get(item_name)
        if not product:
            missing_items.append(item_name)
            continue

        for ing_name, qty in recipe:
            ingredient = ingredient_map.get(ing_name)
            if not ingredient:
                print(f"  [WARN] Ingredient '{ing_name}' not found for '{item_name}'")
                continue

            pi = ProductIngredient(
                product_id=product.id,
                ingredient_id=ingredient.id,
                quantity_needed=qty,
            )
            db.add(pi)
            recipe_count += 1

    db.commit()
    print(f"  [SEED] Created {len(ingredient_map)} ingredients, {recipe_count} recipe mappings")
    if missing_items:
        print(f"  [SEED] Menu items not found in DB (skipped): {missing_items[:5]}...")
