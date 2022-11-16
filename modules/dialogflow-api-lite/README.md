# Dialogflow API Lite

A very simple Dialogflow API implementation.


## Setup

```bash

```


## Usage

```python
# intent recognition
query = ""
contexts = []

config = {
    "project_id": project_id,
    "credential": credential,
}
df = Dialogflow(config)

result = df.detect_intent(query, contexts)

```