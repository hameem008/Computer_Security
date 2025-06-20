from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Fingerprint, CollectionStats
import json

# Connect to the database
engine = create_engine("sqlite:///webfingerprint.db")
Session = sessionmaker(bind=engine)
session = Session()

# Query all fingerprints
fingerprints = session.query(Fingerprint).all()
print("All Fingerprints:")
for fp in fingerprints:
    trace_data = json.loads(fp.trace_data)  # Load trace data
    trace_size = len(trace_data)  # Get size of trace data array
    trace_first_five = trace_data[:5]  # Get first five values
    print(f"ID: {fp.id}, Website: {fp.website}, Index: {fp.website_index}, Timestamp: {fp.timestamp}, Trace Size: {trace_size}, Trace (first 5): {trace_first_five}")

# Query collection stats
stats = session.query(CollectionStats).all()
print("\nCollection Stats:")
for stat in stats:
    print(f"Website: {stat.website}, Traces Collected: {stat.traces_collected}")

session.close()