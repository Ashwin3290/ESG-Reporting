from sentence_transformers import SentenceTransformer
import numpy as np
import torch

def score_esg_narrative(user_input, best_response, worst_response):
    """
    Calculate a normalized score for an ESG narrative based on its similarity 
    to best and worst response benchmarks using Sentence-BERT embeddings.
    
    Args:
        user_input (str): The narrative to be scored
        best_response (str): The benchmark best response
        worst_response (str): The benchmark worst response
        
    Returns:
        float: A score between 0 and 1, where:
            - Scores closer to 1 indicate similarity to the best response
            - Scores closer to 0 indicate similarity to the worst response
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    user_embedding = model.encode(user_input, convert_to_tensor=True)
    best_embedding = model.encode(best_response, convert_to_tensor=True)
    worst_embedding = model.encode(worst_response, convert_to_tensor=True)
    
    distance_to_best = torch.dist(user_embedding, best_embedding).item()
    distance_to_worst = torch.dist(user_embedding, worst_embedding).item()
    normalized_score = distance_to_worst / (distance_to_best + distance_to_worst)
    
    return normalized_score