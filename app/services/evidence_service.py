"""
Evidence Service - Basic evidence processing and analysis
"""
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.models.evidence_models import (
    DocumentType, 
    EvidenceStrength,
    LegalDNA,
    StrategicMapping,
    DocumentClassification,
    EvidenceItem,
    EvidenceReport
)
from app.core.error_handler import DocumentProcessingError


class BasicEvidenceProcessor:
    """Basic evidence processing for legal documents
    
    Phase 1 Implementation:
    - Rule-based document classification
    - Basic legal element extraction  
    - Strategic value assessment
    """
    
    def __init__(self):
        self._classification_rules = self._init_classification_rules()
        self._legal_patterns = self._init_legal_patterns()
    
    def process_document(self, document_id: str, file_path: str, content: str) -> EvidenceReport:
        """Process document and generate evidence report"""
        try:
            # Step 1: Classify document type
            classification = self._classify_document(document_id, content)
            
            # Step 2: Extract legal DNA
            legal_dna = self._extract_legal_dna(document_id, content, classification.primary_type)
            
            # Step 3: Assess strategic value
            strategic_mapping = self._assess_strategic_value(legal_dna, content)
            
            # Step 4: Create evidence item
            evidence_item = EvidenceItem(
                document_id=document_id,
                file_path=file_path,
                legal_dna=legal_dna,
                strategic_mapping=strategic_mapping
            )
            
            # Step 5: Generate recommendations
            recommendations = self._generate_recommendations(evidence_item)
            gaps_identified = self._identify_gaps(evidence_item)
            next_actions = self._suggest_next_actions(evidence_item)
            
            return EvidenceReport(
                document_id=document_id,
                classification=classification,
                evidence_item=evidence_item,
                recommendations=recommendations,
                gaps_identified=gaps_identified,
                next_actions=next_actions
            )
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to process document {document_id}: {e}")
    
    def _classify_document(self, document_id: str, content: str) -> DocumentClassification:
        """Classify document using rule-based approach"""
        content_lower = content.lower()
        
        # Score each document type
        type_scores = {}
        for doc_type, rules in self._classification_rules.items():
            score = 0
            matched_rules = []
            
            for rule_pattern, weight in rules:
                if re.search(rule_pattern, content_lower, re.IGNORECASE):
                    score += weight
                    matched_rules.append(rule_pattern)
            
            type_scores[doc_type] = (score, matched_rules)
        
        # Find best match
        best_type = max(type_scores.items(), key=lambda x: x[1][0])
        primary_type = DocumentType(best_type[0])
        confidence = min(best_type[1][0] / 10.0, 1.0)  # Normalize to 0-1
        
        # Get secondary types (scores > 0)
        secondary_types = [
            DocumentType(doc_type) for doc_type, (score, _) in type_scores.items()
            if score > 0 and doc_type != best_type[0]
        ]
        
        reasoning = f"Matched patterns: {', '.join(best_type[1][1][:3])}"  # Top 3 patterns
        
        return DocumentClassification(
            document_id=document_id,
            primary_type=primary_type,
            confidence=confidence,
            secondary_types=secondary_types,
            classification_reasoning=reasoning
        )
    
    def _extract_legal_dna(self, document_id: str, content: str, doc_type: DocumentType) -> LegalDNA:
        """Extract legal elements from document content"""
        legal_dna = LegalDNA(document_id=document_id, document_type=doc_type)
        
        # Extract legal entities (names, organizations)
        legal_dna.legal_entities = self._extract_entities(content)
        
        # Extract dates
        legal_dna.dates_mentioned = self._extract_dates(content)
        
        # Extract locations  
        legal_dna.locations_mentioned = self._extract_locations(content)
        
        # Extract legal citations
        legal_dna.legal_citations = self._extract_legal_citations(content)
        
        # Extract key facts based on document type
        legal_dna.key_facts = self._extract_key_facts(content, doc_type)
        
        # Extract claims and defenses
        legal_dna.claims_made = self._extract_claims(content)
        legal_dna.defenses_mentioned = self._extract_defenses(content)
        
        # Extract witness references
        legal_dna.witness_references = self._extract_witness_references(content)
        
        # Extract damage claims
        legal_dna.damage_claims = self._extract_damage_claims(content)
        
        # Set confidence based on extraction success
        total_elements = (
            len(legal_dna.legal_entities) + len(legal_dna.dates_mentioned) +
            len(legal_dna.key_facts) + len(legal_dna.claims_made)
        )
        legal_dna.confidence_score = min(total_elements / 10.0, 1.0)
        legal_dna.extraction_method = "rule_based_v1"
        
        return legal_dna
    
    def _assess_strategic_value(self, legal_dna: LegalDNA, content: str) -> StrategicMapping:
        """Assess strategic value for defense arguments"""
        mapping = StrategicMapping()
        
        # Truth Defense Assessment
        truth_indicators = self._count_truth_indicators(content, legal_dna)
        if truth_indicators >= 5:
            mapping.truth_defense_relevance = EvidenceStrength.STRONG
            mapping.truth_defense_notes = f"Strong truth defense evidence: {truth_indicators} indicators found"
        elif truth_indicators >= 3:
            mapping.truth_defense_relevance = EvidenceStrength.MODERATE
            mapping.truth_defense_notes = f"Moderate truth defense evidence: {truth_indicators} indicators found"
        elif truth_indicators >= 1:
            mapping.truth_defense_relevance = EvidenceStrength.WEAK
            mapping.truth_defense_notes = f"Weak truth defense evidence: {truth_indicators} indicators found"
        
        # Good Faith Defense Assessment
        good_faith_indicators = self._count_good_faith_indicators(content, legal_dna)
        if good_faith_indicators >= 4:
            mapping.good_faith_relevance = EvidenceStrength.STRONG
            mapping.good_faith_notes = f"Strong good faith evidence: {good_faith_indicators} indicators found"
        elif good_faith_indicators >= 2:
            mapping.good_faith_relevance = EvidenceStrength.MODERATE
            mapping.good_faith_notes = f"Moderate good faith evidence: {good_faith_indicators} indicators found"
        elif good_faith_indicators >= 1:
            mapping.good_faith_relevance = EvidenceStrength.WEAK
            mapping.good_faith_notes = f"Weak good faith evidence: {good_faith_indicators} indicators found"
        
        # Procedural Defense Assessment
        procedural_indicators = self._count_procedural_indicators(content, legal_dna)
        if procedural_indicators >= 3:
            mapping.procedural_defense_relevance = EvidenceStrength.MODERATE
            mapping.procedural_defense_notes = f"Procedural issues identified: {procedural_indicators} indicators"
        elif procedural_indicators >= 1:
            mapping.procedural_defense_relevance = EvidenceStrength.WEAK
            mapping.procedural_defense_notes = f"Minor procedural issues: {procedural_indicators} indicators"
        
        # Overall strategic value (max of individual assessments)
        strengths = [
            mapping.truth_defense_relevance,
            mapping.good_faith_relevance,
            mapping.procedural_defense_relevance
        ]
        
        strength_values = {
            EvidenceStrength.CRITICAL: 6,
            EvidenceStrength.STRONG: 5,
            EvidenceStrength.MODERATE: 4,
            EvidenceStrength.WEAK: 3,
            EvidenceStrength.NEUTRAL: 2,
            EvidenceStrength.CONTRADICTORY: 1
        }
        
        max_strength = max(strengths, key=lambda x: strength_values[x])
        mapping.overall_strategic_value = max_strength
        
        return mapping
    
    def _generate_recommendations(self, evidence_item: EvidenceItem) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        strategic = evidence_item.strategic_mapping
        legal_dna = evidence_item.legal_dna
        
        # Based on strategic value
        if strategic.overall_strategic_value in [EvidenceStrength.STRONG, EvidenceStrength.CRITICAL]:
            recommendations.append("🌟 High-value evidence - prioritize in defense strategy")
            recommendations.append("📝 Consider highlighting in legal briefs")
        
        # Based on document type
        if legal_dna.document_type == DocumentType.POLICE_REPORT:
            recommendations.append("👮 Police report - verify factual accuracy against other evidence")
        elif legal_dna.document_type == DocumentType.MEDICAL_OPINION:
            recommendations.append("🏥 Medical evidence - cross-reference with other medical documents")
        elif legal_dna.document_type == DocumentType.EMAIL_CORRESPONDENCE:
            recommendations.append("📧 Email correspondence - check dates and recipients for timeline accuracy")
        
        # Based on cross-reference potential
        if len(legal_dna.legal_entities) > 3:
            recommendations.append("🔗 Multiple entities mentioned - look for connections in other documents")
        
        if len(legal_dna.dates_mentioned) > 2:
            recommendations.append("📅 Multiple dates - create timeline with other evidence")
        
        return recommendations
    
    def _identify_gaps(self, evidence_item: EvidenceItem) -> List[str]:
        """Identify information gaps"""
        gaps = []
        legal_dna = evidence_item.legal_dna
        
        if not legal_dna.legal_entities:
            gaps.append("❓ No clear parties identified - may need additional context")
        
        if not legal_dna.dates_mentioned:
            gaps.append("📅 No dates mentioned - timeline unclear")
        
        if not legal_dna.claims_made and legal_dna.document_type != DocumentType.PROCEDURAL_DOCUMENT:
            gaps.append("⚖️ No clear legal claims identified")
        
        if legal_dna.confidence_score < 0.5:
            gaps.append("🔍 Low confidence extraction - may need manual review")
        
        return gaps
    
    def _suggest_next_actions(self, evidence_item: EvidenceItem) -> List[str]:
        """Suggest next actions based on analysis"""
        actions = []
        
        strategic = evidence_item.strategic_mapping
        
        if strategic.truth_defense_relevance == EvidenceStrength.STRONG:
            actions.append("✅ Include in truth defense evidence compilation")
        
        if strategic.good_faith_relevance == EvidenceStrength.STRONG:
            actions.append("🤝 Include in good faith defense documentation")
        
        if strategic.overall_strategic_value == EvidenceStrength.WEAK:
            actions.append("📝 Consider supplementing with additional evidence")
        
        actions.append("🔄 Cross-reference with other processed documents")
        actions.append("👁️ Schedule for human review and validation")
        
        return actions
    
    def _init_classification_rules(self) -> Dict[str, List[tuple]]:
        """Initialize document classification rules"""
        return {
            'court_petition': [
                (r'בית.*משפט', 5),  # Court
                (r'תביעה|תובע|נתבע', 4),  # Lawsuit/plaintiff/defendant
                (r'בקשה|עתירה', 4),  # Petition/request
                (r'כבוד.*השופט', 3),  # Honorable Judge
                (r'פסק.*דין', 3),  # Verdict/judgment
            ],
            'police_report': [
                (r'משטרת.*ישראל', 5),  # Israel Police
                (r'תלונה|דו.*ח.*משטרה', 4),  # Complaint/police report
                (r'חוקר|בלש', 3),  # Investigator/detective
                (r'מס.*תיק', 3),  # File number
                (r'עבירה|חקירה', 3),  # Offense/investigation
            ],
            'medical_opinion': [
                (r'חוות.*דעת.*רפואית', 5),  # Medical opinion
                (r'ד.*ר|פרופ', 4),  # Dr./Prof.
                (r'בית.*חולים|מרפאה', 4),  # Hospital/clinic
                (r'אבחנה|טיפול', 3),  # Diagnosis/treatment
                (r'רפואי|קליני', 3),  # Medical/clinical
            ],
            'email_correspondence': [
                (r'@.*\..*|מאת:|אל:', 5),  # Email patterns
                (r'נשלח.*ב|תאריך.*שליחה', 3),  # Sent on/send date
                (r'נושא:|subject:', 3),  # Subject
                (r'דוא.*ל|email', 4),  # Email
            ],
            'witness_statement': [
                (r'הצהרה|עדות', 5),  # Statement/testimony
                (r'עד|מעיד', 4),  # Witness/testifies
                (r'ראיתי|שמעתי', 3),  # I saw/I heard
                (r'אני.*חתום', 3),  # I hereby sign
            ],
            'evidence_document': [
                (r'ראיה|הוכחה', 4),  # Evidence/proof
                (r'מסמך|תעודה', 3),  # Document/certificate
                (r'מצורף|נספח', 3),  # Attached/appendix
            ]
        }
    
    def _init_legal_patterns(self) -> Dict[str, str]:
        """Initialize legal pattern matching"""
        return {
            'dates': r'\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}|\d{1,2}\s+\w+\s+\d{4}',
            'legal_citations': r'פסק.*דין|פס.*ד|ע.*א|בג.*ץ|ה.*ע.*א',
            'money_amounts': r'\d+\s*₪|\d+\s*שקל|\d+\s*דולר',
            'entities': r'[א-ת][א-ת\s]{2,30}(?=\s|$|[.,])'
        }
    
    def _extract_entities(self, content: str) -> List[str]:
        """Extract legal entities (names, organizations)"""
        # Simple Hebrew name pattern - can be enhanced with NLP
        pattern = r'[א-ת][א-ת\s]{1,25}[א-ת]'
        matches = re.findall(pattern, content)
        
        # Filter and clean
        entities = []
        for match in matches:
            clean_match = match.strip()
            if len(clean_match) > 3 and len(clean_match.split()) <= 4:
                entities.append(clean_match)
        
        # Remove duplicates and return top matches
        return list(set(entities))[:10]
    
    def _extract_dates(self, content: str) -> List[str]:
        """Extract dates from content"""
        date_pattern = self._legal_patterns['dates']
        dates = re.findall(date_pattern, content)
        return list(set(dates))[:5]
    
    def _extract_locations(self, content: str) -> List[str]:
        """Extract location references"""
        # Common Israeli location patterns
        location_patterns = [
            r'תל.*אביב|ירושלים|חיפה|באר.*שבע',
            r'רחוב\s+[א-ת\s]+\d*',
            r'בית.*משפט\s+[א-ת\s]+'
        ]
        
        locations = []
        for pattern in location_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            locations.extend(matches)
        
        return list(set(locations))[:5]
    
    def _extract_legal_citations(self, content: str) -> List[str]:
        """Extract legal citations"""
        citation_pattern = self._legal_patterns['legal_citations']
        citations = re.findall(citation_pattern, content, re.IGNORECASE)
        return list(set(citations))[:5]
    
    def _extract_key_facts(self, content: str, doc_type: DocumentType) -> List[str]:
        """Extract key facts based on document type"""
        # This is a simplified version - can be enhanced with AI
        sentences = content.split('.')
        key_facts = []
        
        # Look for fact-indicating patterns
        fact_patterns = [
            r'העובדה.*ש',  # The fact that
            r'מאחר.*ש',    # Since/because
            r'בשל.*כך',    # Due to this
            r'לאור.*האמור'  # In light of the above
        ]
        
        for sentence in sentences[:20]:  # Check first 20 sentences
            for pattern in fact_patterns:
                if re.search(pattern, sentence):
                    clean_sentence = sentence.strip()
                    if len(clean_sentence) > 20:
                        key_facts.append(clean_sentence)
                        break
        
        return key_facts[:5]
    
    def _extract_claims(self, content: str) -> List[str]:
        """Extract legal claims"""
        claim_patterns = [
            r'תביעה.*ל',   # Claim for
            r'דרישה.*ל',   # Demand for
            r'טענת.*ה'      # Claim that
        ]
        
        claims = []
        for pattern in claim_patterns:
            matches = re.findall(f'{pattern}[^.]*', content)
            claims.extend(matches)
        
        return claims[:3]
    
    def _extract_defenses(self, content: str) -> List[str]:
        """Extract defense arguments"""
        defense_patterns = [
            r'הגנה.*מפני',  # Defense against
            r'בתשובה.*ל',   # In response to
            r'סותר.*את'     # Contradicts
        ]
        
        defenses = []
        for pattern in defense_patterns:
            matches = re.findall(f'{pattern}[^.]*', content)
            defenses.extend(matches)
        
        return defenses[:3]
    
    def _extract_witness_references(self, content: str) -> List[str]:
        """Extract witness references"""
        witness_patterns = [
            r'עד\s+[א-ת\s]+',     # Witness [name]
            r'מעיד\s+[א-ת\s]+',   # Testifies [name]
            r'עדותו.*של'          # Testimony of
        ]
        
        witnesses = []
        for pattern in witness_patterns:
            matches = re.findall(pattern, content)
            witnesses.extend(matches)
        
        return witnesses[:5]
    
    def _extract_damage_claims(self, content: str) -> List[str]:
        """Extract damage claims"""
        damage_patterns = [
            r'נזק.*של.*\d+',      # Damage of [amount]
            r'פיצוי.*בסך.*\d+',   # Compensation of [amount]
            r'הפסד.*כלכלי'        # Economic loss
        ]
        
        damages = []
        for pattern in damage_patterns:
            matches = re.findall(pattern, content)
            damages.extend(matches)
        
        return damages[:3]
    
    def _count_truth_indicators(self, content: str, legal_dna: LegalDNA) -> int:
        """Count indicators supporting truth defense"""
        indicators = 0
        
        # Factual documentation indicators
        if any('עובדה' in fact for fact in legal_dna.key_facts):
            indicators += 2
        
        # Medical/police report indicators  
        if legal_dna.document_type in [DocumentType.POLICE_REPORT, DocumentType.MEDICAL_OPINION]:
            indicators += 3
        
        # Witness testimony indicators
        if legal_dna.witness_references:
            indicators += len(legal_dna.witness_references)
        
        # Documentation date indicators
        if legal_dna.dates_mentioned:
            indicators += 1
        
        return indicators
    
    def _count_good_faith_indicators(self, content: str, legal_dna: LegalDNA) -> int:
        """Count indicators supporting good faith defense"""
        indicators = 0
        
        # Helping/assistance patterns
        help_patterns = [r'עזרה|סיוע|תמיכה', r'למען|בעד', r'הגנה.*על']
        for pattern in help_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                indicators += 2
        
        # Institutional contact indicators
        if legal_dna.legal_entities:
            indicators += 1
        
        # Communication evidence
        if legal_dna.document_type == DocumentType.EMAIL_CORRESPONDENCE:
            indicators += 1
        
        return indicators
    
    def _count_procedural_indicators(self, content: str, legal_dna: LegalDNA) -> int:
        """Count indicators for procedural defense"""
        indicators = 0
        
        # Procedural violation patterns
        violation_patterns = [r'הפרת.*הליך', r'פגם.*בהליך', r'חריגה.*מסמכות']
        for pattern in violation_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                indicators += 2
        
        # Rights violation patterns
        rights_patterns = [r'פגיעה.*בזכות', r'הפרת.*זכות']
        for pattern in rights_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                indicators += 2
        
        return indicators


class EvidenceService:
    """Service for evidence processing and management"""
    
    def __init__(self, data_paths: Dict[str, Path]):
        self.evidence_path = data_paths.get('evidence', Path('data/evidence_items'))
        self.evidence_path.mkdir(parents=True, exist_ok=True)
        self.processor = BasicEvidenceProcessor()
    
    def process_document(self, document_id: str, file_path: str, content: str) -> EvidenceReport:
        """Process document and save evidence report"""
        report = self.processor.process_document(document_id, file_path, content)
        
        # Save evidence report
        self._save_evidence_report(report)
        
        return report
    
    def get_evidence_item(self, document_id: str) -> Optional[EvidenceItem]:
        """Get evidence item by document ID"""
        evidence_file = self.evidence_path / f"{document_id}_evidence.json"
        
        if not evidence_file.exists():
            return None
        
        try:
            with open(evidence_file, 'r', encoding='utf-8') as f:
                import json
                data = json.load(f)
                return EvidenceItem.from_dict(data['evidence_item'])
        except Exception:
            return None
    
    def list_evidence_items(self) -> List[EvidenceItem]:
        """List all processed evidence items"""
        evidence_items = []
        
        for evidence_file in self.evidence_path.glob("*_evidence.json"):
            try:
                with open(evidence_file, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                    evidence_item = EvidenceItem.from_dict(data['evidence_item'])
                    evidence_items.append(evidence_item)
            except Exception:
                continue
        
        return evidence_items
    
    def get_evidence_summary(self) -> Dict[str, Any]:
        """Get summary of all evidence"""
        evidence_items = self.list_evidence_items()
        
        if not evidence_items:
            return {
                'total_items': 0,
                'by_type': {},
                'by_strength': {},
                'processing_stats': {}
            }
        
        # Aggregate statistics
        by_type = {}
        by_strength = {}
        
        for item in evidence_items:
            # Count by document type
            doc_type = item.legal_dna.document_type.value
            by_type[doc_type] = by_type.get(doc_type, 0) + 1
            
            # Count by strategic strength
            strength = item.strategic_mapping.overall_strategic_value.value
            by_strength[strength] = by_strength.get(strength, 0) + 1
        
        return {
            'total_items': len(evidence_items),
            'by_type': by_type,
            'by_strength': by_strength,
            'processing_stats': {
                'avg_confidence': sum(item.legal_dna.confidence_score for item in evidence_items) / len(evidence_items),
                'human_reviewed': sum(1 for item in evidence_items if item.human_reviewed),
                'with_cross_refs': sum(1 for item in evidence_items if item.cross_references)
            }
        }
    
    def _save_evidence_report(self, report: EvidenceReport):
        """Save evidence report to storage"""
        evidence_file = self.evidence_path / f"{report.document_id}_evidence.json"
        
        try:
            with open(evidence_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise DocumentProcessingError(f"Failed to save evidence report: {e}")
    
    def clear_all_evidence(self) -> Dict[str, Any]:
        """Clear all evidence analysis data"""
        results = {
            'evidence_files_deleted': 0,
            'errors': []
        }
        
        try:
            # Clear all evidence files
            for evidence_file in self.evidence_path.glob("*_evidence.json"):
                try:
                    evidence_file.unlink()
                    results['evidence_files_deleted'] += 1
                except Exception as e:
                    results['errors'].append(f"Failed to delete {evidence_file.name}: {e}")
            
        except Exception as e:
            results['errors'].append(f"System error during evidence clearing: {e}")
        
        return results 