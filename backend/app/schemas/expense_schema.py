from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from app.models.enums import ExpenseCategory, PaymentMethod, ExpenseSource

class ExpenseCreate(BaseModel):
    trip_id: int
    title: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    category: ExpenseCategory = ExpenseCategory.MISC
    payment_method: PaymentMethod = PaymentMethod.CASH
    expense_date: date
    currency: str = "USD"
    location_name: Optional[str] = None
    notes: Optional[str] = None
    expense_source: ExpenseSource = ExpenseSource.MANUAL
    receipt_metadata: Optional[Dict[str, Any]] = None
    paid_by_user_id: Optional[int] = None

class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[Decimal] = None
    category: Optional[ExpenseCategory] = None
    payment_method: Optional[PaymentMethod] = None
    expense_date: Optional[date] = None
    currency: Optional[str] = None
    location_name: Optional[str] = None
    notes: Optional[str] = None
    expense_source: Optional[ExpenseSource] = None
    receipt_metadata: Optional[Dict[str, Any]] = None

class ExpenseResponse(BaseModel):
    id: int
    trip_id: int
    title: str
    merchant_normalized: Optional[str] = None
    description: Optional[str] = None
    amount: Decimal
    currency: str
    base_currency: str
    exchange_rate: Decimal
    formatted_amount: str
    category: ExpenseCategory
    payment_method: PaymentMethod
    expense_date: date
    location_name: Optional[str] = None
    receipt_metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    expense_source: ExpenseSource
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BudgetResponse(BaseModel):
    id: int
    trip_id: int
    total_budget: Decimal
    currency: str
    base_currency: str
    spent: Decimal
    remaining: Decimal
    daily_limit: Decimal
    emergency_reserve: Decimal
    budget_used_percentage: float
    formatted_spent: str
    formatted_remaining: str
    formatted_total: str

    class Config:
        from_attributes = True

class CategorySpendItem(BaseModel):
    category: str
    amount: Decimal
    percentage: float
    formatted_amount: str

class MerchantSpendItem(BaseModel):
    merchant: str
    count: int
    total_amount: Decimal
    formatted_amount: str

class DailySpendItem(BaseModel):
    date: str
    day_number: int
    amount: Decimal
    formatted_amount: str

class ExpenseAnalyticsResponse(BaseModel):
    trip_id: int
    total_budget: Decimal
    total_spent: Decimal
    remaining_budget: Decimal
    budget_used_percentage: float
    daily_average: Decimal
    projected_final_spend: Decimal
    highest_spending_category: str
    highest_spending_day: str
    largest_expense: Optional[Dict[str, Any]] = None
    cash_vs_card_ratio: Dict[str, float]
    top_merchants: List[MerchantSpendItem]
    category_breakdown: List[CategorySpendItem]
    daily_trend: List[DailySpendItem]
    spending_heatmap: List[Dict[str, Any]]

class AIExpenseInsightsResponse(BaseModel):
    budget_score: int
    health: str
    forecast: str
    projected_spend: Decimal
    remaining_budget: Decimal
    daily_limit_remaining: Decimal
    recommended_today_spend: Decimal
    highest_category: str
    highest_day: str
    overspending_risk: str
    top_savings: List[str]
    risk_items: List[str]
    smart_alerts: List[str]

class ReceiptOCRResponse(BaseModel):
    merchant: str
    date: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: str = "USD"
    category: ExpenseCategory = ExpenseCategory.MISC
    confidence: float
    missing_fields: List[str] = []
