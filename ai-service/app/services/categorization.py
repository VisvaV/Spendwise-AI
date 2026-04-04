from transformers import pipeline

class CategorizationEngine:
    def __init__(self):
        self.classifier = None
        self.candidate_labels = [
            "Travel", "Meals", "Accommodation", "Software", 
            "Equipment", "Training", "Marketing", "Miscellaneous"
        ]

    def load_model(self):
        if self.classifier is None:
            print("Loading HuggingFace zero-shot classification model...")
            self.classifier = pipeline(
                "zero-shot-classification", 
                model="typeform/distilbert-base-uncased-mnli"
            )

    def categorize(self, title: str, description: str):
        text = f"{title}. {description if description else ''}".lower()
        
        # 1. Fast Path Keyword Matching
        # Using ordered list to ensure specific domains (e.g. Flight/Travel) trigger before generic terms
        keywords_priority = [
            ("Travel", ["flight", "train", "cab", "uber", "taxi", "airline", "irctc"]),
            ("Accommodation", ["hotel", "airbnb", "resort", "motel", "inn"]),
            ("Meals", ["lunch", "dinner", "food", "restaurant", "zomato", "swiggy", "breakfast", "cafe"]),
            ("Software", ["aws", "github", "notion", "subscription", "gcp", "azure", "jira", "slack"]),
            ("Equipment", ["laptop", "mouse", "keyboard", "monitor", "cable", "adapter", "macbook"]),
            ("Training", ["course", "udemy", "coursera", "certification", "seminar"]),
            ("Marketing", ["ads", "facebook ads", "google ads", "campaign", "billboard"])
        ]
        
        for category, words in keywords_priority:
            if any(word in text for word in words):
                return {
                    "predicted_category": category,
                    "confidence_score": 0.95,
                    "method": "keyword"
                }
                
        # 2. HF Pipeline
        try:
            self.load_model()
            result = self.classifier(text, self.candidate_labels)
            return {
                "predicted_category": result['labels'][0],
                "confidence_score": result['scores'][0],
                "method": "model"
            }
        except Exception as e:
            print(f"HF Model failed: {e}")
            return {
                "predicted_category": None,
                "confidence_score": None,
                "method": "fallback"
            }

categorizer = CategorizationEngine()
