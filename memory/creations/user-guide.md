# Dashboard User Guide

## Overview
This dashboard allows you to:
- Submit requests for approval
- Chat with others in real-time
- Approve or deny pending requests

## Features

### Chat Interface
- Type your message in the input field and click "Send" to broadcast to all users.

### Request Submission
- Enter your request in the textarea and click "Submit" to add it to the pending requests list.

### Pending Requests
- View all pending requests in the list.
- Click "Approve" or "Deny" to update the status of a request.

## How to Use

1. **Chat**:
   - Type your message and click "Send". Messages will appear in the chat window and be broadcast to all connected users.

2. **Submit a Request**:
   - Enter your request in the textarea and click "Submit". The request will appear in the pending requests list with "Pending" status.

3. **Approve/Deny Requests**:
   - Click "Approve" or "Deny" next to a pending request. The status will update, and all users will see the change.

## Notes
- All requests and chat messages are stored in a local SQLite database.
- The dashboard is built with Flask and Socket.IO for real-time communication.
- Rate limiting is in place to prevent abuse of the system.

For any issues or further assistance, please contact the administrator.
