from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class InflationRequest(BaseModel):
    start_date: str = Field(..., description="Employment start date in YYYY-MM-DD format")
    original_salary: float = Field(..., gt=0, description="Original annual salary in USD")
    
    @validator('start_date')
    def validate_date(cls, v):
        try:
            date_obj = datetime.strptime(v, '%Y-%m-%d')
            # Ensure date is not in the future
            if date_obj > datetime.now():
                raise ValueError('Start date cannot be in the future')
            # Ensure date is not before 1913 (when CPI data starts)
            if date_obj.year < 1913:
                raise ValueError('Start date cannot be before 1913 (CPI data not available)')
            return v
        except ValueError as e:
            if "does not match format" in str(e):
                raise ValueError('Date must be in YYYY-MM-DD format')
            raise e

class InflationResponse(BaseModel):
    original_salary: float
    start_date: str
    inflation_adjusted_salary: float
    cola_adjusted_salary: Optional[float] = None
    defacto_paycut: Optional[float] = None
    category: str
    summary: str
    inflation_rate: float
    years_elapsed: int