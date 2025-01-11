import streamlit as st
from groq import Groq
import os
import datetime

# Initialize the Groq API key
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("API key is missing. Please set the GROQ_API_KEY environment variable.")
    st.stop()

client = Groq(api_key=api_key)

# Few-shot example for better formatting
few_shot_examples = """
Format
### **Name: {name}**

Work Summary of: {date} 

***Today's Work:***

- Task 1 Formatted professional summary
- Task 2 Formatted professional summary
- Task 3 Formatted professional summary

Example : 
### **Name: Devansh Vora**

Work Summary of: 09/01/2025  

***Today's Work:***

- Organized and planned an upcoming team meeting, reviewing the agenda and ensuring all necessary materials were ready for discussion.
- Coordinated with colleagues to finalize presentation slides and confirmed that all team members had their assigned tasks and responsibilities.
- Reviewed last week's meeting notes to track progress on action items and ensure timely completion of tasks.
- Conducted a thorough review of the project's progress, evaluating timelines and deliverables to identify potential areas for improvement.
- Provided guidance and assistance to a team member experiencing a technical issue, helping them to resolve the problem efficiently and effectively.
"""

# Streamlit UI
st.title("UpdateBuddy AI")
st.markdown("***From Devansh Vora***, Here's a bouquet &mdash; :tulip::cherry_blossom::rose::hibiscus::sunflower::blossom:", unsafe_allow_html=True)
st.markdown(
    """This bot helps you generate daily work summaries based on the tasks you provide. 
       Simply enter a short description of your day, and it will format it for you! 📋"""
)

# Input fields
name = st.text_input("Enter Your Name:", "Devansh Vora")
date = st.date_input("Select the Date:", datetime.date.today())
tasks = st.text_area(
    "Enter Today's Tasks (one task per line):",
    placeholder="E.g.\n- Prepared for a client meeting\n- Reviewed last week's progress",
    height=150,
)

# Generate work summary when the user clicks the button
if st.button("Generate Work Summary"):
    if not tasks.strip():
        st.warning("Please enter at least one task to generate a summary.")
    else:
        try:
            # Format the user's name and date
            formatted_date = date.strftime('%d/%m/%Y')
            
            # Generate the work summary using Groq
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional bot that generates summaries in a structured format.
                                      Format tasks or understand the paragraph and divide them into structured points.
                                      Generate the new points according to the user requirements. 
                                      DO NOT include any notes.
                                      DO NOT include the content from example, just follow the format.
                                      Generate points according to the requirements provided. A fixed number of points is NOT needed.
                                    """
                    },
                    {
                        "role": "user",
                        "content": f"""Generate a professional work summary using the following format:
                                       {few_shot_examples}

                                       Tasks provided by the user:
                                       {tasks}

                                       Name: {name}
                                       Date: {formatted_date}
                                       """
                    },
                ],
                temperature=0.7,
                max_tokens=512,
                top_p=0.9,
                stream=False,
            )
            
            # Extract and format the response
            response_content = completion.choices[0].message.content.strip()
            final_output = f"""{response_content}"""
            
            # Display the formatted output
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
