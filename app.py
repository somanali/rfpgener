from openai import OpenAI
from crewai import Agent, Task, Crew
import os

def clean_output(text):
    if not isinstance(text, str):
        return "⚠️ Error: Output is not valid text."

    # Remove markdown-like characters
    text = text.replace("*", "")
    text = text.replace("#", "")
    text = text.replace("`", "")

    # Remove multiple blank lines
    lines = text.split("\n")
    cleaned_lines = []
    skip = False

    for line in lines:
        if line.strip() == "":
            if not skip:
                cleaned_lines.append("")  # Keep one blank line
            skip = True
        else:
            cleaned_lines.append(line)
            skip = False

    return "\n".join(cleaned_lines).strip()

# Agent A: Cover, Intro, Objectives
agent_intro = Agent(
    role="RFP Initiation Specialist",
    goal="Write the Cover Page, Introduction, and Objectives clearly and formally.",
    backstory="You write the opening of all Saudi government RFPs with precision.",
    verbose=False
)

# Agent B: Scope & Deliverables
agent_scope = Agent(
    role="Scope Expert",
    goal="Create detailed scope, deliverables, and timelines.",
    backstory="You focus on defining exact technical and functional expectations.",
    verbose=False
)

# Agent C: Evaluation & Eligibility
agent_eval = Agent(
    role="Procurement Rules Analyst",
    goal="Define eligibility, proposal submission format, and scoring criteria.",
    backstory="You ensure only qualified vendors can apply and proposals are assessed fairly.",
    verbose=False
)

# Agent D: Legal + Budget
agent_legal = Agent(
    role="Legal & Financial Officer",
    goal="Draft budget guidelines, legal terms, IP clauses, and confidentiality.",
    backstory="You enforce regulatory compliance in public procurement.",
    verbose=False
)

# Supervisor
agent_supervisor = Agent(
    role="RFP Supervisor",
    goal="Compile and clean the final RFP into a single, formatted document.",
    backstory="You finalize RFPs for official publication.",
    verbose=False
)

reference_rfp = """ SAUDIA Group is currently undergoing a period of transformation in line with Saudi
Arabia’s strategy to realize the 2030 Vision.  Much work has been done over the past few
years spanning over hundreds of initiatives under the project management of SAUDIA’s
Transformation Office. Key areas of focus included massive cost reduction and digital
transformation, both of which were conducted with major global consulting firms.
Although we have seen substantial improvement in financial performance, SAUDIA has
not yet reached break-even. The mandate from the board for 2024 is for SAUDIA to
become profitable, and hence operational excellence is what needs to be established to
achieve profitability and to fund future growth
"""

def create_tasks_from_context(context_answers):
    # Task 1: Cover Page, Intro, Objectives
    task_intro = Task(
        description=f"""
Using the context below, generate:
- Cover Page
- Introduction & Background
- Objectives of the RFP

Guidelines:
- Use Saudi government tone
- No markdown formatting (no *, #, etc.)
- Use plain, numbered formatting (e.g., 1.0, 1.1)
- Do NOT invent content not in context
- Each section should be at least 300 words

Match the tone, structure, and level of detail as demonstrated in this reference RFP (do not copy its content, just follow its formality and depth):

Reference RFP Example:
{reference_rfp}

Context:
{context_answers}
""",
        agent=agent_intro,
        expected_output="Cover Page, Introduction, Objectives"
    )

    # Task 2: Scope, Deliverables, Timeline
    task_scope = Task(
        description=f"""
Write the following RFP sections:
- Scope of Work
- Deliverables
- Project Timeline

Use plain text and formal structure with section numbers.
Each part must be 300–500 words.

Context:
{context_answers}
""",
        agent=agent_scope,
        expected_output="Scope, Deliverables, Timeline"
    )

    # Task 3: Eligibility, Submission Format, Evaluation
    task_eval = Task(
        description=f"""
Write:
- Eligibility Criteria
- Proposal Submission Format
- Evaluation Criteria (with scoring breakdown)

Guidelines:
- Use bullet points or numbered lists
- Avoid generic filler
- Ground everything in the context

Context:
{context_answers}
""",
        agent=agent_eval,
        expected_output="Eligibility, Submission Format, Evaluation"
    )

    # Task 4: Budget, Legal, Confidentiality
    task_legal = Task(
        description=f"""
Generate:
- Budget/Cost Proposal Format
- Legal Terms & Conditions
- Confidentiality and IP Clauses

Use a formal tone, realistic legal language, and include examples where applicable.

Context:
{context_answers}
""",
        agent=agent_legal,
        expected_output="Budget, Legal, Confidentiality"
    )

    # Supervisor Task
    task_supervisor = Task(
        description="""
Combine the outputs from all four agents into one complete RFP document.

Guidelines:
- Use only the content from the agents
- Format using numbered section headers (no markdown)
- Remove repetition or irrelevant content
""",
        agent=agent_supervisor,
        expected_output="Final formatted RFP"
    )

    return [task_intro, task_scope, task_eval, task_legal, task_supervisor]

def generate_rfp(org, project, outcomes, specs, budget, deadline, additional):
    context = f"""
1. Organization: {org}
2. Project: {project}
3. Outcomes: {outcomes}
4. Technical Requirements: {specs}
5. Budget & Timeline: {budget}
6. Submission Deadline: {deadline}
7. Additional Info: {additional}
"""

    tasks = create_tasks_from_context(context)

    crew = Crew(
        agents=[agent_intro, agent_scope, agent_eval, agent_legal, agent_supervisor],
        tasks=tasks,
        verbose=False
    )

    result = crew.kickoff()
   # return (result)
    return clean_output(str(result))

import gradio as gr
from pathlib import Path


logo_path = "logo.png"

with gr.Blocks(theme=gr.themes.Base(), css="""
    #main-container {
        background-color: #121212;
        color: white;
        font-family: 'Segoe UI', sans-serif;
    }
    .gr-button {
        background-color: #007acc;
        color: white;
        border-radius: 10px;
        padding: 10px 16px;
        font-size: 16px;
    }
    .gr-button:hover {
        background-color: #005fa3;
    }
    .gr-textbox textarea {
        background-color: #1e1e1e !important;
        color: white !important;
        border-radius: 10px;
        font-size: 14px;
    }
""") as app:
    with gr.Column(elem_id="main-container"):
        with gr.Row():
            if Path(logo_path).exists():
                gr.Image(value=logo_path, show_label=False, show_download_button=False, height=80)
        gr.Markdown("## 📄 Request for proposal Generator ")

        with gr.Accordion("📝 Context Questions", open=True):
            org = gr.Textbox(label="1. What is the name of your organization and provide a brief overview?", lines=3)
            project = gr.Textbox(label="2. Provide the name of the project and a brief overview.", lines=3)
            outcomes = gr.Textbox(label="3. Are there specific outcomes or deliverables expected from the project?", lines=3)
            specs = gr.Textbox(label="4. Are there any technical specifications or specific certifications required from vendors?", lines=3)
            budget = gr.Textbox(label="5. What is the estimated budget and timeline of the project?", lines=3)
            deadline = gr.Textbox(label="6. What is the deadline for proposal submission?", lines=2)
            additional = gr.Textbox(label="7. Contact and Additional Info", lines=3)

        with gr.Group():
            btn = gr.Button("🚀 Generate Full RFP")
            output = gr.Textbox(label="📝 Final Generated RFP", lines=35)

            btn.click(
                fn=generate_rfp,
                inputs=[org, project, outcomes, specs, budget, deadline, additional],
                outputs=output
            )

app.launch()