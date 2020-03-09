from __future__ import print_function

import argparse
import json
import sys

import odil

import jsondiff

def main():
    parser = argparse.ArgumentParser(
        description="Print the differences between two DICOM data sets")
    parser.add_argument("a")
    parser.add_argument("b")
    parser.add_argument(
        "--header", "-H", action="store_true", help="Compare headers")
    parser.add_argument(
        "--exclude", "-x", action="append", 
        type=lambda x: str(getattr(odil.registry, x)),
        help="Exclude elements from comparison")
    arguments = parser.parse_args()
    return diff(**vars(arguments))

def diff(a, b, header, exclude):
    # WARNING? this is wrong for float values as we could have different 
    # representations for close values.
    a = [
        json.loads(odil.as_json(x)) 
        for x in odil.Reader.read_file(odil.iostream(open(a, "rb")))]
    b = [
        json.loads(odil.as_json(x)) 
        for x in odil.Reader.read_file(odil.iostream(open(b, "rb")))]
    
    differences = []
    if header:
        differences.extend(jsondiff.get_differences(a[0], b[0], exclude))
    differences.extend(jsondiff.get_differences(a[1], b[1], exclude))
    
    for difference in differences:
        path = difference[0]
        pretty_path = []
        for element in path:
            if element in ["Value", "InlineBinary", "Alphabetic"]:
                continue
            elif isinstance(element, int):
                pretty_path.append(str(element))
            else:
                tag = odil.Tag(element.encode())
                if tag in odil.registry.public_dictionary:
                    tag = odil.registry.public_dictionary[tag].keyword
                else:
                    tag = str(tag)
                pretty_path.append(tag)
        
        reason = difference[1]
        details = difference[2:]
        
        print(
            "{}: {}, {}".format(
                "/".join(pretty_path), 
                reason, " ".join(str(x) for x in details)))
    
    return 0 if (len(differences) == 0) else 1

if __name__ == "__main__":
    sys.exit(main())
