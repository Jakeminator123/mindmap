"""
Promethius small Business Case

• Streamlit mind-map with persistent JSON storage
• GPT-4.5-preview evaluation (quick & deep) logged in evaluations.json
• Extra founder context:
      – Jakob  = pro poker-player, Python & AI expert
      – Promethius Poker = established poker-community / training brand
• New heading “Description”

Works on both local machine (`streamlit run …`) and Render/Streamlit-Cloud.
"""

import os, json, re, datetime
from pathlib import Path

import streamlit as st
from streamlit_markmap import markmap
from openai import OpenAI

# ── CONFIG ────────────────────────────────────────────────────────────
HEADINGS = [
    "Description",                 # NEW
    "Complexity",
    "Competitors",
    "Synergy with Promethius",
    "Implementation Cost",
    "Risks",
]

DATA_DIR       = Path(__file__).with_name("data")
IDEA_PATH      = DATA_DIR / "ideas.json"
EVAL_PATH      = DATA_DIR / "evaluations.json"
MODEL_NAME     = "gpt-4.5-preview"

FOUNDER_PROFILE = (
    "Jakob is an accomplished poker player, proficient in Python "
    "and highly skilled in AI. Promethius Poker is an established "
    "poker-community and training platform.  The goal is for Jakob "
    "and Promethius to collaborate on a product/service for poker players."
)

# Ensure data folder exists
DATA_DIR.mkdir(exist_ok=True)

# ── FILE HELPERS ──────────────────────────────────────────────────────
def _load_json(path: Path, default):
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return default

def _save_json(path: Path, obj):
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

# ── IDEA PERSISTENCE ─────────────────────────────────────────────────
def load_ideas():
    return _load_json(
        IDEA_PATH,
        {
            "Tracker for Poker":      {h: "" for h in HEADINGS},
            "GTO Clickable-Map":      {h: "" for h in HEADINGS},
            "Interactive AI Hub":     {h: "" for h in HEADINGS},
        },
    )

def save_ideas(ideas: dict):
    _save_json(IDEA_PATH, ideas)

# ── EVALUATION LOG ───────────────────────────────────────────────────
def append_evaluation(entry: dict):
    log = _load_json(EVAL_PATH, [])
    log.append(entry)
    _save_json(EVAL_PATH, log)

# ── UTILS ────────────────────────────────────────────────────────────
def markdown_from_idea(name: str, sections: dict[str, str], show_empty: bool) -> str:
    lines = [f"## {name}"]
    for head, txt in sections.items():
        if txt or show_empty:
            lines.append(f"### {head}")
            for row in txt.splitlines():
                row = row.strip()
                if row:
                    lines.append(f"#### {row}")
    return "\n".join(lines)

def build_mindmap_md(ideas: dict, show_empty: bool) -> str:
    parts = ["# Promethius small Business Case"]
    for nm, sec in ideas.items():
        parts.append(markdown_from_idea(nm, sec, show_empty))
    return "\n".join(parts)

def extract_score(md: str) -> int | None:
    m = re.search(r"\b([1-9]|10)\s*/\s*10\b|\b([1-9]|10)\b(?=.*score)", md, re.I)
    return int(m.group(1) or m.group(2)) if m else None

# ── GPT EVALUATION ───────────────────────────────────────────────────
def gpt_evaluate(client: OpenAI, md: str, deep: bool = False) -> str:
    system = (
        "You are a senior VC analyst. Evaluate the business-case mind-map the user "
        "provides.  Cover: market size, competitors, synergy with Promethius Poker, "
        "synergy with Jakob's poker/AI skills, implementation cost, complexity, risks, "
        "and give a 1–10 score with a short recommendation. Answer in markdown (H2 headings)."
    )
    if deep:
        system += (
            "\n\nThink step-by-step, search publicly available info on Promethius Poker "
            "and the broader poker SAAS landscape, cite concrete numbers where possible, "
            "and provide more granular analysis."
        )

    resp = client.chat.completions.create(
        model   = MODEL_NAME,
        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": FOUNDER_PROFILE},
            {"role": "user",   "content": md},
        ],
        max_tokens = 1400 if deep else 800,
    )
    return resp.choices[0].message.content

# ── STREAMLIT UI ─────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="Promethius small Business Case", layout="wide")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Session init
    if "ideas" not in st.session_state:       st.session_state.ideas = load_ideas()
    if "show_empty" not in st.session_state:  st.session_state.show_empty = False

    st.title("Promethius small Business Case")

    # ── SIDEBAR ───────────────────────────────────────────
    with st.sidebar:
        st.header("➕ Add new idea")
        new_name = st.text_input("Idea name")
        if st.button("Add idea", disabled=not new_name.strip()):
            if new_name in st.session_state.ideas:
                st.error("Idea already exists")
            else:
                st.session_state.ideas[new_name] = {h: "" for h in HEADINGS}
                st.success(f"Added '{new_name}'")

        st.divider()
        st.checkbox("Show empty headings", key="show_empty")

        st.divider()
        if st.button("🚀 Quick evaluate"):
            md = build_mindmap_md(st.session_state.ideas, st.session_state.show_empty)
            with st.spinner("GPT-4.5-preview thinking …"):
                out = gpt_evaluate(client, md, deep=False)
            st.session_state.last_eval = out
            append_evaluation(
                {
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "mode": "quick",
                    "score": extract_score(out),
                    "markdown": out,
                    "model": MODEL_NAME,
                }
            )

        if st.button("🔎 Deep evaluate"):
            md = build_mindmap_md(st.session_state.ideas, st.session_state.show_empty)
            with st.spinner("GPT-4.5-preview deep dive …"):
                out = gpt_evaluate(client, md, deep=True)
            st.session_state.last_eval = out
            append_evaluation(
                {
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "mode": "deep",
                    "score": extract_score(out),
                    "markdown": out,
                    "model": MODEL_NAME,
                }
            )

        st.divider()
        if st.button("💾 Save mind-map"):
            save_ideas(st.session_state.ideas)
            st.success("Mind-map saved")

    # ── IDEA CARDS ───────────────────────────────────────
    cols = st.columns(2)
    for i, (idea, sections) in enumerate(st.session_state.ideas.items()):
        with cols[i % 2]:
            with st.expander(f"✏️ {idea}", expanded=False):
                new_title = st.text_input("Name", idea, key=f"title_{idea}")
                if new_title != idea:
                    st.session_state.ideas[new_title] = st.session_state.ideas.pop(idea)
                    save_ideas(st.session_state.ideas)
                    st.rerun()

                for h in HEADINGS:
                    st.text_area(
                        h, sections[h], key=f"{idea}_{h}", height=80,
                        on_change=lambda i=idea, h=h:
                            sections.update({h: st.session_state[f"{i}_{h}"]})
                    )

                if st.button("🗑️ Delete", key=f"del_{idea}"):
                    st.session_state.ideas.pop(idea)
                    save_ideas(st.session_state.ideas)
                    st.rerun()

    st.divider()
    mindmap_md = build_mindmap_md(st.session_state.ideas, st.session_state.show_empty)
    st.subheader("📊 Mind-map")
    markmap(mindmap_md)

    # Evaluation output
    if "last_eval" in st.session_state:
        score = extract_score(st.session_state.last_eval)
        if score is not None:
            st.metric("Latest score", f"{score}/10")
        st.markdown(st.session_state.last_eval)

if __name__ == "__main__":
    main()
