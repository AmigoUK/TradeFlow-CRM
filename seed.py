"""Populate the database with sample data for demonstration."""

import random
from datetime import date, time, timedelta

from app import create_app
from extensions import db
from models import (
    Company, COMPANY_STATUSES, Interaction, Contact, SocialAccount,
    FollowUp, QuickFunction, DEFAULT_QUICK_FUNCTIONS,
    InteractionType, DEFAULT_INTERACTION_TYPES,
    CustomFieldDefinition, CustomFieldValue, DEFAULT_CUSTOM_FIELDS,
    AttachmentCategory, DEFAULT_ATTACHMENT_CATEGORIES,
    AttachmentTag, DEFAULT_ATTACHMENT_TAGS,
    Attachment,
    User,
)

# ---------------------------------------------------------------------------
# Curated company data
# ---------------------------------------------------------------------------

UK_COMPANIES = [
    # First 15 preserve existing companies
    {"company_name": "Thornbury & Associates", "industry": "Legal Services", "phone": "020 7946 0123", "email": "info@thornbury.co.uk", "contact_person": "Margaret Thornbury", "status": "active"},
    {"company_name": "Brightwell Manufacturing", "industry": "Manufacturing", "phone": "0121 496 0456", "email": "sales@brightwell.co.uk", "contact_person": "David Brightwell", "status": "active"},
    {"company_name": "Hargreaves Digital", "industry": "Technology", "phone": "0161 946 0789", "email": "hello@hargreaves.digital", "contact_person": "Sarah Hargreaves", "status": "active"},
    {"company_name": "Pemberton Logistics", "industry": "Transport & Logistics", "phone": "0113 496 0321", "email": "enquiries@pemberton-logistics.co.uk", "contact_person": "James Pemberton", "status": "prospect"},
    {"company_name": "Ashworth Catering", "industry": "Hospitality", "phone": "0151 946 0654", "email": "bookings@ashworthcatering.co.uk", "contact_person": "Emily Ashworth", "status": "prospect"},
    {"company_name": "Cartwright Properties", "industry": "Real Estate", "phone": "020 7946 0987", "email": "lettings@cartwrightprops.co.uk", "contact_person": "Richard Cartwright", "status": "lead"},
    {"company_name": "Fenwick & Cole Accountants", "industry": "Financial Services", "phone": "0117 496 0147", "email": "partners@fenwickcole.co.uk", "contact_person": "Helen Fenwick", "status": "lead"},
    {"company_name": "Greenfield Organics", "industry": "Agriculture", "phone": "0115 496 0258", "email": "farm@greenfieldorganics.co.uk", "contact_person": "Tom Greenfield", "status": "active"},
    {"company_name": "Mercer Engineering", "industry": "Engineering", "phone": "0114 496 0369", "email": "projects@mercer-eng.co.uk", "contact_person": "Alan Mercer", "status": "inactive"},
    {"company_name": "Whitmore Creative Agency", "industry": "Marketing", "phone": "020 7946 0741", "email": "studio@whitmorecreative.co.uk", "contact_person": "Lucy Whitmore", "status": "lead"},
    {"company_name": "Oakbridge Consulting", "industry": "Management Consulting", "phone": "020 7946 0852", "email": "enquiries@oakbridgeconsulting.co.uk", "contact_person": "William Oakbridge", "status": "active"},
    {"company_name": "Redcastle Healthcare", "industry": "Healthcare", "phone": "0161 946 0963", "email": "admin@redcastlehealthcare.co.uk", "contact_person": "Priya Sharma", "status": "active"},
    {"company_name": "Longmere Education", "industry": "Education", "phone": "0113 496 0174", "email": "info@longmere-education.co.uk", "contact_person": "Catherine Longmere", "status": "prospect"},
    {"company_name": "Stonewick Retail Group", "industry": "Retail", "phone": "0151 946 0285", "email": "buyers@stonewickretail.co.uk", "contact_person": "Daniel Stonewick", "status": "lead"},
    {"company_name": "Blackwood Energy Solutions", "industry": "Energy", "phone": "0131 496 0396", "email": "projects@blackwoodenergy.co.uk", "contact_person": "Fiona Blackwood", "status": "inactive"},
    # 15-39: additional UK companies
    {"company_name": "Harrowgate Telecom", "industry": "Telecom", "phone": "0113 946 0412", "email": "info@harrowgatetelecom.co.uk", "contact_person": "George Harrowgate", "status": "active"},
    {"company_name": "Dunmore Pharma", "industry": "Pharma", "phone": "020 7946 0513", "email": "enquiries@dunmorepharma.co.uk", "contact_person": "Dr. Susan Dunmore", "status": "active"},
    {"company_name": "Crestfield Construction", "industry": "Construction", "phone": "0121 496 0624", "email": "tenders@crestfieldconstruction.co.uk", "contact_person": "Mark Crestfield", "status": "prospect"},
    {"company_name": "Waverly Media Group", "industry": "Media", "phone": "020 7946 0735", "email": "press@waverlymedia.co.uk", "contact_person": "Olivia Waverly", "status": "lead"},
    {"company_name": "Sterling Insurance", "industry": "Insurance", "phone": "0161 946 0846", "email": "claims@sterlinginsurance.co.uk", "contact_person": "Patrick Sterling", "status": "active"},
    {"company_name": "Ashford & Partners", "industry": "Legal Services", "phone": "0117 496 0957", "email": "legal@ashfordpartners.co.uk", "contact_person": "Victoria Ashford", "status": "prospect"},
    {"company_name": "Huxley Biotech", "industry": "Pharma", "phone": "01onal 496 0168", "email": "research@huxleybiotech.co.uk", "contact_person": "Dr. James Huxley", "status": "active"},
    {"company_name": "Pennington Foods", "industry": "Food & Beverage", "phone": "0151 946 0279", "email": "orders@penningtonfoods.co.uk", "contact_person": "Rachel Pennington", "status": "active"},
    {"company_name": "Kingsley Motors", "industry": "Automotive", "phone": "0121 496 0381", "email": "fleet@kingsleymotors.co.uk", "contact_person": "Andrew Kingsley", "status": "prospect"},
    {"company_name": "Beaumont Hotels", "industry": "Hospitality", "phone": "020 7946 0492", "email": "reservations@beaumonthotels.co.uk", "contact_person": "Claire Beaumont", "status": "lead"},
    {"company_name": "Greystone Mining", "industry": "Mining", "phone": "01onal 946 0514", "email": "operations@greystonemining.co.uk", "contact_person": "Robert Greystone", "status": "inactive"},
    {"company_name": "Whitfield Textiles", "industry": "Manufacturing", "phone": "0161 946 0625", "email": "sales@whitfieldtextiles.co.uk", "contact_person": "Emma Whitfield", "status": "active"},
    {"company_name": "Barrington Wealth", "industry": "Financial Services", "phone": "020 7946 0736", "email": "advisory@barringtonwealth.co.uk", "contact_person": "Henry Barrington", "status": "active"},
    {"company_name": "Lockwood Architects", "industry": "Construction", "phone": "0113 496 0847", "email": "design@lockwoodarchitects.co.uk", "contact_person": "Sophie Lockwood", "status": "prospect"},
    {"company_name": "Sanderson Transport", "industry": "Transport & Logistics", "phone": "0114 496 0958", "email": "dispatch@sandersontransport.co.uk", "contact_person": "Neil Sanderson", "status": "lead"},
    {"company_name": "Hartley Publishing", "industry": "Media", "phone": "020 7946 0169", "email": "submissions@hartleypublishing.co.uk", "contact_person": "Diana Hartley", "status": "active"},
    {"company_name": "Cromwell Defence", "industry": "Defence", "phone": "01onal 496 0271", "email": "contracts@cromwelldefence.co.uk", "contact_person": "Colonel Peter Cromwell", "status": "prospect"},
    {"company_name": "Northgate IT Services", "industry": "Technology", "phone": "0161 946 0382", "email": "support@northgateit.co.uk", "contact_person": "Kevin Northgate", "status": "lead"},
    {"company_name": "Aldridge Environmental", "industry": "Environmental Services", "phone": "0117 496 0493", "email": "info@aldridgeenvironmental.co.uk", "contact_person": "Laura Aldridge", "status": "inactive"},
    {"company_name": "Fairfax Recruitment", "industry": "Human Resources", "phone": "020 7946 0515", "email": "hire@fairfaxrecruitment.co.uk", "contact_person": "Simon Fairfax", "status": "active"},
    {"company_name": "Burroughs Aerospace", "industry": "Aerospace", "phone": "01onal 946 0626", "email": "projects@burroughsaero.co.uk", "contact_person": "Dr. Hannah Burroughs", "status": "prospect"},
    {"company_name": "Chilton Veterinary Group", "industry": "Healthcare", "phone": "01onal 496 0737", "email": "reception@chiltonvets.co.uk", "contact_person": "Dr. Michael Chilton", "status": "lead"},
    {"company_name": "Elmswood Furniture", "industry": "Retail", "phone": "0114 496 0848", "email": "showroom@elmswoodfurniture.co.uk", "contact_person": "Jennifer Elmswood", "status": "active"},
    {"company_name": "Rutherford Analytics", "industry": "Technology", "phone": "0131 496 0959", "email": "data@rutherfordanalytics.co.uk", "contact_person": "Dr. Ian Rutherford", "status": "active"},
    {"company_name": "Prescott Shipping", "industry": "Transport & Logistics", "phone": "0151 946 0161", "email": "cargo@prescottshipping.co.uk", "contact_person": "Thomas Prescott", "status": "inactive"},
]

US_COMPANIES = [
    {"company_name": "Pinnacle Software Inc", "industry": "Technology", "phone": "(415) 555-0123", "email": "info@pinnaclesoft.com", "contact_person": "Mike Chen", "status": "active"},
    {"company_name": "Great Lakes Manufacturing", "industry": "Manufacturing", "phone": "(312) 555-0234", "email": "sales@greatlakesmfg.com", "contact_person": "Karen O'Brien", "status": "active"},
    {"company_name": "Redwood Capital Partners", "industry": "Financial Services", "phone": "(212) 555-0345", "email": "invest@redwoodcapital.com", "contact_person": "Jonathan Reeves", "status": "prospect"},
    {"company_name": "Sunshine Health Systems", "industry": "Healthcare", "phone": "(305) 555-0456", "email": "admin@sunshinehealth.com", "contact_person": "Dr. Maria Rodriguez", "status": "active"},
    {"company_name": "Pacific Rim Trading", "industry": "Import/Export", "phone": "(206) 555-0567", "email": "trade@pacificrimtrading.com", "contact_person": "David Tanaka", "status": "prospect"},
    {"company_name": "Liberty Legal Group", "industry": "Legal Services", "phone": "(202) 555-0678", "email": "partners@libertylegal.com", "contact_person": "Sarah Washington", "status": "lead"},
    {"company_name": "Heartland Agriculture Co", "industry": "Agriculture", "phone": "(515) 555-0789", "email": "info@heartlandag.com", "contact_person": "Bob Miller", "status": "active"},
    {"company_name": "Skyline Construction LLC", "industry": "Construction", "phone": "(303) 555-0891", "email": "bids@skylineconstruction.com", "contact_person": "Carlos Mendez", "status": "prospect"},
    {"company_name": "Digital Frontier Media", "industry": "Media", "phone": "(310) 555-0912", "email": "content@digitalfrontier.com", "contact_person": "Ashley Park", "status": "lead"},
    {"company_name": "Patriot Insurance Corp", "industry": "Insurance", "phone": "(617) 555-0134", "email": "claims@patriotinsurance.com", "contact_person": "Brian Murphy", "status": "active"},
    {"company_name": "Mountain View Pharma", "industry": "Pharma", "phone": "(650) 555-0245", "email": "research@mountainviewpharma.com", "contact_person": "Dr. Lisa Chang", "status": "active"},
    {"company_name": "Lone Star Energy", "industry": "Energy", "phone": "(713) 555-0356", "email": "ops@lonestarenergy.com", "contact_person": "Travis Henderson", "status": "prospect"},
    {"company_name": "Harbor Freight Logistics", "industry": "Transport & Logistics", "phone": "(562) 555-0467", "email": "dispatch@harborfreight.com", "contact_person": "Tony Russo", "status": "lead"},
    {"company_name": "Empire State Consulting", "industry": "Management Consulting", "phone": "(212) 555-0578", "email": "engage@empirestateconsulting.com", "contact_person": "Rachel Goldman", "status": "active"},
    {"company_name": "Silicon Prairie Tech", "industry": "Technology", "phone": "(402) 555-0689", "email": "hello@siliconprairie.com", "contact_person": "Jake Anderson", "status": "lead"},
    {"company_name": "Golden Gate Hospitality", "industry": "Hospitality", "phone": "(415) 555-0791", "email": "events@goldengatehospitality.com", "contact_person": "Michelle Torres", "status": "inactive"},
    {"company_name": "Midwest Telecom Solutions", "industry": "Telecom", "phone": "(317) 555-0812", "email": "sales@midwesttelecom.com", "contact_person": "Greg Phillips", "status": "prospect"},
    {"company_name": "Cascade Environmental", "industry": "Environmental Services", "phone": "(503) 555-0923", "email": "info@cascadeenvironmental.com", "contact_person": "Jennifer Olsen", "status": "active"},
    {"company_name": "Blue Ridge Education", "industry": "Education", "phone": "(828) 555-0135", "email": "admissions@blueridgeedu.com", "contact_person": "Dr. William Hayes", "status": "lead"},
    {"company_name": "Chesapeake Marine Services", "industry": "Maritime", "phone": "(410) 555-0246", "email": "fleet@chesapeakemarine.com", "contact_person": "Captain James Cole", "status": "inactive"},
    {"company_name": "Prairie Wind Renewables", "industry": "Energy", "phone": "(316) 555-0357", "email": "projects@prairiewind.com", "contact_person": "Rebecca Foster", "status": "prospect"},
    {"company_name": "Bayou Foods International", "industry": "Food & Beverage", "phone": "(504) 555-0468", "email": "orders@bayoufoods.com", "contact_person": "Antoine Dubois", "status": "active"},
    {"company_name": "Rockpoint Mining Corp", "industry": "Mining", "phone": "(801) 555-0579", "email": "operations@rockpointmining.com", "contact_person": "Dan Mitchell", "status": "inactive"},
    {"company_name": "Apex Aerospace Defense", "industry": "Aerospace", "phone": "(256) 555-0681", "email": "contracts@apexaerospace.com", "contact_person": "Col. Robert Shaw", "status": "active"},
    {"company_name": "Metro Retail Holdings", "industry": "Retail", "phone": "(404) 555-0792", "email": "partnerships@metroretail.com", "contact_person": "Tamara Williams", "status": "lead"},
]

EU_COMPANIES = [
    {"company_name": "Müller Maschinenbau GmbH", "industry": "Manufacturing", "phone": "+49 89 555 0123", "email": "info@muller-maschinenbau.de", "contact_person": "Hans Müller", "status": "active"},
    {"company_name": "Durand et Fils SA", "industry": "Food & Beverage", "phone": "+33 1 55 55 0234", "email": "contact@durandetfils.fr", "contact_person": "Pierre Durand", "status": "prospect"},
    {"company_name": "Van der Berg Shipping BV", "industry": "Transport & Logistics", "phone": "+31 10 555 0345", "email": "logistics@vanderbergshipping.nl", "contact_person": "Jan van der Berg", "status": "active"},
    {"company_name": "García & Asociados SL", "industry": "Legal Services", "phone": "+34 91 555 0456", "email": "legal@garciaasociados.es", "contact_person": "Carmen García", "status": "lead"},
    {"company_name": "Rossi Costruzioni SpA", "industry": "Construction", "phone": "+39 02 555 0567", "email": "progetti@rossicostruzioni.it", "contact_person": "Marco Rossi", "status": "prospect"},
    {"company_name": "Schmidt Pharma AG", "industry": "Pharma", "phone": "+49 30 555 0678", "email": "forschung@schmidtpharma.de", "contact_person": "Dr. Katrin Schmidt", "status": "active"},
    {"company_name": "Lefèvre Consulting SARL", "industry": "Management Consulting", "phone": "+33 4 55 55 0789", "email": "conseil@lefevreconsulting.fr", "contact_person": "Jean-Pierre Lefèvre", "status": "active"},
    {"company_name": "De Groot Technology BV", "industry": "Technology", "phone": "+31 20 555 0891", "email": "info@degroottechnology.nl", "contact_person": "Willem de Groot", "status": "lead"},
    {"company_name": "Fernández Media SL", "industry": "Media", "phone": "+34 93 555 0912", "email": "prensa@fernandezmedia.es", "contact_person": "Ana Fernández", "status": "prospect"},
    {"company_name": "Bianchi Design Studio SRL", "industry": "Marketing", "phone": "+39 06 555 0134", "email": "studio@bianchidesign.it", "contact_person": "Giulia Bianchi", "status": "active"},
    {"company_name": "Weber Energie GmbH", "industry": "Energy", "phone": "+49 40 555 0245", "email": "vertrieb@weberenergie.de", "contact_person": "Thomas Weber", "status": "prospect"},
    {"company_name": "Moreau Insurance SA", "industry": "Insurance", "phone": "+33 3 55 55 0356", "email": "assurance@moreauinsurance.fr", "contact_person": "Claire Moreau", "status": "lead"},
    {"company_name": "Bakker Agriculture BV", "industry": "Agriculture", "phone": "+31 30 555 0467", "email": "info@bakkeragri.nl", "contact_person": "Pieter Bakker", "status": "active"},
    {"company_name": "López Telecom SA", "industry": "Telecom", "phone": "+34 91 555 0578", "email": "ventas@lopeztelecom.es", "contact_person": "Diego López", "status": "inactive"},
    {"company_name": "Conti Financial Services SpA", "industry": "Financial Services", "phone": "+39 02 555 0689", "email": "investimenti@contifinancial.it", "contact_person": "Alessandro Conti", "status": "active"},
    {"company_name": "Fischer Automotive GmbH", "industry": "Automotive", "phone": "+49 711 555 0791", "email": "fleet@fischerautomotive.de", "contact_person": "Stefan Fischer", "status": "lead"},
    {"company_name": "Bernard Hotels Group SA", "industry": "Hospitality", "phone": "+33 1 55 55 0812", "email": "reservations@bernardhotels.fr", "contact_person": "Marie Bernard", "status": "active"},
    {"company_name": "Visser Environmental BV", "industry": "Environmental Services", "phone": "+31 70 555 0923", "email": "milieu@visserenvironmental.nl", "contact_person": "Lisa Visser", "status": "prospect"},
    {"company_name": "Martínez Education SL", "industry": "Education", "phone": "+34 91 555 0135", "email": "academia@martinezeducation.es", "contact_person": "Prof. Rafael Martínez", "status": "inactive"},
    {"company_name": "Romano Healthcare SRL", "industry": "Healthcare", "phone": "+39 06 555 0246", "email": "clinica@romanohealthcare.it", "contact_person": "Dr. Laura Romano", "status": "active"},
    {"company_name": "Braun Defence Systems GmbH", "industry": "Defence", "phone": "+49 89 555 0357", "email": "vertrag@braundefence.de", "contact_person": "Markus Braun", "status": "prospect"},
    {"company_name": "Petit Retail Group SA", "industry": "Retail", "phone": "+33 4 55 55 0468", "email": "achats@petitretail.fr", "contact_person": "Sophie Petit", "status": "lead"},
    {"company_name": "Jansen Recruitment BV", "industry": "Human Resources", "phone": "+31 20 555 0579", "email": "vacatures@jansenrecruitment.nl", "contact_person": "Anna Jansen", "status": "active"},
    {"company_name": "Ruiz Construction SA", "industry": "Construction", "phone": "+34 93 555 0681", "email": "obras@ruizconstruction.es", "contact_person": "Miguel Ruiz", "status": "inactive"},
    {"company_name": "Colombo Aerospace SRL", "industry": "Aerospace", "phone": "+39 011 555 0792", "email": "aviazione@colomboaerospace.it", "contact_person": "Paolo Colombo", "status": "lead"},
]

OTHER_COMPANIES = [
    {"company_name": "Southern Cross Mining", "industry": "Mining", "phone": "+61 2 5550 0123", "email": "ops@southerncrossmining.com.au", "contact_person": "Bruce Campbell", "status": "active"},
    {"company_name": "Sakura Technologies KK", "industry": "Technology", "phone": "+81 3 5550 0234", "email": "info@sakuratech.co.jp", "contact_person": "Yuki Tanaka", "status": "prospect"},
    {"company_name": "Emirates Trading LLC", "industry": "Import/Export", "phone": "+971 4 555 0345", "email": "trade@emiratestrading.ae", "contact_person": "Ahmed Al-Rashid", "status": "active"},
    {"company_name": "Maple Leaf Consulting", "industry": "Management Consulting", "phone": "+1 416 555 0456", "email": "engage@mapleleafconsulting.ca", "contact_person": "Sarah Thompson", "status": "lead"},
    {"company_name": "Tata Digital Solutions", "industry": "Technology", "phone": "+91 22 5550 0567", "email": "solutions@tatadigital.in", "contact_person": "Rajesh Patel", "status": "active"},
    {"company_name": "Seoul Semiconductor Corp", "industry": "Manufacturing", "phone": "+82 2 5550 0678", "email": "sales@seoulsemi.kr", "contact_person": "Min-Jun Park", "status": "prospect"},
    {"company_name": "Kiwi Agricultural Exports", "industry": "Agriculture", "phone": "+64 9 555 0789", "email": "exports@kiwiagri.co.nz", "contact_person": "James Wilson", "status": "lead"},
    {"company_name": "Nordic Shipping AS", "industry": "Transport & Logistics", "phone": "+47 22 55 50 89", "email": "freight@nordicshipping.no", "contact_person": "Erik Johansen", "status": "inactive"},
    {"company_name": "São Paulo Pharma Ltda", "industry": "Pharma", "phone": "+55 11 5550 0912", "email": "pesquisa@saopaulopharma.com.br", "contact_person": "Dr. Ana Silva", "status": "active"},
    {"company_name": "Cape Town Renewables", "industry": "Energy", "phone": "+27 21 555 0134", "email": "projects@capetownrenewables.co.za", "contact_person": "Thabo Molefe", "status": "prospect"},
]

ALL_COMPANIES = UK_COMPANIES + US_COMPANIES + EU_COMPANIES + OTHER_COMPANIES

# Status distribution: 35 active, 25 prospect, 25 lead, 15 inactive
STATUS_SEQUENCE = (
    ["active"] * 35 + ["prospect"] * 25 + ["lead"] * 25 + ["inactive"] * 15
)

INDUSTRIES = [
    "Technology", "Manufacturing", "Financial Services", "Healthcare", "Legal Services",
    "Transport & Logistics", "Real Estate", "Hospitality", "Agriculture", "Engineering",
    "Marketing", "Management Consulting", "Education", "Retail", "Energy",
    "Telecom", "Pharma", "Construction", "Media", "Insurance",
    "Environmental Services", "Food & Beverage", "Automotive", "Mining",
    "Aerospace", "Defence", "Human Resources", "Import/Export", "Maritime",
]

# ---------------------------------------------------------------------------
# Contact templates
# ---------------------------------------------------------------------------

CONTACT_TEMPLATES = {
    "email": [
        {"notes": "Sent introductory email about our services to {person}.", "outcome": "No reply yet — will follow up in two weeks"},
        {"notes": "Emailed updated pricing proposal to {person} at {company}.", "outcome": "{person} acknowledged receipt, under review"},
        {"notes": "Sent case studies and portfolio to {person}.", "outcome": "Forwarded to decision-making team"},
        {"notes": "Follow-up email to {person} on previous conversation.", "outcome": "Requested more details on implementation"},
        {"notes": "Sent quarterly newsletter to {person}.", "outcome": "Opened and clicked through to services page"},
        {"notes": "Responded to inbound enquiry from {person} at {company}.", "outcome": "Sent detailed service overview"},
        {"notes": "Emailed contract draft to {person} for review.", "outcome": "Under legal review, response expected next week"},
        {"notes": "Sent meeting summary and action items to {person}.", "outcome": "{person} confirmed receipt and next steps"},
        {"notes": "Shared industry report with {person} as discussed.", "outcome": "Appreciated — wants to discuss findings"},
        {"notes": "Cold email introducing consultancy services to {person}.", "outcome": "Auto-reply — out of office until next week"},
    ],
    "phone": [
        {"notes": "Exploratory call with {person} about potential engagement.", "outcome": "Interested but busy — call back next month"},
        {"notes": "Follow-up call to {person} on sent proposal.", "outcome": "Positive feedback, scheduling next meeting"},
        {"notes": "Cold call to {company} reception about our services.", "outcome": "Gatekeeper took message for {person}"},
        {"notes": "Discussed project timeline and deliverables with {person}.", "outcome": "Agreed on key milestones"},
        {"notes": "Called {person} to check on contract status.", "outcome": "Awaiting board approval, decision next week"},
        {"notes": "Quick call with {person} about upcoming requirements.", "outcome": "Wants formal proposal by end of month"},
        {"notes": "Year-end check-in call with {person} at {company}.", "outcome": "Reviewing budget for next year — follow up in January"},
        {"notes": "Weekly check-in with {person} — project on track.", "outcome": "Next deliverable due in two weeks"},
    ],
    "meeting": [
        {"notes": "Initial consultation at {company} offices.", "outcome": "Strong interest in full service package"},
        {"notes": "Site visit at {company} to assess current processes.", "outcome": "Identified key improvement areas"},
        {"notes": "Board presentation on proposed engagement.", "outcome": "Board approved budget — proceeding to contract"},
        {"notes": "Strategy workshop with {person} and team.", "outcome": "Defined scope and timeline for pilot project"},
        {"notes": "Coffee meeting with {person} to discuss partnership.", "outcome": "Agreed to formal proposal stage"},
        {"notes": "Quarterly review meeting with {person}.", "outcome": "On track — discussing extension of engagement"},
    ],
}

FOLLOWUP_TEMPLATES = [
    "Follow up on email to {person}",
    "Send proposal to {person} at {company}",
    "Chase {person} on contract status",
    "Schedule meeting with {person}",
    "Prepare presentation materials for {company}",
    "Send case studies to {person}",
    "Call {person} about project timeline",
    "Review deliverables for {company}",
    "Send pricing update to {person}",
    "Arrange site visit at {company}",
    "Prepare quarterly review for {person}",
    "Follow up on board decision at {company}",
    "Draft engagement terms for {person}",
    "Send project update to {person}",
    "Check in with {person} on progress",
    "Prepare kick-off materials for {company}",
    "Follow up on referral from {person}",
    "Send contract amendments to {person}",
    "Discuss budget allocation with {person}",
    "Year-end review with {person} at {company}",
]

# ---------------------------------------------------------------------------
# Address templates by region
# ---------------------------------------------------------------------------

UK_ADDRESSES = [
    "14 Temple Row, Birmingham B2 5JR",
    "Unit 7, MediaCity, Salford M50 2HE",
    "Brightwell Works, Aston Road, Birmingham B6 4RJ",
    "3rd Floor, 25 Canada Square, London E14 5LQ",
    "Redcastle House, Princess Street, Manchester M1 4HB",
    "47 Queen Street, Edinburgh EH2 3NH",
    "12 Park Place, Cardiff CF10 3DQ",
    "Suite 3, Victoria House, Leeds LS1 5AB",
    "8 Broad Street, Bristol BS1 2HG",
    "Unit 15, Innovation Park, Cambridge CB4 0DS",
    "6 Waterloo Street, Glasgow G2 6AY",
    "The Gatehouse, 1 Castle Street, Nottingham NG1 6AA",
    "22 High Street, Guildford GU1 3EL",
    "10 Albert Dock, Liverpool L3 4AF",
    "5 Deansgate, Manchester M3 4EN",
]

US_ADDRESSES = [
    "100 Market Street, Suite 300, San Francisco, CA 94105",
    "233 S Wacker Drive, Floor 42, Chicago, IL 60606",
    "1 World Trade Center, Suite 8500, New York, NY 10007",
    "1600 Amphitheatre Parkway, Mountain View, CA 94043",
    "200 Congress Avenue, Suite 1400, Austin, TX 78701",
    "500 Boylston Street, Boston, MA 02116",
    "1000 Wilshire Blvd, Suite 1500, Los Angeles, CA 90017",
    "2000 Pennsylvania Avenue NW, Washington, DC 20006",
]

EU_ADDRESSES = [
    "Maximilianstraße 35, 80539 München, Germany",
    "12 Rue de la Paix, 75002 Paris, France",
    "Keizersgracht 555, 1017 DR Amsterdam, Netherlands",
    "Paseo de la Castellana 89, 28046 Madrid, Spain",
    "Via Monte Napoleone 8, 20121 Milano, Italy",
    "Friedrichstraße 43-45, 10117 Berlin, Germany",
    "23 Avenue des Champs-Élysées, 75008 Paris, France",
    "Herengracht 182, 1016 BR Amsterdam, Netherlands",
]

OTHER_ADDRESSES = [
    "Level 12, 1 Macquarie Place, Sydney NSW 2000, Australia",
    "Marunouchi 1-9-1, Chiyoda-ku, Tokyo 100-0005, Japan",
    "Dubai Internet City, Building 1, Dubai, UAE",
    "200 Bay Street, Suite 3000, Toronto, ON M5J 2J1, Canada",
    "Bandra Kurla Complex, Mumbai 400051, India",
    "Gangnam-gu, Teheran-ro 521, Seoul 06164, South Korea",
]

LINKEDIN_TEMPLATES = [
    "https://linkedin.com/company/{slug}",
]

TWITTER_TEMPLATES = [
    "https://x.com/{slug}",
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _company_slug(company_name):
    """Convert company name to URL slug."""
    slug = company_name.lower()
    for ch in "&.,/'":
        slug = slug.replace(ch, "")
    return slug.replace(" ", "-").replace("--", "-").strip("-")


def _random_date_in_range(start, end):
    """Return a random date between start and end (inclusive)."""
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(0, delta)))


def _random_time():
    """Return a random business-hours time (9:00-16:00)."""
    hour = random.randint(9, 16)
    minute = random.choice([0, 15, 30, 45])
    return time(hour, minute)


def generate_interactions_for_company(company_obj, company_data, today):
    """Generate interaction records for a single company."""
    status = company_data["status"]
    person = company_data["contact_person"]
    company = company_data["company_name"]

    count_map = {"active": (5, 7), "prospect": (4, 6), "lead": (3, 4), "inactive": (2, 3)}
    lo, hi = count_map.get(status, (3, 4))
    n = random.randint(lo, hi)

    # Date range: April 2025 – March 2026
    start_date = date(2025, 4, 1)
    end_date = date(2026, 3, 31)

    interactions = []
    for _ in range(n):
        # Type mix: ~40% email, 35% phone, 25% meeting
        r = random.random()
        if r < 0.40:
            ctype = "email"
        elif r < 0.75:
            ctype = "phone"
        else:
            ctype = "meeting"

        template = random.choice(CONTACT_TEMPLATES[ctype])
        notes = template["notes"].format(person=person, company=company)
        outcome = template["outcome"].format(person=person, company=company)

        interaction_date = _random_date_in_range(start_date, end_date)
        interaction_time = _random_time() if ctype in ("phone", "meeting") else None

        c = Interaction(
            company_id=company_obj.id,
            user_id=company_obj.user_id,
            date=interaction_date,
            time=interaction_time,
            interaction_type=ctype,
            notes=notes,
            outcome=outcome,
        )
        interactions.append(c)

    return interactions


def generate_followups_for_company(company_obj, company_data, today):
    """Generate follow-up records for a single company."""
    status = company_data["status"]
    person = company_data["contact_person"]
    company = company_data["company_name"]

    count_map = {"active": (5, 7), "prospect": (4, 6), "lead": (3, 5), "inactive": (2, 3)}
    lo, hi = count_map.get(status, (3, 4))
    n = random.randint(lo, hi)

    # Date range: Oct 2025 – Dec 2026, weighted toward current quarter
    start_date = date(2025, 10, 1)
    end_date = date(2026, 12, 31)

    # Weight toward current quarter: 50% within ±45 days of today, 50% spread
    followups = []
    for _ in range(n):
        if random.random() < 0.5:
            # Near current date
            near_start = today - timedelta(days=45)
            near_end = today + timedelta(days=45)
            if near_start < start_date:
                near_start = start_date
            if near_end > end_date:
                near_end = end_date
            due = _random_date_in_range(near_start, near_end)
        else:
            due = _random_date_in_range(start_date, end_date)

        completed = due < today

        # Priority: 25% high, 45% medium, 30% low
        r = random.random()
        if r < 0.25:
            priority = "high"
        elif r < 0.70:
            priority = "medium"
        else:
            priority = "low"

        template = random.choice(FOLLOWUP_TEMPLATES)
        notes = template.format(person=person, company=company)

        # ~40% get a due_time
        due_time = _random_time() if random.random() < 0.4 else None

        fu = FollowUp(
            company_id=company_obj.id,
            user_id=company_obj.user_id,
            due_date=due,
            due_time=due_time,
            priority=priority,
            notes=notes,
            completed=completed,
        )
        followups.append(fu)

    return followups


def generate_custom_fields_for_company(company_obj, company_data, idx, custom_field_defs):
    """Generate custom field values for a single company."""
    values = []
    addr_def = custom_field_defs[0]     # Address
    linkedin_def = custom_field_defs[1]  # LinkedIn
    twitter_def = custom_field_defs[2]   # Twitter / X

    slug = _company_slug(company_data["company_name"])

    # Determine region
    if idx < 40:
        region = "uk"
    elif idx < 65:
        region = "us"
    elif idx < 90:
        region = "eu"
    else:
        region = "other"

    # ~40% get address
    if random.random() < 0.40:
        if region == "uk":
            addr = random.choice(UK_ADDRESSES)
        elif region == "us":
            addr = random.choice(US_ADDRESSES)
        elif region == "eu":
            addr = random.choice(EU_ADDRESSES)
        else:
            addr = random.choice(OTHER_ADDRESSES)
        values.append(CustomFieldValue(
            definition_id=addr_def.id, company_id=company_obj.id, value=addr
        ))

    # ~25% get LinkedIn
    if random.random() < 0.25:
        values.append(CustomFieldValue(
            definition_id=linkedin_def.id,
            company_id=company_obj.id,
            value=f"https://linkedin.com/company/{slug}",
        ))

    # ~15% get Twitter/X
    if random.random() < 0.15:
        values.append(CustomFieldValue(
            definition_id=twitter_def.id,
            company_id=company_obj.id,
            value=f"https://x.com/{slug}",
        ))

    return values


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------

def seed():
    random.seed(42)

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
        Interaction.query.delete()
        Contact.query.delete()
        Company.query.delete()
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

        # --- Companies (100 total) ---
        # User assignment: admin=30, manager1=30, user1=25, user2=15
        user_assignment = (
            [users[0]] * 30 + [users[1]] * 30 + [users[2]] * 25 + [users[3]] * 15
        )

        # Shuffle status sequence with fixed seed (already seeded)
        statuses = STATUS_SEQUENCE[:]
        random.shuffle(statuses)

        today = date.today()
        companies = []
        all_interactions = []
        all_followups = []
        all_custom_values = []

        for idx, company_data in enumerate(ALL_COMPANIES):
            # Override status with balanced distribution
            data = dict(company_data)
            data["status"] = statuses[idx]

            company = Company(
                company_name=data["company_name"],
                industry=data["industry"],
                phone=data["phone"],
                email=data["email"],
                contact_person=data["contact_person"],
                status=data["status"],
                user_id=user_assignment[idx].id,
            )
            db.session.add(company)
            db.session.flush()
            companies.append(company)

            # Generate interactions
            interactions = generate_interactions_for_company(company, data, today)
            all_interactions.extend(interactions)

            # Generate follow-ups
            followups = generate_followups_for_company(company, data, today)
            all_followups.extend(followups)

            # Generate custom field values
            custom_values = generate_custom_fields_for_company(company, data, idx, custom_field_defs)
            all_custom_values.extend(custom_values)

        db.session.add_all(all_interactions)
        db.session.add_all(all_followups)
        db.session.add_all(all_custom_values)
        db.session.commit()

        # ── Create Contact (person) records from contact_person data ──
        companies = Company.query.all()
        for company in companies:
            if company.contact_person:
                parts = company.contact_person.strip().split(" ", 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ""
                contact = Contact(
                    first_name=first_name,
                    last_name=last_name,
                    email=company.email,
                    phone=company.phone,
                    company_id=company.id,
                    is_primary=True,
                    user_id=company.user_id,
                )
                db.session.add(contact)
        db.session.commit()

        contact_count = Contact.query.count()
        print(
            f"Seeded {len(users)} users, {len(companies)} companies, "
            f"{len(all_interactions)} interactions, {len(all_followups)} follow-ups, "
            f"{contact_count} contacts, "
            f"{len(all_custom_values)} custom field values, "
            f"{len(attachment_cats)} attachment categories, "
            f"{len(attachment_tags)} attachment tags."
        )


if __name__ == "__main__":
    seed()
