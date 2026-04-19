import pandas as pd
import pyodbc
from datetime import datetime


# ─────────────────────────────────────────────
#  CONNECTION
# ─────────────────────────────────────────────

def connect_to_db():
    """Create and return a pyodbc connection to SQL Server (SSMS)."""
    return pyodbc.connect(
        'Driver={SQL Server};'
        'Server=Arpit_Laptop\\SQLEXPRESS;'
        'Database=new_schema;'
        'Trusted_Connection=yes;'
    )


# ─────────────────────────────────────────────
#  DASHBOARD KPI METRICS
# ─────────────────────────────────────────────

def get_basic_info(conn):
    """Return a dict of key business metrics for the KPI cards."""
    cursor = conn.cursor()
    queries = {
        "Total Suppliers": "SELECT COUNT(*) FROM suppliers",
        "Total Products": "SELECT COUNT(*) FROM products",
        "Total Categories": "SELECT COUNT(DISTINCT category) FROM products",
        "Total Stock Value": "SELECT ROUND(SUM(stock_quantity * price), 2) FROM products",
        "Total Sale Value (Last 3 Months)": """
            SELECT ROUND(SUM(ABS(se.change_quantity) * p.price), 2)
            FROM stock_entries se
            JOIN products p ON se.product_id = p.product_id
            WHERE se.change_type = 'Sale'
              AND se.entry_date >= (SELECT DATEADD(MONTH, -3, MAX(entry_date)) FROM stock_entries)
        """,
        "Total Restock Value (Last 3 Months)": """
            SELECT ROUND(SUM(ABS(se.change_quantity) * p.price), 2)
            FROM stock_entries se
            JOIN products p ON se.product_id = p.product_id
            WHERE se.change_type = 'Restock'
              AND se.entry_date >= (SELECT DATEADD(MONTH, -3, MAX(entry_date)) FROM stock_entries)
        """,
        "Low Stock (No Pending Reorder)": """
            SELECT COUNT(*)
            FROM products p
            WHERE p.stock_quantity < p.reorder_level
              AND p.product_id NOT IN (
                  SELECT DISTINCT product_id FROM reorders WHERE status = 'Ordered'
              )
        """,
        "Pending Reorders": "SELECT COUNT(*) FROM reorders WHERE status = 'Ordered'",
        "Active Shipments": """
            SELECT COUNT(*) FROM shipments
            WHERE shipment_date >= (SELECT DATEADD(MONTH, -1, MAX(shipment_date)) FROM shipments)
        """,
        "Avg Product Price": "SELECT ROUND(AVG(price), 2) FROM products",
    }
    result = {}
    for label, query in queries.items():
        try:
            cursor.execute(query)
            row = cursor.fetchone()
            result[label] = row[0] if row and row[0] is not None else 0
        except Exception as e:
            print(f"Error in [{label}]: {e}")
            result[label] = "N/A"
    return result


# ─────────────────────────────────────────────
#  PRODUCTS
# ─────────────────────────────────────────────

def get_all_products(conn):
    query = """
        SELECT
            p.product_id        AS [ID],
            p.product_name      AS [Product Name],
            p.category          AS [Category],
            p.price             AS [Price (INR)],
            p.stock_quantity    AS [Stock Qty],
            p.reorder_level     AS [Reorder Level],
            s.supplier_name     AS [Supplier],
            ROUND(p.stock_quantity * p.price, 2) AS [Stock Value (INR)],
            CASE
                WHEN p.stock_quantity = 0                       THEN 'Out of Stock'
                WHEN p.stock_quantity < p.reorder_level         THEN 'Low Stock'
                WHEN p.stock_quantity < p.reorder_level * 1.25  THEN 'Warning'
                ELSE 'Healthy'
            END AS [Status]
        FROM products p
        JOIN suppliers s ON p.supplier_id = s.supplier_id
        ORDER BY p.product_name ASC
    """
    return pd.read_sql(query, conn)


def get_products_dropdown(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, product_name FROM products ORDER BY product_name")
    return cursor.fetchall()


def get_category_list(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
    return [row[0] for row in cursor.fetchall()]


def get_products_by_category(conn, category):
    query = """
        SELECT
            p.product_id        AS [ID],
            p.product_name      AS [Product Name],
            p.category          AS [Category],
            p.price             AS [Price (INR)],
            p.stock_quantity    AS [Stock Qty],
            p.reorder_level     AS [Reorder Level],
            s.supplier_name     AS [Supplier],
            ROUND(p.stock_quantity * p.price, 2) AS [Stock Value (INR)],
            CASE
                WHEN p.stock_quantity = 0                       THEN 'Out of Stock'
                WHEN p.stock_quantity < p.reorder_level         THEN 'Low Stock'
                WHEN p.stock_quantity < p.reorder_level * 1.25  THEN 'Warning'
                ELSE 'Healthy'
            END AS [Status]
        FROM products p
        JOIN suppliers s ON p.supplier_id = s.supplier_id
        WHERE p.category = ?
        ORDER BY p.product_name
    """
    return pd.read_sql(query, conn, params=[category])


def search_products(conn, keyword):
    query = """
        SELECT
            p.product_id        AS [ID],
            p.product_name      AS [Product Name],
            p.category          AS [Category],
            p.price             AS [Price (INR)],
            p.stock_quantity    AS [Stock Qty],
            p.reorder_level     AS [Reorder Level],
            s.supplier_name     AS [Supplier],
            ROUND(p.stock_quantity * p.price, 2) AS [Stock Value (INR)],
            CASE
                WHEN p.stock_quantity = 0                       THEN 'Out of Stock'
                WHEN p.stock_quantity < p.reorder_level         THEN 'Low Stock'
                WHEN p.stock_quantity < p.reorder_level * 1.25  THEN 'Warning'
                ELSE 'Healthy'
            END AS [Status]
        FROM products p
        JOIN suppliers s ON p.supplier_id = s.supplier_id
        WHERE p.product_name LIKE ? OR p.category LIKE ?
        ORDER BY p.product_name
    """
    kw = f"%{keyword}%"
    return pd.read_sql(query, conn, params=[kw, kw])


def add_product(conn, name, category, price, stock_qty, reorder_level, supplier_id):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO products (product_name, category, price, stock_quantity, reorder_level, supplier_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, name, category, float(price), int(stock_qty), int(reorder_level), int(supplier_id))
        conn.commit()
        return True, "Product added successfully."
    except Exception as e:
        return False, str(e)


def update_product_price(conn, product_id, new_price):
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE products SET price = ? WHERE product_id = ?",
                       float(new_price), int(product_id))
        conn.commit()
        return True, f"Price updated to {new_price:.2f}"
    except Exception as e:
        return False, str(e)


def get_product_history(conn, product_id):
    query = """
        SELECT
            se.entry_id, p.product_name, se.change_type, se.change_quantity, se.entry_date
        FROM stock_entries se
        JOIN products p ON se.product_id = p.product_id
        WHERE se.product_id = ?
        ORDER BY se.entry_date DESC
    """
    return pd.read_sql(query, conn, params=[product_id])


def needs_restock(conn, product_id):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT stock_quantity, reorder_level FROM products WHERE product_id = ?",
        int(product_id)
    )
    row = cursor.fetchone()
    if row:
        return row[0] < row[1], row[0], row[1]
    return False, 0, 0


# ─────────────────────────────────────────────
#  SUPPLIERS
# ─────────────────────────────────────────────

def get_all_suppliers(conn):
    query = """
        SELECT
            s.supplier_id       AS [ID],
            s.supplier_name     AS [Supplier Name],
            s.contact_name      AS [Contact Person],
            s.email             AS [Email],
            s.phone             AS [Phone],
            s.address           AS [Address],
            COUNT(p.product_id) AS [Products Supplied],
            ROUND(SUM(p.stock_quantity * p.price), 2) AS [Total Stock Value (INR)]
        FROM suppliers s
        LEFT JOIN products p ON s.supplier_id = p.supplier_id
        GROUP BY s.supplier_id, s.supplier_name, s.contact_name, s.email, s.phone, s.address
        ORDER BY s.supplier_name
    """
    return pd.read_sql(query, conn)


def get_suppliers_dropdown(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT supplier_id, supplier_name FROM suppliers ORDER BY supplier_name")
    return cursor.fetchall()


def get_supplier_performance(conn):
    query = """
        SELECT
            s.supplier_name     AS [Supplier],
            COUNT(sh.shipment_id) AS [Total Shipments],
            SUM(sh.quantity_received) AS [Total Units Received]
        FROM shipments sh
        JOIN suppliers s ON sh.supplier_id = s.supplier_id
        GROUP BY s.supplier_name
        ORDER BY [Total Shipments] DESC
    """
    return pd.read_sql(query, conn)


# ─────────────────────────────────────────────
#  STOCK ENTRIES
# ─────────────────────────────────────────────

def get_stock_entries(conn, limit=200):
    query = f"""
        SELECT TOP {int(limit)}
            se.entry_id         AS [Entry ID],
            p.product_name      AS [Product],
            p.category          AS [Category],
            se.change_type      AS [Type],
            ABS(se.change_quantity) AS [Quantity],
            se.entry_date       AS [Date]
        FROM stock_entries se
        JOIN products p ON se.product_id = p.product_id
        ORDER BY se.entry_date DESC, se.entry_id DESC
    """
    return pd.read_sql(query, conn)


def get_low_stock_products(conn):
    query = """
        SELECT
            p.product_id, p.product_name, p.category,
            p.stock_quantity, p.reorder_level,
            s.supplier_name,
            ROUND((CAST(p.stock_quantity AS FLOAT) / NULLIF(p.reorder_level, 0)) * 100, 1) AS [Stock Pct]
        FROM products p
        JOIN suppliers s ON p.supplier_id = s.supplier_id
        WHERE p.stock_quantity < p.reorder_level
        ORDER BY [Stock Pct] ASC
    """
    return pd.read_sql(query, conn)


def record_stock_movement(conn, product_id, change_type, quantity):
    cursor = conn.cursor()
    try:
        qty = -abs(int(quantity)) if change_type == 'Sale' else abs(int(quantity))
        cursor.execute("""
            INSERT INTO stock_entries (product_id, change_quantity, change_type, entry_date)
            VALUES (?, ?, ?, GETDATE())
        """, int(product_id), qty, change_type)
        if change_type == 'Sale':
            cursor.execute("""
                UPDATE products SET stock_quantity = stock_quantity - ?
                WHERE product_id = ?
            """, abs(int(quantity)), int(product_id))
        else:
            cursor.execute("""
                UPDATE products SET stock_quantity = stock_quantity + ?
                WHERE product_id = ?
            """, abs(int(quantity)), int(product_id))
        conn.commit()
        return True, f"{change_type} of {abs(qty)} units recorded."
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────
#  REORDERS
# ─────────────────────────────────────────────

def get_reorders(conn):
    query = """
        SELECT
            r.reorder_id        AS [Reorder ID],
            p.product_name      AS [Product],
            p.category          AS [Category],
            r.reorder_quantity  AS [Qty Ordered],
            r.reorder_date      AS [Order Date],
            r.status            AS [Status],
            s.supplier_name     AS [Supplier]
        FROM reorders r
        JOIN products p ON r.product_id = p.product_id
        JOIN suppliers s ON p.supplier_id = s.supplier_id
        ORDER BY r.reorder_date DESC
    """
    return pd.read_sql(query, conn)


def place_reorder(conn, product_id, quantity):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO reorders (product_id, reorder_quantity, reorder_date, status)
            VALUES (?, ?, GETDATE(), 'Ordered')
        """, int(product_id), int(quantity))
        conn.commit()
        return True, "Reorder placed successfully."
    except Exception as e:
        return False, str(e)


def mark_reorder_received(conn, reorder_id):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT product_id, reorder_quantity FROM reorders WHERE reorder_id = ?
        """, int(reorder_id))
        row = cursor.fetchone()
        if not row:
            return False, "Reorder not found."
        product_id, qty = row[0], row[1]
        cursor.execute("""
            UPDATE reorders SET status = 'Received' WHERE reorder_id = ?
        """, int(reorder_id))
        cursor.execute("""
            INSERT INTO stock_entries (product_id, change_quantity, change_type, entry_date)
            VALUES (?, ?, 'Restock', GETDATE())
        """, int(product_id), int(qty))
        cursor.execute("""
            UPDATE products SET stock_quantity = stock_quantity + ?
            WHERE product_id = ?
        """, int(qty), int(product_id))
        conn.commit()
        return True, f"Reorder #{reorder_id} marked as Received. Stock updated by +{qty}."
    except Exception as e:
        return False, str(e)


def get_reorder_status_summary(conn):
    query = """
        SELECT status AS [Status], COUNT(*) AS [Count]
        FROM reorders
        GROUP BY status
    """
    return pd.read_sql(query, conn)


# ─────────────────────────────────────────────
#  SHIPMENTS
# ─────────────────────────────────────────────

def get_shipments(conn):
    query = """
        SELECT
            sh.shipment_id          AS [Shipment ID],
            p.product_name          AS [Product],
            p.category              AS [Category],
            s.supplier_name         AS [Supplier],
            sh.quantity_received    AS [Qty Received],
            sh.shipment_date        AS [Shipment Date]
        FROM shipments sh
        JOIN products p ON sh.product_id = p.product_id
        JOIN suppliers s ON sh.supplier_id = s.supplier_id
        ORDER BY sh.shipment_date DESC
    """
    return pd.read_sql(query, conn)


# ─────────────────────────────────────────────
#  ANALYTICS / CHARTS DATA
# ─────────────────────────────────────────────

def get_monthly_sales_trend(conn):
    query = """
        SELECT
            FORMAT(se.entry_date, 'MMM yyyy') AS [Month],
            YEAR(se.entry_date) * 100 + MONTH(se.entry_date) AS sort_key,
            ROUND(SUM(ABS(se.change_quantity) * p.price), 2) AS [Sales Value]
        FROM stock_entries se
        JOIN products p ON se.product_id = p.product_id
        WHERE se.change_type = 'Sale'
          AND se.entry_date >= DATEADD(MONTH, -12, (SELECT MAX(entry_date) FROM stock_entries))
        GROUP BY FORMAT(se.entry_date, 'MMM yyyy'),
                 YEAR(se.entry_date) * 100 + MONTH(se.entry_date)
        ORDER BY sort_key ASC
    """
    return pd.read_sql(query, conn)


def get_monthly_restock_trend(conn):
    query = """
        SELECT
            FORMAT(se.entry_date, 'MMM yyyy') AS [Month],
            YEAR(se.entry_date) * 100 + MONTH(se.entry_date) AS sort_key,
            ROUND(SUM(ABS(se.change_quantity) * p.price), 2) AS [Restock Value]
        FROM stock_entries se
        JOIN products p ON se.product_id = p.product_id
        WHERE se.change_type = 'Restock'
          AND se.entry_date >= DATEADD(MONTH, -12, (SELECT MAX(entry_date) FROM stock_entries))
        GROUP BY FORMAT(se.entry_date, 'MMM yyyy'),
                 YEAR(se.entry_date) * 100 + MONTH(se.entry_date)
        ORDER BY sort_key ASC
    """
    return pd.read_sql(query, conn)


def get_category_breakdown(conn):
    query = """
        SELECT
            category                                    AS [Category],
            COUNT(*)                                    AS [Products],
            ROUND(SUM(stock_quantity * price), 2)       AS [Stock Value],
            ROUND(AVG(price), 2)                        AS [Avg Price]
        FROM products
        GROUP BY category
        ORDER BY [Stock Value] DESC
    """
    return pd.read_sql(query, conn)


def get_top_products_by_value(conn, top_n=10):
    query = f"""
        SELECT TOP {int(top_n)}
            p.product_name                              AS [Product],
            p.category                                  AS [Category],
            ROUND(p.stock_quantity * p.price, 2)        AS [Stock Value],
            p.stock_quantity                            AS [Qty],
            p.price                                     AS [Price]
        FROM products p
        ORDER BY [Stock Value] DESC
    """
    return pd.read_sql(query, conn)


def get_stock_status_counts(conn):
    query = """
        SELECT
            CASE
                WHEN stock_quantity = 0                          THEN 'Out of Stock'
                WHEN stock_quantity < reorder_level              THEN 'Low Stock'
                WHEN stock_quantity < reorder_level * 1.25       THEN 'Warning'
                ELSE 'Healthy'
            END AS [Status],
            COUNT(*) AS [Count]
        FROM products
        GROUP BY
            CASE
                WHEN stock_quantity = 0                          THEN 'Out of Stock'
                WHEN stock_quantity < reorder_level              THEN 'Low Stock'
                WHEN stock_quantity < reorder_level * 1.25       THEN 'Warning'
                ELSE 'Healthy'
            END
    """
    return pd.read_sql(query, conn)


def get_sales_vs_restock(conn):
    query = """
        SELECT
            FORMAT(entry_date, 'MMM yyyy')                          AS [Month],
            YEAR(entry_date) * 100 + MONTH(entry_date)              AS sort_key,
            SUM(CASE WHEN change_type='Sale'    THEN ABS(change_quantity) ELSE 0 END) AS [Units Sold],
            SUM(CASE WHEN change_type='Restock' THEN ABS(change_quantity) ELSE 0 END) AS [Units Restocked]
        FROM stock_entries
        WHERE entry_date >= DATEADD(MONTH, -6, (SELECT MAX(entry_date) FROM stock_entries))
        GROUP BY FORMAT(entry_date, 'MMM yyyy'),
                 YEAR(entry_date) * 100 + MONTH(entry_date)
        ORDER BY sort_key ASC
    """
    return pd.read_sql(query, conn)


def get_recent_activity(conn, limit=15):
    query = f"""
        SELECT TOP {int(limit)}
            se.entry_date       AS [Date],
            p.product_name      AS [Product],
            se.change_type      AS [Type],
            ABS(se.change_quantity) AS [Qty]
        FROM stock_entries se
        JOIN products p ON se.product_id = p.product_id
        ORDER BY se.entry_date DESC, se.entry_id DESC
    """
    return pd.read_sql(query, conn)
