import re
import datetime
import json
import logging
from typing import Tuple, List, Dict, Any, Optional

# NLP imports with graceful fallback
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from detoxify import Detoxify
    DETOXIFY_AVAILABLE = True
except ImportError:
    DETOXIFY_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False


class BiasDetector:
    """NLP-powered bias and non-inclusive language detector."""
    
    def __init__(self):
        self.logger = logging.getLogger("Watchtower_BiasDetector")
        
        # Initialize NLP models
        self._nlp = None
        self._toxicity_model = None
        
        # Semantic categories for bias detection (used with spaCy similarity)
        self.gendered_anchors = [
            "man", "woman", "male", "female", "masculine", "feminine",
            "he", "she", "him", "her", "businessman", "businesswoman"
        ]
        
        self.exclusionary_anchors = [
            "elite", "genius", "superstar", "hero", "warrior", "dominate",
            "aggressive", "cutthroat", "killer"
        ]
        
        # Regex patterns for common bias indicators
        self.bias_patterns = {
            "gendered_suffix": re.compile(r"\b\w+(man|men|woman|women)\b", re.IGNORECASE),
            "ableist": re.compile(r"\b(crazy|insane|lame|blind|deaf|dumb|crippled)\b", re.IGNORECASE),
            "age_bias": re.compile(r"\b(young|youthful|energetic|digital native|old school)\b", re.IGNORECASE),
            "culture_fit": re.compile(r"\b(culture fit|beer|ping pong|frat|bro)\b", re.IGNORECASE),
            "aggressive_language": re.compile(r"\b(crush|kill|destroy|dominate|attack|war room)\b", re.IGNORECASE),
        }
        
        # Fallback static terms (used when NLP isn't available)
        self.fallback_terms = [
            "rockstar", "ninja", "guru", "crush code", "guys", "salesman", 
            "manpower", "chairman", "mankind", "fireman", "policeman",
            "stewardess", "waitress", "cleaning lady", "manmade"
        ]
        
        # Inclusive alternatives mapping
        self.inclusive_alternatives = {
            "guys": "team, folks, everyone",
            "manpower": "workforce, staffing, personnel",
            "chairman": "chairperson, chair",
            "salesman": "salesperson, sales representative",
            "fireman": "firefighter",
            "policeman": "police officer",
            "stewardess": "flight attendant",
            "mankind": "humanity, humankind",
            "ninja": "expert, specialist",
            "rockstar": "high performer, top talent",
            "guru": "expert, specialist, leader",
            "crush it": "excel, succeed, perform well",
        }
    
    @property
    def nlp(self):
        """Lazy-load spaCy model."""
        if self._nlp is None and SPACY_AVAILABLE:
            try:
                self._nlp = spacy.load("en_core_web_md")
                self.logger.info("Loaded spaCy model for semantic analysis")
            except OSError:
                self.logger.warning("spaCy model 'en_core_web_md' not found. Run: python -m spacy download en_core_web_md")
                self._nlp = False
        return self._nlp if self._nlp else None
    
    @property
    def toxicity_model(self):
        """Lazy-load Detoxify model."""
        if self._toxicity_model is None and DETOXIFY_AVAILABLE:
            try:
                self._toxicity_model = Detoxify('original')
                self.logger.info("Loaded Detoxify model for toxicity analysis")
            except Exception as e:
                self.logger.warning(f"Failed to load Detoxify: {e}")
                self._toxicity_model = False
        return self._toxicity_model if self._toxicity_model else None
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive NLP analysis of text for bias and non-inclusive language.
        
        Returns:
            Dict with keys: is_biased, confidence, issues, suggestions
        """
        issues = []
        suggestions = []
        confidence_scores = []
        
        text_lower = text.lower()
        
        # 1. Pattern-based detection (always available)
        pattern_issues = self._check_patterns(text)
        issues.extend(pattern_issues)
        if pattern_issues:
            confidence_scores.append(0.8)
        
        # 2. Toxicity analysis (if Detoxify available)
        if self.toxicity_model:
            toxicity_result = self._check_toxicity(text)
            if toxicity_result:
                issues.append(toxicity_result)
                confidence_scores.append(0.9)
        
        # 3. Semantic similarity analysis (if spaCy available)
        if self.nlp:
            semantic_issues = self._check_semantic_bias(text)
            issues.extend(semantic_issues)
            if semantic_issues:
                confidence_scores.append(0.7)
        
        # 4. Sentiment & subjectivity analysis (if TextBlob available)
        if TEXTBLOB_AVAILABLE:
            sentiment_issues = self._check_sentiment(text)
            issues.extend(sentiment_issues)
            if sentiment_issues:
                confidence_scores.append(0.6)
        
        # 5. Fallback static check (always runs as backup)
        fallback_issues = self._check_fallback_terms(text_lower)
        for term in fallback_issues:
            if term not in [i.get('term') for i in issues]:
                issues.append({'type': 'static_match', 'term': term})
                if term in self.inclusive_alternatives:
                    suggestions.append(f"Replace '{term}' with: {self.inclusive_alternatives[term]}")
        
        # Generate suggestions for detected issues
        for issue in issues:
            term = issue.get('term', '').lower()
            if term in self.inclusive_alternatives and term not in str(suggestions):
                suggestions.append(f"Replace '{term}' with: {self.inclusive_alternatives[term]}")
        
        is_biased = len(issues) > 0
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            'is_biased': is_biased,
            'confidence': avg_confidence,
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _check_patterns(self, text: str) -> List[Dict]:
        """Check regex patterns for common bias indicators."""
        issues = []
        for pattern_name, pattern in self.bias_patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                issues.append({
                    'type': 'pattern',
                    'category': pattern_name,
                    'term': match if isinstance(match, str) else match[0]
                })
        return issues
    
    def _check_toxicity(self, text: str) -> Optional[Dict]:
        """Use Detoxify to check for toxic/offensive language."""
        try:
            results = self.toxicity_model.predict(text)
            # Check various toxicity dimensions
            for key in ['toxicity', 'severe_toxicity', 'identity_attack', 'insult']:
                if results.get(key, 0) > 0.5:
                    return {
                        'type': 'toxicity',
                        'category': key,
                        'score': results[key],
                        'term': f"Text flagged for {key.replace('_', ' ')}"
                    }
        except Exception as e:
            self.logger.debug(f"Toxicity check failed: {e}")
        return None
    
    def _check_semantic_bias(self, text: str) -> List[Dict]:
        """Use spaCy word vectors to find semantically similar biased terms."""
        issues = []
        try:
            doc = self.nlp(text)
            
            # Check each token against bias anchors
            for token in doc:
                if token.has_vector and token.is_alpha and len(token.text) > 2:
                    # Check similarity to exclusionary terms
                    for anchor in self.exclusionary_anchors:
                        anchor_doc = self.nlp(anchor)
                        if anchor_doc.has_vector:
                            similarity = token.similarity(anchor_doc)
                            if similarity > 0.65 and token.text.lower() != anchor:
                                issues.append({
                                    'type': 'semantic',
                                    'category': 'exclusionary',
                                    'term': token.text,
                                    'similar_to': anchor,
                                    'similarity': round(similarity, 2)
                                })
                                break
        except Exception as e:
            self.logger.debug(f"Semantic analysis failed: {e}")
        return issues
    
    def _check_sentiment(self, text: str) -> List[Dict]:
        """Use TextBlob to check for overly aggressive/negative sentiment."""
        issues = []
        try:
            blob = TextBlob(text)
            # Flag very negative or very polarizing content
            if blob.sentiment.polarity < -0.5:
                issues.append({
                    'type': 'sentiment',
                    'category': 'negative_tone',
                    'term': 'Overall negative sentiment detected',
                    'score': blob.sentiment.polarity
                })
            # High subjectivity in professional context can indicate bias
            if blob.sentiment.subjectivity > 0.8:
                issues.append({
                    'type': 'sentiment',
                    'category': 'high_subjectivity',
                    'term': 'Highly subjective language detected',
                    'score': blob.sentiment.subjectivity
                })
        except Exception as e:
            self.logger.debug(f"Sentiment analysis failed: {e}")
        return issues
    
    def _check_fallback_terms(self, text_lower: str) -> List[str]:
        """Fallback to static term matching when NLP unavailable."""
        found = []
        for term in self.fallback_terms:
            if term in text_lower:
                found.append(term)
        return found


class PIIDetector:
    """
    NLP-powered PII (Personally Identifiable Information) detector.
    
    Uses spaCy Named Entity Recognition to detect:
    - Names (PERSON)
    - Organizations (ORG)
    - Locations/Addresses (GPE, LOC, FAC)
    - Dates (DATE)
    - Financial info (MONEY, CARDINAL)
    
    Plus regex patterns for structured data like SSN, phone, email, credit cards.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("Watchtower_PIIDetector")
        self._nlp = None
        
        # NER entity types that are PII
        self.pii_entity_types = {
            "PERSON": "name",
            "GPE": "location",           # Countries, cities, states
            "LOC": "location",           # Non-GPE locations
            "FAC": "facility",           # Buildings, airports, highways
            "ORG": "organization",
            "DATE": "date",
            "MONEY": "financial",
            "CARDINAL": "number",
            "NORP": "demographic",       # Nationalities, religious/political groups
        }
        
        # Regex patterns for structured PII (always run as backup)
        self.structured_patterns = {
            "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "ssn_nodash": re.compile(r"\b\d{9}\b"),
            "phone_us": re.compile(r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
            "phone_intl": re.compile(r"\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b"),
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "credit_card": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
            "passport": re.compile(r"\b[A-Z]{1,2}\d{6,9}\b"),
            "drivers_license": re.compile(r"\b[A-Z]{1,2}\d{5,8}\b"),
            "ip_address": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
            "dob": re.compile(r"\b(0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])[-/](\d{2}|\d{4})\b"),
            "bank_account": re.compile(r"\b\d{8,17}\b"),
            "zip_code": re.compile(r"\b\d{5}(-\d{4})?\b"),
        }
        
        # High-sensitivity patterns (always block/redact in external comms)
        self.high_sensitivity = {"ssn", "ssn_nodash", "credit_card", "bank_account", "passport"}
        
    @property
    def nlp(self):
        """Lazy-load spaCy model for NER."""
        if self._nlp is None and SPACY_AVAILABLE:
            try:
                self._nlp = spacy.load("en_core_web_md")
                self.logger.info("Loaded spaCy model for NER-based PII detection")
            except OSError:
                self.logger.warning("spaCy model not found for PII detection")
                self._nlp = False
        return self._nlp if self._nlp else None
    
    def detect_pii(self, text: str, context: str = "general") -> Dict[str, Any]:
        """
        Detect PII in text using NLP + regex patterns.
        
        Args:
            text: The text to analyze
            context: 'internal', 'external', 'blind_screening' - affects sensitivity
            
        Returns:
            Dict with: has_pii, entities, patterns, redacted_text, risk_level
        """
        entities_found = []
        patterns_found = []
        redacted_text = text
        
        # 1. NER-based detection (if spaCy available)
        if self.nlp:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ in self.pii_entity_types:
                        pii_type = self.pii_entity_types[ent.label_]
                        entities_found.append({
                            "type": pii_type,
                            "ner_label": ent.label_,
                            "text": ent.text,
                            "start": ent.start_char,
                            "end": ent.end_char
                        })
                        # Redact in output
                        redacted_text = redacted_text.replace(
                            ent.text, f"[{pii_type.upper()}_REDACTED]"
                        )
            except Exception as e:
                self.logger.debug(f"NER detection failed: {e}")
        
        # 2. Regex pattern detection (always runs)
        for pattern_name, pattern in self.structured_patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                match_text = match if isinstance(match, str) else match[0] if match else ""
                if match_text and match_text not in [p.get('text') for p in patterns_found]:
                    patterns_found.append({
                        "type": pattern_name,
                        "text": match_text,
                        "high_sensitivity": pattern_name in self.high_sensitivity
                    })
                    # Redact in output
                    redacted_text = redacted_text.replace(
                        match_text, f"[{pattern_name.upper()}_REDACTED]"
                    )
        
        # Calculate risk level
        has_high_sensitivity = any(p.get("high_sensitivity") for p in patterns_found)
        total_pii = len(entities_found) + len(patterns_found)
        
        if has_high_sensitivity:
            risk_level = "critical"
        elif total_pii > 5:
            risk_level = "high"
        elif total_pii > 2:
            risk_level = "medium"
        elif total_pii > 0:
            risk_level = "low"
        else:
            risk_level = "none"
        
        return {
            "has_pii": total_pii > 0,
            "entity_count": len(entities_found),
            "pattern_count": len(patterns_found),
            "entities": entities_found,
            "patterns": patterns_found,
            "redacted_text": redacted_text,
            "risk_level": risk_level,
            "high_sensitivity_detected": has_high_sensitivity
        }
    
    def redact_text(self, text: str, preserve_types: List[str] = None) -> str:
        """
        Redact all PII from text.
        
        Args:
            text: Text to redact
            preserve_types: Optional list of PII types to NOT redact (e.g., ['email'])
        """
        preserve_types = preserve_types or []
        result = self.detect_pii(text)
        
        redacted = text
        
        # Redact NER entities
        for ent in sorted(result["entities"], key=lambda x: x["start"], reverse=True):
            if ent["type"] not in preserve_types:
                redacted = redacted[:ent["start"]] + f"[{ent['type'].upper()}_REDACTED]" + redacted[ent["end"]:]
        
        # Redact pattern matches
        for pat in result["patterns"]:
            if pat["type"] not in preserve_types:
                redacted = redacted.replace(pat["text"], f"[{pat['type'].upper()}_REDACTED]")
        
        return redacted


class BlindScreener:
    """
    NLP-powered blind screening for candidate data.
    
    Uses NER to automatically detect and redact identifying information,
    going beyond static field lists to catch PII in any text field.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("Watchtower_BlindScreener")
        self.pii_detector = PIIDetector()
        
        # Fields that should ALWAYS be redacted (even without NER)
        self.always_redact_fields = {
            "name", "full_name", "first_name", "last_name",
            "email", "phone", "address", "street", "city", "state", "zip",
            "ssn", "social_security", "date_of_birth", "dob", "birthday",
            "gender", "sex", "race", "ethnicity", "nationality",
            "photo", "picture", "image", "headshot",
            "linkedin", "github", "twitter", "social_media",
            "university", "college", "school", "education_institution",
            "graduation_year", "age"
        }
        
        # Fields to PRESERVE (job-relevant, non-identifying)
        self.preserve_fields = {
            "skills", "experience_years", "certifications", "projects",
            "job_title", "role", "level", "department", "id", "candidate_id",
            "status", "score", "recommendation", "notes_redacted"
        }
    
    def blind_screen(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply blind screening to candidate data.
        
        Redacts identifying information while preserving job-relevant details.
        Uses NLP to detect PII in text fields, not just field names.
        
        Args:
            candidate_data: Raw candidate dictionary
            
        Returns:
            Blinded candidate data with PII redacted
        """
        blinded = {}
        redaction_log = []
        
        for key, value in candidate_data.items():
            key_lower = key.lower()
            
            # Always redact certain fields entirely
            if key_lower in self.always_redact_fields:
                blinded[key] = "[REDACTED]"
                redaction_log.append({"field": key, "reason": "always_redact"})
                continue
            
            # Preserve known safe fields
            if key_lower in self.preserve_fields:
                blinded[key] = value
                continue
            
            # For text fields, use NLP to detect and redact embedded PII
            if isinstance(value, str) and len(value) > 10:
                pii_result = self.pii_detector.detect_pii(value, context="blind_screening")
                if pii_result["has_pii"]:
                    blinded[key] = pii_result["redacted_text"]
                    redaction_log.append({
                        "field": key,
                        "reason": "pii_detected",
                        "pii_count": pii_result["entity_count"] + pii_result["pattern_count"]
                    })
                else:
                    blinded[key] = value
            elif isinstance(value, list):
                # For lists, check each item
                blinded[key] = [
                    self._redact_if_pii(item) if isinstance(item, str) else item
                    for item in value
                ]
            elif isinstance(value, dict):
                # Recursively blind nested dicts
                blinded[key] = self.blind_screen(value)
            else:
                blinded[key] = value
        
        # Add metadata about redaction
        blinded["_blind_screening"] = {
            "applied": True,
            "redaction_count": len(redaction_log),
            "method": "nlp_ner" if self.pii_detector.nlp else "pattern_only"
        }
        
        return blinded
    
    def _redact_if_pii(self, text: str) -> str:
        """Redact text if it contains PII."""
        if len(text) < 5:
            return text
        result = self.pii_detector.detect_pii(text)
        return result["redacted_text"] if result["has_pii"] else text
    
    def get_redaction_summary(self, original: Dict, blinded: Dict) -> Dict:
        """Generate a summary of what was redacted."""
        redacted_fields = []
        for key in original:
            if key in blinded:
                if blinded[key] == "[REDACTED]":
                    redacted_fields.append(key)
                elif isinstance(original[key], str) and original[key] != blinded.get(key):
                    redacted_fields.append(key)
        
        return {
            "total_fields": len(original),
            "redacted_fields": redacted_fields,
            "redacted_count": len(redacted_fields),
            "compliance": "BLIND_SCREENING_APPLIED"
        }


class ComplianceEngine:
    def __init__(self):
        self.logger = logging.getLogger("Watchtower_Policy_Engine")
        
        # Initialize NLP-powered detectors
        self.bias_detector = BiasDetector()
        self.pii_detector = PIIDetector()
        self.blind_screener = BlindScreener()
        
        # Load policies if needed (for now hardcoded for demo speed)
        self.weekend_blocked = True
        self.work_hours = (9, 17)  # 9 AM to 5 PM
        
        # Legacy fallback (kept for backwards compatibility)
        self.bias_terms = self.bias_detector.fallback_terms
        # Legacy pii_patterns now handled by PIIDetector, but kept for API compat
        self.pii_patterns = self.pii_detector.structured_patterns
    
    def blind_screen_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply NLP-powered blind screening to candidate data.
        
        Automatically detects and redacts PII using NER, not just static field names.
        """
        return self.blind_screener.blind_screen(candidate_data)
    
    def detect_pii(self, text: str) -> Dict[str, Any]:
        """
        Detect PII in text using NLP + regex patterns.
        
        Returns detailed analysis including entity types, risk level, and redacted text.
        """
        return self.pii_detector.detect_pii(text)
    
    def redact_pii(self, text: str, preserve_types: List[str] = None) -> str:
        """
        Redact all PII from text, optionally preserving certain types.
        """
        return self.pii_detector.redact_text(text, preserve_types)

    def check_intent(self, intent_type, payload, user_role="agent"):
        """
        Main entry point for Watchtower Intent Verification.
        Returns: (allowed: bool, reason: str, modified_payload: dict)
        """
        if intent_type == "schedule_interview":
            return self._check_scheduling(payload)
        elif intent_type == "send_email":
            return self._check_outbound_comm(payload)
        elif intent_type == "generate_offer":
            return self._check_offer_cap(payload)
        elif intent_type == "approve_expense":
            return self._check_expense(payload)
        elif intent_type == "onboard_employee":
            return self._check_legal_status(payload)
        
        return True, "Allowed", payload

    def _check_scheduling(self, payload):
        time_str = payload.get("time")
        if not time_str:
            return False, "Missing time", payload
        
        try:
            # Parse ISO format or simple string
            # Simplified for demo: Assume "YR-MON-DAY HH:MM"
            dt = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            
            # 1. Weekend Check
            if dt.weekday() >= 5: # 5=Sat, 6=Sun
                return False, "Policy Violation: No interviews on Weekends.", payload

            # 2. Hours Check
            if not (self.work_hours[0] <= dt.hour < self.work_hours[1]):
                 return False, f"Policy Violation: Interviews must be between {self.work_hours[0]}:00 and {self.work_hours[1]}:00.", payload
                 
            return True, "Schedule Approved", payload
        except ValueError:
            return False, "Invalid time format (Use YYYY-MM-DD HH:MM)", payload

    def _check_outbound_comm(self, payload):
        recipient = payload.get("recipient", "")
        body = payload.get("body", "")
        
        # 1. NLP-powered Bias & Inclusive Language Check
        bias_result = self.bias_detector.analyze_text(body)
        if bias_result['is_biased']:
            issues = bias_result['issues']
            suggestions = bias_result['suggestions']
            
            # Format the violation message with detected issues
            issue_terms = [i.get('term', 'unknown') for i in issues[:3]]  # Show first 3
            issue_str = ", ".join(f"'{t}'" for t in issue_terms)
            
            # Build helpful response with suggestions
            msg = f"Policy Violation: Non-inclusive language detected ({issue_str})."
            if suggestions:
                msg += f" Suggestions: {'; '.join(suggestions[:2])}"
            else:
                msg += " Please rephrase using inclusive language."
            
            return False, msg, payload

        # 2. NLP-powered PII Check (external recipients only)
        # If sending to external domain (not @company.com)
        if not recipient.endswith("@company.com"):
            # Use NLP-powered PII detection
            pii_result = self.pii_detector.detect_pii(body, context="external")
            
            if pii_result["has_pii"]:
                # Get redacted text, but preserve recipient's email
                redacted_body = pii_result["redacted_text"]
                # Restore recipient email if it was redacted
                if recipient in body and f"[EMAIL_REDACTED]" in redacted_body:
                    redacted_body = redacted_body.replace("[EMAIL_REDACTED]", recipient, 1)
                
                total_pii = pii_result["entity_count"] + pii_result["pattern_count"]
                risk = pii_result["risk_level"]
                
                # Block if high-sensitivity PII detected
                if pii_result["high_sensitivity_detected"]:
                    return False, f"Policy Violation: High-sensitivity PII detected (SSN/credit card/passport). Cannot send externally.", payload
                
                # Otherwise, auto-redact and allow
                payload["body"] = redacted_body
                
                # Build informative message
                entities = [e["type"] for e in pii_result["entities"][:3]]
                patterns = [p["type"] for p in pii_result["patterns"][:3]]
                detected_types = list(set(entities + patterns))
                
                return True, f"Modifying Intent: Redacted {total_pii} PII items ({', '.join(detected_types)}) for external transmission. Risk level: {risk}.", payload

        return True, "Communication Approved", payload

    def _check_offer_cap(self, payload):
        role = payload.get("role")
        salary = payload.get("salary")
        
        # Load bands (mock)
        bands = {
            "L3": 140000,
            "L4": 180000,
            "L5": 240000
        }
        
        cap = bands.get(role, 100000)
        if salary > cap:
            return False, f"Policy Violation: Offer ${salary} exceeds cap ${cap} for role {role}.", payload
            
        return True, "Offer Approved", payload

    def _check_expense(self, payload):
        amount = payload.get("amount", 0)
        category = payload.get("category", "General")
        has_receipt = payload.get("has_receipt", False)
        
        if amount > 50 and not has_receipt:
            return False, "Policy Violation: Expenses > $50 require a receipt.", payload
            
        return True, "Expense Approved", payload

    def _check_legal_status(self, payload):
        i9_status = payload.get("i9_status")
        if i9_status != "verified":
             return False, "Legal Violation: Cannot onboard without verified I-9.", payload
        return True, "Onboarding Approved", payload
