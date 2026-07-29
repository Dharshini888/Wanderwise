BUDGET_ADVISOR_PROMPT = """
Use this prompt to generate structured budget analysis action payloads.

OUTPUT ACTION FORMAT:
{
  "type": "budget_status",
  "title": "Trip Budget Analysis",
  "total_budget": 60000,
  "spent": 42000,
  "remaining": 18000,
  "health": "Healthy/Warning/Exceeded",
  "suggestion": "Reduce daily dining expenses by $15 to stay on budget"
}
"""
