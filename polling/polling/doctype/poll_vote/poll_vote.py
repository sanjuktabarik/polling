# polling/polling/doctype/poll_vote/poll_vote.py

import frappe
import json
from frappe.model.document import Document

class PollVote(Document):
    pass

@frappe.whitelist()
def submit_or_update_poll_vote(poll_name, selections):
    # Ensure selections is a list of dicts, not a JSON string
    if isinstance(selections, str):
        try:
            selections = json.loads(selections)
        except json.JSONDecodeError:
            frappe.throw("Invalid selections data format.")

    if not isinstance(selections, list):
        frappe.throw("Selections should be a list of options with reasons.")

    current_user = frappe.session.user

    # Delete existing votes by this user for this poll
    frappe.db.delete("Poll Vote", {
        "user": current_user,
        "poll_name": poll_name
    })

    # Insert new votes
    for selection in selections:
        if not isinstance(selection, dict):
            continue  # skip if selection is not a dict (safety)

        option = selection.get("option")
        reason = selection.get("reason", "")

        if option:
            vote_doc = frappe.new_doc("Poll Vote")
            vote_doc.user = current_user
            vote_doc.poll_name = poll_name
            vote_doc.option = option
            vote_doc.reason = reason
            vote_doc.insert(ignore_permissions=True)

    frappe.db.commit()

    return "Your vote has been successfully submitted!"

