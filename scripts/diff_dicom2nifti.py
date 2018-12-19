from __future__ import print_function

import filecmp
import os
import shutil
import subprocess
import sys
import tempfile

import nibabel
import numpy.testing

import jsondiff

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    input_ = os.path.join(root, "baseline")
    baseline = os.path.join(root, "baseline")
    
    tests = [
        [
            os.path.join(input_, "20160718_115906_plateforme_fantome_nouille_other_1_7.dcm"),
            os.path.join(baseline, "20160718_115906_plateforme_fantome_nouille_other_1_7.nii")
        ],
        [
            os.path.join(input_, "20160718_115906_plateforme_fantome_nouille_other_1_7.dcm.multi"),
            os.path.join(baseline, "20160718_115906_plateforme_fantome_nouille_other_1_7.nii.multi")
        ],
    ]
    
    for case_input, case_baseline in tests:
        case_output = tempfile.mkdtemp()
        try:
            try:
                subprocess.check_call(["dicom2nifti", case_input, case_output])
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
            baseline_filename = os.path.join(pathname, filename)
            test_filename = os.path.join(test_pathname, filename)
            if not os.path.isfile(os.path.join(test_pathname, filename)):
                print("{} missing in test".format(
                    os.path.join(relative_pathname, filename)))
            else:
                if filename.endswith(".json"):
                    try:
                        subprocess.check_output([
                            os.path.abspath(
                                os.path.join(
                                    os.path.dirname(__file__), "jsondiff")), 
                            baseline_filename, test_filename],
                            stderr=subprocess.STDOUT)
                    except subprocess.CalledProcessError as e:
                        print("Differences on {}".format(
                            os.path.join(relative_pathname, filename)))
                        print(e.output.decode())
                elif filename.endswith(".nii") or filename.endswith(".nii.gz"):
                    differences = get_nifti_differences(
                        baseline_filename, test_filename)
                    if differences:
                        print("Differences on {}".format(
                            os.path.join(relative_pathname, filename)))
                        for difference in differences:
                            path = [str(x) for x in difference[0]]
                            reason = difference[1]
                            details = difference[2:]
                            print(
                                "  {}: {}, {}".format(
                                    "/".join(path), 
                                    reason, " ".join(str(x) for x in details)))
                else:
                    try:
                        subprocess.check_output(
                            ["diff", baseline_filename, test_filename],
                            stderr=subprocess.STDOUT)
                    except subprocess.CalledProcessError as e:
                        print("Differences on {}".format(
                            os.path.join(relative_pathname, filename)))
    
    # Walk the test to find files missing in baseline (the difference between 
    # files has already been tested).
    for pathname, dirnames, filenames in os.walk(test):
        relative_pathname = pathname[len(os.path.join(test, "")):]
        baseline_pathname = os.path.join(baseline, relative_pathname)
        for filename in filenames:
            if not os.path.isfile(os.path.join(baseline_pathname, filename)):
                print("{} missing in baseline".format(
                    os.path.join(relative_pathname, filename)))

def get_nifti_differences(baseline_filename, test_filename):
    baseline_image = nibabel.load(baseline_filename)
    test_image = nibabel.load(test_filename)
    
    differences = []
    
    baseline_data = {}
    test_data = {}
    for field in ["dataobj", "affine"]:
        baseline_field = getattr(baseline_image, field)
        test_field = getattr(test_image, field)
        if not numpy.allclose(baseline_field, test_field):
            differences.append([
                [field], "value modified", 
                "Maximum difference: {}".format(
                    numpy.abs(baseline_field-test_field).max())])
    differences.extend(jsondiff.get_differences(baseline_data, test_data))
    
    return differences
                    
if __name__ == "__main__":
    sys.exit(main())
