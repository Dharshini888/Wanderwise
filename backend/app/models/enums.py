from enum import Enum

class ExpenseCategory(str, Enum):
    ACCOMMODATION = "Accommodation"
    FOOD = "Food"
    TRANSPORT = "Transport"
    SHOPPING = "Shopping"
    ACTIVITIES = "Activities"
    HEALTHCARE = "Healthcare"
    INSURANCE = "Insurance"
    EMERGENCY = "Emergency"
    MISC = "Misc"

class PaymentMethod(str, Enum):
    CASH = "Cash"
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    UPI = "UPI"
    NET_BANKING = "Net Banking"

class ExpenseSource(str, Enum):
    MANUAL = "MANUAL"
    OCR = "OCR"
    AI = "AI"
    IMPORT = "IMPORT"
