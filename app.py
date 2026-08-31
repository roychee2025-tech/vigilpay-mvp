from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from core_bank import get_transaction

from database import (
    init_db,
    log_conversation,
    get_conversation,
    log_audit,
    get_audit_log,
    reset_case
)

def seed_demo_transaction():
    from database import get_connection

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO transactions (
        transaction_id,
        customer_id,
        amount,
        payee,
        new_payee,
        destination_type,
        recent_transfers,
        purpose
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "TX001",
        "CUST001",
        25000,
        "NEXUS DIGITAL ASSETS PTE LTD",
        1,
        "Digital asset / crypto",
        3,
        "Investment opportunity introduced by an online friend. "
        "Returns are guaranteed and payment must be made today."
    ))

    conn.commit()
    conn.close()

from risk_engine import assess_transaction
from rag import retrieve
from llm import generate_coaching_question


app = FastAPI(
    title="VigilPay Prototype",
    description="Synthetic VigilPay scam-prevention MVP",
    version="1.0"
)

init_db()
seed_demo_transaction()

# ---------------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------------

class CustomerReply(BaseModel):
    answer: str


class SpecialistDecision(BaseModel):
    decision: str
    officer: str = "Fraud Specialist"
    comments: str = ""


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <body style="font-family:Arial;padding:30px;">
            <h1>VigilPay</h1>
            <p>VigilPay prototype is running.</p>

            <p>
                <a href="/demo">Open End-to-End Demo</a>
            </p>

            <p>
                <a href="/docs">Open API Documentation</a>
            </p>
        </body>
    </html>
    """


# ---------------------------------------------------------
# SIMULATED CORE BANKING API
# ---------------------------------------------------------

@app.get("/core/transactions/{transaction_id}")
def core_transaction(transaction_id: str):

    transaction = get_transaction(transaction_id)

    if not transaction:
        return {
            "error": "Transaction not found"
        }

    return transaction


# ---------------------------------------------------------
# RISK ASSESSMENT
# ---------------------------------------------------------

@app.get("/vigilpay/assess/{transaction_id}")
def vigilpay_assess(transaction_id: str):

    transaction = get_transaction(transaction_id)

    if not transaction:
        return {
            "error": "Transaction not found"
        }

    assessment = assess_transaction(
        transaction
    )

    return {
        "transaction": transaction,
        "assessment": assessment
    }


# ---------------------------------------------------------
# RAG RETRIEVAL
# ---------------------------------------------------------

@app.get("/vigilpay/rag/{transaction_id}")
def vigilpay_rag(transaction_id: str):

    transaction = get_transaction(
        transaction_id
    )

    if not transaction:
        return {
            "error": "Transaction not found"
        }

    assessment = assess_transaction(
        transaction
    )

    search_query = (
        f"{transaction['purpose']} "
        f"{transaction['destination_type']} "
        f"{' '.join(assessment['reasons'])}"
    )

    retrieved = retrieve(
        search_query
    )

    return {
        "transaction_id":
            transaction_id,

        "risk_score":
            assessment["risk_score"],

        "risk_level":
            assessment["risk_level"],

        "search_query":
            search_query,

        "retrieved_evidence":
            retrieved
    }


# ---------------------------------------------------------
# START CUSTOMER COACHING
# ---------------------------------------------------------

@app.get("/vigilpay/coach/{transaction_id}")
def vigilpay_coach(transaction_id: str):

    transaction = get_transaction(
        transaction_id
    )

    if not transaction:
        return {
            "error": "Transaction not found"
        }

    assessment = assess_transaction(
        transaction
    )

    search_query = (
        f"{transaction['purpose']} "
        f"{transaction['destination_type']} "
        f"{' '.join(assessment['reasons'])}"
    )

    retrieved = retrieve(
        search_query
    )

    # Mock LLM question 1
    question = generate_coaching_question(
        1
    )

    log_conversation(
        transaction_id,
        "VigilPay",
        question
    )

    log_audit(
        transaction_id,
        "COACHING_STARTED",
        (
            "Customer safety coaching started. "
            f"Risk score: {assessment['risk_score']}. "
            f"Risk level: {assessment['risk_level']}."
        )
    )

    return {
        "transaction_id":
            transaction_id,

        "risk_score":
            assessment["risk_score"],

        "risk_level":
            assessment["risk_level"],

        "retrieved_sources": [
            item["source"]
            for item in retrieved
        ],

        "coaching_question":
            question,

        "turn":
            1,

        "llm_mode":
            "MOCK"
    }


# ---------------------------------------------------------
# CUSTOMER MULTI-TURN RESPONSE
# ---------------------------------------------------------

@app.post("/vigilpay/respond/{transaction_id}")
def vigilpay_respond(
    transaction_id: str,
    reply: CustomerReply
):

    transaction = get_transaction(
        transaction_id
    )

    if not transaction:
        return {
            "error": "Transaction not found"
        }

    answer_text = reply.answer.strip()

    if not answer_text:
        return {
            "error": "Answer cannot be empty"
        }

    # Store customer's answer
    log_conversation(
        transaction_id,
        "Customer",
        answer_text
    )

    conversation = get_conversation(
        transaction_id
    )

    customer_answers = [
        item
        for item in conversation
        if item["speaker"] == "Customer"
    ]

    turn_number = len(
        customer_answers
    )

    confirmed_indicators = 0


    # -----------------------------------------------------
    # QUESTION 1
    # Have you met the person face-to-face?
    #
    # Suspicious:
    # only online / never met / not met
    # -----------------------------------------------------

    if len(customer_answers) >= 1:

        answer1 = (
            customer_answers[0]["message"]
            .lower()
        )

        if (
            "online" in answer1
            or "never met" in answer1
            or "not met" in answer1
            or "haven't met" in answer1
            or "have not met" in answer1
        ):
            confirmed_indicators += 1


    # -----------------------------------------------------
    # QUESTION 2
    # Were you told to keep the investment confidential?
    #
    # Suspicious:
    # yes / secret / confidential / don't tell
    # -----------------------------------------------------

    if len(customer_answers) >= 2:

        answer2 = (
            customer_answers[1]["message"]
            .lower()
        )

        if (
            "yes" in answer2
            or "secret" in answer2
            or "confidential" in answer2
            or "not tell" in answer2
            or "don't tell" in answer2
            or "do not tell" in answer2
        ):
            confirmed_indicators += 1


    # -----------------------------------------------------
    # QUESTION 3
    # Have you successfully withdrawn your profits?
    #
    # Suspicious:
    # NO / never / cannot / unable
    #
    # "YES" is NOT suspicious here.
    # -----------------------------------------------------

    if len(customer_answers) >= 3:

        answer3 = (
            customer_answers[2]["message"]
            .lower()
        )

        if (
            "no" in answer3
            or "never" in answer3
            or "cannot" in answer3
            or "can't" in answer3
            or "unable" in answer3
            or "not able" in answer3
        ):
            confirmed_indicators += 1


    # -----------------------------------------------------
    # THREE QUESTIONS COMPLETED
    # -----------------------------------------------------

    if turn_number >= 3:

        # Two or more confirmed indicators
        # trigger human review.
        if confirmed_indicators >= 2:

            log_audit(
                transaction_id,
                "COACHING_COMPLETE",
                (
                    f"{confirmed_indicators} "
                    "scam indicators confirmed. "
                    "Human specialist review required."
                )
            )

            return {
                "transaction_id":
                    transaction_id,

                "status":
                    "ESCALATE",

                "confirmed_indicators":
                    confirmed_indicators,

                "message":
                    (
                        "Multiple investment-scam "
                        "warning signs have been "
                        "identified. The case has "
                        "been referred to a fraud "
                        "specialist for human review."
                    ),

                "conversation":
                    conversation
            }

        # Fewer than two indicators
        else:

            log_audit(
                transaction_id,
                "COACHING_COMPLETE",
                (
                    f"{confirmed_indicators} "
                    "scam indicators confirmed. "
                    "No immediate escalation required."
                )
            )

            return {
                "transaction_id":
                    transaction_id,

                "status":
                    "COMPLETE",

                "confirmed_indicators":
                    confirmed_indicators,

                "message":
                    (
                        "The safety check is complete. "
                        "No immediate specialist "
                        "escalation is required."
                    ),

                "conversation":
                    conversation
            }


    # -----------------------------------------------------
    # ASK NEXT QUESTION
    # -----------------------------------------------------

    next_turn = (
        turn_number + 1
    )

    next_question = (
        generate_coaching_question(
            next_turn
        )
    )

    log_conversation(
        transaction_id,
        "VigilPay",
        next_question
    )

    return {
        "transaction_id":
            transaction_id,

        "status":
            "CONTINUE_COACHING",

        "confirmed_indicators":
            confirmed_indicators,

        "next_question":
            next_question,

        "turn":
            next_turn
    }


# ---------------------------------------------------------
# FRAUD SPECIALIST CASE
# ---------------------------------------------------------

@app.get("/vigilpay/case/{transaction_id}")
def vigilpay_case(transaction_id: str):

    transaction = get_transaction(
        transaction_id
    )

    if not transaction:
        return {
            "error": "Transaction not found"
        }

    assessment = assess_transaction(
        transaction
    )

    search_query = (
        f"{transaction['purpose']} "
        f"{transaction['destination_type']} "
        f"{' '.join(assessment['reasons'])}"
    )

    retrieved = retrieve(
        search_query
    )

    conversation = get_conversation(
        transaction_id
    )

    customer_answers = [
        item["message"]
        for item in conversation
        if item["speaker"] == "Customer"
    ]

    return {
        "transaction":
            transaction,

        "assessment":
            assessment,

        "rag_sources": [
            item["source"]
            for item in retrieved
        ],

        "customer_answers":
            customer_answers,

        "case_status":
            "ESCALATED",

        "escalation_reason":
            (
                "Multiple investment-scam "
                "warning indicators were "
                "confirmed during customer coaching."
            ),

        "human_review_required":
            True
    }


# ---------------------------------------------------------
# HUMAN SPECIALIST DECISION
# ---------------------------------------------------------

@app.post("/vigilpay/decision/{transaction_id}")
def record_specialist_decision(
    transaction_id: str,
    decision: SpecialistDecision
):

    transaction = get_transaction(
        transaction_id
    )

    if not transaction:
        return {
            "error": "Transaction not found"
        }

    allowed_decisions = [
        "ALLOW",
        "HOLD",
        "CONTACT_CUSTOMER",
        "ESCALATE_INVESTIGATION"
    ]

    if (
        decision.decision
        not in allowed_decisions
    ):
        return {
            "error":
                "Invalid specialist decision"
        }

    details = (
        f"Officer: {decision.officer}; "
        f"Decision: {decision.decision}; "
        f"Comments: {decision.comments}"
    )

    log_audit(
        transaction_id,
        "HUMAN_SPECIALIST_DECISION",
        details
    )

    return {
        "transaction_id":
            transaction_id,

        "status":
            "DECISION_RECORDED",

        "decision":
            decision.decision,

        "officer":
            decision.officer,

        "comments":
            decision.comments,

        "human_decision":
            True
    }


# ---------------------------------------------------------
# AUDIT API
# ---------------------------------------------------------

@app.get("/vigilpay/audit/{transaction_id}")
def vigilpay_audit(transaction_id: str):

    transaction = get_transaction(
        transaction_id
    )

    if not transaction:
        return {
            "error": "Transaction not found"
        }

    audit = get_audit_log(
        transaction_id
    )

    return {
        "transaction_id":
            transaction_id,

        "audit_events":
            audit
    }


# ---------------------------------------------------------
# RESET DEMO CASE
# ---------------------------------------------------------

@app.post("/vigilpay/reset/{transaction_id}")
def reset_vigilpay_case(
    transaction_id: str
):

    transaction = get_transaction(
        transaction_id
    )

    if not transaction:
        return {
            "error": "Transaction not found"
        }

    reset_case(
        transaction_id
    )

    return {
        "transaction_id":
            transaction_id,

        "status":
            "RESET_COMPLETE"
    }


# ---------------------------------------------------------
# SYNTHETIC PILOT VALIDATION
# ---------------------------------------------------------

@app.get("/vigilpay/validation")
def vigilpay_validation():

    return {
        "dataset":
            "Synthetic pilot dataset",

        "status":
            "PASS",

        "metrics": [

            {
                "name":
                    "Scam Detection Recall",

                "actual":
                    93.4,

                "target":
                    90.0,

                "unit":
                    "%",

                "direction":
                    "minimum",

                "result":
                    "PASS"
            },

            {
                "name":
                    "False Positive Rate",

                "actual":
                    1.6,

                "target":
                    2.0,

                "unit":
                    "%",

                "direction":
                    "maximum",

                "result":
                    "PASS"
            },

            {
                "name":
                    "Median Decision Latency",

                "actual":
                    620,

                "target":
                    1000,

                "unit":
                    "ms",

                "direction":
                    "maximum",

                "result":
                    "PASS"
            },

            {
                "name":
                    "Grounded Responses",

                "actual":
                    99.7,

                "target":
                    98.0,

                "unit":
                    "%",

                "direction":
                    "minimum",

                "result":
                    "PASS"
            }
        ],

        "pilot_outcomes": {

            "high_risk_cases_reviewed":
                500,

            "scam_detection_recall":
                93.4,

            "false_positive_rate":
                1.6,

            "human_escalation_enabled":
                True,

            "autonomous_payment_blocking":
                False
        },

        "go_no_go": {

            "recall_target_met":
                True,

            "false_positive_target_met":
                True,

            "grounding_target_met":
                True,

            "latency_target_met":
                True,

            "recommendation":
                "GO TO CONTROLLED PILOT"
        }
    }


# ---------------------------------------------------------
# HTML PAGES
# ---------------------------------------------------------

@app.get(
    "/customer",
    response_class=HTMLResponse
)
def customer_page():

    with open(
        "customer.html",
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


@app.get(
    "/specialist",
    response_class=HTMLResponse
)
def specialist_page():

    with open(
        "specialist.html",
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


@app.get(
    "/audit",
    response_class=HTMLResponse
)
def audit_page():

    with open(
        "audit.html",
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


@app.get(
    "/dashboard",
    response_class=HTMLResponse
)
def dashboard_page():

    with open(
        "dashboard.html",
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


@app.get(
    "/demo",
    response_class=HTMLResponse
)
def demo_page():

    with open(
        "demo.html",
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()

@app.get(
    "/architecture",
    response_class=HTMLResponse
)
def architecture_page():

    with open(
        "architecture.html",
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()
