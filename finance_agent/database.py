from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta
finance_engine = create_engine('sqlite:///finance.db')
FinanceSession = sessionmaker(bind=finance_engine)
FinanceBase = declarative_base()
class PendingInvoice(FinanceBase):
    __tablename__ = 'pending_invoices'

    invoice_id    = Column(String, primary_key=True)
    client_name   = Column(String)
    amount        = Column(Float)
    due_date      = Column(String)
    contact_email = Column(String)
    follow_up_count = Column(Integer, default=0)
audit_engine = create_engine('sqlite:///audit.db')
AuditSession = sessionmaker(bind=audit_engine)
AuditBase = declarative_base()

class AuditLog(AuditBase):
    __tablename__ = 'audit_log'
    log_id     = Column(Integer, primary_key=True, autoincrement=True)
    timestamp  = Column(String)
    invoice_id = Column(String)
    tone_used  = Column(String)
    status     = Column(String)
    email_content = Column(String)

def create_databases():
    """
    Sets up both databases.
    - finance.db: always reset (mock invoice data)
    - audit.db:   NEVER reset — logs accumulate over time
    """
    FinanceBase.metadata.drop_all(finance_engine)   # wipe & recreate invoices (mock data)
    FinanceBase.metadata.create_all(finance_engine)
    AuditBase.metadata.create_all(audit_engine)     # only create if not exists, never drop
    print("finance.db reset. audit.db preserved.")

def insert_mock_data():
    """Inserts 5 test invoices into finance.db."""
    session = FinanceSession()
    today = datetime.now()
    invoices = [
        PendingInvoice(invoice_id="INV-001", client_name="Acme Corp",     amount=1500.0,  due_date=(today - timedelta(days=5)).strftime('%Y-%m-%d'),  contact_email="acme@test.com"),
        PendingInvoice(invoice_id="INV-002", client_name="Globex Inc",    amount=3200.0,  due_date=(today - timedelta(days=12)).strftime('%Y-%m-%d'), contact_email="globex@test.com"),
        PendingInvoice(invoice_id="INV-003", client_name="Soylent Corp",  amount=850.0,   due_date=(today - timedelta(days=18)).strftime('%Y-%m-%d'), contact_email="soylent@test.com"),
        PendingInvoice(invoice_id="INV-004", client_name="Initech",       amount=4500.0,  due_date=(today - timedelta(days=25)).strftime('%Y-%m-%d'), contact_email="initech@test.com"),
        PendingInvoice(invoice_id="INV-005", client_name="Umbrella Corp", amount=10000.0, due_date=(today - timedelta(days=35)).strftime('%Y-%m-%d'), contact_email="umbrella@test.com"),
    ]
    session.add_all(invoices)
    session.commit()
    session.close()
    print("Mock invoices inserted into finance.db.")

def get_all_invoices():
    """Fetches all invoices from finance.db."""
    session = FinanceSession()
    all_invoices = session.query(PendingInvoice).all()
    session.close()
    return all_invoices

def get_all_logs():
    """Fetches all audit records from audit.db."""
    session = AuditSession()
    all_logs = session.query(AuditLog).order_by(AuditLog.log_id.desc()).all()
    session.close()
    return all_logs


def save_audit_log(invoice_id: str, tone_used: str, status: str, email_content: str = ""): # <--- Update this line
    session = AuditSession()
    log_entry = AuditLog(
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        invoice_id=invoice_id,
        tone_used=tone_used,
        status=status,
        email_content=email_content
    )
    session.add(log_entry)
    session.commit()
    session.close()

if __name__ == "__main__":
    create_databases()
    insert_mock_data()

    print("\n--- Invoices in finance.db ---")
    print("{:<10} {:<15} {:<10} {:<12} {}".format("InvoiceID", "Client", "Amount", "DueDate", "Email"))
    print("-" * 65)
    for inv in get_all_invoices():
        print("{:<10} {:<15} {:<10} {:<12} {}".format(
            inv.invoice_id, inv.client_name, inv.amount, inv.due_date, inv.contact_email
        ))

    print("\n--- Audit Logs in audit.db ---")
    session = AuditSession()
    logs = session.query(AuditLog).all()
    session.close()
    if logs:
        print("{:<8} {:<22} {:<12} {:<10} {}".format("LogID", "Timestamp", "InvoiceID", "Tone", "Status"))
        print("-" * 65)
        for log in logs:
            print("{:<8} {:<22} {:<12} {:<10} {}".format(
                log.log_id, log.timestamp, log.invoice_id, log.tone_used, log.status
            ))
    else:
        print("  No audit logs yet. Run agent_graph.py first.")
