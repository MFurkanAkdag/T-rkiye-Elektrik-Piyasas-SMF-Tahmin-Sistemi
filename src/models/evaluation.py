import numpy as np
from typing import Dict

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate various evaluation metrics."""
    
    def mape(y_true, y_pred):
        return np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    
    def rmse(y_true, y_pred):
        return np.sqrt(np.mean((y_true - y_pred) ** 2))
    
    def mae(y_true, y_pred):
        return np.mean(np.abs(y_true - y_pred))
    
    return {
        'mape': mape(y_true, y_pred),
        'rmse': rmse(y_true, y_pred),
        'mae': mae(y_true, y_pred)
    }

def evaluate_model(model, X_test, y_test) -> Dict[str, float]:
    """Evaluate model performance."""
    predictions = model.predict(X_test)
    return calculate_metrics(y_test, predictions)