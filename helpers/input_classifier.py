import re
from groq import Groq

def has_temporal_structure(text):
    """
    Detects temporal structure in text with stricter criteria for Jira classification.
    Requires a stronger mix of past AND future references (more than one indicator),
    or explicit issue references with temporal context.
    A single 'will' or past tense verb alone won't trigger Jira.
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
    
    # Count occurrences of each type
    past_count = sum(1 for pattern in past_indicators if re.search(pattern, text_lower))
    future_count = sum(1 for pattern in future_indicators if re.search(pattern, text_lower))
    issue_count = sum(1 for pattern in issue_indicators if re.search(pattern, text_lower))
    
    # Stricter criteria for Jira:
    # - Must have MULTIPLE past AND at least one future reference (or vice versa)
    # - OR must have issue/ticket references with clear temporal context (past or future)
    has_strong_temporal_mix = (past_count > 1 and future_count > 0) or (past_count > 0 and future_count > 1)
    has_issues_with_temporal = issue_count > 0 and (past_count > 0 or future_count > 0)
    
    return has_strong_temporal_mix or has_issues_with_temporal

def classify_input_type(text, client: Groq):
    """
    Classifies input text as 'jira' or 'teams' with a more balanced approach.
    Jira requires a robust mix of past/future (multiple indicators) or issue references;
    otherwise, defaults to teams.
    """
    # Step 1: Check for clear temporal structure or issue references
    if has_temporal_structure(text):
        return 'jira'
    
    # Step 2: If pattern matching isn't conclusive, use LLM with stricter guidance
    system_prompt = """
    You are a classifier that categorizes task updates into one of two types:
    
    1. 'jira' - Updates with a robust temporal structure, requiring:
       - MULTIPLE past tense verbs (e.g., completed, fixed) AND at least one future reference (e.g., will, tomorrow)
       - OR multiple future references with at least one past tense verb
       - OR references to issues/tickets (e.g., 'ABC-123', 'bug') with temporal context
    2. 'teams' - Simple task lists without a strong past/future mix or issue references
    
    A single 'will' or a few past tense verbs alone does NOT make it 'jira'.
    Respond with ONLY a single word: either 'jira' or 'teams'
    """
    
    user_prompt = f"""
    Classify this input as either 'jira' or 'teams':

    {text}
    
    - 'jira' requires a strong mix: MULTIPLE past tense verbs (e.g., completed, fixed) AND at least one future reference (e.g., will, tomorrow),
      OR multiple future references with a past tense verb, OR issue references with temporal context.
    - 'teams' is a simple list without a robust past/future mix or issue mentions.
    
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
    
    # Default to 'teams' unless explicitly classified as 'jira' with strong evidence
    if response == 'jira':
        # Double-check for false positives
        double_check_prompt = f"""
        Analyze this text:
        
        {text}
        
        Does it have:
        1. MULTIPLE past tense verbs (e.g., completed, fixed) AND at least one future reference (e.g., will, tomorrow)?
        2. OR multiple future references with at least one past tense verb?
        3. OR issue/ticket references (e.g., ABC-123, bug) with temporal context?
        
        If YES to any, respond 'jira'. Otherwise, 'teams'.
        """
        
        second_check = client.chat.completions.create(
            model="deepseek-r1-distill-qwen-32b",
            messages=[{"role": "user", "content": double_check_prompt}],
            temperature=0.1,
            max_tokens=10
        )
        
        second_response = second_check.choices[0].message.content.strip().lower()
        return 'jira' if second_response == 'jira' else 'teams'
    
    return 'teams'