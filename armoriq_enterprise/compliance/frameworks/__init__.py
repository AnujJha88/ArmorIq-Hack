"""
Regulatory Compliance Frameworks
================================
Pre-configured policy sets for regulatory compliance.
"""

from typing import List
from ..policies.base import Policy


def get_sox_framework() -> List[Policy]:
    """Get SOX compliance policies."""
    from ..policies.financial import (
        SOXSeparationOfDutiesPolicy,
        ExpenseLimitPolicy,
        InvoiceApprovalPolicy,
    )
    return [
        SOXSeparationOfDutiesPolicy(),
        ExpenseLimitPolicy(),
        InvoiceApprovalPolicy(),
    ]


def get_gdpr_framework() -> List[Policy]:
    """Get GDPR compliance policies."""
    from ..policies.data_privacy import (
        GDPRPolicy,
        PIIProtectionPolicy,
        DataRetentionPolicy,
    )
    return [
        GDPRPolicy(),
        PIIProtectionPolicy(),
        DataRetentionPolicy(),
    ]


def get_hipaa_framework() -> List[Policy]:
    """Get HIPAA compliance policies."""
    from ..policies.data_privacy import HIPAAPolicy, PIIProtectionPolicy
    from ..policies.security import AccessControlPolicy, DataClassificationPolicy
    return [
        HIPAAPolicy(),
        PIIProtectionPolicy(),
        AccessControlPolicy(),
        DataClassificationPolicy(),
    ]


def get_pci_dss_framework() -> List[Policy]:
    """Get PCI-DSS compliance policies."""
    from ..policies.data_privacy import PIIProtectionPolicy
    from ..policies.security import AccessControlPolicy, DataClassificationPolicy
    return [
        PIIProtectionPolicy(),
        AccessControlPolicy(),
        DataClassificationPolicy(),
    ]


def get_iso27001_framework() -> List[Policy]:
    """Get ISO 27001 compliance policies."""
    from ..policies.security import (
        AccessControlPolicy,
        DataClassificationPolicy,
        ChangeManagementPolicy,
        IncidentResponsePolicy,
    )
    return [
        AccessControlPolicy(),
        DataClassificationPolicy(),
        ChangeManagementPolicy(),
        IncidentResponsePolicy(),
    ]
