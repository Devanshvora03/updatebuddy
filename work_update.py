from groq import Groq
import streamlit as st
import os

# Initialize Groq client
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("API key is missing. Please set the GROQ_API_KEY environment variable.")
client = Groq(api_key=api_key)

# Streamlit app title
st.title("Work Update Generator")
st.markdown("***From Devansh Vora***, Here's a bouquet &mdash;\
            :tulip::cherry_blossom::rose::hibiscus::sunflower::blossom:", unsafe_allow_html=True)

st.markdown("""This bot helps you generate daily work summaries based on the tasks you provide. 
               Simply enter a short description of your day, and it will format it for you! 📋""")

# User inputs for name, date, and prompt
user_name = st.text_input("Enter your name:", "Devansh Vora")
user_date = st.date_input("Enter the date:")
user_prompt = st.text_area("Enter your work update prompt:", height=150)

# Predefined system message with placeholders
system_message_template = {
    "role": "system",
    "content": (
        "You are a bot which generates daily-to-daily work updates. You will receive some data from the user, and from the requirements, you have to give the data arranged strictly in the given format. "
        "The Name will be always '{name}'. "
        "Example 1: "
        "Name: {name} "
        "Work Summary of {date}:\n"
        "_____________________________________________________ "
        "Today's Work: "
        "• Discovered that ViT is not capable of handling text + vision tasks effectively. "
        "• Used PixTral Large and Small models for the same task in the Hugging Face Playground. "
        "• Leveraged RunPod to create a serverless endpoint for PixTral. "
        "• Attempted to run the setup, but will continue troubleshooting and refining it tomorrow. "
        "• Calculated the required costing for Mistral via its own API and Sonnet 3 through AWS Bedrock. "
        "Example 2: "
        "Name: {name} "
        "Work Summary of {date}:\n"
        "_____________________________________________________ "
        "Today's Work: "
        "• Finalized the image similarity pipeline, ensuring integration and accurate functionality. "
        "• Merged all code into a single file to streamline the entire process. "
        "• The pipeline removes backgrounds using the RMBG-2.0 model, extracts text using the LLaMA 3.2 Vision model, and calculates both text and image similarity scores for a combined result. "
        "• The objective was successfully completed with promising accuracy. "
        "• Found not feasible to run locally due to computational complexity. "
        "• Encountered GPU and storage limitations in Colab, making it challenging to process large-scale datasets effectively."
    )
}

# Update the system message template with user input (name and date)
system_message = {
    "role": "system",
    "content": system_message_template["content"].format(
        name=user_name,
        date=user_date.strftime("%d/%m/%Y")
    )
}

# Only proceed if the user has entered the prompt
if user_prompt:
    # Prepare user message
    user_message = {"role": "user", "content": user_prompt}

    # Fetch completion from Groq API
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[system_message, user_message],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )

    # Collect the final response
    response = "".join(chunk.choices[0].delta.content or "" for chunk in completion)

    # Display the final response
    st.text_area("Generated Response:", response, height=300)
