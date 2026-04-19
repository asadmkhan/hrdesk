def main() -> None:
    import uvicorn

    uvicorn.run(
        "hrdesk.web.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="warning",
    )
