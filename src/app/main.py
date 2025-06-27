from fastapi import FastAPI
from src.app.api import router       

app = FastAPI(title="EPR-RAG MVP")
app.include_router(router)

# This block is only used if you ever run “python src/app/main.py”
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=True)
