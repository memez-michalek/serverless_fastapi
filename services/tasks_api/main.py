from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from magnum import Magnum

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health_check/")
async def health_check():
    return {"status": "OK"}
 
handle = Magnum(app)