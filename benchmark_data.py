from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error, r2_score
from model_engine import generate_synthetic_training_data, MiniGridDemandModel

def evaluate_on_held_out():
    """
    Validates model generalization on 120 unseen settlement profiles
    to compute MAPE and R² goodness of fit.
    """
    data = generate_synthetic_training_data(n_samples=600, random_state=101)
    train_df, test_df = train_test_split(data, test_size=0.20, random_state=42)
    
    model = MiniGridDemandModel()
    model.train(train_df)
    
    test_features = test_df[model.features]
    y_true = test_df['monthly_kwh_total']
    y_pred_p50 = model.q_p50.predict(test_features)
    
    mape = mean_absolute_percentage_error(y_true, y_pred_p50)
    r2 = r2_score(y_true, y_pred_p50)
    
    print("=" * 55)
    print("VALIDATION RESULTS: UNSEEN HELD-OUT PROFILES")
    print("=" * 55)
    print(f"Validation Sites Evaluated: {len(test_df)}")
    print(f"Mean Absolute Percentage Error (MAPE): {mape * 100:.2f}%")
    print(f"Coefficient of Determination (R²):     {r2:.4f}")
    print("=" * 55)
    
    return model, mape, r2

if __name__ == "__main__":
    evaluate_on_held_out()