import os
import sqlite3
import urllib.request
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database import get_db_connection, init_db

# Serve the static frontend (index.html, style.css, app.js) from this folder
app = Flask(__name__, static_folder=os.path.dirname(__file__), static_url_path='')
# Enable CORS for frontend integration (allows API access when the HTML is
# opened as file:// or served from a different origin during development)
CORS(app)

# Ensure the SQLite schema + seed data exist before the first request.
init_db()

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')
# Helper to serialize sqlite3.Row to dict
def row_to_dict(row):
    return dict(row) if row else None
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    user_id = data.get('userId')
    name = data.get('name', '').strip()
    password = data.get('password', '')
    role = data.get('role', '').strip()
    
    if not user_id or not name or not password or not role:
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400
        
    try:
        user_id_int = int(user_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'User ID must be a number.'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM User 
        WHERE UserID = ? AND Name = ? AND Password = ? AND Role = ?
    ''', (user_id_int, name, password, role))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({
            'success': True,
            'user': {
                'userId': user['UserID'],
                'name': user['Name'],
                'role': user['Role']
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials or role.'}), 401
# ==========================================
# PRODUCT CRUD
# ==========================================
@app.route('/api/products', methods=['GET'])
def get_products():
    q = request.args.get('q', '').strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    if q:
        cursor.execute('''
            SELECT * FROM Product 
            WHERE Name LIKE ? OR Description LIKE ?
        ''', (f'%{q}%', f'%{q}%'))
    else:
        cursor.execute('SELECT * FROM Product')
    products = [row_to_dict(p) for p in cursor.fetchall()]
    conn.close()
    return jsonify(products)
@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    price = data.get('price')
    stock_qty = data.get('stockQty')
    
    if not name or price is None or stock_qty is None:
        return jsonify({'message': 'Product name, price, and quantity are required.'}), 400
        
    try:
        price_val = float(price)
        qty_val = int(stock_qty)
        if price_val < 0 or qty_val < 0:
            raise ValueError()
    except ValueError:
        return jsonify({'message': 'Price and Stock Quantity must be non-negative numbers.'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Product (Name, Description, Price, StockQty)
        VALUES (?, ?, ?, ?)
    ''', (name, description, price_val, qty_val))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    
    return jsonify({
        'message': 'Product added successfully.',
        'productId': new_id
    }), 201
@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.json or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    price = data.get('price')
    stock_qty = data.get('stockQty')
    
    if not name or price is None or stock_qty is None:
        return jsonify({'message': 'Product name, price, and quantity are required.'}), 400
        
    try:
        price_val = float(price)
        qty_val = int(stock_qty)
        if price_val < 0 or qty_val < 0:
            raise ValueError()
    except ValueError:
        return jsonify({'message': 'Price and Stock Quantity must be non-negative numbers.'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute('SELECT 1 FROM Product WHERE ProductID = ?', (product_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'message': 'Product not found.'}), 404
        
    cursor.execute('''
        UPDATE Product 
        SET Name = ?, Description = ?, Price = ?, StockQty = ?
        WHERE ProductID = ?
    ''', (name, description, price_val, qty_val, product_id))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Product updated successfully.'})
@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute('SELECT 1 FROM Product WHERE ProductID = ?', (product_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'message': 'Product not found.'}), 404
        
    cursor.execute('DELETE FROM Product WHERE ProductID = ?', (product_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product deleted successfully.'})
# ==========================================
# CUSTOMER SERVICE
# ==========================================
@app.route('/api/customers', methods=['GET'])
def get_customers():
    phone = request.args.get('phone', '').strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    if phone:
        cursor.execute('''
            SELECT CustomerID AS id, Name AS name, PhoneNumber AS phoneNumber, LoyaltyPoints AS loyaltyPoints
            FROM Customerservice
            WHERE PhoneNumber LIKE ?
        ''', (f'{phone}%',))
    else:
        cursor.execute('''
            SELECT CustomerID AS id, Name AS name, PhoneNumber AS phoneNumber, LoyaltyPoints AS loyaltyPoints
            FROM Customerservice
        ''')
    customers = [row_to_dict(c) for c in cursor.fetchall()]
    conn.close()
    return jsonify(customers)
@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.json or {}
    name = data.get('name', '').strip()
    phone = data.get('phoneNumber', '').strip()
    points = data.get('loyaltyPoints', 0)
    
    if not name or not phone:
        return jsonify({'message': 'Customer name and phone number are required.'}), 400
        
    try:
        points_val = int(points)
    except ValueError:
        return jsonify({'message': 'Loyalty points must be an integer.'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO Customerservice (Name, PhoneNumber, LoyaltyPoints)
            VALUES (?, ?, ?)
        ''', (name, phone, points_val))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return jsonify({
            'message': 'Customer added successfully.',
            'customerId': new_id
        }), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'message': 'A customer with this phone number already exists.'}), 409
@app.route('/api/customers/<string:phone>', methods=['DELETE'])
def delete_customer(phone):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT 1 FROM Customerservice WHERE PhoneNumber = ?', (phone,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'message': 'Customer not found.'}), 404
        
    cursor.execute('DELETE FROM Customerservice WHERE PhoneNumber = ?', (phone,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Customer deleted successfully.'})
# ==========================================
# ORDERS AND TRANSACTIONS (CHECKOUT)
# ==========================================
@app.route('/api/orders', methods=['POST'])
def checkout():
    data = request.json or {}
    user_id = data.get('userId')
    customer_id = data.get('customerId') # optional
    cart_items = data.get('cartItems', [])
    
    if not user_id or not cart_items:
        return jsonify({'message': 'Cashier User ID and cart items are required.'}), 400
        
    try:
        user_id_int = int(user_id)
        cust_id_val = int(customer_id) if customer_id else None
    except ValueError:
        return jsonify({'message': 'Invalid IDs.'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Calculate total and validate stock inside transaction
        conn.execute('BEGIN')
        
        total_amount = 0
        validated_items = []
        
        for item in cart_items:
            product_id = item.get('productId')
            quantity = item.get('quantity')
            
            if not product_id or not quantity or quantity <= 0:
                raise ValueError("Invalid item format in cart.")
                
            cursor.execute('SELECT Name, Price, StockQty FROM Product WHERE ProductID = ?', (product_id,))
            prod = cursor.fetchone()
            if not prod:
                raise ValueError(f"Product ID {product_id} not found.")
                
            if prod['StockQty'] < quantity:
                raise ValueError(f"Insufficient stock for {prod['Name']}. Available: {prod['StockQty']}, Requested: {quantity}")
                
            item_total = prod['Price'] * quantity
            total_amount += item_total
            validated_items.append({
                'productId': product_id,
                'quantity': quantity,
                'unitPrice': prod['Price'],
                'name': prod['Name']
            })
            
        # Create Order
        order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO Orders (UserID, CustomerID, TotalAmount, OrderDate)
            VALUES (?, ?, ?, ?)
        ''', (user_id_int, cust_id_val, total_amount, order_date))
        order_id = cursor.lastrowid
        
        # Add Order Items & Decrease Stock
        for vi in validated_items:
            cursor.execute('''
                INSERT INTO OrderItem (OrderID, ProductID, Quantity, UnitPrice)
                VALUES (?, ?, ?, ?)
            ''', (order_id, vi['productId'], vi['quantity'], vi['unitPrice']))
            
            cursor.execute('''
                UPDATE Product 
                SET StockQty = StockQty - ? 
                WHERE ProductID = ?
            ''', (vi['quantity'], vi['productId']))
            
        # If customer is linked, reward loyalty points (1 point per 100 PKR spent)
        if cust_id_val:
            points_earned = int(total_amount // 100)
            if points_earned > 0:
                cursor.execute('''
                    UPDATE Customerservice 
                    SET LoyaltyPoints = LoyaltyPoints + ? 
                    WHERE CustomerID = ?
                ''', (points_earned, cust_id_val))
                
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Order processed successfully.',
            'orderId': order_id,
            'totalAmount': total_amount,
            'orderDate': order_date
        }), 201
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'message': str(e)}), 400
# ==========================================
# REPORTING & SALES STATS (OWNER VIEW)
# ==========================================
@app.route('/api/sales/overview', methods=['GET'])
def get_sales_overview():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Total Sales Amount
    cursor.execute('SELECT SUM(TotalAmount) FROM Orders')
    total_sales = cursor.fetchone()[0] or 0.0
    
    # 2. Total Invoices Count
    cursor.execute('SELECT COUNT(*) FROM Orders')
    total_invoices = cursor.fetchone()[0] or 0
    
    # 3. Total Customer Count
    cursor.execute('SELECT COUNT(*) FROM Customerservice')
    total_customers = cursor.fetchone()[0] or 0
    
    conn.close()
    return jsonify({
        'totalSales': total_sales,
        'totalInvoices': total_invoices,
        'totalCustomers': total_customers
    })
@app.route('/api/sales/recent', methods=['GET'])
def get_recent_sales():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Joins Order with User table to fetch cashier name
    cursor.execute('''
        SELECT 
            o.OrderID AS invoiceId,
            u.Name AS cashierName,
            o.OrderDate AS date,
            o.TotalAmount AS totalAmount
        FROM Orders o
        JOIN User u ON o.UserID = u.UserID
        ORDER BY o.OrderDate DESC
        LIMIT 10
    ''')
    recent_sales = [row_to_dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(recent_sales)
@app.route('/api/sales/invoice/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get Order details
    cursor.execute('''
        SELECT 
            o.OrderID AS invoiceId,
            o.TotalAmount AS totalAmount,
            o.OrderDate AS date,
            u.Name AS cashierName,
            u.UserID AS cashierId,
            c.Name AS customerName,
            c.PhoneNumber AS customerPhone
        FROM Orders o
        JOIN User u ON o.UserID = u.UserID
        LEFT JOIN Customerservice c ON o.CustomerID = c.CustomerID
        WHERE o.OrderID = ?
    ''', (invoice_id,))
    
    order = cursor.fetchone()
    if not order:
        conn.close()
        return jsonify({'message': 'Invoice not found.'}), 404
        
    # Get Items in Order
    cursor.execute('''
        SELECT 
            oi.ProductID AS productId,
            p.Name AS name,
            oi.Quantity AS quantity,
            oi.UnitPrice AS unitPrice,
            (oi.Quantity * oi.UnitPrice) AS subtotal
        FROM OrderItem oi
        JOIN Product p ON oi.ProductID = p.ProductID
        WHERE oi.OrderID = ?
    ''', (invoice_id,))
    
    items = [row_to_dict(item) for item in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        'invoice': row_to_dict(order),
        'items': items
    })
# ==========================================
# CURRENCY EXCHANGE API PROXY
# ==========================================
@app.route('/api/exchange-rate', methods=['GET'])
def get_exchange_rate():
    # Attempt to fetch real exchange rates from open.er-api.com
    # Fallback to hardcoded mock exchange rates if offline or API is down.
    # Base is PKR (Pakistani Rupee)
    
    default_rates = {
        "USD": 0.0036,  # 1 PKR = 0.0036 USD
        "EUR": 0.0033,  # 1 PKR = 0.0033 EUR
        "GBP": 0.0028,  # 1 PKR = 0.0028 GBP
        "SAR": 0.0135,  # 1 PKR = 0.0135 SAR
        "AED": 0.0132   # 1 PKR = 0.0132 AED
    }
    
    try:
        req = urllib.request.Request(
            'https://open.er-api.com/v6/latest/PKR',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            if data and data.get('result') == 'success':
                rates = data.get('rates', {})
                # Filter only the currencies we want to display
                filtered_rates = {cur: rates[cur] for cur in default_rates.keys() if cur in rates}
                return jsonify({
                    'success': True,
                    'source': 'live',
                    'rates': filtered_rates
                })
    except Exception as e:
        pass # ignore exception and fallback to hardcoded rates
        
    return jsonify({
        'success': True,
        'source': 'fallback',
        'rates': default_rates
    })
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
