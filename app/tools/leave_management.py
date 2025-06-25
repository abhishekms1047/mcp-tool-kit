#!/usr/bin/env python3
"""Simple leave management tools for MCP server."""

import json
from datetime import datetime
from typing import List
import logging

from pydantic import BaseModel

# Ensure compatibility with MCP server
from mcp.server.fastmcp import Context

# External MCP reference for tool registration
_external_mcp = None


def set_external_mcp(mcp):
    """Set the external MCP reference for tool registration"""
    global _external_mcp
    _external_mcp = mcp
    logging.info("Leave management tools MCP reference set")


class LeaveRecord(BaseModel):
    """Representation of a single leave entry."""

    start_date: str
    end_date: str
    days: int


class LeaveManagementService:
    """Service handling leave calculations."""

    def __init__(self, total_leaves: int = 100):
        self.total_leaves = total_leaves
        self.records: List[LeaveRecord] = []

    def _parse_dates(self, start: str, end: str) -> tuple[datetime, datetime, int]:
        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}")
        if end_dt < start_dt:
            raise ValueError("End date must be on or after start date")
        days = (end_dt - start_dt).days + 1
        return start_dt, end_dt, days

    async def apply_leave(self, start_date: str, end_date: str) -> str:
        start_dt, end_dt, days = self._parse_dates(start_date, end_date)
        used = sum(r.days for r in self.records)
        if used + days > self.total_leaves:
            remaining = self.total_leaves - used
            return json.dumps({
                "status": "failed",
                "error": "Not enough leaves remaining",
                "remaining_leaves": remaining
            }, indent=2)
        record = LeaveRecord(start_date=start_dt.isoformat(), end_date=end_dt.isoformat(), days=days)
        self.records.append(record)
        remaining = self.total_leaves - used - days
        return json.dumps({
            "status": "ok",
            "applied_days": days,
            "remaining_leaves": remaining
        }, indent=2)

    async def get_leave_details(self) -> str:
        used = sum(r.days for r in self.records)
        remaining = self.total_leaves - used
        return json.dumps({
            "total_leaves": self.total_leaves,
            "used_leaves": used,
            "remaining_leaves": remaining,
            "records": [r.model_dump() for r in self.records]
        }, indent=2)


_leave_service_instance: LeaveManagementService | None = None


def initialize_leave_service(total_leaves: int = 100):
    """Initialize the leave management service"""
    global _leave_service_instance
    _leave_service_instance = LeaveManagementService(total_leaves)
    return _leave_service_instance


def _get_leave_service() -> LeaveManagementService:
    global _leave_service_instance
    if _leave_service_instance is None:
        _leave_service_instance = LeaveManagementService()
    return _leave_service_instance


async def apply_leave(start_date: str, end_date: str, ctx: Context | None = None) -> str:
    """Apply for leave between two dates."""
    try:
        return await _get_leave_service().apply_leave(start_date, end_date)
    except Exception as e:
        return json.dumps({"status": "failed", "error": str(e)})


async def get_leave_details(ctx: Context | None = None) -> str:
    """Retrieve current leave balance and history."""
    try:
        return await _get_leave_service().get_leave_details()
    except Exception as e:
        return json.dumps({"status": "failed", "error": str(e)})


def get_leave_management_tools():
    """Return leave management tools for MCP registration"""
    return {
        "get_leave_details": get_leave_details,
        "apply_leave": apply_leave,
    }
