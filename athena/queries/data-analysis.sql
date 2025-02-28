-- Sample Athena queries for data analysis

-- 1. Basic data exploration
SELECT 
    COUNT(*) AS total_records,
    COUNT(DISTINCT customer_id) AS unique_customers,
    MIN(order_date) AS earliest_order,
    MAX(order_date) AS latest_order
FROM processed_data.orders;

-- 2. Sales by month
SELECT 
    DATE_FORMAT(order_date, '%Y-%m') AS order_month,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_sales,
    AVG(total_amount) AS average_order_value
FROM processed_data.orders
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY order_month;

-- 3. Top selling products
SELECT 
    p.product_name,
    p.category,
    COUNT(oi.order_id) AS order_count,
    SUM(oi.quantity) AS total_quantity,
    SUM(oi.quantity * oi.unit_price) AS total_revenue
FROM processed_data.order_items oi
JOIN processed_data.products p ON oi.product_id = p.product_id
GROUP BY p.product_name, p.category
ORDER BY total_revenue DESC
LIMIT 10;

-- 4. Customer segmentation by purchase frequency
SELECT 
    purchase_frequency,
    COUNT(*) AS customer_count,
    AVG(total_spent) AS average_spend
FROM (
    SELECT 
        customer_id,
        COUNT(*) AS purchase_count,
        SUM(total_amount) AS total_spent,
        CASE 
            WHEN COUNT(*) >= 10 THEN 'High Frequency'
            WHEN COUNT(*) >= 5 THEN 'Medium Frequency'
            ELSE 'Low Frequency'
        END AS purchase_frequency
    FROM processed_data.orders
    GROUP BY customer_id
) customer_segments
GROUP BY purchase_frequency
ORDER BY customer_count DESC;

-- 5. Processing time analysis
SELECT 
    DATE_FORMAT(order_date, '%Y-%m') AS order_month,
    AVG(processing_days) AS avg_processing_days,
    MIN(processing_days) AS min_processing_days,
    MAX(processing_days) AS max_processing_days
FROM processed_data.orders
WHERE processing_days IS NOT NULL
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY order_month;

-- 6. Geographic distribution of sales
SELECT 
    c.country,
    c.region,
    COUNT(o.order_id) AS order_count,
    SUM(o.total_amount) AS total_sales
FROM processed_data.orders o
JOIN processed_data.customers c ON o.customer_id = c.customer_id
GROUP BY c.country, c.region
ORDER BY total_sales DESC;

-- 7. Product category performance over time
SELECT 
    DATE_FORMAT(o.order_date, '%Y-%m') AS order_month,
    p.category,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(oi.quantity) AS total_quantity,
    SUM(oi.quantity * oi.unit_price) AS total_revenue
FROM processed_data.orders o
JOIN processed_data.order_items oi ON o.order_id = oi.order_id
JOIN processed_data.products p ON oi.

