select* from products
select* from reorders
select* from shipments
select* from stock_entries
select* from suppliers


-- 1  Total Suppliers
select COUNT(*) as total_suppliers from suppliers
-- 2 Total Products
select COUNT(*) as total_products from products
-- 3 Total categories dealing
select count(*) as total_category from products
-- 4 Total sales value made in last 3 months (quantity* price)
SELECT 
    ROUND(SUM(ABS(se.change_quantity) * p.price), 2) AS total_sales_value
FROM stock_entries AS se
JOIN products AS p ON p.product_id = se.product_id
WHERE se.change_type = 'Sale'
  AND se.entry_date >= (
      SELECT DATEADD(MONTH, -3, MAX(entry_date)) 
      FROM stock_entries
  ); 
 -- 5 Total restock value made in last 3 months (quantity* price)
select round(sum(abs(se.change_quantity)* p.price),2) as total_restock_value_in_last_3_months
from stock_entries as se 
join products p 
on p.product_id= se.product_id
where se.change_type='Restock'
and 
se.entry_date>= 
  (
    select DATEADD(MONTH, -3, MAX(entry_date)) from stock_entries
 ) 
 -- 6 Product qunatity less then reorder lavel 
select count(*) from products  as p  where p.stock_quantity<p.reorder_level
 and  product_id NOT IN 
 (
select distinct product_id from reorders  where status ='Pending'
)

-- 7 Suppliers adn their  contact details
select supplier_name, contact_name , email, phone from suppliers

-- 8 Product with their suppliers and current stock
select p.product_name,s.supplier_name , p.stock_quantity, p.reorder_level
from products as p 
join suppliers  s on
p.supplier_id = s.supplier_id
order by p.product_name ASC

-- 9 Product needing reorder
select product_id ,product_name, stock_quantity, reorder_level  from products where stock_quantity<reorder_level

-- 10  Add an new product to the database
CREATE PROCEDURE AddNewProductManualID
   @p_name VARCHAR(255),
   @p_category VARCHAR(100),
   @p_price DECIMAL(10,2),
   @p_stock INT,
   @p_reorder INT,
   @p_supplier INT
AS
BEGIN
    -- Wrap in a transaction so if one insert fails, they all fail (keeps data clean)
    BEGIN TRANSACTION;
    BEGIN TRY
        DECLARE @new_prod_id INT;
        DECLARE @new_shipment_id INT;
        DECLARE @new_entry_id INT;

        -- 1. Calculate and Insert Product
        SELECT @new_prod_id = ISNULL(MAX(product_id), 0) + 1 FROM products;
        INSERT INTO products (product_id, product_name, category, price, stock_quantity, reorder_level, supplier_id)
        VALUES (@new_prod_id, @p_name, @p_category, @p_price, @p_stock, @p_reorder, @p_supplier);

        -- 2. Calculate and Insert Shipment
        SELECT @new_shipment_id = ISNULL(MAX(shipment_id), 0) + 1 FROM shipments;
        INSERT INTO shipments (shipment_id, product_id, supplier_id, quantity_received, shipment_date)
        VALUES (@new_shipment_id, @new_prod_id, @p_supplier, @p_stock, GETDATE());

        -- 3. Calculate and Insert Stock Entry
        SELECT @new_entry_id = ISNULL(MAX(entry_id), 0) + 1 FROM stock_entries;
        INSERT INTO stock_entries (entry_id, product_id, change_quantity, change_type, entry_date)
        VALUES (@new_entry_id, @new_prod_id, @p_stock, 'Restock', GETDATE());

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW; -- Sends the error back to Python
    END CATCH
END
GO

-- Use EXEC instead of CALL
EXEC AddNewProductManualID 'Smart Watch', 'Electronics', 99.99, 100, 25, 5;




-- Use single quotes for the string 'Bettles'
SELECT * FROM products 
WHERE product_name = 'Smart Watch';

-- These remain the same as they use numeric IDs
SELECT * FROM shipments 
WHERE product_id = 201;

SELECT * FROM stock_entries 
WHERE product_id = 201;

---- 11 Product History , [ finding shipment , sales , purchase]
IF OBJECT_ID('product_inventory_history', 'V') IS NOT NULL
    DROP VIEW product_inventory_history;
GO

CREATE VIEW product_inventory_history AS 
SELECT 
    pih.product_id,
    pih.record_type,
    pih.record_date,
    pih.Quantity,
    pih.change_type,
    pr.supplier_id
FROM 
(
    SELECT 
        product_id,
        'Shipment' AS record_type, -- Single quotes for strings
        shipment_date AS record_date,
        quantity_received AS Quantity,
        CAST(NULL AS VARCHAR(50)) AS change_type -- Explicit NULL with type
    FROM shipments

    UNION ALL

    SELECT 
        product_id,
        'Stock Entry' AS record_type,
        entry_date AS record_date,
        change_quantity AS quantity,
        change_type
    FROM stock_entries
) pih
JOIN products pr ON pr.product_id = pih.product_id;
GO

-- To test the view
SELECT * FROM product_inventory_history
WHERE product_id = 123
ORDER BY record_date DESC;

-- 12 Place an reorder
IF EXISTS (SELECT 1 FROM products WHERE product_id = 101)
BEGIN
    INSERT INTO reorders (reorder_id, product_id, reorder_quantity, reorder_date, status)
    SELECT ISNULL(MAX(reorder_id), 0) + 1, 101, 200, GETDATE(), 'ordered' FROM reorders;
    
    PRINT 'Reorder placed successfully.';
END
ELSE
BEGIN
    PRINT 'Error: Product ID 101 does not exist.';
END
select * from stock_entries
select * from shipments 
select * from reorders
select * from products

---receive reorder


CREATE PROCEDURE MarkReorderAsReceived
    @in_reorder_id INT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @prod_id INT;
    DECLARE @qty INT;
    DECLARE @sup_id INT;
    DECLARE @new_shipment_id INT;
    DECLARE @new_entry_id INT;

    BEGIN TRANSACTION;

    BEGIN TRY
        -- 1. Get product_id and quantity from reorders
        SELECT @prod_id = product_id, @qty = reorder_quantity 
        FROM reorders
        WHERE reorder_id = @in_reorder_id;

        -- 2. Get supplier_id from Products
        SELECT @sup_id = supplier_id 
        FROM products 
        WHERE product_id = @prod_id;

        -- 3. Update reorder table status to 'Received'
        UPDATE reorders 
        SET status = 'Received'
        WHERE reorder_id = @in_reorder_id;

        -- 4. Update quantity in product table
        UPDATE products 
        SET stock_quantity = stock_quantity + @qty
        WHERE product_id = @prod_id;

        -- 5. Insert record into shipment table
        SELECT @new_shipment_id = ISNULL(MAX(shipment_id), 0) + 1 FROM shipments;
        INSERT INTO shipments (shipment_id, product_id, supplier_id, quantity_received, shipment_date)
        VALUES (@new_shipment_id, @prod_id, @sup_id, @qty, GETDATE());

        -- 6. Insert record into stock_entries
        SELECT @new_entry_id = ISNULL(MAX(entry_id), 0) + 1 FROM stock_entries;
        INSERT INTO stock_entries (entry_id, product_id, change_quantity, change_type, entry_date)
        VALUES (@new_entry_id, @prod_id, @qty, 'Restock', GETDATE());

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        -- Raise the error so Python can catch it
        THROW; 
    END CATCH
END
GO
select * from reorders where  reorder_id=13
select * from products where product_name= 'Someone Shirt'
select * from reorders where reorder_id= 1
select * from stock_entries where product_id=164 order by entry_date desc
select * from shipments  order  by shipment_id desc