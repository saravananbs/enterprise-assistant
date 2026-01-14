from fastapi import WebSocket, WebSocketDisconnect
from app.services.graph_service import run_graph_stream
from ..utils.serializers import serialize_message

async def chat_socket(websocket: WebSocket):
    await websocket.accept()

    try:
        init = await websocket.receive_json()
        user_id = init["user_id"]
        chat_id = init["chat_id"]

        while True:
            msg = await websocket.receive_json()
            user_input = msg["message"]

            async for event in run_graph_stream(
                user_id=user_id,
                chat_id=chat_id,
                user_message=user_input
            ):
                if "__interrupt__" in event:
                    await websocket.send_json({
                        "type": "interrupt",
                        "payload": event["__interrupt__"]
                    })
                    return
                if "messages" in event:
                    last_msg = event["messages"][-1]

                    await websocket.send_json({
                        "type": "token",
                        "message": serialize_message(last_msg)
                    })

            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        print("Client disconnected")
