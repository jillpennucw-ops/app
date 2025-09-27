# Salary Inflation Calculator - Backend Implementation Contract

## API Contracts

### POST /api/calculate-inflation
**Purpose**: Calculate inflation-adjusted salary based on employment start date and original salary

**Request Body**:
```json
{
  "start_date": "1995-06-15",  // ISO date string (YYYY-MM-DD)
  "original_salary": 45000     // Number (annual salary)
}
```

**Response**:
```json
{
  "original_salary": 45000,
  "start_date": "1995-06-15",
  "inflation_adjusted_salary": 82350,
  "cola_adjusted_salary": 55120,      // Only for 1991-2021 period
  "defacto_paycut": 27230,            // Only for 1991-2021 period
  "category": "1991-2021 Employment (COLA Period)",
  "summary": "Your salary has been adjusted using COLA calculations...",
  "inflation_rate": 0.835,            // Total inflation rate applied
  "years_elapsed": 29
}
```

## Mock Data Replacement

**Frontend Changes Needed**:
- Remove `mockData.js` import from `CalculatorPage.jsx`
- Replace `mockCalculateInflation()` call with actual API call to `/api/calculate-inflation`
- Add proper error handling for API failures
- Keep same UI state management and result display logic

## Backend Implementation Plan

**1. BLS CPI Data Integration**:
- Use BLS public API or historical CPI data for inflation calculations
- Implement caching for CPI data to avoid repeated API calls
- Handle date range validation (ensure start date is valid for CPI data availability)

**2. Business Logic Implementation**:
- **Pre-1991**: Simple inflation adjustment using CPI data
- **Post-2021**: Simple inflation adjustment using CPI data  
- **1991-2021**: Complex COLA calculation:
  - Add $8,000 to original salary (2cola_salary)
  - If 2cola_salary >= $75,000: add $3,000 (cola_adjusted_salary)
  - If 2cola_salary < $75,000: multiply by 1.04 (cola_adjusted_salary)
  - Calculate defacto_paycut = inflation_adjusted_salary - cola_adjusted_salary

**3. Data Models**:
```python
class InflationRequest(BaseModel):
    start_date: str  # ISO date format
    original_salary: float

class InflationResponse(BaseModel):
    original_salary: float
    start_date: str
    inflation_adjusted_salary: float
    cola_adjusted_salary: Optional[float]
    defacto_paycut: Optional[float]
    category: str
    summary: str
    inflation_rate: float
    years_elapsed: int
```

**4. Error Handling**:
- Invalid date formats
- Future dates or dates before CPI data availability
- Invalid salary amounts (negative, zero)
- BLS API failures (fallback to cached data)

## Frontend-Backend Integration

**API Call Pattern**:
```javascript
const response = await axios.post(`${API}/calculate-inflation`, {
  start_date: startDate,
  original_salary: parseFloat(salary)
});
```

**Error Handling**:
- Network errors
- Invalid input validation errors
- Server errors with user-friendly messages

## Testing Requirements

**Backend Testing**:
- Test all three date categories (pre-1991, 1991-2021, post-2021)
- Test COLA calculation edge cases (exactly $75,000 threshold)
- Test invalid inputs and error responses
- Test BLS API integration and caching

**Integration Testing**:
- Verify frontend correctly displays all response fields
- Test loading states and error handling
- Verify currency formatting with real calculation results