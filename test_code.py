import os
import subprocess


def write_to_file(file_path, text):
    with open(file_path, "a") as f:
        f.write(text + "\n")

def analyze_code(directory):
    # List Python files in the directory and subdirectories
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    if not python_files:
        print("No Python files found in the specified directory.")
        return

    # Analyze each Python file using pylint and flake8
    for file_path in python_files:
        analysis_text = f"File \"{file_path}\"\n"

        # Run pylint
        analysis_text += "\nRunning pylint...\n"
        pylint_command = f"pylint {file_path}"
        pylint_result = subprocess.run(pylint_command, shell=True, capture_output=True, text=True)
        analysis_text += pylint_result.stdout + "\n"

        # Run flake8
        analysis_text += "Running flake8...\n"
        flake8_command = f"flake8 {file_path}"
        flake8_result = subprocess.run(flake8_command, shell=True, capture_output=True, text=True)
        analysis_text += flake8_result.stdout + "\n"

        write_to_file("test_code.txt", analysis_text)


if __name__ == "__main__":
    directory = input("Enter the directory to analyze: ")
    analyze_code(directory)
