from os import walk
import os
import sys
import re
from pathlib import Path

'''
Author: Joseph Shimel
Date: 12/5/20
This script creates documentation for a Java project and each class in the
project. Descriptions of classes, methods, and fields is taken from block
comments (/* and */) just before the declaration of a class, method, or field.
'''

FILENAME = "" # Give path to src folder here
TITLE = "" # Give title of project here
DESC = "" # Give project description here


'''
Used to represent classes, fields, methods
'''
class Member:
    def __init__(self):
        self.name = ""
        self.path = ""
        self.description = ""
        self.fields = []
        self.methods = []


'''
Creates project data structure that contains packages of classes, of fields and 
methods.
Creates output directroy if it doesn't already exist.
Writes an HTML file for project and each class
'''
def main():
    outname = Path(sys.argv[0])
    packages = find_packages(FILENAME)
    filtered_packages = filter_files(packages)
    # create project directory if it's not already created
    if not os.path.exists(str(outname.parent) + "/" + TITLE):
        os.makedirs(str(outname.parent) + "/" + TITLE)
    write_project_file(filtered_packages, outname)
    # write all class HTML files
    for package in packages:
        for i in range(len(package) - 1):
            clazz = find_members(package[0] + "/" + package[i + 1])
            write_class_file(clazz, outname)


"""
Given a filename, returns a list of lists, where the first element in the sub-
list is the path to a sub-directory, and the rest are the file's name and
extension.
Packages are flat, and so nested packages will not be nested in their parent
package, they will be in the package list.
"""
def find_packages(filename, package_list = []):
    f = []
    files = []
    filenames = []
    dirnames = []
    dirpath = []
    # get both directories and files
    for(dirpath, dirnames, filenames) in walk(filename):
        f.extend(filenames)
        break
    # add path of package to package if there are files
    if len(filenames) > 0:
        files.append(filename)
    # add filenames to package
    for file in f:
        files.append(file)
    # add package to package_list
    if len(files) > 0:
        package_list.append(files)
    # recurse into directories
    for dir in dirnames:
        find_packages(filename + "\\" + dir, package_list)
    return package_list


'''
Takes in a list of file names as strings, and returns a new list of file names
where each file is a java file.
Returns new list of .java filenames
'''
def filter_files(package_list):
    new_package_list = []
    for package in package_list:
        new_file = []
        for file in package:
            if file[1] == ":" or (len(file) >= 5 and file[-5:] == ".java"):
                new_file.append(file)
        new_package_list.append(new_file)
    return new_package_list


'''
Takes in a filename, returns the UTF8 text in the file
'''
def read_file(filename):
    file = open(filename, "r", encoding="utf8", errors="ignore")
    text = file.read()
    file.close()
    return text


'''
Goes through the file and finds every public class, field, and method in 
the file. Returns a list of class object with its name, fields, and methods
'''
def find_members(filename):
    clazz = Member()
    clazz.path = filename

    text = read_file(filename)
    tokens = re.compile("(?=[ {}\n=;\)\(])|(?<=[\(\)])").split(text)
    tokens = list(filter(lambda a: a is not None and not "@Override" in a, tokens))
    member_name = ""
    go = False;
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.strip() == "public":
            go = True
        elif go and token == "{":
            # Class
            go = False
            clazz.name = member_name;
            end = find_end_comment(tokens, i)
            start = find_start_comment(tokens, end)
            clazz.description = get_comment(tokens, start, end)
            member_name = ""
        elif go and (token == "=" or token == ";"):
            # Field
            go = False
            clazz.fields.append(get_member(tokens, i, member_name))
            member_name = ""
        elif go and token == "(":
            # Method
            go = False
            # get parameter list and add it to name
            while i < len(tokens) and "{" not in tokens[i]:
                member_name += tokens[i].replace("\n", "")
                i += 1
            clazz.methods.append(get_member(tokens, i, member_name))
            member_name = ""
        elif go:
            member_name += token.strip() + " "
        i += 1
    return clazz


'''
Takes in a token list, and a position in that list, and creates a member
with the name and description.
The name is taken from the signature, and the description is the block
comment immediately proceeding it, if there is any.
'''
def get_member(tokens, i, member_name):
    member = Member()
    member.name = member_name
    end = find_end_comment(tokens, i)
    start = find_start_comment(tokens, end)
    member.description = get_comment(tokens, start, end)
    return member


'''
Finds the first "*/ public" tokens before the position i in the token list.
A 'public' token must be immediately proceeded by a '*/' token, otherwise, 
returns -1
'''
def find_end_comment(tokens, i):
    while len(tokens) > i >= 0 and tokens[i].strip() != "*/":
        # Member might not be commented, prevents finding other comments
        if tokens[i].strip() == "public" and tokens[i-1].strip() != "*/":
            return -1
        i -= 1
    return i


'''
Finds the first /** token before the position i in the token list. Returns -1
if none found
'''
def find_start_comment(tokens, i):
    while len(tokens) > i > 0 and tokens[i].strip() != "/**" and tokens[i].strip() != "/*":
        i -= 1
    return i


'''
Extracts the comment in tokens list from start to end, removes any *'s, and
adds a new line before any annotation
'''
def get_comment(tokens, start, end):
    comment = ""
    for i in range(start + 1, end):
        comment += tokens[i].replace("*", "").replace("@", "<br>@")
    return comment


'''
Creates and writes the project HTML page, which has a list of tables for each
package in the project
'''
def write_project_file(packages, outname):
    with open(str(outname.parent) + "/" + TITLE + "/" + TITLE + ".html", "w") as output:
        write_header(output, TITLE, "Classes", DESC)
        for package in packages:
            if len(package) > 1:
                write_table(output, package_to_member_list(package), package[0][len(FILENAME) + 1:].replace("\\", "."))
        write_footer(output)


'''
Takes in a package and converts it to a list of classes
'''
def package_to_member_list(package):
    member_list = []
    for i in range(len(package) -1):
        clazz = find_members(package[0] + "/" + package[i + 1])
        name = clazz.path.split("/")[-1].replace(".java", "")
        clazz.name = "<a href=\"" + name + ".html\">" + name + ".java</a>"
        member_list.append(clazz)
    return member_list


'''
Creates and writes the HTML file for a class, complete with a table for its
fields and methods, if they exist.
'''
def write_class_file(clazz, outname):
    # open output file for project page
    filename = clazz.path.split("/")[-1]
    name = filename.replace(".java", "")
    with open(str(outname.parent) + "\\" + TITLE + "\\" + name + ".html", "w") as output:
        write_header(output, TITLE + ": " + name, name + ".java", clazz.description)
        write_table(output, clazz.fields, "Fields")
        write_table(output, clazz.methods, "Methods")
        write_footer(output)


'''
Writes a header to a given HTML file
'''
def write_header(output, title, name, desc):
    output.write("<html><head><title>")
    output.write(title)
    output.write(
        "</title><link rel=\"stylesheet\" type=\"text/css\" href=\"http://josephs-projects.com/style.css\"></head><body><div class=\"content-white\"><h1><a href=\"" + TITLE + ".html\">")
    output.write(TITLE)
    output.write("</a></h1><h2>" + name + "</h2><p>")
    output.write(desc)
    output.write("</p>")


def write_footer(output):
    output.write("</div><div class=\"bottom\">Powered by <a href=\"https://github.com/Rakhyvel/Skrivare\">Skrivare</a><br>&copy; 2020 Joseph Shimel</div></body></html>")


'''
Writes a member HTML table to a given file
'''
def write_table(output, member_list, name):
    if len(member_list) > 0:
        output.write("<table><caption><h3>" + name + "</h3></caption>")
        output.write("<tr><th>Name</th><th>Description</th></tr>")
        for method in member_list:
            write_row(output, method)
        output.write("</table>")


'''
Writes a row to a given HTML table and member
'''
def write_row(output, member):
    output.write("<tr><td class=\"\"><b>" + member.name + "</b></td><td>")
    if len(member.description) == 0:
        output.write("<em>None.</em>")
    else:
        output.write(member.description)
    output.write("</td></tr>")


main()
