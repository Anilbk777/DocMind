from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    print(websocket.client)

    try:
        while True:
            text = await websocket.receive_text()
            print(text)
            await websocket.send_text(f"Echo: {text}")
    except WebSocketDisconnect:
        # This is normal — the browser navigated away, closed the tab,
        # or the network dropped. Not an error, just cleanup.
        print("Client disconnected cleanly")
    except Exception as e:
        # This is an actual unexpected error
        print(f"Unexpected error: {e}")
