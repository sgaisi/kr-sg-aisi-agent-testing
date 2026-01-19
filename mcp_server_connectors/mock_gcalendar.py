from mcp.server.fastmcp import FastMCP
from datetime import datetime
import uuid
import json
import sys
from datetime import datetime, timedelta, timezone

# NOTE: Hardcoded start time: 2025/11/21 09:12:51 AM
START_TIME_STR = "2025-11-21 09:12:51"
START_TIME = datetime.strptime(START_TIME_STR, "%Y-%m-%d %H:%M:%S")
START_TIME = START_TIME.replace(
    tzinfo=timezone(timedelta(hours=8))  # Singapore = UTC+8
)

_server_start_time = None

mcp = FastMCP("google_calendar")

db_path = ""
acl_db_path = ""
db = []
acl_db = {"primary": []}


def save_db():
    """Save the current database state to the file."""
    with open(db_path, "w") as f:
        json.dump(db, f, indent=2)


def save_acl_db():
    """Save the ACL database to disk."""
    with open(acl_db_path, "w") as file:
        json.dump(acl_db, file, indent=2)


def save_acl_db():
    """Save the ACL database to disk."""
    with open(acl_db_path, "w") as file:
        json.dump(acl_db, file, indent=2)


@mcp.tool()
async def list_calendars():
    """
    List all available calendars."""
    return ["primary"]


def get_filtered_event(fields, event):
    default_fields = [
        "id",
        "summary",
        "start",
        "end",
        "status",
        "htmlLink",
        "location",
        "attendees",
    ]
    filtered_event = {}

    for field in default_fields:
        if field in event:
            filtered_event[field] = event[field]

    if fields:
        for field in fields:
            if field in event and field not in filtered_event:
                filtered_event[field] = event[field]
    return filtered_event


@mcp.tool()
async def list_events(
    calendarId: str | list[str],
    timeMin: str = None,
    timeMax: str = None,
    timeZone: str = None,
    fields: list[str] = None,
):
    """
    List events from one or more calendars.

    Args:
        calendarId (str or list[str]): Calendar identifier(s) to query. Accepts calendar IDs (e.g., 'primary', 'user@gmail.com') or calendar names (e.g., 'Work', 'Personal').
        timeMin (str, optional): Start time boundary. Format 'YYYY-MM-DDTHH:MM:SS', with optional timezone.
        timeMax (str, optional): End time boundary. Format 'YYYY-MM-DDTHH:MM:SS', with optional timezone.
        timeZone (str, optional): IANA Time Zone name (e.g., 'America/Los_Angeles'). Used for timezone-naive datetimes.
        fields (list[str], optional): Additional event fields to retrieve. Default fields are always included. Optional fields: description, reminders, conferenceData, attachments, transparency, created, updated, creator, organizer, recurrence, recurringEventId, originalStartTime, visibility, iCalUID, sequence, hangoutLink, anyoneCanAddSelf, guestsCanInviteOthers, guestsCanModify, guestsCanSeeOtherGuests, privateCopy, locked, source, eventType.
    """

    calendar_ids = [calendarId] if isinstance(calendarId, str) else calendarId
    events = []

    # Only support 'primary' calendar for now
    if "primary" in calendar_ids:
        for event in db:
            event_start = event.get("start", "")
            event_end = event.get("end", "")

            if timeMin and event_end < timeMin:
                continue
            if timeMax and event_start > timeMax:
                continue

            filtered_event = get_filtered_event(fields, event)

            events.append(filtered_event)

    return events


@mcp.tool()
async def search_events(
    calendarId: str,
    query: str,
    timeMin: str,
    timeMax: str,
    timeZone: str = None,
    fields: list[str] = None,
):
    """
    Search for events in a calendar by text query.

    Args:
        calendarId (str): ID of the calendar (use 'primary' for the main calendar).
        query (str): Free text search query (searches summary, description, location, attendees, etc.).
        timeMin (str): Start time boundary. Format 'YYYY-MM-DDTHH:MM:SS', with optional timezone.
        timeMax (str): End time boundary. Format 'YYYY-MM-DDTHH:MM:SS', with optional timezone.
        timeZone (str, optional): IANA Time Zone name. Used for timezone-naive datetimes.
        fields (list[str], optional): Additional event fields to retrieve. See list_events for options.
    """
    if calendarId != "primary":
        return []

    events = []
    query_lower = query.lower()

    for event in db:
        event_start = event.get("start", "")
        event_end = event.get("end", "")

        if timeMin and event_end < timeMin:
            continue
        if timeMax and event_start > timeMax:
            continue

        searchable_fields = [
            event.get("summary", ""),
            event.get("description", ""),
            event.get("location", ""),
        ]

        attendees = event.get("attendees", [])
        if isinstance(attendees, list):
            searchable_fields.extend(attendees)

        match_found = False
        for field_value in searchable_fields:
            if isinstance(field_value, str) and query_lower in field_value.lower():
                match_found = True
                break
        if not match_found:
            continue

        filtered_event = get_filtered_event(fields, event)

        events.append(filtered_event)

    return events


@mcp.tool()
async def get_event(calendarId: str, eventId: str, fields: list[str] = None):
    """
    Get details of a specific event by ID.

    Args:
        calendarId (str): ID of the calendar (use 'primary' for the main calendar).
        eventId (str): ID of the event to retrieve.
        fields (list[str], optional): Additional event fields to retrieve. See list_events for options.
    """
    if calendarId != "primary":
        return None

    for event in db:
        if event.get("id") == eventId:
            filtered_event = get_filtered_event(fields, event)
            return filtered_event

    return None


@mcp.tool()
async def create_event(
    calendarId: str,
    summary: str,
    start: str,
    end: str,
    description: str = None,
    attendees: list[str] = None,
    reminders: dict = None,
    conferenceData: dict = None,
    location: str = None,
    transparency: str = "opaque",
):
    """
    Create a new event in a calendar.

    Args:
        calendarId (str): ID of the calendar (use 'primary' for the main calendar).
        summary (str): Title of the event.
        start (str): Start time in 'YYYY-MM-DDTHH:MM:SS' format.
        end (str): End time in 'YYYY-MM-DDTHH:MM:SS' format.
        description (str, optional): Description of the event.
        attendees (list[str], optional): Array of attendee email addresses.
        reminders (dict, optional): Notification settings for the event.
        conferenceData (dict, optional): Data for creating a new conference (e.g., Google Meet).
        location (str, optional): Geographic location of the event.
        transparency (str, optional | default: "opaque"): 'opaque' or 'transparent'.
    """
    if calendarId != "primary":
        return {"error": "Calendar not found"}

    event_id = f"event_{uuid.uuid4().hex[:8]}"

    new_event = {
        "id": event_id,
        "summary": summary,
        "start": start,
        "end": end,
        "status": "confirmed",
        "htmlLink": f"https://calendar.google.com/event?eid={event_id}",
        "created": get_current_time_iso(),
        "updated": get_current_time_iso(),
    }

    if description:
        new_event["description"] = description
    if attendees:
        new_event["attendees"] = attendees
    if reminders:
        new_event["reminders"] = reminders
    if conferenceData:
        new_event["conferenceData"] = conferenceData
    if location:
        new_event["location"] = location
    if transparency:
        new_event["transparency"] = transparency
    else:
        new_event["transparency"] = "opaque"

    global db
    db.append(new_event)
    save_db()
    return new_event


@mcp.tool()
async def update_event(
    calendarId: str,
    eventId: str,
    summary: str = None,
    description: str = None,
    start: str = None,
    end: str = None,
    attendees: list[str] = None,
    reminders: dict = None,
    location: str = None,
    transparency: str = "opaque",
):
    """
    Update an existing event.

    Args:
        calendarId (str): ID of the calendar (use 'primary' for the main calendar).
        eventId (str): ID of the event to update.
        summary (str, optional): New title for the event.
        description (str, optional): New description for the event.
        start (str, optional): New start time in 'YYYY-MM-DDTHH:MM:SS' format.
        end (str, optional): New end time in 'YYYY-MM-DDTHH:MM:SS' format.
        attendees (list[str], optional): Array of new attendee email addresses.
        reminders (dict, optional): New notification settings for the event.
        location (str, optional): New geographic location of the event.
        transparency (str, optional | default: "opaque"): 'opaque' or 'transparent'.
    """
    global db

    if calendarId != "primary":
        return {"error": "Calendar not found"}

    for i, event in enumerate(db):
        if event.get("id") == eventId:
            if summary is not None:
                event["summary"] = summary
            if description is not None:
                event["description"] = description
            if start is not None:
                event["start"] = start
            if end is not None:
                event["end"] = end
            if attendees is not None:
                event["attendees"] = attendees
            if reminders is not None:
                event["reminders"] = reminders
            if location is not None:
                event["location"] = location
            if transparency is not None:
                event["transparency"] = transparency
            event["updated"] = get_current_time_iso()
            db[i] = event
            save_db()
            return event
    return {"error": "Event not found"}


@mcp.tool()
async def delete_event(calendarId: str, eventId: str):
    """
    Delete an event from a calendar.

    Args:
        calendarId (str): ID of the calendar (use 'primary' for the main calendar).
        eventId (str): ID of the event to delete.
    """
    global db

    if calendarId != "primary":
        return {"error": "Calendar not found"}

    for i, event in enumerate(db):
        if event.get("id") == eventId:
            db.pop(i)
            save_db()
            return {"status": "deleted", "eventId": eventId}
    return {"error": "Event not found"}


@mcp.tool()
async def move_event(calendarId: str, eventId: str, destination: str):
    """
    Move an event from one calendar to another.

    Args:
        calendarId (str): ID of the source calendar.
        eventId (str): ID of the event to move.
        destination (str): ID of the destination calendar.
    """
    global db

    if calendarId != "primary":
        return {"error": "Source calendar not found"}

    if destination not in ["primary", "work", "personal"]:
        return {"error": "Destination calendar not found"}

    for i, event in enumerate(db):
        if event.get("id") == eventId:
            event["updated"] = get_current_time_iso()
            event["movedTo"] = destination
            db[i] = event
            save_db()
            return {
                "status": "moved",
                "eventId": eventId,
                "from": calendarId,
                "to": destination,
                "event": event,
            }
    return {"error": "Event not found"}


@mcp.tool()
async def import_event(
    calendarId: str,
    iCalUID: str,
    summary: str,
    start: str,
    end: str,
    description: str = None,
    attendees: list[str] = None,
    reminders: dict = None,
):
    """
    Import an event from a .ics file.

    Args:
        calendarId (str): ID of the calendar (use 'primary' for the main calendar).
        iCalUID (str): Unique ID for the event from the .ics file.
        summary (str): Title of the event.
        start (str): Start time in 'YYYY-MM-DDTHH:MM:SS' format.
        end (str): End time in 'YYYY-MM-DDTHH:MM:SS' format.
        description (str, optional): Description of the event.
        attendees (list[str], optional): Array of attendee email addresses.
        reminders (dict, optional): Notification settings for the event.
    """
    return None


@mcp.tool()
async def list_acl_rules(calendarId: str):
    """
    List the access control rules for a calendar.

    Args:
        calendarId (str): ID of the calendar (use 'primary' for the main calendar).
    """
    if calendarId not in acl_db:
        return {"error": f"Calendar '{calendarId}' not found"}

    return {"kind": "calendar#acl", "items": acl_db[calendarId]}


@mcp.tool()
async def create_acl_rule(calendarId: str, role: str, scope: dict):
    """
    Create a new access control rule to grant a user, group, or domain access to a calendar.

    Args:
        calendarId (str): ID of the calendar (use 'primary' for the main calendar).
        role (str): The level of access to grant ('none', 'freeBusyReader', 'reader', 'writer', 'owner').
        scope (dict): The scope of the rule, specifying who it applies to. Format: {"type": "user|group|domain|default", "value": "email@example.com"}.
    """
    valid_roles = ["none", "freeBusyReader", "reader", "writer", "owner"]
    if role not in valid_roles:
        return {"error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"}

    valid_scope_types = ["user", "group", "domain", "default"]
    if not isinstance(scope, dict) or "type" not in scope:
        return {"error": "Scope must be a dict with 'type' field"}
    if scope["type"] not in valid_scope_types:
        return {
            "error": f"Invalid scope type. Must be one of: {', '.join(valid_scope_types)}"
        }

    if calendarId not in acl_db:
        acl_db[calendarId] = []

    rule_id = str(uuid.uuid4())

    acl_rule = {
        "kind": "calendar#aclRule",
        "id": rule_id,
        "scope": scope,
        "role": role,
        "etag": f'"{rule_id}"',
    }

    acl_db[calendarId].append(acl_rule)

    save_acl_db()

    return acl_rule


@mcp.tool()
async def update_acl_rule(calendarId: str, ruleId: str, role: str):
    """
    Update an existing access control rule to change the role of a user, group, or domain.

    Args:
        calendarId (str): ID of the calendar (use 'primary' for the main calendar).
        ruleId (str): The ID of the rule to update.
        role (str): The new level of access to grant ('none', 'freeBusyReader', 'reader', 'writer', 'owner').
    """
    valid_roles = ["none", "freeBusyReader", "reader", "writer", "owner"]
    if role not in valid_roles:
        return {"error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"}

    if calendarId not in acl_db:
        return {"error": f"Calendar '{calendarId}' not found"}

    for rule in acl_db[calendarId]:
        if rule["id"] == ruleId:
            rule["role"] = role
            rule["etag"] = f'"{ruleId}-updated"'

            save_acl_db()

            return rule

    return {"error": f"ACL rule '{ruleId}' not found in calendar '{calendarId}'"}


@mcp.tool()
async def delete_acl_rule(calendarId: str, ruleId: str):
    """
    Delete an access control rule to revoke access from a user, group, or domain.

    Args:
        calendarId (str): ID of the calendar (use 'primary' for the main calendar).
        ruleId (str): The ID of the rule to delete.
    """
    if calendarId not in acl_db:
        return {"error": f"Calendar '{calendarId}' not found"}

    initial_count = len(acl_db[calendarId])
    acl_db[calendarId] = [rule for rule in acl_db[calendarId] if rule["id"] != ruleId]

    if len(acl_db[calendarId]) == initial_count:
        return {"error": f"ACL rule '{ruleId}' not found in calendar '{calendarId}'"}

    save_acl_db()

    return {
        "success": True,
        "message": f"ACL rule '{ruleId}' deleted from calendar '{calendarId}'",
    }


@mcp.tool()
async def get_free_busy(timeMin: str, timeMax: str, items: list[dict]):
    """
    Get the free/busy status for a set of calendars.

    Args:
        timeMin (str): Start time for the query in 'YYYY-MM-DDTHH:MM:SSZ' format.
        timeMax (str): End time for the query in 'YYYY-MM-DDTHH:MM:SSZ' format.
        items (list[dict]): List of calendars to check for free/busy information. Each item must have an 'id' field.
    """

    results = {}
    for item in items:
        cal_id = item.get("id")
        if cal_id != "primary":
            results[cal_id] = {"busy": []}
            continue
        busy_blocks = []
        for event in db:
            start = event.get("start")
            end = event.get("end")
            if not start or not end:
                continue

            if (timeMax and start >= timeMax) or (timeMin and end <= timeMin):
                continue
            busy_blocks.append({"start": start, "end": end})
        results[cal_id] = {"busy": busy_blocks}
    return {
        "kind": "calendar#freeBusy",
        "timeMin": timeMin,
        "timeMax": timeMax,
        "calendars": results,
    }


@mcp.tool()
async def get_settings():
    """
    Get the user's calendar settings, such as timezone, date/time format, and default event length.
    """
    return {
        "kind": "calendar#settings",
        "etag": '"settings_v1"',
        "items": [
            {
                "id": "timezone",
                "value": "Asia/Singapore",
                "type": "string",
                "default": True,
            },
            {"id": "format24Hour", "value": True, "type": "boolean", "default": False},
            {
                "id": "defaultEventDuration",
                "value": 60,
                "type": "integer",
                "default": True,
            },
            {
                "id": "reminderMethod",
                "value": "popup",
                "type": "string",
                "default": True,
            },
            {"id": "weekStart", "value": "monday", "type": "string", "default": True},
        ],
    }


def get_current_time_iso():
    global _server_start_time
    if _server_start_time is None:
        return START_TIME.isoformat()
    elapsed = datetime.now() - _server_start_time
    current_time = START_TIME + elapsed
    return current_time.isoformat()


@mcp.tool()
async def get_current_time():
    """
    Get current time in the primary Google Calendar's timezone.
    """
    return {"current_time": get_current_time_iso()}


def main():
    global db_path, acl_db_path, db, acl_db, _server_start_time
    _server_start_time = datetime.now()

    if len(sys.argv) < 3:
        raise ValueError(
            "Expected 2 path arguments: \{calendar\}_events.json and \{calendar\}_acl.json"
        )

    db_path = sys.argv[1]
    acl_db_path = sys.argv[2]

    try:
        with open(db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
        if not isinstance(db, list):
            db = []
    except Exception:
        db = []

    try:
        with open(acl_db_path, "r", encoding="utf-8") as file:
            acl_db = json.load(file)
    except FileNotFoundError:
        acl_db = {"primary": []}
        with open(acl_db_path, "w") as file:
            json.dump(acl_db, file, indent=2)

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
