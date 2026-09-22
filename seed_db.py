from database import init_db, add_vehicle, log_access, get_all_vehicles
from datetime import datetime, timedelta

def seed_database():
    """Seed sample registered vehicles and initial access logs."""
    init_db()
    
    sample_vehicles = [
        ("KA01AB1234", "Dr. Rajesh Kumar", "Sedan"),
        ("MH12DE5678", "Ananya Sharma", "SUV"),
        ("DL03XY9999", "Vikramaditya Singh", "Luxury Sedan"),
        ("TN07CZ4321", "Priya Sundaram", "Hatchback"),
        ("HR26DQ8888", "Amitabh Roy", "Electric Vehicle")
    ]
    
    print("Seeding registered vehicles...")
    for plate, owner, vtype in sample_vehicles:
        success, msg = add_vehicle(plate, owner, vtype)
        print(f" -> {msg}")
        
    print("\nSeeding historical access logs...")
    sample_logs = [
        ("KA01AB1234", "GATE OPEN", "REGISTERED", "Dr. Rajesh Kumar"),
        ("MH12DE5678", "GATE OPEN", "REGISTERED", "Ananya Sharma"),
        ("UP14AB0001", "GATE CLOSED", "UNKNOWN VEHICLE", "Unknown"),
        ("DL03XY9999", "GATE OPEN", "REGISTERED", "Vikramaditya Singh"),
        ("MH04XX7777", "GATE CLOSED", "UNKNOWN VEHICLE", "Unknown")
    ]
    
    for plate, access, vstat, owner in sample_logs:
        log_access(plate, access, vstat, owner)
        
    print(f"\nSeeding complete! Current registered count: {len(get_all_vehicles())}")

if __name__ == "__main__":
    seed_database()
