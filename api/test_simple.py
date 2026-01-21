import logging
from fastapi import FastAPI

# Simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create minimal FastAPI app
app = FastAPI(title="Simple Test API")

@app.get("/")
async def root():
    return {"message": "Hello World - API is running!"}

@app.get("/health")
async def health():
    logger.info("Health check called - returning OK")
    return {"status": "ok", "message": "Simple test API is healthy"}

@app.on_event("startup")
async def startup():
    logger.info("=== SIMPLE API STARTING ===")
    logger.info("No database, no encryption, no auth - just basic FastAPI")
    logger.info("=== SIMPLE API STARTED SUCCESSFULLY ===")

@app.on_event("shutdown") 
async def shutdown():
    logger.info("=== SIMPLE API SHUTTING DOWN ===")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting simple test server...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
