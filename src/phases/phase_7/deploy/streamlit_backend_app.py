from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from pydantic import ValidationError

from src.phases.phase_0.schemas import RecommendationResponse, UserPreferenceInput
from src.phases.phase_2.retriever import dataset_summary, list_localities
from src.phases.phase_4.orchestrator import run_recommendation_orchestration
from src.phases.phase_7.bootstrap_sample_data import ensure_sample_curated_dataset


DEFAULT_CURATED_PATH = "data/processed/restaurants.parquet"


def resolve_curated_path() -> tuple[str, bool]:
    configured = os.getenv("CURATED_DATA_PATH", DEFAULT_CURATED_PATH)
    force_sample = os.getenv("FORCE_SAMPLE_DATA", "false").strip().lower() == "true"
    path = Path(configured)

    if force_sample or not path.exists():
        created = ensure_sample_curated_dataset(output_path=configured)
        return str(created), True
    return configured, False


@st.cache_data(show_spinner=False)
def get_localities(curated_path: str) -> list[str]:
    return list_localities(curated_path=curated_path, limit=500)


@st.cache_data(show_spinner=False)
def get_dataset_summary(curated_path: str) -> dict[str, int]:
    return dataset_summary(curated_path=curated_path)


def render_recommendations(response: RecommendationResponse) -> None:
    if not response.recommendations:
        st.warning("No restaurants found for the selected constraints.")
        return

    st.subheader("Recommendations")
    for idx, item in enumerate(response.recommendations, start=1):
        title = f"{idx}. {item.restaurant_name}"
        locality = f" - {item.locality}" if item.locality else ""
        st.markdown(f"**{title}{locality}**")
        st.write(
            f"Cuisine: {item.cuisine} | Rating: {item.rating or 'NA'} | "
            f"Cost for two: {item.estimated_cost or 'NA'} | Fit: {item.fit_score}"
        )
        st.caption(item.explanation)


def main() -> None:
    st.set_page_config(
        page_title="Zomato Recommendation Backend",
        page_icon=":fork_and_knife:",
        layout="wide",
    )
    st.title("Zomato Recommendation Backend (Streamlit Deployment)")

    curated_path, used_sample_data = resolve_curated_path()
    st.caption(f"Curated dataset path: `{curated_path}`")
    if used_sample_data:
        st.info(
            "Curated parquet was missing (or FORCE_SAMPLE_DATA=true), so sample data was bootstrapped automatically."
        )

    try:
        summary = get_dataset_summary(curated_path)
    except Exception as exc:
        st.error(f"Failed to load curated dataset: {exc}")
        st.stop()

    col1, col2, col3 = st.columns(3)
    col1.metric("Restaurants", summary.get("restaurant_count", 0))
    col2.metric("Localities", summary.get("locality_count", 0))
    col3.metric("Cities", summary.get("city_count", 0))

    try:
        localities = get_localities(curated_path)
    except Exception:
        localities = []

    with st.form("recommendation_form"):
        location = st.selectbox("Locality", options=localities) if localities else st.text_input(
            "Locality", value=""
        )
        budget = st.number_input(
            "Budget for two (numeric max)",
            min_value=0.0,
            value=1000.0,
            step=100.0,
        )
        cuisine = st.text_input("Cuisine", value="Italian")
        minimum_rating = st.slider("Minimum rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1)
        additional_preferences = st.text_area("Additional preferences (optional)", value="")
        top_k = st.slider("Top K", min_value=1, max_value=50, value=10, step=1)
        submitted = st.form_submit_button("Get recommendations")

    if not submitted:
        return

    try:
        payload = UserPreferenceInput(
            location=location,
            budget=float(budget),
            cuisine=cuisine,
            minimum_rating=float(minimum_rating),
            additional_preferences=additional_preferences or None,
            top_k=top_k,
        )
    except ValidationError as exc:
        st.error(f"Invalid input: {exc}")
        return

    with st.spinner("Generating recommendations..."):
        try:
            response = run_recommendation_orchestration(payload, curated_path=curated_path)
        except Exception as exc:
            st.error(f"Recommendation request failed: {exc}")
            return

    render_recommendations(response)
    with st.expander("Response metadata"):
        st.json(response.metadata.model_dump())


if __name__ == "__main__":
    main()
