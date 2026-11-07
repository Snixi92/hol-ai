import sys
import time
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add core-engine to path
core_engine_path = Path(r"C:\Users\Yassir\.gemini\antigravity\scratch\hol-ai\services\core-engine")
if str(core_engine_path) not in sys.path:
    sys.path.insert(0, str(core_engine_path))

from src.services.daily_tasks import DailyTasksService
from src.services.morning_briefing import MorningBriefingService
from src.services.session_manager import ConversationSession, SessionManager

results = {
    "agent": "Agent-2-Productivity-Tasks",
    "tests_run": 0,
    "tests_passed": 0,
    "tests_failed": 0,
    "failures": [],
    "details": []
}

def record_test(name: str, passed: bool, info: str = ""):
    results["tests_run"] += 1
    if passed:
        results["tests_passed"] += 1
        print(f"  [PASS] {name} {info}")
    else:
        results["tests_failed"] += 1
        results["failures"].append({"name": name, "info": info})
        print(f"  [FAIL] {name} {info}")

print("=== STARTING AGENT 2: PRODUCTIVITY, GMAIL, CALENDAR, FINANCE & TASKS AUDIT ===")

# Test 1: Live Gmail IMAP & Inbox Triage
print("\n--- 1. Gmail Inbox Triage & Real IMAP Integration ---")
t0 = time.time()
try:
    inbox_data = DailyTasksService.clean_and_sort_inbox()
    lat = round((time.time() - t0) * 1000, 1)
    is_live = inbox_data.get("is_live_gmail") is True
    has_account = bool(inbox_data.get("account"))
    has_urgent = isinstance(inbox_data.get("important_urgent"), list) and len(inbox_data["important_urgent"]) > 0
    record_test(
        "Live Gmail IMAP Connection", 
        is_live and has_account, 
        f"({lat}ms) -> Account: {inbox_data.get('account')}, Unread: {inbox_data.get('unread_scanned')}"
    )
    record_test(
        "Inbox Urgent Email Extraction", 
        has_urgent, 
        f"Extracted {len(inbox_data.get('important_urgent', []))} emails with subjects & actions"
    )
    # Check that each email has essential fields
    first_mail = inbox_data.get("important_urgent", [])[0] if has_urgent else {}
    has_fields = "from" in first_mail and "subject" in first_mail and "action_suggested" in first_mail
    record_test("Email item structural integrity", has_fields, f"First mail: {first_mail.get('from')} - {first_mail.get('subject')}")
except Exception as e:
    record_test("Live Gmail IMAP Connection", False, f"Exception: {e}")

# Test 2: Calendar & Meeting Conflicts Resolution
print("\n--- 2. Calendar Management & Agenda Optimization ---")
t0 = time.time()
try:
    cal_data = DailyTasksService.manage_calendar_and_conflicts("Planning de demain")
    lat = round((time.time() - t0) * 1000, 1)
    valid_cal = (
        isinstance(cal_data, dict) and 
        "total_meetings" in cal_data and 
        "agenda_today" in cal_data and 
        len(cal_data["agenda_today"]) > 0
    )
    record_test(
        "Calendar conflicts & focus time", 
        valid_cal, 
        f"({lat}ms) -> {cal_data.get('total_meetings')} réunions, {cal_data.get('conflicts_detected')} conflit résolu, +{cal_data.get('focus_time_unlocked_hours')}h focus"
    )
except Exception as e:
    record_test("Calendar conflicts & focus time", False, f"Exception: {e}")

# Test 3: Morning Jarvis Briefing (Weather, News, Schedule)
print("\n--- 3. Morning Jarvis Briefing ---")
t0 = time.time()
try:
    briefing = MorningBriefingService.generate_briefing_sync(city="Paris", topic="tech")
    lat = round((time.time() - t0) * 1000, 1)
    valid_briefing = (
        isinstance(briefing, dict) and 
        "weather" in briefing and 
        "schedule" in briefing and 
        "tasks" in briefing
    )
    w = briefing.get("weather", {})
    record_test(
        "Jarvis Morning Briefing Generation", 
        valid_briefing, 
        f"({lat}ms) -> Météo {w.get('city')}: {w.get('temp_c')}°C {w.get('condition')}, {len(briefing.get('schedule', []))} événements"
    )
except Exception as e:
    record_test("Jarvis Morning Briefing Generation", False, f"Exception: {e}")

# Test 4: Recipe parsing to Supermarket Drive list
print("\n--- 4. Recipe to Grocery List ---")
t0 = time.time()
try:
    grocery = DailyTasksService.parse_instagram_recipe_to_grocery_list("Pâtes Burrata Champignons")
    lat = round((time.time() - t0) * 1000, 1)
    valid_groc = (
        isinstance(grocery, dict) and 
        "aisles" in grocery and 
        len(grocery["aisles"]) > 0 and 
        "total_estimated_eur" in grocery
    )
    total_items = sum(len(items) for items in grocery.get("aisles", {}).values())
    record_test(
        "Recipe conversion to aisles & prices", 
        valid_groc, 
        f"({lat}ms) -> {grocery.get('recipe_name')}: {total_items} articles ({grocery.get('total_estimated_eur')}€)"
    )
except Exception as e:
    record_test("Recipe conversion to aisles & prices", False, f"Exception: {e}")

# Test 5: Multi-Turn Memory & Anaphora Resolution
print("\n--- 5. Multi-Turn Session Memory Integrity ---")
try:
    session = ConversationSession(session_id="audit_mem_test")
    session.add_user_message("combien coûte un iPhone 14 ?")
    
    mock_deal_card = {
        "type": "deal",
        "data": {
            "product": "iPhone 14 128Go",
            "current_drop_price_eur": 629.0,
            "platform": "Cdiscount"
        }
    }
    session.add_assistant_message("Je l'ai trouvé à 629€ sur Cdiscount.", cards=[mock_deal_card])
    
    # User asks elliptical follow up
    session.add_user_message("et sur leboncoin ??")
    history = session.get_formatted_history(max_turns=5)
    
    # Check if assistant turn contains enriched card context
    assistant_turn_content = history[1]["content"]
    has_enriched_context = "iPhone 14" in assistant_turn_content and "629" in assistant_turn_content
    record_test(
        "Multi-turn card data memory persistence", 
        has_enriched_context, 
        "Turn 2 context retains product & price from Turn 1 cards"
    )
    
    # Check last_product tracking
    record_test(
        "Session active product tracking", 
        session.last_product is not None and "iPhone" in session.last_product, 
        f"Active product: '{session.last_product}'"
    )
except Exception as e:
    record_test("Multi-turn memory persistence", False, f"Exception: {e}")

print("\n=== AGENT 2 AUDIT SUMMARY ===")
print(f"Total Tests: {results['tests_run']} | Passed: {results['tests_passed']} | Failed: {results['tests_failed']}")
if results['failures']:
    print("Failures:")
    for f in results['failures']:
        print(f" - {f['name']}: {f['info']}")

report_path = core_engine_path.parent.parent / "scratch" / "multi_agent_audit" / "agent2_report.json"
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"Report saved to {report_path}")
