from fastapi import APIRouter, HTTPException

from app.services.llm import LLMService


router = APIRouter(
    prefix="/api/ai",
    tags=["AI"]
)

llm = LLMService()


@router.get("/test")
def test_ai():

    system_prompt = """
    You are an AI Site Reliability Engineering assistant.

    Analyze software incidents using current telemetry.
    Identify likely causes based on evidence.
    Do not assume that historical information is always correct.
    """

    user_prompt = """
    Analyze this production incident:

    Service: payment-service
    Latency: 9400 ms
    Error rate: 18.2%
    Database connection utilization: 97%
    CPU utilization: 48%
    Memory utilization: 61%

    Explain:
    1. What is the most likely problem?
    2. What evidence supports your conclusion?
    3. What should an engineer investigate or do next?
    """

    try:

        result = llm.analyze(
            system_prompt,
            user_prompt
        )

        return {
            "model": llm.model,
            "analysis": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )