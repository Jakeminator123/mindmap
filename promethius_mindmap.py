"""
Promethius small Business Case
• Streamlit-mind-map med beständig lagring
• GPT-4.5-preview-utvärdering (quick & deep) sparas i evaluations.json
• Tar hänsyn till grundarprofilen (Jakob: pokerproffs, kod- och AI-expert)
"""

import os, json, re, datetime
from pathlib import Path

import streamlit as st
from streamlit_markmap import markmap
from openai import OpenAI

# ── konstanter ─────────────────────────────────────────────
HEADINGS = [
    "Complexity",
    "Competitors",
    "Synergy with Promethius",
    "Implementation Cost",
    "Risks",
]

DATA_DIR = Path(__file__).with_name("data")
DATA_DIR.mkdir(exist_ok=True)

IDEA_PATH = DATA_DIR / "ideas.json"
EVAL_PATH = DATA_DIR / "evaluations.json"

FOUNDER_PROFILE = (
    "Jakob is an accomplished poker player, proficient in Python "
    "and highly skilled in AI. Consider how each idea can leverage "
    "these skills and reputation."
)

MODEL_NAME = "gpt-4.5-preview"

# ── fil-hjälpare ───────────────────────────────────────────
def load_json(path: Path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path: Path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# ── idé-hjälpare ───────────────────────────────────────────
def load_ideas():
    return load_json(
        IDEA_PATH,
        {
            "Tracker for Poker": {h: "" for h in HEADINGS},
            "GTO Clickable-Map": {h: "" for h in HEADINGS},
            "Interactive AI Overviewer": {h: "" for h in HEADINGS},
        },
    )


def save_ideas(ideas: dict):
    save_json(IDEA_PATH, ideas)


# ── evaluation-hjälpare ───────────────────────────────────
def append_evaluation(entry: dict):
    log = load_json(EVAL_PATH, [])
    log.append(entry)
    save_json(EVAL_PATH, log)


def extract_score(markdown: str) -> int | None:
    m = re.search(r"\b([1-9]|10)\s*/\s*10\b|\b([1-9]|10)\b(?=.*score)", markdown, re.I)
    return int(m.group(1) or m.group(2)) if m else None


# ── markdown-generator ────────────────────────────────────
def idea_to_md(name: str, sections: dict[str, str], show_empty: bool) -> str:
    lines = [f"## {name}"]
    for heading, text in sections.items():
        if text or show_empty:
            lines.append(f"### {heading}")
            for row in text.splitlines():
                row = row.strip()
                if row:
                    lines.append(f"#### {row}")
    return "\n".join(lines)


def build_mindmap_md(ideas: dict, show_empty: bool) -> str:
    blocks = ["# Promethius small Business Case"]
    for nm, sec in ideas.items():
        blocks.append(idea_to_md(nm, sec, show_empty))
    return "\n".join(blocks)


# ── GPT-utvärdering ───────────────────────────────────────
def gpt_evaluate(client: OpenAI, md: str, deep: bool = False) -> str:
    system_msg = (
        "You are a senior VC analyst. Evaluate the entire business-case mind-map "
        "provided by the user. Respond in professional English, covering market size, "
        "competitors, synergy with Promethius, synergy with Jakob's poker/AI skills, "
        "implementation cost, complexity, risks, and give a 1-10 score with a short "
        "recommendation. Use markdown with H2 headings."
    )
    if deep:
        system_msg += (
            "\n\nThink step-by-step, perform competitor desk research, cite public data "
            "where possible, and provide more granular numbers."
        )

    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": FOUNDER_PROFILE},
            {"role": "user", "content": md},
        ],
        max_tokens=1400 if deep else 800,
    )
    return resp.choices[0].message.content


# ── Streamlit-UI ──────────────────────────────────────────
def main():
    st.set_page_config(page_title="Promethius small Business Case", layout="wide")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if "ideas" not in st.session_state:
        st.session_state.ideas = load_ideas()
    if "show_empty" not in st.session_state:
        st.session_state.show_empty = False

    st.title("Promethius small Business Case")

    # ── SIDEBAR ───────────────────────────────────────────
    with st.sidebar:
        st.header("➕ Add new idea")
        new_name = st.text_input("Idea name")
        if st.button("Add idea", disabled=not new_name):
            if new_name in st.session_state.ideas:
                st.error("Idea already exists")
            else:
                st.session_state.ideas[new_name] = {h: "" for h in HEADINGS}
                st.success(f"Added {new_name}")

        st.divider()
        st.checkbox("Show empty headings", key="show_empty")

        st.divider()
        if st.button("🚀 Quick evaluate"):
            md = build_mindmap_md(st.session_state.ideas, st.session_state.show_empty)
            with st.spinner("GPT-4.5-preview thinking…"):
                out = gpt_evaluate(client, md, deep=False)
            st.session_state.last_eval = out
            score = extract_score(out)
            append_evaluation(
                {
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "mode": "quick",
                    "score": score,
                    "markdown": out,
                    "model": MODEL_NAME,
                }
            )

        if st.button("🔎 Deep evaluate"):
            md = build_mindmap_md(st.session_state.ideas, st.session_state.show_empty)
            with st.spinner("GPT-4.5-preview deep dive…"):
                out = gpt_evaluate(client, md, deep=True)
            st.session_state.last_eval = out
            score = extract_score(out)
            append_evaluation(
                {
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "mode": "deep",
                    "score": score,
                    "markdown": out,
                    "model": MODEL_NAME,
                }
            )

        st.divider()
        if st.button("💾 Save mind-map"):
            save_ideas(st.session_state.ideas)
            st.success("Mind-map saved")

    # ── IDEA CARDS ────────────────────────────────────────
    cols = st.columns(2)
    for idx, (idea, sections) in enumerate(st.session_state.ideas.items()):
        col = cols[idx % 2]
        with col:
            with st.expander(f"✏️ {idea}", expanded=False):
                new_title = st.text_input("Name", idea, key=f"title_{idea}")
                if new_title != idea:
                    st.session_state.ideas[new_title] = st.session_state.ideas.pop(idea)
                    save_ideas(st.session_state.ideas)
                    st.rerun()
                for heading in HEADINGS:
                    st.text_area(
                        heading,
                        sections[heading],
                        key=f"{idea}_{heading}",
                        height=80,
                        on_change=lambda i=idea, h=heading:
                            sections.update({h: st.session_state[f"{i}_{h}"]}),
                    )
                if st.button("🗑️ Delete", key=f"del_{idea}"):
                    st.session_state.ideas.pop(idea)
                    save_ideas(st.session_state.ideas)
                    st.rerun()

    st.divider()

    # ── MIND-MAP VISUAL ──────────────────────────────────
    mindmap_md = build_mindmap_md(st.session_state.ideas, st.session_state.show_empty)
    st.subheader("📊 Mind-map")
    markmap(mindmap_md)

    # ── EVALUATION OUTPUT ────────────────────────────────
    if "last_eval" in st.session_state:
        score = extract_score(st.session_state.last_eval)
        if score is not None:
            st.metric("Latest score", f"{score}/10")
        st.markdown(st.session_state.last_eval)


if __name__ == "__main__":
    main()
