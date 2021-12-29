#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import logging
import graph2image

import timers


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


def compute_image_for_graph(input_file, write_modified_size):

    logging.info("Computing image from given graph...")
    if not os.path.exists(input_file):
        sys.exit("Graph input file {} not found".format(input_file))
    elif not os.path.isabs(input_file):
        sys.exit("Graph input file {} is not an absolute path".format(input_file))
    else:
        logging.info("Using graph input file {}".format(input_file))


    adjacency_graph = []
    with open(input_file) as f:
        for line in f:
            line = line.rstrip('\n')
            line = line.rstrip(',')
            if line == '':
                successors = []
            else:
                successors = [int(succ) for succ in line.split(',')]
            adjacency_graph.append(successors)
        # logging.debug(adjacency_graph)

    img = None
    with timers.timing("Writing abstract structure graph grayscale 8bit image..", True):
        img = graph2image.write_matrix_image_grayscale(adjacency_graph, os.getcwd(), shrink_ratio=3, bolded=True, target_size=128, write_original_size=False, write_modified_size=write_modified_size)

    if img:
        logging.info("Image creation finished")
        if write_modified_size:
            image_file_name = 'graph-gs-L-bolded-cs.png'
            image_file = os.path.join(os.getcwd(), image_file_name) 
            logging.info("Image written to %s" % image_file)
    else:
        logging.info("Image creation failed")

    return img
