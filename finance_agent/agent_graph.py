import os
from typing import TypedDict
from langgraph.graph import StateGraph, END
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from apscheduler.schedulers.blocking import BlockingScheduler
from database import get_all_invoices, save_audit_log
load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
set_llm_cache(SQLiteCache(database_path="langchain_cache.db"))
class EmailResponse(BaseModel):
    subject: str = Field(description="The subject line of the email")
    body: str = Field(description="The main content of the email, written in the requested tone")
class AgentState(TypedDict):
    invoice_id: str
    client_name: str
    amount: float
    due_date: str
    days_overdue: int
    assigned_tone: str
    email_draft: str
    final_action: str
def ingestion_node(state: AgentState):
    print(f"[Ingestion Node] Processing Invoice {state['invoice_id']}")
    due_date_obj = datetime.strptime(state["due_date"], '%Y-%m-%d')
    days_late = (datetime.now() - due_date_obj).days
    return {"days_overdue": days_late}

# Maps each tone to its specific CTA instruction
TONE_CTA = {
    "Warm":   f"Gently assume it was an oversight and include a payment link in the email body.",
    "Polite": f"Note that payment is still pending and ask them to confirm an expected payment date.",
    "Formal": f"Express escalating concern and demand a written response within 48 hours.",
    "Stern":  f"Give a firm final reminder stating that failure to pay will result in immediate legal escalation."
}

def generate_email_node(state: AgentState):
    print(f"--> [Generate Node] Writing a {state['assigned_tone']} email for {state['client_name']}...")
    structured_llm = llm.with_structured_output(EmailResponse)

    tone = state['assigned_tone']
    cta_instruction = TONE_CTA.get(tone, "")
    payment_link = f"\n    - Include payment link: pay.company.com/{state['invoice_id']}" if tone == "Warm" else ""

    prompt = f"""
    You are an accounts receivable agent for TravelCorp.
    Write a highly professional, well-formatted email to {state['client_name']} regarding their unpaid invoice.

    CRITICAL INSTRUCTION: You MUST use exact newline characters (\\n\\n) to separate paragraphs in the body. Do not squish the text together.

    Use EXACTLY this structure for the body of the email:

    Dear {state['client_name']},

    [Opening paragraph using the {tone} tone regarding Invoice {state['invoice_id']}]

    Please find the details of your outstanding invoice below:
    - Invoice Number: {state['invoice_id']}
    - Amount Due: ${state['amount']}
    - Original Due Date: {state['due_date']}
    - Days Overdue: {state['days_overdue']} days

    [Main body paragraph explaining the urgency based on the {tone} tone. {cta_instruction}{payment_link}]

    Sincerely,
    Accounts Receivable Department
    TravelCorp
    """

    result = structured_llm.invoke(prompt)
    email_text = f"Subject: {result.subject}\n\n{result.body}"
    return {"email_draft": email_text}

def escalate_legal_node(state: AgentState):
    print(f"[Escalate Node] Flagging {state['client_name']} for Legal!")
    save_audit_log(state['invoice_id'], tone_used="N/A", status="ESCALATED")
    return {"final_action": "ESCALATED"}

def mock_send_node(state: AgentState):
    print(f"[Action Node] Sending Mock Email to {state['client_name']}")
    print("\n" + "-"*60)
    print(f"[GENERATED EMAIL] To: {state['client_name']} | Invoice: {state['invoice_id']}")
    print("-"*60)
    print(state['email_draft'])
    print("-"*60 + "\n")
    save_audit_log(state['invoice_id'], tone_used=state['assigned_tone'], status="SENT",email_content=state['email_draft'])
    return {"final_action": "SENT"}
def choose_path(state: AgentState):
    days = state.get("days_overdue", 0)
    
    if days > 30:
        return "escalate" 
    else:
        return "generate" 

def assign_tone(state: AgentState):
    days = state.get("days_overdue", 0)
    if 1 <= days <= 7: return {"assigned_tone": "Warm"}
    elif 8 <= days <= 14: return {"assigned_tone": "Polite"}
    elif 15 <= days <= 21: return {"assigned_tone": "Formal"}
    else: return {"assigned_tone": "Stern"}
workflow = StateGraph(AgentState)
workflow.add_node("ingest", ingestion_node)
workflow.add_node("assign_tone", assign_tone)
workflow.add_node("generate_email", generate_email_node)
workflow.add_node("escalate", escalate_legal_node)
workflow.add_node("send", mock_send_node)
workflow.set_entry_point("ingest")
workflow.add_conditional_edges(
    "ingest",
    choose_path,
    {
        "escalate": "escalate",  
        "generate": "assign_tone"
    }
)
workflow.add_edge("assign_tone", "generate_email")
workflow.add_edge("generate_email", "send")
workflow.add_edge("send", END)
workflow.add_edge("escalate", END)
app = workflow.compile()

def run_automated_agent():
    invoices = get_all_invoices()
    
    for inv in invoices:
        initial_state = {
            "invoice_id": inv.invoice_id,
            "client_name": inv.client_name,
            "amount": inv.amount,
            "due_date": inv.due_date,
            "days_overdue": 0, 
            "assigned_tone": "",
            "email_draft": "",
            "final_action": ""
        }
        app.invoke(initial_state)

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    # For testing, we run it every 10 seconds. 
    scheduler.add_job(run_automated_agent, 'interval', seconds=10)
    scheduler.start()

