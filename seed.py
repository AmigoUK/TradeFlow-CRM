"""Populate the database with sample data for demonstration."""

from datetime import date, time, timedelta

from app import create_app
from extensions import db
from models import (
    Client, Contact, FollowUp, QuickFunction, DEFAULT_QUICK_FUNCTIONS,
    InteractionType, DEFAULT_INTERACTION_TYPES,
    CustomFieldDefinition, CustomFieldValue, DEFAULT_CUSTOM_FIELDS,
)


def seed():
    app = create_app()
    with app.app_context():
        # Clear existing data
        CustomFieldValue.query.delete()
        CustomFieldDefinition.query.delete()
        FollowUp.query.delete()
        Contact.query.delete()
        Client.query.delete()
        QuickFunction.query.delete()
        InteractionType.query.delete()
        db.session.commit()

        # --- Interaction Types ---
        for i, it_data in enumerate(DEFAULT_INTERACTION_TYPES):
            db.session.add(InteractionType(sort_order=i, **it_data))
        db.session.flush()

        # --- Custom Field Definitions ---
        custom_field_defs = []
        for i, cf_data in enumerate(DEFAULT_CUSTOM_FIELDS):
            cf = CustomFieldDefinition(sort_order=i, **cf_data)
            db.session.add(cf)
            custom_field_defs.append(cf)
        db.session.flush()

        # --- Quick Functions ---
        for i, qf_data in enumerate(DEFAULT_QUICK_FUNCTIONS):
            db.session.add(QuickFunction(sort_order=i, **qf_data))
        db.session.flush()

        # --- Clients ---
        clients = [
            Client(
                company_name="Thornbury & Associates",
                industry="Legal Services",
                phone="020 7946 0123",
                email="info@thornbury.co.uk",
                contact_person="Margaret Thornbury",
                status="active",
            ),
            Client(
                company_name="Brightwell Manufacturing",
                industry="Manufacturing",
                phone="0121 496 0456",
                email="sales@brightwell.co.uk",
                contact_person="David Brightwell",
                status="active",
            ),
            Client(
                company_name="Hargreaves Digital",
                industry="Technology",
                phone="0161 946 0789",
                email="hello@hargreaves.digital",
                contact_person="Sarah Hargreaves",
                status="active",
            ),
            Client(
                company_name="Pemberton Logistics",
                industry="Transport & Logistics",
                phone="0113 496 0321",
                email="enquiries@pemberton-logistics.co.uk",
                contact_person="James Pemberton",
                status="prospect",
            ),
            Client(
                company_name="Ashworth Catering",
                industry="Hospitality",
                phone="0151 946 0654",
                email="bookings@ashworthcatering.co.uk",
                contact_person="Emily Ashworth",
                status="prospect",
            ),
            Client(
                company_name="Cartwright Properties",
                industry="Real Estate",
                phone="020 7946 0987",
                email="lettings@cartwrightprops.co.uk",
                contact_person="Richard Cartwright",
                status="lead",
            ),
            Client(
                company_name="Fenwick & Cole Accountants",
                industry="Financial Services",
                phone="0117 496 0147",
                email="partners@fenwickcole.co.uk",
                contact_person="Helen Fenwick",
                status="lead",
            ),
            Client(
                company_name="Greenfield Organics",
                industry="Agriculture",
                phone="01onal 496 0258",
                email="farm@greenfieldorganics.co.uk",
                contact_person="Tom Greenfield",
                status="active",
            ),
            Client(
                company_name="Mercer Engineering",
                industry="Engineering",
                phone="0114 496 0369",
                email="projects@mercer-eng.co.uk",
                contact_person="Alan Mercer",
                status="inactive",
            ),
            Client(
                company_name="Whitmore Creative Agency",
                industry="Marketing",
                phone="020 7946 0741",
                email="studio@whitmorecreative.co.uk",
                contact_person="Lucy Whitmore",
                status="lead",
            ),
        ]
        db.session.add_all(clients)
        db.session.flush()

        today = date.today()

        # --- Contacts (interaction history) ---
        contacts = [
            Contact(client_id=clients[0].id, date=today - timedelta(days=2),
                    time=time(10, 30),
                    contact_type="phone", notes="Discussed quarterly review requirements.",
                    outcome="Agreed to send proposal by Friday"),
            Contact(client_id=clients[0].id, date=today - timedelta(days=10),
                    time=time(14, 0),
                    contact_type="meeting", notes="Initial consultation at their offices.",
                    outcome="Interested in full service package"),
            Contact(client_id=clients[1].id, date=today - timedelta(days=1),
                    contact_type="email", notes="Sent revised quotation for production line upgrade.",
                    outcome="Awaiting board approval"),
            Contact(client_id=clients[1].id, date=today - timedelta(days=7),
                    time=time(9, 0),
                    contact_type="phone", notes="Follow-up on machinery specifications.",
                    outcome="Requested additional technical details"),
            Contact(client_id=clients[2].id, date=today,
                    time=time(11, 0),
                    contact_type="meeting", notes="Software demo at their Salford office.",
                    outcome="Very positive — scheduling trial period"),
            Contact(client_id=clients[2].id, date=today - timedelta(days=14),
                    contact_type="email", notes="Sent introductory brochure and case studies.",
                    outcome="Requested a demo"),
            Contact(client_id=clients[3].id, date=today - timedelta(days=3),
                    time=time(15, 30),
                    contact_type="phone", notes="Cold call — introduced our logistics solutions.",
                    outcome="Interested, asked for more information"),
            Contact(client_id=clients[4].id, date=today - timedelta(days=5),
                    contact_type="email", notes="Followed up after networking event.",
                    outcome="Booked a call for next week"),
            Contact(client_id=clients[5].id, date=today - timedelta(days=1),
                    time=time(16, 0),
                    contact_type="phone", notes="Enquiry about commercial property management.",
                    outcome="Sending portfolio of managed properties"),
            Contact(client_id=clients[6].id, date=today - timedelta(days=8),
                    time=time(12, 0),
                    contact_type="meeting", notes="Met at industry conference.",
                    outcome="Exchanged contacts, will follow up"),
            Contact(client_id=clients[7].id, date=today - timedelta(days=4),
                    time=time(13, 45),
                    contact_type="phone", notes="Discussed seasonal supply contract.",
                    outcome="Drafting contract terms"),
            Contact(client_id=clients[7].id, date=today - timedelta(days=20),
                    contact_type="email", notes="Initial outreach about organic supply chain.",
                    outcome="Positive response, scheduled call"),
            Contact(client_id=clients[0].id, date=today - timedelta(days=30),
                    contact_type="email", notes="Sent introductory email about our services.",
                    outcome="Replied with interest"),
            Contact(client_id=clients[3].id, date=today - timedelta(days=15),
                    contact_type="email", notes="Sent logistics case study.",
                    outcome="No response yet"),
            Contact(client_id=clients[9].id, date=today - timedelta(days=6),
                    contact_type="phone", notes="Discussed potential branding project.",
                    outcome="Interested but budget not confirmed"),
        ]
        db.session.add_all(contacts)

        # --- Follow-ups ---
        followups = [
            FollowUp(client_id=clients[0].id, due_date=today,
                      due_time=time(9, 0),
                      priority="high", notes="Send quarterly review proposal"),
            FollowUp(client_id=clients[1].id, due_date=today,
                      due_time=time(14, 30),
                      priority="medium", notes="Chase board decision on quotation"),
            FollowUp(client_id=clients[2].id, due_date=today + timedelta(days=2),
                      due_time=time(10, 0),
                      priority="high", notes="Set up trial period access"),
            FollowUp(client_id=clients[3].id, due_date=today + timedelta(days=1),
                      priority="medium", notes="Send detailed logistics brochure"),
            FollowUp(client_id=clients[4].id, due_date=today + timedelta(days=3),
                      due_time=time(11, 30),
                      priority="low", notes="Prepare for scheduled call"),
            FollowUp(client_id=clients[5].id, due_date=today - timedelta(days=1),
                      due_time=time(9, 0),
                      priority="high", notes="Send property portfolio — promised yesterday"),
            FollowUp(client_id=clients[6].id, due_date=today - timedelta(days=3),
                      priority="medium", notes="Follow up from conference meeting"),
            FollowUp(client_id=clients[7].id, due_date=today + timedelta(days=5),
                      priority="low", notes="Finalise seasonal contract terms"),
            FollowUp(client_id=clients[8].id, due_date=today - timedelta(days=7),
                      priority="low", notes="Check if reactivation is possible",
                      completed=True),
            FollowUp(client_id=clients[9].id, due_date=today + timedelta(days=7),
                      due_time=time(16, 0),
                      priority="medium", notes="Follow up on budget confirmation"),
            FollowUp(client_id=clients[0].id, due_date=today - timedelta(days=5),
                      priority="high", notes="Prepare meeting summary notes",
                      completed=True),
            FollowUp(client_id=clients[2].id, due_date=today - timedelta(days=2),
                      priority="medium", notes="Send demo recording link",
                      completed=True),
        ]
        db.session.add_all(followups)

        # --- Custom Field Values (sample data for some clients) ---
        # Address field (first definition)
        addr_def = custom_field_defs[0]  # Address
        linkedin_def = custom_field_defs[1]  # LinkedIn
        db.session.add(CustomFieldValue(definition_id=addr_def.id, client_id=clients[0].id, value="14 Temple Row, Birmingham B2 5JR"))
        db.session.add(CustomFieldValue(definition_id=addr_def.id, client_id=clients[2].id, value="Unit 7, MediaCity, Salford M50 2HE"))
        db.session.add(CustomFieldValue(definition_id=linkedin_def.id, client_id=clients[2].id, value="https://linkedin.com/company/hargreaves-digital"))

        db.session.commit()
        print(f"Seeded {len(clients)} clients, {len(contacts)} contacts, {len(followups)} follow-ups.")


if __name__ == "__main__":
    seed()
