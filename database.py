import sqlite3
import os
from datetime import datetime, timedelta
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inventory.db')
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. User table (Authentication and roles)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS User (
        UserID INTEGER PRIMARY KEY,
        Name TEXT NOT NULL,
        Password TEXT NOT NULL,
        Role TEXT NOT NULL CHECK(Role IN ('admin', 'employee', 'owner'))
    );
    ''')
    
    # 2. Product table (Inventory details)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Product (
        ProductID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Description TEXT,
        Price REAL NOT NULL,
        StockQty INTEGER NOT NULL
    );
    ''')
    
    # 3. Customer table (Loyalty program)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Customerservice (
        CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        PhoneNumber TEXT UNIQUE NOT NULL,
        LoyaltyPoints INTEGER DEFAULT 0
    );
    ''')
    
    # 4. Orders table (Transactions header)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Orders (
        OrderID INTEGER PRIMARY KEY AUTOINCREMENT,
        UserID INTEGER NOT NULL,
        CustomerID INTEGER,
        TotalAmount REAL NOT NULL,
        OrderDate TEXT NOT NULL,
        FOREIGN KEY(UserID) REFERENCES User(UserID),
        FOREIGN KEY(CustomerID) REFERENCES Customerservice(CustomerID)
    );
    ''')
    
    # 5. OrderItem table (Transactions details - Composite PK)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS OrderItem (
        OrderID INTEGER NOT NULL,
        ProductID INTEGER NOT NULL,
        Quantity INTEGER NOT NULL,
        UnitPrice REAL NOT NULL,
        PRIMARY KEY (OrderID, ProductID),
        FOREIGN KEY(OrderID) REFERENCES Orders(OrderID) ON DELETE CASCADE,
        FOREIGN KEY(ProductID) REFERENCES Product(ProductID)
    );
    ''')
    
    conn.commit()
    seed_data(conn)
    conn.close()
def seed_data(conn):
    cursor = conn.cursor()
    
    # Seed Users
    users = [
        (1, 'Admin', 'admin123', 'admin'),
        (241462, 'Aruj', 'aruj123', 'employee'),
        (3, 'Owner', 'owner123', 'owner')
    ]
    cursor.executemany('''
    INSERT OR IGNORE INTO User (UserID, Name, Password, Role) 
    VALUES (?, ?, ?, ?);
    ''', users)
    
    # Seed Products
    # Prices stored in PKR (base/local currency).
    products = [
        (1, 'Premium Notebook', 'A5 spiral bound, 120 pages, rule-lined', 250.00, 45),
        (2, 'Luxury Gel Pens', 'Pack of 5, fine-point black gel ink', 350.00, 95),
        (3, 'Wrapping Paper', 'Floral pattern wrapping sheet (large)', 60.00, 150),
        (4, 'Gift Box Set', 'Decorative cardboard gift boxes, set of 3', 850.00, 20),
        (5, 'Art Sketchbook', 'A4 drawing pad, 150gsm cartridge paper', 650.00, 15),
        (6, 'Pencil Case', 'Zippered canvas pencil case, blue color', 180.00, 60),
        (7, 'Fountain Pen', 'Classic metal fountain pen with ink converter', 1200.00, 10),
        (8, 'Sticky Notes Pack', '4 pastel colors, 100 sheets each', 140.00, 120)
    ]
    
    # Use REPLACE or IGNORE depending on whether we want to reset. 
    # For out-of-the-box experience, insert only if table is empty.
    cursor.execute("SELECT COUNT(*) FROM Product")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
        INSERT INTO Product (ProductID, Name, Description, Price, StockQty) 
        VALUES (?, ?, ?, ?, ?);
        ''', products)
        
    # Seed Customers
    customers = [
        (1, 'Mohammad Ali', '03001234567', 15),
        (2, 'Zainab Fatima', '03219876543', 45),
        (3, 'Bilal Khan', '03335552211', 5)
    ]
    cursor.execute("SELECT COUNT(*) FROM Customerservice")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
        INSERT INTO Customerservice (CustomerID, Name, PhoneNumber, LoyaltyPoints) 
        VALUES (?, ?, ?, ?);
        ''', customers)
        
    # Seed Orders
    cursor.execute("SELECT COUNT(*) FROM Orders")
    if cursor.fetchone()[0] == 0:
        # Create some historical orders (dated in the past)
        # Order 1: Zainab bought a Fountain Pen and Premium Notebook (PKR)
        order_date_1 = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO Orders (OrderID, UserID, CustomerID, TotalAmount, OrderDate)
        VALUES (1001, 241462, 2, 1450.00, ?);
        ''', (order_date_1,))
        cursor.execute('''
        INSERT INTO OrderItem (OrderID, ProductID, Quantity, UnitPrice)
        VALUES (1001, 7, 1, 1200.00);
        ''', )
        cursor.execute('''
        INSERT INTO OrderItem (OrderID, ProductID, Quantity, UnitPrice)
        VALUES (1001, 1, 1, 250.00);
        ''')
        
        # Order 2: Bilal bought notebook and sticky notes (PKR)
        order_date_2 = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO Orders (OrderID, UserID, CustomerID, TotalAmount, OrderDate)
        VALUES (1002, 241462, 3, 530.00, ?);
        ''', (order_date_2,))
        cursor.execute('''
        INSERT INTO OrderItem (OrderID, ProductID, Quantity, UnitPrice)
        VALUES (1002, 1, 1, 250.00);
        ''')
        cursor.execute('''
        INSERT INTO OrderItem (OrderID, ProductID, Quantity, UnitPrice)
        VALUES (1002, 8, 2, 140.00);
        ''')
        
    conn.commit()
if __name__ == '__main__':
    # When run directly, initialize database
    init_db()
    print("Database initialized successfully at:", DB_PATH)
