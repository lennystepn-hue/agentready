import os
import httpx
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Support multiple AI providers — configured via env vars
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

@dataclass
class DiscoveryResult:
    query: str
    provider: str  # "perplexity", "openai", "simulated"
    found: bool
    context: str  # snippet where domain was mentioned, or why not found
    confidence: float  # 0-1

async def run_discovery_test(domain: str, product_hints: list[str] = None, site_type: str = "generic") -> dict:
    """
    Run AI discovery test for a domain.
    Sends shopping-related queries to AI APIs and checks if the domain appears.
    Returns discovery score and individual query results.
    """
    # Generate test queries based on domain and product hints
    queries = generate_test_queries(domain, product_hints, site_type)

    results = []
    for query in queries:
        result = await test_single_query(domain, query)
        results.append(result)

    found_count = sum(1 for r in results if r.found)
    total = len(results)
    discovery_score = round((found_count / total) * 100) if total > 0 else 0

    return {
        "domain": domain,
        "discovery_score": discovery_score,
        "queries_tested": total,
        "queries_found": found_count,
        "results": [
            {
                "query": r.query,
                "provider": r.provider,
                "found": r.found,
                "context": r.context,
                "confidence": r.confidence,
            }
            for r in results
        ],
        "summary": generate_summary(domain, discovery_score, found_count, total),
    }

SITE_TYPE_QUERIES = {
    "ecommerce": [
        "What online shops sell products similar to {domain}?",
        "Can you recommend {domain} for shopping?",
        "Is {domain} a reliable online store?",
        "Best alternatives to {domain} for online shopping",
    ],
    "blog": [
        "What does {domain} write about?",
        "Is {domain} a good source for news and articles?",
        "Recommend blogs similar to {domain}",
        "What topics does {base} cover?",
    ],
    "saas": [
        "What does {domain} do? Is it a good tool?",
        "Tell me about the software at {domain}",
        "Best alternatives to {domain}",
        "Is {domain} worth using?",
    ],
    "restaurant": [
        "Tell me about the restaurant {domain}",
        "Is {domain} a good place to eat?",
        "What cuisine does {base} serve?",
        "Recommend restaurants similar to {domain}",
    ],
    "local_business": [
        "What services does {domain} offer?",
        "Is {domain} a reliable local business?",
        "Tell me about {base} and what they do",
        "Best alternatives to {domain} in the area",
    ],
    "professional_service": [
        "What services does {domain} provide?",
        "Is {domain} reputable in their field?",
        "Tell me about {base} professional services",
        "Recommend firms similar to {domain}",
    ],
    "portfolio": [
        "What does the agency {domain} do?",
        "Tell me about {base} and their work",
        "Is {domain} a good agency to work with?",
        "Recommend agencies similar to {domain}",
    ],
    "generic": [
        "What is {domain}?",
        "Tell me about {domain}",
        "Is {domain} a useful website?",
        "What can I find at {domain}?",
    ],
}


def generate_test_queries(domain: str, product_hints: list[str] = None, site_type: str = "generic") -> list[str]:
    """Generate relevant queries based on site type."""
    base = domain.replace("www.", "").split(".")[0]

    templates = SITE_TYPE_QUERIES.get(site_type, SITE_TYPE_QUERIES["generic"])
    queries = [q.format(domain=domain, base=base) for q in templates]

    # Always add a general query
    queries.append(f"What do you know about {domain}?")

    if product_hints:
        for hint in product_hints[:2]:
            queries.append(f"Where can I find {hint}?")

    return queries[:6]

async def test_single_query(domain: str, query: str) -> DiscoveryResult:
    """Test a single query against available AI providers."""

    # Try Perplexity first (best for web search)
    if PERPLEXITY_API_KEY:
        return await query_perplexity(domain, query)

    # Try OpenAI
    if OPENAI_API_KEY:
        return await query_openai(domain, query)

    # Fallback: simulated test based on web presence
    return await query_simulated(domain, query)

async def query_perplexity(domain: str, query: str) -> DiscoveryResult:
    """Query Perplexity API and check if domain is mentioned."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "sonar",
                    "messages": [
                        {"role": "user", "content": query}
                    ],
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                found = domain.lower().replace("www.", "") in content.lower()
                # Extract relevant snippet
                snippet = ""
                if found:
                    idx = content.lower().index(domain.lower().replace("www.", ""))
                    start = max(0, idx - 80)
                    end = min(len(content), idx + 80)
                    snippet = "..." + content[start:end] + "..."
                else:
                    snippet = content[:200] + "..." if len(content) > 200 else content

                return DiscoveryResult(
                    query=query,
                    provider="perplexity",
                    found=found,
                    context=snippet,
                    confidence=0.9 if found else 0.8,
                )
    except Exception as e:
        logger.warning(f"Perplexity query failed: {e}")

    return await query_simulated(domain, query)

async def query_openai(domain: str, query: str) -> DiscoveryResult:
    """Query OpenAI API and check if domain is mentioned."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a helpful shopping assistant. When recommending stores, include their website URLs."},
                        {"role": "user", "content": query}
                    ],
                    "max_tokens": 500,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                found = domain.lower().replace("www.", "") in content.lower()
                snippet = ""
                if found:
                    idx = content.lower().index(domain.lower().replace("www.", ""))
                    start = max(0, idx - 80)
                    end = min(len(content), idx + 80)
                    snippet = "..." + content[start:end] + "..."
                else:
                    snippet = content[:200] + "..." if len(content) > 200 else content

                return DiscoveryResult(
                    query=query,
                    provider="openai",
                    found=found,
                    context=snippet,
                    confidence=0.85 if found else 0.75,
                )
    except Exception as e:
        logger.warning(f"OpenAI query failed: {e}")

    return await query_simulated(domain, query)

async def query_simulated(domain: str, query: str) -> DiscoveryResult:
    """Simulated discovery test using web signals when no AI API is available."""
    # Check if the domain appears in search-like contexts
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            # Check if site is indexed and has good signals
            resp = await client.get(f"https://{domain}", headers={"User-Agent": "AgentCheck-Scanner/1.0"})
            has_structured_data = '"@type"' in resp.text and '"Product"' in resp.text
            has_llms_txt = False
            try:
                llms_resp = await client.get(f"https://{domain}/llms.txt")
                has_llms_txt = llms_resp.status_code == 200
            except:
                pass
            has_ai_txt = False
            try:
                ai_resp = await client.get(f"https://{domain}/ai.txt")
                has_ai_txt = ai_resp.status_code == 200
            except:
                pass

            # Score based on readiness signals
            signals = sum([has_structured_data, has_llms_txt, has_ai_txt, resp.status_code == 200])
            found = signals >= 3  # Likely discoverable if has most signals

            context = f"Simulated check: {'Found' if found else 'Not found'} key AI signals. "
            if has_structured_data: context += "Has structured data. "
            if has_llms_txt: context += "Has llms.txt. "
            if has_ai_txt: context += "Has ai.txt. "
            if not any([has_structured_data, has_llms_txt, has_ai_txt]):
                context += "No AI-readable files or structured data detected."

            return DiscoveryResult(
                query=query,
                provider="simulated",
                found=found,
                context=context.strip(),
                confidence=0.5,  # Lower confidence for simulated
            )
    except Exception as e:
        return DiscoveryResult(
            query=query,
            provider="simulated",
            found=False,
            context=f"Could not reach {domain}: {str(e)[:100]}",
            confidence=0.3,
        )

def generate_summary(domain: str, score: int, found: int, total: int) -> str:
    if score >= 80:
        return f"{domain} is well-represented across AI platforms. AI agents are likely to recommend your store for relevant queries."
    elif score >= 50:
        return f"{domain} appears in some AI responses but not consistently. Improving structured data and AI-readable files will increase visibility."
    elif score >= 20:
        return f"{domain} was found in {found} out of {total} AI queries. Significant improvements are needed for consistent AI agent discovery."
    else:
        return f"{domain} is largely invisible to AI agents. Implementing llms.txt, ai.txt, and structured data markup is critical for discovery."
