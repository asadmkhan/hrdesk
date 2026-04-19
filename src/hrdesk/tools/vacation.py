from typing import Any

import httpx

from hrdesk.config import settings
from hrdesk.observability.logging import get_logger
from hrdesk.tools.base import ToolSchema

log = get_logger(__name__)


class VacationTool:
    schema = ToolSchema(
        name="get_vacation_balance",
        description=(
            "Look up an employee's current vacation balance from the HR system. "
            "Returns total days, days used, and days remaining for the current year. "
            "Use when the user asks about their own or a specific employee's "
            "remaining vacation, PTO, or holiday days."
        ),
        parameters={
            "type": "object",
            "properties": {
                "employee_id": {
                    "type": "string",
                    "description": "The employee ID, e.g. 'E001'",
                }
            },
            "required": ["employee_id"],
        },
    )

    def run(self, arguments: dict[str, Any]) -> str:
        employee_id = arguments["employee_id"]
        url = f"{settings.hr_api_base_url}/employees/{employee_id}/vacation"

        try:
            response = httpx.get(url, timeout=5.0)
        except httpx.RequestError as e:
            log.warning("vacation_tool_network_error", error=str(e))
            return f"Could not reach the HR system: {e}"

        if response.status_code == 404:
            return f"Employee '{employee_id}' was not found in the HR system."

        if response.status_code != 200:
            log.warning("vacation_tool_bad_status", status=response.status_code)
            return f"HR system returned an unexpected status: {response.status_code}"

        data = response.json()
        log.info("vacation_tool_success", employee_id=employee_id)
        return (
            f"{data['employee_name']} (ID {data['employee_id']}) has "
            f"{data['days_remaining']} vacation days remaining out of "
            f"{data['days_total']} for {data['year']} "
            f"({data['days_used']} used)."
        )
