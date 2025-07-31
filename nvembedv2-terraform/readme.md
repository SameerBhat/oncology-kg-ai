terraform init
terraform apply

Step 1
ssh ubuntu@13.204.64.230

cd /home/ubuntu/oncopro
activate the venv
source venv/bin/activate

<!-- scp -r ./oncopro ubuntu@13.204.64.230:~/oncopro -->

Step 2: copy the project
rsync -av \
 --exclude='**pycache**/' \
 --exclude='.idea/' \
 --exclude='node_modules/' \
 --exclude='venv/' \
 --exclude='data/uberblick-solide-tumoren-16012025-heytens-aktuell.mm' \
 ./oncopro/ ubuntu@13.204.64.230:~/oncopro

cd oncopro
chmod +x setup.sh
Step 3: run setup.sh script

activate the venv
source venv/bin/activate

./setup.sh | tee setup.log
tail -f myscript.log # follow live
less +F myscript.log # scrollable follow (quit with Ctrl‑C then q)

python -c "import torch; torch.cuda.empty_cache()"

sudo apt install screen # Only needed once
screen -S embeddings
python3 generate_db_embeddings.py
resume
screen -r embeddings
