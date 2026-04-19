from db_functions import connect_to_db
import pandas as pd

print("1. Deleting from Database...")
conn = connect_to_db()
cursor = conn.cursor()

cursor.execute("""
    SELECT TOP 2 entry_id, product_id, change_quantity 
    FROM stock_entries 
    WHERE change_type = 'Restock' 
    ORDER BY entry_date DESC, entry_id DESC
""")
rows = cursor.fetchall()

if len(rows) > 0:
    for row in rows:
        print(f"Deleting entry_id {row[0]} (product_id {row[1]}, qty {row[2]})")
        cursor.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE product_id = ?", row[2], row[1])
        cursor.execute("DELETE FROM stock_entries WHERE entry_id = ?", row[0])
    conn.commit()
    print("Database updated successfully.")
else:
    print("No restock entries found.")

print("\n2. Deleting from CSV (Dataset)...")
try:
    csv_path = "Data Set/stock_entries.csv"
    df = pd.read_csv(csv_path)
    
    # Get last two restock indices
    restocks = df[df['change_type'] == 'Restock']
    if len(restocks) >= 2:
        indices_to_drop = restocks.tail(2).index
        df = df.drop(indices_to_drop)
        df.to_csv(csv_path, index=False)
        print(f"Dropped {len(indices_to_drop)} rows from {csv_path}")
    else:
        print("Not enough restock entries in CSV.")
except Exception as e:
    print("Error updating CSV:", e)
