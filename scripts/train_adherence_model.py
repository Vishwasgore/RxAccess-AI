"""
Train adherence prediction model
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import pickle

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_synthetic_data(n_samples=1000):
    """Generate synthetic adherence training data"""
    logger.info(f"Generating {n_samples} synthetic samples")
    
    np.random.seed(42)
    
    data = {
        'age': np.random.randint(18, 85, n_samples),
        'num_medications': np.random.randint(1, 10, n_samples),
        'doses_per_day': np.random.randint(1, 12, n_samples),
        'regimen_complexity': np.random.uniform(0, 10, n_samples),
        'cost_burden': np.random.randint(1, 6, n_samples),
        'has_side_effects': np.random.binomial(1, 0.3, n_samples),
        'chronic_condition': np.random.binomial(1, 0.7, n_samples),
        'previous_adherence_rate': np.random.uniform(0.3, 1.0, n_samples),
        'support_system_score': np.random.randint(1, 6, n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Generate target (non-adherent = 1, adherent = 0)
    # Higher risk factors = higher probability of non-adherence
    risk_score = (
        (df['age'] > 65).astype(int) * 0.1 +
        (df['num_medications'] > 5).astype(int) * 0.15 +
        (df['regimen_complexity'] > 7).astype(int) * 0.15 +
        (df['cost_burden'] > 3).astype(int) * 0.15 +
        df['has_side_effects'] * 0.15 +
        (1 - df['previous_adherence_rate']) * 0.2 +
        (5 - df['support_system_score']) / 5 * 0.1
    )
    
    # Add some randomness
    risk_score += np.random.normal(0, 0.1, n_samples)
    risk_score = np.clip(risk_score, 0, 1)
    
    # Convert to binary outcome
    df['non_adherent'] = (risk_score > 0.5).astype(int)
    
    logger.info(f"Non-adherence rate: {df['non_adherent'].mean():.2%}")
    
    return df


def train_model(df):
    """Train XGBoost model"""
    logger.info("Training XGBoost model")
    
    # Features and target
    feature_cols = [
        'age', 'num_medications', 'doses_per_day', 'regimen_complexity',
        'cost_burden', 'has_side_effects', 'chronic_condition',
        'previous_adherence_rate', 'support_system_score'
    ]
    
    X = df[feature_cols]
    y = df['non_adherent']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train XGBoost
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
        eval_metric='logloss'
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    logger.info("\nModel Performance:")
    logger.info(f"\n{classification_report(y_test, y_pred)}")
    logger.info(f"ROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.3f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    logger.info("\nFeature Importance:")
    logger.info(f"\n{feature_importance}")
    
    return model, scaler


def save_model(model, scaler):
    """Save trained model and scaler"""
    model_path = settings.models_dir / "adherence_model.pkl"
    scaler_path = settings.models_dir / "scaler.pkl"
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")
    
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    logger.info(f"Scaler saved to {scaler_path}")


def main():
    """Main training pipeline"""
    print("🤖 Training Adherence Prediction Model")
    print("=" * 50)
    
    print("\n1. Generating synthetic training data...")
    df = generate_synthetic_data(n_samples=2000)
    
    # Save training data
    data_file = settings.synthetic_data_dir / "adherence_data.csv"
    df.to_csv(data_file, index=False)
    print(f"   Saved training data to {data_file}")
    
    print("\n2. Training XGBoost model...")
    model, scaler = train_model(df)
    
    print("\n3. Saving model...")
    save_model(model, scaler)
    
    print("\n✅ Model training complete!")
    print("\nModel files:")
    print(f"  - {settings.models_dir / 'adherence_model.pkl'}")
    print(f"  - {settings.models_dir / 'scaler.pkl'}")


if __name__ == "__main__":
    main()
