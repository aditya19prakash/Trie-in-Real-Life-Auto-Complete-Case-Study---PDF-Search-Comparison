import streamlit as st
import pdfplumber
import re
import html
from trie import AdvancedTrie
from search_utils import normalize_word
import plotly.graph_objects as go

st.set_page_config(page_title="Trie in Real Life: Auto-Complete Case Study", layout="wide")
st.title("Trie in Real Life: Auto-Complete Case Study — PDF Search Comparison")

# ------------------------------
# Session State
# ------------------------------
if 'pdf_cache' not in st.session_state:
    st.session_state.pdf_cache = {}
if 'performance' not in st.session_state:
    st.session_state.performance = {}

uploaded_file = st.file_uploader("Upload PDF", type="pdf")
query = st.text_input("Enter sentence to search:")

# ------------------------------
# Safe Highlighting function
# ------------------------------
def highlight_search_safe(text, query, trie_candidates_set):
    """
    Highlight matches safely:
    - Normal Search only: yellow
    - Trie Prefix Search only: lightgreen
    - Both: orange
    """
    words = text.split()
    result = []

    i = 0
    query_words = query.split()
    query_len = len(query_words)

    while i < len(words):
        segment = " ".join(words[i:i+query_len])
        segment_esc = html.escape(segment)  # Escape unsafe HTML
        segment_lower = segment.lower()
        query_lower = query.lower()

        in_normal = segment_lower == query_lower
        in_trie = any(segment_lower.startswith(tc) for tc in trie_candidates_set)

        if in_normal and in_trie:
            # Both searches
            result.append(f"<mark style='background-color: orange; color: black'>{segment_esc}</mark>")
            i += query_len
        elif in_normal:
            # Normal search only
            result.append(f"<mark style='background-color: yellow; color: black'>{segment_esc}</mark>")
            i += query_len
        elif in_trie:
            # Trie search only
            result.append(f"<mark style='background-color: lightgreen; color: black'>{segment_esc}</mark>")
            i += query_len
        else:
            result.append(segment_esc)
            i += 1

    return " ".join(result)

# ------------------------------
# Process PDF
# ------------------------------
if uploaded_file and query.strip():
    query_norm = query.strip()

    # Load PDF and cache
    if uploaded_file.name not in st.session_state.pdf_cache:
        pdf = pdfplumber.open(uploaded_file)
        st.session_state.pdf_cache[uploaded_file.name] = {
            "pdf_obj": pdf,
            "num_pages": len(pdf.pages),
            "page_texts": {}
        }
        st.session_state.performance[uploaded_file.name] = {
            "page_words": [],
            "normal_ops": [],
            "trie_ops": [],
            "normal_matches": [],
            "trie_matches": []
        }

    cache = st.session_state.pdf_cache[uploaded_file.name]
    perf = st.session_state.performance[uploaded_file.name]
    total_pages = cache["num_pages"]

    # Page navigation
    page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)

    # Load page text on-demand
    if page_num not in cache["page_texts"]:
        page_text = cache["pdf_obj"].pages[page_num-1].extract_text() or ""
        cache["page_texts"][page_num] = page_text
    else:
        page_text = cache["page_texts"][page_num]

    # ----------------
    # Normal Search
    # ----------------
    normal_matches = len(re.findall(re.escape(query_norm), page_text, flags=re.IGNORECASE))
    normal_ops = len(page_text.split())

    # ----------------
    # Trie Prefix Search
    # ----------------
    trie = AdvancedTrie()
    for w in page_text.split():
        trie.insert(normalize_word(w))

    first_word = normalize_word(query_norm.split()[0])
    trie_candidates = trie.search_prefix(first_word)
    trie_candidates_set = set(trie_candidates)
    trie_ops = len(trie_candidates) + len(first_word)

    trie_matches = sum(
        1 for j in range(len(page_text.split()) - len(query_norm.split()) + 1)
        if " ".join(page_text.split()[j:j+len(query_norm.split())]).lower() == query_norm.lower()
    )

    # ----------------
    # Save performance
    # ----------------
    if page_num not in perf["page_words"]:
        perf["page_words"].append(len(page_text.split()))
        perf["normal_ops"].append(normal_ops)
        perf["trie_ops"].append(trie_ops)
        perf["normal_matches"].append(normal_matches)
        perf["trie_matches"].append(trie_matches)

    # ----------------
    # Display results
    # ----------------
    st.success(f"Normal Search: Matches={normal_matches}, Ops={normal_ops}")
    st.success(f"Trie Prefix Search: Matches={trie_matches}, Ops={trie_ops}")

    # Highlight text
    highlighted_text = highlight_search_safe(page_text, query_norm, trie_candidates_set)
    st.markdown(f"""
        <div style="
            background:#fff; 
            border:2px solid #555; 
            padding:20px; 
            border-radius:8px; 
            max-width:800px; 
            margin:auto;
            color: black;">
            <span style='float:right; color:#757575; font-size:15px'>
                Page <b>{page_num}</b> of <b>{total_pages}</b>
            </span>
            <br>
            <div style="white-space: pre-wrap; color: black;">{highlighted_text}</div>
        </div>
    """, unsafe_allow_html=True)

    # ----------------
    # Prepare Plotly graph: Number of Words vs Operations
    # ----------------
    x_words = perf["page_words"]      # number of words in each searched page
    y_normal_ops = perf["normal_ops"] # number of operations for Normal Search
    y_trie_ops = perf["trie_ops"]     # number of operations for Trie Search

    fig = go.Figure()

    # Normal Search
    fig.add_trace(go.Scatter(
        x=x_words,
        y=y_normal_ops,
        mode='lines+markers',
        name="Normal Search Ops",
        line=dict(color='blue'),
        marker=dict(size=8)
    ))

    # Trie Prefix Search
    fig.add_trace(go.Scatter(
        x=x_words,
        y=y_trie_ops,
        mode='lines+markers',
        name="Trie Prefix Search Ops",
        line=dict(color='orange'),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title=f"Search Operations vs Number of Words per Page for '{query_norm}'",
        xaxis_title="Number of Words in Page",
        yaxis_title="Number of Operations",
        template='plotly_white',
        legend=dict(x=0.01, y=0.99)
    )

    st.plotly_chart(fig, use_container_width=True)
