# QA system for Git

Preprocess:

  bash earning/treelstm/download.sh -- download the pre-trained word embedding models FastText and Glove
python3 learning/treelstm/preprocess_lcquad.py -- preprocess the dataset for Tree-LSTM training 
python3 learning/treelstm/main.py -- train Tree-LSTM. The generated checkpoints files are stored in \checkpoints folder

Whole Process:

1. Enter the questions in testingdata.txt "____?" format
2. Make sure that the correct endpoint to query is selected (modify the jena endpoint in complex_queries.py, ownbuild.py, common/graph/path.py and common/graph/graph.py)
3. python3 ownbuild.py
