"""
NidaanPath AI — app/models/patient_case.py
SQLAlchemy model for a patient diagnostic case.
"""
import json
import uuid
from datetime import datetime
from ..extensions import db


class PatientCase(db.Model):
    __tablename__ = 'patient_cases'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_code = db.Column(db.String(16), unique=True, nullable=False)
    demo_mode = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(5), default='en')

    # Patient story
    patient_name = db.Column(db.String(200), default='Anonymous Patient')
    patient_narration = db.Column(db.Text, nullable=True)
    main_concern = db.Column(db.String(500), nullable=True)
    symptom_duration = db.Column(db.String(100), nullable=True)
    narration_extraction_json = db.Column(db.Text, nullable=True)

    # Journey state
    journey_state = db.Column(db.String(50), default='Awaiting Evidence')
    stagnation_signals_json = db.Column(db.Text, default='[]')
    journey_events_json = db.Column(db.Text, default='[]')
    uncertainty_items_json = db.Column(db.Text, default='[]')
    agent_actions_json = db.Column(db.Text, default='[]')
    resolved_gaps_json = db.Column(db.Text, default='[]')
    remaining_gaps_json = db.Column(db.Text, default='[]')
    clinician_packet_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = db.relationship('MedicalDocument', backref='case', lazy=True,
                                 cascade='all, delete-orphan')

    @classmethod
    def generate_case_code(cls):
        import random, string
        return 'NP-' + ''.join(random.choices(string.digits, k=6))

    def get_stagnation_signals(self):
        return json.loads(self.stagnation_signals_json or '[]')

    def set_stagnation_signals(self, signals):
        self.stagnation_signals_json = json.dumps(signals)

    def get_journey_events(self):
        return json.loads(self.journey_events_json or '[]')

    def set_journey_events(self, events):
        self.journey_events_json = json.dumps(events)

    def get_uncertainty_items(self):
        return json.loads(self.uncertainty_items_json or '[]')

    def set_uncertainty_items(self, items):
        self.uncertainty_items_json = json.dumps(items)

    def get_agent_actions(self):
        return json.loads(self.agent_actions_json or '[]')

    def set_agent_actions(self, actions):
        self.agent_actions_json = json.dumps(actions)

    def get_remaining_gaps(self):
        return json.loads(self.remaining_gaps_json or '[]')

    def set_remaining_gaps(self, gaps):
        self.remaining_gaps_json = json.dumps(gaps)

    def get_resolved_gaps(self):
        return json.loads(self.resolved_gaps_json or '[]')

    def set_resolved_gaps(self, gaps):
        self.resolved_gaps_json = json.dumps(gaps)

    def to_dict(self):
        return {
            'id': self.id,
            'case_code': self.case_code,
            'demo_mode': self.demo_mode,
            'language': self.language,
            'patient_name': self.patient_name,
            'main_concern': self.main_concern,
            'symptom_duration': self.symptom_duration,
            'journey_state': self.journey_state,
            'stagnation_signals': self.get_stagnation_signals(),
            'journey_events': self.get_journey_events(),
            'uncertainty_items': self.get_uncertainty_items(),
            'remaining_gaps': self.get_remaining_gaps(),
            'resolved_gaps': self.get_resolved_gaps(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
