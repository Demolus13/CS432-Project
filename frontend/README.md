# FixIIT Frontend

This is the frontend application for the FixIIT maintenance request system.

## Features

- User authentication (login/registration)
- Dashboard for viewing maintenance requests
- Form for submitting new maintenance requests
- Profile management

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the Flask application:
   ```
   python app.py
   ```

3. Access the application at http://localhost:8000

## Structure

- `app.py`: Main Flask application
- `templates/`: HTML templates
- `static/`: Static files (CSS, JavaScript, images)
  - `css/`: CSS stylesheets
  - `js/`: JavaScript files
  - `img/`: Image files

## API Integration

This frontend connects to the FixIIT API for all data operations. The API base URL can be configured in the `app.py` file.

## Mock API Mode

The application includes a mock API mode for testing without a backend server. This is enabled by default and can be configured in the `app.py` file:

```python
class Config:
    # Set to True to use mock API responses instead of real API calls
    USE_MOCK_API = True
```

When mock API mode is enabled, the application will use in-memory data instead of making real API calls. This is useful for development and testing.

