import streamlit as st
from groq import Groq

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Streamlit app title
st.title("Work Update Generator")
st.markdown("***From Devansh Vora***, Here's a bouquet &mdash;\
            :tulip::cherry_blossom::rose::hibiscus::sunflower::blossom:", unsafe_allow_html=True)
# Predefined system message with detailed instructions
system_message = {
    "role": "system",
    "content": (
        "You are a bot which generates daily-to-daily work updates. You will receive some data from the user, and from the requirements, you have to give the data arranged strictly in the given format. "
        "The Name will be always 'Devansh Vora'. "
        "Example 1: "
        "Name: Devansh Vora "
        "Work Summary of 06/01:"
        "_____________________________________________________ "
        "Today's Work: "
        "• Discovered that ViT is not capable of handling text + vision tasks effectively. "
        "• Used PixTral Large and Small models for the same task in the Hugging Face Playground. "
        "• Leveraged RunPod to create a serverless endpoint for PixTral. "
        "• Attempted to run the setup, but will continue troubleshooting and refining it tomorrow. "
        "• Calculated the required costing for Mistral via its own API and Sonnet 3 through AWS Bedrock. "
        "Example 2: "
        "Name: Devansh Vora "
        "Work Summary of 06/01:"
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

# User input prompt with larger, responsive text area
user_prompt = st.text_area("Enter your prompt:", height=150)

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
