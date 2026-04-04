from transformers import pipeline

class CategorizationEngine:
    def __init__(self):
        # We load the model lazily, but for production it's memory aggressive
        self.classifier = None

    def load_model(self):
        if self.classifier is None:
            print("Loading HuggingFace zero-shot classification model...")
            self.classifier = pipeline(
                "zero-shot-classification", 
                model="typeform/distilbert-base-uncased-mnli" # Lighter model for performance
            )

    def categorize(self, title: str, description: str):
        self.load_model()
        
        text = f"{title}. {description if description else ''}"
        candidate_labels = [
            "Travel", "Meals", "Accommodation", "Software", 
            "Equipment", "Training", "Marketing", "Miscellaneous"
        ]
        
        result = self.classifier(text, candidate_labels)
        
        predicted_category = result['labels'][0]
        confidence_score = result['scores'][0]
        
        return {
            "predicted_category": predicted_category,
            "confidence_score": confidence_score
        }

categorizer = CategorizationEngine()
