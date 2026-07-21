# Demo - Mock Mode (No API Key)

Quick demo questions for testing without any LLM API key.

**Setup:** Default configuration with `LLM_PROVIDER=mock` in `app/.env`

**What to expect:** Enhanced mock mode returns unique, contextually relevant answers for each question type. Perfect for demos and testing.

---

## ✅ Vacation & Time Off

### How many vacation days do employees get?

**Answer:**
> According to the employee handbook [company_policy.pdf - Page 1], full-time employees accrue 15 days of paid vacation per year, starting from their first day of employment.

---

### What is the vacation accrual rate?

**Answer:**
> According to the policy [company_policy.pdf - Page 1], PTO accrues at a rate of 1.25 days per month for full-time employees.

---

### How many vacation days can I carry over?

**Answer:**
> Per the vacation policy [company_policy.pdf - Page 1], employees may carry over up to 5 unused vacation days to the following year. Any days beyond this limit will be forfeited unless approved by management.

---

## ✅ Health Insurance & Benefits

### What health insurance options are available?

**Answer:**
> The company offers three health insurance plan options [company_policy.pdf - Page 3]: PPO, HMO, and HDHP (High Deductible Health Plan). The company covers 80% of the premium for all plans.

---

### Does the company offer dental coverage?

**Answer:**
> Yes, dental and vision insurance are included in the benefits package [company_policy.pdf - Page 3]. Both are 100% employer-paid for employees.

---

## ✅ Work Policies

### What is the remote work policy?

**Answer:**
> According to the work policy [company_policy.pdf - Page 2], employees may work remotely up to 2 days per week with manager approval. Fully remote arrangements require VP approval.

---

### What are the standard work hours?

**Answer:**
> Standard work hours are Monday-Friday, 9:00 AM to 5:00 PM [company_policy.pdf - Page 2]. Flexible schedules may be available with manager approval.

---

## ❌ Questions That Return "Not Found"

### What is the weather today?

**Answer:**
> not_found - This question cannot be answered from the uploaded documents.

---

### How do I make pizza?

**Answer:**
> not_found - This question cannot be answered from the uploaded documents.

---

## 📋 Quick Copy (One-Liners)

```
How many vacation days do employees get?
```

```
What is the vacation accrual rate?
```

```
How many vacation days can I carry over?
```

```
What health insurance options are available?
```

```
Does the company offer dental coverage?
```

```
What is the remote work policy?
```

```
What are the standard work hours?
```

```
What is the weather today?
```

---

**Note:** Mock mode provides realistic demo answers without API costs. Each answer is pattern-matched to show different aspects of the document retrieval system.
