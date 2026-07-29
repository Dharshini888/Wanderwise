from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from app.database.connection import get_db
from app.models.expense import Expense, ExpenseSplit
from app.models.trip import Trip
from app.models.user import User
from app.schemas.expense_schema import (
    ExpenseCreate, ExpenseUpdate, ExpenseResponse,
    ExpenseAnalyticsResponse, AIExpenseInsightsResponse, ReceiptOCRResponse, BudgetResponse
)
from app.services.expense_service import (
    create_new_expense, get_or_create_budget, update_existing_expense,
    delete_existing_expense, get_trip_expenses, get_trip_budget_analytics,
    export_expenses_csv
)
from app.services.expense_ocr_service import process_receipt_ocr
from app.services.expense_ai_service import generate_ai_expense_insights
from app.utils.currency_formatter import format_currency
from app.routes.auth import get_current_user_optional

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


def _verify_trip_access(trip_id: int, db: Session, current_user: Optional[User] = None) -> Trip:
    """Helper to verify trip existence and user isolation for expense operations."""
    query = db.query(Trip).filter(Trip.id == trip_id)
    if current_user:
        query = query.filter(Trip.user_id == current_user.id)
    trip = query.first()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


def _serialize_expense(e: Expense) -> dict:
    amt = float(e.amount) if e.amount is not None else 0.0
    return {
        "id": e.id,
        "trip_id": e.trip_id,
        "title": e.title,
        "merchant_normalized": e.merchant_normalized or e.title,
        "description": e.description or "",
        "amount": Decimal(str(round(amt, 2))),
        "currency": e.currency or "USD",
        "base_currency": e.base_currency or "USD",
        "exchange_rate": Decimal(str(e.exchange_rate or 1.0)),
        "formatted_amount": format_currency(amt, e.currency or "USD"),
        "category": e.category.value if hasattr(e.category, "value") else str(e.category),
        "payment_method": e.payment_method.value if hasattr(e.payment_method, "value") else str(e.payment_method),
        "expense_date": e.expense_date,
        "location_name": e.location_name,
        "receipt_metadata": e.receipt_metadata,
        "notes": e.notes,
        "expense_source": e.expense_source.value if hasattr(e.expense_source, "value") else str(e.expense_source),
        "created_at": e.created_at
    }


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
@router.post("/add", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense_endpoint(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    _verify_trip_access(data.trip_id, db, current_user)
    expense = create_new_expense(db, data)
    return _serialize_expense(expense)


@router.get("/trip/{trip_id}", response_model=List[ExpenseResponse])
def get_trip_expenses_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    _verify_trip_access(trip_id, db, current_user)
    expenses = get_trip_expenses(db, trip_id)
    return [_serialize_expense(e) for e in expenses]


@router.get("/analytics/{trip_id}", response_model=ExpenseAnalyticsResponse)
def get_expense_analytics_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    _verify_trip_access(trip_id, db, current_user)
    analytics = get_trip_budget_analytics(db, trip_id)
    return analytics


@router.get("/budget/{trip_id}", response_model=BudgetResponse)
def get_trip_budget_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    trip = _verify_trip_access(trip_id, db, current_user)
    b = get_or_create_budget(db, trip)
    total_b = float(b.total_budget)
    spent = float(b.spent)
    rem = float(b.remaining)
    pct = round((spent / total_b * 100.0), 1) if total_b > 0 else 0.0

    return {
        "id": b.id,
        "trip_id": b.trip_id,
        "total_budget": b.total_budget,
        "currency": b.currency,
        "base_currency": b.base_currency,
        "spent": b.spent,
        "remaining": b.remaining,
        "daily_limit": b.daily_limit,
        "emergency_reserve": b.emergency_reserve,
        "budget_used_percentage": pct,
        "formatted_spent": format_currency(spent, b.currency),
        "formatted_remaining": format_currency(rem, b.currency),
        "formatted_total": format_currency(total_b, b.currency)
    }


@router.get("/{trip_id}/insights", response_model=AIExpenseInsightsResponse)
@router.post("/ai-insights/{trip_id}", response_model=AIExpenseInsightsResponse)
def get_ai_expense_insights_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    _verify_trip_access(trip_id, db, current_user)
    return generate_ai_expense_insights(db, trip_id)


@router.post("/ocr", response_model=ReceiptOCRResponse)
def receipt_ocr_endpoint(file: UploadFile = File(...)):
    contents = file.file.read() if file else b""
    res = process_receipt_ocr(file.filename, contents)
    return res


@router.get("/export/csv")
def export_csv_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    _verify_trip_access(trip_id, db, current_user)
    csv_data = export_expenses_csv(db, trip_id)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=wanderwise_expenses_trip_{trip_id}.csv"}
    )


@router.get("/export/pdf")
def export_pdf_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    trip = _verify_trip_access(trip_id, db, current_user)
    expenses = get_trip_expenses(db, trip_id)
    b = get_or_create_budget(db, trip)
    pdf_text = f"WanderWise Expense Report for {trip.destination}\nTotal Budget: {format_currency(float(b.total_budget), b.currency)}\nTotal Spent: {format_currency(float(b.spent), b.currency)}\nRemaining: {format_currency(float(b.remaining), b.currency)}\nTotal Items: {len(expenses)}"
    
    return Response(
        content=pdf_text.encode("utf-8"),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=wanderwise_expenses_trip_{trip_id}.pdf"}
    )


@router.get("/{id}", response_model=ExpenseResponse)
def get_expense_by_id_endpoint(
    id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    expense = db.query(Expense).filter(Expense.id == id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if current_user:
        _verify_trip_access(expense.trip_id, db, current_user)
    return _serialize_expense(expense)


@router.put("/{id}", response_model=ExpenseResponse)
def update_expense_endpoint(
    id: int,
    data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    expense_obj = db.query(Expense).filter(Expense.id == id).first()
    if not expense_obj:
        raise HTTPException(status_code=404, detail="Expense not found")
    if current_user:
        _verify_trip_access(expense_obj.trip_id, db, current_user)
    
    updated = update_existing_expense(db, id, data)
    return _serialize_expense(updated)


@router.delete("/{id}")
def delete_expense_endpoint(
    id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    expense_obj = db.query(Expense).filter(Expense.id == id).first()
    if not expense_obj:
        raise HTTPException(status_code=404, detail="Expense not found")
    if current_user:
        _verify_trip_access(expense_obj.trip_id, db, current_user)

    ok = delete_existing_expense(db, id)
    return {"status": "success", "message": "Expense deleted successfully"}


@router.get("/{trip_id}/settle-up")
def settle_up(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    _verify_trip_access(trip_id, db, current_user)
    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).all()
    balances = {}
    
    for exp in expenses:
        if exp.paid_by_user_id:
            balances[exp.paid_by_user_id] = balances.get(exp.paid_by_user_id, 0.0) + float(exp.amount)
            
        for split in exp.splits:
            if not split.is_settled:
                balances[split.user_id] = balances.get(split.user_id, 0.0) - float(split.amount_owed)
                
    debtors = []
    creditors = []
    for user_id, balance in balances.items():
        if balance < -0.01:
            debtors.append({"user_id": user_id, "amount": abs(balance)})
        elif balance > 0.01:
            creditors.append({"user_id": user_id, "amount": balance})
            
    debtors.sort(key=lambda x: x["amount"], reverse=True)
    creditors.sort(key=lambda x: x["amount"], reverse=True)
    
    transactions = []
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]
        
        amount = min(debtor["amount"], creditor["amount"])
        
        transactions.append({
            "from_user": debtor["user_id"],
            "to_user": creditor["user_id"],
            "amount": round(amount, 2)
        })
        
        debtor["amount"] -= amount
        creditor["amount"] -= amount
        
        if debtor["amount"] < 0.01:
            i += 1
        if creditor["amount"] < 0.01:
            j += 1
            
    return {"transactions": transactions, "balances": balances}
