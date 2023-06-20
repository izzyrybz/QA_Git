import subprocess

# Define the format string for git log
format_string = "commit:%H,Author:%an,Description:%s,Date:%cd,Parents:%p%nChanged Files:%n"

# Get the commit history with the desired format
log_output = subprocess.check_output(["git", "log", "--graph", "--pretty=format:{}".format(format_string), "--name-status"])

# Initialize an empty list to hold the commit dictionaries
commits = []

# Initialize an empty dictionary to hold the current commit information
current_commit = {}

# Iterate over the lines in the log output

for line in log_output.splitlines():
    line = line.decode("utf-8")
    #line = line.split(',')
    line = line.strip('|')
    line = line.strip()

    #print(line)
    if line.startswith("*"):
        line= line.split(',')
        
        #print("what is this",line)
        # Add the previous commit dictionary to the list, if it exists
        if current_commit:
            commits.append(current_commit)
        # Initialize a new commit dictionary
        current_commit = {
            "commit_ref": line[0].split(":")[1].strip(),
            "author": line[1].split(":")[1].strip(),
            "description": line[2].split(":")[1].strip(),
            "date": line[3].split(":")[1].strip(),
            "parents": line[4].split(":")[1].strip(),
            "changed_files": []
        }
    elif line.startswith(("A", "M", "D", "R", "C", "U")):
        print(line)
        # Add the changed file information to the current commit dictionary
        current_commit["changed_files"].append(line.strip())
    else:
        continue
        # Ignore other lines

# Add the final commit dictionary to the list
if len(current_commit)>1:
    commits.append(current_commit)

# Write the commit information to a file
with open("output.txt", "w") as f:
    for commit in commits:
        f.write(str(commit) + "\n")
