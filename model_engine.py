import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

def generate_synthetic_training_data(n_samples=800, random_state=42):
    np.random.seed(random_state)
    building_count = np.random.randint(50, 600, size=n_samples)
    commercial_ratio = np.random.uniform(0.02, 0.20, size=n_samples)
    has_market = np.random.choice([0, 1], size=n_samples, p=[0.4, 0.6])
    distance_to_grid_km = np.random.uniform(5, 75, size=n_samples)
    viirs_nightlights = np.random.uniform(0.0, 3.5, size=n_samples)
    travel_time_hrs = np.random.uniform(0.5, 12.0, size=n_samples)
    wealth_percentile = np.random.uniform(5, 95, size=n_samples)

    base_kwh = (
        8.0
        + 0.015 * building_count
        + 60.0 * commercial_ratio
        + 4.0 * has_market
        + 2.0 * viirs_nightlights
        - 0.05 * distance_to_grid_km
        + 0.04 * wealth_percentile
        - 0.1 * travel_time_hrs
        + np.random.normal(0, 3.0, size=n_samples)
    )
    base_kwh = np.clip(base_kwh, 5.0, 38.0)
    total_monthly_kwh = building_count * base_kwh

    return pd.DataFrame({
        'building_count': building_count,
        'commercial_ratio': commercial_ratio,
        'has_market': has_market,
        'distance_to_grid_km': distance_to_grid_km,
        'viirs_nightlights': viirs_nightlights,
        'travel_time_hrs': travel_time_hrs,
        'wealth_percentile': wealth_percentile,
        'monthly_kwh_total': total_monthly_kwh,
        'kwh_per_customer_month': base_kwh
    })

class MiniGridDemandModel:
    def __init__(self):
        self.q_p10 = GradientBoostingRegressor(loss='quantile', alpha=0.10, n_estimators=100, random_state=42)
        self.q_p50 = GradientBoostingRegressor(loss='quantile', alpha=0.50, n_estimators=100, random_state=42)
        self.q_p90 = GradientBoostingRegressor(loss='quantile', alpha=0.90, n_estimators=100, random_state=42)
        self.features = [
            'building_count', 'commercial_ratio', 'has_market',
            'distance_to_grid_km', 'viirs_nightlights', 'travel_time_hrs', 'wealth_percentile'
        ]
        self.is_trained = False

    def train(self, df):
        X = df[self.features]
        y = df['monthly_kwh_total']
        self.q_p10.fit(X, y)
        self.q_p50.fit(X, y)
        self.q_p90.fit(X, y)
        self.is_trained = True

    def predict(self, site_dict):
        if not self.is_trained:
            raise ValueError("Train model first.")
        site_df = pd.DataFrame([site_dict])[self.features]
        p10 = float(self.q_p10.predict(site_df)[0])
        p50 = float(self.q_p50.predict(site_df)[0])
        p90 = float(self.q_p90.predict(site_df)[0])
        p10 = max(100.0, p10)
        p50 = max(p10 * 1.05, p50)
        p90 = max(p50 * 1.05, p90)

        comm = site_dict['commercial_ratio']
        lf = min(0.48, 0.22 + comm * 1.2 + (0.05 if site_dict['has_market'] else 0.0))

        growth = {
            "Day 1": round(p50, 1),
            "Month 6": round(p50 * 1.15, 1),
            "Year 1": round(p50 * 1.30, 1),
            "Year 2": round(p50 * 1.55, 1),
            "Year 3": round(p50 * 1.75, 1),
            "Year 4": round(p50 * 1.95, 1),
            "Year 5": round(p50 * 2.15, 1),
        }
        return {
            "p10_low": round(p10, 1),
            "p50_base": round(p50, 1),
            "p90_high": round(p90, 1),
            "p50_daily": round(p50 / 30, 1),
            "p90_daily": round(p90 / 30, 1),
            "load_factor": round(lf * 100, 1),
            "growth": growth,
            "importances": self.q_p50.feature_importances_.tolist()
        }