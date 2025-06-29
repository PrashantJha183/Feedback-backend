from fastapi import APIRouter, HTTPException
from app.models.notification import Notification
from bson import ObjectId

router = APIRouter()

@router.get("/notifications/{employee_id}")
async def get_notifications(employee_id: str):
    notifications = await Notification.find(
        Notification.employee_id == employee_id
    ).sort(-Notification.created_at).to_list()
    return notifications

@router.patch("/notifications/{notification_id}")
async def mark_seen(notification_id: str, seen: bool):
    notif = await Notification.get(ObjectId(notification_id))
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    notif.seen = seen
    await notif.save()
    return {"message": "Notification updated."}

@router.patch("/notifications/mark-all-seen/{employee_id}")
async def mark_all_seen(employee_id: str):
    await Notification.find(
        Notification.employee_id == employee_id
    ).update_many({"$set": {"seen": True}})
    return {"message": "All notifications marked as seen."}
