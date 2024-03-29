# -- coding: utf-8 --

import os.path
import sys
from xml.etree import ElementTree

# script accepts the following arguments
# 1. path to the global xml
# 2. name of the output file
# 3. list of tests or '*' or "__all". The List of tests may be comma-separated or space separated. If the list of tests
#    is space separated, then you should enclose the parameter in quotation marks
# 4. prefix for test cases names. If the name of test case isn't start with the prefix, script adds the prefix
#    to the name of test cases specified in the 3-rd argument.
#
# E.g.:
# xml_collector D:\TMP\consolidate\desktop\GlobalXML.xml D:\TMP\output\new_xml.xml testC375501,testC375502
# xml_collector D:\TMP\consolidate\desktop\GlobalXML.xml new_xml.xml "C375501 C375502" test
# xml_collector D:\TMP\consolidate\desktop\GlobalXML.xml D:\TMP\output\new_xml.xml *
# xml_collector D:\TMP\consolidate\desktop\GlobalXML.xml D:\TMP\output\new_xml.xml __all

# ------------------------------------ global variables ------------------------------------
global_xml_path = "global.xml"  # path to the global xml file
output_file_name = "output.xml"  # path to the output xml file
list_of_tests = []  # list of tests to be collected
collect_all_test_cases = False  # should we collect all test cases?
test_cases_prefix = ""

# test_cases_dict - dictionary, that stores information about collected tests.
# For example,
# test_cases_dict = {'Bar_ChartOptions_ChartTab_General':
#                      {'com.SiemensXHQ.tests.ui.consolidated.charts.barchart.BarChartTest': ['testC1004, testC1005']}}
test_cases_dict = {}  # dictionary, that stores information about collected tests.
collected_tcs = []  # list of collected tests
extended_log_output = False  # should we print additional information about collecting tests in a global xml file?
python_version = 0  # version of the Python


# --------------------------------------- functions ----------------------------------------
def set_variables():
    print("Python version: " + str(sys.version_info[0]) + "." + str(sys.version_info[1]))
    global python_version
    python_version = sys.version_info[0] * 10 + sys.version_info[1]


def parse_args():
    cmd_line = ""
    for i, s in enumerate(sys.argv):
        if i > 0:
            cmd_line = cmd_line + " \"" + s + "\""
        else:
            cmd_line = s
    print("Command line: " + cmd_line)
    if len(sys.argv) > 1:
        global global_xml_path
        global_xml_path = sys.argv[1]
        if len(sys.argv) > 2:
            global output_file_name
            output_file_name = sys.argv[2]
            if len(sys.argv) > 3:
                global list_of_tests
                if "*" == sys.argv[3] or "__all" == sys.argv[3]:
                    global collect_all_test_cases
                    collect_all_test_cases = True
                else:
                    arg_list_of_tests = sys.argv[3].replace(",", " ")
                    list_of_tests = arg_list_of_tests.split()
                    # map(str.strip, list_of_tests)
                    # if python_version < 30:
                    #     list_of_tests = filter(None, list_of_tests)
                    #  else:
                    #     list_of_tests = list(filter(None, list_of_tests))
                if len(sys.argv) > 4:
                    if not collect_all_test_cases:
                        global test_cases_prefix
                        test_cases_prefix = sys.argv[4]
                        for i, s in enumerate(list_of_tests):
                            if not list_of_tests[i].startswith(test_cases_prefix):
                                list_of_tests[i] = test_cases_prefix + list_of_tests[i]

    print("-------------------------------------------------------------")
    print("Arguments:")
    print("path to XML: " + global_xml_path)
    print("output file name: " + output_file_name)
    if collect_all_test_cases:
        print("list of tests: all tests")
    else:
        print("list of tests: " + str(list_of_tests))
    if len(test_cases_prefix) > 0:
        print("test cases names' prefix: " + test_cases_prefix)


def verify_args():
    global list_of_tests
    if not os.path.exists(global_xml_path):
        print("Error: can't find a global xml file")
        quit(111)

    try:
        _file = open(output_file_name, "w+")
        _file.close()
    except FileNotFoundError as e:
        print("Error: cant create an output file: " + output_file_name)
        print("Exception message: " + str(e))
        quit(112)

    if not collect_all_test_cases and len(list_of_tests) == 0:
        print("Error: list of tests should be non-empty")
        quit(113)

    return True


def look_for_tests():
    print("-------------------------------------------------------------")
    print("Looking for the tests in xml: " + global_xml_path)
    look_for_tests_in_xml(global_xml_path, test_cases_dict, "", collected_tcs)


def look_for_tests_in_xml(path_to_xml, tc_dict, output_prefix, _collected_tcs):
    tree = ElementTree.parse(path_to_xml)
    root = tree.getroot()
    for node in root:
        look_for_tests_in_node(path_to_xml, tc_dict, node, collect_all_test_cases,
                               list_of_tests, output_prefix, _collected_tcs)


def look_for_tests_in_node(path_to_xml, tc_dict, node, need_to_collect_all_tcs,
                           _list_of_tests, output_prefix, _collected_tcs):
    if "test" == node.tag:
        test_name = node.attrib["name"]
        write_to_log(output_prefix + "test name = ", test_name)
        for class_element in node[0]:
            if "class" == class_element.tag:
                class_name = class_element.attrib["name"]
                write_to_log(output_prefix + "\tclass name = ", class_name)
                for include_elem in class_element[0]:
                    if "include" == include_elem.tag:
                        test_case_name = include_elem.attrib["name"]
                        if need_to_collect_all_tcs or test_case_name in _list_of_tests:
                            # test case is found, add it to dictionary
                            write_to_log(output_prefix + "\t\ttest = ", test_case_name, "- collected")
                            _collected_tcs.append(test_case_name)
                            add_test_case_to_dictionary(tc_dict, test_name, class_name, test_case_name)
                        else:
                            write_to_log(output_prefix + "\t\ttest = ", test_case_name)
                write_to_log()
    elif "suite-files" == node.tag:
        for suite_file_elem in node:
            if "suite-file" == suite_file_elem.tag:
                new_prefix = output_prefix + "\t"
                relative_path = suite_file_elem.attrib["path"].replace('\\', os.sep).replace('/', os.sep)
                new_file_name = os.path.join(os.path.dirname(os.path.abspath(path_to_xml)), relative_path)
                write_to_log(new_prefix + "-------------------------")
                write_to_log(new_prefix + "Looking for in a new xml: " + new_file_name)
                look_for_tests_in_xml(new_file_name, tc_dict, new_prefix, _collected_tcs)
                write_to_log(new_prefix + "Search in " + new_file_name + " is completed\n")


def add_test_case_to_dictionary(tc_dict, xml_test_name, xml_class_name, xml_test_case_name):
    if xml_test_name in tc_dict:
        if xml_class_name in tc_dict[xml_test_name]:
            tc_dict[xml_test_name][xml_class_name].extend([xml_test_case_name])
        else:
            tc_dict[xml_test_name][xml_class_name] = [xml_test_case_name]
    else:
        tc_dict[xml_test_name] = {xml_class_name: [xml_test_case_name]}


def write_test_cases_dict_to_xml():
    write_to_log("-------------------------------------------------------------")
    write_to_log(len(collected_tcs), "test cases were collected:", collected_tcs)
    initial_prefix = "\n\t"
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n' \
                 '<!DOCTYPE suite SYSTEM "http://testng.org/testng-1.0.dtd">\n'
    blank_xml = '<suite name="mergedSuite">\n' + initial_prefix + '</suite>'
    parser = ElementTree.XMLParser(encoding="utf-8")
    output_xml_tree = ElementTree.fromstring(blank_xml, parser=parser)
    listeners_elem = ElementTree.SubElement(output_xml_tree, 'listeners')
    listeners_elem.text = initial_prefix + "\t"
    listener_elem = ElementTree.SubElement(listeners_elem, 'listener')
    listener_elem.tail = initial_prefix
    listener_elem.set("class-name", "com.SiemensXHQ.core.configuration.MethodAsTestListener")
    create_xml_tree(output_xml_tree, test_cases_dict, initial_prefix)
    if len(output_xml_tree) > 1:
        listeners_elem.tail = "\n" + initial_prefix
    else:
        listeners_elem.tail = "\n\n"

    output_file = open(output_file_name, "w+")
    output_file.write(xml_header)
    if python_version < 30:
        output_file.write(ElementTree.tostring(output_xml_tree, method="xml"))
    else:
        output_file.write(ElementTree.tostring(output_xml_tree, encoding="unicode", method="xml"))
    if len(collected_tcs) == 0:
        print("Error: 0 test cases were written to the file: " + output_file_name)
        quit(101)
    else:
        if extended_log_output:
            print("Test cases were successfully written to the file: " + output_file_name)
        else:
            print(str(len(collected_tcs)) + " test cases were successfully written to the file: " + output_file_name)


def create_xml_tree(xml_tree, tc_dict, initial_prefix):
    dict_len = len(tc_dict)
    index = 1
    for test_key, test_dict in tc_dict.items():
        test_elem = ElementTree.SubElement(xml_tree, 'test')
        test_elem.set("name", test_key)
        if index < dict_len:
            test_elem.tail = "\n" + initial_prefix
        else:
            test_elem.tail = "\n\n"
        test_elem.text = initial_prefix + "\t"
        classes_elem = ElementTree.SubElement(test_elem, 'classes')
        classes_elem.tail = initial_prefix
        classes_elem.text = initial_prefix + "\t\t"
        for class_key, class_list_of_tests in test_dict.items():
            class_elem = ElementTree.SubElement(classes_elem, 'class')
            class_elem.tail = initial_prefix + "\t"
            class_elem.text = initial_prefix + "\t\t\t"
            class_elem.set("name", class_key)
            methods_elem = ElementTree.SubElement(class_elem, 'methods')
            methods_elem.tail = initial_prefix + "\t\t"
            methods_elem.text = initial_prefix + "\t\t\t\t"
            for test in class_list_of_tests:
                include_elem = ElementTree.SubElement(methods_elem, 'include')
                if test == class_list_of_tests[-1]:
                    include_elem.tail = initial_prefix + "\t\t\t"
                else:
                    include_elem.tail = initial_prefix + "\t\t\t\t"
                include_elem.set("name", test)
        index = index + 1


def write_to_log(*strings):
    if extended_log_output:
        c_strings = [str(i) for i in strings]
        print(" ".join(c_strings))
        # print(*strings) - don't work in Python 2.x and earlier


# ------------------------------------------ MAIN ------------------------------------------
set_variables()
parse_args()
if verify_args():
    look_for_tests()
    write_test_cases_dict_to_xml()
