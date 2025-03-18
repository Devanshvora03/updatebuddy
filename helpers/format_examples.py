teams_format_example = """
Format
***Name: {name}***

Work Summary of: {date} 

***Today's Work:***

- Task 1 Formatted professional summary
- Task 2 Formatted professional summary
- Task 3 Formatted professional summary

Example : 
***Name: Devansh Vora***

Work Summary of: 09/01/2025  

***Today's Work:***

- Improved database performance by optimizing queries for better efficiency.
- Resolved UI alignment issues in the dashboard to enhance user experience.
- Collaborated with the backend team to resolve API response delays.
- Reviewed and documented latest feature updates for reference.
"""

jira_format_example = """
Work update: DD/MM/YYYY

1. Task Completed:
   * Task details with description

2. Ongoing task:
   * Task details with description

3. Task for Tomorrow:
   * Task details with description

4. Challenges if any:
   * Concern with description

Example:
Work update: 21/02/2025

1. Task Completed:
   * Bug Fixing in API Response Handling: Corrected status codes for invalid inputs to ensure proper error handling.

2. Ongoing Task:
   * Integrating OAuth2 Authentication: Working on securing the dashboard login and API endpoints.

3. Task for Tomorrow:
   * Unit Testing for User Authentication: Writing test cases to validate authentication and session management.

4. Challenges if any:
   * Database Connection Timeout: Facing intermittent connection issues, possibly due to SQLAlchemy session management.
"""