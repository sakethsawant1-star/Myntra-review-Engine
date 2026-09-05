"""
AI Provider — Configurable Gemini adapter with evidence-span validation.

Reads model name from GEMINI_MODEL env var. Validates that support spans
actually appear in the source text after extraction.
"""

import json
import os
import re
from typing import Dict, Any, Optional, List

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
except ImportError:
    genai = None

from backend.app.ai.schema import AIAnnotation, AIBatchResponse
from backend.app.ai.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


def _normalize_for_comparison(text: str) -> str:
    """Normalize text for fuzzy span matching: lowercase, collapse whitespace, strip punctuation."""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def validate_support_spans(annotation: AIAnnotation, masked_text: str) -> Dict[str, Any]:
    """
    Verify that each claimed support span actually exists in the source text.
    Returns a validation report and adjusts confidence if spans are invalid.
    """
    normalized_source = _normalize_for_comparison(masked_text)
    validation = {"checked": 0, "valid": 0, "invalid": 0, "details": []}

    # Check friction support_spans
    for friction in annotation.frictions:
        validation["checked"] += 1
        norm_span = _normalize_for_comparison(friction.support_span)
        found = norm_span in normalized_source
        validation["details"].append({
            "field": "friction",
            "type": friction.type,
            "span": friction.support_span,
            "valid": found
        })
        if found:
            validation["valid"] += 1
        else:
            validation["invalid"] += 1

    # Check supporting_spans
    for span in annotation.supporting_spans:
        validation["checked"] += 1
        norm_span = _normalize_for_comparison(span.exact_quote)
        found = norm_span in normalized_source
        validation["details"].append({
            "field": "supporting_span",
            "claim": span.claim,
            "span": span.exact_quote,
            "valid": found
        })
        if found:
            validation["valid"] += 1
        else:
            validation["invalid"] += 1

    validation["validation_rate"] = (
        round(validation["valid"] / validation["checked"], 2)
        if validation["checked"] > 0 else 1.0
    )

    return validation


class AIProvider:
    """
    Adapter for AI inference using Google Gemini.
    Model is configurable via GEMINI_MODEL environment variable.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")

        if not genai:
            raise ImportError("google-generativeai is not installed.")

        genai.configure(api_key=self.api_key)

        self.model_name = model_name or os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=SYSTEM_PROMPT
        )

    def analyze_batch(
        self, batch_texts: List[str], source_type: str = "unknown"
    ) -> List[AIAnnotation]:
        """
        Sends a batch of texts to Gemini and enforces the AIBatchResponse Pydantic schema.
        """
        # Convert batch to JSON array string for the prompt
        raw_texts_json = json.dumps([{"id": i, "text": text} for i, text in enumerate(batch_texts)])
        
        prompt = USER_PROMPT_TEMPLATE.format(source_type=source_type, raw_texts=raw_texts_json)

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=AIBatchResponse,
                    temperature=0.0
                )
            )

            json_data = json.loads(response.text)
            batch_response = AIBatchResponse(**json_data)
            
            # Ensure the returned annotations match the input length
            if len(batch_response.annotations) != len(batch_texts):
                print(f"[AIProvider] Warning: Batch size mismatch. Expected {len(batch_texts)}, got {len(batch_response.annotations)}")
                
            return batch_response.annotations

        except Exception as e:
            print(f"[AIProvider] Failed to analyze batch: {e}")
            raise

    def analyze_and_validate_batch(
        self, batch_raw_texts: List[str], batch_masked_texts: List[str], source_type: str = "unknown"
    ) -> List[tuple[AIAnnotation, Dict[str, Any]]]:
        """
        Analyze a batch of evidence AND validate that support spans exist in the source text.
        Returns a list of (annotation, span_validation_report) tuples.
        """
        annotations = self.analyze_batch(batch_texts=batch_raw_texts, source_type=source_type)
        
        results = []
        for i, annotation in enumerate(annotations):
            if i >= len(batch_masked_texts):
                break
                
            masked_text = batch_masked_texts[i]
            validation = validate_support_spans(annotation, masked_text)

            # Downgrade confidence if many spans are invalid
            if validation["checked"] > 0 and validation["validation_rate"] < 0.5:
                annotation.evidence_confidence = max(1, annotation.evidence_confidence - 1)
                
            results.append((annotation, validation))

        return results

    # Backwards-compatible single-item methods for local callers and older tests.
    def analyze_evidence(self, text: str, source_type: str = "unknown") -> AIAnnotation:
        return self.analyze_batch([text], source_type=source_type)[0]

    def analyze_and_validate(
        self, raw_text: str, masked_text: str, source_type: str = "unknown"
    ) -> tuple[AIAnnotation, Dict[str, Any]]:
        return self.analyze_and_validate_batch(
            batch_raw_texts=[raw_text],
            batch_masked_texts=[masked_text],
            source_type=source_type,
        )[0]
