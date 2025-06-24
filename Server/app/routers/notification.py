from fastapi import APIRouter, HTTPException
from app.models.notification import Notification
from typing import List
from datetime import datetime
from beanie import PydanticObjectId

router = APIRouter()

# Get all notifications for an employee
@router.get("/{employee_id}", response_model=List[dict])
async def get_notifications(employee_id: str):
    notifications = await Notification.find(Notification.user_id == employee_id).to_list()
    if not notifications:
        raise HTTPException(status_code=404, detail="No notifications found")
    
    return [
        {
            "id": str(n.id),
            "message": n.message,
            "seen": n.seen,
            "created_at": n.created_at
        }
        for n in notifications
    ]

# Mark a specific notification as seen
@router.patch("/{notification_id}/seen")
async def mark_as_seen(notification_id: str):
    notification = await Notification.get(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    if notification.seen:
        return {"message": "Notification already marked as seen"}

    notification.seen = True
    await notification.save()
    return {"message": "Notification marked as seen"}

# Mark all notifications as seen for an employee
@router.patch("/{employee_id}/mark-all-seen")
async def mark_all_seen(employee_id: str):
    notifications = await Notification.find(Notification.user_id == employee_id, Notification.seen == False).to_list()
    
    if not notifications:
        return {"message": "No unseen notifications"}

    for notification in notifications:
        notification.seen = True
    await Notification.save_all(notifications)

    return {"message": f"Marked {len(notifications)} notifications as seen"}
