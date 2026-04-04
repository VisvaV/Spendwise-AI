from .mongo import get_receipt_metadata_collection, get_activity_logs_collection, get_notifications_collection

def init_mongo_indexes():
    print("Initializing MongoDB Indexes...")
    
    receipts = get_receipt_metadata_collection()
    receipts.create_index("expense_id", unique=True)
    receipts.create_index("perceptual_hash")

    activities = get_activity_logs_collection()
    activities.create_index("actor_id")
    activities.create_index("entity_id")
    activities.create_index("timestamp")

    notifs = get_notifications_collection()
    notifs.create_index("user_id")
    notifs.create_index("expense_id")
    
    print("MongoDB indexes created successfully.")

if __name__ == "__main__":
    init_mongo_indexes()
