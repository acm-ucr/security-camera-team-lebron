# send.py — simple test message
import paho.mqtt.client as mqtt
import json

BROKER = "broker.emqx.io"
PORT = 1883
TOPIC = "security/alert"

# MQTT client — just default, no callback_api_version needed
client = mqtt.Client(client_id="ForgeCamPublisher")
client.connect(BROKER, PORT)
client.loop_start()

# --- Publish a test message ---
test_message = {
    "message": "Hello from send.py!",
    "status": "test"
}

client.publish(TOPIC, json.dumps(test_message))
print(f"Published test message to {TOPIC}")

client.loop_stop()
client.disconnect()
