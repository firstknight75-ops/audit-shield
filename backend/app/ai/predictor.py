from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def predict_next_month_cash_outflow(df: pd.DataFrame) -> dict:
    if df.empty or 'month_index' not in df.columns or 'amount' not in df.columns or len(df) < 3:
        return {'predicted_cash_outflow': 0.0, 'stockout_risk': 'low'}
    x = df[['month_index']].values
    y = pd.to_numeric(df['amount'], errors='coerce').fillna(0).values
    model = LinearRegression()
    model.fit(x, y)
    next_idx = np.array([[df['month_index'].max() + 1]])
    pred = float(model.predict(next_idx)[0])
    stockout_risk = 'high' if pred > y.mean() * 1.2 else 'normal'
    return {'predicted_cash_outflow': max(pred, 0.0), 'stockout_risk': stockout_risk}
