#!/usr/bin/env python3
"""
Hotel Staff Notification MCP Server
호텔 직원 호출 알림 서버

This MCP server provides tools for the AI to notify hotel staff
when guests need human assistance.

Usage:
    uvx mcp run hotel_staff_notification.py
    or
    python hotel_staff_notification.py
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

# Try to import mcp, fall back to simple mode if not available
try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Configuration
NOTIFICATION_LOG_FILE = Path("hotel_notifications.json")
NOTIFICATION_SOUND_ENABLED = True


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()


def load_notifications() -> list:
    """Load existing notifications from file."""
    if NOTIFICATION_LOG_FILE.exists():
        try:
            with open(NOTIFICATION_LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_notification(notification: dict) -> None:
    """Save notification to file."""
    notifications = load_notifications()
    notifications.append(notification)

    # Keep only last 1000 notifications
    if len(notifications) > 1000:
        notifications = notifications[-1000:]

    with open(NOTIFICATION_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(notifications, f, ensure_ascii=False, indent=2)


def play_notification_sound(priority: str = "normal") -> None:
    """Play notification sound (Windows only for now)."""
    if not NOTIFICATION_SOUND_ENABLED:
        return

    try:
        import winsound
        if priority == "urgent":
            # Play urgent sound (3 beeps)
            for _ in range(3):
                winsound.Beep(1000, 200)
                winsound.Beep(1500, 200)
        else:
            # Play normal sound (1 beep)
            winsound.Beep(800, 300)
    except (ImportError, RuntimeError):
        # Not on Windows or sound not available
        pass


def notify_staff(
    reason: str,
    guest_language: str = "Korean",
    priority: str = "normal",
    location: str = "Front Desk Kiosk",
    additional_info: str = ""
) -> dict:
    """
    Notify hotel staff that a guest needs assistance.

    Args:
        reason: Why staff is needed (e.g., "Check-in", "Complaint", "Payment")
        guest_language: Language the guest is speaking
        priority: "normal", "high", or "urgent"
        location: Where the guest is located
        additional_info: Any additional context

    Returns:
        Notification confirmation with ticket number
    """
    # Generate ticket number
    ticket_number = f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    notification = {
        "ticket_number": ticket_number,
        "timestamp": get_timestamp(),
        "reason": reason,
        "guest_language": guest_language,
        "priority": priority,
        "location": location,
        "additional_info": additional_info,
        "status": "pending"
    }

    # Save notification
    save_notification(notification)

    # Play sound
    play_notification_sound(priority)

    # Print to console (for monitoring)
    print(f"\n{'='*60}")
    print(f"🔔 STAFF NOTIFICATION - {priority.upper()}")
    print(f"{'='*60}")
    print(f"Ticket: {ticket_number}")
    print(f"Time: {notification['timestamp']}")
    print(f"Reason: {reason}")
    print(f"Language: {guest_language}")
    print(f"Location: {location}")
    if additional_info:
        print(f"Info: {additional_info}")
    print(f"{'='*60}\n")

    return {
        "success": True,
        "ticket_number": ticket_number,
        "message": f"Staff has been notified. Ticket number: {ticket_number}",
        "estimated_response_time": "2-3 minutes" if priority != "urgent" else "1 minute"
    }


def get_pending_notifications() -> list:
    """Get all pending notifications."""
    notifications = load_notifications()
    return [n for n in notifications if n.get("status") == "pending"]


def mark_notification_resolved(ticket_number: str) -> dict:
    """Mark a notification as resolved."""
    notifications = load_notifications()

    for notification in notifications:
        if notification.get("ticket_number") == ticket_number:
            notification["status"] = "resolved"
            notification["resolved_at"] = get_timestamp()

            with open(NOTIFICATION_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(notifications, f, ensure_ascii=False, indent=2)

            return {"success": True, "message": f"Ticket {ticket_number} marked as resolved"}

    return {"success": False, "message": f"Ticket {ticket_number} not found"}


# MCP Server Setup
if MCP_AVAILABLE:
    mcp = FastMCP("Hotel Staff Notification")

    @mcp.tool()
    def call_staff(
        reason: str,
        guest_language: str = "Korean",
        priority: str = "normal",
        additional_info: str = ""
    ) -> str:
        """
        Call hotel staff for guest assistance.
        Use this when a guest needs human help with:
        - Check-in/Check-out processing
        - Payment issues
        - Reservation changes
        - Complaints or concerns
        - Lost items
        - Medical emergencies

        Args:
            reason: Why staff is needed (e.g., "Guest wants to check in", "Payment question")
            guest_language: Language the guest is speaking (Korean, English, Japanese, Chinese)
            priority: "normal", "high", or "urgent" (use urgent for emergencies)
            additional_info: Any additional context to help staff

        Returns:
            Confirmation message with ticket number
        """
        result = notify_staff(
            reason=reason,
            guest_language=guest_language,
            priority=priority,
            additional_info=additional_info
        )
        return json.dumps(result, ensure_ascii=False)

    @mcp.tool()
    def get_staff_status() -> str:
        """
        Check if there are pending staff notifications.

        Returns:
            Count of pending notifications
        """
        pending = get_pending_notifications()
        return json.dumps({
            "pending_count": len(pending),
            "pending_tickets": [n.get("ticket_number") for n in pending[-5:]]
        })


def main():
    """Main entry point."""
    if MCP_AVAILABLE:
        print("Starting Hotel Staff Notification MCP Server...")
        mcp.run()
    else:
        print("MCP not available. Running in standalone mode.")
        print("Testing notification...")
        result = notify_staff(
            reason="Test notification",
            guest_language="Korean",
            priority="normal",
            additional_info="This is a test"
        )
        print(f"Result: {result}")


if __name__ == "__main__":
    main()
