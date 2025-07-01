import asyncio
import pytest
import websockets

# Example WebSocket server that echoes back any received message
async def echo_server(websocket, path):
    async for message in websocket:
        await websocket.send(f"Echo: {message}")

# Fixture to start the server
@pytest.fixture
async def websocket_server():
    server = await websockets.serve(echo_server, "localhost", 8765)
    yield
    server.close()
    await server.wait_closed()

@pytest.mark.asyncio
async def test_websocket_communication(websocket_server):
    uri = "ws://localhost:8765"

    async with websockets.connect(uri) as websocket:
        test_message = "Hello Server"
        await websocket.send(test_message)

        response = await websocket.recv()
        assert response == f"Echo: {test_message}"