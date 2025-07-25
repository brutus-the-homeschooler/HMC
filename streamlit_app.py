import streamlit as st
import pandas as pd
from streamlit_js_eval import streamlit_js_eval

# Load data
ratings = pd.read_csv("ratings.csv")
metadata = pd.read_csv("metadata.csv", encoding="ISO-8859-1")
df = ratings.merge(metadata, on="movie_id")

# Get unlocked users
unlocked_users = ratings[ratings['unlock'] == 1]['username'].unique()

# Retrieve from localStorage (only runs once when the app loads)
user_from_local = streamlit_js_eval(js_expressions="localStorage.getItem('selected_user')", key="load_user")

# Set default in session_state
if "selected_user" not in st.session_state:
    st.session_state.selected_user = user_from_local if user_from_local in unlocked_users else unlocked_users[0]

# Dropdown selector
selected_user = st.selectbox("Select a user", unlocked_users,
                             index=list(unlocked_users).index(st.session_state.selected_user),
                             key="selected_user")

# Save selection back to localStorage
streamlit_js_eval(js_expressions=f"localStorage.setItem('selected_user', '{selected_user}')", key="save_user")

# Filter merged data for selected user
user_df = df[df['username'] == selected_user]
current_movie = metadata.loc[metadata['movie_id'].idxmax()]

# 🎃 Background styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Creepster&display=swap');
    body {
        background-image: url('https://www.transparenttextures.com/patterns/dark-mosaic.png');
        background-size: cover;
        color: #FF4444;
    }
    h1 {
        font-family: 'Creepster', cursive;
        font-size: 4em;
        text-shadow: 2px 2px 4px #000000;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1>🩸 Horror Movie Club 🧟</h1>", unsafe_allow_html=True)

# Next movie
st.markdown("## 🍿 Our Next Movie Is...")
st.image(current_movie['poster_url'], width=300)
st.markdown(f"### **{current_movie['official_title']}**")
st.markdown(f"**Synopsis:** _{current_movie['synopsis']}_")
st.markdown(
   f"[🎬 IMDb]({current_movie['imdb_url']}) &nbsp;&nbsp;|&nbsp;&nbsp; [📚 Wikipedia]({current_movie['wiki_url']}) &nbsp;&nbsp;|&nbsp;&nbsp; [👀 Watch]({current_movie['osu_library_link']})",
    unsafe_allow_html=True
)
st.video(current_movie["trailer_url"])

# Prediction logic
prediction_placeholder = st.empty()
q1 = user_df['score'].quantile(0.25)
q2 = user_df['score'].mean()
q3 = user_df['score'].quantile(0.75)

def closest_movie_to(value):
    return user_df.iloc[(user_df['score'] - value).abs().argsort()[:1]]

friendly_labels = {
    "Q1": "👎 Lower-Rated Benchmark",
    "Q2": "🤷 Middle-Rated Benchmark",
    "Q3": "👍 Higher-Rated Benchmark"
}

for label, quantile in [("Q1", q1), ("Q2", q2), ("Q3", q3)]:
    movie = closest_movie_to(quantile).iloc[0]
    st.subheader(f"{friendly_labels[label]}: {movie['official_title']} ({movie['year']})")
    st.image(movie['poster_url'], width=200)
    st.markdown(f"**Director:** {movie['director']}")
    st.markdown(f"**RT Score:** {movie['rt_score']}%")
    st.markdown(f"**Synopsis:** _{movie['synopsis']}_")
    st.markdown(f"[IMDb]({movie['imdb_url']}) | [Wikipedia]({movie['wiki_url']})")
    st.radio(
        f"Do you think this week's movie is better than *{movie['official_title']}*?",
        options=["---", "Yes", "No"],
        key=label,
        index=0
    )

# Display score range prediction
if all(k in st.session_state for k in ["Q1", "Q2", "Q3"]):
    q1_answer = st.session_state["Q1"]
    q2_answer = st.session_state["Q2"]
    q3_answer = st.session_state["Q3"]

    if q1_answer == "No":
        prediction = f"Less than {q1:.1f}"
    elif q1_answer == "Yes" and q2_answer == "No":
        prediction = f"Between {q1:.1f} and {q2:.1f}"
    elif q2_answer == "Yes" and q3_answer == "No":
        prediction = f"Between {q2:.1f} and {q3:.1f}"
    elif all(ans == "Yes" for ans in [q1_answer, q2_answer, q3_answer]):
        prediction = f"Greater than {q3:.1f}"
    else:
        prediction = "Unable to predict based on your answers."

    prediction_placeholder.markdown(
        f"### 🧠 Predicted Score Range\nBased on your answers, we think this week's movie score will be: **{prediction}**"
    )

# Bonus refinement
if all(st.session_state.get(k) == "Yes" for k in ["Q1", "Q2", "Q3"]):
    st.markdown("#### 🔁 Let's Refine Your Score Prediction Even More...")

    bonus_df = user_df[user_df['score'] > q3].copy()
    bonus_df = (
        bonus_df.sort_values(by=["score", "movie_id"], ascending=[True, False])
        .drop_duplicates(subset="score", keep="first")
        .sort_values("score")
        .reset_index(drop=True)
    )

    last_yes_score = None
    stop_score = None

    for i, row in bonus_df.iterrows():
        key = f"bonus_{i}"

        if i == 0 or st.session_state.get(f"bonus_{i-1}") == "Yes":
            st.markdown(f"##### 🔍 Compare to: *{row['official_title']}* ({row['score']})")
            st.image(row['poster_url'], width=150)
            response = st.radio(
                f"Is this week's movie better than *{row['official_title']}*?",
                options=["---", "Yes", "No"],
                key=key,
                index=0
            )

            if response == "Yes":
                last_yes_score = row["score"]
            elif response == "No":
                stop_score = row["score"]
                break
        else:
            break

    if last_yes_score is not None and stop_score is not None:
        refined_prediction = f"Between {last_yes_score:.1f} and {stop_score:.1f}"
        prediction_placeholder.markdown(
            f"### 🧠 Refined Predicted Score Range\nBased on your extended answers, the score is likely: **{refined_prediction}**"
        )

# Sidebar ratings
with st.sidebar:
    st.markdown("## 🎬 Your Ratings")
    st.markdown("""
    <style>
    ul.rating-list {
        padding-left: 20px;
    }
    ul.rating-list li {
        margin-bottom: 8px;
        list-style-type: "🎬 ";
        font-size: 16px;
        line-height: 1.4;
    }
    ul.rating-list li strong {
        font-size: 18px;
        color: #FF4444;
    }
    </style>
    """, unsafe_allow_html=True)

    if not user_df.empty:
        st.markdown('<ul class="rating-list">', unsafe_allow_html=True)
        for _, row in user_df.sort_values(by="score", ascending=False).iterrows():
            st.markdown(
                f'<li title="Director: {row["director"]} | RT: {row["rt_score"]}%">'
                f'<strong>{row["official_title"]}</strong> {row["score"]}</li>',
                unsafe_allow_html=True
            )
        st.markdown('</ul>', unsafe_allow_html=True)
    else:
        st.markdown("No ratings found.")

    st.markdown("---")

    # Show all movies
    with st.expander("📚 Show All Movies", expanded=False):
        for _, row in metadata.sort_values("movie_id").iterrows():
            st.image(row["poster_url"], width=150)
            st.markdown(f"**{row['official_title']}**")

            links = f"[IMDb]({row['imdb_url']}) | [Wikipedia]({row['wiki_url']})"
            if pd.notna(row.get("osu_library_link")) and row["osu_library_link"].strip() != "":
                links += f" | [📚 OSU Library]({row['osu_library_link']})"

            st.markdown(links)
            st.markdown("---")
