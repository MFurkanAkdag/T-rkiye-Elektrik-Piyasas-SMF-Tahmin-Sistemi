from abc import ABC, abstractmethod
import numpy as np
import pandas as pd

class BaseModel(ABC):
    """Base class for all forecasting models."""
    
    def __init__(self, name: str):
        self.name = name
        self.model = None
    
    @abstractmethod
    def fit(self, X, y):
        """Train the model."""
        pass
    
    @abstractmethod
    def predict(self, X):
        """Make predictions."""
        pass
    
    def save(self, path: str):
        """Save model to disk."""
        pass
    
    def load(self, path: str):
        """Load model from disk."""
        pass