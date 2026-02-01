"""Agent module initialization."""

try:
    from .agent_definitions_new import (
        CONTRACT_PARSER_AGENT,
        LEGAL_RESEARCH_AGENT,
        COMPLIANCE_CHECKER_AGENT,
        RISK_ASSESSMENT_AGENT,
        LEGAL_MEMO_AGENT,
        ASSISTANT_AGENT,
        get_agent_config,
        get_agent_instructions,
        list_agents,
    )
except ImportError:
    try:
        from .agent_definitions import (
            SCHEDULER_AGENT as CONTRACT_PARSER_AGENT,
            ASSISTANT_AGENT,
        )
    except ImportError:
        CONTRACT_PARSER_AGENT = None

try:
    from .agent_strategies_new import (
        select_agent,
        get_agent_sequence,
        AgentOrchestrator,
    )
except ImportError:
    try:
        from .agent_strategies import (
            ChatbotSelectionStrategy,
            ChatbotTerminationStrategy,
        )
    except ImportError:
        ChatbotSelectionStrategy = None

__all__ = [
    'CONTRACT_PARSER_AGENT',
    'LEGAL_RESEARCH_AGENT',
    'COMPLIANCE_CHECKER_AGENT',
    'RISK_ASSESSMENT_AGENT',
    'LEGAL_MEMO_AGENT',
    'ASSISTANT_AGENT',
    'get_agent_config',
    'list_agents',
]
