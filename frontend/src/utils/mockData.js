// Mock data for the inflation calculator
// This will be replaced with actual BLS CPI API calls in the backend

export const mockCalculateInflation = (startDateStr, originalSalary) => {
  const startDate = new Date(startDateStr);
  const currentYear = new Date().getFullYear();
  
  // Mock inflation rates (roughly based on historical averages)
  const mockInflationRate = 0.025; // 2.5% annual average
  const yearsElapsed = currentYear - startDate.getFullYear();
  
  // Calculate inflation-adjusted salary using compound interest formula
  const inflationAdjustedSalary = originalSalary * Math.pow(1 + mockInflationRate, yearsElapsed);
  
  // Determine category based on date ranges
  let category, summary, colaAdjustedSalary = null, defactoPaycut = null;
  
  if (startDate < new Date('1991-01-01')) {
    category = 'Pre-1991 Employment';
    summary = `Your original salary of $${originalSalary.toLocaleString()} in ${startDate.getFullYear()} would be worth approximately $${Math.round(inflationAdjustedSalary).toLocaleString()} today when adjusted for inflation.`;
  } else if (startDate > new Date('2021-12-31')) {
    category = 'Post-2021 Employment';
    summary = `Your recent salary of $${originalSalary.toLocaleString()} from ${startDate.getFullYear()} would be worth approximately $${Math.round(inflationAdjustedSalary).toLocaleString()} in today's dollars.`;
  } else {
    category = '1991-2021 Employment (COLA Period)';
    
    // COLA calculation logic
    const colaBase = originalSalary + 8000; // Add 8K
    
    if (colaBase >= 75000) {
      colaAdjustedSalary = colaBase + 3000;
    } else {
      const colaIncrease = colaBase * 0.04;
      colaAdjustedSalary = colaBase + colaIncrease;
    }
    
    defactoPaycut = inflationAdjustedSalary - colaAdjustedSalary;
    
    summary = `Your salary has been adjusted using COLA calculations. However, when compared to true inflation, you've experienced a de facto pay cut of $${Math.abs(Math.round(defactoPaycut)).toLocaleString()}.`;
  }
  
  return {
    originalSalary,
    startDate: startDateStr,
    inflationAdjustedSalary: Math.round(inflationAdjustedSalary),
    colaAdjustedSalary: colaAdjustedSalary ? Math.round(colaAdjustedSalary) : null,
    defactoPaycut: defactoPaycut ? Math.round(defactoPaycut) : null,
    category,
    summary
  };
};