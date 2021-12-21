#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import logging

if (sys.version_info > (3, 0)):
    import subprocess
else:
    import subprocess32 as subprocess


GRAPH_CREATION_TIME_LIMIT = 60 # seconds
IMAGE_CREATION_TIME_LIMIT = 180 # seconds

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

def force_remove_file(file_name):
    try:
        os.remove(file_name)
    except OSError:
        pass


def compute_graph_for_task(domain, problem, image_from_lifted_task):
    repo_dir = get_repo_base()
    pwd = os.getcwd()
    if image_from_lifted_task:
        command = [sys.executable, os.path.join(repo_dir, 'src/translate/abstract_structure_module.py'), '--only-functions-from-initial-state', domain, problem]
        graph_file = os.path.join(pwd, 'abstract-structure-graph.txt')
    else:
        command = [sys.executable, os.path.join(repo_dir, 'fast-downward.py'), domain, problem, '--symmetries','sym=structural_symmetries(time_bound=0,search_symmetries=oss,dump_symmetry_graph=true)', '--search', 'astar(max([blind(),const(value=infinity)]),symmetries=sym)']
        graph_file = os.path.join(pwd, 'symmetry-graph.txt')

    # Removing the old file
    force_remove_file(graph_file)
    try:

        FNULL = open(os.devnull, 'w')
        subprocess.check_call(command, timeout=GRAPH_CREATION_TIME_LIMIT, stdout=FNULL, stderr=FNULL)
    except:
        if not os.path.isfile(graph_file):
            # Possibly hit the time limit or other errors occured.
            logging.info("Computing graph from the " + ("lifted" if image_from_lifted_task else "grounded") + " task description failed, switching to fallback!")
            return None
    return graph_file


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
    image_file_name = 'graph-gs-L-bolded-cs.png'
    image_file = os.path.join(os.getcwd(), image_file_name)
    # TODO: we should be able to not hard-code the file names
 
    # Removing the old file
    force_remove_file(image_file)

    logging.info("Computing graph representation of the planning task")
    graph_file = compute_graph_for_task(domain, problem, args.image_from_lifted_task)
    if graph_file is None:
        sys.exit("Graph creation is failed, exiting")
    logging.info("Done computing graph representation, casting graph as image")

    try:
        # Create an image from the graph for the given domain and problem.
        graph_to_image = os.path.join(get_repo_base(), 'src/translate/graph2image.py')
        command = [sys.executable, graph_to_image, 
                                    '--graph-file', graph_file,
                                    '--image-output-directory', os.getcwd(), 
                                    '--write-abstract-structure-image-reg', '--bolding-abstract-structure-image', 
                                    '--abstract-structure-image-target-size', '128']
        
        subprocess.check_call(command, timeout=IMAGE_CREATION_TIME_LIMIT)
        assert os.path.exists(image_file)
        logging.info("Image creation finished, written image to %s" % image_file)
    except:
        logging.info("Image creation failed")

