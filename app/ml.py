from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import joblib
from tensorflow.keras.models import load_model




@dataclass
class ML_MODEL:

    model_path: Path
    model_type: str
    scaler_path: Optional[Path] = None

    model = None
    scaler = None

    def load_model(self):
        if self.model_type == 'neural network':
            self.model = load_model(self.model_path)
        elif self.model_type == 'machine learning':
            self.model = joblib.load(self.model_path)

    def load_scaler(self):
        if self.scaler_path and self.scaler_path.exists():
            self.scaler = joblib.load(self.scaler_path)


        
    





