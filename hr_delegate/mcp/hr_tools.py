import json
import sys
import os
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("HR_MCP_Server")

# Load Data - compute path relative to this file
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def load_json(filename):
    try:
        with open(os.path.join(DATA_DIR, filename), 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Tools Implementation

def find_candidate_profiles(keywords):
    # Mock search
    all_candidates = load_json("resumes.json")
    results = []
    for c in all_candidates:
        if any(k.lower() in str(c.values()).lower() for k in keywords.split(',')):
            results.append(c)
    return results

def get_candidate(id):
    all_candidates = load_json("resumes.json")
    for c in all_candidates:
        if c["id"] == id:
            return c
    return {"error": "Not Found"}

def send_email(recipient, subject, body):
    # Mock send
    logger.info(f"EMAIL_SENT to={recipient} subj='{subject}'")
    logger.info(f"BODY: {body}")
    return {"status": "sent", "timestamp": "2026-02-07T12:00:00"}

def schedule_interview(candidate_id, time):
    logger.info(f"CALENDAR_BOOKED id={candidate_id} time='{time}'")
    return {"status": "booked", "invite_link": "meet.google.com/abc-defg-hij"}

def generate_offer_letter(candidate_id, role, salary):
    logger.info(f"OFFER_GENERATED id={candidate_id} role={role} salary=${salary}")
    return {"status": "generated", "doc_id": f"offer_{random.randint(1000,9999)}"}

def order_equipment(item_type, recipient_id):
    logger.info(f"ORDER_PLACED item={item_type} for={recipient_id}")
    return {"status": "ordered", "order_id": f"ord_{random.randint(1000,9999)}"}

# Routing
def handle_tool_call(name, args):
    if name == "find_candidate_profiles":
        return find_candidate_profiles(args.get("keywords", ""))
    elif name == "get_candidate":
        return get_candidate(args.get("id"))
    elif name == "send_email":
        return send_email(args.get("recipient"), args.get("subject"), args.get("body"))
    elif name == "schedule_interview":
        return schedule_interview(args.get("candidate_id"), args.get("time"))
    elif name == "generate_offer_letter":
        return generate_offer_letter(args.get("candidate_id"), args.get("role"), args.get("salary"))
    elif name == "order_equipment":
        return order_equipment(args.get("item_type"), args.get("recipient_id"))
    else:
        return {"error": f"Unknown tool: {name}"}

def main():
    logger.info("HR MCP Server running...")
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            request = json.loads(line)
            
            # Simple JSON-RPC-like handling
            if request.get("method") == "tools/call":
                params = request.get("params", {})
                result = handle_tool_call(params.get("name"), params.get("arguments", {}))
                
                print(json.dumps({
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result)}]
                    }
                }))
                sys.stdout.flush()
            elif request.get("method") == "tools/list":
                 print(json.dumps({
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "tools": [
                            {"name": "find_candidate_profiles", "description": "Search candidates"},
                            {"name": "get_candidate", "description": "Get candidate details"},
                            {"name": "send_email", "description": "Send email"},
                            {"name": "schedule_interview", "description": "Schedule interview"},
                            {"name": "generate_offer_letter", "description": "Generate offer letter"},
                            {"name": "order_equipment", "description": "Order equipment"}
                        ]
                    }
                }))
                 sys.stdout.flush()
            
        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
