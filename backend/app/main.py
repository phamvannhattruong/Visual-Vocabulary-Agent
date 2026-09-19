from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.app.api.routes import chat, learning
from backend.app.core.settings import ASSETS_DIR, TEMPLATES_DIR, UPLOAD_DIR

app = FastAPI(title="Visual Vocabulary Agent API")

app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Configure templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API routes
app.include_router(learning.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")

@app.get('/learn-image')
async def learn_image(request: Request):
    return templates.TemplateResponse(request=request, name="imagelearn.html")

@app.get('/chat-bot')
async def chat_bot(request: Request):
    return templates.TemplateResponse(request=request, name="chatbot.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
