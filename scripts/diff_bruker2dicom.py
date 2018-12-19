from __future__ import print_function

import filecmp
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile

import odil

import dicomdiff
import jsondiff

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    input_ = os.path.join(root, "input")
    baseline = os.path.join(root, "baseline")
    
    tests = [
        [
            [],
            os.path.join(input_, "20160718_115906_plateforme_fantome_nouille_other_1_7"),
            os.path.join(baseline, "20160718_115906_plateforme_fantome_nouille_other_1_7.dcm")
        ],
        [
            ["-m"],
            os.path.join(input_, "20160718_115906_plateforme_fantome_nouille_other_1_7"),
            os.path.join(baseline, "20160718_115906_plateforme_fantome_nouille_other_1_7.dcm.multi")
        ],
        [
            [],
            os.path.join(input_, "lb_140721.Bq1"),
            os.path.join(baseline, "lb_140721.Bq1.dcm")
        ],
        [
            [],
            os.path.join(input_, "lb_140721.Bx1"),
            os.path.join(baseline, "lb_140721.Bx1.dcm")
        ]
    ]
    
    for arguments, case_input, case_baseline in tests:
        case_output = tempfile.mkdtemp()
        try:
            try:
                subprocess.check_call(
                    ["bruker2dicom", "convert", "--dicomdir"]
                    +arguments
                    +[case_input, case_output])
            except subprocess.CalledProcessError as e:
                print(e.output)
                return
            
            diff(case_baseline, case_output)
        finally:
            shutil.rmtree(case_output)

def diff(baseline, test):
    # Walk the baseline to find missing missing in test and different from test
    for pathname, dirnames, filenames in os.walk(baseline):
        relative_pathname = pathname[len(os.path.join(baseline, "")):]
        test_pathname = os.path.join(test, relative_pathname)
        for filename in filenames:
            if filename == "DICOMDIR":
                logging.warning("Not testing DICOMDIR")
                continue
            
            baseline_filename = os.path.join(pathname, filename)
            test_filename = os.path.join(test_pathname, filename)
            if not os.path.isfile(os.path.join(test_pathname, filename)):
                print("{} missing in test".format(
                    os.path.join(relative_pathname, filename)))
            else:
                result = dicomdiff.diff(
                    baseline_filename, test_filename, True,[
                        str(getattr(odil.registry, x)) for x in [
                            "MediaStorageSOPInstanceUID", "SOPInstanceUID", 
                            "InstanceCreationDate", "InstanceCreationTime", 
                            "SpecificCharacterSet", "ContentDate",
                            "ContentTime", "EncapsulatedDocument"]])
                
                # EncapsulatedDocument may contain different binary 
                # representation of the same Bruker data set: process 
                # separately
                baseline_bruker = get_encapsulated_document(baseline_filename)
                test_bruker = get_encapsulated_document(test_filename)
                if any(x is not None for x in [baseline_bruker, test_bruker]):
                    differences = jsondiff.get_differences(baseline_bruker, test_bruker)
                    for difference in differences:
                        path = [str(x) for x in difference[0]]
                        reason = difference[1]
                        details = difference[2:]
                        print(
                            "{}: {}, {}".format(
                                "/".join(path), 
                                reason, " ".join(str(x) for x in details)))
    
    # Walk the test to find files missing in baseline (the difference between 
    # files has already been tested).
    for pathname, dirnames, filenames in os.walk(test):
        relative_pathname = pathname[len(os.path.join(test, "")):]
        baseline_pathname = os.path.join(baseline, relative_pathname)
        for filename in filenames:
            if not os.path.isfile(os.path.join(baseline_pathname, filename)):
                print("{} missing in baseline".format(
                    os.path.join(relative_pathname, filename)))

def get_encapsulated_document(path):
    with odil.open(path, "rb") as fd:
        data_set = odil.Reader.read_file(fd)[1]
    if "EncapsulatedDocument" in data_set:
        data = data_set.as_binary("EncapsulatedDocument")[0].get_memory_view().tobytes()
        return json.loads(data.decode())
    else:
        return None

if __name__ == "__main__":
    sys.exit(main())