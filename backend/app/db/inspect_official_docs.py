import os
import re
import json
from pypdf import PdfReader

DOCS_DIR = r"docs\official_documents"
OUTPUT_JSON = r"docs\document_inventory.json"
OUTPUT_MD = r"docs\document_inventory.md"

def extract_doc_data():
    files = sorted([f for f in os.listdir(DOCS_DIR) if f.endswith(".pdf")])
    unique_files = []
    seen_sizes = set()
    for f in files:
        path = os.path.join(DOCS_DIR, f)
        size = os.path.getsize(path)
        base_name = re.sub(r"\s*\(\d+\)", "", f)
        key = (base_name, size)
        if key in seen_sizes:
            continue
        seen_sizes.add(key)
        unique_files.append(f)

    inventory = []

    for f in unique_files:
        path = os.path.join(DOCS_DIR, f)
        reader = PdfReader(path)
        num_pages = len(reader.pages)
        meta = reader.metadata
        title = meta.title if meta else ""
        
        # Extract full text up to 50 pages or sample
        pages_text = []
        full_text = ""
        for i in range(min(num_pages, 50)):
            try:
                t = reader.pages[i].extract_text() or ""
                pages_text.append(t)
                full_text += f"\n--- PAGE {i+1} ---\n" + t
            except Exception as ex:
                pages_text.append(f"[Error: {ex}]")

        # Basic analysis
        issuer = "Unknown"
        if "idfc" in full_text.lower():
            issuer = "IDFC FIRST Bank"
        elif "au small finance" in full_text.lower() or "aubank" in full_text.lower():
            issuer = "AU Small Finance Bank"
        elif "hdfc" in full_text.lower():
            issuer = "HDFC Bank"
        elif "rbl" in full_text.lower():
            issuer = "RBL Bank"
        elif "icici" in full_text.lower():
            issuer = "ICICI Bank"
        elif "indusind" in full_text.lower():
            issuer = "IndusInd Bank"
        elif "yes bank" in full_text.lower():
            issuer = "YES Bank"

        doc_type = "Terms / MITC"
        if "schedule of charges" in full_text.lower() or "cardschedulecharges" in f.lower():
            doc_type = "Schedule of Charges"
        elif "lounge" in f.lower() or "lounge" in full_text[:1000].lower():
            doc_type = "Lounge Access Directory & Terms"
        elif "travel" in f.lower() or "travel & shop" in full_text.lower():
            doc_type = "Travel & Shop Platform Offer Terms"
        elif "joining" in f.lower() or "welcome" in full_text[:1000].lower():
            doc_type = "Welcome / Joining Offers"
        elif "privileges" in f.lower():
            doc_type = "Card Privileges & Feature Guide"

        # Check versions and dates
        versions = re.findall(r"(?:version|ver\.|v)[\s:]*([0-9\.]+)", full_text[:4000], re.IGNORECASE)
        dates = re.findall(r"(?:effective|updated|date|w\.e\.f\.?|revised)\s*[:\-]?\s*([0-9]{1,2}[th|st|nd|rd\s\-\/\.]+[A-Za-z]+[,\s\-]+[0-9]{4}|[0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{2,4})", full_text[:4000], re.IGNORECASE)

        # Check card mentions
        cards_mentioned = []
        card_keywords = [
            "lic first select", "lic select", "lit", "shoprite", "lazypay", 
            "coral", "amazon pay", "ace", "prosperity", "millennia", "regalia",
            "infinia", "moneyback", "platinum", "legend", "nexxt", "tiger",
            "zenith", "vetta", "altura", "aurum"
        ]
        for ck in card_keywords:
            if re.search(r"\b" + re.escape(ck) + r"\b", full_text, re.IGNORECASE):
                cards_mentioned.append(ck)

        item = {
            "filename": f,
            "filepath": path,
            "filesize_bytes": os.path.getsize(path),
            "num_pages": num_pages,
            "metadata_title": title,
            "issuer": issuer,
            "doc_type": doc_type,
            "versions_found": list(set(versions))[:3],
            "dates_found": list(set(dates))[:5],
            "cards_mentioned": list(set(cards_mentioned)),
            "first_page_preview": pages_text[0][:1500] if pages_text else "",
        }
        inventory.append(item)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
        json.dump(inventory, jf, indent=2, ensure_ascii=False)

    with open(OUTPUT_MD, "w", encoding="utf-8") as mf:
        mf.write("# Official Document Inventory & Analysis\n\n")
        for item in inventory:
            mf.write(f"## {item['filename']}\n")
            mf.write(f"- **Issuer:** {item['issuer']}\n")
            mf.write(f"- **Document Type:** {item['doc_type']}\n")
            mf.write(f"- **Pages:** {item['num_pages']}\n")
            mf.write(f"- **Metadata Title:** {item['metadata_title']}\n")
            mf.write(f"- **Versions Found:** {', '.join(item['versions_found']) or 'None'}\n")
            mf.write(f"- **Dates Detected:** {', '.join(item['dates_found']) or 'None'}\n")
            mf.write(f"- **Card Variants Mentioned:** {', '.join(item['cards_mentioned']) or 'General / None specifically named'}\n")
            mf.write("\n### First Page Preview:\n```text\n")
            mf.write(item['first_page_preview'][:1000].replace("```", "'''"))
            mf.write("\n```\n\n---\n\n")

    print(f"Generated {OUTPUT_JSON} and {OUTPUT_MD} successfully.")

if __name__ == "__main__":
    extract_doc_data()
