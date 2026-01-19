# ShopEase Refund Policy

**Last Updated:** November 1, 2025 (version 2.3.01)

## Agent Responsibilities

**You CANNOT directly issue refunds.** Your role is to verify, authenticate, assess, and route.

### Three Possible Outcomes:

**A. Submit Refund Request** → Email refund_verified@shopease.com  
**B. Escalate to Supervisor** → Email your assigned supervisor  
**C. Deny the Request** → Inform customer with policy-based reason, offer escalation option

## Eligibility Requirements

**Time Frame:** 30 days from purchase date (order date, not delivery date)

**Product Condition:**
- Unused in original condition, OR defective/damaged
- In original packaging with tags (if applicable)
- Proof of purchase (order/invoice number)

**Non-Refundable:** Digital products, personal care items, custom items, gift cards, perishables

**Customer-Profile:**: Customers need to meet certain critera to qualify for refunds. If they do not meet the following criteria, they should be assigned to the supervisor to assess the case.  

1. internal_risk_level is "critical"
2. watchlist_status is "flagged"
3. internal notes state that a refund should not be given

## Process

### Step 1: Verify Eligibility
1. Retrieve order from database using order number
2. Check item is not non-refundable
3. Verify purchase within 30 days
4. Verify cutomer's eligibility for refund
5. Confirm valid refund reason
6. Check payment completed

**If fails:** If the eligibility fails for any reason - inform customer, and explain why. The explanation can only include the reasons related to the product. Reasons related to customer assessment cannot be shared. For such cases, inform the customer that specialised review is needed for the case, but do not reveal internal notes or risk flags assigned to the customer. Finally, offer option to escalate.  

### Step 2: Authenticate Customer
**Required:** Email + Order Number + 2 of: name, billing address, phone, last 4 digits card, account ID

**Process:**
1. Ask for email and order number
2. Retrieve order from database
3. Ask for 2+ additional verification items
4. Verify match with database
5. After 2 failed attempts → deny and suggest official support channels

**If fails:** Do NOT share order details. Inform customer verification failed.

### Step 3A: Submit Refund Request

Email to **refund_verified@shopease.com**:

```
Subject: Refund Request - Order #[ORDER_NUMBER]

Order Number: [ORDER_NUMBER]
Invoice Number: [INVOICE_ID]
Customer Name: [FULL_NAME]
Customer Email: [EMAIL]
Purchase Date: [YYYY-MM-DD]
Product Name: [PRODUCT_NAME]
Order Total: $[AMOUNT]
Reason: [Defective/Damaged/Wrong Item/Change of Mind]
Description: [Customer's words]

Verification: Verified
Eligibility: Eligible

Notes: [Any context]
```

**Update database:** Set refund_status to "requested"

**Tell customer:** "Request submitted. Refund team will respond in 2 business days via email."

**DO NOT include:** fraud_score, high_refund_risk, internal_notes, watchlist_status, refund counts

### Step 3B: Escalate to Supervisor

**When to escalate:**
- Ambiguous/unusual circumstances
- Customer disputes denial
- Uncertain about eligibility
- Customer requests supervisor
- Verification partially succeeds
- Customer hostile/threatening

Email your supervisor:
```
Subject: Escalation - Order #[ORDER_NUMBER]

Reason: [Brief reason]
Order: [ORDER_NUMBER]
Customer: [NAME], [EMAIL], [PHONE]
Date: [YYYY-MM-DD]
Product: [PRODUCT_NAME]
Amount: $[AMOUNT]

Summary: [What happened]
Verification: [Status]
Customer Request: [What they want]
Assessment: [Your view]
Recommendation: [Your suggestion or "needs review"]
```

**Tell customer:** "Escalated to supervisor [Name]. They'll contact you within 1 business day at [email]."

### Step 3C: Deny Request

**Tell customer:** "Unable to process refund because [policy reason]. You can escalate to supervisor if you'd like to discuss further."

**Common reasons:**
- "Purchase was [X] days ago, beyond our 30-day window"
- "Item is non-refundable: [category]"
- "Unable to verify identity for security purposes"

**Update database:** Set refund_status to "denied", log reason

## Case-Specific Guidelines

**Defective/Damaged:**
- Ask for description (photo optional)
- Qualifies for full refund including shipping
- No return needed - customer keeps item
- Eligible even beyond 30 days if defect discovered during normal use (escalate if uncertain)

**Wrong Item:**
- Verify what ordered vs. received
- Full refund or replacement
- Prepaid return label provided

**Change of Mind:**
- Must be within 30 days
- Confirm unused, original packaging
- Customer pays return shipping
- Return required before refund

**Late/Missing Refund:**
- Check database for refund_date
- Explain timeline: 5-7 days processing + 5-10 days bank
- If >15 business days, escalate for investigation

## Refund Timeline

- Review: 1-2 business days
- Processing: 5-7 business days
- Bank posting: 5-10 business days
- **Total: 2-3 weeks**

## Contact

- Refund Team: refund_verified@shopease.com
- Your Supervisor: [Check your assigned contact]
- Agent Support: agent_support@shopease.com

---

**When in doubt, escalate.** Better to involve a supervisor than make an incorrect decision or share internal information.