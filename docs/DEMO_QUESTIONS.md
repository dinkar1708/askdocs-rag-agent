# Demo Questions & Answers

Copy-paste these questions into the web UI (http://localhost:3000) when running locally with `company_policy.pdf`.

> **⚠️ Mock Mode:** Default local setup uses mock LLM (no API key needed). All questions return the same generic answer, but **source retrieval is working correctly** - notice sources come from different pages.
>
> **For production/real demos:** Set `LLM_PROVIDER=gemini` in `app/.env` with a real API key to get unique, intelligent answers for each question.

## Vacation & Time Off

**Q: How many vacation days do employees get?**
> **Mock:** Generic answer about company policies (sources: page 1) ✅
> **Real LLM:** "Full-time employees accrue 15 days of paid vacation per year, starting from their first day of employment."

**Q: What is the vacation accrual rate?**
> **Mock:** Generic answer about company policies (sources: page 1) ✅
> **Real LLM:** "PTO accrues at a rate of 1.25 days per month."

**Q: How many vacation days can I carry over?**
> **Mock:** Generic answer about company policies (sources: page 1) ✅
> **Real LLM:** "Employees may carry over up to 5 unused vacation days to the following year."

## Health Insurance & Benefits

**Q: What health insurance options are available?**
> **Mock:** Generic answer about benefits (sources: page 3) ✅
> **Real LLM:** "The company offers PPO, HMO, and HDHP health insurance plans with 80% premium covered."

**Q: Does the company offer dental coverage?**
> **Mock:** Generic answer about benefits (sources: page 3) ✅
> **Real LLM:** "Yes, dental and vision insurance are included in the comprehensive benefits package."

## Work Policies

**Q: What is the remote work policy?**
> **Mock:** Generic answer (sources: relevant pages) ✅
> **Real LLM:** "Remote work and flexible arrangements are available with manager approval."

**Q: What are the standard work hours?**
> **Mock:** Generic answer (sources: relevant pages) ✅
> **Real LLM:** "Standard work hours are 9:00 AM to 5:00 PM, Monday through Friday."

## Performance Reviews

**Q: How often are performance reviews?**
> **Mock:** Generic answer (sources: relevant pages) ✅
> **Real LLM:** "Performance reviews are conducted annually each December."

## "Not Found" Examples

These questions will return `"not_found"` because they're not in the documents:

**Q: What is the weather today?**
> not_found - This question cannot be answered from the uploaded documents.

**Q: How do I make pizza?**
> not_found - This question cannot be answered from the uploaded documents.

