"""
Compliance Tools
Tools for regulatory compliance checking.
"""

from typing import Dict, List, Any, Optional

from services.firestore_service import get_firestore_service


# Compliance frameworks with their requirements
COMPLIANCE_FRAMEWORKS = {
    "GDPR": {
        "name": "General Data Protection Regulation",
        "region": "EU",
        "requirements": [
            {
                "id": "gdpr_lawful_basis",
                "requirement": "Lawful basis for processing",
                "description": "Contract must specify the lawful basis for processing personal data",
                "keywords": ["lawful basis", "legitimate interest", "consent", "contractual necessity"]
            },
            {
                "id": "gdpr_data_subject_rights",
                "requirement": "Data subject rights",
                "description": "Must include provisions for data subject rights (access, rectification, erasure, etc.)",
                "keywords": ["right to access", "right to erasure", "data portability", "right to object"]
            },
            {
                "id": "gdpr_data_transfers",
                "requirement": "International data transfers",
                "description": "Must address cross-border data transfers with appropriate safeguards",
                "keywords": ["data transfer", "standard contractual clauses", "adequacy decision", "binding corporate rules"]
            },
            {
                "id": "gdpr_data_breach",
                "requirement": "Data breach notification",
                "description": "Must include data breach notification procedures",
                "keywords": ["data breach", "security incident", "notification", "72 hours"]
            },
            {
                "id": "gdpr_dpa",
                "requirement": "Data Processing Agreement",
                "description": "Must include a DPA when engaging data processors",
                "keywords": ["data processing agreement", "processor", "sub-processor", "processing instructions"]
            },
            {
                "id": "gdpr_retention",
                "requirement": "Data retention policy",
                "description": "Must specify data retention periods and deletion procedures",
                "keywords": ["retention", "deletion", "data minimization", "storage limitation"]
            }
        ]
    },
    "HIPAA": {
        "name": "Health Insurance Portability and Accountability Act",
        "region": "USA",
        "requirements": [
            {
                "id": "hipaa_phi_definition",
                "requirement": "PHI definition and scope",
                "description": "Must define Protected Health Information and its handling",
                "keywords": ["protected health information", "phi", "health data", "medical records"]
            },
            {
                "id": "hipaa_baa",
                "requirement": "Business Associate Agreement",
                "description": "Must include BAA for business associates handling PHI",
                "keywords": ["business associate", "baa", "covered entity", "subcontractor"]
            },
            {
                "id": "hipaa_safeguards",
                "requirement": "Security safeguards",
                "description": "Must specify administrative, physical, and technical safeguards",
                "keywords": ["security rule", "safeguards", "encryption", "access controls"]
            },
            {
                "id": "hipaa_breach",
                "requirement": "Breach notification",
                "description": "Must include breach notification requirements",
                "keywords": ["breach notification", "security incident", "hhs notification"]
            },
            {
                "id": "hipaa_minimum_necessary",
                "requirement": "Minimum necessary standard",
                "description": "Must limit PHI disclosure to minimum necessary",
                "keywords": ["minimum necessary", "limited disclosure", "need to know"]
            }
        ]
    },
    "CCPA": {
        "name": "California Consumer Privacy Act",
        "region": "California, USA",
        "requirements": [
            {
                "id": "ccpa_categories",
                "requirement": "Categories of personal information",
                "description": "Must disclose categories of personal information collected",
                "keywords": ["categories of information", "personal information", "data collected"]
            },
            {
                "id": "ccpa_consumer_rights",
                "requirement": "Consumer rights",
                "description": "Must respect consumer rights to know, delete, and opt-out",
                "keywords": ["right to know", "right to delete", "opt-out", "do not sell"]
            },
            {
                "id": "ccpa_service_provider",
                "requirement": "Service provider requirements",
                "description": "Must include service provider contractual requirements",
                "keywords": ["service provider", "business purpose", "written contract"]
            }
        ]
    },
    "SOX": {
        "name": "Sarbanes-Oxley Act",
        "region": "USA",
        "requirements": [
            {
                "id": "sox_financial_controls",
                "requirement": "Internal financial controls",
                "description": "Must address internal controls for financial reporting",
                "keywords": ["internal controls", "financial reporting", "audit", "compliance"]
            },
            {
                "id": "sox_records_retention",
                "requirement": "Records retention",
                "description": "Must specify records retention requirements",
                "keywords": ["records retention", "document retention", "audit trail"]
            }
        ]
    }
}


async def check_compliance(
    contract_id: str,
    content: str,
    frameworks: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Check contract compliance against regulatory frameworks.
    
    Args:
        contract_id: The contract ID
        content: Contract text content
        frameworks: List of frameworks to check (default: all)
        
    Returns:
        Compliance assessment results
    """
    firestore = get_firestore_service()
    
    # Default to all frameworks if none specified
    if not frameworks:
        frameworks = list(COMPLIANCE_FRAMEWORKS.keys())
    
    content_lower = content.lower()
    results = {}
    
    for framework_key in frameworks:
        if framework_key not in COMPLIANCE_FRAMEWORKS:
            continue
        
        framework = COMPLIANCE_FRAMEWORKS[framework_key]
        framework_results = {
            "name": framework["name"],
            "region": framework["region"],
            "requirements": [],
            "compliant_count": 0,
            "non_compliant_count": 0,
            "partial_count": 0,
        }
        
        for req in framework["requirements"]:
            # Check if keywords are present
            matches = sum(1 for kw in req["keywords"] if kw in content_lower)
            total_keywords = len(req["keywords"])
            
            if matches == 0:
                status = "non-compliant"
                framework_results["non_compliant_count"] += 1
            elif matches < total_keywords / 2:
                status = "partial"
                framework_results["partial_count"] += 1
            else:
                status = "compliant"
                framework_results["compliant_count"] += 1
            
            framework_results["requirements"].append({
                "id": req["id"],
                "requirement": req["requirement"],
                "description": req["description"],
                "status": status,
                "matched_keywords": matches,
                "total_keywords": total_keywords,
            })
        
        # Calculate overall framework compliance
        total = len(framework["requirements"])
        if framework_results["non_compliant_count"] == 0 and framework_results["partial_count"] == 0:
            framework_results["overall_status"] = "compliant"
        elif framework_results["compliant_count"] == 0:
            framework_results["overall_status"] = "non-compliant"
        else:
            framework_results["overall_status"] = "partial"
        
        results[framework_key] = framework_results
    
    # Calculate overall compliance score
    total_requirements = sum(
        len(COMPLIANCE_FRAMEWORKS[f]["requirements"])
        for f in frameworks if f in COMPLIANCE_FRAMEWORKS
    )
    compliant_total = sum(r["compliant_count"] for r in results.values())
    
    overall_score = (compliant_total / total_requirements * 100) if total_requirements > 0 else 0
    
    # Determine overall status
    if overall_score >= 80:
        overall_status = "compliant"
    elif overall_score >= 50:
        overall_status = "partial"
    else:
        overall_status = "non-compliant"
    
    # Update contract with compliance status
    await firestore.update_document(
        firestore.CONTRACTS,
        contract_id,
        {
            "compliance_status": overall_status,
            "compliance_score": overall_score,
            "compliance_details": results,
        }
    )
    
    return {
        "status": "success",
        "contract_id": contract_id,
        "overall_status": overall_status,
        "overall_score": round(overall_score, 2),
        "frameworks": results,
    }


async def get_compliance_requirements(
    framework: str
) -> Dict[str, Any]:
    """Get compliance requirements for a specific framework.
    
    Args:
        framework: Framework name (GDPR, HIPAA, CCPA, SOX)
        
    Returns:
        Framework requirements
    """
    framework_upper = framework.upper()
    
    if framework_upper not in COMPLIANCE_FRAMEWORKS:
        return {
            "status": "error",
            "message": f"Unknown framework: {framework}. Available: {', '.join(COMPLIANCE_FRAMEWORKS.keys())}"
        }
    
    return {
        "status": "success",
        "framework": framework_upper,
        **COMPLIANCE_FRAMEWORKS[framework_upper]
    }


async def list_compliance_frameworks() -> Dict[str, Any]:
    """List all available compliance frameworks.
    
    Returns:
        List of frameworks with summaries
    """
    frameworks = []
    
    for key, framework in COMPLIANCE_FRAMEWORKS.items():
        frameworks.append({
            "key": key,
            "name": framework["name"],
            "region": framework["region"],
            "requirement_count": len(framework["requirements"]),
        })
    
    return {
        "status": "success",
        "frameworks": frameworks,
        "count": len(frameworks)
    }


async def check_specific_requirement(
    content: str,
    requirement_id: str,
) -> Dict[str, Any]:
    """Check contract against a specific compliance requirement.
    
    Args:
        content: Contract text content
        requirement_id: The requirement ID to check
        
    Returns:
        Compliance check result for that requirement
    """
    # Find the requirement
    requirement = None
    framework_key = None
    
    for fw_key, framework in COMPLIANCE_FRAMEWORKS.items():
        for req in framework["requirements"]:
            if req["id"] == requirement_id:
                requirement = req
                framework_key = fw_key
                break
        if requirement:
            break
    
    if not requirement:
        return {
            "status": "error",
            "message": f"Requirement {requirement_id} not found"
        }
    
    content_lower = content.lower()
    matches = sum(1 for kw in requirement["keywords"] if kw in content_lower)
    total_keywords = len(requirement["keywords"])
    
    if matches == 0:
        status = "non-compliant"
        recommendation = f"Contract does not address {requirement['requirement']}. Consider adding relevant provisions."
    elif matches < total_keywords / 2:
        status = "partial"
        recommendation = f"Contract partially addresses {requirement['requirement']}. Consider strengthening the language."
    else:
        status = "compliant"
        recommendation = f"Contract adequately addresses {requirement['requirement']}."
    
    return {
        "status": "success",
        "framework": framework_key,
        "requirement": requirement,
        "compliance_status": status,
        "matched_keywords": matches,
        "total_keywords": total_keywords,
        "recommendation": recommendation,
    }


async def get_compliance_recommendations(
    contract_id: str,
) -> Dict[str, Any]:
    """Get compliance improvement recommendations for a contract.
    
    Args:
        contract_id: The contract ID
        
    Returns:
        List of recommendations
    """
    firestore = get_firestore_service()
    contract = await firestore.get_contract(contract_id)
    
    if not contract:
        return {
            "status": "error",
            "message": f"Contract {contract_id} not found"
        }
    
    compliance_details = contract.get("compliance_details", {})
    recommendations = []
    
    for framework_key, framework_result in compliance_details.items():
        for req in framework_result.get("requirements", []):
            if req["status"] in ["non-compliant", "partial"]:
                priority = "high" if req["status"] == "non-compliant" else "medium"
                
                recommendations.append({
                    "framework": framework_key,
                    "requirement_id": req["id"],
                    "requirement": req["requirement"],
                    "description": req["description"],
                    "current_status": req["status"],
                    "priority": priority,
                    "action": f"Add or strengthen provisions for {req['requirement']}",
                })
    
    # Sort by priority
    recommendations.sort(key=lambda x: 0 if x["priority"] == "high" else 1)
    
    return {
        "status": "success",
        "contract_id": contract_id,
        "recommendations": recommendations,
        "count": len(recommendations),
        "high_priority_count": len([r for r in recommendations if r["priority"] == "high"]),
    }


# Tool definitions for Gemini function calling
COMPLIANCE_TOOLS = [
    {
        "name": "check_compliance",
        "description": "Check contract compliance against regulatory frameworks (GDPR, HIPAA, CCPA, SOX). Analyzes contract text and identifies compliant/non-compliant areas.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "string",
                    "description": "The contract ID"
                },
                "content": {
                    "type": "string",
                    "description": "Contract text content to analyze"
                },
                "frameworks": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["GDPR", "HIPAA", "CCPA", "SOX"]
                    },
                    "description": "Frameworks to check against (default: all)"
                }
            },
            "required": ["contract_id", "content"]
        },
        "handler": check_compliance
    },
    {
        "name": "get_compliance_requirements",
        "description": "Get detailed requirements for a specific compliance framework.",
        "parameters": {
            "type": "object",
            "properties": {
                "framework": {
                    "type": "string",
                    "description": "Framework name",
                    "enum": ["GDPR", "HIPAA", "CCPA", "SOX"]
                }
            },
            "required": ["framework"]
        },
        "handler": get_compliance_requirements
    },
    {
        "name": "list_compliance_frameworks",
        "description": "List all available compliance frameworks with summaries.",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "handler": list_compliance_frameworks
    },
    {
        "name": "check_specific_requirement",
        "description": "Check contract against a specific compliance requirement ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Contract text content"
                },
                "requirement_id": {
                    "type": "string",
                    "description": "The requirement ID to check (e.g., gdpr_data_breach)"
                }
            },
            "required": ["content", "requirement_id"]
        },
        "handler": check_specific_requirement
    },
    {
        "name": "get_compliance_recommendations",
        "description": "Get actionable recommendations to improve contract compliance.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "string",
                    "description": "The contract ID"
                }
            },
            "required": ["contract_id"]
        },
        "handler": get_compliance_recommendations
    }
]


def get_compliance_tools() -> List[Dict[str, Any]]:
    """Get all compliance tool definitions."""
    return COMPLIANCE_TOOLS


# Export for tool registry
TOOL_DEFINITIONS = COMPLIANCE_TOOLS
