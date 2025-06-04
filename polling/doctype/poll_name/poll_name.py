# Copyright (c) 2025, amol and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

# In Poll Name DocType > Server Script (API Event)
# Ensure this script name is unique, e.g., 'cast_vote_method'

class PollName(Document): # <-- This is the missing part
    # Any DocType specific logic can go here.
    # For now, we just need the class to exist.
    pass

@frappe.whitelist(allow_guest=True) # Allow guests to call this method if poll allows guest voting
def cast_vote(poll_name, selected_option_docname):
    # 1. Fetch Poll and Option
    try:
        poll = frappe.get_doc("Poll Name", poll_name)
    except frappe.DoesNotExistError:
        frappe.throw("Poll not found.")

    # Check if poll is open
    if poll.status != "Open":
        frappe.throw("This poll is closed for voting.")

    # Find the selected option by its document name (name field)
    selected_option = None
    for option in poll.poll_options: # Use poll_options field from your DocType
        if option.name == selected_option_docname:
            selected_option = option
            break

    if not selected_option:
        frappe.throw("Selected option not found for this poll.")

    # 2. Check for Duplicate Votes
    current_user = frappe.session.user
    ip_address = frappe.get_request_header("X-Forwarded-For") or frappe.get_request_header("Remote-Addr")

    if not ip_address:
        frappe.throw("Could not determine your IP address for voting.")

    if current_user != "Guest":
        # Check for logged-in user's vote
        existing_vote = frappe.db.exists(
            "Poll Vote",
            {"poll_name": poll_name, "user": current_user}
        )
        if existing_vote:
            frappe.throw("You have already voted in this poll.")
    else:
        # Check if guest voting is allowed for this specific poll
        if not poll.allow_guest_to_vote: # Use your field name: allow_guest_to_vote
            frappe.throw("Guest voting is not allowed for this poll. Please log in to vote.")

        # Check for guest's vote by IP address
        existing_vote = frappe.db.exists(
            "Poll Vote",
            {"poll_name": poll_name, "voter_ip_address": ip_address}
        )
        if existing_vote:
            frappe.throw("You have already voted in this poll from this IP address.")

    # 3. Increment Vote Count and Create Poll Vote Record
    try:
        # Increment vote count on the selected Poll Option (child document)
        selected_option.votes = (selected_option.votes or 0) + 1
        poll.save() # Saves the parent and child table

        # Create new Poll Vote record
        vote_doc = frappe.new_doc("Poll Vote")
        vote_doc.poll_name = poll_name
        vote_doc.option = selected_option.option # Store the actual option text
        vote_doc.user = current_user if current_user != "Guest" else None
        vote_doc.voter_ip_address = ip_address if current_user == "Guest" else None # Add this field to Poll Vote DocType
        vote_doc.insert(ignore_permissions=True) # Insert, ignoring permissions if needed for guest votes

        frappe.db.commit() # Commit transaction

        return "Your vote has been recorded!"

    except Exception as e:
        frappe.db.rollback() # Rollback if any error occurs
        frappe.throw(f"An error occurred while casting your vote: {e}")
