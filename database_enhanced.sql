-- ShopLocal Enhanced Database Schema
-- Supports: Web App, Mobile App, Admin Panel, Inventory, Recommendations

CREATE DATABASE IF NOT EXISTS shoplocal;
USE shoplocal;

-- ============================================================================
-- PRODUCTS TABLE (Enhanced)
-- ============================================================================
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    image_url VARCHAR(500),
    stock INT DEFAULT 0,
    category VARCHAR(100),
    low_stock_threshold INT DEFAULT 10,
    status ENUM('active', 'inactive', 'out_of_stock') DEFAULT 'active',
    views INT DEFAULT 0,
    purchases INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_status (status),
    INDEX idx_purchases (purchases)
);

-- ============================================================================
-- ADMIN USERS TABLE
-- ============================================================================
CREATE TABLE admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    full_name VARCHAR(200),
    role ENUM('admin', 'manager', 'staff') DEFAULT 'staff',
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default admin user (password: admin123 - CHANGE IN PRODUCTION!)
-- Password hash for 'admin123' using werkzeug
INSERT INTO admin_users (username, password_hash, email, full_name, role) VALUES
('admin', 'pbkdf2:sha256:600000$vJZQXZ9K$8f3d0c6e4a5b2d1f9e8c7b6a5d4c3b2a1f0e9d8c7b6a5d4c3b2a1f0e9d8c7b6a', 'admin@shoplocal.com', 'System Administrator', 'admin');

-- ============================================================================
-- ORDERS TABLE (Enhanced)
-- ============================================================================
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(200) NOT NULL,
    customer_email VARCHAR(200) NOT NULL,
    customer_phone VARCHAR(20),
    total_amount DECIMAL(10, 2) NOT NULL,
    status ENUM('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    payment_status ENUM('pending', 'paid', 'failed', 'refunded') DEFAULT 'pending',
    shipping_address TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_order_number (order_number),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- ============================================================================
-- ORDER ITEMS TABLE
-- ============================================================================
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    product_name VARCHAR(200),
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id)
);

-- ============================================================================
-- INVENTORY LOG TABLE
-- ============================================================================
CREATE TABLE inventory_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    change_type ENUM('stock_in', 'stock_out', 'adjustment', 'sale') NOT NULL,
    quantity_change INT NOT NULL,
    previous_stock INT NOT NULL,
    new_stock INT NOT NULL,
    reference_type VARCHAR(50),
    reference_id INT,
    notes TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (created_by) REFERENCES admin_users(id),
    INDEX idx_product_id (product_id),
    INDEX idx_created_at (created_at)
);

-- ============================================================================
-- PRODUCT VIEWS TABLE (For Recommendations)
-- ============================================================================
CREATE TABLE product_views (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    session_id VARCHAR(100),
    ip_address VARCHAR(50),
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_product_id (product_id),
    INDEX idx_viewed_at (viewed_at)
);

-- ============================================================================
-- PRODUCT RECOMMENDATIONS TABLE
-- ============================================================================
CREATE TABLE product_recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    recommended_product_id INT NOT NULL,
    score DECIMAL(5, 2) DEFAULT 0.00,
    recommendation_type ENUM('also_bought', 'similar', 'category', 'trending') DEFAULT 'also_bought',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (recommended_product_id) REFERENCES products(id),
    UNIQUE KEY unique_recommendation (product_id, recommended_product_id, recommendation_type),
    INDEX idx_product_id (product_id),
    INDEX idx_score (score)
);

-- ============================================================================
-- INSERT SAMPLE PRODUCTS (30 Indian Artisan Products)
-- ============================================================================
INSERT INTO products (name, description, price, image_url, stock, category, low_stock_threshold, status) VALUES
('Handwoven Cotton Saree', 'Beautiful handloom saree from Rajasthan artisans', 2499.00, 'https://via.placeholder.com/400x400?text=Saree', 15, 'Clothing', 5, 'active'),
('Terracotta Pottery Set', 'Traditional clay pottery set, hand-painted', 899.00, 'https://via.placeholder.com/400x400?text=Pottery', 25, 'Home Decor', 10, 'active'),
('Wooden Carved Elephant', 'Handcrafted wooden elephant statue', 1299.00, 'https://via.placeholder.com/400x400?text=Elephant', 20, 'Handicrafts', 5, 'active'),
('Brass Oil Lamp (Diya)', 'Traditional brass diya for festivals', 399.00, 'https://via.placeholder.com/400x400?text=Diya', 50, 'Pooja Items', 15, 'active'),
('Madhubani Painting', 'Original Madhubani art on canvas', 3499.00, 'https://via.placeholder.com/400x400?text=Painting', 8, 'Art', 3, 'active'),
('Jute Shopping Bag', 'Eco-friendly handwoven jute bag', 299.00, 'https://via.placeholder.com/400x400?text=Bag', 100, 'Accessories', 20, 'active'),
('Copper Water Bottle', 'Pure copper water bottle, handmade', 799.00, 'https://via.placeholder.com/400x400?text=Bottle', 40, 'Kitchen', 10, 'active'),
('Block Print Bedsheet', 'Hand block printed cotton bedsheet', 1899.00, 'https://via.placeholder.com/400x400?text=Bedsheet', 30, 'Home Textile', 8, 'active'),
('Silver Anklet (Payal)', 'Traditional silver anklet with bells', 1599.00, 'https://via.placeholder.com/400x400?text=Anklet', 12, 'Jewelry', 5, 'active'),
('Clay Tea Cups Set', 'Set of 6 handmade clay tea cups', 499.00, 'https://via.placeholder.com/400x400?text=Cups', 35, 'Kitchen', 10, 'active'),
('Bamboo Wind Chimes', 'Handcrafted bamboo wind chimes', 599.00, 'https://via.placeholder.com/400x400?text=Chimes', 28, 'Home Decor', 10, 'active'),
('Leather Journal', 'Hand-stitched leather diary', 899.00, 'https://via.placeholder.com/400x400?text=Journal', 22, 'Stationery', 8, 'active'),
('Dhokra Art Figurine', 'Traditional metal casting art piece', 2199.00, 'https://via.placeholder.com/400x400?text=Figurine', 10, 'Art', 3, 'active'),
('Cotton Kurta', 'Handloom cotton kurta for men', 1299.00, 'https://via.placeholder.com/400x400?text=Kurta', 45, 'Clothing', 12, 'active'),
('Wooden Spice Box', 'Carved wooden masala dabba', 699.00, 'https://via.placeholder.com/400x400?text=Spicebox', 18, 'Kitchen', 8, 'active'),
('Handmade Soap Set', 'Natural herbal soap collection', 399.00, 'https://via.placeholder.com/400x400?text=Soap', 60, 'Personal Care', 15, 'active'),
('Cane Basket', 'Traditional cane basket, handwoven', 549.00, 'https://via.placeholder.com/400x400?text=Basket', 32, 'Home Storage', 10, 'active'),
('Pashmina Shawl', 'Pure pashmina wool shawl', 4999.00, 'https://via.placeholder.com/400x400?text=Shawl', 6, 'Clothing', 3, 'active'),
('Marble Coaster Set', 'Hand-painted marble coasters (set of 4)', 799.00, 'https://via.placeholder.com/400x400?text=Coasters', 24, 'Home Decor', 8, 'active'),
('Dreamcatcher', 'Handmade dreamcatcher with feathers', 449.00, 'https://via.placeholder.com/400x400?text=Dreamcatcher', 38, 'Home Decor', 10, 'active'),
('Peacock Wall Hanging', 'Metal peacock wall art', 1899.00, 'https://via.placeholder.com/400x400?text=Peacock', 14, 'Wall Art', 5, 'active'),
('Embroidered Cushion Cover', 'Hand-embroidered cushion cover', 599.00, 'https://via.placeholder.com/400x400?text=Cushion', 55, 'Home Textile', 15, 'active'),
('Sandalwood Incense', 'Pure sandalwood agarbatti pack', 199.00, 'https://via.placeholder.com/400x400?text=Incense', 80, 'Pooja Items', 20, 'active'),
('Clay Ganesh Idol', 'Eco-friendly clay Ganesh statue', 349.00, 'https://via.placeholder.com/400x400?text=Ganesh', 42, 'Pooja Items', 15, 'active'),
('Warli Art Plate', 'Decorative plate with Warli painting', 899.00, 'https://via.placeholder.com/400x400?text=Plate', 19, 'Home Decor', 8, 'active'),
('Handloom Table Runner', 'Cotton table runner with tribal print', 699.00, 'https://via.placeholder.com/400x400?text=Runner', 27, 'Home Textile', 10, 'active'),
('Wooden Puzzle Box', 'Handcrafted wooden secret box', 1099.00, 'https://via.placeholder.com/400x400?text=Box', 16, 'Toys', 5, 'active'),
('Terracotta Jewelry', 'Eco-friendly terracotta necklace set', 499.00, 'https://via.placeholder.com/400x400?text=Jewelry', 33, 'Jewelry', 10, 'active'),
('Banana Fiber Lamp', 'Handmade eco-lamp from banana fiber', 1499.00, 'https://via.placeholder.com/400x400?text=Lamp', 11, 'Lighting', 5, 'active'),
('Tribal Mask', 'Handpainted traditional tribal mask', 1199.00, 'https://via.placeholder.com/400x400?text=Mask', 9, 'Art', 3, 'active');

-- ============================================================================
-- GENERATE INITIAL RECOMMENDATIONS (Category-based)
-- ============================================================================
-- This will be enhanced by the recommendation engine
INSERT INTO product_recommendations (product_id, recommended_product_id, score, recommendation_type)
SELECT p1.id, p2.id, 70.00, 'category'
FROM products p1
CROSS JOIN products p2
WHERE p1.category = p2.category
  AND p1.id != p2.id
  AND p2.status = 'active'
LIMIT 100;
