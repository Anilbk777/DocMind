# connection_manager.py
from fastapi import WebSocket
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)

class WebSocketManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, batch_id: str, websocket: WebSocket):
        await websocket.accept()
        self._connections[batch_id] = websocket
        logger.info(f"WebSocket connected for batch: {batch_id}")

    def disconnect(self, batch_id: str):
        self._connections.pop(batch_id, None)
        logger.info(f"WebSocket disconnected for batch: {batch_id}")

    async def notify(self, batch_id: str, payload: dict, close: bool = False):
        """
        Send one message through the batch's connection.
        
        The 'close' flag tells us whether this is the final message —
        meaning all files in the batch have finished and we can clean up.
        If close=False, the connection stays open waiting for more messages.
        """
        websocket = self._connections.get(batch_id)
        if websocket is None:
            logger.info(f"No active WebSocket for batch {batch_id} — client disconnected.")
            return

        try:
            await websocket.send_json(payload)
            logger.info(f"Notified batch {batch_id}: {payload.get('status')} for job {payload.get('job_id')}")
        except Exception as e:
            logger.warning(f"Failed to notify batch {batch_id}: {e}")
        finally:
            # Only clean up the connection when explicitly told to close.
            # For intermediate notifications (files 1-4 of 5), we leave it open.
            if close:
                self.disconnect(batch_id)

websocket_manager = WebSocketManager()