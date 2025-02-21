import streamlit as st
from groq import Groq
from phi.agent import Agent
from phi.model.groq import Groq as PhiGroq
import os
import datetime
import json
import re

# Initialize API keys
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    st.error("API key is missing. Please set the GROQ_API_KEY environment variable.")
    st.stop()

# Initialize Groq client for direct API calls
direct_client = Groq(api_key=groq_api_key)

# Define format examples
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

def contains_jira_pattern(text):
    """Enhanced function to detect Jira patterns with stricter requirements"""
    # Explicit format checks
    explicit_patterns = [
        r"task completed:",
        r"ongoing task:",
        r"task for tomorrow:",
        r"challenges? if any:",
        r"work update:"
    ]
    
    # Natural language pattern checks - Made more specific
    natural_patterns = {
        'completed': r"(today,? i|i have|have just|just|recently) (completed|finished|delivered|closed|done)",
        'ongoing': r"(currently|right now|in progress|actively) (working on|developing|implementing|handling)",
        'future': r"(tomorrow|next|planning to|will|going to) (implement|develop|work on|start|begin)",
        'challenges': r"(facing|encountered|dealing with|struggling with) (challenges?|issues?|problems?|difficulties)"
    }
    
    text_lower = text.lower()
    
    # Check for explicit format
    explicit_matches = sum(1 for pattern in explicit_patterns if re.search(pattern, text_lower))
    if explicit_matches >= 2:  # If at least 2 explicit patterns are found
        return True
        
    # Check for natural language format - Require more specific matches
    natural_matches = sum(1 for pattern_type, pattern in natural_patterns.items() 
                         if re.search(pattern, text_lower))
    
    # Must match at least 3 categories (completed, ongoing/future, challenges)
    # AND must follow the temporal pattern (past, present, future)
    if natural_matches >= 3 and any(re.search(natural_patterns['completed'], text_lower)) and \
       (any(re.search(natural_patterns['ongoing'], text_lower)) or 
        any(re.search(natural_patterns['future'], text_lower))):
        return True
    
    return False

def initialize_agents():
    """Initialize all agents with their proper instructions"""
    
    # Task Recognizer Agent
    tasks_agent = Agent(
        name="Task Recognizer",
        role="Understand the user's requirements and identify task format",
        model=PhiGroq(id="qwen-2.5-32b", api_key=groq_api_key),
        instructions=[
            "You analyze input to determine if it follows the Jira update structure in either format:",
            "1. Explicit Format:",
            "   - Contains section headers like 'Task Completed:', 'Ongoing task:', etc.",
            "   - Starts with 'Work update:'",
            "2. Natural Language Format:",
            "   - Contains mentions of completed/finished/done tasks (past tense)",
            "   - Contains current/ongoing work (present tense)",
            "   - Contains tomorrow's/future plans",
            "   - Contains challenges/issues/concerns",
            "If the input matches atleast 3 format pattern from natural language format, then only classify as 'jira'.",
            "Otherwise, classify as 'teams'.",
            "Return ONLY a JSON response with format: {'type': 'teams'|'jira', 'content': <original_content>}",
            "Do not include any explanations, just the JSON output."
        ],
        markdown=True,
    )
    
    # Teams Agent
    teams_agent = Agent(
        name="Teams Update Summarizer",
        role="Generate professional work summaries from task descriptions",
        model=PhiGroq(id="qwen-2.5-32b", api_key=groq_api_key),
        instructions=[
            f"You are a professional bot that generates structured work summaries for regular tasks.",
            f"You receive tasks in plain text and format them according to these length guidelines:",
            f"- Short: Keep each bullet point between 15-20 words. Focus on core actions only.",
            f"- Normal: Keep each bullet point between 20-25 words. Include basic context and outcomes.",
            f"- Long: Keep each bullet point between 35-40 words. Add moderate detail while staying focused.",
            f"Format Example: {teams_format_example}",
            f"DO NOT exceed the word limit for each length option.",
            f"DO NOT include any notes or explanations. Only return the formatted summary.",
            f"DO NOT copy from examples; only follow the structure."
        ],
        markdown=True,
    )
    
    # Jira Agent
    jira_agent = Agent(
        name="Jira Update Summarizer",
        role="Generate professional work summaries in Jira format",
        model=PhiGroq(id="qwen-2.5-32b", api_key=groq_api_key),
        instructions=[
            f"You are a professional bot that generates structured work summaries in Jira format.",
            f"You receive input in either structured or natural language format.",
            f"Convert any natural language input into this exact structure:",
            f"Work update: [date]",
            f"1. Task Completed:",
            f"   * Extract and format completed tasks from the input",
            f"2. Ongoing task:",
            f"   * Extract and format current/ongoing work",
            f"3. Task for Tomorrow:",
            f"   * Extract and format planned future tasks",
            f"4. Challenges if any:",
            f"   * Extract and format mentioned challenges/issues",
            f"For natural language input:",
            f"- Look for past tense verbs for completed tasks",
            f"- Look for present continuous tense for ongoing tasks",
            f"- Look for future tense or tomorrow mentions for upcoming tasks",
            f"- Look for challenge/issue/problem mentions for challenges",
            f"Follow these length guidelines:",
            f"- Short: 15-20 words per description",
            f"- Normal: 20-25 words per description",
            f"- Long: 35-40 words per description",
            f"Format Example: {jira_format_example}",
            f"DO NOT deviate from this format.",
            f"DO NOT include any notes or explanations."
        ],
        markdown=True,
    )
    
    # Formatter Agent
    formatter_agent = Agent(
        name="Update Formatter and Response Validator",
        role="Format and validate work summaries",
        model=PhiGroq(id="qwen-2.5-32b", api_key=groq_api_key),
        instructions=[
            "You validate and format work summaries based on their type (teams or jira).",
            "For teams format, use:",
            "***Name: [name]***",
            "Work Summary of: [date]",
            "***Today's Work:***",
            "- Task bullets...",
            "For Jira format, use:",
            "Work update: [date]",
            "1. Task Completed:",
            "   * Task details",
            "2. Ongoing task:",
            "   * Task details",
            "3. Task for Tomorrow:",
            "   * Task details",
            "4. Challenges if any:",
            "   * Details",
            "Fix any formatting issues but preserve content.",
            "Return ONLY the properly formatted summary."
        ],
        markdown=True,
    )
    
    return tasks_agent, teams_agent, jira_agent, formatter_agent

# Streamlit UI
st.title("UpdateBuddy AI")
st.markdown("***From Devansh Vora***, Here's a bouquet &mdash; :tulip::cherry_blossom::rose::hibiscus::sunflower::blossom:", unsafe_allow_html=True)
st.markdown(
    """This bot helps you generate daily work summaries based on the tasks you provide. 
       Simply enter a short description of your day, and it will format it for you! 📋"""
)

# Sidebar for agent inspection
with st.sidebar:
    st.header("Agent System")
    st.info("UpdateBuddy now uses a multi-agent system to generate better summaries!")
    show_agent_logs = st.checkbox("Show Agent Logs", value=True)
    
    if show_agent_logs:
        st.subheader("Agent System:")
        st.markdown("""
        1. **Task Recognizer**: Analyzes your input format (Jira or Teams style)
        2. **Teams Summarizer**: Handles regular task lists
        3. **Jira Summarizer**: Processes structured/natural language Jira updates
        4. **Formatter**: Ensures proper formatting and validates output
        """)

# Input fields
name = st.text_input("Enter Your Name:", "Devansh Vora")
date = st.date_input("Select the Date:", datetime.date.today())

# Length Option Selection
length_option = st.selectbox("Select Summary Length:", ["Short", "Normal", "Long"], index=1)

length_explanations = {
    "Short": "Keep each point brief and focused on key actions only (15-20 words per point).",
    "Normal": "Include basic context and outcomes (20-25 words per point).",
    "Long": "Add moderate detail while maintaining clarity (35-40 words per point)."
}

task_placeholder="E.g.\n- Mention your work summary here\n- Mention the lines you require as the result\n- Also specify the tone if you want",

# # Updated placeholder showing both formats
# task_placeholder = """Example 1 (Natural language):
# Today, I completed the client presentation. Currently working on project proposals. Planning to start development tomorrow. Facing some delays with client feedback.

# Example 2 (Structured):
# 1. Task Completed:
#    * Finished client presentation
# 2. Ongoing task:
#    * Working on proposals
# 3. Task for Tomorrow:
#    * Start development
# 4. Challenges if any:
#    * Client feedback delays"""

tasks = st.text_area(
    "Enter Today's Tasks:",
    placeholder="E.g.\n- Mention your work summary here\n- Mention the lines you require as the result\n- Also specify the tone if you want",
    # placeholder=task_placeholder,
    height=150,
)

# Generate work summary when the user clicks the button
if st.button("Generate Work Summary"):
    if not tasks.strip():
        st.warning("Please enter at least one task to generate a summary.")
    else:
        try:
            with st.spinner("Agents are working on your summary..."):
                # Initialize agents
                tasks_agent, teams_agent, jira_agent, formatter_agent = initialize_agents()
                
                formatted_date = date.strftime('%d/%m/%Y')
                
                # Create log container
                log_container = st.container() if show_agent_logs else None
                
                # Step 1: Task Recognition
                if show_agent_logs:
                    with log_container:
                        st.subheader("Step 1: Task Analysis")
                        st.write("Analyzing your input...")
                
                task_recognition_prompt = """
                Analyze the following input to determine if it follows a Jira update structure:

                {input_text}

                A Jira update MUST include at least 3 of these 4 components:
                1. Completed/past tasks with clear completion indicators
                2. Current/ongoing work with explicit "in progress" indicators
                3. Future/planned tasks with clear tomorrow/next indicators
                4. Specific challenges or issues being faced

                Regular task lists that only contain completed items should be classified as 'teams'.

                Example of Jira format:
                "Today I completed the database migration. Currently working on API integration. Tomorrow, will implement user authentication. Facing issues with server deployment."

                Example of Teams format (regular task list):
                "Updated the database schema. Fixed UI alignment issues. Implemented new feature. Conducted code review."

                Return ONLY a JSON with format: {{"type": "teams"|"jira", "content": "<original content>"}}
                """
                
                # Update the system prompt for task recognition API call
                task_recognition_system_prompt = """You are a task classifier that strictly distinguishes between Jira updates and regular task lists.

                Jira updates MUST have:
                - Clear temporal structure (past, present, future)
                - Explicit ongoing or planned work
                - Preferably mentions of challenges/issues

                Regular task lists (teams) are:
                - Lists of completed tasks
                - Tasks without clear temporal structure
                - Tasks without explicit ongoing/future work

                Be strict in classification - if in doubt, classify as 'teams'."""

                # Modify the task recognition API call section:
                detection_completion = direct_client.chat.completions.create(
                    model="qwen-2.5-32b",
                    messages=[
                        {"role": "system", "content": task_recognition_system_prompt},
                        {"role": "user", "content": task_recognition_prompt.format(input_text=tasks)}
                    ],
                    temperature=0.2,
                    max_tokens=256
                )
                task_recognition_result = detection_completion.choices[0].message.content.strip()
                
                # Add an additional validation check after getting the API response
                def validate_task_type(text, initial_classification):
                    """Double-check the task classification with strict rules"""
                    has_temporal_structure = contains_jira_pattern(text)  # Use our updated pattern matcher
                    
                    # If it's just a list of completed tasks without temporal structure, force it to 'teams'
                    if not has_temporal_structure and initial_classification['type'] == 'jira':
                        return {"type": "teams", "content": text}
                    
                    return initial_classification

                try:
                    json_match = re.search(r'{.*}', task_recognition_result, re.DOTALL)
                    if json_match:
                        task_analysis = json.loads(json_match.group(0))
                    else:
                        # Use pattern matching function
                        is_jira_pattern = contains_jira_pattern(tasks)
                        task_analysis = {
                            "type": "jira" if is_jira_pattern else "teams",
                            "content": tasks
                        }
                except Exception as json_error:
                    # Fallback to pattern matching
                    is_jira_pattern = contains_jira_pattern(tasks)
                    task_analysis = {
                        "type": "jira" if is_jira_pattern else "teams",
                        "content": tasks
                    }
                
                if show_agent_logs:
                    with log_container:
                        st.write(f"Task type detected: {task_analysis['type']}")
                        st.json(task_analysis)
                
                # Step 2: Generate Summary based on detected task type
                if show_agent_logs:
                    with log_container:
                        st.subheader(f"Step 2: Generating {task_analysis['type'].capitalize()} Summary")
                
                if task_analysis["type"] == "teams":
                    system_prompt = """You are a professional bot that generates structured work summaries for regular tasks.
                    Format the tasks professionally, following the length guidelines provided.
                    DO NOT exceed the word limit for each length option.
                    DO NOT include any notes or explanations. Only return the formatted summary.
                    DO NOT copy from examples; only follow the structure."""
                else:  # jira
                    system_prompt = """You are a professional bot that generates structured work summaries in Jira format.
                    Convert input into this exact structure:
                    Work update: [date]
                    1. Task Completed:
                       * Details
                    2. Ongoing task:
                       * Details
                    3. Task for Tomorrow:
                       * Details
                    4. Challenges if any:
                       * Details
                    Extract and categorize tasks from natural language if needed.
                    DO NOT deviate from this format.
                    DO NOT include any notes or explanations."""
                
                user_prompt = f"""
                Generate a professional work summary using the following input:
                {tasks}
                
                Name: {name}
                Date: {formatted_date}
                
                Content Length Preference: {length_option} ({length_explanations[length_option]})
                """
                
                summary_completion = direct_client.chat.completions.create(
                    model="qwen-2.5-32b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.5,
                    max_tokens=1024
                )
                raw_summary = summary_completion.choices[0].message.content.strip()
                
                if show_agent_logs:
                    with log_container:
                        st.markdown(raw_summary)
                        st.subheader("Step 3: Formatting and Validation")
                
                # Step 3: Format and Validate
                validation_system_prompt = """You validate and format work summaries based on their type.
                For teams format:
                ***Name: [name]***
                Work Summary of: [date]
                ***Today's Work:***
                - Task bullets...

                For Jira format:
                Work update: [date]
                1. Task Completed:
                   * Task details
                2. Ongoing task:
                   * Task details
                3. Task for Tomorrow:
                   * Task details
                4. Challenges if any:
                   * Details

                Fix any formatting issues but preserve content.
                Return ONLY the properly formatted summary."""
                
                validation_user_prompt = f"""
                Validate and ensure proper formatting for this work summary:
                
                {raw_summary}

                Type: {task_analysis['type']}
                
                Fix any formatting issues but preserve content.
                Return ONLY the properly formatted summary.
                """
                
                formatting_completion = direct_client.chat.completions.create(
                    model="qwen-2.5-32b",
                    messages=[
                        {"role": "system", "content": validation_system_prompt},
                        {"role": "user", "content": validation_user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1024
                )
                final_output = formatting_completion.choices[0].message.content.strip()
                
                # Display the formatted output
                st.markdown("### Generated Summary")
                st.markdown(final_output, unsafe_allow_html=True)
                
                # Offer a downloadable version of the work summary
                st.download_button(
                    label="Download Summary",
                    data=final_output,
                    file_name=f"Work_Summary_{formatted_date.replace('/', '-')}.txt",
                    mime="text/plain",
                )
                        
        except Exception as e:
            st.error(f"An error occurred while generating the summary: {e}")
            if show_agent_logs:
                st.error(f"Detailed error: {str(e)}")

# Add a footer
st.markdown("---")
st.markdown("Made with ❤️ by Devansh Vora | UpdateBuddy AI")