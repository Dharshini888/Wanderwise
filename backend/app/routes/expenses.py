from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from app.database.connection import get_db
from app.models.expense import Expense, ExpenseSplit
from typing import List

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])

class ExpenseSplitCreate(BaseModel):
    user_id: int
    amount_owed: float

class ExpenseCreate(BaseModel):
    trip_id: int
    category: str
    amount: float
    description: str = None
    date: date
    paid_by_user_id: int = None
    splits: List[ExpenseSplitCreate] = []

@router.post("/add")
def add_expense(data: ExpenseCreate, db: Session = Depends(get_db)):
    expense = Expense(
        trip_id=data.trip_id,
        category=data.category,
        amount=data.amount,
        description=data.description,
        date=data.date,
        paid_by_user_id=data.paid_by_user_id
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    
    if data.splits:
        for split in data.splits:
            expense_split = ExpenseSplit(
                expense_id=expense.id,
                user_id=split.user_id,
                amount_owed=split.amount_owed
            )
            db.add(expense_split)
        db.commit()
        
    return expense

@router.get("/{trip_id}")
def get_expenses(trip_id: int, db: Session = Depends(get_db)):
    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).all()
    total = sum(e.amount for e in expenses)
    return {"expenses": expenses, "total": total}

@router.get("/{trip_id}/settle-up")
def settle_up(trip_id: int, db: Session = Depends(get_db)):
    # Calculate net balances for each user based on expenses and splits
    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).all()
    
    balances = {} # user_id -> balance (positive means they are owed money, negative means they owe money)
    
    for exp in expenses:
        if exp.paid_by_user_id:
            balances[exp.paid_by_user_id] = balances.get(exp.paid_by_user_id, 0) + exp.amount
            
        for split in exp.splits:
            if not split.is_settled:
                balances[split.user_id] = balances.get(split.user_id, 0) - split.amount_owed
                
    # Simplify debts (greedy algorithm)
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
