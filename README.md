# Hogwarts Hackathon - Backend

Flask backend for the Hogwarts Hackathon registration website.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. The necessary directories (`instance/` and `uploads/`) are already created with `.gitkeep` files.

3. Run the application:
```bash
python app.py
```

The server will start on `http://localhost:5000`

4. To connect the frontend to the backend, include the `api-integration.js` script in your HTML files:
   - For `register.html`: Add `<script src="api-integration.js"></script>` before the closing `</body>` tag
   - For `teams.html`: Add `<script src="api-integration.js"></script>` before the closing `</body>` tag

Note: The frontend HTML files remain unchanged. The integration script handles the API communication.

## API Endpoints

### Register Team
- **POST** `/api/register`
- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `team_name` (string, required)
  - `house` (string, required) - Options: gryffindor, slytherin, ravenclaw, hufflepuff, muggles
  - `team_size` (integer, required) - Between 1 and 4
  - `utr_transaction_id` (string, required)
  - `payment_proof` (file, optional) - Image file (png, jpg, jpeg, gif, pdf)
  - `member_1_name`, `member_1_email`, `member_1_phone` (required for member 1)
  - `member_2_name`, `member_2_email`, `member_2_phone` (required if team_size >= 2)
  - `member_3_name`, `member_3_email`, `member_3_phone` (required if team_size >= 3)
  - `member_4_name`, `member_4_email`, `member_4_phone` (required if team_size >= 4)

### Get Teams
- **GET** `/api/teams`
- **Query Parameters**:
  - `house` (optional) - Filter by house name
  - `search` (optional) - Search by team name
- **Response**: List of teams with summary information

### Get Team Details
- **GET** `/api/teams/<team_id>`
- **Response**: Full team details including all members

## Database

SQLite database is stored in `instance/hogwarts_hackathon.db`

### Tables

- **teams**: Stores team information
- **members**: Stores team member information

## File Structure

```
.
├── app.py                 # Main application entry point
├── app/
│   ├── __init__.py       # App factory
│   ├── config.py         # Configuration
│   ├── models.py         # Database models
│   └── routes.py         # API routes
├── instance/             # SQLite database location
├── uploads/             # Payment proof uploads
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Notes

- The frontend files (HTML, CSS, assets) remain unchanged
- Payment screenshots are stored in the `uploads/` directory
- Team names must be unique
- Email addresses must be unique across all members

