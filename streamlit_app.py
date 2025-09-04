import streamlit as st
import pandas as pd
from streamlit_js_eval import streamlit_js_eval
#import matplotlib.pyplot as plt

# ============================
# Load Data
# ============================
ratings = pd.read_csv("ratings.csv")
metadata = pd.read_csv("metadata.csv", encoding="ISO-8859-1")
df = ratings.merge(metadata, on="movie_id")

# ============================
# User Handling
# ============================
unlocked_users = ratings[ratings['unlock'] == 1]['username'].unique()

# Retrieve from localStorage (only runs once when app loads)
user_from_local = streamlit_js_eval(
    js_expressions="localStorage.getItem('selected_user')", key="load_user"
)

# Set default in session_state
if "selected_user" not in st.session_state:
    st.session_state.selected_user = (
        user_from_local if user_from_local in unlocked_users else unlocked_users[0]
    )

# Dropdown selector
selected_user = st.selectbox(
    "Select a user",
    unlocked_users,
    index=list(unlocked_users).index(st.session_state.selected_user),
    key="selected_user",
)

# Save selection back to localStorage
streamlit_js_eval(
    js_expressions=f"localStorage.setItem('selected_user', '{selected_user}')",
    key="save_user",
)

# Filter data for this user
user_df = df[df['username'] == selected_user]
current_movie = metadata.loc[metadata['movie_id'].idxmax()]

# ============================
# Styling
# ============================
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

# ============================
# Tabs
# ============================
tab1, tab2, tab3 = st.tabs(["🍿 Next Movie", "🧠 Prediction", "📈 Trends"])

# ----------------------------
# TAB 1: Next Movie
# ----------------------------
with tab1:
    st.markdown("## 🍿 Our Next Movie Is...")
    st.image(current_movie['poster_url'], width=300)
    st.markdown(f"### **{current_movie['official_title']}**")
    st.markdown(f"**Synopsis:** _{current_movie['synopsis']}_")
    st.markdown(
       f"[🎬 IMDb]({current_movie['imdb_url']}) | [📚 Wikipedia]({current_movie['wiki_url']}) | [👀 Watch]({current_movie['osu_library_link']})",
        unsafe_allow_html=True
    )
    st.video(current_movie["trailer_url"])

# ----------------------------
# TAB 2: Prediction
# ----------------------------
with tab2:
    st.markdown("## 🧠 Rate Prediction")

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

# ----------------------------
# TAB 3: Trends & Global Stats
# ----------------------------
with tab3:
    st.markdown("## 📈 Trends & Insights")

    avg_score = user_df['score'].mean()
    global_avg = df['score'].mean()

    col1, col2 = st.columns(2)
    col1.metric("🎯 Your Avg Score", f"{avg_score:.2f}")
    col2.metric("🌍 Global Avg Score", f"{global_avg:.2f}")

    if avg_score > global_avg:
        st.success("🍭 You tend to be more generous than the club average.")
    elif avg_score < global_avg:
        st.error("🪓 You tend to be harsher than the club average.")
    else:
        st.info("⚖️ You rate right on the club average.")

    # Top & Bottom 5
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("### 🏆 Top 5 Movies")
        top5 = user_df.sort_values("score", ascending=False).head(min(5, len(user_df)))
        for _, row in top5.iterrows():
            st.image(row["poster_url"], width=100)
            st.markdown(f"**{row['official_title']}** ({row['score']})")

    with col4:
        st.markdown("### 💀 Bottom 5 Movies")
        bottom5 = user_df.sort_values("score", ascending=True).head(min(5, len(user_df)))
        for _, row in bottom5.iterrows():
            st.image(row["poster_url"], width=100)
            st.markdown(f"**{row['official_title']}** ({row['score']})")

    # Timeline
    if "date_watched" in user_df.columns:
        user_df["date_watched"] = pd.to_datetime(user_df["date_watched"], errors="coerce")
        timeline_df = user_df.dropna(subset=["date_watched"]).sort_values("date_watched")

        if not timeline_df.empty:
            st.markdown("### ⏳ Ratings Over Time")
            st.line_chart(timeline_df.set_index("date_watched")["score"])

            st.markdown("### 📅 Movies Watched Per Month")
            monthly_counts = (
                timeline_df.groupby(timeline_df['date_watched'].dt.to_period("M")).size()
            )
            st.bar_chart(monthly_counts)

    # Similarity to Other Users
    similarities = {}
    for other_user in unlocked_users:
        if other_user == selected_user:
            continue
        merged = pd.merge(
            user_df[['movie_id', 'score']],
            df[df['username'] == other_user][['movie_id', 'score']],
            on='movie_id',
            suffixes=('_user', '_other')
        )
        if len(merged) >= 3:
            corr = merged['score_user'].corr(merged['score_other'])
            if pd.notna(corr):
                similarities[other_user] = corr

    if similarities:
        top_matches = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:3]
        st.markdown("### 🧑‍🤝‍🧑 You Review Movies Like...")
        st.markdown(", ".join([name for name, _ in top_matches]))
    else:
        st.markdown("### 🧑‍🤝‍🧑 No strong similarities found yet.")
