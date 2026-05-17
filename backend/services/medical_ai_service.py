import json
import re
import time
from typing import Dict, List, Optional

from google import genai
from google.genai import types

try:
    from config import config
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from config import config


class MedicalAIService:
    """Service for medical AI processing using Google Gemini"""

    def __init__(self):
        if not config.is_gemini_configured():
            raise ValueError("Gemini API key not configured")

        self.api_keys = config.get_gemini_api_keys()
        self.clients_by_key = {api_key: genai.Client(api_key=api_key) for api_key in self.api_keys}
        self.model_candidates = self._get_model_candidates()
        self._analysis_cache: Dict[str, Dict] = {}
        self._gemini_disabled_until_by_key: Dict[str, float] = {api_key: 0.0 for api_key in self.api_keys}
        self._gemini_disabled_until_global: float = 0.0

    def _get_model_candidates(self) -> List[str]:
        return ["gemini-2.5-flash-lite"]

    @staticmethod
    def _quota_retry_seconds(error: Exception) -> int:
        error_text = str(error)
        match = re.search(r"retryDelay['\"]?:\s*['\"]?(\d+)s", error_text)
        if match:
            try:
                return max(60, int(match.group(1)))
            except ValueError:
                pass
        return 60

    def _generate_content(self, prompt: str):
        last_error = None
        now = time.time()

        if now < self._gemini_disabled_until_global:
            raise RuntimeError("Gemini temporarily disabled after quota exhaustion")

        for api_key in self.api_keys:
            if now < self._gemini_disabled_until_by_key.get(api_key, 0.0):
                continue

            client = self.clients_by_key[api_key]

            for model_name in self.model_candidates:
                try:
                    return client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                            max_output_tokens=4096,
                            response_mime_type="application/json",
                        ),
                    )
                except Exception as e:
                    last_error = e
                    print(f"Gemini key ending in {api_key[-4:]} model {model_name} failed: {e}")
                    if self._is_quota_error(e):
                        retry_seconds = self._quota_retry_seconds(e)
                        disabled_until = time.time() + retry_seconds
                        self._gemini_disabled_until_by_key[api_key] = disabled_until
                        self._gemini_disabled_until_global = max(self._gemini_disabled_until_global, disabled_until)
                        break

        raise last_error

    @staticmethod
    def _is_quota_error(error: Exception) -> bool:
        error_text = str(error).lower()
        return (
            "resource_exhausted" in error_text
            or "quota exceeded" in error_text
            or "rate limit" in error_text
            or "429" in error_text
            or "limit: 0" in error_text
        )

    @staticmethod
    def _normalize_text(transcript: str) -> str:
        return re.sub(r"\s+", " ", transcript.lower()).strip()

    def _extract_symptoms(self, transcript: str) -> List[str]:
        text = self._normalize_text(transcript)
        symptom_map = {
            "fever": ["fever"],
            "cough": ["cough"],
            "sore throat": ["sore throat"],
            "headache": ["headache"],
            "pain": ["pain"],
            "nausea": ["nausea"],
            "vomiting": ["vomiting"],
            "diarrhea": ["diarrhea"],
            "fatigue": ["fatigue"],
            "dizziness": ["dizziness"],
            "shortness of breath": ["shortness of breath", "breathless"],
            "rash": ["rash"],
        }

        symptoms = []
        for label, variants in symptom_map.items():
            if any(variant in text for variant in variants):
                symptoms.append(label)
        return symptoms

    @staticmethod
    def _prepare_prescription_text(transcript: str) -> str:
        return (
            transcript.replace("’", "'")
            .replace("“", '"')
            .replace("”", '"')
            .replace("—", "-")
            .replace("–", "-")
        )

    def _extract_prescribed_medications(self, transcript: str) -> List[Dict]:
        medications = []

        normalized_transcript = self._prepare_prescription_text(transcript)
        lines = [line.strip() for line in normalized_transcript.splitlines() if line.strip()]

        prescription_lines: List[str] = []
        in_prescription_section = False
        for line in lines:
            clean_line = line.strip()
            lower_line = clean_line.lower()

            if re.search(r"\b(?:i['\"]?m|i am|im)\s+prescribing\b", lower_line):
                in_prescription_section = True
                continue

            if in_prescription_section:
                if re.match(r"^(doctor|patient)\s*:", clean_line, re.I):
                    break
                prescription_lines.append(clean_line)

        if not prescription_lines:
            prescription_lines = [
                line for line in lines
                if re.search(r"\b(tablet|tab|capsule|cap|syrup|injection|cream|ointment|lozenge|drops)\b", line, re.I)
                or re.match(r"^\d+\.\s*", line)
                or re.search(r"\b(take|use|apply|administer)\b", line, re.I)
            ]

        medication_pattern = re.compile(
            r"^(?:\d+\.\s*)?(?P<name>[A-Za-z][A-Za-z0-9\s\-]{1,80}?)(?:\s+(?P<dosage>\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu|units?)\b))?\s*(?:tablet|tab|capsule|cap|syrup|cream|ointment|lozenge|drops|injection)?\s*[-:]\s*(?P<instructions>.+)$",
            re.I,
        )
        frequency_pattern = re.compile(
            r"(?P<frequency>.+?)\s+for\s+(?P<duration>\d+\s+(?:day|days|week|weeks|month|months))",
            re.I,
        )
        simple_duration_pattern = re.compile(r"\bfor\s+(?P<duration>\d+\s+(?:day|days|week|weeks|month|months))", re.I)

        seen = set()
        for line in prescription_lines:
            match = medication_pattern.search(line)
            if not match:
                continue

            name = match.group("name").strip()
            dosage = (match.group("dosage") or "").strip()
            instructions = (match.group("instructions") or "").strip()
            frequency = ""
            duration = ""

            dur_match = frequency_pattern.search(instructions)
            if dur_match:
                frequency = dur_match.group("frequency").strip().rstrip(".")
                duration = dur_match.group("duration").strip()
            else:
                dur_match = simple_duration_pattern.search(instructions)
                if dur_match:
                    duration = dur_match.group("duration").strip()
                    frequency = instructions.replace(dur_match.group(0), "").strip().rstrip(".")
                else:
                    frequency = instructions

            if not name:
                continue

            key = (name.lower(), dosage.lower(), frequency.lower(), duration.lower())
            if key in seen:
                continue
            seen.add(key)

            medications.append(
                {
                    "name": name.title(),
                    "dosage": dosage,
                    "frequency": frequency,
                    "duration": duration,
                    "instructions": instructions or frequency,
                }
            )

        return medications

    def _infer_diagnoses(self, transcript: str, symptoms: List[str]) -> List[str]:
        text = self._normalize_text(transcript)
        diagnoses = []

        if any(item in symptoms for item in ["fever", "cough", "sore throat"]):
            diagnoses.append("Upper respiratory infection")
        if "headache" in symptoms and "fever" not in symptoms:
            diagnoses.append("Tension headache")
        if "pain" in symptoms:
            diagnoses.append("Pain complaint")
        if any(term in text for term in ["high blood pressure", "hypertension", "bp"]):
            diagnoses.append("Hypertension")
        if any(term in text for term in ["diabetes", "blood sugar", "glucose"]):
            diagnoses.append("Diabetes mellitus")

        return diagnoses

    def _infer_medications(self, transcript: str, symptoms: List[str]) -> List[Dict]:
        medications = self._extract_prescribed_medications(transcript)

        return medications

    def _build_local_soap_notes(self, transcript: str, entities: Dict) -> str:
        symptoms = entities.get("symptoms", [])
        diagnoses = entities.get("diagnoses", [])
        medications = entities.get("medications", [])

        subjective = "Chief complaint and symptoms reported: " + (", ".join(symptoms) if symptoms else "No clear chief complaint identified from the transcript.")
        objective = "Objective findings were not explicitly documented in the transcript." if not entities.get("vitals") else f"Objective findings: {json.dumps(entities.get('vitals', {}))}"
        assessment = "Assessment: " + (", ".join(diagnoses) if diagnoses else "No definitive diagnosis established from transcript alone.")
        plan_items = []
        if medications:
            plan_items.append("Medications: " + "; ".join([med.get("name", "") for med in medications]))
        if entities.get("tests_recommended"):
            plan_items.append("Tests: " + ", ".join(entities["tests_recommended"]))
        if entities.get("follow_up"):
            plan_items.append("Follow-up: " + entities["follow_up"])
        if not plan_items:
            plan_items.append("Supportive care and follow-up as needed.")

        return "\n".join(
            [
                "SUBJECTIVE:",
                f"- {subjective}",
                "",
                "OBJECTIVE:",
                f"- {objective}",
                "",
                "ASSESSMENT:",
                f"- {assessment}",
                "",
                "PLAN:",
                *[f"- {item}" for item in plan_items],
            ]
        )

    def _build_local_quality(self, transcript: str) -> Dict:
        text = self._normalize_text(transcript)
        has_symptom = any(keyword in text for keyword in ["pain", "fever", "cough", "headache", "nausea", "rash"])
        has_plan = any(keyword in text for keyword in ["follow up", "follow-up", "take", "prescribe", "rest", "return"])
        has_diagnosis = any(keyword in text for keyword in ["diagnosis", "likely", "possible", "suspect"])

        completeness = 20
        completeness += 20 if has_symptom else 0
        completeness += 20 if has_diagnosis else 0
        completeness += 20 if has_plan else 0
        completeness += 20 if any(keyword in text for keyword in ["exam", "blood pressure", "temperature", "heart rate"]) else 0

        missing_information = []
        if not has_symptom:
            missing_information.append("clear chief complaint")
        if not has_diagnosis:
            missing_information.append("diagnosis or working assessment")
        if not has_plan:
            missing_information.append("treatment plan or follow-up")

        return {
            "completeness_score": completeness,
            "missing_information": missing_information,
            "clarity_score": 60 if len(text) > 40 else 30,
            "suggestions": ["Capture a clearer chief complaint.", "Add objective findings if available."] if missing_information else ["Transcript is reasonably complete."],
            "has_chief_complaint": has_symptom,
            "has_history": len(text) > 80,
            "has_examination": any(keyword in text for keyword in ["exam", "blood pressure", "temperature", "heart rate"]),
            "has_diagnosis": has_diagnosis,
            "has_plan": has_plan,
        }

    def _build_local_analysis(self, transcript: str, patient_info: Optional[Dict] = None) -> Dict:
        symptoms = self._extract_symptoms(transcript)
        diagnoses = self._infer_diagnoses(transcript, symptoms)
        medications = self._infer_medications(transcript, symptoms)
        entities = {
            "symptoms": symptoms,
            "diagnoses": diagnoses,
            "medications": medications,
            "tests_recommended": [],
            "allergies": [],
            "vitals": {},
            "duration_of_illness": "",
            "follow_up": "",
        }

        return {
            "entities": entities,
            "soap_notes": self._build_local_soap_notes(transcript, entities),
            "prescription": {
                "patient_info": patient_info or {},
                "medications": medications,
                "diagnoses": diagnoses,
                "tests_recommended": [],
                "follow_up": "",
                "allergies": [],
            },
            "quality_analysis": self._build_local_quality(transcript),
        }

    def _build_local_fallback_analysis(self, transcript: str, patient_info: Optional[Dict] = None, reason: Optional[str] = None) -> Dict:
        analysis = self._build_local_analysis(transcript, patient_info)
        analysis["analysis_source"] = "local_fallback"
        if reason:
            analysis["fallback_reason"] = reason
        return analysis

    @staticmethod
    def _extract_text(response) -> str:
        text = getattr(response, "text", None)
        if text:
            return text.strip()

        parts = []
        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                part_text = getattr(part, "text", None)
                if part_text:
                    parts.append(part_text)
        return "".join(parts).strip()

    @staticmethod
    def _clean_json_text(result_text: str) -> str:
        cleaned_text = result_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        return cleaned_text.strip()

    @staticmethod
    def _extract_json_object(result_text: str) -> str:
        """Try to isolate the outer JSON object if Gemini wrapped it in extra text."""
        start_index = result_text.find("{")
        end_index = result_text.rfind("}")
        if start_index != -1 and end_index != -1 and end_index > start_index:
            return result_text[start_index:end_index + 1].strip()
        return result_text.strip()

    def _default_entities(self) -> Dict:
        return {
            "symptoms": [],
            "diagnoses": [],
            "medications": [],
            "tests_recommended": [],
            "allergies": [],
            "vitals": {},
            "duration_of_illness": "",
            "follow_up": "",
        }

    def _default_quality(self) -> Dict:
        return {
            "completeness_score": 0,
            "missing_information": [],
            "clarity_score": 0,
            "suggestions": [],
            "has_chief_complaint": False,
            "has_history": False,
            "has_examination": False,
            "has_diagnosis": False,
            "has_plan": False,
        }

    def _default_prescription(self, patient_info: Optional[Dict] = None) -> Dict:
        return {
            "patient_info": patient_info or {},
            "medications": [],
            "diagnoses": [],
            "tests_recommended": [],
            "follow_up": "",
            "allergies": [],
        }

    def _get_cached_consultation_analysis(self, transcript: str, patient_info: Optional[Dict] = None) -> Dict:
        cache_key = transcript.strip()
        if cache_key in self._analysis_cache:
            cached = self._analysis_cache[cache_key]
            if patient_info and not cached.get("prescription", {}).get("patient_info"):
                cached["prescription"]["patient_info"] = patient_info
            return cached

        prompt = f"""
You are a medical AI assistant. Analyze the following doctor-patient consultation transcript and return a single JSON object.

Transcript:
{transcript}

Return ONLY valid JSON in this exact shape:
{{
  "entities": {{
    "symptoms": ["list of symptoms mentioned"],
    "diagnoses": ["list of diagnoses or suspected conditions"],
        "medications": [
      {{
                "name": "exact medicine name prescribed in the transcript",
                "dosage": "dosage information from the transcript if present",
                "frequency": "how often to take",
                "duration": "how long to take",
                "instructions": "special instructions from the transcript"
      }}
    ],
    "tests_recommended": ["list of tests or investigations recommended"],
    "allergies": ["list of allergies mentioned"],
    "vitals": {{
      "temperature": "value if mentioned",
      "blood_pressure": "value if mentioned",
      "heart_rate": "value if mentioned",
      "weight": "value if mentioned"
    }},
    "duration_of_illness": "how long patient has been experiencing symptoms",
    "follow_up": "follow-up instructions if any"
  }},
  "soap_notes": "full SOAP note string using SUBJECTIVE, OBJECTIVE, ASSESSMENT, PLAN sections",
  "prescription": {{
    "patient_info": {json.dumps(patient_info or {})},
    "medications": [
      {{
        "name": "medication name",
        "dosage": "dosage",
        "frequency": "frequency",
        "duration": "duration",
        "instructions": "special instructions"
      }}
    ],
    "diagnoses": ["diagnoses array"],
    "tests_recommended": ["tests array"],
    "follow_up": "follow-up text",
    "allergies": ["allergies array"]
  }},
  "quality_analysis": {{
    "completeness_score": 0,
    "missing_information": ["list of important missing information"],
    "clarity_score": 0,
    "suggestions": ["suggestions for improvement"],
    "has_chief_complaint": true,
    "has_history": true,
    "has_examination": true,
    "has_diagnosis": true,
    "has_plan": true
  }}
}}

Use concise, medically accurate language. Prioritize extracting the actual medicines prescribed from the transcript. If information is missing, return empty arrays, empty strings, or false values rather than inventing details.
"""

        try:
            response = self._generate_content(prompt)
            result_text = self._clean_json_text(self._extract_text(response))
            try:
                analysis = json.loads(result_text)
            except json.JSONDecodeError:
                analysis = json.loads(self._extract_json_object(result_text))
        except json.JSONDecodeError:
            print("Gemini returned invalid JSON for consolidated medical analysis; using local fallback.")
            analysis = self._build_local_fallback_analysis(transcript, patient_info, "invalid_json")
        except Exception as e:
            print(f"Gemini analysis failed; using local fallback: {e}")
            analysis = self._build_local_fallback_analysis(transcript, patient_info, str(e))

        analysis.setdefault("entities", self._default_entities())
        analysis.setdefault("soap_notes", "")
        analysis.setdefault("prescription", self._default_prescription(patient_info))
        analysis.setdefault("quality_analysis", self._default_quality())

        extracted_medications = self._extract_prescribed_medications(transcript)
        if extracted_medications:
            analysis.setdefault("prescription", self._default_prescription(patient_info))
            analysis["prescription"]["medications"] = extracted_medications
            analysis.setdefault("entities", self._default_entities())
            analysis["entities"]["medications"] = extracted_medications

        self._analysis_cache[cache_key] = analysis
        return analysis

    def get_consultation_analysis(self, transcript: str, patient_info: Optional[Dict] = None) -> Dict:
        """Return the full consultation analysis payload, including fallback metadata."""
        return self._get_cached_consultation_analysis(transcript, patient_info)

    def extract_medical_entities(self, transcript: str) -> Dict:
        analysis = self._get_cached_consultation_analysis(transcript)
        return analysis.get("entities", self._default_entities())

    def generate_soap_notes(self, transcript: str, entities: Dict) -> str:
        analysis = self._get_cached_consultation_analysis(transcript)
        return analysis.get("soap_notes") or self._build_local_soap_notes(transcript, entities)

    def generate_prescription(self, transcript: str, entities: Dict, patient_info: Optional[Dict] = None) -> Dict:
        analysis = self._get_cached_consultation_analysis(transcript, patient_info)
        prescription = analysis.get("prescription", self._default_prescription(patient_info))

        if not prescription.get("medications"):
            prescription["medications"] = self._infer_medications(transcript, entities.get("symptoms", [])) or entities.get("medications", [])
        if not prescription.get("diagnoses"):
            prescription["diagnoses"] = entities.get("diagnoses", [])
        if not prescription.get("tests_recommended"):
            prescription["tests_recommended"] = entities.get("tests_recommended", [])
        if not prescription.get("follow_up"):
            prescription["follow_up"] = entities.get("follow_up", "")
        if not prescription.get("allergies"):
            prescription["allergies"] = entities.get("allergies", [])
        if patient_info and not prescription.get("patient_info"):
            prescription["patient_info"] = patient_info

        return prescription

    def analyze_transcript_quality(self, transcript: str) -> Dict:
        analysis = self._get_cached_consultation_analysis(transcript)
        return analysis.get("quality_analysis", self._build_local_quality(transcript))


# Singleton instance
_medical_ai_service = None


def get_medical_ai_service() -> MedicalAIService:
    """Get or create singleton instance of MedicalAIService"""
    global _medical_ai_service
    if _medical_ai_service is None:
        _medical_ai_service = MedicalAIService()
    return _medical_ai_service


# Made with Bob