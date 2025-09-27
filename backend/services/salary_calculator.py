from datetime import datetime
from typing import Dict, Any
from .inflation_service import InflationService
from ..models.inflation_models import InflationRequest, InflationResponse

class SalaryCalculator:
    def __init__(self):
        self.inflation_service = InflationService()
    
    def calculate_adjusted_salary(self, request: InflationRequest) -> InflationResponse:
        """Main calculation method that handles all date ranges and logic"""
        
        start_date = datetime.strptime(request.start_date, '%Y-%m-%d')
        original_salary = request.original_salary
        
        # Get inflation data
        inflation_rate, years_elapsed = self.inflation_service.calculate_inflation_rate(request.start_date)
        inflation_adjusted_salary = original_salary * (1 + inflation_rate)
        
        # Determine category and apply appropriate logic
        category, cola_adjusted_salary, defacto_paycut, summary = self._determine_category_and_calculate(
            start_date, original_salary, inflation_adjusted_salary
        )
        
        return InflationResponse(
            original_salary=original_salary,
            start_date=request.start_date,
            inflation_adjusted_salary=round(inflation_adjusted_salary, 2),
            cola_adjusted_salary=round(cola_adjusted_salary, 2) if cola_adjusted_salary else None,
            defacto_paycut=round(defacto_paycut, 2) if defacto_paycut else None,
            category=category,
            summary=summary,
            inflation_rate=round(inflation_rate, 4),
            years_elapsed=years_elapsed
        )
    
    def _determine_category_and_calculate(self, start_date: datetime, original_salary: float, 
                                        inflation_adjusted_salary: float) -> tuple[str, float, float, str]:
        """Determine date category and perform appropriate calculations"""
        
        pre_1991 = datetime(1991, 1, 1)
        post_2021 = datetime(2021, 12, 31)
        
        if start_date < pre_1991:
            return self._handle_pre_1991(start_date, original_salary, inflation_adjusted_salary)
        elif start_date > post_2021:
            return self._handle_post_2021(start_date, original_salary, inflation_adjusted_salary)
        else:
            return self._handle_cola_period(start_date, original_salary, inflation_adjusted_salary)
    
    def _handle_pre_1991(self, start_date: datetime, original_salary: float, 
                        inflation_adjusted_salary: float) -> tuple[str, None, None, str]:
        """Handle employment starting before January 1, 1991"""
        category = "Pre-1991 Employment"
        summary = (
            f"Your original salary of ${original_salary:,.0f} from {start_date.year} "
            f"would be worth approximately ${inflation_adjusted_salary:,.0f} today "
            f"when adjusted for inflation using official CPI data."
        )
        return category, None, None, summary
    
    def _handle_post_2021(self, start_date: datetime, original_salary: float,
                         inflation_adjusted_salary: float) -> tuple[str, None, None, str]:
        """Handle employment starting after December 31, 2021"""
        category = "Post-2021 Employment"
        summary = (
            f"Your salary of ${original_salary:,.0f} from {start_date.year} "
            f"would be worth approximately ${inflation_adjusted_salary:,.0f} "
            f"in today's purchasing power when adjusted for inflation."
        )
        return category, None, None, summary
    
    def _handle_cola_period(self, start_date: datetime, original_salary: float,
                           inflation_adjusted_salary: float) -> tuple[str, float, float, str]:
        """Handle employment between January 1, 1991 and December 31, 2021 (COLA period)"""
        category = "1991-2021 Employment (COLA Period)"
        
        # Step 1: Add $8,000 to starting salary (2cola_salary)
        cola_base_salary = original_salary + 8000
        
        # Step 2: Apply COLA adjustment based on threshold
        if cola_base_salary >= 75000:
            # If 2cola_salary >= $75,000, add $3,000
            cola_adjusted_salary = cola_base_salary + 3000
        else:
            # If 2cola_salary < $75,000, multiply by 1.04 (4% increase)
            cola_adjusted_salary = cola_base_salary * 1.04
        
        # Step 3: Calculate de facto pay cut
        defacto_paycut = inflation_adjusted_salary - cola_adjusted_salary
        
        # Generate summary
        if defacto_paycut > 0:
            summary = (
                f"Your salary started at ${original_salary:,.0f} in {start_date.year}. "
                f"After COLA adjustments, your effective salary is ${cola_adjusted_salary:,.0f}. "
                f"However, true inflation suggests it should be ${inflation_adjusted_salary:,.0f}, "
                f"resulting in a de facto pay cut of ${abs(defacto_paycut):,.0f}."
            )
        else:
            summary = (
                f"Your salary started at ${original_salary:,.0f} in {start_date.year}. "
                f"After COLA adjustments to ${cola_adjusted_salary:,.0f}, "
                f"your purchasing power has kept pace with or exceeded inflation "
                f"(${inflation_adjusted_salary:,.0f} inflation-adjusted value)."
            )
        
        return category, cola_adjusted_salary, defacto_paycut, summary