from core.agent_router import AgentRouter
from core.types import WorkflowDefinition, WorkflowStep


def register_default_workflows(router: AgentRouter) -> None:
    """Register the default ISO 37301 compliance workflow."""
    router.register_workflow(
        WorkflowDefinition(
            name="iso37301_compliance",
            description="ISO 37301 compliance management system assessment and governance",
            capabilities=[
                "iso",
                "37301",
                "compliance",
                "governance",
                "obligations",
                "risk",
                "audit",
                "nonconformity",
                "corrective",
                "policy",
                "management",
            ],
            steps=[
                WorkflowStep(name="understand_context_and_scope"),
                WorkflowStep(name="identify_compliance_obligations"),
                WorkflowStep(name="assess_compliance_risk"),
                WorkflowStep(name="evaluate_evidence_and_gaps"),
                WorkflowStep(name="recommend_corrective_action", required_approval=True),
            ],
            allowed_tools=[],
            approval_tools=["recommend_corrective_action"],
            max_steps=15,
            system_prompt=(
                "You are an ISO 37301 compliance management system agent. "
                "Use the retrieved ISO governance knowledge as the governing reference. "
                "Separate requirements, evidence, findings, risks, nonconformities, "
                "and corrective actions. Do not invent compliance obligations. "
                "Cite the relevant ISO clause when making an assessment."
            ),
            workflow_documents=[
                "ISO 37301 assessment workflow: establish context and scope, identify compliance obligations, assess compliance risk, evaluate evidence and gaps, and recommend corrective action.",
            ],
        )
    )
