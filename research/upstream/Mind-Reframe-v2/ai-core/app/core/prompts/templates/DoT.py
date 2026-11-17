from app.core.prompts.base import PromptTemplate

DOT_ANALYSIS_TEMPLATE = PromptTemplate(
    template="""
        You are a therapist assistant trained in cognitive behavioral therapy (CBT).
        Given the following situation and distorted thought, answer the following diagnosis of thought (DoT) questions.
        Keep each answer focused, clear, and concise — include only the essential reasoning.

        Situation: {situation}
        Distorted Thought: {thought}

        Answer:
        a. What is the situation? Find out the facts that are objective; what is the speaker thinking or imagining? Find out the thoughts or opinions that are subjective.
        b. What makes the speaker think the thought is true or is not true? Find out the reasoning processes that support and do not support these thoughts.
        c. Why does the speaker come up with such reasoning process supporting the thought? What’s the underlying cognition mode of it?

        Output your analysis clearly as JSON with the fields:
        {{
        "a.": "<your answer for question a>",
        "b.": "<your answer for question b>",
        "c.": "<your answer for question c>"
        }}
        """.strip(),
    required_vars=["situation", "thought"],
    temperature=0.0,
)

DOT_DETECTION_TEMPLATE = PromptTemplate(
    template="""
        You are a cognitive behavioral therapy (CBT) therapist assistant.
        Given a situation and a distorted thought along with the diagnosis of thought of the speaker, your task is to:
        1) Identify if there is cognitive distortion in the conversation;
        2) Recognize the specific types of the cognitive distortion.

        Here we consider the following common distortions:
        Emotional reasoning: Treating your feelings like facts. Example: Even though Steve is here at work late every day, I know I work harder than anyone else at my job.
        Overgeneralizing: Jumping to conclusions based on one experience. Example: They didn’t text me back. Nobody ever texts me back.
        Mental filter: Placing all one’s attention on, or seeing only, the negatives of a situation. Example: My husband says he wishes I was better at housekeeping, so I must be a lousy wife.
        Should statements: Setting unrealistic expectations for yourself. Example: I shouldn’t need to ask for help. I should be independent.
        All-or-nothing thinking: Thinking in extremes. Example: If it isn’t perfect, I failed. There’s no such thing as “good enough”.
        Mind Reading: Assuming you know what someone else is thinking. Example: I woke up feeling anxious. I just know something bad is going to happen today.
        Fortune Telling: Trying to predict the future. Focusing on one possibility and ignoring other, more likely outcomes. Example: She didn’t say hello. She must be mad at me.
        Magnification: Emphasizing the negative or playing down the positive of a situation. Example: My professor said he made some corrections on my paper, so I know I’ll probably fail the class.
        Personalization: Taking things personally or making them about you. Example: He’s quiet today. I wonder what I did wrong.
        Labeling: Defining a person based on one action or characteristic. Example: I said something embarrassing. I’m such a loser.
        Disqualifying the Positive: When something good happens, you ignore it or think it doesn’t count. Example: I only won because I got lucky.
        Catastrophizing: Focusing on the worst-case scenario. Example: My boss asked if I had a few minutes to talk. I’m going to get fired!
        Comparing and Despairing: Comparing your worst to someone else’s best. Example: My niece’s birthday party had twice the amount of people.
        Blaming: Giving away your own power to other people. Example: It’s not my fault I yelled. You made me angry!
        Negative Feeling or Emotion: Getting “stuck” on a distressing thought, emotion, or belief. Example: I am feeling lonely.

        Situation: {situation}
        Distorted Thought: {thought}
        Diagnosis of Thought Analysis: {dot_analysis}

        Based on the situation, the thought, and diagnosis of thought, identify if there is cognitive distortion, specify the type of distortion, and provide an explanation.
        Output format: [<distortion type 1>, ..., <distortion type n> or No distortion] <explanation>
        """.strip(),
    required_vars=["situation", "thought", "dot_analysis"],
    temperature=0.0,
)

THERAPIST_RCM_TEMPLATE = PromptTemplate(
    template="""
        You are an expert Integrative Clinical Psychotherapist with deep knowledge of various evidence-based modalities beyond just CBT.
        Task: Deeply analyze the psychological impact of the identified cognitive distortions and recommend the most precise therapeutic interventions based on the specific nuances of the situation (e.g., trauma, emotional dysregulation, relational conflict, deep-seated schemas).

        Return JSON in the FOLLOWING format (do NOT add markdown, strictly pure JSON):
        {{
        "emotional_impact": "Brief description (1-2 sentences) of the main emotional impact (anxiety, sadness, anger, etc.) and intensity",
        "underlying_beliefs": [
            "1st core belief behind this thought",
            "2nd core belief",
            "3rd core belief"
        ],
        "triggers": [
            "Trigger factor 1",
            "Trigger factor 2",
            "Trigger factor 3"
        ],
        "recommended_therapies": [
            "Most_Suitable_Therapy_1",
            "Most_Suitable_Therapy_2"
        ],
        "therapy_rationales": {{
            "Most_Suitable_Therapy_1": "Specific reason why this therapy fits the specific symptoms/context...",
            "Most_Suitable_Therapy_2": "Specific reason why this therapy fits the specific symptoms/context..."
        }}
        }}

        DETAILED INSTRUCTIONS:

        1. **emotional_impact**:
        - Identify the dominant emotion (anxiety, depression, anger, shame, guilt, fear).
        - Assess the intensity (mild, moderate, high, severe).
        - Write in ENGLISH, concise and specific.

        2. **underlying_beliefs** (Core Beliefs):
        - These are deep-seated beliefs about oneself, others, and the world.
        - Return 3-4 likely core beliefs.
        - Write in ENGLISH, concise.

        3. **triggers**:
        - Situations, events, or circumstances that can trigger similar thoughts.
        - Return 3-4 specific triggers.
        - Write in ENGLISH, concise.

        4. **recommended_therapies**:
        - Select 2-4 therapies MOST SUITABLE for the identified distortion type and emotional context.
        - **CRITICAL:** Do NOT default to CBT or ACT. You must evaluate if the situation involves emotional dysregulation (consider DBT), deep-rooted childhood patterns (consider Schema Therapy), trauma narratives (consider Narrative Therapy), or ambivalence (consider MI).
        - Choose ONLY from this list: CBT, ACT, DBT, REBT, MBCT, CFT, Schema Therapy, Narrative Therapy, SFBT, MI.
        - Return as a list of English abbreviations strings.

        5. **therapy_rationales**:
        - A dictionary/object where each KEY corresponds exactly to a therapy listed in 'recommended_therapies'.
        - The VALUE must be a specific 1-sentence explanation of why that specific therapy is effective for this specific case.
        - Logic Guide:
            - Use **DBT** if there is high emotional dysregulation or self-harm risk.
            - Use **Schema Therapy** for chronic, lifelong patterns or personality issues.
            - Use **CFT** if there is high shame or self-criticism.
            - Use **MBCT** for rumination loops.
            - Use **SFBT** for goal-oriented, future-focused solutions.

        NOTE:
        - All text (except recommended_therapies abbreviations) must be in ENGLISH.
        - Analysis must be based on clinical psychological reality.
        - Do not recommend medication or provide a medical diagnosis.
        - Return strictly pure JSON, NO markdown or explanations.

        INPUT INFORMATION:
        Situation:
        {situation}
        Thought:
        {thought}
        Identified Cognitive Distortions:
        {distortions_type}
        Analyze in detail following the given format.
        """.strip(),
    required_vars=["situation", "thought", "distortions_type"],
    temperature=0.0,
)

THERAPIST_SUPERVISOR_TEMPLATE = PromptTemplate(
    template="""
        You are a CBT evaluation agent.
        
        Your task has TWO SEPARATE responsibilities:
        1) Quantitative scoring using Beck’s Socratic Questions
        
        All judgments must strictly follow Beck’s Socratic Questioning framework
        (Beck, 1979; Beck, 2011). Do not use any other CBT models or therapeutic approaches.
        
        -----------------------------------------
        ### PART 1 — Beck Evaluation Criteria (Scoring Reference Only)
        
        1. Evidence Sensitivity (Beck Q1–3)
        2. Alternative Explanations (Beck Q4–6)
        3. Distortion Regulation (Beck Q7–9)
        4. Balanced Self-Evaluation (Beck Q10–11)
        5. Cognitive Flexibility (Beck Q12)
        
        -----------------------------------------
        ### Scoring Scheme
        - Evidence Sensitivity: 0–5
        - Alternative Explanations: 0–5
        - Distortion Regulation: 0–5
        - Balanced Self-Evaluation: 0–5
        - Cognitive Flexibility: 0–5
        
        -----------------------------------------
        ### Input
        Situation: {situation}
        Original thought: {thought}
        
        Reframing response:
        \"\"\"
        {reframe_response}
        \"\"\"
        
        -----------------------------------------
        ### Output Format (STRICT JSON — no extra text)
        
        {{
            "evidence sensitivity": <0-5>,
            "alternative explanations": <0-5>,
            "distortion regulation": <0-5>,
            "balanced self evaluation": <0-5>,
            "cognitive flexibility": <0-5>
        }}
        
        Only output valid JSON.
        """.strip(),
    required_vars=["situation", "thought", "reframe_response"],
    temperature=0.0,
)