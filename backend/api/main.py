from fastapi import FastAPI
from backend.api.inferenceAPI import router as inference_router
from backend.api.getTableInfoAPI import router as table_info_router


app = FastAPI()

# Register the router
app.include_router(inference_router, prefix="/inference", tags=["Inference"])
app.include_router(table_info_router, prefix="/table", tags=["Table"])
