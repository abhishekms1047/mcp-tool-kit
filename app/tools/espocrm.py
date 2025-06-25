#!/usr/bin/env python3
"""EspoCRM tool module for MCP Tool Kit."""

import os
import json
import logging

from mcp.server.fastmcp import Context

import httpx

external_mcp = None


def set_external_mcp(mcp):
    """Set the external MCP reference for tool registration"""
    global external_mcp
    external_mcp = mcp
    logging.info("EspoCRM tools MCP reference set")


class EspoCRMService:
    """Simple service wrapper around the EspoCRM REST API."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key

    async def get_contacts(self, limit: int = 20):
        """Retrieve a list of contacts."""
        url = f"{self.base_url}/api/v1/Contact"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"maxSize": limit}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()


_espocrm_service: EspoCRMService | None = None


def initialize_espocrm_service(base_url: str | None = None, api_key: str | None = None):
    """Initialize the EspoCRM service."""
    global _espocrm_service
    if base_url is None:
        base_url = os.environ.get("ESPOCRM_BASE_URL")
    if api_key is None:
        api_key = os.environ.get("ESPOCRM_API_KEY")

    if not base_url or not api_key:
        logging.warning(
            "EspoCRM credentials not configured. Set ESPOCRM_BASE_URL and ESPOCRM_API_KEY.")
        return None

    _espocrm_service = EspoCRMService(base_url, api_key)
    return _espocrm_service


def _get_espocrm_service() -> EspoCRMService | None:
    global _espocrm_service
    if _espocrm_service is None:
        _espocrm_service = initialize_espocrm_service()
    return _espocrm_service


async def espocrm_get_contacts(limit: int = 20, ctx: Context | None = None) -> str:
    """Get a list of contacts from EspoCRM."""
    service = _get_espocrm_service()
    if not service:
        return (
            "EspoCRM is not configured. Please set ESPOCRM_BASE_URL and ESPOCRM_API_KEY."
        )
    try:
        result = await service.get_contacts(limit)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error retrieving contacts: {e}"


def get_espocrm_tools():
    """Return EspoCRM tools for MCP registration."""
    return {
        "espocrm_get_contacts": espocrm_get_contacts,
    }


def initialize(mcp=None):
    """Initialize the EspoCRM module."""
    if mcp:
        set_external_mcp(mcp)

    service = initialize_espocrm_service()
    if service:
        logging.info("EspoCRM service initialized successfully")
    else:
        logging.warning("Failed to initialize EspoCRM service")

    return service is not None
