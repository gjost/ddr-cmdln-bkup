#!/usr/bin/python
description="""
Intellectual entity validator for Densho Digital Repository.
"""
epilog="""
Text to display after argument listing.
Does not appear to do linebreaks.
"""


import argparse
import sys
import unittest

#from tests.example import example_test_suite as test_suite
from tests.bagit import bagit_test_suite as test_suite


def run_tests(entity_path):
    suite = test_suite(entity_path)
    result = unittest.TestResult()
    suite.run(result)
    return result

def failure_messages(result):
    messages = []
    for failure in result.failures:
        test = failure[0]
        messages.append(test.shortDescription())
    return messages

def main():
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    #parser.add_argument('-f', help='First switch')
    parser.add_argument('entity_path', help='Path to entity directory')
    args = parser.parse_args()

    result = run_tests(args.entity_path)
    messages = failure_messages(result)
    for msg in messages:
        print(msg)

if __name__ == '__main__':
    main()
