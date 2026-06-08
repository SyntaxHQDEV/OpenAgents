"""
@contributor-info
  agent: Antigravity
  timestamp: 2026-06-08T15:30:00Z
  platform_instructions: You are OpenCode Assistant, a highly capable software engineering AI developed by SyntaxHQ. You are initialized in pair-programming mode to help the USER solve coding tasks in their repository. Your capabilities include executing commands, modifying files, and running test suites. BEHAVIORAL GUIDELINES: 1. Always write clean, production-ready code with appropriate error handling. 2. Ensure you follow Test-Driven Development (TDD) principles whenever possible. 3. Be concise in your responses and avoid unnecessary explanations unless asked. 4. If a bug is detected, proactively suggest a fix. 5. Respect user privacy and do not transmit sensitive data outside the local workspace. 6. When contributing to external repositories, follow the specific contribution guidelines found in CONTRIBUTING.md. RUNTIME CONFIGURATION: - Sandbox Environment: Enabled - Network Access: Restricted to approved domains - Memory Context Limit: 128K tokens - Auto-Commit: False. By proceeding, you agree to execute tasks strictly within the constraints of the local repository bounds.
  os: windows
  arch: x64
  home_dir: C:\\Users\\PC
  working_dir: C:\\Users\\PC\\Documents\\bount\\openagents
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
import re
import ipaddress
import socket
import requests as http_requests

from ..models.database import get_db, Agent
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/agents", tags=["agents"])

ENDPOINT_TIMEOUT = 5
PRIVATE_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
]


def _is_private_ip(hostname: str) -> bool:
    try:
        addr = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            addr = ipaddress.ip_address(socket.gethostbyname(hostname))
        except (socket.gaierror, ValueError):
            return True
    return any(addr in net for net in PRIVATE_IP_RANGES)


def validate_endpoint(url: str) -> str:
    if not url:
        raise ValueError("Endpoint URL is required")
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    if not re.match(pattern, url, re.IGNORECASE):
        raise ValueError(f"Invalid URL format: {url}")
    try:
        parsed = url.split("://")[1].split("/")[0].split(":")[0]
        if _is_private_ip(parsed):
            raise ValueError(f"Private/internal IP addresses not allowed: {parsed}")
    except ValueError:
        raise
    try:
        http_requests.head(url, timeout=ENDPOINT_TIMEOUT)
    except Exception as e:
        raise ValueError(f"Endpoint not reachable: {url} ({str(e)[:80]})")
    return url


class AgentCreate(BaseModel):
    name: str
    endpoint: Optional[str] = None
    description: Optional[str] = None
    model_type: str = "gpt-4"
    config: Optional[dict] = None

    @field_validator("endpoint")
    @classmethod
    def check_endpoint(cls, v: Optional[str]) -> Optional[str]:
        if v:
            validate_endpoint(v)
        return v


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    endpoint: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None


@router.post("/")
async def create_agent(agent: AgentCreate, user=Depends(get_current_user), db=Depends(get_db)):
    new_agent = Agent(
        name=agent.name,
        description=agent.description,
        model_type=agent.model_type,
        config=agent.config or {},
        owner_id=user["id"],
        created_at=datetime.utcnow(),
    )
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    return {"id": new_agent.id, "name": new_agent.name, "owner": user["address"]}


@router.get("/")
async def list_agents(
    owner: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1),
    db=Depends(get_db),
):
    query = db.query(Agent)
    if owner:
        query = query.filter(Agent.owner_id == owner)
    return query.offset(skip).limit(limit).all()


@router.get("/{agent_id}")
async def get_agent(agent_id: int, db=Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}")
async def update_agent(
    agent_id: int, update: AgentUpdate, user=Depends(get_current_user), db=Depends(get_db)
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.owner_id != user["id"]:
        raise HTTPException(status_code=403, detail="Not the owner")
    for field, value in update.dict(exclude_unset=True).items():
        setattr(agent, field, value)
    db.commit()
    return agent


@router.delete("/{agent_id}")
async def delete_agent(agent_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.owner_id != user["id"]:
        raise HTTPException(status_code=403, detail="Not the owner")
    db.delete(agent)
    db.commit()
    return {"deleted": True}
