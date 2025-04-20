import os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from slack_sdk import WebClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

token = os.environ["SLACK_TOKEN"]


# Set up a WebClient with the Slack OAuth token
client = WebClient(token=token)

# Disable pandas display truncation
pd.set_option('display.max_rows', None)     # Show all rows
pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.width', None)        # No line wrapping
pd.set_option('display.colheader_justify', 'left')  # Left-align column headers


# Read log file
log_file_path = "system_logs.txt"  # Update with your file path if needed
with open(log_file_path, "r") as file:
    logs = file.readlines()

# Parse logs into a structured DataFrame
data = []
for log in logs:
    parts = log.strip().split(" ", 3)  # Ensure the message part is captured fully
    if len(parts) < 4:
        continue  # Skip malformed lines
    timestamp = parts[0] + " " + parts[1]
    level = parts[2]
    message = parts[3]
    data.append([timestamp, level, message])

df = pd.DataFrame(data, columns=["timestamp", "level", "message"])

# Convert timestamp to datetime format for sorting
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Assign numeric scores to log levels
level_mapping = {"INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
df["level_score"] = df["level"].map(level_mapping)

# Add message length as a new feature
df["message_length"] = df["message"].apply(len)

# AI Model for Anomaly Detection (Isolation Forest)
model = IsolationForest(contamination=0.1, random_state=42)  # Lower contamination for better accuracy
df["anomaly"] = model.fit_predict(df[["level_score", "message_length"]])

# Mark anomalies in a readable format
df["is_anomaly"] = df["anomaly"].apply(lambda x: "❌ Anomaly" if x == -1 else "✅ Normal")

# Print only detected anomalies
anomalies = df[df["is_anomaly"] == "❌ Anomaly"]

message = f"\n🔍 **Detected Anomalies:**\n{anomalies}"

#print(message)



# Send a message to slack
client.chat_postMessage(
    channel="log-notifications", 
    text=message, 
    username="Bot User"
)



