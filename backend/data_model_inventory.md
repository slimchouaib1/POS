# POS Backend Data Model Inventory

### **StockMovement** (`stock_movements`)
* **Columns:**
  * `id`: Integer, primary_key, index
  * `product_id`: Integer, foreign_key(`products.id`), nullable=False
  * `quantity_change`: Integer, nullable=False (Note: positive=in, negative=out)
  * `reason`: String(100), default="", nullable=True
  * `details`: Text, default="", nullable=True
  * `triggered_by`: Integer, foreign_key(`users.id`), nullable=True
  * `created_at`: DateTime, server_default=func.now()
* **Methods:** None
* **Relationships:** None explicitly defined with `relationship()`.

### **Category** (`categories`)
* **Columns:**
  * `id`: Integer, primary_key, index
  * `name`: String(100), unique=True, nullable=False
  * `description`: Text, default="", nullable=True
  * `icon`: String(50), default="📦", nullable=True
  * `display_order`: Integer, default=0, nullable=True
  * `created_at`: DateTime, server_default=func.now()
* **Methods:** None
* **Relationships:**
  * `products`: Category (one) to Product (many), back_populates="category"

### **Product** (`products`)
* **Columns:**
  * `id`: Integer, primary_key, index
  * `name`: String(200), nullable=False, index
  * `category_id`: Integer, foreign_key(`categories.id`), nullable=False
  * `section`: String(50), default="", nullable=True (Note: restaurant_type)
  * `price`: Float, nullable=False
  * `description`: Text, default="", nullable=True
  * `image_url`: String(500), default="", nullable=True
  * `is_available`: Boolean, default=True, nullable=True
  * `stock_quantity`: Integer, default=100, nullable=True
  * `low_stock_threshold`: Integer, default=10, nullable=True
  * `created_at`: DateTime, server_default=func.now()
  * `updated_at`: DateTime, server_default=func.now(), onupdate=func.now()
* **Methods:** None
* **Relationships:**
  * `category`: Product (many) to Category (one), back_populates="products"
  * `recipe`: Product (one) to ProductIngredient (many), back_populates="product"

### **Ingredient** (`ingredients`)
* **Columns:**
  * `id`: Integer, primary_key, index
  * `name`: String(200), nullable=False, unique=True, index
  * `unit`: String(50), nullable=False (Note: g, ml, pcs, leaves, etc.)
  * `current_stock`: Float, default=0, nullable=True
  * `low_stock_threshold`: Float, default=500, nullable=True
  * `cost_per_unit`: Float, default=0.01, nullable=True
  * `supplier`: String(200), default="", nullable=True
  * `category`: String(100), default="", nullable=True
  * `created_at`: DateTime, server_default=func.now()
* **Methods:** None
* **Relationships:**
  * `recipe_usages`: Ingredient (one) to ProductIngredient (many), back_populates="ingredient"

### **ProductIngredient** (`product_ingredients`) - *Association Table*
* **Columns:**
  * `id`: Integer, primary_key, index
  * `product_id`: Integer, foreign_key(`products.id`), nullable=False
  * `ingredient_id`: Integer, foreign_key(`ingredients.id`), nullable=False
  * `quantity_needed`: Float, nullable=False
* **Methods:** None
* **Relationships:**
  * `product`: ProductIngredient (many) to Product (one), back_populates="recipe"
  * `ingredient`: ProductIngredient (many) to Ingredient (one), back_populates="recipe_usages"

### **Payment** (`payments`)
* **Columns:**
  * `id`: Integer, primary_key, index
  * `order_id`: Integer, foreign_key(`orders.id`), nullable=False
  * `amount`: Float, nullable=False
  * `method`: String(20), default="cash", nullable=True
  * `status`: String(20), default="completed", nullable=True
  * `reference`: String(100), default="", nullable=True
  * `created_at`: DateTime, server_default=func.now()
* **Methods:** None
* **Relationships:** None explicitly defined with `relationship()`.

### **Table** (`tables`)
* **Columns:**
  * `id`: Integer, primary_key, index
  * `number`: Integer, unique=True, nullable=False
  * `section`: String(50), default="Main", nullable=True
  * `capacity`: Integer, default=4, nullable=True
  * `status`: String(20), default="available", nullable=True
* **Methods:** None
* **Relationships:**
  * `orders`: Table (one) to Order (many), back_populates="table"

### **Order** (`orders`)
* **Columns:**
  * `id`: Integer, primary_key, index
  * `table_id`: Integer, foreign_key(`tables.id`), nullable=True
  * `customer_id`: Integer, foreign_key(`customers.id`), nullable=True
  * `cashier_id`: Integer, foreign_key(`users.id`), nullable=False
  * `status`: String(20), default="draft", nullable=True
  * `total_amount`: Float, default=0.0, nullable=True
  * `discount_pct`: Float, default=0.0, nullable=True
  * `discount_amount`: Float, default=0.0, nullable=True
  * `notes`: Text, default="", nullable=True
  * `cancel_reason`: Text, default="", nullable=True
  * `created_at`: DateTime, server_default=func.now()
  * `updated_at`: DateTime, server_default=func.now(), onupdate=func.now()
* **Methods:** None
* **Relationships:**
  * `table`: Order (many) to Table (one), back_populates="orders"
  * `items`: Order (one) to OrderItem (many), back_populates="order", cascade="all, delete-orphan"

### **OrderItem** (`order_items`)
* **Columns:**
  * `id`: Integer, primary_key, index
  * `order_id`: Integer, foreign_key(`orders.id`, ondelete="CASCADE"), nullable=False
  * `product_id`: Integer, foreign_key(`products.id`), nullable=False
  * `product_name`: String(200), default="", nullable=True
  * `quantity`: Integer, default=1, nullable=True
  * `unit_price`: Float, nullable=False
  * `discount_pct`: Float, default=0.0, nullable=True
  * `subtotal`: Float, nullable=False
  * `notes`: Text, default="", nullable=True
* **Methods:** None
* **Relationships:**
  * `order`: OrderItem (many) to Order (one), back_populates="items"

### **Customer** (`customers`)
* **Columns:**
  * `id`: Integer, primary_key, index
  * `name`: String(100), nullable=False
  * `email`: String(100), default="", nullable=True
  * `phone`: String(20), default="", nullable=True
  * `archetype`: String(50), default="", nullable=True
  * `price_tier`: String(20), default="", nullable=True
  * `time_preference`: String(20), default="", nullable=True
  * `day_preference`: String(20), default="", nullable=True
  * `visit_count`: Integer, default=0, nullable=True
  * `total_spent`: Float, default=0.0, nullable=True
  * `last_visit`: DateTime, nullable=True
  * `created_at`: DateTime, server_default=func.now()
* **Methods:** None
* **Relationships:** None explicitly defined with `relationship()`.

### **User** (`users`)
* **Columns:**
  * `id`: Integer, primary_key, index
  * `username`: String(50), unique=True, index, nullable=False
  * `full_name`: String(100), nullable=False
  * `email`: String(100), unique=True, index, nullable=False
  * `hashed_password`: String(255), nullable=False
  * `role`: String(20), default="cashier", nullable=False
  * `is_active`: Boolean, default=True, nullable=True
  * `created_at`: DateTime, server_default=func.now()
  * `updated_at`: DateTime, server_default=func.now(), onupdate=func.now()
* **Methods:** None
* **Relationships:** None explicitly defined with `relationship()`.

### **AuditLog** (`audit_logs`)
* **Columns:**
  * `id`: Integer, primary_key, index
  * `user_id`: Integer, foreign_key(`users.id`), nullable=True
  * `action`: String(50), nullable=False
  * `entity_type`: String(50), default="", nullable=True
  * `entity_id`: Integer, nullable=True
  * `details`: Text, default="", nullable=True
  * `ip_address`: String(50), default="", nullable=True
  * `created_at`: DateTime, server_default=func.now()
* **Methods:** None
* **Relationships:** None explicitly defined with `relationship()`.

### **AnomalyAlert** (`anomaly_alerts`)
* **Columns:**
  * `id`: Integer, primary_key, index
  * `order_id`: String(50), default="", nullable=True
  * `risk_score`: Float, default=0.0, nullable=True
  * `risk_level`: String(20), default="NORMAL", nullable=True
  * `predicted_label`: Integer, default=0, nullable=True
  * `anomaly_type`: String(100), default="", nullable=True
  * `reason_codes`: Text, default="", nullable=True
  * `alert_explanation`: Text, default="", nullable=True
  * `model_name`: String(50), default="Random Forest", nullable=True
  * `status`: String(30), default="new", nullable=True
  * `assigned_to`: Integer, foreign_key(`users.id`), nullable=True
  * `created_at`: DateTime, server_default=func.now()
  * `updated_at`: DateTime, server_default=func.now(), onupdate=func.now()
* **Methods:** None
* **Relationships:**
  * `comments`: AnomalyAlert (one) to AlertComment (many), back_populates="alert", cascade="all, delete-orphan"

### **AlertComment** (`alert_comments`)
* **Columns:**
  * `id`: Integer, primary_key, index
  * `alert_id`: Integer, foreign_key(`anomaly_alerts.id`, ondelete="CASCADE"), nullable=False
  * `user_id`: Integer, foreign_key(`users.id`), nullable=True
  * `comment`: Text, nullable=False
  * `action`: String(50), default="", nullable=True
  * `created_at`: DateTime, server_default=func.now()
* **Methods:** None
* **Relationships:**
  * `alert`: AlertComment (many) to AnomalyAlert (one), back_populates="comments"

---

### **ENUMS**
*Note: The project does not define explicit Python Enum classes or SQL ENUM types, but rather stores them as `String` columns with the accepted sets documented via comments:*
* **Table.status:** available, occupied, reserved
* **Order.status:** draft, in_progress, served, paid, cancelled
* **Payment.method:** cash, card, mobile
* **Payment.status:** completed, refunded
* **User.role:** admin, manager, cashier, stock_manager
* **AuditLog.action:** login, create_order, update_product, etc.
* **AuditLog.entity_type:** order, product, user, etc.
* **AnomalyAlert.risk_level:** NORMAL, ALERTE, CRITIQUE
* **AnomalyAlert.predicted_label (Integer):** 0=normal, 1=anomaly
* **AnomalyAlert.status:** new, assigned, under_review, confirmed_fraud, false_positive, escalated, closed
* **AlertComment.action:** status_change, comment, escalate

---

### **RELATIONSHIPS SUMMARY**
*Explicit Relationships (defined via `relationship()`):*
* Category [one] — [many] Product (via category_id)
* Product [many] — [many] Ingredient (via junction table ProductIngredient)
* Table [one] — [many] Order (via table_id)
* Order [one] — [many] OrderItem (via order_id)
* AnomalyAlert [one] — [many] AlertComment (via alert_id)

*Implicit Relationships (Foreign keys exist but no `relationship()` defined on classes):*
* User [one] — [many] Order (via cashier_id)
* Customer [one] — [many] Order (via customer_id)
* Order [one] — [many] Payment (via order_id)
* Product [one] — [many] OrderItem (via product_id)
* User [one] — [many] StockMovement (via triggered_by)
* Product [one] — [many] StockMovement (via product_id)
* User [one] — [many] AuditLog (via user_id)
* User [one] — [many] AnomalyAlert (via assigned_to)
* User [one] — [many] AlertComment (via user_id)

---

### **UNCERTAIN / AMBIGUOUS**
1. **AnomalyAlert to Order mapping problem:** `AnomalyAlert.order_id` is typed as a `String(50)` without any `ForeignKey` constraints. However, `Order.id` is strictly an `Integer`. There is no direct DB-level relationship or referential integrity connecting alerts to orders. 
2. **One-Way Relationships:** Most core entities (User, Product, Order, Customer, Payment) have foreign keys, but lack back-referencing `relationship()` bindings. (e.g., `OrderItem` has `product_id`, but `Product` does not have a `relationship("OrderItem")`). The UML generator should probably be instructed to display these as standard One-To-Many relationships based on the Foreign Keys.
3. **AuditLog polymorphic associations:** `AuditLog` uses `entity_type` (String) and `entity_id` (Integer) to reference various tables generically. This is effectively a soft/polymorphic relation without foreign keys and can't be represented securely as a standard one-to-many relationship in a standard strict ERD context.
