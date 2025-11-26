from flask import Blueprint, request, jsonify, send_from_directory, current_app, make_response, session, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os
from pathlib import Path
from app.models import db, Team, Member, ProblemStatement, AdminSettings, Admin, TeamLogin, Review
from app.config import Config
from datetime import datetime
import io
try:
    from openpyxl import Workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Add CORS headers
@api_bp.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@api_bp.route('/register', methods=['POST'])
def register_team():
    try:
        # Get form data
        team_name = request.form.get('team_name', '').strip()
        house = request.form.get('house', '').strip()
        team_size = request.form.get('team_size', type=int)
        utr_transaction_id = request.form.get('utr_transaction_id', '').strip()
        
        # Validate required fields
        if not team_name:
            return jsonify({'error': 'Team name is required'}), 400
        
        # Normalize team name (trim and remove extra spaces)
        team_name = ' '.join(team_name.split())
        if not house:
            return jsonify({'error': 'House selection is required'}), 400
        if not team_size or team_size < 1 or team_size > 4:
            return jsonify({'error': 'Team size must be between 1 and 4'}), 400
        if not utr_transaction_id:
            return jsonify({'error': 'UTR/Transaction ID is required'}), 400
        
        # Check if team name already exists (case-insensitive)
        existing_team = Team.query.filter(
            db.func.lower(Team.team_name) == db.func.lower(team_name)
        ).first()
        if existing_team:
            return jsonify({'error': 'Team name already exists'}), 400
        
        # Handle file upload
        payment_proof_path = None
        if 'payment_proof' in request.files:
            file = request.files['payment_proof']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create unique filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = Path(Config.UPLOAD_FOLDER) / filename
                file.save(str(filepath))
                payment_proof_path = f"uploads/{filename}"
        
        # Create team with pending approval status
        team = Team(
            team_name=team_name,
            house=house.capitalize(),
            team_size=team_size,
            utr_transaction_id=utr_transaction_id,
            payment_proof_path=payment_proof_path,
            approval_status='pending'  # Explicitly set to pending
        )
        db.session.add(team)
        db.session.flush()  # Get team ID
        
        # Get member data from form
        members_data = []
        for i in range(1, team_size + 1):
            name = request.form.get(f'member_{i}_name', '').strip()
            email = request.form.get(f'member_{i}_email', '').strip()
            phone = request.form.get(f'member_{i}_phone', '').strip()
            
            if not name or not email or not phone:
                db.session.rollback()
                return jsonify({'error': f'All fields are required for member {i}'}), 400
            
            # Check for duplicate emails
            existing_member = Member.query.filter_by(email=email).first()
            if existing_member:
                db.session.rollback()
                return jsonify({'error': f'Email {email} is already registered'}), 400
            
            member = Member(
                team_id=team.id,
                name=name,
                email=email,
                phone=phone,
                is_leader=(i == 1),
                member_order=i
            )
            db.session.add(member)
            members_data.append(member)
        
        # Commit all changes to database - this ensures data is stored
        try:
            db.session.commit()
        except Exception as commit_error:
            db.session.rollback()
            return jsonify({'error': f'Failed to save data: {str(commit_error)}'}), 500
        
        # Verify data was saved by querying it back
        saved_team = Team.query.get(team.id)
        if not saved_team:
            return jsonify({'error': 'Registration failed - data not saved'}), 500
        
        # Only return success after confirming data is in database
        response_data = {
            'success': True,
            'message': 'Team registered successfully',
            'team_id': team.id,
            'team': team.to_dict()
        }
        response = jsonify(response_data)
        response.status_code = 201
        return response
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/teams', methods=['GET'])
def get_teams():
    try:
        house_filter = request.args.get('house', '').strip()
        search_term = request.args.get('search', '').strip()
        
        # Build query
        query = Team.query
        
        # Apply house filter
        if house_filter:
            query = query.filter(Team.house == house_filter)
        
        # Apply search filter
        if search_term:
            query = query.filter(Team.team_name.ilike(f'%{search_term}%'))
        
        teams = query.order_by(Team.registered_at.desc()).all()
        
        return jsonify({
            'success': True,
            'teams': [team.to_dict_summary() for team in teams]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/teams/<int:team_id>', methods=['GET'])
def get_team(team_id):
    try:
        team = Team.query.get_or_404(team_id)
        return jsonify({
            'success': True,
            'team': team.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/uploads/<filename>', methods=['GET'])
def uploaded_file(filename):
    try:
        upload_folder = str(Config.UPLOAD_FOLDER)
        return send_from_directory(upload_folder, filename)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

# ============ ADMIN ROUTES ============

@api_bp.route('/admin/pending-teams', methods=['GET'])
def get_pending_teams():
    """Get all teams with pending approval status"""
    try:
        teams = Team.query.filter_by(approval_status='pending').order_by(Team.registered_at.desc()).all()
        return jsonify({
            'success': True,
            'teams': [team.to_dict() for team in teams]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/approve-team/<int:team_id>', methods=['POST'])
def approve_team(team_id):
    """Approve a team - sets status to approved and creates login credentials"""
    try:
        team = Team.query.get_or_404(team_id)
        
        # Get team lead (first member or member with is_leader=True)
        team_lead = Member.query.filter_by(team_id=team_id, is_leader=True).first()
        if not team_lead:
            # Fallback to first member if no leader marked
            team_lead = Member.query.filter_by(team_id=team_id).order_by(Member.member_order).first()
        
        if not team_lead:
            return jsonify({'error': 'Team lead not found'}), 400
        
        # Check if login credentials already exist
        existing_login = TeamLogin.query.filter_by(team_id=team_id).first()
        
        if not existing_login:
            # Create login credentials for team lead
            # Username: team lead name, Password: UTR
            team_login = TeamLogin(
                team_id=team.id,
                username=team_lead.name,
                password=team.utr_transaction_id,
                house=team.house
            )
            db.session.add(team_login)
        
        # Update team approval status
        team.approval_status = 'approved'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Team {team.team_name} has been approved. Login credentials created.',
            'team': team.to_dict(),
            'login': {
                'username': team_lead.name,
                'password': team.utr_transaction_id,
                'house': team.house
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/reject-team/<int:team_id>', methods=['POST'])
def reject_team(team_id):
    """Reject a team - sets status to rejected"""
    try:
        team = Team.query.get_or_404(team_id)
        team.approval_status = 'rejected'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Team {team.team_name} has been rejected',
            'team': team.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/problem-statements', methods=['GET'])
def get_problem_statements():
    """Get all problem statements"""
    try:
        house_filter = request.args.get('house', '').strip()
        domain_filter = request.args.get('domain', '').strip()
        
        query = ProblemStatement.query
        
        if house_filter:
            # Show statements for the house OR statements available to all (house is null)
            query = query.filter(
                db.or_(
                    ProblemStatement.house == house_filter,
                    ProblemStatement.house.is_(None)
                )
            )
        
        if domain_filter:
            query = query.filter(ProblemStatement.domain == domain_filter)
        
        statements = query.order_by(ProblemStatement.created_at.desc()).all()
        
        # Count teams that selected each statement
        result = []
        for stmt in statements:
            count = Team.query.filter_by(selected_problem_statement_id=stmt.id).count()
            stmt_dict = stmt.to_dict()
            stmt_dict['selected_count'] = count
            result.append(stmt_dict)
        
        return jsonify({
            'success': True,
            'statements': result
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/problem-statements', methods=['POST'])
def add_problem_statement():
    """Add a new problem statement"""
    try:
        data = request.get_json()
        
        # Safely get and strip values, handling None cases
        title = str(data.get('title') or '').strip()
        description = str(data.get('description') or '').strip()
        domain = str(data.get('domain') or '').strip()
        difficulty = str(data.get('difficulty') or '').strip()
        house = str(data.get('house') or '').strip() if data.get('house') else None
        
        if not title or not description or not domain or not difficulty:
            return jsonify({'error': 'All fields are required'}), 400
        
        statement = ProblemStatement(
            title=title,
            description=description,
            domain=domain,
            difficulty=difficulty,
            house=house
        )
        db.session.add(statement)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Problem statement added successfully',
            'statement': statement.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/problem-statements/<int:stmt_id>', methods=['DELETE'])
def delete_problem_statement(stmt_id):
    """Delete a problem statement"""
    try:
        statement = ProblemStatement.query.get_or_404(stmt_id)
        db.session.delete(statement)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Problem statement deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/login-toggle', methods=['GET'])
def get_login_toggle():
    """Get current login toggle status"""
    try:
        setting = AdminSettings.query.filter_by(key='login_enabled').first()
        if not setting:
            # Default to disabled
            setting = AdminSettings(key='login_enabled', value='false')
            db.session.add(setting)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'enabled': setting.value.lower() == 'true'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/login-toggle', methods=['POST'])
def toggle_login():
    """Toggle login button visibility"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        setting = AdminSettings.query.filter_by(key='login_enabled').first()
        if not setting:
            setting = AdminSettings(key='login_enabled', value='false')
            db.session.add(setting)
        
        setting.value = 'true' if enabled else 'false'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'enabled': enabled,
            'message': f'Login button is now {"enabled" if enabled else "disabled"}'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/registration-toggle', methods=['GET'])
def get_registration_toggle():
    """Get current registration toggle status"""
    try:
        setting = AdminSettings.query.filter_by(key='registration_enabled').first()
        if not setting:
            # Default to disabled
            setting = AdminSettings(key='registration_enabled', value='false')
            db.session.add(setting)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'enabled': setting.value.lower() == 'true'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/registration-toggle', methods=['POST'])
def toggle_registration():
    """Toggle registration button visibility"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        setting = AdminSettings.query.filter_by(key='registration_enabled').first()
        if not setting:
            setting = AdminSettings(key='registration_enabled', value='false')
            db.session.add(setting)
        
        setting.value = 'true' if enabled else 'false'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'enabled': enabled,
            'message': f'Registration is now {"enabled" if enabled else "disabled"}'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============ LOGIN ROUTES ============

@api_bp.route('/login', methods=['POST'])
def login():
    """Team lead login - username is team_name, password is UTR
    Admin login - username is 'harry potter', password is 'hogwarts house cup'"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        is_admin = data.get('is_admin', False)
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Check for admin login
        if is_admin or username.lower() == 'harry potter':
            # Check admin credentials from database
            admin = Admin.query.filter_by(username=username.lower()).first()
            if admin and check_password_hash(admin.password_hash, password):
                return jsonify({
                    'success': True,
                    'message': 'Admin login successful',
                    'is_admin': True,
                    'admin': {
                        'username': admin.username,
                        'name': admin.username.title()
                    }
                }), 200
            else:
                return jsonify({'error': 'Invalid admin credentials'}), 401
        
        # Team lead login
        # First check if login credentials exist in TeamLogin table
        team_login = TeamLogin.query.filter(
            db.func.lower(TeamLogin.username) == db.func.lower(username)
        ).first()
        
        if not team_login:
            return jsonify({'error': 'Login credentials not found. Team may not be approved yet.'}), 401
        
        # Verify password (UTR) matches
        if team_login.password != password:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Get team details
        team = Team.query.get(team_login.team_id)
        if not team:
            return jsonify({'error': 'Team not found'}), 404
        
        # Double-check team is approved
        if team.approval_status != 'approved':
            return jsonify({'error': 'Team is not approved yet'}), 403
        
        # Return team info (without sensitive data)
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'is_admin': False,
            'team': {
                'id': team.id,
                'team_name': team.team_name,
                'house': team.house,
                'selected_problem_statement_id': team.selected_problem_statement_id
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ PROBLEM STATEMENT SELECTION ============

@api_bp.route('/admin/problem-statements/<int:stmt_id>/teams', methods=['GET'])
def get_teams_for_statement(stmt_id):
    """Get all teams that selected a specific problem statement"""
    try:
        statement = ProblemStatement.query.get_or_404(stmt_id)
        teams = Team.query.filter_by(selected_problem_statement_id=stmt_id).all()
        
        return jsonify({
            'success': True,
            'teams': [team.to_dict_summary() for team in teams]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/select-problem-statement', methods=['POST'])
def select_problem_statement():
    """Team selects/applies for a problem statement"""
    try:
        data = request.get_json()
        team_id = data.get('team_id')
        problem_statement_id = data.get('problem_statement_id')
        
        if not team_id or not problem_statement_id:
            return jsonify({'error': 'Team ID and Problem Statement ID are required'}), 400
        
        team = Team.query.get_or_404(team_id)
        
        # Check if team is approved
        if team.approval_status != 'approved':
            return jsonify({'error': 'Team is not approved yet'}), 403
        
        # Check if team has already selected a problem statement - prevent any resubmission
        if team.selected_problem_statement_id:
            # Check if trying to select the same statement
            if team.selected_problem_statement_id == problem_statement_id:
                return jsonify({'error': 'You have already applied for this problem statement. Resubmission is not allowed.'}), 400
            # Prevent selecting a different statement - no resubmissions allowed
            return jsonify({'error': 'You have already applied for a problem statement. Resubmission or changing your selection is not allowed.'}), 400
        
        problem_statement = ProblemStatement.query.get_or_404(problem_statement_id)
        
        # Update team's selected problem statement
        team.selected_problem_statement_id = problem_statement_id
        
        # If the problem statement is from a different house, update team's house
        if problem_statement.house and problem_statement.house != team.house:
            team.house = problem_statement.house
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Problem statement selected successfully',
            'team': team.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/teams', methods=['GET'])
def get_all_teams():
    """Get all approved teams for review marks dropdown"""
    try:
        teams = Team.query.filter_by(approval_status='approved').order_by(Team.team_name).all()
        return jsonify({
            'success': True,
            'teams': [{'id': team.id, 'team_name': team.team_name, 'house': team.house} for team in teams]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/review-marks', methods=['POST'])
def add_review_marks():
    """Add or update review marks for a team - stores all reviews in one row"""
    try:
        import json
        data = request.get_json()
        team_id = data.get('team_id')
        review_number = data.get('review_number')
        marks = data.get('marks')
        feedback = data.get('feedback', '').strip()
        criteria = data.get('criteria', [])  # List of criteria objects
        
        if not team_id or not review_number or marks is None:
            return jsonify({'error': 'Team ID, Review Number, and Marks are required'}), 400
        
        if review_number not in [1, 2, 3]:
            return jsonify({'error': 'Review number must be 1, 2, or 3'}), 400
        
        if marks < 0:
            return jsonify({'error': 'Marks must be non-negative'}), 400
        
        if not feedback:
            return jsonify({'error': 'Feedback is required'}), 400
        
        # Check if team exists and is approved
        team = Team.query.get_or_404(team_id)
        if team.approval_status != 'approved':
            return jsonify({'error': 'Team is not approved'}), 403
        
        # Get or create review row for this team (one row per team)
        review = Review.query.filter_by(team_id=team_id).first()
        
        # Prepare review data as JSON
        review_data = {
            'feedback': feedback,
            'criteria': criteria
        }
        review_data_json = json.dumps(review_data)
        
        if review:
            # Update existing review row
            setattr(review, f'review{review_number}_marks', marks)
            setattr(review, f'review{review_number}_data', review_data_json)
            review.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Review {review_number} updated successfully for team {team.team_name}',
                'review': review.get_review(review_number),
                'is_update': True
            }), 200
        else:
            # Create new review row for this team
            new_review = Review(
                team_id=team_id
            )
            setattr(new_review, f'review{review_number}_marks', marks)
            setattr(new_review, f'review{review_number}_data', review_data_json)
            db.session.add(new_review)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Review {review_number} added successfully for team {team.team_name}',
                'review': new_review.get_review(review_number),
                'is_update': False
            }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/review-marks/export', methods=['GET'])
def export_review_marks():
    """Export all review marks as Excel file with 3 sheets (Review 1, 2, 3)"""
    try:
        import json
        
        if not OPENPYXL_AVAILABLE:
            # Fallback to JSON if openpyxl not available
            reviews = Review.query.join(Team).filter(Team.approval_status == 'approved').order_by(Team.team_name).all()
            review_data = {1: [], 2: [], 3: []}
            
            for review in reviews:
                for review_num in [1, 2, 3]:
                    review_info = review.get_review(review_num)
                    if review_info and review_info.get('marks', 0) > 0:
                        review_data[review_num].append({
                            'team_id': review.team_id,
                            'team_name': review.team.team_name,
                            'house': review.team.house,
                            'review_number': review_num,
                            'total_marks': review_info.get('marks', 0),
                            'feedback': review_info.get('feedback', ''),
                            'criteria': review_info.get('criteria', [])
                        })
            
            return jsonify({
                'success': True,
                'data': review_data
            }), 200
        
        # Get all reviews with team information (one row per team now)
        reviews = Review.query.join(Team).filter(Team.approval_status == 'approved').order_by(Team.team_name).all()
        
        # Create Excel workbook
        wb = Workbook()
        wb.remove(wb.active)  # Remove default sheet
        
        # Process each review (1, 2, 3)
        for review_num in [1, 2, 3]:
            # Create sheet for this review
            ws = wb.create_sheet(title=f'Review {review_num}')
            
            # Collect all teams and their criteria for this review
            team_reviews = []
            all_criteria = set()
            
            for review in reviews:
                review_info = review.get_review(review_num)
                if review_info and review_info.get('marks', 0) > 0:
                    criteria_list = review_info.get('criteria', [])
                    # Collect unique criteria names
                    for crit in criteria_list:
                        if crit.get('name'):
                            all_criteria.add(crit.get('name'))
                    
                    team_reviews.append({
                        'team_name': review.team.team_name,
                        'total_marks': review_info.get('marks', 0),
                        'criteria': criteria_list
                    })
            
            criteria_list = sorted(list(all_criteria))
            
            # Create header row: Team Name, [Criteria columns], Total Marks
            header = ['Team Name'] + criteria_list + ['Total Marks']
            ws.append(header)
            
            # Bold header row
            from openpyxl.styles import Font
            for cell in ws[1]:
                cell.font = Font(bold=True)
            
            # Add data rows
            for team_review in team_reviews:
                row = [team_review['team_name']]
                
                # Add marks for each criterion
                for crit_name in criteria_list:
                    crit = next((c for c in team_review['criteria'] if c.get('name') == crit_name), None)
                    marks = crit.get('marks', 0) if crit else 0
                    row.append(marks)
                
                # Add total marks
                row.append(team_review['total_marks'])
                ws.append(row)
            
            # Auto-adjust column widths
            from openpyxl.utils import get_column_letter
            for col in range(1, len(header) + 1):
                column_letter = get_column_letter(col)
                max_length = 0
                for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=col, max_col=col):
                    cell_value = str(row[0].value) if row[0].value else ''
                    max_length = max(max_length, len(cell_value))
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to BytesIO
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Return Excel file
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='review_marks.xlsx'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/admin/download-db', methods=['GET'])
def download_database():
    """Download database file - admin only"""
    try:
        # Check admin authentication via session or request header
        # For simplicity, we'll check if admin is logged in via session
        # In production, use proper JWT or session management
        username = request.args.get('username', '').strip()
        password = request.args.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'error': 'Admin credentials required'}), 401
        
        # Verify admin credentials
        admin = Admin.query.filter_by(username=username.lower()).first()
        if not admin or not check_password_hash(admin.password_hash, password):
            return jsonify({'error': 'Invalid admin credentials'}), 401
        
        # Get database file path from config
        from app.config import Config
        db_path = str(Config.DATABASE_PATH)
        
        # Check if file exists
        if not os.path.exists(db_path):
            return jsonify({'error': 'Database file not found'}), 404
        
        # Send file
        return send_file(
            db_path,
            mimetype='application/x-sqlite3',
            as_attachment=True,
            download_name='hogwarts_hackathon.db'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get leaderboard data with all teams and their review marks"""
    try:
        import json
        # Get all approved teams
        teams = Team.query.filter_by(approval_status='approved').all()
        
        leaderboard_data = []
        for team in teams:
            # Get review row for this team (one row per team now)
            review = Review.query.filter_by(team_id=team.id).first()
            
            # Initialize review data
            review_1 = {'score': 0, 'comment': ''}
            review_2 = {'score': 0, 'comment': ''}
            review_3 = {'score': 0, 'comment': ''}
            
            # Populate review data from single row
            if review:
                # Get review 1 - always get data
                r1_data = review.get_review(1)
                if r1_data:
                    marks_1 = r1_data.get('marks', 0) or 0
                    review_1 = {
                        'score': int(marks_1),
                        'comment': str(r1_data.get('feedback', '') or '')
                    }
                
                # Get review 2
                r2_data = review.get_review(2)
                if r2_data:
                    marks_2 = r2_data.get('marks', 0) or 0
                    review_2 = {
                        'score': int(marks_2),
                        'comment': str(r2_data.get('feedback', '') or '')
                    }
                
                # Get review 3
                r3_data = review.get_review(3)
                if r3_data:
                    marks_3 = r3_data.get('marks', 0) or 0
                    review_3 = {
                        'score': int(marks_3),
                        'comment': str(r3_data.get('feedback', '') or '')
                    }
            
            total = review_1['score'] + review_2['score'] + review_3['score']
            
            leaderboard_data.append({
                'id': team.id,
                'name': team.team_name,
                'house': team.house,
                'r1': review_1,
                'r2': review_2,
                'r3': review_3,
                'total': total
            })
        
        # Sort by total points descending
        leaderboard_data.sort(key=lambda x: x['total'], reverse=True)
        
        return jsonify({
            'success': True,
            'teams': leaderboard_data
        }), 200
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

def register_blueprints(app):
    app.register_blueprint(api_bp)
    Config.init_app(app)

