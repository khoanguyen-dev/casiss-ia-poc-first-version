import spacy
from spacy.training.example import Example
from spacy.util import minibatch, compounding
import random
from migrant_questions_data import TRAINING_DATA

# Step 1: Load a pre-trained French model
nlp = spacy.load("fr_core_news_sm")

# Step 2: Remove unnecessary components
for pipe in ["parser", "ner", "tagger"]:
    if pipe in nlp.pipe_names:
        nlp.remove_pipe(pipe)

# Step 3: Add the TextCategorizer component
if "textcat" not in nlp.pipe_names:
    textcat = nlp.add_pipe("textcat", last=True)
else:
    textcat = nlp.get_pipe("textcat")

# Add labels (categories)
categories = [
    "Santé", "Titre de séjour", "Cours de français", "Travail", "Logement",
    "Assurances", "Aides sociales", "Impôts", "Formation", "État civil",
    "Vie pratique", "Vie sociale", "Droits politiques", "Interprétation",
    "Arrivée", "Contacts utiles"
]

for category in categories:
    textcat.add_label(category)

# Step 4: Prepare training data (minimal example for demonstration)
TRAINING_DATA = [
    ("Comment puis-je obtenir une carte de santé ?", {"cats": {"Santé": 1.0, **{cat: 0.0 for cat in categories if cat != "Santé"}}}),
    ("Quelles sont les démarches pour renouveler mon titre de séjour ?", {"cats": {"Titre de séjour": 1.0, **{cat: 0.0 for cat in categories if cat != "Titre de séjour"}}}),
    ("Où puis-je trouver des cours de français gratuits ?", {"cats": {"Cours de français": 1.0, **{cat: 0.0 for cat in categories if cat != "Cours de français"}}}),
    ("Comment chercher un emploi en tant que migrant ?", {"cats": {"Travail": 1.0, **{cat: 0.0 for cat in categories if cat != "Travail"}}}),
]

# Step 5: Split data into training and validation sets
random.shuffle(TRAINING_DATA)
split = int(0.9 * len(TRAINING_DATA))
train_data = TRAINING_DATA[:split]
valid_data = TRAINING_DATA[split:]

# Step 6: Define the training function
def train_model(nlp, train_data, valid_data, n_iter=20):
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "textcat"]
    with nlp.disable_pipes(*other_pipes):  
        optimizer = nlp.begin_training()
        for i in range(n_iter):
            random.shuffle(train_data)
            losses = {}
            batches = minibatch(train_data, size=compounding(4.0, 32.0, 1.001))
            for batch in batches:
                texts, annotations = zip(*batch)
                examples = [Example.from_dict(nlp.make_doc(text), annotation) for text, annotation in zip(texts, annotations)]
                nlp.update(examples, drop=0.3, losses=losses)
            
            with nlp.use_params(optimizer.averages):
                scores = evaluate_model(nlp, valid_data)
            print(f"Iteration {i + 1}, Losses: {losses}, Accuracy: {scores['accuracy']:.3f}")

def evaluate_model(nlp, data):
    correct = 0
    total = len(data)
    for text, annot in data:
        doc = nlp(text)
        predicted_category = max(doc.cats, key=doc.cats.get)
        true_category = max(annot['cats'], key=annot['cats'].get)
        if predicted_category == true_category:
            correct += 1
    return {"accuracy": correct / total}

# Step 7: Train the model
print("Starting training...")
train_model(nlp, train_data, valid_data)
print("Training completed!")

# Step 8: Define categorization function with default category
CONFIDENCE_THRESHOLD = 0.3

def categorize_text(text: str) -> dict:
    """Classify text with fallback to 'default' category"""
    doc = nlp(text)
    scores = doc.cats
    max_category = max(scores, key=scores.get)
    max_score = scores[max_category]
    
    # Add default category if confidence is low
    if max_score <= CONFIDENCE_THRESHOLD:
        return {
            "text": text,
            "categories": scores,
            "predicted_category": "default",
            "confidence": max_score
        }
    
    return {
        "text": text,
        "categories": scores,
        "predicted_category": max_category,
        "confidence": max_score
    }

# Step 9: Test the trained model on new examples
test_texts = [
    "Comment puis-je trouver un médecin qui parle ma langue ?",
    "Quels documents dois-je fournir pour ma demande de titre de séjour ?",
    "Y a-t-il des cours du soir pour apprendre le français ?",
    "Comment puis-je faire reconnaître mes diplômes pour travailler ici ?",
    "J’ai besoin de lunettes, puis-je les obtenir avec l’aide sociale?",
    "Je suis étudiant boursier avec un permis B réfugié. Si je veux travailler, combien d'heures puis-je travailler?",
    "Bonjour, comment ça va ?",  # Generic greeting (should be default)
    "Quelle est la capitale de la France ?",  # Unrelated question (should be default)
    "Comment renouveler mon titre de séjour ?",  # Clear category
]

print("\nTesting the model on new texts...")
for text in test_texts:
    result = categorize_text(text)
    print(f"Texte : {result['text']}")
    print(f"Catégories prédites : {result['categories']}")
    print(f"Catégorie prédite : {result['predicted_category']} (Confiance : {result['confidence']:.2f})")
    print("---")

# Step 10: Save the trained model to disk
output_dir = "./french_migrant_questions_model"
nlp.to_disk(output_dir)
print(f"Modèle sauvegardé dans {output_dir}")
