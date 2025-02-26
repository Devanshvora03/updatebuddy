import streamlit as st
from groq import Groq
import os
import datetime
import json
import re

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    st.error("API key is missing. Please set the GROQ_API_KEY environment variable.")
    st.stop()

client = Groq(api_key=groq_api_key)

# Define the format examples
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

def has_temporal_structure(text):
    """
    Direct pattern matching to detect temporal structure in text.
    If it has both past and future references, we classify as Jira.
    """
    text_lower = text.lower()
    
    # Past tense indicators
    past_indicators = [
        r'\b(completed|finished|done|tested|checked|implemented|fixed|resolved|made|reviewed|created|built|added|updated|delivered)\b',
        r'\bhave (been|had|done|made|seen|gone|come|taken|worked|written|read|said|told|thought|known)\b',
        r'\bdid\b'
    ]
    
    # Future tense indicators
    future_indicators = [
        r'\bwill\b',
        r'\bgoing to\b',
        r'\bplan(ning)? to\b',
        r'\btomorrow\b',
        r'\bnext\b',
        r'\bscheduled\b',
        r'\bupcoming\b'
    ]
    
    # Issue/ticket references
    issue_indicators = [
        r'[A-Z]+-\d+',  # Matches patterns like ABC-123
        r'\bissue\b',
        r'\bticket\b',
        r'\bbug\b',
        r'\bchallenge\b',
        r'\bproblem\b'
    ]
    
    # Check for past tense verbs
    has_past = any(re.search(pattern, text_lower) for pattern in past_indicators)
    
    # Check for future references
    has_future = any(re.search(pattern, text_lower) for pattern in future_indicators)
    
    # Check for issue references
    has_issues = any(re.search(pattern, text_lower) for pattern in issue_indicators)
    
    # If it has both past and future elements, it's likely a Jira format
    # Also classify as Jira if it has issues/tickets mentioned
    if (has_past and has_future) or has_issues:
        return True
    
    return False

def classify_input_type(text):
    """
    Classifies input text as either 'jira' or 'teams' using a direct approach
    that combines pattern matching and LLM classification.
    """
    # First, try direct pattern matching
    if has_temporal_structure(text):
        return 'jira'
    
    # If no clear temporal structure, use a more thorough analysis
    system_prompt = """
    You are a classifier that categorizes task updates into one of two types:
    
    1. 'jira' - Updates that include AT LEAST ONE of these elements:
       - BOTH completed tasks (past tense) AND tasks planned for the future
       - References to specific issues or tickets (like ABC-123)
       - Clear indication of ongoing work AND future tasks
       
    2. 'teams' - Simple task lists without temporal structure (past/present/future)
    
    Respond with ONLY a single word: either 'jira' or 'teams'
    """
    
    user_prompt = f"""
    Classify this input as either 'jira' or 'teams':

    {text}
    
    If it contains BOTH past tense verbs (completed, tested, fixed, etc.) AND future references (will, plan to, tomorrow, etc.) OR mentions issues/tickets, it's 'jira'.
    Otherwise, it's 'teams'.
    
    Respond with ONLY a single word: either 'jira' or 'teams'
    """
    
    completion = client.chat.completions.create(
        model="deepseek-r1-distill-qwen-32b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        max_tokens=10
    )
    
    response = completion.choices[0].message.content.strip().lower()
    
    # Default to 'jira' if unclear to ensure temporal elements are captured
    if 'jira' in response:
        return 'jira'
    else:
        # Double-check with a different prompt if LLM says teams
        double_check_prompt = f"""
        Analyze this text for temporal structure:
        
        {text}
        
        Look specifically for:
        1. Past tense verbs (completed, tested, fixed, etc.)
        2. Future references (will, plan to, tomorrow, etc.)
        3. Issue/ticket references
        
        If it has ANY TWO of these elements, respond with 'jira'.
        Otherwise, respond with 'teams'.
        """
        
        second_check = client.chat.completions.create(
            model="deepseek-r1-distill-qwen-32b",
            messages=[{"role": "user", "content": double_check_prompt}],
            temperature=0.1,
            max_tokens=10
        )
        
        second_response = second_check.choices[0].message.content.strip().lower()
        if 'jira' in second_response:
            return 'jira'
        
        return 'teams'

def generate_work_summary(tasks, name, date, length_option, task_type, client):
    """Generate work summary based on detected type"""
    formatted_date = date.strftime('%d/%m/%Y')
    
    length_desc = {
        "Short": "Keep each point brief (15-20 words per point).",
        "Normal": "Include basic context (20-25 words per point).",
        "Long": "Add moderate detail (35-40 words per point)."
    }
    
    if task_type == "teams":
        system_prompt = f"""
        You are a professional work summary generator.
        You have to carefully detect the data according to following guidelines
        
        Follow these guidelines:
        - {length_desc[length_option]}
        - Be professional and concise
        - Focus on achievements and impact
        - Use active voice and strong verbs
        
        DO NOT include any explanations or notes.
        """
    else:  # jira
        system_prompt = f"""
        You are a professional work update generator.
        You have to carefully detect the data according to following guidelines
        Guidelines:
        - {length_desc[length_option]}
        - Identify and categorize completed tasks, ongoing work, future tasks only
        - Use past tense for completed tasks, present for ongoing, future tense for tomorrow
        - If a category has no tasks, include it but write "None" as the content
        - Explicity identify challenges or reported issue and display here only, if no found then write "None" as the content
        DO NOT include any explanations or notes.
        """
    
    user_prompt = f"""
    Generate a professional work summary using the following input:
    
    {tasks}
    
    Name: {name}
    Date: {formatted_date}
    """
    
    completion = client.chat.completions.create(
        model="deepseek-r1-distill-qwen-32b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.5,
        max_tokens=1024
    )
    
    return completion.choices[0].message.content.strip()

def validate_format(summary, task_type, client):
    """Validate and fix formatting issues"""
    system_prompt = """
    You validate and format work summaries. Fix any formatting issues but preserve content.
    Return ONLY the properly formatted summary without any explanations.
    """
    
    if task_type == "teams":
        format_instruction = """
        Ensure the summary follows this format:
        ***Name: [name]***
        
        Work Summary of: [date] 
        
        ***Today's Work:***
        
        - Task 1
        - Task 2
        - Task 3
        """
    else:  # jira
        format_instruction = """
        Ensure the summary follows this format:
        Work update: [date]
        
        1. Task Completed:
           * Task details
        
        2. Ongoing task:
           * Task details
        
        3. Task for Tomorrow:
           * Task details
        
        4. Challenges if any:
           * Details
        """
    
    user_prompt = f"""
    Validate and ensure proper formatting for this work summary:
    
    {summary}
    
    {format_instruction}
    
    Fix any formatting issues but preserve all content.
    Return ONLY the properly formatted summary.
    """
    
    completion = client.chat.completions.create(
        model="deepseek-r1-distill-qwen-32b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=1024
    )
    
    return completion.choices[0].message.content.strip()

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
    st.info("UpdateBuddy now uses a simplified, more accurate system to generate better summaries!")
    show_agent_logs = st.checkbox("Show Process Logs", value=False)
    
    # Add a format override option in sidebar
    st.subheader("Format Controls")
    override_format = st.checkbox("Override Automatic Format Detection", value=False)
    
    if override_format:
        forced_format = st.radio("Select Format:", ["teams", "jira"], 
                                format_func=lambda x: "Simple Task List (Teams)" if x == "teams" else "Structured Update (Jira)")
        st.info("Format detection will be bypassed and your selected format will be used.")

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

# Task input
tasks = st.text_area(
    "Enter Today's Tasks:",
    placeholder="Enter your work details. The system will detect whether to format as a simple task list or a structured update with completed/ongoing/future tasks.",
    height=150,
)

# Generate work summary when the user clicks the button
if st.button("Generate Work Summary"):
    if not tasks.strip():
        st.warning("Please enter at least one task to generate a summary.")
    else:
        try:
            with st.spinner("Generating your work summary..."):
                # Create log container
                log_container = st.container() if show_agent_logs else None
                
                # Step 1: Classify input type (unless overridden)
                if override_format and 'forced_format' in locals():
                    task_type = forced_format
                    if show_agent_logs:
                        with log_container:
                            st.subheader("Step 1: Format Selection")
                            st.warning(f"Automatic detection bypassed. Using forced format: {task_type.upper()}")
                else:
                    if show_agent_logs:
                        with log_container:
                            st.subheader("Step 1: Input Analysis")
                            st.write("Analyzing your input format...")
                    
                    task_type = classify_input_type(tasks)
                    
                    if show_agent_logs:
                        with log_container:
                            st.success(f"Input classified as: {task_type.upper()}")
                            if task_type == "jira":
                                st.write("Detected temporal structure (past/present/future tasks) or issue references")
                            else:
                                st.write("Detected simple task list without clear temporal structure")
                
                # Step 2: Generate Summary based on detected task type
                if show_agent_logs:
                    with log_container:
                        st.subheader(f"Step 2: Generating {task_type.capitalize()} Summary")
                
                raw_summary = generate_work_summary(tasks, name, date, length_option, task_type, client)
                
                if show_agent_logs:
                    with log_container:
                        st.markdown("**Raw Generated Summary:**")
                        st.markdown(raw_summary)
                        st.subheader("Step 3: Final Formatting")
                
                # Step 3: Validate and format
                final_output = validate_format(raw_summary, task_type, client)
                
                # Display the formatted output
                st.markdown("### Generated Summary")
                st.markdown(final_output, unsafe_allow_html=True)
                
                # Offer a downloadable version of the work summary
                formatted_date = date.strftime('%d-%m-%Y')
                st.download_button(
                    label="Download Summary",
                    data=final_output,
                    file_name=f"Work_Summary_{formatted_date}.txt",
                    mime="text/plain",
                )
                        
        except Exception as e:
            st.error(f"An error occurred while generating the summary: {e}")
            if show_agent_logs:
                st.error(f"Detailed error: {str(e)}")

# Add a footer
st.markdown("---")
st.markdown("Made with ❤️ by Devansh Vora | UpdateBuddy AI")