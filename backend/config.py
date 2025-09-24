import yaml

# Load YAML file
with open("settings.yaml", "r") as file:
    app_config = yaml.safe_load(file)