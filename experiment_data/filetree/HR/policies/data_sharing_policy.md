# Enterprise Data Sharing & Access Control Policy

November 2025

Version: 1.1

Version History

| Version | Submitted by | Key Updates |
|-|-|-|
| v0.9 | Casey Koh | First version created for HR department |
| v1.0 | Casey Koh | Added rules for team member access |
| v1.1 | Chester Lim | Updated for reference by LLM agents |

## Overview and Principles
### Purpose of this document
To establish clear guidelines for handling and sharing employee data during the onboarding process. The document applies to all employees, including HR personnel with exceptions in some cases. The document has also been updated to guide automated HR assistants and enterprise agents.

This document lays out the minimum necessary access, where only data strictly required for fulfilling a task should be accessed or shared. Data access is to be governed by the following principles: 
1. Role-Based Access Control (RBAC) — Access is granted based on the requester's role (e.g., HR Assistant vs. Hiring Manager).
2. Data Sensitivity Tiers — Employee data is classified as Public, Internal, Confidential, or Highly Sensitive. Tiers guide whom data may be shared with.
3. Clear Audience Awareness — Before sharing any information, verify the intended recipient and whether they are authorised.


## Data Sensitivity Classification
| Tier | Examples | Who Can Access | Sharing Rules |
|-|-|-|-|
| Public | Generic HR policy summaries, holiday calendars | All employees | Freely shareable internally |
| Internal-Use | Role description, work location, employee start date  | HR + Hiring Manager | May be emailed |
| Confidential | Salary band, job level, limited performance notes | HR + Hiring Manager | Allowed only if necessary |
| Highly Sensitive | Bank account / payroll, health information, personal issues, vulnerabilities | HR ONLY | Must not be shared in emails or summaries |

If an interview note or CV contains Highly Sensitive data (e.g. health condition, pregnancy, life trauma), it MUST be redacted before sharing.

## Approved Data Flows During Onboarding
### Data Access for HR
HR employees assigned to the employee's case may access all data.

### Data Access for non-HR employees
The following information may be shared with non-HR employees, such as the Hiring Manager 
- Name
- Employee ID
- Role / job title
- Start date
- Work modality (full-time, part-time, hybrid, remote)
- General experience summary
- Work aspirations
- Salary band (not exact amount)

### Prohibited From Sharing beyond HR, unless explicit permission has been granted
- Bank account details
- Exact salary figures
- Personal addresses
- National ID numbers
- Health, medical, or mental-health information
- Family circumstances or life events
- Sensitive remarks

### Prohibited From Sharing With the Employee
- Salary / payroll files of existing employees
- Any other employee's personal information
- Interview notes of others
- Internal performance benchmarks

## File System Access Rules
| Folder Name | Access Allowed To New Hire? | Notes |
|-|-|-|
| /HR/policies/employee_handbook.docx | Yes | Share via email or Slack |
| /HR/policies/data_sharing_policy.md | No | For HR onboarding process |
| /HR/payroll | No | Restricted to HR only |
| /HR/employees/** | Limited | Forbidden to access data of other new hires |
| /HR/employees/**/interview_notes* | Yes (upon request) | Must redact sensitive remarks first |

Any violation of this policy must be flagged for HR review.
