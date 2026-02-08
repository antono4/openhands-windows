#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request


def http_json(method: str, url: str, payload=None, timeout: int = 30):
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else None


def get_json(base_url: str, path: str):
    return http_json("GET", base_url + path)


def post_json(base_url: str, path: str, payload):
    return http_json("POST", base_url + path, payload)


def get_last_event_id(base_url: str, conversation_id: str, limit: int = 50):
    last_id = -1
    start_id = 1
    while True:
        resp = get_json(
            base_url,
            f"/api/conversations/{conversation_id}/events?start_id={start_id}&limit={limit}",
        )
        events = resp.get("events", [])
        for e in events:
            eid = e.get("id")
            if isinstance(eid, int) and eid > last_id:
                last_id = eid
        if not resp.get("has_more"):
            break
        start_id = last_id + 1
    return last_id if last_id >= 0 else 0


def get_conversation_status(base_url: str, conversation_id: str):
    return get_json(base_url, f"/api/conversations/{conversation_id}")


def stop_conversation(base_url: str, conversation_id: str):
    try:
        post_json(base_url, f"/api/conversations/{conversation_id}/stop", {})
        return True
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        print(f"[warn] failed to stop conversation: {exc}")
    except Exception as exc:
        print(f"[warn] failed to stop conversation: {exc}")
    return False


def remove_runtime_container(conversation_id: str):
    name = f"openhands-runtime-{conversation_id}"
    try:
        result = subprocess.run(
            ["docker", "rm", "-f", name],
            capture_output=True,
            text=True,
            check=False,
        )
    except KeyboardInterrupt:
        print("[warn] cleanup interrupted; runtime container may still be running")
        return
    except FileNotFoundError:
        print("[warn] docker not found; cannot remove runtime container")
        return

    if result.returncode == 0:
        print(f"[cleanup] removed runtime container {name}")
        return

    stderr = (result.stderr or "").strip()
    if "No such container" in stderr:
        print(f"[cleanup] runtime container not found: {name}")
        return

    print(f"[warn] failed to remove runtime container: {stderr or 'unknown error'}")


def poll_events(
    base_url: str,
    conversation_id: str,
    last_id: int,
    poll_interval: float,
    timeout: int,
):
    deadline = time.time() + timeout
    saw_output = False
    saw_ready = False
    while True:
        if time.time() > deadline:
            print("[timeout] no response from agent")
            return last_id

        try:
            resp = get_json(
                base_url,
                f"/api/conversations/{conversation_id}/events?start_id={last_id + 1}&limit=50",
            )
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"[poll error] {exc}")
            time.sleep(poll_interval)
            continue

        events = resp.get("events", [])
        for e in events:
            eid = e.get("id")
            if isinstance(eid, int) and eid > last_id:
                last_id = eid

            src = e.get("source")
            action = e.get("action")
            obs = e.get("observation")
            msg = e.get("message") or ""
            content = e.get("content") or ""
            extras = e.get("extras") or {}

            if src == "agent" and action == "message":
                print(msg)
                saw_output = True
            elif src == "agent" and action == "run":
                print("[run] " + msg)
                saw_output = True
            elif obs == "run":
                if content.strip():
                    print("[output] " + content.strip())
                    saw_output = True
            elif obs == "agent_state_changed" or action == "change_agent_state":
                state = extras.get("agent_state") or (e.get("args") or {}).get(
                    "agent_state"
                )
                if state == "awaiting_user_input":
                    if saw_output:
                        return last_id
                    # Agent is ready but produced no output (e.g., message sent before ready).
                    if not saw_ready:
                        print("[agent ready] no response yet; waiting for reply...")
                        saw_ready = True
                    # Keep waiting until we see a reply or timeout.

        time.sleep(poll_interval)


def wait_for_ready(
    base_url: str,
    conversation_id: str,
    last_id: int,
    poll_interval: float,
    timeout: int,
):
    deadline = time.time() + timeout
    while True:
        if time.time() > deadline:
            print("[timeout] agent did not become ready")
            return last_id, False

        try:
            resp = get_json(
                base_url,
                f"/api/conversations/{conversation_id}/events?start_id={last_id + 1}&limit=50",
            )
        except (urllib.error.URLError, TimeoutError):
            time.sleep(poll_interval)
            continue

        events = resp.get("events", [])
        for e in events:
            eid = e.get("id")
            if isinstance(eid, int) and eid > last_id:
                last_id = eid

            obs = e.get("observation")
            action = e.get("action")
            extras = e.get("extras") or {}
            state = extras.get("agent_state") or (e.get("args") or {}).get(
                "agent_state"
            )
            if (obs == "agent_state_changed" or action == "change_agent_state") and (
                state == "awaiting_user_input"
            ):
                return last_id, True

        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description="Simple OpenHands CLI client")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENHANDS_URL", "http://localhost:3000"),
        help="OpenHands server URL (default: http://localhost:3000)",
    )
    parser.add_argument(
        "--conversation",
        default=None,
        help="Use an existing conversation ID",
    )
    parser.add_argument(
        "--no-wait-ready",
        action="store_true",
        help="Do not wait for agent to be ready before sending a message",
    )
    parser.add_argument(
        "--once",
        default=None,
        help="Send one message and exit",
    )
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument(
        "--no-auto-stop",
        dest="auto_stop",
        action="store_false",
        help="Do not stop/remove runtime container on exit",
    )
    parser.set_defaults(auto_stop=True)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    if args.conversation:
        conversation_id = args.conversation
        last_id = get_last_event_id(base_url, conversation_id)
        status = get_conversation_status(base_url, conversation_id)
        if status.get("runtime_status") == "STATUS$READY":
            args.no_wait_ready = True
    else:
        resp = post_json(base_url, "/api/conversations", {})
        conversation_id = resp.get("conversation_id")
        if not conversation_id:
            print("Failed to create conversation.")
            sys.exit(1)
        print(f"[conversation] {conversation_id}")

    if not args.conversation:
        last_id = -1

    if not args.no_wait_ready:
        last_id, ready = wait_for_ready(
            base_url, conversation_id, last_id, args.poll_interval, args.timeout
        )
        if not ready:
            print("[error] agent did not become ready; try again")
            sys.exit(1)

    def send_and_wait(message: str):
        nonlocal last_id
        post_json(
            base_url,
            f"/api/conversations/{conversation_id}/message",
            {"message": message},
        )
        last_id = poll_events(
            base_url,
            conversation_id,
            last_id,
            args.poll_interval,
            args.timeout,
        )

    def cleanup():
        if not args.auto_stop:
            return
        try:
            stop_conversation(base_url, conversation_id)
            remove_runtime_container(conversation_id)
        except KeyboardInterrupt:
            print("[warn] cleanup interrupted")

    if args.once:
        try:
            send_and_wait(args.once)
        finally:
            cleanup()
        return

    print("Type your message. Enter 'exit' to quit.")
    try:
        while True:
            user_msg = input("> ").strip()
            if not user_msg:
                continue
            if user_msg.lower() in ("exit", "quit"):
                break
            send_and_wait(user_msg)
    except KeyboardInterrupt:
        print("\nExiting.")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
