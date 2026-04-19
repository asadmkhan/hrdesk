from typing import Any

import httpx

from hrdesk.config import settings
from hrdesk.observability.logging import get_logger
from hrdesk.tools.base import ToolSchema

log = get_logger(__name__)


class ProfileTool:
    schema = ToolSchema(
        name="get_my_profile",
        description=(
            "Get basic info about the current user: their name and employee ID. "
            "Use this for questions like 'what is my name?' or 'who am I?'. "
            "Only returns data for the authenticated user."
        ),
        parameters={"type": "object", "properties": {}, "required": []},
    )

    def run(self, arguments: dict[str, Any], auth_user_id: str) -> str:
        url = f"{settings.hr_api_base_url}/employees/{auth_user_id}/profile"

        try:
            response = httpx.get(url, timeout=5.0)
        except httpx.RequestError as e:
            log.warning("profile_tool_network_error", error=str(e))
            return "Could not reach the HR system."

        if response.status_code != 200:
            log.warning("profile_tool_bad_status", status=response.status_code)
            return "Could not retrieve your profile right now."

        data = response.json()
        log.info("profile_tool_success", employee_id=auth_user_id)
        return f"Your name is {data['employee_name']} and your employee ID is {data['employee_id']}."
