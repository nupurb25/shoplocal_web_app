# ShopLocal Enhanced - Web Application

Complete e-commerce platform supporting web app, mobile app, and admin panel.

## 🚀 Features

### Customer-Facing (Web App)
- **Product Browsing**: Category-based filtering, search
- **Product Details**: High-quality images, descriptions, recommendations
- **Shopping Cart**: Session-based cart management
- **Checkout**: Simple order placement
- **Order Tracking**: Confirmation pages with order details

### Admin Panel
- **Dashboard**: Sales statistics, recent orders, low stock alerts
- **Product Management**: Add, edit, delete products with image upload
- **Order Management**: View and track all orders
- **Inventory Log**: Complete audit trail of stock changes
- **S3 Integration**: Upload product images to AWS S3 or local storage

### REST API
- **Mobile App Support**: Complete API for React Native app
- **Endpoints**: Products, categories, orders, product details
- **CORS Enabled**: Ready for mobile app integration

### Advanced Features
- **Recommendation Engine**: "You may also like" suggestions
- **Inventory Tracking**: Automatic stock updates, low stock alerts
- **Analytics**: Product views, purchase counts, revenue tracking
- **Image Management**: S3 upload or local storage fallback
- **Health Check**: `/health` endpoint for load balancer

## 📋 Prerequisites

- Python 3.9+
- MySQL 8.0+
- AWS Account (optional, for S3 images)

## 🛠️ Installation

### 1. Clone/Extract Files

```bash
cd shoplocal-master/web-app
```

### 2. Install Dependencies

```bash
pip3 install -r requirements.txt --break-system-packages
```

### 3. Set Up Database

```bash
mysql -u root -p < database_enhanced.sql
```

This creates:
- `shoplocal` database
- Products table with 30 sample products
- Admin users (default: admin/admin123)
- Orders, inventory, recommendations tables

### 4. Configure Environment

```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=your_mysql_password
export DB_NAME=shoplocal
export SECRET_KEY=$(openssl rand -hex 16)

# Optional: For S3 image uploads
export AWS_S3_BUCKET=your-bucket-name
export AWS_REGION=ap-south-1
```

### 5. Run Application

```bash
python3 app.py
```

Application runs on: `http://localhost:8080`

## 🌐 Accessing the Application

### Customer Website
- Homepage: http://localhost:8080
- Browse products, add to cart, checkout

### Admin Panel
- Login: http://localhost:8080/admin/login
- Default credentials: `admin` / `admin123`
- **⚠️ IMPORTANT**: Change default password after first login!

### API Endpoints
- Products: http://localhost:8080/api/products
- Categories: http://localhost:8080/api/categories
- Product Detail: http://localhost:8080/api/product/1
- Create Order: POST http://localhost:8080/api/order

## 📁 Project Structure

```
web-app/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── database_enhanced.sql           # Database schema + sample data
├── templates/
│   ├── base.html                   # Customer base template
│   ├── home.html                   # Product listing page
│   ├── product.html                # Product detail page
│   ├── cart.html                   # Shopping cart
│   ├── checkout.html               # Checkout page
│   ├── order_confirmation.html     # Order success page
│   ├── about.html                  # About page
│   ├── 404.html                    # Error pages
│   ├── 500.html
│   └── admin/
│       ├── base.html               # Admin base template
│       ├── login.html              # Admin login
│       ├── dashboard.html          # Admin dashboard
│       ├── products.html           # Product management
│       ├── product_form.html       # Add/Edit product
│       ├── orders.html             # Order list
│       ├── order_detail.html       # Order details
│       └── inventory.html          # Inventory log
└── static/
    └── uploads/                    # Local image storage (if not using S3)
```

## 🔑 Admin Panel Features

### Dashboard
- Total products, orders, revenue
- Low stock alerts
- Recent orders
- Quick actions

### Product Management
- Add new products with images
- Edit existing products
- Update stock levels
- Set low stock thresholds
- Track views and purchases

### Order Management
- View all orders
- Order status tracking
- Customer information
- Order items breakdown

### Inventory Log
- Complete audit trail
- Stock in/out transactions
- Manual adjustments
- Reference to orders

## 🖼️ Image Management

### Option 1: AWS S3 (Production)

```bash
# Set environment variables
export AWS_S3_BUCKET=shoplocal-images
export AWS_REGION=ap-south-1

# AWS credentials automatically picked up from:
# - EC2 instance role (recommended)
# - ~/.aws/credentials
# - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
```

**S3 Bucket Configuration:**
1. Create bucket: `shoplocal-images`
2. Enable public read access
3. Add bucket policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::shoplocal-images/products/*"
    }
  ]
}
```

### Option 2: Local Storage (Development)

If S3 is not configured, images are saved to `static/uploads/`

## 📱 REST API Documentation

### Get All Products
```bash
GET /api/products
GET /api/products?category=Clothing

Response:
{
  "success": true,
  "products": [
    {
      "id": 1,
      "name": "Product Name",
      "price": 1999.00,
      "stock": 50,
      "category": "Clothing",
      ...
    }
  ]
}
```

### Get Product Details
```bash
GET /api/product/1

Response:
{
  "success": true,
  "product": {...},
  "recommendations": [...]
}
```

### Create Order
```bash
POST /api/order
Content-Type: application/json

{
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "customer_phone": "9876543210",
  "shipping_address": "123 Main St",
  "items": [
    {
      "product_id": 1,
      "quantity": 2
    }
  ]
}

Response:
{
  "success": true,
  "order_id": 1,
  "order_number": "SL-20241209120000-ABC123",
  "total": 3998.00
}
```

## 🔒 Security Notes

1. **Change Default Password**: Admin password is `admin123` - change immediately
2. **Secret Key**: Use strong secret key in production
3. **Database Security**: Use strong MySQL password
4. **HTTPS**: Always use HTTPS in production
5. **S3 Permissions**: Restrict S3 write access to application only

## 🚀 Production Deployment

### EC2 Deployment Script

```bash
#!/bin/bash
# Run this script in EC2 user data

# Update system
yum update -y
yum install python3 python3-pip git mysql -y

# Clone/download application
cd /home/ec2-user
# [Extract shoplocal-master here]

cd shoplocal-master/web-app

# Install dependencies
pip3 install -r requirements.txt --break-system-packages

# Configure environment
export DB_HOST=your-rds-endpoint.rds.amazonaws.com
export DB_USER=admin
export DB_PASSWORD=your-rds-password
export DB_NAME=shoplocal
export SECRET_KEY=$(openssl rand -hex 16)
export AWS_S3_BUCKET=shoplocal-images
export AWS_REGION=ap-south-1

# Initialize database (run once)
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD < database_enhanced.sql

# Run application
nohup python3 app.py > /var/log/shoplocal.log 2>&1 &
```

### RDS Database Setup

1. Create RDS MySQL instance (db.t3.micro)
2. Security group: Allow 3306 from EC2 security group
3. Run `database_enhanced.sql` to initialize

### ALB Configuration

- Target: EC2 instances on port 8080
- Health check: `/health`
- HTTPS listener with ACM certificate

## 📊 Database Schema

### Products Table
- id, name, description, price, image_url
- stock, category, low_stock_threshold
- status (active/inactive/out_of_stock)
- views, purchases
- created_at, updated_at

### Admin Users Table
- id, username, password_hash, email
- role (admin/manager/staff)
- is_active, last_login

### Orders Table
- id, order_number, customer details
- total_amount, status, payment_status
- shipping_address, created_at

### Inventory Log Table
- Tracks all stock changes
- References orders and admin users
- Complete audit trail

### Product Recommendations Table
- Stores product recommendations
- Recommendation types: also_bought, similar, category, trending

## 🧪 Testing

### Test Customer Flow
1. Browse products: http://localhost:8080
2. Add items to cart
3. Checkout with test data
4. View order confirmation

### Test Admin Panel
1. Login: http://localhost:8080/admin/login
2. Add new product with image
3. Edit product stock
4. View orders
5. Check inventory log

### Test API
```bash
# Get products
curl http://localhost:8080/api/products

# Health check
curl http://localhost:8080/health
```

## 📝 Notes

- **Password Hash**: Default admin password uses werkzeug pbkdf2:sha256
- **Session Storage**: Flask sessions (cookie-based)
- **Image Formats**: JPG, PNG, GIF, WEBP (max 5MB)
- **Database**: UTF-8 encoding for proper Indian character support

## 🆘 Troubleshooting

### Database Connection Failed
```bash
# Check MySQL is running
systemctl status mysqld

# Verify credentials
mysql -u root -p
```

### S3 Upload Failed
```bash
# Check AWS credentials
aws s3 ls

# Verify bucket permissions
aws s3api get-bucket-policy --bucket shoplocal-images
```

### Port 8080 Already in Use
```bash
# Find process
lsof -i :8080

# Kill process
kill -9 <PID>
```

## 🎯 Next Steps

This is **Phase 1** of the master codebase. Next phases:
- **Phase 2**: React Native Mobile App (Expo)
- **Phase 3**: Advanced Features (recommendations, analytics)
- **Phase 4**: Week 2 Assignment Package

## 📧 Support

For AWS L2 training support:
- Instructor: Vish, Nixace Technologies
- Email: support@nixace.com

---

**Master Codebase Version**: 1.0  
**Created**: December 2024  
**Purpose**: AWS Cloud Engineering Training
