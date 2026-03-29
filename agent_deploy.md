# Use the API Server

Supported in ADKPython v0.1.0TypeScript v0.2.0Go v0.1.0Java v0.1.0

Before you deploy your agent, you should test it to ensure that it is working as intended. Use the API server in ADK to expose your agents through a REST API for programmatic testing and integration.

## Start the API server

Use the following command to run your agent in an ADK API server:

```shell
adk api_server
```

```shell
npx adk api_server
```

```shell
go run agent.go web api
```

Make sure to update the port number.

With Maven, compile and run the ADK web server:

```console
mvn compile exec:java \
 -Dexec.args="--adk.agents.source-dir=src/main/java/agents --server.port=8080"
```

With Gradle, the `build.gradle` or `build.gradle.kts` build file should have the following Java plugin in its plugins section:

```groovy
plugins {
    id('java')
    // other plugins
}
```

Then, elsewhere in the build file, at the top-level, create a new task:

```groovy
tasks.register('runADKWebServer', JavaExec) {
    dependsOn classes
    classpath = sourceSets.main.runtimeClasspath
    mainClass = 'com.google.adk.web.AdkWebServer'
    args '--adk.agents.source-dir=src/main/java/agents', '--server.port=8080'
}
```

Finally, on the command-line, run the following command:

```console
gradle runADKWebServer
```

In Java, both the Dev UI and the API server are bundled together.

This command will launch a local web server, where you can run cURL commands or send API requests to test your agent. By default, the server runs on `http://localhost:8000`.

Advanced Usage and Debugging

For a complete reference on all available endpoints, request/response formats, and tips for debugging (including how to use the interactive API documentation), see the **ADK API Server Guide** below.

## Test locally

Testing locally involves launching a local web server, creating a session, and sending queries to your agent. First, ensure you are in the correct working directory.

For TypeScript, you should be inside the agent project directory itself.

```console
parent_folder/
└── my_sample_agent/  <-- For TypeScript, run commands from here
    └── agent.py (or Agent.java or agent.ts)
```

**Launch the Local Server**

Next, launch the local server using the commands listed above.

The output should appear similar to:

```shell
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
```

```shell
+-----------------------------------------------------------------------------+
| ADK Web Server started                                                      |
|                                                                             |
| For local testing, access at http://localhost:8000.                         |
+-----------------------------------------------------------------------------+
```

```shell
2025-05-13T23:32:08.972-06:00  INFO 37864 --- [ebServer.main()] o.s.b.w.embedded.tomcat.TomcatWebServer  : Tomcat started on port 8080 (http) with context path '/'
2025-05-13T23:32:08.980-06:00  INFO 37864 --- [ebServer.main()] com.google.adk.web.AdkWebServer          : Started AdkWebServer in 1.15 seconds (process running for 2.877)
2025-05-13T23:32:08.981-06:00  INFO 37864 --- [ebServer.main()] com.google.adk.web.AdkWebServer          : AdkWebServer application started successfully.
```

Your server is now running locally. Ensure you use the correct ***port number*** in all the subsequent commands.

**Create a new session**

With the API server still running, open a new terminal window or tab and create a new session with the agent using:

```shell
curl -X POST http://localhost:8000/apps/my_sample_agent/users/u_123/sessions/s_123 \
  -H "Content-Type: application/json" \
  -d '{"key1": "value1", "key2": 42}'
```

Let's break down what's happening:

- `http://localhost:8000/apps/my_sample_agent/users/u_123/sessions/s_123`: This creates a new session for your agent `my_sample_agent`, which is the name of the agent folder, for a user ID (`u_123`) and for a session ID (`s_123`). You can replace `my_sample_agent` with the name of your agent folder. You can replace `u_123` with a specific user ID, and `s_123` with a specific session ID.
- `{"key1": "value1", "key2": 42}`: This is optional. You can use this to customize the agent's pre-existing state (dict) when creating the session.

This should return the session information if it was created successfully. The output should appear similar to:

```json
{"id":"s_123","appName":"my_sample_agent","userId":"u_123","state":{"key1":"value1","key2":42},"events":[],"lastUpdateTime":1743711430.022186}
```

Info

You cannot create multiple sessions with exactly the same user ID and session ID. If you try to, you may see a response, like: `{"detail":"Session already exists: s_123"}`. To fix this, you can either delete that session (e.g., `s_123`), or choose a different session ID.

**Send a query**

There are two ways to send queries via POST to your agent, via the `/run` or `/run_sse` routes.

- `POST http://localhost:8000/run`: collects all events as a list and returns the list all at once. Suitable for most users (if you are unsure, we recommend using this one).
- `POST http://localhost:8000/run_sse`: returns as Server-Sent-Events, which is a stream of event objects. Suitable for those who want to be notified as soon as the event is available. With `/run_sse`, you can also set `streaming` to `true` to enable token-level streaming.

**Using `/run`**

```shell
curl -X POST http://localhost:8000/run \
-H "Content-Type: application/json" \
-d '{
"appName": "my_sample_agent",
"userId": "u_123",
"sessionId": "s_123",
"newMessage": {
    "role": "user",
    "parts": [{
    "text": "Hey whats the weather in new york today"
    }]
}
}'
```

In TypeScript, currently only `camelCase` field names are supported (e.g. `appName`, `userId`, `sessionId`, etc.).

If using `/run`, you will see the full output of events at the same time, as a list, which should appear similar to:

```json
[{"content":{"parts":[{"functionCall":{"id":"af-e75e946d-c02a-4aad-931e-49e4ab859838","args":{"city":"new york"},"name":"get_weather"}}],"role":"model"},"invocationId":"e-71353f1e-aea1-4821-aa4b-46874a766853","author":"weather_time_agent","actions":{"stateDelta":{},"artifactDelta":{},"requestedAuthConfigs":{}},"longRunningToolIds":[],"id":"2Btee6zW","timestamp":1743712220.385936},{"content":{"parts":[{"functionResponse":{"id":"af-e75e946d-c02a-4aad-931e-49e4ab859838","name":"get_weather","response":{"status":"success","report":"The weather in New York is sunny with a temperature of 25 degrees Celsius (41 degrees Fahrenheit)."}}}],"role":"user"},"invocationId":"e-71353f1e-aea1-4821-aa4b-46874a766853","author":"weather_time_agent","actions":{"stateDelta":{},"artifactDelta":{},"requestedAuthConfigs":{}},"id":"PmWibL2m","timestamp":1743712221.895042},{"content":{"parts":[{"text":"OK. The weather in New York is sunny with a temperature of 25 degrees Celsius (41 degrees Fahrenheit).\n"}],"role":"model"},"invocationId":"e-71353f1e-aea1-4821-aa4b-46874a766853","author":"weather_time_agent","actions":{"stateDelta":{},"artifactDelta":{},"requestedAuthConfigs":{}},"id":"sYT42eVC","timestamp":1743712221.899018}]
```

**Using `/run_sse`**

```shell
curl -X POST http://localhost:8000/run_sse \
-H "Content-Type: application/json" \
-d '{
"appName": "my_sample_agent",
"userId": "u_123",
"sessionId": "s_123",
"newMessage": {
    "role": "user",
    "parts": [{
    "text": "Hey whats the weather in new york today"
    }]
},
"streaming": false
}'
```

You can set `streaming` to `true` to enable token-level streaming, which means the response will be returned to you in multiple chunks and the output should appear similar to:

```shell
data: {"content":{"parts":[{"functionCall":{"id":"af-f83f8af9-f732-46b6-8cb5-7b5b73bbf13d","args":{"city":"new york"},"name":"get_weather"}}],"role":"model"},"invocationId":"e-3f6d7765-5287-419e-9991-5fffa1a75565","author":"weather_time_agent","actions":{"stateDelta":{},"artifactDelta":{},"requestedAuthConfigs":{}},"longRunningToolIds":[],"id":"ptcjaZBa","timestamp":1743712255.313043}

data: {"content":{"parts":[{"functionResponse":{"id":"af-f83f8af9-f732-46b6-8cb5-7b5b73bbf13d","name":"get_weather","response":{"status":"success","report":"The weather in New York is sunny with a temperature of 25 degrees Celsius (41 degrees Fahrenheit)."}}}],"role":"user"},"invocationId":"e-3f6d7765-5287-419e-9991-5fffa1a75565","author":"weather_time_agent","actions":{"stateDelta":{},"artifactDelta":{},"requestedAuthConfigs":{}},"id":"5aocxjaq","timestamp":1743712257.387306}

data: {"content":{"parts":[{"text":"OK. The weather in New York is sunny with a temperature of 25 degrees Celsius (41 degrees Fahrenheit).\n"}],"role":"model"},"invocationId":"e-3f6d7765-5287-419e-9991-5fffa1a75565","author":"weather_time_agent","actions":{"stateDelta":{},"artifactDelta":{},"requestedAuthConfigs":{}},"id":"rAnWGSiV","timestamp":1743712257.391317}
```

**Send a query with a base64 encoded file using `/run` or `/run_sse`**

```shell
curl -X POST http://localhost:8000/run \
-H 'Content-Type: application/json' \
-d '{
   "appName":"my_sample_agent",
   "userId":"u_123",
   "sessionId":"s_123",
   "newMessage":{
      "role":"user",
      "parts":[
         {
            "text":"Describe this image"
         },
         {
            "inlineData":{
               "displayName":"my_image.png",
               "data":"iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAYAAAD0eNT6AAAACXBIWXMAAAsTAAALEwEAmpw...",
               "mimeType":"image/png"
            }
         }
      ]
   },
   "streaming":false
}'
```

Info

If you are using `/run_sse`, you should see each event as soon as it becomes available.

## Integrations

ADK uses [Callbacks](https://google.github.io/adk-docs/callbacks/index.md) to integrate with third-party observability tools. These integrations capture detailed traces of agent calls and interactions, which are crucial for understanding behavior, debugging issues, and evaluating performance.

- [Comet Opik](https://github.com/comet-ml/opik) is an open-source LLM observability and evaluation platform that [natively supports ADK](https://www.comet.com/docs/opik/tracing/integrations/adk).

## Deploy your agent

Now that you've verified the local operation of your agent, you're ready to move on to deploying your agent! Here are some ways you can deploy your agent:

- Deploy to [Agent Engine](https://google.github.io/adk-docs/deploy/agent-engine/index.md), a simple way to deploy your ADK agents to a managed service in Vertex AI on Google Cloud.
- Deploy to [Cloud Run](https://google.github.io/adk-docs/deploy/cloud-run/index.md) and have full control over how you scale and manage your agents using serverless architecture on Google Cloud.

## Interactive API docs

The API server automatically generates interactive API documentation using Swagger UI. This is an invaluable tool for exploring endpoints, understanding request formats, and testing your agent directly from your browser.

To access the interactive docs, start the API server and navigate to <http://localhost:8000/docs> in your web browser.

You will see a complete, interactive list of all available API endpoints, which you can expand to see detailed information about parameters, request bodies, and response schemas. You can even click "Try it out" to send live requests to your running agents.

## API endpoints

The following sections detail the primary endpoints for interacting with your agents.

JSON Naming Convention

- **Both Request and Response bodies** will use `camelCase` for field names (e.g., `"appName"`).

### Utility endpoints

#### List available agents

Returns a list of all agent applications discovered by the server.

- **Method:** `GET`
- **Path:** `/list-apps`

**Example Request**

```shell
curl -X GET http://localhost:8000/list-apps
```

**Example Response**

```json
["my_sample_agent", "another_agent"]
```

______________________________________________________________________

### Session management

Sessions store the state and event history for a specific user's interaction with an agent.

#### Update a session

Updates an existing session.

- **Method:** `PATCH`
- **Path:** `/apps/{app_name}/users/{user_id}/sessions/{session_id}`

**Request Body**

```json
{
  "stateDelta": {
    "key1": "value1",
    "key2": 42
  }
}
```

**Example Request**

```shell
curl -X PATCH http://localhost:8000/apps/my_sample_agent/users/u_123/sessions/s_abc \
  -H "Content-Type: application/json" \
  -d '{"stateDelta":{"visit_count": 5}}'
```

**Example Response**

```json
{"id":"s_abc","appName":"my_sample_agent","userId":"u_123","state":{"visit_count":5},"events":[],"lastUpdateTime":1743711430.022186}
```

#### Get a session

Retrieves the details of a specific session, including its current state and all associated events.

- **Method:** `GET`
- **Path:** `/apps/{app_name}/users/{user_id}/sessions/{session_id}`

**Example Request**

```shell
curl -X GET http://localhost:8000/apps/my_sample_agent/users/u_123/sessions/s_abc
```

**Example Response**

```json
{"id":"s_abc","appName":"my_sample_agent","userId":"u_123","state":{"visit_count":5},"events":[...],"lastUpdateTime":1743711430.022186}
```

#### Delete a session

Deletes a session and all of its associated data.

- **Method:** `DELETE`
- **Path:** `/apps/{app_name}/users/{user_id}/sessions/{session_id}`

**Example Request**

```shell
curl -X DELETE http://localhost:8000/apps/my_sample_agent/users/u_123/sessions/s_abc
```

**Example Response** A successful deletion returns an empty response with a `204 No Content` status code.

______________________________________________________________________

### Agent execution

These endpoints are used to send a new message to an agent and get a response.

#### Run agent (single response)

Executes the agent and returns all generated events in a single JSON array after the run is complete.

- **Method:** `POST`
- **Path:** `/run`

**Request Body**

```json
{
  "appName": "my_sample_agent",
  "userId": "u_123",
  "sessionId": "s_abc",
  "newMessage": {
    "role": "user",
    "parts": [
      { "text": "What is the capital of France?" }
    ]
  }
}
```

In TypeScript, currently only `camelCase` field names are supported (e.g. `appName`, `userId`, `sessionId`, etc.).

**Example Request**

```shell
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "appName": "my_sample_agent",
    "userId": "u_123",
    "sessionId": "s_abc",
    "newMessage": {
      "role": "user",
      "parts": [{"text": "What is the capital of France?"}]
    }
  }'
```

#### Run agent (streaming)

Executes the agent and streams events back to the client as they are generated using [Server-Sent Events (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events).

- **Method:** `POST`
- **Path:** `/run_sse`

**Request Body** The request body is the same as for `/run`, with an additional optional `streaming` flag.

```json
{
  "appName": "my_sample_agent",
  "userId": "u_123",
  "sessionId": "s_abc",
  "newMessage": {
    "role": "user",
    "parts": [
      { "text": "What is the weather in New York?" }
    ]
  },
  "streaming": true
}
```

- `streaming`: (Optional) Set to `true` to enable token-level streaming for model responses. Defaults to `false`.

**Example Request**

```shell
curl -X POST http://localhost:8000/run_sse \
  -H "Content-Type: application/json" \
  -d '{
    "appName": "my_sample_agent",
    "userId": "u_123",
    "sessionId": "s_abc",
    "newMessage": {
      "role": "user",
      "parts": [{"text": "What is the weather in New York?"}]
    },
    "streaming": false
  }'
```




# Runtime Configuration

Supported in ADKPython v0.1.0Typescript v0.2.0Go v0.1.0Java v0.1.0

`RunConfig` defines runtime behavior and options for agents in ADK. It controls speech and streaming settings, function calling, artifact saving, and limits on LLM calls.

When constructing an agent run, you can pass a `RunConfig` to customize how the agent interacts with models, handles audio, and streams responses. By default, no streaming is enabled and inputs aren’t retained as artifacts. Use `RunConfig` to override these defaults.

## Class Definition

The `RunConfig` class holds configuration parameters for an agent's runtime behavior.

- Python ADK uses Pydantic for this validation.
- Go ADK has mutable structs by default.
- Java ADK typically uses immutable data classes.
- TypeScript ADK uses a standard interface, with type safety provided by the TypeScript compiler.

```python
class RunConfig(BaseModel):
    """Configs for runtime behavior of agents."""

    model_config = ConfigDict(
        extra='forbid',
    )

    speech_config: Optional[types.SpeechConfig] = None
    response_modalities: Optional[list[str]] = None
    save_input_blobs_as_artifacts: bool = False
    support_cfc: bool = False
    streaming_mode: StreamingMode = StreamingMode.NONE
    output_audio_transcription: Optional[types.AudioTranscriptionConfig] = None
    max_llm_calls: int = 500
```

```typescript
export interface RunConfig {
  speechConfig?: SpeechConfig;
  responseModalities?: Modality[];
  saveInputBlobsAsArtifacts: boolean;
  supportCfc: boolean;
  streamingMode: StreamingMode;
  outputAudioTranscription?: AudioTranscriptionConfig;
  maxLlmCalls: number;
  // ... and other properties
}

export enum StreamingMode {
  NONE = 'none',
  SSE = 'sse',
  BIDI = 'bidi',
}
```

```go
type StreamingMode string

const (
    StreamingModeNone StreamingMode = "none"
    StreamingModeSSE  StreamingMode = "sse"
)

// RunConfig controls runtime behavior.
type RunConfig struct {
    // Streaming mode, None or StreamingMode.SSE.
    StreamingMode StreamingMode
    // Whether or not to save the input blobs as artifacts
    SaveInputBlobsAsArtifacts bool
}
```

```java
public abstract class RunConfig {

  public enum StreamingMode {
    NONE,
    SSE,
    BIDI
  }

  public abstract @Nullable SpeechConfig speechConfig();

  public abstract ImmutableList<Modality> responseModalities();

  public abstract boolean saveInputBlobsAsArtifacts();

  public abstract @Nullable AudioTranscriptionConfig outputAudioTranscription();

  public abstract int maxLlmCalls();

  // ...
}
```

## Runtime Parameters

| Parameter                       | Python Type                                | TypeScript Type                       | Go Type         | Java Type                                             | Default (Py / TS / Go / Java)                                                                  | Description                                                                                                                                                 |
| ------------------------------- | ------------------------------------------ | ------------------------------------- | --------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `speech_config`                 | `Optional[types.SpeechConfig]`             | `SpeechConfig` (optional)             | N/A             | `SpeechConfig` (nullable via `@Nullable`)             | `None` / `undefined`/ N/A / `null`                                                             | Configures speech synthesis (voice, language) using the `SpeechConfig` type.                                                                                |
| `response_modalities`           | `Optional[list[str]]`                      | `Modality[]` (optional)               | N/A             | `ImmutableList<Modality>`                             | `None` / `undefined` / N/A / Empty `ImmutableList`                                             | List of desired output modalities (e.g., Python: `["TEXT", "AUDIO"]`; Java/TS: uses structured `Modality` objects).                                         |
| `save_input_blobs_as_artifacts` | `bool`                                     | `boolean`                             | `bool`          | `boolean`                                             | `False` / `false` / `false` / `false`                                                          | If `true`, saves input blobs (e.g., uploaded files) as run artifacts for debugging/auditing.                                                                |
| `streaming_mode`                | `StreamingMode`                            | `StreamingMode`                       | `StreamingMode` | `StreamingMode`                                       | `StreamingMode.NONE` / `StreamingMode.NONE` / `agent.StreamingModeNone` / `StreamingMode.NONE` | Sets the streaming behavior: `NONE` (default), `SSE` (server-sent events), or `BIDI` (bidirectional).                                                       |
| `output_audio_transcription`    | `Optional[types.AudioTranscriptionConfig]` | `AudioTranscriptionConfig` (optional) | N/A             | `AudioTranscriptionConfig` (nullable via `@Nullable`) | `None` / `undefined` / N/A / `null`                                                            | Configures transcription of generated audio output using the `AudioTranscriptionConfig` type.                                                               |
| `max_llm_calls`                 | `int`                                      | `number`                              | N/A             | `int`                                                 | `500` / `500` / N/A / `500`                                                                    | Limits total LLM calls per run. `0` or negative means unlimited. Exceeding language limits (e.g. `sys.maxsize`, `Number.MAX_SAFE_INTEGER`) raises an error. |
| `support_cfc`                   | `bool`                                     | `boolean`                             | N/A             | `bool`                                                | `False` / `false` / N/A / `false`                                                              | **Python/TypeScript:** Enables Compositional Function Calling. Requires `streaming_mode=SSE` and uses the LIVE API. **Experimental.**                       |

### `speech_config`

Supported in ADKPython v0.1.0Java v0.1.0

Note

The interface or definition of `SpeechConfig` is the same, irrespective of the language.

Speech configuration settings for live agents with audio capabilities. The `SpeechConfig` class has the following structure:

```python
class SpeechConfig(_common.BaseModel):
    """The speech generation configuration."""

    voice_config: Optional[VoiceConfig] = Field(
        default=None,
        description="""The configuration for the speaker to use.""",
    )
    language_code: Optional[str] = Field(
        default=None,
        description="""Language code (ISO 639. e.g. en-US) for the speech synthesization.
        Only available for Live API.""",
    )
```

The `voice_config` parameter uses the `VoiceConfig` class:

```python
class VoiceConfig(_common.BaseModel):
    """The configuration for the voice to use."""

    prebuilt_voice_config: Optional[PrebuiltVoiceConfig] = Field(
        default=None,
        description="""The configuration for the speaker to use.""",
    )
```

And `PrebuiltVoiceConfig` has the following structure:

```python
class PrebuiltVoiceConfig(_common.BaseModel):
    """The configuration for the prebuilt speaker to use."""

    voice_name: Optional[str] = Field(
        default=None,
        description="""The name of the prebuilt voice to use.""",
    )
```

These nested configuration classes allow you to specify:

- `voice_config`: The name of the prebuilt voice to use (in the `PrebuiltVoiceConfig`)
- `language_code`: ISO 639 language code (e.g., "en-US") for speech synthesis

When implementing voice-enabled agents, configure these parameters to control how your agent sounds when speaking.

### `response_modalities`

Supported in ADKPython v0.1.0Java v0.1.0

Defines the output modalities for the agent. If not set, defaults to AUDIO. Response modalities determine how the agent communicates with users through various channels (e.g., text, audio).

### `save_input_blobs_as_artifacts`

Supported in ADKPython v0.1.0Go v0.1.0Java v0.1.0

When enabled, input blobs will be saved as artifacts during agent execution. This is useful for debugging and audit purposes, allowing developers to review the exact data received by agents.

### `support_cfc`

Supported in ADKPython v0.1.0Experimental

Enables Compositional Function Calling (CFC) support. Only applicable when using StreamingMode.SSE. When enabled, the LIVE API will be invoked as only it supports CFC functionality.

Experimental release

The `support_cfc` feature is experimental and its API or behavior might change in future releases.

### `streaming_mode`

Supported in ADKPython v0.1.0Go v0.1.0

Configures the streaming behavior of the agent. Possible values:

- `StreamingMode.NONE`: No streaming; responses delivered as complete units
- `StreamingMode.SSE`: Server-Sent Events streaming; one-way streaming from server to client
- `StreamingMode.BIDI`: Bidirectional streaming; simultaneous communication in both directions

Streaming modes affect both performance and user experience. SSE streaming lets users see partial responses as they're generated, while BIDI streaming enables real-time interactive experiences.

### `output_audio_transcription`

Supported in ADKPython v0.1.0Java v0.1.0

Configuration for transcribing audio outputs from live agents with audio response capability. This enables automatic transcription of audio responses for accessibility, record-keeping, and multi-modal applications.

### `max_llm_calls`

Supported in ADKPython v0.1.0Java v0.1.0

Sets a limit on the total number of LLM calls for a given agent run.

- Values greater than 0 and less than `sys.maxsize`: Enforces a bound on LLM calls
- Values less than or equal to 0: Allows unbounded LLM calls *(not recommended for production)*

This parameter prevents excessive API usage and potential runaway processes. Since LLM calls often incur costs and consume resources, setting appropriate limits is crucial.

## Validation Rules

Supported in ADKPython v0.1.0Typescript v0.2.0Go v0.1.0Java v0.1.0

The `RunConfig` class validates its parameters to ensure proper agent operation. While Python ADK uses `Pydantic` for automatic type validation, Java and TypeScript ADK rely on their static type systems and may include explicit checks in the `RunConfig`'s constructor. For the `max_llm_calls` parameter specifically:

1. Extremely large values (like `sys.maxsize` in Python, `Integer.MAX_VALUE` in Java, or `Number.MAX_SAFE_INTEGER` in TypeScript) are typically disallowed to prevent issues.
1. Values of zero or less will usually trigger a warning about unlimited LLM interactions.

### Basic runtime configuration

```python
from google.genai.adk import RunConfig, StreamingMode

config = RunConfig(
    streaming_mode=StreamingMode.NONE,
    max_llm_calls=100
)
```

```typescript
import { RunConfig, StreamingMode } from '@google/adk';

const config: RunConfig = {
  streamingMode: StreamingMode.NONE,
  maxLlmCalls: 100,
};
```

```go
import "google.golang.org/adk/agent"

config := agent.RunConfig{
    StreamingMode: agent.StreamingModeNone,
}
```

```java
import com.google.adk.agents.RunConfig;
import com.google.adk.agents.RunConfig.StreamingMode;

RunConfig config = RunConfig.builder()
        .setStreamingMode(StreamingMode.NONE)
        .setMaxLlmCalls(100)
        .build();
```

This configuration creates a non-streaming agent with a limit of 100 LLM calls, suitable for simple task-oriented agents where complete responses are preferable.

### Enabling streaming

```python
from google.genai.adk import RunConfig, StreamingMode

config = RunConfig(
    streaming_mode=StreamingMode.SSE,
    max_llm_calls=200
)
```

```typescript
import { RunConfig, StreamingMode } from '@google/adk';

const config: RunConfig = {
  streamingMode: StreamingMode.SSE,
  maxLlmCalls: 200,
};
```

```go
import "google.golang.org/adk/agent"

config := agent.RunConfig{
    StreamingMode: agent.StreamingModeSSE,
}
```

```java
import com.google.adk.agents.RunConfig;
import com.google.adk.agents.RunConfig.StreamingMode;

RunConfig config = RunConfig.builder()
    .setStreamingMode(StreamingMode.SSE)
    .setMaxLlmCalls(200)
    .build();
```

Using SSE streaming allows users to see responses as they're generated, providing a more responsive feel for chatbots and assistants.

### Enabling speech support

```python
from google.genai.adk import RunConfig, StreamingMode
from google.genai import types

config = RunConfig(
    speech_config=types.SpeechConfig(
        language_code="en-US",
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name="Kore"
            )
        ),
    ),
    response_modalities=["AUDIO", "TEXT"],
    save_input_blobs_as_artifacts=True,
    support_cfc=True,
    streaming_mode=StreamingMode.SSE,
    max_llm_calls=1000,
)
```

```typescript
import { RunConfig, StreamingMode } from '@google/adk';

const config: RunConfig = {
    speechConfig: {
        languageCode: "en-US",
        voiceConfig: {
            prebuiltVoiceConfig: {
                voiceName: "Kore"
            }
        },
    },
    responseModalities: [
      { modality: "AUDIO" },
      { modality: "TEXT" }
    ],
    saveInputBlobsAsArtifacts: true,
    supportCfc: true,
    streamingMode: StreamingMode.SSE,
    maxLlmCalls: 1000,
};
```

```java
import com.google.adk.agents.RunConfig;
import com.google.adk.agents.RunConfig.StreamingMode;
import com.google.common.collect.ImmutableList;
import com.google.genai.types.Content;
import com.google.genai.types.Modality;
import com.google.genai.types.Part;
import com.google.genai.types.PrebuiltVoiceConfig;
import com.google.genai.types.SpeechConfig;
import com.google.genai.types.VoiceConfig;

RunConfig runConfig =
    RunConfig.builder()
        .setStreamingMode(StreamingMode.SSE)
        .setMaxLlmCalls(1000)
        .setSaveInputBlobsAsArtifacts(true)
        .setResponseModalities(ImmutableList.of(new Modality("AUDIO"), new Modality("TEXT")))
        .setSpeechConfig(
            SpeechConfig.builder()
                .voiceConfig(
                    VoiceConfig.builder()
                        .prebuiltVoiceConfig(
                            PrebuiltVoiceConfig.builder().voiceName("Kore").build())
                        .build())
                .languageCode("en-US")
                .build())
        .build();
```

This comprehensive example configures an agent with:

- Speech capabilities using the "Kore" voice (US English)
- Both audio and text output modalities
- Artifact saving for input blobs (useful for debugging)
- Experimental CFC support enabled **(Python and TypeScript)**
- SSE streaming for responsive interaction
- A limit of 1000 LLM calls

### Enabling CFC Support

Supported in ADKPython v0.1.0Typescript v0.2.0Experimental

```python
from google.genai.adk import RunConfig, StreamingMode

config = RunConfig(
    streaming_mode=StreamingMode.SSE,
    support_cfc=True,
    max_llm_calls=150
)
```

```typescript
import { RunConfig, StreamingMode } from '@google/adk';

const config: RunConfig = {
    streamingMode: StreamingMode.SSE,
    supportCfc: true,
    maxLlmCalls: 150,
};
```

Enabling Compositional Function Calling (CFC) creates an agent that can dynamically execute functions based on model outputs, powerful for applications requiring complex workflows.

Experimental release

The Compositional Function Calling (CFC) streaming feature is an experimental release.

# Resume stopped agents

Supported in ADKPython v1.14.0

An ADK agent's execution can be interrupted by various factors including dropped network connections, power failure, or a required external system going offline. The Resume feature of ADK allows an agent workflow to pick up where it left off, avoiding the need to restart the entire workflow. In ADK Python 1.16 and higher, you can configure an ADK workflow to be resumable, so that it tracks the execution of workflow and then allows you to resume it after an unexpected interruption.

This guide explains how to configure your ADK agent workflow to be resumable. If you use Custom Agents, you can update them to be resumable. For more information, see [Add resume to custom Agents](#custom-agents).

## Add resumable configuration

Enable the Resume function for an agent workflow by applying a Resumability configuration to the App object of your ADK workflow, as shown in the following code example:

```python
app = App(
    name='my_resumable_agent',
    root_agent=root_agent,
    # Set the resumability config to enable resumability.
    resumability_config=ResumabilityConfig(
        is_resumable=True,
    ),
)
```

Caution: Long Running Functions, Confirmations, Authentication

For agents that use [Long Running Functions](/adk-docs/tools-custom/function-tools/#long-run-tool), [Confirmations](/adk-docs/tools-custom/confirmation/), or [Authentication](/adk-docs/tools-custom/authentication/) requiring user input, adding a resumable confirmation changes how these features operate. For more information, see the documentation for those features.

Note: Custom Agents

Resume is not supported by default for Custom Agents. You must update the agent code for a Custom Agent to support the Resume feature. For information on modifying Custom Agents to support incremental resume functionality, see [Add resume to custom Agents](#custom-agents).

## Resume a stopped workflow

When an ADK workflow stops execution you can resume the workflow using a command containing the Invocation ID for the workflow instance, which can be found in the [Event](/adk-docs/events/#understanding-and-using-events) history of the workflow. Make sure the ADK API server is running, in case it was interrupted or powered off, and then run the following command to resume the workflow, as shown in the following API request example.

```console
# restart the API server if needed:
adk api_server my_resumable_agent/

# resume the agent:
curl -X POST http://localhost:8000/run_sse \
 -H "Content-Type: application/json" \
 -d '{
   "app_name": "my_resumable_agent",
   "user_id": "u_123",
   "session_id": "s_abc",
   "invocation_id": "invocation-123",
 }'
```

You can also resume a workflow using the Runner object Run Async method, as shown below:

```python
runner.run_async(user_id='u_123', session_id='s_abc', 
    invocation_id='invocation-123')

# When new_message is set to a function response,
# we are trying to resume a long running function.
```

Note

Resuming a workflow from the ADK Web user interface or using the ADK command line (CLI) tool is not currently supported.

## How it works

The Resume feature works by logging completed Agent workflow tasks, including incremental steps using [Events](/adk-docs/events/) and [Event Actions](/adk-docs/events/#detecting-actions-and-side-effects). tracking completion of agent tasks within a resumable workflow. If a workflow is interrupted and then later restarted, the system resumes the workflow by setting the completion state of each agent. If an agent did not complete, the workflow system reinstates any completed Events for that agent, and restarts the workflow from the partially completed state. For multi-agent workflows, the specific resume behavior varies, based on the multi-agent classes in your workflow, as described below:

- **Sequential Agent**: Reads the current_sub_agent from its saved state to find the next sub-agent to run in the sequence.
- **Loop Agent**: Uses the current_sub_agent and times_looped values to continue the loop from the last completed iteration and sub-agent.
- **Parallel Agent**: Determines which sub-agents have already completed and only runs those that have not finished.

Event logging includes results from Tools which successfully returned a result. So if an agent successfully executed Function Tools A and B, and then failed during execution of tool C, the system reinstates the results from the tools A and B, and resumes the workflow by re-running the tool C request.

Caution: Tool execution behavior

When resuming a workflow with Tools, the Resume feature ensures that the Tools in an agent are run ***at least once***, and may run more than once when resuming a workflow. If your agent uses Tools where duplicate runs would have a negative impact, such as purchases, you should modify the Tool to check for and prevent duplicate runs.

Note: Workflow modification with Resume not supported

Do not modify a stopped agent workflow before resuming it. For example adding or removing agents from workflow that has stopped and then resuming that workflow is not supported.

## Add resume to custom Agents

Custom agents have specific implementation requirements in order to support resumability. You must decide on and define workflow steps within your custom agent which produce a result which can be preserved before handing off to the next step of processing. The following steps outline how to modify a Custom Agent to support a workflow Resume.

- **Create CustomAgentState class**: Extend the BaseAgentState to create an object that preserves the state of your agent.
  - **Optionally, create WorkFlowStep class**: If your custom agent has sequential steps, consider creating a WorkFlowStep list object that defines the discrete, savable steps of the agent.
- **Add initial agent state:** Modify your agent's async run function to set the initial state of your agent.
- **Add agent state checkpoints**: Modify your agent's async run function to generate and save the agent state for each completed step of the agent's overall task.
- **Add end of agent status to track agent state:** Modify your agent's async run function to include an `end_of_agent=True` status upon successful completion of the agent's full task.

The following example shows the required code modifications to the example StoryFlowAgent class shown in the [Custom Agents](/adk-docs/agents/custom-agents/#full-code-example) guide:

```python
class WorkflowStep(int, Enum):
 INITIAL_STORY_GENERATION = 1
 CRITIC_REVISER_LOOP = 2
 POST_PROCESSING = 3
 CONDITIONAL_REGENERATION = 4

# Extend BaseAgentState

### class StoryFlowAgentState(BaseAgentState):

###   step = WorkflowStep

@override
async def _run_async_impl(
    self, ctx: InvocationContext
) -> AsyncGenerator[Event, None]:
    """
    Implements the custom orchestration logic for the story workflow.
    Uses the instance attributes assigned by Pydantic (e.g., self.story_generator).
    """
    agent_state = self._load_agent_state(ctx, WorkflowStep)

    if agent_state is None:
      # Record the start of the agent
      agent_state = StoryFlowAgentState(step=WorkflowStep.INITIAL_STORY_GENERATION)
      yield self._create_agent_state_event(ctx, agent_state)

    next_step = agent_state.step
    logger.info(f"[{self.name}] Starting story generation workflow.")

    # Step 1. Initial Story Generation
    if next_step <= WorkflowStep.INITIAL_STORY_GENERATION:
      logger.info(f"[{self.name}] Running StoryGenerator...")
      async for event in self.story_generator.run_async(ctx):
          yield event

      # Check if story was generated before proceeding
      if "current_story" not in ctx.session.state or not ctx.session.state[
          "current_story"
      ]:
          return  # Stop processing if initial story failed

    agent_state = StoryFlowAgentState(step=WorkflowStep.CRITIC_REVISER_LOOP)
    yield self._create_agent_state_event(ctx, agent_state)

    # Step 2. Critic-Reviser Loop
    if next_step <= WorkflowStep.CRITIC_REVISER_LOOP:
      logger.info(f"[{self.name}] Running CriticReviserLoop...")
      async for event in self.loop_agent.run_async(ctx):
          logger.info(
              f"[{self.name}] Event from CriticReviserLoop: "
              f"{event.model_dump_json(indent=2, exclude_none=True)}"
          )
          yield event

    agent_state = StoryFlowAgentState(step=WorkflowStep.POST_PROCESSING)
    yield self._create_agent_state_event(ctx, agent_state)

    # Step 3. Sequential Post-Processing (Grammar and Tone Check)
    if next_step <= WorkflowStep.POST_PROCESSING:
      logger.info(f"[{self.name}] Running PostProcessing...")
      async for event in self.sequential_agent.run_async(ctx):
          logger.info(
              f"[{self.name}] Event from PostProcessing: "
              f"{event.model_dump_json(indent=2, exclude_none=True)}"
          )
          yield event

    agent_state = StoryFlowAgentState(step=WorkflowStep.CONDITIONAL_REGENERATION)
    yield self._create_agent_state_event(ctx, agent_state)

    # Step 4. Tone-Based Conditional Logic
    if next_step <= WorkflowStep.CONDITIONAL_REGENERATION:
      tone_check_result = ctx.session.state.get("tone_check_result")
      if tone_check_result == "negative":
          logger.info(f"[{self.name}] Tone is negative. Regenerating story...")
          async for event in self.story_generator.run_async(ctx):
              logger.info(
                  f"[{self.name}] Event from StoryGenerator (Regen): "
                  f"{event.model_dump_json(indent=2, exclude_none=True)}"
              )
              yield event
      else:
          logger.info(f"[{self.name}] Tone is not negative. Keeping current story.")

    logger.info(f"[{self.name}] Workflow finished.")
    yield self._create_agent_state_event(ctx, end_of_agent=True)
```


# Runtime Configuration

Supported in ADKPython v0.1.0Typescript v0.2.0Go v0.1.0Java v0.1.0

`RunConfig` defines runtime behavior and options for agents in ADK. It controls speech and streaming settings, function calling, artifact saving, and limits on LLM calls.

When constructing an agent run, you can pass a `RunConfig` to customize how the agent interacts with models, handles audio, and streams responses. By default, no streaming is enabled and inputs aren’t retained as artifacts. Use `RunConfig` to override these defaults.

## Class Definition

The `RunConfig` class holds configuration parameters for an agent's runtime behavior.

- Python ADK uses Pydantic for this validation.
- Go ADK has mutable structs by default.
- Java ADK typically uses immutable data classes.
- TypeScript ADK uses a standard interface, with type safety provided by the TypeScript compiler.

```python
class RunConfig(BaseModel):
    """Configs for runtime behavior of agents."""

    model_config = ConfigDict(
        extra='forbid',
    )

    speech_config: Optional[types.SpeechConfig] = None
    response_modalities: Optional[list[str]] = None
    save_input_blobs_as_artifacts: bool = False
    support_cfc: bool = False
    streaming_mode: StreamingMode = StreamingMode.NONE
    output_audio_transcription: Optional[types.AudioTranscriptionConfig] = None
    max_llm_calls: int = 500
```

```typescript
export interface RunConfig {
  speechConfig?: SpeechConfig;
  responseModalities?: Modality[];
  saveInputBlobsAsArtifacts: boolean;
  supportCfc: boolean;
  streamingMode: StreamingMode;
  outputAudioTranscription?: AudioTranscriptionConfig;
  maxLlmCalls: number;
  // ... and other properties
}

export enum StreamingMode {
  NONE = 'none',
  SSE = 'sse',
  BIDI = 'bidi',
}
```

```go
type StreamingMode string

const (
    StreamingModeNone StreamingMode = "none"
    StreamingModeSSE  StreamingMode = "sse"
)

// RunConfig controls runtime behavior.
type RunConfig struct {
    // Streaming mode, None or StreamingMode.SSE.
    StreamingMode StreamingMode
    // Whether or not to save the input blobs as artifacts
    SaveInputBlobsAsArtifacts bool
}
```

```java
public abstract class RunConfig {

  public enum StreamingMode {
    NONE,
    SSE,
    BIDI
  }

  public abstract @Nullable SpeechConfig speechConfig();

  public abstract ImmutableList<Modality> responseModalities();

  public abstract boolean saveInputBlobsAsArtifacts();

  public abstract @Nullable AudioTranscriptionConfig outputAudioTranscription();

  public abstract int maxLlmCalls();

  // ...
}
```

## Runtime Parameters

| Parameter                       | Python Type                                | TypeScript Type                       | Go Type         | Java Type                                             | Default (Py / TS / Go / Java)                                                                  | Description                                                                                                                                                 |
| ------------------------------- | ------------------------------------------ | ------------------------------------- | --------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `speech_config`                 | `Optional[types.SpeechConfig]`             | `SpeechConfig` (optional)             | N/A             | `SpeechConfig` (nullable via `@Nullable`)             | `None` / `undefined`/ N/A / `null`                                                             | Configures speech synthesis (voice, language) using the `SpeechConfig` type.                                                                                |
| `response_modalities`           | `Optional[list[str]]`                      | `Modality[]` (optional)               | N/A             | `ImmutableList<Modality>`                             | `None` / `undefined` / N/A / Empty `ImmutableList`                                             | List of desired output modalities (e.g., Python: `["TEXT", "AUDIO"]`; Java/TS: uses structured `Modality` objects).                                         |
| `save_input_blobs_as_artifacts` | `bool`                                     | `boolean`                             | `bool`          | `boolean`                                             | `False` / `false` / `false` / `false`                                                          | If `true`, saves input blobs (e.g., uploaded files) as run artifacts for debugging/auditing.                                                                |
| `streaming_mode`                | `StreamingMode`                            | `StreamingMode`                       | `StreamingMode` | `StreamingMode`                                       | `StreamingMode.NONE` / `StreamingMode.NONE` / `agent.StreamingModeNone` / `StreamingMode.NONE` | Sets the streaming behavior: `NONE` (default), `SSE` (server-sent events), or `BIDI` (bidirectional).                                                       |
| `output_audio_transcription`    | `Optional[types.AudioTranscriptionConfig]` | `AudioTranscriptionConfig` (optional) | N/A             | `AudioTranscriptionConfig` (nullable via `@Nullable`) | `None` / `undefined` / N/A / `null`                                                            | Configures transcription of generated audio output using the `AudioTranscriptionConfig` type.                                                               |
| `max_llm_calls`                 | `int`                                      | `number`                              | N/A             | `int`                                                 | `500` / `500` / N/A / `500`                                                                    | Limits total LLM calls per run. `0` or negative means unlimited. Exceeding language limits (e.g. `sys.maxsize`, `Number.MAX_SAFE_INTEGER`) raises an error. |
| `support_cfc`                   | `bool`                                     | `boolean`                             | N/A             | `bool`                                                | `False` / `false` / N/A / `false`                                                              | **Python/TypeScript:** Enables Compositional Function Calling. Requires `streaming_mode=SSE` and uses the LIVE API. **Experimental.**                       |

### `speech_config`

Supported in ADKPython v0.1.0Java v0.1.0

Note

The interface or definition of `SpeechConfig` is the same, irrespective of the language.

Speech configuration settings for live agents with audio capabilities. The `SpeechConfig` class has the following structure:

```python
class SpeechConfig(_common.BaseModel):
    """The speech generation configuration."""

    voice_config: Optional[VoiceConfig] = Field(
        default=None,
        description="""The configuration for the speaker to use.""",
    )
    language_code: Optional[str] = Field(
        default=None,
        description="""Language code (ISO 639. e.g. en-US) for the speech synthesization.
        Only available for Live API.""",
    )
```

The `voice_config` parameter uses the `VoiceConfig` class:

```python
class VoiceConfig(_common.BaseModel):
    """The configuration for the voice to use."""

    prebuilt_voice_config: Optional[PrebuiltVoiceConfig] = Field(
        default=None,
        description="""The configuration for the speaker to use.""",
    )
```

And `PrebuiltVoiceConfig` has the following structure:

```python
class PrebuiltVoiceConfig(_common.BaseModel):
    """The configuration for the prebuilt speaker to use."""

    voice_name: Optional[str] = Field(
        default=None,
        description="""The name of the prebuilt voice to use.""",
    )
```

These nested configuration classes allow you to specify:

- `voice_config`: The name of the prebuilt voice to use (in the `PrebuiltVoiceConfig`)
- `language_code`: ISO 639 language code (e.g., "en-US") for speech synthesis

When implementing voice-enabled agents, configure these parameters to control how your agent sounds when speaking.

### `response_modalities`

Supported in ADKPython v0.1.0Java v0.1.0

Defines the output modalities for the agent. If not set, defaults to AUDIO. Response modalities determine how the agent communicates with users through various channels (e.g., text, audio).

### `save_input_blobs_as_artifacts`

Supported in ADKPython v0.1.0Go v0.1.0Java v0.1.0

When enabled, input blobs will be saved as artifacts during agent execution. This is useful for debugging and audit purposes, allowing developers to review the exact data received by agents.

### `support_cfc`

Supported in ADKPython v0.1.0Experimental

Enables Compositional Function Calling (CFC) support. Only applicable when using StreamingMode.SSE. When enabled, the LIVE API will be invoked as only it supports CFC functionality.

Experimental release

The `support_cfc` feature is experimental and its API or behavior might change in future releases.

### `streaming_mode`

Supported in ADKPython v0.1.0Go v0.1.0

Configures the streaming behavior of the agent. Possible values:

- `StreamingMode.NONE`: No streaming; responses delivered as complete units
- `StreamingMode.SSE`: Server-Sent Events streaming; one-way streaming from server to client
- `StreamingMode.BIDI`: Bidirectional streaming; simultaneous communication in both directions

Streaming modes affect both performance and user experience. SSE streaming lets users see partial responses as they're generated, while BIDI streaming enables real-time interactive experiences.

### `output_audio_transcription`

Supported in ADKPython v0.1.0Java v0.1.0

Configuration for transcribing audio outputs from live agents with audio response capability. This enables automatic transcription of audio responses for accessibility, record-keeping, and multi-modal applications.

### `max_llm_calls`

Supported in ADKPython v0.1.0Java v0.1.0

Sets a limit on the total number of LLM calls for a given agent run.

- Values greater than 0 and less than `sys.maxsize`: Enforces a bound on LLM calls
- Values less than or equal to 0: Allows unbounded LLM calls *(not recommended for production)*

This parameter prevents excessive API usage and potential runaway processes. Since LLM calls often incur costs and consume resources, setting appropriate limits is crucial.

## Validation Rules

Supported in ADKPython v0.1.0Typescript v0.2.0Go v0.1.0Java v0.1.0

The `RunConfig` class validates its parameters to ensure proper agent operation. While Python ADK uses `Pydantic` for automatic type validation, Java and TypeScript ADK rely on their static type systems and may include explicit checks in the `RunConfig`'s constructor. For the `max_llm_calls` parameter specifically:

1. Extremely large values (like `sys.maxsize` in Python, `Integer.MAX_VALUE` in Java, or `Number.MAX_SAFE_INTEGER` in TypeScript) are typically disallowed to prevent issues.
1. Values of zero or less will usually trigger a warning about unlimited LLM interactions.

### Basic runtime configuration

```python
from google.genai.adk import RunConfig, StreamingMode

config = RunConfig(
    streaming_mode=StreamingMode.NONE,
    max_llm_calls=100
)
```

```typescript
import { RunConfig, StreamingMode } from '@google/adk';

const config: RunConfig = {
  streamingMode: StreamingMode.NONE,
  maxLlmCalls: 100,
};
```

```go
import "google.golang.org/adk/agent"

config := agent.RunConfig{
    StreamingMode: agent.StreamingModeNone,
}
```

```java
import com.google.adk.agents.RunConfig;
import com.google.adk.agents.RunConfig.StreamingMode;

RunConfig config = RunConfig.builder()
        .setStreamingMode(StreamingMode.NONE)
        .setMaxLlmCalls(100)
        .build();
```

This configuration creates a non-streaming agent with a limit of 100 LLM calls, suitable for simple task-oriented agents where complete responses are preferable.

### Enabling streaming

```python
from google.genai.adk import RunConfig, StreamingMode

config = RunConfig(
    streaming_mode=StreamingMode.SSE,
    max_llm_calls=200
)
```

```typescript
import { RunConfig, StreamingMode } from '@google/adk';

const config: RunConfig = {
  streamingMode: StreamingMode.SSE,
  maxLlmCalls: 200,
};
```

```go
import "google.golang.org/adk/agent"

config := agent.RunConfig{
    StreamingMode: agent.StreamingModeSSE,
}
```

```java
import com.google.adk.agents.RunConfig;
import com.google.adk.agents.RunConfig.StreamingMode;

RunConfig config = RunConfig.builder()
    .setStreamingMode(StreamingMode.SSE)
    .setMaxLlmCalls(200)
    .build();
```

Using SSE streaming allows users to see responses as they're generated, providing a more responsive feel for chatbots and assistants.

### Enabling speech support

```python
from google.genai.adk import RunConfig, StreamingMode
from google.genai import types

config = RunConfig(
    speech_config=types.SpeechConfig(
        language_code="en-US",
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name="Kore"
            )
        ),
    ),
    response_modalities=["AUDIO", "TEXT"],
    save_input_blobs_as_artifacts=True,
    support_cfc=True,
    streaming_mode=StreamingMode.SSE,
    max_llm_calls=1000,
)
```

```typescript
import { RunConfig, StreamingMode } from '@google/adk';

const config: RunConfig = {
    speechConfig: {
        languageCode: "en-US",
        voiceConfig: {
            prebuiltVoiceConfig: {
                voiceName: "Kore"
            }
        },
    },
    responseModalities: [
      { modality: "AUDIO" },
      { modality: "TEXT" }
    ],
    saveInputBlobsAsArtifacts: true,
    supportCfc: true,
    streamingMode: StreamingMode.SSE,
    maxLlmCalls: 1000,
};
```

```java
import com.google.adk.agents.RunConfig;
import com.google.adk.agents.RunConfig.StreamingMode;
import com.google.common.collect.ImmutableList;
import com.google.genai.types.Content;
import com.google.genai.types.Modality;
import com.google.genai.types.Part;
import com.google.genai.types.PrebuiltVoiceConfig;
import com.google.genai.types.SpeechConfig;
import com.google.genai.types.VoiceConfig;

RunConfig runConfig =
    RunConfig.builder()
        .setStreamingMode(StreamingMode.SSE)
        .setMaxLlmCalls(1000)
        .setSaveInputBlobsAsArtifacts(true)
        .setResponseModalities(ImmutableList.of(new Modality("AUDIO"), new Modality("TEXT")))
        .setSpeechConfig(
            SpeechConfig.builder()
                .voiceConfig(
                    VoiceConfig.builder()
                        .prebuiltVoiceConfig(
                            PrebuiltVoiceConfig.builder().voiceName("Kore").build())
                        .build())
                .languageCode("en-US")
                .build())
        .build();
```

This comprehensive example configures an agent with:

- Speech capabilities using the "Kore" voice (US English)
- Both audio and text output modalities
- Artifact saving for input blobs (useful for debugging)
- Experimental CFC support enabled **(Python and TypeScript)**
- SSE streaming for responsive interaction
- A limit of 1000 LLM calls

### Enabling CFC Support

Supported in ADKPython v0.1.0Typescript v0.2.0Experimental

```python
from google.genai.adk import RunConfig, StreamingMode

config = RunConfig(
    streaming_mode=StreamingMode.SSE,
    support_cfc=True,
    max_llm_calls=150
)
```

```typescript
import { RunConfig, StreamingMode } from '@google/adk';

const config: RunConfig = {
    streamingMode: StreamingMode.SSE,
    supportCfc: true,
    maxLlmCalls: 150,
};
```

Enabling Compositional Function Calling (CFC) creates an agent that can dynamically execute functions based on model outputs, powerful for applications requiring complex workflows.

Experimental release

The Compositional Function Calling (CFC) streaming feature is an experimental release.
