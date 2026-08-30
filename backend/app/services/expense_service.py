import re
import csv
import io
from decimal import Decimal
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.expense import Expense, ExpenseSplit
from app.models.budget import Budget
from app.models.trip import Trip
from app.models.enums import ExpenseCategory, PaymentMethod, ExpenseSource
from app.utils.currency_formatter import format_currency
from app.core.currencies import get_currency_info

def normalize_merchant_name(raw_name: Optional[str]) -> str:
    """Normalize merchant names to aggregate variations like STARBUCKS / Starbucks Coffee -> Starbucks."""
    if not raw_name or not raw_name.strip():
        return "General Merchant"
    
    clean = raw_name.strip()
    # Common suffix removal
    patterns = [
        (r"(?i)\s+coffee$", ""),
        (r"(?i)\s+bistro$", ""),
        (r"(?i)\s+restaurant$", ""),
        (r"(?i)\s+inc\.?$", ""),
        (r"(?i)\s+ltd\.?$", ""),
        (r"(?i)\s+pvt\.?$", ""),
        (r"(?i)\s+store$", ""),
    ]
    for pat, repl in patterns:
        clean = re.sub(pat, repl, clean)
    
    # Title Case
    return clean.strip().title()

def get_or_create_budget(db: Session, trip: Trip) -> Budget:
    """Fetch or initialize Budget record for a trip and synchronize metrics."""
    budget = db.query(Budget).filter(Budget.trip_id == trip.id).first()
    
    total_b = Decimal(str(trip.budget or 1000.00))
    curr = trip.currency or "USD"

    if not budget:
        budget = Budget(
            trip_id=trip.id,
            total_budget=total_b,
            currency=curr,
            base_currency=curr,
            spent=Decimal("0.00"),
            remaining=total_b,
            daily_limit=Decimal("0.00"),
            emergency_reserve=Decimal(str(round(float(total_b) * 0.10, 2)))
        )
        db.add(budget)
        db.commit()
        db.refresh(budget)

    # Recalculate spending metrics
    sync_budget_metrics(db, trip.id)
    db.refresh(budget)
    return budget

def sync_budget_metrics(db: Session, trip_id: int):
    """Synchronize spent, remaining, daily limit, and emergency reserve on Budget entity."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        return

    budget = db.query(Budget).filter(Budget.trip_id == trip_id).first()
    if not budget:
        budget = Budget(
            trip_id=trip.id,
            total_budget=Decimal(str(trip.budget or 1000.00)),
            currency=trip.currency or "USD",
            base_currency=trip.currency or "USD"
        )
        db.add(budget)
        db.commit()
        db.refresh(budget)

    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).all()
    total_spent = sum(Decimal(str(e.amount)) for e in expenses) if expenses else Decimal("0.00")
    total_budget = Decimal(str(trip.budget or 1000.00))
    
    remaining = total_budget - total_spent
    
    # Calculate trip total days
    days_count = 1
    if trip.start_date and trip.end_date:
        days_count = max(1, (trip.end_date - trip.start_date).days + 1)
    
    daily_limit = Decimal(str(round(float(remaining) / float(days_count), 2))) if float(remaining) > 0 else Decimal("0.00")
    emergency_reserve = Decimal(str(round(float(total_budget) * 0.10, 2)))

    budget.total_budget = total_budget
    budget.currency = trip.currency or "USD"
    budget.spent = total_spent
    budget.remaining = remaining
    budget.daily_limit = daily_limit
    budget.emergency_reserve = emergency_reserve
    db.commit()

def create_new_expense(db: Session, data) -> Expense:
    """Create a new expense item and sync Budget entity."""
    merchant = normalize_merchant_name(data.title)
    
    expense = Expense(
        trip_id=data.trip_id,
        title=data.title,
        merchant_normalized=merchant,
        amount=Decimal(str(data.amount)),
        currency=data.currency,
        base_currency=data.currency,
        exchange_rate=Decimal("1.0"),
        category=data.category,
        payment_method=data.payment_method,
        expense_date=data.expense_date,
        location_name=data.location_name,
        notes=data.notes,
        expense_source=data.expense_source,
        receipt_metadata=data.receipt_metadata,
        paid_by_user_id=data.paid_by_user_id
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    sync_budget_metrics(db, data.trip_id)
    return expense

def update_existing_expense(db: Session, expense_id: int, data) -> Optional[Expense]:
    """Update expense details and sync Budget entity."""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        return None

    if data.title is not None:
        expense.title = data.title
        expense.merchant_normalized = normalize_merchant_name(data.title)
    if data.amount is not None:
        expense.amount = Decimal(str(data.amount))
    if data.category is not None:
        expense.category = data.category
    if data.payment_method is not None:
        expense.payment_method = data.payment_method
    if data.expense_date is not None:
        expense.expense_date = data.expense_date
    if data.currency is not None:
        expense.currency = data.currency
    if data.location_name is not None:
        expense.location_name = data.location_name
    if data.notes is not None:
        expense.notes = data.notes
    if data.expense_source is not None:
        expense.expense_source = data.expense_source
    if data.receipt_metadata is not None:
        expense.receipt_metadata = data.receipt_metadata

    db.commit()
    db.refresh(expense)
    sync_budget_metrics(db, expense.trip_id)
    return expense

def delete_existing_expense(db: Session, expense_id: int) -> bool:
    """Delete an expense record and update Budget entity."""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        return False
    
    trip_id = expense.trip_id
    db.delete(expense)
    db.commit()
    
    sync_budget_metrics(db, trip_id)
    return True

def get_trip_expenses(db: Session, trip_id: int) -> List[Expense]:
    """Fetch all expense items for a trip sorted by date descending."""
    return db.query(Expense).filter(Expense.trip_id == trip_id).order_by(Expense.expense_date.desc(), Expense.id.desc()).all()

def get_trip_budget_analytics(db: Session, trip_id: int) -> Dict[str, Any]:
    """Compute rich budget analytics, category breakdown, trend, heatmap, and merchant metrics."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        return {}

    budget = get_or_create_budget(db, trip)
    expenses = get_trip_expenses(db, trip_id)
    
    total_b = float(budget.total_budget)
    total_spent = float(budget.spent)
    remaining = float(budget.remaining)
    curr = budget.currency or "USD"
    pct = round((total_spent / total_b * 100.0), 1) if total_b > 0 else 0.0

    days_count = max(1, (trip.end_date - trip.start_date).days + 1) if trip.start_date and trip.end_date else 1
    daily_avg = round(total_spent / days_count, 2)
    projected_spend = round(daily_avg * days_count, 2)

    # Category breakdown
    cat_map = {}
    payment_map = {"Cash": 0.0, "Card": 0.0}
    merchant_map = {}
    date_map = {}

    largest_exp = None
    max_exp_amt = -1.0

    for e in expenses:
        amt = float(e.amount)
        cat = e.category.value if hasattr(e.category, "value") else str(e.category)
        cat_map[cat] = cat_map.get(cat, 0.0) + amt

        pm = e.payment_method.value if hasattr(e.payment_method, "value") else str(e.payment_method)
        if "Card" in pm or "UPI" in pm or "Banking" in pm:
            payment_map["Card"] += amt
        else:
            payment_map["Cash"] += amt

        merch = e.merchant_normalized or normalize_merchant_name(e.title)
        if merch not in merchant_map:
            merchant_map[merch] = {"count": 0, "amount": 0.0}
        merchant_map[merch]["count"] += 1
        merchant_map[merch]["amount"] += amt

        d_str = str(e.expense_date)
        date_map[d_str] = date_map.get(d_str, 0.0) + amt

        if amt > max_exp_amt:
            max_exp_amt = amt
            largest_exp = {
                "id": e.id,
                "title": e.title,
                "amount": amt,
                "formatted_amount": format_currency(amt, curr),
                "category": cat,
                "date": d_str
            }

    # Category Breakdown list
    category_breakdown = []
    for cat, amt in cat_map.items():
        category_breakdown.append({
            "category": cat,
            "amount": Decimal(str(round(amt, 2))),
            "percentage": round((amt / total_spent * 100.0), 1) if total_spent > 0 else 0.0,
            "formatted_amount": format_currency(amt, curr)
        })
    category_breakdown.sort(key=lambda x: float(x["amount"]), reverse=True)

    highest_cat = category_breakdown[0]["category"] if category_breakdown else "None"

    # Top Merchants
    top_merchants = []
    for merch, m_data in merchant_map.items():
        top_merchants.append({
            "merchant": merch,
            "count": m_data["count"],
            "total_amount": Decimal(str(round(m_data["amount"], 2))),
            "formatted_amount": format_currency(m_data["amount"], curr)
        })
    top_merchants.sort(key=lambda x: float(x["total_amount"]), reverse=True)

    # Cash vs Card Ratio
    tot_pay = payment_map["Cash"] + payment_map["Card"]
    cash_vs_card = {
        "cash_percentage": round((payment_map["Cash"] / tot_pay * 100.0), 1) if tot_pay > 0 else 50.0,
        "card_percentage": round((payment_map["Card"] / tot_pay * 100.0), 1) if tot_pay > 0 else 50.0,
        "cash_amount": payment_map["Cash"],
        "card_amount": payment_map["Card"]
    }

    # Daily trend & Heatmap
    daily_trend = []
    spending_heatmap = []
    highest_day = "Day 1"
    max_day_spend = -1.0

    from datetime import timedelta
    for d_i in range(days_count):
        d_obj = trip.start_date + timedelta(days=d_i) if trip.start_date else date.today()
        d_str = str(d_obj)
        amt = date_map.get(d_str, 0.0)
        
        daily_trend.append({
            "date": d_str,
            "day_number": d_i + 1,
            "amount": Decimal(str(round(amt, 2))),
            "formatted_amount": format_currency(amt, curr)
        })

        spending_heatmap.append({
            "date": d_str,
            "day_number": d_i + 1,
            "amount": amt,
            "intensity": "high" if amt > (daily_avg * 1.5) else ("medium" if amt > 0 else "zero")
        })

        if amt > max_day_spend:
            max_day_spend = amt
            highest_day = f"Day {d_i + 1}"

    return {
        "trip_id": trip.id,
        "total_budget": Decimal(str(total_b)),
        "total_spent": Decimal(str(total_spent)),
        "remaining_budget": Decimal(str(remaining)),
        "budget_used_percentage": pct,
        "daily_average": Decimal(str(daily_avg)),
        "projected_final_spend": Decimal(str(projected_spend)),
        "highest_spending_category": highest_cat,
        "highest_spending_day": highest_day,
        "largest_expense": largest_exp,
        "cash_vs_card_ratio": cash_vs_card,
        "top_merchants": top_merchants[:5],
        "category_breakdown": category_breakdown,
        "daily_trend": daily_trend,
        "spending_heatmap": spending_heatmap
    }

def export_expenses_csv(db: Session, trip_id: int) -> str:
    """Generate CSV string of expenses for export."""
    expenses = get_trip_expenses(db, trip_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Title", "Merchant", "Category", "Amount", "Currency", "Payment Method", "Date", "Location", "Source", "Notes"])
    
    for e in expenses:
        writer.writerow([
            e.id,
            e.title,
            e.merchant_normalized or e.title,
            e.category.value if hasattr(e.category, "value") else str(e.category),
            float(e.amount),
            e.currency,
            e.payment_method.value if hasattr(e.payment_method, "value") else str(e.payment_method),
            str(e.expense_date),
            e.location_name or "",
            e.expense_source.value if hasattr(e.expense_source, "value") else str(e.expense_source),
            e.notes or ""
        ])
    return output.getvalue()

def export_expenses_pdf(db: Session, trip_id: int) -> bytes:
    """Generate PDF bytes of expenses for export."""
    try:
        from fpdf import FPDF
    except ImportError:
        raise ValueError("fpdf2 is not installed.")

    expenses = get_trip_expenses(db, trip_id)
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=16)
    pdf.cell(0, 10, text=f"Expense Report - {trip.destination if trip else 'Trip'}", new_x="LMARGIN", new_y="NEXT", align='C')
    
    pdf.set_font("helvetica", size=10)
    pdf.ln(10)
    
    # Table header
    pdf.set_font("helvetica", style='B', size=10)
    pdf.cell(40, 10, text="Date", border=1)
    pdf.cell(60, 10, text="Title / Merchant", border=1)
    pdf.cell(40, 10, text="Category", border=1)
    pdf.cell(40, 10, text="Amount", border=1, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", size=10)
    total = 0
    for e in expenses:
        total += float(e.amount)
        date_str = str(e.expense_date)[:10]
        title_str = (e.merchant_normalized or e.title)[:25]
        cat_str = (e.category.value if hasattr(e.category, "value") else str(e.category))[:15]
        amt_str = f"{e.currency} {float(e.amount):.2f}"
        
        pdf.cell(40, 10, text=date_str, border=1)
        pdf.cell(60, 10, text=title_str, border=1)
        pdf.cell(40, 10, text=cat_str, border=1)
        pdf.cell(40, 10, text=amt_str, border=1, new_x="LMARGIN", new_y="NEXT")
        
    pdf.ln(5)
    pdf.set_font("helvetica", style='B', size=12)
    pdf.cell(0, 10, text=f"Total Expenses: {total:.2f}", new_x="LMARGIN", new_y="NEXT", align='R')
    
    return bytes(pdf.output())
