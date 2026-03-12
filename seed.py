"""Populate the database with sample data for demonstration."""

from datetime import date, time, timedelta

from app import create_app
from extensions import db
from models import (
    Client, Contact, FollowUp, QuickFunction, DEFAULT_QUICK_FUNCTIONS,
    InteractionType, DEFAULT_INTERACTION_TYPES,
    CustomFieldDefinition, CustomFieldValue, DEFAULT_CUSTOM_FIELDS,
    AttachmentCategory, DEFAULT_ATTACHMENT_CATEGORIES,
    AttachmentTag, DEFAULT_ATTACHMENT_TAGS,
    Attachment,
    User,
)


def seed():
    app = create_app()
    with app.app_context():
        # Clear existing data
        db.session.execute(db.text("DELETE FROM attachment_tag_map"))
        Attachment.query.delete()
        AttachmentTag.query.delete()
        AttachmentCategory.query.delete()
        CustomFieldValue.query.delete()
        CustomFieldDefinition.query.delete()
        FollowUp.query.delete()
        Contact.query.delete()
        Client.query.delete()
        QuickFunction.query.delete()
        InteractionType.query.delete()
        User.query.delete()
        db.session.commit()

        # --- Users ---
        users = []
        for udata in [
            {"username": "admin", "display_name": "Administrator", "role": "admin", "pw": "admin123"},
            {"username": "manager1", "display_name": "Sarah Manager", "role": "manager", "pw": "manager123"},
            {"username": "user1", "display_name": "James User", "role": "user", "pw": "user123"},
            {"username": "user2", "display_name": "Emily User", "role": "user", "pw": "user123"},
        ]:
            u = User(username=udata["username"], display_name=udata["display_name"], role=udata["role"])
            u.set_password(udata["pw"])
            db.session.add(u)
            users.append(u)
        db.session.flush()

        # Ownership mapping: clients 0-4 → admin, 5-9 → manager1, 10-12 → user1, 13-14 → user2
        owner_map = (
            [users[0]] * 5 + [users[1]] * 5 + [users[2]] * 3 + [users[3]] * 2
        )

        # --- Interaction Types ---
        for i, it_data in enumerate(DEFAULT_INTERACTION_TYPES):
            db.session.add(InteractionType(sort_order=i, **it_data))
        db.session.flush()

        # --- Attachment Categories ---
        attachment_cats = []
        for i, ac_data in enumerate(DEFAULT_ATTACHMENT_CATEGORIES):
            ac = AttachmentCategory(sort_order=i, **ac_data)
            db.session.add(ac)
            attachment_cats.append(ac)
        db.session.flush()

        # --- Attachment Tags ---
        attachment_tags = []
        for i, at_data in enumerate(DEFAULT_ATTACHMENT_TAGS):
            at = AttachmentTag(sort_order=i, **at_data)
            db.session.add(at)
            attachment_tags.append(at)
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

        # --- Clients (15 total) ---
        clients = [
            # 0 – Thornbury & Associates
            Client(
                company_name="Thornbury & Associates",
                industry="Legal Services",
                phone="020 7946 0123",
                email="info@thornbury.co.uk",
                contact_person="Margaret Thornbury",
                status="active",
            ),
            # 1 – Brightwell Manufacturing
            Client(
                company_name="Brightwell Manufacturing",
                industry="Manufacturing",
                phone="0121 496 0456",
                email="sales@brightwell.co.uk",
                contact_person="David Brightwell",
                status="active",
            ),
            # 2 – Hargreaves Digital
            Client(
                company_name="Hargreaves Digital",
                industry="Technology",
                phone="0161 946 0789",
                email="hello@hargreaves.digital",
                contact_person="Sarah Hargreaves",
                status="active",
            ),
            # 3 – Pemberton Logistics
            Client(
                company_name="Pemberton Logistics",
                industry="Transport & Logistics",
                phone="0113 496 0321",
                email="enquiries@pemberton-logistics.co.uk",
                contact_person="James Pemberton",
                status="prospect",
            ),
            # 4 – Ashworth Catering
            Client(
                company_name="Ashworth Catering",
                industry="Hospitality",
                phone="0151 946 0654",
                email="bookings@ashworthcatering.co.uk",
                contact_person="Emily Ashworth",
                status="prospect",
            ),
            # 5 – Cartwright Properties
            Client(
                company_name="Cartwright Properties",
                industry="Real Estate",
                phone="020 7946 0987",
                email="lettings@cartwrightprops.co.uk",
                contact_person="Richard Cartwright",
                status="lead",
            ),
            # 6 – Fenwick & Cole Accountants
            Client(
                company_name="Fenwick & Cole Accountants",
                industry="Financial Services",
                phone="0117 496 0147",
                email="partners@fenwickcole.co.uk",
                contact_person="Helen Fenwick",
                status="lead",
            ),
            # 7 – Greenfield Organics
            Client(
                company_name="Greenfield Organics",
                industry="Agriculture",
                phone="0115 496 0258",
                email="farm@greenfieldorganics.co.uk",
                contact_person="Tom Greenfield",
                status="active",
            ),
            # 8 – Mercer Engineering
            Client(
                company_name="Mercer Engineering",
                industry="Engineering",
                phone="0114 496 0369",
                email="projects@mercer-eng.co.uk",
                contact_person="Alan Mercer",
                status="inactive",
            ),
            # 9 – Whitmore Creative Agency
            Client(
                company_name="Whitmore Creative Agency",
                industry="Marketing",
                phone="020 7946 0741",
                email="studio@whitmorecreative.co.uk",
                contact_person="Lucy Whitmore",
                status="lead",
            ),
            # 10 – Oakbridge Consulting
            Client(
                company_name="Oakbridge Consulting",
                industry="Management Consulting",
                phone="020 7946 0852",
                email="enquiries@oakbridgeconsulting.co.uk",
                contact_person="William Oakbridge",
                status="active",
            ),
            # 11 – Redcastle Healthcare
            Client(
                company_name="Redcastle Healthcare",
                industry="Healthcare",
                phone="0161 946 0963",
                email="admin@redcastlehealthcare.co.uk",
                contact_person="Priya Sharma",
                status="active",
            ),
            # 12 – Longmere Education
            Client(
                company_name="Longmere Education",
                industry="Education",
                phone="0113 496 0174",
                email="info@longmere-education.co.uk",
                contact_person="Catherine Longmere",
                status="prospect",
            ),
            # 13 – Stonewick Retail Group
            Client(
                company_name="Stonewick Retail Group",
                industry="Retail",
                phone="0151 946 0285",
                email="buyers@stonewickretail.co.uk",
                contact_person="Daniel Stonewick",
                status="lead",
            ),
            # 14 – Blackwood Energy Solutions
            Client(
                company_name="Blackwood Energy Solutions",
                industry="Energy",
                phone="0131 496 0396",
                email="projects@blackwoodenergy.co.uk",
                contact_person="Fiona Blackwood",
                status="inactive",
            ),
        ]
        # Assign ownership to clients
        for i, client in enumerate(clients):
            client.user_id = owner_map[i].id

        db.session.add_all(clients)
        db.session.flush()

        # Helper: get owner for a client by index
        def _owner_id(client_idx):
            return owner_map[client_idx].id

        today = date.today()

        # --- Contacts (interaction history) ---
        contacts = [
            # ── Recent contacts (existing, relative to today) ──
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

            # ── Q3 2025 — earliest outreach (Jul–Sep 2025) ──
            Contact(client_id=clients[0].id, date=date(2025, 7, 15),
                    contact_type="email",
                    notes="Cold email introducing our consultancy services.",
                    outcome="Auto-reply — out of office until August"),
            Contact(client_id=clients[1].id, date=date(2025, 8, 5),
                    time=time(10, 0),
                    contact_type="phone",
                    notes="Initial cold call to discuss manufacturing support.",
                    outcome="Gatekeeper took message, promised callback"),
            Contact(client_id=clients[8].id, date=date(2025, 8, 22),
                    contact_type="email",
                    notes="Sent introductory email about engineering project management.",
                    outcome="Replied with interest in autumn projects"),
            Contact(client_id=clients[14].id, date=date(2025, 9, 10),
                    time=time(14, 30),
                    contact_type="phone",
                    notes="Cold call — introduced energy consultancy services.",
                    outcome="Asked to send overview brochure"),

            # ── Q4 2025 — follow-up meetings, proposals (Oct–Dec 2025) ──
            Contact(client_id=clients[0].id, date=date(2025, 10, 3),
                    time=time(11, 0),
                    contact_type="meeting",
                    notes="First face-to-face meeting at their Birmingham office.",
                    outcome="Strong interest — requested formal proposal"),
            Contact(client_id=clients[1].id, date=date(2025, 10, 18),
                    contact_type="email",
                    notes="Sent detailed proposal for production line assessment.",
                    outcome="Forwarded to technical director"),
            Contact(client_id=clients[8].id, date=date(2025, 11, 7),
                    time=time(9, 30),
                    contact_type="meeting",
                    notes="On-site visit to review current engineering workflows.",
                    outcome="Identified three areas for improvement"),
            Contact(client_id=clients[10].id, date=date(2025, 11, 20),
                    contact_type="email",
                    notes="Referral from industry contact — sent introductory pack.",
                    outcome="William replied, keen to discuss in new year"),
            Contact(client_id=clients[14].id, date=date(2025, 12, 2),
                    contact_type="email",
                    notes="Sent energy audit proposal document.",
                    outcome="Under internal review"),
            Contact(client_id=clients[11].id, date=date(2025, 12, 15),
                    time=time(10, 0),
                    contact_type="phone",
                    notes="Initial call with Priya about healthcare compliance consulting.",
                    outcome="Scheduled January meeting"),

            # ── Q1 2026 — active engagement, demos, negotiations (Jan–Mar) ──
            Contact(client_id=clients[10].id, date=date(2026, 1, 8),
                    time=time(14, 0),
                    contact_type="meeting",
                    notes="Strategy workshop at Oakbridge offices in Canary Wharf.",
                    outcome="Agreed on scope for pilot project"),
            Contact(client_id=clients[11].id, date=date(2026, 1, 22),
                    time=time(11, 30),
                    contact_type="meeting",
                    notes="Presented compliance audit framework to leadership team.",
                    outcome="Requested pricing for full audit"),
            Contact(client_id=clients[12].id, date=date(2026, 1, 28),
                    contact_type="email",
                    notes="Responded to inbound enquiry about education sector consulting.",
                    outcome="Sent case studies from similar projects"),
            Contact(client_id=clients[13].id, date=date(2026, 2, 5),
                    time=time(15, 0),
                    contact_type="phone",
                    notes="Exploratory call about retail inventory optimisation.",
                    outcome="Interested — wants to see ROI projections"),
            Contact(client_id=clients[12].id, date=date(2026, 2, 14),
                    time=time(10, 0),
                    contact_type="meeting",
                    notes="Campus tour and requirements gathering session.",
                    outcome="Detailed brief received, preparing proposal"),
            Contact(client_id=clients[4].id, date=date(2026, 2, 20),
                    contact_type="email",
                    notes="Sent revised catering partnership terms after feedback.",
                    outcome="Under review by their events director"),
            Contact(client_id=clients[13].id, date=date(2026, 3, 1),
                    contact_type="email",
                    notes="Sent ROI projections and implementation timeline.",
                    outcome="Shared with board, decision expected April"),
            Contact(client_id=clients[5].id, date=date(2026, 3, 5),
                    time=time(9, 0),
                    contact_type="phone",
                    notes="Followed up on property portfolio — discussed specific listings.",
                    outcome="Narrowed interest to three commercial units"),
            Contact(client_id=clients[6].id, date=date(2026, 3, 8),
                    contact_type="email",
                    notes="Sent accounting software integration proposal.",
                    outcome="Helen forwarded to IT department for review"),
        ]
        # Assign ownership to contacts based on their client's owner
        for c in contacts:
            c.user_id = db.session.get(Client, c.client_id).user_id
        db.session.add_all(contacts)

        # --- Follow-ups ---
        followups = [
            # ── Current week (existing, relative to today) ──
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

            # ── Q4 2025 & Q1 2026 — completed historical follow-ups ──
            FollowUp(client_id=clients[0].id, due_date=date(2025, 10, 10),
                      priority="high",
                      notes="Prepare formal proposal after initial meeting",
                      completed=True),
            FollowUp(client_id=clients[1].id, due_date=date(2025, 11, 1),
                      priority="medium",
                      notes="Chase technical director on proposal feedback",
                      completed=True),
            FollowUp(client_id=clients[8].id, due_date=date(2025, 11, 15),
                      priority="high",
                      notes="Send improvement recommendations after site visit",
                      completed=True),
            FollowUp(client_id=clients[10].id, due_date=date(2026, 1, 5),
                      priority="medium",
                      notes="Schedule new year strategy workshop",
                      completed=True),
            FollowUp(client_id=clients[11].id, due_date=date(2026, 1, 20),
                      priority="high",
                      notes="Prepare compliance audit presentation for leadership",
                      completed=True),
            FollowUp(client_id=clients[14].id, due_date=date(2026, 2, 1),
                      priority="low",
                      notes="Follow up on energy audit proposal status",
                      completed=True),

            # ── Q2 2026 (Apr–Jun) — near-term pipeline ──
            FollowUp(client_id=clients[10].id, due_date=date(2026, 4, 7),
                      due_time=time(10, 0),
                      priority="high",
                      notes="Kick-off meeting for pilot consulting project"),
            FollowUp(client_id=clients[13].id, due_date=date(2026, 4, 15),
                      priority="high",
                      notes="Chase board decision on retail optimisation proposal"),
            FollowUp(client_id=clients[11].id, due_date=date(2026, 5, 1),
                      due_time=time(14, 0),
                      priority="medium",
                      notes="Deliver compliance audit pricing and timeline"),
            FollowUp(client_id=clients[12].id, due_date=date(2026, 5, 20),
                      priority="medium",
                      notes="Submit education consulting proposal"),
            FollowUp(client_id=clients[4].id, due_date=date(2026, 6, 10),
                      priority="low",
                      notes="Follow up on catering partnership terms review"),

            # ── Q3 2026 (Jul–Sep) — mid-term planning ──
            FollowUp(client_id=clients[0].id, due_date=date(2026, 7, 1),
                      priority="medium",
                      notes="Schedule mid-year service review with Margaret"),
            FollowUp(client_id=clients[7].id, due_date=date(2026, 8, 15),
                      priority="medium",
                      notes="Renegotiate autumn supply contract terms"),
            FollowUp(client_id=clients[1].id, due_date=date(2026, 9, 1),
                      priority="low",
                      notes="Check in on production line upgrade progress"),
            FollowUp(client_id=clients[14].id, due_date=date(2026, 9, 20),
                      priority="low",
                      notes="Re-engage about energy audit — new financial year"),

            # ── Q4 2026 (Oct–Dec) — long-term reminders ──
            FollowUp(client_id=clients[10].id, due_date=date(2026, 10, 5),
                      priority="low",
                      notes="Review pilot project outcomes and plan phase two"),
            FollowUp(client_id=clients[2].id, due_date=date(2026, 11, 1),
                      priority="low",
                      notes="Annual contract renewal discussion with Sarah"),
            FollowUp(client_id=clients[3].id, due_date=date(2026, 12, 1),
                      priority="low",
                      notes="Year-end review — assess logistics partnership value"),
        ]
        # Assign ownership to follow-ups based on their client's owner
        for fu in followups:
            fu.user_id = db.session.get(Client, fu.client_id).user_id
        db.session.add_all(followups)

        # --- Custom Field Values (sample data for some clients) ---
        addr_def = custom_field_defs[0]     # Address
        linkedin_def = custom_field_defs[1]  # LinkedIn
        twitter_def = custom_field_defs[2]   # Twitter / X

        custom_values = [
            # Existing values
            CustomFieldValue(definition_id=addr_def.id, client_id=clients[0].id,
                             value="14 Temple Row, Birmingham B2 5JR"),
            CustomFieldValue(definition_id=addr_def.id, client_id=clients[2].id,
                             value="Unit 7, MediaCity, Salford M50 2HE"),
            CustomFieldValue(definition_id=linkedin_def.id, client_id=clients[2].id,
                             value="https://linkedin.com/company/hargreaves-digital"),
            # New values
            CustomFieldValue(definition_id=addr_def.id, client_id=clients[1].id,
                             value="Brightwell Works, Aston Road, Birmingham B6 4RJ"),
            CustomFieldValue(definition_id=addr_def.id, client_id=clients[10].id,
                             value="3rd Floor, 25 Canada Square, London E14 5LQ"),
            CustomFieldValue(definition_id=addr_def.id, client_id=clients[11].id,
                             value="Redcastle House, Princess Street, Manchester M1 4HB"),
            CustomFieldValue(definition_id=linkedin_def.id, client_id=clients[10].id,
                             value="https://linkedin.com/company/oakbridge-consulting"),
            CustomFieldValue(definition_id=linkedin_def.id, client_id=clients[0].id,
                             value="https://linkedin.com/company/thornbury-associates"),
            CustomFieldValue(definition_id=twitter_def.id, client_id=clients[9].id,
                             value="https://x.com/whitmorecreative"),
            CustomFieldValue(definition_id=twitter_def.id, client_id=clients[2].id,
                             value="https://x.com/hargreavesdigital"),
            CustomFieldValue(definition_id=twitter_def.id, client_id=clients[11].id,
                             value="https://x.com/redcastlehealth"),
        ]
        db.session.add_all(custom_values)

        db.session.commit()
        print(
            f"Seeded {len(users)} users, {len(clients)} clients, {len(contacts)} contacts, "
            f"{len(followups)} follow-ups, {len(custom_values)} custom field values, "
            f"{len(attachment_cats)} attachment categories, {len(attachment_tags)} attachment tags."
        )


if __name__ == "__main__":
    seed()
