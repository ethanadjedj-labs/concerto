from fastapi import APIRouter, HTTPException

from maestro import db

router = APIRouter()


@router.get("/api/buyer/{token}/status")
async def buyer_status(token: str):
    buyer = await db.get_buyer(token)
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    resp: dict = {"status": buyer["status"]}
    if buyer.get("vps_ip"):
        resp["vps_ip"] = buyer["vps_ip"]
    if buyer.get("mcp_url"):
        resp["mcp_url"] = buyer["mcp_url"]
    if buyer.get("bearer_token"):
        resp["bearer_token"] = buyer["bearer_token"]
    if buyer["status"] == "awaiting_oauth":
        resp["dashboard_ready_url"] = f"https://maestro.run/dashboard/{token}"
    return resp
