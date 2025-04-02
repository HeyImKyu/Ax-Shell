import os

def main():
    file_paths = [
        f"~/.config/vesktop/settings/quickCss.css",
        f"~/.config/Vencord/settings/quickCss.css"
    ]

    for path in file_paths:
        ext_path = os.path.expanduser(path)
        rewrite_file(ext_path)

def rewrite_file(file_path):
    import_file_path = os.path.expanduser(f"~/.config/matugen/styles/colors.css")

    with open(import_file_path, 'r') as import_file:
        import_content = import_file.read()

    import_content = import_content.replace("vars", "root")

    with open(file_path, 'r') as original_file:
        original_content = original_file.read()

    start_marker = '/* start fakeimport */'
    end_marker = '/* end fakeimport */'

    start_index = original_content.find(start_marker)
    end_index = original_content.find(end_marker)

    if start_index == -1 or end_index == -1:
        raise ValueError("Start or end marker not found in the original file.")

    start_marker_end = start_index + len(start_marker)
    end_marker_start = end_index

    new_content = (
        original_content[:start_marker_end] +
        '\n' + import_content + '\n' + 
        original_content[end_marker_start:]
    )

    # Write the modified content back to the original file
    with open(file_path, 'w') as original_file:
        original_file.write(new_content)

if __name__ == "__main__":
    main()
