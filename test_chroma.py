import os
from dotenv import load_dotenv
import chromadb

# Load environment variables
load_dotenv()

tenant = os.getenv("CHROMA_TENANT")
database = os.getenv("CHROMA_DATABASE", "default")
api_key = os.getenv("CHROMA_API_KEY")

print("--- Environment Check ---")
print(f"CHROMA_TENANT: {tenant}")
print(f"CHROMA_DATABASE: {database}")
print(f"CHROMA_API_KEY Loaded: {bool(api_key)}")
print("-------------------------\n")

print("Attempting to connect via native CloudClient...")
try:
    # Initialize using the dedicated Cloud wrapper
    client = chromadb.CloudClient(
        cloud_host="europe-west1.gcp.trychroma.com",
        cloud_port=443,
        tenant=tenant,
        database=database,
        api_key=api_key,
    )

    # Trigger identity handshake
    identity = client.get_user_identity()
    print("🎉 Connection Successful!")
    print(f"Authenticated User Identity: {identity}")

except Exception as e:
    print("\n❌ Connection failed.")
    print(f"Error Details: {str(e)}")
