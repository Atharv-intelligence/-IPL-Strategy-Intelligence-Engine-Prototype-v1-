import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ---------------- LOAD DATA ---------------- #
@st.cache_data
def load_data():
    return pd.read_csv("data/deliveries (2).csv")

deliveries = load_data()

# ---------------- FEATURE ENGINEERING ---------------- #
def get_phase(over):
    if over <= 6:
        return "Powerplay"
    elif over <= 15:
        return "Middle"
    else:
        return "Death"

deliveries['phase'] = deliveries['over'].apply(get_phase)
deliveries['is_wicket'] = deliveries['dismissal_kind'].notna().astype(int)

# ---------------- CORE FUNCTIONS ---------------- #
def final_decision(batsman, phase):
    df = deliveries[
        (deliveries['batsman'] == batsman) &
        (deliveries['phase'] == phase)
    ]

    if df.empty:
        return None, None

    stats = df.groupby('bowler').agg({
        'batsman_runs': 'sum',
        'ball': 'count',
        'is_wicket': 'sum'
    }).reset_index()

    # Safety check
    stats = stats[stats['ball'] > 0]

    stats['strike_rate'] = (stats['batsman_runs'] / stats['ball']) * 100

    # Remove small sample size
    stats = stats[stats['ball'] > 10]

    if stats.empty:
        return None, None

    best = stats.sort_values(by='strike_rate').head(5)
    worst = stats.sort_values(by='strike_rate', ascending=False).head(5)

    return best, worst


def simulate_matchup(batsman, bowler, phase):
    df = deliveries[
        (deliveries['batsman'] == batsman) &
        (deliveries['bowler'] == bowler) &
        (deliveries['phase'] == phase)
    ]

    if df.empty or len(df) < 10:
        return None

    runs = df['batsman_runs'].sum()
    balls = df.shape[0]
    wickets = df['is_wicket'].sum()

    strike_rate = (runs / balls) * 100
    wicket_prob = wickets / balls

    return strike_rate, wicket_prob

# ---------------- UI ---------------- #

st.title("🏏 IPL Strategy Intelligence Engine")

st.write(
    "An intelligent system that analyzes IPL data to recommend optimal bowling strategies "
    "and simulate real match scenarios using historical performance data."
)

# ================= STRATEGY ================= #

st.markdown("## 🎯 Strategy Recommendation")

batsman = st.selectbox(
    "Select Batsman",
    sorted(deliveries['batsman'].dropna().unique())
)

phase = st.selectbox(
    "Select Phase",
    ["Powerplay", "Middle", "Death"]
)

if st.button("Get Strategy"):

    best, worst = final_decision(batsman, phase)

    if best is None or worst is None:
        st.warning("⚠️ Not enough data available.")
    else:

        # Best bowlers
        st.subheader("✅ Best Bowlers to Use")
        st.dataframe(best)

        for _, row in best.iterrows():
            st.write(
                f"{row['bowler']} → SR: {row['strike_rate']:.2f}, "
                f"Wickets: {row['is_wicket']}"
            )

        # Graph
        st.subheader("📊 Strike Rate Comparison")

        best_sorted = best.sort_values(by='strike_rate')

        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.barh(best_sorted['bowler'], best_sorted['strike_rate'])

        for bar in bars:
            width = bar.get_width()
            ax.text(width + 1, bar.get_y() + bar.get_height()/2,
                    f"{width:.1f}", va='center')

        ax.set_xlabel("Strike Rate")
        ax.set_title("Best Bowlers vs Batsman (Lower is Better)")
        plt.tight_layout()

        st.pyplot(fig)

        # Worst bowlers
        st.subheader("❌ Bowlers to Avoid")
        st.dataframe(worst)

        # Insight
        best_bowler = best.iloc[0]['bowler']
        worst_bowler = worst.iloc[0]['bowler']

        st.subheader("📊 Strategy Insight")
        st.success(f"👉 Best option: {best_bowler}")
        st.error(f"👉 Avoid: {worst_bowler}")

# ================= SIMULATION ================= #

st.markdown("## 🔬 Match Simulation")

sim_batsman = st.selectbox(
    "Select Batsman (Simulation)",
    sorted(deliveries['batsman'].dropna().unique()),
    key="sim_batsman"
)

sim_bowler = st.selectbox(
    "Select Bowler",
    sorted(deliveries['bowler'].dropna().unique())
)

sim_phase = st.selectbox(
    "Select Phase (Simulation)",
    ["Powerplay", "Middle", "Death"],
    key="sim_phase"
)

if st.button("Simulate Matchup"):

    result = simulate_matchup(sim_batsman, sim_bowler, sim_phase)

    if result is None:
        st.warning("⚠️ Not enough data to simulate.")
    else:
        sr, wicket_prob = result

        st.subheader("📊 Simulation Result")
        st.write(f"Strike Rate: {sr:.2f}")
        st.write(f"Wicket Probability: {wicket_prob:.2f}")

        if sr > 150:
            st.error("🔥 High Risk — Batsman dominates")
        elif sr < 100:
            st.success("🛡️ Safe — Bowler controls")
        else:
            st.info("⚖️ Balanced matchup")

# ================= FOOTER ================= #

st.markdown("---")
st.write("Built by Atharv Shinde ")
