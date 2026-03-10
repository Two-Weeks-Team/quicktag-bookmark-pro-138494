from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from routes import router

app = FastAPI()

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def root():
    html = """
    <html>
    <head>
        <title>QuickTag Bookmark Pro</title>
        <style>
            body { background-color: #111; color: #eee; font-family: Arial, Helvetica, sans-serif; padding: 2rem; }
            a { color: #4ea1ff; }
            h1 { color: #4ea1ff; }
            .endpoint { margin-bottom: 1rem; }
            .stack { margin-top: 2rem; font-size: 0.9rem; color: #bbb; }
        </style>
    </head>
    <body>
        <h1>QuickTag Bookmark Pro</h1>
        <p>Fast, private, AI‑enhanced bookmarking – zero‑login optional, encrypted cloud sync when you need it.</p>
        <h2>Available API Endpoints</h2>
        <div class="endpoint"><strong>GET</strong> <code>/health</code> – health check</div>
        <div class="endpoint"><strong>POST</strong> <code>/api/bookmarks</code> – add bookmark with AI summary/tags</div>
        <div class="endpoint"><strong>GET</strong> <code>/api/bookmarks</code> – list bookmarks (optional filters)</div>
        <div class="endpoint"><strong>POST</strong> <code>/api/ai/summarize</code> – generate AI summary for a URL</div>
        <div class="endpoint"><strong>POST</strong> <code>/api/ai/suggest-tags</code> – AI tag suggestions</div>
        <div class="endpoint"><strong>POST</strong> <code>/api/sync/token</code> – create encrypted sync token</div>
        <div class="endpoint"><strong>POST</strong> <code>/api/sync/apply</code> – apply sync token to retrieve data</div>
        <p>Documentation: <a href="/docs">/docs</a> | <a href="/redoc">/redoc</a></p>
        <div class="stack">
            <p>Tech Stack: FastAPI 0.115.0, PostgreSQL, DigitalOcean Serverless Inference (openai‑gpt‑oss‑120b), Python 3.12+</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)

app.include_router(router)
