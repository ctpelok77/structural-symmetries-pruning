#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import logging
import components
import delfi2018.selector as selector

if (sys.version_info > (3, 0)):
    import subprocess
else:
    import subprocess32 as subprocess

def get_script():
    """Get file name of main script."""
    return os.path.abspath(sys.argv[0])


def get_script_dir():
    """Get directory of main script.

    Usually a relative directory (depends on how it was called by the user.)"""
    return os.path.dirname(get_script())

def get_repo_base():
    """Get base directory of the repository, as an absolute path.

    Search upwards in the directory tree from the main script until a
    directory with a subdirectory named ".git" is found.

    Abort if the repo base cannot be found."""
    path = os.path.abspath(get_script_dir())
    while os.path.dirname(path) != path:
        if os.path.exists(os.path.join(path, ".git")):
            return path
        path = os.path.dirname(path)
    sys.exit("repo base could not be found")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)-8s %(message)s",
                        stream=sys.stdout)

    parser.add_argument("domain_file")
    parser.add_argument("problem_file")
    # parser.add_argument("plan_file")
    parser.add_argument(
        "--image-from-lifted-task", action="store_true",
        help="If true, create the abstract structure graph based on the PDDL "
        "description of the task and then create an image from it.")

    args = parser.parse_args()

    domain = args.domain_file
    problem = args.problem_file

    graph_file = components.compute_graph_for_task(domain, problem, args.image_from_lifted_task)
    img = components.compute_image_for_graph(graph_file, write_modified_size=False)

    # Use the learned model to select the appropriate planner (its command line options)
    delfi2018_model_folder = os.path.join(get_repo_base(), 'delfi', 'delfi2018', 'models')

    if args.image_from_lifted_task:
        model_subfolder = 'lifted'
    else:
        model_subfolder = 'grounded'

    json_model = os.path.join(delfi2018_model_folder, model_subfolder, 'model.json')
    h5_model = os.path.join(delfi2018_model_folder, model_subfolder, 'model.h5')
    selected_algorithm = selector.select_algorithm_from_model(json_model, h5_model, img)
    logging.info("Selected planner: {}".format(selected_algorithm))

