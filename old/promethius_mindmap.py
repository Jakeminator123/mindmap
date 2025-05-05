"""
Promethius small Business Case – collaborative mind-map + GPT-evaluation
• Persistent JSON save (ideas.json)
• Quick  & Deep evaluation
"""

import os, json, re, datetime
import streamlit as st
from streamlit_markmap import markmap
from openai import OpenAI
from pathlib import Path

# ── config ────────────────────────────────────────────────────────────
HEADINGS = [
    "Complexity",
    "Competitors",
    "Synergy with Promethius",
    "Implementation Cost",
    "Risks",
]
SAVE_PATH = Path(__file__).with_name("ideas.json")

# ── helpers ───────────────────────────────────────────────────────────
def load_ideas():
    if SAVE_PATH.exists():
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "Tracker for Poker": {h: "" for h in HEADINGS},
        "GTO Clickable-Map": {h: "" for h in HEADINGS},
        "Interactive AI Overviewer": {h: "" for h in HEADINGS},
    }


def save_ideas(ideas: dict):
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(ideas, f, ensure_ascii=False, indent=2)


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


def extract_score(markdown: str) -> int | None:
    """Hitta första heltal 1-10 i GPT-svaret."""
    m = re.search(r"\b([1-9]|10)\s*/\s*10\b|\b([1-9]|10)\b(?=.*score)", markdown, re.I)
    if m:
        return int(m.group(1) or m.group(2))
    return None


def gpt_evaluate(client: OpenAI, md: str, deep: bool = False) -> str:
    system_msg = (
        "You are a senior VC analyst. Evaluate the entire business-case mind-map "
        "provided by the user. Respond in professional English, covering market "
        "size, competitors, synergy with Promethius, implementation cost, complexity, "
        "risks, and give a 1-10 score with a short recommendation. Use markdown with H2 headings."
    )
    if deep:
        system_msg += (
            "\n\nThink step-by-step, perform competitor desk research, consider secondary "
            "data sources, and provide more granular numbers where possible."
        )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": md},
        ],
        max_tokens=1400 if deep else 800,
    )
    return resp.choices[0].message.content


# ── Streamlit UI ──────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="Promethius small Business Case", layout="wide")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # ── init session state ─────────────
    if "ideas" not in st.session_state:
        st.session_state.ideas = load_ideas()
    if "show_empty" not in st.session_state:
        st.session_state.show_empty = False

    st.title("Promethius small Business Case")

    # ── sidebar ───────────────────────
    with st.sidebar:
        st.header("➕ Add new idea")
        new_name = st.text_input("Idea name")
        if st.button("Add idea", use_container_width=True, disabled=not new_name):
            if new_name in st.session_state.ideas:
                st.error("Idea already exists")
            else:
                st.session_state.ideas[new_name] = {h: "" for h in HEADINGS}
                st.success(f"Added {new_name}")

        st.divider()
        st.checkbox("Show empty headings", key="show_empty")

        st.divider()
        # ⬇ evaluation buttons
        if st.button("🚀 Quick evaluate", use_container_width=True):
            md = build_mindmap_md(st.session_state.ideas, st.session_state.show_empty)
            with st.spinner("GPT-4o thinking…"):
                out = gpt_evaluate(client, md, deep=False)
            st.session_state["last_eval"] = out
        if st.button("🔎 Deep evaluate", use_container_width=True):
            md = build_mindmap_md(st.session_state.ideas, st.session_state.show_empty)
            with st.spinner("GPT-4o deep dive…"):
                out = gpt_evaluate(client, md, deep=True)
            st.session_state["last_eval"] = out

        st.divider()
        # 💾 save
        if st.button("💾 Save mind-map", use_container_width=True):
            save_ideas(st.session_state.ideas)
            st.success(f"Saved {SAVE_PATH.name}   "
                       f"({datetime.datetime.now().strftime('%H:%M:%S')})")

    # ── editable cards ────────────────
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
                            sections.update({h: st.session_state[f"{i}_{h}"]})
                    )
                if st.button("🗑️ Delete", key=f"del_{idea}", type="primary"):
                    st.session_state.ideas.pop(idea)
                    save_ideas(st.session_state.ideas)
                    st.rerun()

    st.divider()

    # ── mind-map render ───────────────
    mindmap_md = build_mindmap_md(st.session_state.ideas, st.session_state.show_empty)
    st.subheader("📊 Mind-map")
    markmap(mindmap_md)

    # ── evaluation output ─────────────
    if "last_eval" in st.session_state:
        score = extract_score(st.session_state.last_eval)
        if score:
            st.metric("Overall score", f"{score}/10")
        st.markdown(st.session_state.last_eval)


if __name__ == "__main__":
    main()
