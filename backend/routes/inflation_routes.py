from fastapi import APIRouter, HTTPException
from models.inflation_models import InflationRequest, InflationResponse
from services.salary_calculator import SalaryCalculator
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
calculator = SalaryCalculator()

@router.post("/calculate-inflation", response_model=InflationResponse)
async def calculate_inflation(request: InflationRequest):
    """
    Calculate inflation-adjusted salary based on employment start date and original salary.
    
    This endpoint handles three scenarios:
    - Pre-1991: Simple inflation adjustment using CPI data
    - 1991-2021: COLA calculations with de facto pay cut analysis  
    - Post-2021: Simple inflation adjustment using CPI data
    """
    try:
        logger.info(f"Processing inflation calculation for date: {request.start_date}, salary: ${request.original_salary}")
        
        result = calculator.calculate_adjusted_salary(request)
        
        logger.info(f"Calculation completed successfully for {request.start_date}")
        return result
        
    except ValueError as e:
        logger.warning(f"Invalid input for inflation calculation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error in inflation calculation: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="An error occurred while calculating inflation. Please try again later."
        )