"""
Evidence processing data models
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import json


class DocumentType(Enum):
    """Legal document classification types"""
    COURT_PETITION = "court_petition"
    POLICE_REPORT = "police_report"
    MEDICAL_OPINION = "medical_opinion"
    EMAIL_CORRESPONDENCE = "email_correspondence"
    WITNESS_STATEMENT = "witness_statement"
    LEGAL_BRIEF = "legal_brief"
    EVIDENCE_DOCUMENT = "evidence_document"
    PROCEDURAL_DOCUMENT = "procedural_document"
    UNKNOWN = "unknown"


class EvidenceStrength(Enum):
    """Evidence strength assessment"""
    CRITICAL = "critical"      # Strongest evidence, case-defining
    STRONG = "strong"          # Significant supporting evidence
    MODERATE = "moderate"      # Helpful supporting evidence
    WEAK = "weak"             # Minor supporting evidence
    NEUTRAL = "neutral"       # No clear impact
    CONTRADICTORY = "contradictory"  # Potentially harmful


@dataclass
class LegalDNA:
    """Legal DNA - core legal elements extracted from document"""
    document_id: str
    document_type: DocumentType = DocumentType.UNKNOWN
    key_facts: List[str] = field(default_factory=list)
    legal_entities: List[str] = field(default_factory=list)  # People, organizations
    dates_mentioned: List[str] = field(default_factory=list)
    locations_mentioned: List[str] = field(default_factory=list)
    legal_citations: List[str] = field(default_factory=list)
    procedural_elements: List[str] = field(default_factory=list)
    evidence_references: List[str] = field(default_factory=list)
    claims_made: List[str] = field(default_factory=list)
    defenses_mentioned: List[str] = field(default_factory=list)
    witness_references: List[str] = field(default_factory=list)
    damage_claims: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    extraction_method: str = "manual"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'document_id': self.document_id,
            'document_type': self.document_type.value,
            'key_facts': self.key_facts,
            'legal_entities': self.legal_entities,
            'dates_mentioned': self.dates_mentioned,
            'locations_mentioned': self.locations_mentioned,
            'legal_citations': self.legal_citations,
            'procedural_elements': self.procedural_elements,
            'evidence_references': self.evidence_references,
            'claims_made': self.claims_made,
            'defenses_mentioned': self.defenses_mentioned,
            'witness_references': self.witness_references,
            'damage_claims': self.damage_claims,
            'confidence_score': self.confidence_score,
            'extraction_method': self.extraction_method
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LegalDNA':
        """Create from dictionary"""
        return cls(
            document_id=data['document_id'],
            document_type=DocumentType(data.get('document_type', 'unknown')),
            key_facts=data.get('key_facts', []),
            legal_entities=data.get('legal_entities', []),
            dates_mentioned=data.get('dates_mentioned', []),
            locations_mentioned=data.get('locations_mentioned', []),
            legal_citations=data.get('legal_citations', []),
            procedural_elements=data.get('procedural_elements', []),
            evidence_references=data.get('evidence_references', []),
            claims_made=data.get('claims_made', []),
            defenses_mentioned=data.get('defenses_mentioned', []),
            witness_references=data.get('witness_references', []),
            damage_claims=data.get('damage_claims', []),
            confidence_score=data.get('confidence_score', 0.0),
            extraction_method=data.get('extraction_method', 'manual')
        )


@dataclass
class StrategicMapping:
    """Mapping of evidence to legal defense strategies"""
    truth_defense_relevance: EvidenceStrength = EvidenceStrength.NEUTRAL
    truth_defense_notes: str = ""
    good_faith_relevance: EvidenceStrength = EvidenceStrength.NEUTRAL
    good_faith_notes: str = ""
    procedural_defense_relevance: EvidenceStrength = EvidenceStrength.NEUTRAL
    procedural_defense_notes: str = ""
    overall_strategic_value: EvidenceStrength = EvidenceStrength.NEUTRAL
    recommended_actions: List[str] = field(default_factory=list)
    
    def get_strongest_defense(self) -> str:
        """Get the defense strategy this evidence best supports"""
        strengths = {
            'truth_defense': self.truth_defense_relevance,
            'good_faith_defense': self.good_faith_relevance,
            'procedural_defense': self.procedural_defense_relevance
        }
        
        # Sort by enum value (assumes stronger enums have higher precedence)
        strength_order = {
            EvidenceStrength.CRITICAL: 6,
            EvidenceStrength.STRONG: 5,
            EvidenceStrength.MODERATE: 4,
            EvidenceStrength.WEAK: 3,
            EvidenceStrength.NEUTRAL: 2,
            EvidenceStrength.CONTRADICTORY: 1
        }
        
        return max(strengths.items(), key=lambda x: strength_order[x[1]])[0]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'truth_defense_relevance': self.truth_defense_relevance.value,
            'truth_defense_notes': self.truth_defense_notes,
            'good_faith_relevance': self.good_faith_relevance.value,
            'good_faith_notes': self.good_faith_notes,
            'procedural_defense_relevance': self.procedural_defense_relevance.value,
            'procedural_defense_notes': self.procedural_defense_notes,
            'overall_strategic_value': self.overall_strategic_value.value,
            'recommended_actions': self.recommended_actions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategicMapping':
        """Create from dictionary"""
        return cls(
            truth_defense_relevance=EvidenceStrength(data.get('truth_defense_relevance', 'neutral')),
            truth_defense_notes=data.get('truth_defense_notes', ''),
            good_faith_relevance=EvidenceStrength(data.get('good_faith_relevance', 'neutral')),
            good_faith_notes=data.get('good_faith_notes', ''),
            procedural_defense_relevance=EvidenceStrength(data.get('procedural_defense_relevance', 'neutral')),
            procedural_defense_notes=data.get('procedural_defense_notes', ''),
            overall_strategic_value=EvidenceStrength(data.get('overall_strategic_value', 'neutral')),
            recommended_actions=data.get('recommended_actions', [])
        )


@dataclass
class CrossReference:
    """Cross-reference connection between documents"""
    source_document_id: str
    target_document_id: str
    connection_type: str  # "supports", "contradicts", "supplements", "references"
    connection_strength: float  # 0.0 to 1.0
    description: str
    specific_elements: List[str] = field(default_factory=list)  # Specific facts/elements that connect
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'source_document_id': self.source_document_id,
            'target_document_id': self.target_document_id,
            'connection_type': self.connection_type,
            'connection_strength': self.connection_strength,
            'description': self.description,
            'specific_elements': self.specific_elements
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CrossReference':
        """Create from dictionary"""
        return cls(
            source_document_id=data['source_document_id'],
            target_document_id=data['target_document_id'],
            connection_type=data['connection_type'],
            connection_strength=data['connection_strength'],
            description=data['description'],
            specific_elements=data.get('specific_elements', [])
        )


@dataclass
class EvidenceItem:
    """Complete evidence item with all analysis"""
    document_id: str
    file_path: str
    legal_dna: LegalDNA
    strategic_mapping: StrategicMapping
    cross_references: List[CrossReference] = field(default_factory=list)
    processing_timestamp: datetime = field(default_factory=datetime.now)
    processing_version: str = "1.0"
    human_reviewed: bool = False
    review_notes: str = ""
    tags: Set[str] = field(default_factory=set)
    
    def add_cross_reference(self, cross_ref: CrossReference):
        """Add cross-reference connection"""
        self.cross_references.append(cross_ref)
    
    def get_summary(self) -> str:
        """Get human-readable summary of evidence"""
        doc_type = self.legal_dna.document_type.value.replace('_', ' ').title()
        strongest_defense = self.strategic_mapping.get_strongest_defense().replace('_', ' ').title()
        
        summary = f"📄 {doc_type}\n"
        summary += f"🎯 Primary Defense: {strongest_defense}\n"
        summary += f"💪 Strategic Value: {self.strategic_mapping.overall_strategic_value.value.title()}\n"
        
        if self.legal_dna.key_facts:
            summary += f"📋 Key Facts: {len(self.legal_dna.key_facts)} identified\n"
        
        if self.cross_references:
            summary += f"🔗 Connected to {len(self.cross_references)} other documents\n"
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'document_id': self.document_id,
            'file_path': self.file_path,
            'legal_dna': self.legal_dna.to_dict(),
            'strategic_mapping': self.strategic_mapping.to_dict(),
            'cross_references': [ref.to_dict() for ref in self.cross_references],
            'processing_timestamp': self.processing_timestamp.isoformat(),
            'processing_version': self.processing_version,
            'human_reviewed': self.human_reviewed,
            'review_notes': self.review_notes,
            'tags': list(self.tags)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvidenceItem':
        """Create from dictionary"""
        return cls(
            document_id=data['document_id'],
            file_path=data['file_path'],
            legal_dna=LegalDNA.from_dict(data['legal_dna']),
            strategic_mapping=StrategicMapping.from_dict(data['strategic_mapping']),
            cross_references=[CrossReference.from_dict(ref_data) for ref_data in data.get('cross_references', [])],
            processing_timestamp=datetime.fromisoformat(data['processing_timestamp']),
            processing_version=data.get('processing_version', '1.0'),
            human_reviewed=data.get('human_reviewed', False),
            review_notes=data.get('review_notes', ''),
            tags=set(data.get('tags', []))
        )


@dataclass
class DocumentClassification:
    """Classification result for a legal document"""
    document_id: str
    primary_type: DocumentType
    confidence: float
    secondary_types: List[DocumentType] = field(default_factory=list)
    classification_reasoning: str = ""
    classifier_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'document_id': self.document_id,
            'primary_type': self.primary_type.value,
            'confidence': self.confidence,
            'secondary_types': [dt.value for dt in self.secondary_types],
            'classification_reasoning': self.classification_reasoning,
            'classifier_version': self.classifier_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentClassification':
        """Create from dictionary"""
        return cls(
            document_id=data['document_id'],
            primary_type=DocumentType(data['primary_type']),
            confidence=data['confidence'],
            secondary_types=[DocumentType(dt) for dt in data.get('secondary_types', [])],
            classification_reasoning=data.get('classification_reasoning', ''),
            classifier_version=data.get('classifier_version', '1.0')
        )


@dataclass
class EvidenceReport:
    """Comprehensive evidence analysis report"""
    document_id: str
    classification: DocumentClassification
    evidence_item: EvidenceItem
    recommendations: List[str] = field(default_factory=list)
    gaps_identified: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'document_id': self.document_id,
            'classification': self.classification.to_dict(),
            'evidence_item': self.evidence_item.to_dict(),
            'recommendations': self.recommendations,
            'gaps_identified': self.gaps_identified,
            'next_actions': self.next_actions,
            'generated_at': self.generated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvidenceReport':
        """Create from dictionary"""
        return cls(
            document_id=data['document_id'],
            classification=DocumentClassification.from_dict(data['classification']),
            evidence_item=EvidenceItem.from_dict(data['evidence_item']),
            recommendations=data.get('recommendations', []),
            gaps_identified=data.get('gaps_identified', []),
            next_actions=data.get('next_actions', []),
            generated_at=datetime.fromisoformat(data['generated_at'])
        ) 