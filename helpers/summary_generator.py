from groq import Groq

def generate_work_summary(tasks, name, date, length_option, task_type, client: Groq):
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

def validate_format(summary, task_type, client: Groq):
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