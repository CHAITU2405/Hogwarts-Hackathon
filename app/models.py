from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(200), nullable=False, unique=True)
    house = db.Column(db.String(50), nullable=False)
    team_size = db.Column(db.Integer, nullable=False)
    utr_transaction_id = db.Column(db.String(200), nullable=False)
    payment_proof_path = db.Column(db.String(500), nullable=True)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    approval_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    selected_problem_statement_id = db.Column(db.Integer, db.ForeignKey('problem_statements.id'), nullable=True)
    git_repo_url = db.Column(db.String(500), nullable=True)  # GitHub/GitLab repository URL
    
    # Relationships
    members = db.relationship('Member', backref='team', lazy=True, cascade='all, delete-orphan')
    selected_problem = db.relationship('ProblemStatement', foreign_keys=[selected_problem_statement_id], backref='teams_selected')
    
    def to_dict(self):
        return {
            'id': self.id,
            'team_name': self.team_name,
            'house': self.house,
            'team_size': self.team_size,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
            'approval_status': self.approval_status,
            'utr_transaction_id': self.utr_transaction_id,
            'payment_proof_path': self.payment_proof_path,
            'selected_problem_statement_id': self.selected_problem_statement_id,
            'git_repo_url': self.git_repo_url or '',
            'members': [member.to_dict() for member in self.members]
        }
    
    def to_dict_summary(self):
        # Get college name from team members (first member's college or empty)
        college_name = ''
        try:
            if self.members and len(self.members) > 0:
                # Get college from first member (leader)
                first_member = self.members[0]
                if hasattr(first_member, 'college_name') and first_member.college_name:
                    college_name = first_member.college_name
        except (AttributeError, KeyError, Exception):
            college_name = ''
        
        # Safely get members
        members_list = []
        try:
            if self.members:
                members_list = [member.name for member in self.members]
        except (AttributeError, Exception):
            members_list = []
        
        return {
            'id': self.id,
            'name': self.team_name,
            'house': self.house,
            'members': members_list,
            'projectUrl': self.git_repo_url or '',  # Git repository URL
            'college': college_name,
            'description': f'A brave team from {self.house} house',
            'approval_status': self.approval_status
        }

class Member(db.Model):
    __tablename__ = 'members'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    college_name = db.Column(db.String(200), nullable=True)
    is_leader = db.Column(db.Boolean, default=False)
    member_order = db.Column(db.Integer, nullable=False)  # Order in team (1, 2, 3, 4)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'college_name': self.college_name or '',
            'is_leader': self.is_leader,
            'member_order': self.member_order
        }

class ProblemStatement(db.Model):
    __tablename__ = 'problem_statements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=False)
    domain = db.Column(db.String(50), nullable=False)  # gryffindor, slytherin, ravenclaw, hufflepuff, muggles
    difficulty = db.Column(db.String(20), nullable=False)  # easy, medium, hard
    house = db.Column(db.String(50), nullable=True)  # null means available to all houses
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'domain': self.domain,
            'difficulty': self.difficulty,
            'house': self.house,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AdminSettings(db.Model):
    __tablename__ = 'admin_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(500), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'key': self.key,
            'value': self.value
        }

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)  # Store hashed password
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TeamLogin(db.Model):
    __tablename__ = 'team_logins'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False, unique=True)
    username = db.Column(db.String(200), nullable=False, unique=True)  # team_name
    password = db.Column(db.String(200), nullable=False)  # UTR
    house = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    team = db.relationship('Team', backref='login_credentials', uselist=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'username': self.username,
            'house': self.house,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False, unique=True)  # One row per team
    review1_marks = db.Column(db.Integer, default=0, nullable=False)  # Total marks for review 1
    review2_marks = db.Column(db.Integer, default=0, nullable=False)  # Total marks for review 2
    review3_marks = db.Column(db.Integer, default=0, nullable=False)  # Total marks for review 3
    review1_data = db.Column(db.Text, nullable=True)  # JSON: {criteria: [...], feedback: "..."}
    review2_data = db.Column(db.Text, nullable=True)  # JSON: {criteria: [...], feedback: "..."}
    review3_data = db.Column(db.Text, nullable=True)  # JSON: {criteria: [...], feedback: "..."}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    team = db.relationship('Team', backref='review', uselist=False, lazy=True)
    
    def to_dict(self):
        """Convert to dictionary with all review data"""
        def parse_review_data(data_str, review_num):
            if not data_str:
                return {
                    'marks': getattr(self, f'review{review_num}_marks', 0),
                    'feedback': '',
                    'criteria': []
                }
            try:
                data = json.loads(data_str)
                data['marks'] = getattr(self, f'review{review_num}_marks', 0)
                return data
            except:
                return {
                    'marks': getattr(self, f'review{review_num}_marks', 0),
                    'feedback': '',
                    'criteria': []
                }
        
        return {
            'id': self.id,
            'team_id': self.team_id,
            'review1': parse_review_data(self.review1_data, 1),
            'review2': parse_review_data(self.review2_data, 2),
            'review3': parse_review_data(self.review3_data, 3),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_review(self, review_number):
        """Get specific review data (1, 2, or 3)"""
        if review_number not in [1, 2, 3]:
            return None
        
        marks = getattr(self, f'review{review_number}_marks', 0)
        data_str = getattr(self, f'review{review_number}_data', None)
        
        if not data_str:
            return {
                'marks': marks,
                'feedback': '',
                'criteria': []
            }
        
        try:
            data = json.loads(data_str)
            data['marks'] = marks
            return data
        except:
            return {
                'marks': marks,
                'feedback': '',
                'criteria': []
            }

