import streamlit as st
from groq import Groq
import os
import datetime
from helpers.input_classifier import classify_input_type
from helpers.summary_generator import generate_work_summary, validate_format
from helpers.format_examples import teams_format_example, jira_format_example

# Initialize Groq client
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    st.error("API key is missing. Please set the GROQ_API_KEY environment variable.")
    st.stop()

client = Groq(api_key=groq_api_key)

# Streamlit UI
st.title("UpdateBuddy AI")
st.markdown("***From Devansh Vora***, Here's a bouquet — :tulip::cherry_blossom::rose::hibiscus::sunflower::blossom:", unsafe_allow_html=True)
st.markdown(
    """This bot helps you generate daily work summaries based on the tasks you provide. 
       Simply enter a short description of your day, and it will format it for you! 📋"""
)

# Sidebar for agent inspection
with st.sidebar:
    st.header("Agent System")
    st.info("UpdateBuddy now uses a simplified, more accurate system to generate better summaries!")
    show_agent_logs = st.checkbox("Show Process Logs", value=False)
    
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
                    
                    task_type = classify_input_type(tasks, client)
                    
                    if show_agent_logs:
                        with log_container:
                            st.success(f"Input classified as: {task_type.upper()}")
                            if task_type == "jira":
                                st.write("Detected temporal structure (past/present/future tasks) or issue references")
                            else:
                                st.write("Detected simple task list without clear temporal structure")
                
                # Step 2: Generate Summary
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
                
                # Offer a downloadable version
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