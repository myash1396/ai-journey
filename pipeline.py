import os
from datetime import datetime
from tools.ba_agent import analyze_brd
from tools.tech_lead_agent import design_from_ba
from tools.developer_agent import create_implementation
from tools.reviewer_agent import review_implementation

MAX_REVIEW_ITERATIONS = 2  # max times developer can revise

def word_count(text: str) -> int:
    return len(text.split()) if text else 0

def get_latest_file(prefix: str, ext: str = ".md") -> str:
    outputs_dir = "outputs"
    files = [f for f in os.listdir(outputs_dir) 
             if f.startswith(prefix) and f.endswith(ext)]
    files.sort(reverse=True)
    return os.path.join(outputs_dir, files[0]) if files else None

def run_pipeline(brd_file: str):
    print(f"\n{'='*60}")
    print("🚀 MULTI AGENT PIPELINE - FULL RUN")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    start_time = datetime.now()

    # ─── STEP 1: READ BRD ───
    print("📄 Reading BRD document...")
    with open(brd_file, "r", encoding="utf-8") as f:
        brd_content = f.read()
    print(f"✅ BRD loaded: {word_count(brd_content)} words\n")

    # ─── STEP 2: BA AGENT ───
    print(f"{'='*60}")
    print("🤖 AGENT 1: Senior BA Agent")
    print(f"{'='*60}")
    agent1_start = datetime.now()

    ba_output = analyze_brd(brd_content)

    agent1_time = (datetime.now() - agent1_start).seconds
    ba_words = word_count(ba_output)
    print(f"\n✅ BA Agent complete")
    print(f"   Words generated: {ba_words}")
    print(f"   Time taken: {agent1_time}s")

    # Check latest saved file
    latest_ba = get_latest_file("ba_analysis_")
    if latest_ba:
        with open(latest_ba, "r", encoding="utf-8") as f:
            saved_words = word_count(f.read())
        print(f"   Saved file: {os.path.basename(latest_ba)} ({saved_words} words)")

    # ─── STEP 3: TECH LEAD AGENT ───
    print(f"\n{'='*60}")
    print("🏗️ AGENT 2: Tech Lead Agent")
    print(f"{'='*60}")
    agent2_start = datetime.now()

    tech_output = design_from_ba(ba_output)

    agent2_time = (datetime.now() - agent2_start).seconds
    tech_words = word_count(tech_output)
    print(f"\n✅ Tech Lead Agent complete")
    print(f"   Words generated: {tech_words}")
    print(f"   Time taken: {agent2_time}s")

    latest_tl = get_latest_file("tech_lead_analysis_")
    if latest_tl:
        with open(latest_tl, "r", encoding="utf-8") as f:
            saved_words = word_count(f.read())
        print(f"   Saved file: {os.path.basename(latest_tl)} ({saved_words} words)")

    # ─── STEP 4: DEVELOPER + REVIEWER LOOP ───
    print(f"\n{'='*60}")
    print("💻 AGENT 3: Developer Agent")
    print(f"{'='*60}")

    current_dev_output = None
    verdict = None
    iteration = 0

    while iteration < MAX_REVIEW_ITERATIONS:
        iteration += 1
        print(f"\n--- Developer Iteration {iteration} ---")
        agent3_start = datetime.now()

        # Developer runs on tech output (first time) or with feedback (subsequent)
        if iteration == 1:
            dev_input = tech_output
        else:
            # Pass tech output + review feedback for revision
            dev_input = f"{tech_output}\n\n---REVIEWER FEEDBACK---\n{current_review_output}"

        current_dev_output = create_implementation(dev_input)

        agent3_time = (datetime.now() - agent3_start).seconds
        dev_words = word_count(current_dev_output)
        print(f"\n✅ Developer iteration {iteration} complete")
        print(f"   Words generated: {dev_words}")
        print(f"   Time taken: {agent3_time}s")

        # ─── REVIEWER ───
        print(f"\n{'='*60}")
        print(f"🔍 AGENT 4: Reviewer Agent (iteration {iteration})")
        print(f"{'='*60}")
        agent4_start = datetime.now()

        current_review_output = review_implementation(current_dev_output)

        agent4_time = (datetime.now() - agent4_start).seconds
        review_words = word_count(current_review_output)
        print(f"\n✅ Reviewer iteration {iteration} complete")
        print(f"   Words generated: {review_words}")
        print(f"   Time taken: {agent4_time}s")

        latest_review = get_latest_file("review_report_")
        if latest_review:
            with open(latest_review, "r", encoding="utf-8") as f:
                saved_words = word_count(f.read())
            print(f"   Saved file: {os.path.basename(latest_review)} ({saved_words} words)")

        # Check verdict
        if "VERDICT: APPROVED" in current_review_output:
            verdict = "APPROVED"
            print(f"\n🎉 VERDICT: APPROVED after {iteration} iteration(s)")
            break
        elif "VERDICT: REVISION NEEDED" in current_review_output:
            verdict = "REVISION NEEDED"
            print(f"\n⚠️ VERDICT: REVISION NEEDED - iteration {iteration}")
            if iteration < MAX_REVIEW_ITERATIONS:
                print(f"   Sending back to Developer for revision...")
            else:
                print(f"   Max iterations reached. Stopping pipeline.")

    # ─── PIPELINE SUMMARY ───
    total_time = (datetime.now() - start_time).seconds
    print(f"\n{'='*60}")
    print("📊 PIPELINE SUMMARY")
    print(f"{'='*60}")
    print(f"BRD Input:        {word_count(brd_content)} words")
    print(f"BA Output:        {ba_words} words")
    print(f"Tech Lead Output: {tech_words} words")
    print(f"Developer Output: {word_count(current_dev_output)} words")
    print(f"Review Output:    {word_count(current_review_output)} words")
    print(f"Iterations:       {iteration}")
    print(f"Final Verdict:    {verdict}")
    print(f"Total Time:       {total_time}s")
    print(f"\n📁 All outputs saved to outputs/ folder")
    print(f"{'='*60}\n")

    return {
        "ba_output": ba_output,
        "tech_output": tech_output,
        "dev_output": current_dev_output,
        "review_output": current_review_output,
        "verdict": verdict,
        "iterations": iteration
    }

if __name__ == "__main__":
    brd_file = os.path.join("docs", "mini_brd.txt")
    run_pipeline(brd_file)