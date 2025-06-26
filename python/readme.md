
This creates a folder called venv which contains the isolated Python environment.
python3 -m venv venv

# To activate the virtual environment, run the following command:
source venv/bin/activate


You can also generate it later using:


pip freeze > requirements.txt


Install all packages listed in requirements.txt:


pip install -r requirements.txt

Deactivate When Done

deactivate