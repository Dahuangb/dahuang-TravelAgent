from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List

class Activity(BaseModel):
    name: str
    start: datetime
    end: datetime
    transport_mode: str = "步行"
    transport_duration: int = 0
    category: str

class DayPlan(BaseModel):
    day: int
    activities: List[Activity]
    accommodation: int = Field(default=0, description="住宿费用（元）")
    restaurant: int = Field(default=0, description="餐饮费用（元）")
    transport: int = Field(default=0, description="交通费用（元）")
    attraction: int = Field(default=0, description="门票费用（元）")
    contingency: int = Field(default=0, description="备用金（元）")