import streamlit as st
from groq import Groq
import os
import datetime

# Initialize the Groq API key
api_key = os.getenv("GROQ_API_KEY_2")
if not api_key:
    st.error("API key is missing. Please set the GROQ_API_KEY environment variable.")
    st.stop()

client = Groq(api_key=api_key)

# Few-shot example for better formatting
few_shot_examples = """
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
    placeholder="E.g.\n- Mention your work summary here\n- Mention the lines you require as the result\n- Also specify the tone if you want",
    height=150,
)

# Length Option Selection
length_option = st.radio("Select Summary Length:", ["Short", "Normal", "Long"], index=1)

# Updated length explanations with more precise instructions
length_explanations = {
    "Short": "Keep each point brief and focused on key actions only (15-20 words per point).",
    "Normal": "Include basic context and outcomes (20-25 words per point).",
    "Long": "Add moderate detail while maintaining clarity (35-40 words per point)."
}

# Generate work summary when the user clicks the button
if st.button("Generate Work Summary"):
    if not tasks.strip():
        st.warning("Please enter at least one task to generate a summary.")
    else:
        try:
            formatted_date = date.strftime('%d/%m/%Y')

            # Updated System Prompt with stricter length guidelines
            system_prompt = f"""
            You are a professional bot that generates structured work summaries. 
            Format the tasks professionally, following these strict length guidelines:

            - Short: Keep each bullet point between 15-20 words. Focus on core actions only.
            - Normal: Keep each bullet point between 20-25 words. Include basic context and outcomes.
            - Long: Keep each bullet point between 35-40 words. Add moderate detail while staying focused.
            
            DO NOT exceed the word limit for each length option.
            DO NOT include any notes or explanations. Only return the formatted summary.
            DO NOT copy from examples; only follow the structure.

            Format Example:
            {few_shot_examples}
            """

            # User Prompt
            user_prompt = f"""
            Generate a professional work summary using the following format:
            {few_shot_examples}

            Tasks provided by the user:
            {tasks}

            Name: {name}
            Date: {formatted_date}
            
            Content Length Preference: {length_option} ({length_explanations[length_option]})
            """

            # API Call with adjusted temperature for more consistent length
            completion = client.chat.completions.create(
                model="qwen-2.5-32b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,  # Reduced for more consistent output
                max_tokens=1024,
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