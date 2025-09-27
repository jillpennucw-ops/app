import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Calendar, DollarSign, TrendingUp, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "./ui/alert";
import { Badge } from "./ui/badge";
import { Separator } from "./ui/separator";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CalculatorPage = () => {
  const [startDate, setStartDate] = useState("");
  const [salary, setSalary] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCalculate = async () => {
    if (!startDate || !salary) {
      alert("Please fill in all fields");
      return;
    }

    setLoading(true);
    
    try {
      const response = await axios.post(`${API}/calculate-inflation`, {
        start_date: startDate,
        original_salary: parseFloat(salary)
      });
      
      setResult(response.data);
    } catch (error) {
      console.error('Error calculating inflation:', error);
      let errorMessage = "An error occurred while calculating inflation. Please try again.";
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.status === 400) {
        errorMessage = "Please check your input values and try again.";
      }
      
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-2 mb-4">
            <TrendingUp className="h-8 w-8 text-blue-600" />
            <h1 className="text-4xl font-bold text-gray-900">
              Salary Inflation Calculator
            </h1>
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Calculate how your starting salary compares to today's value with inflation adjustments and COLA considerations
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input Form */}
          <Card className="shadow-xl border-0 bg-white">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-t-lg">
              <CardTitle className="flex items-center gap-2 text-xl">
                <Calendar className="h-5 w-5 text-blue-600" />
                Employment Details
              </CardTitle>
              <CardDescription>
                Enter your employment start date and initial salary
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              <div className="space-y-2">
                <Label htmlFor="startDate" className="text-sm font-medium text-gray-700">
                  Employment Start Date
                </Label>
                <Input
                  id="startDate"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="h-11 border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="salary" className="text-sm font-medium text-gray-700">
                  Starting Annual Salary
                </Label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    id="salary"
                    type="number"
                    placeholder="50000"
                    value={salary}
                    onChange={(e) => setSalary(e.target.value)}
                    className="pl-10 h-11 border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
              </div>

              <Button 
                onClick={handleCalculate} 
                disabled={loading}
                className="w-full h-12 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold transition-all duration-200"
              >
                {loading ? "Calculating..." : "Calculate Inflation Impact"}
              </Button>
            </CardContent>
          </Card>

          {/* Results */}
          <Card className="shadow-xl border-0 bg-white">
            <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-t-lg">
              <CardTitle className="flex items-center gap-2 text-xl">
                <TrendingUp className="h-5 w-5 text-green-600" />
                Calculation Results
              </CardTitle>
              <CardDescription>
                Your salary adjustment analysis
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              {!result ? (
                <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                  <AlertCircle className="h-12 w-12 mb-4 text-gray-300" />
                  <p className="text-center">Enter your details and click calculate to see results</p>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <p className="text-sm text-gray-600">Original Salary</p>
                      <p className="text-xl font-bold text-blue-600">
                        {formatCurrency(result.original_salary)}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatDate(result.start_date)}
                      </p>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <p className="text-sm text-gray-600">Today's Value</p>
                      <p className="text-xl font-bold text-green-600">
                        {formatCurrency(result.inflation_adjusted_salary)}
                      </p>
                      <p className="text-xs text-gray-500">
                        Inflation Adjusted
                      </p>
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Time Period</span>
                      <Badge variant="secondary">
                        {result.category}
                      </Badge>
                    </div>

                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">Total Inflation Rate</span>
                          <span className="font-medium">
                            {(result.inflation_rate * 100).toFixed(1)}%
                          </span>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">Years Elapsed</span>
                          <span className="font-medium">
                            {result.years_elapsed} years
                          </span>
                        </div>

                    {result.cola_adjusted_salary && (
                      <>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">COLA Adjusted Salary</span>
                          <span className="font-medium">
                            {formatCurrency(result.cola_adjusted_salary)}
                          </span>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">De facto Pay Cut</span>
                          <span className="font-medium text-red-600">
                            -{formatCurrency(Math.abs(result.defacto_paycut))}
                          </span>
                        </div>

                        <Alert>
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription>
                            <strong>Analysis:</strong> Your salary has effectively been reduced by{" "}
                            <strong>{formatCurrency(Math.abs(result.defacto_paycut))}</strong>{" "}
                            when accounting for COLA adjustments vs. true inflation.
                          </AlertDescription>
                        </Alert>
                      </>
                    )}

                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="font-semibold text-gray-900 mb-2">Summary</h4>
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {result.summary}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Info Section */}
        <Card className="mt-8 shadow-lg border-0 bg-gradient-to-r from-amber-50 to-yellow-50">
          <CardContent className="p-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-amber-900 mb-2">How It Works</h4>
                <ul className="text-sm text-amber-800 space-y-1">
                  <li>• <strong>Pre-1991:</strong> Shows inflation-adjusted salary using CPI data</li>
                  <li>• <strong>Post-2021:</strong> Shows inflation-adjusted salary using CPI data</li>
                  <li>• <strong>1991-2021:</strong> Applies COLA calculations and compares with true inflation</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CalculatorPage;