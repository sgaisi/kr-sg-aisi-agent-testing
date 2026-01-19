import json
import mimetypes
import os
import secrets
import sys
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from time import sleep
from typing import Literal, Any
from pathlib import Path

mcp = FastMCP("gmail")

# NOTE: Hardcoded start time: 2025/11/21 09:12:51 AM
START_TIME_STR = "2025-11-21 09:12:51"
START_TIME = datetime.strptime(START_TIME_STR, "%Y-%m-%d %H:%M:%S")

_server_start_time = None


def get_current_time():
    if _server_start_time is None:
        return START_TIME
    elapsed = datetime.now() - _server_start_time
    current_time = START_TIME + elapsed
    return current_time


# LABEL STRINGS
LABELS = "labels"
SENT = "SENT"
DRAFT = "DRAFT"
INBOX = "INBOX"
SPAM = "SPAM"
TRASH = "TRASH"
UNREAD = "UNREAD"
STARRED = "STARRED"
IMPORTANT = "IMPORTANT"
PERSONAL = "CATEGORY_PERSONAL"
SOCIAL = "CATEGORY_SOCIAL"
PROMOTIONS = "CATEGORY_PROMOTIONS"
UPDATES = "CATEGORY_UPDATES"
FORUMS = "CATEGORY_FORUMS"

# EMAIL STRINGS
ID = "id"
USER = "me"
TIMESTAMP = "timestamp"
EMAIL_ARGS = "email_args"
FROM = "from"
TO = "to"
SUBJECT = "subject"
BODY = "body"
HTML_BODY = "html_body"
MIME_TYPE = "mime_type"
CC = "cc"
BCC = "bcc"
THREAD_ID = "thread_id"
IN_REPLY_TO = "in_reply_to"
ATTACHMENTS = "attachments"

# LABEL INFO STRINGS
NAME = "name"
TYPE = "type"
SYSTEM_TYPE = "system"
USER_TYPE = "user"
MESSAGE_VISIBILITY = "messageListVisibility"
MESSAGE_SHOW = "show"
MESSAGE_HIDE = "hide"
LABEL_VISIBILITY = "labelListVisibility"
LABEL_SHOW = "labelShow"
LABEL_SHOW_IF_UNREAD = "labelShowIfUnread"
LABEL_HIDE = "labelHide"


def setup_timestamps(timestamp_str: str):
    timestamp_format = "%Y-%m-%d %H:%M:%S.%f"
    return datetime.strptime(timestamp_str, timestamp_format)


def load_gmail_database(db_path) -> dict:
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"ERROR: Database file not found at '{db_path}'.")

    try:
        with open(db_path, "r", encoding="utf-8") as f:
            mock_gmail_db = json.load(f)

        if not isinstance(mock_gmail_db, dict):
            raise TypeError("ERROR: Database content is not a dictionary.")

        for mail in mock_gmail_db.values():
            if TIMESTAMP not in mail:
                raise Exception(
                    f"ERROR: Mail object {mail.get('id', 'N/A')} has no {TIMESTAMP} field."
                )
            mail[TIMESTAMP] = setup_timestamps(mail[TIMESTAMP])

            if LABELS not in mail:
                raise Exception(
                    f"ERROR: Mail object {mail.get('id', 'N/A')} has no {LABELS} field."
                )
            mail[LABELS] = set(mail[LABELS])

        return mock_gmail_db

    except json.JSONDecodeError as e:
        raise ValueError(
            f"ERROR: Database file at '{db_path}' contains malformed JSON. Details: {e}"
        )

    except Exception as e:
        raise RuntimeError(
            f"ERROR: An unexpected error occurred while loading the database: {e}"
        )


# Database with records indexed by id (str)
# Each record contains id, labels (sent, drafts, inbox, unread), timestamp, and email_args
DEFAULT_DB_PATH = "experiment_data/mock_gmail_db/1_1_emails.json"
GMAIL_DATABASE = load_gmail_database(DEFAULT_DB_PATH)

LABELS_USER = set()
LABELS_LOWERCASE_NAMES_USER = set()
LABELS_EXCLUSIVE = {INBOX, SPAM, TRASH}
LABELS_MODIFIABLE = {
    UNREAD,
    STARRED,
    IMPORTANT,
    PERSONAL,
    SOCIAL,
    PROMOTIONS,
    UPDATES,
    FORUMS,
}
LABELS_UNMODIFIABLE = {SENT, DRAFT}
LABELS_SYSTEM = LABELS_EXCLUSIVE.union(LABELS_MODIFIABLE).union(LABELS_UNMODIFIABLE)
LABELS_DICT = {
    INBOX: {
        ID: INBOX,
        NAME: INBOX,
        TYPE: SYSTEM_TYPE,
        MESSAGE_VISIBILITY: MESSAGE_SHOW,
        LABEL_VISIBILITY: LABEL_SHOW,
    },
    SPAM: {
        ID: SPAM,
        NAME: SPAM,
        TYPE: SYSTEM_TYPE,
        MESSAGE_VISIBILITY: MESSAGE_HIDE,
        LABEL_VISIBILITY: LABEL_SHOW,
    },
    TRASH: {
        ID: TRASH,
        NAME: TRASH,
        TYPE: SYSTEM_TYPE,
        MESSAGE_VISIBILITY: MESSAGE_HIDE,
        LABEL_VISIBILITY: LABEL_SHOW,
    },
    SENT: {
        ID: SENT,
        NAME: SENT,
        TYPE: SYSTEM_TYPE,
        MESSAGE_VISIBILITY: MESSAGE_SHOW,
        LABEL_VISIBILITY: LABEL_SHOW,
    },
    DRAFT: {
        ID: DRAFT,
        NAME: DRAFT,
        TYPE: SYSTEM_TYPE,
        MESSAGE_VISIBILITY: MESSAGE_SHOW,
        LABEL_VISIBILITY: LABEL_SHOW,
    },
    STARRED: {
        ID: STARRED,
        NAME: STARRED,
        TYPE: SYSTEM_TYPE,
        MESSAGE_VISIBILITY: MESSAGE_SHOW,
        LABEL_VISIBILITY: LABEL_SHOW,
    },
    IMPORTANT: {
        ID: IMPORTANT,
        NAME: IMPORTANT,
        TYPE: SYSTEM_TYPE,
        MESSAGE_VISIBILITY: MESSAGE_SHOW,
        LABEL_VISIBILITY: LABEL_HIDE,
    },
    UNREAD: {
        ID: UNREAD,
        NAME: UNREAD,
        TYPE: SYSTEM_TYPE,
        MESSAGE_VISIBILITY: MESSAGE_SHOW,
        LABEL_VISIBILITY: LABEL_HIDE,
    },
    PERSONAL: {
        ID: PERSONAL,
        NAME: PERSONAL,
        TYPE: SYSTEM_TYPE,
        MESSAGE_VISIBILITY: MESSAGE_SHOW,
        LABEL_VISIBILITY: LABEL_SHOW,
    },
    SOCIAL: {
        ID: SOCIAL,
        NAME: SOCIAL,
        TYPE: SYSTEM_TYPE,
        MESSAGE_VISIBILITY: MESSAGE_HIDE,
        LABEL_VISIBILITY: LABEL_HIDE,
    },
    PROMOTIONS: {
        ID: PROMOTIONS,
        NAME: PROMOTIONS,
        TYPE: SYSTEM_TYPE,
        MESSAGE_VISIBILITY: MESSAGE_HIDE,
        LABEL_VISIBILITY: LABEL_HIDE,
    },
    UPDATES: {
        ID: UPDATES,
        NAME: UPDATES,
        TYPE: SYSTEM_TYPE,
        MESSAGE_VISIBILITY: MESSAGE_HIDE,
        LABEL_VISIBILITY: LABEL_HIDE,
    },
    FORUMS: {
        ID: FORUMS,
        NAME: FORUMS,
        TYPE: SYSTEM_TYPE,
        MESSAGE_VISIBILITY: MESSAGE_HIDE,
        LABEL_VISIBILITY: LABEL_HIDE,
    },
}


def generate_id(length: int) -> str:
    possible_chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "".join(secrets.choice(possible_chars) for _ in range(length))


def generate_message_id() -> str:
    return generate_id(13)


def generate_attachment_id() -> str:
    return generate_id(11) + "-" + generate_id(11) + "_" + generate_id(11)


def retrieve_email(message_id):
    if not GMAIL_DATABASE.get(message_id):
        raise Exception(f"No email found with ID: {message_id}")
    else:
        return GMAIL_DATABASE[message_id]


def handle_email_action(
    folder: Literal["SENT", "DRAFT"], email_args: dict[str, Any]
) -> str:
    """
    Handles sending or drafting an email using the Gmail API, supporting attachments.

    Args:
        folder: "SENT" or "DRAFT".
        email_args: Dictionary containing email data, including optional 'attachments' and 'thread_id'.
        return: A string representing the result.
    """
    if email_args.get(ATTACHMENTS) and len(email_args[ATTACHMENTS]) > 0:
        email_args[ATTACHMENTS] = {
            generate_attachment_id(): path_str for path_str in email_args[ATTACHMENTS]
        }
        sleep(0.02)

    email_id = generate_message_id()

    new_record = {
        ID: email_id,
        LABELS: {folder},
        TIMESTAMP: get_current_time(),
        EMAIL_ARGS: email_args,
    }

    GMAIL_DATABASE[email_id] = new_record

    if folder == SENT:
        return f"Email sent successfully with ID: {email_id}"
    elif folder == DRAFT:
        return f"Email draft created successfully with ID: {email_id}"


@mcp.tool()
async def send_email(
    to: list[str],
    subject: str,
    body: str,
    html_body: str | None = None,
    mime_type: Literal[
        "text/plain", "text/html", "multipart/alternative"
    ] = "text/plain",
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    in_reply_to: str | None = None,
    attachments: list[str] | None = None,
) -> str:
    """Sends a new email

    Args:
        to: List of recipient email addresses
        subject: Email subject
        body: Email body content (used for text/plain or when html_body not provided)
        html_body: HTML version of the email body
        mime_type: Email content type
        cc: List of CC recipients
        bcc: List of BCC recipients
        in_reply_to: Message ID being replied to
        attachments: List of file paths to attach to the email
    """
    email_args = {
        FROM: USER,
        TO: to,
        SUBJECT: subject,
        BODY: body,
        HTML_BODY: html_body,
        MIME_TYPE: mime_type,
        CC: cc,
        BCC: bcc,
        IN_REPLY_TO: in_reply_to,
        ATTACHMENTS: attachments,
    }
    return handle_email_action(SENT, email_args)


@mcp.tool()
async def draft_email(
    to: list[str],
    subject: str,
    body: str,
    html_body: str | None = None,
    mime_type: Literal[
        "text/plain", "text/html", "multipart/alternative"
    ] = "text/plain",
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    in_reply_to: str | None = None,
    attachments: list[str] | None = None,
) -> str:
    """Drafts a new email

    Args:
        to: List of recipient email addresses
        subject: Email subject
        body: Email body content (used for text/plain or when html_body not provided)
        html_body: HTML version of the email body
        mime_type: Email content type
        cc: List of CC recipients
        bcc: List of BCC recipients
        in_reply_to: Message ID being replied to
        attachments: List of file paths to attach to the email
    """
    email_args = {
        FROM: USER,
        TO: to,
        SUBJECT: subject,
        BODY: body,
        HTML_BODY: html_body,
        MIME_TYPE: mime_type,
        CC: cc,
        BCC: bcc,
        IN_REPLY_TO: in_reply_to,
        ATTACHMENTS: attachments,
    }
    return handle_email_action(DRAFT, email_args)


def get_file_info(id: str, path_str: str):
    """Extracts filename, and guesses MIME type from the filename."""
    filename = Path(path_str).name
    mime_type, _ = mimetypes.guess_type(filename, False)
    return f"- {filename} ({mime_type}, ID: {id})"


def get_readable_timestamp(timestamp: float) -> str:
    return timestamp.strftime("%a, %d %b %Y %H:%M:%S")  # timezone (%z) omitted


def read_email_helper(message_id: str) -> str:
    email = retrieve_email(message_id)
    email_args = email[EMAIL_ARGS]
    timestamp = email[TIMESTAMP]
    subject = email_args[SUBJECT]
    from_header = email_args[FROM]
    to_header = email_args[TO]
    text_content = email_args[BODY]
    html_content = email_args[HTML_BODY]

    date_header = get_readable_timestamp(timestamp)

    body = text_content or html_content or ""

    content_type_note = ""
    if not text_content and html_content:
        content_type_note = "[Note: This email is HTML-formatted. Plain text version not available.]\n\n"

    attachments = email_args[ATTACHMENTS]
    attachment_info = ""
    if attachments:
        attachment_info = f"\n\nAttachments ({len(attachments)}):\n" + "\n".join(
            get_file_info(id, path_str) for id, path_str in attachments.items()
        )

    final_text = (
        f"Subject: {subject}\n"
        f"From: {from_header}\n"
        f"To: {to_header}\n"
        f"Date: {date_header}\n\n"
        f"{content_type_note}{body}{attachment_info}"
    )

    return final_text


@mcp.tool()
async def read_email(message_id: str) -> str:
    """Retrieves the content of a specific email

    Args:
        message_id: ID of the email message to retrieve
    """
    return read_email_helper(message_id)


@mcp.tool()
async def download_attachment(
    message_id: str, attachment_id: str, filename: str = None, save_path: str = None
) -> str:
    """Downloads an email attachment to a specified location

    Args:
        message_id: ID of the email message containing the attachment
        attachment_id: ID of the attachment to download
        filename: Filename to save the attachment as (if not provided, uses original filename)
        save_path: Directory path to save the attachment (defaults to current directory)
    """
    try:
        email = retrieve_email(message_id)

        if not email[EMAIL_ARGS][ATTACHMENTS] or not email[EMAIL_ARGS][ATTACHMENTS].get(
            attachment_id
        ):
            raise Exception("No attachment data received")

        if not filename:
            filename = email[EMAIL_ARGS][ATTACHMENTS][attachment_id]

        if not save_path:
            save_path = "."

        return (
            "Attachment downloaded successfully:\n"
            f"File: {filename}\n"
            f"Saved to: {save_path}"
        )

    except Exception as e:
        raise Exception(f"Failed to download attachment: {str(e)}")


def is_timestamp_after_date(date_string, timestamp):
    formats_to_try = ["%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]
    date = None

    for date_format in formats_to_try:
        try:
            date = datetime.strptime(date_string, date_format)
            break
        except ValueError:
            continue

    if date is None:
        raise ValueError(
            f"Date string '{date_string}' does not match expected formats."
        )

    if date.date() <= timestamp.date():
        return True
    else:
        return False


def search_emails_helper(query: str, max_results: int):
    terms = [t.strip().lower() for t in query.split()]
    matching_emails = []

    for email in GMAIL_DATABASE.values():
        if len(matching_emails) >= max_results:
            break

        match = True

        email_args = email[EMAIL_ARGS]
        email_content = (
            f"{email_args[SUBJECT]} {email_args[FROM]} "
            f"{email_args[TO]} {email_args[BODY]}"
        ).lower()
        email_labels = {label.lower() for label in email[LABELS]}

        for term in terms:
            if term.startswith("from:"):
                from_addr = term.replace("from:", "")
                if from_addr not in email_args[FROM].lower():
                    match = False
                    break
            elif term.startswith("to:"):
                to_addr = term.replace("to:", "")
                if not any(to_addr in email.lower() for email in email_args[TO]):
                    match = False
                    break
            elif term.startswith("subject:"):
                subject = term.replace("subject:", "")
                if subject not in email_args[SUBJECT].lower():
                    match = False
                    break
            elif term.startswith("after:"):
                date = term.replace("after:", "")
                if not is_timestamp_after_date(date, email[TIMESTAMP]):
                    match = False
                    break
            elif term.startswith("before:"):
                date = term.replace("before:", "")
                if is_timestamp_after_date(date, email[TIMESTAMP]):
                    match = False
                    break
            elif term.startswith("in:") or term.startswith("label:"):
                label = term.replace("in:", "").replace("label:", "")
                if label not in email_labels:
                    match = False
                    break
            elif term.startswith("is:"):
                status = term.replace("is:", "")
                if (
                    (status == "unread")
                    != ("unread" in email_labels)  # Unread mismatch
                    or (status == "important" and "important" not in email_labels)
                    or (status == "starred" and "starred" not in email_labels)
                ):
                    match = False
                    break
            elif term == "has:attachment":
                if not email_args[ATTACHMENTS]:
                    match = False
                    break
            elif (
                term not in email_content
            ):  # Simple keyword search in subject/from/to/body fields
                match = False
                break

        if match:
            matching_emails.append(email)

    if not matching_emails:
        return "No emails found matching the criteria."

    formatted_results = "\n".join(
        f"ID: {email[ID]}\n"
        f"Subject: {email[EMAIL_ARGS][SUBJECT]}\n"
        f"From: {email[EMAIL_ARGS][FROM]}\n"
        f"Date: {email[TIMESTAMP].strftime('%a, %d %b %Y')}\n"
        for email in matching_emails
    )

    return formatted_results


@mcp.tool()
async def search_emails(query: str, max_results: int = 10) -> str:
    """Searches for emails using Gmail search syntax

    Args:
        query: Gmail search query (e.g., 'from:example@gmail.com')
        max_results: Maximum number of results to return
    """
    return search_emails_helper(query, max_results)


def add_label(email: dict, label: str):
    email[LABELS].add(label)


def remove_label(email: dict, label: str):
    email[LABELS].discard(label)


@mcp.tool()
async def modify_email(
    message_id: str, add_label_ids: list[str] = None, remove_label_ids: list[str] = None
) -> str:
    """Modifies email labels (move to different folders)

    Args:
        message_id: ID of the email message to modify
        add_label_ids: List of label IDs to add to the message
        remove_label_ids: List of label IDs to remove from the message
    """
    email = retrieve_email(message_id)

    if add_label_ids:
        for label in add_label_ids:
            if label in LABELS_UNMODIFIABLE:
                raise Exception(f"Invalid label: {label}")
            elif label in LABELS_DICT.keys():
                add_label(email, label)
            else:
                raise Exception(f'Label with ID "{label}" not found.')

        # Maintain Exclusivity of SPAM > TRASH > INBOX
        if SPAM in add_label_ids:
            remove_label(email, TRASH)
            remove_label(email, INBOX)
        elif TRASH in add_label_ids:
            remove_label(email, SPAM)
            remove_label(email, INBOX)
        elif INBOX in add_label_ids:
            remove_label(email, SPAM)
            remove_label(email, TRASH)

    if remove_label_ids:
        for label in remove_label_ids:
            if label in LABELS_UNMODIFIABLE:
                raise Exception(f"Invalid label: {label}")
            elif label in LABELS_DICT.keys():
                remove_label(email, label)
            else:
                raise Exception(f'Label with ID "{label}" not found.')

    return f"Email {message_id} labels updated successfully"


@mcp.tool()
async def delete_email(message_id: str) -> str:
    """Permanently deletes an email

    Args:
        message_id: ID of the email message to delete
    """
    if GMAIL_DATABASE.pop(message_id, ""):
        return "Email deleted."
    else:
        return "Email not found."


@mcp.tool()
async def list_email_labels() -> str:
    """Retrieves all available Gmail labels"""

    def id_name_joiner(labels):
        return "\n\n".join(
            f"ID: {LABELS_DICT[label][ID]}\nName: {LABELS_DICT[label][NAME]}"
            for label in labels
        )

    return (
        f"Found {len(LABELS_USER) + len(LABELS_SYSTEM)} labels "
        f"({len(LABELS_SYSTEM)} system, {len(LABELS_USER)} user):\n\n"
        f"System Labels:\n{id_name_joiner(LABELS_SYSTEM)}\n\n"
        f"User Labels:\n{id_name_joiner(LABELS_USER)}"
    )


def generate_label_id() -> str:
    return "Label_" + generate_id(5)


@mcp.tool()
async def create_label(
    name: str,
    messageListVisibility: Literal["show", "hide"] = MESSAGE_SHOW,
    labelListVisibility: Literal[
        "labelShow", "labelShowIfUnread", "labelHide"
    ] = LABEL_SHOW,
) -> str:
    """Creates a new Gmail label

    Args:
        name: Name for the new label
        messageListVisibility: Whether to show or hide the label in the message list
        labelListVisibility: Visibility of the label in the label list
    """
    if name.upper() in LABELS_SYSTEM or name.lower() in LABELS_LOWERCASE_NAMES_USER:
        return f'Label "{name}" already exists. Please use a different name.'

    label_id = generate_label_id()
    while LABELS_DICT.get(label_id):
        label_id = generate_label_id()

    LABELS_DICT[label_id] = {
        ID: label_id,
        NAME: name,
        TYPE: USER_TYPE,
        MESSAGE_VISIBILITY: messageListVisibility,
        LABEL_VISIBILITY: labelListVisibility,
    }
    LABELS_USER.add(label_id)
    LABELS_LOWERCASE_NAMES_USER.add(name.lower())

    return (
        f"Label created successfully:\nID: {label_id}\nName: {name}\nType: {USER_TYPE}"
    )


def main():
    global GMAIL_DATABASE, _server_start_time
    _server_start_time = datetime.now()

    if len(sys.argv) < 2:
        raise ValueError("ERROR: No database path provided as command-line argument.")

    db_path = os.path.abspath(sys.argv[1])

    print(f"Loading Gmail database from: {db_path}", file=sys.stderr)
    GMAIL_DATABASE = load_gmail_database(db_path)
    print(f"Loaded {len(GMAIL_DATABASE)} email(s) from database", file=sys.stderr)

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
