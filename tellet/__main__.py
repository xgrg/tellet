import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "tellet.main:app", host="0.0.0.0", port=8888, log_level="info", reload=True
    )
