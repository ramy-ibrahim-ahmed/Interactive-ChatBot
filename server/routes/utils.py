import json
import asyncio
from typing import AsyncGenerator, Dict, Any


def _format_sse_message(event_data: Dict[str, Any]) -> str:
    return f"data: {json.dumps(event_data)}\n\n"


def _serialize_if_needed(data: Any) -> Any:
    return data.dict() if hasattr(data, "dict") else data


async def stream_workflow_events(
    workflow, user_message: str, history: str
) -> AsyncGenerator[str, None]:
    """
    Streams events from the workflow, yielding them as SSE messages.
    Captures the final AI response to be used for history update.
    """
    final_response = None
    try:
        # --- Pass history into the workflow's initial state ---
        async for event in workflow.astream_events(
            {
                "user_message": user_message,
                "history": history,
            },
            version="v2",
        ):
            kind = event["event"]
            name = event["name"]

            if kind == "on_chain_start" and name != "LangGraph":
                event_data = {"event": "start_node", "node": name}
                yield _format_sse_message(event_data)
                await asyncio.sleep(0.1)

            elif kind == "on_chain_stream" and name == "__chat__":
                if chunk := event["data"].get("chunk"):
                    event_data = {"event": "stream_chunk", "data": chunk}
                    yield _format_sse_message(event_data)
                    await asyncio.sleep(0.01)

            elif kind == "on_chain_end" and name == "LangGraph":
                final_state = event["data"]["output"]

                # Capture the final response
                final_response = final_state.get("response")
                final_payload = {
                    "answer": final_response,
                    "enhanced_query": _serialize_if_needed(final_state.get("queries")),
                    "search_results": final_state.get("search"),
                    "user_message": final_state.get("user_message"),
                }
                event_data = {"event": "final_answer", "data": final_payload}
                yield _format_sse_message(event_data)

    except Exception as e:
        print(f"Error during streaming: {e}")
        error_data = {"event": "error", "message": str(e)}
        yield _format_sse_message(error_data)
