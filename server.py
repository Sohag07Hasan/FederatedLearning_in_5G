import flwr as fl
from strategy import create_strategy  
from dataloader import get_datasets, get_centralized_testset
from config import LEARNING_RATE, EPOCHS, NUM_ROUNDS, SERVER_ADDRESS, NUM_ROUNDS, HISTORY_PATH_TXT, HISTORY_PATH_PKL
from flwr.common import Metrics, Scalar
from utils import get_evaluate_fn, clear_cuda_cache
from typing import Dict, List, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import pickle


## Collecting Datasets
centralized_testset = get_centralized_testset()

#before fitting each client locally this function will send the fit configuraiton
def fit_config(server_round: int) -> Dict[str, Scalar]:
    """Return a configuration with static batch size and (local) epochs."""
    config = {
        "epochs": EPOCHS,  # Number of local epochs done by clients
        "lr": LEARNING_RATE,  # Learning rate to use by clients during fit()
    }
    return config

def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    """Aggregation function for (federated) evaluation metrics, i.e. those returned by
    the client's evaluate() method."""
    # Multiply accuracy of each client by number of examples used
    accuracies = [num_examples * m["accuracy"] for num_examples, m in metrics]
    examples = [num_examples for num_examples, _ in metrics]

    # Aggregate and return custom metric (weighted average)
    return {"accuracy": sum(accuracies) / sum(examples)}


def fit_metrics_aggregation(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    # Example: compute weighted average accuracy
    #print(metrics)
    accuracies = [num_examples * m["accuracy"] for num_examples, m in metrics]
    examples = [num_examples for num_examples, _ in metrics]

    # Aggregate and return custom metric (weighted average)
    return {"accuracy": sum(accuracies) / sum(examples)}

#Store the history
def save_history(history, path_text=HISTORY_PATH_TXT, path_pkl=HISTORY_PATH_PKL):
    with open(path_pkl, "wb") as file:
        pickle.dump(history, file)

        # Save as a plain text file
    with open(path_text, 'w') as file:
        file.write(str(history))
    print(f"history saved as text @ {path_text}")
    print(f"history saved as picle @ {path_text}")
    



if __name__ == "__main__":
    
    #clear the GPU cache
    clear_cuda_cache()

    # Define the server configuration and start the server
    server_config = fl.server.ServerConfig(num_rounds=NUM_ROUNDS)
    strategy = create_strategy(fit_config, weighted_average, get_evaluate_fn(centralized_testset), fit_metrics_aggregation)
    history = fl.server.start_server(
        server_address=SERVER_ADDRESS,
        config=server_config,
        strategy=strategy,  # Use the imported strategy
    )
    save_history(history)
