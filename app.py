"""
ShopLocal Enhanced - E-commerce Platform
Features: Web App, REST API, Admin Panel, S3 Integration
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pymysql
import os
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
from datetime import datetime
import uuid
import functools

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)  # Enable CORS for mobile app

# ============================================================================
# CONFIGURATION
# ============================================================================


# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'nupur-db.c18yme60g2po.us-west-2.rds.amazonaws.com'),
    'user': os.environ.get('DB_USER', 'nupur'),
    'password': os.environ.get('DB_PASSWORD', 'nupur123123'),
    'database': os.environ.get('DB_NAME', 'shoplocal'),
    'cursorclass': pymysql.cursors.DictCursor
}

# S3 Configuration (Optional - falls back to local storage)
AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET', '')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')
USE_S3 = bool(AWS_S3_BUCKET)
print("USE_S3 =", USE_S3)

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# S3 Client (if configured)
s3_client = None
if USE_S3:
    try:
        s3_client = boto3.client('s3', region_name=AWS_REGION)
    except Exception as e:
        print(f"S3 client initialization failed: {e}")
        USE_S3 = False

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_db_connection():
    """Create database connection"""
    return pymysql.connect(**DB_CONFIG)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

'''def upload_to_s3(file, filename):
    """Upload file to S3 bucket"""
    if not USE_S3 or not s3_client:
        return None
    
    try:
        s3_client.upload_fileobj(
            file,
            AWS_S3_BUCKET,
            f'products/{filename}',
            ExtraArgs={'ACL': 'public-read', 'ContentType': file.content_type}
        )
        return f'https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/products/{filename}'
    except ClientError as e:
        print(f"S3 upload error: {e}")
        return None
 '''
def upload_to_s3(file, filename):
    if not USE_S3 or not s3_client:
        return None

    try:
        s3_client.upload_fileobj(
            file,
            AWS_S3_BUCKET,
            f'images/{filename}',
            ExtraArgs={'ACL': 'public-read', 'ContentType': file.content_type}
        )
        return f'https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/images/{filename}'
    except ClientError as e:
        print(f"S3 upload error: {e}")
        return None

def save_file_locally(file, filename):
    """Save file to local uploads folder"""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return f'/static/uploads/{filename}'

def admin_required(f):
    """Decorator to require admin login"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login to access admin panel', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_order_number():
    """Generate unique order number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = str(uuid.uuid4())[:6].upper()
    return f'SL-{timestamp}-{random_str}'

def update_inventory(product_id, quantity_change, change_type, reference_type=None, reference_id=None, notes=None):
    """Update inventory and log the change"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current stock
    cursor.execute('SELECT stock FROM products WHERE id = %s', (product_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False
    
    previous_stock = result['stock']
    new_stock = previous_stock + quantity_change
    
    if new_stock < 0:
        conn.close()
        return False
    
    # Update product stock
    cursor.execute('UPDATE products SET stock = %s WHERE id = %s', (new_stock, product_id))
    
    # Log inventory change
    admin_id = session.get('admin_id')
    cursor.execute('''
        INSERT INTO inventory_log 
        (product_id, change_type, quantity_change, previous_stock, new_stock, 
         reference_type, reference_id, notes, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (product_id, change_type, quantity_change, previous_stock, new_stock, 
          reference_type, reference_id, notes, admin_id))
    
    # Update product status based on stock
    if new_stock == 0:
        cursor.execute('UPDATE products SET status = %s WHERE id = %s', ('out_of_stock', product_id))
    elif previous_stock == 0 and new_stock > 0:
        cursor.execute('UPDATE products SET status = %s WHERE id = %s', ('active', product_id))
    
    conn.commit()
    conn.close()
    return True

# ============================================================================
# CUSTOMER-FACING ROUTES (Web App)
# ============================================================================

@app.route('/')
def home():
    """Homepage - Display all products"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    category = request.args.get('category')
    if category:
        cursor.execute('SELECT * FROM products WHERE category = %s AND status = %s ORDER BY created_at DESC', 
                      (category, 'active'))
    else:
        cursor.execute('SELECT * FROM products WHERE status = %s ORDER BY created_at DESC', ('active',))
    
    products = cursor.fetchall()
    
    # Get all categories
    cursor.execute('SELECT DISTINCT category FROM products WHERE status = %s ORDER BY category', ('active',))
    categories = [row['category'] for row in cursor.fetchall()]
    
    conn.close()
    return render_template('home.html', products=products, categories=categories, current_category=category)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page with recommendations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get product
    cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cursor.fetchone()
    
    if not product:
        flash('Product not found', 'error')
        conn.close()
        return redirect(url_for('home'))
    
    # Update view count
    cursor.execute('UPDATE products SET views = views + 1 WHERE id = %s', (product_id,))
    
    # Log product view
    session_id = session.get('session_id', str(uuid.uuid4()))
    session['session_id'] = session_id
    cursor.execute('INSERT INTO product_views (product_id, session_id, ip_address) VALUES (%s, %s, %s)',
                  (product_id, session_id, request.remote_addr))
    
    # Get recommendations
    cursor.execute('''
        SELECT p.* FROM products p
        INNER JOIN product_recommendations pr ON p.id = pr.recommended_product_id
        WHERE pr.product_id = %s AND p.status = %s
        ORDER BY pr.score DESC
        LIMIT 4
    ''', (product_id, 'active'))
    recommendations = cursor.fetchall()
    
    conn.commit()
    conn.close()
    
    return render_template('product.html', product=product, recommendations=recommendations)

@app.route('/cart')
def view_cart():
    """View shopping cart"""
    cart = session.get('cart', {})
    cart_items = []
    total = Decimal('0.00')
    
    if cart:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for product_id, quantity in cart.items():
            cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
            product = cursor.fetchone()
            if product and product['status'] == 'active':
                item_total = Decimal(str(product['price'])) * quantity
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'item_total': item_total
                })
                total += item_total
        
        conn.close()
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart"""
    quantity = int(request.form.get('quantity', 1))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = %s AND status = %s', (product_id, 'active'))
    product = cursor.fetchone()
    conn.close()
    
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('home'))
    
    if product['stock'] < quantity:
        flash(f'Only {product["stock"]} items available', 'error')
        return redirect(url_for('product_detail', product_id=product_id))
    
    cart = session.get('cart', {})
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        new_quantity = cart[product_id_str] + quantity
        if product['stock'] < new_quantity:
            flash(f'Cannot add more. Only {product["stock"]} items available', 'error')
            return redirect(url_for('product_detail', product_id=product_id))
        cart[product_id_str] = new_quantity
    else:
        cart[product_id_str] = quantity
    
    session['cart'] = cart
    flash(f'{product["name"]} added to cart!', 'success')
    
    return redirect(url_for('view_cart'))

@app.route('/update-cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    """Update quantity in cart"""
    quantity = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    product_id_str = str(product_id)
    
    if quantity > 0:
        cart[product_id_str] = quantity
    else:
        cart.pop(product_id_str, None)
    
    session['cart'] = cart
    flash('Cart updated', 'success')
    return redirect(url_for('view_cart'))

@app.route('/remove-from-cart/<int:product_id>')
def remove_from_cart(product_id):
    """Remove item from cart"""
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    flash('Item removed from cart', 'success')
    return redirect(url_for('view_cart'))

@app.route('/checkout')
def checkout():
    """Checkout page"""
    cart = session.get('cart', {})
    
    if not cart:
        flash('Your cart is empty', 'error')
        return redirect(url_for('home'))
    
    cart_items = []
    total = Decimal('0.00')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for product_id, quantity in cart.items():
        cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
        product = cursor.fetchone()
        if product:
            item_total = Decimal(str(product['price'])) * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'item_total': item_total
            })
            total += item_total
    
    conn.close()
    
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/place-order', methods=['POST'])
def place_order():
    """Place order"""
    cart = session.get('cart', {})
    
    if not cart:
        flash('Your cart is empty', 'error')
        return redirect(url_for('home'))
    
    customer_name = request.form.get('customer_name')
    customer_email = request.form.get('customer_email')
    customer_phone = request.form.get('customer_phone')
    shipping_address = request.form.get('shipping_address', '')
    
    if not all([customer_name, customer_email, customer_phone]):
        flash('Please fill all required fields', 'error')
        return redirect(url_for('checkout'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    total = Decimal('0.00')
    order_items = []
    
    # Validate stock and calculate total
    for product_id, quantity in cart.items():
        cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
        product = cursor.fetchone()
        if product and product['stock'] >= quantity:
            item_total = Decimal(str(product['price'])) * quantity
            total += item_total
            order_items.append({
                'product_id': product_id,
                'product_name': product['name'],
                'quantity': quantity,
                'price': product['price'],
                'subtotal': item_total
            })
    
    if not order_items:
        flash('Unable to process order. Please check product availability.', 'error')
        conn.close()
        return redirect(url_for('view_cart'))
    
    # Create order
    order_number = generate_order_number()
    cursor.execute('''
        INSERT INTO orders 
        (order_number, customer_name, customer_email, customer_phone, total_amount, 
         status, payment_status, shipping_address)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (order_number, customer_name, customer_email, customer_phone, total, 
          'confirmed', 'paid', shipping_address))
    
    order_id = cursor.lastrowid
    
    # Create order items and update stock
    for item in order_items:
        cursor.execute('''
            INSERT INTO order_items 
            (order_id, product_id, product_name, quantity, price, subtotal)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (order_id, item['product_id'], item['product_name'], item['quantity'], 
              item['price'], item['subtotal']))
        
        # Update inventory
        update_inventory(item['product_id'], -item['quantity'], 'sale', 'order', order_id, 
                        f"Order {order_number}")
        
        # Update purchase count
        cursor.execute('UPDATE products SET purchases = purchases + %s WHERE id = %s',
                      (item['quantity'], item['product_id']))
    
    conn.commit()
    conn.close()
    
    # Clear cart
    session.pop('cart', None)
    
    flash(f'Order {order_number} placed successfully!', 'success')
    return redirect(url_for('order_confirmation', order_id=order_id))

@app.route('/order/<int:order_id>')
def order_confirmation(order_id):
    """Order confirmation page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
    order = cursor.fetchone()
    
    if not order:
        flash('Order not found', 'error')
        conn.close()
        return redirect(url_for('home'))
    
    cursor.execute('SELECT * FROM order_items WHERE order_id = %s', (order_id,))
    order_items = cursor.fetchall()
    
    conn.close()
    
    return render_template('order_confirmation.html', order=order, order_items=order_items)

# ============================================================================
# REST API ROUTES (For Mobile App)
# ============================================================================

@app.route('/api/products', methods=['GET'])
def api_products():
    """API: Get all active products"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    category = request.args.get('category')
    if category:
        cursor.execute('SELECT * FROM products WHERE category = %s AND status = %s ORDER BY created_at DESC', 
                      (category, 'active'))
    else:
        cursor.execute('SELECT * FROM products WHERE status = %s ORDER BY created_at DESC', ('active',))
    
    products = cursor.fetchall()
    conn.close()
    
    # Convert Decimal to float for JSON serialization
    for product in products:
        product['price'] = float(product['price'])
    
    return jsonify({'success': True, 'products': products})

@app.route('/api/product/<int:product_id>', methods=['GET'])
def api_product_detail(product_id):
    """API: Get product details with recommendations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cursor.fetchone()
    
    if not product:
        conn.close()
        return jsonify({'success': False, 'error': 'Product not found'}), 404
    
    product['price'] = float(product['price'])
    
    # Get recommendations
    cursor.execute('''
        SELECT p.* FROM products p
        INNER JOIN product_recommendations pr ON p.id = pr.recommended_product_id
        WHERE pr.product_id = %s AND p.status = %s
        ORDER BY pr.score DESC
        LIMIT 4
    ''', (product_id, 'active'))
    recommendations = cursor.fetchall()
    
    for rec in recommendations:
        rec['price'] = float(rec['price'])
    
    conn.close()
    
    return jsonify({'success': True, 'product': product, 'recommendations': recommendations})

@app.route('/api/categories', methods=['GET'])
def api_categories():
    """API: Get all product categories"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT category FROM products WHERE status = %s ORDER BY category', ('active',))
    categories = [row['category'] for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'success': True, 'categories': categories})

@app.route('/api/order', methods=['POST'])
def api_create_order():
    """API: Create new order"""
    data = request.get_json()
    
    if not data or not data.get('items'):
        return jsonify({'success': False, 'error': 'No items in order'}), 400
    
    customer_name = data.get('customer_name')
    customer_email = data.get('customer_email')
    customer_phone = data.get('customer_phone')
    shipping_address = data.get('shipping_address', '')
    items = data.get('items', [])
    
    if not all([customer_name, customer_email, customer_phone]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    total = Decimal('0.00')
    order_items = []
    
    # Validate stock and calculate total
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 1)
        
        cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
        product = cursor.fetchone()
        
        if not product or product['stock'] < quantity:
            conn.close()
            return jsonify({'success': False, 'error': f'Product {product_id} not available'}), 400
        
        item_total = Decimal(str(product['price'])) * quantity
        total += item_total
        order_items.append({
            'product_id': product_id,
            'product_name': product['name'],
            'quantity': quantity,
            'price': product['price'],
            'subtotal': item_total
        })
    
    # Create order
    order_number = generate_order_number()
    cursor.execute('''
        INSERT INTO orders 
        (order_number, customer_name, customer_email, customer_phone, total_amount, 
         status, payment_status, shipping_address)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (order_number, customer_name, customer_email, customer_phone, total, 
          'confirmed', 'paid', shipping_address))
    
    order_id = cursor.lastrowid
    
    # Create order items and update stock
    for item in order_items:
        cursor.execute('''
            INSERT INTO order_items 
            (order_id, product_id, product_name, quantity, price, subtotal)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (order_id, item['product_id'], item['product_name'], item['quantity'], 
              item['price'], item['subtotal']))
        
        update_inventory(item['product_id'], -item['quantity'], 'sale', 'order', order_id)
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True, 
        'order_id': order_id,
        'order_number': order_number,
        'total': float(total)
    })

# ============================================================================
# ADMIN PANEL ROUTES
# ============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admin_users WHERE username = %s AND is_active = TRUE', (username,))
        admin = cursor.fetchone()
        
        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            session['admin_role'] = admin['role']
            
            # Update last login
            cursor.execute('UPDATE admin_users SET last_login = NOW() WHERE id = %s', (admin['id'],))
            conn.commit()
            conn.close()
            
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
            conn.close()
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    session.pop('admin_role', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get statistics
    cursor.execute('SELECT COUNT(*) as count FROM products WHERE status = %s', ('active',))
    total_products = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM products WHERE stock <= low_stock_threshold AND status = %s', ('active',))
    low_stock_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM orders WHERE status != %s', ('cancelled',))
    total_orders = cursor.fetchone()['count']
    
    cursor.execute('SELECT SUM(total_amount) as revenue FROM orders WHERE payment_status = %s', ('paid',))
    total_revenue = cursor.fetchone()['revenue'] or 0
    
    # Recent orders
    cursor.execute('SELECT * FROM orders ORDER BY created_at DESC LIMIT 10')
    recent_orders = cursor.fetchall()
    
    # Low stock products
    cursor.execute('SELECT * FROM products WHERE stock <= low_stock_threshold AND status = %s ORDER BY stock ASC LIMIT 10', ('active',))
    low_stock_products = cursor.fetchall()
    
    conn.close()
    
    stats = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'total_orders': total_orders,
        'total_revenue': float(total_revenue)
    }
    
    return render_template('admin/dashboard.html', stats=stats, 
                         recent_orders=recent_orders, low_stock_products=low_stock_products)

@app.route('/admin/products')
@admin_required
def admin_products():
    """Admin products list"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products ORDER BY created_at DESC')
    products = cursor.fetchall()
    conn.close()
    
    return render_template('admin/products.html', products=products)

@app.route('/admin/product/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    """Add new product"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        stock = request.form.get('stock')
        category = request.form.get('category')
        low_stock_threshold = request.form.get('low_stock_threshold', 10)
        
        # Handle image upload
        image_url = 'https://via.placeholder.com/400x400?text=Product'
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                
                if USE_S3:
                    image_url = upload_to_s3(file, filename) or image_url
                else:
                    image_url = save_file_locally(file, filename)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (name, description, price, stock, category, image_url, low_stock_threshold, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (name, description, price, stock, category, image_url, low_stock_threshold, 'active'))
        
        product_id = cursor.lastrowid
        
        # Log inventory
        update_inventory(product_id, int(stock), 'stock_in', notes='Initial stock')
        
        conn.commit()
        conn.close()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/product_form.html', product=None)

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    """Edit product"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        stock = request.form.get('stock')
        category = request.form.get('category')
        low_stock_threshold = request.form.get('low_stock_threshold')
        status = request.form.get('status')
        
        # Get current product
        cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
        current_product = cursor.fetchone()
        
        image_url = current_product['image_url']
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                
                if USE_S3:
                    new_url = upload_to_s3(file, filename)
                    if new_url:
                        image_url = new_url
                else:
                    image_url = save_file_locally(file, filename)
        
        # Update product
        cursor.execute('''
            UPDATE products 
            SET name = %s, description = %s, price = %s, stock = %s, category = %s, 
                image_url = %s, low_stock_threshold = %s, status = %s
            WHERE id = %s
        ''', (name, description, price, stock, category, image_url, low_stock_threshold, status, product_id))
        
        # Log stock change if different
        stock_change = int(stock) - current_product['stock']
        if stock_change != 0:
            change_type = 'stock_in' if stock_change > 0 else 'stock_out'
            update_inventory(product_id, stock_change, 'adjustment', notes='Manual adjustment')
        
        conn.commit()
        conn.close()
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cursor.fetchone()
    conn.close()
    
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/product_form.html', product=product)

@app.route('/admin/orders')
@admin_required
def admin_orders():
    """Admin orders list"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders ORDER BY created_at DESC')
    orders = cursor.fetchall()
    conn.close()
    
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/order/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    """Admin order detail"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
    order = cursor.fetchone()
    
    if not order:
        flash('Order not found', 'error')
        conn.close()
        return redirect(url_for('admin_orders'))
    
    cursor.execute('SELECT * FROM order_items WHERE order_id = %s', (order_id,))
    order_items = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin/order_detail.html', order=order, order_items=order_items)

@app.route('/admin/inventory')
@admin_required
def admin_inventory():
    """Admin inventory log"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT il.*, p.name as product_name, au.username as admin_username
        FROM inventory_log il
        LEFT JOIN products p ON il.product_id = p.id
        LEFT JOIN admin_users au ON il.created_by = au.id
        ORDER BY il.created_at DESC
        LIMIT 100
    ''')
    logs = cursor.fetchall()
    conn.close()
    
    return render_template('admin/inventory.html', logs=logs)

# ============================================================================
# UTILITY ROUTES
# ============================================================================

@app.route('/health')
def health_check():
    """Health check endpoint for load balancer"""
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# ============================================================================
# TEMPLATE FILTERS
# ============================================================================

@app.template_filter('currency')
def currency_filter(value):
    """Format currency for Indian Rupees"""
    return f"₹{value:,.2f}"

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
