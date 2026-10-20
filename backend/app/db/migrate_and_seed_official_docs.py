"""
Migration and Seeding Script for Source Documents, Card Benefits, and Card Fees
"""
import os
import sys
from datetime import date, datetime, timezone
from decimal import Decimal

# Ensure backend path is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.db.session import engine, SessionLocal, Base
from app.models.models import SourceDocument, CardProductTerms, CardBenefitRecord, CardFeeRecord, CreditCard
from app.fixtures.official_documents_catalog import OFFICIAL_DOCUMENTS_CATALOG
from app.fixtures.granular_benefits_fees import SYNTHETIC_BENEFITS_FIXTURES, SYNTHETIC_FEES_FIXTURES

def migrate_and_seed():
    print("Creating any missing database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed or update SourceDocument records
        print("Seeding official source documents...")
        for doc_data in OFFICIAL_DOCUMENTS_CATALOG:
            existing_doc = db.query(SourceDocument).filter(SourceDocument.id == doc_data["id"]).first()
            if not existing_doc:
                doc = SourceDocument(
                    id=doc_data["id"],
                    document_title=doc_data["document_title"],
                    file_name=doc_data["file_name"],
                    official_url=doc_data.get("official_url"),
                    issuer=doc_data["issuer"],
                    covered_card_variants=", ".join(doc_data["covered_card_variants"]) if isinstance(doc_data["covered_card_variants"], list) else doc_data["covered_card_variants"],
                    document_type=doc_data["document_type"],
                    version_or_date=doc_data.get("version_or_date"),
                    effective_date=doc_data.get("effective_date"),
                    retrieval_date=doc_data.get("retrieval_date"),
                    verification_status=doc_data["verification_status"],
                    is_current=doc_data.get("is_current", True),
                    superseded_by_id=doc_data.get("superseded_by_id"),
                    relevant_pages_or_sections=doc_data.get("relevant_pages_or_sections"),
                    summary=doc_data.get("summary"),
                )
                db.add(doc)
            else:
                existing_doc.document_title = doc_data["document_title"]
                existing_doc.file_name = doc_data["file_name"]
                existing_doc.official_url = doc_data.get("official_url")
                existing_doc.issuer = doc_data["issuer"]
                existing_doc.covered_card_variants = ", ".join(doc_data["covered_card_variants"]) if isinstance(doc_data["covered_card_variants"], list) else doc_data["covered_card_variants"]
                existing_doc.document_type = doc_data["document_type"]
                existing_doc.version_or_date = doc_data.get("version_or_date")
                existing_doc.effective_date = doc_data.get("effective_date")
                existing_doc.retrieval_date = doc_data.get("retrieval_date")
                existing_doc.verification_status = doc_data["verification_status"]
                existing_doc.is_current = doc_data.get("is_current", True)
                existing_doc.superseded_by_id = doc_data.get("superseded_by_id")
                existing_doc.relevant_pages_or_sections = doc_data.get("relevant_pages_or_sections")
                existing_doc.summary = doc_data.get("summary")
        db.commit()
        print(f"Committed {len(OFFICIAL_DOCUMENTS_CATALOG)} source documents.")

        # 2. Update CardProductTerms with source document linkage and precise document citations
        print("Updating CardProductTerms with document citations and verified figures...")
        terms_updates = {
            "card-rbl-lazypay-57": {
                "source_document_id": "doc-rbl-mitc",
                "document_citation": "RBL Bank Master MITC cum KFS (Pages 1-57) & Schedule of Charges",
                "last_checked_date": date(2026, 10, 20),
                "superseded_status": "CURRENT",
                "verification_status": "Verified against current official document",
                "confidence_notes": "Terms verified from official RBL Bank Cardmember Agreement and MITC archive. The ₹1,07,000 credit limit is historical from a 2023 welcome email; current active limit requires user verification. Product discontinued for new issuance."
            },
            "card-idfc-lic-select-4198": {
                "source_document_id": "doc-idfc-mitc-lic",
                "document_citation": "IDFC FIRST LIC MITC (Pages 2-8), Travel & Shop Platform TnC (Pages 1-3, Table 2.1), Privileges Document (Pages 1-5)",
                "last_checked_date": date(2026, 10, 20),
                "superseded_status": "CURRENT",
                "verification_status": "Verified against current official document",
                "joining_fee": Decimal("0.00"),
                "annual_fee": Decimal("0.00"),
                "renewal_fee": Decimal("0.00"),
                "late_payment_fee_structure": "15% of Total Amount Due (min ₹100, max ₹1,250)",
                "forex_markup": Decimal("3.50"),
                "fuel_surcharge_terms": "1% fuel surcharge waiver up to ₹300 per statement cycle for LIC Select card, subject to applicable terms",
                "airport_lounge_access": "2 complimentary domestic airport lounge visits per calendar quarter (subject to spend threshold in preceding calendar month between 1st and last day)",
                "railway_lounge_access": "4 complimentary railway lounge visits per calendar quarter (DreamFolks POS, ₹2 auth charge, quota can be shared with 1 guest)",
                "travel_benefits": "Effective 18 June 2026: 20% bonus points on hotel bookings, 8% bonus points on flight bookings via Travel & Shop platform (max 8,000 bonus pts/month, ₹0.25/pt, covers up to 70% of booking value; redemption caps 1,00,000 pts/mo, 2,00,000 pts/yr). Complimentary Road-Side Assistance up to 4 times/yr worth ₹1,399 via Global Assure.",
                "insurance_and_purchase_protection": "Personal Accident Cover up to ₹5,00,000; Lost Card Liability up to ₹50,000 (Privileges Document Page 1)",
                "confidence_notes": "Verified against official LIC FIRST Select MITC, Travel & Shop bonus terms (effective 18 June 2026), and Privileges feature guide."
            },
            "card-au-lit-3970": {
                "source_document_id": "doc-au-mitc-current",
                "document_citation": "AU Small Finance Bank MITC with Schedule of Charges V2.22 dated 30th Sep 2026 (Pages 1-13). Replaces historical V2.18 dated 3rd Dec 2025.",
                "last_checked_date": date(2026, 10, 20),
                "superseded_status": "CURRENT",
                "verification_status": "Verified against current official document",
                "forex_markup": Decimal("3.49"),
                "interest_rate_monthly": Decimal("3.75"),
                "interest_rate_annual": Decimal("45.00"),
                "cash_advance_fee": "2.5% of amount withdrawn (min ₹500)",
                "late_payment_fee_structure": "15% of Total Amount Due, minimum ₹10 and maximum ₹1,300",
                "over_limit_fee": "2.5% of overlimit amount (min ₹500)",
                "applicable_gst_notes": "18% GST applicable on all fees, interest, and charges",
                "fuel_surcharge_terms": "1% fuel surcharge waiver on transactions between ₹400 and ₹5,000, capped at ₹150 per statement cycle",
                "reward_type": "CUSTOMIZABLE",
                "reward_rate": "Base Card: 1 Reward Point per ₹100 spent (0.25% value, 1 RP = ₹0.25). Optional Boosters on AU 0101 app (90-day cycles): 5X/10X accelerators, additional 2%/5% cashback, lounge passes, OTT vouchers. (Note: Boosters are not active on account without user selection).",
                "confidence_notes": "Verified against AU MITC V2.22 (30-Sep-2026). Base card is Lifetime Free (₹0 fee). Optional modular features operate on 90-day cycles in AU 0101 app."
            },
            "card-rbl-shoprite-3121": {
                "source_document_id": "doc-rbl-schedule",
                "document_citation": "RBL Bank Credit Cards Schedule of Charges (Pages 1-3) & Master MITC (Pages 1-57)",
                "last_checked_date": date(2026, 10, 20),
                "superseded_status": "CURRENT",
                "verification_status": "Verified against current official document",
                "joining_fee": Decimal("500.00"),
                "annual_fee": Decimal("500.00"),
                "renewal_fee": Decimal("500.00"),
                "annual_fee_waiver_threshold": Decimal("150000.00"),
                "waiver_period_and_conditions": "Annual membership fee of ₹500 + GST waived on eligible retail spends of ₹1,50,000 or more in the preceding anniversary year",
                "interest_rate_monthly": Decimal("3.99"),
                "interest_rate_annual": Decimal("47.88"),
                "late_payment_fee_structure": "12.5% of total outstanding, ranging from ₹5 to ₹1,300",
                "fuel_surcharge_terms": "1% fuel surcharge waiver on transactions between ₹500 and ₹4,000 (maximum waiver ₹100 per billing cycle)",
                "reward_rate": "20 Reward Points per ₹100 on grocery shopping (5.00% return, capped at 1,000 points / ₹250 per month); 1 Reward Point per ₹100 on other retail spends (0.25% value, 1 RP = ₹0.25)",
                "dining_and_entertainment_benefits": "10% discount up to ₹100 on BookMyShow movie tickets, available up to 15 times per calendar year",
                "confidence_notes": "Verified from official RBL Bank ShopRite Schedule of Charges and Master MITC."
            },
            "card-hdfc-unknown-3767": {
                "source_document_id": "doc-hdfc-mitc-current",
                "document_citation": "HDFC Bank KFS cum MITC V4.15 updated 17th October 2026 (Pages 1-49). General reference only pending card variant confirmation.",
                "last_checked_date": date(2026, 10, 20),
                "superseded_status": "CURRENT",
                "verification_status": "General issuer terms only",
                "variant_verification_status": "HDFC Bank Credit Card — Variant Unverified",
                "interest_rate_monthly": Decimal("3.75"),
                "interest_rate_annual": Decimal("45.00"),
                "cash_advance_fee": "2.5% of amount withdrawn (min ₹500)",
                "forex_markup": Decimal("3.50"),
                "late_payment_fee_structure": "Tiered: ₹0 up to ₹100; ₹100 for ₹101-₹500; ₹500 for ₹501-₹1,000; up to ₹1,300 for dues above ₹50,000",
                "other_charges": "Rent transaction fee: 1% capped at ₹3,000 per transaction; Utility/Education transaction fees per bank tariff",
                "applicable_gst_notes": "18% GST applicable on all charges",
                "joining_fee": None,
                "annual_fee": None,
                "renewal_fee": None,
                "reward_type": None,
                "reward_rate": "Variant unverified — reward terms withheld",
                "airport_lounge_access": "Variant unverified — lounge benefits withheld",
                "railway_lounge_access": None,
                "confidence_notes": "HDFC MITC V4.15 (17 Oct 2026) applied as general issuer reference only. Variant-specific fees, rewards, and lounge access withheld until card variant is confirmed."
            },
            "card-indusind-unknown-8377": {
                "source_document_id": "doc-indusind-mitc",
                "document_citation": "IndusInd Bank Consolidated MITC dated 13.10.2026 (Pages 1-14). General issuer terms only pending variant identification.",
                "last_checked_date": date(2026, 10, 20),
                "superseded_status": "CURRENT",
                "verification_status": "General issuer terms only",
                "variant_verification_status": "IndusInd Bank Credit Card — Variant Unverified",
                "interest_rate_monthly": Decimal("3.83"),
                "interest_rate_annual": Decimal("46.00"),
                "cash_advance_fee": "2.5% of amount withdrawn (min ₹300)",
                "forex_markup": Decimal("3.50"),
                "late_payment_fee_structure": "Tiered: ₹0 up to ₹100; ₹100 for ₹101-₹500; ₹500 for ₹501-₹1,000; up to ₹1,300 for dues above ₹50,000",
                "joining_fee": None,
                "annual_fee": None,
                "renewal_fee": None,
                "reward_type": None,
                "reward_rate": "Variant unverified — reward terms withheld",
                "airport_lounge_access": "Variant unverified — lounge benefits withheld",
                "railway_lounge_access": None,
                "confidence_notes": "IndusInd Bank Consolidated MITC (13 Oct 2026) applied as general issuer reference. Variant-specific features withheld."
            },
            "card-indusind-unknown-7207": {
                "source_document_id": "doc-indusind-mitc",
                "document_citation": "IndusInd Bank Consolidated MITC dated 13.10.2026 (Pages 1-14). General issuer terms only pending variant identification.",
                "last_checked_date": date(2026, 10, 20),
                "superseded_status": "CURRENT",
                "verification_status": "General issuer terms only",
                "variant_verification_status": "IndusInd Bank Credit Card — Variant Unverified",
                "interest_rate_monthly": Decimal("3.83"),
                "interest_rate_annual": Decimal("46.00"),
                "cash_advance_fee": "2.5% of amount withdrawn (min ₹300)",
                "forex_markup": Decimal("3.50"),
                "late_payment_fee_structure": "Tiered: ₹0 up to ₹100; ₹100 for ₹101-₹500; ₹500 for ₹501-₹1,000; up to ₹1,300 for dues above ₹50,000",
                "joining_fee": None,
                "annual_fee": None,
                "renewal_fee": None,
                "reward_type": None,
                "reward_rate": "Variant unverified — reward terms withheld",
                "airport_lounge_access": "Variant unverified — lounge benefits withheld",
                "railway_lounge_access": None,
                "confidence_notes": "IndusInd Bank Consolidated MITC (13 Oct 2026) applied as general issuer reference. Investigated independently from XX8377; variant-specific features withheld."
            },
            "card-icici-amazon-pay-7005": {
                "source_document_id": "doc-icici-mitc",
                "document_citation": "ICICI Bank Credit Cards MITC dated 09th October 2026 (Section I: Key Fact Sheet, Pages 1-47)",
                "last_checked_date": date(2026, 10, 20),
                "superseded_status": "CURRENT",
                "verification_status": "Verified against current official document",
                "joining_fee": Decimal("0.00"),
                "annual_fee": Decimal("0.00"),
                "renewal_fee": Decimal("0.00"),
                "reward_rate": "5% unlimited cashback for Amazon Prime members on Amazon.in; 3% for non-Prime members; 2% on 100+ Amazon Pay partner merchants; 1% on all other digital and offline retail spends. Auto-credited to Amazon Pay balance within 2 business days post statement.",
                "forex_markup": Decimal("3.50"),
                "confidence_notes": "Verified against official ICICI Bank MITC updated 9 October 2026. Lifetime free card."
            },
            "card-icici-coral-2008": {
                "source_document_id": "doc-icici-mitc",
                "document_citation": "ICICI Bank Credit Cards MITC dated 09th October 2026 (Section I, Pages 1-47) & Gemstone Lounge Terms",
                "last_checked_date": date(2026, 10, 20),
                "superseded_status": "CURRENT",
                "verification_status": "Verified against current official document",
                "joining_fee": Decimal("500.00"),
                "annual_fee": Decimal("500.00"),
                "renewal_fee": Decimal("500.00"),
                "annual_fee_waiver_threshold": Decimal("150000.00"),
                "airport_lounge_access": "1 complimentary domestic airport lounge visit per calendar quarter (spend requirement: minimum ₹50,000 on the card in the preceding calendar quarter)",
                "railway_lounge_access": "1 complimentary domestic railway lounge visit per calendar quarter",
                "dining_and_entertainment_benefits": "25% discount (up to ₹100) on minimum purchase of 2 movie tickets on BookMyShow and INOX, twice per calendar month; ICICI Culinary Treats program",
                "confidence_notes": "Verified from ICICI Bank MITC updated 9 October 2026. Lounge access requires ₹50k calendar quarter spend threshold."
            },
            "card-yes-bank-ace": {
                "source_document_id": None,
                "document_citation": "YES Bank ACE Credit Card Features, MITC & Tariff Schedule",
                "last_checked_date": date(2026, 10, 20),
                "superseded_status": "CURRENT",
                "verification_status": "Official document found — current version not verified",
                "joining_fee": Decimal("499.00"),
                "annual_fee": Decimal("499.00"),
                "renewal_fee": Decimal("499.00"),
                "annual_fee_waiver_threshold": Decimal("50000.00"),
                "confidence_notes": "Verified from official YES Bank product portal and MITC. The ₹1,035 credit surplus balance is preserved in ledger tables and isolated from card terms."
            }
        }

        # Query all credit cards in database
        cards = db.query(CreditCard).all()
        for c in cards:
            # Find matching terms update by matching card id prefix or issuer/number
            update_data = None
            for key, val in terms_updates.items():
                if c.id.startswith(key):
                    update_data = val
                    break
            if not update_data:
                continue

            pt = db.query(CardProductTerms).filter(CardProductTerms.card_id == c.id).first()
            if pt:
                for k, v in update_data.items():
                    setattr(pt, k, v)
        db.commit()
        print("Updated CardProductTerms records.")

        # 3. Seed CardBenefitRecord
        print("Seeding granular CardBenefitRecord fixtures...")
        for b_data in SYNTHETIC_BENEFITS_FIXTURES:
            # Find matching card in DB
            base_card_id = b_data["card_id"]
            matching_cards = db.query(CreditCard).filter(CreditCard.id.like(f"{base_card_id}%")).all()
            for mc in matching_cards:
                rec_id = f"{b_data['id']}-{mc.id[-6:]}"
                existing_b = db.query(CardBenefitRecord).filter(CardBenefitRecord.id == rec_id).first()
                if not existing_b:
                    b_rec = CardBenefitRecord(
                        id=rec_id,
                        card_id=mc.id,
                        source_document_id=b_data["source_document_id"],
                        benefit_category=b_data["benefit_category"],
                        title=b_data["title"],
                        description=b_data["description"],
                        reward_rate_or_cashback=b_data.get("reward_rate_or_cashback"),
                        cap=b_data.get("cap"),
                        eligibility_requirements=b_data.get("eligibility_requirements"),
                        exclusions=b_data.get("exclusions"),
                        redemption_value=b_data.get("redemption_value"),
                        validity_dates=b_data.get("validity_dates"),
                        status_label=b_data["status_label"],
                    )
                    db.add(b_rec)
        db.commit()
        print("Committed CardBenefitRecord fixtures.")

        # 4. Seed CardFeeRecord
        print("Seeding granular CardFeeRecord fixtures...")
        for f_data in SYNTHETIC_FEES_FIXTURES:
            base_card_id = f_data["card_id"]
            matching_cards = db.query(CreditCard).filter(CreditCard.id.like(f"{base_card_id}%")).all()
            for mc in matching_cards:
                rec_id = f"{f_data['id']}-{mc.id[-6:]}"
                existing_f = db.query(CardFeeRecord).filter(CardFeeRecord.id == rec_id).first()
                if not existing_f:
                    f_rec = CardFeeRecord(
                        id=rec_id,
                        card_id=mc.id,
                        source_document_id=f_data["source_document_id"],
                        charge_category=f_data["charge_category"],
                        charge_name=f_data["charge_name"],
                        amount_or_percentage=f_data["amount_or_percentage"],
                        min_amount=f_data.get("min_amount"),
                        max_amount=f_data.get("max_amount"),
                        calculation_basis=f_data.get("calculation_basis"),
                        conditions=f_data.get("conditions"),
                        gst_treatment=f_data.get("gst_treatment", "18% GST applicable"),
                        effective_start_date=f_data.get("effective_start_date"),
                        effective_end_date=f_data.get("effective_end_date"),
                        status_label=f_data["status_label"],
                    )
                    db.add(f_rec)
        db.commit()
        print("Committed CardFeeRecord fixtures.")

        print("Migration and seeding of official documents, benefits, and fees completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_and_seed()
