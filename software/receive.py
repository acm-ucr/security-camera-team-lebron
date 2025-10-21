import paho.mqtt.client as mqtt

# MQTT broker settings
BROKER = "broker.emqx.io"  # Public broker for testing
PORT = 1883
TOPIC = "security/alert"        # Replace with your topic

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
        client.subscribe(TOPIC)
        print(f"📡 Subscribed to topic: {TOPIC}")
    else:
        print(f"❌ Failed to connect, return code {rc}")

# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    print(f"📨 Received message from {msg.topic}: {msg.payload.decode()}")

# Create an MQTT client instance
client = mqtt.Client()

# Assign callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
client.connect(BROKER, PORT, keepalive=60)

# Blocking loop to process network traffic and dispatch callbacks
client.loop_forever()