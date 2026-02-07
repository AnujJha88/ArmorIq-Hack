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
        self.logger = logging.getLogger("ArmorIQ_BiasDetector")
        
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


class ComplianceEngine:
    def __init__(self):
        self.logger = logging.getLogger("ArmorIQ_Policy_Engine")
        
        # Initialize NLP-powered bias detector
        self.bias_detector = BiasDetector()
        
        # Load policies if needed (for now hardcoded for demo speed)
        self.weekend_blocked = True
        self.work_hours = (9, 17)  # 9 AM to 5 PM
        self.pii_patterns = {
            "phone": r"\+?1?[-.]?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}",
            "email": r"[\w\.-]+@[\w\.-]+",
            "ssn": r"\d{3}-\d{2}-\d{4}"
        }
        
        # Legacy fallback (kept for backwards compatibility, but bias_detector is preferred)
        self.bias_terms = self.bias_detector.fallback_terms

    def check_intent(self, intent_type, payload, user_role="agent"):
        """
        Main entry point for ArmorIQ Intent Verification.
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

        # 2. PII Check
        # If sending to external domain (not @company.com)
        if not recipient.endswith("@company.com"):
            redacted_body = body
            redacted_count = 0
            for label, pattern in self.pii_patterns.items():
                # Don't redact the recipient's own email if it appears in body, but redact others
                matches = re.findall(pattern, body)
                for m in matches:
                    if m != recipient:
                        redacted_body = redacted_body.replace(m, f"[{label.upper()}_REDACTED]")
                        redacted_count += 1
            
            if redacted_count > 0:
                payload["body"] = redacted_body
                return True, f"Modifying Intent: Redacted {redacted_count} PII fields for external transmission.", payload

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
