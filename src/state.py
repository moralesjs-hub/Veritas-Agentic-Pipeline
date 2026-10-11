import operator
from typing import Annotated, List, Literal, TypedDict
from pydantic import BaseModel, Field

class FactCheckResult(BaseModel):
    claim: str = Field(description="The factual claim extracted from the synthesized text")
    supported: bool = Field(description="True if the retrieved evidence explicitly confirms the claim, False otherwise")
    critique: str = Field(description="Specific feedback on discrepancies or missing citations")

class AgentState(TypedDict):
    query: str
    search_queries: List[str]
    retrieved_docs: Annotated[List[str], operator.add]
    draft: str
    fact_check_results: List[FactCheckResult]
    verification_status: Literal["PENDING", "APPROVED", "REVISE"]
    iteration_count: int