Step 1
ssh ubuntu@3.111.29.24

activate the venv
source venv/bin/activate

<!-- scp -r ./oncopro ubuntu@3.111.29.24:~/oncopro -->

Step 2: copy the project
rsync -av \
 --exclude='**pycache**/' \
 --exclude='.idea/' \
 --exclude='node_modules/' \
 --exclude='venv/' \
 --exclude='data/uberblick-solide-tumoren-16012025-heytens-aktuell.mm' \
 ./oncopro/ ubuntu@3.111.29.24:~/oncopro

cd oncopro
chmod +x setup.sh
Step 3: run setup.sh script

./setup.sh | tee setup.log
tail -f myscript.log # follow live
less +F myscript.log # scrollable follow (quit with Ctrl‑C then q)

python -c "import torch; torch.cuda.empty_cache()"

sudo apt install screen # Only needed once
screen -S embeddings
python3 generate_db_embeddings.py
resume
screen -r 62503.embeddings
