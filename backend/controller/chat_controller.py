from collections import defaultdict
from fastapi import APIRouter, Depends, WebSocket, Cookie, WebSocketDisconnect, WebSocketException
from fastapi.responses import HTMLResponse
import json
from dto.request.message.more_message_request import MoreMessageRequest
from dto.response.message.message_response import MessageResponse
from dto.response.success_response import SuccessResponse
from dto.response.user_response import UserResponse
from dto.response.websocket.websocket_response import WebSocketResponse
from enums.enum_message_type import E_Message_Type
from service.auth_service import AuthService
from service.message_service import MessageService
from service.user_room_service import UserRoomService
from service.user_service import UserService

chat_router = APIRouter()

auth_service = AuthService()
user_room_service = UserRoomService()
message_service = MessageService()
user_service = UserService()

map_user_connection = {}
map_room_user = defaultdict(set)


@chat_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, access_token=Cookie(...)):
    # Check token is correct or not
    try:
        current_user = auth_service.check_token(access_token)
    except:
        await websocket.close(code=4000)
        return

    # Connecting via WebSocket and add to the list of connected
    await websocket.accept()

    map_user_connection[current_user.user_id] = websocket
    await update_status(is_online = True, user_id = current_user.user_id)

    print("[INFO] map_user_connection: ", list(map_user_connection.keys()))

    list_room_of_current_user = user_room_service.get_all_room_of_user(current_user.user_id)

    for room_id_of_user in list_room_of_current_user:
        map_room_user[room_id_of_user].add(current_user.user_id)

    try:
        while True:
            data = await websocket.receive_text()

            data_json = json.loads(data)
            action = data_json.get("action", None)
            if action == "chat":
                await chat(data_json, current_user)
            elif action == "join":
                join(data_json, current_user)
            elif action == "leave":
                leave(data_json, current_user)
            elif action == "make-request-friend":
                await make_request_friend(data_json, current_user)
            elif action == "change-contact":
                await relay_message(data_json)
            elif action == "remove":
                await remove(data_json)
            elif action == "delete-room":
                await delete_room(data_json)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        map_user_connection.pop(current_user.user_id, None)
        await update_status(is_online = False, user_id = current_user.user_id)


async def broadcast_message(room_id: str, message: str):
    connections = []
    for user_id in map_room_user[room_id]:
        if user_id in map_user_connection:
            connections.append(map_user_connection[user_id])
    for connection in connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            print(f"Error sending message: {e}")

async def boardcast(message: str):
    list_user_id = list(map_user_connection.keys()) # fix: RuntimeError: dictionary changed size during iteration
    for user_id in list_user_id:
        try:
            await map_user_connection[user_id].send_text(message)
        except Exception as e:
            print(f"Error sending message: {e}")

@chat_router.get("")
async def get_all_mess_in_room(room_id: str):
    return SuccessResponse(result=message_service.get_all_mess_in_room(room_id))


@chat_router.post("/more")
async def get_more_mess_in_room(request: MoreMessageRequest):
    return SuccessResponse(result=message_service.get_more_mess_in_room(
        room_id=request.room_id,
        created_at=request.created_at,
        limit=request.limit
    ))

@chat_router.get("/online-user")
async def get_online_user_ids():
    return SuccessResponse(result= list(map_user_connection.keys()))

async def chat(data_json, current_user):
    data = data_json["data"]
    room_id = data.get("room_id")
    content = data.get("content", None)
    message_type = data.get("message_type", 0)
    file_url = data.get("file_url", None)

    if isinstance(content, str) and content.strip() == "":
        return

    if current_user.user_id not in map_room_user[room_id]:
        print(f"User {current_user.user_id} is not in {room_id}, skipped message")
        return

        # Save message
    mess_db = message_service.save(
        sender_id=current_user.user_id,
        room_id=room_id,
        message_type=E_Message_Type.fromNumber(message_type),
        content=content,
        file_url=file_url
    )

    mess_response = MessageResponse(
        id=mess_db.id,
        room_id=mess_db.room_id,
        message_type=mess_db.message_type,
        content=mess_db.content,
        file_url=mess_db.file_url,
        created_at=mess_db.created_at,
        updated_at=mess_db.updated_at,
        sender=UserResponse.fromUserModel(current_user)
    )
    res = WebSocketResponse(
        action=data_json["action"],
        data=mess_response
    )
    res_json = res.json()
    print("res_json: ", res_json)
    await broadcast_message(room_id, res_json)


def join(data_json, current_user):
    """
    data_json: {
        action: "join",
        data: {
            room_id: "xxx",`
            user_ids: ["user_1", "user_2"]
        }
    }
    
    """
    data = data_json["data"]
    room_id = data["room_id"]
    user_ids = data["user_ids"]
    for user_id in user_ids:
        map_room_user[room_id].add(user_id)
    # 
    map_room_user[room_id].add(current_user.user_id)


def leave(data_json, current_user):
    """
    data_json: {
        action: "leave",
        data: {
            room_id: "xxx",
        }
    }
    """
    data = data_json["data"]
    room_id = data["room_id"]
    if current_user.user_id in map_room_user[room_id]:
        map_room_user[room_id].remove(current_user.user_id)


async def make_request_friend(data_json, current_user):
    """
    data_json: {
        "action": "make-request-friend",
        "data": {
            to: "email"
        }
    }
    """
    data = data_json["data"]
    res = WebSocketResponse(
        action=data_json["action"],
        data={
            "from": current_user.user_id
        }
    )
    try:
        to_user = user_service.get_user_by_email(
            email=data["to"]
        )
        if to_user is not None and to_user.user_id in map_user_connection:
            await map_user_connection[to_user.user_id].send_text(res.json())
    except Exception as e:
        print(f"Error sending message: {e}")

async def update_status(is_online: bool, user_id: str):
    online_user_ids = []
    offline_user_ids = []
    if is_online:
        online_user_ids.append(user_id)
    else:
        offline_user_ids.append(user_id)
    res = WebSocketResponse(
        action="update-status",
        data = {
            "online_user_ids": online_user_ids,
            "offline_user_ids": offline_user_ids
        }
    )
    await boardcast(res.json())

async def relay_message(data_json):
    """
    data_json: {
        "action": "change-contact",
        "data": {
            user_ids: ["1", "2"]
        }
    }
    """
    data = data_json["data"]
    list_user_id = data.get("user_ids", [])
    res = WebSocketResponse(
        action=data_json["action"],
        data= data
    )
    try:
        for user_id in list_user_id:
            if user_id in map_user_connection:
                await map_user_connection[user_id].send_text(res.json())
    except Exception as e:
        print(f"Error sending message: {e}")

async def remove(data_json):
    """
    data_json: {
        action: "remove",
        data: {
            room_id: "xxx",`
            user_ids: ["user_1", "user_2"]
        }
    }
    
    """
    data = data_json["data"]
    room_id = data["room_id"]
    user_ids = data["user_ids"]
    for user_id in user_ids:
        if user_id in map_room_user[room_id]:
            map_room_user[room_id].remove(user_id)
    
    # await relay_message(data_json)

async def delete_room(data_json):
    """
    data_json: {
        action: "delete-room",
        data: {
            room_id: "xxx",`
        }
    }
    """
    data = data_json["data"]
    room_id = data["room_id"]
    if room_id in map_room_user:
        map_room_user.pop(room_id)