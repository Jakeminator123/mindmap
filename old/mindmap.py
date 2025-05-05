import streamlit as st
from streamlit_markmap import markmap

# ── constants ───────────────────────────────────────────────────────────
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

# ── helpers ─────────────────────────────────────────────────────────────
def init_state() -> None:
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


# ── UI ──────────────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(page_title="Promethius small Business Case", layout="wide")
    init_state()

    st.title("Promethius small Business Case")

    # sidebar – add idea / options
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

    # editable idea cards
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

    # render mind-map
    md_blocks = ["# Promethius small Business Case"]
    for name, secs in st.session_state.ideas.items():
        md_blocks.append(idea_to_md(name, secs))

    st.subheader("📊 Mind-map")
    markmap("\n".join(md_blocks))
    st.caption("Edit the fields above – the graph updates instantly.")


if __name__ == "__main__":
    main()
