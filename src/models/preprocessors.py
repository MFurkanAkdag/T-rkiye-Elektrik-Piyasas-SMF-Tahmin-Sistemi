import pandas as pd
import numpy as np
from typing import List, Optional

class DataPreprocessor:
    """Handle data preprocessing tasks."""
    
    def __init__(self):
        self.scalers = {}
    
    
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in the dataset."""
        # Linear interpolation for continuous variables
        # !!! You may use different types of interpolations
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].interpolate(method='linear') # You may use different methods for interpolation
        return df
    
    # You may use remove outliers or not ,nstead you may replace these values with constants or clever values 
    def remove_outliers(self, df: pd.DataFrame, columns: List[str], method: str = 'iqr') -> pd.DataFrame:
        """Remove outliers using specified method."""
        if method == 'iqr':
            for col in columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                df = df[~((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR)))]
        return df
    # You may apply different type of scalers such as MIN-MAX, Scalar, Standard and other methods
    def scale_features(self, df: pd.DataFrame, columns: List[str], method: str = 'standard') -> pd.DataFrame:
        """Scale features using specified method."""
        if method == 'standard':
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            df[columns] = scaler.fit_transform(df[columns])
            self.scalers['standard'] = scaler
        return df