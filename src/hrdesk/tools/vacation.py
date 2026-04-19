from typing import Any

import httpx

from hrdesk.config import settings
from hrdesk.observability.logging import get_logger
from hrdesk.tools.base import ToolSchema

log = get_logger(__name__)


class VacationTool:
    schema = ToolSchema(
        name="get_my_vacation_balance",
        description=(
            "Look up the current user's vacation balance (total days, used, remaining). "
            "Only returns data for the authenticated user. Does not accept a name or ID."
        ),
        parameters={"type": "object", "properties": {}, "required": []},
    )

    def run(self, arguments: dict[str, Any], auth_user_id: str) -> str:
        url = f"{settings.hr_api_base_url}/employees/{auth_user_id}/vacation"

        try:
            response = httpx.get(url, timeout=5.0)
        except httpx.RequestError as e:
            log.warning("vacation_tool_network_error", error=str(e))
            return "Could not reach the HR system."

        if response.status_code != 200:
            log.warning("vacation_tool_bad_status", status=response.status_code)
            return "Could not retrieve your vacation balance right now."

        data = response.json()
        log.info("vacation_tool_success", employee_id=auth_user_id)
        return (
            f"You have {data['days_remaining']} vacation days remaining out of "
            f"{data['days_total']} for {data['year']} ({data['days_used']} used)."
        )
