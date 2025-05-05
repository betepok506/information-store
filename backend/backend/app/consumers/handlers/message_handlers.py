from aio_pika.abc import AbstractIncomingMessage
import json
from backend.app.services.message_processing import TextDataMessageProcessor



async def handle_message_event(
    message: AbstractIncomingMessage, 
    processor: TextDataMessageProcessor
):
    try:
        payload = json.loads(message.body.decode())
        success = await processor.process_message(payload)
        if success:
            print(f"Processed message: {payload}")
        else:
            await message.reject(requeue=False)
    except json.JSONDecodeError:
        print("Invalid JSON format")
        await message.reject(requeue=False)