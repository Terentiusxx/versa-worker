import os
import requests
import runpod

LLAMA_URL = os.environ.get("LLAMA_URL", "http://127.0.0.1:8080")
TIMEOUT = int(os.environ.get("LLAMA_TIMEOUT_SECONDS", "900"))

OPTIONAL_PARAMS = {
    "temperature",
    "top_p",
    "top_k",
    "min_p",
    "max_tokens",
    "presence_penalty",
    "frequency_penalty",
    "repeat_penalty",
    "seed",
    "stop",
    "response_format",
    "tools",
    "tool_choice",
    "reasoning_effort",
    "chat_template_kwargs",
}


def handler(job):
    job_input = job.get("input") or {}
    messages = job_input.get("messages")

    if not isinstance(messages, list) or not messages:
        return {"error": "input.messages must be a non-empty array"}

    body = {
        "model": job_input.get("model", "versa-chat"),
        "messages": messages,
        "stream": False,
    }

    for key in OPTIONAL_PARAMS:
        if key in job_input:
            body[key] = job_input[key]

    try:
        response = requests.post(
            f"{LLAMA_URL}/v1/chat/completions",
            json=body,
            timeout=TIMEOUT,
        )

        try:
            result = response.json()
        except Exception:
            result = {
                "error": "llama-server returned a non-JSON response",
                "status_code": response.status_code,
                "body": response.text[:2000],
            }

        if response.status_code >= 400:
            return {
                "error": "llama-server request failed",
                "status_code": response.status_code,
                "details": result,
            }

        return result

    except requests.RequestException as exc:
        return {
            "error": "Could not reach llama-server",
            "details": str(exc),
        }


# Keep this at module scope so RunPod's GitHub source scanner can detect it.
runpod.serverless.start({"handler": handler})
