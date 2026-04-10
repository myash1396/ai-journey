import os
from datetime import datetime
from tools.ba_agent import analyze_brd
from tools.tech_lead_agent import design_from_ba

def run_pipeline(brd_file: str):
    print(f"\n{'='*60}")
    print("🚀 MULTI AGENT PIPELINE STARTING")
    print(f"{'='*60}\n")

    # ─── STEP 1: READ BRD ───
    print("📄 Reading BRD document...")
    with open(brd_file, "r", encoding="utf-8") as f:
        brd_content = f.read()
    print(f"✅ BRD loaded: {len(brd_content.split())} words\n")

    # ─── STEP 2: BA AGENT ───
    print(f"{'='*60}")
    print("🤖 AGENT 1: Senior BA Agent analyzing BRD...")
    print(f"{'='*60}\n")

    ba_output = analyze_brd(brd_content)

    print(f"\n✅ BA Analysis complete — {len(ba_output.split())} words generated")

    # ─── STEP 3: TECH LEAD AGENT ───
    print(f"\n{'='*60}")
    print("🏗️ AGENT 2: Tech Lead Agent designing solution...")
    print(f"{'='*60}\n")

    tech_output = design_from_ba(ba_output)

    print(f"\n✅ Technical Design complete — {len(tech_output.split())} words generated")

    # ─── PIPELINE COMPLETE ───
    print(f"\n{'='*60}")
    print("✅ PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"📁 Check outputs/ folder for:")
    print(f"   - ba_analysis_[timestamp].md")
    print(f"   - tech_lead_analysis_[timestamp].md")
    print(f"{'='*60}\n")

    return ba_output, tech_output

if __name__ == "__main__":
    brd_file = os.path.join("docs", "mini_brd.txt")
    run_pipeline(brd_file)