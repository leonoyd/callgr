import argparse
import subprocess
import pipes
import os
import fnmatch
import os
import re
import glob

args = None

def strip_line(line):
    call_index = line.find(' -> ')
    if call_index == -1:
        return []

    call_string = line[:call_index]
    callee_style_string = line[call_index+4:]

    style_index = callee_style_string.find(' [')
    callee_string = callee_style_string[:style_index]
    style_string = callee_style_string[style_index+1:]

    return [call_string, callee_string, style_string]

def get_function_index(fn, parsed_line_list):
    fn_call_indexes = []
    fn_callee_indexes = []

    line_idx = 0
    for line in parsed_line_list:
        if -1 != line[0].find(fn):
            fn_callee_indexes.append(line_idx)
        if -1 !=  line[1].find(fn):
            fn_call_indexes.append(line_idx)
        line_idx = line_idx + 1
    return [fn_call_indexes, fn_callee_indexes]

def get_file_content(file):

    line_list = []
    for line in file:
        line_list.append(line)

    return line_list

def split_line_list(line_list):
    parsed_line_list = []
    for line in line_list[1:-1]:
        ret_list = strip_line(line)
        if ret_list:
            parsed_line_list.append(ret_list)

    return parsed_line_list

def get_table_index_recursively(fn_index, fn_call_string, parse_line_list, side, accumulated_idx):
    for idx in fn_index:
        my_fn_string = parse_line_list[idx][side]
        my_fn_index = get_function_index(my_fn_string, parse_line_list)
        if my_fn_index[side]:
            temp_fn_idx = []
            for item in my_fn_index[side]:
                if item not in accumulated_idx:
                    temp_fn_idx.append(item)

            if temp_fn_idx:
                accumulated_idx += temp_fn_idx
                tmp_idx = get_table_index_recursively(temp_fn_idx, my_fn_string, parse_line_list, side, accumulated_idx)

                if tmp_idx:
                    accumulated_idx =tmp_idx

    return accumulated_idx

def remove_duplicates(line_list):
    retval = list(set(line_list))
    return retval

def parse_arguments():
    global args

    parser = argparse.ArgumentParser(
              description='Generate a call graph for C/C++ projects')

    parser.add_argument(
        dest='functionnames',
        metavar='functionnames',
        nargs='*')

    parser.add_argument('--verbose',
        dest='verbose',
        action='store_true',
        help='verbose mode')

    parser.add_argument('-v', '--version',
        dest='version',
        action='store_true',
        help='display version information')

    parser.add_argument('-o', '--outfile',
        dest='outfile',
        action='store',
        help='output filename')

    parser.add_argument('--include',
        dest='include',
        action='store',
        help='include only function specified')

    parser.add_argument('--exclude',
        dest='exclude',
        action='store',
        help='exclude all functions but those specified')

    parser.add_argument('-A',
            dest='callcount',
            action='store',
            help='traverse and display x linkage up the stack')

    parser.add_argument('-B',
            dest='calleecount',
            action='store',
            help='traverse and display x linkage down the stack')

    parser.add_argument('-u',
            dest='update',
            action='store_true',
            help='updates the file source_mapping with recent rtl information')

    args = parser.parse_args()

def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result

parse_arguments()

if args.update:
    dot_expand_files = find ('*.expand', '.')
    program_arg = ["perl", "/usr/local/bin/egypt"]
    program_arg.extend(dot_expand_files)
    pipe = subprocess.Popen(program_arg,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    w_file = open(".source_mapping", "w")

    output, error = pipe.communicate()
    if not error:
        print("updating record")
        w_file.writelines(output)
    else:
        print("Error updating record")

    w_file.close()

file = open(".source_mapping", "r")
line_list = get_file_content(file)

#if(arg.functionnames)
#    function_list =
parsed_line_list = split_line_list(line_list)
fn_string = args.functionnames[0]
fn_idx = get_function_index(fn_string, parsed_line_list)

accumulated_idx = []
# handling call side
if fn_idx[0]:
    fn = parsed_line_list[fn_idx[0][0]]
    accumulated_idx = fn_idx[0]
    tmp_idx = get_table_index_recursively(fn_idx[0], fn, parsed_line_list, 0, accumulated_idx)
    if tmp_idx:
        accumulated_idx = tmp_idx

# handling callee side
if fn_idx[1]:
    fn = parsed_line_list[fn_idx[1][0]]
    accumulated_idx += fn_idx[1]
    tmp_idx = get_table_index_recursively(fn_idx[1], fn, parsed_line_list, 1, accumulated_idx)
    if tmp_idx:
        accumulated_idx = tmp_idx

print(line_list[0])
for idx in accumulated_idx:
    print(parsed_line_list[idx][0] + " -> " + parsed_line_list[idx][1] + " " + parsed_line_list[idx][2])
print (line_list[-1])

line = '"prvIdleTask" -> "xTaskResumeAll" [style=dotted];'
ret_list = strip_line(line)
