from pydantic import BaseModel, Field, validator
from datetime import date

class TripRequest(BaseModel):
    departure:      str = Field(..., min_length=1, description="出发城市")
    destination:    str = Field(..., min_length=1, description="目的城市")
    start_date:     date
    end_date:       date
    adults:         int = Field(..., ge=1, le=20)
    children:       int = Field(..., ge=0, le=20)
    budget:         int = Field(..., ge=100)
    personal:       str = "无"

    @validator("end_date")
    def check_dates(cls, v, values):
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("返回日期不能早于出发日期")
        return v