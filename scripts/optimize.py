import json
import os
import sys
import optuna

# Add repo root to sys.path so we can import lorex
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lorex.db.session import init_db, get_session, Base, engine
from scripts.evaluate import setup_mock_db
from lorex.engine.retrieval import HybridRetrievalEngine

def load_cases():
    with open('tests/benchmark_cases.json', 'r') as f:
        return json.load(f)

def objective(trial):
    cases = load_cases()
    
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    init_db()
    
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session = get_session()
    try:
        setup_mock_db(session, cases)
        
        alpha = trial.suggest_float("alpha", 0.1, 1.0)
        beta = trial.suggest_float("beta", 0.0, 1.0)
        gamma = trial.suggest_float("gamma", 0.1, 1.0)
        delta = trial.suggest_float("delta", 0.1, 1.0)
        
        # We need to explicitly name the module so we don't shadow it with `engine = ...`
        from lorex.engine.retrieval import HybridRetrievalEngine
        retrieval_engine = HybridRetrievalEngine(alpha, beta, gamma, delta)
        
        rec_acc = 0
        temp_acc = 0
        
        for case in cases:
            query = case['query']
            expected = case['expected_recommendation'].lower()
            
            results = retrieval_engine.retrieve(query, session, top_k=1)
            if results:
                top_exp, score = results[0]
                
                # Recommendation Accuracy
                if expected in top_exp.action.lower():
                    rec_acc += 1
                    
                # Temporal Accuracy
                if top_exp.status == "VERIFIED":
                    temp_acc += 1
                    
        rec_acc_score = rec_acc / len(cases)
        temp_acc_score = temp_acc / len(cases)
        
        # Calculate F1 Score
        if (rec_acc_score + temp_acc_score) == 0:
            f1_score = 0.0
        else:
            f1_score = 2 * (rec_acc_score * temp_acc_score) / (rec_acc_score + temp_acc_score)
            
        return f1_score
    finally:
        session.close()

def run_bayesian_optimization():
    print("Running Bayesian Optimization for HybridRetrievalEngine weights using Optuna...")
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=50)
    
    print("\n==========================================")
    print(" LORE-X Algorithmic Optimization Result ")
    print("==========================================")
    print(f"Optimal F1 Score: {study.best_value * 100:.1f}%")
    print(f"Best Weights:")
    for key, value in study.best_params.items():
        print(f"  {key}: {value:.3f}")
    print("==========================================")

if __name__ == "__main__":
    run_bayesian_optimization()
