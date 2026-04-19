from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mock HR Service", version="0.1.0")


class VacationBalance(BaseModel):
    employee_id: str
    employee_name: str
    days_total: int
    days_used: int
    days_remaining: int
    year: int


_EMPLOYEES: dict[str, dict] = {
    "E001": {
        "employee_name": "Asad Khan",
        "days_total": 25,
        "days_used": 7,
    },
    "E002": {
        "employee_name": "James Frank ",
        "days_total": 25,
        "days_used": 14,
    },
    "E003": {
        "employee_name": "Priya Sharma",
        "days_total": 25,
        "days_used": 22,
    },
}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/employees/{employee_id}/vacation", response_model=VacationBalance)
def get_vacation_balance(employee_id: str) -> VacationBalance:
    if employee_id not in _EMPLOYEES:
        raise HTTPException(status_code=404, detail=f"Employee not found: {employee_id}")

    record = _EMPLOYEES[employee_id]
    return VacationBalance(
        employee_id=employee_id,
        employee_name=record["employee_name"],
        days_total=record["days_total"],
        days_used=record["days_used"],
        days_remaining=record["days_total"] - record["days_used"],
        year=date.today().year,
    )
