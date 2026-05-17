import sys
import os
import pickle

# Automatically finds your project root directory
project_root = r"d:\Collage\Semester 6\Unsuperwised Learning\Project\weather-pattern-clustering"
sys.path.append(project_root)

# Now Python can find the 'src' module
model_path = os.path.join(project_root, "outputs", "models", "gmm_model.pkl")

with open(model_path, 'rb') as file:
    model = pickle.load(file)

print("Model loaded successfully!")
