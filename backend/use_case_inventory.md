# POS Use Case Inventory

## 1. ACTORS / ROLES
The system defines three distinct user roles, verified via `require_role(...)` in the backend and frontend redirection (`RoleRedirect`).
- **manager** (Store management, reporting, catalogue, AI review)
- **cashier** (POS operations)
- **stock_manager** (Inventory and forecasting)

---

## 2 & 3. USE CASES BY PACKAGE

### Authentication & Access
* **Register user**: Create new users. (Roles: **manager**) -> `POST /api/auth/register`
* **List users**: View all users. (Roles: **manager**) -> `GET /api/users`, UI: `/users`
* **Get user details**: View a specific user. (Roles: **manager**) -> `GET /api/users/{user_id}`
* **Update user**: Edit user info. (Roles: **manager**) -> `PUT /api/users/{user_id}`
* **Deactivate user**: Soft delete a user. (Roles: **manager**) -> `DELETE /api/users/{user_id}`
* **View activity logs**: Review audit trails. (Roles: **manager**) -> `GET /api/audit/logs`, UI: `/activity-logs`

### POS Operations
*(Note: Most core operations are restricted to `get_current_user` in the backend, meaning any authenticated user can technically perform them, though the frontend directs Cashiers to these tools).*
* **Update table status**: Mark as occupied, available, reserved. (Roles: manager, cashier, stock_manager) -> `PUT /api/tables/{table_id}/status`
* **Create order**: Start a new draft order. (Roles: manager, cashier, stock_manager) -> `POST /api/orders`, UI: `/pos`
* **Update order**: Add/remove items or change discounts. (Roles: manager, cashier, stock_manager) -> `PUT /api/orders/{order_id}`
* **Update order status**: Move order through states (draft -> in_progress -> served -> paid/cancelled). (Roles: manager, cashier, stock_manager) -> `PATCH /api/orders/{order_id}/status`
* **Process payment**: Record a cash/card transaction. (Roles: manager, cashier, stock_manager) -> `POST /api/payments`, UI: `/pos/payment`
* **Refund payment**: Refund a completed payment. (Roles: manager, cashier, stock_manager) -> `POST /api/payments/{payment_id}/refund`

### Product & Catalogue
* **Create category**: (Roles: **manager**) -> `POST /api/categories`
* **Update category**: (Roles: **manager**) -> `PUT /api/categories/{cat_id}`
* **Create product**: (Roles: **manager**) -> `POST /api/products`, UI: `/products`
* **Update product**: (Roles: **manager**) -> `PUT /api/products/{product_id}`
* **Toggle product availability**: (Roles: **manager**) -> `PATCH /api/products/{product_id}/toggle`
* **Delete product**: (Roles: **manager**) -> `DELETE /api/products/{product_id}`

### Inventory / Stock
* **Adjust stock**: Manually increment/decrement stock. (Roles: **manager**, **stock_manager**) -> `POST /api/stock/adjust`, UI: `/stock/inventory`

### Reporting & Dashboards
* **View dashboard KPIs**: High-level store metrics. (Roles: **manager**) -> `GET /api/reports/dashboard`, UI: `/dashboard`
* **View sales report**: Revenue over time. (Roles: **manager**) -> `GET /api/reports/sales`, UI: `/sales-reports`
* **View product performance**: Best-selling items. (Roles: **manager**) -> `GET /api/reports/products`

### AI Modules
**Segmentation:**
* **View segmentation overview**: Review customer segments. (Roles: **manager**) -> `GET /api/ai/segmentation/overview`, UI: `/ai/segments`

**Anomalies:**
* **List alerts**: View suspected fraud orders. (Roles: **manager**) -> `GET /api/ai/anomaly/alerts`, UI: `/ai/anomalies`
* **Get alert details**: Review anomaly context. (Roles: **manager**) -> `GET /api/ai/anomaly/alerts/{alert_id}`
* **Update alert status**: E.g., confirm fraud, dismiss. (Roles: **manager**) -> `PATCH /api/ai/anomaly/alerts/{alert_id}/status`
* **Add comment to alert**: Leave notes. (Roles: **manager**) -> `POST /api/ai/anomaly/alerts/{alert_id}/comment`
* **View anomaly order details**: View the transaction log. (Roles: **manager**) -> `GET /api/ai/anomaly/order-details/{order_id}`

**Forecasting:**
* **Get next week forecast**: Predicted sales. (Roles: **manager**, **stock_manager**) -> `GET /api/ai/forecasting/next-week`, UI: `/ai/forecasting`
* **Predict item sales**: Specific item prediction. (Roles: **manager**, **stock_manager**) -> `POST /api/ai/forecasting/predict`
* **Get ingredient forecast**: Predicted raw material usage. (Roles: **manager**, **stock_manager**) -> `GET /api/ai/forecasting/ingredient-forecast`

---

## 4. SHARED USE CASES
*These are endpoints and actions protected only by `get_current_user`, meaning ALL authenticated roles (manager, cashier, stock_manager) have access to them:*
* **Log in**: `POST /api/auth/login`, UI: `/login`
* **Log out**: Handled in frontend
* **View own profile**: `GET /api/auth/me`
* **List tables**: `GET /api/tables`
* **List orders / View order details**: `GET /api/orders`, `GET /api/orders/{order_id}`
* **View payments for order**: `GET /api/payments/{order_id}`
* **List categories**: `GET /api/categories`
* **List products**: `GET /api/products`
* **List customers / View customer details**: `GET /api/customers`, `GET /api/customers/{customer_id}`
* **View stock overview / alerts / movements**: `GET /api/stock`, `GET /api/stock/alerts`, `GET /api/stock/movements`, UI: `/stock/dashboard`, `/stock/movements`
* **Get customer AI segment**: `GET /api/ai/segmentation/customer/{customer_id}`
* **Get AI recommendations**: `POST /api/ai/recommendations`
* **View AI recommendations summary**: `GET /api/ai/recommendations/summary`
* **View anomaly metadata**: `GET /api/ai/anomaly/metadata`

---

## 5. INCLUDE / EXTEND RELATIONSHIPS
*These define system behaviors where one action triggers another:*
* **Create order** `<<include>>` **Mark table as occupied** (Table status changed on creation)
* **Update order status (to cancelled)** `<<include>>` **Free table** (Table status freed)
* **Update order status (to paid)** `<<include>>` **Free table** AND `<<include>>` **Deduct stock** (Product quantity reduced)
* **Process payment** `<<include>>` **Update order status (to paid)** AND `<<include>>` **Free table** (Payment endpoint triggers order completion)
* **Update alert status** `<<include>>` **Add system comment** (Automatically logs a comment about the transition)

---

## 6. UNCERTAIN / AMBIGUOUS
* **Frontend vs Backend Restrictions**: In the backend, routes like `/api/orders` (Create/Update) only require standard authentication (`Depends(get_current_user)`). This means *any* user (including a Manager or Stock Manager) can technically create an order via the API. In the frontend, the `RoleRedirect` pushes cashiers directly to `/pos` and stock managers to `/stock/dashboard`, but the frontend `App.tsx` router doesn't strictly block roles from accessing other components if they type in the URL, unless the component itself checks `user.role`.
* **Cashier Read-Only Access**: Because many GET endpoints (like `/api/stock`, `/api/products`, `/api/ai/recommendations`) are open to all authenticated users, Cashiers have backend permission to view stock levels, categories, and AI recommendations. The UML diagram should represent these as Shared Use Cases, even if the POS UI doesn't explicitly surface them.
