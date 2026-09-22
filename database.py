import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smart_gate.db")

def get_connection():
    """Establish and return SQLite connection with dictionary-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables for registered vehicles and entry logs."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table for registered authorized vehicles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            plate_number TEXT PRIMARY KEY,
            owner_name TEXT NOT NULL,
            vehicle_type TEXT DEFAULT 'Car',
            status TEXT DEFAULT 'Active',
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table for entry logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT NOT NULL,
            owner_name TEXT DEFAULT 'Unknown',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            access_status TEXT NOT NULL,
            vehicle_status TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def normalize_plate(plate_number):
    """Clean plate number string for consistent database searching."""
    if not plate_number:
        return ""
    return "".join(c for c in str(plate_number).upper() if c.isalnum())

def is_plate_registered(plate_number):
    """
    Check if a number plate is registered.
    Returns: tuple (is_registered: bool, owner_name: str)
    """
    clean_plate = normalize_plate(plate_number)
    if not clean_plate:
        return False, "Unknown"
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check exact clean match or partial normalized match
    cursor.execute("SELECT plate_number, owner_name, status FROM vehicles")
    rows = cursor.fetchall()
    conn.close()
    
    for row in rows:
        reg_clean = normalize_plate(row['plate_number'])
        if reg_clean == clean_plate or (len(clean_plate) >= 4 and clean_plate in reg_clean):
            if row['status'].upper() == 'ACTIVE':
                return True, row['owner_name']
                
    return False, "Unknown"

def add_vehicle(plate_number, owner_name, vehicle_type="Car"):
    """Register a new vehicle in the database."""
    clean_plate = normalize_plate(plate_number)
    if not clean_plate:
        return False, "Invalid plate number format"
        
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO vehicles (plate_number, owner_name, vehicle_type) VALUES (?, ?, ?)",
            (clean_plate, owner_name, vehicle_type)
        )
        conn.commit()
        conn.close()
        return True, f"Vehicle {clean_plate} registered successfully."
    except Exception as e:
        conn.close()
        return False, f"Database error: {str(e)}"

def delete_vehicle(plate_number):
    """Remove a vehicle from the registered database."""
    clean_plate = normalize_plate(plate_number)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vehicles WHERE plate_number = ?", (clean_plate,))
    conn.commit()
    conn.close()
    return True

def get_all_vehicles():
    """Retrieve all registered vehicles."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT plate_number, owner_name, vehicle_type, status, registered_at FROM vehicles ORDER BY registered_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def log_access(plate_number, access_status, vehicle_status, owner_name="Unknown"):
    """Log an access attempt event."""
    clean_plate = normalize_plate(plate_number)
    if not clean_plate:
        clean_plate = "NO_PLATE"
        
    conn = get_connection()
    cursor = conn.cursor()
    
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO logs (plate_number, owner_name, timestamp, access_status, vehicle_status) VALUES (?, ?, ?, ?, ?)",
        (clean_plate, owner_name, timestamp_str, access_status, vehicle_status)
    )
    conn.commit()
    conn.close()

def get_recent_logs(limit=25):
    """Fetch recent access logs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, plate_number, owner_name, timestamp, access_status, vehicle_status FROM logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

if __name__ == "__main__":
    init_db()
