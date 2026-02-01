"""
Risk Tools
Tools for risk assessment and analysis.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from services.firestore_service import get_firestore_service


# Risk patterns and indicators
RISK_INDICATORS = {
    "high_liability": {
        "description": "Clauses that expose party to significant liability",
        "patterns": [
            "unlimited liability",
            "all damages",
            "consequential damages",
            "punitive damages",
            "no cap",
            "full indemnification",
        ],
        "base_score": 25,
    },
    "weak_termination": {
        "description": "Unfavorable termination terms",
        "patterns": [
            "no termination for convenience",
            "automatic renewal",
            "long notice period",
            "penalty for termination",
            "termination fee",
        ],
        "base_score": 20,
    },
    "one_sided": {
        "description": "One-sided or unfair terms",
        "patterns": [
            "sole discretion",
            "unilateral",
            "at any time without notice",
            "non-negotiable",
            "as we see fit",
        ],
        "base_score": 20,
    },
    "ip_risk": {
        "description": "Intellectual property ownership risks",
        "patterns": [
            "work for hire",
            "all ip belongs",
            "transfer of ownership",
            "assigns all rights",
            "perpetual license",
        ],
        "base_score": 20,
    },
    "data_risk": {
        "description": "Data handling and privacy risks",
        "patterns": [
            "share with third parties",
            "no encryption",
            "unlimited retention",
            "no deletion",
            "transfer outside",
        ],
        "base_score": 20,
    },
    "vague_language": {
        "description": "Ambiguous or vague language that could be exploited",
        "patterns": [
            "reasonable efforts",
            "as appropriate",
            "may include",
            "generally",
            "to the extent possible",
            "best efforts",
        ],
        "base_score": 10,
    },
    "missing_protection": {
        "description": "Missing standard protections",
        "patterns": [
            "no warranty",
            "as is",
            "no representation",
            "waives all claims",
            "releases all liability",
        ],
        "base_score": 25,
    },
    "dispute_risk": {
        "description": "Unfavorable dispute resolution terms",
        "patterns": [
            "binding arbitration",
            "waive jury trial",
            "class action waiver",
            "inconvenient venue",
            "foreign jurisdiction",
        ],
        "base_score": 15,
    },
}


async def assess_contract_risk(
    contract_id: str,
    content: str,
) -> Dict[str, Any]:
    """Perform comprehensive risk assessment on contract.
    
    Args:
        contract_id: The contract ID
        content: Contract text content
        
    Returns:
        Detailed risk assessment
    """
    firestore = get_firestore_service()
    
    content_lower = content.lower()
    risk_findings = []
    total_score = 0
    
    for risk_type, risk_info in RISK_INDICATORS.items():
        matches = []
        for pattern in risk_info["patterns"]:
            if pattern in content_lower:
                # Find context around the match
                idx = content_lower.find(pattern)
                start = max(0, idx - 100)
                end = min(len(content), idx + len(pattern) + 100)
                context = content[start:end]
                
                matches.append({
                    "pattern": pattern,
                    "context": f"...{context}...",
                })
        
        if matches:
            score = risk_info["base_score"] * min(len(matches), 3)  # Cap at 3x
            total_score += score
            
            risk_findings.append({
                "risk_type": risk_type,
                "description": risk_info["description"],
                "score": score,
                "matches": matches,
                "severity": _get_severity(score),
            })
    
    # Calculate overall risk level
    overall_score = min(100, total_score)
    overall_level = _get_risk_level(overall_score)
    
    # Generate recommendations
    recommendations = _generate_risk_recommendations(risk_findings)
    
    # Update contract with risk assessment
    await firestore.update_document(
        firestore.CONTRACTS,
        contract_id,
        {
            "overall_risk_score": overall_score,
            "risk_level": overall_level,
            "risk_findings": risk_findings,
            "risk_assessment_date": datetime.utcnow().isoformat(),
        }
    )
    
    return {
        "status": "success",
        "contract_id": contract_id,
        "overall_risk_score": overall_score,
        "overall_risk_level": overall_level,
        "findings": risk_findings,
        "finding_count": len(risk_findings),
        "recommendations": recommendations,
    }


def _get_severity(score: int) -> str:
    """Get severity level from score."""
    if score >= 50:
        return "critical"
    elif score >= 30:
        return "high"
    elif score >= 15:
        return "medium"
    return "low"


def _get_risk_level(score: int) -> str:
    """Get overall risk level from total score."""
    if score >= 75:
        return "critical"
    elif score >= 50:
        return "high"
    elif score >= 25:
        return "medium"
    return "low"


def _generate_risk_recommendations(findings: List[Dict]) -> List[Dict]:
    """Generate recommendations based on risk findings."""
    recommendations = []
    
    recommendation_templates = {
        "high_liability": {
            "action": "Negotiate liability caps",
            "detail": "Request a cap on liability, typically limited to the contract value or a multiple thereof. Exclude consequential damages."
        },
        "weak_termination": {
            "action": "Improve termination rights",
            "detail": "Add termination for convenience with reasonable notice (30-90 days). Remove or reduce termination penalties."
        },
        "one_sided": {
            "action": "Balance contract terms",
            "detail": "Negotiate mutual rights where possible. Add 'reasonable' qualifiers to discretionary terms."
        },
        "ip_risk": {
            "action": "Clarify IP ownership",
            "detail": "Clearly define IP ownership boundaries. Consider joint ownership or license back provisions."
        },
        "data_risk": {
            "action": "Strengthen data protections",
            "detail": "Add data security requirements, retention limits, and deletion rights. Restrict third-party sharing."
        },
        "vague_language": {
            "action": "Clarify ambiguous terms",
            "detail": "Replace vague terms with specific, measurable criteria. Define what constitutes 'reasonable'."
        },
        "missing_protection": {
            "action": "Add standard protections",
            "detail": "Request basic warranties and representations. Avoid blanket waivers without negotiation."
        },
        "dispute_risk": {
            "action": "Improve dispute resolution",
            "detail": "Negotiate a favorable or neutral venue. Consider mediation before arbitration. Review jury waiver."
        },
    }
    
    for finding in findings:
        risk_type = finding["risk_type"]
        if risk_type in recommendation_templates:
            template = recommendation_templates[risk_type]
            recommendations.append({
                "risk_type": risk_type,
                "severity": finding["severity"],
                "action": template["action"],
                "detail": template["detail"],
                "priority": "high" if finding["severity"] in ["critical", "high"] else "medium",
            })
    
    # Sort by priority
    recommendations.sort(key=lambda x: 0 if x["priority"] == "high" else 1)
    
    return recommendations


async def assess_clause_risk(
    clause_id: str,
    content: str,
) -> Dict[str, Any]:
    """Assess risk for a specific clause.
    
    Args:
        clause_id: The clause ID
        content: Clause text content
        
    Returns:
        Clause risk assessment
    """
    firestore = get_firestore_service()
    
    content_lower = content.lower()
    risk_factors = []
    total_score = 0
    
    for risk_type, risk_info in RISK_INDICATORS.items():
        for pattern in risk_info["patterns"]:
            if pattern in content_lower:
                risk_factors.append({
                    "type": risk_type,
                    "pattern": pattern,
                    "description": risk_info["description"],
                })
                total_score += risk_info["base_score"] / 2  # Lower weight for clause-level
                break  # Count each risk type once per clause
    
    # Determine risk level
    score = min(100, int(total_score))
    level = _get_risk_level(score)
    
    # Update clause with risk assessment
    explanation = "; ".join([f["description"] for f in risk_factors]) if risk_factors else "No significant risks identified"
    
    await firestore.update_document(
        firestore.CLAUSES,
        clause_id,
        {
            "risk_level": level,
            "risk_score": score,
            "risk_explanation": explanation,
        }
    )
    
    return {
        "status": "success",
        "clause_id": clause_id,
        "risk_score": score,
        "risk_level": level,
        "risk_factors": risk_factors,
        "explanation": explanation,
    }


async def get_contract_risk_summary(
    contract_id: str,
) -> Dict[str, Any]:
    """Get risk summary for a contract.
    
    Args:
        contract_id: The contract ID
        
    Returns:
        Risk summary with statistics
    """
    firestore = get_firestore_service()
    
    contract = await firestore.get_contract(contract_id)
    if not contract:
        return {
            "status": "error",
            "message": f"Contract {contract_id} not found"
        }
    
    # Get clause risk distribution
    clauses = await firestore.get_clauses_for_contract(contract_id)
    
    risk_distribution = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0,
    }
    
    for clause in clauses:
        level = clause.get("risk_level", "low")
        if level in risk_distribution:
            risk_distribution[level] += 1
    
    return {
        "status": "success",
        "contract_id": contract_id,
        "overall_risk_score": contract.get("overall_risk_score"),
        "overall_risk_level": contract.get("risk_level"),
        "assessment_date": contract.get("risk_assessment_date"),
        "clause_count": len(clauses),
        "risk_distribution": risk_distribution,
        "high_risk_clause_count": risk_distribution["high"] + risk_distribution["critical"],
        "findings": contract.get("risk_findings", []),
    }


async def compare_contract_risks(
    contract_ids: List[str],
) -> Dict[str, Any]:
    """Compare risks across multiple contracts.
    
    Args:
        contract_ids: List of contract IDs to compare
        
    Returns:
        Comparative risk analysis
    """
    firestore = get_firestore_service()
    
    comparisons = []
    
    for contract_id in contract_ids:
        contract = await firestore.get_contract(contract_id)
        if contract:
            comparisons.append({
                "contract_id": contract_id,
                "title": contract.get("title"),
                "overall_risk_score": contract.get("overall_risk_score", 0),
                "overall_risk_level": contract.get("risk_level", "unknown"),
                "finding_count": len(contract.get("risk_findings", [])),
            })
    
    # Sort by risk score (highest first)
    comparisons.sort(key=lambda x: x.get("overall_risk_score", 0), reverse=True)
    
    # Calculate statistics
    scores = [c.get("overall_risk_score", 0) for c in comparisons if c.get("overall_risk_score")]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    return {
        "status": "success",
        "contracts": comparisons,
        "count": len(comparisons),
        "average_risk_score": round(avg_score, 2),
        "highest_risk": comparisons[0] if comparisons else None,
        "lowest_risk": comparisons[-1] if comparisons else None,
    }


# Tool definitions for Gemini function calling
RISK_TOOLS = [
    {
        "name": "assess_contract_risk",
        "description": "Perform comprehensive risk assessment on a contract. Identifies liability risks, unfair terms, IP issues, data risks, and more.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "string",
                    "description": "The contract ID"
                },
                "content": {
                    "type": "string",
                    "description": "Full contract text content"
                }
            },
            "required": ["contract_id", "content"]
        },
        "handler": assess_contract_risk
    },
    {
        "name": "assess_clause_risk",
        "description": "Assess risk for a specific clause. Identifies risk factors and provides risk score.",
        "parameters": {
            "type": "object",
            "properties": {
                "clause_id": {
                    "type": "string",
                    "description": "The clause ID"
                },
                "content": {
                    "type": "string",
                    "description": "Clause text content"
                }
            },
            "required": ["clause_id", "content"]
        },
        "handler": assess_clause_risk
    },
    {
        "name": "get_contract_risk_summary",
        "description": "Get a risk summary for a contract including overall score, risk distribution across clauses, and key findings.",
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
        "handler": get_contract_risk_summary
    },
    {
        "name": "compare_contract_risks",
        "description": "Compare risks across multiple contracts. Useful for analyzing portfolio risk or choosing between options.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of contract IDs to compare"
                }
            },
            "required": ["contract_ids"]
        },
        "handler": compare_contract_risks
    }
]


def get_risk_tools() -> List[Dict[str, Any]]:
    """Get all risk tool definitions."""
    return RISK_TOOLS


# Export for tool registry
TOOL_DEFINITIONS = RISK_TOOLS
