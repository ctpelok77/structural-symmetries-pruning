#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import logging
import shutil

if (sys.version_info > (3, 0)):
    import subprocess
else:
    import subprocess32 as subprocess


GRAPH_CREATION_TIME_LIMIT = 600 # seconds
IMAGE_CREATION_TIME_LIMIT = 1800 # seconds

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


def compute_graph_for_task(problem):
    repo_dir = get_repo_base()
    pwd = os.getcwd()
 
    command = [sys.executable, os.path.join(repo_dir, 'fast-downward.py'), problem, '--symmetries','sym=structural_symmetries(time_bound=0,search_symmetries=oss,dump_symmetry_graph=true)', '--search', 'astar(max([blind(),const(value=infinity)]),symmetries=sym)']
    graph_file = os.path.join(pwd, 'symmetry-graph.txt')

    # Removing the old file
    force_remove_file(graph_file)
    try:

        FNULL = open(os.devnull, 'w')
        subprocess.check_call(command, timeout=GRAPH_CREATION_TIME_LIMIT, stdout=FNULL, stderr=FNULL)
    except:
        if not os.path.isfile(graph_file):
            # Possibly hit the time limit or other errors occured.
            logging.info("Computing graph from the grounded task description failed, switching to fallback!")
            return None
    return graph_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)-8s %(message)s",
                        stream=sys.stdout)

    parser.add_argument("sas_file")
    # parser.add_argument("image_file")

    args = parser.parse_args()

    problem = args.sas_file
    image_file = problem.replace(".sas", ".png")

    tmp_image_file = os.path.join(os.getcwd(), 'graph-gs-L-bolded-cs.png')
    # TODO: we should be able to not hard-code the file names
 
    # Removing the old file
    force_remove_file(tmp_image_file)

    logging.info("Computing graph representation of the planning task")
    graph_file = compute_graph_for_task(problem)
    if graph_file is None:
        sys.exit("Graph creation is failed, exiting")
    logging.info("Done computing graph representation, casting graph as image")

    try:
        # Create an image from the graph for the given domain and problem.
        graph_to_image = os.path.join(get_repo_base(), 'delfi/graph2image.py')
        command = [sys.executable, graph_to_image, 
                                    '--graph-file', graph_file,
                                    '--image-output-directory', os.getcwd(), 
                                    '--write-abstract-structure-image-reg', '--bolding-abstract-structure-image', 
                                    '--abstract-structure-image-target-size', '128']
        
        subprocess.check_call(command, timeout=IMAGE_CREATION_TIME_LIMIT)
        assert os.path.exists(tmp_image_file)
        shutil.copy(tmp_image_file, image_file)

        logging.info("Image creation finished, written image to %s" % image_file)
    except:
        logging.info("Image creation failed")

