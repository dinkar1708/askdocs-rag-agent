# Demo - Ollama Local LLM (100% Offline)

Test results using Ollama with llama3.2 model - completely offline, zero API costs.

**Setup:**
```bash
# Install Ollama
brew install ollama
brew services start ollama
ollama pull llama3.2

# Configure in app/.env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

**Tested:** 2026-07-21 with company_policy.pdf

---

## ✅ Test Results

### Question 1: How many vacation days do employees get?

**Answer:**
> According to the company policy, employees receive PTO accrual at a rate of 1.25 days per month. The document does not specify an annual amount of vacation days. However, it states that employees may carry over up to 5 unused vacation days to the following year.
>
> Employees get up to 5 unused vacation days that can be carried over, but the actual number of paid vacation days is not specified in the provided context.

**Sources:** company_policy.pdf - Page 1
**Model:** ollama:llama3.2
**Response Time:** ~14 seconds
**Confidence:** 0.63

**Notes:** Ollama correctly extracted the accrual rate and carryover policy, though it could be more concise.

---

### Question 2: What is the remote work policy?

**Answer:**
> The remote work policy states that employees may work remotely up to 2 days per week with manager approval, and remote work arrangements must be documented and approved in writing.
>
> [company_policy.pdf - Page 2]

**Sources:** company_policy.pdf - Page 2
**Model:** ollama:llama3.2
**Response Time:** ~1.5 seconds
**Confidence:** 0.61

**Notes:** Excellent grounded answer with proper citation format.

---

### Question 3: What health insurance options are available?

**Answer:**
> According to the document, the company provides comprehensive health insurance coverage including medical, dental, and vision. The company pays 80% of the premium for employee coverage and 60% for family coverage.
>
> [company_policy.pdf - Page 3]

**Sources:** company_policy.pdf - Page 3
**Model:** ollama:llama3.2
**Response Time:** ~1.4 seconds
**Confidence:** 0.47

**Notes:** Accurate answer with correct premium sharing details.

---

## 📊 Performance Summary

| Metric | Value |
|--------|-------|
| **Model** | llama3.2 (2GB) |
| **First Response** | ~14s (model loading) |
| **Subsequent Responses** | 1-2s |
| **Accuracy** | ✅ All answers grounded in documents |
| **Citations** | ✅ Proper page references |
| **Hallucinations** | ❌ None detected |
| **API Cost** | $0.00 (100% local) |

---

## 🎯 Advantages

✅ **Zero Cost** - No API fees, unlimited queries
✅ **100% Offline** - Works without internet
✅ **Data Privacy** - Documents never leave your machine
✅ **Decent Quality** - llama3.2 provides good grounded answers
✅ **Fast After Warmup** - 1-2s response time after initial load

---

## ⚠️ Limitations

- **Initial Warmup:** First query takes 10-15s (model loading)
- **Answer Length:** Sometimes more verbose than cloud LLMs
- **Complex Reasoning:** Not as strong as Gemini/GPT-4 for multi-hop questions
- **Hardware Requirements:** Needs ~4GB RAM for llama3.2

---

## 📋 Quick Copy Questions

Test these yourself:

```
How many vacation days do employees get?
```

```
What is the remote work policy?
```

```
What health insurance options are available?
```

```
Does the company offer dental coverage?
```

```
What are the standard work hours?
```

---

## 🔄 Switching Between Providers

**Mock Mode (instant, no setup):**
```bash
LLM_PROVIDER=mock
```

**Ollama (local, no cost):**
```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

**Gemini (cloud, best quality):**
```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-api-key-here
```

Just change `app/.env` and restart: `docker compose -f app/docker-compose.yml restart api`

---

**Verdict:** Ollama with llama3.2 is perfect for privacy-sensitive deployments, internal company use, or cost-conscious production environments. Answers are grounded, cited, and accurate - just a bit slower than cloud APIs.
