Step 1
ssh ubuntu@13.201.184.42

activate the venv
source venv/bin/activate

<!-- scp -r ./oncopro ubuntu@13.201.184.42:~/oncopro -->

Step 2: copy the project
rsync -av \
 --exclude='**pycache**/' \
 --exclude='.idea/' \
 --exclude='node_modules/' \
 --exclude='venv/' \
 --exclude='data/uberblick-solide-tumoren-16012025-heytens-aktuell.mm' \
 ./oncopro/ ubuntu@13.201.184.42:~/oncopro

cd oncopro
chmod +x setup.sh
Step 3: run setup.sh script
cd /home/ubuntu/oncopro
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

until python3 generate_db_embeddings.py; do
echo "Command failed. Retrying in 5 seconds..."
sleep 5
done
