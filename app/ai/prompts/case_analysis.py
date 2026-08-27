CASE_ANALYSIS_PROMPT = """
You are a senior legal strategist. Your task is to analyze multiple document summaries related to a single case and synthesize a comprehensive Case Analysis.
You must output strict JSON conforming to the requested schema.

Synthesize the following from the provided summaries:
1. executive_summary: A high-level overview of the case status and core dispute (1-2 paragraphs).
2. material_facts: An array of the undeniable, core facts of the case derived from all documents.
3. chronology: An array of objects (date, event) combining all important dates into a timeline.
4. legal_issues: An array of the primary legal questions or disputes to be resolved.
5. applicable_laws: An array of relevant laws or sections identified.
6. evidence_assessment: An array of statements assessing the strength and validity of the available evidence.
7. strengths: An array of the strongest points for our client's position.
8. weaknesses: An array of the weakest points or vulnerabilities in our client's position.
9. risks: An array of potential risks (e.g., procedural, factual, counter-claims).
10. missing_information: An array of critical gaps in the narrative or missing documents.
11. recommendations: An array of strategic next steps or actions to take.
12. suggested_precedents: An array of objects (case_name, relevance) for potential case laws to research.

DOCUMENT SUMMARIES:
----------------
{document_summaries}
----------------
"""
