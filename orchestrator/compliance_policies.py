"""
Enterprise Compliance Policy Engine
====================================
Real-world policies based on actual HR compliance requirements,
employment law, and enterprise documentation standards.

Compliance Frameworks Covered:
- US Employment Law (FLSA, EEOC, ADA, FMLA)
- Hiring Compliance (I-9, E-Verify, FCRA, Ban-the-Box)
- Data Privacy (GDPR, CCPA, HIPAA, SOC2)
- Financial Controls (SOX, Internal Audit)
- DEI & Inclusive Hiring (OFCCP, Pay Equity)
"""

import re
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger("Orchestrator.Compliance")


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════════

class ComplianceCategory(Enum):
    """Categories of compliance requirements."""
    EMPLOYMENT_LAW = "employment_law"           # FLSA, EEOC, ADA, FMLA
    HIRING_COMPLIANCE = "hiring_compliance"     # I-9, E-Verify, FCRA
    DATA_PRIVACY = "data_privacy"               # GDPR, CCPA, HIPAA
    FINANCIAL_CONTROLS = "financial_controls"   # SOX, approval limits
    DEI_COMPLIANCE = "dei_compliance"           # OFCCP, pay equity
    INTERNAL_POLICY = "internal_policy"         # Company-specific rules
    SECURITY = "security"                       # Access controls, SOC2


class RegulatoryFramework(Enum):
    """Regulatory frameworks referenced."""
    FLSA = "Fair Labor Standards Act"
    EEOC = "Equal Employment Opportunity Commission"
    ADA = "Americans with Disabilities Act"
    FMLA = "Family Medical Leave Act"
    FCRA = "Fair Credit Reporting Act"
    GDPR = "General Data Protection Regulation"
    CCPA = "California Consumer Privacy Act"
    HIPAA = "Health Insurance Portability Act"
    SOX = "Sarbanes-Oxley Act"
    OFCCP = "Office of Federal Contract Compliance"
    WARN = "Worker Adjustment and Retraining Notification Act"
    IRCA = "Immigration Reform and Control Act"


class PolicyAction(Enum):
    """Actions a policy can take."""
    ALLOW = "allow"
    REQUIRE_DOCUMENTATION = "require_documentation"
    REQUIRE_APPROVAL = "require_approval"
    MODIFY = "modify"
    WARN = "warn"
    BLOCK = "block"
    ESCALATE = "escalate"
    AUDIT_LOG = "audit_log"


class ApprovalLevel(Enum):
    """Approval hierarchy levels."""
    NONE = "none"
    MANAGER = "manager"
    DIRECTOR = "director"
    VP = "vp"
    C_LEVEL = "c_level"
    BOARD = "board"
    LEGAL = "legal"
    HR_DIRECTOR = "hr_director"
    COMPENSATION_COMMITTEE = "compensation_committee"


@dataclass
class ComplianceResult:
    """Result of a compliance check."""
    compliant: bool
    action: PolicyAction
    policy_id: str
    policy_name: str
    category: ComplianceCategory
    regulatory_reference: Optional[RegulatoryFramework] = None
    reason: str = ""
    required_documentation: List[str] = field(default_factory=list)
    required_approval: Optional[ApprovalLevel] = None
    remediation_steps: List[str] = field(default_factory=list)
    modified_payload: Optional[Dict] = None
    risk_score: float = 0.0
    audit_required: bool = False
    metadata: Dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# BASE COMPLIANCE POLICY
# ═══════════════════════════════════════════════════════════════════════════════

class CompliancePolicy(ABC):
    """Base class for all compliance policies."""

    def __init__(
        self,
        policy_id: str,
        name: str,
        description: str,
        category: ComplianceCategory,
        regulatory_reference: RegulatoryFramework = None,
        effective_date: datetime = None,
        version: str = "1.0"
    ):
        self.policy_id = policy_id
        self.name = name
        self.description = description
        self.category = category
        self.regulatory_reference = regulatory_reference
        self.effective_date = effective_date or datetime.now()
        self.version = version
        self.enabled = True
        self.evaluations = 0
        self.violations = 0

    @abstractmethod
    def evaluate(self, action: str, payload: Dict, context: Dict) -> ComplianceResult:
        """Evaluate compliance for an action."""
        pass

    @abstractmethod
    def applies_to(self, action: str) -> bool:
        """Check if policy applies to action."""
        pass

    def to_dict(self) -> Dict:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "regulatory_reference": self.regulatory_reference.value if self.regulatory_reference else None,
            "effective_date": self.effective_date.isoformat(),
            "version": self.version,
            "enabled": self.enabled,
            "evaluations": self.evaluations,
            "violations": self.violations
        }


# ═══════════════════════════════════════════════════════════════════════════════
# I-9 / EMPLOYMENT ELIGIBILITY (IRCA Compliance)
# ═══════════════════════════════════════════════════════════════════════════════

class I9CompliancePolicy(CompliancePolicy):
    """
    I-9 Employment Eligibility Verification

    Legal Requirement: Immigration Reform and Control Act (IRCA)

    Rules:
    - I-9 must be completed within 3 business days of hire
    - Cannot work without I-9 verification
    - Section 1 completed by employee on/before first day
    - Section 2 completed by employer within 3 business days
    - Documents must be from List A, or List B + List C
    - E-Verify required for federal contractors
    """

    def __init__(self):
        super().__init__(
            policy_id="i9_compliance",
            name="I-9 Employment Eligibility Verification",
            description="Verify employment eligibility per IRCA requirements",
            category=ComplianceCategory.HIRING_COMPLIANCE,
            regulatory_reference=RegulatoryFramework.IRCA
        )

        # Valid document lists per USCIS
        self.list_a_documents = [
            "us_passport", "passport_card", "permanent_resident_card",
            "foreign_passport_with_i94", "employment_authorization_document"
        ]
        self.list_b_documents = [
            "drivers_license", "state_id", "school_id", "voter_registration",
            "military_id", "military_dependent_id"
        ]
        self.list_c_documents = [
            "social_security_card", "birth_certificate", "certification_of_birth_abroad",
            "native_american_tribal_document", "employment_authorization_dhs"
        ]

    def applies_to(self, action: str) -> bool:
        return action in [
            "onboard_employee", "start_employment", "provision_access",
            "create_employee_record", "activate_employee", "complete_hiring"
        ]

    def evaluate(self, action: str, payload: Dict, context: Dict) -> ComplianceResult:
        self.evaluations += 1

        i9_status = payload.get("i9_status") or context.get("i9_status")
        i9_documents = payload.get("i9_documents", [])
        start_date = payload.get("start_date")

        # Check if I-9 is verified
        if i9_status == "verified":
            return ComplianceResult(
                compliant=True,
                action=PolicyAction.ALLOW,
                policy_id=self.policy_id,
                policy_name=self.name,
                category=self.category,
                regulatory_reference=self.regulatory_reference,
                reason="I-9 verification complete",
                audit_required=True,
                metadata={"i9_status": "verified"}
            )

        # Check document combinations
        has_list_a = any(doc in self.list_a_documents for doc in i9_documents)
        has_list_b = any(doc in self.list_b_documents for doc in i9_documents)
        has_list_c = any(doc in self.list_c_documents for doc in i9_documents)

        if has_list_a or (has_list_b and has_list_c):
            return ComplianceResult(
                compliant=True,
                action=PolicyAction.REQUIRE_DOCUMENTATION,
                policy_id=self.policy_id,
                policy_name=self.name,
                category=self.category,
                regulatory_reference=self.regulatory_reference,
                reason="Documents acceptable, complete I-9 form",
                required_documentation=["I-9 Form Section 1", "I-9 Form Section 2"],
                remediation_steps=[
                    "Employee completes Section 1 on or before first day of work",
                    "Employer completes Section 2 within 3 business days",
                    "Retain I-9 for 3 years after hire or 1 year after termination"
                ],
                audit_required=True
            )

        # I-9 not complete - BLOCK employment
        self.violations += 1
        return ComplianceResult(
            compliant=False,
            action=PolicyAction.BLOCK,
            policy_id=self.policy_id,
            policy_name=self.name,
            category=self.category,
            regulatory_reference=self.regulatory_reference,
            reason="I-9 verification required before employment can begin",
            required_documentation=[
                "One document from List A (e.g., US Passport, Permanent Resident Card)",
                "OR one document from List B (e.g., Driver's License) AND one from List C (e.g., Social Security Card)"
            ],
            remediation_steps=[
                "1. Obtain acceptable identity and employment authorization documents",
                "2. Complete I-9 Section 1 on or before first day",
                "3. Employer verifies documents and completes Section 2 within 3 days"
            ],
            risk_score=0.4,
            audit_required=True,
            metadata={"violation": "missing_i9"}
        )


# ═══════════════════════════════════════════════════════════════════════════════
# BACKGROUND CHECK COMPLIANCE (FCRA)
# ═══════════════════════════════════════════════════════════════════════════════

class BackgroundCheckPolicy(CompliancePolicy):
    """
    Background Check Compliance

    Legal Framework: Fair Credit Reporting Act (FCRA)

    Rules:
    - Written consent required BEFORE background check
    - Standalone disclosure document required
    - Pre-adverse action notice if considering not hiring
    - Copy of report + summary of rights to candidate
    - Adverse action notice with dispute rights
    - Ban-the-Box: Cannot ask criminal history on application (many states)
    """

    def __init__(self):
        super().__init__(
            policy_id="background_check_fcra",
            name="Background Check FCRA Compliance",
            description="Ensure background checks comply with FCRA requirements",
            category=ComplianceCategory.HIRING_COMPLIANCE,
            regulatory_reference=RegulatoryFramework.FCRA
        )

        # States with Ban-the-Box laws
        self.ban_the_box_states = {
            "CA", "CT", "HI", "IL", "MA", "MN", "NJ", "NM", "OR", "RI", "VT", "WA"
        }

        # Required FCRA documentation
        self.required_documents = [
            "standalone_disclosure",
            "written_authorization",
            "summary_of_rights"
        ]

    def applies_to(self, action: str) -> bool:
        return action in [
            "run_background_check", "initiate_background_check",
            "check_criminal_history", "verify_employment_history",
            "check_credit_report", "make_hiring_decision"
        ]

    def evaluate(self, action: str, payload: Dict, context: Dict) -> ComplianceResult:
        self.evaluations += 1

        has_consent = payload.get("candidate_consent", False)
        has_disclosure = payload.get("disclosure_provided", False)
        candidate_state = payload.get("candidate_state", "")
        check_type = payload.get("check_type", "standard")
        stage = payload.get("hiring_stage", "post_offer")

        # Ban-the-Box check
        if stage == "application" and candidate_state in self.ban_the_box_states:
            self.violations += 1
            return ComplianceResult(
                compliant=False,
                action=PolicyAction.BLOCK,
                policy_id=self.policy_id,
                policy_name=self.name,
                category=self.category,
                regulatory_reference=self.regulatory_reference,
                reason=f"Ban-the-Box law in {candidate_state}: Cannot inquire about criminal history at application stage",
                remediation_steps=[
                    "Remove criminal history questions from application",
                    "Delay background check until conditional offer made",
                    "Follow state-specific timing requirements"
                ],
                risk_score=0.35,
                audit_required=True,
                metadata={"ban_the_box_state": candidate_state}
            )

        # Check FCRA requirements
        missing_requirements = []

        if not has_disclosure:
            missing_requirements.append("Standalone disclosure document not provided")

        if not has_consent:
            missing_requirements.append("Written authorization from candidate not obtained")

        if missing_requirements:
            self.violations += 1
            return ComplianceResult(
                compliant=False,
                action=PolicyAction.BLOCK,
                policy_id=self.policy_id,
                policy_name=self.name,
                category=self.category,
                regulatory_reference=self.regulatory_reference,
                reason="FCRA requirements not met",
                required_documentation=self.required_documents,
                remediation_steps=[
                    "Provide standalone disclosure (not combined with other documents)",
                    "Obtain written authorization from candidate",
                    "Provide 'Summary of Your Rights Under the FCRA' document",
                    "Maintain records of consent and disclosure"
                ] + missing_requirements,
                risk_score=0.3,
                audit_required=True
            )

        return ComplianceResult(
            compliant=True,
            action=PolicyAction.ALLOW,
            policy_id=self.policy_id,
            policy_name=self.name,
            category=self.category,
            regulatory_reference=self.regulatory_reference,
            reason="FCRA requirements satisfied",
            audit_required=True,
            metadata={"fcra_compliant": True, "check_type": check_type}
        )


# ═══════════════════════════════════════════════════════════════════════════════
# COMPENSATION COMPLIANCE (Pay Equity / Pay Transparency)
# ═══════════════════════════════════════════════════════════════════════════════

class CompensationCompliancePolicy(CompliancePolicy):
    """
    Compensation Compliance Policy

    Covers:
    - Pay Equity (Equal Pay Act, state laws)
    - Pay Transparency (CO, CA, NY, WA requirements)
    - Salary History Bans
    - Level-based compensation bands
    - Approval hierarchies
    """

    def __init__(self):
        super().__init__(
            policy_id="compensation_compliance",
            name="Compensation & Pay Equity Compliance",
            description="Ensure compensation decisions comply with pay equity and transparency laws",
            category=ComplianceCategory.DEI_COMPLIANCE,
            regulatory_reference=RegulatoryFramework.EEOC
        )

        # Pay transparency required states (must include salary range in postings)
        self.pay_transparency_states = {"CO", "CA", "NY", "WA", "CT", "NV", "RI", "MD"}

        # Salary history ban states
        self.salary_history_ban_states = {
            "CA", "CO", "CT", "DE", "HI", "IL", "MA", "MD", "NJ", "NY", "OR", "PA", "VT", "WA"
        }

        # Compensation bands by level (should come from company data)
        self.compensation_bands = {
            "IC1": {"min": 60000, "mid": 75000, "max": 90000},
            "IC2": {"min": 80000, "mid": 100000, "max": 120000},
            "IC3": {"min": 100000, "mid": 125000, "max": 150000},
            "IC4": {"min": 130000, "mid": 160000, "max": 190000},
            "IC5": {"min": 170000, "mid": 210000, "max": 250000},
            "IC6": {"min": 220000, "mid": 280000, "max": 340000},
            "M1": {"min": 120000, "mid": 150000, "max": 180000},
            "M2": {"min": 150000, "mid": 190000, "max": 230000},
            "M3": {"min": 200000, "mid": 260000, "max": 320000},
            "D1": {"min": 250000, "mid": 320000, "max": 400000},
            "VP": {"min": 350000, "mid": 450000, "max": 600000},
        }

        # Approval thresholds
        self.approval_matrix = {
            "at_or_below_mid": ApprovalLevel.MANAGER,
            "above_mid_to_max": ApprovalLevel.DIRECTOR,
            "above_max_10pct": ApprovalLevel.VP,
            "above_max_20pct": ApprovalLevel.C_LEVEL,
            "above_max_30pct": ApprovalLevel.COMPENSATION_COMMITTEE,
        }

    def applies_to(self, action: str) -> bool:
        return action in [
            "generate_offer", "create_offer", "negotiate_offer", "adjust_salary",
            "promote_employee", "set_compensation", "approve_compensation",
            "post_job", "create_job_posting"
        ]

    def evaluate(self, action: str, payload: Dict, context: Dict) -> ComplianceResult:
        self.evaluations += 1

        # Check for salary history request violation
        if action in ["generate_offer", "create_offer"]:
            if payload.get("based_on_salary_history"):
                candidate_state = payload.get("candidate_state", "")
                if candidate_state in self.salary_history_ban_states:
                    self.violations += 1
                    return ComplianceResult(
                        compliant=False,
                        action=PolicyAction.BLOCK,
                        policy_id=self.policy_id,
                        policy_name=self.name,
                        category=self.category,
                        reason=f"Salary history ban in {candidate_state}: Cannot base offer on candidate's prior salary",
                        remediation_steps=[
                            "Remove salary history from consideration",
                            "Base offer on role requirements, market data, and internal equity",
                            "Document objective factors used in compensation decision"
                        ],
                        risk_score=0.3,
                        audit_required=True
                    )

        # Check pay transparency for job postings
        if action in ["post_job", "create_job_posting"]:
            location_state = payload.get("location_state", "")
            salary_range_included = payload.get("salary_range_included", False)

            if location_state in self.pay_transparency_states and not salary_range_included:
                self.violations += 1
                return ComplianceResult(
                    compliant=False,
                    action=PolicyAction.BLOCK,
                    policy_id=self.policy_id,
                    policy_name=self.name,
                    category=self.category,
                    reason=f"Pay transparency required in {location_state}: Job posting must include salary range",
                    remediation_steps=[
                        "Add salary/hourly range to job posting",
                        "Range must be good faith estimate of compensation",
                        "Include any additional compensation components"
                    ],
                    risk_score=0.25,
                    audit_required=True
                )

        # Check compensation against bands
        level = payload.get("level", "")
        salary = payload.get("salary", 0)
        total_comp = payload.get("total_compensation", salary)

        if level and salary and level in self.compensation_bands:
            band = self.compensation_bands[level]

            # Determine position in band
            if salary <= band["mid"]:
                required_approval = self.approval_matrix["at_or_below_mid"]
                position = "at or below midpoint"
            elif salary <= band["max"]:
                required_approval = self.approval_matrix["above_mid_to_max"]
                position = "above midpoint, within band"
            elif salary <= band["max"] * 1.1:
                required_approval = self.approval_matrix["above_max_10pct"]
                position = f"up to 10% above band maximum"
            elif salary <= band["max"] * 1.2:
                required_approval = self.approval_matrix["above_max_20pct"]
                position = f"10-20% above band maximum"
            elif salary <= band["max"] * 1.3:
                required_approval = self.approval_matrix["above_max_30pct"]
                position = f"20-30% above band maximum"
            else:
                # Way over band
                self.violations += 1
                return ComplianceResult(
                    compliant=False,
                    action=PolicyAction.BLOCK,
                    policy_id=self.policy_id,
                    policy_name=self.name,
                    category=self.category,
                    reason=f"Salary ${salary:,} exceeds {level} band maximum ${band['max']:,} by more than 30%",
                    remediation_steps=[
                        f"Review if correct level ({level}) is assigned",
                        "Consider re-leveling candidate if warranted",
                        f"Maximum approvable salary for {level}: ${int(band['max'] * 1.3):,}",
                        "Escalate to Compensation Committee for exception"
                    ],
                    risk_score=0.4,
                    required_approval=ApprovalLevel.BOARD,
                    audit_required=True
                )

            # Within approvable range
            if salary > band["max"]:
                return ComplianceResult(
                    compliant=True,
                    action=PolicyAction.REQUIRE_APPROVAL,
                    policy_id=self.policy_id,
                    policy_name=self.name,
                    category=self.category,
                    reason=f"Salary {position} for {level} - requires {required_approval.value} approval",
                    required_approval=required_approval,
                    remediation_steps=[
                        f"Obtain {required_approval.value} approval before extending offer",
                        "Document business justification for above-band offer",
                        "Confirm internal equity analysis completed"
                    ],
                    audit_required=True,
                    metadata={
                        "level": level,
                        "salary": salary,
                        "band_min": band["min"],
                        "band_mid": band["mid"],
                        "band_max": band["max"],
                        "position_in_band": position
                    }
                )

            # Within band
            return ComplianceResult(
                compliant=True,
                action=PolicyAction.ALLOW,
                policy_id=self.policy_id,
                policy_name=self.name,
                category=self.category,
                reason=f"Salary within {level} band ({position})",
                audit_required=True,
                metadata={
                    "level": level,
                    "salary": salary,
                    "band_min": band["min"],
                    "band_mid": band["mid"],
                    "band_max": band["max"],
                    "percentile": round((salary - band["min"]) / (band["max"] - band["min"]) * 100, 1)
                }
            )

        # No level specified or unknown level
        return ComplianceResult(
            compliant=True,
            action=PolicyAction.WARN,
            policy_id=self.policy_id,
            policy_name=self.name,
            category=self.category,
            reason="Unable to validate against compensation bands - level not specified",
            audit_required=True
        )


# ═══════════════════════════════════════════════════════════════════════════════
# DATA PRIVACY COMPLIANCE (GDPR / CCPA)
# ═══════════════════════════════════════════════════════════════════════════════

class DataPrivacyPolicy(CompliancePolicy):
    """
    Data Privacy Compliance

    Frameworks:
    - GDPR (EU residents)
    - CCPA/CPRA (California residents)
    - General PII protection

    Rules:
    - Consent required for data processing
    - Purpose limitation
    - Data minimization
    - Right to access/delete
    - Cross-border transfer restrictions
    - Retention limits
    """

    def __init__(self):
        super().__init__(
            policy_id="data_privacy",
            name="Data Privacy & Protection Policy",
            description="Ensure personal data handling complies with GDPR, CCPA, and privacy regulations",
            category=ComplianceCategory.DATA_PRIVACY,
            regulatory_reference=RegulatoryFramework.GDPR
        )

        # PII patterns for detection
        self.pii_patterns = {
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "ssn_no_dash": r"\b\d{9}\b",
            "ein": r"\b\d{2}-\d{7}\b",
            "passport": r"\b[A-Z]\d{8}\b",
            "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "phone_us": r"\b(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "dob": r"\b(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])/\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            "bank_account": r"\b\d{8,17}\b",
        }

        # Sensitive data categories
        self.sensitive_categories = {
            "racial_ethnic_origin", "political_opinions", "religious_beliefs",
            "trade_union_membership", "genetic_data", "biometric_data",
            "health_data", "sexual_orientation", "criminal_convictions"
        }

        # Data retention periods (months)
        self.retention_periods = {
            "candidate_data_hired": 84,      # 7 years
            "candidate_data_not_hired": 24,  # 2 years
            "employee_data_active": -1,      # Duration of employment
            "employee_data_terminated": 84,   # 7 years post-termination
            "i9_forms": 36,                  # 3 years after hire or 1 year after term
            "background_checks": 60,          # 5 years
            "payroll_records": 84,            # 7 years
        }

    def applies_to(self, action: str) -> bool:
        return action in [
            "export_data", "send_email", "share_data", "store_data",
            "transfer_data", "delete_data", "access_employee_data",
            "generate_report", "create_document", "send_to_external"
        ]

    def evaluate(self, action: str, payload: Dict, context: Dict) -> ComplianceResult:
        self.evaluations += 1

        # Check data subject location for applicable laws
        data_subject_location = payload.get("data_subject_location", "")
        is_eu = data_subject_location in ["EU", "EEA", "UK"] or payload.get("is_eu_resident", False)
        is_california = data_subject_location == "CA" or payload.get("is_california_resident", False)

        # Check for cross-border transfer
        destination = payload.get("destination", "")
        is_cross_border = destination and destination not in ["US", data_subject_location]

        if is_cross_border and is_eu:
            # GDPR cross-border restrictions
            has_adequacy = payload.get("adequacy_decision", False)
            has_sccs = payload.get("standard_contractual_clauses", False)
            has_bcr = payload.get("binding_corporate_rules", False)

            if not (has_adequacy or has_sccs or has_bcr):
                self.violations += 1
                return ComplianceResult(
                    compliant=False,
                    action=PolicyAction.BLOCK,
                    policy_id=self.policy_id,
                    policy_name=self.name,
                    category=self.category,
                    regulatory_reference=RegulatoryFramework.GDPR,
                    reason="GDPR: Cross-border data transfer requires legal mechanism",
                    required_documentation=[
                        "Standard Contractual Clauses (SCCs)",
                        "Binding Corporate Rules (BCRs)",
                        "Adequacy decision documentation"
                    ],
                    remediation_steps=[
                        "Implement Standard Contractual Clauses with recipient",
                        "Conduct Transfer Impact Assessment",
                        "Document supplementary measures if needed",
                        "Consult with DPO before proceeding"
                    ],
                    risk_score=0.4,
                    required_approval=ApprovalLevel.LEGAL,
                    audit_required=True
                )

        # Check for PII in content
        content_fields = ["body", "message", "content", "data", "text"]
        content = ""
        for field in content_fields:
            if field in payload:
                content += " " + str(payload[field])

        detected_pii = []
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                detected_pii.append(pii_type)

        # Check destination (internal vs external)
        is_external = payload.get("is_external", False)
        recipient = payload.get("to", payload.get("recipient", ""))
        if recipient and "@" in recipient:
            company_domain = context.get("company_domain", "company.com")
            is_external = company_domain not in recipient

        if detected_pii and is_external:
            # PII being sent externally - redact or block
            self.violations += 1

            # Try to redact
            modified_content = content
            for pii_type, pattern in self.pii_patterns.items():
                if pii_type in detected_pii:
                    modified_content = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", modified_content)

            modified_payload = dict(payload)
            for field in content_fields:
                if field in modified_payload:
                    modified_payload[field] = modified_content

            return ComplianceResult(
                compliant=False,
                action=PolicyAction.MODIFY,
                policy_id=self.policy_id,
                policy_name=self.name,
                category=self.category,
                regulatory_reference=RegulatoryFramework.GDPR if is_eu else RegulatoryFramework.CCPA if is_california else None,
                reason=f"PII detected in external communication: {', '.join(detected_pii)}",
                modified_payload=modified_payload,
                remediation_steps=[
                    "PII has been automatically redacted",
                    "Review if data sharing is necessary",
                    "Ensure data processing agreement in place with recipient"
                ],
                risk_score=0.2,
                audit_required=True,
                metadata={"pii_detected": detected_pii, "redacted": True}
            )

        # Check for data export
        if action in ["export_data", "generate_report"]:
            record_count = payload.get("record_count", 0)
            data_type = payload.get("data_type", "")

            if record_count > 100 or any(s in data_type.lower() for s in ["salary", "ssn", "personal", "sensitive"]):
                return ComplianceResult(
                    compliant=True,
                    action=PolicyAction.REQUIRE_APPROVAL,
                    policy_id=self.policy_id,
                    policy_name=self.name,
                    category=self.category,
                    regulatory_reference=RegulatoryFramework.GDPR if is_eu else RegulatoryFramework.CCPA if is_california else None,
                    reason="Bulk data export or sensitive data requires approval",
                    required_approval=ApprovalLevel.LEGAL,
                    remediation_steps=[
                        "Document business justification for export",
                        "Obtain Legal/DPO approval",
                        "Ensure data will be secured appropriately",
                        "Log export in data processing records"
                    ],
                    audit_required=True
                )

        return ComplianceResult(
            compliant=True,
            action=PolicyAction.ALLOW,
            policy_id=self.policy_id,
            policy_name=self.name,
            category=self.category,
            reason="Data handling compliant with privacy requirements",
            audit_required=True
        )


# ═══════════════════════════════════════════════════════════════════════════════
# WORKING TIME COMPLIANCE (FLSA / State Laws)
# ═══════════════════════════════════════════════════════════════════════════════

class WorkingTimePolicy(CompliancePolicy):
    """
    Working Time & Scheduling Compliance

    Frameworks:
    - FLSA (overtime, minimum wage)
    - State meal/rest break laws
    - Predictive scheduling laws
    - Work-life balance policies
    """

    def __init__(self):
        super().__init__(
            policy_id="working_time",
            name="Working Time & Scheduling Compliance",
            description="Ensure scheduling complies with labor laws and company policy",
            category=ComplianceCategory.EMPLOYMENT_LAW,
            regulatory_reference=RegulatoryFramework.FLSA
        )

        # Business hours (company policy)
        self.business_hours = {
            "start": 8,   # 8 AM
            "end": 18,    # 6 PM
            "core_start": 10,  # Core hours start
            "core_end": 16,    # Core hours end
        }

        # States with predictive scheduling
        self.predictive_scheduling_states = {"OR", "CA", "NY", "IL", "WA", "NJ", "VT"}

        # Minimum notice for schedule changes (hours)
        self.schedule_notice_requirements = {
            "OR": 168,  # 7 days
            "CA": 336,  # 14 days (SF)
            "NY": 168,  # 7 days (NYC)
        }

    def applies_to(self, action: str) -> bool:
        return action in [
            "schedule_interview", "schedule_meeting", "set_start_time",
            "schedule_shift", "modify_schedule", "assign_overtime"
        ]

    def evaluate(self, action: str, payload: Dict, context: Dict) -> ComplianceResult:
        self.evaluations += 1

        time_str = payload.get("time") or payload.get("start_time") or payload.get("datetime")

        if not time_str:
            return ComplianceResult(
                compliant=True,
                action=PolicyAction.ALLOW,
                policy_id=self.policy_id,
                policy_name=self.name,
                category=self.category,
                reason="No time specified"
            )

        try:
            if "T" in time_str:
                scheduled_time = datetime.fromisoformat(time_str)
            else:
                scheduled_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        except ValueError:
            return ComplianceResult(
                compliant=True,
                action=PolicyAction.WARN,
                policy_id=self.policy_id,
                policy_name=self.name,
                category=self.category,
                reason="Could not parse scheduled time"
            )

        hour = scheduled_time.hour
        day_of_week = scheduled_time.weekday()  # 0=Monday, 6=Sunday

        # Check weekend
        if day_of_week >= 5:  # Saturday or Sunday
            day_name = "Saturday" if day_of_week == 5 else "Sunday"
            self.violations += 1
            return ComplianceResult(
                compliant=False,
                action=PolicyAction.BLOCK,
                policy_id=self.policy_id,
                policy_name=self.name,
                category=self.category,
                reason=f"Cannot schedule on {day_name} - work-life balance policy",
                remediation_steps=[
                    "Choose a weekday (Monday-Friday)",
                    "If weekend work is essential, obtain manager approval",
                    "Ensure compensatory time off if weekend work approved"
                ],
                risk_score=0.2,
                required_approval=ApprovalLevel.MANAGER if action == "schedule_interview" else ApprovalLevel.DIRECTOR,
                audit_required=True
            )

        # Check business hours
        if hour < self.business_hours["start"] or hour >= self.business_hours["end"]:
            time_period = "before business hours" if hour < self.business_hours["start"] else "after business hours"
            self.violations += 1
            return ComplianceResult(
                compliant=False,
                action=PolicyAction.BLOCK,
                policy_id=self.policy_id,
                policy_name=self.name,
                category=self.category,
                reason=f"Scheduled time ({scheduled_time.strftime('%I:%M %p')}) is {time_period}",
                remediation_steps=[
                    f"Schedule between {self.business_hours['start']}:00 AM and {self.business_hours['end']-12}:00 PM",
                    "Consider time zone differences if applicable",
                    "Respect work-life balance guidelines"
                ],
                risk_score=0.15
            )

        # Check for interview candidate experience
        if action == "schedule_interview":
            # Prefer core hours for candidates
            if not (self.business_hours["core_start"] <= hour < self.business_hours["core_end"]):
                return ComplianceResult(
                    compliant=True,
                    action=PolicyAction.WARN,
                    policy_id=self.policy_id,
                    policy_name=self.name,
                    category=self.category,
                    reason=f"Interview outside core hours ({self.business_hours['core_start']}AM-{self.business_hours['core_end']-12}PM) - consider candidate availability"
                )

        return ComplianceResult(
            compliant=True,
            action=PolicyAction.ALLOW,
            policy_id=self.policy_id,
            policy_name=self.name,
            category=self.category,
            reason="Scheduling compliant with working time policy",
            metadata={"scheduled_time": scheduled_time.isoformat(), "within_core_hours": self.business_hours["core_start"] <= hour < self.business_hours["core_end"]}
        )


# ═══════════════════════════════════════════════════════════════════════════════
# DIVERSITY & INCLUSION COMPLIANCE
# ═══════════════════════════════════════════════════════════════════════════════

class DEICompliancePolicy(CompliancePolicy):
    """
    Diversity, Equity & Inclusion Compliance

    Covers:
    - EEOC non-discrimination requirements
    - OFCCP affirmative action (federal contractors)
    - Inclusive language standards
    - Diverse candidate slate requirements
    - Bias mitigation in hiring
    """

    def __init__(self):
        super().__init__(
            policy_id="dei_compliance",
            name="DEI & Non-Discrimination Compliance",
            description="Ensure hiring practices comply with non-discrimination laws and DEI standards",
            category=ComplianceCategory.DEI_COMPLIANCE,
            regulatory_reference=RegulatoryFramework.EEOC
        )

        # Problematic language (biased or non-inclusive terms)
        self.problematic_terms = {
            # Gendered language
            "he/him": "they/them",
            "she/her": "they/them",
            "manpower": "workforce",
            "man-hours": "person-hours",
            "mankind": "humanity",
            "chairman": "chairperson",
            "salesman": "sales representative",
            "foreman": "supervisor",

            # Ableist language
            "crazy": "unexpected",
            "insane": "remarkable",
            "blind spot": "oversight",
            "tone deaf": "unaware",
            "crippled": "limited",

            # Age-biased
            "young": "",
            "recent graduate": "",
            "digital native": "tech-savvy",
            "energetic": "motivated",

            # Cultural bias
            "rockstar": "high performer",
            "ninja": "expert",
            "guru": "specialist",
            "wizard": "expert",
            "crusade": "initiative",
            "spirit animal": "inspiration",

            # Exclusionary
            "culture fit": "values alignment",
            "native english speaker": "fluent in English",
            "clean-shaven": "",
            "professional appearance": "",
        }

        # Protected characteristics (cannot be used in hiring decisions)
        self.protected_characteristics = {
            "race", "color", "religion", "sex", "national_origin",
            "age", "disability", "genetic_information", "pregnancy",
            "sexual_orientation", "gender_identity", "veteran_status"
        }

    def applies_to(self, action: str) -> bool:
        return action in [
            "post_job", "create_job_posting", "screen_resume", "make_hiring_decision",
            "send_email", "send_communication", "write_feedback", "evaluate_candidate",
            "reject_candidate", "select_candidate"
        ]

    def evaluate(self, action: str, payload: Dict, context: Dict) -> ComplianceResult:
        self.evaluations += 1

        # Check for diverse candidate slate
        if action in ["make_hiring_decision", "select_candidate"]:
            candidate_pool = payload.get("candidate_pool", [])
            diverse_candidates = payload.get("diverse_candidates_interviewed", 0)
            total_interviewed = payload.get("total_interviewed", len(candidate_pool))

            # Rooney Rule check (at least 1 diverse candidate in final round)
            if total_interviewed > 0 and diverse_candidates == 0:
                return ComplianceResult(
                    compliant=False,
                    action=PolicyAction.WARN,
                    policy_id=self.policy_id,
                    policy_name=self.name,
                    category=self.category,
                    regulatory_reference=self.regulatory_reference,
                    reason="Diverse candidate slate requirement: No diverse candidates in interview pool",
                    remediation_steps=[
                        "Expand sourcing to include diverse candidate pipelines",
                        "Review job requirements for unnecessary barriers",
                        "Document good faith efforts to create diverse slate",
                        "Consult with DEI team before proceeding"
                    ],
                    risk_score=0.2,
                    audit_required=True
                )

        # Check for biased language
        text_fields = ["body", "message", "content", "description", "title", "requirements", "qualifications"]
        combined_text = ""
        for field in text_fields:
            if field in payload:
                combined_text += " " + str(payload[field]).lower()

        found_issues = []
        suggestions = []

        for term, replacement in self.problematic_terms.items():
            if term.lower() in combined_text:
                found_issues.append(term)
                if replacement:
                    suggestions.append(f"'{term}' → '{replacement}'")
                else:
                    suggestions.append(f"Remove '{term}'")

        if found_issues:
            self.violations += 1

            # Create modified payload
            modified_payload = dict(payload)
            for field in text_fields:
                if field in modified_payload:
                    text = str(modified_payload[field])
                    for term, replacement in self.problematic_terms.items():
                        if replacement:
                            text = re.sub(rf"\b{re.escape(term)}\b", replacement, text, flags=re.IGNORECASE)
                        else:
                            text = re.sub(rf"\b{re.escape(term)}\b\s*", "", text, flags=re.IGNORECASE)
                    modified_payload[field] = text

            return ComplianceResult(
                compliant=False,
                action=PolicyAction.MODIFY,
                policy_id=self.policy_id,
                policy_name=self.name,
                category=self.category,
                regulatory_reference=self.regulatory_reference,
                reason=f"Non-inclusive language detected: {', '.join(found_issues[:5])}",
                modified_payload=modified_payload,
                remediation_steps=["Language has been automatically updated"] + suggestions[:5],
                risk_score=0.1,
                audit_required=True,
                metadata={"terms_found": found_issues, "suggestions": suggestions}
            )

        # Check for protected characteristic mentions in hiring
        if action in ["screen_resume", "evaluate_candidate", "reject_candidate"]:
            reason = payload.get("reason", "").lower()
            notes = payload.get("notes", "").lower()
            evaluation_text = reason + " " + notes

            for characteristic in self.protected_characteristics:
                if characteristic.replace("_", " ") in evaluation_text:
                    self.violations += 1
                    return ComplianceResult(
                        compliant=False,
                        action=PolicyAction.BLOCK,
                        policy_id=self.policy_id,
                        policy_name=self.name,
                        category=self.category,
                        regulatory_reference=self.regulatory_reference,
                        reason=f"EEOC Violation: Reference to protected characteristic ({characteristic}) in hiring evaluation",
                        remediation_steps=[
                            "Remove any reference to protected characteristics",
                            "Base evaluation solely on job-related criteria",
                            "Document objective, job-related reasons for decision",
                            "Consult with Legal/HR before proceeding"
                        ],
                        risk_score=0.5,
                        required_approval=ApprovalLevel.LEGAL,
                        audit_required=True
                    )

        return ComplianceResult(
            compliant=True,
            action=PolicyAction.ALLOW,
            policy_id=self.policy_id,
            policy_name=self.name,
            category=self.category,
            reason="Communication compliant with DEI standards"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCIAL CONTROLS (SOX-inspired)
# ═══════════════════════════════════════════════════════════════════════════════

class FinancialControlsPolicy(CompliancePolicy):
    """
    Financial Controls Policy

    Covers:
    - Signing bonus limits
    - Relocation package limits
    - Approval hierarchies
    - Segregation of duties
    - Audit trail requirements
    """

    def __init__(self):
        super().__init__(
            policy_id="financial_controls",
            name="Financial Controls & Approval Policy",
            description="Ensure financial commitments follow approval hierarchy and limits",
            category=ComplianceCategory.FINANCIAL_CONTROLS,
            regulatory_reference=RegulatoryFramework.SOX
        )

        # Signing bonus limits by level
        self.signing_bonus_limits = {
            "IC1": 5000,
            "IC2": 10000,
            "IC3": 15000,
            "IC4": 25000,
            "IC5": 50000,
            "IC6": 75000,
            "M1": 20000,
            "M2": 35000,
            "M3": 50000,
            "D1": 75000,
            "VP": 100000,
        }

        # Relocation limits
        self.relocation_limits = {
            "domestic": {
                "IC": 15000,
                "M": 25000,
                "D": 40000,
                "VP": 75000,
            },
            "international": {
                "IC": 50000,
                "M": 75000,
                "D": 100000,
                "VP": 150000,
            }
        }

        # Approval thresholds (total commitment value)
        self.approval_thresholds = [
            (50000, ApprovalLevel.MANAGER),
            (100000, ApprovalLevel.DIRECTOR),
            (250000, ApprovalLevel.VP),
            (500000, ApprovalLevel.C_LEVEL),
            (1000000, ApprovalLevel.BOARD),
        ]

    def applies_to(self, action: str) -> bool:
        return action in [
            "generate_offer", "create_offer", "approve_signing_bonus",
            "approve_relocation", "process_expense", "approve_expense",
            "commit_budget", "process_payment"
        ]

    def evaluate(self, action: str, payload: Dict, context: Dict) -> ComplianceResult:
        self.evaluations += 1

        level = payload.get("level", "IC4")
        level_prefix = level[:2] if len(level) >= 2 else level[0]

        # Calculate total commitment
        salary = payload.get("salary", 0)
        signing_bonus = payload.get("signing_bonus", 0)
        relocation = payload.get("relocation", 0)
        equity_value = payload.get("equity_value", 0)

        total_commitment = signing_bonus + relocation + equity_value

        issues = []

        # Check signing bonus limit
        if signing_bonus > 0 and level in self.signing_bonus_limits:
            limit = self.signing_bonus_limits[level]
            if signing_bonus > limit:
                issues.append(f"Signing bonus ${signing_bonus:,} exceeds {level} limit of ${limit:,}")

        # Check relocation limit
        if relocation > 0:
            reloc_type = payload.get("relocation_type", "domestic")
            reloc_limits = self.relocation_limits.get(reloc_type, self.relocation_limits["domestic"])
            limit = reloc_limits.get(level_prefix, reloc_limits.get("IC", 15000))
            if relocation > limit:
                issues.append(f"Relocation ${relocation:,} exceeds {level_prefix}/{reloc_type} limit of ${limit:,}")

        if issues:
            self.violations += 1
            return ComplianceResult(
                compliant=False,
                action=PolicyAction.REQUIRE_APPROVAL,
                policy_id=self.policy_id,
                policy_name=self.name,
                category=self.category,
                reason="; ".join(issues),
                required_approval=ApprovalLevel.VP,
                remediation_steps=[
                    "Obtain exception approval from VP or above",
                    "Document business justification",
                    "Confirm budget availability"
                ],
                risk_score=0.2,
                audit_required=True
            )

        # Determine required approval level based on total commitment
        required_approval = ApprovalLevel.NONE
        for threshold, approval_level in self.approval_thresholds:
            if total_commitment >= threshold:
                required_approval = approval_level

        if required_approval != ApprovalLevel.NONE:
            return ComplianceResult(
                compliant=True,
                action=PolicyAction.REQUIRE_APPROVAL,
                policy_id=self.policy_id,
                policy_name=self.name,
                category=self.category,
                reason=f"Total commitment ${total_commitment:,} requires {required_approval.value} approval",
                required_approval=required_approval,
                audit_required=True,
                metadata={"total_commitment": total_commitment}
            )

        return ComplianceResult(
            compliant=True,
            action=PolicyAction.ALLOW,
            policy_id=self.policy_id,
            policy_name=self.name,
            category=self.category,
            reason="Financial commitment within policy limits",
            audit_required=True
        )


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class ComplianceEngine:
    """
    Enterprise Compliance Engine

    Evaluates all applicable compliance policies and returns
    the combined result with all requirements.
    """

    def __init__(self):
        self.policies: Dict[str, CompliancePolicy] = {}
        self.evaluation_history: List[Dict] = []
        self._register_default_policies()
        logger.info(f"Compliance Engine initialized with {len(self.policies)} policies")

    def _register_default_policies(self):
        """Register all compliance policies."""
        policies = [
            I9CompliancePolicy(),
            BackgroundCheckPolicy(),
            CompensationCompliancePolicy(),
            DataPrivacyPolicy(),
            WorkingTimePolicy(),
            DEICompliancePolicy(),
            FinancialControlsPolicy(),
        ]

        for policy in policies:
            self.register(policy)

    def register(self, policy: CompliancePolicy):
        """Register a compliance policy."""
        self.policies[policy.policy_id] = policy
        logger.info(f"Registered compliance policy: {policy.name}")

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Tuple[ComplianceResult, List[ComplianceResult]]:
        """
        Evaluate all applicable compliance policies.

        Returns:
            Tuple of (final_result, all_results)
        """
        context = context or {}
        all_results = []

        for policy in self.policies.values():
            if not policy.enabled:
                continue

            if policy.applies_to(action):
                result = policy.evaluate(action, payload, context)
                all_results.append(result)

                self.evaluation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": action,
                    "policy_id": policy.policy_id,
                    "compliant": result.compliant,
                    "action_taken": result.action.value
                })

        if not all_results:
            return ComplianceResult(
                compliant=True,
                action=PolicyAction.ALLOW,
                policy_id="default",
                policy_name="No Applicable Policy",
                category=ComplianceCategory.INTERNAL_POLICY,
                reason="No compliance policies apply to this action"
            ), []

        # Sort by severity (BLOCK > ESCALATE > REQUIRE_APPROVAL > MODIFY > WARN > ALLOW)
        priority = {
            PolicyAction.BLOCK: 7,
            PolicyAction.ESCALATE: 6,
            PolicyAction.REQUIRE_APPROVAL: 5,
            PolicyAction.REQUIRE_DOCUMENTATION: 4,
            PolicyAction.MODIFY: 3,
            PolicyAction.WARN: 2,
            PolicyAction.AUDIT_LOG: 1,
            PolicyAction.ALLOW: 0,
        }

        all_results.sort(key=lambda r: priority.get(r.action, 0), reverse=True)

        # Aggregate results
        final = all_results[0]

        # Collect all required documentation
        all_docs = []
        for result in all_results:
            all_docs.extend(result.required_documentation)
        final.required_documentation = list(set(all_docs))

        # Collect all remediation steps
        all_steps = []
        for result in all_results:
            all_steps.extend(result.remediation_steps)
        final.remediation_steps = all_steps[:10]  # Limit to top 10

        # Aggregate risk
        final.risk_score = sum(r.risk_score for r in all_results)

        # Take highest approval level
        approval_priority = list(ApprovalLevel)
        for result in all_results:
            if result.required_approval:
                if final.required_approval is None:
                    final.required_approval = result.required_approval
                elif approval_priority.index(result.required_approval) > approval_priority.index(final.required_approval):
                    final.required_approval = result.required_approval

        # Set audit required if any policy requires it
        final.audit_required = any(r.audit_required for r in all_results)

        # Use modified payload if any
        for result in all_results:
            if result.modified_payload:
                final.modified_payload = result.modified_payload
                break

        return final, all_results

    def get_policy_stats(self) -> Dict:
        """Get compliance statistics."""
        return {
            "total_policies": len(self.policies),
            "by_category": {
                cat.value: len([p for p in self.policies.values() if p.category == cat])
                for cat in ComplianceCategory
            },
            "total_evaluations": sum(p.evaluations for p in self.policies.values()),
            "total_violations": sum(p.violations for p in self.policies.values()),
            "policies": [p.to_dict() for p in self.policies.values()]
        }

    def get_regulatory_coverage(self) -> Dict:
        """Get which regulatory frameworks are covered."""
        coverage = {}
        for policy in self.policies.values():
            if policy.regulatory_reference:
                ref = policy.regulatory_reference
                if ref not in coverage:
                    coverage[ref.value] = []
                coverage[ref.value].append(policy.name)
        return coverage


# Singleton
_compliance_engine = None

def get_compliance_engine() -> ComplianceEngine:
    global _compliance_engine
    if _compliance_engine is None:
        _compliance_engine = ComplianceEngine()
    return _compliance_engine
