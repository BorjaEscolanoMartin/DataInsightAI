"""Generate the synthetic CSV files of the DataInsight AI public demo.

The data is invented and seeded: every run writes byte-identical files.
Column names and values are in Spanish because they are what the demo shows.
Usage: python demo/generate_demo_data.py [output_dir]
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
DAILY_SALES_CSV = "demo_ventas_diarias.csv"
HOUSING_CSV = "demo_viviendas.csv"


def daily_sales(rng: np.random.Generator) -> pd.DataFrame:
    """Fictitious online coffee shop: one row per day, no gaps (the forecast path)."""
    dates = pd.date_range("2024-10-01", "2026-09-30", freq="D")
    n = len(dates)
    t = np.arange(n)
    trend = 1800 + 1.1 * t  # gentle growth
    weekly = np.array([0.92, 0.95, 0.97, 1.0, 1.08, 1.18, 1.10])[dates.dayofweek]
    yearly = 1 + 0.12 * np.cos(2 * np.pi * (dates.dayofyear - 350) / 365.25)  # winter peak
    promotion = rng.random(n) < 0.08  # about 8 % of days have a promotion
    noise = rng.normal(1, 0.06, n)
    sales = trend * weekly * yearly * np.where(promotion, 1.25, 1.0) * noise
    black_friday = (
        (dates.month == 11) & (dates.dayofweek == 4) & (dates.day >= 22) & (dates.day <= 28)
    )
    sales = np.where(black_friday, sales * 2.6, sales)  # realistic outlier
    ticket = rng.normal(31, 2.5, n).clip(22, 42)
    orders = np.round(sales / ticket).astype(int)
    visits = np.round(orders / rng.normal(0.034, 0.003, n).clip(0.025, 0.045)).astype(float)
    visits[rng.choice(n, 6, replace=False)] = np.nan  # days without web analytics
    weekdays = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    return pd.DataFrame({
        "Fecha": dates.strftime("%Y-%m-%d"),
        "Ventas": sales.round(2),
        "Pedidos": orders,
        "Visitas web": visits,
        "Día de la semana": [weekdays[d] for d in dates.dayofweek],
        "Promoción": np.where(promotion, "Sí", "No"),
    })


def housing(rng: np.random.Generator) -> pd.DataFrame:
    """Fictitious homes for sale: no dates, so the analysis takes the regression path."""
    n = 1500
    zones = {"Centro": 2900, "Playa": 3300, "Norte": 2100, "Sur": 1900, "Periferia": 1500}
    kinds = {"Estudio": 0.95, "Piso": 1.0, "Ático": 1.2, "Adosado": 1.1}
    zone = rng.choice(list(zones), n, p=[0.22, 0.18, 0.22, 0.2, 0.18])
    kind = rng.choice(list(kinds), n, p=[0.1, 0.6, 0.12, 0.18])
    base_m2 = {"Estudio": 40, "Piso": 85, "Ático": 95, "Adosado": 140}
    metres = np.round([rng.normal(base_m2[x], base_m2[x] * 0.22) for x in kind]).clip(25, 320)
    rooms = np.clip(np.round(metres / 30 + rng.normal(0, 0.6, n)), 1, 6).astype(int)
    bathrooms = np.clip(np.round(rooms / 2 + rng.normal(0, 0.4, n)), 1, 4).astype(int)
    age = rng.integers(0, 60, n)
    terrace = rng.random(n) < np.where(kind == "Ático", 0.95, 0.45)
    sea_distance = np.where(
        zone == "Playa", rng.uniform(0.1, 1.2, n), rng.uniform(0.8, 9, n)
    ).round(1)
    price_m2 = (
        np.array([zones[z] for z in zone])
        * np.array([kinds[x] for x in kind])
        * (1 - 0.004 * age)
        * np.where(terrace, 1.06, 1.0)
        * (1 - 0.015 * sea_distance)
        * rng.normal(1, 0.08, n)
    )
    price = (metres * price_m2 / 1000).round() * 1000
    return pd.DataFrame({
        "Zona": zone,
        "Tipo": kind,
        "Terraza": np.where(terrace, "Sí", "No"),
        "Metros": metres.astype(int),
        "Habitaciones": rooms,
        "Baños": bathrooms,
        "Antigüedad (años)": age,
        "Distancia al mar (km)": sea_distance,
        "Precio": price.astype(int),
    })


def generate(output_dir: Path) -> list[Path]:
    """Write both CSV files. One generator feeds both, in this order, so the order matters."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    written = []
    for name, frame in [(DAILY_SALES_CSV, daily_sales(rng)), (HOUSING_CSV, housing(rng))]:
        path = output_dir / name
        frame.to_csv(path, index=False, encoding="utf-8")
        written.append(path)
    return written


if __name__ == "__main__":
    output = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent)
    for path in generate(output):
        print(path.name)
