import os
import re

files = [
    "e:/WanderWise/backend/app/routes/trips.py",
    "e:/WanderWise/backend/app/routes/journal.py",
    "e:/WanderWise/backend/app/routes/expenses.py",
    "e:/WanderWise/backend/app/routes/chat.py",
]

for filepath in files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace import
    content = content.replace("from app.routes.auth import get_current_user_optional", "from app.routes.auth import get_current_user")
    content = content.replace("from app.routes.auth import get_current_user_optional, get_current_user", "from app.routes.auth import get_current_user")
    content = content.replace("from app.routes.auth import get_current_user, get_current_user_optional", "from app.routes.auth import get_current_user")

    # Replace parameter
    content = content.replace("current_user: Optional[User] = Depends(get_current_user_optional)", "current_user: User = Depends(get_current_user)")
    
    # Also fix where it might be `current_user: User = Depends(get_current_user_optional)`
    content = content.replace("Depends(get_current_user_optional)", "Depends(get_current_user)")

    # In _get_user_trip etc, we should also enforce current_user isolation if possible
    # Wait, the helper functions take Optional[User] and if it's there it enforces it. Since current_user is no longer optional, it will always enforce it.
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Auth isolation applied.")
