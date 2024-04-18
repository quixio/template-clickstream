import json
import uuid
import asyncio
import websockets
from quixstreams import Application

from dotenv import load_dotenv
load_dotenv()


class WebSocketSubscriber:
    def __init__(self, app, topics, consumers, websocket_connections):
        self.app = app
        self.topics = topics
        self.consumers = consumers
        self.websocket_connections = websocket_connections


    async def consume_messages(self, topic_name):
        consumer = self.consumers[topic_name]
        while True:
            message = consumer.poll(1)
            if message is None:
                print(f'No messages found on {topic_name}')
            if message is not None:
                value = bytes.decode(message.value())
                closed_connections = []
                if topic_name in self.websocket_connections:
                    for client in self.websocket_connections[topic_name]:
                        try:
                            await client.send(json.dumps(value))
                            
                        except websockets.exceptions.ConnectionClosed:
                            print("Connection already closed.")
                            closed_connections.append(client)

                    print(f"Removing {len(closed_connections)} closed connections from {topic_name}.")
                    for client in closed_connections:
                        self.websocket_connections[topic_name].remove(client)

                    print(f"{value} was sent to {len(self.websocket_connections[topic_name])} subscribers of {topic_name}.")
            else:
                await asyncio.sleep(0.1)


    async def subscribe_messages(self, websocket, path):
        print(f"Client connected to socket. Path={path}")
        path_parts = path.strip('/').split('/')
        topic_name = path_parts[1] 

        if topic_name not in self.topics:
            my_topic = self.app.topic(name=topic_name)
            self.topics[topic_name] = my_topic
            self.consumers[topic_name] = self.app.get_consumer()
            self.consumers[topic_name].subscribe([my_topic.name])
            # Start consuming messages for this topic
            asyncio.create_task(self.consume_messages(topic_name))

        if topic_name not in self.websocket_connections:
            self.websocket_connections[topic_name] = []
        self.websocket_connections[topic_name].append(websocket)
        print(f'There are {len(self.websocket_connections[topic_name])} subscribers')

        try:
            await websocket.wait_closed()
        except websockets.exceptions.ConnectionClosedOK:
            print(f"Client {path} disconnected normally.")
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Client {path} disconnected with error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            print("Removing client from connection list")
            if topic_name in self.websocket_connections:
                self.websocket_connections[topic_name].remove(websocket)


    async def start_subscriber_server(self):
        print("Starting subscriber server...")
        server = await websockets.serve(self.subscribe_messages, '0.0.0.0', 80)
        await server.wait_closed()


async def main():
    app = Application(consumer_group="websocket"+str(uuid.uuid4()), auto_offset_reset="latest", use_changelog_topics=False)
    
    topics = {}
    consumers = {}
    websocket_connections = {}

    subscriber = WebSocketSubscriber(app, topics, consumers, websocket_connections)

    await asyncio.gather(
        subscriber.start_subscriber_server()
    )

# Run the application with exception handling
try:
    asyncio.run(main())
except Exception as e:
    print(f"An error occurred: {e}")