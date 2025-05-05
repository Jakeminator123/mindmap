import os
import streamlit as st
from streamlit_markmap import markmap
from openai import OpenAI               # <── NYTT

# ── konstanter ──────────────────────────────────────────────
HEADINGS = [
    "Complexity",
    "Competitors",
    "Synergy with Promethius",
    "Implementation Cost",
    "Risks",
]
INITIAL_IDEAS = {
    "Tracker for Poker": {h: "" for h in HEADINGS},
    "GTO Clickable-Map": {h: "" for h in HEADINGS},
    "Interactive AI Overviewer": {h: "" for h in HEADINGS},
}

# ── hjälp­­funktioner ────────────────────────────────────────
def init_state():
    if "ideas" not in st.session_state:
        st.session_state.ideas = INITIAL_IDEAS.copy()
    st.session_state.setdefault("show_empty", False)

def idea_to_md(name: str, sections: dict[str, str]) -> str:
    lines = [f"## {name}"]
    for heading, text in sections.items():
        if text or st.session_state.show_empty:
            lines.append(f"### {heading}")
            for row in text.splitlines():
                row = row.strip()
                if row:
                    lines.append(f"#### {row}")
    return "\n".join(lines)

# ── huvud­­funktion ─────────────────────────────────────────
def main():
    st.set_page_config(page_title="Promethius small Business Case", layout="wide")
    init_state()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # <── NYTT

    st.title("Promethius small Business Case")

    # ── sidebar: add idea ──────────────────────────────────
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
        st.checkbox("Show empty headings", key="show_empty", value=False)

    # ── idékort ────────────────────────────────────────────
    cols = st.columns(2)
    for idx, (idea, sections) in enumerate(st.session_state.ideas.items()):
        col = cols[idx % 2]
        with col:
            with st.expander(f"✏️ {idea}", expanded=False):
                new_title = st.text_input("Name", idea, key=f"title_{idea}")
                if new_title != idea:
                    st.session_state.ideas[new_title] = st.session_state.ideas.pop(idea)
                    st.rerun()
                for heading in HEADINGS:
                    st.text_area(
                        heading,
                        sections[heading],
                        key=f"{idea}_{heading}",
                        height=80,
                        on_change=lambda i=idea, h=heading: sections.update(
                            {h: st.session_state[f"{i}_{h}"]}
                        ),
                    )
                if st.button("🗑️ Delete", key=f"del_{idea}", type="primary"):
                    st.session_state.ideas.pop(idea)
                    st.rerun()

    st.divider()

    # ── bygg markdown + rendera markmap ────────────────────
    md_blocks = ["# Promethius small Business Case"]
    for name, secs in st.session_state.ideas.items():
        md_blocks.append(idea_to_md(name, secs))
    mindmap_md = "\n".join(md_blocks)

    st.subheader("📊 Mind-map")
    markmap(mindmap_md)

    # ── knappen Evaluate ───────────────────────────────────
    if st.button("🚀 Evaluate business case"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("OPENAI_API_KEY not set")
        else:
            with st.spinner("Asking GPT-4o for an evaluation…"):
                system_msg = (
                    "You are a senior VC analyst. Evaluate the entire business-case "
                    "mind-map provided by the user. Respond in professional English, "
                    "covering market size, competitors, synergy with Promethius, "
                    "implementation cost, complexity, risks, and give a 1-10 score "
                    "with a short recommendation. Use markdown with H2 headings."
                )
                try:
                    resp = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": mindmap_md},
                        ],
                        max_tokens=800,
                    )
                    st.markdown("---")
                    st.markdown("## 📑 GPT-4o Evaluation")
                    st.markdown(resp.choices[0].message.content)
                except Exception as e:
                    st.error(f"OpenAI error: {e}")

if __name__ == "__main__":
    main()
