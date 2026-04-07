import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001";

const initialForm = {
  location: "Indiranagar",
  budget: 1200,
  cuisine: "Italian",
  minimum_rating: 4.0,
  additional_preferences: ""
};

export default function App() {
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [localities, setLocalities] = useState([]);
  const [summary, setSummary] = useState(null);

  const canSubmit = useMemo(() => !!form.location && !!form.cuisine, [form]);

  useEffect(() => {
    async function loadLocalities() {
      try {
        const response = await fetch(`${API_BASE}/localities`);
        if (!response.ok) {
          throw new Error("Failed to fetch localities");
        }
        const data = await response.json();
        const values = data.localities || [];
        setLocalities(values);
        if (values.length > 0 && !values.includes(form.location)) {
          setForm((prev) => ({ ...prev, location: values[0] }));
        }
        const summaryResponse = await fetch(`${API_BASE}/dataset-summary`);
        if (summaryResponse.ok) {
          setSummary(await summaryResponse.json());
        }
      } catch (err) {
        setError(err.message);
      }
    }
    loadLocalities();
  }, []);

  async function requestRecommendations(nextForm) {
    setLoading(true);
    setError("");
    setHasSearched(true);
    try {
      const response = await fetch(`${API_BASE}/recommendations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...nextForm,
          budget: Number(nextForm.budget),
          minimum_rating: Number(nextForm.minimum_rating),
          top_k: 200
        })
      });
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Failed to fetch recommendations");
      }
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(event) {
    event?.preventDefault();
    await requestRecommendations(form);
  }

  function updateFormField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setResult(null);
    setHasSearched(false);
  }

  return (
    <div className="page">
      <div className="hero">
        <h1 className="title">Find Your Perfect Meal with Zomato AI</h1>
        {summary && (
          <p className="muted">
            Data loaded: {summary.restaurant_count} restaurants across {summary.locality_count} localities in {summary.city_count} cities.
          </p>
        )}
        <div className="panel">
          <form onSubmit={handleSubmit}>
            <div className="grid-2">
              <label>
                Locality
                <select value={form.location} onChange={(e) => updateFormField("location", e.target.value)}>
                  {localities.length === 0 ? (
                    <option value={form.location || ""}>{form.location || "Loading..."}</option>
                  ) : (
                    localities.map((loc) => (
                      <option key={loc} value={loc}>
                        {loc}
                      </option>
                    ))
                  )}
                </select>
              </label>

              <label>
                Cuisine
                <input value={form.cuisine} onChange={(e) => updateFormField("cuisine", e.target.value)} placeholder="e.g. Italian, North Indian" />
              </label>

              <label>
                Budget (max for two)
                <input type="number" min="0" step="50" value={form.budget} onChange={(e) => updateFormField("budget", e.target.value)} />
              </label>

              <label>
                Minimum rating
                <input type="number" step="0.1" min="0" max="5" value={form.minimum_rating} onChange={(e) => updateFormField("minimum_rating", e.target.value)} />
              </label>
            </div>

            <button className="submit" type="submit" disabled={!canSubmit || loading}>
              {loading ? "Loading..." : "Get Recommendations"}
            </button>
          </form>
          {error && <p style={{ color: "crimson" }}>{error}</p>}
        </div>
      </div>

      {!hasSearched && (
        <div className="results">
          <h2>Personalized Picks for You</h2>
          <p className="muted">No records yet. Submit your preferences to see relevant restaurants.</p>
        </div>
      )}

      {hasSearched && result && (
        <div className="results">
          <h2>Personalized Picks for You</h2>
          {(!result.recommendations || result.recommendations.length === 0) ? (
            <p className="muted">No restaurants found.</p>
          ) : (
            <div className="cards">
              {result.recommendations.map((item, idx) => (
                <div key={`${item.restaurant_name}-${idx}`} className="card">
                  <h3>{item.restaurant_name}</h3>
                  <div className="muted">{item.locality || "Unknown locality"} • {item.cuisine} • Rating {item.rating ?? "N/A"} • ₹{item.estimated_cost ?? "N/A"} for two</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
