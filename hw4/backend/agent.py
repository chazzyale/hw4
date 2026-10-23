"""Shop chatbot entry point: builds the PydanticAI agent and runs one chat turn.

Wiring:
- System prompt: prompts/prompt.md (Campus Customs voice and safety basics).
- Model: OPENAI_MODEL (default gpt-6-luna) through the Portkey gateway, using PORTKEY_API_KEY from .env.
- Tools: tools.py ("Product Confirmation", "Information Output", plus search for recommendations).
- Output: models.AgentReply (reply text, flow step, product_id, product_ids); product cards are then
  rebuilt from the database, and the Yes/No or size buttons come from models.STEP_CHOICES.
- Flow state (models.ChatState) round-trips with the website so the server tracks which product was
  confirmed, which were rejected, and which size was picked.
"""

import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from functools import cache
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")  # keep the server log clean

from dotenv import find_dotenv, load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai import Agent, capture_run_messages
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

from models import (
    PREVIEW_NOT_FOUND_REPLY,
    SIZE_OPTIONS,
    ProductPreviewResult,
    STEP_CHOICES,
    AgentReply,
    ChatRequest,
    ChatResponse,
    ChatState,
    ChatTurn,
    CustomerInfo,
    HistoryMessage,
    PageContext,
    ProductCard,
    SizeStock,
)
from tools import TOOLS, find_product

# Finds the nearest .env walking up from backend/ (the course key lives in AI Foundations/.env).
load_dotenv(find_dotenv())

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "prompt.md"
DEFAULT_MODEL = "gpt-6-luna"
HISTORY_TURNS = 12  # earlier messages sent to the model for context
MAX_CARDS = 6


def build_model() -> OpenAIResponsesModel:
    """OpenAI-compatible model through Portkey. Uses the Responses API because
    gpt-6-luna rejects function tools on /v1/chat/completions."""
    key = os.getenv("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is missing. Add it to the .env file.")
    client = AsyncOpenAI(
        api_key=key,
        base_url=os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"),
        default_headers={"x-portkey-api-key": key},
    )
    model_name = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    return OpenAIResponsesModel(model_name, provider=OpenAIProvider(openai_client=client))


@cache
def shop_agent() -> Agent[None, AgentReply]:
    """Built once on first use. Restart the server after editing prompts/prompt.md."""
    return Agent(
        build_model(),
        instructions=PROMPT_PATH.read_text(encoding="utf-8"),
        tools=TOOLS,
        output_type=AgentReply,
        name="campus-customs-assistant",
    )


def to_history(request: ChatRequest) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for turn in request.history[-HISTORY_TURNS:]:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


def product_cards(product_ids: list[str]) -> list[ProductCard]:
    """Turn the agent's product_ids into cards using live database values; unknown ids are dropped."""
    cards: list[ProductCard] = []
    for pid in dict.fromkeys(product_ids):  # de-duplicate, keep order
        p = find_product(pid)
        if p is None:
            continue
        cards.append(
            ProductCard(
                product_id=p["product_id"],
                name=p["name"],
                price=p["price"],
                image_url=p["image_url"],
                url=f"/products/{p['product_id']}",
                category=p["category"],
                total_stock=p["total_stock"],
                inventory=[SizeStock(**s) for s in p["inventory"]],
            )
        )
        if len(cards) == MAX_CARDS:
            break
    return cards


FILTERED_REPLY = (
    "Sorry, I can't help with that request. I never share or change account passwords. "
    "I'm happy to help you find Campus Customs gear, sizes, and stock. Go Bulldogs!"
)

YES = {"yes", "y", "yep", "yeah", "correct", "that's it", "thats it"}
NO = {"no", "n", "nope", "not it", "no it isn't", "wrong"}
FLOW_STEPS = {"confirm_product", "ask_more_details", "ask_specific_size", "choose_size", "information_output", "timeout"}


def apply_answer(state: ChatState, message: str) -> ChatState:
    """Record the shopper's answer to the last flow question (usually a button click) in the state."""
    state = state.model_copy(deep=True)
    answer = message.strip().lower().rstrip(".!")
    if state.step == "confirm_product" and state.product_id:
        if answer in YES:
            state.confirmed = True
        elif answer in NO:
            state.rejected_product_ids.append(state.product_id)
            state.product_id, state.product_name, state.confirmed = None, None, False
    elif state.step == "ask_specific_size" and answer in NO:
        state.size = None
    elif state.step == "choose_size" and message.strip().upper() in SIZE_OPTIONS:
        state.size = message.strip().upper()
    return state


def state_note(state: ChatState) -> str:
    """Server-written context for the model, so it knows exactly where the product flow is."""
    if state.step == "none" and not state.product_id and not state.rejected_product_ids:
        return "[Chat state from the server] Not in the product inquiry flow yet."
    lines = [f"[Chat state from the server] Last question you asked: {state.step}."]
    if state.product_id:
        lines.append(
            f'Product: "{state.product_name}" (product_id {state.product_id}), '
            f"{'CONFIRMED by the shopper' if state.confirmed else 'not yet confirmed'}."
        )
    if state.size:
        lines.append(f"Size the shopper picked: {state.size}.")
    if state.rejected_product_ids:
        lines.append(f"Shopper said No to these product_ids (pass as exclude_product_ids): {state.rejected_product_ids}.")
    return " ".join(lines)


def next_state(previous: ChatState, output: AgentReply) -> ChatState:
    if output.step not in FLOW_STEPS:
        return ChatState()  # general chat: the product flow starts over next time
    state = previous.model_copy(deep=True)
    state.step = output.step
    if output.step == "confirm_product" and output.product_id and output.product_id != previous.product_id:
        # A new candidate from Product Confirmation: not confirmed yet, no size picked.
        state.product_id, state.confirmed, state.size = output.product_id, False, None
    if state.product_id:
        p = find_product(state.product_id)
        if p is None:  # never keep an id the database doesn't know
            state.product_id, state.product_name, state.confirmed = None, None, False
        else:
            state.product_name = p["name"]
    return state


def preview_from_run(messages: list[ModelMessage]) -> ProductPreviewResult | None:
    """The last Product Preview tool result from this run, exactly as the tool returned it."""
    for message in reversed(messages):
        for part in getattr(message, "parts", []):
            if isinstance(part, ToolReturnPart) and part.tool_name == "product_preview":
                content = part.content
                return content if isinstance(content, ProductPreviewResult) else ProductPreviewResult.model_validate(content)
    return None


# --- Audit trail: append-only output/audit_trail.json ---
# Append-only audit trail of agent-loop activity: output/audit_trail.json.
#
# One entry per chat turn (one agent loop): when it ran, who and where (guest or user id, page), the
# model, every tool call with short args and a short result, the stop reason, how long it took, and
# any owner flags. Every value is copied from what the server actually observed (PydanticAI's message
# log, timers, usage counters); nothing is written by the model itself.
#
# Owner-only flags (never shown to customers):
# - slow_loop: the loop took longer than 30 seconds.
# - unapproved_tool:<name>: the model tried to call a tool that isn't one we built.
# Flags are written to the audit entry and also logged as warnings in the server console.
#
# The file is a valid JSON array that only grows: new entries are appended in place before the closing
# bracket; existing entries are never rewritten or removed, and nothing wipes the file between runs.

AUDIT_PATH = Path(os.environ.get("CC_AUDIT_PATH", Path(__file__).resolve().parents[1] / "output" / "audit_trail.json"))
SLOW_LOOP_SECONDS = 30
SHORT = 180  # characters kept for args / results

audit_log = logging.getLogger("campus_customs.audit")
_audit_lock = threading.Lock()


def audit_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def audit_short(value, limit: int = SHORT) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str, ensure_ascii=False)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def audit_summarize(content) -> str:
    """A short, factual summary of a tool result: its plain fields, list sizes, and the key names."""
    if isinstance(content, BaseModel):
        content = content.model_dump()
    if isinstance(content, dict):
        out = {}
        for key, value in content.items():
            if key == "message":
                continue  # instructions to the model; not useful in the audit
            if isinstance(value, (str, int, float, bool)) or value is None:
                out[key] = value
            elif isinstance(value, list):
                names = [v.get("name") or v.get("size") for v in value if isinstance(v, dict)]
                out[key] = f"{len(value)} items" + (f" ({', '.join(str(n) for n in names[:3])}...)" if names[:3] else "")
            elif isinstance(value, dict):
                if value.get("intents"):  # General Inquiry: what it understood the shopper wanted
                    out[key] = ", ".join(value["intents"])
                else:
                    out[key] = value.get("name") or value.get("product_id") or f"{len(value)} fields"
        return audit_short(out)
    if isinstance(content, list):
        return audit_short(f"{len(content)} items")
    return audit_short(content)


def audit_append(entry: dict) -> None:
    """Append one entry to the JSON array without rewriting earlier entries."""
    line = json.dumps(entry, ensure_ascii=False, default=str)
    with _audit_lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not AUDIT_PATH.exists() or AUDIT_PATH.stat().st_size == 0:
            AUDIT_PATH.write_text(f"[\n{line}\n]\n", encoding="utf-8")
            return
        with AUDIT_PATH.open("r+b") as f:
            # Find the closing "]" at the end of the file and insert the new entry before it.
            f.seek(0, os.SEEK_END)
            pos = f.tell()
            while pos > 0:
                pos -= 1
                f.seek(pos)
                ch = f.read(1)
                if ch == b"]":
                    break
                if not ch.isspace():
                    raise ValueError(f"{AUDIT_PATH} is not a JSON array; refusing to modify it")
            # Is the array empty ("[ ]")? Then no comma before the first entry.
            before = pos
            while before > 0:
                before -= 1
                f.seek(before)
                prev = f.read(1)
                if not prev.isspace():
                    break
            separator = "" if prev == b"[" else ","
            f.seek(pos)
            f.truncate()
            f.write(f"{separator}\n{line}\n]\n".encode("utf-8"))
    for flag in entry.get("flags", []):
        # "Flag to the owner": a warning in the server console, plus the flag in the audit entry.
        audit_log.warning("AUDIT FLAG %s (run %s, %ss)", flag, entry.get("run_id"), entry.get("duration_s"))


# --- Loop limits and the audit trail ---

# Hard cap per chat turn: at most 8 model requests and 12 tool calls, so a confused loop can't run on.
USAGE_LIMITS = UsageLimits(request_limit=8, tool_calls_limit=12)
LOOP_LIMIT_REPLY = "Sorry, I got a bit tangled up on that one. Could you ask it another way?"
APPROVED_TOOLS = {t.__name__ for t in TOOLS}
OUTPUT_TOOL_PREFIX = "final_result"  # PydanticAI's built-in tool for returning the structured AgentReply


def audit_entry(*, started_at: str, duration: float, messages: list[ModelMessage], result, stop_reason: str,
                customer: CustomerInfo | None, page: PageContext | None) -> dict:
    """One audit-trail entry for a chat turn, from the run's actual messages, timers, and usage."""
    calls: dict[str, dict] = {}
    retries: list[str] = []
    finish_reason = None
    for message in messages:
        if isinstance(message, ModelResponse):
            finish_reason = message.finish_reason or finish_reason
            for part in message.parts:
                if isinstance(part, ToolCallPart) and not part.tool_name.startswith(OUTPUT_TOOL_PREFIX):
                    calls[part.tool_call_id] = {
                        "time": message.timestamp.isoformat(timespec="seconds"),
                        "tool": part.tool_name,
                        "approved": part.tool_name in APPROVED_TOOLS,
                        "args": audit_short(part.args_as_dict()),
                        "result": None,
                    }
        elif isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, ToolReturnPart) and part.tool_call_id in calls:
                    calls[part.tool_call_id]["result"] = audit_summarize(part.content)
                elif isinstance(part, RetryPromptPart) and part.tool_name:
                    if part.tool_call_id in calls:
                        calls[part.tool_call_id]["result"] = "rejected: " + audit_short(str(part.content), 120)
                    retries.append(part.tool_name)

    flags = []
    if duration > SLOW_LOOP_SECONDS:
        flags.append("slow_loop")
    flags += [f"unapproved_tool:{c['tool']}" for c in calls.values() if not c["approved"]]

    entry = {
        "time": started_at,
        "run_id": uuid.uuid4().hex[:12],
        "customer": f"user:{customer.id}" if customer else "guest",
        "page": page.path if page else None,
        "model": os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        "tool_calls": list(calls.values()),
        "stop_reason": stop_reason,
        "finish_reason": finish_reason,
        "final_step": result.output.step if result is not None else None,
        "duration_s": round(duration, 2),
        "flags": flags,
    }
    if result is not None:
        usage = result.usage() if callable(result.usage) else result.usage
        entry["usage"] = {
            "model_requests": usage.requests,
            "tool_calls": usage.tool_calls,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
        }
    if retries:
        entry["retried_tools"] = retries
    return entry


def customer_note(customer: CustomerInfo | None) -> str:
    if customer is None:
        return "[Customer] Guest (not logged in). This chat is not saved."
    return (
        f"[Customer] Logged in as user_id {customer.id}: name \"{customer.name}\", email {customer.email}. "
        "This is the shopper you are talking to. Their chat is being saved."
    )


def page_note(page: PageContext | None) -> str:
    if page is None:
        return "[Page context] Unknown page."
    if page.product_name or page.image_file_path:
        return (
            f"[Page context] The shopper is on a product page ({page.path}). "
            f"Name on the page: \"{page.product_name}\". Image on the page: {page.image_file_path}. "
            "If they say \"this\", \"it\", or \"this one\", they mean this product: identify it with identify_page_product."
        )
    return f"[Page context] The shopper is on {page.path} (not a single product page)."


async def chat(
    request: ChatRequest,
    customer: CustomerInfo | None = None,
    saved_history: list[HistoryMessage] | None = None,
) -> ChatResponse:
    state = apply_answer(request.state, request.message)
    notes = "\n".join([customer_note(customer), page_note(request.page), state_note(state)])
    prompt = f"{notes}\n\n[Shopper message]\n{request.message}"
    # Logged-in shoppers: context comes from their saved chat_messages rows (looked up by user_id).
    # Guests: from the website's copy of this conversation.
    if saved_history is not None:
        request = request.model_copy(
            update={"history": [ChatTurn(role=m.role, content=m.content) for m in saved_history]}
        )
    history = to_history(request)
    started, started_at = time.monotonic(), audit_now()
    stop_reason, result = "completed", None
    with capture_run_messages() as run_messages:
        try:
            result = await shop_agent().run(prompt, message_history=history, usage_limits=USAGE_LIMITS)
        except ModelHTTPError as e:
            # The model provider's safety filter blocked the message (e.g. a jailbreak attempt).
            # Answer with a polite refusal instead of an error; nothing was revealed.
            stop_reason = "content_filter" if "content_filter" in str(e.body) else f"error: model HTTP {e.status_code}"
            if stop_reason != "content_filter":
                raise
            return ChatResponse(reply=FILTERED_REPLY, state=ChatState())
        except UsageLimitExceeded as e:
            stop_reason = f"loop_limit: {e}"
            return ChatResponse(reply=LOOP_LIMIT_REPLY, state=ChatState())
        except Exception as e:
            stop_reason = f"error: {type(e).__name__}"
            raise
        finally:
            # Append-only audit of this loop, built from what actually happened (never from the model's words).
            # A problem writing the audit must never break the customer's chat, so it is logged instead.
            try:
                audit_append(audit_entry(
                    started_at=started_at,
                    duration=time.monotonic() - started,
                    messages=list(run_messages)[len(history):],
                    result=result,
                    stop_reason=stop_reason,
                    customer=customer,
                    page=request.page,
                ))
            except Exception:
                audit_log.exception("Could not write the audit trail entry")
    output = result.output

    # Product Preview: the page shows the tool's own results (max 6), not cards the model picked.
    preview = preview_from_run(result.new_messages())
    if preview is not None:
        output.step = "product_preview"
        if preview.status == "no_match":
            output.reply = PREVIEW_NOT_FOUND_REPLY  # exact wording, every time
        output.product_ids = []  # cards go on the page, not in the chat bubble
    state = next_state(state, output)

    product_ids = list(output.product_ids)
    if output.step == "information_output" and state.product_id and state.product_id not in product_ids:
        product_ids.insert(0, state.product_id)  # always show the confirmed product's card with its stock
    return ChatResponse(
        reply=output.reply,
        products=product_cards(product_ids),
        choices=STEP_CHOICES.get(output.step, []),
        state=state,
        preview=preview,
    )
